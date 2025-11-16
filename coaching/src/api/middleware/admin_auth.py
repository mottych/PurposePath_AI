"""Admin authentication and authorization middleware."""

import structlog
from coaching.src.api.auth import get_current_context
from fastapi import Depends, HTTPException, Request, status

from shared.models.multitenant import RequestContext, UserRole

logger = structlog.get_logger()


def require_admin_access(
    request: Request,
    context: RequestContext = Depends(get_current_context),
) -> RequestContext:
    """
    Verify that the current user has admin access.

    For OPTIONS requests (CORS preflight), allows the request to proceed without validation.

    Args:
        request: FastAPI request object (to check HTTP method)
        context: Current request context with user and permissions

    Returns:
        RequestContext if admin access is granted

    Raises:
        HTTPException: 403 if user lacks admin permissions
    """
    # Allow OPTIONS requests without admin check (CORS preflight)
    if request.method == "OPTIONS":
        return context

    if context.role not in [UserRole.ADMIN, UserRole.OWNER]:
        logger.warning(
            "Admin access denied",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            role=context.role,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This operation requires administrative privileges.",
        )

    logger.debug(
        "Admin access granted",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
    )

    return context


__all__ = ["require_admin_access"]
