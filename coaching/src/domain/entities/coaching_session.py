"""Coaching Session aggregate root.

This module defines the CoachingSession entity as an aggregate root that manages
the state and business rules for a multi-turn coaching conversation.

The CoachingSession is the core entity for the generic coaching engine,
tracking conversation state, messages, and enforcing session lifecycle rules.
"""

from datetime import UTC, datetime
from typing import Any

from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.core.types import (
    SessionId,
    TenantId,
    UserId,
    create_session_id,
)
from pydantic import BaseModel, Field, field_validator


class CoachingMessage(BaseModel):
    """A message within a coaching session.

    Simplified message model for coaching conversations.
    Immutable once created.

    Attributes:
        role: The role of the message sender (user, assistant, system)
        content: The message content
        timestamp: When the message was created (UTC)
        metadata: Optional additional information
    """

    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Message creation timestamp (UTC)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional message metadata")

    model_config = {"frozen": True}


class CoachingSession(BaseModel):
    """Coaching Session aggregate root.

    Manages the state and lifecycle of a multi-turn coaching conversation.
    Each session belongs to one tenant and one topic, with a single user
    owning the session.

    Key Business Rules:
        - One active session per tenant per topic
        - Only the owning user can interact with the session
        - Sessions can be paused, resumed, completed, or cancelled
        - Completed/cancelled sessions are eventually deleted (TTL)
        - Messages cannot be added to non-active sessions

    Attributes:
        session_id: Unique identifier for this session
        tenant_id: ID of the tenant/organization
        topic_id: ID of the coaching topic (e.g., "core_values")
        user_id: ID of the user who owns this session
        status: Current status of the session
        messages: List of messages in the conversation
        context: Session-specific context data (e.g., enriched parameters)
        created_at: When session was created
        updated_at: When session was last updated
        last_activity_at: When user last interacted (for inactivity timeout)
        completed_at: When session was completed (if applicable)
        result: Final extracted result (only when completed)
    """

    session_id: SessionId = Field(
        default_factory=create_session_id,
        description="Unique session identifier",
    )
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    topic_id: str = Field(..., min_length=1, description="Coaching topic ID")
    user_id: UserId = Field(..., description="User who owns this session")
    status: ConversationStatus = Field(
        default=ConversationStatus.ACTIVE,
        description="Current session status",
    )
    messages: list[CoachingMessage] = Field(
        default_factory=list,
        description="Conversation messages",
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Session context (enriched parameters, etc.)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
    )
    last_activity_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last user activity timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="Final extracted result (only when completed)",
    )

    model_config = {"extra": "forbid"}

    # =========================================================================
    # Factory Methods
    # =========================================================================

    @classmethod
    def create(
        cls,
        tenant_id: str,
        topic_id: str,
        user_id: str,
        context: dict[str, Any] | None = None,
    ) -> "CoachingSession":
        """Create a new coaching session.

        Args:
            tenant_id: The tenant identifier
            topic_id: The coaching topic identifier
            user_id: The user who will own this session
            context: Optional initial context (e.g., enriched parameters)

        Returns:
            A new CoachingSession instance
        """
        return cls(
            tenant_id=TenantId(tenant_id),
            topic_id=topic_id,
            user_id=UserId(user_id),
            context=context or {},
        )

    # =========================================================================
    # State Queries
    # =========================================================================

    def is_active(self) -> bool:
        """Check if the session is active.

        Returns:
            True if session status is ACTIVE
        """
        return bool(self.status == ConversationStatus.ACTIVE)

    def is_paused(self) -> bool:
        """Check if the session is paused.

        Returns:
            True if session status is PAUSED
        """
        return bool(self.status == ConversationStatus.PAUSED)

    def is_completed(self) -> bool:
        """Check if the session is completed.

        Returns:
            True if session status is COMPLETED
        """
        return bool(self.status == ConversationStatus.COMPLETED)

    def is_cancelled(self) -> bool:
        """Check if the session is cancelled.

        Returns:
            True if session status is CANCELLED
        """
        return bool(self.status == ConversationStatus.CANCELLED)

    def can_accept_messages(self) -> bool:
        """Check if the session can accept new messages.

        Returns:
            True if session is active
        """
        return self.is_active()

    def get_message_count(self) -> int:
        """Get the total number of messages.

        Returns:
            Number of messages in the session
        """
        return len(self.messages)

    def get_user_message_count(self) -> int:
        """Get the number of user messages.

        Returns:
            Number of messages with role USER
        """
        return sum(1 for m in self.messages if m.role == MessageRole.USER)

    def get_assistant_message_count(self) -> int:
        """Get the number of assistant messages.

        Returns:
            Number of messages with role ASSISTANT
        """
        return sum(1 for m in self.messages if m.role == MessageRole.ASSISTANT)

    # =========================================================================
    # State Mutations
    # =========================================================================

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> CoachingMessage:
        """Add a message to the session.

        Args:
            role: The role of the message sender
            content: The message content
            metadata: Optional message metadata

        Returns:
            The created message

        Raises:
            ValueError: If session cannot accept messages
        """
        if not self.can_accept_messages():
            raise ValueError(f"Cannot add message to session with status: {self.status.value}")

        message = CoachingMessage(
            role=role,
            content=content,
            metadata=metadata or {},
        )

        self.messages.append(message)
        self._touch()

        # Update last_activity_at for user messages (for inactivity tracking)
        if role == MessageRole.USER:
            self.last_activity_at = datetime.now(UTC)

        return message

    def add_user_message(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> CoachingMessage:
        """Add a user message to the session.

        Convenience method for adding user messages.

        Args:
            content: The message content
            metadata: Optional message metadata

        Returns:
            The created message
        """
        return self.add_message(MessageRole.USER, content, metadata)

    def add_assistant_message(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> CoachingMessage:
        """Add an assistant message to the session.

        Convenience method for adding assistant messages.

        Args:
            content: The message content
            metadata: Optional message metadata

        Returns:
            The created message
        """
        return self.add_message(MessageRole.ASSISTANT, content, metadata)

    def pause(self) -> None:
        """Pause the session.

        Only active sessions can be paused.

        Raises:
            ValueError: If session is not active
        """
        if not self.is_active():
            raise ValueError(f"Cannot pause session with status: {self.status.value}")

        self.status = ConversationStatus.PAUSED
        self._touch()

    def resume(self) -> None:
        """Resume a paused session.

        Only paused sessions can be resumed.

        Raises:
            ValueError: If session is not paused
        """
        if not self.is_paused():
            raise ValueError(f"Cannot resume session with status: {self.status.value}")

        self.status = ConversationStatus.ACTIVE
        self.last_activity_at = datetime.now(UTC)
        self._touch()

    def complete(self, result: dict[str, Any]) -> None:
        """Complete the session with a final result.

        Only active sessions can be completed.

        Args:
            result: The final extracted result

        Raises:
            ValueError: If session is not active
        """
        if not self.is_active():
            raise ValueError(f"Cannot complete session with status: {self.status.value}")

        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.result = result
        self._touch()

    def cancel(self) -> None:
        """Cancel the session.

        Active or paused sessions can be cancelled.

        Raises:
            ValueError: If session cannot be cancelled
        """
        if self.status not in (ConversationStatus.ACTIVE, ConversationStatus.PAUSED):
            raise ValueError(f"Cannot cancel session with status: {self.status.value}")

        self.status = ConversationStatus.CANCELLED
        self._touch()

    def mark_abandoned(self) -> None:
        """Mark the session as abandoned (due to inactivity).

        Only paused sessions can be marked abandoned.

        Raises:
            ValueError: If session is not paused
        """
        if not self.is_paused():
            raise ValueError(f"Cannot abandon session with status: {self.status.value}")

        self.status = ConversationStatus.ABANDONED
        self._touch()

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(UTC)

    def get_messages_for_llm(self, max_messages: int = 30) -> list[dict[str, str]]:
        """Get messages formatted for LLM context.

        Applies sliding window to limit context size.

        Args:
            max_messages: Maximum number of messages to include

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        recent_messages = self.messages[-max_messages:]
        return [{"role": msg.role.value, "content": msg.content} for msg in recent_messages]

    def calculate_estimated_completion(self, estimated_total: int = 20) -> float:
        """Calculate estimated completion percentage.

        Based on number of user messages vs estimated total.

        Args:
            estimated_total: Estimated total messages for completion

        Returns:
            Completion percentage (0.0 to 1.0)
        """
        user_messages = self.get_user_message_count()
        return min(1.0, user_messages / max(1, estimated_total))

    @field_validator("messages")
    @classmethod
    def validate_messages_chronological(cls, v: list[CoachingMessage]) -> list[CoachingMessage]:
        """Ensure messages are in chronological order."""
        if len(v) > 1:
            for i in range(len(v) - 1):
                if v[i].timestamp > v[i + 1].timestamp:
                    raise ValueError("Messages must be in chronological order")
        return v
