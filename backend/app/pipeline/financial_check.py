
import logging
from typing import TypedDict

from app.services.vector_store import get_chroma_client, GUIDELINES_COLLECTION, get_embedding_function
from app.services.llm_client import chat_completion_json

logger = logging.getLogger(__name__)

GUIDELINE_TOP_K = 6

EXTRACT_SYSTEM_PROMPT = """You are a financial analyst reviewing R&D proposal budgets for a \
coal-sector funding body. Given the budget and timeline text of a proposal, extract a \
structured summary of its financial parameters. Respond ONLY as a JSON object with this shape:
{
  "total_project_cost_lakhs": <number or null, total project cost in INR Lakhs>,
  "duration_months": <number or null>,
  "currency_stated": <true/false, whether currency units (INR Lakh/Crore) are explicitly stated>,
  "budget_heads": {
     "manpower_lakhs": <number or null>,
     "equipment_lakhs": <number or null>,
     "consumables_lakhs": <number or null>,
     "contingency_travel_lakhs": <number or null>,
     "overheads_lakhs": <number or null>,
     "contractual_services_lakhs": <number or null>,
     "other_lakhs": <number or null>
  },
  "year_wise_breakup_present": <true/false>,
  "co_funding_mentioned": <true/false>,
  "upfront_disbursement_100_percent": <true/false, true only if proposal explicitly requests full upfront payment>,
  "ineligible_items_mentioned": [<list of strings describing any ineligible items found, e.g. "land purchase", "vehicle purchase", "PI honorarium", "construction"> ],
  "institution_type": <one of "academic", "cil_psu", "industry", "unknown">,
  "notes": <short string with any other observations relevant to financial review>
}
If a value cannot be determined from the text, use null (for numbers) or false/empty list as appropriate. \
1 Crore = 100 Lakhs; convert all amounts to Lakhs. Do not include any keys other than those shown."""

COMPLIANCE_SYSTEM_PROMPT = """You are a financial compliance reviewer for the S&T Grant-in-Aid \
scheme of a coal-sector R&D funding body (CMPDI/NaCCER). You are given:
1. A structured JSON summary of a proposal's extracted budget figures.
2. PRE-COMPUTED percentages of each budget head relative to the Total Project Cost (TPC), and \
a pre-computed reconciliation check (sum of heads vs. stated TPC). These numbers are already \
calculated correctly — use them directly, do NOT recompute or second-guess the arithmetic.
3. Relevant excerpts from the official S&T Funding Guidelines document.

Compare the PRE-COMPUTED percentages against the ceiling percentages stated in the guideline \
excerpts (e.g. Manpower up to 40%, Equipment up to 30%, etc.). Only flag a budget head if its \
pre-computed percentage EXCEEDS the stated ceiling. If a percentage is at or below the ceiling, \
do NOT flag it, even if it is close to the limit. For each issue found, assign a severity: \
"HIGH", "MEDIUM", or "LOW", following the severity criteria described in the guideline excerpts.

Respond ONLY as a JSON object with this shape:
{
  "issues": [
    {
      "severity": "HIGH" | "MEDIUM" | "LOW",
      "issue": <short description of the violation, citing the actual computed percentage vs. the ceiling, e.g. "Manpower is 42.5% of TPC, exceeding the 40% ceiling">,
      "guideline_reference": <short reference to the relevant guideline section/rule>,
      "recommendation": <concise actionable recommendation to fix it>
    }
  ],
  "compliance_score": <integer 0-100, where 100 = fully compliant with no issues, deduct points based on number and severity of issues (HIGH=-25, MEDIUM=-10, LOW=-5, floor at 0)>,
  "overall_assessment": <2-3 sentence summary of the financial compliance status>
}
If no issues are found (i.e. all percentages are within ceilings and the budget reconciles), \
return an empty issues list and compliance_score of 100. Base your assessment ONLY on the \
provided data and guideline excerpts; do not invent rules or flag items that are within limits."""


class ComplianceIssue(TypedDict):
    severity: str
    issue: str
    guideline_reference: str
    recommendation: str


class FinancialCheckResult(TypedDict):
    extracted_budget: dict
    budget_percentages: dict
    issues: list[ComplianceIssue]
    compliance_score: int
    overall_assessment: str
    retrieved_guideline_chunks: list[str]


