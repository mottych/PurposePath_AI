"""Admin API: persisted LLM usage (per-call metrics for ops and quota-style reads)."""

from datetime import UTC, datetime

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies.ai_engine import get_llm_usage_repository
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.application.llm_usage.llm_usage_summary import (
    LlmUsageSummary,
    summarize_usage_rows,
)
from coaching.src.domain.entities.llm_usage_record import LlmUsageRecord
from coaching.src.infrastructure.repositories.dynamodb_llm_usage_repository import (
    DynamoDBLlmUsageRepository,
)
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


class LlmUsageRecordResponse(BaseModel):
    """Single usage row returned to admin clients."""

    usage_id: str
    occurred_at: str
    billing_period: str
    tenant_id: str
    user_id: str | None = None
    topic_id: str
    topic_category: str
    topic_type: str
    model_code: str
    model_name: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    max_tokens_topic_config: int
    max_tokens_effective: int
    wall_time_ms: int
    estimated_duration_ms: int | None = None
    finish_reason: str
    cost_usd: float | None = None
    job_id: str | None = None
    correlation_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    entry_source: str
    success: bool
    error_kind: str | None = None


class LlmUsageQueryResponse(BaseModel):
    """Usage rows plus optional roll-up (on-the-fly aggregation over returned rows)."""

    records: list[LlmUsageRecordResponse]
    summary: LlmUsageSummary | None = None


def _months_in_range(start: datetime, end: datetime) -> list[str]:
    months: list[str] = []
    y, m = start.year, start.month
    end_y, end_m = end.year, end.month
    while (y, m) <= (end_y, end_m):
        months.append(f"{y:04d}-{m:02d}")
        if m == 12:
            m = 1
            y += 1
        else:
            m += 1
    return months


def _record_to_response(r: LlmUsageRecord) -> LlmUsageRecordResponse:
    return LlmUsageRecordResponse(
        usage_id=r.usage_id,
        occurred_at=r.occurred_at.astimezone(UTC).isoformat(),
        billing_period=r.billing_period,
        tenant_id=r.tenant_id,
        user_id=r.user_id,
        topic_id=r.topic_id,
        topic_category=r.topic_category,
        topic_type=r.topic_type,
        model_code=r.model_code,
        model_name=r.model_name,
        input_tokens=r.input_tokens,
        output_tokens=r.output_tokens,
        total_tokens=r.total_tokens,
        max_tokens_topic_config=r.max_tokens_topic_config,
        max_tokens_effective=r.max_tokens_effective,
        wall_time_ms=r.wall_time_ms,
        estimated_duration_ms=r.estimated_duration_ms,
        finish_reason=r.finish_reason,
        cost_usd=r.cost_usd,
        job_id=r.job_id,
        correlation_id=r.correlation_id,
        session_id=r.session_id,
        conversation_id=r.conversation_id,
        entry_source=r.entry_source,
        success=r.success,
        error_kind=r.error_kind,
    )


@router.get("/llm-usage", response_model=ApiResponse[LlmUsageQueryResponse])
async def query_llm_usage(
    billing_period: str | None = Query(
        None,
        description="YYYY-MM (preferred; single Dynamo GSI query per month)",
    ),
    time_from: datetime | None = Query(None, description="UTC inclusive lower bound (ISO 8601)"),
    time_to: datetime | None = Query(None, description="UTC inclusive upper bound (ISO 8601)"),
    tenant_id: str | None = Query(None, description="Filter to one tenant"),
    topic_id: str | None = None,
    topic_category: str | None = None,
    topic_type: str | None = None,
    model: str | None = Query(None, description="Substring match on resolved model_name"),
    limit: int = Query(500, ge=1, le=2000),
    include_summary: bool = Query(True, description="Include on-the-fly aggregates over returned rows"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    repo: DynamoDBLlmUsageRepository = Depends(get_llm_usage_repository),
) -> ApiResponse[LlmUsageQueryResponse]:
    """
    List persisted LLM usage rows (ops / analytics / quota-style roll-ups).

    **Quota-oriented reads:** Prefer `billing_period` for efficient queries (one GSI partition per month).
    Monthly token totals can be obtained by setting `include_summary=true` over the full month partition
    (optionally filtered by `tenant_id`). For ranges spanning multiple months, `time_from` + `time_to`
    are expanded to consecutive `YYYY-MM` values and queried sequentially.

    **Cost:** Derived from `coaching/src/infrastructure/llm/model_pricing.py` (AWS Bedrock list prices);
    unknown models contribute `0` until added to `MODEL_PRICING`.
    """
    _ = context
    if billing_period:
        periods = [billing_period]
    elif time_from is not None and time_to is not None:
        tf = time_from.astimezone(UTC) if time_from.tzinfo else time_from.replace(tzinfo=UTC)
        tt = time_to.astimezone(UTC) if time_to.tzinfo else time_to.replace(tzinfo=UTC)
        periods = _months_in_range(tf, tt)
    else:
        now = datetime.now(UTC)
        periods = [f"{now.year:04d}-{now.month:02d}"]

    per_period_cap = max(limit // max(len(periods), 1), 1)
    rows: list[LlmUsageRecord] = []
    for bp in periods:
        batch = await repo.query_billing_period(
            billing_period=bp,
            tenant_id_prefix=tenant_id,
            topic_id=topic_id,
            model_substring=model,
            topic_category=topic_category,
            topic_type=topic_type,
            time_from=time_from,
            time_to=time_to,
            limit=per_period_cap,
        )
        rows.extend(batch)
        if len(rows) >= limit:
            rows = rows[:limit]
            break

    summary = summarize_usage_rows(rows) if include_summary else None
    payload = LlmUsageQueryResponse(
        records=[_record_to_response(r) for r in rows],
        summary=summary,
    )
    return ApiResponse(success=True, data=payload)
