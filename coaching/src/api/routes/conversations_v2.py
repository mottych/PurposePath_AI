"""Conversation API routes using new architecture (Phase 7).

This module provides REST API endpoints for conversation management,
integrating with the Phase 4-6 application services and domain layer.
"""

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies_v2 import (
    get_conversation_service_v2,
    get_llm_service_v2,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.conversations import (
    CompleteConversationRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    ConversationSummary,
    InitiateConversationRequest,
    MessageRequest,
    MessageResponse,
    PauseConversationRequest,
)
from coaching.src.application.conversation.conversation_service import (
    ConversationApplicationService,
)
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.constants import MessageRole
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.exceptions.conversation_exceptions import (
    ConversationNotActive,
    ConversationNotFound,
)
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

logger = structlog.get_logger()
router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/initiate", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def initiate_conversation(
    request: InitiateConversationRequest,
    user: UserContext = Depends(get_current_user),
    conversation_service: ConversationApplicationService = Depends(get_conversation_service_v2),
    llm_service: LLMApplicationService = Depends(get_llm_service_v2),
) -> ConversationResponse:
    """Initiate a new coaching conversation.

    This endpoint creates a new conversation for the authenticated user
    and generates an initial coaching prompt.

    **Authentication**: Bearer token required
    **user_id and tenant_id**: Extracted from JWT token

    Args:
        request: Conversation initiation request
        user: Authenticated user context (from JWT)
        conversation_service: Conversation application service
        llm_service: LLM service for generating initial prompt

    Returns:
        ConversationResponse with conversation details and initial message

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 500: If conversation creation fails
    """
    try:
        logger.info(
            "Initiating conversation",
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            topic=request.topic.value,
        )

        # Generate initial coaching prompt using LLM service
        initial_prompt = f"Welcome! Let's explore your {request.topic.value.replace('_', ' ')}. "
        if request.topic.value == "core_values":
            initial_prompt += "What matters most to you in your work and life?"
        elif request.topic.value == "purpose":
            initial_prompt += "What gives your work meaning and direction?"
        elif request.topic.value == "vision":
            initial_prompt += "Where do you see yourself and your work heading?"
        else:
            initial_prompt += "Let's begin this journey together."

        # Start conversation using application service
        conversation = await conversation_service.start_conversation(
            user_id=UserId(user.user_id),
            tenant_id=TenantId(user.tenant_id),
            topic=request.topic,
            initial_message_content=initial_prompt,
            metadata=request.context,
        )

        logger.info(
            "Conversation initiated successfully",
            conversation_id=conversation.conversation_id,
            user_id=user.user_id,
        )

        # Build response
        return ConversationResponse(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            tenant_id=conversation.tenant_id,
            topic=conversation.topic,
            status=conversation.status,
            current_phase=conversation.context.phase,
            initial_message=initial_prompt,
            progress=conversation.calculate_progress(),
            created_at=conversation.created_at,
        )

    except Exception as e:
        logger.error(
            "Failed to initiate conversation",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate conversation",
        ) from e


