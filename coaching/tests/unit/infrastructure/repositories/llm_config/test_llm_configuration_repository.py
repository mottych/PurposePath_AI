from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from boto3.dynamodb.conditions import Attr
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.infrastructure.repositories.llm_config.llm_configuration_repository import (
    LLMConfigurationRepository,
)


class TestLLMConfigurationRepository:
    """Test suite for LLMConfigurationRepository."""

    @pytest.fixture
    def mock_dynamodb_resource(self):
        """Create a mock DynamoDB resource."""
        mock_resource = MagicMock()
        mock_table = MagicMock()
        mock_resource.Table.return_value = mock_table

        # Create a real exception class for the mock to use
        class ConditionalCheckFailedError(Exception):
            pass

        # Assign it to the mock's exceptions
        mock_resource.meta.client.exceptions.ConditionalCheckFailedException = (
            ConditionalCheckFailedError
        )

        return mock_resource

    @pytest.fixture
    def repository(self, mock_dynamodb_resource):
        """Create repository instance with mock DynamoDB."""
        return LLMConfigurationRepository(mock_dynamodb_resource, "test-table")

    @pytest.fixture
    def sample_config(self):
        """Create a sample LLMConfiguration entity."""
        return LLMConfiguration(
            config_id="cfg_123",
            interaction_code="COACHING_SESSION",
            template_id="tpl_456",
            model_code="gpt-4",
            tier="premium",
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            is_active=True,
            effective_from=datetime.now(UTC),
            effective_until=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="admin",
        )

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_dynamodb_resource, sample_config):
        """Test successful creation of a configuration."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        # Act
        result = await repository.create(sample_config)

        # Assert
        assert result == sample_config
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args
        assert call_args.kwargs["Item"]["config_id"] == sample_config.config_id
        assert "ConditionExpression" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_create_duplicate_id(self, repository, mock_dynamodb_resource, sample_config):
        """Test creation fails when ID already exists."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        # Use the custom exception class we defined in the fixture
        error_class = mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException
        mock_table.put_item.side_effect = error_class("Duplicate")

        # Act & Assert
        with pytest.raises(
            ValueError, match=f"Configuration ID already exists: {sample_config.config_id}"
        ):
            await repository.create(sample_config)

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, repository, mock_dynamodb_resource, sample_config):
        """Test successful retrieval by ID."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        # Mock DynamoDB item format
        item = {
            "config_id": sample_config.config_id,
            "interaction_code": sample_config.interaction_code,
            "template_id": sample_config.template_id,
            "model_code": sample_config.model_code,
            "tier": sample_config.tier,
            "temperature": str(sample_config.temperature),
            "max_tokens": sample_config.max_tokens,
            "top_p": str(sample_config.top_p),
            "frequency_penalty": str(sample_config.frequency_penalty),
            "presence_penalty": str(sample_config.presence_penalty),
            "is_active": sample_config.is_active,
            "effective_from": sample_config.effective_from.isoformat(),
            "effective_until": None,
            "created_at": sample_config.created_at.isoformat(),
            "updated_at": sample_config.updated_at.isoformat(),
            "created_by": sample_config.created_by,
        }
        mock_table.get_item.return_value = {"Item": item}

        # Act
        result = await repository.get_by_id(sample_config.config_id)

        # Assert
        assert result is not None
        assert result.config_id == sample_config.config_id
        assert result.interaction_code == sample_config.interaction_code
        mock_table.get_item.assert_called_once_with(Key={"config_id": sample_config.config_id})

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_dynamodb_resource):
        """Test retrieval returns None when not found."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value
        mock_table.get_item.return_value = {}

        # Act
        result = await repository.get_by_id("non_existent")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_dynamodb_resource, sample_config):
        """Test successful update."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        # Act
        result = await repository.update(sample_config)

        # Assert
        assert result == sample_config
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args
        assert call_args.kwargs["Item"]["config_id"] == sample_config.config_id
        assert "ConditionExpression" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_dynamodb_resource, sample_config):
        """Test update fails when configuration doesn't exist."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value
        error_class = mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException
        mock_table.put_item.side_effect = error_class("Not Found")

        # Act & Assert
        with pytest.raises(ValueError, match=f"Configuration not found: {sample_config.config_id}"):
            await repository.update(sample_config)

    @pytest.mark.asyncio
    async def test_delete_success(self, repository, mock_dynamodb_resource, sample_config):
        """Test successful deletion."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        # Act
        await repository.delete(sample_config.config_id)

        # Assert
        mock_table.delete_item.assert_called_once_with(
            Key={"config_id": sample_config.config_id},
            ConditionExpression=Attr("config_id").exists(),
        )

    @pytest.mark.asyncio
    async def test_delete_not_found(self, repository, mock_dynamodb_resource, sample_config):
        """Test deletion fails when configuration doesn't exist."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value
        error_class = mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException
        mock_table.delete_item.side_effect = error_class("Not Found")

        # Act & Assert
        with pytest.raises(ValueError, match=f"Configuration not found: {sample_config.config_id}"):
            await repository.delete(sample_config.config_id)

    @pytest.mark.asyncio
    async def test_deactivate_success(self, repository, mock_dynamodb_resource, sample_config):
        """Test successful deactivation."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        # Act
        await repository.deactivate(sample_config.config_id)

        # Assert
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert call_args.kwargs["Key"] == {"config_id": sample_config.config_id}
        assert ":inactive" in call_args.kwargs["ExpressionAttributeValues"]
        assert call_args.kwargs["ExpressionAttributeValues"][":inactive"] is False

    @pytest.mark.asyncio
    async def test_deactivate_not_found(self, repository, mock_dynamodb_resource, sample_config):
        """Test deactivation fails when configuration doesn't exist."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value
        error_class = mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException
        mock_table.update_item.side_effect = error_class("Not Found")

        # Act & Assert
        with pytest.raises(ValueError, match=f"Configuration not found: {sample_config.config_id}"):
            await repository.deactivate(sample_config.config_id)

    @pytest.mark.asyncio
    async def test_activate_success(self, repository, mock_dynamodb_resource, sample_config):
        """Test successful activation."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        # Act
        await repository.activate(sample_config.config_id)

        # Assert
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args
        assert call_args.kwargs["Key"] == {"config_id": sample_config.config_id}
        assert ":active" in call_args.kwargs["ExpressionAttributeValues"]
        assert call_args.kwargs["ExpressionAttributeValues"][":active"] is True

    @pytest.mark.asyncio
    async def test_activate_not_found(self, repository, mock_dynamodb_resource, sample_config):
        """Test activation fails when configuration doesn't exist."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value
        error_class = mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException
        mock_table.update_item.side_effect = error_class("Not Found")

        # Act & Assert
        with pytest.raises(ValueError, match=f"Configuration not found: {sample_config.config_id}"):
            await repository.activate(sample_config.config_id)

    @pytest.mark.asyncio
    async def test_list_all_with_filters(self, repository, mock_dynamodb_resource, sample_config):
        """Test listing with filters."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        item = {
            "config_id": sample_config.config_id,
            "interaction_code": sample_config.interaction_code,
            "template_id": sample_config.template_id,
            "model_code": sample_config.model_code,
            "tier": sample_config.tier,
            "temperature": str(sample_config.temperature),
            "max_tokens": sample_config.max_tokens,
            "top_p": str(sample_config.top_p),
            "frequency_penalty": str(sample_config.frequency_penalty),
            "presence_penalty": str(sample_config.presence_penalty),
            "is_active": sample_config.is_active,
            "effective_from": sample_config.effective_from.isoformat(),
            "effective_until": None,
            "created_at": sample_config.created_at.isoformat(),
            "updated_at": sample_config.updated_at.isoformat(),
            "created_by": sample_config.created_by,
        }
        mock_table.scan.return_value = {"Items": [item]}

        # Act
        results = await repository.list_all(
            interaction_code="COACHING_SESSION", tier="premium", active_only=True
        )

        # Assert
        assert len(results) == 1
        assert results[0].config_id == sample_config.config_id
        mock_table.scan.assert_called_once()
        call_args = mock_table.scan.call_args
        assert "FilterExpression" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_list_all_pagination(self, repository, mock_dynamodb_resource, sample_config):
        """Test listing with pagination."""
        # Arrange
        mock_table = mock_dynamodb_resource.Table.return_value

        item = {
            "config_id": sample_config.config_id,
            "interaction_code": sample_config.interaction_code,
            "template_id": sample_config.template_id,
            "model_code": sample_config.model_code,
            "tier": sample_config.tier,
            "temperature": str(sample_config.temperature),
            "max_tokens": sample_config.max_tokens,
            "top_p": str(sample_config.top_p),
            "frequency_penalty": str(sample_config.frequency_penalty),
            "presence_penalty": str(sample_config.presence_penalty),
            "is_active": sample_config.is_active,
            "effective_from": sample_config.effective_from.isoformat(),
            "effective_until": None,
            "created_at": sample_config.created_at.isoformat(),
            "updated_at": sample_config.updated_at.isoformat(),
            "created_by": sample_config.created_by,
        }

        # First call returns one item and LastEvaluatedKey
        # Second call returns one item and no LastEvaluatedKey
        mock_table.scan.side_effect = [
            {"Items": [item], "LastEvaluatedKey": {"config_id": "key1"}},
            {"Items": [item]},
        ]

        # Act
        results = await repository.list_all()

        # Assert
        assert len(results) == 2
        assert mock_table.scan.call_count == 2
        assert "ExclusiveStartKey" in mock_table.scan.call_args_list[1].kwargs
