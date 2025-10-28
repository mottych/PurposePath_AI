"""Strategy recommendation value object for coaching analysis."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

PriorityLevel = Literal["high", "medium", "low"]


class StrategyRecommendation(BaseModel):
    """
    Immutable value object representing a strategic recommendation.

    Attributes:
        title: Brief title of the recommendation
        description: Detailed description
        priority: Priority level (high/medium/low)
        rationale: Reasoning behind the recommendation
        expected_impact: Expected impact if implemented
    """

    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=1000)
    priority: PriorityLevel = Field(...)
    rationale: str = Field(..., min_length=10, max_length=500)
    expected_impact: str = Field(..., min_length=10, max_length=500)

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("title", "description", "rationale", "expected_impact")
    @classmethod
    def validate_not_whitespace(cls, v: str) -> str:
        """Ensure fields are not just whitespace."""
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()

    def is_high_priority(self) -> bool:
        """Check if recommendation is high priority."""
        return self.priority == "high"

    def is_medium_priority(self) -> bool:
        """Check if recommendation is medium priority."""
        return self.priority == "medium"

    def is_low_priority(self) -> bool:
        """Check if recommendation is low priority."""
        return self.priority == "low"


__all__ = ["PriorityLevel", "StrategyRecommendation"]
