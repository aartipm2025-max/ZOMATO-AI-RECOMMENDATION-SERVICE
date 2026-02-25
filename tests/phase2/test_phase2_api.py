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
            "name": "Budget Bites",
            "location": "City Center",
            "cuisines": "Italian, Pizza",
            "approx_cost(for two people)": "500",
            "rate": "3.8/5",
        },
        {
            "name": "Fine Dine",
            "location": "City Center",
            "cuisines": "Italian, Continental",
            "approx_cost(for two people)": "2,000",
            "rate": "4.6/5",
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


def test_recommendations_endpoint_filters_by_location_cuisine_and_rating():
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)

    app = create_app(engine=engine)
    client = TestClient(app)

    response = client.post(
        "/recommendations",
        json={
            "location": "City Center",
            "min_rating": 4.0,
            "preferred_cuisines": ["Italian"],
            "limit": 5,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert "recommendations" in body

    recs = body["recommendations"]
    # Should include City Center Italian places with rating >= 4.0
    assert len(recs) == 1
    assert recs[0]["name"] == "Fine Dine"
    assert recs[0]["location"] == "City Center"
    assert "Italian" in recs[0]["cuisines"]


def test_recommendations_endpoint_applies_price_filters():
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)

    app = create_app(engine=engine)
    client = TestClient(app)

    # Restrict max_price so that the expensive restaurant is filtered out.
    response = client.post(
        "/recommendations",
        json={
            "location": "City Center",
            "preferred_cuisines": ["Italian"],
            "max_price": 1000,
            "limit": 5,
        },
    )

    assert response.status_code == 200
    recs = response.json()["recommendations"]

    # Only the budget option should remain under this price cap.
    assert len(recs) == 1
    assert recs[0]["name"] == "Budget Bites"


def test_locations_endpoint_returns_sorted_unique_locations():
    engine = _make_in_memory_engine()
    _seed_sample_data(engine)

    app = create_app(engine=engine)
    client = TestClient(app)

    resp = client.get("/locations")
    assert resp.status_code == 200

    locations = resp.json()
    assert isinstance(locations, list)

    # Our seed data has exactly two distinct locations.
    assert set(locations) == {"City Center", "Old Town"}

    # Must be sorted case-insensitively.
    assert locations == sorted(locations, key=str.casefold)

    # No duplicates.
    assert len(locations) == len(set(locations))

