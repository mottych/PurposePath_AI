from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from coaching.src.core.constants import (
    CoachingTopic,
    ConversationStatus,
    MessageRole,
)
from coaching.src.core.types import (
    ConversationId,
    create_tenant_id,
    create_user_id,
)
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.value_objects.conversation_context import ConversationContext
from coaching.src.domain.value_objects.message import Message
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)


@pytest.fixture
def mock_dynamodb_resource() -> MagicMock:
    resource = MagicMock()
    table = MagicMock()
    resource.Table.return_value = table
    return resource


@pytest.fixture
def mock_table(mock_dynamodb_resource: MagicMock) -> MagicMock:
    return mock_dynamodb_resource.Table.return_value


@pytest.fixture
def repository(mock_dynamodb_resource: MagicMock) -> DynamoDBConversationRepository:
    return DynamoDBConversationRepository(mock_dynamodb_resource, "test-table")


@pytest.fixture
def sample_conversation() -> Conversation:
    return Conversation(
        conversation_id=ConversationId("conv-123"),
        user_id=create_user_id("user-123"),
        tenant_id=create_tenant_id("tenant-123"),
        topic=CoachingTopic.GOALS,
        status=ConversationStatus.ACTIVE,
        messages=[
            Message(role=MessageRole.USER, content="Hello", timestamp=datetime.now(UTC)),
            Message(role=MessageRole.ASSISTANT, content="Hi", timestamp=datetime.now(UTC)),
        ],
        context=ConversationContext(),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        metadata={"key": "value"},
    )


@pytest.mark.asyncio
async def test_save_success(
    repository: DynamoDBConversationRepository,
    mock_table: MagicMock,
    sample_conversation: Conversation,
) -> None:
    # Act
    await repository.save(sample_conversation)

    # Assert
    mock_table.put_item.assert_called_once()
    call_args = mock_table.put_item.call_args
    item = call_args.kwargs["Item"]

    assert item["conversation_id"] == sample_conversation.conversation_id
    assert item["user_id"] == sample_conversation.user_id
    assert item["tenant_id"] == sample_conversation.tenant_id
    assert item["topic"] == sample_conversation.topic
    assert item["status"] == sample_conversation.status.value
    assert len(item["messages"]) == 2
    assert "ttl" in item


@pytest.mark.asyncio
async def test_save_error(
    repository: DynamoDBConversationRepository,
    mock_table: MagicMock,
    sample_conversation: Conversation,
) -> None:
    # Arrange
    mock_table.put_item.side_effect = Exception("DynamoDB Error")

    # Act & Assert
    with pytest.raises(Exception, match="DynamoDB Error"):
        await repository.save(sample_conversation)


@pytest.mark.asyncio
async def test_get_by_id_success(
    repository: DynamoDBConversationRepository,
    mock_table: MagicMock,
    sample_conversation: Conversation,
) -> None:
    # Arrange
    # Mock the item returned by DynamoDB
    # We need to manually construct the item dict as it would be stored
    item = repository._to_dynamodb_item(sample_conversation)
    mock_table.get_item.return_value = {"Item": item}

    # Act
    result = await repository.get_by_id(ConversationId("conv-123"), create_tenant_id("tenant-123"))

    # Assert
    assert result is not None
    assert result.conversation_id == sample_conversation.conversation_id
    assert result.user_id == sample_conversation.user_id
    assert len(result.messages) == 2


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    repository: DynamoDBConversationRepository, mock_table: MagicMock
) -> None:
    # Arrange
    mock_table.get_item.return_value = {}

    # Act
    result = await repository.get_by_id(ConversationId("conv-123"))

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_id_tenant_mismatch(
    repository: DynamoDBConversationRepository,
    mock_table: MagicMock,
    sample_conversation: Conversation,
) -> None:
    # Arrange
    item = repository._to_dynamodb_item(sample_conversation)
    mock_table.get_item.return_value = {"Item": item}

    # Act
    result = await repository.get_by_id(
        ConversationId("conv-123"), create_tenant_id("other-tenant")
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_success(repository, mock_table, sample_conversation):
    # Arrange
    item = repository._to_dynamodb_item(sample_conversation)
    mock_table.query.return_value = {"Items": [item]}

    # Act
    results = await repository.get_by_user("user-123", "tenant-123")

    # Assert
    assert len(results) == 1
    assert results[0].conversation_id == sample_conversation.conversation_id

    # Verify query params
    mock_table.query.assert_called_once()
    call_kwargs = mock_table.query.call_args.kwargs
    assert call_kwargs["IndexName"] == "user_id-index"
    assert call_kwargs["Limit"] == 10


@pytest.mark.asyncio
async def test_get_by_user_active_only(repository, mock_table):
    # Arrange
    mock_table.query.return_value = {"Items": []}

    # Act
    await repository.get_by_user("user-123", active_only=True)

    # Assert
    call_kwargs = mock_table.query.call_args.kwargs
    assert "FilterExpression" in call_kwargs
    # Note: Checking exact FilterExpression structure with boto3 conditions is tricky in mocks
    # We assume if FilterExpression is present, logic was triggered


@pytest.mark.asyncio
async def test_delete_success(repository, mock_table, sample_conversation):
    # Arrange
    # First get_by_id is called
    item = repository._to_dynamodb_item(sample_conversation)
    mock_table.get_item.return_value = {"Item": item}

    # Act
    result = await repository.delete("conv-123", "tenant-123")

    # Assert
    assert result is True
    mock_table.update_item.assert_called_once()
    call_kwargs = mock_table.update_item.call_args.kwargs
    assert call_kwargs["Key"] == {"conversation_id": "conv-123"}
    assert ":status" in call_kwargs["ExpressionAttributeValues"]
    assert call_kwargs["ExpressionAttributeValues"][":status"] == ConversationStatus.ABANDONED.value


@pytest.mark.asyncio
async def test_delete_not_found(repository, mock_table):
    # Arrange
    mock_table.get_item.return_value = {}

    # Act
    result = await repository.delete("conv-123")

    # Assert
    assert result is False
    mock_table.update_item.assert_not_called()


@pytest.mark.asyncio
async def test_exists(repository, mock_table, sample_conversation):
    # Arrange
    item = repository._to_dynamodb_item(sample_conversation)
    mock_table.get_item.return_value = {"Item": item}

    # Act
    exists = await repository.exists("conv-123")

    # Assert
    assert exists is True


@pytest.mark.asyncio
async def test_get_active_count(repository, mock_table, sample_conversation):
    # Arrange
    item = repository._to_dynamodb_item(sample_conversation)
    mock_table.query.return_value = {"Items": [item, item]}  # Return 2 items

    # Act
    count = await repository.get_active_count("user-123")

    # Assert
    assert count == 2
    call_kwargs = mock_table.query.call_args.kwargs
    assert call_kwargs["Limit"] == 100
