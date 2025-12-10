"""API models for async AI execution endpoints.

This module provides request and response models for the async AI
execution endpoints (POST /ai/execute-async, GET /ai/jobs/{jobId}).
"""

from datetime import datetime
from typing import Any

from coaching.src.domain.entities.ai_job import AIJob
from pydantic import BaseModel, Field


class AsyncAIRequest(BaseModel):
    """Request model for async AI execution.

    Same structure as GenericAIRequest to maintain consistency.

    Attributes:
        topic_id: Topic identifier from endpoint registry
        parameters: Parameters to pass to the AI prompt template
    """

    topic_id: str = Field(
        ...,
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

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "topic_id": "niche_review",
                    "parameters": {"current_value": "We help small businesses grow"},
                },
            ]
        }
    }


class AsyncJobCreatedResponse(BaseModel):
    """Response model for async job creation.

    Returned immediately when a job is created, before execution completes.

    Attributes:
        success: Always True for successful creation
        data: Job details
    """

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

    job_id: str = Field(
        ...,
        description="Unique job identifier for tracking",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    status: str = Field(
        ...,
        description="Current job status",
        examples=["pending"],
    )
    topic_id: str = Field(
        ...,
        description="AI topic being executed",
        examples=["niche_review"],
    )
    estimated_duration_ms: int = Field(
        ...,
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

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Current job status")
    topic_id: str = Field(..., description="AI topic being executed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: datetime | None = Field(None, description="Completion timestamp")
    result: dict[str, Any] | None = Field(None, description="AI result (if completed)")
    error: str | None = Field(None, description="Error message (if failed)")
    error_code: str | None = Field(None, description="Error code (if failed)")
    processing_time_ms: int | None = Field(None, description="Actual processing time")
    estimated_duration_ms: int = Field(30000, description="Estimated processing time")

    @classmethod
    def from_job(cls, job: AIJob) -> "JobStatusData":
        """Create JobStatusData from AIJob domain model.

        Args:
            job: AIJob domain model

        Returns:
            JobStatusData for API response
        """
        return cls(
            job_id=job.job_id,
            status=job.status.value,
            topic_id=job.topic_id,
            created_at=job.created_at,
            completed_at=job.completed_at,
            result=job.result,
            error=job.error,
            error_code=job.error_code.value if job.error_code else None,
            processing_time_ms=job.processing_time_ms,
            estimated_duration_ms=job.estimated_duration_ms,
        )


# Update forward references
AsyncJobCreatedResponse.model_rebuild()
JobStatusResponse.model_rebuild()
