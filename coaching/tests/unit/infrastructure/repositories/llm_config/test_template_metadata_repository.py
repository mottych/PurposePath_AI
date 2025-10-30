"""Unit tests for TemplateMetadataRepository."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from coaching.src.infrastructure.repositories.llm_config.template_metadata_repository import (
    TemplateMetadataRepository,
)


@pytest.fixture
def mock_dynamodb_resource():
    """Mock DynamoDB resource."""
    mock_resource = MagicMock()
    mock_table = MagicMock()
    mock_resource.Table.return_value = mock_table
    mock_resource.meta.client.exceptions.ConditionalCheckFailedException = type(
        "ConditionalCheckFailedException", (Exception,), {}
    )
    return mock_resource


@pytest.fixture
def template_metadata_repository(mock_dynamodb_resource):
    """Create TemplateMetadataRepository with mocked dependencies."""
    return TemplateMetadataRepository(
        dynamodb_resource=mock_dynamodb_resource,
        table_name="test_templates_table",
    )


@pytest.fixture
def sample_template_metadata():
    """Sample template metadata for testing."""
    return TemplateMetadata(
        template_id="tmpl_test123",
        template_code="ALIGNMENT_ANALYSIS_V1",
        interaction_code="ALIGNMENT_ANALYSIS",
        name="Alignment Analysis Template v1",
        description="Template for analyzing alignment between goals and values",
        s3_bucket="test-bucket",
        s3_key="templates/alignment_analysis_v1.txt",
        version="1.0.0",
        is_active=True,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        created_by="admin",
    )


# ===========================
# Test: Repository Initialization
# ===========================


@pytest.mark.unit
def test_repository_initialization(mock_dynamodb_resource):
    """Test repository initializes correctly."""
    repo = TemplateMetadataRepository(
        dynamodb_resource=mock_dynamodb_resource,
        table_name="test_table",
    )

    assert repo.dynamodb == mock_dynamodb_resource
    assert repo.table == mock_dynamodb_resource.Table.return_value
    mock_dynamodb_resource.Table.assert_called_once_with("test_table")


# ===========================
# Test: Create Template Metadata
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_template_metadata_success(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test creating template metadata successfully."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.put_item.return_value = {}

    result = await template_metadata_repository.create(sample_template_metadata)

    assert result.template_id == "tmpl_test123"
    assert result.template_code == "ALIGNMENT_ANALYSIS_V1"
    assert result.interaction_code == "ALIGNMENT_ANALYSIS"
    mock_table.put_item.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_template_metadata_generates_id(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test creating template metadata generates ID if not provided."""
    sample_template_metadata.template_id = ""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.put_item.return_value = {}

    result = await template_metadata_repository.create(sample_template_metadata)

    assert result.template_id.startswith("tmpl_")
    assert len(result.template_id) > 5
    mock_table.put_item.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_template_metadata_sets_timestamps(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test creating template metadata sets timestamps."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.put_item.return_value = {}

    before_create = datetime.utcnow()
    result = await template_metadata_repository.create(sample_template_metadata)
    after_create = datetime.utcnow()

    assert before_create <= result.created_at <= after_create
    assert before_create <= result.updated_at <= after_create


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_template_metadata_duplicate_id(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test creating template metadata with duplicate ID raises error."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.put_item.side_effect = (
        mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException(
            {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
        )
    )

    with pytest.raises(ValueError, match="Template ID already exists"):
        await template_metadata_repository.create(sample_template_metadata)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_create_template_metadata_invalid_interaction(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test creating template with invalid interaction code raises error."""
    sample_template_metadata.interaction_code = "INVALID_CODE"

    with pytest.raises(ValueError, match="Cannot create/update template for unknown interaction"):
        await template_metadata_repository.create(sample_template_metadata)


# ===========================
# Test: Get Template by ID
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_id_found(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test getting template by ID when it exists."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.get_item.return_value = {
        "Item": {
            "template_id": "tmpl_test123",
            "template_code": "ALIGNMENT_ANALYSIS_V1",
            "interaction_code": "ALIGNMENT_ANALYSIS",
            "name": "Test Template",
            "description": "Test description",
            "s3_bucket": "test-bucket",
            "s3_key": "templates/test.txt",
            "version": "1.0.0",
            "is_active": True,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "created_by": "admin",
        }
    }

    result = await template_metadata_repository.get_by_id("tmpl_test123")

    assert result is not None
    assert result.template_id == "tmpl_test123"
    assert result.template_code == "ALIGNMENT_ANALYSIS_V1"
    mock_table.get_item.assert_called_once_with(Key={"template_id": "tmpl_test123"})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_id_not_found(template_metadata_repository, mock_dynamodb_resource):
    """Test getting template by ID when it doesn't exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.get_item.return_value = {}

    result = await template_metadata_repository.get_by_id("nonexistent")

    assert result is None
    mock_table.get_item.assert_called_once()


# ===========================
# Test: Get Template by Code
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_code_found(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test getting template by code when it exists."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {
        "Items": [
            {
                "template_id": "tmpl_test123",
                "template_code": "ALIGNMENT_ANALYSIS_V1",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Test Template",
                "description": "Test description",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/test.txt",
                "version": "1.0.0",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "created_by": "admin",
            }
        ]
    }

    result = await template_metadata_repository.get_by_code("ALIGNMENT_ANALYSIS_V1")

    assert result is not None
    assert result.template_code == "ALIGNMENT_ANALYSIS_V1"
    mock_table.query.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_code_not_found(template_metadata_repository, mock_dynamodb_resource):
    """Test getting template by code when it doesn't exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {"Items": []}

    result = await template_metadata_repository.get_by_code("NONEXISTENT")

    assert result is None


# ===========================
# Test: Get Templates by Interaction
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_interaction_found(template_metadata_repository, mock_dynamodb_resource):
    """Test getting templates by interaction code."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {
        "Items": [
            {
                "template_id": "tmpl_test1",
                "template_code": "ALIGNMENT_V1",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Template 1",
                "description": "Description 1",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/test1.txt",
                "version": "1.0.0",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "created_by": "admin",
            },
            {
                "template_id": "tmpl_test2",
                "template_code": "ALIGNMENT_V2",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Template 2",
                "description": "Description 2",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/test2.txt",
                "version": "2.0.0",
                "is_active": False,
                "created_at": "2024-01-02T12:00:00",
                "updated_at": "2024-01-02T12:00:00",
                "created_by": "admin",
            },
        ]
    }

    result = await template_metadata_repository.get_by_interaction("ALIGNMENT_ANALYSIS")

    assert len(result) == 2
    assert result[0].template_id == "tmpl_test1"
    assert result[1].template_id == "tmpl_test2"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_interaction_empty(template_metadata_repository, mock_dynamodb_resource):
    """Test getting templates by interaction when none exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {"Items": []}

    result = await template_metadata_repository.get_by_interaction("NONEXISTENT")

    assert len(result) == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_by_interaction_pagination(template_metadata_repository, mock_dynamodb_resource):
    """Test getting templates by interaction handles pagination."""
    mock_table = mock_dynamodb_resource.Table.return_value

    # First page
    mock_table.query.side_effect = [
        {
            "Items": [
                {
                    "template_id": "tmpl_test1",
                    "template_code": "ALIGNMENT_V1",
                    "interaction_code": "ALIGNMENT_ANALYSIS",
                    "name": "Template 1",
                    "description": "Description 1",
                    "s3_bucket": "test-bucket",
                    "s3_key": "templates/test1.txt",
                    "version": "1.0.0",
                    "is_active": True,
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00",
                    "created_by": "admin",
                }
            ],
            "LastEvaluatedKey": {"template_id": "tmpl_test1"},
        },
        # Second page
        {
            "Items": [
                {
                    "template_id": "tmpl_test2",
                    "template_code": "ALIGNMENT_V2",
                    "interaction_code": "ALIGNMENT_ANALYSIS",
                    "name": "Template 2",
                    "description": "Description 2",
                    "s3_bucket": "test-bucket",
                    "s3_key": "templates/test2.txt",
                    "version": "2.0.0",
                    "is_active": True,
                    "created_at": "2024-01-02T12:00:00",
                    "updated_at": "2024-01-02T12:00:00",
                    "created_by": "admin",
                }
            ]
        },
    ]

    result = await template_metadata_repository.get_by_interaction("ALIGNMENT_ANALYSIS")

    assert len(result) == 2
    assert mock_table.query.call_count == 2


# ===========================
# Test: Get Active Template for Interaction
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_for_interaction_found(
    template_metadata_repository, mock_dynamodb_resource
):
    """Test getting active template for interaction."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {
        "Items": [
            {
                "template_id": "tmpl_active",
                "template_code": "ALIGNMENT_V1",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Active Template",
                "description": "Active description",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/active.txt",
                "version": "1.0.0",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "created_by": "admin",
            },
            {
                "template_id": "tmpl_inactive",
                "template_code": "ALIGNMENT_V2",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Inactive Template",
                "description": "Inactive description",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/inactive.txt",
                "version": "2.0.0",
                "is_active": False,
                "created_at": "2024-01-02T12:00:00",
                "updated_at": "2024-01-02T12:00:00",
                "created_by": "admin",
            },
        ]
    }

    result = await template_metadata_repository.get_active_for_interaction("ALIGNMENT_ANALYSIS")

    assert result is not None
    assert result.template_id == "tmpl_active"
    assert result.is_active is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_for_interaction_not_found(
    template_metadata_repository, mock_dynamodb_resource
):
    """Test getting active template when none exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {"Items": []}

    result = await template_metadata_repository.get_active_for_interaction("NONEXISTENT")

    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_for_interaction_multiple_active(
    template_metadata_repository, mock_dynamodb_resource
):
    """Test getting active template when multiple active templates exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {
        "Items": [
            {
                "template_id": "tmpl_old",
                "template_code": "ALIGNMENT_V1",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Old Template",
                "description": "Old description",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/old.txt",
                "version": "1.0.0",
                "is_active": True,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "created_by": "admin",
            },
            {
                "template_id": "tmpl_new",
                "template_code": "ALIGNMENT_V2",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "New Template",
                "description": "New description",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/new.txt",
                "version": "2.0.0",
                "is_active": True,
                "created_at": "2024-01-02T12:00:00",
                "updated_at": "2024-01-02T12:00:00",
                "created_by": "admin",
            },
        ]
    }

    result = await template_metadata_repository.get_active_for_interaction("ALIGNMENT_ANALYSIS")

    # Should return the most recently updated
    assert result is not None
    assert result.template_id == "tmpl_new"


# ===========================
# Test: List Template Versions
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_versions_success(template_metadata_repository, mock_dynamodb_resource):
    """Test listing versions of a template."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {
        "Items": [
            {
                "template_id": "tmpl_v1",
                "template_code": "ALIGNMENT_TEMPLATE",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Version 1",
                "description": "First version",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/v1.txt",
                "version": "1.0.0",
                "is_active": False,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00",
                "created_by": "admin",
            },
            {
                "template_id": "tmpl_v2",
                "template_code": "ALIGNMENT_TEMPLATE",
                "interaction_code": "ALIGNMENT_ANALYSIS",
                "name": "Version 2",
                "description": "Second version",
                "s3_bucket": "test-bucket",
                "s3_key": "templates/v2.txt",
                "version": "2.0.0",
                "is_active": True,
                "created_at": "2024-01-02T12:00:00",
                "updated_at": "2024-01-02T12:00:00",
                "created_by": "admin",
            },
        ]
    }

    result = await template_metadata_repository.list_versions("ALIGNMENT_TEMPLATE")

    assert len(result) == 2
    # Should be sorted newest first
    assert result[0].version == "2.0.0"
    assert result[1].version == "1.0.0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_versions_empty(template_metadata_repository, mock_dynamodb_resource):
    """Test listing versions when none exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.query.return_value = {"Items": []}

    result = await template_metadata_repository.list_versions("NONEXISTENT")

    assert len(result) == 0


# ===========================
# Test: Update Template Metadata
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_template_metadata_success(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test updating template metadata successfully."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.put_item.return_value = {}

    sample_template_metadata.name = "Updated Name"
    result = await template_metadata_repository.update("tmpl_test123", sample_template_metadata)

    assert result.template_id == "tmpl_test123"
    assert result.name == "Updated Name"
    mock_table.put_item.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_template_metadata_not_found(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test updating template that doesn't exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.put_item.side_effect = (
        mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException(
            {"Error": {"Code": "ConditionalCheckFailedException"}}, "PutItem"
        )
    )

    with pytest.raises(ValueError, match="Template not found"):
        await template_metadata_repository.update("nonexistent", sample_template_metadata)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_template_metadata_invalid_interaction(
    template_metadata_repository, sample_template_metadata, mock_dynamodb_resource
):
    """Test updating template with invalid interaction code."""
    sample_template_metadata.interaction_code = "INVALID_CODE"

    with pytest.raises(ValueError, match="Cannot create/update template for unknown interaction"):
        await template_metadata_repository.update("tmpl_test123", sample_template_metadata)


# ===========================
# Test: Deactivate Template
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deactivate_template_success(template_metadata_repository, mock_dynamodb_resource):
    """Test deactivating template successfully."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.update_item.return_value = {}

    result = await template_metadata_repository.deactivate("tmpl_test123")

    assert result is True
    mock_table.update_item.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_deactivate_template_not_found(template_metadata_repository, mock_dynamodb_resource):
    """Test deactivating template that doesn't exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.update_item.side_effect = (
        mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException(
            {"Error": {"Code": "ConditionalCheckFailedException"}}, "UpdateItem"
        )
    )

    with pytest.raises(ValueError, match="Template not found"):
        await template_metadata_repository.deactivate("nonexistent")


# ===========================
# Test: Activate Template
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_activate_template_success(template_metadata_repository, mock_dynamodb_resource):
    """Test activating template successfully."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.update_item.return_value = {}

    result = await template_metadata_repository.activate("tmpl_test123")

    assert result is True
    mock_table.update_item.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_activate_template_not_found(template_metadata_repository, mock_dynamodb_resource):
    """Test activating template that doesn't exist."""
    mock_table = mock_dynamodb_resource.Table.return_value
    mock_table.update_item.side_effect = (
        mock_dynamodb_resource.meta.client.exceptions.ConditionalCheckFailedException(
            {"Error": {"Code": "ConditionalCheckFailedException"}}, "UpdateItem"
        )
    )

    with pytest.raises(ValueError, match="Template not found"):
        await template_metadata_repository.activate("nonexistent")


# ===========================
# Test: Entity Mapping
# ===========================


@pytest.mark.unit
def test_to_dynamodb_item(template_metadata_repository, sample_template_metadata):
    """Test converting entity to DynamoDB item."""
    item = template_metadata_repository._to_dynamodb_item(sample_template_metadata)

    assert item["template_id"] == "tmpl_test123"
    assert item["template_code"] == "ALIGNMENT_ANALYSIS_V1"
    assert item["interaction_code"] == "ALIGNMENT_ANALYSIS"
    assert item["name"] == "Alignment Analysis Template v1"
    assert item["is_active"] is True
    assert item["created_at"] == "2024-01-01T12:00:00"


@pytest.mark.unit
def test_from_dynamodb_item(template_metadata_repository):
    """Test converting DynamoDB item to entity."""
    item = {
        "template_id": "tmpl_test123",
        "template_code": "ALIGNMENT_ANALYSIS_V1",
        "interaction_code": "ALIGNMENT_ANALYSIS",
        "name": "Test Template",
        "description": "Test description",
        "s3_bucket": "test-bucket",
        "s3_key": "templates/test.txt",
        "version": "1.0.0",
        "is_active": True,
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00",
        "created_by": "admin",
    }

    entity = template_metadata_repository._from_dynamodb_item(item)

    assert entity.template_id == "tmpl_test123"
    assert entity.template_code == "ALIGNMENT_ANALYSIS_V1"
    assert entity.interaction_code == "ALIGNMENT_ANALYSIS"
    assert entity.is_active is True
    assert entity.created_at == datetime(2024, 1, 1, 12, 0, 0)
