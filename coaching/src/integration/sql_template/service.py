"""Application service for SQL template generation events."""

from __future__ import annotations

import asyncio
import random
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

import structlog
from coaching.src.integration.sql_template.cdata_mcp_client import SchemaDiscoveryClient
from coaching.src.integration.sql_template.enums import ErrorCode, ErrorStage, GenerationStatus
from coaching.src.integration.sql_template.errors import SqlTemplateGenerationError, ValidationError
from coaching.src.integration.sql_template.idempotency import GenerationIdempotencyStore
from coaching.src.integration.sql_template.models import (
    CompletedDetail,
    CompletedEvent,
    FailedDetail,
    FailedEvent,
    GenerationMetadata,
    GenerationRecord,
    RequestedEvent,
    SqlGenerationResult,
    ValidationResult,
)
from coaching.src.integration.sql_template.publisher import IntegrationEventPublisher
from coaching.src.integration.sql_template.sql_generator import SqlTemplateGenerator
from coaching.src.integration.sql_template.sql_validator import SqlTemplateValidator

logger = structlog.get_logger()


class GenerationMetricsCollector(Protocol):
    """Metrics sink for SQL template generation pipeline."""

    def increment_requests(self) -> None:
        """Record request intake."""

    def increment_success(self) -> None:
        """Record successful terminal generation."""

    def increment_failure(self, error_code: str) -> None:
        """Record failed terminal generation by error code."""

    def observe_latency_ms(self, duration_ms: int) -> None:
        """Record total generation latency."""

    def increment_retry(self) -> None:
        """Record retry attempt count."""

    def increment_validation_failure(self, code: str) -> None:
        """Record validation failure code frequency."""


class NoOpGenerationMetricsCollector:
    """Default metrics collector when no backend is wired."""

    def increment_requests(self) -> None:
        return None

    def increment_success(self) -> None:
        return None

    def increment_failure(self, error_code: str) -> None:
        _ = error_code
        return None

    def observe_latency_ms(self, duration_ms: int) -> None:
        _ = duration_ms
        return None

    def increment_retry(self) -> None:
        return None

    def increment_validation_failure(self, code: str) -> None:
        _ = code
        return None


