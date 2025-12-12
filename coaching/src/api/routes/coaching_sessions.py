"""API routes for generic coaching sessions.

This module provides FastAPI endpoints for the generic coaching conversation
engine supporting topic-based coaching with configurable prompts.

Endpoints:
    GET  /ai/coaching/topics    - Get available topics with user status
    POST /ai/coaching/start     - Start or resume a coaching session
    POST /ai/coaching/message   - Send a message in active session
    POST /ai/coaching/pause     - Pause an active session
    POST /ai/coaching/complete  - Complete a session with result extraction
    POST /ai/coaching/cancel    - Cancel an active session
    GET  /ai/coaching/session   - Get session details

All endpoints require authentication and enforce tenant isolation.
"""

from typing import Any

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.multitenant_dependencies import (
    get_dynamodb_client,
    get_llm_service,
)
from coaching.src.core.coaching_topic_registry import list_coaching_topics
from coaching.src.core.config_multitenant import settings
from coaching.src.core.constants import ConversationStatus
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
)
from coaching.src.services.coaching_session_service import (
    MessageResponse as ServiceMessageResponse,
)
from coaching.src.services.llm_service import LLMService
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/ai/coaching", tags=["coaching-sessions"])


# =============================================================================
# Request/Response Models
# =============================================================================


class TopicStatus(BaseModel):
    """Status of a coaching topic for a user."""

    topic_id: str
    name: str
    description: str
    status: str = Field(description="Status: 'not_started', 'in_progress', 'paused', 'completed'")
    session_id: str | None = Field(default=None, description="Session ID if in_progress or paused")
    completed_at: str | None = Field(default=None, description="Completion timestamp if completed")


class TopicsResponse(BaseModel):
    """Response containing all topics with status."""

    topics: list[TopicStatus]


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
    llm_service: LLMService = Depends(get_llm_service),
    session_repository: DynamoDBCoachingSessionRepository = Depends(
        get_coaching_session_repository
    ),
) -> CoachingSessionService:
    """Get coaching session service with dependencies injected."""
    _ = context  # For tenant context in future enhancements
    return CoachingSessionService(
        session_repository=session_repository,
        llm_service=llm_service,
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/topics", response_model=ApiResponse[TopicsResponse])
async def get_topics_status(
    context: RequestContext = Depends(get_current_context),
    session_repository: DynamoDBCoachingSessionRepository = Depends(
        get_coaching_session_repository
    ),
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
        # Get all available topics from registry
        all_topics = list_coaching_topics()

        # Get user's sessions to determine status
        user_sessions = await session_repository.list_by_tenant_user(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )

        # Build a map of topic_id -> latest session
        topic_sessions: dict[str, Any] = {}
        for session in user_sessions:
            topic_id = session.topic_id
            if topic_id not in topic_sessions:
                topic_sessions[topic_id] = session
            else:
                # Keep the most recent session
                existing = topic_sessions[topic_id]
                if session.updated_at > existing.updated_at:
                    topic_sessions[topic_id] = session

        # Build response
        topic_statuses: list[TopicStatus] = []
        for topic in all_topics:
            existing_session = topic_sessions.get(topic.topic_id)

            if existing_session is None:
                status = "not_started"
                session_id = None
                completed_at = None
            elif existing_session.status == ConversationStatus.ACTIVE:
                status = "in_progress"
                session_id = existing_session.session_id
                completed_at = None
            elif existing_session.status == ConversationStatus.PAUSED:
                status = "paused"
                session_id = existing_session.session_id
                completed_at = None
            elif existing_session.status == ConversationStatus.COMPLETED:
                status = "completed"
                session_id = existing_session.session_id
                completed_at = (
                    existing_session.completed_at.isoformat()
                    if existing_session.completed_at
                    else None
                )
            else:
                # Cancelled - treat as not started
                status = "not_started"
                session_id = None
                completed_at = None

            topic_statuses.append(
                TopicStatus(
                    topic_id=topic.topic_id,
                    name=topic.name,
                    description=topic.description,
                    status=status,
                    session_id=session_id,
                    completed_at=completed_at,
                )
            )

        return ApiResponse(
            success=True,
            data=TopicsResponse(topics=topic_statuses),
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
        HTTPException 400: Invalid topic ID
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

    except InvalidTopicError as e:
        logger.warning(
            "coaching_sessions.start_session.invalid_topic",
            topic_id=request.topic_id,
            tenant_id=context.tenant_id,
        )
        raise HTTPException(status_code=400, detail=str(e)) from e

    except SessionValidationError as e:
        logger.warning(
            "coaching_sessions.start_session.validation_error",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        raise HTTPException(status_code=400, detail=str(e)) from e

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
        HTTPException 404: Session not found
        HTTPException 400: Session not active (paused/completed/cancelled)
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

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e

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
        HTTPException 404: Session not found
        HTTPException 400: Session cannot be paused (not active)
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

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e

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
        HTTPException 404: Session not found
        HTTPException 400: Session cannot be completed (not active/paused)
        HTTPException 500: Failed to complete session
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

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e

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
        HTTPException 404: Session not found
        HTTPException 400: Session cannot be cancelled (already completed)
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

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail=error_msg) from e
        raise HTTPException(status_code=400, detail=error_msg) from e

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
        HTTPException 404: Session not found
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
        )

        if response is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}",
            )

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

    except HTTPException:
        raise

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
