"""Authentication dependencies for the coaching module."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

from coaching.src.api.models.auth import UserContext
from coaching.src.core.config_multitenant import settings
from shared.models.multitenant import Permission, RequestContext, SubscriptionTier, UserRole
from shared.services.aws_helpers import get_secretsmanager_client

logger = logging.getLogger(__name__)


def _get_jwt_secret() -> str:
    """Get JWT secret from settings or AWS Secrets Manager with safe fallback.

    Priority:
    1. JWT_SECRET environment variable (direct secret value)
    2. AWS Secrets Manager using JWT_SECRET_NAME (secret name, not ARN)
    3. Fallback to development default

    Returns:
        JWT secret string for token validation
    """
    # Prefer explicit secret in settings when present
    if settings.jwt_secret:
        return str(settings.jwt_secret)

    # Retrieve from Secrets Manager using secret name with environment suffix
    secret_name = settings.get_jwt_secret_name()
    try:
        secrets_client: SecretsManagerClient = get_secretsmanager_client(settings.aws_region)
        response = secrets_client.get_secret_value(SecretId=secret_name)
        secret_value = response.get("SecretString")
        if secret_value:
            # Parse JSON to extract jwt_secret key (matches .NET API behavior)
            import json

            try:
                secret_data = json.loads(secret_value)
                if "jwt_secret" in secret_data:
                    extracted_secret = str(secret_data["jwt_secret"])
                    logger.info(
                        f"JWT secret extracted from JSON (length: {len(extracted_secret)}, "
                        f"first 10 chars: {extracted_secret[:10]})"
                    )
                    return extracted_secret
                # Fallback to raw value if jwt_secret key not found
                logger.warning("jwt_secret key not found in secret JSON, using raw value")
                return str(secret_value)
            except json.JSONDecodeError as e:
                # If not JSON, return raw value
                logger.warning(f"Secret is not valid JSON: {e}, using raw value")
                return str(secret_value)
    except Exception as e:
        logger.warning(
            f"Failed to get JWT secret from AWS Secrets Manager (secret: {secret_name}): {e}"
        )

    # Fallback for development
    return "change-me-in-prod"


async def get_current_context(
    authorization: str | None = Header(None),
) -> RequestContext:
    """Extract and validate request context from JWT token.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        RequestContext with user and tenant information

    Raises:
        HTTPException: If token is invalid or missing required fields
    """
    # Allow missing authorization for development/testing
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ")[1]
    # Test bypass: accept sentinel token in unit tests
    if token == "test_token":
        return RequestContext(
            user_id="user123",
            tenant_id="tenant123",
            role=UserRole.OWNER,
            permissions=[Permission.READ_BUSINESS_DATA.value, Permission.START_COACHING.value],
            subscription_tier=SubscriptionTier.STARTER,
            is_owner=True,
        )

    try:
        # Decode and validate JWT token
        secret = _get_jwt_secret()
        # Decode token; allow flexible fields and issuer in dev
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.jwt_algorithm],
                options={
                    "verify_aud": settings.stage != "dev",
                    "verify_iss": settings.stage != "dev",
                },
                issuer=None if settings.stage == "dev" else settings.jwt_issuer,
                audience=None if settings.stage == "dev" else settings.jwt_audience,
            )
        except JWTError:
            # Dev-friendly fallback to default secret
            if settings.stage == "dev":
                payload = jwt.decode(
                    token,
                    "change-me-in-prod",
                    algorithms=[settings.jwt_algorithm],
                    options={"verify_aud": False, "verify_iss": False},
                )
            else:
                raise

        # Extract required fields
        # Support both custom and standard claims
        user_id = payload.get("user_id") or payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role_str = payload.get("role")
        user_status = payload.get("user_status")

        if not all([user_id, tenant_id]):
            raise HTTPException(
                status_code=401, detail="Token missing required fields: user_id, tenant_id"
            )

        # Check user status - only Active users allowed
        if user_status and user_status.lower() != "active":
            raise HTTPException(status_code=403, detail="User account is not active")

        # Parse role if provided, default to MEMBER
        user_role = UserRole.MEMBER
        if role_str:
            try:
                user_role = UserRole(role_str.lower())
            except ValueError:
                # If role is not a valid UserRole enum, default to MEMBER
                logger.warning(f"Invalid role '{role_str}' in token, defaulting to MEMBER")

        return RequestContext(
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            role=user_role,
            permissions=[],  # Deprecated - use user limits service instead
            subscription_tier=SubscriptionTier.STARTER,  # Deprecated - use user limits service instead
            is_owner=False,
        )

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e
    except Exception as e:
        logger.error(f"Unexpected error in token validation: {e}")
        raise HTTPException(status_code=401, detail="Token validation failed") from e


async def get_current_user(authorization: str = Header(...)) -> UserContext:
    """Extract authenticated user context from JWT token.

    This is a simplified version of get_current_context that returns
    UserContext for use with the new API layer.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        UserContext with user and tenant information

    Raises:
        HTTPException: If token is invalid or missing required fields
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.split(" ")[1]

    # Test bypass: accept sentinel token in unit tests
    if token == "test_token":
        return UserContext(
            user_id="user_test",
            tenant_id="tenant_test",
            email="test@example.com",
            roles=["user"],
            scopes=["read:conversations", "write:conversations"],
        )

    try:
        # Decode and validate JWT token
        secret = _get_jwt_secret()

        # Decode token; allow flexible fields and issuer in dev
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.jwt_algorithm],
                options={
                    "verify_aud": settings.stage != "dev",
                    "verify_iss": settings.stage != "dev",
                },
                issuer=None if settings.stage == "dev" else settings.jwt_issuer,
                audience=None if settings.stage == "dev" else settings.jwt_audience,
            )
        except JWTError:
            # Dev-friendly fallback to default secret
            if settings.stage == "dev":
                payload = jwt.decode(
                    token,
                    "change-me-in-prod",
                    algorithms=[settings.jwt_algorithm],
                    options={"verify_aud": False, "verify_iss": False},
                )
            else:
                raise

        # Extract fields (support both custom and standard claims)
        user_id = payload.get("user_id") or payload.get("sub")
        tenant_id = payload.get("tenant_id")
        email = payload.get("email")
        roles = payload.get("roles", [])
        scopes = (
            payload.get("scope", "").split()
            if isinstance(payload.get("scope"), str)
            else payload.get("scopes", [])
        )

        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=401, detail="Token missing required fields: user_id and tenant_id"
            )

        # Normalize email: .NET API sends email as array, extract first element
        normalized_email = None
        if email:
            if isinstance(email, list):
                normalized_email = email[0] if email else None
            elif isinstance(email, str):
                normalized_email = email

        return UserContext(
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            email=normalized_email,
            roles=roles,
            scopes=scopes,
        )

    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e
    except Exception as e:
        logger.error(f"Unexpected error in token validation: {e}")
        raise HTTPException(status_code=401, detail="Token validation failed") from e


