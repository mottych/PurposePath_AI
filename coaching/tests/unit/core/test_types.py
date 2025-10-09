"""Unit tests for core type system.

Tests domain ID types and factory functions to ensure type safety
and proper ID generation.
"""

from uuid import UUID

import pytest
from coaching.src.core.types import (
    create_analysis_request_id,
    create_conversation_id,
    create_message_id,
    create_session_id,
    create_template_id,
    create_tenant_id,
    create_user_id,
)


class TestConversationId:
    """Test suite for ConversationId type."""

    def test_create_conversation_id_generates_unique_ids(self) -> None:
        """Test that create_conversation_id generates unique IDs."""
        # Arrange & Act
        id1 = create_conversation_id()
        id2 = create_conversation_id()

        # Assert
        assert id1 != id2
        assert isinstance(id1, str)
        assert isinstance(id2, str)

    def test_create_conversation_id_has_correct_prefix(self) -> None:
        """Test that conversation IDs have the 'conv_' prefix."""
        # Arrange & Act
        conv_id = create_conversation_id()

        # Assert
        assert conv_id.startswith("conv_")

    def test_create_conversation_id_contains_valid_uuid(self) -> None:
        """Test that conversation ID contains a valid UUID."""
        # Arrange & Act
        conv_id = create_conversation_id()
        uuid_part = conv_id.split("conv_")[1]

        # Assert
        try:
            UUID(uuid_part)
            assert True
        except ValueError:
            pytest.fail("Conversation ID does not contain a valid UUID")

    def test_conversation_id_is_string_at_runtime(self) -> None:
        """Test that ConversationId behaves as string at runtime."""
        # Arrange & Act
        conv_id = create_conversation_id()

        # Assert
        assert isinstance(conv_id, str)
        assert len(conv_id) > 5  # At least "conv_" + some UUID


class TestTemplateId:
    """Test suite for TemplateId type."""

    def test_create_template_id_generates_unique_ids(self) -> None:
        """Test that create_template_id generates unique IDs."""
        # Arrange & Act
        id1 = create_template_id()
        id2 = create_template_id()

        # Assert
        assert id1 != id2

    def test_create_template_id_has_correct_prefix(self) -> None:
        """Test that template IDs have the 'tmpl_' prefix."""
        # Arrange & Act
        template_id = create_template_id()

        # Assert
        assert template_id.startswith("tmpl_")

    def test_create_template_id_contains_valid_uuid(self) -> None:
        """Test that template ID contains a valid UUID."""
        # Arrange & Act
        template_id = create_template_id()
        uuid_part = template_id.split("tmpl_")[1]

        # Assert
        UUID(uuid_part)  # Will raise ValueError if invalid


class TestAnalysisRequestId:
    """Test suite for AnalysisRequestId type."""

    def test_create_analysis_request_id_generates_unique_ids(self) -> None:
        """Test that create_analysis_request_id generates unique IDs."""
        # Arrange & Act
        id1 = create_analysis_request_id()
        id2 = create_analysis_request_id()

        # Assert
        assert id1 != id2

    def test_create_analysis_request_id_has_correct_prefix(self) -> None:
        """Test that analysis request IDs have the 'anls_' prefix."""
        # Arrange & Act
        analysis_id = create_analysis_request_id()

        # Assert
        assert analysis_id.startswith("anls_")

    def test_create_analysis_request_id_contains_valid_uuid(self) -> None:
        """Test that analysis request ID contains a valid UUID."""
        # Arrange & Act
        analysis_id = create_analysis_request_id()
        uuid_part = analysis_id.split("anls_")[1]

        # Assert
        UUID(uuid_part)  # Will raise ValueError if invalid


class TestUserId:
    """Test suite for UserId type."""

    def test_create_user_id_with_valid_string(self) -> None:
        """Test creating a user ID from a valid string."""
        # Arrange
        raw_id = "user_12345"

        # Act
        user_id = create_user_id(raw_id)

        # Assert
        assert user_id == raw_id
        assert isinstance(user_id, str)

    def test_create_user_id_preserves_input(self) -> None:
        """Test that create_user_id preserves the input string."""
        # Arrange
        raw_id = "custom_user_identifier_456"

        # Act
        user_id = create_user_id(raw_id)

        # Assert
        assert user_id == raw_id

    def test_create_user_id_with_empty_string(self) -> None:
        """Test creating a user ID with an empty string."""
        # Arrange
        raw_id = ""

        # Act
        user_id = create_user_id(raw_id)

        # Assert
        assert user_id == ""


class TestTenantId:
    """Test suite for TenantId type."""

    def test_create_tenant_id_with_valid_string(self) -> None:
        """Test creating a tenant ID from a valid string."""
        # Arrange
        raw_id = "tenant_789"

        # Act
        tenant_id = create_tenant_id(raw_id)

        # Assert
        assert tenant_id == raw_id
        assert isinstance(tenant_id, str)

    def test_create_tenant_id_preserves_input(self) -> None:
        """Test that create_tenant_id preserves the input string."""
        # Arrange
        raw_id = "org_xyz_123"

        # Act
        tenant_id = create_tenant_id(raw_id)

        # Assert
        assert tenant_id == raw_id


