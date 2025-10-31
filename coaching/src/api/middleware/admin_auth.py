"""Admin authentication and authorization middleware."""

import structlog
from fastapi import HTTPException, status

from shared.models.multitenant import RequestContext, UserRole

logger = structlog.get_logger()


def require_admin_access(context: RequestContext) -> RequestContext:
    """
    Verify that the current user has admin access.

    Args:
        context: Current request context with user and permissions

    Returns:
        RequestContext if admin access is granted

    Raises:
        HTTPException: 403 if user lacks admin permissions
    """
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
