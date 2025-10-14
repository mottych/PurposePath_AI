"""Conversation models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from coaching.src.core.constants import ConversationPhase, ConversationStatus, MessageRole
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A message in a conversation."""

    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationContext(BaseModel):
    """Context information for a conversation."""

    phase: ConversationPhase = ConversationPhase.INTRODUCTION
    identified_values: List[str] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    progress_markers: Dict[str, Any] = Field(default_factory=dict)
    categories_explored: List[str] = Field(default_factory=list)
    response_count: int = 0
    deepening_count: int = 0

    # Multitenant context fields
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    business_context: Dict[str, Any] = Field(default_factory=dict)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    language: str = "en"

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like access for backwards compatibility."""
        return getattr(self, key, default)


class ConversationSession(BaseModel):
    """Session data for active conversation."""

    conversation_id: str
    phase: ConversationPhase
    context: Dict[str, Any]
    message_count: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    memory_summary: Optional[str] = None


class Conversation(BaseModel):
    """Complete conversation model."""

    conversation_id: str
    user_id: str
    topic: str
    status: ConversationStatus = ConversationStatus.ACTIVE
    messages: List[Message] = Field(default_factory=list)
    context: ConversationContext = Field(default_factory=ConversationContext)
    llm_config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    ttl: Optional[int] = None

    def add_message(
        self, role: MessageRole, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the conversation."""
        message = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)

        if role == MessageRole.USER:
            self.context.response_count += 1

    def get_conversation_history(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """Get conversation history for LLM context."""
        messages = self.messages[-max_messages:] if max_messages else self.messages
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]

    def calculate_progress(self) -> float:
        """Calculate conversation progress."""
        from coaching.src.core.constants import PHASE_PROGRESS_WEIGHTS

        return PHASE_PROGRESS_WEIGHTS.get(self.context.phase, 0.0)

    def is_active(self) -> bool:
        """Check if conversation is active."""
        return self.status == ConversationStatus.ACTIVE

    def mark_completed(self) -> None:
        """Mark conversation as completed."""
        self.status = ConversationStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def mark_paused(self) -> None:
        """Mark conversation as paused."""
        self.status = ConversationStatus.PAUSED
        self.paused_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def resume(self) -> None:
        """Resume a paused conversation."""
        if self.status == ConversationStatus.PAUSED:
            self.status = ConversationStatus.ACTIVE
            self.updated_at = datetime.now(timezone.utc)
