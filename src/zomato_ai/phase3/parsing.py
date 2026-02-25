from __future__ import annotations

import json
from typing import Any

from .models import LLMRecommendationResult


def _extract_json_object(text: str) -> str:
    """
    Best-effort extraction of a JSON object from LLM output.
    We instruct strict JSON, but this makes parsing more robust.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM output")
    return text[start : end + 1]


def parse_llm_result(text: str) -> LLMRecommendationResult:
    raw = _extract_json_object(text)
    data: Any = json.loads(raw)
    return LLMRecommendationResult.model_validate(data)

