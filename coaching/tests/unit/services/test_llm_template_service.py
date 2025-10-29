"""Unit tests for LLMTemplateService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from coaching.src.services.llm_template_service import (
    InvalidTemplateSyntaxError,
    LLMTemplateService,
    TemplateNotFoundError,
    TemplateRenderError,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create mock template repository."""
    return MagicMock()


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Create mock S3 client."""
    return MagicMock()


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create mock cache service."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def service(
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    mock_cache: MagicMock,
) -> LLMTemplateService:
    """Create LLMTemplateService with mocks."""
    return LLMTemplateService(
        template_repository=mock_repository,
        s3_client=mock_s3_client,
        cache_service=mock_cache,
    )


@pytest.fixture
def service_no_cache(
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
) -> LLMTemplateService:
    """Create LLMTemplateService without cache."""
    return LLMTemplateService(
        template_repository=mock_repository,
        s3_client=mock_s3_client,
        cache_service=None,
    )


@pytest.fixture
def sample_metadata() -> TemplateMetadata:
    """Create sample template metadata."""
    return TemplateMetadata(
        template_id="tmpl_test123",
        template_code="ALIGNMENT_ANALYSIS_V1",
        interaction_code="ALIGNMENT_ANALYSIS",
        name="Alignment Analysis Template",
        description="Template for alignment analysis",
        s3_bucket="test-bucket",
        s3_key="templates/alignment_analysis_v1.txt",
        version="1.0.0",
        is_active=True,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=datetime(2024, 1, 1, 12, 0, 0),
        created_by="admin",
    )


@pytest.fixture
def sample_template_content() -> str:
    """Create sample template content."""
    return """You are analyzing alignment between a goal and core values.

Goal: {{ goal_text }}
Purpose: {{ purpose }}
Values: {{ values }}

Provide a comprehensive analysis."""


# ===========================
# Test: Service Initialization
# ===========================


@pytest.mark.unit
def test_service_initialization(
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    mock_cache: MagicMock,
) -> None:
    """Test service initializes correctly."""
    service = LLMTemplateService(
        template_repository=mock_repository,
        s3_client=mock_s3_client,
        cache_service=mock_cache,
    )

    assert service.repository == mock_repository
    assert service.s3_client == mock_s3_client
    assert service.cache == mock_cache


# ===========================
# Test: Get Template by ID
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_template_by_id_success(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
    sample_template_content: str,
) -> None:
    """Test getting template by ID successfully."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: sample_template_content.encode("utf-8"))
    }

    metadata, content = await service.get_template_by_id("tmpl_test123")

    assert metadata == sample_metadata
    assert content == sample_template_content
    mock_repository.get_by_id.assert_called_once_with("tmpl_test123")
    mock_s3_client.get_object.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_template_by_id_not_found(
    service: LLMTemplateService,
    mock_repository: MagicMock,
) -> None:
    """Test getting template when metadata not found."""
    mock_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(TemplateNotFoundError) as exc_info:
        await service.get_template_by_id("nonexistent")

    assert exc_info.value.template_id == "nonexistent"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_template_by_id_s3_not_found(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
) -> None:
    """Test getting template when S3 object not found."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    error_response = {"Error": {"Code": "NoSuchKey"}}
    mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

    with pytest.raises(TemplateNotFoundError):
        await service.get_template_by_id("tmpl_test123")


# ===========================
# Test: Get Active Template for Interaction
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_template_for_interaction_success(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
    sample_template_content: str,
) -> None:
    """Test getting active template for interaction."""
    mock_repository.get_active_for_interaction = AsyncMock(return_value=sample_metadata)
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: sample_template_content.encode("utf-8"))
    }

    metadata, content = await service.get_active_template_for_interaction("ALIGNMENT_ANALYSIS")

    assert metadata == sample_metadata
    assert content == sample_template_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_active_template_for_interaction_not_found(
    service: LLMTemplateService,
    mock_repository: MagicMock,
) -> None:
    """Test getting active template when none exists."""
    mock_repository.get_active_for_interaction = AsyncMock(return_value=None)

    with pytest.raises(TemplateNotFoundError) as exc_info:
        await service.get_active_template_for_interaction("ALIGNMENT_ANALYSIS")

    assert "interaction:ALIGNMENT_ANALYSIS" in str(exc_info.value)


# ===========================
# Test: Render Template
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_render_template_success(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
    sample_template_content: str,
) -> None:
    """Test rendering template successfully."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: sample_template_content.encode("utf-8"))
    }

    parameters = {
        "goal_text": "Increase revenue",
        "purpose": "Help businesses grow",
        "values": "Integrity, Innovation",
    }

    rendered = await service.render_template("tmpl_test123", parameters)

    assert "Increase revenue" in rendered
    assert "Help businesses grow" in rendered
    assert "Integrity, Innovation" in rendered


