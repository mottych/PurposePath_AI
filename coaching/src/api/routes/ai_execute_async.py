"""API routes for async AI execution.

This module provides endpoints for asynchronous AI execution:
- POST /ai/execute-async — canonical orchestration envelope for all async kickoffs
- GET /ai/jobs/{jobId} — job status (polling fallback)

These endpoints support long-running AI operations beyond API Gateway timeouts.
"""

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Path, status

from coaching.src.api.auth import get_tenant_for_async_job_access
from coaching.src.api.dependencies.async_execution import get_async_execution_service
from coaching.src.api.models.async_ai import (
    AsyncAIRequest,
    AsyncJobCreatedResponse,
    AsyncJobData,
    JobStatusData,
    JobStatusResponse,
)
from coaching.src.api.models.job_status_contract import api_contract_status_for_job_status
from coaching.src.services.async_execution_service import (
    AsyncAIExecutionService,
    JobNotFoundError,
    JobValidationError,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/ai", tags=["AI Async Execute"])


@router.post(
    "/execute-async",
    response_model=AsyncJobCreatedResponse,
    response_model_by_alias=True,
    summary="Start an async AI job",
    description="""
Start an asynchronous AI job for long-running operations.

Uses the **canonical execute-async JSON body** (orchestration envelope): tenant/user,
correlation, idempotency, `activityData` for topic parameters, and `authContext` for
the service enrichment token. See shared spec: `email-insights-api-contract.md` §4
and §4.7.

**Flow:**
1. Call this endpoint → receive `jobId` immediately
2. Listen for WebSocket events (`ai.job.completed` or `ai.job.failed`)
3. Optionally poll `GET /ai/jobs/{jobId}` as fallback
""",
    responses={
        200: {"description": "Job created successfully"},
        400: {
            "description": "Invalid request - topic inactive or wrong type",
            "content": {
                "application/json": {"example": {"detail": "Topic niche_review is not active"}}
            },
        },
        404: {
            "description": "Topic not found",
            "content": {
                "application/json": {"example": {"detail": "Topic not found: unknown_topic"}}
            },
        },
        422: {
            "description": "Missing or invalid envelope / parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Missing required parameters for topic niche_review: ['current_value']"
                    }
                }
            },
        },
    },
)
async def execute_async(
    request_body: AsyncAIRequest,
    service: AsyncAIExecutionService = Depends(get_async_execution_service),
    authorization: str | None = Header(None),
) -> AsyncJobCreatedResponse:
    """Start an async AI job from the canonical orchestration envelope."""
    tenant_id = str(request_body.tenant_id)
    user_id = str(request_body.user_id)
    parameters = request_body.activity_data
    jwt_token = request_body.auth_context.service_token

    logger.info(
        "async_execute.started",
        topic_id=request_body.topic_id,
        tenant_id=tenant_id,
        user_id=user_id,
        correlation_id=request_body.correlation_id,
        idempotency_key=request_body.idempotency_key,
        event_id=request_body.event_id,
        has_bearer_header=bool(authorization and authorization.startswith("Bearer ")),
    )

    try:
        job = await service.create_job(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=request_body.topic_id,
            parameters=parameters,
            jwt_token=jwt_token,
            correlation_id=request_body.correlation_id,
            idempotency_key=request_body.idempotency_key,
            event_id=request_body.event_id,
            request_id=request_body.request_id,
            topic_category=request_body.topic_category,
            event_signal=request_body.event_signal,
            kickoff_transport="api",
        )

        logger.info(
            "async_execute.job_created",
            job_id=job.job_id,
            topic_id=job.topic_id,
        )

        return AsyncJobCreatedResponse(
            success=True,
            data=AsyncJobData.model_validate(
                {
                    "jobId": job.job_id,
                    "status": api_contract_status_for_job_status(job.status),
                    "topicId": job.topic_id,
                    "estimatedDurationMs": job.estimated_duration_ms,
                }
            ),
        )

    except JobValidationError as e:
        error_msg = str(e)
        logger.warning(
            "async_execute.validation_error",
            topic_id=request_body.topic_id,
            error=error_msg,
        )

        if "not found" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "missing required parameters" in error_msg.lower():
            status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(status_code=status_code, detail=error_msg) from e

    except Exception as e:
        logger.exception(
            "async_execute.unexpected_error",
            topic_id=request_body.topic_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {e!s}",
        ) from e


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    response_model_by_alias=True,
    summary="Get job status",
    description="""
Get the current status of an async AI job.

Use this endpoint as a polling fallback when:
- WebSocket connection drops during job execution
- Page refresh while job is pending
- Debugging and testing

**Response (Pending/Processing):**
```json
{
    "success": true,
    "data": {
        "jobId": "550e8400-e29b-41d4-a716-446655440000",
        "status": "processing",
        "topicId": "niche_review",
        "createdAt": "2025-12-10T20:00:00Z"
    }
}
```

**Response (Completed):**
```json
{
    "success": true,
    "data": {
        "jobId": "550e8400-e29b-41d4-a716-446655440000",
        "status": "completed",
        "topicId": "niche_review",
        "createdAt": "2025-12-10T20:00:00Z",
        "completedAt": "2025-12-10T20:00:35Z",
        "result": { "qualityReview": "...", "suggestions": [...] },
        "processingTimeMs": 35000
    }
}
```
""",
    responses={
        200: {"description": "Job status retrieved"},
        404: {
            "description": "Job not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Job not found: 550e8400-e29b-41d4-a716-446655440000"}
                }
            },
        },
    },
)
async def get_job_status(
    job_id: str = Path(
        ...,
        description="Unique job identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    tenant_id: str = Depends(get_tenant_for_async_job_access),
    service: AsyncAIExecutionService = Depends(get_async_execution_service),
) -> JobStatusResponse:
    """Get job status by ID (tenant from Bearer JWT: user session or service token)."""
    try:
        job = await service.get_job(job_id=job_id, tenant_id=tenant_id)

        return JobStatusResponse(
            success=True,
            data=JobStatusData.from_job(job),
        )

    except JobNotFoundError as e:
        logger.warning(
            "get_job_status.not_found",
            job_id=job_id,
            tenant_id=tenant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.exception(
            "get_job_status.unexpected_error",
            job_id=job_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {e!s}",
        ) from e
