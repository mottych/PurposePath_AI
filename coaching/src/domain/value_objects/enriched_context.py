"""Enriched context value objects for business coaching."""

from typing import Any

from pydantic import BaseModel, Field


class BusinessFoundation(BaseModel):
    """
    Business foundation information.

    Attributes:
        purpose: Company purpose statement
        core_values: List of core values
        mission: Mission statement
        vision: Vision statement
    """

    purpose: str = Field(..., min_length=10)
    core_values: list[str] = Field(default=..., min_length=1)
    mission: str = Field(..., min_length=10)
    vision: str = Field(..., min_length=10)

    model_config = {"frozen": True, "extra": "forbid"}


class GoalContext(BaseModel):
    """
    Goal context information.

    Attributes:
        goal_description: Description of the goal
        target_date: Target completion date (ISO format)
        metrics: Success metrics
        stakeholders: Involved stakeholders
    """

    goal_description: str = Field(..., min_length=10)
    target_date: str = Field(...)
    metrics: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}


class EnrichedContext(BaseModel):
    """
    Complete enriched context for analysis.

    Attributes:
        business_foundation: Core business information
        goal_context: Goal-related context (optional)
        additional_data: Any additional context data
    """

    business_foundation: BusinessFoundation = Field(...)
    goal_context: GoalContext | None = Field(default=None)
    additional_data: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}

    def has_goal_context(self) -> bool:
        """Check if goal context is present."""
        return self.goal_context is not None


__all__ = ["BusinessFoundation", "GoalContext", "EnrichedContext"]
