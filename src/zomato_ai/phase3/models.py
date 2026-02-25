from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class LLMRecommendationItem(BaseModel):
    id: int = Field(..., description="Restaurant ID from the provided candidate list.")
    reason: str = Field(..., description="Short explanation for recommending this restaurant.")


class LLMRecommendationResult(BaseModel):
    summary: str = Field(..., description="Overall summary of the recommendations.")
    recommendations: List[LLMRecommendationItem]

