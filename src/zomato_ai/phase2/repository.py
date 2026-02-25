from __future__ import annotations

from typing import Iterable, Mapping, Any, List

from sqlalchemy import (
    Column,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    select,
)
from sqlalchemy.engine import Engine

from zomato_ai.phase1.ingestion import DEFAULT_DB_URL


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


def create_engine_for_url(db_url: str | None = None) -> Engine:
    """
    Create a SQLAlchemy engine for the given database URL.

    Defaults to the Phase 1 SQLite database if no URL is provided.
    """
    return create_engine(db_url or DEFAULT_DB_URL, future=True)


def fetch_all_restaurants(engine: Engine) -> List[Mapping[str, Any]]:
    """Fetch all restaurants from the database as plain mapping objects."""
    stmt = select(
        restaurants_table.c.id,
        restaurants_table.c.name,
        restaurants_table.c.location,
        restaurants_table.c.cuisines,
        restaurants_table.c.price_range,
        restaurants_table.c.rating,
    )
    with engine.connect() as conn:
        result = conn.execute(stmt)
        rows = result.mappings().all()
    return list(rows)

