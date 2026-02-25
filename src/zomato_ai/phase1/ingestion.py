from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any, List
import re

from datasets import load_dataset
from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    insert,
    text,
)
from sqlalchemy.engine import Engine


DEFAULT_DB_URL = "sqlite:///./zomato_restaurants.db"
DATASET_NAME = "ManikaSaini/zomato-restaurant-recommendation"


metadata = MetaData()

restaurants_table = Table(
    "restaurants",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("location", String, nullable=True),
    Column("cuisines", String, nullable=True),
    Column("price_range", Integer, nullable=True),
    Column("rating", Float, nullable=True),
)


@dataclass
class RestaurantRecord:
    """Normalized restaurant record as stored in the database."""

    name: str
    location: str | None
    cuisines: str | None
    price_range: int | None
    rating: float | None


def create_engine_for_url(db_url: str = DEFAULT_DB_URL) -> Engine:
    """Create a SQLAlchemy engine for the given database URL."""
    return create_engine(db_url, future=True)


def create_schema(engine: Engine) -> None:
    """Create the restaurants table in the target database if it does not exist."""
    metadata.create_all(engine)


def _parse_price_to_int(value: Any) -> int | None:
    """
    Parse a price field that may contain commas, currency symbols, or text like
    '1,500', '₹1,500 for two people', etc. into an integer.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    s = str(value).strip()
    if not s:
        return None

    # Keep only digits to handle values like "1,500" or "₹1,500 for two people".
    digits = re.sub(r"[^\d]", "", s)
    if not digits:
        return None

    try:
        return int(digits)
    except ValueError:
        return None


def _parse_rating_to_float(value: Any) -> float | None:
    """
    Parse a rating field that may contain strings like '4.1', '4.1/5', or
    markers such as 'NEW' or '-' into a float.
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    s = str(value).strip()
    if not s:
        return None

    upper = s.upper()
    if upper in {"NEW", "N/A", "-", "NULL"}:
        return None

    # Handle formats like "4.1/5".
    if "/" in s:
        s = s.split("/", 1)[0].strip()

    try:
        return float(s)
    except ValueError:
        return None


def normalize_row(row: Mapping[str, Any]) -> RestaurantRecord:
    """
    Normalize a single raw dataset row into a RestaurantRecord.

    This function assumes the Hugging Face dataset provides, at minimum,
    fields for name, location, cuisines, price, and rating. Missing or
    malformed values are converted to None where appropriate.
    """
    name = str(row.get("name") or row.get("restaurant_name") or "").strip()
    if not name:
        raise ValueError("Restaurant row is missing a name")

    location = (row.get("location") or row.get("city") or row.get("address") or None)
    if isinstance(location, str):
        location = location.strip() or None

    raw_cuisines = row.get("cuisines") or row.get("cuisine")
    cuisines: str | None
    if raw_cuisines is None:
        cuisines = None
    elif isinstance(raw_cuisines, str):
        # Split and re-join to ensure consistent trimming and spacing.
        parts = [part.strip() for part in raw_cuisines.split(",") if part.strip()]
        cuisines = ", ".join(parts) or None
    elif isinstance(raw_cuisines, list):
        parts_list: list[str] = []
        for item in raw_cuisines:
            if item is None:
                continue
            for piece in str(item).split(","):
                piece = piece.strip()
                if piece:
                    parts_list.append(piece)
        # Deduplicate while preserving order.
        deduped = list(dict.fromkeys(parts_list))
        cuisines = ", ".join(deduped) or None
    else:
        cuisines = None

    price_raw = (
        row.get("price_range")
        or row.get("price")
        or row.get("approx_cost")
        or row.get("approx_cost(for two people)")
    )
    price_range = _parse_price_to_int(price_raw)

    rating_raw = row.get("rating") or row.get("aggregate_rating") or row.get("rate")
    rating = _parse_rating_to_float(rating_raw)

    return RestaurantRecord(
        name=name,
        location=location,
        cuisines=cuisines,
        price_range=price_range,
        rating=rating,
    )


def ingest_records(engine: Engine, records: Iterable[Mapping[str, Any]]) -> int:
    """
    Ingest an iterable of raw restaurant records into the database.

    Returns the number of successfully inserted rows.
    """
    create_schema(engine)

    normalized: List[dict[str, Any]] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in records:
        try:
            record = normalize_row(row)
        except ValueError:
            # Skip rows that are missing required fields such as name.
            continue

        # Deduplicate on (name, location) to avoid duplicate restaurants.
        key = (record.name.strip().lower(), (record.location or "").strip().lower())
        if key in seen_keys:
            continue
        seen_keys.add(key)

        normalized.append(
            {
                "name": record.name,
                "location": record.location,
                "cuisines": record.cuisines,
                "price_range": record.price_range,
                "rating": record.rating,
            }
        )

    if not normalized:
        return 0

    with engine.begin() as conn:
        conn.execute(insert(restaurants_table), normalized)

    return len(normalized)


def ingest_huggingface_dataset(db_url: str = DEFAULT_DB_URL) -> int:
    """
    Load the Zomato dataset from Hugging Face and ingest it into the database.

    Returns the number of inserted restaurant rows.
    """
    engine = create_engine_for_url(db_url)
    dataset = load_dataset(DATASET_NAME, split="train")
    count = ingest_records(engine, (dict(row) for row in dataset))

    # Basic sanity check query to ensure the table is readable.
    with engine.connect() as conn:
        conn.execute(text("SELECT COUNT(*) FROM restaurants"))

    return count

