"""
Canonical data models for multitenant API standardization.
All models use snake_case fields and ISO 8601 datetime strings.
"""

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer

# Generic type for ApiResponse
T = TypeVar("T")


class BaseModelWithDatetime(BaseModel):
    """Base model with datetime serialization for all datetime fields."""

    @field_serializer("*", when_used="json")
    def serialize_datetime(self, value: Any) -> Any:
        """Serialize datetime objects to ISO format strings."""
        if isinstance(value, datetime):
            return value.isoformat() if value else None
        return value


class ApiResponse(BaseModelWithDatetime, Generic[T]):
    """Standard API response envelope for all endpoints."""

    success: bool
    data: T | None = None
    message: str | None = None
    error: str | None = None


class PaginationMeta(BaseModelWithDatetime):
    """Pagination metadata for list responses."""

    page: int
    limit: int
    total: int
    total_pages: int = Field(alias="total_pages")

    model_config = ConfigDict(
        populate_by_name=True,
    )


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response envelope."""

    success: bool
    data: list[T]
    pagination: PaginationMeta
    message: str | None = None
    error: str | None = None

    model_config = ConfigDict(
        populate_by_name=True,
    )


class UserProfile(BaseModelWithDatetime):
    """User profile with standardized fields."""

    user_id: str = Field(alias="userId")
    tenant_id: str = Field(alias="tenantId")
    email: str
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    role: str | None = None
    status: str = "active"
    email_verified: bool = Field(default=False, alias="emailVerified")
    avatar_url: str | None = Field(default=None, alias="avatarUrl")
    phone: str | None = None
    timezone: str = "UTC"
    language: str = "en"
    preferences: dict[str, Any] = Field(default_factory=dict)
    last_login: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        # Pydantic V2: datetime serialization handled automatically
    )


class TenantInfo(BaseModelWithDatetime):
    """Tenant information model."""

    tenant_id: str
    name: str
    status: str
    subscription_tier: str | None = None

    model_config = ConfigDict(
        # Pydantic V2: datetime serialization handled automatically
    )


class AuthResponse(BaseModelWithDatetime):
    """Authentication response with tokens and user profile."""

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    user: UserProfile
    tenant: TenantInfo | None = None

    model_config = ConfigDict(
        populate_by_name=True,
    )


class RegistrationVerificationPending(BaseModelWithDatetime):
    """Response when email verification is required after registration."""

    requires_email_verification: bool = Field(alias="requiresEmailVerification")
    tenant_id: str | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        # Pydantic V2: datetime serialization handled automatically
    )


class UpdateUserProfileRequest(BaseModelWithDatetime):
    """Request model for updating user profile."""

    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    preferences: dict[str, Any] | None = None


class UpdateSubscriptionRequest(BaseModelWithDatetime):
    """Request model for updating subscription."""

    plan: Literal["monthly", "yearly"] | None = None
    tier: Literal["starter", "professional", "enterprise"] | None = None


class LoginRequest(BaseModelWithDatetime):
    """Login request model."""

    email: str
    password: str
    tenant_id: str | None = None


class RegisterRequest(BaseModelWithDatetime):
    """Registration request model with split names."""

    email: str
    password: str
    first_name: str
    last_name: str
    tenant_name: str | None = None
    invite_token: str | None = None
    role: Literal["owner", "admin", "manager", "member", "viewer"] | None = None


class RefreshTokenRequest(BaseModelWithDatetime):
    """Refresh token request model."""

    refresh_token: str


class ForgotPasswordRequest(BaseModelWithDatetime):
    """Forgot password request model."""

    email: str


class ResetPasswordRequest(BaseModelWithDatetime):
    """Reset password request model."""

    token: str
    new_password: str


class ConfirmEmailRequest(BaseModelWithDatetime):
    """Email confirmation request model."""

    token: str


class GoogleAuthRequest(BaseModelWithDatetime):
    """Google OAuth request model."""

    token: str
    tenant_id: str | None = None