@pytest.mark.unit
@pytest.mark.asyncio
async def test_render_template_missing_required_parameter(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
    sample_template_content: str,
) -> None:
    """Test rendering template with missing required parameter."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: sample_template_content.encode("utf-8"))
    }

    parameters = {
        "goal_text": "Increase revenue",
        # Missing 'purpose' and 'values'
    }

    with pytest.raises(TemplateRenderError) as exc_info:
        await service.render_template("tmpl_test123", parameters)

    assert "Missing required parameters" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_render_template_from_cache(
    service: LLMTemplateService,
    mock_cache: MagicMock,
    mock_repository: MagicMock,
) -> None:
    """Test rendering template from cache."""
    cached_rendered = "Cached rendered content"
    mock_cache.get = AsyncMock(return_value=cached_rendered)

    parameters = {
        "goal_text": "Test",
        "purpose": "Test",
        "values": "Test",
    }

    result = await service.render_template("tmpl_test123", parameters)

    assert result == cached_rendered
    # Repository should not be called
    mock_repository.get_by_id.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_render_template_caches_result(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    mock_cache: MagicMock,
    sample_metadata: TemplateMetadata,
    sample_template_content: str,
) -> None:
    """Test rendered template is cached."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: sample_template_content.encode("utf-8"))
    }

    parameters = {
        "goal_text": "Test",
        "purpose": "Test",
        "values": "Test",
    }

    await service.render_template("tmpl_test123", parameters)

    # Cache set should be called twice (once for content, once for rendered)
    assert mock_cache.set.call_count == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_render_template_invalid_syntax(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
) -> None:
    """Test rendering template with invalid Jinja2 syntax."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    invalid_template = "{{ unclosed_variable"
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: invalid_template.encode("utf-8"))
    }

    parameters = {
        "goal_text": "Test",
        "purpose": "Test",
        "values": "Test",
    }

    with pytest.raises(InvalidTemplateSyntaxError):
        await service.render_template("tmpl_test123", parameters)


# ===========================
# Test: Validate Template Syntax
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_template_syntax_valid(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
    sample_template_content: str,
) -> None:
    """Test validating valid template syntax."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: sample_template_content.encode("utf-8"))
    }

    result = await service.validate_template_syntax("tmpl_test123")

    assert result is True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_template_syntax_invalid(
    service: LLMTemplateService,
    mock_repository: MagicMock,
    mock_s3_client: MagicMock,
    sample_metadata: TemplateMetadata,
) -> None:
    """Test validating invalid template syntax."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_metadata)
    invalid_template = "{{ unclosed_variable"
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: invalid_template.encode("utf-8"))
    }

    with pytest.raises(InvalidTemplateSyntaxError):
        await service.validate_template_syntax("tmpl_test123")


# ===========================
# Test: Cache Invalidation
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalidate_cache(
    service: LLMTemplateService,
    mock_cache: MagicMock,
) -> None:
    """Test cache invalidation."""
    await service.invalidate_cache("tmpl_test123")

    mock_cache.delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalidate_cache_no_cache_service(
    service_no_cache: LLMTemplateService,
) -> None:
    """Test cache invalidation when no cache service."""
    # Should not raise error
    await service_no_cache.invalidate_cache("tmpl_test123")


# ===========================
# Test: Template Content Caching
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_template_content_from_cache(
    service: LLMTemplateService,
    mock_cache: MagicMock,
    sample_metadata: TemplateMetadata,
) -> None:
    """Test fetching template content from cache."""
    cached_content = "Cached template content"
    mock_cache.get = AsyncMock(return_value=cached_content)

    content = await service._fetch_template_content(sample_metadata)

    assert content == cached_content


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_template_content_caches_s3_result(
    service: LLMTemplateService,
    mock_s3_client: MagicMock,
    mock_cache: MagicMock,
    sample_metadata: TemplateMetadata,
    sample_template_content: str,
) -> None:
    """Test S3 content is cached."""
    mock_s3_client.get_object.return_value = {
        "Body": MagicMock(read=lambda: sample_template_content.encode("utf-8"))
    }

    await service._fetch_template_content(sample_metadata)

    mock_cache.set.assert_called_once()


# ===========================
# Test: Cache Key Generation
# ===========================


@pytest.mark.unit
def test_get_content_cache_key(service: LLMTemplateService) -> None:
    """Test content cache key generation."""
    key = service._get_content_cache_key("tmpl_test123")
    assert key == "template_content:tmpl_test123"


@pytest.mark.unit
def test_get_rendered_cache_key(service: LLMTemplateService) -> None:
    """Test rendered cache key generation."""
    parameters = {"goal_text": "Test", "purpose": "Test"}
    key = service._get_rendered_cache_key("tmpl_test123", parameters)

    assert "template_rendered:tmpl_test123:" in key
    # Parameters should be deterministic
    key2 = service._get_rendered_cache_key("tmpl_test123", parameters)
    assert key == key2
