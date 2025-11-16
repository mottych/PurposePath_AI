"""Conversation models."""

from datetime import UTC, datetime
from typing import Any

from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.domain.value_objects.message import Message
from pydantic import BaseModel, Field


class ConversationContext(BaseModel):
    """Context information for a conversation."""

    # Phase removed - no longer used
    identified_values: list[str] = Field(default_factory=list)
    key_insights: list[str] = Field(default_factory=list)
    progress_markers: dict[str, Any] = Field(default_factory=dict)
    categories_explored: list[str] = Field(default_factory=list)
    response_count: int = 0
    deepening_count: int = 0

    # Multitenant context fields
    tenant_id: str | None = None
    session_id: str | None = None
    business_context: dict[str, Any] = Field(default_factory=dict)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    language: str = "en"

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like access for backwards compatibility."""
        return getattr(self, key, default)


class ConversationSession(BaseModel):
    """Session data for active conversation."""

    conversation_id: str
    # Phase removed - no longer used
    status: str = "active"
    context: dict[str, Any]
    message_count: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    memory_summary: str | None = None


class Conversation(BaseModel):
    """Complete conversation model."""

    conversation_id: str
    user_id: str
    topic: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: list[Message] = Field(default_factory=list)
    context: ConversationContext = Field(default_factory=ConversationContext)
    llm_config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    paused_at: datetime | None = None
    ttl: int | None = None

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: dict[str, Any] | None = None,
        tokens: dict[str, int] | None = None,
        cost: float | None = None,
        model_id: str | None = None,
    ) -> None:
        """Add a message to the conversation.

        Args:
            role: Message role (USER, ASSISTANT, SYSTEM)
            content: Message content
            metadata: Optional metadata
            tokens: Token usage dict with 'input', 'output', 'total' keys
            cost: Calculated cost in USD for this message
            model_id: LLM model identifier used
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {},
            tokens=tokens,
            cost=cost,
            model_id=model_id,
        )
        self.messages.append(message)
        self.updated_at = datetime.now(UTC)

        if role == MessageRole.USER:
            self.context.response_count += 1

    def get_conversation_history(self, max_messages: int | None = None) -> list[dict[str, str]]:
        """Get conversation history for LLM context."""
        messages = self.messages[-max_messages:] if max_messages else self.messages
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    def calculate_progress(self) -> float:
        """Calculate conversation progress based on message count."""
        total_messages = len(self.messages)
        if total_messages == 0:
            return 0.0
        # Simple heuristic: typical conversation completes around 12 messages
        return min(1.0, total_messages / 12.0)

    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE

    def mark_completed(self) -> None:
        """Mark conversation as completed."""
        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def mark_paused(self) -> None:
        """Mark conversation as paused."""
        self.status = ConversationStatus.PAUSED
        self.paused_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def resume(self) -> None:
        """Resume a paused conversation."""
        if self.status == ConversationStatus.PAUSED:
            self.status = ConversationStatus.ACTIVE
            self.updated_at = datetime.now(UTC)
