
import re
import json
import logging
from typing import Optional

import pdfplumber
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SECTION_PATTERNS = {
    "title": [r"^\s*title\s*[:\-]?\s*"],
    "abstract": [r"^\s*(abstract|summary|executive summary)\s*[:\-]?\s*$"],
    "objectives": [r"^\s*(objectives?|aims? and objectives?|research objectives?)\s*[:\-]?\s*$"],
    "methodology": [r"^\s*(methodology|research methodology|methods?|work plan)\s*[:\-]?\s*$"],
    "budget": [r"^\s*(budget|financial outlay|cost estimate|budget estimate)\s*[:\-]?\s*$"],
    "timeline": [r"^\s*(timeline|time schedule|project duration|milestones?|work schedule)\s*[:\-]?\s*$"],
    "deliverables": [r"^\s*(deliverables?|expected outcomes?|outputs?)\s*[:\-]?\s*$"],
}

ALL_SECTION_KEYS = list(SECTION_PATTERNS.keys())


class ExtractedProposal(BaseModel):
    title: str = ""
    abstract: str = ""
    objectives: str = ""
    methodology: str = ""
    budget: str = ""
    timeline: str = ""
    deliverables: str = ""
    raw_text: str = ""
    institution: Optional[str] = None
    research_area: Optional[str] = None


def extract_text_from_pdf(file_path: str) -> str:
   
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def _line_matches_section(line: str) -> Optional[str]:
    
    clean = line.strip().lower()
    if not clean or len(clean) > 80:
        return None
    for key, patterns in SECTION_PATTERNS.items():
        for pat in patterns:
            if re.match(pat, clean, flags=re.IGNORECASE):
                return key
    return None


def segment_text_heuristic(raw_text: str) -> ExtractedProposal:
    
    lines = raw_text.split("\n")
    sections: dict[str, list[str]] = {key: [] for key in ALL_SECTION_KEYS}
    current_section: Optional[str] = None

    title_candidate = ""
    for line in lines:
        if line.strip():
            title_candidate = line.strip()
            break

    for line in lines:
        matched = _line_matches_section(line)
        if matched:
            current_section = matched
            remainder = re.sub(SECTION_PATTERNS[matched][0], "", line.strip(), flags=re.IGNORECASE).strip()
            if remainder and matched != "title":
                sections[matched].append(remainder)
            continue
        if current_section:
            sections[current_section].append(line)

    result = ExtractedProposal(
        title=sections["title"][0] if sections["title"] else title_candidate,
        abstract="\n".join(sections["abstract"]).strip(),
        objectives="\n".join(sections["objectives"]).strip(),
        methodology="\n".join(sections["methodology"]).strip(),
        budget="\n".join(sections["budget"]).strip(),
        timeline="\n".join(sections["timeline"]).strip(),
        deliverables="\n".join(sections["deliverables"]).strip(),
        raw_text=raw_text,
    )
    return result


def extract_proposal(file_path: str) -> ExtractedProposal:
   
    raw_text = extract_text_from_pdf(file_path)
    if not raw_text.strip():
        raise ValueError("No extractable text found in PDF. The file may be scanned/image-based.")

    extracted = segment_text_heuristic(raw_text)

    missing = [k for k in ["abstract", "objectives", "methodology", "budget", "timeline"]
               if not getattr(extracted, k).strip()]

    if missing:
        try:
            from app.services.llm_extraction import llm_segment_proposal
            llm_filled = llm_segment_proposal(raw_text, missing_fields=missing)
            for key, value in llm_filled.items():
                if value and not getattr(extracted, key, "").strip():
                    setattr(extracted, key, value)
        except Exception as exc:
            logger.warning("LLM extraction fallback failed: %s", exc)

    return extracted


def proposal_to_dict(extracted: ExtractedProposal) -> dict:
    return extracted.model_dump(exclude={"raw_text"})


if __name__ == "__main__":
    import sys
    path = sys.argv[1]
    result = extract_proposal(path)
    print(json.dumps(proposal_to_dict(result), indent=2))