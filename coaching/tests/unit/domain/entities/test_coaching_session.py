"""Unit tests for CoachingSession entity.

Tests for the CoachingSession aggregate root, including state management,
message handling, and lifecycle operations.
"""

from datetime import UTC, datetime

import pytest
from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.core.types import TenantId, UserId
from coaching.src.domain.entities.coaching_session import (
    CoachingMessage,
    CoachingSession,
)


class TestCoachingMessage:
    """Tests for CoachingMessage value object."""

    def test_create_message_with_defaults(self) -> None:
        """Test creating a message with default values."""
        message = CoachingMessage(
            role=MessageRole.USER,
            content="Hello, coach!",
        )

        assert message.role == MessageRole.USER
        assert message.content == "Hello, coach!"
        assert message.metadata == {}
        assert message.timestamp is not None

    def test_create_message_with_metadata(self) -> None:
        """Test creating a message with custom metadata."""
        metadata = {"source": "web", "client_version": "1.0.0"}
        message = CoachingMessage(
            role=MessageRole.ASSISTANT,
            content="How can I help you?",
            metadata=metadata,
        )

        assert message.metadata == metadata

    def test_message_is_frozen(self) -> None:
        """Test that messages are immutable."""
        message = CoachingMessage(
            role=MessageRole.USER,
            content="Test",
        )

        with pytest.raises(Exception):  # ValidationError or similar
            message.content = "Modified"  # type: ignore[misc]


class TestCoachingSessionCreation:
    """Tests for CoachingSession creation and initialization."""

    def test_create_session_with_factory(self) -> None:
        """Test creating a session using the factory method."""
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

        assert session.tenant_id == TenantId("tenant_123")
        assert session.topic_id == "core_values"
        assert session.user_id == UserId("user_456")
        assert session.status == ConversationStatus.ACTIVE
        assert session.messages == []
        assert session.context == {}
        assert session.result is None
        assert session.completed_at is None

    def test_create_session_with_context(self) -> None:
        """Test creating a session with initial context."""
        context = {"enriched_param": "value", "user_name": "John"}
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="purpose",
            user_id="user_456",
            context=context,
        )

        assert session.context == context

    def test_session_has_valid_timestamps(self) -> None:
        """Test that sessions have valid timestamps on creation."""
        before = datetime.now(UTC)
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="vision",
            user_id="user_456",
        )
        after = datetime.now(UTC)

        assert before <= session.created_at <= after
        assert before <= session.updated_at <= after
        assert before <= session.last_activity_at <= after

    def test_session_has_unique_id(self) -> None:
        """Test that each session gets a unique ID."""
        session1 = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )
        session2 = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

        assert session1.session_id != session2.session_id
        assert str(session1.session_id).startswith("sess_")


class TestCoachingSessionStateQueries:
    """Tests for session state query methods."""

    @pytest.fixture
    def active_session(self) -> CoachingSession:
        """Create an active session for testing."""
        return CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

    def test_is_active_returns_true_for_active_session(
        self, active_session: CoachingSession
    ) -> None:
        """Test is_active() returns True for active sessions."""
        assert active_session.is_active() is True
        assert active_session.is_paused() is False
        assert active_session.is_completed() is False
        assert active_session.is_cancelled() is False

    def test_can_accept_messages_when_active(self, active_session: CoachingSession) -> None:
        """Test that active sessions can accept messages."""
        assert active_session.can_accept_messages() is True

    def test_message_counts_start_at_zero(self, active_session: CoachingSession) -> None:
        """Test that new sessions have zero messages."""
        assert active_session.get_message_count() == 0
        assert active_session.get_user_message_count() == 0
        assert active_session.get_assistant_message_count() == 0


class TestCoachingSessionMessageHandling:
    """Tests for adding and managing messages."""

    @pytest.fixture
    def session(self) -> CoachingSession:
        """Create a session for testing."""
        return CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

    def test_add_user_message(self, session: CoachingSession) -> None:
        """Test adding a user message."""
        message = session.add_user_message("What are my core values?")

        assert message.role == MessageRole.USER
        assert message.content == "What are my core values?"
        assert session.get_message_count() == 1
        assert session.get_user_message_count() == 1

    def test_add_assistant_message(self, session: CoachingSession) -> None:
        """Test adding an assistant message."""
        message = session.add_assistant_message("Let's explore your values together.")

        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Let's explore your values together."
        assert session.get_message_count() == 1
        assert session.get_assistant_message_count() == 1

    def test_add_multiple_messages(self, session: CoachingSession) -> None:
        """Test adding multiple messages in sequence."""
        session.add_user_message("First message")
        session.add_assistant_message("First response")
        session.add_user_message("Second message")
        session.add_assistant_message("Second response")

        assert session.get_message_count() == 4
        assert session.get_user_message_count() == 2
        assert session.get_assistant_message_count() == 2

    def test_add_message_updates_last_activity_for_user(self, session: CoachingSession) -> None:
        """Test that user messages update last_activity_at."""
        initial_activity = session.last_activity_at
        session.add_user_message("Test message")

        assert session.last_activity_at >= initial_activity

    def test_add_message_to_paused_session_raises_error(self, session: CoachingSession) -> None:
        """Test that paused sessions reject new messages."""
        session.pause()

        with pytest.raises(ValueError, match="Cannot add message"):
            session.add_user_message("Should fail")

    def test_add_message_to_completed_session_raises_error(self, session: CoachingSession) -> None:
        """Test that completed sessions reject new messages."""
        session.complete({"core_values": []})

        with pytest.raises(ValueError, match="Cannot add message"):
            session.add_user_message("Should fail")


