"""API models for async AI execution endpoints.

This module provides request and response models for the async AI
execution endpoints (POST /ai/execute-async, GET /ai/jobs/{jobId}).
"""

from datetime import UTC, datetime
from typing import Any

from coaching.src.api.models.job_status_contract import api_contract_status_for_job_status
from coaching.src.domain.entities.ai_job import AIJob
from pydantic import BaseModel, ConfigDict, Field, model_validator


class AuthContext(BaseModel):
    """Authorization context for backend-triggered enrichment calls."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    service_token: str = Field(
        alias="serviceToken",
        min_length=1,
        description="Backend-issued short-lived bearer token for enrichment APIs",
    )
    expires_at_utc: datetime = Field(
        alias="expiresAtUtc",
        description="Token expiration timestamp in UTC",
    )
    issuer: str = Field(
        min_length=1,
        description="Token issuer identifier",
    )
    token_type: str = Field(
        alias="tokenType",
        min_length=1,
        description="Token type, expected value: service_enrichment",
    )

    @model_validator(mode="after")
    def validate_token_expiry(self) -> "AuthContext":
        """Require non-expired service tokens for enrichment calls."""
        expires_at = (
            self.expires_at_utc.replace(tzinfo=UTC)
            if self.expires_at_utc.tzinfo is None
            else self.expires_at_utc.astimezone(UTC)
        )
        if expires_at <= datetime.now(UTC):
            raise ValueError("authContext.serviceToken is expired")
        return self


class AsyncAIRequest(BaseModel):
    """Request model for async AI execution.

    Same structure as GenericAIRequest to maintain consistency.

    Attributes:
        topic_id: Topic identifier from endpoint registry
        parameters: Parameters to pass to the AI prompt template
    """

    topic_id: str = Field(
        ...,
        alias="topicId",
        min_length=1,
        max_length=100,
        description="Topic identifier from endpoint registry",
        examples=["niche_review", "ica_review", "value_proposition_review"],
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to pass to the AI prompt template",
        examples=[{"current_value": "We help small businesses grow"}],
    )

    # Generic v2 backend-triggered request envelope (optional for backwards compatibility)
    event_id: str | None = Field(default=None, alias="eventId")
    occurred_at_utc: datetime | None = Field(default=None, alias="occurredAtUtc")
    source_service: str | None = Field(default=None, alias="sourceService")
    schema_version: str | None = Field(default=None, alias="schemaVersion")
    correlation_id: str | None = Field(default=None, alias="correlationId")
    idempotency_key: str | None = Field(default=None, alias="idempotencyKey")
    retry_attempt: int | None = Field(default=None, alias="retryAttempt")
    tenant_id: str | None = Field(default=None, alias="tenantId")
    user_id: str | None = Field(default=None, alias="userId")
    topic_category: str | None = Field(default=None, alias="topicCategory")
    event_signal: str | None = Field(default=None, alias="eventSignal")
    locale: str | None = Field(default=None)
    timezone: str | None = Field(default=None)
    activity_data: dict[str, Any] | None = Field(default=None, alias="activityData")
    auth_context: AuthContext | None = Field(default=None, alias="authContext")
    causation_id: str | None = Field(default=None, alias="causationId")
    metadata: dict[str, Any] | None = Field(default=None)

    @property
    def is_backend_contract_v2(self) -> bool:
        """Whether this request uses the generic backend-triggered envelope."""
        return self.auth_context is not None or self.activity_data is not None

    @model_validator(mode="after")
    def validate_v2_contract_requirements(self) -> "AsyncAIRequest":
        """Enforce required fields only when v2 contract envelope is used."""
        if not self.is_backend_contract_v2:
            return self

        required_fields = {
            "eventId": self.event_id,
            "occurredAtUtc": self.occurred_at_utc,
            "sourceService": self.source_service,
            "schemaVersion": self.schema_version,
            "correlationId": self.correlation_id,
            "idempotencyKey": self.idempotency_key,
            "retryAttempt": self.retry_attempt,
            "tenantId": self.tenant_id,
            "userId": self.user_id,
            "topicCategory": self.topic_category,
            "topicId": self.topic_id,
            "eventSignal": self.event_signal,
            "locale": self.locale,
            "timezone": self.timezone,
            "activityData": self.activity_data,
            "authContext": self.auth_context,
        }
        missing = [field_name for field_name, value in required_fields.items() if value is None]
        if missing:
            raise ValueError(f"Missing required v2 contract fields: {missing}")
        if self.topic_category != "email_insight":
            raise ValueError("topicCategory must be 'email_insight' for v2 backend contract")
        if self.auth_context and self.auth_context.token_type != "service_enrichment":
            raise ValueError("authContext.tokenType must be 'service_enrichment'")
        return self

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "topic_id": "niche_review",
                    "parameters": {"current_value": "We help small businesses grow"},
                },
                {
                    "eventId": "evt-123",
                    "occurredAtUtc": "2026-03-27T16:00:00Z",
                    "sourceService": "PurposePath_Api",
                    "schemaVersion": "2.0",
                    "correlationId": "corr-123",
                    "idempotencyKey": "idem-123",
                    "retryAttempt": 0,
                    "tenantId": "tenant_456",
                    "userId": "user_123",
                    "topicCategory": "email_insight",
                    "topicId": "goal_created_email_insight",
                    "eventSignal": "goal_created",
                    "locale": "en-US",
                    "timezone": "UTC",
                    "activityData": {"goal_id": "goal_1"},
                    "authContext": {
                        "serviceToken": "token-value",
                        "expiresAtUtc": "2026-03-27T16:15:00Z",
                        "issuer": "PurposePath_Api",
                        "tokenType": "service_enrichment",
                    },
                },
            ]
        },
    )


class AsyncJobCreatedResponse(BaseModel):
    """Response model for async job creation.

    Returned immediately when a job is created, before execution completes.

    Attributes:
        success: Always True for successful creation
        data: Job details
    """

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    success: bool = Field(default=True, description="Whether job creation succeeded")
    data: "AsyncJobData" = Field(..., description="Created job details")


class AsyncJobData(BaseModel):
    """Data for a created async job.

    Attributes:
        job_id: Unique job identifier for tracking
        status: Current job status (pending on creation)
        topic_id: AI topic being executed
        estimated_duration_ms: Estimated processing time
    """

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    job_id: str = Field(
        ...,
        alias="jobId",
        serialization_alias="jobId",
        description="Unique job identifier for tracking",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: str = Field(
        ...,
        description="Current job status",
        examples=["queued"],
    )
    topic_id: str = Field(
        ...,
        alias="topicId",
        serialization_alias="topicId",
        description="AI topic being executed",
        examples=["niche_review"],
    )
    estimated_duration_ms: int = Field(
        ...,
        alias="estimatedDurationMs",
        serialization_alias="estimatedDurationMs",
        description="Estimated processing time in milliseconds",
        examples=[30000],
    )


class JobStatusResponse(BaseModel):
    """Response model for job status query.

    Used by GET /ai/jobs/{jobId} for polling fallback.

    Attributes:
        success: Always True for successful query
        data: Job status details
    """

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    success: bool = Field(default=True, description="Whether query succeeded")
    data: "JobStatusData" = Field(..., description="Job status details")


class JobStatusData(BaseModel):
    """Data for job status query.

    Includes full job details including result/error for terminal states.

    Attributes:
        job_id: Unique job identifier
        status: Current job status
        topic_id: AI topic being executed
        created_at: Job creation timestamp
        completed_at: Completion timestamp (if terminal)
        result: AI execution result (if completed)
        error: Error message (if failed)
        error_code: Error categorization (if failed)
        processing_time_ms: Actual processing time (if terminal)
        estimated_duration_ms: Estimated processing time
    """

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    job_id: str = Field(
        ...,
        alias="jobId",
        serialization_alias="jobId",
        description="Unique job identifier",
    )
    status: str = Field(..., description="Current job status")
    topic_id: str = Field(
        ...,
        alias="topicId",
        serialization_alias="topicId",
        description="AI topic being executed",
    )
    created_at: datetime = Field(
        ...,
        alias="createdAt",
        serialization_alias="createdAt",
        description="Job creation timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        alias="completedAt",
        serialization_alias="completedAt",
        description="Completion timestamp",
    )
    result: dict[str, Any] | None = Field(None, description="AI result (if completed)")
    error: str | None = Field(None, description="Error message (if failed)")
    error_code: str | None = Field(
        default=None,
        alias="errorCode",
        serialization_alias="errorCode",
        description="Error code (if failed)",
    )
    processing_time_ms: int | None = Field(
        default=None,
        alias="processingTimeMs",
        serialization_alias="processingTimeMs",
        description="Actual processing time",
    )
    estimated_duration_ms: int = Field(
        default=30000,
        alias="estimatedDurationMs",
        serialization_alias="estimatedDurationMs",
        description="Estimated processing time",
    )

    @classmethod
    def from_job(cls, job: AIJob) -> "JobStatusData":
        """Create JobStatusData from AIJob domain model.

        Args:
            job: AIJob domain model

        Returns:
            JobStatusData for API response
        """
        return cls.model_validate(
            {
                "jobId": job.job_id,
                "status": api_contract_status_for_job_status(job.status),
                "topicId": job.topic_id,
                "createdAt": job.created_at,
                "completedAt": job.completed_at,
                "result": job.result,
                "error": job.error,
                "errorCode": job.error_code.value if job.error_code else None,
                "processingTimeMs": job.processing_time_ms,
                "estimatedDurationMs": job.estimated_duration_ms,
            }
        )


# Update forward references
AsyncJobCreatedResponse.model_rebuild()
JobStatusResponse.model_rebuild()
