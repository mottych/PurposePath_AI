from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from coaching.src.core.constants import CoachingTopic, ConversationStatus
from coaching.src.core.exceptions import ConversationNotFoundError
from coaching.src.domain.entities.prompt_template import PromptTemplate
from coaching.src.models.conversation import Conversation
from coaching.src.models.responses import ConversationResponse, MessageResponse
from coaching.src.services.conversation_service import ConversationService


class TestConversationService:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_llm_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cache_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_prompt_service(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo, mock_llm_service, mock_cache_service, mock_prompt_service):
        return ConversationService(
            conversation_repository=mock_repo,
            llm_service=mock_llm_service,
            cache_service=mock_cache_service,
            prompt_service=mock_prompt_service,
        )

    @pytest.fixture
    def sample_conversation(self):
        return Conversation(
            conversation_id="conv-123",
            user_id="user-123",
            topic="purpose",
            status=ConversationStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            messages=[],
            context={"current_phase": "discovery"},
        )

    @pytest.mark.asyncio
    async def test_initiate_conversation(
        self, service, mock_prompt_service, mock_repo, mock_cache_service
    ):
        # Arrange
        user_id = "user-123"
        topic = CoachingTopic.PURPOSE

        mock_template = Mock(spec=PromptTemplate)
        mock_template.initial_message = "Hello!"
        mock_template.version = "1.0"
        mock_template.llm_config = Mock()
        mock_template.llm_config.model_dump.return_value = {"model": "gpt-4"}

        mock_prompt_service.get_template.return_value = mock_template

        mock_conversation = Mock(spec=Conversation)
        mock_conversation.conversation_id = "conv-123"
        mock_conversation.status = ConversationStatus.ACTIVE
        mock_conversation.calculate_progress.return_value = 0
        mock_conversation.context = {"current_phase": "introduction"}

        mock_repo.create.return_value = mock_conversation

        # Act
        response = await service.initiate_conversation(user_id, topic)

        # Assert
        assert isinstance(response, ConversationResponse)
        assert response.conversation_id == "conv-123"
        assert response.current_question == "Hello!"

        mock_prompt_service.get_template.assert_called_once_with(topic.value)
        mock_repo.create.assert_called_once()
        mock_cache_service.save_session_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_message_success(
        self, service, mock_repo, mock_llm_service, sample_conversation
    ):
        # Arrange
        conversation_id = "conv-123"
        user_message = "My purpose is to help."

        mock_repo.get.return_value = sample_conversation

        mock_ai_response = Mock()
        mock_ai_response.response = "That's great!"
        mock_ai_response.follow_up_question = "How?"
        mock_ai_response.insights = ["Helpful"]
        mock_ai_response.is_complete = False
        mock_ai_response.token_usage = {"input": 10, "output": 20}
        mock_ai_response.model_id = "gpt-4"

        mock_llm_service.generate_coaching_response.return_value = mock_ai_response

        # Act
        response = await service.process_message(conversation_id, user_message)

        # Assert
        assert isinstance(response, MessageResponse)
        assert response.ai_response == "That's great!"

        mock_repo.get.assert_called()
        mock_repo.add_message.assert_called()
        assert mock_repo.add_message.call_count == 2  # User message + AI response

    @pytest.mark.asyncio
    async def test_process_message_not_found(self, service, mock_repo):
        # Arrange
        mock_repo.get.return_value = None

        # Act & Assert
        with pytest.raises(ConversationNotFoundError):
            await service.process_message("non-existent", "hello")

    @pytest.mark.asyncio
    async def test_get_conversation(self, service, mock_repo, sample_conversation):
        # Arrange
        mock_repo.get.return_value = sample_conversation

        # Act
        result = await service.get_conversation("conv-123")

        # Assert
        assert result == sample_conversation
        mock_repo.get.assert_called_once_with("conv-123")

    @pytest.mark.asyncio
    async def test_pause_conversation(self, service, mock_repo, sample_conversation):
        # Arrange
        mock_repo.get.return_value = sample_conversation

        # Act
        await service.pause_conversation("conv-123")

        # Assert
        # Since sample_conversation is a real object (not a mock), we can check its state if the method modifies it in place.
        # However, the service calls conversation.mark_paused() which is a method on the entity.
        # Let's verify repo.update was called.
        mock_repo.update.assert_called_once_with(sample_conversation)
        assert sample_conversation.status == ConversationStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_conversation(
        self, service, mock_repo, mock_prompt_service, sample_conversation
    ):
        # Arrange
        sample_conversation.status = ConversationStatus.PAUSED
        mock_repo.get.return_value = sample_conversation

        mock_template = Mock()
        mock_prompt_service.get_template.return_value = mock_template

        # Act
        response = await service.resume_conversation("conv-123")

        # Assert
        assert isinstance(response, ConversationResponse)
        assert sample_conversation.status == ConversationStatus.ACTIVE
        mock_repo.update.assert_called_once_with(sample_conversation)

    @pytest.mark.asyncio
    async def test_complete_conversation(self, service, mock_repo, sample_conversation):
        # Arrange
        mock_repo.get.return_value = sample_conversation

        # Act
        await service.complete_conversation("conv-123")

        # Assert
        assert sample_conversation.status == ConversationStatus.COMPLETED
        mock_repo.update.assert_called_once_with(sample_conversation)

    @pytest.mark.asyncio
    async def test_abandon_conversation(self, service, mock_repo):
        # Act
        await service.abandon_conversation("conv-123")

        # Assert
        mock_repo.delete.assert_called_once_with("conv-123")

    @pytest.mark.asyncio
    async def test_list_user_conversations(self, service, mock_repo, sample_conversation):
        # Arrange
        mock_repo.list_by_user.return_value = [sample_conversation]

        # Act
        response = await service.list_user_conversations("user-123")

        # Assert
        assert response.total == 1
        assert response.conversations[0].conversation_id == sample_conversation.conversation_id
        mock_repo.list_by_user.assert_called_once()
