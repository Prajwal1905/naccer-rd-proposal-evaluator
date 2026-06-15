
import logging
from typing import TypedDict, Optional

from app.services.llm_client import chat_completion_json

logger = logging.getLogger(__name__)

# Thresholds for triggering improvement suggestions
NOVELTY_SCORE_THRESHOLD = 50.0
COMPLIANCE_SCORE_THRESHOLD = 70
RELEVANCE_SCORE_THRESHOLD = 50

REPORT_SYSTEM_PROMPT = """You are a senior reviewer for the S&T Grant-in-Aid scheme of a \
coal-sector R&D funding body (CMPDI/NaCCER). You are given structured results from four \
automated evaluation checks on a proposal: Novelty/Duplication, Financial Compliance, \
Feasibility/Relevance, and an ML-based Approval Likelihood prediction.

Write a reviewer-style evaluation note in the same tone and structure a human committee \
member would use when summarizing a proposal for discussion. Respond ONLY as a JSON object \
with this shape:
{
  "overall_recommendation": "RECOMMEND" | "RECOMMEND WITH REVISIONS" | "NOT RECOMMENDED",
  "overall_score": <integer 0-100, a holistic score combining novelty, financial compliance, and relevance>,
  "reviewer_note": <a 3-5 paragraph reviewer-style narrative covering: (1) brief summary of the proposal's aim, (2) novelty assessment, (3) financial compliance assessment, (4) feasibility/relevance and ML prediction assessment, (5) overall recommendation with justification>,
  "key_strengths": [<list of 2-4 short strings>],
  "key_concerns": [<list of 2-4 short strings>]
}
Base the overall_score on a weighted combination: novelty (30%), financial compliance (30%), \
feasibility/relevance (40%). Be objective, specific, and reference concrete figures/findings \
from the provided data where relevant. Do not invent information not present in the inputs."""

SUGGESTIONS_SYSTEM_PROMPT = """You are a research proposal advisor for a coal-sector R&D \
funding body (CMPDI/NaCCER). A proposal has scored below acceptable thresholds in one or more \
evaluation dimensions (novelty, financial compliance, and/or feasibility/relevance). Given the \
specific issues identified, generate concrete, actionable improvement suggestions the \
applicant could implement before resubmission.

Respond ONLY as a JSON object with this shape:
{
  "improvement_suggestions": [
    {
      "dimension": "novelty" | "financial_compliance" | "feasibility_relevance",
      "issue_summary": <short string describing the issue>,
      "suggestion": <specific, actionable suggestion for resubmission, 1-3 sentences>
    }
  ]
}
Provide one suggestion per significant issue identified in the input. If an issue list is \
empty for a dimension, do not generate a suggestion for that dimension. Be specific — \
reference the actual flagged items, not generic advice."""


class AggregatedReport(TypedDict):
    overall_recommendation: str
    overall_score: int
    reviewer_note: str
    key_strengths: list[str]
    key_concerns: list[str]
    improvement_suggestions: list[dict]
    component_scores: dict


