"""Unit tests for LLMConfigurationRepository."""

from datetime import datetime
from unittest.mock import Mock

import pytest
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.infrastructure.repositories.llm_config.llm_configuration_repository import (
    LLMConfigurationRepository,
)


@pytest.fixture
def mock_dynamodb_resource():
    """Create a mock DynamoDB resource."""
    resource = Mock()
    table = Mock()
    resource.Table.return_value = table
    resource.meta.client.exceptions.ConditionalCheckFailedException = type(
        "ConditionalCheckFailedException", (Exception,), {}
    )
    return resource


@pytest.fixture
def mock_table(mock_dynamodb_resource):
    """Get the mock table from the resource."""
    return mock_dynamodb_resource.Table.return_value


@pytest.fixture
def repository(mock_dynamodb_resource):
    """Create repository instance with mocked DynamoDB."""
    return LLMConfigurationRepository(
        dynamodb_resource=mock_dynamodb_resource, table_name="test-llm-configs"
    )


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return LLMConfiguration(
        config_id="cfg_test123",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="CORE_VALUES/1.0.0",
        model_code="claude-3-5-sonnet",
        tier="premium",
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        is_active=True,
        effective_from=datetime.utcnow(),
        effective_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="test_admin",
    )


@pytest.mark.unit
class TestLLMConfigurationRepositoryInit:
    """Test repository initialization."""

    def test_init_creates_repository(self, mock_dynamodb_resource):
        """Test that repository initializes correctly."""
        # Act
        repo = LLMConfigurationRepository(
            dynamodb_resource=mock_dynamodb_resource, table_name="test-table"
        )

        # Assert
        assert repo is not None
        assert repo.table is not None
        mock_dynamodb_resource.Table.assert_called_once_with("test-table")


@pytest.mark.unit
class TestCreateConfiguration:
    """Test configuration creation."""

    @pytest.mark.asyncio
    async def test_create_generates_id_when_not_provided(
        self, repository, mock_table, sample_config
    ):
        """Test that create generates config_id if not provided."""
        # Arrange
        sample_config.config_id = ""
        mock_table.put_item.return_value = {}

        # Act
        result = await repository.create(sample_config)

        # Assert
        assert result.config_id != ""
        assert result.config_id.startswith("cfg_")
        mock_table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_preserves_provided_id(self, repository, mock_table, sample_config):
        """Test that create preserves provided config_id."""
        # Arrange
        expected_id = "cfg_custom123"
        sample_config.config_id = expected_id
        mock_table.put_item.return_value = {}

        # Act
        result = await repository.create(sample_config)

        # Assert
        assert result.config_id == expected_id
        mock_table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_sets_timestamps(self, repository, mock_table, sample_config):
        """Test that create sets created_at and updated_at."""
        # Arrange
        mock_table.put_item.return_value = {}
        original_created = sample_config.created_at

        # Act
        result = await repository.create(sample_config)

        # Assert
        assert result.created_at != original_created
        assert result.updated_at != original_created
        assert result.created_at == result.updated_at

    @pytest.mark.asyncio
    async def test_create_uses_condition_expression(self, repository, mock_table, sample_config):
        """Test that create uses conditional expression to prevent duplicates."""
        # Arrange
        mock_table.put_item.return_value = {}

        # Act
        await repository.create(sample_config)

        # Assert
        call_args = mock_table.put_item.call_args
        assert "ConditionExpression" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_create_raises_error_on_duplicate_id(
        self, repository, mock_table, sample_config, mock_dynamodb_resource
    ):
        """Test that create raises ValueError when config_id already exists."""
        # Arrange
        mock_table.put_item.side_effect = (
            mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="already exists"):
            await repository.create(sample_config)


