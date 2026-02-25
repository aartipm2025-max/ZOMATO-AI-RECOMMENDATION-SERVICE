from __future__ import annotations

from typing import Sequence

from zomato_ai.phase2.models import Restaurant, UserPreference

from .groq_client import GroqLLMClient
from .models import LLMRecommendationResult
from .parsing import parse_llm_result
from .prompt_builder import build_recommendation_prompt


def recommend_with_groq(
    *,
    client: GroqLLMClient,
    preferences: UserPreference,
    candidates: Sequence[Restaurant],
    limit: int,
) -> LLMRecommendationResult:
    """
    Ask Groq LLM to pick and explain the best restaurants from candidates.
    """
    system_prompt, user_prompt = build_recommendation_prompt(
        preferences=preferences,
        candidates=candidates,
        limit=limit,
    )
    raw = client.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
    return parse_llm_result(raw)

