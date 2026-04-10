"""Build and persist LlmUsageRecord rows from engine/session outcomes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog

from coaching.src.application.llm_usage.llm_invocation_context import LlmInvocationContext
from coaching.src.application.llm_usage.token_usage import normalize_token_counts
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.entities.llm_usage_record import LlmUsageRecord
from coaching.src.domain.ports.llm_provider_port import LLMResponse
from coaching.src.domain.ports.llm_usage_repository_port import LlmUsageRepositoryPort
from coaching.src.infrastructure.llm.model_pricing import calculate_cost

logger = structlog.get_logger()


def _billing_period(dt: datetime) -> str:
    aware = dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)
    return f"{aware.year:04d}-{aware.month:02d}"


class LlmUsageRecordingService:
    """Application service: usage rows for observability (never raises to callers)."""

    def __init__(self, repository: LlmUsageRepositoryPort) -> None:
        self._repository = repository

    async def record(
        self,
        *,
        topic: LLMTopic,
        tenant_id: str | None,
        user_id: str | None,
        model_code: str,
        max_tokens_topic_config: int,
        max_tokens_effective: int,
        wall_time_ms: int,
        llm_response: LLMResponse | None,
        invocation: LlmInvocationContext,
        pipeline_success: bool,
        error_kind: str | None = None,
    ) -> None:
        occurred_at = datetime.now(UTC)
        inp, out, total = (0, 0, 0)
        finish_reason = ""
        model_name = ""
        cost: float | None = None

        if llm_response is not None:
            inp, out, total = normalize_token_counts(llm_response.usage)
            finish_reason = llm_response.finish_reason or ""
            model_name = llm_response.model or ""
            cost = calculate_cost(inp, out, model_name)

        tenant = tenant_id or ""
        if not tenant:
            logger.warning("llm_usage.skip_no_tenant", topic_id=topic.topic_id)
            return

        record = LlmUsageRecord(
            usage_id=str(uuid.uuid4()),
            occurred_at=occurred_at,
            billing_period=_billing_period(occurred_at),
            tenant_id=tenant,
            user_id=user_id,
            topic_id=topic.topic_id,
            topic_category=str(topic.category),
            topic_type=str(topic.topic_type),
            model_code=model_code,
            model_name=model_name or model_code,
            input_tokens=inp,
            output_tokens=out,
            total_tokens=total,
            max_tokens_topic_config=max_tokens_topic_config,
            max_tokens_effective=max_tokens_effective,
            wall_time_ms=wall_time_ms,
            estimated_duration_ms=invocation.estimated_duration_ms,
            finish_reason=finish_reason,
            cost_usd=cost,
            job_id=invocation.job_id,
            correlation_id=invocation.correlation_id,
            session_id=invocation.session_id,
            conversation_id=invocation.conversation_id,
            entry_source=invocation.entry_source,
            success=pipeline_success,
            error_kind=error_kind,
        )

        try:
            await self._repository.append(record)
        except Exception as e:
            logger.error(
                "llm_usage.append_failed",
                topic_id=topic.topic_id,
                tenant_id=tenant,
                error=str(e),
            )
