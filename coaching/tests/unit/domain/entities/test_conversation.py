"""Unit tests for Conversation aggregate root."""

import pytest
from coaching.src.core.constants import (
    CoachingTopic,
    ConversationPhase,
    ConversationStatus,
    MessageRole,
)
from coaching.src.core.types import (
    create_conversation_id,
    create_tenant_id,
    create_user_id,
)
from coaching.src.domain.entities.conversation import Conversation


class TestConversationCreation:
    """Test suite for Conversation creation."""

    def test_create_conversation_with_required_fields(self) -> None:
        """Test creating conversation with required fields."""
        # Arrange & Act
        conversation = Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

        # Assert
        assert conversation.conversation_id is not None
        assert conversation.user_id == "user_123"
        assert conversation.tenant_id == "tenant_456"
        assert conversation.topic == CoachingTopic.CORE_VALUES
        assert conversation.status == ConversationStatus.ACTIVE
        assert len(conversation.messages) == 0
        assert conversation.context.current_phase == ConversationPhase.INTRODUCTION

    def test_create_conversation_initializes_timestamps(self) -> None:
        """Test that timestamps are auto-initialized."""
        # Arrange & Act
        conversation = Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.PURPOSE,
        )

        # Assert
        assert conversation.created_at is not None
        assert conversation.updated_at is not None
        assert conversation.completed_at is None


class TestConversationMessageManagement:
    """Test suite for message management."""

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing a test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_add_message_to_active_conversation(self, conversation: Conversation) -> None:
        """Test adding message to active conversation."""
        # Arrange
        initial_count = len(conversation.messages)

        # Act
        conversation.add_message(role=MessageRole.USER, content="What are my values?")

        # Assert
        assert len(conversation.messages) == initial_count + 1
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.messages[0].content == "What are my values?"

    def test_add_user_message_increments_response_count(self, conversation: Conversation) -> None:
        """Test that user messages increment response count."""
        # Arrange
        initial_count = conversation.context.response_count

        # Act
        conversation.add_message(role=MessageRole.USER, content="Test message")

        # Assert
        assert conversation.context.response_count == initial_count + 1

    def test_add_assistant_message_does_not_increment_response_count(
        self, conversation: Conversation
    ) -> None:
        """Test that assistant messages don't increment response count."""
        # Arrange
        initial_count = conversation.context.response_count

        # Act
        conversation.add_message(role=MessageRole.ASSISTANT, content="Response message")

        # Assert
        assert conversation.context.response_count == initial_count

    def test_add_message_updates_timestamp(self, conversation: Conversation) -> None:
        """Test that adding message updates conversation timestamp."""
        # Arrange
        original_timestamp = conversation.updated_at

        # Act
        conversation.add_message(role=MessageRole.USER, content="Test")

        # Assert
        assert conversation.updated_at >= original_timestamp

    def test_add_message_to_completed_conversation_raises_error(
        self, conversation: Conversation
    ) -> None:
        """Test that adding message to completed conversation raises error."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)
        conversation.mark_completed()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot add message to completed"):
            conversation.add_message(role=MessageRole.USER, content="Test")

    def test_add_message_to_paused_conversation_raises_error(
        self, conversation: Conversation
    ) -> None:
        """Test that adding message to paused conversation raises error."""
        # Arrange
        conversation.mark_paused()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot add message to paused"):
            conversation.add_message(role=MessageRole.USER, content="Test")

    def test_add_message_with_metadata(self, conversation: Conversation) -> None:
        """Test adding message with metadata."""
        # Arrange
        metadata = {"source": "web", "timestamp": "2024-01-01"}

        # Act
        conversation.add_message(role=MessageRole.USER, content="Test", metadata=metadata)

        # Assert
        assert conversation.messages[0].metadata == metadata


class TestConversationPhaseTransitions:
    """Test suite for phase transition business rules."""

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing a test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_transition_to_next_phase(self, conversation: Conversation) -> None:
        """Test transitioning to next phase."""
        # Arrange
        assert conversation.context.current_phase == ConversationPhase.INTRODUCTION

        # Act
        conversation.transition_to_phase(ConversationPhase.EXPLORATION)

        # Assert
        assert conversation.context.current_phase == ConversationPhase.EXPLORATION

    def test_transition_updates_progress_percentage(self, conversation: Conversation) -> None:
        """Test that phase transition updates progress."""
        # Arrange & Act
        conversation.transition_to_phase(ConversationPhase.DEEPENING)

        # Assert
        assert conversation.context.progress_percentage == 50.0

    def test_transition_to_same_phase_succeeds(self, conversation: Conversation) -> None:
        """Test that staying in same phase is allowed."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.EXPLORATION)

        # Act
        conversation.transition_to_phase(ConversationPhase.EXPLORATION)

        # Assert
        assert conversation.context.current_phase == ConversationPhase.EXPLORATION

    def test_transition_backward_raises_error(self, conversation: Conversation) -> None:
        """Test that backward phase transition is not allowed."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.DEEPENING)

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot move backward"):
            conversation.transition_to_phase(ConversationPhase.EXPLORATION)

    def test_transition_paused_conversation_raises_error(self, conversation: Conversation) -> None:
        """Test that paused conversations cannot transition."""
        # Arrange
        conversation.mark_paused()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot transition paused"):
            conversation.transition_to_phase(ConversationPhase.EXPLORATION)

    def test_transition_updates_timestamp(self, conversation: Conversation) -> None:
        """Test that phase transition updates timestamp."""
        # Arrange
        original_timestamp = conversation.updated_at

        # Act
        conversation.transition_to_phase(ConversationPhase.EXPLORATION)

        # Assert
        assert conversation.updated_at >= original_timestamp


class TestConversationInsights:
    """Test suite for insight management."""

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing a test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_add_insight(self, conversation: Conversation) -> None:
        """Test adding insight to conversation."""
        # Arrange & Act
        conversation.add_insight("Values autonomy highly")

        # Assert
        assert len(conversation.context.insights) == 1
        assert conversation.context.insights[0] == "Values autonomy highly"

    def test_add_multiple_insights(self, conversation: Conversation) -> None:
        """Test adding multiple insights."""
        # Arrange & Act
        conversation.add_insight("First insight")
        conversation.add_insight("Second insight")

        # Assert
        assert len(conversation.context.insights) == 2

    def test_add_insight_strips_whitespace(self, conversation: Conversation) -> None:
        """Test that insight whitespace is stripped."""
        # Arrange & Act
        conversation.add_insight("  Insight with spaces  ")

        # Assert
        assert conversation.context.insights[0] == "Insight with spaces"

    def test_add_empty_insight_raises_error(self, conversation: Conversation) -> None:
        """Test that empty insight raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Insight cannot be empty"):
            conversation.add_insight("")

    def test_add_whitespace_only_insight_raises_error(self, conversation: Conversation) -> None:
        """Test that whitespace-only insight raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Insight cannot be empty"):
            conversation.add_insight("   ")


class TestConversationStatusTransitions:
    """Test suite for status transition business rules."""

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing a test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_mark_completed_in_validation_phase(self, conversation: Conversation) -> None:
        """Test marking conversation completed in validation phase."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        # Act
        conversation.mark_completed()

        # Assert
        assert conversation.status == ConversationStatus.COMPLETED
        assert conversation.completed_at is not None

    def test_mark_completed_in_completion_phase(self, conversation: Conversation) -> None:
        """Test marking conversation completed in completion phase."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.COMPLETION)

        # Act
        conversation.mark_completed()

        # Assert
        assert conversation.status == ConversationStatus.COMPLETED

    def test_mark_completed_in_early_phase_raises_error(self, conversation: Conversation) -> None:
        """Test that completing early phase conversation raises error."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.EXPLORATION)

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot complete conversation in exploration"):
            conversation.mark_completed()

    def test_mark_paused(self, conversation: Conversation) -> None:
        """Test pausing active conversation."""
        # Arrange & Act
        conversation.mark_paused()

        # Assert
        assert conversation.status == ConversationStatus.PAUSED

    def test_mark_paused_when_already_paused_raises_error(self, conversation: Conversation) -> None:
        """Test that pausing paused conversation raises error."""
        # Arrange
        conversation.mark_paused()

        # Act & Assert
        with pytest.raises(ValueError, match="Cannot pause paused"):
            conversation.mark_paused()

    def test_resume_paused_conversation(self, conversation: Conversation) -> None:
        """Test resuming paused conversation."""
        # Arrange
        conversation.mark_paused()

        # Act
        conversation.resume()

        # Assert
        assert conversation.status == ConversationStatus.ACTIVE

    def test_resume_active_conversation_raises_error(self, conversation: Conversation) -> None:
        """Test that resuming active conversation raises error."""
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="Cannot resume active"):
            conversation.resume()


