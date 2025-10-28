"""Shared multitenant data models for PurposePath."""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TenantStatus(str, Enum):
    """Status of a tenant."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    """User roles within a tenant."""

    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    """Status of a user."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class InvitationStatus(str, Enum):
    """Status of an invitation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SubscriptionTier(str, Enum):
    """Available subscription tiers."""

    TRIAL = "trial"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class CoachingTopic(str, Enum):
    """Available coaching topics."""

    CORE_VALUES = "core_values"
    PURPOSE = "purpose"
    VISION = "vision"
    GOALS = "goals"


class Permission(str, Enum):
    """Available permissions for multitenant access control."""

    START_COACHING = "start_coaching"
    VIEW_ALL_SESSIONS = "view_all_sessions"
    READ_BUSINESS_DATA = "read_business_data"
    WRITE_BUSINESS_DATA = "write_business_data"
    MANAGE_USERS = "manage_users"
    ADMIN_ACCESS = "admin_access"


# Base Models with Common Fields


class TimestampMixin(BaseModel):
    """Mixin for common timestamp fields."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TenantScopedMixin(BaseModel):
    """Mixin for tenant-scoped entities."""

    tenant_id: str = Field(..., description="Unique identifier for the tenant")


# Core Entity Models


class Tenant(TimestampMixin):
    """Tenant entity representing an organization."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: str = Field(default_factory=lambda: f"tenant_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., min_length=1, max_length=100, description="Organization name")
    domain: str | None = Field(None, max_length=100, description="Organization domain")
    owner_user_id: str = Field(..., description="User ID of the tenant owner")
    status: TenantStatus = Field(default=TenantStatus.TRIAL)
    settings: dict[str, Any] = Field(default_factory=dict, description="Tenant-specific settings")

    # Metadata
    industry: str | None = Field(None, max_length=100)
    company_size: str | None = Field(None)
    timezone: str = Field(default="UTC")


class User(TimestampMixin, TenantScopedMixin):
    """User entity with tenant association."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: str = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: UserRole = Field(default=UserRole.MEMBER)
    status: UserStatus = Field(default=UserStatus.PENDING)

    # Authentication fields
    password_hash: str | None = Field(None, description="Hashed password")
    email_verified: bool = Field(default=False)
    last_login: datetime | None = Field(None)

    # Profile information
    avatar_url: str | None = Field(None)
    phone: str | None = Field(None)
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")

    # User preferences and settings
    preferences: dict[str, Any] = Field(
        default_factory=dict, description="User-specific preferences and settings"
    )

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}"


class Subscription(TimestampMixin, TenantScopedMixin):
    """Subscription entity managing tenant billing and limits."""

    model_config = ConfigDict(from_attributes=True)

    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    tier: SubscriptionTier = Field(default=SubscriptionTier.STARTER)
    status: str = Field(default="active")  # active, cancelled, past_due, etc.

    # Billing information
    billing_cycle: str = Field(default="monthly")  # monthly, yearly
    amount: int = Field(default=0, description="Amount in cents")
    currency: str = Field(default="USD")

    # Subscription dates
    trial_ends_at: datetime | None = Field(None)
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(UTC))
    current_period_end: datetime = Field(default_factory=lambda: datetime.now(UTC))
    cancelled_at: datetime | None = Field(None)

    # Usage limits and tracking
    limits: dict[str, int] = Field(
        default_factory=dict, description="Subscription limits (max_users, max_sessions, etc.)"
    )
    usage: dict[str, int] = Field(default_factory=dict, description="Current usage tracking")

    # External billing system integration
    external_subscription_id: str | None = Field(None, description="ID from billing provider")


class Invitation(TimestampMixin, TenantScopedMixin):
    """Invitation entity for user onboarding."""

    model_config = ConfigDict(from_attributes=True)

    invitation_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    email: str = Field(..., description="Email address of invitee")
    invited_by_user_id: str = Field(..., description="User who sent the invitation")
    role: UserRole = Field(default=UserRole.MEMBER, description="Assigned role for invitee")
    status: InvitationStatus = Field(default=InvitationStatus.PENDING)

    # Invitation details
    token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    expires_at: datetime = Field(..., description="When invitation expires")
    accepted_at: datetime | None = Field(None)
    message: str | None = Field(None, max_length=500, description="Personal message")

    # Tracking
    email_sent_at: datetime | None = Field(None)
    reminders_sent: int = Field(default=0)
    accepted_user_id: str | None = Field(None, description="User ID when accepted")


