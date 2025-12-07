"""Analysis domain events.

This module contains all events related to analysis operations
(alignment scoring, strategy recommendations, etc.).
"""

from coaching.src.core.constants import AnalysisType
from coaching.src.domain.events.base_event import DomainEvent
from pydantic import Field


class AnalysisRequested(DomainEvent):  # type: ignore[misc]
    """
    Event emitted when an analysis is requested.

    Marks the start of an analysis operation (alignment, strategy, KPI, etc.).

    Attributes:
        analysis_type: Type of analysis being requested
        user_id: ID of the user requesting analysis
        tenant_id: ID of the tenant/organization
        request_context: Additional context for the analysis request
    """

    event_type: str = Field(default="AnalysisRequested", frozen=True)
    aggregate_type: str = Field(default="AnalysisRequest", frozen=True)

    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    user_id: str = Field(..., description="ID of the user")
    tenant_id: str = Field(..., description="ID of the tenant/organization")
    request_context: dict[str, str] = Field(
        default_factory=dict, description="Additional request context"
    )


class AnalysisCompleted(DomainEvent):  # type: ignore[misc]
    """
    Event emitted when an analysis successfully completes.

    Captures metrics about the analysis execution for observability.

    Attributes:
        analysis_type: Type of analysis that was completed
        user_id: ID of the user
        tenant_id: ID of the tenant/organization
        duration_ms: Duration of analysis in milliseconds
        token_count: Number of LLM tokens used
        result_summary: Brief summary of results (not full result)
        confidence_score: Confidence in analysis results (0-100)
    """

    event_type: str = Field(default="AnalysisCompleted", frozen=True)
    aggregate_type: str = Field(default="AnalysisRequest", frozen=True)

    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    user_id: str = Field(..., description="ID of the user")
    tenant_id: str = Field(..., description="ID of the tenant/organization")
    duration_ms: float = Field(..., ge=0, description="Analysis duration in milliseconds")
    token_count: int = Field(..., ge=0, description="LLM tokens used")
    result_summary: str = Field(..., description="Brief summary of results")
    confidence_score: float = Field(..., ge=0.0, le=100.0, description="Confidence in results")


class AnalysisFailed(DomainEvent):  # type: ignore[misc]
    """
    Event emitted when an analysis fails.

    Captures failure information for debugging and monitoring.

    Attributes:
        analysis_type: Type of analysis that failed
        user_id: ID of the user
        tenant_id: ID of the tenant/organization
        error_type: Type/category of the error
        error_message: Error message (sanitized, no sensitive data)
        duration_ms: Duration before failure
        retry_count: Number of retries attempted
        is_retryable: Whether the operation can be retried
    """

    event_type: str = Field(default="AnalysisFailed", frozen=True)
    aggregate_type: str = Field(default="AnalysisRequest", frozen=True)

    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    user_id: str = Field(..., description="ID of the user")
    tenant_id: str = Field(..., description="ID of the tenant/organization")
    error_type: str = Field(..., description="Type/category of error")
    error_message: str = Field(..., description="Sanitized error message")
    duration_ms: float = Field(..., ge=0, description="Duration before failure")
    retry_count: int = Field(default=0, ge=0, description="Number of retries")
    is_retryable: bool = Field(default=False, description="Whether operation can be retried")


__all__ = [
    "AnalysisCompleted",
    "AnalysisFailed",
    "AnalysisRequested",
]
