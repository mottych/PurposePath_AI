"""Integration tests for conversation API routes (Phase 7).

Tests the refactored conversation routes using new architecture with
application services, domain entities, and auth-based context.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.api.main_v2 import app
from coaching.src.core.constants import CoachingTopic, ConversationPhase, ConversationStatus
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.value_objects.conversation_context import ConversationContext
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_conversation():
    """Create mock conversation entity."""
    conversation = Conversation.create(
        user_id=UserId("user_test"),
        tenant_id=TenantId("tenant_test"),
        topic=CoachingTopic.CORE_VALUES,
        metadata={},
    )
    # Add initial message
    from coaching.src.core.constants import MessageRole

    conversation.add_message(
        role=MessageRole.ASSISTANT,
        content="Welcome! Let's explore your core values.",
    )
    return conversation


class TestConversationInitiation:
    """Test conversation initiation endpoint."""

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    @patch("coaching.src.api.routes.conversations_v2.get_llm_service_v2")
    def test_initiate_conversation_success(
        self, mock_llm_service_dep, mock_conv_service_dep, client, mock_conversation
    ):
        """Test successful conversation initiation."""
        # Setup mocks
        mock_conv_service = AsyncMock()
        mock_conv_service.start_conversation = AsyncMock(return_value=mock_conversation)
        mock_conv_service_dep.return_value = mock_conv_service

        mock_llm_service = AsyncMock()
        mock_llm_service_dep.return_value = mock_llm_service

        # Make request
        response = client.post(
            "/api/v1/conversations/initiate",
            json={
                "topic": "core_values",
                "context": {},
                "language": "en",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 201
        data = response.json()
        assert data["conversation_id"] == mock_conversation.conversation_id
        assert data["topic"] == "core_values"
        assert data["status"] == ConversationStatus.ACTIVE.value
        assert "initial_message" in data

    def test_initiate_conversation_no_auth(self, client):
        """Test conversation initiation without authentication."""
        response = client.post(
            "/api/v1/conversations/initiate",
            json={
                "topic": "core_values",
            },
        )

        # Should fail with 401 or 422 (missing auth header)
        assert response.status_code in [401, 422]

    def test_initiate_conversation_invalid_topic(self, client):
        """Test conversation initiation with invalid topic."""
        response = client.post(
            "/api/v1/conversations/initiate",
            json={
                "topic": "invalid_topic",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Should fail with validation error
        assert response.status_code == 422


class TestMessageSending:
    """Test message sending endpoint."""

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    @patch("coaching.src.api.routes.conversations_v2.get_llm_service_v2")
    def test_send_message_success(
        self, mock_llm_service_dep, mock_conv_service_dep, client, mock_conversation
    ):
        """Test successful message sending."""
        # Add user message to conversation
        from coaching.src.core.constants import MessageRole

        mock_conversation.add_message(
            role=MessageRole.USER,
            content="I value honesty and transparency",
        )

        # Setup mocks
        mock_conv_service = AsyncMock()
        mock_conv_service.add_message = AsyncMock(return_value=mock_conversation)
        mock_conv_service.complete_conversation = AsyncMock(return_value=mock_conversation)
        mock_conv_service_dep.return_value = mock_conv_service

        from coaching.src.domain.ports.llm_provider_port import LLMResponse

        mock_llm_response = LLMResponse(
            content="That's wonderful! Honesty is a powerful core value.",
            model="test-model",
            usage={"total_tokens": 50},
            provider="test",
            finish_reason="stop",
        )
        mock_llm_service = AsyncMock()
        mock_llm_service.generate_response = AsyncMock(return_value=mock_llm_response)
        mock_llm_service_dep.return_value = mock_llm_service

        # Make request
        response = client.post(
            f"/api/v1/conversations/{mock_conversation.conversation_id}/message",
            json={
                "user_message": "I value honesty and transparency",
                "metadata": {},
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == mock_conversation.conversation_id
        assert "ai_response" in data
        assert "progress" in data

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    def test_send_message_conversation_not_found(self, mock_conv_service_dep, client):
        """Test message sending to non-existent conversation."""
        from coaching.src.domain.exceptions.conversation_exceptions import (
            ConversationNotFound,
        )

        # Setup mock to raise exception
        mock_conv_service = AsyncMock()
        mock_conv_service.add_message = AsyncMock(
            side_effect=ConversationNotFound(
                ConversationId("nonexistent"),
                TenantId("tenant_test"),
            )
        )
        mock_conv_service_dep.return_value = mock_conv_service

        # Make request
        response = client.post(
            "/api/v1/conversations/nonexistent/message",
            json={
                "user_message": "Test message",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 404
        assert response.status_code == 404


class TestConversationRetrieval:
    """Test conversation retrieval endpoint."""

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    def test_get_conversation_success(self, mock_conv_service_dep, client, mock_conversation):
        """Test successful conversation retrieval."""
        # Setup mock
        mock_conv_service = AsyncMock()
        mock_conv_service.get_conversation = AsyncMock(return_value=mock_conversation)
        mock_conv_service_dep.return_value = mock_conv_service

        # Make request
        response = client.get(
            f"/api/v1/conversations/{mock_conversation.conversation_id}",
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == mock_conversation.conversation_id
        assert "messages" in data
        assert isinstance(data["messages"], list)

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    def test_get_conversation_not_found(self, mock_conv_service_dep, client):
        """Test conversation retrieval when not found."""
        from coaching.src.domain.exceptions.conversation_exceptions import (
            ConversationNotFound,
        )

        # Setup mock to raise exception
        mock_conv_service = AsyncMock()
        mock_conv_service.get_conversation = AsyncMock(
            side_effect=ConversationNotFound(
                ConversationId("nonexistent"),
                TenantId("tenant_test"),
            )
        )
        mock_conv_service_dep.return_value = mock_conv_service

        # Make request
        response = client.get(
            "/api/v1/conversations/nonexistent",
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 404
        assert response.status_code == 404


class TestConversationListing:
    """Test conversation listing endpoint."""

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    def test_list_conversations_success(self, mock_conv_service_dep, client, mock_conversation):
        """Test successful conversation listing."""
        # Setup mock
        mock_conv_service = AsyncMock()
        mock_conv_service.list_user_conversations = AsyncMock(return_value=[mock_conversation])
        mock_conv_service_dep.return_value = mock_conv_service

        # Make request
        response = client.get(
            "/api/v1/conversations/",
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)
        assert data["total"] >= 0

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    def test_list_conversations_with_pagination(
        self, mock_conv_service_dep, client, mock_conversation
    ):
        """Test conversation listing with pagination."""
        # Setup mock
        mock_conv_service = AsyncMock()
        mock_conv_service.list_user_conversations = AsyncMock(return_value=[mock_conversation])
        mock_conv_service_dep.return_value = mock_conv_service

        # Make request with pagination
        response = client.get(
            "/api/v1/conversations/?page=1&page_size=10",
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestConversationActions:
    """Test conversation action endpoints (pause, complete)."""

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    def test_pause_conversation_success(self, mock_conv_service_dep, client, mock_conversation):
        """Test successful conversation pausing."""
        # Setup mock
        mock_conv_service = AsyncMock()
        mock_conv_service.pause_conversation = AsyncMock(return_value=mock_conversation)
        mock_conv_service_dep.return_value = mock_conv_service

        # Make request
        response = client.post(
            f"/api/v1/conversations/{mock_conversation.conversation_id}/pause",
            json={"reason": "Taking a break"},
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 204 No Content
        assert response.status_code == 204

    @patch("coaching.src.api.routes.conversations_v2.get_conversation_service_v2")
    def test_complete_conversation_success(self, mock_conv_service_dep, client, mock_conversation):
        """Test successful conversation completion."""
        # Setup mock
        mock_conv_service = AsyncMock()
        mock_conv_service.complete_conversation = AsyncMock(return_value=mock_conversation)
        mock_conv_service_dep.return_value = mock_conv_service

        # Make request
        response = client.post(
            f"/api/v1/conversations/{mock_conversation.conversation_id}/complete",
            json={"feedback": "Great session!", "rating": 5},
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 204 No Content
        assert response.status_code == 204
