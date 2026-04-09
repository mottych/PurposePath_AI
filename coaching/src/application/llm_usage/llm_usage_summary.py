"""Aggregate metrics from usage rows (on-the-fly quota-oriented sums)."""

from coaching.src.domain.entities.llm_usage_record import LlmUsageRecord
from pydantic import BaseModel, Field


class LlmUsageSummary(BaseModel):
    """Roll-up over a set of usage rows (same source as Dynamo detail store)."""

    row_count: int = Field(0, ge=0)
    total_input_tokens: int = Field(0, ge=0)
    total_output_tokens: int = Field(0, ge=0)
    total_tokens: int = Field(0, ge=0)
    total_cost_usd: float = Field(0.0, ge=0.0)
    success_count: int = Field(0, ge=0)
    failure_count: int = Field(0, ge=0)
    truncation_count: int = Field(0, ge=0, description="finish_reason == length")
    avg_wall_time_ms: float = Field(0.0, ge=0.0)


def summarize_usage_rows(rows: list[LlmUsageRecord]) -> LlmUsageSummary:
    """Compute aggregates for admin / quota previews."""
    n = len(rows)
    total_in = sum(r.input_tokens for r in rows)
    total_out = sum(r.output_tokens for r in rows)
    total_tok = sum(r.total_tokens for r in rows)
    total_cost = sum((r.cost_usd or 0.0) for r in rows)
    success = sum(1 for r in rows if r.success)
    failure = n - success
    trunc = sum(1 for r in rows if r.finish_reason == "length")
    wall_sum = sum(r.wall_time_ms for r in rows)
    avg_wall = wall_sum / n if n else 0.0

    return LlmUsageSummary(
        row_count=n,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        total_tokens=total_tok,
        total_cost_usd=round(total_cost, 6),
        success_count=success,
        failure_count=failure,
        truncation_count=trunc,
        avg_wall_time_ms=round(avg_wall, 3),
    )
