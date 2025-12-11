"""Unit tests for async execution service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.domain.entities.ai_job import AIJob, AIJobStatus
from coaching.src.services.async_execution_service import (
    AsyncAIExecutionService,
    JobNotFoundError,
    JobValidationError,
)
from shared.services.eventbridge_client import EventBridgePublishError


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

    @pytest.mark.asyncio
    async def test_create_job_publishes_event(
        self,
        service: AsyncAIExecutionService,
        mock_job_repository: AsyncMock,
        mock_eventbridge: MagicMock,
    ) -> None:
        """Test that create_job publishes ai.job.created event."""
        # Arrange
        mock_job_repository.save.return_value = None
        mock_eventbridge.publish_ai_job_created.return_value = "event-123"

        # Mock the endpoint registry to return a valid topic
        with patch(
            "coaching.src.services.async_execution_service.get_endpoint_by_topic_id"
        ) as mock_get_endpoint:
            from coaching.src.core.constants import TopicType
            from coaching.src.core.endpoint_registry import EndpointDefinition

            mock_endpoint = MagicMock(spec=EndpointDefinition)
            mock_endpoint.is_active = True
            mock_endpoint.topic_type = TopicType.SINGLE_SHOT
            mock_endpoint.response_model = "NicheReviewResponse"
            mock_get_endpoint.return_value = mock_endpoint

            with patch(
                "coaching.src.services.async_execution_service.get_required_parameter_names_for_topic"
            ) as mock_get_params:
                mock_get_params.return_value = ["current_value"]

                with patch(
                    "coaching.src.services.async_execution_service.get_response_model"
                ) as mock_get_response:
                    mock_get_response.return_value = MagicMock()

                    # Act
                    job = await service.create_job(
                        tenant_id="tenant_456",
                        user_id="user_123",
                        topic_id="niche_review",
                        parameters={"current_value": "Test value"},
                    )

        # Assert
        assert job is not None
        mock_job_repository.save.assert_called_once()
        mock_eventbridge.publish_ai_job_created.assert_called_once()

        # Verify the event was published with correct parameters
        call_kwargs = mock_eventbridge.publish_ai_job_created.call_args.kwargs
        assert call_kwargs["job_id"] == job.job_id
        assert call_kwargs["tenant_id"] == "tenant_456"
        assert call_kwargs["user_id"] == "user_123"
        assert call_kwargs["topic_id"] == "niche_review"
        assert call_kwargs["parameters"] == {"current_value": "Test value"}

    @pytest.mark.asyncio
    async def test_create_job_fails_on_event_publish_error(
        self,
        service: AsyncAIExecutionService,
        mock_job_repository: AsyncMock,
        mock_eventbridge: MagicMock,
    ) -> None:
        """Test that create_job fails gracefully when event publishing fails."""
        # Arrange
        mock_job_repository.save.return_value = None
        mock_eventbridge.publish_ai_job_created.side_effect = EventBridgePublishError(
            "Failed to publish"
        )

        # Mock the endpoint registry to return a valid topic
        with patch(
            "coaching.src.services.async_execution_service.get_endpoint_by_topic_id"
        ) as mock_get_endpoint:
            from coaching.src.core.constants import TopicType
            from coaching.src.core.endpoint_registry import EndpointDefinition

            mock_endpoint = MagicMock(spec=EndpointDefinition)
            mock_endpoint.is_active = True
            mock_endpoint.topic_type = TopicType.SINGLE_SHOT
            mock_endpoint.response_model = "NicheReviewResponse"
            mock_get_endpoint.return_value = mock_endpoint

            with patch(
                "coaching.src.services.async_execution_service.get_required_parameter_names_for_topic"
            ) as mock_get_params:
                mock_get_params.return_value = ["current_value"]

                with patch(
                    "coaching.src.services.async_execution_service.get_response_model"
                ) as mock_get_response:
                    mock_get_response.return_value = MagicMock()

                    # Act & Assert
                    with pytest.raises(JobValidationError, match="Failed to trigger"):
                        await service.create_job(
                            tenant_id="tenant_456",
                            user_id="user_123",
                            topic_id="niche_review",
                            parameters={"current_value": "Test value"},
                        )

        # Verify job was marked as failed
        mock_job_repository.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_job_from_event_success(
        self,
        service: AsyncAIExecutionService,
        mock_job_repository: AsyncMock,
        mock_eventbridge: MagicMock,
        mock_ai_engine: AsyncMock,
    ) -> None:
        """Test execute_job_from_event executes pending job."""
        # Arrange
        job = AIJob(
            user_id="user_123",
            tenant_id="tenant_456",
            topic_id="niche_review",
            parameters={"current_value": "Test value"},
            status=AIJobStatus.PENDING,
        )
        mock_job_repository.get_by_id_for_tenant.return_value = job
        mock_job_repository.update_status.return_value = None

        # Mock the endpoint registry
        with patch(
            "coaching.src.services.async_execution_service.get_endpoint_by_topic_id"
        ) as mock_get_endpoint:
            from coaching.src.core.endpoint_registry import EndpointDefinition

            mock_endpoint = MagicMock(spec=EndpointDefinition)
            mock_endpoint.response_model = "NicheReviewResponse"
            mock_get_endpoint.return_value = mock_endpoint

            with patch(
                "coaching.src.services.async_execution_service.get_response_model"
            ) as mock_get_response:
                mock_response_model = MagicMock()
                mock_get_response.return_value = mock_response_model

                # Mock AI engine result
                mock_result = MagicMock()
                mock_result.model_dump.return_value = {"quality_review": "Good", "suggestions": []}
                mock_ai_engine.execute_single_shot.return_value = mock_result

                # Act
                await service.execute_job_from_event(
                    job_id=job.job_id,
                    tenant_id="tenant_456",
                )

        # Assert
        mock_job_repository.get_by_id_for_tenant.assert_called_once_with(job.job_id, "tenant_456")
        mock_ai_engine.execute_single_shot.assert_called_once()
        mock_eventbridge.publish_ai_job_completed.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_job_from_event_skips_non_pending(
        self,
        service: AsyncAIExecutionService,
        mock_job_repository: AsyncMock,
        mock_ai_engine: AsyncMock,
    ) -> None:
        """Test execute_job_from_event skips already processed jobs."""
        # Arrange - job is already completed
        job = AIJob(
            user_id="user_123",
            tenant_id="tenant_456",
            topic_id="niche_review",
            parameters={"current_value": "Test value"},
            status=AIJobStatus.COMPLETED,
        )
        mock_job_repository.get_by_id_for_tenant.return_value = job

        # Act
        await service.execute_job_from_event(
            job_id=job.job_id,
            tenant_id="tenant_456",
        )

        # Assert - AI engine should NOT be called
        mock_ai_engine.execute_single_shot.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_job_from_event_not_found(
        self,
        service: AsyncAIExecutionService,
        mock_job_repository: AsyncMock,
    ) -> None:
        """Test execute_job_from_event raises error for non-existent job."""
        # Arrange
        mock_job_repository.get_by_id_for_tenant.return_value = None

        # Act & Assert
        with pytest.raises(JobNotFoundError):
            await service.execute_job_from_event(
                job_id="nonexistent",
                tenant_id="tenant_456",
            )
