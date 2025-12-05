from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from botocore.exceptions import ClientError
from coaching.src.domain.entities.llm_config.template_metadata import TemplateMetadata
from coaching.src.infrastructure.repositories.llm_config.template_metadata_repository import (
    TemplateMetadataRepository,
)
from coaching.src.services.cache_service import CacheService
from coaching.src.services.llm_template_service import (
    InvalidTemplateSyntaxError,
    LLMTemplateService,
    TemplateNotFoundError,
    TemplateRenderError,
)


class TestLLMTemplateService:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock(spec=TemplateMetadataRepository)

    @pytest.fixture
    def mock_s3_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_cache_service(self):
        return AsyncMock(spec=CacheService)

    @pytest.fixture
    def service(self, mock_repo, mock_s3_client, mock_cache_service):
        return LLMTemplateService(
            template_repository=mock_repo,
            s3_client=mock_s3_client,
            cache_service=mock_cache_service,
        )

    @pytest.fixture
    def sample_metadata(self):
        return TemplateMetadata(
            template_id="tmpl-123",
            template_code="COACHING_RESPONSE_V1",
            interaction_code="COACHING_RESPONSE",
            name="Coaching Response Template",
            description="Template for coaching responses",
            version="1.0",
            s3_bucket="test-bucket",
            s3_key="templates/tmpl-123.j2",
            created_by="user-123",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            is_active=True,
        )

    @pytest.mark.asyncio
    async def test_get_template_by_id_success(
        self, service, mock_repo, mock_s3_client, mock_cache_service, sample_metadata
    ):
        # Arrange
        mock_repo.get_by_id.return_value = sample_metadata
        mock_cache_service.get.return_value = None

        mock_body = MagicMock()
        mock_body.read.return_value = b"Hello {{ name }}!"
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Act
        metadata, content = await service.get_template_by_id("tmpl-123")

        # Assert
        assert metadata == sample_metadata
        assert content == "Hello {{ name }}!"
        mock_repo.get_by_id.assert_called_once_with("tmpl-123")
        mock_s3_client.get_object.assert_called_once_with(
            Bucket="test-bucket", Key="templates/tmpl-123.j2"
        )
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found_metadata(self, service, mock_repo):
        # Arrange
        mock_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(TemplateNotFoundError):
            await service.get_template_by_id("non-existent")

    @pytest.mark.asyncio
    async def test_get_template_by_id_s3_not_found(
        self, service, mock_repo, mock_s3_client, sample_metadata
    ):
        # Arrange
        mock_repo.get_by_id.return_value = sample_metadata

        error_response = {"Error": {"Code": "NoSuchKey"}}
        mock_s3_client.get_object.side_effect = ClientError(error_response, "GetObject")

        # Act & Assert
        with pytest.raises(TemplateNotFoundError):
            await service.get_template_by_id("tmpl-123")

    @pytest.mark.asyncio
    async def test_get_active_template_for_interaction(
        self, service, mock_repo, mock_s3_client, sample_metadata
    ):
        # Arrange
        mock_repo.get_active_for_interaction.return_value = sample_metadata

        mock_body = MagicMock()
        mock_body.read.return_value = b"Hello {{ name }}!"
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Act
        metadata, content = await service.get_active_template_for_interaction("COACHING_SESSION")

        # Assert
        assert metadata == sample_metadata
        assert content == "Hello {{ name }}!"
        mock_repo.get_active_for_interaction.assert_called_once_with("COACHING_SESSION")

    @pytest.mark.asyncio
    async def test_render_template_success(
        self, service, mock_repo, mock_s3_client, sample_metadata
    ):
        # Arrange
        mock_repo.get_by_id.return_value = sample_metadata

        mock_body = MagicMock()
        mock_body.read.return_value = (
            b"Context: {{ conversation_context }}\nMessage: {{ user_message }}"
        )
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Act
        result = await service.render_template(
            "tmpl-123", {"conversation_context": "History", "user_message": "Hello"}
        )

        # Assert
        assert result == "Context: History\nMessage: Hello"

    @pytest.mark.asyncio
    async def test_render_template_missing_params(
        self, service, mock_repo, mock_s3_client, sample_metadata
    ):
        # Arrange
        mock_repo.get_by_id.return_value = sample_metadata

        mock_body = MagicMock()
        mock_body.read.return_value = b"Context: {{ conversation_context }}"
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Act & Assert
        with pytest.raises(TemplateRenderError) as exc:
            await service.render_template("tmpl-123", {})

        assert "Missing required parameters" in str(exc.value)

    @pytest.mark.asyncio
    async def test_render_template_syntax_error(
        self, service, mock_repo, mock_s3_client, sample_metadata
    ):
        # Arrange
        mock_repo.get_by_id.return_value = sample_metadata

        mock_body = MagicMock()
        mock_body.read.return_value = b"Hello {{ name "  # Invalid syntax
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Act & Assert
        with pytest.raises(InvalidTemplateSyntaxError):
            await service.render_template(
                "tmpl-123", {"conversation_context": "History", "user_message": "Hello"}
            )

    @pytest.mark.asyncio
    async def test_render_template_cache_hit(self, service, mock_cache_service):
        # Arrange
        mock_cache_service.get.return_value = "Cached Result"

        # Act
        result = await service.render_template("tmpl-123", {"name": "World"})

        # Assert
        assert result == "Cached Result"
        # Should not call repo or s3 if cache hit
        service.repository.get_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_template_syntax_valid(
        self, service, mock_repo, mock_s3_client, sample_metadata
    ):
        # Arrange
        mock_repo.get_by_id.return_value = sample_metadata

        mock_body = MagicMock()
        mock_body.read.return_value = b"Hello {{ name }}!"
        mock_s3_client.get_object.return_value = {"Body": mock_body}

        # Act
        result = await service.validate_template_syntax("tmpl-123")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, service, mock_cache_service):
        # Act
        await service.invalidate_cache("tmpl-123")

        # Assert
        mock_cache_service.delete.assert_called_once()
