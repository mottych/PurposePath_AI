"""Shared multitenant data models for PurposePath."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

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
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TenantScopedMixin(BaseModel):
    """Mixin for tenant-scoped entities."""
    tenant_id: str = Field(..., description="Unique identifier for the tenant")


# Core Entity Models

class Tenant(TimestampMixin):
    """Tenant entity representing an organization."""

    model_config = ConfigDict(from_attributes=True)

    tenant_id: str = Field(default_factory=lambda: f"tenant_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., min_length=1, max_length=100, description="Organization name")
    domain: Optional[str] = Field(None, max_length=100, description="Organization domain")
    owner_user_id: str = Field(..., description="User ID of the tenant owner")
    status: TenantStatus = Field(default=TenantStatus.TRIAL)
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant-specific settings")

    # Metadata
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None)
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
    password_hash: Optional[str] = Field(None, description="Hashed password")
    email_verified: bool = Field(default=False)
    last_login: Optional[datetime] = Field(None)

    # Profile information
    avatar_url: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    timezone: str = Field(default="UTC")
    language: str = Field(default="en")

    # User preferences and settings
    preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="User-specific preferences and settings"
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
    trial_ends_at: Optional[datetime] = Field(None)
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_period_end: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cancelled_at: Optional[datetime] = Field(None)

    # Usage limits and tracking
    limits: Dict[str, int] = Field(
        default_factory=dict,
        description="Subscription limits (max_users, max_sessions, etc.)"
    )
    usage: Dict[str, int] = Field(
        default_factory=dict,
        description="Current usage tracking"
    )

    # External billing system integration
    external_subscription_id: Optional[str] = Field(None, description="ID from billing provider")


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
    accepted_at: Optional[datetime] = Field(None)
    message: Optional[str] = Field(None, max_length=500, description="Personal message")

    # Tracking
    email_sent_at: Optional[datetime] = Field(None)
    reminders_sent: int = Field(default=0)
    accepted_user_id: Optional[str] = Field(None, description="User ID when accepted")


# Shared Business Data Models

class BusinessData(TimestampMixin, TenantScopedMixin):
    """Shared business data within a tenant."""

    model_config = ConfigDict(from_attributes=True)

    business_id: str = Field(..., description="Business data identifier (typically tenant_id)")

    # Core business elements (shared across tenant)
    core_values: Optional[List[str]] = Field(None, description="Organization's core values")
    purpose: Optional[str] = Field(None, description="Organization's purpose statement")
    vision: Optional[str] = Field(None, description="Organization's vision statement")
    goals: Optional[List[Dict[str, Any]]] = Field(None, description="Organization's strategic goals")

    # Additional business information
    mission: Optional[str] = Field(None, description="Organization's mission statement")
    culture_attributes: Optional[List[str]] = Field(None, description="Cultural attributes")
    strategic_priorities: Optional[List[str]] = Field(None, description="Current strategic priorities")

    # Metadata
    version: str = Field(default="1.0", description="Version of business data")
    last_updated_by: str = Field(..., description="User who last updated the data")
    approved_by: Optional[str] = Field(None, description="User who approved the data")
    approval_date: Optional[datetime] = Field(None)

    # Change tracking
    change_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="History of changes made to business data"
    )


class CoachingSession(TimestampMixin, TenantScopedMixin):
    """Coaching session entity (user-specific but outcomes shared)."""

    model_config = ConfigDict(from_attributes=True)

    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:12]}")
    user_id: str = Field(..., description="User who initiated the session")
    topic: CoachingTopic = Field(..., description="Coaching topic")
    status: str = Field(default="active", description="Session status")

    # Session data (private to user)
    session_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Private session conversation data"
    )

    # Outcomes (shared with tenant business data)
    outcomes: Optional[Dict[str, Any]] = Field(
        None,
        description="Session outcomes to be shared with business data"
    )

    # Session metadata
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None)
    paused_at: Optional[datetime] = Field(None)

    # AI/LLM metadata
    model_used: Optional[str] = Field(None, description="AI model used for coaching")
    total_tokens: Optional[int] = Field(None, description="Total tokens consumed")
    session_cost: Optional[float] = Field(None, description="Cost of the session")


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
    email_notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "coaching_reminders": True,
            "team_updates": True,
            "system_notifications": True,
            "marketing": False
        }
    )

    # Coaching preferences
    coaching_preferences: Dict[str, Any] = Field(
        default_factory=lambda: {
            "preferred_session_length": 30,  # minutes
            "reminder_frequency": "weekly",
            "coaching_style": "collaborative"
        }
    )

    # Dashboard and view preferences
    dashboard_layout: Dict[str, Any] = Field(
        default_factory=dict,
        description="User's dashboard layout preferences"
    )


# Request/Response Models

class RequestContext(BaseModel):
    """Request context with user and tenant information."""

    user_id: str
    tenant_id: str
    role: UserRole
    permissions: List[str] = []
    subscription_tier: SubscriptionTier = SubscriptionTier.STARTER
    is_owner: bool = False


class TenantCreateRequest(BaseModel):
    """Request model for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=100)
    domain: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None)
    timezone: str = Field(default="UTC")


class UserInviteRequest(BaseModel):
    """Request model for inviting a user to a tenant."""

    email: str = Field(..., description="Email address of the user to invite")
    role: UserRole = Field(default=UserRole.MEMBER)
    message: Optional[str] = Field(None, max_length=500)


class BusinessDataUpdateRequest(BaseModel):
    """Request model for updating shared business data."""

    core_values: Optional[List[str]] = None
    purpose: Optional[str] = None
    vision: Optional[str] = None
    goals: Optional[List[Dict[str, Any]]] = None
    mission: Optional[str] = None
    culture_attributes: Optional[List[str]] = None
    strategic_priorities: Optional[List[str]] = None
