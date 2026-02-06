"""Coaching Session aggregate root.

This module defines the CoachingSession entity as an aggregate root that manages
the state and business rules for a multi-turn coaching conversation.

The CoachingSession is the core entity for the generic coaching engine,
tracking conversation state, messages, and enforcing session lifecycle rules.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.core.types import (
    SessionId,
    TenantId,
    UserId,
    create_session_id,
)
from coaching.src.domain.exceptions import (
    MaxTurnsReachedError,
    SessionExpiredError,
    SessionNotActiveError,
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
        - One active session per tenant per topic per user (Issue #157)
        - Only the owning user can interact with the session
        - Sessions can be paused, resumed, completed, or cancelled
        - Completed/cancelled sessions are eventually deleted (TTL)
        - Messages cannot be added to non-active sessions
        - Sessions have a max turn limit and can expire

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
        max_turns: Maximum number of conversation turns
        idle_timeout_minutes: Idle timeout in minutes
        expires_at: Absolute expiration time
        extracted_result: Final extracted result (only when completed)
        extraction_model: Model used for result extraction
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

    # Session limits (Issue #174)
    max_turns: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Maximum number of conversation turns (0 = unlimited)",
    )
    idle_timeout_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,  # Max 24 hours
        description="Idle timeout in minutes before session can be expired",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="Absolute expiration timestamp",
    )

    # Results (populated on completion)
    extracted_result: dict[str, Any] | None = Field(
        default=None,
        description="Final extracted result (only when completed)",
    )
    extraction_model: str | None = Field(
        default=None,
        description="Model used for result extraction",
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
        max_turns: int = 0,
        idle_timeout_minutes: int = 30,
        expires_at: datetime | None = None,
    ) -> "CoachingSession":
        """Create a new coaching session.

        Args:
            tenant_id: The tenant identifier
            topic_id: The coaching topic identifier
            user_id: The user who will own this session
            context: Optional initial context (e.g., enriched parameters)
            max_turns: Maximum number of conversation turns (0 = unlimited)
            idle_timeout_minutes: Idle timeout in minutes (default: 30)
            expires_at: Optional absolute expiration time

        Returns:
            A new CoachingSession instance
        """
        return cls(
            tenant_id=TenantId(tenant_id),
            topic_id=topic_id,
            user_id=UserId(user_id),
            context=context or {},
            max_turns=max_turns,
            idle_timeout_minutes=idle_timeout_minutes,
            expires_at=expires_at,
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

    def get_turn_count(self) -> int:
        """Get the number of conversation turns.

        A turn is counted as one user message.

        Returns:
            Number of turns (user messages)
        """
        return self.get_user_message_count()

    def is_expired(self) -> bool:
        """Check if the session has expired.

        Returns:
            True if expires_at is set and has passed
        """
        if self.expires_at is None:
            return False
        return datetime.now(UTC) >= self.expires_at

    def is_idle(self) -> bool:
        """Check if the session is idle (exceeded idle timeout).

        Returns:
            True if last_activity_at + idle_timeout has passed
        """
        if self.last_activity_at is None:
            return False
        idle_threshold = self.last_activity_at + timedelta(minutes=self.idle_timeout_minutes)
        return datetime.now(UTC) >= idle_threshold

    def can_add_turn(self) -> bool:
        """Check if another turn can be added to the session.

        Returns:
            True if max_turns is 0 (unlimited) or current turn count is less than max_turns
        """
        if self.max_turns == 0:
            return True  # Unlimited
        return self.get_turn_count() < self.max_turns

    def get_remaining_turns(self) -> int | None:
        """Get the number of remaining turns.

        Returns:
            Number of turns remaining before max_turns is reached, or None if unlimited
        """
        if self.max_turns == 0:
            return None  # Unlimited
        return max(0, self.max_turns - self.get_turn_count())

    def can_continue(self) -> bool:
        """Check if the session can continue accepting messages.

        A session can continue if:
        - It is active
        - It has not expired
        - It has not exceeded idle timeout
        - It has not reached max turns

        Returns:
            True if the session can accept more messages
        """
        return (
            self.is_active()
            and not self.is_expired()
            and not self.is_idle()
            and self.can_add_turn()
        )

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
            SessionNotActiveError: If session is not active
            SessionExpiredError: If session has expired
            SessionIdleTimeoutError: If session has exceeded idle timeout
            MaxTurnsReachedError: If adding a user message would exceed max turns
        """
        # Check session is active
        if not self.is_active():
            raise SessionNotActiveError(self.session_id, self.status.value)

        # Check expiration
        if self.is_expired():
            raise SessionExpiredError(self.session_id)

        # Note: Idle check removed - idle sessions can still receive messages
        # Users may have stepped away, had power outage, etc.
        # TTL handles cleanup of truly abandoned sessions after extended period

        # Check turn limit for user messages
        if role == MessageRole.USER and not self.can_add_turn():
            raise MaxTurnsReachedError(
                self.session_id,
                current_turn=self.get_turn_count(),
                max_turns=self.max_turns,
            )

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

    def complete(self, result: dict[str, Any], extraction_model: str | None = None) -> None:
        """Complete the session with a final result.

        Only active sessions can be completed.

        Args:
            result: The final extracted result
            extraction_model: The model used for extraction (optional)

        Raises:
            ValueError: If session is not active
        """
        if not self.is_active():
            raise ValueError(f"Cannot complete session with status: {self.status.value}")

        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.extracted_result = result
        self.extraction_model = extraction_model
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

    def mark_expired(self) -> None:
        """Mark the session as expired (due to expiration or idle timeout).

        Active sessions can be marked expired.

        Raises:
            ValueError: If session is not active
        """
        if not self.is_active():
            raise ValueError(f"Cannot expire session with status: {self.status.value}")

        self.status = ConversationStatus.ABANDONED  # Use ABANDONED for expired sessions
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