def _build_report(
    proposal_sections: dict,
    novelty_result: Optional[dict],
    financial_result: Optional[dict],
    feasibility_result: Optional[dict],
    ml_result: Optional[dict],
) -> dict:
    novelty_result = novelty_result or {}
    financial_result = financial_result or {}
    feasibility_result = feasibility_result or {}
    ml_result = ml_result or {}

    user_prompt = (
        f"PROPOSAL TITLE: {proposal_sections.get('title', '')}\n\n"
        f"PROPOSAL ABSTRACT (excerpt):\n{proposal_sections.get('abstract', '')[:800]}\n\n"
        f"--- NOVELTY CHECK RESULT ---\n"
        f"Overall novelty score: {novelty_result.get('overall_novelty_score')}\n"
        f"Flags: {novelty_result.get('flags', [])}\n"
        f"Summary: {novelty_result.get('summary', '')}\n\n"
        f"--- FINANCIAL COMPLIANCE RESULT ---\n"
        f"Compliance score: {financial_result.get('compliance_score')}\n"
        f"Issues: {financial_result.get('issues', [])}\n"
        f"Overall assessment: {financial_result.get('overall_assessment', '')}\n\n"
        f"--- FEASIBILITY/RELEVANCE RESULT ---\n"
        f"Relevance score: {feasibility_result.get('relevance_score')}\n"
        f"Priority area match: {feasibility_result.get('priority_area_match', {})}\n"
        f"Overall reasoning: {feasibility_result.get('overall_reasoning', '')}\n\n"
        f"--- ML APPROVAL PREDICTION RESULT ---\n"
        f"Approval probability: {ml_result.get('approval_probability')}\n"
        f"Predicted label: {ml_result.get('predicted_label')}\n"
        f"Top contributing factors: {ml_result.get('top_factors', [])}\n"
    )

    return chat_completion_json(REPORT_SYSTEM_PROMPT, user_prompt, max_tokens=2048)


def _build_improvement_suggestions(
    novelty_result: dict, financial_result: dict, feasibility_result: dict
) -> list[dict]:
    needs_suggestions = (
        novelty_result.get("overall_novelty_score", 100) < NOVELTY_SCORE_THRESHOLD
        or financial_result.get("compliance_score", 100) < COMPLIANCE_SCORE_THRESHOLD
        or feasibility_result.get("relevance_score", 100) < RELEVANCE_SCORE_THRESHOLD
    )

    if not needs_suggestions:
        return []

    user_prompt = (
        f"--- NOVELTY ISSUES ---\n"
        f"Novelty score: {novelty_result.get('overall_novelty_score')}\n"
        f"Flags: {novelty_result.get('flags', [])}\n\n"
        f"--- FINANCIAL COMPLIANCE ISSUES ---\n"
        f"Compliance score: {financial_result.get('compliance_score')}\n"
        f"Issues: {financial_result.get('issues', [])}\n\n"
        f"--- FEASIBILITY/RELEVANCE ISSUES ---\n"
        f"Relevance score: {feasibility_result.get('relevance_score')}\n"
        f"Operational specificity: {feasibility_result.get('operational_specificity', {})}\n"
        f"Differentiation from prior work: {feasibility_result.get('differentiation_from_prior_work', {})}\n"
        f"Overall reasoning: {feasibility_result.get('overall_reasoning', '')}\n"
    )

    try:
        result = chat_completion_json(SUGGESTIONS_SYSTEM_PROMPT, user_prompt, max_tokens=1536)
        return result.get("improvement_suggestions", [])
    except Exception as exc:
        logger.warning("Improvement suggestions generation failed: %s", exc)
        return []


def run_aggregator(
    proposal_sections: dict,
    novelty_result: Optional[dict],
    financial_result: Optional[dict],
    feasibility_result: Optional[dict],
    ml_result: Optional[dict],
) -> AggregatedReport:
    novelty_result = novelty_result or {}
    financial_result = financial_result or {}
    feasibility_result = feasibility_result or {}
    ml_result = ml_result or {}

    report = _build_report(proposal_sections, novelty_result, financial_result, feasibility_result, ml_result)
    suggestions = _build_improvement_suggestions(novelty_result, financial_result, feasibility_result)

    return {
        "overall_recommendation": report.get("overall_recommendation", "NOT RECOMMENDED"),
        "overall_score": report.get("overall_score", 0),
        "reviewer_note": report.get("reviewer_note", ""),
        "key_strengths": report.get("key_strengths", []),
        "key_concerns": report.get("key_concerns", []),
        "improvement_suggestions": suggestions,
        "component_scores": {
            "novelty_score": novelty_result.get("overall_novelty_score", 0),
            "financial_compliance_score": financial_result.get("compliance_score", 0),
            "feasibility_relevance_score": feasibility_result.get("relevance_score", 0),
            "ml_approval_probability": ml_result.get("approval_probability", 0),
        },
    }