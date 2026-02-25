from __future__ import annotations

from typing import Sequence

from sqlalchemy.engine import Engine

from zomato_ai.phase2.filtering import filter_restaurants
from zomato_ai.phase2.models import Restaurant, UserPreference
from zomato_ai.phase3.groq_client import GroqLLMClient, load_groq_config_from_env
from zomato_ai.phase3.orchestrator import recommend_with_groq
from zomato_ai.phase4.events import log_recommendation_event

from .models import PipelineRecommendation, PipelineResponse


def run_pipeline(
    *,
    engine: Engine,
    preferences: UserPreference,
) -> PipelineResponse:
    """
    End-to-end pipeline:
    User preferences → Filter candidates → Groq LLM chooses/explains → Response with restaurant details.
    """
    try:
        config = load_groq_config_from_env()
    except RuntimeError:
        # Let caller decide how to map to HTTP status.
        raise

    # Filter a larger candidate pool; LLM selects top N from it.
    candidate_pool = filter_restaurants(
        engine,
        preferences.model_copy(update={"limit": max(preferences.limit * 3, 15)}),
    )

    if not candidate_pool:
        log_recommendation_event(
            engine=engine,
            endpoint="/recommendations/pipeline",
            preferences=preferences.model_dump(),
            candidate_count=0,
            returned_count=0,
        )
        return PipelineResponse(summary="No matches found.", recommendations=[])

    client = GroqLLMClient(config)
    llm_result = recommend_with_groq(
        client=client,
        preferences=preferences,
        candidates=candidate_pool,
        limit=preferences.limit,
    )

    # Join LLM-ranked ids back to restaurant objects.
    by_id: dict[int, Restaurant] = {r.id: r for r in candidate_pool}
    joined: list[PipelineRecommendation] = []
    for item in llm_result.recommendations:
        r = by_id.get(item.id)
        if not r:
            continue
        joined.append(
            PipelineRecommendation(
                id=r.id,
                name=r.name,
                location=r.location,
                cuisines=r.cuisines,
                price_range=r.price_range,
                rating=r.rating,
                score=r.score,
                reason=item.reason,
            )
        )

    log_recommendation_event(
        engine=engine,
        endpoint="/recommendations/pipeline",
        preferences=preferences.model_dump(),
        candidate_count=len(candidate_pool),
        returned_count=len(joined),
    )

    return PipelineResponse(summary=llm_result.summary, recommendations=joined)

