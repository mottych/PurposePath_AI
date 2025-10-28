"""Insights API routes for coaching recommendations and analytics."""

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_insights_service
from coaching.src.models.responses import (
    InsightActionResponse,
    InsightResponse,
    InsightsSummaryResponse,
)
from coaching.src.services.insights_service import InsightsService
from fastapi import APIRouter, Depends, HTTPException, Query

from shared.models.multitenant import Permission, RequestContext
from shared.models.schemas import ApiResponse, PaginatedResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post("/generate", response_model=PaginatedResponse[InsightResponse])
async def generate_coaching_insights(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: str | None = Query(None, description="Filter by category"),
    priority: str | None = Query(None, description="Filter by priority"),
    status: str | None = Query(None, description="Filter by status"),
    context: RequestContext = Depends(get_current_context),
    service: InsightsService = Depends(get_insights_service),
) -> PaginatedResponse[InsightResponse]:
    """Generate fresh coaching insights using AI/LLM.

    This endpoint generates NEW insights from real-time business data.
    The frontend should persist results via .NET backend.
    For viewing persisted insights, call .NET API directly.
    """
    logger.info(
        "Generating coaching insights",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        page=page,
        page_size=page_size,
        category=category,
        priority=priority,
        status=status,
    )

    try:
        # Check permission to generate insights
        if Permission.READ_BUSINESS_DATA not in context.permissions:
            raise HTTPException(
                status_code=403, detail="Permission required to generate coaching insights"
            )

        response = await service.generate_insights(
            page=page,
            page_size=page_size,
            category=category,
            priority=priority,
            status=status,
        )

        return response

    except Exception as e:
        logger.error("Error retrieving insights", user_id=context.user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve insights") from e


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
