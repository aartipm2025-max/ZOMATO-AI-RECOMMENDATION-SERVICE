from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    insert,
)
from sqlalchemy.engine import Engine


metadata = MetaData()

recommendation_events_table = Table(
    "recommendation_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("endpoint", String, nullable=False),
    Column("preferences_json", String, nullable=False),
    Column("candidate_count", Integer, nullable=False),
    Column("returned_count", Integer, nullable=False),
)


def create_schema(engine: Engine) -> None:
    """Create Phase 4 logging tables if they do not exist."""
    metadata.create_all(engine)


def log_recommendation_event(
    *,
    engine: Engine,
    endpoint: str,
    preferences: Mapping[str, Any],
    candidate_count: int,
    returned_count: int,
) -> None:
    """
    Persist a lightweight analytics event for evaluation/feedback loops.
    """
    create_schema(engine)
    payload = {
        "created_at": datetime.now(timezone.utc),
        "endpoint": endpoint,
        "preferences_json": json.dumps(preferences, ensure_ascii=False),
        "candidate_count": int(candidate_count),
        "returned_count": int(returned_count),
    }
    with engine.begin() as conn:
        conn.execute(insert(recommendation_events_table), [payload])

