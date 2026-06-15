
import re

from app.pipeline.ml_prediction import VALID_RESEARCH_AREAS, ApprovalFeatures

# Maps CIL/MoC priority area names to the
# closest matching research_area category used in the ML training dataset.
PRIORITY_AREA_TO_RESEARCH_AREA = {
    "mine safety": "Mine Safety",
    "disaster prevention": "Mine Safety",
    "environmental management": "Environmental Rehabilitation",
    "mine closure": "Environmental Rehabilitation",
    "automation": "Automation in Mining",
    "digitalization": "Automation in Mining",
    "ai in mining": "Automation in Mining",
    "coal beneficiation": "Coal Quality Assessment",
    "coal bed methane": "Coal Bed Methane",
    "cbm": "Coal Bed Methane",
    "gasification": "Underground Coal Gasification",
    "geological": "Coal Quality Assessment",
    "reserve assessment": "Coal Quality Assessment",
    "mine waste": "Mine Waste Utilization",
    "general it": "General IT Infrastructure",
    "it infrastructure": "General IT Infrastructure",
}


def map_priority_area_to_research_area(matched_area_name: str) -> str:

    if not matched_area_name:
        return "General IT Infrastructure"

    name_lower = matched_area_name.lower()
    for keyword, research_area in PRIORITY_AREA_TO_RESEARCH_AREA.items():
        if keyword in name_lower:
            return research_area

    # Exact match against valid categories as a fallback
    for area in VALID_RESEARCH_AREAS:
        if area.lower() in name_lower:
            return area

    return "General IT Infrastructure"


def count_objectives(objectives_text: str) -> int:
    
    if not objectives_text.strip():
        return 0
    # Match patterns like "1.", "2)", "- ", "* " at line starts
    matches = re.findall(r"(?:^|\n)\s*(?:\d{1,2}[\.\)]|[-*•])\s+", objectives_text)
    if matches:
        return len(matches)
    # Fallback: count sentences as a rough proxy
    sentences = [s for s in re.split(r"[.!?]\s+", objectives_text) if s.strip()]
    return max(1, len(sentences))


def build_approval_features(
    proposal_sections: dict[str, str],
    feasibility_result: dict,
    extracted_budget: dict,
) -> ApprovalFeatures:
    matched_area_name = feasibility_result.get("priority_area_match", {}).get("matched_area_name", "")
    research_area = map_priority_area_to_research_area(matched_area_name)

    institution_type = extracted_budget.get("institution_type", "unknown")
    if institution_type == "unknown":
        institution_type = "academic"  # most common default in dataset

    requested_amount_lakhs = extracted_budget.get("total_project_cost_lakhs")
    duration_months = extracted_budget.get("duration_months")
    num_objectives = count_objectives(proposal_sections.get("objectives", ""))

    return {
        "research_area": research_area,
        "institution_type": institution_type,
        "requested_amount_lakhs": requested_amount_lakhs,
        "duration_months": duration_months,
        "num_objectives": num_objectives,
    }