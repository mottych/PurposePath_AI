from unittest.mock import AsyncMock

import pytest
from coaching.src.application.conversation.conversation_service import (
    ConversationApplicationService,
)
from coaching.src.core.constants import CoachingTopic, ConversationStatus, MessageRole
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.exceptions.conversation_exceptions import (
    ConversationNotActive,
    ConversationNotFound,
)
from coaching.src.domain.ports.conversation_repository_port import ConversationRepositoryPort


@pytest.fixture
def mock_repo():
    return AsyncMock(spec=ConversationRepositoryPort)


@pytest.fixture
def service(mock_repo):
    return ConversationApplicationService(mock_repo)


@pytest.fixture
def user_id():
    return UserId("user_123")


@pytest.fixture
def tenant_id():
    return TenantId("tenant_456")


@pytest.fixture
def conversation_id():
    return ConversationId("conv_123")


@pytest.fixture
def sample_conversation(user_id, tenant_id, conversation_id):
    return Conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        tenant_id=tenant_id,
        topic=CoachingTopic.CORE_VALUES,
        metadata={},
    )


@pytest.mark.asyncio
class TestConversationApplicationService:
    async def test_start_conversation_success(self, service, mock_repo, user_id, tenant_id):
        # Arrange
        mock_repo.get_active_count.return_value = 0
        mock_repo.save.return_value = None

        # Act
        conversation = await service.start_conversation(
            user_id=user_id,
            tenant_id=tenant_id,
            topic=CoachingTopic.CORE_VALUES,
            initial_message_content="Hello",
        )

        # Assert
        assert conversation.user_id == user_id
        assert conversation.tenant_id == tenant_id
        assert conversation.topic == CoachingTopic.CORE_VALUES
        assert len(conversation.messages) == 1
        assert conversation.messages[0].role == MessageRole.ASSISTANT
        assert conversation.messages[0].content == "Hello"
        mock_repo.save.assert_called_once()

    async def test_start_conversation_limit_warning(self, service, mock_repo, user_id, tenant_id):
        # Arrange
        mock_repo.get_active_count.return_value = 5
        mock_repo.save.return_value = None

        # Act
        conversation = await service.start_conversation(
            user_id=user_id,
            tenant_id=tenant_id,
            topic=CoachingTopic.CORE_VALUES,
            initial_message_content="Hello",
        )

        # Assert
        assert conversation is not None
        mock_repo.save.assert_called_once()

    async def test_add_message_success(self, service, mock_repo, sample_conversation):
        # Arrange
        mock_repo.get_by_id.return_value = sample_conversation
        mock_repo.save.return_value = None

        # Act
        updated_conversation = await service.add_message(
            conversation_id=sample_conversation.conversation_id,
            tenant_id=sample_conversation.tenant_id,
            role=MessageRole.USER,
            content="User message",
        )

        # Assert
        assert len(updated_conversation.messages) == 1
        assert updated_conversation.messages[0].role == MessageRole.USER
        assert updated_conversation.messages[0].content == "User message"
        mock_repo.save.assert_called_once()

    async def test_add_message_not_found(self, service, mock_repo, conversation_id, tenant_id):
        # Arrange
        mock_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ConversationNotFound):
            await service.add_message(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                role=MessageRole.USER,
                content="User message",
            )

    async def test_add_message_not_active(self, service, mock_repo, sample_conversation):
        # Arrange
        from coaching.src.core.constants import ConversationPhase

        new_context = sample_conversation.context.model_copy(
            update={"current_phase": ConversationPhase.COMPLETION}
        )
        object.__setattr__(sample_conversation, "context", new_context)

        sample_conversation.mark_completed()
        mock_repo.get_by_id.return_value = sample_conversation

        # Act & Assert
        with pytest.raises(ConversationNotActive):
            await service.add_message(
                conversation_id=sample_conversation.conversation_id,
                tenant_id=sample_conversation.tenant_id,
                role=MessageRole.USER,
                content="User message",
            )

    async def test_get_conversation_success(self, service, mock_repo, sample_conversation):
        # Arrange
        mock_repo.get_by_id.return_value = sample_conversation

        # Act
        conversation = await service.get_conversation(
            conversation_id=sample_conversation.conversation_id,
            tenant_id=sample_conversation.tenant_id,
        )

        # Assert
        assert conversation == sample_conversation

    async def test_get_conversation_not_found(self, service, mock_repo, conversation_id, tenant_id):
        # Arrange
        mock_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ConversationNotFound):
            await service.get_conversation(conversation_id, tenant_id)

    async def test_list_user_conversations(
        self, service, mock_repo, user_id, tenant_id, sample_conversation
    ):
        # Arrange
        mock_repo.get_by_user.return_value = [sample_conversation]

        # Act
        conversations = await service.list_user_conversations(user_id=user_id, tenant_id=tenant_id)

        # Assert
        assert len(conversations) == 1
        assert conversations[0] == sample_conversation
        mock_repo.get_by_user.assert_called_once_with(
            user_id=user_id, tenant_id=tenant_id, limit=10, active_only=False
        )

    async def test_pause_conversation(self, service, mock_repo, sample_conversation):
        # Arrange
        mock_repo.get_by_id.return_value = sample_conversation
        mock_repo.save.return_value = None

        # Act
        conversation = await service.pause_conversation(
            conversation_id=sample_conversation.conversation_id,
            tenant_id=sample_conversation.tenant_id,
        )

        # Assert
        assert conversation.status == ConversationStatus.PAUSED
        mock_repo.save.assert_called_once()

    async def test_resume_conversation(self, service, mock_repo, sample_conversation):
        # Arrange
        sample_conversation.mark_paused()
        mock_repo.get_by_id.return_value = sample_conversation
        mock_repo.save.return_value = None

        # Act
        conversation = await service.resume_conversation(
            conversation_id=sample_conversation.conversation_id,
            tenant_id=sample_conversation.tenant_id,
        )

        # Assert
        assert conversation.status == ConversationStatus.ACTIVE
        mock_repo.save.assert_called_once()

    async def test_complete_conversation(self, service, mock_repo, sample_conversation):
        # Arrange
        from coaching.src.core.constants import ConversationPhase

        new_context = sample_conversation.context.model_copy(
            update={"current_phase": ConversationPhase.COMPLETION}
        )
        object.__setattr__(sample_conversation, "context", new_context)

        mock_repo.get_by_id.return_value = sample_conversation
        mock_repo.save.return_value = None

        # Act
        conversation = await service.complete_conversation(
            conversation_id=sample_conversation.conversation_id,
            tenant_id=sample_conversation.tenant_id,
        )

        # Assert
        assert conversation.status == ConversationStatus.COMPLETED
        mock_repo.save.assert_called_once()

    async def test_abandon_conversation(self, service, mock_repo, conversation_id, tenant_id):
        # Arrange
        mock_repo.delete.return_value = True

        # Act
        result = await service.abandon_conversation(conversation_id, tenant_id)

        # Assert
        assert result is True
        mock_repo.delete.assert_called_once_with(conversation_id, tenant_id)

    async def test_abandon_conversation_not_found(
        self, service, mock_repo, conversation_id, tenant_id
    ):
        # Arrange
        mock_repo.delete.return_value = False

        # Act
        result = await service.abandon_conversation(conversation_id, tenant_id)

        # Assert
        assert result is False
        mock_repo.delete.assert_called_once_with(conversation_id, tenant_id)
