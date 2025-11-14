"""ConversationContext value object for coaching conversations.

This module defines the immutable ConversationContext that tracks the state
and progress of a coaching conversation.
"""

from typing import Any

from coaching.src.core.constants import ConversationPhase
from pydantic import BaseModel, Field, field_validator


class ConversationContext(BaseModel):
    """
    Immutable value object representing conversation context and progress.

    Tracks the current phase, collected insights, response count, and
    overall progress percentage for a coaching conversation.

    Attributes:
        current_phase: The current phase of the conversation
        insights: List of key insights gathered during the conversation
        response_count: Number of user responses received
        progress_percentage: Overall progress (0-100)
        metadata: Optional additional context information

    Example:
        >>> context = ConversationContext(
        ...     current_phase=ConversationPhase.EXPLORATION,
        ...     insights=["Values autonomy", "Seeks growth"],
        ...     response_count=5,
        ...     progress_percentage=30.0
        ... )
    """

    current_phase: ConversationPhase = Field(..., description="Current phase of the conversation")
    insights: list[str] = Field(default_factory=list, description="Key insights collected")
    response_count: int = Field(default=0, ge=0, description="Number of user responses")
    progress_percentage: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Overall progress (0-100)"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional context metadata")

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("insights")
    @classmethod
    def validate_insights_not_empty_strings(cls, v: list[str]) -> list[str]:
        """Ensure insights are not empty strings."""
        if any(not insight.strip() for insight in v):
            raise ValueError("Insights cannot contain empty strings")
        return [insight.strip() for insight in v]

    def has_insights(self) -> bool:
        """
        Check if any insights have been collected.

        Returns:
            bool: True if insights list is not empty
        """
        return len(self.insights) > 0

    def get_insight_count(self) -> int:
        """
        Get the number of insights collected.

        Returns:
            int: Number of insights
        """
        return len(self.insights)

    def is_in_phase(self, phase: ConversationPhase) -> bool:
        """
        Check if conversation is in a specific phase.

        Args:
            phase: The phase to check

        Returns:
            bool: True if current phase matches
        """
        return self.current_phase == phase

    def is_introduction_phase(self) -> bool:
        """Check if conversation is in introduction phase."""
        return self.current_phase == ConversationPhase.INTRODUCTION

    def is_exploration_phase(self) -> bool:
        """Check if conversation is in exploration phase."""
        return self.current_phase == ConversationPhase.EXPLORATION

    def is_deepening_phase(self) -> bool:
        """Check if conversation is in deepening phase."""
        return self.current_phase == ConversationPhase.DEEPENING

    def is_synthesis_phase(self) -> bool:
        """Check if conversation is in synthesis phase."""
        return self.current_phase == ConversationPhase.SYNTHESIS

    def is_validation_phase(self) -> bool:
        """Check if conversation is in validation phase."""
        return self.current_phase == ConversationPhase.VALIDATION

    def is_completion_phase(self) -> bool:
        """Check if conversation is in completion phase."""
        return self.current_phase == ConversationPhase.COMPLETION

    def has_sufficient_responses(self, minimum: int) -> bool:
        """
        Check if conversation has minimum number of responses.

        Args:
            minimum: Minimum required responses

        Returns:
            bool: True if response_count >= minimum
        """
        return self.response_count >= minimum

    def is_complete(self) -> bool:
        """
        Check if conversation progress is complete (100%).

        Returns:
            bool: True if progress is 100%
        """
        return self.progress_percentage >= 100.0


__all__ = ["ConversationContext"]
