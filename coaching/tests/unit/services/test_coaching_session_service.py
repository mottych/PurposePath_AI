"""Unit tests for CoachingSessionService.

Tests the application layer service that orchestrates coaching sessions.
Per spec requirement: 75%+ coverage for application layer.

Test Cases per spec (section 10.1):
    - test_initiate_creates_new_session
    - test_initiate_resumes_existing_session
    - test_initiate_blocks_different_user (Issue #157 - deferred)
    - test_add_message_validates_ownership
    - test_add_message_checks_idle_timeout
    - test_complete_triggers_extraction
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from coaching.src.core.constants import ConversationStatus, TopicCategory, TopicType
from coaching.src.core.topic_registry import (
    TemplateType,
    TopicDefinition,
)
from coaching.src.core.types import SessionId, TenantId, UserId
from coaching.src.domain.entities.coaching_session import CoachingSession
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.exceptions import (
    MaxTurnsReachedError,
    SessionAccessDeniedError,
    SessionIdleTimeoutError,
    SessionNotActiveError,
    SessionNotFoundError,
)
from coaching.src.services.coaching_session_service import (
    CoachingSessionService,
    InvalidTopicError,
    MessageResponse,
    ResponseMetadata,
    SessionCompletionResponse,
    SessionResponse,
    TopicNotActiveError,
)


class TestCoachingSessionService:
    """Tests for CoachingSessionService public methods."""

    @pytest.fixture
    def mock_session_repository(self) -> AsyncMock:
        """Create a mock session repository."""
        repo = AsyncMock()
        repo.get_active_for_user_topic = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.get_by_id_for_tenant = AsyncMock(return_value=None)
        repo.get_by_user = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_topic_repository(self) -> AsyncMock:
        """Create a mock topic repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def mock_s3_prompt_storage(self) -> AsyncMock:
        """Create a mock S3 prompt storage."""
        storage = AsyncMock()
        storage.get_prompt = AsyncMock()
        return storage

    @pytest.fixture
    def mock_template_processor(self) -> AsyncMock:
        """Create a mock template processor."""
        processor = AsyncMock()
        result = Mock()
        result.parameters = {}
        processor.process_template_parameters = AsyncMock(return_value=result)
        return processor

    @pytest.fixture
    def mock_provider_factory(self) -> Mock:
        """Create a mock LLM provider factory."""
        factory = Mock()
        # Mock provider returned by get_provider_for_model
        mock_provider = AsyncMock()
        mock_llm_response = Mock()
        mock_llm_response.content = "Hello! I'm your coach."
        mock_llm_response.model = "claude-3-haiku"
        mock_llm_response.usage = {"total_tokens": 100}
        mock_llm_response.finish_reason = "stop"
        mock_provider.generate = AsyncMock(return_value=mock_llm_response)

        factory.get_provider_for_model = Mock(return_value=(mock_provider, "claude-3-haiku"))
        return factory

    @pytest.fixture
    def sample_endpoint_definition(self) -> TopicDefinition:
        """Create a sample endpoint definition."""
        return TopicDefinition(
            topic_id="core_values",
            description="Discover your core values",
            topic_type=TopicType.CONVERSATION_COACHING,
            category=TopicCategory.STRATEGIC_PLANNING,
            templates={
                TemplateType.SYSTEM: "system.md",
                TemplateType.INITIATION: "initiation.md",
                TemplateType.RESUME: "resume.md",
            },
            result_model="CoreValuesResult",
            is_active=True,
        )

    @pytest.fixture
    def sample_llm_topic(self) -> LLMTopic:
        """Create a sample LLM topic configuration."""
        return LLMTopic(
            topic_id="core_values",
            topic_name="Core Values Discovery",
            topic_type="conversation_coaching",
            category="strategic_planning",
            basic_model_code="claude-haiku",
            premium_model_code="claude-haiku",
            is_active=True,
            max_tokens=2000,
            temperature=0.7,
            additional_config={
                "max_turns": 10,
                "idle_timeout_minutes": 30,
                "session_ttl_hours": 336,
            },
        )

    @pytest.fixture
    def sample_session(self) -> CoachingSession:
        """Create a sample coaching session."""
        session = CoachingSession(
            session_id=SessionId("test-session-123"),
            tenant_id=TenantId("tenant-123"),
            topic_id="core_values",
            user_id=UserId("user-123"),
            status=ConversationStatus.ACTIVE,
            max_turns=10,
            idle_timeout_minutes=30,
            expires_at=datetime.now(UTC) + timedelta(hours=336),
            context={"company_name": "Acme Corp"},
        )
        session.add_assistant_message("Welcome! Let's discover your core values.")
        return session

    @pytest.fixture
    def service(
        self,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        mock_template_processor: AsyncMock,
        mock_provider_factory: Mock,
    ) -> CoachingSessionService:
        """Create a coaching session service with mocked dependencies."""
        # Mock the topic index building
        with patch.object(CoachingSessionService, "_build_topic_index"):
            svc = CoachingSessionService(
                session_repository=mock_session_repository,
                topic_repository=mock_topic_repository,
                s3_prompt_storage=mock_s3_prompt_storage,
                template_processor=mock_template_processor,
                provider_factory=mock_provider_factory,
            )
            # Manually set up topic index
            svc._topic_index = {}
            return svc

    # =========================================================================
    # get_or_create_session Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_initiate_creates_new_session(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
    ) -> None:
        """Test that initiating a session creates a new one when none exists."""
        # Arrange
        service._topic_index["core_values"] = sample_endpoint_definition
        mock_topic_repository.get.return_value = sample_llm_topic
        mock_s3_prompt_storage.get_prompt.side_effect = [
            "You are a coaching assistant.",  # system template
            "Let's begin the coaching session.",  # initiation template
        ]
        mock_session_repository.get_active_for_user_topic.return_value = None

        # Act
        response = await service.get_or_create_session(
            topic_id="core_values",
            tenant_id="tenant-123",
            user_id="user-123",
            context={},
        )

        # Assert
        assert isinstance(response, SessionResponse)
        assert response.topic_id == "core_values"
        assert response.status == ConversationStatus.ACTIVE
        assert response.resumed is False
        # Turn is 0 after first assistant message (turn counts user messages)
        assert response.turn == 0
        assert response.max_turns == 10
        assert response.is_final is False
        assert response.metadata is not None
        assert response.metadata.model == "claude-3-haiku"

        # Verify repository was called to create
        mock_session_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_resumes_existing_session(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
        sample_session: CoachingSession,
    ) -> None:
        """Test that initiating when session exists resumes it instead."""
        # Arrange
        service._topic_index["core_values"] = sample_endpoint_definition
        mock_topic_repository.get.return_value = sample_llm_topic
        mock_session_repository.get_active_for_user_topic.return_value = sample_session
        mock_s3_prompt_storage.get_prompt.side_effect = [
            "Let's continue where we left off.",  # resume template
            "You are a coaching assistant.",  # system template
        ]

        # Act
        response = await service.get_or_create_session(
            topic_id="core_values",
            tenant_id="tenant-123",
            user_id="user-123",
        )

        # Assert
        assert isinstance(response, SessionResponse)
        assert response.resumed is True
        assert response.session_id == "test-session-123"

        # Verify create was NOT called (session exists)
        mock_session_repository.create.assert_not_called()
        # Verify update was called for resume
        mock_session_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_initiate_invalid_topic_raises_error(
        self,
        service: CoachingSessionService,
    ) -> None:
        """Test that initiating with invalid topic raises InvalidTopicError."""
        # Arrange - topic not in index
        service._topic_index = {}

        # Act & Assert
        with pytest.raises(InvalidTopicError) as exc_info:
            await service.get_or_create_session(
                topic_id="nonexistent_topic",
                tenant_id="tenant-123",
                user_id="user-123",
            )

        assert exc_info.value.topic_id == "nonexistent_topic"
        assert "not found" in exc_info.value.reason.lower()

    @pytest.mark.asyncio
    async def test_initiate_inactive_topic_raises_error(
        self,
        service: CoachingSessionService,
        mock_topic_repository: AsyncMock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
    ) -> None:
        """Test that initiating with inactive topic raises TopicNotActiveError."""
        # Arrange
        from dataclasses import replace

        service._topic_index["core_values"] = sample_endpoint_definition
        inactive_topic = replace(sample_llm_topic, is_active=False)
        mock_topic_repository.get.return_value = inactive_topic

        # Act & Assert
        with pytest.raises(TopicNotActiveError) as exc_info:
            await service.get_or_create_session(
                topic_id="core_values",
                tenant_id="tenant-123",
                user_id="user-123",
            )

        assert exc_info.value.topic_id == "core_values"

    @pytest.mark.asyncio
    async def test_initiate_race_condition_same_user_returns_existing_session(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
        sample_session: CoachingSession,
    ) -> None:
        """Test idempotent behavior: race condition with same user returns existing session.

        Issue #179: When a user retries after timeout, and a race condition causes
        SessionConflictError (because first request completed after second request
        started), the service should return the existing session with resumed=True
        instead of failing with a 500 error.

        Scenario:
        1. First request starts creating session
        2. Second request (retry) also starts, sees no existing session
        3. First request completes, saves session
        4. Second request tries to save -> SessionConflictError with same user_id
        5. Expected: Return existing session, NOT raise error
        """
        from coaching.src.domain.exceptions import SessionConflictError

        # Arrange
        service._topic_index["core_values"] = sample_endpoint_definition
        mock_topic_repository.get.return_value = sample_llm_topic
        mock_s3_prompt_storage.get_prompt.side_effect = [
            "You are a coaching assistant.",  # system template
            "Let's begin the coaching session.",  # initiation template
        ]
        # First check returns None (race condition - session being created)
        mock_session_repository.get_active_for_user_topic.return_value = None

        # When create() is called, raise SessionConflictError with existing session
        # This simulates the race condition where another request created the session
        mock_session_repository.create.side_effect = SessionConflictError(
            topic_id="core_values",
            tenant_id="tenant-123",
            requesting_user_id="user-123",
            owning_user_id="user-123",  # Same user - this is a retry!
            existing_session=sample_session,
        )

        # Act
        response = await service.get_or_create_session(
            topic_id="core_values",
            tenant_id="tenant-123",
            user_id="user-123",
            context={},
        )

        # Assert - should return existing session, not raise error
        assert isinstance(response, SessionResponse)
        assert response.resumed is True  # Key assertion for idempotent behavior
        assert response.session_id == str(sample_session.session_id)
        assert response.topic_id == "core_values"
        assert response.status == sample_session.status
        # Should NOT have called update (just returning existing session)

    @pytest.mark.asyncio
    async def test_initiate_race_condition_different_user_raises_conflict(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
        sample_session: CoachingSession,
    ) -> None:
        """Test that SessionConflictError is raised when different user owns session.

        Issue #157: When a different user has an active session for the same topic,
        the service should raise SessionConflictError for proper 409 handling.

        This is NOT idempotent - this is a legitimate conflict that should error.
        """
        from coaching.src.domain.exceptions import SessionConflictError

        # Arrange
        service._topic_index["core_values"] = sample_endpoint_definition
        mock_topic_repository.get.return_value = sample_llm_topic
        mock_s3_prompt_storage.get_prompt.side_effect = [
            "You are a coaching assistant.",  # system template
            "Let's begin the coaching session.",  # initiation template
        ]
        mock_session_repository.get_active_for_user_topic.return_value = None

        # When create() is called, raise SessionConflictError with DIFFERENT user
        mock_session_repository.create.side_effect = SessionConflictError(
            topic_id="core_values",
            tenant_id="tenant-123",
            requesting_user_id="user-456",  # Different user attempting!
            owning_user_id="user-123",  # Original owner
            existing_session=sample_session,
        )

        # Act & Assert - should raise SessionConflictError for API layer
        with pytest.raises(SessionConflictError) as exc_info:
            await service.get_or_create_session(
                topic_id="core_values",
                tenant_id="tenant-123",
                user_id="user-456",  # Different user
                context={},
            )

        assert exc_info.value.topic_id == "core_values"
        assert exc_info.value.owning_user_id == "user-123"
        assert exc_info.value.requesting_user_id == "user-456"

    # =========================================================================
    # send_message Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_send_message_success(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
        sample_session: CoachingSession,
    ) -> None:
        """Test sending a message successfully returns response."""
        # Arrange
        service._topic_index["core_values"] = sample_endpoint_definition
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session
        mock_topic_repository.get.return_value = sample_llm_topic
        mock_s3_prompt_storage.get_prompt.return_value = "You are a coaching assistant."

        # Act
        response = await service.send_message(
            session_id="test-session-123",
            tenant_id="tenant-123",
            user_id="user-123",
            user_message="I value honesty and integrity.",
        )

        # Assert
        assert isinstance(response, MessageResponse)
        assert response.session_id == "test-session-123"
        assert response.status == ConversationStatus.ACTIVE
        assert response.message  # Has coach response
        assert response.metadata is not None
        mock_session_repository.update.assert_called()

    @pytest.mark.asyncio
    async def test_send_message_validates_ownership(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test that sending message with wrong user raises SessionAccessDeniedError."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act & Assert - different user trying to send message
        with pytest.raises(SessionAccessDeniedError):
            await service.send_message(
                session_id="test-session-123",
                tenant_id="tenant-123",
                user_id="different-user-456",  # Not the session owner
                user_message="Hello",
            )

    @pytest.mark.asyncio
    async def test_send_message_session_not_found(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test that sending message to nonexistent session raises SessionNotFoundError."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = None

        # Act & Assert
        with pytest.raises(SessionNotFoundError):
            await service.send_message(
                session_id="nonexistent-session",
                tenant_id="tenant-123",
                user_id="user-123",
                user_message="Hello",
            )

    @pytest.mark.asyncio
    async def test_send_message_checks_idle_timeout(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test that sending message to idle session raises SessionIdleTimeoutError."""
        # Arrange - session with old last_activity_at
        idle_session = CoachingSession(
            session_id=SessionId("idle-session"),
            tenant_id=TenantId("tenant-123"),
            topic_id="core_values",
            user_id=UserId("user-123"),
            status=ConversationStatus.ACTIVE,
            max_turns=10,
            idle_timeout_minutes=30,
            expires_at=datetime.now(UTC) + timedelta(hours=336),
            last_activity_at=datetime.now(UTC) - timedelta(minutes=60),  # 60 min ago
        )
        mock_session_repository.get_by_id_for_tenant.return_value = idle_session

        # Act & Assert
        with pytest.raises(SessionIdleTimeoutError):
            await service.send_message(
                session_id="idle-session",
                tenant_id="tenant-123",
                user_id="user-123",
                user_message="Hello",
            )

    @pytest.mark.asyncio
    async def test_send_message_not_active_session(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test that sending message to paused/completed session raises SessionNotActiveError."""
        # Arrange - paused session
        paused_session = CoachingSession(
            session_id=SessionId("paused-session"),
            tenant_id=TenantId("tenant-123"),
            topic_id="core_values",
            user_id=UserId("user-123"),
            status=ConversationStatus.PAUSED,
            max_turns=10,
            idle_timeout_minutes=30,
            expires_at=datetime.now(UTC) + timedelta(hours=336),
        )
        mock_session_repository.get_by_id_for_tenant.return_value = paused_session

        # Act & Assert
        with pytest.raises(SessionNotActiveError):
            await service.send_message(
                session_id="paused-session",
                tenant_id="tenant-123",
                user_id="user-123",
                user_message="Hello",
            )

    @pytest.mark.asyncio
    async def test_send_message_max_turns_reached(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
    ) -> None:
        """Test that sending message when max turns reached raises MaxTurnsReachedError."""
        # Arrange - session at max turns
        at_limit_session = CoachingSession(
            session_id=SessionId("at-limit-session"),
            tenant_id=TenantId("tenant-123"),
            topic_id="core_values",
            user_id=UserId("user-123"),
            status=ConversationStatus.ACTIVE,
            max_turns=2,  # Low max
            idle_timeout_minutes=30,
            expires_at=datetime.now(UTC) + timedelta(hours=336),
        )
        # Add messages to reach the limit (2 turns = 4 messages: user/assistant/user/assistant)
        at_limit_session.add_user_message("Message 1")
        at_limit_session.add_assistant_message("Response 1")
        at_limit_session.add_user_message("Message 2")
        at_limit_session.add_assistant_message("Response 2")

        service._topic_index["core_values"] = sample_endpoint_definition
        mock_session_repository.get_by_id_for_tenant.return_value = at_limit_session
        mock_topic_repository.get.return_value = sample_llm_topic
        mock_s3_prompt_storage.get_prompt.return_value = "You are a coach."

        # Act & Assert
        with pytest.raises(MaxTurnsReachedError):
            await service.send_message(
                session_id="at-limit-session",
                tenant_id="tenant-123",
                user_id="user-123",
                user_message="One more message",
            )

    # =========================================================================
    # complete_session Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_complete_session_triggers_extraction(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        mock_topic_repository: AsyncMock,
        mock_s3_prompt_storage: AsyncMock,
        mock_provider_factory: Mock,
        sample_endpoint_definition: TopicDefinition,
        sample_llm_topic: LLMTopic,
        sample_session: CoachingSession,
    ) -> None:
        """Test that completing a session triggers result extraction."""
        # Arrange
        service._topic_index["core_values"] = sample_endpoint_definition
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session
        mock_topic_repository.get.return_value = sample_llm_topic
        mock_s3_prompt_storage.get_prompt.return_value = "You are a coach."

        # Mock extraction response - valid JSON
        extraction_response = Mock()
        extraction_response.content = '{"core_values": ["honesty", "integrity"]}'
        extraction_response.model = "claude-3-haiku"
        extraction_response.usage = {"total_tokens": 50}
        extraction_response.finish_reason = "stop"

        mock_provider = AsyncMock()
        mock_provider.generate = AsyncMock(return_value=extraction_response)
        mock_provider_factory.get_provider_for_model.return_value = (
            mock_provider,
            "claude-3-haiku",
        )

        # Act
        response = await service.complete_session(
            session_id="test-session-123",
            tenant_id="tenant-123",
            user_id="user-123",
        )

        # Assert
        assert isinstance(response, SessionCompletionResponse)
        assert response.session_id == "test-session-123"
        assert response.status == ConversationStatus.COMPLETED
        # Result should contain something (either extracted data or raw_response)
        assert response.result is not None
        assert len(response.result) > 0
        mock_session_repository.update.assert_called()

    @pytest.mark.asyncio
    async def test_complete_session_validates_ownership(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test that completing session with wrong user raises error."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act & Assert
        with pytest.raises(SessionAccessDeniedError):
            await service.complete_session(
                session_id="test-session-123",
                tenant_id="tenant-123",
                user_id="different-user",  # Not the owner
            )

    # =========================================================================
    # pause_session Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_pause_session_success(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test pausing a session successfully."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act
        response = await service.pause_session(
            session_id="test-session-123",
            tenant_id="tenant-123",
            user_id="user-123",
        )

        # Assert
        assert response.status == ConversationStatus.PAUSED
        mock_session_repository.update.assert_called()

    @pytest.mark.asyncio
    async def test_pause_session_validates_ownership(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test that pausing with wrong user raises error."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act & Assert
        with pytest.raises(SessionAccessDeniedError):
            await service.pause_session(
                session_id="test-session-123",
                tenant_id="tenant-123",
                user_id="different-user",
            )

    # =========================================================================
    # cancel_session Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_cancel_session_success(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test cancelling a session successfully."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act
        response = await service.cancel_session(
            session_id="test-session-123",
            tenant_id="tenant-123",
            user_id="user-123",
        )

        # Assert
        assert response.status == ConversationStatus.CANCELLED
        mock_session_repository.update.assert_called()

    # =========================================================================
    # get_session Tests
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_session_returns_details(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test getting session details returns SessionDetails."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act
        response = await service.get_session(
            session_id="test-session-123",
            tenant_id="tenant-123",
            user_id="user-123",
        )

        # Assert
        assert response.session_id == "test-session-123"
        assert response.topic_id == "core_values"
        assert len(response.messages) == 1  # One assistant message

    @pytest.mark.asyncio
    async def test_get_session_not_found_raises_error(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
    ) -> None:
        """Test getting nonexistent session raises SessionNotFoundError."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = None

        # Act & Assert
        with pytest.raises(SessionNotFoundError):
            await service.get_session(
                session_id="nonexistent",
                tenant_id="tenant-123",
                user_id="user-123",
            )

    @pytest.mark.asyncio
    async def test_get_session_validates_ownership(
        self,
        service: CoachingSessionService,
        mock_session_repository: AsyncMock,
        sample_session: CoachingSession,
    ) -> None:
        """Test getting session with wrong user raises error."""
        # Arrange
        mock_session_repository.get_by_id_for_tenant.return_value = sample_session

        # Act & Assert
        with pytest.raises(SessionAccessDeniedError):
            await service.get_session(
                session_id="test-session-123",
                tenant_id="tenant-123",
                user_id="different-user",
            )


class TestResponseMetadata:
    """Tests for ResponseMetadata model."""

    def test_response_metadata_defaults(self) -> None:
        """Test ResponseMetadata has correct defaults."""
        metadata = ResponseMetadata(model="claude-3-haiku")
        assert metadata.model == "claude-3-haiku"
        assert metadata.processing_time_ms == 0
        assert metadata.tokens_used == 0

    def test_response_metadata_with_values(self) -> None:
        """Test ResponseMetadata with explicit values."""
        metadata = ResponseMetadata(
            model="claude-3-sonnet",
            processing_time_ms=500,
            tokens_used=1500,
        )
        assert metadata.model == "claude-3-sonnet"
        assert metadata.processing_time_ms == 500
        assert metadata.tokens_used == 1500


class TestSessionResponse:
    """Tests for SessionResponse model."""

    def test_session_response_new_session(self) -> None:
        """Test SessionResponse for new session."""
        response = SessionResponse(
            session_id="sess-123",
            tenant_id="tenant-123",
            topic_id="core_values",
            status=ConversationStatus.ACTIVE,
            message="Hello!",
            turn=1,
            max_turns=10,
            is_final=False,
            resumed=False,
        )
        assert response.resumed is False
        assert response.turn == 1
        assert response.is_final is False

    def test_session_response_resumed_session(self) -> None:
        """Test SessionResponse for resumed session."""
        response = SessionResponse(
            session_id="sess-123",
            tenant_id="tenant-123",
            topic_id="core_values",
            status=ConversationStatus.ACTIVE,
            message="Welcome back!",
            turn=5,
            max_turns=10,
            is_final=False,
            resumed=True,
        )
        assert response.resumed is True
        assert response.turn == 5


class TestMessageResponse:
    """Tests for MessageResponse model."""

    def test_message_response_not_final(self) -> None:
        """Test MessageResponse when not final."""
        response = MessageResponse(
            session_id="sess-123",
            message="Great insight!",
            status=ConversationStatus.ACTIVE,
            turn=3,
            max_turns=10,
            is_final=False,
            message_count=5,
        )
        assert response.is_final is False
        assert response.result is None

    def test_message_response_final_with_result(self) -> None:
        """Test MessageResponse when final includes result."""
        response = MessageResponse(
            session_id="sess-123",
            message="Session complete!",
            status=ConversationStatus.ACTIVE,
            turn=10,
            max_turns=10,
            is_final=True,
            message_count=20,
            result={"core_values": ["honesty", "integrity"]},
        )
        assert response.is_final is True
        assert response.result is not None
        assert "core_values" in response.result
