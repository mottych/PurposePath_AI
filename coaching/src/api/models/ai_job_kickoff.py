"""Pydantic models for PurposePath_Api EventBridge async job kickoff (issue #302)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from coaching.src.api.models.async_ai import AuthContext
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApiAiJobRequestedDetail(BaseModel):
    """EventBridge `detail` for `ai.job.requested` (email_insight kickoff).

    Canonical fields align with docs/shared/Specifications/ai-api/email-insights-api-contract.md §3.4.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    event_id: str = Field(alias="eventId")
    request_id: str = Field(alias="requestId", min_length=1)
    occurred_at_utc: datetime = Field(alias="occurredAtUtc")
    source_service: str = Field(alias="sourceService")
    schema_version: str = Field(alias="schemaVersion")
    correlation_id: str = Field(alias="correlationId")
    idempotency_key: str = Field(alias="idempotencyKey")
    retry_attempt: int = Field(alias="retryAttempt")
    tenant_id: str = Field(alias="tenantId")
    user_id: str = Field(alias="userId")
    topic_category: str = Field(alias="topicCategory")
    topic_id: str = Field(alias="topicId")
    event_signal: str = Field(alias="eventSignal")
    locale: str
    timezone: str
    activity_data: dict[str, Any] = Field(alias="activityData")
    auth_context: AuthContext = Field(alias="authContext")
    job_id: str = Field(alias="jobId", min_length=1)
    event_type: str = Field(alias="eventType", min_length=1)
    kickoff_transport: Literal["eventbridge"] = Field(alias="kickoffTransport")
    stage: str | None = Field(
        default=None,
        description="Optional environment gate; when set must match AI service stage",
    )
    causation_id: str | None = Field(default=None, alias="causationId")
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_email_insight_category(self) -> ApiAiJobRequestedDetail:
        if self.topic_category != "email_insight":
            raise ValueError("topicCategory must be 'email_insight' for this kickoff contract")
        return self
