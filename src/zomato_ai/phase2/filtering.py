from __future__ import annotations

from typing import List, Mapping, Any

from sqlalchemy.engine import Engine

from .models import Restaurant, UserPreference
from .repository import fetch_all_restaurants
from zomato_ai.phase4.dedup import dedup_rows_by_name_location


def _matches_location(row: Mapping[str, Any], location: str | None) -> bool:
    if not location:
        return True
    if not row.get("location"):
        return False
    return location.lower() in str(row["location"]).lower()


def _matches_price(row: Mapping[str, Any], min_price: int | None, max_price: int | None) -> bool:
    price = row.get("price_range")
    if price is None:
        return True
    if min_price is not None and price < min_price:
        return False
    if max_price is not None and price > max_price:
        return False
    return True


def _matches_rating(row: Mapping[str, Any], min_rating: float | None) -> bool:
    rating = row.get("rating")
    if min_rating is None or rating is None:
        return True
    return rating >= min_rating


def _matches_cuisines(row: Mapping[str, Any], preferred_cuisines: list[str] | None) -> bool:
    if not preferred_cuisines:
        return True
    cuisines_value = row.get("cuisines")
    if not cuisines_value:
        return False
    cuisines_lower = [c.strip().lower() for c in str(cuisines_value).split(",") if c.strip()]
    cuisine_set = set(cuisines_lower)
    for pref in preferred_cuisines:
        if pref.strip().lower() in cuisine_set:
            return True
    return False


def compute_score(row: Mapping[str, Any], preferences: UserPreference) -> float:
    """
    Compute a simple heuristic score for a restaurant.

    Higher rating improves the score. Prices above the user's preferred max
    price incur a small penalty. This is intentionally simple for Phase 2.
    """
    rating = row.get("rating") or 0.0
    price = row.get("price_range") or 0
    base = float(rating) * 2.0

    penalty = 0.0
    if preferences.max_price is not None and price and price > preferences.max_price:
        penalty = (price - preferences.max_price) * 0.01

    return base - penalty


def filter_restaurants(engine: Engine, preferences: UserPreference) -> List[Restaurant]:
    """
    Filter restaurants from the database according to user preferences and
    return them sorted by a heuristic score.
    """
    rows = dedup_rows_by_name_location(fetch_all_restaurants(engine))

    filtered: list[Restaurant] = []
    for row in rows:
        if not _matches_location(row, preferences.location):
            continue
        if not _matches_price(row, preferences.min_price, preferences.max_price):
            continue
        if not _matches_rating(row, preferences.min_rating):
            continue
        if not _matches_cuisines(row, preferences.preferred_cuisines or []):
            continue

        score = compute_score(row, preferences)
        filtered.append(
            Restaurant(
                id=row["id"],
                name=row["name"],
                location=row.get("location"),
                cuisines=row.get("cuisines"),
                price_range=row.get("price_range"),
                rating=row.get("rating"),
                score=score,
            )
        )

    filtered.sort(key=lambda r: r.score, reverse=True)

    return filtered[: preferences.limit]