def _compute_budget_percentages(extracted_budget: dict) -> dict:
   
    tpc = extracted_budget.get("total_project_cost_lakhs")
    heads = extracted_budget.get("budget_heads", {}) or {}

    if not tpc or tpc <= 0:
        return {"error": "TPC is missing or zero; percentages cannot be computed."}

    percentages = {}
    total_heads = 0.0
    for head, value in heads.items():
        if value is None:
            percentages[head] = None
            continue
        pct = round((value / tpc) * 100, 1)
        percentages[head] = pct
        total_heads += value

    sum_vs_tpc_diff_pct = round(abs(total_heads - tpc) / tpc * 100, 2)

    return {
        "tpc_lakhs": tpc,
        "percentages_of_tpc": percentages,
        "sum_of_heads_lakhs": round(total_heads, 1),
        "sum_vs_tpc_difference_percent": sum_vs_tpc_diff_pct,
        "reconciles_within_2_percent": sum_vs_tpc_diff_pct <= 2.0,
    }


def _extract_budget_fields(budget_text: str, timeline_text: str) -> dict:
    combined = f"BUDGET SECTION:\n{budget_text[:3000]}\n\nTIMELINE/DURATION SECTION:\n{timeline_text[:1000]}"
    return chat_completion_json(EXTRACT_SYSTEM_PROMPT, combined, max_tokens=1024)


def _retrieve_guideline_chunks(extracted_budget: dict, budget_text: str) -> list[str]:
    client = get_chroma_client()
    ef = get_embedding_function()
    collection = client.get_or_create_collection(name=GUIDELINES_COLLECTION, embedding_function=ef)

    query_text = (
        f"Budget compliance check. TPC (Lakhs): {extracted_budget.get('total_project_cost_lakhs')}. "
        f"Duration (months): {extracted_budget.get('duration_months')}. "
        f"Budget heads: {extracted_budget.get('budget_heads')}. "
        f"Ineligible items mentioned: {extracted_budget.get('ineligible_items_mentioned')}. "
        f"Raw budget text excerpt: {budget_text[:500]}"
    )

    results = collection.query(query_texts=[query_text], n_results=GUIDELINE_TOP_K)
    documents = results.get("documents", [[]])[0]
    return documents


def _check_compliance(extracted_budget: dict, budget_percentages: dict, guideline_chunks: list[str]) -> dict:
    guidelines_text = "\n\n---\n\n".join(guideline_chunks)
    user_prompt = (
        f"PROPOSAL BUDGET SUMMARY (JSON):\n{extracted_budget}\n\n"
        f"PRE-COMPUTED BUDGET PERCENTAGES (use these directly, do not recompute):\n{budget_percentages}\n\n"
        f"RELEVANT GUIDELINE EXCERPTS:\n{guidelines_text}"
    )
    return chat_completion_json(COMPLIANCE_SYSTEM_PROMPT, user_prompt, max_tokens=1536)


def run_financial_check(proposal_sections: dict[str, str]) -> FinancialCheckResult:
    budget_text = proposal_sections.get("budget", "")
    timeline_text = proposal_sections.get("timeline", "")

    if not budget_text.strip():
        return {
            "extracted_budget": {},
            "budget_percentages": {},
            "issues": [{
                "severity": "HIGH",
                "issue": "No budget section could be found or extracted from the proposal.",
                "guideline_reference": "Section 10 - Required Financial Documentation Checklist",
                "recommendation": "Include a clearly labeled budget section with head-wise, year-wise breakup and TPC.",
            }],
            "compliance_score": 0,
            "overall_assessment": "Financial compliance cannot be assessed because no budget information was found in the proposal.",
            "retrieved_guideline_chunks": [],
        }

    extracted_budget = _extract_budget_fields(budget_text, timeline_text)
    budget_percentages = _compute_budget_percentages(extracted_budget)
    guideline_chunks = _retrieve_guideline_chunks(extracted_budget, budget_text)
    compliance = _check_compliance(extracted_budget, budget_percentages, guideline_chunks)

    return {
        "extracted_budget": extracted_budget,
        "budget_percentages": budget_percentages,
        "issues": compliance.get("issues", []),
        "compliance_score": compliance.get("compliance_score", 0),
        "overall_assessment": compliance.get("overall_assessment", ""),
        "retrieved_guideline_chunks": guideline_chunks,
    }