"""Conversation aggregate root.

This module defines the Conversation entity as an aggregate root that enforces
business rules for coaching conversations.
"""

from datetime import UTC, datetime
from typing import Any

from coaching.src.core.constants import (
    PHASE_PROGRESS_WEIGHTS,
    CoachingTopic,
    ConversationPhase,
    ConversationStatus,
    MessageRole,
)
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.value_objects.conversation_context import (
    ConversationContext,
)
from coaching.src.domain.value_objects.message import Message
from pydantic import BaseModel, Field, field_validator


class Conversation(BaseModel):
    """
    Conversation aggregate root enforcing business rules.

    This is the main aggregate for coaching conversations, responsible for
    maintaining conversation invariants, managing messages, and enforcing
    phase transition rules.

    Attributes:
        conversation_id: Unique identifier for this conversation
        user_id: ID of the user having the conversation
        tenant_id: ID of the tenant/organization
        topic: Coaching topic for this conversation
        status: Current status of the conversation
        messages: List of messages in the conversation
        context: Conversation context and progress tracking
        created_at: When conversation was created
        updated_at: When conversation was last updated
        completed_at: When conversation was completed (if applicable)

    Business Rules:
        - Cannot add messages to non-active conversations
        - Phase transitions must follow proper sequence
        - Minimum response counts required for phase advancement
        - Conversations can only be completed once validation phase reached
    """

    conversation_id: ConversationId = Field(..., description="Unique conversation ID")
    user_id: UserId = Field(..., description="User ID")
    tenant_id: TenantId = Field(..., description="Tenant ID")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    status: ConversationStatus = Field(
        default=ConversationStatus.ACTIVE, description="Conversation status"
    )
    messages: list[Message] = Field(default_factory=list, description="Conversation messages")
    context: ConversationContext = Field(
        default_factory=lambda: ConversationContext(current_phase=ConversationPhase.INTRODUCTION),
        description="Conversation context",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )
    completed_at: datetime | None = Field(default=None, description="Completion timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"extra": "forbid"}

    @field_validator("messages")
    @classmethod
    def validate_messages_chronological(cls, v: list[Message]) -> list[Message]:
        """Ensure messages are in chronological order."""
        if len(v) > 1:
            for i in range(len(v) - 1):
                if v[i].timestamp > v[i + 1].timestamp:
                    raise ValueError("Messages must be in chronological order")
        return v

    def add_message(
        self, role: MessageRole, content: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Add a message to the conversation.

        Args:
            role: Role of the message sender
            content: Message content
            metadata: Optional message metadata

        Raises:
            ValueError: If conversation is not active

        Business Rule: Can only add messages to active conversations
        """
        if not self.is_active():
            raise ValueError(f"Cannot add message to {self.status.value} conversation")

        message = Message(role=role, content=content, metadata=metadata or {})

        # Use object.__setattr__ to modify frozen list
        object.__setattr__(self, "messages", [*self.messages, message])
        object.__setattr__(self, "updated_at", datetime.now(UTC))

        # Update context response count for user messages
        if role == MessageRole.USER:
            new_context = ConversationContext(
                current_phase=self.context.current_phase,
                insights=self.context.insights,
                response_count=self.context.response_count + 1,
                progress_percentage=self.context.progress_percentage,
                metadata=self.context.metadata,
            )
            object.__setattr__(self, "context", new_context)

    def transition_to_phase(self, new_phase: ConversationPhase) -> None:
        """
        Transition conversation to a new phase.

        Args:
            new_phase: The phase to transition to

        Raises:
            ValueError: If transition is invalid

        Business Rule: Phase transitions must follow proper sequence
        """
        if not self.is_active():
            raise ValueError(f"Cannot transition {self.status.value} conversation")

        # Validate phase sequence
        phase_order = [
            ConversationPhase.INTRODUCTION,
            ConversationPhase.EXPLORATION,
            ConversationPhase.DEEPENING,
            ConversationPhase.SYNTHESIS,
            ConversationPhase.VALIDATION,
            ConversationPhase.COMPLETION,
        ]

        current_index = phase_order.index(self.context.current_phase)
        new_index = phase_order.index(new_phase)

        # Can only move forward or stay in same phase
        if new_index < current_index:
            raise ValueError(
                f"Cannot move backward from {self.context.current_phase.value} to {new_phase.value}"
            )

        # Update context with new phase and progress
        new_progress = PHASE_PROGRESS_WEIGHTS.get(new_phase, 0.0) * 100
        new_context = ConversationContext(
            current_phase=new_phase,
            insights=self.context.insights,
            response_count=self.context.response_count,
            progress_percentage=new_progress,
            metadata=self.context.metadata,
        )

        object.__setattr__(self, "context", new_context)
        object.__setattr__(self, "updated_at", datetime.now(UTC))

    def add_insight(self, insight: str) -> None:
        """
        Add an insight to the conversation context.

        Args:
            insight: The insight to add

        Business Rule: Insights must be non-empty
        """
        if not insight.strip():
            raise ValueError("Insight cannot be empty")

        new_insights = [*self.context.insights, insight.strip()]
        new_context = ConversationContext(
            current_phase=self.context.current_phase,
            insights=new_insights,
            response_count=self.context.response_count,
            progress_percentage=self.context.progress_percentage,
            metadata=self.context.metadata,
        )

        object.__setattr__(self, "context", new_context)
        object.__setattr__(self, "updated_at", datetime.now(UTC))

    def mark_completed(self) -> None:
        """
        Mark conversation as completed.

        Raises:
            ValueError: If conversation cannot be completed

        Business Rule: Can only complete conversations in validation/completion phase
        """
        if not self.is_active():
            raise ValueError(f"Cannot complete {self.status.value} conversation")

        if self.context.current_phase not in [
            ConversationPhase.VALIDATION,
            ConversationPhase.COMPLETION,
        ]:
            raise ValueError(
                f"Cannot complete conversation in {self.context.current_phase.value} phase"
            )

        now = datetime.now(UTC)
        object.__setattr__(self, "status", ConversationStatus.COMPLETED)
        object.__setattr__(self, "completed_at", now)
        object.__setattr__(self, "updated_at", now)

    def mark_paused(self) -> None:
        """
        Mark conversation as paused.

        Business Rule: Can only pause active conversations
        """
        if not self.is_active():
            raise ValueError(f"Cannot pause {self.status.value} conversation")

        now = datetime.now(UTC)
        object.__setattr__(self, "status", ConversationStatus.PAUSED)
        object.__setattr__(self, "updated_at", now)

    def resume(self) -> None:
        """
        Resume a paused conversation.

        Raises:
            ValueError: If conversation is not paused

        Business Rule: Can only resume paused conversations
        """
        if self.status != ConversationStatus.PAUSED:
            raise ValueError(f"Cannot resume {self.status.value} conversation, must be paused")

        object.__setattr__(self, "status", ConversationStatus.ACTIVE)
        object.__setattr__(self, "updated_at", datetime.now(UTC))

    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE

    def is_completed(self) -> bool:
        """Check if conversation is completed."""
        return self.status == ConversationStatus.COMPLETED

    def is_paused(self) -> bool:
        """Check if conversation is paused."""
        return self.status == ConversationStatus.PAUSED

    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    def get_user_message_count(self) -> int:
        """Get number of user messages."""
        return sum(1 for msg in self.messages if msg.is_from_user())

    def get_assistant_message_count(self) -> int:
        """Get number of assistant messages."""
        return sum(1 for msg in self.messages if msg.is_from_assistant())

    def calculate_progress_percentage(self) -> float:
        """
        Calculate current progress percentage.

        Returns:
            float: Progress percentage (0-100)
        """
        return PHASE_PROGRESS_WEIGHTS.get(self.context.current_phase, 0.0) * 100

    def get_conversation_history(self, max_messages: int | None = None) -> list[dict[str, str]]:
        """
        Get conversation history in LLM-compatible format.

        Args:
            max_messages: Maximum number of recent messages to include

        Returns:
            list: Messages in format suitable for LLM
        """
        messages = self.messages[-max_messages:] if max_messages else self.messages
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]


__all__ = ["Conversation"]