@router.post("/{conversation_id}/message", response_model=MessageResponse)
async def send_message(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: MessageRequest = ...,
    user: UserContext = Depends(get_current_user),
    conversation_service: ConversationApplicationService = Depends(get_conversation_service_v2),
    llm_service: LLMApplicationService = Depends(get_llm_service_v2),
) -> MessageResponse:
    """Send a message in an existing conversation.

    This endpoint adds a user message to the conversation and generates
    an AI coaching response.

    **Authentication**: Bearer token required

    Args:
        conversation_id: Unique conversation identifier
        request: Message request with user content
        user: Authenticated user context
        conversation_service: Conversation application service
        llm_service: LLM service for generating responses

    Returns:
        MessageResponse with AI response and conversation state

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 403: If user doesn't own conversation
        HTTPException 409: If conversation is not active
    """
    try:
        logger.info(
            "Processing message",
            conversation_id=conversation_id,
            user_id=user.user_id,
            message_length=len(request.user_message),
        )

        # Add user message
        conversation = await conversation_service.add_message(
            conversation_id=ConversationId(conversation_id),
            tenant_id=TenantId(user.tenant_id),
            role=MessageRole.USER,
            content=request.user_message,
        )

        # Verify ownership
        if conversation.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )

        # Build conversation history for LLM
        llm_messages = [
            LLMMessage(role=msg.role.value, content=msg.content) for msg in conversation.messages
        ]

        # Generate AI response
        llm_response = await llm_service.generate_response(
            messages=llm_messages,
            system_prompt=f"You are a professional coach helping with {conversation.topic.value.replace('_', ' ')}.",
            temperature=0.7,
        )

        # Add AI response to conversation
        conversation = await conversation_service.add_message(
            conversation_id=ConversationId(conversation_id),
            tenant_id=TenantId(user.tenant_id),
            role=MessageRole.ASSISTANT,
            content=llm_response.content,
        )

        # Check if conversation should complete
        is_complete = conversation.should_complete()
        if is_complete:
            conversation = await conversation_service.complete_conversation(
                conversation_id=ConversationId(conversation_id),
                tenant_id=TenantId(user.tenant_id),
            )

        logger.info(
            "Message processed successfully",
            conversation_id=conversation_id,
            message_count=len(conversation.messages),
            is_complete=is_complete,
        )

        # Extract insights from conversation
        user_messages = [msg for msg in conversation.messages if msg.is_from_user()]
        insights = [f"User mentioned: {msg.content[:50]}..." for msg in user_messages[-3:]]

        return MessageResponse(
            conversation_id=conversation.conversation_id,
            ai_response=llm_response.content,
            follow_up_question=None,  # Could be extracted from AI response
            current_phase=conversation.context.phase,
            progress=conversation.calculate_progress(),
            is_complete=is_complete,
            insights=insights,
            identified_values=[],  # Could be extracted from context
            next_steps=None,
        )

    except ConversationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    except ConversationNotActive as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conversation is not active: {e}",
        )
    except Exception as e:
        logger.error(
            "Failed to process message",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message",
        ) from e


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    user: UserContext = Depends(get_current_user),
    conversation_service: ConversationApplicationService = Depends(get_conversation_service_v2),
) -> ConversationDetailResponse:
    """Get detailed information about a specific conversation.

    **Authentication**: Bearer token required

    Args:
        conversation_id: Unique conversation identifier
        user: Authenticated user context
        conversation_service: Conversation application service

    Returns:
        ConversationDetailResponse with full conversation details

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 403: If user doesn't own conversation
    """
    try:
        logger.info(
            "Fetching conversation",
            conversation_id=conversation_id,
            user_id=user.user_id,
        )

        conversation = await conversation_service.get_conversation(
            conversation_id=ConversationId(conversation_id),
            tenant_id=TenantId(user.tenant_id),
        )

        # Verify ownership
        if conversation.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )

        # Build detailed response
        return ConversationDetailResponse(
            conversation_id=conversation.conversation_id,
            user_id=conversation.user_id,
            tenant_id=conversation.tenant_id,
            topic=conversation.topic,
            status=conversation.status,
            current_phase=conversation.context.phase,
            progress=conversation.calculate_progress(),
            messages=[
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in conversation.messages
            ],
            insights=conversation.context.insights,
            identified_values=[],  # Extract from context if available
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            completed_at=conversation.completed_at,
            metadata=conversation.metadata,
        )

    except ConversationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    except Exception as e:
        logger.error(
            "Failed to fetch conversation",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation",
        ) from e


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    user: UserContext = Depends(get_current_user),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(False, description="Only active conversations"),
    conversation_service: ConversationApplicationService = Depends(get_conversation_service_v2),
) -> ConversationListResponse:
    """List conversations for the authenticated user.

    **Authentication**: Bearer token required

    Args:
        user: Authenticated user context
        page: Page number for pagination
        page_size: Number of items per page
        active_only: Filter to only active conversations
        conversation_service: Conversation application service

    Returns:
        ConversationListResponse with paginated conversation list
    """
    try:
        logger.info(
            "Listing conversations",
            user_id=user.user_id,
            page=page,
            page_size=page_size,
            active_only=active_only,
        )

        conversations = await conversation_service.list_user_conversations(
            user_id=UserId(user.user_id),
            tenant_id=TenantId(user.tenant_id),
            limit=page_size,
            active_only=active_only,
        )

        # Build summaries
        summaries = [
            ConversationSummary(
                conversation_id=conv.conversation_id,
                user_id=conv.user_id,
                tenant_id=conv.tenant_id,
                topic=conv.topic,
                status=conv.status,
                current_phase=conv.context.phase,
                progress=conv.calculate_progress(),
                message_count=len(conv.messages),
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                completed_at=conv.completed_at,
            )
            for conv in conversations
        ]

        return ConversationListResponse(
            conversations=summaries,
            total=len(summaries),  # TODO: Get actual total from repository
            page=page,
            page_size=page_size,
            has_more=len(summaries) == page_size,
        )

    except Exception as e:
        logger.error(
            "Failed to list conversations",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations",
        ) from e


