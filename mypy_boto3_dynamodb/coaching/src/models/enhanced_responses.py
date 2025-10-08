"""Enhanced coaching models with proper Pydantic structures."""

from datetime import datetime
from typing import Any

from coaching.src.core.constants import ConversationPhase, ConversationStatus
from pydantic import BaseModel, Field
from shared.models.base import BaseResponseModel


# Proper message model instead of Dict[str, Any]
class ConversationMessage(BaseModel):
    """Individual message in a conversation."""

    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional message metadata"
    )
    message_id: str | None = Field(None, description="Unique message identifier")


# Proper context model instead of Dict[str, Any]
class ConversationContext(BaseModel):
    """Conversation context data."""

    user_background: dict[str, Any] = Field(
        default_factory=dict, description="User background information"
    )
    session_preferences: dict[str, Any] = Field(
        default_factory=dict, description="Session preferences"
    )
    previous_insights: list[str] = Field(
        default_factory=list, description="Previously identified insights"
    )
    coaching_style: str | None = Field(None, description="Preferred coaching style")
    language: str = Field(default="en", description="Conversation language")
    timezone: str = Field(default="UTC", description="User timezone")


# Session data model instead of Dict[str, Any]
class SessionData(BaseModel):
    """Session-specific data."""

    ai_model: str | None = Field(None, description="AI model used")
    token_count: int | None = Field(None, description="Total tokens used")
    conversation_flow: list[str] = Field(
        default_factory=list, description="Flow of conversation topics"
    )
    key_revelations: list[str] = Field(default_factory=list, description="Key user revelations")
    coaching_techniques_used: list[str] = Field(
        default_factory=list, description="Coaching techniques applied"
    )


# Enhanced response models with proper Pydantic structures
class ConversationResponse(BaseResponseModel):  # type: ignore[misc]
    """Response for conversation initiation."""

    conversation_id: str = Field(..., description="Unique conversation identifier")
    status: ConversationStatus = Field(..., description="Current conversation status")
    current_question: str = Field(..., description="Current question being asked")
    progress: float = Field(..., ge=0.0, le=1.0, description="Conversation progress (0-1)")
    phase: ConversationPhase = Field(..., description="Current conversation phase")
    session_data: SessionData | None = Field(None, description="Session-specific data")


class MessageResponse(BaseResponseModel):  # type: ignore[misc]
    """Response for a message in conversation."""

    ai_response: str = Field(..., description="AI coach response")
    follow_up_question: str | None = Field(None, description="Follow-up question")
    insights: list[str] | None = Field(None, description="Generated insights")
    progress: float = Field(..., ge=0.0, le=1.0, description="Updated progress")
    is_complete: bool = Field(default=False, description="Whether conversation is complete")
    next_steps: list[str] | None = Field(None, description="Suggested next steps")
    identified_values: list[str] | None = Field(None, description="Newly identified values")
    phase: ConversationPhase = Field(..., description="Current conversation phase")


class ConversationSummary(BaseResponseModel):  # type: ignore[misc]
    """Summary of a conversation."""

    conversation_id: str = Field(..., description="Conversation identifier")
    topic: str = Field(..., description="Conversation topic")
    status: ConversationStatus = Field(..., description="Current status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    message_count: int = Field(..., ge=0, description="Number of messages in conversation")


class ConversationListResponse(BaseResponseModel):  # type: ignore[misc]
    """Response for listing conversations."""

    conversations: list[ConversationSummary] = Field(
        ..., description="List of conversation summaries"
    )
    total: int = Field(..., ge=0, description="Total number of conversations")
    page: int = Field(default=1, ge=1, description="Current page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class ConversationDetailResponse(BaseResponseModel):  # type: ignore[misc]
    """Detailed conversation response with proper message structure."""

    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    topic: str = Field(..., description="Conversation topic")
    status: ConversationStatus = Field(..., description="Current status")
    messages: list[ConversationMessage] = Field(..., description="Conversation messages")
    context: ConversationContext = Field(..., description="Conversation context")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress percentage")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")


class ErrorResponse(BaseResponseModel):  # type: ignore[misc]
    """Error response model."""

    error: str = Field(..., description="Error message")
    error_code: str | None = Field(None, description="Specific error code")
    details: dict[str, Any] | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")


# Additional coaching-specific models
class InsightResponse(BaseResponseModel):  # type: ignore[misc]
    """Response for generated insights."""

    insight_id: str = Field(..., description="Unique insight identifier")
    content: str = Field(..., description="Insight content")
    category: str = Field(..., description="Insight category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    generated_at: datetime = Field(..., description="Generation timestamp")


class SuggestionResponse(BaseResponseModel):  # type: ignore[misc]
    """Response for coaching suggestions."""

    suggestion_id: str = Field(..., description="Unique suggestion identifier")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Detailed description")
    priority: str = Field(..., description="Suggestion priority")
    category: str = Field(..., description="Suggestion category")
    estimated_time: int | None = Field(None, description="Estimated time to complete (minutes)")


class CoachingMetrics(BaseResponseModel):  # type: ignore[misc]
    """Coaching session metrics."""

    total_conversations: int = Field(..., ge=0, description="Total conversations")
    completed_conversations: int = Field(..., ge=0, description="Completed conversations")
    average_session_length: float | None = Field(
        None, description="Average session length (minutes)"
    )
    completion_rate: float = Field(..., ge=0.0, le=1.0, description="Completion rate percentage")
    user_satisfaction: float | None = Field(
        None, ge=0.0, le=5.0, description="Average user satisfaction (1-5)"
    )
    insights_generated: int = Field(..., ge=0, description="Total insights generated")


class WebsiteResponse(BaseResponseModel):  # type: ignore[misc]
    """Response for website coaching integration."""

    widget_config: dict[str, Any] = Field(..., description="Widget configuration")
    api_endpoints: dict[str, str] = Field(..., description="Available API endpoints")
    authentication_info: dict[str, str] = Field(..., description="Authentication information")
