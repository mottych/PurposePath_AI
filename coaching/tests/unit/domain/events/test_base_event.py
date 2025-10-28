"""Unit tests for base DomainEvent."""

from datetime import UTC, datetime

import pytest
from coaching.src.domain.events.base_event import DomainEvent


class TestDomainEventCreation:
    """Test suite for DomainEvent creation and initialization."""

    def test_create_event_with_required_fields(self) -> None:
        """Test creating event with only required fields."""
        event = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-123",
            aggregate_type="TestAggregate",
        )

        assert event.event_type == "TestEvent"
        assert event.aggregate_id == "test-123"
        assert event.aggregate_type == "TestAggregate"
        assert event.event_id is not None  # Auto-generated UUID
        assert isinstance(event.occurred_at, datetime)
        assert event.correlation_id is None
        assert event.causation_id is None
        assert event.metadata == {}

    def test_create_event_with_all_fields(self) -> None:
        """Test creating event with all fields."""
        occurred_at = datetime.now(UTC)
        event = DomainEvent(
            event_id="custom-event-id",
            event_type="TestEvent",
            aggregate_id="test-123",
            aggregate_type="TestAggregate",
            occurred_at=occurred_at,
            correlation_id="corr-456",
            causation_id="cause-789",
            metadata={"key": "value"},
        )

        assert event.event_id == "custom-event-id"
        assert event.correlation_id == "corr-456"
        assert event.causation_id == "cause-789"
        assert event.metadata == {"key": "value"}
        assert event.occurred_at == occurred_at

    def test_event_id_auto_generation(self) -> None:
        """Test that event_id is auto-generated as UUID."""
        event1 = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-123",
            aggregate_type="TestAggregate",
        )
        event2 = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-456",
            aggregate_type="TestAggregate",
        )

        assert event1.event_id != event2.event_id
        assert len(event1.event_id) == 36  # UUID format


class TestDomainEventImmutability:
    """Test suite for event immutability."""

    def test_event_is_frozen(self) -> None:
        """Test that events cannot be modified after creation."""
        event = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-123",
            aggregate_type="TestAggregate",
        )

        with pytest.raises(Exception):  # Pydantic raises ValidationError for frozen models
            event.event_type = "ModifiedEvent"  # type: ignore

    def test_metadata_is_not_frozen(self) -> None:
        """Test that metadata dict can be modified (mutable field)."""
        event = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-123",
            aggregate_type="TestAggregate",
            metadata={"initial": "value"},
        )

        # Metadata is a dict, so it can be modified (not frozen)
        event.metadata["new_key"] = "new_value"
        assert event.metadata["new_key"] == "new_value"


class TestDomainEventSerialization:
    """Test suite for event serialization and deserialization."""

    def test_to_dict(self) -> None:
        """Test converting event to dictionary."""
        event = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-123",
            aggregate_type="TestAggregate",
            correlation_id="corr-456",
            metadata={"key": "value"},
        )

        data = event.to_dict()

        assert data["event_type"] == "TestEvent"
        assert data["aggregate_id"] == "test-123"
        assert data["aggregate_type"] == "TestAggregate"
        assert data["correlation_id"] == "corr-456"
        assert data["metadata"] == {"key": "value"}
        assert "occurred_at" in data
        assert isinstance(data["occurred_at"], str)  # ISO format

    def test_to_json(self) -> None:
        """Test converting event to JSON string."""
        event = DomainEvent(
            event_type="TestEvent",
            aggregate_id="test-123",
            aggregate_type="TestAggregate",
        )

        json_str = event.to_json()

        assert isinstance(json_str, str)
        assert "TestEvent" in json_str
        assert "test-123" in json_str

    def test_from_dict(self) -> None:
        """Test reconstructing event from dictionary."""
        original = DomainEvent(
            event_id="event-123",
            event_type="TestEvent",
            aggregate_id="agg-456",
            aggregate_type="TestAggregate",
            correlation_id="corr-789",
        )

        data = original.to_dict()
        reconstructed = DomainEvent.from_dict(data)

        assert reconstructed.event_id == original.event_id
        assert reconstructed.event_type == original.event_type
        assert reconstructed.aggregate_id == original.aggregate_id
        assert reconstructed.correlation_id == original.correlation_id

    def test_from_dict_with_iso_timestamp(self) -> None:
        """Test deserializing event with ISO format timestamp."""
        data = {
            "event_id": "event-123",
            "event_type": "TestEvent",
            "aggregate_id": "agg-456",
            "aggregate_type": "TestAggregate",
            "occurred_at": "2025-10-09T17:00:00+00:00",
            "correlation_id": None,
            "causation_id": None,
            "metadata": {},
        }

        event = DomainEvent.from_dict(data)

        assert isinstance(event.occurred_at, datetime)
        assert event.occurred_at.tzinfo is not None  # Has timezone info


class TestDomainEventTraceability:
    """Test suite for correlation and causation tracking."""

    def test_correlation_id_propagation(self) -> None:
        """Test that correlation_id can be set for tracing."""
        correlation_id = "trace-correlate-123"

        event1 = DomainEvent(
            event_type="Event1",
            aggregate_id="agg-1",
            aggregate_type="Aggregate",
            correlation_id=correlation_id,
        )

        event2 = DomainEvent(
            event_type="Event2",
            aggregate_id="agg-2",
            aggregate_type="Aggregate",
            correlation_id=correlation_id,
            causation_id=event1.event_id,
        )

        assert event1.correlation_id == correlation_id
        assert event2.correlation_id == correlation_id
        assert event2.causation_id == event1.event_id

    def test_causation_chain(self) -> None:
        """Test tracking causation chain across events."""
        event1 = DomainEvent(
            event_type="InitialEvent",
            aggregate_id="agg-1",
            aggregate_type="Aggregate",
        )

        event2 = DomainEvent(
            event_type="DerivedEvent",
            aggregate_id="agg-1",
            aggregate_type="Aggregate",
            causation_id=event1.event_id,
        )

        event3 = DomainEvent(
            event_type="FinalEvent",
            aggregate_id="agg-1",
            aggregate_type="Aggregate",
            causation_id=event2.event_id,
        )

        # Chain: event1 -> event2 -> event3
        assert event2.causation_id == event1.event_id
        assert event3.causation_id == event2.event_id
