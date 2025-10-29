"""Multitenant conversation API routes with business data integration."""

from typing import Any

import structlog
from coaching.src.api.auth import get_current_context, require_permission
from coaching.src.api.dependencies import get_conversation_repository
from coaching.src.api.multitenant_dependencies import get_multitenant_conversation_service
from coaching.src.models.requests import (
    CompleteConversationRequest,
    InitiateConversationRequest,
    MessageRequest,
    PauseConversationRequest,
)
from coaching.src.models.responses import (
    BusinessDataSummaryResponse,
    ConversationActionResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from coaching.src.services.multitenant_conversation_service import MultitenantConversationService
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

from shared.models.multitenant import CoachingTopic, Permission, RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post("/initiate", response_model=ApiResponse[ConversationResponse])
async def initiate_conversation(
    request: InitiateConversationRequest,
    context: RequestContext = Depends(get_current_context),
    service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ApiResponse[ConversationResponse]:
    """Initiate a new coaching conversation with tenant context."""
    logger.info(
        "Initiating conversation",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        topic=request.topic.value,
    )

    # Check permission to start coaching
    if Permission.START_COACHING not in context.permissions:
        raise HTTPException(
            status_code=403, detail="Permission required to start coaching sessions"
        )

    try:
        response = await service.initiate_conversation(
            topic=CoachingTopic(request.topic.value),
            context_data=request.context,
            language=request.language,
        )

        logger.info(
            "Conversation initiated",
            conversation_id=response.conversation_id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            session_id=response.session_data.get("session_id") if response.session_data else None,
        )

        return ApiResponse(success=True, data=response)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{conversation_id}/message", response_model=MessageResponse)
async def send_message(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: MessageRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> MessageResponse:
    """Send a message in an existing conversation."""
    logger.info(
        "Processing message",
        conversation_id=conversation_id,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        message_length=len(request.user_message),
    )

    try:
        response = await service.process_message(
            conversation_id=conversation_id,
            user_message=request.user_message,
            metadata=request.metadata,
        )

        logger.info(
            "Message processed",
            conversation_id=conversation_id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            is_complete=response.is_complete,
            progress=response.progress,
        )

        return response

    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Access denied to this conversation") from e


@router.get("/business-data", response_model=ApiResponse[BusinessDataSummaryResponse])
async def get_business_data_summary(
    context: RequestContext = Depends(get_current_context),
    service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ApiResponse[BusinessDataSummaryResponse]:
    """Get current business data summary for the tenant."""
    logger.info(
        "Fetching business data summary", user_id=context.user_id, tenant_id=context.tenant_id
    )

    try:
        # Check permission to read business data (avoid method to handle duplicate models)
        if Permission.READ_BUSINESS_DATA.value not in (context.permissions or []):
            return ApiResponse(success=False, error="Permission required to read business data")

        summary = service.get_business_data_summary()

        business_summary = BusinessDataSummaryResponse(
            tenant_id=context.tenant_id, business_data=dict(summary)
        )
        return ApiResponse(success=True, data=business_summary)

    except Exception as e:
        logger.error(f"Error getting business data summary: {e}")
        return ApiResponse(success=False, error=f"Failed to retrieve business data summary: {e}")


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    context: RequestContext = Depends(get_current_context),
    conversation_repo: Any = Depends(get_conversation_repository),
) -> ConversationDetailResponse:
    """Get details of a specific conversation."""
    logger.info(
        "Fetching conversation",
        conversation_id=conversation_id,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    try:
        conversation = await conversation_repo.get(conversation_id)

        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        # Verify tenant access
        if conversation.context.get("tenant_id") != context.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied to this conversation")

        # Check permissions (users can view their own sessions, managers can view all)
        if (
            conversation.user_id != context.user_id
            and Permission.VIEW_ALL_SESSIONS not in context.permissions
        ):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return ConversationDetailResponse(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            topic=conversation.topic,
            status=conversation.status,
            messages=[
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in conversation.messages
            ],
            context=conversation.context.model_dump(),
            progress=conversation.calculate_progress(),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            completed_at=conversation.completed_at,
        )

    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Access denied to this conversation") from e


@router.post("/{conversation_id}/complete")
async def complete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: CompleteConversationRequest | None = None,
    context: RequestContext = Depends(get_current_context),
    service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ConversationActionResponse:
    """Mark a conversation as complete and extract business outcomes."""
    logger.info(
        "Completing conversation",
        conversation_id=conversation_id,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    try:
        result = await service.complete_conversation(
            conversation_id=conversation_id,
            _feedback=request.feedback if request else None,
            _rating=request.rating if request else None,
        )

        logger.info(
            "Conversation completed",
            conversation_id=conversation_id,
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            business_data_updated=result.get("business_data_updated", False),
        )

        return ConversationActionResponse(
            message="Conversation completed successfully", result=dict(result)
        )

    except PermissionError as e:
        raise HTTPException(status_code=403, detail="Access denied to this conversation") from e


@router.post("/{conversation_id}/pause")
async def pause_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    _request: PauseConversationRequest | None = None,
    context: RequestContext = Depends(get_current_context),
    _service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ConversationActionResponse:
    """Pause an active conversation."""
    logger.info(
        "Pausing conversation",
        conversation_id=conversation_id,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    # For now, delegate to the base service
    # TODO: Implement tenant-aware pause functionality
    # Pause functionality not yet implemented in MultitenantConversationService
    raise HTTPException(status_code=501, detail="Pause conversation feature not implemented")

    return ConversationActionResponse(message="Conversation paused successfully")


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    context: RequestContext = Depends(get_current_context),
    _service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ConversationActionResponse:
    """Delete (abandon) a conversation."""
    logger.info(
        "Deleting conversation",
        conversation_id=conversation_id,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    # Delete functionality not yet implemented in MultitenantConversationService
    raise HTTPException(status_code=501, detail="Delete conversation feature not implemented")

    return ConversationActionResponse(message="Conversation deleted successfully")


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    topic: str | None = Query(None, description="Filter by topic"),
    context: RequestContext = Depends(get_current_context),
    service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ConversationListResponse:
    """List conversations for the current user within their tenant."""
    logger.info(
        "Listing conversations",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        page=page,
        page_size=page_size,
        status=status,
        topic=topic,
    )

    coaching_topic = None
    if topic:
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid topic: {topic}") from e

    response = await service.list_user_conversations(
        page=page,
        page_size=page_size,
        status=status,
        topic=coaching_topic,
    )

    return response


@router.get("/tenant/all", response_model=ConversationListResponse)
async def list_all_tenant_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    topic: str | None = Query(None, description="Filter by topic"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    context: RequestContext = Depends(require_permission(Permission.VIEW_ALL_SESSIONS)),
    service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ConversationListResponse:
    """List all conversations within the tenant (admin/manager only)."""
    logger.info(
        "Listing all tenant conversations",
        admin_user_id=context.user_id,
        tenant_id=context.tenant_id,
        filter_user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
        topic=topic,
    )

    # TODO: Implement tenant-wide conversation listing
    # For now, return user's own conversations
    coaching_topic = None
    if topic:
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid topic: {topic}") from e

    response = await service.list_user_conversations(
        page=page,
        page_size=page_size,
        status=status,
        topic=coaching_topic,
    )

    return response
