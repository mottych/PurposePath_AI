"""Conversation API routes."""

from typing import Optional

import structlog
from coaching.src.api.dependencies import get_conversation_service
from coaching.src.models.requests import (
    CompleteConversationRequest,
    InitiateConversationRequest,
    MessageRequest,
    PauseConversationRequest,
)
from coaching.src.models.responses import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    MessageResponse,
)
from coaching.src.services.conversation_service import ConversationService
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query

logger = structlog.get_logger()
router = APIRouter()


@router.post("/initiate", response_model=ConversationResponse)
async def initiate_conversation(
    request: InitiateConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Initiate a new coaching conversation."""
    logger.info(
        "Initiating conversation",
        user_id=request.user_id,
        topic=request.topic.value,
    )

    response = await service.initiate_conversation(
        user_id=request.user_id,
        topic=request.topic,
        context=request.context,
        language=request.language,
    )

    logger.info(
        "Conversation initiated",
        conversation_id=response.conversation_id,
        user_id=request.user_id,
    )

    return response


@router.post("/{conversation_id}/message", response_model=MessageResponse)
async def send_message(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: MessageRequest = Body(...),
    service: ConversationService = Depends(get_conversation_service),
) -> MessageResponse:
    """Send a message in an existing conversation."""
    logger.info(
        "Processing message",
        conversation_id=conversation_id,
        message_length=len(request.user_message),
    )

    response = await service.process_message(
        conversation_id=conversation_id,
        user_message=request.user_message,
        metadata=request.metadata,
    )

    logger.info(
        "Message processed",
        conversation_id=conversation_id,
        is_complete=response.is_complete,
        progress=response.progress,
    )

    return response


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationDetailResponse:
    """Get details of a specific conversation."""
    logger.info("Fetching conversation", conversation_id=conversation_id)

    conversation = await service.get_conversation(conversation_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

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


@router.post("/{conversation_id}/pause")
async def pause_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: Optional[PauseConversationRequest] = None,
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, str]:
    """Pause an active conversation."""
    logger.info("Pausing conversation", conversation_id=conversation_id)

    await service.pause_conversation(
        conversation_id=conversation_id,
        reason=request.reason if request else None,
    )

    return {"message": "Conversation paused successfully"}


@router.post("/{conversation_id}/resume")
async def resume_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """Resume a paused conversation."""
    logger.info("Resuming conversation", conversation_id=conversation_id)

    response = await service.resume_conversation(conversation_id)

    return response


@router.post("/{conversation_id}/complete")
async def complete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: Optional[CompleteConversationRequest] = None,
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, str]:
    """Mark a conversation as complete."""
    logger.info("Completing conversation", conversation_id=conversation_id)

    await service.complete_conversation(
        conversation_id=conversation_id,
        feedback=request.feedback if request else None,
        rating=request.rating if request else None,
    )

    return {"message": "Conversation completed successfully"}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    service: ConversationService = Depends(get_conversation_service),
) -> dict[str, str]:
    """Delete (abandon) a conversation."""
    logger.info("Deleting conversation", conversation_id=conversation_id)

    await service.abandon_conversation(conversation_id)

    return {"message": "Conversation deleted successfully"}


@router.get("/user/{user_id}", response_model=ConversationListResponse)
async def list_user_conversations(
    user_id: str = Path(..., description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationListResponse:
    """List conversations for a specific user."""
    logger.info(
        "Listing user conversations",
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
    )

    response = await service.list_user_conversations(
        user_id=user_id,
        page=page,
        page_size=page_size,
        status=status,
    )

    return response
