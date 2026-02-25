from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class UserPreference(BaseModel):
    """User preference input model for recommendations."""

    location: Optional[str] = Field(
        default=None, description="City or area where the user wants to eat."
    )
    min_rating: Optional[float] = Field(
        default=None, ge=0.0, le=5.0, description="Minimum acceptable restaurant rating."
    )
    min_price: Optional[int] = Field(
        default=None, ge=0, description="Minimum price filter (approx cost for two)."
    )
    max_price: Optional[int] = Field(
        default=None, ge=0, description="Maximum price filter (approx cost for two)."
    )
    preferred_cuisines: Optional[List[str]] = Field(
        default=None,
        description="List of cuisines the user prefers, e.g. ['Italian', 'Chinese'].",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of restaurants to return.",
    )


class Restaurant(BaseModel):
    """Restaurant as returned by the recommendation API (Phase 2)."""

    id: int
    name: str
    location: Optional[str]
    cuisines: Optional[str]
    price_range: Optional[int]
    rating: Optional[float]
    score: float


class RecommendationsResponse(BaseModel):
    """Response model for the /recommendations endpoint in Phase 2."""

    recommendations: List[Restaurant]

