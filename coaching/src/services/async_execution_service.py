"""Async AI execution service.

This module provides the service layer for async AI job execution,
coordinating between the API, domain models, repository, and event publishing.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import structlog

from coaching.src.api.models.ai_job_kickoff import ApiAiJobRequestedDetail
from coaching.src.application.ai_engine.unified_ai_engine import (
    ParameterValidationError,
    PromptRenderError,
    TopicNotFoundError,
    UnifiedAIEngine,
)
from coaching.src.application.llm_usage.llm_invocation_context import LlmInvocationContext
from coaching.src.core.config_multitenant import settings
from coaching.src.core.constants import TopicCategory, TopicType
from coaching.src.core.response_model_registry import get_response_model
from coaching.src.core.topic_registry import (
    get_required_parameter_names_for_topic,
    get_topic_by_topic_id,
)
from coaching.src.domain.entities.ai_job import AIJob, AIJobErrorCode, AIJobStatus
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient
from coaching.src.infrastructure.repositories.dynamodb_job_repository import DynamoDBJobRepository
from coaching.src.services.template_parameter_processor import TemplateParameterProcessor
from shared.services.dynamodb_serialization import convert_floats_to_decimal
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

    def _validate_and_build_pending_job(
        self,
        *,
        job_id: str,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        parameters: dict[str, Any],
        jwt_token: str | None,
        correlation_id: str | None,
        idempotency_key: str | None,
        event_id: str | None,
        request_id: str | None = None,
        topic_category: str | None = None,
        event_signal: str | None = None,
        kickoff_transport: str | None = None,
    ) -> AIJob:
        """Validate topic/params and build a pending AIJob (no persistence)."""
        endpoint = get_topic_by_topic_id(topic_id)
        if endpoint is None:
            raise JobValidationError(f"Topic not found: {topic_id}")

        if not endpoint.is_active:
            raise JobValidationError(f"Topic is not active: {topic_id}")

        if endpoint.topic_type != TopicType.SINGLE_SHOT:
            raise JobValidationError(
                f"Topic {topic_id} is type {endpoint.topic_type.value}, "
                "only single-shot topics are supported for async execution"
            )

        required_params = get_required_parameter_names_for_topic(topic_id)
        missing = [p for p in required_params if p not in parameters]
        if missing:
            raise JobValidationError(f"Missing required parameters for topic {topic_id}: {missing}")

        response_model = get_response_model(endpoint.response_model)
        if response_model is None:
            raise JobValidationError(f"Response model not configured: {endpoint.response_model}")

        estimated_duration = self._estimate_duration(topic_id)
        job = AIJob(
            job_id=job_id,
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            parameters=parameters,
            jwt_token=jwt_token,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            event_id=event_id,
            request_id=request_id,
            topic_category=topic_category,
            event_signal=event_signal,
            kickoff_transport=kickoff_transport,
            status=AIJobStatus.PENDING,
            estimated_duration_ms=estimated_duration,
        )
        job.set_ttl(hours=24)
        return job

    def _publish_job_created_trigger(self, job: AIJob) -> None:
        """Publish `ai.job.created` so a separate Lambda invocation runs the worker."""
        self._publisher.publish_ai_job_created(
            job_id=job.job_id,
            tenant_id=job.tenant_id,
            user_id=job.user_id,
            topic_id=job.topic_id,
            parameters=job.parameters,
            estimated_duration_ms=job.estimated_duration_ms,
            correlation_id=job.correlation_id,
            idempotency_key=job.idempotency_key,
            event_id=job.event_id,
        )

    @staticmethod
    def _should_publish_email_insight_domain_terminal(job: AIJob) -> bool:
        """v2.4 domain-bus terminals only for Api EventBridge kickoff (issue #305)."""
        return (
            job.request_id is not None
            and job.topic_category == TopicCategory.EMAIL_INSIGHT.value
            and job.event_id is not None
            and job.kickoff_transport == "eventbridge"
        )

    def _publish_async_job_completed_terminal(
        self,
        job: AIJob,
        *,
        result_dict: dict[str, Any],
        processing_time_ms: int,
    ) -> None:
        """Publish completion: v2.4 terminal to domain bus or legacy WebSocket-oriented event."""
        if self._should_publish_email_insight_domain_terminal(job):
            self._publisher.publish_email_insight_terminal_v24(
                terminal_status="completed",
                terminal_event_id=str(uuid4()),
                occurred_at_utc=datetime.now(UTC),
                job_id=job.job_id,
                request_id=job.request_id or "",
                kickoff_event_id=job.event_id or "",
                tenant_id=job.tenant_id,
                user_id=job.user_id,
                correlation_id=job.correlation_id or "",
                idempotency_key=job.idempotency_key or "",
                topic_category=job.topic_category or TopicCategory.EMAIL_INSIGHT.value,
                topic_id=job.topic_id,
                event_signal=job.event_signal or job.topic_id,
                data={"result": result_dict},
            )
            return
        self._publisher.publish_ai_job_completed(
            job_id=job.job_id,
            tenant_id=job.tenant_id,
            user_id=job.user_id,
            topic_id=job.topic_id,
            result=result_dict,
            processing_time_ms=processing_time_ms,
        )

    def _publish_async_job_failed_terminal(
        self,
        job: AIJob,
        *,
        error: str,
        error_code: AIJobErrorCode,
        _processing_time_ms: int,
    ) -> None:
        """Publish failure: v2.4 terminal or legacy failed event."""
        if self._should_publish_email_insight_domain_terminal(job):
            self._publisher.publish_email_insight_terminal_v24(
                terminal_status="failed",
                terminal_event_id=str(uuid4()),
                occurred_at_utc=datetime.now(UTC),
                job_id=job.job_id,
                request_id=job.request_id or "",
                kickoff_event_id=job.event_id or "",
                tenant_id=job.tenant_id,
                user_id=job.user_id,
                correlation_id=job.correlation_id or "",
                idempotency_key=job.idempotency_key or "",
                topic_category=job.topic_category or TopicCategory.EMAIL_INSIGHT.value,
                topic_id=job.topic_id,
                event_signal=job.event_signal or job.topic_id,
                data={"errorCode": error_code.value, "error": error},
            )
            return
        self._publisher.publish_ai_job_failed(
            job_id=job.job_id,
            tenant_id=job.tenant_id,
            user_id=job.user_id,
            topic_id=job.topic_id,
            error=error,
            error_code=error_code.value,
        )

    async def ingest_api_job_requested_event(self, detail: ApiAiJobRequestedDetail) -> None:
        """Persist job from PurposePath_Api EventBridge kickoff and trigger async execution (#302)."""
        if detail.stage is not None and detail.stage != settings.stage:
            raise JobValidationError(
                f"Event stage {detail.stage!r} does not match AI service stage {settings.stage!r}"
            )

        parameters = dict(detail.activity_data)
        parameters.setdefault("locale", detail.locale)
        parameters.setdefault("timezone", detail.timezone)

        job = self._validate_and_build_pending_job(
            job_id=detail.job_id,
            tenant_id=detail.tenant_id,
            user_id=detail.user_id,
            topic_id=detail.topic_id,
            parameters=parameters,
            jwt_token=detail.auth_context.service_token,
            correlation_id=detail.correlation_id,
            idempotency_key=detail.idempotency_key,
            event_id=detail.event_id,
            request_id=detail.request_id,
            topic_category=detail.topic_category,
            event_signal=detail.event_signal,
            kickoff_transport="eventbridge",
        )

        inserted = await self._repository.put_if_absent(job)
        if inserted:
            logger.info(
                "async_job.api_kickoff_inserted",
                job_id=job.job_id,
                tenant_id=job.tenant_id,
                topic_id=job.topic_id,
                correlation_id=job.correlation_id,
                idempotency_key=job.idempotency_key,
                event_id=job.event_id,
            )
            try:
                self._publish_job_created_trigger(job)
                logger.info(
                    "async_job.api_kickoff_execution_triggered",
                    job_id=job.job_id,
                    topic_id=job.topic_id,
                )
            except EventBridgePublishError as e:
                logger.error(
                    "async_job.api_kickoff_trigger_failed",
                    job_id=job.job_id,
                    error=str(e),
                )
                await self._repository.update_status(
                    job_id=job.job_id,
                    status=AIJobStatus.FAILED,
                    error=f"Failed to trigger execution: {e}",
                    error_code=AIJobErrorCode.INTERNAL_ERROR,
                )
                raise JobValidationError(f"Failed to trigger job execution: {e}") from e
            return

        existing = await self._repository.get_by_id_for_tenant(job.job_id, job.tenant_id)
        if existing is None:
            raise JobValidationError(
                f"Job id {job.job_id} already exists for a different tenant (isolation violation)"
            )
        if existing.status == AIJobStatus.PENDING:
            logger.info(
                "async_job.api_kickoff_idempotent_pending",
                job_id=job.job_id,
                tenant_id=job.tenant_id,
            )
            await self.execute_job_from_event(job_id=job.job_id, tenant_id=job.tenant_id)

    async def create_job(
        self,
        tenant_id: str,
        user_id: str,
        topic_id: str,
        parameters: dict[str, Any],
        jwt_token: str | None = None,
        correlation_id: str | None = None,
        idempotency_key: str | None = None,
        event_id: str | None = None,
        request_id: str | None = None,
        topic_category: str | None = None,
        event_signal: str | None = None,
        kickoff_transport: str | None = None,
    ) -> AIJob:
        """Create and validate a new async AI job.

        This method validates the request, creates a job record,
        and publishes an event to trigger async execution.
        It returns immediately with the job ID for tracking.

        The actual execution happens in a separate Lambda invocation
        triggered by the ai.job.created EventBridge event.

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
        job = self._validate_and_build_pending_job(
            job_id=str(uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            parameters=parameters,
            jwt_token=jwt_token,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            event_id=event_id,
            request_id=request_id,
            topic_category=topic_category,
            event_signal=event_signal,
            kickoff_transport=kickoff_transport,
        )

        await self._repository.save(job)

        logger.info(
            "async_job.created",
            job_id=job.job_id,
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=topic_id,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            event_id=event_id,
        )

        try:
            self._publish_job_created_trigger(job)
            logger.info(
                "async_job.execution_triggered",
                job_id=job.job_id,
                topic_id=topic_id,
            )
        except EventBridgePublishError as e:
            logger.error(
                "async_job.trigger_failed",
                job_id=job.job_id,
                error=str(e),
            )
            await self._repository.update_status(
                job_id=job.job_id,
                status=AIJobStatus.FAILED,
                error=f"Failed to trigger execution: {e}",
                error_code=AIJobErrorCode.INTERNAL_ERROR,
            )
            raise JobValidationError(f"Failed to trigger job execution: {e}") from e

        return job

    async def execute_job_from_event(
        self,
        job_id: str,
        tenant_id: str,
    ) -> None:
        """Execute a job triggered by an EventBridge event.

        This method is called by the internal job execution endpoint
        when EventBridge delivers an ai.job.created event.

        Args:
            job_id: The job ID to execute
            tenant_id: Tenant ID for job lookup

        Raises:
            JobNotFoundError: If job doesn't exist
        """
        # Retrieve the job
        job = await self._repository.get_by_id_for_tenant(job_id, tenant_id)
        if job is None:
            logger.error(
                "async_job.execute_from_event.not_found",
                job_id=job_id,
                tenant_id=tenant_id,
            )
            raise JobNotFoundError(job_id)

        if job.status != AIJobStatus.PENDING:
            logger.warning(
                "async_job.execute_from_event.already_processed",
                job_id=job_id,
                current_status=job.status.value,
            )
            return

        if not await self._repository.claim_pending_job(job_id):
            logger.info(
                "async_job.execute_from_event.claim_lost",
                job_id=job_id,
                tenant_id=tenant_id,
            )
            return

        job = await self._repository.get_by_id_for_tenant(job_id, tenant_id)
        if job is None or job.status != AIJobStatus.PROCESSING:
            logger.warning(
                "async_job.execute_from_event.unexpected_after_claim",
                job_id=job_id,
                has_job=job is not None,
                status=job.status.value if job else None,
            )
            return

        logger.info(
            "async_job.execute_from_event.starting",
            job_id=job_id,
            tenant_id=tenant_id,
            topic_id=job.topic_id,
        )

        await self._execute_job(job, already_processing=True)

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

    async def _execute_job(self, job: AIJob, *, already_processing: bool = False) -> None:
        """Execute an AI job asynchronously.

        This method:
        1. Publishes job.started event
        2. Executes the AI topic
        3. Publishes job.completed or job.failed event
        4. Updates job record in DynamoDB

        Args:
            job: The job to execute
            already_processing: When True, skip transition to processing (claim already applied)
        """
        start_time = time.time()

        try:
            if not already_processing:
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
            endpoint = get_topic_by_topic_id(job.topic_id)
            if endpoint is None:
                raise TopicNotFoundError(job.topic_id)

            response_model = get_response_model(endpoint.response_model)
            if response_model is None:
                raise PromptRenderError(
                    job.topic_id,
                    "system",
                    f"Response model not configured: {endpoint.response_model}",
                )
            if (
                getattr(endpoint, "category", None) == TopicCategory.EMAIL_INSIGHT
                and not job.jwt_token
            ):
                raise PermissionError("missing service token")

            # Create template processor for parameter enrichment
            logger.info(
                "async_job.creating_template_processor",
                job_id=job.job_id,
                topic_id=job.topic_id,
            )
            template_processor = self._create_template_processor(job.jwt_token)

            # Execute AI with enrichment
            logger.info(
                "async_job.starting_ai_execution",
                job_id=job.job_id,
                topic_id=job.topic_id,
                parameter_count=len(job.parameters),
            )
            result = await self._engine.execute_single_shot(
                topic_id=job.topic_id,
                parameters=job.parameters,
                response_model=response_model,
                user_id=job.user_id,
                tenant_id=job.tenant_id,
                template_processor=template_processor,
                invocation_context=LlmInvocationContext(
                    entry_source="async_job",
                    job_id=job.job_id,
                    correlation_id=job.correlation_id,
                    estimated_duration_ms=job.estimated_duration_ms,
                ),
            )
            logger.info(
                "async_job.ai_execution_completed",
                job_id=job.job_id,
                topic_id=job.topic_id,
            )

            processing_time_ms = int((time.time() - start_time) * 1000)
            # Use mode='json' to serialize datetime objects to ISO format strings
            result_dict = result.model_dump(by_alias=True, mode="json")

            # Convert floats to Decimal for DynamoDB compatibility
            result_dict_dynamodb = convert_floats_to_decimal(result_dict)

            # Update job with result
            await self._repository.update_status(
                job_id=job.job_id,
                status=AIJobStatus.COMPLETED,
                result=result_dict_dynamodb,
                processing_time_ms=processing_time_ms,
            )

            # Publish completed event (v2.4 domain terminal or legacy)
            try:
                self._publish_async_job_completed_terminal(
                    job,
                    result_dict=result_dict,
                    processing_time_ms=processing_time_ms,
                )
            except EventBridgePublishError as e:
                logger.warning(
                    "async_job.completed_event_failed",
                    job_id=job.job_id,
                    request_id=job.request_id,
                    idempotency_key=job.idempotency_key,
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

        except PermissionError as e:
            auth_error_code = self._map_auth_failure_error_code(str(e))
            await self._handle_failure(
                job=job,
                error=str(e),
                error_code=auth_error_code,
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

        # Publish failed event (v2.4 domain terminal or legacy)
        try:
            self._publish_async_job_failed_terminal(
                job,
                error=error,
                error_code=error_code,
                _processing_time_ms=processing_time_ms,
            )
        except EventBridgePublishError as e:
            logger.warning(
                "async_job.failed_event_failed",
                job_id=job.job_id,
                request_id=job.request_id,
                idempotency_key=job.idempotency_key,
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

    @staticmethod
    def _map_auth_failure_error_code(error_message: str) -> AIJobErrorCode:
        """Map auth/enrichment failures to deterministic error codes."""
        normalized = error_message.lower()
        if "missing service token" in normalized:
            return AIJobErrorCode.AUTH_MISSING_SERVICE_TOKEN
        if "expired token" in normalized:
            return AIJobErrorCode.AUTH_SERVICE_TOKEN_EXPIRED
        if "invalid token" in normalized:
            return AIJobErrorCode.AUTH_SERVICE_TOKEN_INVALID
        if "insufficient scope" in normalized or "insufficient claims" in normalized:
            return AIJobErrorCode.AUTH_SERVICE_TOKEN_INSUFFICIENT_SCOPE
        if "authorization failed" in normalized or "forbidden" in normalized:
            return AIJobErrorCode.AUTH_ENRICHMENT_FORBIDDEN
        return AIJobErrorCode.INTERNAL_ERROR

    def _create_template_processor(
        self,
        jwt_token: str | None,
    ) -> TemplateParameterProcessor | None:
        """Create template processor for parameter enrichment.

        Args:
            jwt_token: JWT token for API authentication, or None to skip enrichment

        Returns:
            Template processor for enrichment, or None if no token available
        """
        if not jwt_token:
            logger.warning(
                "async_job.no_jwt_token",
                message="Cannot create template processor without JWT token, "
                "parameter enrichment will be skipped",
            )
            return None

        # Create API client with JWT token
        api_client = BusinessApiClient(
            base_url=settings.business_api_base_url,
            jwt_token=jwt_token,
        )

        # Create and return processor
        return TemplateParameterProcessor(business_api_client=api_client)

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
            "strategy_alignment_evaluation": 40000,
            "strategy_suggestions": 40000,
            "kpi_recommendations": 40000,
        }
        return estimates.get(topic_id, 30000)
