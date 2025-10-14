"""Base domain event for event sourcing and observability.

This module provides the foundational event class for all domain events
in the system, supporting distributed tracing and event serialization.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """
    Base class for all domain events.

    Domain events represent significant business occurrences that have
    happened in the system. They are immutable facts about the past.

    Attributes:
        event_id: Unique identifier for this event instance
        event_type: Type/name of the event (e.g., "ConversationInitiated")
        aggregate_id: ID of the aggregate root that produced this event
        aggregate_type: Type of the aggregate (e.g., "Conversation")
        occurred_at: UTC timestamp when the event occurred
        correlation_id: ID to correlate related events across services
        causation_id: ID of the event/command that caused this event
        metadata: Additional context-specific data

    Design Principles:
        - Immutable: Events are facts that cannot be changed
        - Serializable: Can be converted to/from JSON for storage/transmission
        - Traceable: Include correlation IDs for distributed tracing
        - Self-describing: Contains all necessary context
    """

    model_config = {"frozen": True}  # Immutable

    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this event instance",
    )
    event_type: str = Field(..., description="Type/name of the event")
    aggregate_id: str = Field(..., description="ID of the aggregate that produced this event")
    aggregate_type: str = Field(..., description="Type of the aggregate root")
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when the event occurred",
    )
    correlation_id: str | None = Field(
        default=None, description="ID to correlate related events across services"
    )
    causation_id: str | None = Field(
        default=None, description="ID of the event/command that caused this event"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context-specific data"
    )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert event to dictionary for serialization.

        Returns:
            dict: Event data as dictionary with ISO format timestamps

        Business Rule: Events must be serializable for storage and transmission
        """
        data = self.model_dump()
        # Convert datetime to ISO format string
        if isinstance(data.get("occurred_at"), datetime):
            data["occurred_at"] = data["occurred_at"].isoformat()
        return data

    def to_json(self) -> str:
        """
        Convert event to JSON string.

        Returns:
            str: JSON representation of the event

        Business Rule: Events must be JSON serializable for event store
        """
        return self.model_dump_json()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DomainEvent":
        """
        Create event from dictionary.

        Args:
            data: Event data as dictionary

        Returns:
            DomainEvent: Reconstructed event instance

        Business Rule: Events must be deserializable from storage
        """
        # Convert ISO format string back to datetime if needed
        if isinstance(data.get("occurred_at"), str):
            data["occurred_at"] = datetime.fromisoformat(data["occurred_at"])
        return cls(**data)


__all__ = ["DomainEvent"]
