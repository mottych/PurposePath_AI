"""
Canonical data models for multitenant API standardization.
All models use snake_case fields and ISO 8601 datetime strings.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer

if TYPE_CHECKING:
    pass  # Forward references will be resolved at runtime
import uuid
from enum import Enum

# Generic type for ApiResponse
T = TypeVar("T")


class BaseModelWithDatetime(BaseModel):
    """Base model with datetime serialization for all datetime fields."""

    @field_serializer("*", when_used="json", check_fields=False)
    def serialize_datetime(self, value: Any) -> Any:
        """Serialize datetime objects to ISO format strings."""
        if isinstance(value, datetime):
            return value.isoformat() if value else None
        return value


class ErrorCode(str, Enum):
    """Standardized error codes for all API responses."""

    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    TOKEN_MISSING = "TOKEN_MISSING"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"

    # Resource errors
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Business logic errors
    SUBSCRIPTION_REQUIRED = "SUBSCRIPTION_REQUIRED"
    SUBSCRIPTION_EXPIRED = "SUBSCRIPTION_EXPIRED"
    SUBSCRIPTION_NOT_FOUND = "SUBSCRIPTION_NOT_FOUND"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    QUOTA_EXCEEDED = "QUOTA_EXCEEDED"

    # Account and user errors
    EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    INVALID_EMAIL_FORMAT = "INVALID_EMAIL_FORMAT"
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    ACCOUNT_INACTIVE = "ACCOUNT_INACTIVE"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"

    # Tenant errors
    TENANT_NOT_FOUND = "TENANT_NOT_FOUND"
    TENANT_INACTIVE = "TENANT_INACTIVE"
    TENANT_LIMIT_EXCEEDED = "TENANT_LIMIT_EXCEEDED"

    # Payment and billing errors
    PAYMENT_REQUIRED = "PAYMENT_REQUIRED"
    BILLING_PORTAL_ERROR = "BILLING_PORTAL_ERROR"

    # Input validation errors
    INVALID_INPUT = "INVALID_INPUT"
    INVALID_DATA_FORMAT = "INVALID_DATA_FORMAT"

    # External service errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    GOOGLE_AUTH_ERROR = "GOOGLE_AUTH_ERROR"
    STRIPE_ERROR = "STRIPE_ERROR"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Server errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"


class ApiResponse(BaseModelWithDatetime, Generic[T]):
    """Standard API response envelope for all endpoints."""

    success: bool
    data: T | None = None
    message: str | None = None
    error: str | None = None
    error_code: ErrorCode | None = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def success_response(cls, data: T | None = None, message: str | None = None) -> ApiResponse[T]:
        """Create a successful response."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error_response(
        cls, error_message: str, error_code: ErrorCode | None = None
    ) -> ApiResponse[None]:
        """Create an error response."""
        return ApiResponse[None](
            success=False, data=None, error=error_message, error_code=error_code
        )


class PaginationMeta(BaseModelWithDatetime):
    """Pagination metadata for list responses."""

    page: int
    limit: int
    total: int
    total_pages: int = Field(alias="total_pages")

    model_config = ConfigDict(
        populate_by_name=True,
    )


class PaginatedResponse(BaseModelWithDatetime, Generic[T]):
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
    """Canonical user profile model with snake_case fields."""

    user_id: str
    tenant_id: str
    email: str
    first_name: str
    last_name: str
    role: Literal["owner", "admin", "manager", "member", "viewer"]
    status: Literal["active", "inactive", "pending", "disabled"]
    email_verified: bool
    avatar_url: str | None = None
    phone: str | None = None
    timezone: str = "UTC"
    language: str = "en"
    preferences: dict[str, Any] = Field(default_factory=dict)
    last_login: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserReference(BaseModelWithDatetime):
    """Minimal user reference for lists and references."""

    user_id: str
    first_name: str
    last_name: str
    email: str
    avatar_url: str | None = None
    role: Literal["owner", "admin", "manager", "member", "viewer"]
    status: Literal["active", "inactive", "pending", "disabled"]


class TenantInfo(BaseModelWithDatetime):
    """Tenant information model with subscription details."""

    tenant_id: str
    name: str
    status: str
    subscription_tier: str | None = None
    subscription_status: str | None = None
    trial_ends_at: datetime | None = None
    owner_user_id: str | None = None
    created_at: datetime | None = None


class AuthResponse(BaseModelWithDatetime):
    """Authentication response with tokens and user profile.
    Uses snake_case keys to match API spec.
    """

    access_token: str
    refresh_token: str
    user: UserProfile
    tenant: TenantInfo | None = None


class RegistrationVerificationPending(BaseModelWithDatetime):
    """Response when email verification is required after registration.
    Uses snake_case keys to match API spec.
    """

    requires_email_verification: bool
    tenant_id: str | None = None

    model_config = ConfigDict()


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


# Enhanced business domain models
class NotificationSettings(BaseModelWithDatetime):
    """User notification preferences."""

    email: bool = True
    push: bool = True
    sms: bool = False
    marketing: bool = False

    model_config = ConfigDict()


