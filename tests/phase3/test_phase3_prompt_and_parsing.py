from zomato_ai.phase2.models import Restaurant, UserPreference
from zomato_ai.phase3.models import LLMRecommendationItem, LLMRecommendationResult
from zomato_ai.phase3.parsing import parse_llm_result
from zomato_ai.phase3.prompt_builder import build_recommendation_prompt
from zomato_ai.phase3.orchestrator import recommend_with_groq


class DummyGroqClient:
    """Dummy client that returns a fixed JSON payload without calling Groq."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:  # type: ignore[override]
        assert "STRICT JSON" in system_prompt
        assert "Candidate restaurants" in user_prompt
        return """
        {
          "summary": "Top choices based on your preferences.",
          "recommendations": [
            { "id": 1, "reason": "Great rating and matches your cuisine preferences." },
            { "id": 2, "reason": "Also a strong match with slightly lower price." }
          ]
        }
        """


def test_build_recommendation_prompt_includes_preferences_and_candidates():
    prefs = UserPreference(
        location="City Center",
        min_rating=4.0,
        max_price=1500,
        preferred_cuisines=["Italian"],
        limit=5,
    )
    candidates = [
        Restaurant(
            id=1,
            name="Resto A",
            location="City Center",
            cuisines="Italian, Pizza",
            price_range=1200,
            rating=4.5,
            score=9.0,
        ),
        Restaurant(
            id=2,
            name="Resto B",
            location="City Center",
            cuisines="Italian, Continental",
            price_range=1400,
            rating=4.2,
            score=8.4,
        ),
    ]

    system_prompt, user_prompt = build_recommendation_prompt(
        preferences=prefs,
        candidates=candidates,
        limit=prefs.limit,
    )

    assert "ONLY recommend restaurants from the candidate list" in system_prompt
    assert "location contains: City Center" in user_prompt
    assert "minimum rating: 4.0" in user_prompt
    assert "maximum price: 1500" in user_prompt
    assert "Resto A" in user_prompt
    assert "Resto B" in user_prompt


def test_parse_llm_result_and_orchestrator_with_dummy_client():
    prefs = UserPreference(
        location="City Center",
        min_rating=4.0,
        max_price=1500,
        preferred_cuisines=["Italian"],
        limit=2,
    )
    candidates = [
        Restaurant(
            id=1,
            name="Resto A",
            location="City Center",
            cuisines="Italian, Pizza",
            price_range=1200,
            rating=4.5,
            score=9.0,
        ),
        Restaurant(
            id=2,
            name="Resto B",
            location="City Center",
            cuisines="Italian, Continental",
            price_range=1400,
            rating=4.2,
            score=8.4,
        ),
    ]

    dummy_client = DummyGroqClient()

    result = recommend_with_groq(
        client=dummy_client,  # type: ignore[arg-type]
        preferences=prefs,
        candidates=candidates,
        limit=prefs.limit,
    )

    assert isinstance(result, LLMRecommendationResult)
    assert result.summary.startswith("Top choices")
    assert len(result.recommendations) == 2
    assert all(isinstance(item, LLMRecommendationItem) for item in result.recommendations)
    assert {item.id for item in result.recommendations} == {1, 2}

