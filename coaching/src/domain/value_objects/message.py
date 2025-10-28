"""Message value object for coaching conversations.

This module defines the immutable Message value object that represents
a single message within a coaching conversation.
"""

from datetime import UTC, datetime
from typing import Any

from coaching.src.core.constants import MessageRole
from coaching.src.core.types import MessageId, create_message_id
from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    """
    Immutable value object representing a message in a conversation.

    A message captures a single exchange with role, content, timestamp,
    and optional metadata. Messages are immutable once created.

    Attributes:
        message_id: Unique identifier for this message
        role: The role of the message sender (user, assistant, system)
        content: The actual message content
        timestamp: When the message was created (UTC)
        metadata: Optional additional information about the message
        tokens: Token usage data (input, output, total) for LLM responses
        cost: Calculated cost in USD for this message
        model_id: LLM model identifier used to generate this message

    Example:
        >>> message = Message(
        ...     role=MessageRole.USER,
        ...     content="What are my core values?",
        ...     metadata={"source": "web"}
        ... )
        >>> print(message.role)
        MessageRole.USER
    """

    message_id: MessageId = Field(
        default_factory=create_message_id,
        description="Unique identifier for this message",
    )
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Message creation timestamp (UTC)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional message metadata")

    # Token tracking fields for LLM usage analytics
    tokens: dict[str, int] | None = Field(
        default=None,
        description="Token usage: {'input': int, 'output': int, 'total': int}",
    )
    cost: float | None = Field(
        default=None,
        description="Calculated cost in USD for this message",
        ge=0.0,
    )
    model_id: str | None = Field(
        default=None,
        description="LLM model identifier (e.g., 'anthropic.claude-3-5-sonnet-20241022-v2:0')",
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not just whitespace."""
        if not v.strip():
            raise ValueError("Message content cannot be empty or whitespace only")
        return v.strip()

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp_not_future(cls, v: datetime) -> datetime:
        """Ensure timestamp is not in the future."""
        now = datetime.now(UTC)
        if v > now:
            raise ValueError("Message timestamp cannot be in the future")
        return v

    def is_from_user(self) -> bool:
        """
        Check if this message is from the user.

        Returns:
            bool: True if the message role is USER
        """
        return self.role == MessageRole.USER

    def is_from_assistant(self) -> bool:
        """
        Check if this message is from the assistant.

        Returns:
            bool: True if the message role is ASSISTANT
        """
        return self.role == MessageRole.ASSISTANT

    def is_system_message(self) -> bool:
        """
        Check if this message is a system message.

        Returns:
            bool: True if the message role is SYSTEM
        """
        return self.role == MessageRole.SYSTEM

    def get_content_length(self) -> int:
        """
        Get the character count of the message content.

        Returns:
            int: Number of characters in the content
        """
        return len(self.content)

    def has_metadata(self) -> bool:
        """
        Check if this message has any metadata.

        Returns:
            bool: True if metadata dict is not empty
        """
        return len(self.metadata) > 0


__all__ = ["Message"]