# Shared Business Data Models


class BusinessData(TimestampMixin, TenantScopedMixin):
    """Shared business data within a tenant."""

    model_config = ConfigDict(from_attributes=True)

    business_id: str = Field(..., description="Business data identifier (typically tenant_id)")

    # Core business elements (shared across tenant)
    core_values: list[str] | None = Field(None, description="Organization's core values")
    purpose: str | None = Field(None, description="Organization's purpose statement")
    vision: str | None = Field(None, description="Organization's vision statement")
    goals: list[dict[str, Any]] | None = Field(
        None, description="Organization's strategic goals"
    )

    # Additional business information
    mission: str | None = Field(None, description="Organization's mission statement")
    culture_attributes: list[str] | None = Field(None, description="Cultural attributes")
    strategic_priorities: list[str] | None = Field(
        None, description="Current strategic priorities"
    )

    # Metadata
    version: str = Field(default="1.0", description="Version of business data")
    last_updated_by: str = Field(..., description="User who last updated the data")
    approved_by: str | None = Field(None, description="User who approved the data")
    approval_date: datetime | None = Field(None)

    # Change tracking
    change_history: list[dict[str, Any]] = Field(
        default_factory=list, description="History of changes made to business data"
    )


class CoachingSession(TimestampMixin, TenantScopedMixin):
    """Coaching session entity (user-specific but outcomes shared)."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    user_id: str = Field(..., description="User who initiated the session")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    status: str = Field(default="active", description="Session status")

    # Session data (private to user)
    session_data: dict[str, Any] = Field(
        default_factory=dict, description="Private session conversation data"
    )

    # Outcomes (shared with tenant business data)
    outcomes: dict[str, Any] | None = Field(
        None, description="Session outcomes to be shared with business data"
    )

    # Session metadata
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(None)
    paused_at: datetime | None = Field(None)

    # AI/LLM metadata
    model_used: str | None = Field(None, description="AI model used for coaching")
    total_tokens: int | None = Field(None, description="Total tokens consumed")
    session_cost: float | None = Field(None, description="Cost of the session")


class UserPreferences(TimestampMixin, TenantScopedMixin):
    """User-specific preferences and settings."""

    model_config = ConfigDict(from_attributes=True)

    user_id: str = Field(..., description="User identifier")

    # UI/UX preferences
    theme: str = Field(default="light")  # light, dark, auto
    language: str = Field(default="en")
    timezone: str = Field(default="UTC")
    date_format: str = Field(default="YYYY-MM-DD")
    time_format: str = Field(default="24h")  # 12h, 24h

    # Notification preferences
    email_notifications: dict[str, bool] = Field(
        default_factory=lambda: {
            "coaching_reminders": True,
            "team_updates": True,
            "system_notifications": True,
            "marketing": False,
        }
    )

    # Coaching preferences
    coaching_preferences: dict[str, Any] = Field(
        default_factory=lambda: {
            "preferred_session_length": 30,  # minutes
            "reminder_frequency": "weekly",
            "coaching_style": "collaborative",
        }
    )

    # Dashboard and view preferences
    dashboard_layout: dict[str, Any] = Field(
        default_factory=dict, description="User's dashboard layout preferences"
    )


# Request/Response Models


class RequestContext(BaseModel):
    """Request context with user and tenant information."""

    user_id: str
    tenant_id: str
    role: UserRole
    permissions: list[str] = []
    subscription_tier: SubscriptionTier = SubscriptionTier.STARTER
    is_owner: bool = False


class TenantCreateRequest(BaseModel):
    """Request model for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=100)
    domain: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)
    company_size: str | None = Field(None)
    timezone: str = Field(default="UTC")


class UserInviteRequest(BaseModel):
    """Request model for inviting a user to a tenant."""

    email: str = Field(..., description="Email address of the user to invite")
    role: UserRole = Field(default=UserRole.MEMBER)
    message: str | None = Field(None, max_length=500)


class BusinessDataUpdateRequest(BaseModel):
    """Request model for updating shared business data."""

    core_values: list[str] | None = None
    purpose: str | None = None
    vision: str | None = None
    goals: list[dict[str, Any]] | None = None
    mission: str | None = None
    culture_attributes: list[str] | None = None
    strategic_priorities: list[str] | None = None
