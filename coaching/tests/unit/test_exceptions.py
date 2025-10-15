"""Unit tests for custom exceptions."""

import pytest
from coaching.src.core.exceptions import (
    ConversationNotFoundError,
    ConversationNotFoundCompatError,
    InvalidTopicError,
    InvalidPhaseTransitionError,
)


@pytest.mark.unit
class TestConversationNotFoundError:
    """Test ConversationNotFoundError exception."""

    def test_exception_message(self):
        """Test exception message formatting."""
        # Arrange
        conversation_id = "conv-123"

        # Act
        error = ConversationNotFoundError(conversation_id)

        # Assert
        assert conversation_id in str(error)
        assert "not found" in str(error).lower()

    def test_exception_can_be_raised(self):
        """Test that exception can be raised and caught."""
        # Arrange
        conversation_id = "conv-456"

        # Act & Assert
        with pytest.raises(ConversationNotFoundError) as exc_info:
            raise ConversationNotFoundError(conversation_id)
        
        assert conversation_id in str(exc_info.value)

    def test_exception_inherits_from_exception(self):
        """Test that custom exception inherits from Exception."""
        # Arrange & Act
        error = ConversationNotFoundError("test")

        # Assert
        assert isinstance(error, Exception)


@pytest.mark.unit
class TestConversationNotFoundCompatError:
    """Test ConversationNotFoundCompatError exception."""

    def test_compat_exception_message(self):
        """Test compat exception message formatting."""
        # Arrange
        conversation_id = "conv-789"

        # Act
        error = ConversationNotFoundCompatError(conversation_id)

        # Assert
        assert conversation_id in str(error)

    def test_compat_exception_can_be_raised(self):
        """Test that compat exception can be raised."""
        # Arrange
        conversation_id = "conv-compat"

        # Act & Assert
        with pytest.raises(ConversationNotFoundCompatError):
            raise ConversationNotFoundCompatError(conversation_id)


@pytest.mark.unit
class TestInvalidTopicError:
    """Test InvalidTopicError exception."""

    def test_invalid_topic_error_message(self):
        """Test invalid topic error message."""
        # Arrange
        topic = "invalid_topic"

        # Act
        error = InvalidTopicError(topic)

        # Assert
        assert topic in str(error)
        assert "invalid" in str(error).lower() or "topic" in str(error).lower()

    def test_invalid_topic_error_can_be_raised(self):
        """Test that invalid topic error can be raised."""
        # Arrange
        topic = "bad_topic"

        # Act & Assert
        with pytest.raises(InvalidTopicError):
            raise InvalidTopicError(topic)


@pytest.mark.unit
class TestInvalidPhaseTransitionError:
    """Test InvalidPhaseTransitionError exception."""

    def test_invalid_phase_transition_message(self):
        """Test invalid phase transition error message."""
        # Arrange
        from_phase = "introduction"
        to_phase = "completion"

        # Act
        error = InvalidPhaseTransitionError(from_phase, to_phase)

        # Assert
        error_str = str(error)
        assert from_phase in error_str
        assert to_phase in error_str

    def test_invalid_phase_transition_can_be_raised(self):
        """Test that phase transition error can be raised."""
        # Arrange
        from_phase = "exploration"
        to_phase = "introduction"

        # Act & Assert
        with pytest.raises(InvalidPhaseTransitionError):
            raise InvalidPhaseTransitionError(from_phase, to_phase)


@pytest.mark.unit
class TestExceptionHierarchy:
    """Test exception hierarchy and relationships."""

    def test_all_exceptions_inherit_from_exception(self):
        """Test that all custom exceptions inherit from Exception."""
        # Act & Assert
        assert issubclass(ConversationNotFoundError, Exception)
        assert issubclass(ConversationNotFoundCompatError, Exception)
        assert issubclass(InvalidTopicError, Exception)
        assert issubclass(InvalidPhaseTransitionError, Exception)

    def test_exceptions_can_be_caught_as_exception(self):
        """Test that custom exceptions can be caught as generic Exception."""
        # Arrange & Act & Assert
        with pytest.raises(Exception):
            raise ConversationNotFoundError("test")
        
        with pytest.raises(Exception):
            raise InvalidTopicError("test")
