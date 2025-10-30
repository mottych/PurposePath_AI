"""Integration tests for LLM Template service (simplified for existing methods)."""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from coaching.src.services.llm_template_service import (
    LLMTemplateService,
    TemplateNotFoundError,
)


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock template repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_s3_client() -> MagicMock:
    """Mock S3 client."""
    s3 = MagicMock()
    return s3


@pytest.fixture
def mock_cache() -> MagicMock:
    """Mock cache service."""
    cache = MagicMock()
    cache.get.return_value = None  # No cached value by default
    return cache


@pytest.fixture
def service(
    mock_repository: AsyncMock,
    mock_s3_client: MagicMock,
    mock_cache: MagicMock,
) -> LLMTemplateService:
    """Create service with mocked dependencies."""
    return LLMTemplateService(
        template_repository=mock_repository,
        s3_client=mock_s3_client,
        cache_service=mock_cache,
    )


@pytest.fixture
def template_metadata() -> TemplateMetadata:
    """Sample template metadata."""
    return TemplateMetadata(
        template_id="template_123",
        template_code="ALIGNMENT_ANALYSIS_V1",
        interaction_code="ALIGNMENT_ANALYSIS",
        name="Alignment Analysis Template",
        description="Template for analyzing goal alignment",
        s3_bucket="test-templates-bucket",
        s3_key="templates/alignment_analysis_v1.jinja2",
        version="1.0.0",
        is_active=True,
        created_by="admin_123",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestGetTemplateByIdIntegration:
    """Integration tests for getting template by ID."""

    @pytest.mark.asyncio
    async def test_get_template_by_id_success(
        self,
        service: LLMTemplateService,
        mock_repository: AsyncMock,
        mock_s3_client: MagicMock,
        template_metadata: TemplateMetadata,
    ) -> None:
        """Test getting template by ID returns metadata and content."""
        # Setup
        mock_repository.get.return_value = template_metadata
        template_content = "Analyze: {{ goal_text }} with {{ purpose }}"
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: template_content.encode("utf-8"))
        }

        # Execute
        metadata, content = await service.get_template_by_id("template_123")

        # Verify
        assert metadata.template_id == "template_123"
        assert content == template_content

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(
        self,
        service: LLMTemplateService,
        mock_repository: AsyncMock,
    ) -> None:
        """Test getting nonexistent template raises error."""
        # Setup
        mock_repository.get.return_value = None

        # Execute & Verify
        with pytest.raises(TemplateNotFoundError):
            await service.get_template_by_id("nonexistent")


class TestGetActiveTemplateIntegration:
    """Integration tests for getting active template for interaction."""

    @pytest.mark.asyncio
    async def test_get_active_template_for_interaction(
        self,
        service: LLMTemplateService,
        mock_repository: AsyncMock,
        mock_s3_client: MagicMock,
        template_metadata: TemplateMetadata,
    ) -> None:
        """Test getting active template for interaction."""
        # Setup
        mock_repository.get_active_for_interaction.return_value = template_metadata
        template_content = "Analyze: {{ goal_text }}"
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: template_content.encode("utf-8"))
        }

        # Execute
        metadata, content = await service.get_active_template_for_interaction("ALIGNMENT_ANALYSIS")

        # Verify
        assert metadata.interaction_code == "ALIGNMENT_ANALYSIS"
        assert content == template_content


class TestRenderTemplateIntegration:
    """Integration tests for template rendering."""

    @pytest.mark.asyncio
    async def test_render_template_with_parameters(
        self,
        service: LLMTemplateService,
        mock_repository: AsyncMock,
        mock_s3_client: MagicMock,
        template_metadata: TemplateMetadata,
    ) -> None:
        """Test rendering template with parameters."""
        # Setup
        mock_repository.get.return_value = template_metadata
        template_content = "Goal: {{ goal_text }}\nPurpose: {{ purpose }}"
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: template_content.encode("utf-8"))
        }

        # Execute
        parameters: dict[str, Any] = {
            "goal_text": "Increase revenue by 20%",
            "purpose": "Business growth",
        }

        rendered = await service.render_template(
            template_id="template_123",
            parameters=parameters,
        )

        # Verify
        assert "Increase revenue by 20%" in rendered
        assert "Business growth" in rendered


class TestValidateSyntaxIntegration:
    """Integration tests for template syntax validation."""

    @pytest.mark.asyncio
    async def test_validate_template_syntax_valid(
        self,
        service: LLMTemplateService,
        mock_repository: AsyncMock,
        mock_s3_client: MagicMock,
        template_metadata: TemplateMetadata,
    ) -> None:
        """Test validating template with valid syntax."""
        # Setup
        mock_repository.get.return_value = template_metadata
        valid_template = "Analyze: {{ goal_text }} with {{ purpose }}"
        mock_s3_client.get_object.return_value = {
            "Body": MagicMock(read=lambda: valid_template.encode("utf-8"))
        }

        # Execute
        is_valid = await service.validate_template_syntax("template_123")

        # Verify
        assert is_valid is True


class TestCacheInvalidationIntegration:
    """Integration tests for template cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_calls_cache_service(
        self,
        service: LLMTemplateService,
        mock_cache: MagicMock,
    ) -> None:
        """Test cache invalidation."""
        # Execute
        await service.invalidate_cache(template_id="template_123")

        # Verify: Cache delete was called (may be called multiple times for different keys)
        assert mock_cache.delete.called


__all__ = []  # Test module, no exports
