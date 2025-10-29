"""Business data and metrics API routes (Issue #65)."""

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.models.auth import Permission, RequestContext
from coaching.src.models.responses import ApiResponse, BusinessDataSummaryResponse
from coaching.src.services.multitenant_conversation_service import (
    MultitenantConversationService,
    get_multitenant_conversation_service,
)
from fastapi import APIRouter, Depends, HTTPException, status

logger = structlog.get_logger(__name__)
router = APIRouter(tags=["business-data"])


@router.get(
    "/business-data",
    response_model=ApiResponse[BusinessDataSummaryResponse],
    status_code=status.HTTP_200_OK,
)
async def get_business_data_summary(
    context: RequestContext = Depends(get_current_context),
    service: MultitenantConversationService = Depends(get_multitenant_conversation_service),
) -> ApiResponse[BusinessDataSummaryResponse]:
    """Get current business data summary for the tenant."""
    logger.info("business_data.fetch.started", user_id=context.user_id, tenant_id=context.tenant_id)

    try:
        if Permission.READ_BUSINESS_DATA.value not in (context.permissions or []):
            logger.warning(
                "business_data.permission_denied",
                user_id=context.user_id,
                tenant_id=context.tenant_id,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission required to read business data",
            )

        summary = service.get_business_data_summary()
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
