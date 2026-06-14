
from app.services.llm_client import chat_completion_json

SYSTEM_PROMPT = """You are an expert assistant that extracts structured fields from \
R&D research proposal documents submitted to a coal-sector R&D funding body (NaCCER/CMPDI). \
You will be given the raw text of a proposal and a list of fields that could not be located \
by automated heading detection. Extract each requested field as accurately as possible from \
the document content, even if there is no explicit heading for it (e.g. infer 'objectives' \
from a numbered goals list, infer 'budget' from any cost/financial table or figures present). \
If a field genuinely cannot be found anywhere in the text, return an empty string for it. \
Respond ONLY with a JSON object mapping each requested field name to its extracted text. \
Do not include any other keys, commentary, or markdown formatting."""

MAX_CHARS = 12000


def llm_segment_proposal(raw_text: str, missing_fields: list[str]) -> dict[str, str]:
    truncated = raw_text[:MAX_CHARS]
    user_prompt = (
        f"Fields to extract: {', '.join(missing_fields)}\n\n"
        f"--- PROPOSAL TEXT START ---\n{truncated}\n--- PROPOSAL TEXT END ---"
    )
    result = chat_completion_json(SYSTEM_PROMPT, user_prompt, max_tokens=2048)
    cleaned = {}
    for field in missing_fields:
        value = result.get(field, "")
        cleaned[field] = value if isinstance(value, str) else str(value)
    return cleaned