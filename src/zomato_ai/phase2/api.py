from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from sqlalchemy.engine import Engine

from zomato_ai.phase1.ingestion import DEFAULT_DB_URL

from .filtering import filter_restaurants
from .models import RecommendationsResponse, UserPreference
from zomato_ai.phase3.groq_client import GroqLLMClient, load_groq_config_from_env
from zomato_ai.phase3.orchestrator import recommend_with_groq
from zomato_ai.phase3.models import LLMRecommendationResult
from .repository import create_engine_for_url, fetch_unique_locations
from zomato_ai.phase4.events import log_recommendation_event
from zomato_ai.phase5.pipeline import run_pipeline
from zomato_ai.phase5.models import PipelineResponse
from zomato_ai.phase5.ui import mount_ui


def create_app(db_url: str | None = None, engine: Engine | None = None) -> FastAPI:
    """
    Create and configure the FastAPI application for Phase 2.

    The database URL can be overridden (useful for tests); otherwise it falls
    back to the Phase 1 default or an environment variable.
    """
    effective_db_url = db_url or os.getenv("ZOMATO_DB_URL") or DEFAULT_DB_URL
    effective_engine = engine or create_engine_for_url(effective_db_url)

    app = FastAPI(
        title="Zomato AI Restaurant Recommendation Service - Phase 2",
        version="0.1.0",
        description="Core backend and filtering API without LLM integration.",
    )

    mount_ui(app)

    @app.post(
        "/recommendations",
        response_model=RecommendationsResponse,
        summary="Get restaurant recommendations based on user preferences (Phase 2)",
    )
    def get_recommendations(preferences: UserPreference) -> RecommendationsResponse:
        recommendations = filter_restaurants(effective_engine, preferences)
        log_recommendation_event(
            engine=effective_engine,
            endpoint="/recommendations",
            preferences=preferences.model_dump(),
            candidate_count=0,
            returned_count=len(recommendations),
        )
        return RecommendationsResponse(recommendations=recommendations)

    @app.post(
        "/recommendations/llm",
        response_model=LLMRecommendationResult,
        summary="Get LLM-enhanced recommendations (Phase 3 - Groq)",
    )
    def get_recommendations_llm(preferences: UserPreference) -> LLMRecommendationResult:
        """
        Phase 3 endpoint. Requires GROQ_API_KEY to be set.

        Note: We intentionally do not run any automated tests that call Groq
        until an API key is configured.
        """
        try:
            config = load_groq_config_from_env()
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

        # Get a slightly larger candidate pool for the LLM to choose from.
        candidates = filter_restaurants(
            effective_engine,
            preferences.model_copy(update={"limit": max(preferences.limit * 3, 15)}),
        )
        if not candidates:
            log_recommendation_event(
                engine=effective_engine,
                endpoint="/recommendations/llm",
                preferences=preferences.model_dump(),
                candidate_count=0,
                returned_count=0,
            )
            return LLMRecommendationResult(summary="No matches found.", recommendations=[])

        client = GroqLLMClient(config)
        result = recommend_with_groq(
            client=client,
            preferences=preferences,
            candidates=candidates,
            limit=preferences.limit,
        )
        log_recommendation_event(
            engine=effective_engine,
            endpoint="/recommendations/llm",
            preferences=preferences.model_dump(),
            candidate_count=len(candidates),
            returned_count=len(result.recommendations),
        )
        return result

    @app.post(
        "/recommendations/pipeline",
        response_model=PipelineResponse,
        summary="User → Filter → Groq LLM → Response (Phase 5)",
    )
    def get_recommendations_pipeline(preferences: UserPreference) -> PipelineResponse:
        try:
            return run_pipeline(engine=effective_engine, preferences=preferences)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(
        "/locations",
        response_model=list[str],
        summary="Get all unique restaurant locations from the dataset",
    )
    def get_locations() -> list[str]:
        """
        Returns a sorted list of every unique location present in the
        restaurants table.  Used by the UI to populate the location dropdown.
        """
        return fetch_unique_locations(effective_engine)

    return app


app = create_app()