@pytest.mark.unit
class TestGetById:
    """Test retrieving configuration by ID."""

    @pytest.mark.asyncio
    async def test_get_by_id_returns_config_when_found(self, repository, mock_table, sample_config):
        """Test that get_by_id returns configuration when found."""
        # Arrange
        mock_table.get_item.return_value = {
            "Item": {
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
        }

        # Act
        result = await repository.get_by_id(sample_config.config_id)

        # Assert
        assert result is not None
        assert result.config_id == sample_config.config_id
        assert result.interaction_code == sample_config.interaction_code
        mock_table.get_item.assert_called_once_with(Key={"config_id": sample_config.config_id})

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_not_found(self, repository, mock_table):
        """Test that get_by_id returns None when configuration not found."""
        # Arrange
        mock_table.get_item.return_value = {}  # No Item key

        # Act
        result = await repository.get_by_id("nonexistent_id")

        # Assert
        assert result is None


@pytest.mark.unit
class TestListAll:
    """Test listing configurations with filters."""

    @pytest.mark.asyncio
    async def test_list_all_without_filters(self, repository, mock_table, sample_config):
        """Test listing all configurations without filters."""
        # Arrange
        mock_table.scan.return_value = {
            "Items": [
                {
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
            ]
        }

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 1
        assert result[0].config_id == sample_config.config_id
        mock_table.scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_all_with_interaction_filter(self, repository, mock_table):
        """Test listing configurations filtered by interaction code."""
        # Arrange
        mock_table.scan.return_value = {"Items": []}

        # Act
        await repository.list_all(interaction_code="ALIGNMENT_ANALYSIS")

        # Assert
        call_args = mock_table.scan.call_args
        assert "FilterExpression" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_list_all_with_active_only_filter(self, repository, mock_table):
        """Test listing only active configurations."""
        # Arrange
        mock_table.scan.return_value = {"Items": []}

        # Act
        await repository.list_all(active_only=True)

        # Assert
        call_args = mock_table.scan.call_args
        assert "FilterExpression" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_list_all_handles_pagination(self, repository, mock_table, sample_config):
        """Test that list_all handles DynamoDB pagination."""
        # Arrange
        first_item = {
            "config_id": "cfg_1",
            "interaction_code": sample_config.interaction_code,
            "template_id": sample_config.template_id,
            "model_code": sample_config.model_code,
            "tier": None,
            "temperature": "0.7",
            "max_tokens": 2000,
            "top_p": "1.0",
            "frequency_penalty": "0.0",
            "presence_penalty": "0.0",
            "is_active": True,
            "effective_from": datetime.utcnow().isoformat(),
            "effective_until": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": "admin",
        }

        second_item = {**first_item, "config_id": "cfg_2"}

        mock_table.scan.side_effect = [
            {"Items": [first_item], "LastEvaluatedKey": {"config_id": "cfg_1"}},
            {"Items": [second_item]},
        ]

        # Act
        result = await repository.list_all()

        # Assert
        assert len(result) == 2
        assert mock_table.scan.call_count == 2


@pytest.mark.unit
class TestUpdateConfiguration:
    """Test updating configurations."""

    @pytest.mark.asyncio
    async def test_update_modifies_configuration(self, repository, mock_table, sample_config):
        """Test that update modifies the configuration."""
        # Arrange
        mock_table.put_item.return_value = {}
        sample_config.temperature = 0.9  # Modified value

        # Act
        result = await repository.update(sample_config)

        # Assert
        assert result.temperature == 0.9
        mock_table.put_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_sets_updated_timestamp(self, repository, mock_table, sample_config):
        """Test that update sets updated_at timestamp."""
        # Arrange
        mock_table.put_item.return_value = {}
        original_updated = sample_config.updated_at

        # Act
        result = await repository.update(sample_config)

        # Assert
        assert result.updated_at != original_updated

    @pytest.mark.asyncio
    async def test_update_uses_condition_expression(self, repository, mock_table, sample_config):
        """Test that update uses conditional expression to ensure existence."""
        # Arrange
        mock_table.put_item.return_value = {}

        # Act
        await repository.update(sample_config)

        # Assert
        call_args = mock_table.put_item.call_args
        assert "ConditionExpression" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_update_raises_error_when_not_found(
        self, repository, mock_table, sample_config, mock_dynamodb_resource
    ):
        """Test that update raises ValueError when configuration doesn't exist."""
        # Arrange
        mock_table.put_item.side_effect = (
            mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await repository.update(sample_config)


@pytest.mark.unit
class TestDeleteConfiguration:
    """Test deleting configurations."""

    @pytest.mark.asyncio
    async def test_delete_removes_configuration(self, repository, mock_table):
        """Test that delete removes the configuration."""
        # Arrange
        config_id = "cfg_test123"
        mock_table.delete_item.return_value = {}

        # Act
        await repository.delete(config_id)

        # Assert
        mock_table.delete_item.assert_called_once_with(
            Key={"config_id": config_id},
            ConditionExpression=mock_table.delete_item.call_args.kwargs["ConditionExpression"],
        )

    @pytest.mark.asyncio
    async def test_delete_raises_error_when_not_found(
        self, repository, mock_table, mock_dynamodb_resource
    ):
        """Test that delete raises ValueError when configuration doesn't exist."""
        # Arrange
        mock_table.delete_item.side_effect = (
            mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await repository.delete("nonexistent_id")


@pytest.mark.unit
class TestDeactivateConfiguration:
    """Test deactivating configurations."""

    @pytest.mark.asyncio
    async def test_deactivate_sets_active_false(self, repository, mock_table):
        """Test that deactivate sets is_active to False."""
        # Arrange
        config_id = "cfg_test123"
        mock_table.update_item.return_value = {}

        # Act
        await repository.deactivate(config_id)

        # Assert
        call_args = mock_table.update_item.call_args
        assert (
            call_args.kwargs["UpdateExpression"] == "SET is_active = :inactive, updated_at = :now"
        )
        assert call_args.kwargs["ExpressionAttributeValues"][":inactive"] is False

    @pytest.mark.asyncio
    async def test_deactivate_raises_error_when_not_found(
        self, repository, mock_table, mock_dynamodb_resource
    ):
        """Test that deactivate raises ValueError when configuration doesn't exist."""
        # Arrange
        mock_table.update_item.side_effect = (
            mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await repository.deactivate("nonexistent_id")


@pytest.mark.unit
class TestActivateConfiguration:
    """Test activating configurations."""

    @pytest.mark.asyncio
    async def test_activate_sets_active_true(self, repository, mock_table):
        """Test that activate sets is_active to True."""
        # Arrange
        config_id = "cfg_test123"
        mock_table.update_item.return_value = {}

        # Act
        await repository.activate(config_id)

        # Assert
        call_args = mock_table.update_item.call_args
        assert call_args.kwargs["UpdateExpression"] == "SET is_active = :active, updated_at = :now"
        assert call_args.kwargs["ExpressionAttributeValues"][":active"] is True

    @pytest.mark.asyncio
    async def test_activate_raises_error_when_not_found(
        self, repository, mock_table, mock_dynamodb_resource
    ):
        """Test that activate raises ValueError when configuration doesn't exist."""
        # Arrange
        mock_table.update_item.side_effect = (
            mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException()
        )

        # Act & Assert
        with pytest.raises(ValueError, match="not found"):
            await repository.activate("nonexistent_id")


@pytest.mark.unit
class TestEntityMapping:
    """Test entity to/from DynamoDB mapping."""

    def test_to_dynamodb_item_converts_correctly(self, repository, sample_config):
        """Test that entity is correctly converted to DynamoDB item."""
        # Act
        item = repository._to_dynamodb_item(sample_config)

        # Assert
        assert item["config_id"] == sample_config.config_id
        assert item["interaction_code"] == sample_config.interaction_code
        assert item["template_id"] == sample_config.template_id
        assert item["model_code"] == sample_config.model_code
        assert item["tier"] == sample_config.tier
        assert isinstance(item["temperature"], str)  # Stored as string for precision
        assert item["max_tokens"] == sample_config.max_tokens
        assert item["is_active"] == sample_config.is_active
        assert isinstance(item["effective_from"], str)  # ISO format
        assert isinstance(item["created_at"], str)

    def test_to_dynamodb_item_handles_none_tier(self, repository, sample_config):
        """Test that None tier is preserved in DynamoDB item."""
        # Arrange
        sample_config.tier = None

        # Act
        item = repository._to_dynamodb_item(sample_config)

        # Assert
        assert item["tier"] is None

    def test_from_dynamodb_item_converts_correctly(self, repository):
        """Test that DynamoDB item is correctly converted to entity."""
        # Arrange
        now = datetime.utcnow()
        item = {
            "config_id": "cfg_test123",
            "interaction_code": "ALIGNMENT_ANALYSIS",
            "template_id": "CORE_VALUES/1.0.0",
            "model_code": "claude-3-5-sonnet",
            "tier": "premium",
            "temperature": "0.7",
            "max_tokens": 2000,
            "top_p": "1.0",
            "frequency_penalty": "0.0",
            "presence_penalty": "0.0",
            "is_active": True,
            "effective_from": now.isoformat(),
            "effective_until": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": "test_admin",
        }

        # Act
        config = repository._from_dynamodb_item(item)

        # Assert
        assert isinstance(config, LLMConfiguration)
        assert config.config_id == item["config_id"]
        assert config.temperature == 0.7  # Converted from string
        assert config.max_tokens == 2000
        assert isinstance(config.effective_from, datetime)
        assert config.effective_until is None

    def test_from_dynamodb_item_handles_none_tier(self, repository):
        """Test that from_dynamodb_item handles None tier."""
        # Arrange
        now = datetime.utcnow()
        item = {
            "config_id": "cfg_test123",
            "interaction_code": "ALIGNMENT_ANALYSIS",
            "template_id": "CORE_VALUES/1.0.0",
            "model_code": "claude-3-5-sonnet",
            "tier": None,  # None tier
            "temperature": "0.7",
            "max_tokens": 2000,
            "top_p": "1.0",
            "frequency_penalty": "0.0",
            "presence_penalty": "0.0",
            "is_active": True,
            "effective_from": now.isoformat(),
            "effective_until": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "created_by": "test_admin",
        }

        # Act
        config = repository._from_dynamodb_item(item)

        # Assert
        assert config.tier is None
