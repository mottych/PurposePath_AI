"""Integration tests for conversation API routes (Phase 7).

Tests the refactored conversation routes using new architecture with
application services, domain entities, and auth-based context.
"""

from unittest.mock import AsyncMock

import pytest
from coaching.src.api.dependencies import get_conversation_service
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.main import app
from coaching.src.core.constants import CoachingTopic, ConversationStatus
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from fastapi.testclient import TestClient


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


@pytest.fixture
def mock_conversation_service(mock_conversation):
    """Create mock conversation service."""
    service = AsyncMock()
    service.start_conversation = AsyncMock(return_value=mock_conversation)
    service.get_conversation = AsyncMock(return_value=mock_conversation)
    service.add_message = AsyncMock(return_value=mock_conversation)
    service.complete_conversation = AsyncMock(return_value=mock_conversation)
    service.list_user_conversations = AsyncMock(return_value=[mock_conversation])
    service.pause_conversation = AsyncMock(return_value=mock_conversation)
    return service


@pytest.fixture
def mock_generic_handler(mock_conversation):
    """Create mock generic handler."""
    handler = AsyncMock()
    handler.get_initial_prompt = AsyncMock(return_value="Welcome! Let's explore your core values.")
    handler.handle_conversation_initiate = AsyncMock(return_value=mock_conversation)
    handler.handle_conversation_message = AsyncMock(
        return_value={
            "content": "That's wonderful! Honesty is a powerful core value.",
            "is_complete": False,
        }
    )
    handler.handle_conversation_pause = AsyncMock(return_value=None)
    handler.handle_conversation_complete = AsyncMock(return_value=None)
    return handler


@pytest.fixture
def client(mock_conversation_service, mock_generic_handler):
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_generic_handler] = lambda: mock_generic_handler

    with TestClient(app) as c:
        yield c

    # Clean up overrides
    app.dependency_overrides = {}


class TestConversationInitiation:
    """Test conversation initiation endpoint."""

    def test_initiate_conversation_success(self, client, mock_conversation):
        """Test successful conversation initiation."""
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
        # Clear overrides for this test to ensure auth is checked (though auth is usually separate)
        # But here we just want to check if missing header fails.
        # The dependency override for services doesn't affect auth unless we override auth too.

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

    def test_send_message_success(self, client, mock_conversation):
        """Test successful message sending."""
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

    def test_send_message_conversation_not_found(self, client, mock_generic_handler):
        """Test message sending to non-existent conversation."""
        from coaching.src.domain.exceptions.conversation_exceptions import (
            ConversationNotFound,
        )

        # Update mock to raise exception
        mock_generic_handler.handle_conversation_message.side_effect = ConversationNotFound(
            ConversationId("nonexistent"),
            TenantId("tenant_test"),
        )

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

        # Reset side effect
        mock_generic_handler.handle_conversation_message.side_effect = None


class TestConversationRetrieval:
    """Test conversation retrieval endpoint."""

    def test_get_conversation_success(self, client, mock_conversation):
        """Test successful conversation retrieval."""
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

    def test_get_conversation_not_found(self, client, mock_conversation_service):
        """Test conversation retrieval when not found."""
        from coaching.src.domain.exceptions.conversation_exceptions import (
            ConversationNotFound,
        )

        # Update mock to raise exception
        mock_conversation_service.get_conversation.side_effect = ConversationNotFound(
            ConversationId("nonexistent"),
            TenantId("tenant_test"),
        )

        # Make request
        response = client.get(
            "/api/v1/conversations/nonexistent",
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 404
        assert response.status_code == 404

        # Reset side effect
        mock_conversation_service.get_conversation.side_effect = None


class TestConversationListing:
    """Test conversation listing endpoint."""

    def test_list_conversations_success(self, client, mock_conversation):
        """Test successful conversation listing."""
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

    def test_list_conversations_with_pagination(self, client, mock_conversation):
        """Test conversation listing with pagination."""
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

    def test_pause_conversation_success(self, client, mock_conversation):
        """Test successful conversation pausing."""
        # Make request
        response = client.post(
            f"/api/v1/conversations/{mock_conversation.conversation_id}/pause",
            json={"reason": "Taking a break"},
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 204 No Content
        assert response.status_code == 204

    def test_complete_conversation_success(self, client, mock_conversation):
        """Test successful conversation completion."""
        # Make request
        response = client.post(
            f"/api/v1/conversations/{mock_conversation.conversation_id}/complete",
            json={"feedback": "Great session!", "rating": 5},
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 204 No Content
        assert response.status_code == 204
