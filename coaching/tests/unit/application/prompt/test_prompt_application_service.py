from unittest.mock import AsyncMock, Mock

import pytest
from coaching.src.application.prompt.prompt_service import PromptApplicationService
from coaching.src.core.constants import CoachingTopic
from coaching.src.domain.entities.prompt_template import PromptTemplate
from coaching.src.domain.ports.prompt_repository_port import PromptRepositoryPort


class TestPromptApplicationService:
    @pytest.fixture
    def mock_repository(self):
        return Mock(spec=PromptRepositoryPort)

    @pytest.fixture
    def service(self, mock_repository):
        return PromptApplicationService(prompt_repository=mock_repository)

    @pytest.fixture
    def mock_template(self):
        template = Mock(spec=PromptTemplate)
        template.template_id = "template-123"
        template.topic = CoachingTopic.GOALS
        return template

    @pytest.mark.asyncio
    async def test_get_template_for_topic_found(self, service, mock_repository, mock_template):
        """Test retrieving a template for a topic when it exists."""
        mock_repository.get_by_topic = AsyncMock(return_value=mock_template)

        result = await service.get_template_for_topic(CoachingTopic.GOALS, "v1.0")

        assert result == mock_template
        mock_repository.get_by_topic.assert_called_once_with(CoachingTopic.GOALS, "v1.0")

    @pytest.mark.asyncio
    async def test_get_template_for_topic_not_found(self, service, mock_repository):
        """Test retrieving a template for a topic when it does not exist."""
        mock_repository.get_by_topic = AsyncMock(return_value=None)

        result = await service.get_template_for_topic(CoachingTopic.GOALS, "v1.0")

        assert result is None
        mock_repository.get_by_topic.assert_called_once_with(CoachingTopic.GOALS, "v1.0")

    @pytest.mark.asyncio
    async def test_get_template_by_id_found(self, service, mock_repository, mock_template):
        """Test retrieving a template by ID when it exists."""
        mock_repository.get_by_id = AsyncMock(return_value=mock_template)

        result = await service.get_template_by_id("template-123")

        assert result == mock_template
        mock_repository.get_by_id.assert_called_once_with("template-123")

    @pytest.mark.asyncio
    async def test_get_template_by_id_not_found(self, service, mock_repository):
        """Test retrieving a template by ID when it does not exist."""
        mock_repository.get_by_id = AsyncMock(return_value=None)

        result = await service.get_template_by_id("template-123")

        assert result is None
        mock_repository.get_by_id.assert_called_once_with("template-123")

    @pytest.mark.asyncio
    async def test_list_template_versions(self, service, mock_repository):
        """Test listing template versions."""
        versions = ["v2.0", "v1.0"]
        mock_repository.list_versions = AsyncMock(return_value=versions)

        result = await service.list_template_versions(CoachingTopic.GOALS)

        assert result == versions
        mock_repository.list_versions.assert_called_once_with(CoachingTopic.GOALS)

    @pytest.mark.asyncio
    async def test_template_exists(self, service, mock_repository):
        """Test checking if a template exists."""
        mock_repository.exists = AsyncMock(return_value=True)

        result = await service.template_exists(CoachingTopic.GOALS, "v1.0")

        assert result is True
        mock_repository.exists.assert_called_once_with(CoachingTopic.GOALS, "v1.0")

    @pytest.mark.asyncio
    async def test_create_template_success(self, service, mock_repository, mock_template):
        """Test creating a new template version successfully."""
        mock_repository.save = AsyncMock()

        await service.create_template(mock_template, "v1.0")

        mock_repository.save.assert_called_once_with(mock_template, "v1.0")

    @pytest.mark.asyncio
    async def test_create_template_failure(self, service, mock_repository, mock_template):
        """Test creating a new template version failure."""
        mock_repository.save = AsyncMock(side_effect=ValueError("Version exists"))

        with pytest.raises(ValueError, match="Version exists"):
            await service.create_template(mock_template, "v1.0")

    @pytest.mark.asyncio
    async def test_update_template(self, service, mock_repository, mock_template):
        """Test updating a template (creating new version)."""
        mock_repository.save = AsyncMock()

        await service.update_template(mock_template, "v2.0")

        mock_repository.save.assert_called_once_with(mock_template, "v2.0")

    @pytest.mark.asyncio
    async def test_delete_template_version_success(self, service, mock_repository):
        """Test deleting a template version successfully."""
        mock_repository.delete = AsyncMock(return_value=True)

        result = await service.delete_template_version(CoachingTopic.GOALS, "v1.0")

        assert result is True
        mock_repository.delete.assert_called_once_with(CoachingTopic.GOALS, "v1.0")

    @pytest.mark.asyncio
    async def test_delete_template_version_not_found(self, service, mock_repository):
        """Test deleting a non-existent template version."""
        mock_repository.delete = AsyncMock(return_value=False)

        result = await service.delete_template_version(CoachingTopic.GOALS, "v1.0")

        assert result is False
        mock_repository.delete.assert_called_once_with(CoachingTopic.GOALS, "v1.0")

    @pytest.mark.asyncio
    async def test_delete_template_version_failure(self, service, mock_repository):
        """Test deleting a template version failure (e.g. latest)."""
        mock_repository.delete = AsyncMock(side_effect=ValueError("Cannot delete latest"))

        with pytest.raises(ValueError, match="Cannot delete latest"):
            await service.delete_template_version(CoachingTopic.GOALS, "latest")

    @pytest.mark.asyncio
    async def test_set_latest_version_success(self, service, mock_repository):
        """Test setting the latest version successfully."""
        mock_repository.set_latest = AsyncMock()

        await service.set_latest_version(CoachingTopic.GOALS, "v2.0")

        mock_repository.set_latest.assert_called_once_with(CoachingTopic.GOALS, "v2.0")

    @pytest.mark.asyncio
    async def test_set_latest_version_failure(self, service, mock_repository):
        """Test setting the latest version failure."""
        mock_repository.set_latest = AsyncMock(side_effect=ValueError("Version not found"))

        with pytest.raises(ValueError, match="Version not found"):
            await service.set_latest_version(CoachingTopic.GOALS, "v2.0")

    @pytest.mark.asyncio
    async def test_create_draft_from_version_success(self, service, mock_repository, mock_template):
        """Test creating a draft from an existing version successfully."""
        mock_repository.create_new_version = AsyncMock(return_value=mock_template)

        result = await service.create_draft_from_version(CoachingTopic.GOALS, "v1.0", "v1.1-draft")

        assert result == mock_template
        mock_repository.create_new_version.assert_called_once_with(
            CoachingTopic.GOALS, "v1.0", "v1.1-draft"
        )

    @pytest.mark.asyncio
    async def test_create_draft_from_version_failure(self, service, mock_repository):
        """Test creating a draft failure."""
        mock_repository.create_new_version = AsyncMock(side_effect=ValueError("Source not found"))

        with pytest.raises(ValueError, match="Source not found"):
            await service.create_draft_from_version(CoachingTopic.GOALS, "v1.0", "v1.1-draft")
