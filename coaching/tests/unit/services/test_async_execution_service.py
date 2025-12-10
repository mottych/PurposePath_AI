"""Unit tests for async execution service."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.domain.entities.ai_job import AIJob
from coaching.src.services.async_execution_service import (
    AsyncAIExecutionService,
    JobNotFoundError,
    JobValidationError,
)


class TestAsyncAIExecutionService:
    """Tests for async execution service."""

    @pytest.fixture
    def mock_job_repository(self) -> AsyncMock:
        """Create mock job repository."""
        repo = AsyncMock()
        return repo

    @pytest.fixture
    def mock_eventbridge(self) -> MagicMock:
        """Create mock EventBridge publisher."""
        publisher = MagicMock()
        publisher.publish_event = MagicMock(return_value="event-123")
        return publisher

    @pytest.fixture
    def mock_ai_engine(self) -> AsyncMock:
        """Create mock AI engine."""
        engine = AsyncMock()
        return engine

    @pytest.fixture
    def service(
        self,
        mock_job_repository: AsyncMock,
        mock_eventbridge: MagicMock,
        mock_ai_engine: AsyncMock,
    ) -> AsyncAIExecutionService:
        """Create service instance with mocks."""
        return AsyncAIExecutionService(
            job_repository=mock_job_repository,
            ai_engine=mock_ai_engine,
            event_publisher=mock_eventbridge,
        )

    @pytest.fixture
    def sample_job(self) -> AIJob:
        """Create a sample job for testing."""
        return AIJob(
            user_id="user_123",
            tenant_id="tenant_456",
            topic_id="onboarding_review",
            parameters={"review_text": "Test review"},
        )

    @pytest.mark.asyncio
    async def test_create_job_validates_topic_not_found(
        self,
        service: AsyncAIExecutionService,
    ) -> None:
        """Test that creating job with invalid topic raises error."""
        # The endpoint registry won't find this topic
        with pytest.raises(JobValidationError, match="Topic not found"):
            await service.create_job(
                user_id="user_123",
                tenant_id="tenant_456",
                topic_id="nonexistent_topic",
                parameters={},
            )

    @pytest.mark.asyncio
    async def test_get_job_returns_job(
        self,
        service: AsyncAIExecutionService,
        mock_job_repository: AsyncMock,
        sample_job: AIJob,
    ) -> None:
        """Test getting job by ID."""
        # Arrange
        mock_job_repository.get_by_id_for_tenant.return_value = sample_job

        # Act
        result = await service.get_job(
            job_id=sample_job.job_id,
            tenant_id="tenant_456",
        )

        # Assert
        assert result == sample_job
        mock_job_repository.get_by_id_for_tenant.assert_called_once_with(
            sample_job.job_id, "tenant_456"
        )

    @pytest.mark.asyncio
    async def test_get_job_raises_not_found(
        self,
        service: AsyncAIExecutionService,
        mock_job_repository: AsyncMock,
    ) -> None:
        """Test that getting non-existent job raises error."""
        # Arrange
        mock_job_repository.get_by_id_for_tenant.return_value = None

        # Act & Assert
        with pytest.raises(JobNotFoundError):
            await service.get_job(
                job_id="nonexistent",
                tenant_id="tenant_456",
            )
