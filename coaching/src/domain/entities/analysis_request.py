"""AnalysisRequest value object.

This module defines the AnalysisRequest for requesting business analysis.
"""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.core.constants import AnalysisType
from src.core.types import AnalysisRequestId, ConversationId, UserId


class AnalysisRequest(BaseModel):
    """
    Value object representing a business analysis request.

    Captures all information needed to perform a business analysis
    including context, goals, and analysis type.

    Attributes:
        request_id: Unique identifier for this request
        conversation_id: Related conversation ID
        user_id: User requesting the analysis
        analysis_type: Type of analysis to perform
        context_data: Business context for analysis
        goals: Specific goals or questions for analysis
        created_at: When request was created
    """

    request_id: AnalysisRequestId = Field(..., description="Unique request ID")
    conversation_id: ConversationId = Field(..., description="Related conversation ID")
    user_id: UserId = Field(..., description="User ID")
    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    context_data: dict[str, Any] = Field(..., description="Business context for analysis")
    goals: list[str] = Field(default_factory=list, description="Specific goals for analysis")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Request creation time",
    )

    model_config = {"frozen": True, "extra": "forbid"}

    def has_goals(self) -> bool:
        """Check if request has specific goals."""
        return len(self.goals) > 0

    def is_alignment_analysis(self) -> bool:
        """Check if this is an alignment analysis."""
        return self.analysis_type == AnalysisType.ALIGNMENT

    def is_strategy_analysis(self) -> bool:
        """Check if this is a strategy analysis."""
        return self.analysis_type == AnalysisType.STRATEGY

    def is_swot_analysis(self) -> bool:
        """Check if this is a SWOT analysis."""
        return self.analysis_type == AnalysisType.SWOT


__all__ = ["AnalysisRequest"]
