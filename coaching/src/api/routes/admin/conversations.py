"""Admin API routes for conversation monitoring."""

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_conversation_repository
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.types import create_tenant_id, create_user_id
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from coaching.src.models.admin_responses import (
    ConversationDetail,
    ConversationMessage,
    ConversationSummary,
)
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse, PaginatedResponse, PaginationMeta

logger = structlog.get_logger()
router = APIRouter()


@router.get("/conversations", response_model=PaginatedResponse[ConversationSummary])
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: str | None = Query(None, description="Filter by tenant ID"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    status: str | None = Query(None, description="Filter by status"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    conversation_repo: DynamoDBConversationRepository = Depends(get_conversation_repository),
) -> PaginatedResponse[ConversationSummary]:
    """
    Get list of active AI coaching conversations for monitoring.

    This endpoint allows administrators to monitor all active conversations
    across tenants for support and quality assurance purposes.

    **Permissions Required:** ADMIN_ACCESS

    **Query Parameters:**
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)
    - `tenant_id`: Filter by specific tenant
    - `user_id`: Filter by specific user
    - `status`: Filter by conversation status

    **Returns:**
    - Paginated list of conversation summaries
    - Basic metadata (tenant, user, topic, message count)
    """
    logger.info(
        "Fetching conversations list",
        admin_user_id=context.user_id,
        page=page,
        page_size=page_size,
        filters={"tenant_id": tenant_id, "user_id": user_id, "status": status},
    )

    try:
        # For Phase 1 (read-only), we'll implement a basic version
        # In production, this would use a DynamoDB scan with filters
        # or a dedicated GSI for admin queries

        conversations = []

        # If user_id is provided, we can use the existing get_by_user method
        if user_id:
            user_conversations = await conversation_repo.get_by_user(
                user_id=create_user_id(user_id),
                tenant_id=create_tenant_id(tenant_id) if tenant_id else None,
                limit=page_size * page,  # Get enough for pagination
                active_only=(status == "active") if status else False,
            )

            # Apply pagination
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            conversations = user_conversations[start_idx:end_idx]
        else:
            # For admin listing all conversations, we'd need a scan operation
            # For now, return empty list with a note that filters are required
            logger.warning(
                "Admin list all conversations requires user_id filter in Phase 1",
                admin_user_id=context.user_id,
            )

        # Convert to response format
        summaries = []
        for conv in conversations:
            summary = ConversationSummary(
                conversationId=conv.conversation_id,
                tenantId=conv.tenant_id,
                userId=conv.user_id,
                topic="unknown",  # ConversationContext doesn't have topic attribute
                status=conv.status.value,
                messageCount=len(conv.messages),
                createdAt=conv.created_at,
                lastActivity=conv.updated_at,
            )
            summaries.append(summary)

        total = len(summaries)  # Simplified for Phase 1
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        logger.info(
            "Conversations list retrieved",
            admin_user_id=context.user_id,
            count=len(summaries),
            total=total,
        )

        return PaginatedResponse(
            success=True,
            data=summaries,
            pagination=PaginationMeta(
                page=page,
                limit=page_size,
                total=total,
                total_pages=total_pages,
            ),
        )

    except Exception as e:
        logger.error(
            "Failed to fetch conversations",
            error=str(e),
            admin_user_id=context.user_id,
        )
        return PaginatedResponse(
            success=False,
            data=[],
            pagination=PaginationMeta(page=page, limit=page_size, total=0, total_pages=0),
        )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ApiResponse[ConversationDetail],
)
async def get_conversation_details(
    conversation_id: str = Path(..., description="Conversation identifier"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    conversation_repo: DynamoDBConversationRepository = Depends(get_conversation_repository),
) -> ApiResponse[ConversationDetail]:
    """
    Get detailed conversation history and metadata.

    This endpoint retrieves the complete conversation history including
    all messages, metadata, and usage statistics.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `conversation_id`: Unique conversation identifier

    **Returns:**
    - Complete conversation history
    - All messages with timestamps
    - Token usage and metadata
    """
    logger.info(
        "Fetching conversation details",
        conversation_id=conversation_id,
        admin_user_id=context.user_id,
    )

    try:
        # Fetch conversation
        from coaching.src.core.types import ConversationId
        conversation = await conversation_repo.get_by_id(ConversationId(conversation_id))

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation not found: {conversation_id}",
            )

        # Convert messages to response format
        messages = []
        total_tokens = 0

        for msg in conversation.messages:
            message = ConversationMessage(
                role=msg.role.value,
                content=msg.content,
                timestamp=msg.timestamp,
                tokensUsed=msg.tokens_used if hasattr(msg, "tokens_used") else None,
            )
            messages.append(message)

            if hasattr(msg, "tokens_used") and msg.tokens_used:
                total_tokens += msg.tokens_used

        # Build response
        detail = ConversationDetail(
            conversationId=conversation.conversation_id,
            tenantId=conversation.tenant_id,
            userId=conversation.user_id,
            topic="unknown",  # ConversationContext doesn't have topic attribute
            status=conversation.status.value,
            messages=messages,
            metadata={},  # ConversationContext doesn't have additional_context attribute
            createdAt=conversation.created_at,
            lastActivity=conversation.updated_at,
            totalTokens=total_tokens,
        )

        logger.info(
            "Conversation details retrieved",
            conversation_id=conversation_id,
            message_count=len(messages),
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=detail)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch conversation details",
            conversation_id=conversation_id,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to retrieve conversation details for: {conversation_id}",
        )


__all__ = ["router"]
