"""Response models for API endpoints."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from coaching.src.core.constants import ConversationPhase, ConversationStatus
from pydantic import BaseModel, Field


class ConversationResponse(BaseModel):
    """Response for conversation initiation."""

    conversation_id: str
    status: ConversationStatus
    current_question: str
    progress: float = Field(ge=0.0, le=1.0)
    phase: ConversationPhase
    session_data: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    """Response for a message in conversation."""

    ai_response: str
    follow_up_question: Optional[str] = None
    insights: Optional[List[str]] = None
    progress: float = Field(ge=0.0, le=1.0)
    is_complete: bool = False
    next_steps: Optional[List[str]] = None
    identified_values: Optional[List[str]] = None
    phase: ConversationPhase


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

    conversations: List[ConversationSummary]
    total: int
    page: int = 1


class BusinessContext(BaseModel):
    """Business context data structure."""

    industry: Optional[str] = Field(default=None, description="Business industry")
    company_size: Optional[str] = Field(default=None, description="Company size")
    goals: Optional[List[str]] = Field(default=None, description="Business goals")
    challenges: Optional[List[str]] = Field(default=None, description="Business challenges")
    values: Optional[List[str]] = Field(default=None, description="Business values")
    metrics: Optional[List[str]] = Field(default=None, description="Key metrics")


class UserPreferences(BaseModel):
    """User preferences data structure."""

    communication_style: Optional[str] = Field(
        default=None, description="Preferred communication style"
    )
    coaching_frequency: Optional[str] = Field(
        default=None, description="Preferred coaching frequency"
    )
    focus_areas: Optional[List[str]] = Field(default=None, description="Areas of focus")
    notification_preferences: Optional[Dict[str, bool]] = Field(
        default_factory=dict, description="Notification settings"
    )


class SessionContextData(BaseModel):
    """Session context data structure."""

    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")
    phase: str = Field(description="Current conversation phase")
    context: Dict[str, str] = Field(default_factory=dict, description="Additional context")
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

    phase: str = Field(description="Current phase")
    context: Dict[str, str] = Field(default_factory=dict, description="Context data")
    message_count: int = Field(description="Number of messages")
    template_version: str = Field(description="Template version")
    session_id: str = Field(description="Session identifier")
    business_context: BusinessContext = Field(description="Business context")


class AIResponseData(BaseModel):
    """AI response data structure."""

    response: str = Field(description="AI response text")
    confidence: Optional[float] = Field(default=None, description="Response confidence")
    metadata: Optional[Dict[str, str]] = Field(
        default_factory=dict, description="Response metadata"
    )
    suggested_actions: Optional[List[str]] = Field(
        default=None, description="Suggested next actions"
    )


class SessionOutcomesData(BaseModel):
    """Session outcomes data structure."""

    insights: List[str] = Field(default_factory=list, description="Generated insights")
    action_items: List[str] = Field(default_factory=list, description="Action items")
    key_decisions: List[str] = Field(default_factory=list, description="Key decisions made")
    next_steps: List[str] = Field(default_factory=list, description="Next steps")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Session metrics")
    page_size: int = 20


class ConversationDetailResponse(BaseModel):
    """Detailed conversation response."""

    conversation_id: str
    user_id: str
    topic: str
    status: ConversationStatus
    messages: List[Dict[str, Any]]
    context: Dict[str, Any]
    progress: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class InsightMetadata(BaseModel):
    """Metadata for an insight."""

    conversation_count: int = Field(
        ge=0, description="Number of conversations contributing to this insight"
    )
    business_impact: str = Field(description="Business impact level (low, medium, high)")
    effort_required: str = Field(description="Effort required to implement (low, medium, high)")


class InsightResponse(BaseModel):
    """Response model for coaching insights."""

    id: str = Field(description="Unique insight identifier")
    title: str = Field(description="Insight title")
    description: str = Field(description="Detailed insight description")
    category: str = Field(description="Insight category")
    priority: str = Field(description="Priority level")
    status: str = Field(description="Current status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    metadata: InsightMetadata = Field(description="Additional insight metadata")


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
    by_category: Dict[str, int] = Field(description="Count by category")
    by_priority: Dict[str, int] = Field(description="Count by priority")
    by_status: Dict[str, int] = Field(description="Count by status")
    recent_activity: List[RecentActivity] = Field(description="Recent insight activities")


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
    last_analyzed: Optional[datetime] = Field(None, description="Last analysis timestamp")
    analysis_status: str = Field(description="Status of analysis")
    insights: List[str] = Field(default_factory=list, description="Business insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


class BulkScanResult(BaseModel):
    """Result for a single website in bulk scan."""

    url: str = Field(description="Website URL")
    status: str = Field(description="Scan status")
    data: Optional[Dict[str, Any]] = Field(None, description="Analysis data")


class BusinessDataSummaryResponse(BaseModel):
    """Response for business data summary."""

    tenant_id: str = Field(description="Tenant identifier")
    business_data: Dict[str, Any] = Field(description="Business data summary")


class ConversationActionResponse(BaseModel):
    """Response for conversation actions (complete, pause, delete)."""

    message: str = Field(description="Action result message")
    result: Optional[Dict[str, Any]] = Field(None, description="Additional result data")


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
    recommendations: List[str] = Field(default_factory=list, description="Coaching recommendations")
    insights: List[str] = Field(default_factory=list, description="Generated insights")
    assessments: List[str] = Field(default_factory=list, description="Assessment results")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