class SqlTemplateGenerationService:
    """End-to-end processing for integration SQL template generation requests."""

    def __init__(
        self,
        idempotency_store: GenerationIdempotencyStore,
        discovery_client: SchemaDiscoveryClient,
        generator: SqlTemplateGenerator,
        validator: SqlTemplateValidator,
        publisher: IntegrationEventPublisher,
        metrics: GenerationMetricsCollector | None = None,
        max_attempts: int = 3,
        base_retry_delay_seconds: float = 0.2,
    ) -> None:
        self._idempotency_store = idempotency_store
        self._discovery_client = discovery_client
        self._generator = generator
        self._validator = validator
        self._publisher = publisher
        self._metrics = metrics or NoOpGenerationMetricsCollector()
        self._max_attempts = max_attempts
        self._base_retry_delay_seconds = base_retry_delay_seconds

    async def process_event(self, raw_event: dict[str, object]) -> dict[str, str]:
        request = RequestedEvent.model_validate(raw_event)
        generation_id = str(request.detail.generation_id)
        start_time = datetime.now(UTC)
        event_logger = logger.bind(
            correlation_id=str(request.detail.correlation_id),
            generation_id=generation_id,
            tenant_id=str(request.detail.tenant_id),
            measure_integration_id=str(request.detail.measure_integration_id),
        )
        self._metrics.increment_requests()

        event_logger.info(
            "integration_sql.request_received",
        )

        existing = await self._idempotency_store.get(generation_id)
        if existing and existing.terminal_payload and existing.published:
            event_logger.info(
                "integration_sql.duplicate_already_published",
                status=existing.status,
            )
            return {"status": "duplicate_published"}

        if existing and existing.terminal_payload and not existing.published:
            await self._publish_terminal_from_record(existing)
            await self._idempotency_store.mark_published(generation_id)
            return {"status": "republished_terminal"}

        reserved = await self._idempotency_store.reserve_processing(generation_id)
        if not reserved:
            event_logger.info("integration_sql.duplicate_processing")
            return {"status": "duplicate_in_progress"}

        try:
            result = await self._generate_with_retries(request)
            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            completed = self._build_completed_event(request, result, duration_ms)
            payload = completed.model_dump(mode="json", by_alias=True)
            await self._idempotency_store.save_terminal(
                generation_id=generation_id,
                status="success",
                detail_type=completed.detail_type,
                payload=payload,
            )
            self._publisher.publish_modeled_event(
                event_model=completed.detail,
                detail_type=completed.detail_type,
                source=completed.source,
            )
            await self._idempotency_store.mark_published(generation_id)
            self._metrics.increment_success()
            self._metrics.observe_latency_ms(duration_ms)
            return {"status": "completed"}
        except SqlTemplateGenerationError as exc:
            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            failed = self._build_failed_event(request, exc, duration_ms)
            payload = failed.model_dump(mode="json", by_alias=True)
            await self._idempotency_store.save_terminal(
                generation_id=generation_id,
                status="failed",
                detail_type=failed.detail_type,
                payload=payload,
            )
            self._publisher.publish_modeled_event(
                event_model=failed.detail,
                detail_type=failed.detail_type,
                source=failed.source,
            )
            await self._idempotency_store.mark_published(generation_id)
            self._metrics.increment_failure(exc.code.value)
            self._metrics.observe_latency_ms(duration_ms)
            for failure in exc.validation_failures or []:
                self._metrics.increment_validation_failure(failure.code.value)
            return {"status": "failed", "error_code": exc.code.value}
        except Exception as exc:
            duration_ms = int((datetime.now(UTC) - start_time).total_seconds() * 1000)
            wrapped = SqlTemplateGenerationError(
                code=ErrorCode.INTERNAL_UNHANDLED,
                stage=ErrorStage.PUBLISH,
                message=f"Unhandled SQL generation error: {exc}",
                retryable=False,
            )
            failed = self._build_failed_event(request, wrapped, duration_ms)
            payload = failed.model_dump(mode="json", by_alias=True)
            await self._idempotency_store.save_terminal(
                generation_id=generation_id,
                status=GenerationStatus.FAILED.value,
                detail_type=failed.detail_type,
                payload=payload,
            )
            self._publisher.publish_modeled_event(
                event_model=failed.detail,
                detail_type=failed.detail_type,
                source=failed.source,
            )
            await self._idempotency_store.mark_published(generation_id)
            self._metrics.increment_failure(wrapped.code.value)
            self._metrics.observe_latency_ms(duration_ms)
            return {"status": "failed", "error_code": wrapped.code.value}

    async def _generate_with_retries(self, request: RequestedEvent) -> SqlGenerationResult:
        last_error: SqlTemplateGenerationError | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                discovered = await self._discovery_client.discover_columns(request.detail)
                generated = self._generator.generate(request.detail, discovered)
                self._validator.validate(request.detail, generated)
                await self._discovery_client.dry_run(request.detail, generated.sql_template)
                generated.validation_attempt_count = attempt
                return generated
            except ValidationError as exc:
                raise exc
            except SqlTemplateGenerationError as exc:
                exc.attempt_count = attempt
                last_error = exc
                if not exc.retryable or attempt >= self._max_attempts:
                    raise exc
                self._metrics.increment_retry()
                await self._sleep_with_jitter(attempt)
            except Exception as exc:
                wrapped = SqlTemplateGenerationError(
                    code=ErrorCode.MCP_TOOL_ERROR,
                    stage=ErrorStage.GENERATE,
                    message=f"Unexpected generation failure: {exc}",
                    retryable=attempt < self._max_attempts,
                    attempt_count=attempt,
                )
                last_error = wrapped
                if attempt >= self._max_attempts:
                    raise wrapped from exc
                self._metrics.increment_retry()
                await self._sleep_with_jitter(attempt)

        assert last_error is not None
        raise last_error

    async def _sleep_with_jitter(self, attempt: int) -> None:
        backoff = self._base_retry_delay_seconds * (2 ** (attempt - 1))
        jitter = random.uniform(0, backoff / 2)
        await asyncio.sleep(backoff + jitter)

    def _build_completed_event(
        self,
        request: RequestedEvent,
        generation: SqlGenerationResult,
        duration_ms: int,
    ) -> CompletedEvent:
        return CompletedEvent(
            id=uuid4(),
            time=datetime.now(UTC),
            account=request.account,
            region=request.region,
            resources=request.resources,
            detail=CompletedDetail(
                eventVersion=request.detail.event_version,
                provider=request.detail.provider,
                correlationId=request.detail.correlation_id,
                generationId=request.detail.generation_id,
                tenantId=request.detail.tenant_id,
                measureIntegrationId=request.detail.measure_integration_id,
                idempotencyKey=request.detail.idempotency_key,
                catalogMeasureId=request.detail.catalog_measure_id,
                measureId=request.detail.measure_id,
                definition=request.detail.definition,
                system=request.detail.system,
                status=GenerationStatus.SUCCESS.value,
                sqlTemplate=generation.sql_template,
                sqlTemplateHash=generation.sql_template_hash,
                parameterBindingsSchema=generation.parameter_bindings_schema,
                appliedParameters=generation.applied_parameters,
                ignoredParameters=generation.ignored_parameters,
                validated=True,
                validation=ValidationResult(
                    method=generation.validation_method,
                    attemptCount=generation.validation_attempt_count,
                ),
                generationMetadata=GenerationMetadata(
                    durationMs=duration_ms,
                    toolCalls=generation.tool_calls,
                ),
            ),
        )

    def _build_failed_event(
        self,
        request: RequestedEvent,
        error: SqlTemplateGenerationError,
        duration_ms: int,
    ) -> FailedEvent:
        return FailedEvent(
            id=uuid4(),
            time=datetime.now(UTC),
            account=request.account,
            region=request.region,
            resources=request.resources,
            detail=FailedDetail(
                eventVersion=request.detail.event_version,
                provider=request.detail.provider,
                correlationId=request.detail.correlation_id,
                generationId=request.detail.generation_id,
                tenantId=request.detail.tenant_id,
                measureIntegrationId=request.detail.measure_integration_id,
                idempotencyKey=request.detail.idempotency_key,
                catalogMeasureId=request.detail.catalog_measure_id,
                measureId=request.detail.measure_id,
                definition=request.detail.definition,
                system=request.detail.system,
                status=GenerationStatus.FAILED.value,
                errorCode=error.code,
                errorStage=error.stage,
                retryable=error.retryable,
                retryAfterSeconds=1 if error.retryable else None,
                message=error.message,
                durationMs=duration_ms,
                attemptCount=error.attempt_count,
                cdataErrorCode=error.cdata_error_code,
                validationFailures=error.validation_failures or [],
            ),
        )

    async def _publish_terminal_from_record(self, record: GenerationRecord) -> None:
        """Re-publish previously persisted terminal payload."""
        if not record.terminal_payload or not record.terminal_detail_type:
            return

        payload = record.terminal_payload
        detail_type = record.terminal_detail_type
        source = "purposepath.integration.ai"
        detail = payload.get("detail")
        if not isinstance(detail, dict):
            return
        self._publisher.publish_modeled_event(
            event_model=CompletedDetail.model_validate(detail)
            if detail_type.endswith(".completed")
            else FailedDetail.model_validate(detail),
            detail_type=detail_type,
            source=source,
        )
