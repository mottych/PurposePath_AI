"""Unit tests for CompletionValidator domain service."""

import pytest
from coaching.src.core.constants import CoachingTopic, ConversationPhase, MessageRole
from coaching.src.core.types import (
    create_conversation_id,
    create_tenant_id,
    create_user_id,
)
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.services.completion_validator import CompletionValidator


class TestCompletionValidatorBasics:
    """Test suite for basic completion validation."""

    @pytest.fixture
    def validator(self) -> CompletionValidator:
        """Fixture providing validator instance."""
        return CompletionValidator()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_cannot_complete_early_phase_conversation(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test that conversations in early phases cannot complete."""
        # Act
        can_complete = validator.can_complete(conversation)

        # Assert
        assert can_complete is False

    def test_cannot_complete_paused_conversation(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test that paused conversations cannot complete."""
        # Arrange
        conversation.mark_paused()

        # Act
        can_complete = validator.can_complete(conversation)

        # Assert
        assert can_complete is False

    def test_can_complete_with_all_requirements_met(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test completion with all requirements met."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        # Add messages
        for i in range(5):
            conversation.add_message(role=MessageRole.USER, content=f"User message {i}")
            conversation.add_message(role=MessageRole.ASSISTANT, content=f"Assistant response {i}")

        # Add insights
        for i in range(8):
            conversation.add_insight(f"Insight {i}")

        # Act
        can_complete = validator.can_complete(conversation)

        # Assert
        assert can_complete is True


class TestCompletionValidatorDetailed:
    """Test suite for detailed validation feedback."""

    @pytest.fixture
    def validator(self) -> CompletionValidator:
        """Fixture providing validator instance."""
        return CompletionValidator()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_validate_completion_returns_reasons_for_failure(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test that validation provides specific failure reasons."""
        # Act
        is_valid, reasons = validator.validate_completion(conversation)

        # Assert
        assert is_valid is False
        assert len(reasons) > 0
        assert any("phase" in reason.lower() for reason in reasons)

    def test_validate_completion_identifies_missing_messages(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test that validation identifies insufficient messages."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        # Act
        is_valid, reasons = validator.validate_completion(conversation)

        # Assert
        assert is_valid is False
        assert any("messages" in reason for reason in reasons)

    def test_validate_completion_identifies_missing_insights(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test that validation identifies insufficient insights."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        # Add enough messages
        for i in range(10):
            conversation.add_message(role=MessageRole.USER, content=f"Message {i}")

        # Act
        is_valid, reasons = validator.validate_completion(conversation)

        # Assert
        assert is_valid is False
        assert any("insights" in reason.lower() for reason in reasons)

    def test_validate_completion_success_returns_empty_reasons(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test that successful validation returns empty reasons."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        for i in range(5):
            conversation.add_message(role=MessageRole.USER, content=f"User message {i}")
            conversation.add_message(role=MessageRole.ASSISTANT, content=f"Assistant response {i}")

        for i in range(8):
            conversation.add_insight(f"Insight {i}")

        # Act
        is_valid, reasons = validator.validate_completion(conversation)

        # Assert
        assert is_valid is True
        assert len(reasons) == 0


class TestCompletionValidatorProgress:
    """Test suite for completion progress calculations."""

    @pytest.fixture
    def validator(self) -> CompletionValidator:
        """Fixture providing validator instance."""
        return CompletionValidator()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_get_completion_progress_at_zero(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test progress calculation with no criteria met."""
        # Act
        progress = validator.get_completion_progress(conversation)

        # Assert
        assert progress == 0.0

    def test_get_completion_progress_partial(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test progress calculation with some criteria met."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        # Act
        progress = validator.get_completion_progress(conversation)

        # Assert
        assert 0 < progress < 100

    def test_get_completion_progress_at_full(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test progress calculation with all criteria met."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        for i in range(5):
            conversation.add_message(role=MessageRole.USER, content=f"User message {i}")
            conversation.add_message(role=MessageRole.ASSISTANT, content=f"Assistant response {i}")

        for i in range(8):
            conversation.add_insight(f"Insight {i}")

        # Act
        progress = validator.get_completion_progress(conversation)

        # Assert
        assert progress == 100.0


class TestCompletionValidatorRequirements:
    """Test suite for specific requirement checks."""

    @pytest.fixture
    def validator(self) -> CompletionValidator:
        """Fixture providing validator instance."""
        return CompletionValidator()

    @pytest.fixture
    def conversation(self) -> Conversation:
        """Fixture providing test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic=CoachingTopic.CORE_VALUES,
        )

    def test_validates_minimum_total_messages(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test validation of minimum total messages."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        for i in range(4):  # Less than minimum
            conversation.add_message(role=MessageRole.USER, content=f"Message {i}")

        # Act
        is_valid, reasons = validator.validate_completion(conversation)

        # Assert
        assert is_valid is False
        assert any("10 total messages" in reason for reason in reasons)

    def test_validates_minimum_user_responses(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test validation of minimum user responses."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        # Add mostly assistant messages
        for i in range(10):
            conversation.add_message(role=MessageRole.ASSISTANT, content=f"Message {i}")

        # Act
        is_valid, reasons = validator.validate_completion(conversation)

        # Assert
        assert is_valid is False
        assert any("user responses" in reason.lower() for reason in reasons)

    def test_validates_minimum_assistant_messages(
        self, validator: CompletionValidator, conversation: Conversation
    ) -> None:
        """Test validation of minimum assistant messages."""
        # Arrange
        conversation.transition_to_phase(ConversationPhase.VALIDATION)

        # Add mostly user messages
        for i in range(10):
            conversation.add_message(role=MessageRole.USER, content=f"Message {i}")

        for i in range(8):
            conversation.add_insight(f"Insight {i}")

        # Act
        is_valid, reasons = validator.validate_completion(conversation)

        # Assert
        assert is_valid is False
        assert any("assistant messages" in reason.lower() for reason in reasons)
