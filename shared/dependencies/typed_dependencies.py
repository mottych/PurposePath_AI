"""Typed wrapper functions for common FastAPI dependency injection patterns.

Provides strongly-typed, reusable dependency functions that eliminate
the need for dict[str, Any] types in route handlers.

Note: This file previously contained traction service dependencies which have been
removed as traction is a .NET project, not part of the Python workspace.
"""

from typing import Any

from fastapi import HTTPException, status

from shared.types import TenantId, UserId
from shared.types.common import JSONDict


class TypedRequestContext:
    """Strongly-typed request context for dependency injection"""

    def __init__(self, user_id: UserId, tenant_id: TenantId, role: str, permissions: list[str]):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.role = role
        self.permissions = permissions


class PermissionChecker:
    """Type-safe permission checking for route handlers"""

    @staticmethod
    def require_owner_or_admin(context: TypedRequestContext) -> None:
        """Require owner or admin role"""
        if context.role not in ["owner", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Owner or admin role required"
            )

    @staticmethod
    def require_manager_or_above(context: TypedRequestContext) -> None:
        """Require manager role or above"""
        if context.role not in ["owner", "admin", "manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Manager role or above required"
            )

    @staticmethod
    def has_permission(context: TypedRequestContext, permission: str) -> bool:
        """Check if context has specific permission"""
        return permission in context.permissions


def validate_request_body(body: JSONDict, required_fields: list[str]) -> None:
    """Validate request body has required fields"""
    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required fields: {', '.join(missing_fields)}",
        )


class TypedResponseBuilder:
    """Helper for building typed API responses"""

    @staticmethod
    def success(data: Any, message: str | None = None) -> dict[str, Any]:
        """Build success response"""
        return {"success": True, "data": data, "message": message}

    @staticmethod
    def error(message: str, error_code: str | None = None) -> dict[str, Any]:
        """Build error response"""
        return {"success": False, "error": message, "error_code": error_code}
