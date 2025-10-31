"""Business data and metrics API routes (Issue #65)."""

from typing import Any, Generic, TypeVar

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.api.models.auth import UserContext

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["business-data"])

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response wrapper."""
    success: bool
    data: T


class BusinessDataSummaryResponse(BaseModel):
    """Business data summary response."""
    tenant_id: str
    business_data: dict[str, Any]


@router.get(
    "/business-data",
    response_model=ApiResponse[BusinessDataSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_business_data_summary(
    context: UserContext = Depends(get_current_user),
) -> ApiResponse[BusinessDataSummaryResponse]:
    """Get current business data summary for the tenant."""
    logger.info("business_data.fetch.started", user_id=context.user_id, tenant_id=context.tenant_id)

    try:
        # Placeholder - return empty business data for now
        summary: dict[str, Any] = {}
        business_summary = BusinessDataSummaryResponse(
            tenant_id=context.tenant_id, business_data=dict(summary)
        )
        logger.info(
            "business_data.fetch.completed", user_id=context.user_id, tenant_id=context.tenant_id
        )
        return ApiResponse(success=True, data=business_summary)

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
