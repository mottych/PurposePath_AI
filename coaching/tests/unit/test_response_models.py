"""Unit tests for response models."""

from datetime import datetime

import pytest
from coaching.src.core.constants import ConversationPhase, ConversationStatus
from coaching.src.models.responses import (
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
    MessageResponse,
)


@pytest.mark.unit
class TestConversationResponse:
    """Test ConversationResponse model."""

    def test_valid_conversation_response(self):
        """Test creating valid conversation response."""
        # Arrange & Act
        response = ConversationResponse(
            conversation_id="conv-123",
            status=ConversationStatus.ACTIVE,
            current_question="How can I help you?",
            progress=0.25,
            phase=ConversationPhase.INTRODUCTION,
        )

        # Assert
        assert response.conversation_id == "conv-123"
        assert response.status == ConversationStatus.ACTIVE
        assert response.current_question == "How can I help you?"
        assert response.progress == 0.25
        assert response.phase == ConversationPhase.INTRODUCTION

    def test_conversation_response_with_metadata(self):
        """Test conversation response with optional metadata."""
        # Arrange & Act
        response = ConversationResponse(
            conversation_id="conv-456",
            status=ConversationStatus.PAUSED,
            current_question="Let's continue...",
            progress=0.50,
            phase=ConversationPhase.DEEPENING,
        )

        # Assert
        assert response.progress == 0.50
        assert response.status == ConversationStatus.PAUSED


@pytest.mark.unit
class TestMessageResponse:
    """Test MessageResponse model."""

    def test_valid_message_response(self):
        """Test creating valid message response."""
        # Arrange & Act
        response = MessageResponse(
            ai_response="Here's my coaching advice...",
            follow_up_question="What would you like to explore next?",
            insights=["Insight 1", "Insight 2"],
            progress=0.60,
            is_complete=False,
            phase=ConversationPhase.SYNTHESIS,
        )

        # Assert
        assert response.ai_response == "Here's my coaching advice..."
        assert response.follow_up_question == "What would you like to explore next?"
        assert len(response.insights) == 2
        assert response.progress == 0.60
        assert response.is_complete is False
        assert response.phase == ConversationPhase.SYNTHESIS

    def test_message_response_minimal(self):
        """Test message response with minimal fields."""
        # Arrange & Act
        response = MessageResponse(
            ai_response="Short response",
            progress=0.10,
            phase=ConversationPhase.INTRODUCTION,
        )

        # Assert
        assert response.ai_response == "Short response"
        assert response.follow_up_question is None
        assert response.insights is None
        assert response.is_complete is False

    def test_message_response_completed(self):
        """Test message response for completed conversation."""
        # Arrange & Act
        response = MessageResponse(
            ai_response="Great work! We're done.",
            next_steps=["Review your values", "Create action plan"],
            identified_values=["Integrity", "Growth", "Innovation"],
            progress=1.0,
            is_complete=True,
            phase=ConversationPhase.COMPLETION,
        )

        # Assert
        assert response.is_complete is True
        assert response.progress == 1.0
        assert len(response.next_steps) == 2
        assert len(response.identified_values) == 3


@pytest.mark.unit
class TestConversationSummary:
    """Test ConversationSummary model."""

    def test_valid_conversation_summary(self):
        """Test creating valid conversation summary."""
        # Arrange
        now = datetime.now()

        # Act
        summary = ConversationSummary(
            conversation_id="conv-789",
            topic="strategy",
            status=ConversationStatus.ACTIVE,
            progress=0.40,
            created_at=now,
            updated_at=now,
            message_count=5,
        )

        # Assert
        assert summary.conversation_id == "conv-789"
        assert summary.topic == "strategy"
        assert summary.status == ConversationStatus.ACTIVE
        assert summary.progress == 0.40
        assert summary.message_count == 5
        assert summary.created_at == now

    def test_conversation_summary_with_different_statuses(self):
        """Test summaries with different statuses."""
        # Arrange
        now = datetime.now()

        # Act & Assert
        for status in ConversationStatus:
            summary = ConversationSummary(
                conversation_id=f"conv-{status.value}",
                topic="test",
                status=status,
                progress=0,
                created_at=now,
                updated_at=now,
                message_count=0,
            )
            assert summary.status == status


@pytest.mark.unit
class TestConversationListResponse:
    """Test ConversationListResponse model."""

    def test_valid_list_response(self):
        """Test creating valid list response."""
        # Arrange
        now = datetime.now()
        summaries = [
            ConversationSummary(
                conversation_id="conv-1",
                topic="strategy",
                status=ConversationStatus.ACTIVE,
                progress=50,
                created_at=now,
                updated_at=now,
                message_count=3,
            ),
            ConversationSummary(
                conversation_id="conv-2",
                topic="leadership",
                status=ConversationStatus.COMPLETED,
                progress=100,
                created_at=now,
                updated_at=now,
                message_count=10,
            ),
        ]

        # Act
        list_response = ConversationListResponse(
            conversations=summaries,
            total=2,
            page=1,
            page_size=20,
        )

        # Assert
        assert len(list_response.conversations) == 2
        assert list_response.total == 2
        assert list_response.page == 1

    def test_empty_list_response(self):
        """Test list response with no conversations."""
        # Arrange & Act
        list_response = ConversationListResponse(
            conversations=[],
            total=0,
            page=1,
        )

        # Assert
        assert len(list_response.conversations) == 0
        assert list_response.total == 0

    def test_list_response_pagination(self):
        """Test list response with different pagination."""
        # Arrange & Act
        list_response = ConversationListResponse(
            conversations=[],
            total=100,
            page=5,
        )

        # Assert
        assert list_response.page == 5
        assert list_response.total == 100
