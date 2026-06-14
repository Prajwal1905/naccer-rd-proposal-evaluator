
import logging
from typing import TypedDict

from app.services.vector_store import get_chroma_client, PAST_PROPOSALS_COLLECTION, get_embedding_function
from app.services.llm_client import chat_completion_json

logger = logging.getLogger(__name__)

CHECK_SECTIONS = ["abstract", "objectives", "methodology"]

HIGH_SIMILARITY_THRESHOLD = 75.0
MODERATE_SIMILARITY_THRESHOLD = 55.0

TOP_K = 3

EXPLAIN_SYSTEM_PROMPT = """You are a research proposal novelty reviewer for a coal-sector \
R&D funding body (NaCCER/CMPDI). You are given a section of a NEW proposal and the most \
similar section from a PAST (already funded or rejected) proposal, along with a computed \
similarity percentage. Write a concise (2-3 sentence) explanation of the nature of the overlap: \
what specifically is similar, and whether the new proposal appears to be largely duplicative, \
a meaningful extension/improvement, or only superficially similar (e.g. same general topic but \
different methodology/scope). Respond ONLY as a JSON object with keys "overlap_explanation" \
(string) and "verdict" (one of "duplicative", "extension", "superficial_overlap")."""


class SectionMatch(TypedDict):
    matched_proposal_id: str
    matched_title: str
    matched_section: str
    matched_research_area: str
    similarity_percent: float
    overlap_explanation: str
    verdict: str


class NoveltyResult(TypedDict):
    section_results: dict
    overall_novelty_score: float
    flags: list[str]
    summary: str


def _distance_to_similarity_percent(distance: float) -> float:
    
    similarity = 1 - (distance / 2)
    return round(max(0.0, min(1.0, similarity)) * 100, 1)


def _explain_overlap(new_text: str, matched_text: str, similarity_percent: float) -> dict:
    user_prompt = (
        f"Similarity score: {similarity_percent}%\n\n"
        f"NEW PROPOSAL SECTION:\n{new_text[:1500]}\n\n"
        f"PAST PROPOSAL SECTION:\n{matched_text[:1500]}"
    )
    try:
        return chat_completion_json(EXPLAIN_SYSTEM_PROMPT, user_prompt, max_tokens=400)
    except Exception as exc:
        logger.warning("Overlap explanation failed: %s", exc)
        return {"overlap_explanation": "Explanation unavailable due to an LLM error.", "verdict": "superficial_overlap"}


def run_novelty_check(proposal_sections: dict[str, str]) -> NoveltyResult:
    
    client = get_chroma_client()
    ef = get_embedding_function()
    collection = client.get_or_create_collection(name=PAST_PROPOSALS_COLLECTION, embedding_function=ef)

    section_results: dict[str, list[SectionMatch]] = {}
    flags: list[str] = []
    max_similarity_overall = 0.0
    section_count = 0
    similarity_sum = 0.0

    for section in CHECK_SECTIONS:
        text = proposal_sections.get(section, "").strip()
        if not text:
            continue
        section_count += 1

        results = collection.query(
            query_texts=[text],
            n_results=TOP_K,
            where={"section": section},
        )

        matches: list[SectionMatch] = []
        ids = results.get("ids", [[]])[0]
        if not ids:
            section_results[section] = []
            continue

        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]

        top_similarity = _distance_to_similarity_percent(distances[0])
        similarity_sum += top_similarity
        max_similarity_overall = max(max_similarity_overall, top_similarity)

        for dist, meta, doc in zip(distances, metadatas, documents):
            sim_pct = _distance_to_similarity_percent(dist)
            match: SectionMatch = {
                "matched_proposal_id": meta["proposal_id"],
                "matched_title": meta["title"],
                "matched_section": meta["section"],
                "matched_research_area": meta["research_area"],
                "similarity_percent": sim_pct,
                "overlap_explanation": "",
                "verdict": "",
            }
            if dist == distances[0] and sim_pct >= MODERATE_SIMILARITY_THRESHOLD:
                explanation = _explain_overlap(text, doc, sim_pct)
                match["overlap_explanation"] = explanation.get("overlap_explanation", "")
                match["verdict"] = explanation.get("verdict", "")
            matches.append(match)

        section_results[section] = matches

        if top_similarity >= HIGH_SIMILARITY_THRESHOLD:
            flags.append(
                f"HIGH similarity ({top_similarity}%) between proposal's '{section}' section and "
                f"past proposal '{matches[0]['matched_title']}' ({matches[0]['matched_proposal_id']})."
            )
        elif top_similarity >= MODERATE_SIMILARITY_THRESHOLD:
            flags.append(
                f"MODERATE similarity ({top_similarity}%) between proposal's '{section}' section and "
                f"past proposal '{matches[0]['matched_title']}' ({matches[0]['matched_proposal_id']})."
            )

    avg_similarity = (similarity_sum / section_count) if section_count else 0.0
    overall_novelty_score = round(max(0.0, 100.0 - avg_similarity), 1)

    if not flags:
        summary = (
            f"No significant overlap detected with past proposals (max similarity "
            f"{max_similarity_overall}%). Proposal appears novel relative to the reference set."
        )
    else:
        summary = (
            f"Overlap detected with {len(flags)} section(s) against past proposals "
            f"(max similarity {max_similarity_overall}%). Review flagged sections for "
            f"duplication vs. genuine extension."
        )

    return {
        "section_results": section_results,
        "overall_novelty_score": overall_novelty_score,
        "flags": flags,
        "summary": summary,
    }