@router.post("/{conversation_id}/pause", status_code=status.HTTP_204_NO_CONTENT)
async def pause_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: PauseConversationRequest = ...,
    user: UserContext = Depends(get_current_user),
    conversation_service: ConversationApplicationService = Depends(get_conversation_service_v2),
) -> None:
    """Pause an active conversation.

    **Authentication**: Bearer token required

    Args:
        conversation_id: Unique conversation identifier
        request: Pause request with optional reason
        user: Authenticated user context
        conversation_service: Conversation application service

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 403: If user doesn't own conversation
        HTTPException 409: If conversation cannot be paused
    """
    try:
        logger.info(
            "Pausing conversation",
            conversation_id=conversation_id,
            user_id=user.user_id,
            reason=request.reason,
        )

        conversation = await conversation_service.pause_conversation(
            conversation_id=ConversationId(conversation_id),
            tenant_id=TenantId(user.tenant_id),
        )

        # Verify ownership
        if conversation.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )

        logger.info("Conversation paused successfully", conversation_id=conversation_id)

    except ConversationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    except Exception as e:
        logger.error(
            "Failed to pause conversation",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause conversation",
        ) from e


@router.post("/{conversation_id}/complete", status_code=status.HTTP_204_NO_CONTENT)
async def complete_conversation(
    conversation_id: str = Path(..., description="Conversation ID"),
    request: CompleteConversationRequest = ...,
    user: UserContext = Depends(get_current_user),
    conversation_service: ConversationApplicationService = Depends(get_conversation_service_v2),
) -> None:
    """Mark a conversation as complete.

    **Authentication**: Bearer token required

    Args:
        conversation_id: Unique conversation identifier
        request: Completion request with optional feedback
        user: Authenticated user context
        conversation_service: Conversation application service

    Raises:
        HTTPException 404: If conversation not found
        HTTPException 403: If user doesn't own conversation
    """
    try:
        logger.info(
            "Completing conversation",
            conversation_id=conversation_id,
            user_id=user.user_id,
            rating=request.rating,
        )

        conversation = await conversation_service.complete_conversation(
            conversation_id=ConversationId(conversation_id),
            tenant_id=TenantId(user.tenant_id),
        )

        # Verify ownership
        if conversation.user_id != user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this conversation",
            )

        # TODO: Store feedback and rating if provided

        logger.info("Conversation completed successfully", conversation_id=conversation_id)

    except ConversationNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    except Exception as e:
        logger.error(
            "Failed to complete conversation",
            conversation_id=conversation_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete conversation",
        ) from e


__all__ = ["router"]
