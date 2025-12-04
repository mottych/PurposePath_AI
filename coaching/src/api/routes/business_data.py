"""Business data and metrics API routes (Issue #65)."""

from typing import Any, Generic, TypeVar, cast

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.auth import UserContext
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["business-data"])

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""

    success: bool
    data: T


class BusinessMetricsRequest(BaseModel):
    """Request model for business metrics (empty for GET)."""

    pass


class BusinessMetricsResponse(BaseModel):
    """Business metrics response."""

    tenant_id: str
    business_data: dict[str, Any]


@router.get(
    "/business-data",
    response_model=ApiResponse[BusinessMetricsResponse],
    status_code=status.HTTP_200_OK,
)
async def get_business_data_summary(
    context: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> ApiResponse[BusinessMetricsResponse]:
    """Get current business data summary for the tenant.

    Migrated to unified topic-driven architecture.
    Uses 'business_metrics' topic.
    """
    logger.info("business_data.fetch.started", user_id=context.user_id, tenant_id=context.tenant_id)

    try:
        # Create empty request for GET
        request = BusinessMetricsRequest()

        result = await handler.handle_single_shot(
            http_method="GET",
            endpoint_path="/multitenant/conversations/business-data",
            request_body=request,
            user_context=context,
            response_model=BusinessMetricsResponse,
        )

        logger.info(
            "business_data.fetch.completed", user_id=context.user_id, tenant_id=context.tenant_id
        )
        return ApiResponse(success=True, data=cast(BusinessMetricsResponse, result))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "business_data.fetch.failed",
            error=str(e),
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve business data summary",
        ) from e


__all__ = ["router"]
