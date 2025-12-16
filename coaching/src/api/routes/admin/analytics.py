"""Admin API routes for usage analytics and template testing.

Endpoint Usage Status:
- GET /usage: DEPRECATED - not called by Admin UI
- GET /models/{model_id}/metrics: DEPRECATED - not called by Admin UI

Note: LLM dashboard metrics come from /topics/stats endpoint in admin/topics.py
"""

from datetime import datetime

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import (
    get_conversation_repository,
)
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.infrastructure.repositories.dynamodb_conversation_repository import (
    DynamoDBConversationRepository,
)
from coaching.src.services.usage_analytics_service import (
    ModelUsageMetrics,
    UsageAnalyticsService,
    UsageMetrics,
)
from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


class UsageQueryParams(BaseModel):
    """Query parameters for usage analytics."""

    tenant_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    model_id: str | None = None
    topic: str | None = None


@router.get("/usage", response_model=ApiResponse[UsageMetrics])
async def get_usage_analytics(
    tenant_id: str | None = Query(None, description="Filter by tenant ID"),
    start_date: datetime | None = Query(None, description="Start date (ISO 8601)"),
    end_date: datetime | None = Query(None, description="End date (ISO 8601)"),
    model_id: str | None = Query(None, description="Filter by model ID"),
    topic: str | None = Query(None, description="Filter by coaching topic"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    conversation_repo: DynamoDBConversationRepository = Depends(get_conversation_repository),
) -> ApiResponse[UsageMetrics]:
    """
    Get aggregated LLM usage analytics.

    This endpoint provides comprehensive usage statistics including
    token consumption, costs, and request volumes with flexible filtering.

    **Permissions Required:** ADMIN_ACCESS

    **Query Parameters:**
    - `tenant_id` (optional) - Filter by specific tenant
    - `start_date` (optional) - Start of date range (ISO 8601)
    - `end_date` (optional) - End of date range (ISO 8601)
    - `model_id` (optional) - Filter by specific model
    - `topic` (optional) - Filter by coaching topic

    **Returns:**
    - Total requests, tokens (input/output/total), costs
    - Averages per request
    - Aggregated across all filters

    **Example:**
    ```
    GET /api/v1/admin/usage?start_date=2025-10-01T00:00:00Z&end_date=2025-10-31T23:59:59Z
    ```
    """
    logger.info(
        "Getting usage analytics",
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        admin_user_id=context.user_id,
    )

    try:
        # Create analytics service
        analytics_service = UsageAnalyticsService(conversation_repo)

        # Get metrics
        metrics = await analytics_service.get_usage_metrics(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            model_id=model_id,
            topic=topic,
        )

        logger.info(
            "Usage analytics retrieved",
            total_requests=metrics.total_requests,
            total_cost=metrics.total_cost,
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=metrics)

    except Exception as e:
        logger.error(
            "Failed to retrieve usage analytics",
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to retrieve usage analytics: {e!s}",
        )


@router.get("/models/{model_id}/metrics", response_model=ApiResponse[ModelUsageMetrics])
async def get_model_metrics(
    model_id: str = Path(..., description="Model identifier"),
    tenant_id: str | None = Query(None, description="Filter by tenant ID"),
    start_date: datetime | None = Query(None, description="Start date (ISO 8601)"),
    end_date: datetime | None = Query(None, description="End date (ISO 8601)"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    conversation_repo: DynamoDBConversationRepository = Depends(get_conversation_repository),
) -> ApiResponse[ModelUsageMetrics]:
    """
    Get usage metrics for a specific AI model.

    This endpoint provides detailed usage statistics for a particular
    model including request volume, token consumption, and costs.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `model_id`: Unique model identifier

    **Query Parameters:**
    - `tenant_id` (optional) - Filter by specific tenant
    - `start_date` (optional) - Start of date range
    - `end_date` (optional) - End of date range

    **Returns:**
    - Model-specific usage metrics
    - Request volume and trends
    - Token usage breakdown
    - Cost analysis

    **Example:**
    ```
    GET /api/v1/admin/models/anthropic.claude-3-5-sonnet-20241022-v2:0/metrics
    ```
    """
    logger.info(
        "Getting model metrics",
        model_id=model_id,
        tenant_id=tenant_id,
        admin_user_id=context.user_id,
    )

    try:
        # Create analytics service
        analytics_service = UsageAnalyticsService(conversation_repo)

        # Get model metrics
        metrics = await analytics_service.get_model_metrics(
            model_id=model_id,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )

        logger.info(
            "Model metrics retrieved",
            model_id=model_id,
            total_requests=metrics.total_requests,
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=metrics)

    except Exception as e:
        logger.error(
            "Failed to get model metrics",
            model_id=model_id,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to retrieve model metrics: {e!s}",
        )


__all__ = ["router"]
