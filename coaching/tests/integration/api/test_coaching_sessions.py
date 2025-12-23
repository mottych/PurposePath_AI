"""Integration tests for coaching sessions API routes.

Tests the generic coaching engine API endpoints with mocked dependencies.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from coaching.src.api.main import app
from coaching.src.api.routes.coaching_sessions import (
    get_coaching_session_repository,
    get_coaching_session_service,
)
from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.domain.entities.coaching_session import CoachingSession
from coaching.src.services.coaching_session_service import (
    CoachingSessionService,
    InvalidTopicError,
    MessageResponse,
    SessionCompletionResponse,
    SessionDetails,
    SessionResponse,
    SessionStateResponse,
    SessionSummary,
    TopicStatus,
    TopicsWithStatusResponse,
)
from fastapi.testclient import TestClient

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session() -> CoachingSession:
    """Create a mock coaching session entity."""
    return CoachingSession.create(
        tenant_id="tenant_test",
        user_id="user_test",
        topic_id="core_values",
        context={"business_name": "Test Business"},
    )


@pytest.fixture
def mock_session_response() -> SessionResponse:
    """Create a mock session response."""
    return SessionResponse(
        session_id="session_123",
        tenant_id="tenant_test",
        topic_id="core_values",
        status=ConversationStatus.ACTIVE,
        message="Welcome! Let's explore your core values.",
        message_count=1,
        estimated_completion=0.05,
    )


@pytest.fixture
def mock_message_response() -> MessageResponse:
    """Create a mock message response."""
    return MessageResponse(
        session_id="session_123",
        message="That's a great insight! Tell me more.",
        message_count=3,
        estimated_completion=0.15,
        status=ConversationStatus.ACTIVE,
    )


@pytest.fixture
def mock_state_response() -> SessionStateResponse:
    """Create a mock state change response."""
    return SessionStateResponse(
        session_id="session_123",
        status=ConversationStatus.PAUSED,
        topic_id="core_values",
        turn_count=1,
        max_turns=10,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
        message="Session paused successfully",
    )


@pytest.fixture
def mock_completion_response() -> SessionCompletionResponse:
    """Create a mock completion response."""
    return SessionCompletionResponse(
        session_id="session_123",
        status=ConversationStatus.COMPLETED,
        result={"core_values": [{"name": "Integrity", "description": "Acting with honesty"}]},
        message_count=10,
    )


@pytest.fixture
def mock_session_details() -> SessionDetails:
    """Create mock session details."""
    from coaching.src.services.coaching_session_service import MessageDetail

    return SessionDetails(
        session_id="session_123",
        tenant_id="tenant_test",
        topic_id="core_values",
        user_id="user_test",
        status=ConversationStatus.ACTIVE,
        messages=[
            MessageDetail(
                role=MessageRole.ASSISTANT,
                content="Welcome!",
                timestamp=datetime.now(UTC).isoformat(),
            ),
            MessageDetail(
                role=MessageRole.USER,
                content="Hello",
                timestamp=datetime.now(UTC).isoformat(),
            ),
        ],
        context={"business_name": "Test Business"},
        max_turns=10,
        message_count=2,
        estimated_completion=0.1,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )


@pytest.fixture
def mock_session_summary() -> SessionSummary:
    """Create mock session summary."""
    return SessionSummary(
        session_id="session_123",
        topic_id="core_values",
        status=ConversationStatus.ACTIVE,
        turn_count=5,
        message_count=5,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )


@pytest.fixture
def mock_coaching_session_service(
    mock_session_response,
    mock_message_response,
    mock_state_response,
    mock_completion_response,
    mock_session_details,
    mock_session_summary,
):
    """Create mock coaching session service."""
    service = AsyncMock(spec=CoachingSessionService)
    service.initiate_session = AsyncMock(return_value=mock_session_response)
    service.resume_session = AsyncMock(return_value=mock_session_response)
    service.get_or_create_session = AsyncMock(return_value=mock_session_response)
    service.send_message = AsyncMock(return_value=mock_message_response)
    service.pause_session = AsyncMock(return_value=mock_state_response)
    service.cancel_session = AsyncMock(
        return_value=SessionStateResponse(
            session_id="session_123",
            status=ConversationStatus.CANCELLED,
            topic_id="core_values",
            turn_count=1,
            max_turns=10,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
            message="Session cancelled",
        )
    )
    service.complete_session = AsyncMock(return_value=mock_completion_response)
    service.get_session = AsyncMock(return_value=mock_session_details)
    service.list_user_sessions = AsyncMock(return_value=[mock_session_summary])
    service.get_topics_with_status = AsyncMock(
        return_value=TopicsWithStatusResponse(
            topics=[
                TopicStatus(
                    topic_id="core_values",
                    name="Core Values",
                    description="Define and refine company core values",
                    status="not_started",
                    session_id=None,
                    completed_at=None,
                )
            ]
        )
    )
    return service


@pytest.fixture
def mock_session_repository(mock_session):
    """Create mock session repository."""
    repo = AsyncMock()
    repo.list_by_tenant_user = AsyncMock(return_value=[mock_session])
    return repo


@pytest.fixture
def client(mock_coaching_session_service, mock_session_repository):
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_coaching_session_service] = lambda: mock_coaching_session_service
    app.dependency_overrides[get_coaching_session_repository] = lambda: mock_session_repository

    with TestClient(app) as c:
        yield c

    # Clean up overrides
    app.dependency_overrides = {}


# =============================================================================
# Test Classes
# =============================================================================


class TestGetTopicsStatus:
    """Tests for GET /ai/coaching/topics endpoint."""

    def test_get_topics_status_success(self, client, mock_session):
        """Test successful retrieval of topics with status."""
        response = client.get(
            "/api/v1/ai/coaching/topics",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "topics" in data["data"]
        topics = data["data"]["topics"]
        assert len(topics) > 0

        # Check topic structure
        topic = topics[0]
        assert "topic_id" in topic
        assert "name" in topic
        assert "description" in topic
        assert "status" in topic


class TestStartSession:
    """Tests for POST /ai/coaching/start endpoint."""

    def test_start_session_success(self, client, mock_session_response):
        """Test successful session start."""
        response = client.post(
            "/api/v1/ai/coaching/start",
            json={"topic_id": "core_values"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == mock_session_response.session_id
        assert data["data"]["topic_id"] == "core_values"
        assert data["data"]["status"] == "active"

    def test_start_session_with_context(self, client, mock_coaching_session_service):
        """Test session start with context data."""
        response = client.post(
            "/api/v1/ai/coaching/start",
            json={
                "topic_id": "core_values",
                "context": {"business_name": "Test Corp"},
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        mock_coaching_session_service.get_or_create_session.assert_called_once()

    def test_start_session_invalid_topic(self, client, mock_coaching_session_service):
        """Test session start with invalid topic returns 422."""
        mock_coaching_session_service.get_or_create_session.side_effect = InvalidTopicError(
            "invalid_topic"
        )

        response = client.post(
            "/api/v1/ai/coaching/start",
            json={"topic_id": "invalid_topic"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["code"] == "INVALID_TOPIC"


class TestSendMessage:
    """Tests for POST /ai/coaching/message endpoint."""

    def test_send_message_success(self, client, mock_message_response):
        """Test successful message send."""
        response = client.post(
            "/api/v1/ai/coaching/message",
            json={
                "session_id": "session_123",
                "message": "I believe integrity is my core value",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "coach_message" in data["data"]
        assert data["data"]["session_id"] == "session_123"

    def test_send_message_session_not_found(self, client, mock_coaching_session_service):
        """Test message to non-existent session returns 422."""
        from coaching.src.domain.exceptions.session_exceptions import SessionNotFoundError

        mock_coaching_session_service.send_message.side_effect = SessionNotFoundError(
            session_id="invalid_id"
        )

        response = client.post(
            "/api/v1/ai/coaching/message",
            json={
                "session_id": "invalid_id",
                "message": "Hello",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["code"] == "SESSION_NOT_FOUND"

    def test_send_message_empty_message_rejected(self, client):
        """Test that empty message is rejected by validation."""
        response = client.post(
            "/api/v1/ai/coaching/message",
            json={
                "session_id": "session_123",
                "message": "",
            },
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422  # Validation error


class TestPauseSession:
    """Tests for POST /ai/coaching/pause endpoint."""

    def test_pause_session_success(self, client, mock_state_response):
        """Test successful session pause."""
        response = client.post(
            "/api/v1/ai/coaching/pause",
            json={"session_id": "session_123"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "paused"
        assert data["data"]["session_id"] == "session_123"
        assert data["data"]["topic_id"] == "core_values"
        assert data["data"]["turn_count"] == 1
        assert data["data"]["max_turns"] == 10
        assert "created_at" in data["data"]
        assert "updated_at" in data["data"]

    def test_pause_session_not_found(self, client, mock_coaching_session_service):
        """Test pause of non-existent session returns 422."""
        from coaching.src.domain.exceptions.session_exceptions import SessionNotFoundError

        mock_coaching_session_service.pause_session.side_effect = SessionNotFoundError(
            session_id="invalid_id"
        )

        response = client.post(
            "/api/v1/ai/coaching/pause",
            json={"session_id": "invalid_id"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["code"] == "SESSION_NOT_FOUND"


class TestCompleteSession:
    """Tests for POST /ai/coaching/complete endpoint."""

    def test_complete_session_success(self, client, mock_completion_response):
        """Test successful session completion."""
        response = client.post(
            "/api/v1/ai/coaching/complete",
            json={"session_id": "session_123"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "completed"
        assert "result" in data["data"]
        assert "core_values" in data["data"]["result"]

    def test_complete_session_not_active(self, client, mock_coaching_session_service):
        """Test completion of non-active session returns 400."""
        from coaching.src.domain.exceptions.session_exceptions import SessionNotActiveError

        mock_coaching_session_service.complete_session.side_effect = SessionNotActiveError(
            session_id="session_123",
            current_status="paused",
        )

        response = client.post(
            "/api/v1/ai/coaching/complete",
            json={"session_id": "session_123"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "SESSION_NOT_ACTIVE"


class TestCancelSession:
    """Tests for POST /ai/coaching/cancel endpoint."""

    def test_cancel_session_success(self, client):
        """Test successful session cancellation."""
        response = client.post(
            "/api/v1/ai/coaching/cancel",
            json={"session_id": "session_123"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "cancelled"


class TestGetSession:
    """Tests for GET /ai/coaching/session endpoint."""

    def test_get_session_success(self, client, mock_session_details):
        """Test successful session retrieval."""
        response = client.get(
            "/api/v1/ai/coaching/session",
            params={"session_id": "session_123"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["session_id"] == "session_123"
        assert "messages" in data["data"]

    def test_get_session_not_found(self, client, mock_coaching_session_service):
        """Test get non-existent session returns 422."""
        mock_coaching_session_service.get_session.return_value = None

        response = client.get(
            "/api/v1/ai/coaching/session",
            params={"session_id": "invalid_id"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["code"] == "SESSION_NOT_FOUND"


class TestListSessions:
    """Tests for GET /ai/coaching/sessions endpoint."""

    def test_list_sessions_success(self, client, mock_session_summary):
        """Test successful session listing."""
        response = client.get(
            "/api/v1/ai/coaching/sessions",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 1

    def test_list_sessions_with_filters(self, client, mock_coaching_session_service):
        """Test session listing with filters."""
        response = client.get(
            "/api/v1/ai/coaching/sessions",
            params={"include_completed": "true", "limit": "10"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        mock_coaching_session_service.list_user_sessions.assert_called_once()


class TestErrorHandling:
    """Tests for error handling across endpoints."""

    def test_internal_server_error_handled(self, client, mock_coaching_session_service):
        """Test that internal errors return 500."""
        mock_coaching_session_service.get_or_create_session.side_effect = Exception(
            "Database connection failed"
        )

        response = client.post(
            "/api/v1/ai/coaching/start",
            json={"topic_id": "core_values"},
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


__all__ = [
    "TestCancelSession",
    "TestCompleteSession",
    "TestErrorHandling",
    "TestGetSession",
    "TestGetTopicsStatus",
    "TestListSessions",
    "TestPauseSession",
    "TestSendMessage",
    "TestStartSession",
]
