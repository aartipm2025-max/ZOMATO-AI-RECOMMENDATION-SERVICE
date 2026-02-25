from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class PipelineRecommendation(BaseModel):
    id: int
    name: str
    location: Optional[str]
    cuisines: Optional[str]
    price_range: Optional[int]
    rating: Optional[float]
    score: float
    reason: str = Field(..., description="LLM explanation for why this restaurant is recommended.")


class PipelineResponse(BaseModel):
    summary: str
    recommendations: List[PipelineRecommendation]

