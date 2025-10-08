"""Unit tests for data models."""

from datetime import datetime

import pytest
from coaching.src.core.constants import (
    CoachingTopic,
    ConversationPhase,
    ConversationStatus,
    MessageRole,
)
from coaching.src.models.conversation import Conversation, ConversationContext, Message
from coaching.src.models.requests import InitiateConversationRequest, MessageRequest
from coaching.src.models.responses import ConversationResponse, MessageResponse


class TestConversationModels:
    """Test conversation model classes."""

    def test_message_creation(self) -> None:
        """Test Message model creation."""
        message = Message(
            role=MessageRole.USER,
            content="Test message",
            metadata={"test": "value"}
        )

        assert message.role == MessageRole.USER
        assert message.content == "Test message"
        assert message.metadata == {"test": "value"}
        assert isinstance(message.timestamp, datetime)

    def test_conversation_context_creation(self) -> None:
        """Test ConversationContext model creation."""
        context = ConversationContext(
            phase=ConversationPhase.EXPLORATION,
            identified_values=["growth", "autonomy"],
            key_insights=["Values-driven", "Seeks independence"],
        )

        assert context.phase == ConversationPhase.EXPLORATION
        assert context.identified_values == ["growth", "autonomy"]
        assert context.key_insights == ["Values-driven", "Seeks independence"]
        assert context.response_count == 0

    def test_coaching_session_creation(self) -> None:
        """Test Conversation model creation."""
        conversation = Conversation(
            conversation_id="test-123",
            user_id="user-456",
            topic="core_values"
        )

        assert conversation.conversation_id == "test-123"
        assert conversation.user_id == "user-456"
        assert conversation.topic == "core_values"
        assert conversation.status == ConversationStatus.ACTIVE
        assert len(conversation.messages) == 0
        assert isinstance(conversation.created_at, datetime)

    def test_conversation_add_message(self) -> None:
        """Test adding messages to conversation."""
        conversation = Conversation(
            conversation_id="test-123",
            user_id="user-456",
            topic="core_values"
        )

        # Add user message
        conversation.add_message(MessageRole.USER, "Hello", {"source": "test"})

        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.messages[0].content == "Hello"
        assert conversation.messages[0].metadata == {"source": "test"}
        assert conversation.context.response_count == 1

    def test_conversation_progress_calculation(self) -> None:
        """Test conversation progress calculation."""
        conversation = Conversation(
            conversation_id="test-123",
            user_id="user-456",
            topic="core_values"
        )

        # Initial progress
        assert conversation.calculate_progress() == 0.1  # INTRODUCTION phase

        # Change to exploration phase
        conversation.context.phase = ConversationPhase.EXPLORATION
        assert conversation.calculate_progress() == 0.3

        # Change to completion phase
        conversation.context.phase = ConversationPhase.COMPLETION
        assert conversation.calculate_progress() == 1.0

    def test_conversation_status_changes(self) -> None:
        """Test conversation status management."""
        conversation = Conversation(
            conversation_id="test-123",
            user_id="user-456",
            topic="core_values"
        )

        # Initial state
        assert conversation.is_active()
        assert conversation.completed_at is None

        # Mark completed
        conversation.mark_completed()
        assert conversation.status == ConversationStatus.COMPLETED
        assert not conversation.is_active()
        assert conversation.completed_at is not None

        # Test pause/resume
        conversation.status = ConversationStatus.ACTIVE  # Reset
        conversation.mark_paused()
        assert conversation.status == ConversationStatus.PAUSED
        assert conversation.paused_at is not None

        conversation.resume()
        assert conversation.status == ConversationStatus.ACTIVE


class TestRequestModels:
    """Test request model classes."""

    def test_initiate_conversation_request(self) -> None:
        """Test InitiateConversationRequest validation."""
        request = InitiateConversationRequest(
            user_id="test-user",
            topic=CoachingTopic.CORE_VALUES,
            context={"preference": "detailed"},
            language="en"
        )

        assert request.user_id == "test-user"
        assert request.topic == CoachingTopic.CORE_VALUES
        assert request.context == {"preference": "detailed"}
        assert request.language == "en"

    def test_initiate_conversation_request_validation(self) -> None:
        """Test request validation."""
        # Empty user_id should be rejected
        with pytest.raises(ValueError):
            InitiateConversationRequest(
                user_id="   ",
                topic=CoachingTopic.CORE_VALUES
            )

    def test_message_request(self) -> None:
        """Test MessageRequest validation."""
        request = MessageRequest(
            user_message="I value growth and learning",
            metadata={"session": "1"}
        )

        assert request.user_message == "I value growth and learning"
        assert request.metadata == {"session": "1"}

    def test_message_request_validation(self) -> None:
        """Test message request validation."""
        # Empty message should be rejected
        with pytest.raises(ValueError):
            MessageRequest(user_message="   ")


class TestResponseModels:
    """Test response model classes."""

    def test_conversation_response(self) -> None:
        """Test ConversationResponse model."""
        response = ConversationResponse(
            conversation_id="test-123",
            status=ConversationStatus.ACTIVE,
            current_question="What energizes you?",
            progress=0.3,
            phase=ConversationPhase.EXPLORATION
        )

        assert response.conversation_id == "test-123"
        assert response.status == ConversationStatus.ACTIVE
        assert response.progress == 0.3
        assert response.phase == ConversationPhase.EXPLORATION

    def test_message_response(self) -> None:
        """Test MessageResponse model."""
        response = MessageResponse(
            ai_response="That's interesting! Tell me more.",
            follow_up_question="Can you give an example?",
            insights=["Shows growth orientation"],
            progress=0.4,
            is_complete=False,
            phase=ConversationPhase.EXPLORATION
        )

        assert response.ai_response == "That's interesting! Tell me more."
        assert response.follow_up_question == "Can you give an example?"
        assert response.insights == ["Shows growth orientation"]
        assert response.progress == 0.4
        assert not response.is_complete
        assert response.phase == ConversationPhase.EXPLORATION
