"""Response models for API endpoints."""

import uuid
from datetime import UTC, datetime
from typing import Any

from coaching.src.core.constants import ConversationPhase, ConversationStatus
from pydantic import BaseModel, Field


def _default_notification_preferences() -> dict[str, bool]:
    return {}


def _default_metadata() -> dict[str, str]:
    return {}


class ConversationResponse(BaseModel):
    """Response for conversation initiation."""

    conversation_id: str
    status: ConversationStatus
    current_question: str
    progress: float = Field(ge=0.0, le=1.0)
    phase: ConversationPhase | None = None
    session_data: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    """Response for a message in conversation."""

    ai_response: str
    follow_up_question: str | None = None
    insights: list[str] | None = None
    progress: float = Field(ge=0.0, le=1.0)
    phase: ConversationPhase | None = None
    is_complete: bool = False
    next_steps: list[str] | None = None
    identified_values: list[str] | None = None


class ConversationSummary(BaseModel):
    """Summary of a conversation."""

    conversation_id: str
    topic: str
    status: ConversationStatus
    progress: float
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""

    conversations: list[ConversationSummary]
    total: int
    page: int = 1


class BusinessContext(BaseModel):
    """Business context data structure."""

    industry: str | None = Field(default=None, description="Business industry")
    company_size: str | None = Field(default=None, description="Company size")
    goals: list[str] | None = Field(default=None, description="Business goals")
    challenges: list[str] | None = Field(default=None, description="Business challenges")
    values: list[str] | None = Field(default=None, description="Business values")
    metrics: list[str] | None = Field(default=None, description="Key metrics")


class UserPreferences(BaseModel):
    """User preferences data structure."""

    communication_style: str | None = Field(
        default=None, description="Preferred communication style"
    )
    coaching_frequency: str | None = Field(default=None, description="Preferred coaching frequency")
    focus_areas: list[str] | None = Field(default=None, description="Areas of focus")
    notification_preferences: dict[str, bool] | None = Field(
        default_factory=_default_notification_preferences, description="Notification settings"
    )


class SessionContextData(BaseModel):
    """Session context data structure."""

    conversation_id: str | None = Field(default=None, description="Conversation identifier")
    status: str = Field(default="active", description="Current conversation status")
    context: dict[str, str] = Field(default_factory=dict, description="Additional context")
    business_context: BusinessContext = Field(
        default_factory=BusinessContext, description="Business context"
    )
    user_preferences: UserPreferences = Field(
        default_factory=UserPreferences, description="User preferences"
    )


class ConversationContextData(BaseModel):
    """Conversation context data structure."""

    session_id: str = Field(description="Session identifier")
    tenant_id: str = Field(description="Tenant identifier")
    business_context: BusinessContext = Field(description="Business context")
    user_preferences: UserPreferences = Field(description="User preferences")
    language: str = Field(default="en", description="Language code")


class CacheSessionData(BaseModel):
    """Cache session data structure."""

    status: str = Field(default="active", description="Current status")
    context: dict[str, str] = Field(default_factory=dict, description="Context data")
    message_count: int = Field(description="Number of messages")
    template_version: str = Field(description="Template version")
    session_id: str = Field(description="Session identifier")
    business_context: BusinessContext = Field(description="Business context")


class AIResponseData(BaseModel):
    """AI response data structure."""

    response: str = Field(description="AI response text")
    confidence: float | None = Field(default=None, description="Response confidence")
    metadata: dict[str, str] | None = Field(
        default_factory=_default_metadata, description="Response metadata"
    )
    suggested_actions: list[str] | None = Field(default=None, description="Suggested next actions")


class SessionOutcomesData(BaseModel):
    """Session outcomes data structure."""

    insights: list[str] = Field(default_factory=list, description="Generated insights")
    action_items: list[str] = Field(default_factory=list, description="Action items")
    key_decisions: list[str] = Field(default_factory=list, description="Key decisions made")
    next_steps: list[str] = Field(default_factory=list, description="Next steps")
    metrics: dict[str, float] = Field(default_factory=dict, description="Session metrics")
    page_size: int = 20


class ConversationDetailResponse(BaseModel):
    """Detailed conversation response."""

    conversation_id: str
    user_id: str
    topic: str
    status: ConversationStatus
    messages: list[dict[str, Any]]
    context: dict[str, Any]
    progress: float
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class InsightMetadata(BaseModel):
    """Metadata for an insight."""

    conversation_count: int = Field(
        ge=0, description="Number of conversations contributing to this insight"
    )
    business_impact: str = Field(description="Business impact level (low, medium, high)")
    effort_required: str = Field(description="Effort required to implement (low, medium, high)")


