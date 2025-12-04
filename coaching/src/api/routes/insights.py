"""Insights API routes - partially migrated to topic-driven architecture (Issue #113).

Migration Status:
- generate: Migrated to topic-driven (insights_generation topic)
- categories, priorities, dismiss, acknowledge: Not migrated (CRUD operations, not AI)
"""

from typing import cast

import structlog
from coaching.src.api.auth import get_current_context, get_current_user
from coaching.src.api.dependencies import get_insights_service
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.auth import UserContext
from coaching.src.models.responses import (
    InsightActionResponse,
    InsightResponse,
    InsightsSummaryResponse,
)
from coaching.src.services.insights_service import InsightsService
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse, PaginatedResponse

logger = structlog.get_logger()
router = APIRouter()


class InsightsGenerationRequest(BaseModel):
    """Request model for insights generation."""

    page: int = 1
    page_size: int = 20
    category: str | None = None
    priority: str | None = None
    status: str | None = None


@router.post("/generate", response_model=PaginatedResponse[InsightResponse])
async def generate_coaching_insights(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: str | None = Query(None, description="Filter by category"),
    priority: str | None = Query(None, description="Filter by priority"),
    status: str | None = Query(None, description="Filter by status"),
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> PaginatedResponse[InsightResponse]:
    """Generate fresh coaching insights using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'insights_generation' topic for consistent prompt management.

    This endpoint generates NEW insights from real-time business data.
    """
    logger.info(
        "Generating coaching insights",
        user_id=user.user_id,
        page=page,
        page_size=page_size,
        category=category,
        priority=priority,
        status=status,
    )

    # Create request model from query parameters
    request = InsightsGenerationRequest(
        page=page, page_size=page_size, category=category, priority=priority, status=status
    )

    result = await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/insights/generate",
        request_body=request,
        user_context=user,
        response_model=PaginatedResponse[InsightResponse],
    )
    return cast(PaginatedResponse[InsightResponse], result)


@router.get("/categories", response_model=ApiResponse[list[str]])
async def get_insight_categories(
    _context: RequestContext = Depends(get_current_context),
    service: InsightsService = Depends(get_insights_service),
) -> ApiResponse[list[str]]:
    """Get available insight categories."""
    try:
        categories = await service.get_categories()
        return ApiResponse(success=True, data=categories)
    except Exception as e:
        logger.error(f"Error getting insight categories: {e}")
        return ApiResponse(success=False, error="Failed to retrieve categories", data=[])


@router.get("/priorities", response_model=ApiResponse[list[str]])
async def get_insight_priorities(
    _context: RequestContext = Depends(get_current_context),
    service: InsightsService = Depends(get_insights_service),
) -> ApiResponse[list[str]]:
    """Get available insight priorities."""
    try:
        priorities = await service.get_priorities()
        return ApiResponse(success=True, data=priorities)
    except Exception as e:
        logger.error(f"Error getting insight priorities: {e}")
        return ApiResponse(success=False, error="Failed to retrieve priorities", data=[])


@router.post("/{insight_id}/dismiss", response_model=ApiResponse[InsightActionResponse])
async def dismiss_insight(
    insight_id: str,
    context: RequestContext = Depends(get_current_context),
    service: InsightsService = Depends(get_insights_service),
) -> ApiResponse[InsightActionResponse]:
    """Dismiss an insight (mark as not relevant)."""
    logger.info(
        "Dismissing insight",
        insight_id=insight_id,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    try:
        await service.dismiss_insight(insight_id, context.user_id)

        action_response = InsightActionResponse(insight_id=insight_id, status="dismissed")
        return ApiResponse(
            success=True,
            data=action_response,
            message="Insight dismissed successfully",
        )

    except Exception as e:
        logger.error(f"Error dismissing insight: {e}")
        return ApiResponse(success=False, error="Failed to dismiss insight")


@router.post("/{insight_id}/acknowledge", response_model=ApiResponse[InsightActionResponse])
async def acknowledge_insight(
    insight_id: str,
    context: RequestContext = Depends(get_current_context),
    service: InsightsService = Depends(get_insights_service),
) -> ApiResponse[InsightActionResponse]:
    """Acknowledge an insight (mark as reviewed)."""
    logger.info(
        "Acknowledging insight",
        insight_id=insight_id,
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    try:
        await service.acknowledge_insight(insight_id, context.user_id)

        action_response = InsightActionResponse(insight_id=insight_id, status="acknowledged")
        return ApiResponse(
            success=True,
            data=action_response,
            message="Insight acknowledged successfully",
        )

    except Exception as e:
        logger.error(f"Error acknowledging insight: {e}")
        return ApiResponse(success=False, error="Failed to acknowledge insight")


@router.get("/summary", response_model=ApiResponse[InsightsSummaryResponse])
async def get_insights_summary(
    context: RequestContext = Depends(get_current_context),
    service: InsightsService = Depends(get_insights_service),
) -> ApiResponse[InsightsSummaryResponse]:
    """Get insights summary with counts by category and priority."""
    logger.info("Fetching insights summary", user_id=context.user_id, tenant_id=context.tenant_id)

    try:
        summary = await service.get_insights_summary(context.user_id)

        return ApiResponse(success=True, data=summary)

    except Exception as e:
        logger.error(f"Error getting insights summary: {e}")
        return ApiResponse(success=False, error="Failed to retrieve insights summary")
