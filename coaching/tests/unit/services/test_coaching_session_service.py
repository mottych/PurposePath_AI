"""Unit tests for CoachingSessionService.

This module provides comprehensive tests for the coaching session service,
covering session lifecycle, message processing, state management, and queries.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.core.exceptions import ConversationNotFoundError
from coaching.src.domain.entities.coaching_session import CoachingSession
from coaching.src.models.llm_models import LLMResponse
from coaching.src.services.coaching_session_service import (
    ActiveSessionExistsError,
    CoachingSessionService,
    InvalidTopicError,
    MessageDetail,
    MessageResponse,
    SessionCompletionResponse,
    SessionDetails,
    SessionResponse,
    SessionStateResponse,
    SessionSummary,
    SessionValidationError,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_session_repository() -> AsyncMock:
    """Create a mock session repository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.get_by_id_for_tenant = AsyncMock()
    repo.get_active_by_tenant_topic = AsyncMock()
    repo.list_by_tenant_user = AsyncMock()
    return repo


@pytest.fixture
def mock_llm_service() -> MagicMock:
    """Create a mock LLM service."""
    service = MagicMock()
    service.generate_coaching_response = AsyncMock(
        return_value=LLMResponse(
            response="Test coach response",
            model_id="test-model",
            token_usage={"input": 10, "output": 20, "total": 30},
            cost=0.001,
        )
    )
    return service


@pytest.fixture
def coaching_session_service(
    mock_session_repository: AsyncMock,
    mock_llm_service: MagicMock,
) -> CoachingSessionService:
    """Create a coaching session service with mocked dependencies."""
    return CoachingSessionService(
        session_repository=mock_session_repository,
        llm_service=mock_llm_service,
    )


@pytest.fixture
def sample_session() -> CoachingSession:
    """Create a sample coaching session."""
    return CoachingSession.create(
        tenant_id="tenant_123",
        user_id="user_456",
        topic_id="core_values",
        context={"business_name": "Test Business"},
    )


@pytest.fixture
def sample_session_with_messages(sample_session: CoachingSession) -> CoachingSession:
    """Create a sample session with some messages."""
    sample_session.add_assistant_message(
        content="Hello! Let's explore your core values.",
        metadata={"type": "initiation"},
    )
    sample_session.add_user_message(
        content="I believe in honesty and integrity.",
        metadata={},
    )
    sample_session.add_assistant_message(
        content="Those are great values! Tell me more.",
        metadata={"type": "response"},
    )
    return sample_session


# =============================================================================
# Response Model Tests
# =============================================================================


class TestSessionResponse:
    """Test SessionResponse model."""

    def test_valid_session_response(self) -> None:
        """Test creating a valid session response."""
        response = SessionResponse(
            session_id="session_123",
            tenant_id="tenant_456",
            topic_id="core_values",
            status=ConversationStatus.ACTIVE,
            coach_message="Hello!",
            message_count=1,
            estimated_completion=0.1,
        )
        assert response.session_id == "session_123"
        assert response.status == ConversationStatus.ACTIVE

    def test_session_response_optional_coach_message(self) -> None:
        """Test session response with no coach message."""
        response = SessionResponse(
            session_id="session_123",
            tenant_id="tenant_456",
            topic_id="core_values",
            status=ConversationStatus.ACTIVE,
            message_count=0,
            estimated_completion=0.0,
        )
        assert response.coach_message is None


class TestMessageResponse:
    """Test MessageResponse model."""

    def test_valid_message_response(self) -> None:
        """Test creating a valid message response."""
        response = MessageResponse(
            session_id="session_123",
            coach_message="Great answer!",
            message_count=5,
            estimated_completion=0.5,
            status=ConversationStatus.ACTIVE,
        )
        assert response.coach_message == "Great answer!"
        assert response.message_count == 5


class TestSessionStateResponse:
    """Test SessionStateResponse model."""

    def test_valid_state_response(self) -> None:
        """Test creating a valid state response."""
        response = SessionStateResponse(
            session_id="session_123",
            status=ConversationStatus.PAUSED,
            message="Session paused",
        )
        assert response.status == ConversationStatus.PAUSED


class TestSessionDetails:
    """Test SessionDetails model."""

    def test_valid_session_details(self) -> None:
        """Test creating valid session details."""
        details = SessionDetails(
            session_id="session_123",
            tenant_id="tenant_456",
            topic_id="core_values",
            user_id="user_789",
            status=ConversationStatus.ACTIVE,
            messages=[
                MessageDetail(
                    role=MessageRole.ASSISTANT,
                    content="Hello!",
                    timestamp="2024-01-01T00:00:00",
                )
            ],
            message_count=1,
            estimated_completion=0.1,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
        )
        assert len(details.messages) == 1
        assert details.result is None