class EnhancedUserPreferences(BaseModelWithDatetime):
    """Enhanced user preferences with comprehensive settings."""

    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    timezone: str = "America/New_York"
    language: str = "en"
    theme: Literal["light", "dark", "auto"] = "light"
    date_format: str = "MM/DD/YYYY"
    time_format: Literal["12h", "24h"] = "12h"
    currency: str = "USD"

    model_config = ConfigDict()


class PaymentMethod(BaseModelWithDatetime):
    """Payment method information."""

    id: str
    type: Literal["card", "google_pay", "apple_pay", "bank_account"]
    last4: str | None = None
    brand: str | None = None
    expiry_month: int | None = None
    expiry_year: int | None = None
    is_default: bool = True
    created_at: datetime

    model_config = ConfigDict()


class Subscription(BaseModelWithDatetime):
    """User subscription information with comprehensive details."""

    id: str
    user_id: str
    tenant_id: str
    plan: Literal["monthly", "yearly"]
    tier: Literal["starter", "professional", "enterprise"] = "starter"
    status: Literal["active", "cancelled", "past_due", "trialing", "unpaid"] = "active"
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    cancelled_at: datetime | None = None
    trial_start: datetime | None = None
    trial_end: datetime | None = None
    price: float
    currency: str = "USD"
    payment_method: PaymentMethod | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict()


class Address(BaseModelWithDatetime):
    """Business address information."""

    street: str
    city: str
    state: str
    zip_code: str = Field(alias="zip")
    country: str = "US"

    model_config = ConfigDict(
        populate_by_name=True,
    )


class Product(BaseModelWithDatetime):
    """Business product/service information."""

    id: str | None = None
    name: str
    description: str | None = None
    problem: str
    target_market: str | None = None
    price_point: float | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict()


class OnboardingStep3(BaseModelWithDatetime):
    """Onboarding step 3: Business positioning."""

    niche: str | None = None
    ica: str | None = None  # Ideal Customer Avatar
    value_proposition: str | None = Field(alias="valueProposition", default=None)
    competitive_advantage: str | None = None
    market_size: str | None = None

    model_config = ConfigDict(
        populate_by_name=True,
    )


class OnboardingStep4(BaseModelWithDatetime):
    """Onboarding step 4: Core business values and vision."""

    core_values: list[str] = Field(alias="coreValues", default_factory=list)
    core_values_status: Literal["Not started", "In progress", "Completed"] = Field(
        alias="coreValuesStatus", default="Not started"
    )
    purpose: str | None = None
    purpose_status: Literal["Not started", "In progress", "Completed"] = Field(
        alias="purposeStatus", default="Not started"
    )
    vision: str | None = None
    vision_status: Literal["Not started", "In progress", "Completed"] = Field(
        alias="visionStatus", default="Not started"
    )
    mission: str | None = None
    mission_status: Literal["Not started", "In progress", "Completed"] = Field(
        alias="missionStatus", default="Not started"
    )

    model_config = ConfigDict(
        populate_by_name=True,
    )


class OnboardingData(BaseModelWithDatetime):
    """Comprehensive business onboarding data."""

    id: str | None = None
    user_id: str
    tenant_id: str
    business_name: str | None = Field(alias="businessName", default=None)
    website: str | None = None
    industry: str | None = None
    business_type: Literal["LLC", "Corporation", "Partnership", "Sole Proprietorship"] | None = None
    employee_count: Literal["1", "2-10", "11-50", "51-200", "200+"] | None = None
    address: Address | None = None
    products: list[Product] = Field(default_factory=list)
    step3: OnboardingStep3 | None = None
    step4: OnboardingStep4 | None = None
    completed_steps: list[int] = Field(default_factory=list)
    is_completed: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        populate_by_name=True,
    )


# Rebuild models to resolve forward references
OnboardingData.model_rebuild()


class BillingPortalRequest(BaseModelWithDatetime):
    """Request model for billing portal access."""

    return_url: str | None = None

    model_config = ConfigDict()


class BillingPortalResponse(BaseModelWithDatetime):
    """Response model for billing portal URL."""

    url: str
    expires_at: datetime

    model_config = ConfigDict()


class UserLimitsResponse(BaseModelWithDatetime):
    """Response model for user subscription limits."""

    subscription_tier: str
    limits: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    reset_date: datetime | None = None

    model_config = ConfigDict()


# Request models for API endpoints
class CreateProductRequest(BaseModelWithDatetime):
    """Request model for creating a new product."""

    name: str
    description: str | None = None
    problem: str
    target_market: str | None = None
    price_point: float | None = None


class UpdateProductRequest(BaseModelWithDatetime):
    """Request model for updating an existing product."""

    name: str | None = None
    description: str | None = None
    problem: str | None = None
    target_market: str | None = None
    price_point: float | None = None


class UpdateOnboardingRequest(BaseModelWithDatetime):
    """Request model for updating onboarding data."""

    business_name: str | None = Field(alias="businessName", default=None)
    website: str | None = None
    industry: str | None = None
    business_type: Literal["LLC", "Corporation", "Partnership", "Sole Proprietorship"] | None = None
    employee_count: Literal["1", "2-10", "11-50", "51-200", "200+"] | None = None
    address: Address | None = None
    step3: OnboardingStep3 | None = None
    step4: OnboardingStep4 | None = None

    model_config = ConfigDict(
        populate_by_name=True,
    )