class InsightResponse(BaseModel):
    """Response model for coaching insights."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique insight identifier"
    )
    title: str = Field(description="Insight title")
    description: str = Field(description="Detailed insight description")
    category: str = Field(description="Insight category")
    priority: str = Field(description="Priority level")
    kiss_category: str | None = Field(
        default=None, description="KISS framework category (keep, improve, start, stop)"
    )
    alignment_impact: str | None = Field(
        default=None, description="How this affects purpose/values alignment and business outcomes"
    )
    status: str = Field(default="active", description="Current status")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Last update timestamp"
    )
    metadata: InsightMetadata = Field(description="Additional insight metadata")


class InsightLLMResponse(BaseModel):
    """LLM-generated insight data (ephemeral, not persisted).

    The Python AI service generates insights and returns them to the frontend.
    The .NET backend handles persistence and adds system fields (id, timestamps, status).
    """

    title: str = Field(description="Insight title")
    description: str = Field(description="Detailed insight description")
    category: str = Field(
        description=(
            "Insight category: strategy, operations, finance, marketing, leadership, "
            "technology"
        )
    )
    priority: str = Field(description="Priority level: critical, high, medium, low")
    kiss_category: str = Field(
        description="KISS framework category: keep, improve, start, stop"
    )
    alignment_impact: str = Field(
        description="How this affects purpose/values alignment and business outcomes"
    )
    business_impact: str = Field(description="Business impact level: low, medium, high")
    effort_required: str = Field(
        description="Effort required to implement: low, medium, high"
    )


class InsightsGenerationResponse(BaseModel):
    """Response for insights generation - LLM returns a list of insights.

    Used by the insights_generation topic where the LLM generates multiple insights
    in a single response. System fields (id, status, timestamps) are added by backend.
    """

    insights: list[InsightLLMResponse] = Field(
        description="List of generated insights (typically 5-10)",
        min_length=1,
    )


class InsightActionResponse(BaseModel):
    """Response for insight actions (dismiss, acknowledge)."""

    insight_id: str = Field(description="Insight identifier")
    status: str = Field(description="New status after action")


class RecentActivity(BaseModel):
    """Recent activity for insights."""

    insight_id: str = Field(description="Insight identifier")
    action: str = Field(description="Action performed")
    timestamp: datetime = Field(description="When action occurred")


class InsightsSummaryResponse(BaseModel):
    """Summary response for insights overview."""

    total_insights: int = Field(ge=0, description="Total number of insights")
    by_category: dict[str, int] = Field(description="Count by category")
    by_priority: dict[str, int] = Field(description="Count by priority")
    by_status: dict[str, int] = Field(description="Count by status")
    recent_activity: list[RecentActivity] = Field(description="Recent insight activities")


class OnboardingSuggestionResponse(BaseModel):
    """Response for onboarding suggestions."""

    suggestion: str = Field(description="Generated suggestion for onboarding")


class ProductInfo(BaseModel):
    """Information about a product/service."""

    id: str = Field(description="Product identifier")
    name: str = Field(description="Product name")
    problem: str = Field(description="Problem the product solves")


class WebsiteAnalysisResponse(BaseModel):
    """Response for website analysis results."""

    domain: str = Field(description="Domain name analyzed")
    last_analyzed: datetime | None = Field(None, description="Last analysis timestamp")
    analysis_status: str = Field(description="Status of analysis")
    insights: list[str] = Field(default_factory=list, description="Business insights")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations")


class BulkScanResult(BaseModel):
    """Result for a single website in bulk scan."""

    url: str = Field(description="Website URL")
    status: str = Field(description="Scan status")
    data: dict[str, Any] | None = Field(None, description="Analysis data")


class BusinessDataSummaryResponse(BaseModel):
    """Response for business data summary."""

    tenant_id: str = Field(description="Tenant identifier")
    business_data: dict[str, Any] = Field(description="Business data summary")


class ConversationActionResponse(BaseModel):
    """Response for conversation actions (complete, pause, delete)."""

    message: str = Field(description="Action result message")
    result: dict[str, Any] | None = Field(None, description="Additional result data")


class HealthCheckResponse(BaseModel):
    """Response for basic health check."""

    status: str = Field(description="Service status")
    timestamp: str = Field(description="Check timestamp")
    stage: str = Field(description="Environment stage")


class ServiceStatus(BaseModel):
    """Status for individual services."""

    dynamodb: str = Field(description="DynamoDB status")
    s3: str = Field(description="S3 status")
    redis: str = Field(description="Redis status")
    bedrock: str = Field(description="Bedrock status")


class ReadinessCheckResponse(BaseModel):
    """Response for readiness check with all dependencies."""

    timestamp: str = Field(description="Check timestamp")
    stage: str = Field(description="Environment stage")
    status: str = Field(description="Overall status")
    services: ServiceStatus = Field(description="Individual service statuses")


class CoachingResponse(BaseModel):
    """Generic response for coaching endpoints."""

    reply: str = Field(description="Coaching response message")
    completed: bool = Field(description="Whether coaching session is complete")
    recommendations: list[str] = Field(default_factory=list, description="Coaching recommendations")
    insights: list[str] = Field(default_factory=list, description="Generated insights")
    assessments: list[str] = Field(default_factory=list, description="Assessment results")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    error_code: str | None = None
    details: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
