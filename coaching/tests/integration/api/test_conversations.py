"""Integration tests for conversation API routes (Phase 7).

Tests the refactored conversation routes using new architecture with
application services, domain entities, and auth-based context.
"""

from unittest.mock import AsyncMock

import pytest
from coaching.src.api.dependencies import get_conversation_repository, get_conversation_service
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.multitenant_dependencies import get_multitenant_conversation_service
from coaching.src.api.main import app
from coaching.src.core.constants import CoachingTopic, ConversationStatus
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.models.responses import (
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
    MessageResponse,
)
from fastapi.testclient import TestClient


@pytest.fixture
def mock_conversation():
    """Create mock conversation entity."""
    conversation = Conversation.create(
        user_id=UserId("user123"),
        tenant_id=TenantId("tenant123"),
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

    conversation_response = ConversationResponse(
        conversation_id=str(mock_conversation.conversation_id),
        status=mock_conversation.status,
        current_question="Welcome! Let's explore your core values.",
        progress=0.0,
        phase=mock_conversation.context.current_phase,
        session_data={"session_id": "session_test"},
    )

    service.start_conversation = AsyncMock(return_value=mock_conversation)
    service.get_conversation = AsyncMock(return_value=mock_conversation)
    service.add_message = AsyncMock(return_value=mock_conversation)
    service.complete_conversation = AsyncMock(return_value={"business_data_updated": False})
    service.pause_conversation = AsyncMock(return_value=mock_conversation)
    service.initiate_conversation = AsyncMock(return_value=conversation_response)
    service.process_message = AsyncMock(
        return_value=MessageResponse(
            ai_response="That's wonderful! Honesty is a powerful core value.",
            follow_up_question=None,
            insights=None,
            progress=0.25,
            phase=mock_conversation.context.current_phase,
            is_complete=False,
            next_steps=None,
            identified_values=None,
        )
    )
    service.list_user_conversations = AsyncMock(
        return_value=ConversationListResponse(
            conversations=[
                ConversationSummary(
                    conversation_id=str(mock_conversation.conversation_id),
                    topic=mock_conversation.topic,
                    status=mock_conversation.status,
                    progress=0.0,
                    created_at=mock_conversation.created_at,
                    updated_at=mock_conversation.updated_at,
                    message_count=len(mock_conversation.messages),
                )
            ],
            total=1,
            page=1,
        )
    )
    return service


@pytest.fixture
def mock_conversation_repository(mock_conversation):
    """Create mock conversation repository matching route expectations."""

    class RepoConversation:
        def __init__(self, source: Conversation):
            self.conversation_id = str(source.conversation_id)
            self.user_id = str(source.user_id)
            self.topic = source.topic
            self.status = source.status
            self.messages = source.messages
            self.context = self.RepoContext({"tenant_id": str(source.tenant_id)})
            self.created_at = source.created_at
            self.updated_at = source.updated_at
            self.completed_at = source.completed_at

        class RepoContext(dict):
            def model_dump(self) -> dict[str, str]:
                return dict(self)

        def calculate_progress(self) -> float:
            return 0.0

    repo = AsyncMock()
    repo.get = AsyncMock(return_value=RepoConversation(mock_conversation))
    return repo


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
def client(mock_conversation_service, mock_generic_handler, mock_conversation_repository):
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_conversation_service] = lambda: mock_conversation_service
    app.dependency_overrides[get_generic_handler] = lambda: mock_generic_handler
    app.dependency_overrides[get_multitenant_conversation_service] = (
        lambda: mock_conversation_service
    )
    app.dependency_overrides[get_conversation_repository] = lambda: mock_conversation_repository

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
            "/api/v1/multitenant/conversations/initiate",
            json={
                "topic": "core_values",
                "user_id": "user_test",
                "context": {},
                "language": "en",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        data = payload["data"]
        assert data["conversation_id"] == str(mock_conversation.conversation_id)
        assert data["status"] == ConversationStatus.ACTIVE.value
        assert data["current_question"]

    def test_initiate_conversation_no_auth(self, client):
        """Test conversation initiation without authentication."""
        # Clear overrides for this test to ensure auth is checked (though auth is usually separate)
        # But here we just want to check if missing header fails.
        # The dependency override for services doesn't affect auth unless we override auth too.

        response = client.post(
            "/api/v1/multitenant/conversations/initiate",
            json={
                "topic": "core_values",
                "user_id": "user_test",
            },
        )

        # Should fail with 401 or 422 (missing auth header)
        assert response.status_code in [401, 422]

    def test_initiate_conversation_invalid_topic(self, client):
        """Test conversation initiation with invalid topic."""
        response = client.post(
            "/api/v1/multitenant/conversations/initiate",
            json={
                "topic": "invalid_topic",
                "user_id": "user_test",
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
            f"/api/v1/multitenant/conversations/{mock_conversation.conversation_id}/message",
            json={
                "user_message": "I value honesty and transparency",
                "metadata": {},
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert "ai_response" in data
        assert "progress" in data

    def test_send_message_conversation_not_found(self, client, mock_conversation_service):
        """Test message sending to non-existent conversation."""
        from coaching.src.domain.exceptions.conversation_exceptions import (
            ConversationNotFound,
        )

        # Update mock to raise exception
        mock_conversation_service.process_message.side_effect = ConversationNotFound(
            ConversationId("nonexistent"),
            TenantId("tenant_test"),
        )

        # Make request
        response = client.post(
            "/api/v1/multitenant/conversations/nonexistent/message",
            json={
                "user_message": "Test message",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 404
        assert response.status_code == 404

        # Reset side effect
        mock_conversation_service.process_message.side_effect = None


class TestConversationRetrieval:
    """Test conversation retrieval endpoint."""

    def test_get_conversation_success(self, client, mock_conversation):
        """Test successful conversation retrieval."""
        # Make request
        response = client.get(
            f"/api/v1/multitenant/conversations/{mock_conversation.conversation_id}",
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == mock_conversation.conversation_id
        assert "messages" in data
        assert isinstance(data["messages"], list)

    def test_get_conversation_not_found(self, client, mock_conversation_repository):
        """Test conversation retrieval when not found."""
        # Update repo mock to simulate missing conversation
        mock_conversation_repository.get.return_value = None

        # Make request
        response = client.get(
            "/api/v1/multitenant/conversations/nonexistent",
            headers={"Authorization": "Bearer test_token"},
        )

        # Should return 404
        assert response.status_code == 404

        # Reset side effect
        mock_conversation_repository.get.return_value = None


class TestConversationListing:
    """Test conversation listing endpoint."""

    def test_list_conversations_success(self, client, mock_conversation):
        """Test successful conversation listing."""
        # Make request
        response = client.get(
            "/api/v1/multitenant/conversations",
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
            "/api/v1/multitenant/conversations?page=1&page_size=10",
            headers={"Authorization": "Bearer test_token"},
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1


class TestConversationActions:
    """Test conversation action endpoints (pause, complete)."""

    def test_pause_conversation_success(self, client, mock_conversation):
        """Test successful conversation pausing."""
        # Make request
        response = client.post(
            f"/api/v1/multitenant/conversations/{mock_conversation.conversation_id}/pause",
            json={"reason": "Taking a break"},
            headers={"Authorization": "Bearer test_token"},
        )

        # Pause is not implemented, expect 501
        assert response.status_code == 501

    def test_complete_conversation_success(self, client, mock_conversation):
        """Test successful conversation completion."""
        # Make request
        response = client.post(
            f"/api/v1/multitenant/conversations/{mock_conversation.conversation_id}/complete",
            json={"feedback": "Great session!", "rating": 5},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get("result", {}).get("business_data_updated") is False
