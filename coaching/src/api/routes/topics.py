"""Topics API routes.

================================================================================
DEPRECATED - This entire file is dead code.
================================================================================
Migration: Topic listing superseded by:
- GET /ai/topics (ai_execute.py) for single-shot topics
- GET /ai/coaching/topics (coaching_sessions.py) for coaching topics
Usage: No frontend callers exist.
Status: Safe to remove.
================================================================================
"""

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_topic_repository
from coaching.src.models.topics import AvailableTopic
from coaching.src.repositories.topic_repository import TopicRepository
from fastapi import APIRouter, Depends, HTTPException
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/available", response_model=ApiResponse[list[AvailableTopic]])
async def list_available_topics(
    context: RequestContext = Depends(get_current_context),
    topic_repository: TopicRepository = Depends(get_topic_repository),
) -> ApiResponse[list[AvailableTopic]]:
    try:
        topics = await topic_repository.list_by_type(
            topic_type="conversation_coaching",
            include_inactive=False,
        )

        available = [
            AvailableTopic(
                id=topic.topic_id,
                name=topic.topic_name,
                category=topic.category,
                description=topic.description,
                displayOrder=topic.display_order,
                createdAt=topic.created_at,
                updatedAt=topic.updated_at,
            )
            for topic in sorted(topics, key=lambda t: t.display_order)
        ]

        return ApiResponse(success=True, data=available)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to list available topics",
            error=str(exc),
            tenant_id=context.tenant_id,
            user_id=context.user_id,
        )
        raise HTTPException(status_code=500, detail="Failed to list available topics") from exc


__all__ = ["router"]
