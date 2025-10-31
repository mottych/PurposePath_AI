"""
This module contains all events related to conversation lifecycle and interactions.
"""

from datetime import datetime

from src.core.constants import CoachingTopic, ConversationPhase, MessageRole
from src.domain.events.base_event import DomainEvent
from pydantic import Field


class ConversationInitiated(DomainEvent):
    """
    Event emitted when a new conversation is created.

    This marks the beginning of a coaching conversation session.

    Attributes:
        user_id: ID of the user starting the conversation
        tenant_id: ID of the tenant (organization)
        topic: The coaching topic for this conversation
        initial_phase: Starting phase (typically INTRODUCTION)
    """

    event_type: str = Field(default="ConversationInitiated", frozen=True)
    aggregate_type: str = Field(default="Conversation", frozen=True)

    user_id: str = Field(..., description="ID of the user")
    tenant_id: str = Field(..., description="ID of the tenant/organization")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    initial_phase: ConversationPhase = Field(..., description="Starting phase")


class MessageAdded(DomainEvent):
    """
    Event emitted when a message is added to a conversation.

    Captures both user and assistant messages for conversation flow tracking.

    Attributes:
        role: Who sent the message (user, assistant, system)
        content_length: Length of message content (not the content itself for privacy)
        message_index: Position of this message in conversation
        phase: Current conversation phase when message was added
    """

    event_type: str = Field(default="MessageAdded", frozen=True)
    aggregate_type: str = Field(default="Conversation", frozen=True)

    role: MessageRole = Field(..., description="Message sender role")
    content_length: int = Field(..., ge=0, description="Length of message content")
    message_index: int = Field(..., ge=0, description="Position in conversation")
    phase: ConversationPhase = Field(..., description="Current conversation phase")


class PhaseTransitioned(DomainEvent):
    """
    Event emitted when conversation transitions between phases.

    Phase transitions represent significant milestones in the coaching journey.

    Attributes:
        from_phase: The phase being transitioned from
        to_phase: The phase being transitioned to
        reason: Optional reason or trigger for the transition
        progress_percentage: Overall conversation progress (0-100)
    """

    event_type: str = Field(default="PhaseTransitioned", frozen=True)
    aggregate_type: str = Field(default="Conversation", frozen=True)

    from_phase: ConversationPhase = Field(..., description="Previous phase")
    to_phase: ConversationPhase = Field(..., description="New phase")
    reason: str | None = Field(default=None, description="Reason for transition")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall progress")


class ConversationCompleted(DomainEvent):
    """
    Event emitted when a conversation successfully completes.

    Marks the successful conclusion of a coaching conversation.

    Attributes:
        topic: The coaching topic that was addressed
        total_messages: Total number of messages in conversation
        duration_seconds: Duration from start to completion
        insights_count: Number of insights gathered
        final_phase: Final phase reached (should be COMPLETION)
    """

    event_type: str = Field(default="ConversationCompleted", frozen=True)
    aggregate_type: str = Field(default="Conversation", frozen=True)

    topic: CoachingTopic = Field(..., description="Coaching topic")
    total_messages: int = Field(..., ge=0, description="Total message count")
    duration_seconds: float = Field(..., ge=0, description="Conversation duration")
    insights_count: int = Field(..., ge=0, description="Number of insights gathered")
    final_phase: ConversationPhase = Field(..., description="Final phase reached")


class ConversationPaused(DomainEvent):
    """
    Event emitted when a conversation is paused.

    Allows users to pause and resume conversations later.

    Attributes:
        reason: Reason for pausing (user request, timeout, etc.)
        current_phase: Phase when conversation was paused
        message_count: Number of messages at pause time
        can_resume: Whether conversation can be resumed
    """

    event_type: str = Field(default="ConversationPaused", frozen=True)
    aggregate_type: str = Field(default="Conversation", frozen=True)

    reason: str = Field(..., description="Reason for pausing")
    current_phase: ConversationPhase = Field(..., description="Phase when paused")
    message_count: int = Field(..., ge=0, description="Messages at pause time")
    can_resume: bool = Field(default=True, description="Whether conversation can be resumed")


class ConversationResumed(DomainEvent):
    """
    Event emitted when a paused conversation is resumed.

    Marks the continuation of a previously paused conversation.

    Attributes:
        paused_at: When the conversation was originally paused
        paused_duration_seconds: How long it was paused
        resume_phase: Phase being resumed into
        message_count: Number of messages at resume time
    """

    event_type: str = Field(default="ConversationResumed", frozen=True)
    aggregate_type: str = Field(default="Conversation", frozen=True)

    paused_at: datetime = Field(..., description="When conversation was paused")
    paused_duration_seconds: float = Field(..., ge=0, description="Duration of pause")
    resume_phase: ConversationPhase = Field(..., description="Phase being resumed")
    message_count: int = Field(..., ge=0, description="Messages at resume time")


__all__ = [
    "ConversationCompleted",
    "ConversationInitiated",
    "ConversationPaused",
    "ConversationResumed",
    "MessageAdded",
    "PhaseTransitioned",
]
