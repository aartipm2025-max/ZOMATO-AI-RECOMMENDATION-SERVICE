from typing import Any, Dict, List

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from zomato_ai.phase1.ingestion import create_schema, ingest_records


def _make_in_memory_engine():
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def test_ingest_records_creates_schema_and_inserts_rows():
    engine = _make_in_memory_engine()

    # Schema should be created automatically by ingest_records
    sample_records: List[Dict[str, Any]] = [
        {
            "name": "Test Restaurant A",
            "location": "City Center",
            "cuisines": "Italian, Pizza",
            "price_range": 2,
            "rating": 4.5,
        },
        {
            "name": "Test Restaurant B",
            "location": "Old Town",
            "cuisines": ["Indian", "Curry"],
            "price_range": "3",
            "rating": "4.0",
        },
        {
            # This record is missing a name and should be skipped
            "location": "Nowhere",
            "cuisines": "Unknown",
        },
    ]

    inserted_count = ingest_records(engine, sample_records)
    assert inserted_count == 2

    # Verify that the table exists and has the expected number of rows.
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name, location, cuisines, price_range, rating FROM restaurants"))
        rows = result.fetchall()

    assert len(rows) == 2

    # Basic content checks
    names = {row[0] for row in rows}
    assert "Test Restaurant A" in names
    assert "Test Restaurant B" in names

def test_create_schema_is_idempotent():
    engine = _make_in_memory_engine()

    # Calling create_schema multiple times should not raise errors.
    create_schema(engine)
    create_schema(engine)

    # Confirm table exists via sqlite_master query.
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='restaurants';")
        ).fetchone()
    assert row is not None
    assert row[0] == "restaurants"


def test_ingest_records_cleans_price_rating_cuisines_and_deduplicates():
    engine = _make_in_memory_engine()

    sample_records: List[Dict[str, Any]] = [
        {
            "name": "Duplicate Restaurant",
            "location": "City X",
            "cuisines": "Italian,  Pizza ",
            "approx_cost(for two people)": "1,500",
            "rate": "4.1/5",
        },
        {
            # Same name and location should be treated as duplicate and skipped.
            "name": "Duplicate Restaurant",
            "location": "City X",
            "cuisines": ["Italian", "Pizza"],
            "approx_cost(for two people)": "2,000",
            "rate": "NEW",
        },
        {
            "name": "Another Restaurant",
            "location": "City Y",
            "cuisines": ["North Indian ", "   Biryani"],
            "approx_cost(for two people)": "₹800 for two people",
            "rate": "-",
        },
    ]

    inserted_count = ingest_records(engine, sample_records)
    # First and third records should be inserted; the duplicate second one skipped.
    assert inserted_count == 2

    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name, location, cuisines, price_range, rating FROM restaurants ORDER BY name")
        )
        rows = result.fetchall()

    assert len(rows) == 2

    # Validate cleaning for "Duplicate Restaurant"
    dup = next(row for row in rows if row[0] == "Duplicate Restaurant")
    assert dup[1] == "City X"
    # Cuisines should be trimmed and consistently spaced.
    assert dup[2] == "Italian, Pizza"
    # Price cleaned from "1,500" to 1500.
    assert dup[3] == 1500
    # Rating cleaned from "4.1/5" to 4.1.
    assert dup[4] == 4.1

    # Validate cleaning for "Another Restaurant"
    other = next(row for row in rows if row[0] == "Another Restaurant")
    assert other[1] == "City Y"
    # Cuisines should be trimmed and combined without extra spaces.
    assert other[2] == "North Indian, Biryani"
    # Price cleaned from "₹800 for two people" to 800.
    assert other[3] == 800
    # Rating "-" should become NULL/None.
    assert other[4] is None