class TestConversationUtilityMethods:
    """Test suite for utility methods."""

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing a test conversation with messages."""
        conv = Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )
        conv.add_message(role=MessageRole.USER, content="Message 1")
        conv.add_message(role=MessageRole.ASSISTANT, content="Response 1")
        conv.add_message(role=MessageRole.USER, content="Message 2")
        return conv

    def test_is_active_returns_true_for_active(self, conversation: Conversation) -> None:
        """Test is_active returns True for active conversation."""
        # Assert
        assert conversation.is_active() is True

    def test_is_completed_returns_false_for_active(self, conversation: Conversation) -> None:
        """Test is_completed returns False for active conversation."""
        # Assert
        assert conversation.is_completed() is False

    def test_get_message_count(self, conversation: Conversation) -> None:
        """Test getting total message count."""
        # Act
        count = conversation.get_message_count()

        # Assert
        assert count == 3

    def test_get_user_message_count(self, conversation: Conversation) -> None:
        """Test getting user message count."""
        # Act
        count = conversation.get_user_message_count()

        # Assert
        assert count == 2

    def test_get_assistant_message_count(self, conversation: Conversation) -> None:
        """Test getting assistant message count."""
        # Act
        count = conversation.get_assistant_message_count()

        # Assert
        assert count == 1

    def test_calculate_progress_percentage(self, conversation: Conversation) -> None:
        """Test calculating progress percentage."""
        # Act
        conversation.transition_to_phase(ConversationPhase.SYNTHESIS)
        progress = conversation.calculate_progress_percentage()

        # Assert
        assert progress == 70.0

    def test_get_conversation_history(self, conversation: Conversation) -> None:
        """Test getting conversation history."""
        # Act
        history = conversation.get_conversation_history()

        # Assert
        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Message 1"

    def test_get_conversation_history_with_max_messages(self, conversation: Conversation) -> None:
        """Test getting limited conversation history."""
        # Act
        history = conversation.get_conversation_history(max_messages=2)

        # Assert
        assert len(history) == 2
        assert history[0]["content"] == "Response 1"
