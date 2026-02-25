from __future__ import annotations

from typing import Iterable, Mapping, Any, List


def dedup_rows_by_name_location(rows: Iterable[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    """
    Deduplicate restaurant rows using (name, location) as a key.

    This protects downstream filtering/ranking even if the DB already contains
    duplicates from earlier ingestions.
    """
    seen: set[tuple[str, str]] = set()
    unique: list[Mapping[str, Any]] = []
    for row in rows:
        name = str(row.get("name") or "").strip().lower()
        location = str(row.get("location") or "").strip().lower()
        key = (name, location)
        if not name:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
    return unique

