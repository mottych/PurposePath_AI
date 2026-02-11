from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from coaching.src.infrastructure.repositories.llm_config.template_metadata_repository import (
    TemplateMetadataRepository,
)


class TestTemplateMetadataRepository:
    @pytest.fixture
    def mock_dynamodb_resource(self):
        mock = Mock()

        # Create a real class for the exception
        class ConditionalCheckFailedError(Exception):
            pass

        mock.meta.client.exceptions.ConditionalCheckFailedException = ConditionalCheckFailedError
        return mock

    @pytest.fixture
    def mock_table(self):
        return Mock()

    @pytest.fixture
    def repository(self, mock_dynamodb_resource, mock_table):
        mock_dynamodb_resource.Table.return_value = mock_table
        return TemplateMetadataRepository(mock_dynamodb_resource, "test-table")

    @pytest.fixture
    def sample_metadata(self):
        return TemplateMetadata(
            template_id="tmpl_123",
            template_code="test_template",
            interaction_code="COACHING_SESSION",
            name="Test Template",
            description="Test template description",
            s3_bucket="test-bucket",
            s3_key="templates/test_template/v1.0.json",
            version="1.0",
            is_active=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            created_by="user_123",
        )

    @pytest.mark.asyncio
    async def test_create_success(self, repository, mock_table, sample_metadata):
        # Arrange
        mock_table.put_item.return_value = {}

        # Mock validation of interaction code
        with patch(
            "coaching.src.infrastructure.repositories.llm_config.template_metadata_repository.TemplateMetadataRepository._validate_interaction_code"
        ):
            # Act
            result = await repository.create(sample_metadata)

            # Assert
            assert result == sample_metadata
            mock_table.put_item.assert_called_once()
            call_args = mock_table.put_item.call_args[1]
            assert call_args["Item"]["template_id"] == sample_metadata.template_id
            assert call_args["Item"]["template_code"] == sample_metadata.template_code

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_table, sample_metadata):
        # Arrange
        item = {
            "template_id": sample_metadata.template_id,
            "template_code": sample_metadata.template_code,
            "interaction_code": sample_metadata.interaction_code,
            "name": sample_metadata.name,
            "description": sample_metadata.description,
            "s3_bucket": sample_metadata.s3_bucket,
            "s3_key": sample_metadata.s3_key,
            "version": sample_metadata.version,
            "is_active": sample_metadata.is_active,
            "created_at": sample_metadata.created_at.isoformat(),
            "updated_at": sample_metadata.updated_at.isoformat(),
            "created_by": sample_metadata.created_by,
        }
        mock_table.get_item.return_value = {"Item": item}

        # Act
        result = await repository.get_by_id(sample_metadata.template_id)

        # Assert
        assert result is not None
        assert result.template_id == sample_metadata.template_id
        mock_table.get_item.assert_called_once_with(
            Key={"template_id": sample_metadata.template_id}
        )

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_table):
        # Arrange
        mock_table.get_item.return_value = {}

        # Act
        result = await repository.get_by_id("non_existent")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_code_found(self, repository, mock_table, sample_metadata):
        # Arrange
        item = {
            "template_id": sample_metadata.template_id,
            "template_code": sample_metadata.template_code,
            "interaction_code": sample_metadata.interaction_code,
            "name": sample_metadata.name,
            "description": sample_metadata.description,
            "s3_bucket": sample_metadata.s3_bucket,
            "s3_key": sample_metadata.s3_key,
            "version": sample_metadata.version,
            "is_active": sample_metadata.is_active,
            "created_at": sample_metadata.created_at.isoformat(),
            "updated_at": sample_metadata.updated_at.isoformat(),
            "created_by": sample_metadata.created_by,
        }
        mock_table.query.return_value = {"Items": [item]}

        # Act
        result = await repository.get_by_code(sample_metadata.template_code)

        # Assert
        assert result is not None
        assert result.template_code == sample_metadata.template_code
        mock_table.query.assert_called_once()
        call_args = mock_table.query.call_args[1]
        assert call_args["IndexName"] == "code-index"

    @pytest.mark.asyncio
    async def test_get_by_interaction(self, repository, mock_table, sample_metadata):
        # Arrange
        item = {
            "template_id": sample_metadata.template_id,
            "template_code": sample_metadata.template_code,
            "interaction_code": sample_metadata.interaction_code,
            "name": sample_metadata.name,
            "description": sample_metadata.description,
            "s3_bucket": sample_metadata.s3_bucket,
            "s3_key": sample_metadata.s3_key,
            "version": sample_metadata.version,
            "is_active": sample_metadata.is_active,
            "created_at": sample_metadata.created_at.isoformat(),
            "updated_at": sample_metadata.updated_at.isoformat(),
            "created_by": sample_metadata.created_by,
        }
        mock_table.query.return_value = {"Items": [item]}

        # Act
        results = await repository.get_by_interaction(sample_metadata.interaction_code)

        # Assert
        assert len(results) == 1
        assert results[0].interaction_code == sample_metadata.interaction_code
        mock_table.query.assert_called_once()
        call_args = mock_table.query.call_args[1]
        assert call_args["IndexName"] == "interaction-index"

    @pytest.mark.asyncio
    async def test_get_active_for_interaction(self, repository, mock_table, sample_metadata):
        # Arrange
        # Mock get_by_interaction to return a list with one active template
        with patch.object(repository, "get_by_interaction", return_value=[sample_metadata]):
            # Act
            result = await repository.get_active_for_interaction(sample_metadata.interaction_code)

            # Assert
            assert result is not None
            assert result.is_active is True
            repository.get_by_interaction.assert_called_once_with(sample_metadata.interaction_code)

    @pytest.mark.asyncio
    async def test_list_versions(self, repository, mock_table, sample_metadata):
        # Arrange
        v1 = sample_metadata.model_copy()
        v1.version = "1.0"
        v1.created_at = datetime.now(UTC) - timedelta(days=1)

        v2 = sample_metadata.model_copy()
        v2.version = "2.0"
        v2.created_at = datetime.now(UTC)

        item1 = {
            "template_id": v1.template_id,
            "template_code": v1.template_code,
            "interaction_code": v1.interaction_code,
            "name": v1.name,
            "description": v1.description,
            "s3_bucket": v1.s3_bucket,
            "s3_key": v1.s3_key,
            "version": v1.version,
            "is_active": v1.is_active,
            "created_at": v1.created_at.isoformat(),
            "updated_at": v1.updated_at.isoformat(),
            "created_by": v1.created_by,
        }
        item2 = {
            "template_id": v2.template_id,
            "template_code": v2.template_code,
            "interaction_code": v2.interaction_code,
            "name": v2.name,
            "description": v2.description,
            "s3_bucket": v2.s3_bucket,
            "s3_key": v2.s3_key,
            "version": v2.version,
            "is_active": v2.is_active,
            "created_at": v2.created_at.isoformat(),
            "updated_at": v2.updated_at.isoformat(),
            "created_by": v2.created_by,
        }

        mock_table.query.return_value = {"Items": [item1, item2]}

        # Act
        results = await repository.list_versions(sample_metadata.template_code)

        # Assert
        assert len(results) == 2
        # Should be sorted by created_at desc (v2 then v1)
        assert results[0].version == "2.0"
        assert results[1].version == "1.0"

    @pytest.mark.asyncio
    async def test_update_success(self, repository, mock_table, sample_metadata):
        # Arrange
        mock_table.put_item.return_value = {}

        with patch(
            "coaching.src.infrastructure.repositories.llm_config.template_metadata_repository.TemplateMetadataRepository._validate_interaction_code"
        ):
            # Act
            result = await repository.update(sample_metadata.template_id, sample_metadata)

            # Assert
            assert result == sample_metadata
            mock_table.put_item.assert_called_once()
            call_args = mock_table.put_item.call_args[1]
            assert call_args["Item"]["template_id"] == sample_metadata.template_id
            assert "ConditionExpression" in call_args

    @pytest.mark.asyncio
    async def test_update_not_found(self, repository, mock_table, sample_metadata):
        # Arrange
        # Mock ConditionalCheckFailedException
        exception = repository.dynamodb.meta.client.exceptions.ConditionalCheckFailedException(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "The conditional request failed",
                }
            },
            "PutItem",
        )
        mock_table.put_item.side_effect = exception

        with (
            patch(
                "coaching.src.infrastructure.repositories.llm_config.template_metadata_repository.TemplateMetadataRepository._validate_interaction_code"
            ),
            pytest.raises(ValueError, match=f"Template not found: {sample_metadata.template_id}"),
        ):
            # Act & Assert
            await repository.update(sample_metadata.template_id, sample_metadata)

    @pytest.mark.asyncio
    async def test_deactivate_success(self, repository, mock_table, sample_metadata):
        # Arrange
        mock_table.update_item.return_value = {}

        # Act
        result = await repository.deactivate(sample_metadata.template_id)

        # Assert
        assert result is True
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        assert call_args["Key"]["template_id"] == sample_metadata.template_id
        assert "SET is_active = :inactive" in call_args["UpdateExpression"]

    @pytest.mark.asyncio
    async def test_deactivate_not_found(self, repository, mock_table, sample_metadata):
        # Arrange
        exception = repository.dynamodb.meta.client.exceptions.ConditionalCheckFailedException(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "The conditional request failed",
                }
            },
            "UpdateItem",
        )
        mock_table.update_item.side_effect = exception

        # Act & Assert
        with pytest.raises(ValueError, match=f"Template not found: {sample_metadata.template_id}"):
            await repository.deactivate(sample_metadata.template_id)

    @pytest.mark.asyncio
    async def test_activate_success(self, repository, mock_table, sample_metadata):
        # Arrange
        mock_table.update_item.return_value = {}

        # Act
        result = await repository.activate(sample_metadata.template_id)

        # Assert
        assert result is True
        mock_table.update_item.assert_called_once()
        call_args = mock_table.update_item.call_args[1]
        assert call_args["Key"]["template_id"] == sample_metadata.template_id
        assert "SET is_active = :active" in call_args["UpdateExpression"]

    @pytest.mark.asyncio
    async def test_activate_not_found(self, repository, mock_table, sample_metadata):
        # Arrange
        exception = repository.dynamodb.meta.client.exceptions.ConditionalCheckFailedException(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "The conditional request failed",
                }
            },
            "UpdateItem",
        )
        mock_table.update_item.side_effect = exception

        # Act & Assert
        with pytest.raises(ValueError, match=f"Template not found: {sample_metadata.template_id}"):
            await repository.activate(sample_metadata.template_id)

    @pytest.mark.asyncio
    async def test_create_duplicate_id(self, repository, mock_table, sample_metadata):
        # Arrange
        exception = repository.dynamodb.meta.client.exceptions.ConditionalCheckFailedException(
            {
                "Error": {
                    "Code": "ConditionalCheckFailedException",
                    "Message": "The conditional request failed",
                }
            },
            "PutItem",
        )
        mock_table.put_item.side_effect = exception

        with (
            patch(
                "coaching.src.infrastructure.repositories.llm_config.template_metadata_repository.TemplateMetadataRepository._validate_interaction_code"
            ),
            pytest.raises(
                ValueError, match=f"Template ID already exists: {sample_metadata.template_id}"
            ),
        ):
            # Act & Assert
            await repository.create(sample_metadata)
