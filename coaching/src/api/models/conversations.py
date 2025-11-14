"""API models for conversation endpoints.

This module provides Pydantic models for conversation-related API requests and responses.
These models handle API-layer concerns (serialization, validation, documentation).
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.core.constants import CoachingTopic, ConversationStatus

# Request Models


class InitiateConversationRequest(BaseModel):
    """Request to initiate a new coaching conversation.

    This model validates and structures the initial conversation request.
    Note: user_id and tenant_id are extracted from JWT token, not from request body.
    """

    topic: CoachingTopic = Field(
        ...,
        description="Coaching topic to focus on",
        examples=[CoachingTopic.CORE_VALUES],
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for the conversation",
        examples=[{"prior_sessions": 3, "last_topic": "purpose"}],
    )
    language: str = Field(
        default="en",
        max_length=5,
        description="Language code for the conversation",
        examples=["en", "es", "fr"],
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        return v.lower().strip()


class MessageRequest(BaseModel):
    """Request to send a message in an existing conversation.

    This model validates user messages sent during a conversation.
    """

    user_message: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User's message content",
        examples=["I value honesty and transparency"],
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata for the message",
        examples=[{"source": "web_app", "session_duration": 120}],
    )

    @field_validator("user_message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message content."""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace")
        return v.strip()


class PauseConversationRequest(BaseModel):
    """Request to pause an active conversation.

    This model captures the reason for pausing, useful for analytics.
    """

    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Optional reason for pausing",
        examples=["Need to gather more information", "Break requested by user"],
    )


class CompleteConversationRequest(BaseModel):
    """Request to mark a conversation as complete.

    This model captures user feedback at conversation end.
    """

    feedback: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional user feedback",
        examples=["Very helpful session, gained clarity on my values"],
    )
    rating: int | None = Field(
        default=None,
        ge=1,
        le=5,
        description="Optional rating (1-5 stars)",
        examples=[5],
    )


# Response Models


class ConversationResponse(BaseModel):
    """Response for conversation initiation.

    This model provides the initial state and first question to the user.
    """

    conversation_id: str = Field(
        ...,
        description="Unique identifier for the conversation",
        examples=["conv_abc123"],
    )
    user_id: str = Field(
        ...,
        description="User identifier",
        examples=["user_123"],
    )
    tenant_id: str = Field(
        ...,
        description="Tenant identifier",
        examples=["tenant_456"],
    )
    topic: CoachingTopic = Field(
        ...,
        description="Coaching topic",
    )
    status: ConversationStatus = Field(
        ...,
        description="Current conversation status",
    )
    initial_message: str = Field(
        ...,
        description="Initial coach message/question",
        examples=["Welcome! Let's explore your core values together. What matters most to you?"],
    )
    progress: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Conversation progress (0.0-1.0)",
        examples=[0.1],
    )
    created_at: datetime = Field(
        ...,
        description="Conversation creation timestamp",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "conversation_id": "conv_abc123",
                "user_id": "user_123",
                "tenant_id": "tenant_456",
                "topic": "core_values",
                "status": "active",
                "current_phase": "introduction",
                "initial_message": "Welcome! Let's explore your core values.",
                "progress": 0.1,
                "created_at": "2025-10-10T21:00:00Z",
            }
        }
    }


class MessageResponse(BaseModel):
    """Response for a message in an ongoing conversation.

    This model provides the AI's response and conversation state updates.
    """

    conversation_id: str = Field(
        ...,
        description="Conversation identifier",
    )
    ai_response: str = Field(
        ...,
        description="AI coach's response",
        examples=["That's wonderful! Honesty is a powerful core value."],
    )
    follow_up_question: str | None = Field(
        default=None,
        description="Optional follow-up question",
        examples=["How does honesty show up in your daily work?"],
    )
    progress: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Conversation progress",
        examples=[0.3],
    )
    is_complete: bool = Field(
        ...,
        description="Whether conversation is complete",
        examples=[False],
    )
    insights: list[str] = Field(
        default_factory=list,
        description="Insights extracted from this exchange",
        examples=[["User values honesty", "Looking for authenticity in work"]],
    )
    identified_values: list[str] = Field(
        default_factory=list,
        description="Core values identified",
        examples=[["Honesty", "Transparency", "Integrity"]],
    )
    next_steps: list[str] | None = Field(
        default=None,
        description="Suggested next steps (if conversation complete)",
        examples=[["Reflect on how these values align with your goals"]],
    )


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views.

    This model provides essential conversation information for overview/list endpoints.
    """

    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    status: ConversationStatus = Field(..., description="Conversation status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress")
    message_count: int = Field(..., ge=0, description="Number of messages")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")


class ConversationListResponse(BaseModel):
    """Response for listing conversations.

    This model provides paginated conversation lists.
    """

    conversations: list[ConversationSummary] = Field(
        ...,
        description="List of conversation summaries",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of conversations",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Current page number",
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    )
    has_more: bool = Field(
        ...,
        description="Whether there are more pages",
    )


class ConversationDetailResponse(BaseModel):
    """Detailed response for a specific conversation.

    This model provides complete conversation details including message history.
    """

    conversation_id: str = Field(..., description="Conversation identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    status: ConversationStatus = Field(..., description="Conversation status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress")
    messages: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Conversation messages",
    )
    insights: list[str] = Field(
        default_factory=list,
        description="Accumulated insights",
    )
    identified_values: list[str] = Field(
        default_factory=list,
        description="Identified core values",
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


__all__ = [
    "CompleteConversationRequest",
    "ConversationDetailResponse",
    "ConversationListResponse",
    # Responses
    "ConversationResponse",
    "ConversationSummary",
    # Requests
    "InitiateConversationRequest",
    "MessageRequest",
    "MessageResponse",
    "PauseConversationRequest",
]