class TestMessageId:
    """Test suite for MessageId type."""

    def test_create_message_id_generates_unique_ids(self) -> None:
        """Test that create_message_id generates unique IDs."""
        # Arrange & Act
        id1 = create_message_id()
        id2 = create_message_id()

        # Assert
        assert id1 != id2

    def test_create_message_id_has_correct_prefix(self) -> None:
        """Test that message IDs have the 'msg_' prefix."""
        # Arrange & Act
        message_id = create_message_id()

        # Assert
        assert message_id.startswith("msg_")

    def test_create_message_id_contains_valid_uuid(self) -> None:
        """Test that message ID contains a valid UUID."""
        # Arrange & Act
        message_id = create_message_id()
        uuid_part = message_id.split("msg_")[1]

        # Assert
        UUID(uuid_part)  # Will raise ValueError if invalid


class TestSessionId:
    """Test suite for SessionId type."""

    def test_create_session_id_generates_unique_ids(self) -> None:
        """Test that create_session_id generates unique IDs."""
        # Arrange & Act
        id1 = create_session_id()
        id2 = create_session_id()

        # Assert
        assert id1 != id2

    def test_create_session_id_has_correct_prefix(self) -> None:
        """Test that session IDs have the 'sess_' prefix."""
        # Arrange & Act
        session_id = create_session_id()

        # Assert
        assert session_id.startswith("sess_")

    def test_create_session_id_contains_valid_uuid(self) -> None:
        """Test that session ID contains a valid UUID."""
        # Arrange & Act
        session_id = create_session_id()
        uuid_part = session_id.split("sess_")[1]

        # Assert
        UUID(uuid_part)  # Will raise ValueError if invalid


class TestTypeSafety:
    """Test suite for type safety across all ID types."""

    def test_all_id_types_are_strings_at_runtime(self) -> None:
        """Test that all ID types behave as strings at runtime."""
        # Arrange & Act
        conv_id = create_conversation_id()
        template_id = create_template_id()
        analysis_id = create_analysis_request_id()
        user_id = create_user_id("user_1")
        tenant_id = create_tenant_id("tenant_1")
        message_id = create_message_id()
        session_id = create_session_id()

        # Assert
        assert isinstance(conv_id, str)
        assert isinstance(template_id, str)
        assert isinstance(analysis_id, str)
        assert isinstance(user_id, str)
        assert isinstance(tenant_id, str)
        assert isinstance(message_id, str)
        assert isinstance(session_id, str)

    def test_id_types_can_be_used_in_string_operations(self) -> None:
        """Test that ID types support string operations."""
        # Arrange
        conv_id = create_conversation_id()

        # Act & Assert
        assert len(conv_id) > 0
        assert conv_id.upper() == conv_id.upper()
        assert conv_id in [conv_id]  # Can be used in collections
        assert conv_id.startswith("conv_")
        assert "_" in conv_id

    def test_id_uniqueness_across_multiple_calls(self) -> None:
        """Test that generating many IDs produces unique values."""
        # Arrange & Act
        conv_ids = {create_conversation_id() for _ in range(100)}
        template_ids = {create_template_id() for _ in range(100)}

        # Assert
        assert len(conv_ids) == 100  # All unique
        assert len(template_ids) == 100  # All unique

    def test_id_types_can_be_compared(self) -> None:
        """Test that ID types support comparison operations."""
        # Arrange
        id1 = create_conversation_id()
        id2 = create_conversation_id()
        id3 = id1

        # Act & Assert
        assert id1 == id3
        assert id1 != id2
        assert (id1 < id2) or (id1 > id2)  # One must be true

    def test_id_types_can_be_hashed(self) -> None:
        """Test that ID types can be used as dictionary keys."""
        # Arrange
        conv_id = create_conversation_id()
        test_dict = {conv_id: "test_value"}

        # Act & Assert
        assert test_dict[conv_id] == "test_value"
        assert conv_id in test_dict

    def test_user_id_with_special_characters(self) -> None:
        """Test user ID creation with various formats."""
        # Arrange & Act
        id_with_dash = create_user_id("user-123-abc")
        id_with_underscore = create_user_id("user_123_abc")
        id_with_mixed = create_user_id("org#user@123")

        # Assert
        assert id_with_dash == "user-123-abc"
        assert id_with_underscore == "user_123_abc"
        assert id_with_mixed == "org#user@123"

    def test_tenant_id_with_special_characters(self) -> None:
        """Test tenant ID creation with various formats."""
        # Arrange & Act
        id_with_dash = create_tenant_id("tenant-xyz-789")
        id_with_underscore = create_tenant_id("org_name_123")

        # Assert
        assert id_with_dash == "tenant-xyz-789"
        assert id_with_underscore == "org_name_123"