class TestCoachingSessionStateTransitions:
    """Tests for session lifecycle state transitions."""

    @pytest.fixture
    def session(self) -> CoachingSession:
        """Create a session for testing."""
        return CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

    def test_pause_active_session(self, session: CoachingSession) -> None:
        """Test pausing an active session."""
        session.pause()

        assert session.is_paused() is True
        assert session.is_active() is False
        assert session.can_accept_messages() is False

    def test_resume_paused_session(self, session: CoachingSession) -> None:
        """Test resuming a paused session."""
        session.pause()
        session.resume()

        assert session.is_active() is True
        assert session.is_paused() is False
        assert session.can_accept_messages() is True

    def test_resume_updates_last_activity(self, session: CoachingSession) -> None:
        """Test that resume updates last_activity_at."""
        session.pause()
        initial_activity = session.last_activity_at
        session.resume()

        assert session.last_activity_at >= initial_activity

    def test_complete_session_with_result(self, session: CoachingSession) -> None:
        """Test completing a session with a result."""
        result = {
            "core_values": [
                {"name": "Integrity", "description": "Being honest and ethical"},
            ]
        }
        session.complete(result)

        assert session.is_completed() is True
        assert session.result == result
        assert session.completed_at is not None
        assert session.can_accept_messages() is False

    def test_cancel_active_session(self, session: CoachingSession) -> None:
        """Test cancelling an active session."""
        session.cancel()

        assert session.is_cancelled() is True
        assert session.can_accept_messages() is False

    def test_cancel_paused_session(self, session: CoachingSession) -> None:
        """Test cancelling a paused session."""
        session.pause()
        session.cancel()

        assert session.is_cancelled() is True

    def test_cannot_pause_paused_session(self, session: CoachingSession) -> None:
        """Test that pausing a paused session raises error."""
        session.pause()

        with pytest.raises(ValueError, match="Cannot pause"):
            session.pause()

    def test_cannot_resume_active_session(self, session: CoachingSession) -> None:
        """Test that resuming an active session raises error."""
        with pytest.raises(ValueError, match="Cannot resume"):
            session.resume()

    def test_cannot_complete_paused_session(self, session: CoachingSession) -> None:
        """Test that completing a paused session raises error."""
        session.pause()

        with pytest.raises(ValueError, match="Cannot complete"):
            session.complete({"result": "test"})

    def test_cannot_cancel_completed_session(self, session: CoachingSession) -> None:
        """Test that cancelling a completed session raises error."""
        session.complete({"result": "test"})

        with pytest.raises(ValueError, match="Cannot cancel"):
            session.cancel()

    def test_mark_abandoned_from_paused(self, session: CoachingSession) -> None:
        """Test marking a paused session as abandoned."""
        session.pause()
        session.mark_abandoned()

        assert session.status == ConversationStatus.ABANDONED

    def test_cannot_abandon_active_session(self, session: CoachingSession) -> None:
        """Test that active sessions cannot be directly abandoned."""
        with pytest.raises(ValueError, match="Cannot abandon"):
            session.mark_abandoned()


class TestCoachingSessionLLMFormatting:
    """Tests for LLM context formatting."""

    @pytest.fixture
    def session_with_messages(self) -> CoachingSession:
        """Create a session with multiple messages."""
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )
        session.add_user_message("First user message")
        session.add_assistant_message("First assistant response")
        session.add_user_message("Second user message")
        session.add_assistant_message("Second assistant response")
        return session

    def test_get_messages_for_llm_format(self, session_with_messages: CoachingSession) -> None:
        """Test that messages are formatted correctly for LLM."""
        messages = session_with_messages.get_messages_for_llm()

        assert len(messages) == 4
        assert messages[0] == {"role": "user", "content": "First user message"}
        assert messages[1] == {"role": "assistant", "content": "First assistant response"}

    def test_get_messages_for_llm_sliding_window(self) -> None:
        """Test that sliding window limits message count."""
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

        # Add 35 messages
        for i in range(35):
            if i % 2 == 0:
                session.add_user_message(f"User message {i}")
            else:
                session.add_assistant_message(f"Assistant message {i}")

        # Request max 10 messages
        messages = session.get_messages_for_llm(max_messages=10)

        assert len(messages) == 10
        # Should be the last 10 messages
        assert "34" in messages[-1]["content"]  # Last message index


class TestCoachingSessionCompletionEstimate:
    """Tests for completion estimation."""

    def test_calculate_completion_with_no_messages(self) -> None:
        """Test completion estimate with no messages."""
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

        estimate = session.calculate_estimated_completion(estimated_total=20)
        assert estimate == 0.0

    def test_calculate_completion_partial(self) -> None:
        """Test completion estimate with some messages."""
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

        # Add 5 user messages
        for _ in range(5):
            session.add_user_message("Test")
            session.add_assistant_message("Response")

        estimate = session.calculate_estimated_completion(estimated_total=20)
        assert estimate == 0.25  # 5/20

    def test_calculate_completion_caps_at_100_percent(self) -> None:
        """Test that completion estimate doesn't exceed 1.0."""
        session = CoachingSession.create(
            tenant_id="tenant_123",
            topic_id="core_values",
            user_id="user_456",
        )

        # Add more messages than estimated total
        for _ in range(30):
            session.add_user_message("Test")

        estimate = session.calculate_estimated_completion(estimated_total=20)
        assert estimate == 1.0
