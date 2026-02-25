from typing import Any, Dict, List

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
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


def _seed_data_with_duplicates(engine) -> None:
    create_schema(engine)

    # Two identical restaurants (name+location) to simulate DB duplicates.
    # Phase 2 filtering should deduplicate at query time (Phase 4 requirement).
    sample_records: List[Dict[str, Any]] = [
        {
            "name": "Dup Place",
            "location": "City Center",
            "cuisines": "Italian, Pizza",
            "approx_cost(for two people)": "1,000",
            "rate": "4.4/5",
        },
        {
            "name": "Dup Place",
            "location": "City Center",
            "cuisines": "Italian, Pizza",
            "approx_cost(for two people)": "1,000",
            "rate": "4.4/5",
        },
        {
            "name": "Solo Place",
            "location": "City Center",
            "cuisines": "Indian, Biryani",
            "approx_cost(for two people)": "800",
            "rate": "4.2/5",
        },
    ]

    # Using Phase 1 ingest_records may dedup within the batch, but we want to
    # ensure Phase 2 filtering ALSO dedups even if duplicates exist.
    # Insert duplicates explicitly by bypassing ingest_records dedup: do two calls.
    ingest_records(engine, [sample_records[0]])
    ingest_records(engine, [sample_records[1]])
    ingest_records(engine, [sample_records[2]])

    # Sanity: confirm DB has 3 rows.
    # Sanity: confirm DB has 3 rows.
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM restaurants")).scalar_one()
    assert count == 3


def test_filtering_works_and_duplicates_removed():
    engine = _make_in_memory_engine()
    _seed_data_with_duplicates(engine)

    app = create_app(engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/recommendations",
        json={
            "location": "City Center",
            "preferred_cuisines": ["Italian"],
            "min_rating": 4.0,
            "limit": 10,
        },
    )
    assert resp.status_code == 200
    recs = resp.json()["recommendations"]

    # Only one "Dup Place" should appear even though DB has two duplicate rows.
    names = [r["name"] for r in recs]
    assert names.count("Dup Place") == 1


def test_empty_result_handling_phase2_endpoint():
    engine = _make_in_memory_engine()
    create_schema(engine)

    app = create_app(engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/recommendations",
        json={"location": "Nowhere", "limit": 5},
    )
    assert resp.status_code == 200
    assert resp.json()["recommendations"] == []


def test_empty_result_handling_phase3_llm_endpoint_does_not_call_groq(monkeypatch):
    engine = _make_in_memory_engine()
    create_schema(engine)

    # Provide a dummy key so the endpoint passes config load.
    monkeypatch.setenv("GROQ_API_KEY", "dummy-key")

    # If GroqLLMClient were invoked, we'd rather fail the test.
    from zomato_ai import phase2 as phase2_pkg  # noqa: F401
    import zomato_ai.phase2.api as api_mod

    def _boom(*args, **kwargs):
        raise AssertionError("Groq client should not be called when there are no candidates")

    monkeypatch.setattr(api_mod, "GroqLLMClient", _boom)

    app = create_app(engine=engine)
    client = TestClient(app)

    resp = client.post(
        "/recommendations/llm",
        json={"location": "Nowhere", "limit": 5},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["recommendations"] == []
    assert body["summary"] == "No matches found."

