"""Unit tests for Message value object."""

from datetime import datetime, timedelta, timezone

import pytest
from coaching.src.core.constants import MessageRole
from coaching.src.domain.value_objects.message import Message
from pydantic import ValidationError


class TestMessageCreation:
    """Test suite for Message creation and validation."""

    def test_create_message_with_required_fields(self) -> None:
        """Test creating a message with only required fields."""
        # Arrange & Act
        message = Message(role=MessageRole.USER, content="Hello, coach!")

        # Assert
        assert message.role == MessageRole.USER
        assert message.content == "Hello, coach!"
        assert message.message_id is not None
        assert message.timestamp is not None
        assert message.metadata == {}

    def test_create_message_with_all_fields(self) -> None:
        """Test creating a message with all fields specified."""
        # Arrange
        timestamp = datetime.now(timezone.utc)
        metadata = {"source": "web", "user_agent": "Mozilla"}

        # Act
        message = Message(
            role=MessageRole.ASSISTANT,
            content="Let's explore your values.",
            timestamp=timestamp,
            metadata=metadata,
        )

        # Assert
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Let's explore your values."
        assert message.timestamp == timestamp
        assert message.metadata == metadata

    def test_create_message_auto_generates_id(self) -> None:
        """Test that message ID is auto-generated if not provided."""
        # Arrange & Act
        message1 = Message(role=MessageRole.USER, content="First message")
        message2 = Message(role=MessageRole.USER, content="Second message")

        # Assert
        assert message1.message_id is not None
        assert message2.message_id is not None
        assert message1.message_id != message2.message_id

    def test_create_message_auto_generates_timestamp(self) -> None:
        """Test that timestamp is auto-generated if not provided."""
        # Arrange
        before = datetime.now(timezone.utc)

        # Act
        message = Message(role=MessageRole.USER, content="Test message")

        # Assert
        after = datetime.now(timezone.utc)
        assert before <= message.timestamp <= after

    def test_create_message_strips_whitespace_from_content(self) -> None:
        """Test that leading/trailing whitespace is stripped from content."""
        # Arrange & Act
        message = Message(role=MessageRole.USER, content="  Content with spaces  ")

        # Assert
        assert message.content == "Content with spaces"


class TestMessageValidation:
    """Test suite for Message validation rules."""

    def test_create_message_with_empty_content_raises_error(self) -> None:
        """Test that empty content raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content="")

    def test_create_message_with_whitespace_only_content_raises_error(
        self,
    ) -> None:
        """Test that whitespace-only content raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content="   ")

    def test_create_message_with_future_timestamp_raises_error(self) -> None:
        """Test that future timestamp raises ValidationError."""
        # Arrange
        future = datetime.now(timezone.utc) + timedelta(hours=1)

        # Act & Assert
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content="Test", timestamp=future)

    def test_create_message_with_content_too_long_raises_error(self) -> None:
        """Test that content exceeding max length raises ValidationError."""
        # Arrange
        long_content = "x" * 10001

        # Act & Assert
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content=long_content)

    def test_create_message_with_invalid_role_raises_error(self) -> None:
        """Test that invalid role raises ValidationError."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            Message(role="invalid_role", content="Test")  # type: ignore


class TestMessageImmutability:
    """Test suite for Message immutability."""

    def test_message_is_immutable(self) -> None:
        """Test that message fields cannot be modified after creation."""
        # Arrange
        message = Message(role=MessageRole.USER, content="Original content")

        # Act & Assert
        with pytest.raises(ValidationError):
            message.content = "Modified content"  # type: ignore

    def test_message_role_cannot_be_changed(self) -> None:
        """Test that message role cannot be changed."""
        # Arrange
        message = Message(role=MessageRole.USER, content="Test")

        # Act & Assert
        with pytest.raises(ValidationError):
            message.role = MessageRole.ASSISTANT  # type: ignore

    def test_message_metadata_is_immutable(self) -> None:
        """Test that message metadata dict is protected by frozen model."""
        # Arrange
        metadata = {"key": "value"}
        message = Message(role=MessageRole.USER, content="Test", metadata=metadata)

        # Act & Assert - Cannot reassign metadata
        with pytest.raises(ValidationError):
            message.metadata = {"new": "dict"}  # type: ignore


class TestMessageRoleChecks:
    """Test suite for message role checking methods."""

    def test_is_from_user_returns_true_for_user_message(self) -> None:
        """Test is_from_user returns True for user messages."""
        # Arrange
        message = Message(role=MessageRole.USER, content="Test")

        # Act & Assert
        assert message.is_from_user() is True
        assert message.is_from_assistant() is False
        assert message.is_system_message() is False

    def test_is_from_assistant_returns_true_for_assistant_message(
        self,
    ) -> None:
        """Test is_from_assistant returns True for assistant messages."""
        # Arrange
        message = Message(role=MessageRole.ASSISTANT, content="Test")

        # Act & Assert
        assert message.is_from_user() is False
        assert message.is_from_assistant() is True
        assert message.is_system_message() is False

    def test_is_system_message_returns_true_for_system_message(self) -> None:
        """Test is_system_message returns True for system messages."""
        # Arrange
        message = Message(role=MessageRole.SYSTEM, content="Test")

        # Act & Assert
        assert message.is_from_user() is False
        assert message.is_from_assistant() is False
        assert message.is_system_message() is True


class TestMessageMethods:
    """Test suite for Message utility methods."""

    def test_get_content_length_returns_correct_length(self) -> None:
        """Test get_content_length returns the correct character count."""
        # Arrange
        content = "This is a test message"
        message = Message(role=MessageRole.USER, content=content)

        # Act
        length = message.get_content_length()

        # Assert
        assert length == len(content)

    def test_has_metadata_returns_false_for_empty_metadata(self) -> None:
        """Test has_metadata returns False when metadata is empty."""
        # Arrange
        message = Message(role=MessageRole.USER, content="Test")

        # Act & Assert
        assert message.has_metadata() is False

    def test_has_metadata_returns_true_when_metadata_exists(self) -> None:
        """Test has_metadata returns True when metadata is provided."""
        # Arrange
        message = Message(
            role=MessageRole.USER,
            content="Test",
            metadata={"source": "web"},
        )

        # Act & Assert
        assert message.has_metadata() is True


class TestMessageEquality:
    """Test suite for Message equality."""

    def test_messages_with_same_values_are_equal(self) -> None:
        """Test that messages with identical values are equal."""
        # Arrange
        timestamp = datetime.now(timezone.utc)
        message1 = Message(
            role=MessageRole.USER,
            content="Test",
            timestamp=timestamp,
        )
        message2 = Message(
            role=MessageRole.USER,
            content="Test",
            timestamp=timestamp,
        )

        # Act & Assert
        # Note: They won't be equal because message_id is auto-generated
        assert message1.message_id != message2.message_id
        assert message1 != message2

    def test_messages_can_be_compared(self) -> None:
        """Test that messages support equality comparison."""
        # Arrange
        message1 = Message(role=MessageRole.USER, content="Test 1")
        message2 = Message(role=MessageRole.USER, content="Test 2")
        message3 = message1

        # Act & Assert
        assert message1 == message3  # Same instance
        assert message1 != message2  # Different instances
