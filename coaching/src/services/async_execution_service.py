"""Async AI execution service.

This module provides the service layer for async AI job execution,
coordinating between the API, domain models, repository, and event publishing.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import structlog
from coaching.src.application.ai_engine.unified_ai_engine import (
    ParameterValidationError,
    PromptRenderError,
    TopicNotFoundError,
    UnifiedAIEngine,
)
from coaching.src.core.constants import TopicType
from coaching.src.core.endpoint_registry import (
    get_endpoint_by_topic_id,
    get_required_parameter_names_for_topic,
)
from coaching.src.core.response_model_registry import get_response_model
from coaching.src.domain.entities.ai_job import AIJob, AIJobErrorCode, AIJobStatus
from coaching.src.infrastructure.repositories.dynamodb_job_repository import DynamoDBJobRepository
from shared.services.eventbridge_client import EventBridgePublisher, EventBridgePublishError

logger = structlog.get_logger()


class AsyncAIExecutionError(Exception):
    """Base exception for async AI execution errors."""

    pass


class JobNotFoundError(AsyncAIExecutionError):
    """Raised when a job is not found."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job not found: {job_id}")


class JobValidationError(AsyncAIExecutionError):
    """Raised when job parameters are invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class AsyncAIExecutionService:
    """Service for async AI job execution.

    This service handles:
    - Creating and validating async jobs
    - Executing jobs asynchronously
    - Publishing events for real-time notifications
    - Retrieving job status and results

    Design:
        - Jobs are created synchronously and returned immediately
        - Execution happens asynchronously via background task
        - Events are published to EventBridge for WebSocket delivery
        - Results are stored in DynamoDB for polling fallback
    """

    def __init__(
        self,
        job_repository: DynamoDBJobRepository,
        ai_engine: UnifiedAIEngine,
        event_publisher: EventBridgePublisher,
    ) -> None:
        """Initialize the async execution service.

        Args:
            job_repository: Repository for job persistence
            ai_engine: UnifiedAIEngine for AI execution
            event_publisher: EventBridge publisher for notifications
        """
        self._repository = job_repository
        self._engine = ai_engine
        self._publisher = event_publisher

    async def create_job(
        self,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        parameters: dict[str, Any],
    ) -> AIJob:
        """Create and validate a new async AI job.

        This method validates the request, creates a job record,
        and starts background execution. It returns immediately
        with the job ID for tracking.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            topic_id: AI topic to execute
            parameters: Input parameters for the topic

        Returns:
            Created AIJob with pending status

        Raises:
            JobValidationError: If topic or parameters are invalid
        """
        # Validate topic exists and is active
        endpoint = get_endpoint_by_topic_id(topic_id)
        if endpoint is None:
            raise JobValidationError(f"Topic not found: {topic_id}")

        if not endpoint.is_active:
            raise JobValidationError(f"Topic is not active: {topic_id}")

        # Validate topic is single-shot
        if endpoint.topic_type != TopicType.SINGLE_SHOT:
            raise JobValidationError(
                f"Topic {topic_id} is type {endpoint.topic_type.value}, "
                "only single-shot topics are supported for async execution"
            )

        # Validate required parameters
        required_params = get_required_parameter_names_for_topic(topic_id)
        missing = [p for p in required_params if p not in parameters]
        if missing:
            raise JobValidationError(f"Missing required parameters for topic {topic_id}: {missing}")

        # Validate response model exists
        response_model = get_response_model(endpoint.response_model)
        if response_model is None:
            raise JobValidationError(f"Response model not configured: {endpoint.response_model}")

        # Create job
        job = AIJob(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            parameters=parameters,
            status=AIJobStatus.PENDING,
            estimated_duration_ms=self._estimate_duration(topic_id),
        )
        job.set_ttl(hours=24)  # Auto-cleanup after 24 hours

        # Save job
        await self._repository.save(job)

        logger.info(
            "async_job.created",
            job_id=job.job_id,
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
        )

        # Start background execution
        # Note: We don't await this task - it runs in the background
        # The task is fire-and-forget; results are delivered via EventBridge
        task = asyncio.create_task(self._execute_job(job))
        # Add callback to log any unexpected errors
        task.add_done_callback(self._task_done_callback)

        return job

    def _task_done_callback(self, task: asyncio.Task[None]) -> None:
        """Callback for background task completion.

        Logs any unexpected exceptions from background tasks.
        """
        if task.cancelled():
            logger.warning("async_job.task_cancelled")
        elif task.exception():
            logger.exception(
                "async_job.task_exception",
                error=str(task.exception()),
            )

    async def get_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> AIJob:
        """Get job by ID with tenant isolation.

        Args:
            job_id: Job identifier
            tenant_id: Tenant identifier for isolation

        Returns:
            AIJob if found

        Raises:
            JobNotFoundError: If job not found or tenant mismatch
        """
        job = await self._repository.get_by_id_for_tenant(job_id, tenant_id)
        if job is None:
            raise JobNotFoundError(job_id)
        return job

    async def _execute_job(self, job: AIJob) -> None:
        """Execute an AI job asynchronously.

        This method:
        1. Publishes job.started event
        2. Executes the AI topic
        3. Publishes job.completed or job.failed event
        4. Updates job record in DynamoDB

        Args:
            job: The job to execute
        """
        start_time = time.time()

        try:
            # Update status to processing
            await self._repository.update_status(job.job_id, AIJobStatus.PROCESSING)

            # Publish started event
            try:
                self._publisher.publish_ai_job_started(
                    job_id=job.job_id,
                    tenant_id=job.tenant_id,
                    user_id=job.user_id,
                    topic_id=job.topic_id,
                    estimated_duration_ms=job.estimated_duration_ms,
                )
            except EventBridgePublishError as e:
                logger.warning(
                    "async_job.started_event_failed",
                    job_id=job.job_id,
                    error=str(e),
                )

            # Get response model
            endpoint = get_endpoint_by_topic_id(job.topic_id)
            if endpoint is None:
                raise TopicNotFoundError(job.topic_id)

            response_model = get_response_model(endpoint.response_model)
            if response_model is None:
                raise PromptRenderError(
                    job.topic_id,
                    "system",
                    f"Response model not configured: {endpoint.response_model}",
                )

            # Execute AI
            result = await self._engine.execute_single_shot(
                topic_id=job.topic_id,
                parameters=job.parameters,
                response_model=response_model,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)
            result_dict = result.model_dump()

            # Update job with result
            await self._repository.update_status(
                job_id=job.job_id,
                status=AIJobStatus.COMPLETED,
                result=result_dict,
                processing_time_ms=processing_time_ms,
            )

            # Publish completed event
            try:
                self._publisher.publish_ai_job_completed(
                    job_id=job.job_id,
                    tenant_id=job.tenant_id,
                    user_id=job.user_id,
                    topic_id=job.topic_id,
                    result=result_dict,
                    processing_time_ms=processing_time_ms,
                )
            except EventBridgePublishError as e:
                logger.warning(
                    "async_job.completed_event_failed",
                    job_id=job.job_id,
                    error=str(e),
                )

            logger.info(
                "async_job.completed",
                job_id=job.job_id,
                topic_id=job.topic_id,
                processing_time_ms=processing_time_ms,
            )

        except TopicNotFoundError as e:
            await self._handle_failure(
                job=job,
                error=str(e),
                error_code=AIJobErrorCode.TOPIC_NOT_FOUND,
                start_time=start_time,
            )

        except ParameterValidationError as e:
            await self._handle_failure(
                job=job,
                error=str(e),
                error_code=AIJobErrorCode.PARAMETER_VALIDATION,
                start_time=start_time,
            )

        except PromptRenderError as e:
            await self._handle_failure(
                job=job,
                error=str(e),
                error_code=AIJobErrorCode.PROMPT_RENDER_ERROR,
                start_time=start_time,
            )

        except TimeoutError:
            await self._handle_failure(
                job=job,
                error="LLM request timed out",
                error_code=AIJobErrorCode.LLM_TIMEOUT,
                start_time=start_time,
            )

        except Exception as e:
            logger.exception(
                "async_job.execution_error",
                job_id=job.job_id,
                error=str(e),
            )
            await self._handle_failure(
                job=job,
                error=f"Internal error: {e!s}",
                error_code=AIJobErrorCode.INTERNAL_ERROR,
                start_time=start_time,
            )

    async def _handle_failure(
        self,
        job: AIJob,
        error: str,
        error_code: AIJobErrorCode,
        start_time: float,
    ) -> None:
        """Handle job failure.

        Args:
            job: The failed job
            error: Error message
            error_code: Error categorization
            start_time: Job start time for duration calculation
        """
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Update job with error
        await self._repository.update_status(
            job_id=job.job_id,
            status=AIJobStatus.FAILED,
            error=error,
            error_code=error_code,
            processing_time_ms=processing_time_ms,
        )

        # Publish failed event
        try:
            self._publisher.publish_ai_job_failed(
                job_id=job.job_id,
                tenant_id=job.tenant_id,
                user_id=job.user_id,
                topic_id=job.topic_id,
                error=error,
                error_code=error_code.value,
            )
        except EventBridgePublishError as e:
            logger.warning(
                "async_job.failed_event_failed",
                job_id=job.job_id,
                error=str(e),
            )

        logger.warning(
            "async_job.failed",
            job_id=job.job_id,
            topic_id=job.topic_id,
            error=error,
            error_code=error_code.value,
            processing_time_ms=processing_time_ms,
        )

    def _estimate_duration(self, topic_id: str) -> int:
        """Estimate processing duration for a topic.

        Args:
            topic_id: The topic to estimate

        Returns:
            Estimated duration in milliseconds
        """
        # Topic-specific estimates based on complexity
        estimates = {
            "niche_review": 35000,
            "ica_review": 35000,
            "value_proposition_review": 35000,
            "website_scan": 45000,
            "alignment_check": 30000,
            "strategy_suggestions": 40000,
            "kpi_recommendations": 40000,
        }
        return estimates.get(topic_id, 30000)
