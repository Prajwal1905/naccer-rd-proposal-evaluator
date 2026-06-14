
import json
import logging
import re
from typing import Optional

from groq import Groq

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None


def get_client() -> Groq:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Create a .env file from .env.example "
                "and add your Groq API key (https://console.groq.com/keys)."
            )
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    json_mode: bool = False,
) -> str:
    
    settings = get_settings()
    client = get_client()

    kwargs = dict(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


def chat_completion_json(system_prompt: str, user_prompt: str, **kwargs) -> dict:
    
    raw = chat_completion(system_prompt, user_prompt, json_mode=True, **kwargs)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(json)?|```$", "", cleaned, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON from LLM response: %s\nRaw: %s", exc, raw)
        raise