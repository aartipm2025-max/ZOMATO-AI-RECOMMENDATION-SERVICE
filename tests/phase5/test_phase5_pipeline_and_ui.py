from typing import Any, Dict, List

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from zomato_ai.phase1.ingestion import create_schema, ingest_records
from zomato_ai.phase2.api import create_app


def _make_in_memory_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _seed_sample_data(engine) -> None:
    create_schema(engine)
    sample_records: List[Dict[str, Any]] = [
        {
            "name": "Fine Dine",
            "location": "City Center",
            "cuisines": "Italian, Continental",
            "approx_cost(for two people)": "2,000",
            "rate": "4.6/5",
        },
        {
            "name": "Budget Bites",
            "location": "City Center",
            "cuisines": "Italian, Pizza",
            "approx_cost(for two people)": "500",
            "rate": "3.8/5",
        },
        {
            "name": "Spicy House",
            "location": "Old Town",
            "cuisines": "Indian, Biryani",
            "approx_cost(for two people)": "800",
            "rate": "4.2/5",
        },
    ]
    ingest_records(engine, sample_records)


def test_ui_page_served():
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)
    app = create_app(engine=engine)
    client = TestClient(app)

    resp = client.get("/")
    assert resp.status_code == 200
    assert "Restaurant Recommendations" in resp.text
    assert "/recommendations/pipeline" in resp.text


def test_pipeline_endpoint_user_filter_llm_response(monkeypatch):
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)

    # Make pipeline think a key exists.
    monkeypatch.setenv("GROQ_API_KEY", "dummy-key")

    # Patch GroqLLMClient used inside phase5.pipeline.
    import zomato_ai.phase5.pipeline as pipeline_mod

    class DummyGroqClient:
        def __init__(self, *args, **kwargs):
            pass

        def complete_json(self, *, system_prompt: str, user_prompt: str) -> str:
            # Pick Fine Dine first, then Budget Bites.
            return """
            {
              "summary": "Best matches in City Center for Italian.",
              "recommendations": [
                { "id": 1, "reason": "Highest rated Italian option." },
                { "id": 2, "reason": "Cheaper Italian alternative." }
              ]
            }
            """

    monkeypatch.setattr(pipeline_mod, "GroqLLMClient", DummyGroqClient)

    app = create_app(engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/recommendations/pipeline",
        json={
            "location": "City Center",
            "preferred_cuisines": ["Italian"],
            "limit": 2,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["summary"].startswith("Best matches")
    assert len(body["recommendations"]) == 2
    assert body["recommendations"][0]["name"] == "Fine Dine"
    assert body["recommendations"][0]["reason"] == "Highest rated Italian option."
    assert body["recommendations"][1]["name"] == "Budget Bites"

