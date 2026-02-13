"""API routes for generic coaching sessions.

This module provides FastAPI endpoints for the generic coaching conversation
engine supporting topic-based coaching with configurable prompts.

Endpoints:
    GET  /ai/coaching/topics         - Get available topics with user status
        USED BY: FE - BusinessOnboarding.tsx
    GET  /ai/coaching/session/check  - Check if session exists for topic
        USED BY: FE - To detect existing sessions and conflicts before start/resume
    POST /ai/coaching/start          - Start NEW coaching session (cancels existing)
        USED BY: FE - When user wants to start fresh conversation
    POST /ai/coaching/resume         - Resume existing session with RESUME template
        USED BY: FE - When user wants to continue existing conversation
    POST /ai/coaching/message        - Send a message in active session
        USED BY: FE - OnboardingCoachPanel.tsx
    POST /ai/coaching/pause          - Pause an active session
        USED BY: FE - OnboardingCoachPanel.tsx
    POST /ai/coaching/complete       - Complete a session with result extraction
        USED BY: FE - OnboardingCoachPanel.tsx
    POST /ai/coaching/cancel         - Cancel an active session
        USED BY: FE - OnboardingCoachPanel.tsx
    GET  /ai/coaching/session        - Get session details
        USED BY: FE - api.ts (getCoachingSession)
    GET  /ai/coaching/sessions       - List user sessions (UNUSED - verify if needed)

All endpoints require authentication and enforce tenant isolation.

Error Responses:
    400 - SESSION_NOT_ACTIVE: Session is not in active state
    403 - SESSION_ACCESS_DENIED: User does not own this session
    409 - SESSION_CONFLICT: Another user has an active session for this topic
    410 - SESSION_EXPIRED: Session has expired or timed out
    422 - SESSION_NOT_FOUND: Session not found
    422 - MAX_TURNS_REACHED: Maximum conversation turns reached
    422 - INVALID_TOPIC: Topic not found or invalid
    500 - EXTRACTION_FAILED: Failed to extract results from session
"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse
from shared.services.eventbridge_client import EventBridgePublisher

from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies.ai_engine import create_template_processor
from coaching.src.api.multitenant_dependencies import (
    get_dynamodb_client,
)
from coaching.src.core.config_multitenant import settings
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.ai_job import AIJobStatus
from coaching.src.domain.exceptions.session_exceptions import (
    ExtractionFailedError,
    SessionAccessDeniedError,
    SessionConflictError,
    SessionNotActiveError,
    SessionNotFoundError,
)
from coaching.src.infrastructure.repositories.dynamodb_coaching_session_repository import (
    DynamoDBCoachingSessionRepository,
)
from coaching.src.infrastructure.repositories.dynamodb_job_repository import (
    DynamoDBJobRepository,
)
from coaching.src.services.coaching_message_job_service import (
    CoachingMessageJobService,
    MessageJobNotFoundError,
    MessageJobValidationError,
)
from coaching.src.services.coaching_session_service import (
    CoachingSessionService,
    InvalidTopicError,
    SessionCompletionResponse,
    SessionDetails,
    SessionResponse,
    SessionStateResponse,
    SessionSummary,
    SessionValidationError,
    TemplateNotFoundError,
    TopicNotActiveError,
    TopicsWithStatusResponse,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/ai/coaching", tags=["coaching-sessions"])


# =============================================================================
# Request/Response Models
# =============================================================================

# TopicStatus is imported from coaching_session_service
# TopicsWithStatusResponse is imported from coaching_session_service

# Alias for API response compatibility
TopicsResponse = TopicsWithStatusResponse


class StartSessionRequest(BaseModel):
    """Request to start or resume a coaching session."""

    topic_id: str = Field(..., description="ID of the coaching topic")
    context: dict[str, Any] | None = Field(
        default=None, description="Optional context data for the session"
    )


class SendMessageRequest(BaseModel):
    """Request to send a message in a coaching session."""

    session_id: str = Field(..., description="ID of the coaching session")
    message: str = Field(..., min_length=1, description="User's message content")


class SessionIdRequest(BaseModel):
    """Request with just a session ID."""

    session_id: str = Field(..., description="ID of the coaching session")


class MessageJobResponse(BaseModel):
    """Response for async message job creation."""

    job_id: str = Field(..., description="Unique job identifier for tracking")
    session_id: str = Field(..., description="Coaching session ID")
    status: str = Field(default="pending", description="Initial job status")
    estimated_duration_ms: int = Field(
        default=45000, description="Estimated processing time in milliseconds"
    )


class MessageJobStatusResponse(BaseModel):
    """Response for message job status polling."""

    job_id: str = Field(..., description="Unique job identifier")
    session_id: str = Field(..., description="Coaching session ID")
    status: str = Field(..., description="Current job status (pending/processing/completed/failed)")
    message: str | None = Field(default=None, description="Coach's response (when completed)")
    is_final: bool | None = Field(default=None, description="Whether this is the final message")
    result: dict[str, Any] | None = Field(default=None, description="Extraction result (if final)")
    turn: int | None = Field(default=None, description="Current turn number")
    max_turns: int | None = Field(default=None, description="Maximum turns allowed")
    message_count: int | None = Field(default=None, description="Total messages in conversation")
    error: str | None = Field(default=None, description="Error message (if failed)")
    processing_time_ms: int | None = Field(
        default=None, description="Actual processing time (if completed/failed)"
    )


# =============================================================================
# Dependencies
# =============================================================================


async def get_coaching_session_repository() -> DynamoDBCoachingSessionRepository:
    """Get coaching session repository instance."""
    dynamodb = get_dynamodb_client()
    return DynamoDBCoachingSessionRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.coaching_sessions_table,
    )


async def get_coaching_session_service(
    context: RequestContext = Depends(get_current_context),
    session_repository: DynamoDBCoachingSessionRepository = Depends(
        get_coaching_session_repository
    ),
    authorization: str | None = Header(None, description="Authorization header with Bearer token"),
) -> CoachingSessionService:
    """Get coaching session service with dependencies injected.

    Creates a TemplateParameterProcessor with the user's JWT token for
    parameter enrichment via Business API calls.
    """
    from coaching.src.api.dependencies.ai_engine import (
        get_provider_factory,
        get_s3_prompt_storage,
        get_topic_repository,
    )

    _ = context  # For tenant context in future enhancements

    # Extract JWT token for template processor
    jwt_token = None
    if authorization and authorization.startswith("Bearer "):
        jwt_token = authorization.split(" ", 1)[1]

    # Template processor is always created - it handles missing JWT gracefully
    template_processor = create_template_processor(jwt_token)

    # Get dependencies for coaching session service
    topic_repository = await get_topic_repository()
    s3_prompt_storage = await get_s3_prompt_storage()
    provider_factory = await get_provider_factory()

    return CoachingSessionService(
        session_repository=session_repository,
        topic_repository=topic_repository,
        s3_prompt_storage=s3_prompt_storage,
        template_processor=template_processor,
        provider_factory=provider_factory,
    )


async def get_job_repository() -> DynamoDBJobRepository:
    """Get job repository instance."""
    dynamodb = get_dynamodb_client()
    return DynamoDBJobRepository(
        dynamodb_resource=dynamodb,
        table_name=settings.ai_jobs_table,
    )


async def get_event_publisher() -> EventBridgePublisher:
    """Get EventBridge publisher instance."""
    return EventBridgePublisher(
        region_name="us-east-1",
        stage=settings.stage,
    )


async def get_coaching_message_job_service(
    job_repository: DynamoDBJobRepository = Depends(get_job_repository),
    session_service: CoachingSessionService = Depends(get_coaching_session_service),
    event_publisher: EventBridgePublisher = Depends(get_event_publisher),
) -> CoachingMessageJobService:
    """Get coaching message job service with dependencies injected."""
    return CoachingMessageJobService(
        job_repository=job_repository,
        session_service=session_service,
        event_publisher=event_publisher,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/topics", response_model=ApiResponse[TopicsResponse])
async def get_topics_status(
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[TopicsResponse]:
    """Get all coaching topics with user's completion status.

    Returns the list of available coaching topics along with the user's
    progress status for each:
    - not_started: User has never started this topic
    - in_progress: User has an active session
    - paused: User has a paused session
    - completed: User has completed this topic

    Returns:
        ApiResponse with TopicsResponse containing topic statuses
    """
    logger.info(
        "coaching_sessions.get_topics_status",
        tenant_id=context.tenant_id,
        user_id=context.user_id,
    )

    try:
        response = await service.get_topics_with_status(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Topics retrieved successfully",
        )

    except Exception as e:
        logger.error(
            "coaching_sessions.get_topics_status.error",
            error=str(e),
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve topics status",
        ) from e


@router.post("/start", response_model=ApiResponse[SessionResponse])
async def start_session(
    request: StartSessionRequest,
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[SessionResponse]:
    """Start a new coaching session or resume an existing one.

    If the user has an active or paused session for the topic, it will
    be resumed. Otherwise, a new session is created.

    Args:
        request: Contains topic_id and optional context data

    Returns:
        ApiResponse with SessionResponse containing session details

    Raises:
        HTTPException 409: Another user has an active session for this topic
        HTTPException 422: Invalid topic ID
        HTTPException 500: Failed to start session
    """
    logger.info(
        "coaching_sessions.start_session",
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        topic_id=request.topic_id,
    )

    try:
        response = await service.get_or_create_session(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            topic_id=request.topic_id,
            context=request.context or {},
        )

        logger.info(
            "coaching_sessions.start_session.success",
            session_id=response.session_id,
            status=response.status.value,
            tenant_id=context.tenant_id,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Session started successfully",
        )

    except SessionConflictError as e:
        logger.warning(
            "coaching_sessions.start_session.conflict",
            topic_id=request.topic_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=409,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except InvalidTopicError as e:
        logger.warning(
            "coaching_sessions.start_session.invalid_topic",
            topic_id=request.topic_id,
            tenant_id=context.tenant_id,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_TOPIC", "message": str(e)},
        ) from e

    except TopicNotActiveError as e:
        logger.warning(
            "coaching_sessions.start_session.topic_not_active",
            topic_id=request.topic_id,
            tenant_id=context.tenant_id,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": "TOPIC_NOT_ACTIVE", "message": str(e)},
        ) from e

    except TemplateNotFoundError as e:
        logger.error(
            "coaching_sessions.start_session.template_not_found",
            topic_id=request.topic_id,
            tenant_id=context.tenant_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500,
            detail={"code": "TEMPLATE_NOT_FOUND", "message": str(e)},
        ) from e

    except SessionValidationError as e:
        logger.warning(
            "coaching_sessions.start_session.validation_error",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        raise HTTPException(
            status_code=400,
            detail={"code": "VALIDATION_ERROR", "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.start_session.error",
            error=str(e),
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            topic_id=request.topic_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to start coaching session",
        ) from e


@router.post("/resume", response_model=ApiResponse[SessionResponse])
async def resume_session(
    request: SessionIdRequest,
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[SessionResponse]:
    """Resume an existing coaching session with RESUME template.

    This endpoint continues an existing session using the RESUME template,
    which welcomes the user back and summarizes the conversation so far.

    Works for both ACTIVE and PAUSED sessions:
    - PAUSED: User explicitly paused or session was idle when they left
    - ACTIVE: Chat window was closed by mistake, user wants to continue

    Args:
        request: Contains session_id

    Returns:
        ApiResponse with SessionResponse containing:
        - session_id: ID of the resumed session
        - message: Welcome back message with conversation summary
        - status: Session status (will be ACTIVE after resume)
        - resumed: True

    Raises:
        HTTPException 403: User does not own this session
        HTTPException 422: Session not found
        HTTPException 500: Failed to resume session

    Example Response:
        {
          "success": true,
          "data": {
            "session_id": "sess_abc123",
            "message": "Welcome back! Last time we discussed...",
            "status": "active",
            "turn": 3,
            "max_turns": 10,
            "resumed": true
          }
        }
    """
    logger.info(
        "coaching_sessions.resume",
        session_id=request.session_id,
        tenant_id=context.tenant_id,
    )

    try:
        response = await service.resume_session(
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )

        logger.info(
            "coaching_sessions.resume.success",
            session_id=request.session_id,
            status=response.status.value,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Session resumed successfully",
        )

    except SessionNotFoundError as e:
        logger.warning(
            "coaching_sessions.resume.not_found",
            session_id=request.session_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionAccessDeniedError as e:
        logger.warning(
            "coaching_sessions.resume.access_denied",
            session_id=request.session_id,
            user_id=context.user_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=403,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.resume.error",
            error=str(e),
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to resume session",
        ) from e


@router.post("/message", response_model=ApiResponse[MessageJobResponse], status_code=202)
async def send_message_async(
    request: SendMessageRequest,
    context: RequestContext = Depends(get_current_context),
    job_service: CoachingMessageJobService = Depends(get_coaching_message_job_service),
) -> ApiResponse[MessageJobResponse]:
    """Send a message in an active coaching session (async processing).

    Creates an async job and returns immediately with 202 Accepted.
    The message is processed in the background to avoid API Gateway 30s timeout.

    Frontend should:
    1. Connect to WebSocket to receive ai.message.completed event
    2. Or poll GET /message/{job_id} for status

    Args:
        request: Contains session_id and message content

    Returns:
        ApiResponse with MessageJobResponse (job_id for tracking)

    Raises:
        HTTPException 422: Invalid parameters or session not found
        HTTPException 500: Failed to create job
    """
    logger.info(
        "coaching_sessions.send_message_async",
        session_id=request.session_id,
        tenant_id=context.tenant_id,
        message_length=len(request.message),
    )

    try:
        # Create async job (returns immediately)
        job = await job_service.create_message_job(
            session_id=ConversationId(request.session_id),
            tenant_id=TenantId(context.tenant_id),
            user_id=UserId(context.user_id),
            topic_id="conversation_coaching",  # Get from session if needed
            user_message=request.message,
        )

        response = MessageJobResponse(
            job_id=job.job_id,
            session_id=request.session_id,
            status=job.status.value,
            estimated_duration_ms=job.estimated_duration_ms,
        )

        logger.info(
            "coaching_sessions.send_message_async.job_created",
            job_id=job.job_id,
            session_id=request.session_id,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Message job created, processing asynchronously",
        )

    except MessageJobValidationError as e:
        logger.warning(
            "coaching_sessions.send_message_async.validation_error",
            session_id=request.session_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=422,
            detail={"code": "JOB_VALIDATION_ERROR", "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.send_message_async.error",
            error=str(e),
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to create message job",
        ) from e


@router.get("/message/{job_id}", response_model=ApiResponse[MessageJobStatusResponse])
async def get_message_job_status(
    job_id: str,
    context: RequestContext = Depends(get_current_context),
    job_service: CoachingMessageJobService = Depends(get_coaching_message_job_service),
) -> ApiResponse[MessageJobStatusResponse]:
    """Get status of an async message job (polling fallback).

    Used when WebSocket is unavailable or for debugging.

    Args:
        job_id: Job identifier from POST /message response

    Returns:
        ApiResponse with MessageJobStatusResponse

    Raises:
        HTTPException 404: Job not found
        HTTPException 500: Failed to retrieve job status
    """
    logger.info(
        "coaching_sessions.get_message_job_status",
        job_id=job_id,
        tenant_id=context.tenant_id,
    )

    try:
        job = await job_service.get_job(job_id=job_id, tenant_id=context.tenant_id)

        # Build response based on job status
        response = MessageJobStatusResponse(
            job_id=job.job_id,
            session_id=job.session_id or "",
            status=job.status.value,
            processing_time_ms=job.processing_time_ms,
        )

        # Add result data if completed
        if job.status == AIJobStatus.COMPLETED and job.result:
            response.message = job.result.get("message")
            response.is_final = job.result.get("is_final")
            response.result = job.result.get("result")
            response.turn = job.result.get("turn")
            response.max_turns = job.result.get("max_turns")
            response.message_count = job.result.get("message_count")

        # Add error if failed
        if job.status == AIJobStatus.FAILED:
            response.error = job.error

        return ApiResponse(
            success=True,
            data=response,
            message=f"Job status: {job.status.value}",
        )

    except MessageJobNotFoundError as e:
        logger.warning(
            "coaching_sessions.get_message_job_status.not_found",
            job_id=job_id,
            tenant_id=context.tenant_id,
        )
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.get_message_job_status.error",
            error=str(e),
            job_id=job_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve job status",
        ) from e


@router.post("/pause", response_model=ApiResponse[SessionStateResponse])
async def pause_session(
    request: SessionIdRequest,
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[SessionStateResponse]:
    """Pause an active coaching session.

    The session can be resumed later with POST /ai/coaching/start.

    Args:
        request: Contains session_id

    Returns:
        ApiResponse with SessionStateResponse confirming pause

    Raises:
        HTTPException 400: Session cannot be paused (not active)
        HTTPException 403: User does not own this session
        HTTPException 422: Session not found
        HTTPException 500: Failed to pause session
    """
    logger.info(
        "coaching_sessions.pause_session",
        session_id=request.session_id,
        tenant_id=context.tenant_id,
    )

    try:
        response = await service.pause_session(
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )

        logger.info(
            "coaching_sessions.pause_session.success",
            session_id=request.session_id,
            status=response.status.value,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Session paused successfully",
        )

    except SessionNotFoundError as e:
        logger.warning(
            "coaching_sessions.pause_session.not_found",
            session_id=request.session_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionAccessDeniedError as e:
        logger.warning(
            "coaching_sessions.pause_session.access_denied",
            session_id=request.session_id,
            user_id=context.user_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=403,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionNotActiveError as e:
        logger.warning(
            "coaching_sessions.pause_session.not_active",
            session_id=request.session_id,
            current_status=e.current_status,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=400,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.pause_session.error",
            error=str(e),
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to pause session",
        ) from e


@router.post("/complete", response_model=ApiResponse[SessionCompletionResponse])
async def complete_session(
    request: SessionIdRequest,
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[SessionCompletionResponse]:
    """Complete a coaching session and extract results.

    Triggers LLM-based result extraction and marks the session as complete.

    Args:
        request: Contains session_id

    Returns:
        ApiResponse with SessionCompletionResponse containing extracted results

    Raises:
        HTTPException 400: Session cannot be completed (not active/paused)
        HTTPException 403: User does not own this session
        HTTPException 422: Session not found
        HTTPException 500: Extraction failed or internal error
    """
    logger.info(
        "coaching_sessions.complete_session",
        session_id=request.session_id,
        tenant_id=context.tenant_id,
    )

    try:
        response = await service.complete_session(
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )

        logger.info(
            "coaching_sessions.complete_session.success",
            session_id=request.session_id,
            status=response.status.value,
            has_result=bool(response.result),
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Session completed successfully",
        )

    except SessionNotFoundError as e:
        logger.warning(
            "coaching_sessions.complete_session.not_found",
            session_id=request.session_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionAccessDeniedError as e:
        logger.warning(
            "coaching_sessions.complete_session.access_denied",
            session_id=request.session_id,
            user_id=context.user_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=403,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionNotActiveError as e:
        logger.warning(
            "coaching_sessions.complete_session.not_active",
            session_id=request.session_id,
            current_status=e.current_status,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=400,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except ExtractionFailedError as e:
        logger.error(
            "coaching_sessions.complete_session.extraction_failed",
            session_id=request.session_id,
            reason=e.reason,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=500,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.complete_session.error",
            error=str(e),
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to complete session",
        ) from e


@router.post("/cancel", response_model=ApiResponse[SessionStateResponse])
async def cancel_session(
    request: SessionIdRequest,
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[SessionStateResponse]:
    """Cancel a coaching session.

    The session will be marked as cancelled and cannot be resumed.

    Args:
        request: Contains session_id

    Returns:
        ApiResponse with SessionStateResponse confirming cancellation

    Raises:
        HTTPException 400: Session cannot be cancelled (already completed)
        HTTPException 403: User does not own this session
        HTTPException 422: Session not found
        HTTPException 500: Failed to cancel session
    """
    logger.info(
        "coaching_sessions.cancel_session",
        session_id=request.session_id,
        tenant_id=context.tenant_id,
    )

    try:
        response = await service.cancel_session(
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )

        logger.info(
            "coaching_sessions.cancel_session.success",
            session_id=request.session_id,
            status=response.status.value,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Session cancelled successfully",
        )

    except SessionNotFoundError as e:
        logger.warning(
            "coaching_sessions.cancel_session.not_found",
            session_id=request.session_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionAccessDeniedError as e:
        logger.warning(
            "coaching_sessions.cancel_session.access_denied",
            session_id=request.session_id,
            user_id=context.user_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=403,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionNotActiveError as e:
        logger.warning(
            "coaching_sessions.cancel_session.not_active",
            session_id=request.session_id,
            current_status=e.current_status,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=400,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.cancel_session.error",
            error=str(e),
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to cancel session",
        ) from e


@router.get("/session/check", response_model=ApiResponse[dict[str, Any]])
async def check_session_exists(
    topic_id: str = Query(..., description="Coaching topic ID to check"),
    context: RequestContext = Depends(get_current_context),
    repo: DynamoDBCoachingSessionRepository = Depends(get_coaching_session_repository),
) -> ApiResponse[dict[str, Any]]:
    """Check if a resumable session exists for a topic.

    This endpoint allows the frontend to check for existing sessions before
    starting/resuming, and to detect if another user from the same tenant
    has an active session (conflict detection).

    Status Logic:
    - Returns "paused" if:
      - Session is explicitly PAUSED (user clicked pause), OR
      - Session is ACTIVE but idle > 30 minutes (implied pause)
    - Returns "active" if session is ACTIVE and NOT idle

    This allows frontend to show "Resume or Start New?" dialog appropriately.

    Args:
        topic_id: Coaching topic ID to check

    Returns:
        ApiResponse with session status information:
        - has_session: boolean - whether current user has active/paused session
        - session_id: string | null - session ID if exists
        - status: string - "active" | "paused" (computed based on idle time)
        - actual_status: string - raw session status from database
        - is_idle: boolean - whether session has been idle > 30 minutes
        - conflict: boolean - whether another user has active session
        - conflict_user_id: string | null - other user's ID if conflict

    Example Response (Idle Session - returned as "paused"):
        {
          "success": true,
          "data": {
            "has_session": true,
            "session_id": "sess_xxx",
            "status": "paused",
            "actual_status": "active",
            "is_idle": true,
            "conflict": false,
            "conflict_user_id": null
          }
        }
    """
    logger.info(
        "coaching_sessions.check_session",
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        topic_id=topic_id,
    )

    try:
        # Check for user's own session
        user_session = await repo.get_active_for_user_topic(
            user_id=context.user_id,
            topic_id=topic_id,
            tenant_id=context.tenant_id,
        )

        # Check for any active session for this tenant+topic
        tenant_session = await repo.get_active_by_tenant_topic(
            tenant_id=context.tenant_id,
            topic_id=topic_id,
        )

        # Compute status for frontend: "paused" if explicitly paused OR idle
        computed_status = None
        actual_status = None
        is_idle = False

        if user_session:
            actual_status = user_session.status.value
            is_idle = user_session.is_idle()

            # Return "paused" if explicitly PAUSED or if ACTIVE but idle
            if user_session.status.value == "paused" or is_idle:
                computed_status = "paused"
            else:
                computed_status = "active"

        result = {
            "has_session": user_session is not None,
            "session_id": str(user_session.session_id) if user_session else None,
            "status": computed_status,  # Computed status for frontend
            "actual_status": actual_status,  # Raw DB status
            "is_idle": is_idle,  # Helper flag
            "conflict": (
                tenant_session is not None and str(tenant_session.user_id) != context.user_id
            ),
            "conflict_user_id": (
                str(tenant_session.user_id)
                if tenant_session and str(tenant_session.user_id) != context.user_id
                else None
            ),
        }

        logger.info(
            "coaching_sessions.check_session.result",
            has_session=result["has_session"],
            status=result["status"],
            is_idle=result["is_idle"],
            conflict=result["conflict"],
        )

        return ApiResponse(
            success=True,
            data=result,
        )

    except Exception as e:
        logger.error(
            "coaching_sessions.check_session.error",
            error=str(e),
            topic_id=topic_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to check session status",
        ) from e


@router.get("/session", response_model=ApiResponse[SessionDetails])
async def get_session(
    session_id: str = Query(..., description="ID of the coaching session"),
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[SessionDetails]:
    """Get detailed information about a coaching session.

    Returns full session details including message history.

    Args:
        session_id: ID of the session to retrieve

    Returns:
        ApiResponse with SessionDetails

    Raises:
        HTTPException 403: User does not own this session
        HTTPException 422: Session not found
        HTTPException 500: Failed to retrieve session
    """
    logger.info(
        "coaching_sessions.get_session",
        session_id=session_id,
        tenant_id=context.tenant_id,
    )

    try:
        response = await service.get_session(
            session_id=session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )

        if response is None:
            raise SessionNotFoundError(session_id=session_id, tenant_id=context.tenant_id)

        logger.info(
            "coaching_sessions.get_session.success",
            session_id=session_id,
            status=response.status.value,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Session retrieved successfully",
        )

    except SessionNotFoundError as e:
        logger.warning(
            "coaching_sessions.get_session.not_found",
            session_id=session_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionAccessDeniedError as e:
        logger.warning(
            "coaching_sessions.get_session.access_denied",
            session_id=session_id,
            user_id=context.user_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=403,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.get_session.error",
            error=str(e),
            session_id=session_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve session",
        ) from e


@router.get("/sessions", response_model=ApiResponse[list[SessionSummary]])
async def list_user_sessions(
    include_completed: bool = Query(
        default=False, description="Include completed and cancelled sessions"
    ),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum sessions to return"),
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[list[SessionSummary]]:
    """List all coaching sessions for the current user.

    Args:
        include_completed: Whether to include completed/cancelled sessions
        limit: Maximum number of sessions to return (1-100)

    Returns:
        ApiResponse with list of SessionSummary

    Raises:
        HTTPException 500: Failed to list sessions
    """
    logger.info(
        "coaching_sessions.list_sessions",
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        include_completed=include_completed,
        limit=limit,
    )

    try:
        sessions = await service.list_user_sessions(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            include_completed=include_completed,
            limit=limit,
        )

        logger.info(
            "coaching_sessions.list_sessions.success",
            count=len(sessions),
            tenant_id=context.tenant_id,
        )

        return ApiResponse(
            success=True,
            data=sessions,
            message=f"Found {len(sessions)} sessions",
        )

    except Exception as e:
        logger.error(
            "coaching_sessions.list_sessions.error",
            error=str(e),
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to list sessions",
        ) from e


__all__ = ["router"]
