"""Unit tests for conversation domain exceptions."""

import pytest
from coaching.src.core.constants import ConversationPhase, ConversationStatus
from coaching.src.domain.exceptions.conversation_exceptions import (
    ConversationCompletionError,
    ConversationNotActive,
    ConversationNotFound,
    ConversationTTLExpired,
    InvalidMessageContent,
    InvalidPhaseTransition,
)

pytestmark = pytest.mark.unit


class TestConversationNotFound:
    """Tests for ConversationNotFound exception."""

    def test_create_with_conversation_id_only(self) -> None:
        """Test creating exception with just conversation ID."""
        exc = ConversationNotFound(conversation_id="conv-123")

        assert exc.message == "Conversation 'conv-123' not found"
        assert exc.code == "CONVERSATION_NOT_FOUND"
        assert exc.context["conversation_id"] == "conv-123"
        assert "tenant_id" not in exc.context

    def test_create_with_tenant_id(self) -> None:
        """Test creating exception with tenant context."""
        exc = ConversationNotFound(conversation_id="conv-123", tenant_id="tenant-456")

        assert exc.context["conversation_id"] == "conv-123"
        assert exc.context["tenant_id"] == "tenant-456"

    def test_raise_and_catch(self) -> None:
        """Test raising and catching the exception."""
        with pytest.raises(ConversationNotFound) as exc_info:
            raise ConversationNotFound(conversation_id="conv-999")

        exc = exc_info.value
        assert "conv-999" in exc.message


class TestInvalidPhaseTransition:
    """Tests for InvalidPhaseTransition exception."""

    def test_create_with_basic_info(self) -> None:
        """Test creating exception with basic transition info."""
        exc = InvalidPhaseTransition(
            conversation_id="conv-123",
            current_phase=ConversationPhase.INTRODUCTION,
            target_phase=ConversationPhase.COMPLETION,
        )

        assert "introduction" in exc.message.lower()
        assert "completion" in exc.message.lower()
        assert exc.code == "INVALID_PHASE_TRANSITION"
        assert exc.context["current_phase"] == "introduction"
        assert exc.context["target_phase"] == "completion"

    def test_create_with_reason(self) -> None:
        """Test creating exception with specific reason."""
        exc = InvalidPhaseTransition(
            conversation_id="conv-123",
            current_phase=ConversationPhase.EXPLORATION,
            target_phase=ConversationPhase.SYNTHESIS,
            reason="Not enough insights gathered",
        )

        assert "Not enough insights gathered" in exc.message
        assert exc.context["reason"] == "Not enough insights gathered"

    def test_backward_transition_scenario(self) -> None:
        """Test exception for backward phase transition."""
        exc = InvalidPhaseTransition(
            conversation_id="conv-123",
            current_phase=ConversationPhase.DEEPENING,
            target_phase=ConversationPhase.EXPLORATION,
            reason="Backward transitions not allowed",
        )

        assert "deepening" in exc.message.lower()
        assert "exploration" in exc.message.lower()


class TestConversationNotActive:
    """Tests for ConversationNotActive exception."""

    def test_create_for_completed_conversation(self) -> None:
        """Test exception when trying to modify completed conversation."""
        exc = ConversationNotActive(
            conversation_id="conv-123",
            current_status=ConversationStatus.COMPLETED,
            operation="add message",
        )

        assert "add message" in exc.message
        assert "completed" in exc.message.lower()
        assert exc.code == "CONVERSATION_NOT_ACTIVE"
        assert exc.context["current_status"] == "completed"
        assert exc.context["operation"] == "add message"

    def test_create_for_paused_conversation(self) -> None:
        """Test exception when trying to modify paused conversation."""
        exc = ConversationNotActive(
            conversation_id="conv-123",
            current_status=ConversationStatus.PAUSED,
            operation="transition phase",
        )

        assert "paused" in exc.message.lower()
        assert exc.context["current_status"] == "paused"

    def test_create_for_abandoned_conversation(self) -> None:
        """Test exception for abandoned conversation."""
        exc = ConversationNotActive(
            conversation_id="conv-123",
            current_status=ConversationStatus.ABANDONED,
            operation="resume",
        )

        assert exc.context["current_status"] == "abandoned"


class TestInvalidMessageContent:
    """Tests for InvalidMessageContent exception."""

    def test_create_with_single_validation_error(self) -> None:
        """Test exception with single validation error."""
        exc = InvalidMessageContent(
            conversation_id="conv-123",
            validation_errors=["Message too short"],
            content_length=5,
        )

        assert "Message too short" in exc.message
        assert exc.code == "INVALID_MESSAGE_CONTENT"
        assert exc.context["validation_errors"] == ["Message too short"]
        assert exc.context["content_length"] == 5

    def test_create_with_multiple_validation_errors(self) -> None:
        """Test exception with multiple validation errors."""
        errors = ["Message too short", "Contains profanity", "Invalid characters"]
        exc = InvalidMessageContent(
            conversation_id="conv-123", validation_errors=errors, content_length=10
        )

        assert "Message too short" in exc.message
        assert "Contains profanity" in exc.message
        assert len(exc.context["validation_errors"]) == 3

    def test_create_without_content_length(self) -> None:
        """Test exception without content length."""
        exc = InvalidMessageContent(
            conversation_id="conv-123", validation_errors=["Invalid format"]
        )

        assert exc.context["content_length"] == 0


class TestConversationTTLExpired:
    """Tests for ConversationTTLExpired exception."""

    def test_create_with_expiry_time(self) -> None:
        """Test creating exception with expiry timestamp."""
        exc = ConversationTTLExpired(conversation_id="conv-123", expired_at="2025-10-09T10:00:00Z")

        assert "2025-10-09T10:00:00Z" in exc.message
        assert exc.code == "CONVERSATION_TTL_EXPIRED"
        assert exc.context["conversation_id"] == "conv-123"
        assert exc.context["expired_at"] == "2025-10-09T10:00:00Z"

    def test_message_includes_expiry_time(self) -> None:
        """Test that message clearly states when conversation expired."""
        expired_time = "2025-10-01T00:00:00Z"
        exc = ConversationTTLExpired(conversation_id="conv-456", expired_at=expired_time)

        assert "expired" in exc.message.lower()
        assert expired_time in exc.message


class TestConversationCompletionError:
    """Tests for ConversationCompletionError exception."""

    def test_create_with_single_missing_requirement(self) -> None:
        """Test exception with single missing requirement."""
        exc = ConversationCompletionError(
            conversation_id="conv-123",
            missing_requirements=["Not in completion phase"],
            progress=75.0,
        )

        assert "Not in completion phase" in exc.message
        assert exc.code == "CONVERSATION_COMPLETION_ERROR"
        assert exc.context["progress_percentage"] == 75.0

    def test_create_with_multiple_missing_requirements(self) -> None:
        """Test exception with multiple missing requirements."""
        missing = [
            "Minimum 10 messages required",
            "Minimum 5 insights required",
            "Must be in validation phase",
        ]
        exc = ConversationCompletionError(
            conversation_id="conv-123", missing_requirements=missing, progress=50.0
        )

        assert "Minimum 10 messages required" in exc.message
        assert len(exc.context["missing_requirements"]) == 3
        assert exc.context["progress_percentage"] == 50.0

    def test_create_without_progress(self) -> None:
        """Test exception without progress percentage."""
        exc = ConversationCompletionError(
            conversation_id="conv-123", missing_requirements=["Not ready"]
        )

        assert exc.context["progress_percentage"] == 0.0