# =============================================================================
# Exception Tests
# =============================================================================


class TestExceptions:
    """Test custom exceptions."""

    def test_invalid_topic_error(self) -> None:
        """Test InvalidTopicError."""
        error = InvalidTopicError("unknown_topic")
        assert error.topic_id == "unknown_topic"
        assert "unknown_topic" in str(error)

    def test_session_validation_error(self) -> None:
        """Test SessionValidationError."""
        error = SessionValidationError("Cannot resume")
        assert "Cannot resume" in str(error)

    def test_active_session_exists_error(self) -> None:
        """Test ActiveSessionExistsError."""
        error = ActiveSessionExistsError("session_123", "core_values")
        assert error.existing_session_id == "session_123"
        assert error.topic_id == "core_values"
        assert "core_values" in str(error)


# =============================================================================
# Session Initiation Tests
# =============================================================================


class TestInitiateSession:
    """Tests for session initiation."""

    @pytest.mark.asyncio
    async def test_initiate_session_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_llm_service: MagicMock,
    ) -> None:
        """Test successful session initiation."""
        # Arrange
        mock_session_repository.get_active_by_tenant_topic.return_value = None
        mock_session_repository.save.side_effect = lambda s: s

        # Act
        response = await coaching_session_service.initiate_session(
            tenant_id="tenant_123",
            user_id="user_456",
            topic_id="core_values",
            context={"business_name": "Test Business"},
        )

        # Assert
        assert isinstance(response, SessionResponse)
        assert response.topic_id == "core_values"
        assert response.status == ConversationStatus.ACTIVE
        assert response.coach_message is not None
        mock_session_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_session_invalid_topic(
        self,
        coaching_session_service: CoachingSessionService,
    ) -> None:
        """Test initiation with invalid topic raises error."""
        with pytest.raises(InvalidTopicError) as exc_info:
            await coaching_session_service.initiate_session(
                tenant_id="tenant_123",
                user_id="user_456",
                topic_id="invalid_topic",
            )
        assert exc_info.value.topic_id == "invalid_topic"

    @pytest.mark.asyncio
    async def test_initiate_session_existing_active_session(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test initiation fails when active session exists."""
        # Arrange
        mock_session_repository.get_active_by_tenant_topic.return_value = sample_session

        # Act & Assert
        with pytest.raises(ActiveSessionExistsError) as exc_info:
            await coaching_session_service.initiate_session(
                tenant_id="tenant_123",
                user_id="user_456",
                topic_id="core_values",
            )
        assert exc_info.value.topic_id == "core_values"


# =============================================================================
# Resume Session Tests
# =============================================================================


class TestResumeSession:
    """Tests for session resumption."""

    @pytest.mark.asyncio
    async def test_resume_session_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test successful session resumption."""
        # Arrange
        sample_session_with_messages.pause()
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session_with_messages
        mock_session_repository.save.side_effect = lambda s: s

        # Act
        response = await coaching_session_service.resume_session(
            session_id=str(sample_session_with_messages.session_id),
            tenant_id="tenant_123",
        )

        # Assert
        assert isinstance(response, SessionResponse)
        assert response.status == ConversationStatus.ACTIVE
        assert response.coach_message is not None

    @pytest.mark.asyncio
    async def test_resume_session_not_paused(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test resume fails for non-paused session."""
        # Arrange - session is active, not paused
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act & Assert
        with pytest.raises(SessionValidationError):
            await coaching_session_service.resume_session(
                session_id=str(sample_session.session_id),
                tenant_id="tenant_123",
            )

    @pytest.mark.asyncio
    async def test_resume_session_not_found(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test resume fails for non-existent session."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = None

        # Act & Assert
        with pytest.raises(ConversationNotFoundError):
            await coaching_session_service.resume_session(
                session_id="nonexistent_session",
                tenant_id="tenant_123",
            )


# =============================================================================
# Get Or Create Session Tests
# =============================================================================


class TestGetOrCreateSession:
    """Tests for get_or_create_session."""

    @pytest.mark.asyncio
    async def test_get_or_create_returns_existing(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test returns existing active session."""
        # Arrange
        mock_session_repository.get_active_by_tenant_topic.return_value = (
            sample_session_with_messages
        )

        # Act
        response = await coaching_session_service.get_or_create_session(
            tenant_id="tenant_123",
            user_id="user_456",
            topic_id="core_values",
        )

        # Assert
        assert response.session_id == str(sample_session_with_messages.session_id)
        assert response.coach_message is None  # No new message for existing

    @pytest.mark.asyncio
    async def test_get_or_create_resumes_paused(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test resumes paused session."""
        # Arrange
        sample_session_with_messages.pause()
        mock_session_repository.get_active_by_tenant_topic.return_value = (
            sample_session_with_messages
        )
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session_with_messages
        mock_session_repository.save.side_effect = lambda s: s

        # Act
        response = await coaching_session_service.get_or_create_session(
            tenant_id="tenant_123",
            user_id="user_456",
            topic_id="core_values",
        )

        # Assert
        assert response.status == ConversationStatus.ACTIVE
        assert response.coach_message is not None  # Resume message

    @pytest.mark.asyncio
    async def test_get_or_create_creates_new(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test creates new session when none exists."""
        # Arrange
        mock_session_repository.get_active_by_tenant_topic.return_value = None
        mock_session_repository.save.side_effect = lambda s: s

        # Act
        response = await coaching_session_service.get_or_create_session(
            tenant_id="tenant_123",
            user_id="user_456",
            topic_id="core_values",
        )

        # Assert
        assert response.status == ConversationStatus.ACTIVE
        assert response.coach_message is not None


# =============================================================================
# Send Message Tests
# =============================================================================


class TestSendMessage:
    """Tests for message sending."""

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test successful message sending."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session_with_messages
        mock_session_repository.save.side_effect = lambda s: s
        initial_count = sample_session_with_messages.get_message_count()

        # Act
        response = await coaching_session_service.send_message(
            session_id=str(sample_session_with_messages.session_id),
            tenant_id="tenant_123",
            user_message="What about teamwork?",
        )

        # Assert
        assert isinstance(response, MessageResponse)
        assert response.coach_message == "Test coach response"
        assert response.message_count == initial_count + 2  # User + coach
        assert response.status == ConversationStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_send_message_to_paused_session(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test sending message to paused session fails."""
        # Arrange
        sample_session_with_messages.pause()
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session_with_messages

        # Act & Assert
        with pytest.raises(SessionValidationError):
            await coaching_session_service.send_message(
                session_id=str(sample_session_with_messages.session_id),
                tenant_id="tenant_123",
                user_message="Hello?",
            )


# =============================================================================
# Session State Management Tests
# =============================================================================


class TestPauseSession:
    """Tests for session pausing."""

    @pytest.mark.asyncio
    async def test_pause_session_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test successful session pausing."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session
        mock_session_repository.save.side_effect = lambda s: s

        # Act
        response = await coaching_session_service.pause_session(
            session_id=str(sample_session.session_id),
            tenant_id="tenant_123",
        )

        # Assert
        assert isinstance(response, SessionStateResponse)
        assert response.status == ConversationStatus.PAUSED
        assert "paused" in response.message.lower()


class TestCancelSession:
    """Tests for session cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_session_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test successful session cancellation."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session
        mock_session_repository.save.side_effect = lambda s: s

        # Act
        response = await coaching_session_service.cancel_session(
            session_id=str(sample_session.session_id),
            tenant_id="tenant_123",
        )

        # Assert
        assert isinstance(response, SessionStateResponse)
        assert response.status == ConversationStatus.CANCELLED
        assert "cancelled" in response.message.lower()


class TestCompleteSession:
    """Tests for session completion."""

    @pytest.mark.asyncio
    async def test_complete_session_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_llm_service: MagicMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test successful session completion with result extraction."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session_with_messages
        mock_session_repository.save.side_effect = lambda s: s
        mock_llm_service.generate_coaching_response.return_value = LLMResponse(
            response='{"core_values": [{"name": "Honesty", "description": "Being truthful"}]}',
            model_id="test-model",
            token_usage={"input": 10, "output": 20, "total": 30},
            cost=0.001,
        )

        # Act
        response = await coaching_session_service.complete_session(
            session_id=str(sample_session_with_messages.session_id),
            tenant_id="tenant_123",
        )

        # Assert
        assert isinstance(response, SessionCompletionResponse)
        assert response.status == ConversationStatus.COMPLETED
        assert isinstance(response.result, dict)

    @pytest.mark.asyncio
    async def test_complete_session_already_completed(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test completing an already completed session fails."""
        # Arrange
        sample_session_with_messages.complete(result={"test": "result"})
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session_with_messages

        # Act & Assert
        with pytest.raises(SessionValidationError):
            await coaching_session_service.complete_session(
                session_id=str(sample_session_with_messages.session_id),
                tenant_id="tenant_123",
            )


# =============================================================================
# Query Method Tests
# =============================================================================


class TestGetSession:
    """Tests for getting session details."""

    @pytest.mark.asyncio
    async def test_get_session_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session_with_messages: CoachingSession,
    ) -> None:
        """Test successful session retrieval."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session_with_messages

        # Act
        details = await coaching_session_service.get_session(
            session_id=str(sample_session_with_messages.session_id),
            tenant_id="tenant_123",
        )

        # Assert
        assert isinstance(details, SessionDetails)
        assert details.topic_id == "core_values"
        assert len(details.messages) == sample_session_with_messages.get_message_count()

    @pytest.mark.asyncio
    async def test_get_session_not_found(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test getting non-existent session raises error."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = None

        # Act & Assert
        with pytest.raises(ConversationNotFoundError):
            await coaching_session_service.get_session(
                session_id="nonexistent",
                tenant_id="tenant_123",
            )


class TestListUserSessions:
    """Tests for listing user sessions."""

    @pytest.mark.asyncio
    async def test_list_user_sessions_success(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test successful session listing."""
        # Arrange
        mock_session_repository.list_by_tenant_user.return_value = [sample_session]

        # Act
        summaries = await coaching_session_service.list_user_sessions(
            tenant_id="tenant_123",
            user_id="user_456",
        )

        # Assert
        assert len(summaries) == 1
        assert isinstance(summaries[0], SessionSummary)
        assert summaries[0].topic_id == "core_values"

    @pytest.mark.asyncio
    async def test_list_user_sessions_empty(
        self,
        coaching_session_service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test listing when no sessions exist."""
        # Arrange
        mock_session_repository.list_by_tenant_user.return_value = []

        # Act
        summaries = await coaching_session_service.list_user_sessions(
            tenant_id="tenant_123",
            user_id="user_456",
        )

        # Assert
        assert summaries == []


# =============================================================================
# Private Helper Method Tests
# =============================================================================


class TestRenderTemplate:
    """Tests for template rendering."""

    def test_render_template_with_placeholders(
        self,
        coaching_session_service: CoachingSessionService,
    ) -> None:
        """Test rendering template with placeholders."""
        template = "Hello {name}, welcome to {company}!"
        context = {"name": "John", "company": "Acme"}

        result = coaching_session_service._render_template(template, context)

        assert result == "Hello John, welcome to Acme!"

    def test_render_template_missing_placeholder(
        self,
        coaching_session_service: CoachingSessionService,
    ) -> None:
        """Test rendering with missing placeholder leaves it."""
        template = "Hello {name}, your role is {role}."
        context = {"name": "John"}

        result = coaching_session_service._render_template(template, context)

        assert result == "Hello John, your role is {role}."


class TestParseJsonFromResponse:
    """Tests for JSON parsing from LLM responses."""

    def test_parse_direct_json(
        self,
        coaching_session_service: CoachingSessionService,
    ) -> None:
        """Test parsing direct JSON."""
        response = '{"key": "value", "number": 42}'

        result = coaching_session_service._parse_json_from_response(response)

        assert result == {"key": "value", "number": 42}

    def test_parse_json_from_markdown_block(
        self,
        coaching_session_service: CoachingSessionService,
    ) -> None:
        """Test parsing JSON from markdown code block."""
        response = """Here is the result:
```json
{"core_values": ["honesty", "integrity"]}
```
"""
        result = coaching_session_service._parse_json_from_response(response)

        assert result == {"core_values": ["honesty", "integrity"]}

    def test_parse_json_from_text_with_json(
        self,
        coaching_session_service: CoachingSessionService,
    ) -> None:
        """Test parsing JSON embedded in text."""
        response = (
            'Based on our conversation, here is the result: {"name": "Test"} and that is all.'
        )

        result = coaching_session_service._parse_json_from_response(response)

        assert result == {"name": "Test"}

    def test_parse_invalid_json_returns_empty(
        self,
        coaching_session_service: CoachingSessionService,
    ) -> None:
        """Test invalid JSON returns empty dict."""
        response = "This is not JSON at all"

        result = coaching_session_service._parse_json_from_response(response)

        assert result == {}
