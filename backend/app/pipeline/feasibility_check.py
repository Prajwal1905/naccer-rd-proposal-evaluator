
import logging
from typing import TypedDict

from app.services.vector_store import get_chroma_client, PRIORITY_AREAS_COLLECTION, get_embedding_function
from app.services.llm_client import chat_completion_json

logger = logging.getLogger(__name__)

PRIORITY_TOP_K = 6

FEASIBILITY_SYSTEM_PROMPT = """You are a feasibility and relevance reviewer for the S&T \
Grant-in-Aid scheme of a coal-sector R&D funding body (CMPDI/NaCCER). You are given:
1. Key sections of a NEW proposal (title, abstract, objectives, methodology).
2. Relevant excerpts from the official CIL/MoC Priority Research Areas document, including
   scoring guidance.

Using ONLY the scoring guidance and priority area definitions in the excerpts, evaluate the \
proposal and respond ONLY as a JSON object with this shape:
{
  "relevance_score": <integer 0-100>,
  "priority_area_match": {
    "category": "HIGH" | "MEDIUM" | "LOWER" | "UNCLEAR",
    "matched_area_name": <string, name of the specific priority area/sub-area matched, e.g. "A1. Mine Safety & Disaster Prevention">,
    "reasoning": <1-2 sentence explanation>
  },
  "operational_specificity": {
    "score_out_of_25": <integer 0-25>,
    "reasoning": <1-2 sentence explanation, noting whether specific CIL subsidiary/coalfield/mine type is mentioned>
  },
  "technology_domain_alignment": {
    "score_out_of_20": <integer 0-20>,
    "reasoning": <1-2 sentence explanation>
  },
  "differentiation_from_prior_work": {
    "score_out_of_15": <integer 0-15>,
    "reasoning": <1-2 sentence explanation>
  },
  "overall_reasoning": <2-3 sentence summary explaining the overall relevance_score>,
  "is_low_relevance": <true if relevance_score < 40, else false>
}
The relevance_score should be consistent with the sum of the component scores scaled to 100 \
(Priority Area Match contributes up to 40, Operational Specificity up to 25, Technology-Domain \
Alignment up to 20, Differentiation up to 15). Base your evaluation ONLY on the provided \
excerpts and proposal text; do not invent priority areas not present in the excerpts."""


class FeasibilityResult(TypedDict):
    relevance_score: int
    priority_area_match: dict
    operational_specificity: dict
    technology_domain_alignment: dict
    differentiation_from_prior_work: dict
    overall_reasoning: str
    is_low_relevance: bool
    retrieved_priority_chunks: list[str]


def _retrieve_priority_chunks(proposal_sections: dict[str, str]) -> list[str]:
    client = get_chroma_client()
    ef = get_embedding_function()
    collection = client.get_or_create_collection(name=PRIORITY_AREAS_COLLECTION, embedding_function=ef)

    query_text = (
        f"Title: {proposal_sections.get('title', '')}\n"
        f"Abstract: {proposal_sections.get('abstract', '')[:800]}\n"
        f"Objectives: {proposal_sections.get('objectives', '')[:500]}"
    )

    results = collection.query(query_texts=[query_text], n_results=PRIORITY_TOP_K)
    documents = results.get("documents", [[]])[0]
    return documents


def _score_feasibility(proposal_sections: dict[str, str], priority_chunks: list[str]) -> dict:
    priority_text = "\n\n---\n\n".join(priority_chunks)
    user_prompt = (
        f"PROPOSAL TITLE: {proposal_sections.get('title', '')}\n\n"
        f"PROPOSAL ABSTRACT:\n{proposal_sections.get('abstract', '')[:1500]}\n\n"
        f"PROPOSAL OBJECTIVES:\n{proposal_sections.get('objectives', '')[:1000]}\n\n"
        f"PROPOSAL METHODOLOGY (excerpt):\n{proposal_sections.get('methodology', '')[:800]}\n\n"
        f"RELEVANT CIL/MoC PRIORITY AREA EXCERPTS:\n{priority_text}"
    )
    return chat_completion_json(FEASIBILITY_SYSTEM_PROMPT, user_prompt, max_tokens=1536)


def run_feasibility_check(proposal_sections: dict[str, str]) -> FeasibilityResult:
    if not proposal_sections.get("abstract", "").strip() and not proposal_sections.get("objectives", "").strip():
        return {
            "relevance_score": 0,
            "priority_area_match": {"category": "UNCLEAR", "matched_area_name": "", "reasoning": "Insufficient proposal content to assess."},
            "operational_specificity": {"score_out_of_25": 0, "reasoning": "Insufficient content."},
            "technology_domain_alignment": {"score_out_of_20": 0, "reasoning": "Insufficient content."},
            "differentiation_from_prior_work": {"score_out_of_15": 0, "reasoning": "Insufficient content."},
            "overall_reasoning": "The proposal's abstract and objectives could not be extracted, so feasibility/relevance cannot be assessed.",
            "is_low_relevance": True,
            "retrieved_priority_chunks": [],
        }

    priority_chunks = _retrieve_priority_chunks(proposal_sections)
    result = _score_feasibility(proposal_sections, priority_chunks)

    return {
        "relevance_score": result.get("relevance_score", 0),
        "priority_area_match": result.get("priority_area_match", {}),
        "operational_specificity": result.get("operational_specificity", {}),
        "technology_domain_alignment": result.get("technology_domain_alignment", {}),
        "differentiation_from_prior_work": result.get("differentiation_from_prior_work", {}),
        "overall_reasoning": result.get("overall_reasoning", ""),
        "is_low_relevance": result.get("is_low_relevance", result.get("relevance_score", 0) < 40),
        "retrieved_priority_chunks": priority_chunks,
    }