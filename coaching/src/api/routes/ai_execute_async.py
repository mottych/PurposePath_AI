"""API routes for async AI execution.

This module provides endpoints for asynchronous AI execution:
- POST /ai/execute-async - Start an async AI job
- GET /ai/jobs/{jobId} - Check job status (polling fallback)

These endpoints enable long-running AI operations that exceed
API Gateway's 30-second timeout limit.
"""

import structlog
from coaching.src.api.dependencies.async_execution import get_async_execution_service
from coaching.src.api.models.async_ai import (
    AsyncAIRequest,
    AsyncJobCreatedResponse,
    AsyncJobData,
    JobStatusData,
    JobStatusResponse,
)
from coaching.src.services.async_execution_service import (
    AsyncAIExecutionService,
    JobNotFoundError,
    JobValidationError,
)
from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

logger = structlog.get_logger()

router = APIRouter(prefix="/ai", tags=["AI Async Execute"])


@router.post(
    "/execute-async",
    response_model=AsyncJobCreatedResponse,
    summary="Start an async AI job",
    description="""
Start an asynchronous AI job for long-running operations.

This endpoint returns immediately with a job ID. The actual AI execution
happens asynchronously, and results are delivered via WebSocket events.

**Flow:**
1. Call this endpoint → receive `jobId` immediately
2. Listen for WebSocket events (`ai.job.completed` or `ai.job.failed`)
3. Optionally poll `GET /ai/jobs/{jobId}` as fallback

**Use this endpoint for:**
- Operations that may take longer than 30 seconds
- Better UX with progress indicators
- Resilient handling of long AI operations

**Request:**
```json
{
    "topic_id": "niche_review",
    "parameters": {
        "current_value": "We help small businesses grow"
    }
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "jobId": "550e8400-e29b-41d4-a716-446655440000",
        "status": "pending",
        "topicId": "niche_review",
        "estimatedDurationMs": 35000
    }
}
```
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
            "description": "Missing required parameters",
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
    request: Request,
    service: AsyncAIExecutionService = Depends(get_async_execution_service),
) -> AsyncJobCreatedResponse:
    """Start an async AI job.

    Creates a new job record and starts background execution.
    Returns immediately with job ID for tracking.

    Args:
        request_body: AI execution request with topic_id and parameters
        request: FastAPI request for user context
        service: Async execution service from DI

    Returns:
        AsyncJobCreatedResponse with job ID and status

    Raises:
        HTTPException: Various status codes for validation errors
    """
    # Extract tenant and user from request state (set by auth middleware)
    tenant_id = getattr(request.state, "tenant_id", None)
    user_id = getattr(request.state, "user_id", None)

    if not tenant_id or not user_id:
        logger.error(
            "async_execute.missing_context",
            has_tenant=bool(tenant_id),
            has_user=bool(user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication context",
        )

    logger.info(
        "async_execute.started",
        topic_id=request_body.topic_id,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    try:
        job = await service.create_job(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=request_body.topic_id,
            parameters=request_body.parameters,
        )

        logger.info(
            "async_execute.job_created",
            job_id=job.job_id,
            topic_id=job.topic_id,
        )

        return AsyncJobCreatedResponse(
            success=True,
            data=AsyncJobData(
                job_id=job.job_id,
                status=job.status.value,
                topic_id=job.topic_id,
                estimated_duration_ms=job.estimated_duration_ms,
            ),
        )

    except JobValidationError as e:
        error_msg = str(e)
        logger.warning(
            "async_execute.validation_error",
            topic_id=request_body.topic_id,
            error=error_msg,
        )

        # Determine appropriate status code
        if "not found" in error_msg.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "missing required parameters" in error_msg.lower():
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
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
    request: Request,
    job_id: str = Path(
        ...,
        description="Unique job identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    service: AsyncAIExecutionService = Depends(get_async_execution_service),
) -> JobStatusResponse:
    """Get job status by ID.

    Retrieves current job status, including result if completed
    or error if failed. Enforces tenant isolation.

    Args:
        job_id: Unique job identifier
        request: FastAPI request for tenant context
        service: Async execution service from DI

    Returns:
        JobStatusResponse with current job status

    Raises:
        HTTPException: 404 if job not found or tenant mismatch
    """
    # Extract tenant from request state
    tenant_id = getattr(request.state, "tenant_id", None) if request else None

    if not tenant_id:
        logger.error("get_job_status.missing_tenant")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication context",
        )

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
