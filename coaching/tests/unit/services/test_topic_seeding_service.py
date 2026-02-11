from unittest.mock import AsyncMock, Mock, patch

import pytest
from coaching.src.core.topic_seed_data import TopicSeedData
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.services.topic_seeding_service import (
    SeedingResult,
    TopicSeedingService,
    ValidationReport,
)


class TestTopicSeedingService:
    @pytest.fixture
    def mock_topic_repo(self) -> Mock:
        repo = Mock()
        repo.get = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def mock_s3_storage(self) -> Mock:
        storage = Mock()
        storage.save_prompt = AsyncMock(return_value="s3_key")
        storage.get_prompt = AsyncMock(return_value="Test prompt content")
        storage.prompt_exists = AsyncMock(return_value=True)
        storage.bucket_name = "test-bucket"
        return storage

    @pytest.fixture
    def service(self, mock_topic_repo: Mock, mock_s3_storage: Mock) -> TopicSeedingService:
        return TopicSeedingService(
            topic_repo=mock_topic_repo, s3_storage=mock_s3_storage, default_created_by="test_user"
        )

    def test_seeding_result_properties(self) -> None:
        result = SeedingResult()
        result.created = ["topic1"]
        result.updated = ["topic2"]
        result.skipped = ["topic3"]
        result.errors = [("topic4", "error")]

        assert result.total_processed == 3
        assert result.success_count == 2
        assert result.failure_count == 1
        assert not result.is_successful

    def test_validation_report_properties(self) -> None:
        report = ValidationReport()
        assert report.is_valid

        report.missing_topics = ["topic1"]
        assert not report.is_valid

    @pytest.mark.asyncio
    async def test_seed_all_topics_creates_new(
        self, service: TopicSeedingService, mock_topic_repo: Mock, mock_s3_storage: Mock
    ) -> None:
        # Arrange
        mock_topic_repo.get.return_value = None
        mock_topic_repo.create.return_value = Mock(spec=LLMTopic)

        with (
            patch(
                "coaching.src.services.topic_seeding_service.list_all_endpoints"
            ) as mock_list_endpoints,
            patch(
                "coaching.src.services.topic_seeding_service.get_seed_data_for_topic"
            ) as mock_get_seed,
        ):
            mock_endpoint = Mock()
            mock_endpoint.topic_id = "test_topic"
            mock_list_endpoints.return_value = [mock_endpoint]

            mock_seed = Mock(spec=TopicSeedData)
            mock_seed.topic_id = "test_topic"
            mock_seed.topic_name = "Test Topic"
            mock_seed.topic_type = "single_shot"
            mock_seed.category = "test"
            mock_seed.description = "test"
            mock_seed.model_code = "test-model"
            mock_seed.temperature = 0.7
            mock_seed.max_tokens = 100
            mock_seed.top_p = 1.0
            mock_seed.frequency_penalty = 0.0
            mock_seed.presence_penalty = 0.0
            mock_seed.default_system_prompt = "system"
            mock_seed.default_user_prompt = "user"
            mock_seed.display_order = 1
            mock_get_seed.return_value = mock_seed

            # Act
            result = await service.seed_all_topics(force_update=False)

            # Assert
            assert len(result.created) > 0
            assert result.is_successful
            assert mock_topic_repo.create.called
            assert mock_s3_storage.save_prompt.called

    @pytest.mark.asyncio
    async def test_seed_all_topics_skips_existing(
        self, service: TopicSeedingService, mock_topic_repo: Mock
    ) -> None:
        # Arrange
        existing_topic = Mock(spec=LLMTopic)
        existing_topic.version = "1.0.0"
        mock_topic_repo.get.return_value = existing_topic

        with (
            patch(
                "coaching.src.services.topic_seeding_service.list_all_endpoints"
            ) as mock_list_endpoints,
            patch(
                "coaching.src.services.topic_seeding_service.get_seed_data_for_topic"
            ) as mock_get_seed,
        ):
            mock_endpoint = Mock()
            mock_endpoint.topic_id = "test_topic"
            mock_list_endpoints.return_value = [mock_endpoint]

            mock_seed = Mock(spec=TopicSeedData)
            mock_seed.topic_id = "test_topic"
            mock_get_seed.return_value = mock_seed

            # Act
            result = await service.seed_all_topics(force_update=False)

            # Assert
            assert len(result.skipped) > 0
            assert not mock_topic_repo.create.called
            assert not mock_topic_repo.update.called

    @pytest.mark.asyncio
    async def test_seed_all_topics_force_update(
        self, service: TopicSeedingService, mock_topic_repo: Mock, mock_s3_storage: Mock
    ) -> None:
        # Arrange
        existing_topic = Mock(spec=LLMTopic)
        existing_topic.version = "1.0.0"
        existing_topic.prompts = []
        existing_topic.get_prompt = Mock(return_value=None)
        mock_topic_repo.get.return_value = existing_topic
        mock_topic_repo.update.return_value = existing_topic

        with (
            patch(
                "coaching.src.services.topic_seeding_service.list_all_endpoints"
            ) as mock_list_endpoints,
            patch(
                "coaching.src.services.topic_seeding_service.get_seed_data_for_topic"
            ) as mock_get_seed,
        ):
            mock_endpoint = Mock()
            mock_endpoint.topic_id = "test_topic"
            mock_list_endpoints.return_value = [mock_endpoint]

            mock_seed = Mock(spec=TopicSeedData)
            mock_seed.topic_id = "test_topic"
            mock_seed.topic_name = "Test Topic"
            mock_seed.topic_type = "single_shot"
            mock_seed.category = "test"
            mock_seed.description = "test"
            mock_seed.model_code = "test-model"
            mock_seed.temperature = 0.7
            mock_seed.max_tokens = 100
            mock_seed.top_p = 1.0
            mock_seed.frequency_penalty = 0.0
            mock_seed.presence_penalty = 0.0
            mock_seed.default_system_prompt = "system"
            mock_seed.default_user_prompt = "user"
            mock_seed.display_order = 1
            mock_get_seed.return_value = mock_seed

            # Act
            result = await service.seed_all_topics(force_update=True)

            # Assert
            assert len(result.updated) > 0
            assert mock_topic_repo.update.called
            assert mock_s3_storage.save_prompt.called

    @pytest.mark.asyncio
    async def test_validate_topics(
        self, service: TopicSeedingService, mock_topic_repo: Mock
    ) -> None:
        # Arrange
        mock_topic_repo.list_all.return_value = []

        with (
            patch(
                "coaching.src.services.topic_seeding_service.list_all_endpoints"
            ) as mock_list_endpoints,
            patch(
                "coaching.src.services.topic_seeding_service.get_seed_data_for_topic"
            ) as mock_get_seed,
        ):
            mock_endpoint = Mock()
            mock_endpoint.topic_id = "test_topic"
            mock_list_endpoints.return_value = [mock_endpoint]
            mock_get_seed.return_value = None  # Simulate missing seed data

            # Act
            report = await service.validate_topics()

            # Assert
            assert isinstance(report, ValidationReport)
            assert len(report.missing_topics) > 0
