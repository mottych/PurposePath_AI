"""Request models for API endpoints."""

from typing import Any

from coaching.src.core.constants import CoachingTopic
from pydantic import BaseModel, Field, field_validator


class InitiateConversationRequest(BaseModel):
    """Request to initiate a new conversation."""

    user_id: str = Field(..., min_length=1, max_length=128)
    topic: CoachingTopic
    context: dict[str, Any] | None = Field(default=None)
    language: str = Field(default="en", max_length=5)

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user ID format."""
        if not v.strip():
            raise ValueError("User ID cannot be empty")
        return v.strip()


class MessageRequest(BaseModel):
    """Request to send a message in a conversation."""

    user_message: str = Field(..., min_length=1, max_length=4000)
    metadata: dict[str, Any] | None = Field(default=None)

    @field_validator("user_message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message content."""
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class PauseConversationRequest(BaseModel):
    """Request to pause a conversation."""

    reason: str | None = Field(default=None, max_length=500)


class ResumeConversationRequest(BaseModel):
    """Request to resume a conversation."""

    continue_from_last: bool = Field(default=True)


class CompleteConversationRequest(BaseModel):
    """Request to mark a conversation as complete."""

    feedback: str | None = Field(default=None, max_length=1000)
    rating: int | None = Field(default=None, ge=1, le=5)


class OnboardingSuggestionRequest(BaseModel):
    """Request for generating onboarding suggestions."""

    kind: str = Field(..., description="Type of suggestion (niche, ica, valueProposition)")
    current: str | None = Field(default="", description="Current value to improve upon")

    @field_validator("kind")
    @classmethod
    def validate_kind(cls, v: str) -> str:
        """Validate suggestion kind."""
        if v not in {"niche", "ica", "valueProposition"}:
            raise ValueError("kind must be one of: niche, ica, valueProposition")
        return v


class CoachingRequest(BaseModel):
    """Generic request for coaching endpoints."""

    context: dict[str, Any] | None = Field(
        None, description="Additional context for coaching session"
    )
    focus_area: str | None = Field(None, description="Specific focus area for coaching")
    goals: list[str] | None = Field(None, description="Specific goals to work on")
