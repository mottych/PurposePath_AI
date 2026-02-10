"""Coaching message job service for async message processing.

This module provides async processing of coaching conversation messages
to avoid API Gateway 30s timeout when LLM responses take 20-90 seconds.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.ai_job import AIJob, AIJobErrorCode, AIJobStatus, AIJobType
from coaching.src.infrastructure.repositories.dynamodb_job_repository import DynamoDBJobRepository
from coaching.src.services.coaching_session_service import (
    CoachingSessionService,
    MaxTurnsReachedError,
    SessionAccessDeniedError,
    SessionIdleTimeoutError,
    SessionNotActiveError,
    SessionNotFoundError,
)
from shared.services.eventbridge_client import EventBridgePublisher, EventBridgePublishError

logger = structlog.get_logger()


class CoachingMessageJobError(Exception):
    """Base exception for coaching message job errors."""

    pass


class MessageJobNotFoundError(CoachingMessageJobError):
    """Raised when a message job is not found."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Message job not found: {job_id}")


class MessageJobValidationError(CoachingMessageJobError):
    """Raised when message job parameters are invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class CoachingMessageJobService:
    """Service for async coaching message processing.

    This service handles:
    - Creating message jobs (returns 202 Accepted immediately)
    - Executing jobs asynchronously via worker Lambda
    - Publishing events for WebSocket delivery
    - Storing results for polling fallback

    Design:
        - POST /message creates job, publishes ai.message.created event
        - Worker Lambda processes message via coaching_session_service
        - Complete message published via ai.message.completed (no token streaming)
        - Frontend receives full response via WebSocket or polling
    """

    def __init__(
        self,
        job_repository: DynamoDBJobRepository,
        session_service: CoachingSessionService,
        event_publisher: EventBridgePublisher,
    ) -> None:
        """Initialize the coaching message job service.

        Args:
            job_repository: Repository for job persistence
            session_service: CoachingSessionService for message processing
            event_publisher: EventBridge publisher for notifications
        """
        self._repository = job_repository
        self._session_service = session_service
        self._publisher = event_publisher

    async def create_message_job(
        self,
        session_id: ConversationId,
        tenant_id: TenantId,
        user_id: UserId,
        topic_id: str,
        user_message: str,
    ) -> AIJob:
        """Create a new message job for async processing.

        This method creates a job record and publishes an event to
        trigger async execution. It returns immediately with 202 Accepted.

        Args:
            session_id: Coaching session identifier
            tenant_id: Tenant identifier
            user_id: User identifier
            topic_id: AI topic (coaching configuration)
            user_message: User's message content

        Returns:
            Created AIJob with pending status

        Raises:
            MessageJobValidationError: If parameters are invalid
        """
        # Validate message not empty
        if not user_message or not user_message.strip():
            raise MessageJobValidationError("User message cannot be empty")

        # Create job with CONVERSATION_MESSAGE type
        job = AIJob(
            job_type=AIJobType.CONVERSATION_MESSAGE,
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            session_id=session_id,
            user_message=user_message,
            status=AIJobStatus.PENDING,
            estimated_duration_ms=45000,  # 45s estimate (avoid 30s timeout)
        )
        job.set_ttl(hours=24)  # Auto-cleanup after 24 hours

        # Save job
        await self._repository.save(job)

        logger.info(
            "coaching_message_job.created",
            job_id=job.job_id,
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        # Publish event to trigger async execution
        try:
            self._publisher.publish_ai_message_created(
                job_id=job.job_id,
                session_id=session_id,
                tenant_id=tenant_id,
                user_id=user_id,
                topic_id=topic_id,
                user_message=user_message,
            )
            logger.info(
                "coaching_message_job.execution_triggered",
                job_id=job.job_id,
                session_id=session_id,
            )
        except EventBridgePublishError as e:
            # If we can't publish, mark job as failed immediately
            logger.error(
                "coaching_message_job.trigger_failed",
                job_id=job.job_id,
                error=str(e),
            )
            await self._repository.update_status(
                job_id=job.job_id,
                status=AIJobStatus.FAILED,
                error=f"Failed to trigger execution: {e}",
                error_code=AIJobErrorCode.INTERNAL_ERROR,
            )
            raise MessageJobValidationError(f"Failed to trigger job execution: {e}") from e

        return job

    async def execute_message_job_from_event(
        self,
        job_id: str,
        tenant_id: str,
    ) -> None:
        """Execute a message job triggered by EventBridge event.

        This method is called by the worker Lambda when EventBridge
        delivers an ai.message.created event.

        Args:
            job_id: The job ID to execute
            tenant_id: Tenant ID for job lookup

        Raises:
            MessageJobNotFoundError: If job doesn't exist
        """
        # Retrieve the job
        job = await self._repository.get_by_id_for_tenant(job_id, tenant_id)
        if job is None:
            logger.error(
                "coaching_message_job.execute_from_event.not_found",
                job_id=job_id,
                tenant_id=tenant_id,
            )
            raise MessageJobNotFoundError(job_id)

        # Check if job is still pending (not already processed)
        if job.status != AIJobStatus.PENDING:
            logger.warning(
                "coaching_message_job.execute_from_event.already_processed",
                job_id=job_id,
                current_status=job.status.value,
            )
            return

        # Validate job type
        if job.job_type != AIJobType.CONVERSATION_MESSAGE:
            logger.error(
                "coaching_message_job.execute_from_event.wrong_type",
                job_id=job_id,
                job_type=job.job_type.value,
            )
            return

        logger.info(
            "coaching_message_job.execute_from_event.starting",
            job_id=job_id,
            session_id=job.session_id,
            tenant_id=tenant_id,
        )

        # Execute the job
        await self._execute_message_job(job)

    async def get_job(
        self,
        job_id: str,
        tenant_id: str,
    ) -> AIJob:
        """Get message job by ID with tenant isolation.

        Args:
            job_id: Job identifier
            tenant_id: Tenant identifier for isolation

        Returns:
            AIJob if found

        Raises:
            MessageJobNotFoundError: If job not found or tenant mismatch
        """
        job = await self._repository.get_by_id_for_tenant(job_id, tenant_id)
        if job is None:
            raise MessageJobNotFoundError(job_id)
        return job

    async def _execute_message_job(self, job: AIJob) -> None:
        """Execute a coaching message job asynchronously.

        This method:
        1. Updates job status to processing
        2. Calls coaching_session_service.send_message()
        3. Publishes ai.message.completed with full response
        4. Updates job record with result

        No token streaming - sends complete message when ready.

        Args:
            job: The job to execute
        """
        start_time = time.time()

        if not job.session_id or not job.user_message:
            await self._handle_failure(
                job=job,
                error="Job missing session_id or user_message",
                error_code=AIJobErrorCode.PARAMETER_VALIDATION,
                start_time=start_time,
            )
            return

        try:
            # Update status to processing
            await self._repository.update_status(job.job_id, AIJobStatus.PROCESSING)

            logger.info(
                "coaching_message_job.processing_message",
                job_id=job.job_id,
                session_id=job.session_id,
                topic_id=job.topic_id,
            )

            # Execute message through coaching session service
            message_response = await self._session_service.send_message(
                session_id=job.session_id,
                tenant_id=job.tenant_id,
                user_id=job.user_id,
                user_message=job.user_message,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)

            # Build result dict (may include extraction result if final)
            result_dict: dict[str, Any] = {
                "message": message_response.message,
                "is_final": message_response.is_final,
                "status": message_response.status.value,
                "turn": message_response.turn,
                "max_turns": message_response.max_turns,
                "message_count": message_response.message_count,
            }

            if message_response.result:
                result_dict["result"] = message_response.result.model_dump(
                    by_alias=True, mode="json"
                )

            if message_response.metadata:
                result_dict["metadata"] = message_response.metadata

            # Update job with result
            await self._repository.update_status(
                job_id=job.job_id,
                status=AIJobStatus.COMPLETED,
                result=result_dict,
                processing_time_ms=processing_time_ms,
            )

            # Publish completed event with full response (no streaming)
            try:
                self._publisher.publish_ai_message_completed(
                    job_id=job.job_id,
                    session_id=job.session_id,
                    tenant_id=job.tenant_id,
                    user_id=job.user_id,
                    topic_id=job.topic_id,
                    message=message_response.message,
                    is_final=message_response.is_final,
                    result=result_dict.get("result"),
                )
            except EventBridgePublishError as e:
                logger.warning(
                    "coaching_message_job.completed_event_failed",
                    job_id=job.job_id,
                    error=str(e),
                )

            logger.info(
                "coaching_message_job.completed",
                job_id=job.job_id,
                session_id=job.session_id,
                is_final=message_response.is_final,
                processing_time_ms=processing_time_ms,
            )

        except SessionNotFoundError as e:
            await self._handle_failure(
                job=job,
                error=f"Session not found: {e}",
                error_code=AIJobErrorCode.PARAMETER_VALIDATION,
                start_time=start_time,
            )

        except SessionAccessDenied

Error as e:
            await self._handle_failure(
                job=job,
                error=f"Session access denied: {e}",
                error_code=AIJobErrorCode.PARAMETER_VALIDATION,
                start_time=start_time,
            )

        except (SessionNotActiveError, SessionIdleTimeoutError) as e:
            await self._handle_failure(
                job=job,
                error=str(e),
                error_code=AIJobErrorCode.PARAMETER_VALIDATION,
                start_time=start_time,
            )

        except MaxTurnsReachedError as e:
            await self._handle_failure(
                job=job,
                error=str(e),
                error_code=AIJobErrorCode.PARAMETER_VALIDATION,
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
                "coaching_message_job.execution_error",
                job_id=job.job_id,
                session_id=job.session_id,
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
        """Handle job failure by updating status and publishing event.

        Args:
            job: The failed job
            error: Error message
            error_code: Error categorization
            start_time: Execution start time for duration calculation
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
            self._publisher.publish_ai_message_failed(
                job_id=job.job_id,
                session_id=job.session_id or "",
                tenant_id=job.tenant_id,
                user_id=job.user_id,
                topic_id=job.topic_id,
                error=error,
                error_code=error_code.value,
            )
        except EventBridgePublishError as e:
            logger.warning(
                "coaching_message_job.failed_event_failed",
                job_id=job.job_id,
                error=str(e),
            )

        logger.error(
            "coaching_message_job.failed",
            job_id=job.job_id,
            error=error,
            error_code=error_code.value,
            processing_time_ms=processing_time_ms,
        )
