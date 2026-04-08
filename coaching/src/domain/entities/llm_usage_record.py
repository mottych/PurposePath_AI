"""Per-invocation LLM usage record for observability and quota-oriented reads."""

from datetime import datetime

from pydantic import BaseModel, Field


class LlmUsageRecord(BaseModel):
    """One row per LLM provider call (or failed attempt before a response).

    topic_category and topic_type are copied from topic metadata at write time as plain
    strings—no closed enum in persistence.
    """

    usage_id: str = Field(..., description="Unique id for this row")
    occurred_at: datetime = Field(..., description="When the LLM call finished (UTC)")
    billing_period: str = Field(..., description="YYYY-MM for partition-friendly queries")
    tenant_id: str = Field(..., description="Tenant id")
    user_id: str | None = Field(default=None, description="User id when available")
    topic_id: str = Field(..., description="Topic id")
    topic_category: str = Field(..., description="Category string from topic at emit time")
    topic_type: str = Field(..., description="Topic type string from topic at emit time")
    model_code: str = Field(..., description="Registry / tier model code")
    model_name: str = Field(..., description="Provider-resolved model id")
    input_tokens: int = Field(0, ge=0)
    output_tokens: int = Field(0, ge=0)
    total_tokens: int = Field(0, ge=0)
    max_tokens_topic_config: int = Field(..., ge=0)
    max_tokens_effective: int = Field(..., ge=0)
    wall_time_ms: int = Field(..., ge=0, description="LLM call wall time")
    estimated_duration_ms: int | None = Field(
        default=None,
        description="Expected duration when known (e.g. async job estimate)",
    )
    finish_reason: str = Field(default="", description="Provider finish_reason when available")
    cost_usd: float | None = Field(
        default=None,
        description="Estimated USD from coaching.src.infrastructure.llm.model_pricing",
    )
    job_id: str | None = None
    correlation_id: str | None = None
    session_id: str | None = Field(default=None, description="Coaching session id when applicable")
    conversation_id: str | None = None
    entry_source: str = Field(
        ...,
        description="Which product path invoked the LLM (string, not a persisted enum)",
    )
    success: bool = Field(..., description="End-to-end success for this invocation path")
    error_kind: str | None = Field(
        default=None,
        description="provider_error | serialization | timeout | unknown",
    )

    model_config = {"frozen": True, "extra": "forbid"}
