"""AI Job domain models for async execution.

This module provides domain models for tracking asynchronous AI job
execution, including job status, results, and error handling.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AIJobStatus(str, Enum):
    """Status of an AI job.

    States:
        PENDING: Job accepted, queued for processing
        PROCESSING: Job is actively being processed
        COMPLETED: Job finished successfully
        FAILED: Job failed with error
    """

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AIJobErrorCode(str, Enum):
    """Error codes for AI job failures.

    Provides categorization for different failure types to enable
    appropriate client-side handling and retry logic.
    """

    TOPIC_NOT_FOUND = "TOPIC_NOT_FOUND"
    PARAMETER_VALIDATION = "PARAMETER_VALIDATION"
    PROMPT_RENDER_ERROR = "PROMPT_RENDER_ERROR"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_ERROR = "LLM_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AIJob(BaseModel):
    """Domain model for an async AI job.

    Represents a single async AI execution request with its current
    status, parameters, and results.

    Attributes:
        job_id: Unique job identifier
        tenant_id: Tenant that owns this job
        user_id: User who initiated the job
        topic_id: AI topic being executed
        parameters: Input parameters for the AI topic
        status: Current job status
        result: AI execution result (when completed)
        error: Error message (when failed)
        error_code: Error categorization (when failed)
        created_at: Job creation timestamp
        started_at: Processing start timestamp
        completed_at: Completion timestamp
        estimated_duration_ms: Estimated processing time
        processing_time_ms: Actual processing time
        ttl: Time-to-live for auto-cleanup (Unix timestamp)
    """

    job_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique job identifier",
    )
    tenant_id: str = Field(
        ...,
        description="Tenant that owns this job",
    )
    user_id: str = Field(
        ...,
        description="User who initiated the job",
    )
    topic_id: str = Field(
        ...,
        description="AI topic being executed",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Input parameters for the AI topic",
    )
    status: AIJobStatus = Field(
        default=AIJobStatus.PENDING,
        description="Current job status",
    )
    result: dict[str, Any] | None = Field(
        default=None,
        description="AI execution result (when completed)",
    )
    error: str | None = Field(
        default=None,
        description="Error message (when failed)",
    )
    error_code: AIJobErrorCode | None = Field(
        default=None,
        description="Error categorization (when failed)",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Job creation timestamp",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Processing start timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp",
    )
    estimated_duration_ms: int = Field(
        default=30000,
        description="Estimated processing time in milliseconds",
    )
    processing_time_ms: int | None = Field(
        default=None,
        description="Actual processing time in milliseconds",
    )
    ttl: int | None = Field(
        default=None,
        description="Time-to-live for auto-cleanup (Unix timestamp)",
    )

    def mark_processing(self) -> None:
        """Mark job as processing."""
        self.status = AIJobStatus.PROCESSING
        self.started_at = datetime.now(UTC)

    def mark_completed(
        self,
        result: dict[str, Any],
        processing_time_ms: int,
    ) -> None:
        """Mark job as completed with result.

        Args:
            result: The AI execution result
            processing_time_ms: Time taken to process
        """
        self.status = AIJobStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(UTC)
        self.processing_time_ms = processing_time_ms

    def mark_failed(
        self,
        error: str,
        error_code: AIJobErrorCode,
    ) -> None:
        """Mark job as failed with error.

        Args:
            error: Error message
            error_code: Error categorization
        """
        self.status = AIJobStatus.FAILED
        self.error = error
        self.error_code = error_code
        self.completed_at = datetime.now(UTC)

    def is_terminal(self) -> bool:
        """Check if job is in a terminal state.

        Returns:
            True if job is completed or failed
        """
        return self.status in (AIJobStatus.COMPLETED, AIJobStatus.FAILED)

    def set_ttl(self, hours: int = 24) -> None:
        """Set TTL for auto-cleanup.

        Args:
            hours: Number of hours until expiration (default: 24)
        """
        expiration = datetime.now(UTC).timestamp() + (hours * 3600)
        self.ttl = int(expiration)


class AIJobCreate(BaseModel):
    """Request model for creating an AI job.

    Attributes:
        tenant_id: Tenant identifier
        user_id: User identifier
        topic_id: AI topic to execute
        parameters: Input parameters
    """

    tenant_id: str
    user_id: str
    topic_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class AIJobResponse(BaseModel):
    """Response model for AI job status.

    Attributes:
        job_id: Unique job identifier
        status: Current job status
        topic_id: AI topic being executed
        created_at: Job creation timestamp
        completed_at: Completion timestamp (if terminal)
        result: AI result (if completed)
        error: Error message (if failed)
        error_code: Error code (if failed)
        processing_time_ms: Actual processing time (if terminal)
        estimated_duration_ms: Estimated processing time
    """

    job_id: str
    status: AIJobStatus
    topic_id: str
    created_at: datetime
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    error_code: str | None = None
    processing_time_ms: int | None = None
    estimated_duration_ms: int = 30000

    @classmethod
    def from_job(cls, job: AIJob) -> AIJobResponse:
        """Create response from AIJob domain model.

        Args:
            job: The AIJob domain model

        Returns:
            AIJobResponse for API response
        """
        return cls(
            job_id=job.job_id,
            status=job.status,
            topic_id=job.topic_id,
            created_at=job.created_at,
            completed_at=job.completed_at,
            result=job.result,
            error=job.error,
            error_code=job.error_code.value if job.error_code else None,
            processing_time_ms=job.processing_time_ms,
            estimated_duration_ms=job.estimated_duration_ms,
        )
