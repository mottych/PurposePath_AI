"""Unit tests for conversation domain events."""

from datetime import UTC, datetime

import pytest
from coaching.src.core.constants import CoachingTopic, ConversationPhase, MessageRole
from coaching.src.domain.events.conversation_events import (
    ConversationCompleted,
    ConversationInitiated,
    ConversationPaused,
    ConversationResumed,
    MessageAdded,
    PhaseTransitioned,
)


class TestConversationInitiated:
    """Tests for ConversationInitiated event."""

    def test_create_conversation_initiated_event(self) -> None:
        """Test creating conversation initiated event."""
        event = ConversationInitiated(
            aggregate_id="conv-123",
            user_id="user-456",
            tenant_id="tenant-789",
            topic=CoachingTopic.CORE_VALUES,
            initial_phase=ConversationPhase.INTRODUCTION,
        )

        assert event.event_type == "ConversationInitiated"
        assert event.aggregate_type == "Conversation"
        assert event.user_id == "user-456"
        assert event.tenant_id == "tenant-789"
        assert event.topic == CoachingTopic.CORE_VALUES
        assert event.initial_phase == ConversationPhase.INTRODUCTION

    def test_event_is_immutable(self) -> None:
        """Test that event cannot be modified."""
        event = ConversationInitiated(
            aggregate_id="conv-123",
            user_id="user-456",
            tenant_id="tenant-789",
            topic=CoachingTopic.PURPOSE,
            initial_phase=ConversationPhase.INTRODUCTION,
        )

        with pytest.raises(Exception):
            event.user_id = "different-user"  # type: ignore

    def test_serialization(self) -> None:
        """Test event can be serialized and deserialized."""
        event = ConversationInitiated(
            aggregate_id="conv-123",
            user_id="user-456",
            tenant_id="tenant-789",
            topic=CoachingTopic.VISION,
            initial_phase=ConversationPhase.INTRODUCTION,
        )

        data = event.to_dict()
        assert data["topic"] == "vision"
        assert data["initial_phase"] == "introduction"


class TestMessageAdded:
    """Tests for MessageAdded event."""

    def test_create_user_message_event(self) -> None:
        """Test creating message added event for user message."""
        event = MessageAdded(
            aggregate_id="conv-123",
            role=MessageRole.USER,
            content_length=150,
            message_index=5,
            phase=ConversationPhase.EXPLORATION,
        )

        assert event.role == MessageRole.USER
        assert event.content_length == 150
        assert event.message_index == 5
        assert event.phase == ConversationPhase.EXPLORATION

    def test_create_assistant_message_event(self) -> None:
        """Test creating message added event for assistant message."""
        event = MessageAdded(
            aggregate_id="conv-123",
            role=MessageRole.ASSISTANT,
            content_length=300,
            message_index=6,
            phase=ConversationPhase.EXPLORATION,
        )

        assert event.role == MessageRole.ASSISTANT
        assert event.content_length == 300

    def test_message_index_validation(self) -> None:
        """Test that message_index must be non-negative."""
        with pytest.raises(Exception):  # Pydantic validation error
            MessageAdded(
                aggregate_id="conv-123",
                role=MessageRole.USER,
                content_length=100,
                message_index=-1,  # Invalid
                phase=ConversationPhase.INTRODUCTION,
            )


class TestPhaseTransitioned:
    """Tests for PhaseTransitioned event."""

    def test_create_phase_transition_event(self) -> None:
        """Test creating phase transition event."""
        event = PhaseTransitioned(
            aggregate_id="conv-123",
            from_phase=ConversationPhase.INTRODUCTION,
            to_phase=ConversationPhase.EXPLORATION,
            reason="User provided initial values",
            progress_percentage=20.0,
        )

        assert event.from_phase == ConversationPhase.INTRODUCTION
        assert event.to_phase == ConversationPhase.EXPLORATION
        assert event.reason == "User provided initial values"
        assert event.progress_percentage == 20.0

    def test_transition_without_reason(self) -> None:
        """Test transition event without specific reason."""
        event = PhaseTransitioned(
            aggregate_id="conv-123",
            from_phase=ConversationPhase.EXPLORATION,
            to_phase=ConversationPhase.DEEPENING,
            progress_percentage=40.0,
        )

        assert event.reason is None

    def test_progress_validation(self) -> None:
        """Test that progress must be within 0-100."""
        with pytest.raises(Exception):  # Pydantic validation
            PhaseTransitioned(
                aggregate_id="conv-123",
                from_phase=ConversationPhase.INTRODUCTION,
                to_phase=ConversationPhase.EXPLORATION,
                progress_percentage=150.0,  # Invalid
            )


class TestConversationCompleted:
    """Tests for ConversationCompleted event."""

    def test_create_completed_event(self) -> None:
        """Test creating conversation completed event."""
        event = ConversationCompleted(
            aggregate_id="conv-123",
            topic=CoachingTopic.GOALS,
            total_messages=25,
            duration_seconds=1800.5,
            insights_count=12,
            final_phase=ConversationPhase.COMPLETION,
        )

        assert event.topic == CoachingTopic.GOALS
        assert event.total_messages == 25
        assert event.duration_seconds == 1800.5
        assert event.insights_count == 12
        assert event.final_phase == ConversationPhase.COMPLETION

    def test_message_count_validation(self) -> None:
        """Test that total_messages must be non-negative."""
        with pytest.raises(Exception):
            ConversationCompleted(
                aggregate_id="conv-123",
                topic=CoachingTopic.PURPOSE,
                total_messages=-5,  # Invalid
                duration_seconds=1000.0,
                insights_count=10,
                final_phase=ConversationPhase.COMPLETION,
            )


class TestConversationPaused:
    """Tests for ConversationPaused event."""

    def test_create_paused_event(self) -> None:
        """Test creating conversation paused event."""
        event = ConversationPaused(
            aggregate_id="conv-123",
            reason="User requested pause",
            current_phase=ConversationPhase.DEEPENING,
            message_count=15,
            can_resume=True,
        )

        assert event.reason == "User requested pause"
        assert event.current_phase == ConversationPhase.DEEPENING
        assert event.message_count == 15
        assert event.can_resume is True

    def test_cannot_resume_scenario(self) -> None:
        """Test paused event where resumption is not allowed."""
        event = ConversationPaused(
            aggregate_id="conv-123",
            reason="Session timeout",
            current_phase=ConversationPhase.INTRODUCTION,
            message_count=2,
            can_resume=False,
        )

        assert event.can_resume is False


class TestConversationResumed:
    """Tests for ConversationResumed event."""

    def test_create_resumed_event(self) -> None:
        """Test creating conversation resumed event."""
        paused_time = datetime(2025, 10, 9, 12, 0, 0, tzinfo=UTC)

        event = ConversationResumed(
            aggregate_id="conv-123",
            paused_at=paused_time,
            paused_duration_seconds=3600.0,
            resume_phase=ConversationPhase.DEEPENING,
            message_count=15,
        )

        assert event.paused_at == paused_time
        assert event.paused_duration_seconds == 3600.0
        assert event.resume_phase == ConversationPhase.DEEPENING
        assert event.message_count == 15
