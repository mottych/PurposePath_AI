import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from coaching.src.models.conversation import Conversation, Message
from coaching.src.models.prompt import LLMConfig, PromptTemplate
from coaching.src.models.responses import (
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from coaching.src.services.multitenant_conversation_service import MultitenantConversationService

from shared.models.multitenant import CoachingTopic as SharedCoachingTopic
from shared.models.multitenant import RequestContext


class TestMultitenantConversationService:
    @pytest.fixture
    def mock_context(self):
        return RequestContext(
            tenant_id="tenant-123",
            user_id="user-123",
            request_id="req-123",
            correlation_id="corr-123",
            role="member",
        )

    @pytest.fixture
    def mock_repos(self):
        return {
            "conversation": Mock(),
            "llm": Mock(),
            "cache": Mock(),
            "prompt": Mock(),
            "session": Mock(),
            "business": Mock(),
            "user_prefs": Mock(),
        }

    @pytest.fixture
    def service(self, mock_context, mock_repos):
        with (
            patch(
                "coaching.src.services.multitenant_conversation_service.CoachingSessionRepository"
            ) as mock_session_repo,
            patch(
                "coaching.src.services.multitenant_conversation_service.BusinessDataRepository"
            ) as mock_business_repo,
            patch(
                "coaching.src.services.multitenant_conversation_service.UserPreferencesRepository"
            ) as mock_user_prefs_repo,
        ):
            mock_session_repo.return_value = mock_repos["session"]
            mock_business_repo.return_value = mock_repos["business"]
            mock_user_prefs_repo.return_value = mock_repos["user_prefs"]

            service = MultitenantConversationService(
                context=mock_context,
                conversation_repository=mock_repos["conversation"],
                llm_service=mock_repos["llm"],
                cache_service=mock_repos["cache"],
                prompt_service=mock_repos["prompt"],
            )
            return service

    @pytest.mark.asyncio
    async def test_initiate_conversation_success(self, service, mock_repos):
        # Arrange
        topic = SharedCoachingTopic.GOALS
        mock_repos["business"].get_by_tenant = Mock(return_value=None)
        mock_repos["user_prefs"].get_by_user_id = Mock(return_value=None)

        mock_template = Mock(spec=PromptTemplate)
        mock_template.initial_message = "Hello!"
        mock_template.version = "1.0"
        mock_template.llm_config = Mock(spec=LLMConfig)
        mock_template.llm_config.model_dump.return_value = {}

        mock_repos["prompt"].get_template = AsyncMock(return_value=mock_template)

        # Fix: Mock get_by_user_and_topic to return empty list (no existing sessions)
        mock_repos["session"].get_by_user_and_topic = Mock(return_value=[])

        mock_session_data = {
            "session_id": str(uuid.uuid4()),
            "tenant_id": "tenant-123",
            "user_id": "user-123",
            "topic": topic.value,
            "status": "active",
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        mock_repos["session"].create = Mock(return_value=mock_session_data)
        mock_repos["session"].update = Mock()

        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = mock_session_data["session_id"]
        mock_conversation.status = "active"
        mock_conversation.calculate_progress.return_value = 0
        mock_conversation.context = {"current_phase": "introduction"}
        mock_conversation.messages = [Message(role="assistant", content="Hello!")]

        mock_repos["conversation"].create = AsyncMock(return_value=mock_conversation)
        mock_repos["cache"].save_session_data = AsyncMock()

        # Act
        response = await service.initiate_conversation(topic)

        # Assert
        assert isinstance(response, ConversationResponse)
        assert response.conversation_id == mock_session_data["session_id"]
        assert response.current_question == "Hello!"
        mock_repos["session"].create.assert_called_once()
        mock_repos["conversation"].create.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_success(self, service, mock_repos):
        # Arrange
        conversation_id = str(uuid.uuid4())
        message = "My goal is to grow revenue."

        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = conversation_id
        mock_conversation.topic = SharedCoachingTopic.GOALS.value
        mock_conversation.context = {"tenant_id": "tenant-123", "current_phase": "exploration"}
        mock_conversation.get_conversation_history.return_value = []
        mock_conversation.calculate_progress.return_value = 0.1

        mock_repos["conversation"].get = AsyncMock(return_value=mock_conversation)
        mock_repos["conversation"].add_message = AsyncMock()

        mock_repos["cache"].get_session_data = AsyncMock(
            return_value={
                "topic": SharedCoachingTopic.GOALS.value,
                "business_context": {},
                "user_preferences": {},
                "session_id": "session-123",
            }
        )

        mock_ai_response = Mock()
        mock_ai_response.response = "That's a great goal."
        mock_ai_response.metadata = {}
        mock_ai_response.insights = []
        mock_ai_response.token_usage = 100
        mock_ai_response.model_id = "claude-3"
        mock_ai_response.is_complete = False
        mock_ai_response.follow_up_question = "How?"
        mock_ai_response.cost = 0.01

        mock_repos["llm"].generate_coaching_response = AsyncMock(return_value=mock_ai_response)
        mock_repos["business"].get_by_tenant = Mock(return_value=None)
        mock_repos["session"].get_by_id = Mock(return_value={})
        mock_repos["session"].update = Mock()

        # Act
        response = await service.process_message(conversation_id, message)

        # Assert
        assert isinstance(response, MessageResponse)
        assert response.ai_response == "That's a great goal."
        mock_repos["llm"].generate_coaching_response.assert_called_once()
        mock_repos["conversation"].add_message.assert_called()

    @pytest.mark.asyncio
    async def test_get_conversation(self, service, mock_repos):
        # Arrange
        conversation_id = str(uuid.uuid4())
        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = conversation_id
        mock_conversation.messages = [Message(role="assistant", content="Hello")]
        mock_conversation.created_at = datetime.now(UTC)
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation.status = "active"
        mock_conversation.topic = SharedCoachingTopic.GOALS.value
        mock_conversation.context = {"tenant_id": "tenant-123", "current_phase": "exploration"}
        mock_conversation.calculate_progress.return_value = 0.5

        mock_repos["conversation"].get = AsyncMock(return_value=mock_conversation)
        mock_repos["cache"].get_session_data = AsyncMock(return_value={"session_id": "sess-123"})

        # Act
        response = await service.get_conversation(conversation_id)

        # Assert
        assert isinstance(response, ConversationResponse)
        assert response.conversation_id == conversation_id
        mock_repos["conversation"].get.assert_called_once_with(conversation_id)

    @pytest.mark.asyncio
    async def test_list_user_conversations(self, service, mock_repos):
        # Arrange
        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = str(uuid.uuid4())
        mock_conversation.topic = SharedCoachingTopic.GOALS.value
        mock_conversation.status = "active"
        mock_conversation.created_at = datetime.now(UTC)
        mock_conversation.updated_at = datetime.now(UTC)
        mock_conversation.messages = []
        mock_conversation.calculate_progress.return_value = 0

        mock_repos["conversation"].list_by_user = AsyncMock(return_value=[mock_conversation])

        # Act
        response = await service.list_user_conversations(page=1, page_size=10)

        # Assert
        assert isinstance(response, ConversationListResponse)
        assert len(response.conversations) == 1
        assert response.conversations[0].conversation_id == mock_conversation.conversation_id
        mock_repos["conversation"].list_by_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_conversation_success(self, service, mock_repos):
        # Arrange
        conversation_id = str(uuid.uuid4())
        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = conversation_id
        mock_conversation.topic = SharedCoachingTopic.GOALS.value
        mock_conversation.context = {"tenant_id": "tenant-123"}
        mock_conversation.mark_completed = Mock()

        mock_repos["conversation"].get = AsyncMock(return_value=mock_conversation)
        mock_repos["conversation"].update = AsyncMock()

        mock_repos["cache"].get_session_data = AsyncMock(return_value={"session_id": "session-123"})

        mock_repos["session"].update = Mock()
        mock_repos["session"].get_by_id = Mock(return_value={"outcomes": None})

        mock_repos["business"].get_by_tenant = Mock(return_value=None)

        # Mock _extract_and_save_outcomes implicitly by mocking what it calls or just let it run if mocked enough
        # Since it's a private method, we might want to mock the LLM service call it makes
        mock_outcomes = Mock()
        mock_outcomes.success = True
        mock_outcomes.confidence = 0.9
        mock_outcomes.to_dict.return_value = {"extracted_data": "some data"}
        mock_repos["llm"].extract_session_outcomes = AsyncMock(return_value=mock_outcomes)

        # Act
        response = await service.complete_conversation(conversation_id)

        # Assert
        assert response["conversation_id"] == conversation_id
        assert response["session_id"] == "session-123"
        mock_conversation.mark_completed.assert_called_once()
        mock_repos["conversation"].update.assert_called_once()
        mock_repos["session"].update.assert_called()

    @pytest.mark.asyncio
    async def test_initiate_conversation_limit_reached(self, service, mock_repos):
        # Arrange
        topic = SharedCoachingTopic.GOALS

        # Mock session limits check
        # We need to mock settings.coaching_topics.get to return a limit
        # Since settings is imported in the service, we might need to patch it or mock the repo call result
        # The service calls self.coaching_session_repo.get_by_user_and_topic

        # Let's assume we can trigger the limit by returning enough sessions
        # But we need to make sure the limit is > 0 in settings.
        # If we can't easily patch settings, we might skip this or try to patch it.

        with patch(
            "coaching.src.services.multitenant_conversation_service.settings"
        ) as mock_settings:
            mock_settings.coaching_topics.get.return_value = {"max_sessions_per_user": 1}

            mock_repos["session"].get_by_user_and_topic = Mock(
                return_value=[{"status": "active"}]  # 1 active session, limit is 1 -> should fail
            )

            # Act & Assert
            with pytest.raises(ValueError, match="Maximum 1 sessions allowed"):
                await service.initiate_conversation(topic)

    def test_get_business_data_summary(self, service, mock_repos):
        # Arrange
        mock_business_data = Mock()
        mock_business_data.model_dump.return_value = {
            "core_values": ["Integrity"],
            "purpose": "To serve",
            "vision": "A better world",
            "goals": ["Growth"],
            "updated_at": "2023-01-01",
            "version": "1.0",
        }
        mock_repos["business"].get_by_tenant = Mock(return_value=mock_business_data)

        # Act
        summary = service.get_business_data_summary()

        # Assert
        assert summary["core_values"] == ["Integrity"]
        assert summary["version"] == "1.0"
        mock_repos["business"].get_by_tenant.assert_called_once()