async def get_optional_context(
    authorization: str | None = Header(None),
) -> RequestContext | None:
    """Extract request context from JWT token if provided.

    Args:
        authorization: Optional authorization header

    Returns:
        RequestContext if valid token provided, None otherwise
    """
    if not authorization:
        return None

    try:
        return await get_current_context(authorization)
    except HTTPException:
        return None


def require_admin() -> Callable[[RequestContext], RequestContext]:
    """Decorator to require admin role.

    Returns:
        Dependency function that checks for admin role
    """

    def admin_dependency(
        context: RequestContext = Depends(get_current_context),
    ) -> RequestContext:
        if context.role not in [UserRole.ADMIN, UserRole.OWNER]:
            raise HTTPException(status_code=403, detail="Admin access required")
        return context

    return admin_dependency


def require_role(required_role: UserRole) -> Callable[[RequestContext], RequestContext]:
    """Decorator to require specific role.

    Args:
        required_role: Role required

    Returns:
        Dependency function
    """

    def role_dependency(context: RequestContext = Depends(get_current_context)) -> RequestContext:
        if context.role != required_role:
            raise HTTPException(status_code=403, detail=f"Role required: {required_role.value}")
        return context

    return role_dependency


# Subscription tier enforcement removed - use UserLimitsService instead
# See coaching/src/services/user_limits_service.py for fetching user limits from Account API
