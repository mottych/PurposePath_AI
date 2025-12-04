"""TypedDict models for coaching service boundaries."""

from datetime import datetime
from typing import NotRequired, TypedDict

from .common import JSONValue


# Core coaching session models
class SessionData(TypedDict, total=False):
    """Nested session data structure."""

    conversation_id: str | None
    phase: str
    context: dict[str, JSONValue]
    business_context: dict[str, JSONValue]
    user_preferences: dict[str, JSONValue]


class CoachingSession(TypedDict):
    """Coaching session record from repository."""

    session_id: str
    user_id: str
    tenant_id: str
    topic: str
    status: str  # active, completed, cancelled
    session_data: SessionData
    outcomes: dict[str, JSONValue] | None
    started_at: datetime
    completed_at: NotRequired[datetime | None]
    model_used: str
    total_tokens: int
    session_cost: float


class SessionOutcomes(TypedDict, total=False):
    """Session outcomes extracted by LLM."""

    extracted_data: dict[str, JSONValue]
    confidence: float
    insights: list[str]
    recommendations: list[str]
    business_impact: str
    next_steps: list[str]


# User preferences models
class CoachingPreferences(TypedDict, total=False):
    """User's coaching preferences."""

    preferred_style: str  # direct, supportive, challenging
    session_frequency: str  # daily, weekly, bi-weekly
    reminder_enabled: bool
    language: str
    timezone: str


class UserPreferences(TypedDict):
    """User preferences from repository."""

    user_id: str
    tenant_id: str
    coaching_preferences: CoachingPreferences
    notification_preferences: dict[str, JSONValue]
    updated_at: datetime


# Business context models
class BusinessContext(TypedDict, total=False):
    """Business context for coaching sessions."""

    has_existing_data: bool
    tenant_id: str
    core_values: list[str]
    purpose: str | None
    vision: str | None
    goals: list[dict[str, JSONValue]]
    # Dynamic fields based on topic
    existing_core_values: NotRequired[list[str]]
    existing_purpose: NotRequired[str]
    existing_vision: NotRequired[str]
    existing_goals: NotRequired[list[dict[str, JSONValue]]]


# Repository method signatures
class SessionCreateData(TypedDict):
    """Data for creating a new coaching session."""

    session_id: str
    user_id: str
    tenant_id: str
    topic: str
    status: str
    session_data: SessionData
    outcomes: dict[str, JSONValue] | None
    started_at: datetime
    model_used: str
    total_tokens: int
    session_cost: float


class SessionUpdateData(TypedDict, total=False):
    """Data for updating a coaching session."""

    status: NotRequired[str]
    session_data: NotRequired[SessionData]
    outcomes: NotRequired[dict[str, JSONValue]]
    completed_at: NotRequired[datetime]
    total_tokens: NotRequired[int]
    session_cost: NotRequired[float]


# Response models
class CompletionSummary(TypedDict):
    """Summary returned when completing a conversation."""

    conversation_id: str
    session_id: str | None
    completed_at: datetime
    business_data_updated: bool
    current_business_data: NotRequired[dict[str, JSONValue]]


class BusinessDataSummary(TypedDict, total=False):
    """Summary of business data for responses."""

    core_values: list[str]
    purpose: str | None
    vision: str | None
    goals: list[dict[str, JSONValue]]
    last_updated: datetime | None
    version: str


class SessionLimitsCheck(TypedDict):
    """Result of session limits checking."""

    within_limits: bool
    current_count: int
    max_allowed: int
    message: str | None
