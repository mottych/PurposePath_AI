"""API routes for generic coaching sessions.

This module provides FastAPI endpoints for the generic coaching conversation
engine supporting topic-based coaching with configurable prompts.

Endpoints:
    GET  /ai/coaching/topics    - Get available topics with user status
        USED BY: FE - BusinessOnboarding.tsx
    POST /ai/coaching/start     - Start or resume a coaching session
        USED BY: FE - OnboardingCoachPanel.tsx
    POST /ai/coaching/message   - Send a message in active session
        USED BY: FE - OnboardingCoachPanel.tsx
    POST /ai/coaching/pause     - Pause an active session
        USED BY: FE - OnboardingCoachPanel.tsx
    POST /ai/coaching/complete  - Complete a session with result extraction
        USED BY: FE - OnboardingCoachPanel.tsx
    POST /ai/coaching/cancel    - Cancel an active session
        USED BY: FE - OnboardingCoachPanel.tsx
    GET  /ai/coaching/session   - Get session details
        USED BY: FE - api.ts (getCoachingSession)
    GET  /ai/coaching/sessions  - List user sessions (UNUSED - verify if needed)

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
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies.ai_engine import create_template_processor
from coaching.src.api.multitenant_dependencies import (
    get_dynamodb_client,
)
from coaching.src.core.config_multitenant import settings
from coaching.src.domain.exceptions.session_exceptions import (
    ExtractionFailedError,
    MaxTurnsReachedError,
    SessionAccessDeniedError,
    SessionConflictError,
    SessionExpiredError,
    SessionIdleTimeoutError,
    SessionNotActiveError,
    SessionNotFoundError,
)
from coaching.src.infrastructure.repositories.dynamodb_coaching_session_repository import (
    DynamoDBCoachingSessionRepository,
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
    TopicsWithStatusResponse,
)
from coaching.src.services.coaching_session_service import (
    MessageResponse as ServiceMessageResponse,
)
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

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


@router.post("/message", response_model=ApiResponse[ServiceMessageResponse])
async def send_message(
    request: SendMessageRequest,
    context: RequestContext = Depends(get_current_context),
    service: CoachingSessionService = Depends(get_coaching_session_service),
) -> ApiResponse[ServiceMessageResponse]:
    """Send a message in an active coaching session.

    Processes the user's message and generates a coach response using
    the configured LLM and prompt templates.

    Args:
        request: Contains session_id and message content

    Returns:
        ApiResponse with MessageResponse containing coach's reply

    Raises:
        HTTPException 400: Session not active (paused/completed/cancelled)
        HTTPException 403: User does not own this session
        HTTPException 410: Session expired or idle timeout
        HTTPException 422: Session not found or max turns reached
        HTTPException 500: Failed to process message
    """
    logger.info(
        "coaching_sessions.send_message",
        session_id=request.session_id,
        tenant_id=context.tenant_id,
        message_length=len(request.message),
    )

    try:
        response = await service.send_message(
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            user_message=request.message,
        )

        logger.info(
            "coaching_sessions.send_message.success",
            session_id=request.session_id,
            message_count=response.message_count,
            status=response.status.value,
        )

        return ApiResponse(
            success=True,
            data=response,
            message="Message processed successfully",
        )

    except SessionNotFoundError as e:
        logger.warning(
            "coaching_sessions.send_message.not_found",
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionAccessDeniedError as e:
        logger.warning(
            "coaching_sessions.send_message.access_denied",
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=403,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except SessionNotActiveError as e:
        logger.warning(
            "coaching_sessions.send_message.not_active",
            session_id=request.session_id,
            current_status=e.current_status,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=400,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except (SessionExpiredError, SessionIdleTimeoutError) as e:
        logger.warning(
            "coaching_sessions.send_message.expired",
            session_id=request.session_id,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=410,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except MaxTurnsReachedError as e:
        logger.warning(
            "coaching_sessions.send_message.max_turns",
            session_id=request.session_id,
            current_turn=e.current_turn,
            max_turns=e.max_turns,
            error_code=e.code,
        )
        raise HTTPException(
            status_code=422,
            detail={"code": e.code, "message": str(e)},
        ) from e

    except Exception as e:
        logger.error(
            "coaching_sessions.send_message.error",
            error=str(e),
            session_id=request.session_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to process message",
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
