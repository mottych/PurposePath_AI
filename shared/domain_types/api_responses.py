"""TypedDict structures for FastAPI response models.

These provide type safety for API responses while maintaining
compatibility with existing route handlers.
"""

from typing import Literal, NotRequired, TypedDict

from shared.domain_types.common import (
    ActionStatus,
    GoalId,
    ISODateString,
    StrategyId,
    SubscriptionTier,
    UserId,
)

from .common import JSONValue

# ========================================
# Strategy API Response Types
# ========================================


class StrategyResponse(TypedDict):
    """Strategy response structure for API endpoints"""

    strategy_id: StrategyId
    goal_id: GoalId
    title: NotRequired[str]
    description: NotRequired[str]
    status: NotRequired[ActionStatus]
    priority: NotRequired[int]
    due_date: NotRequired[ISODateString]
    owner_id: NotRequired[UserId]
    tags: NotRequired[list[str]]
    created_at: ISODateString
    updated_at: ISODateString


class StrategyListResponse(TypedDict):
    """List of strategies response structure"""

    strategies: list[StrategyResponse]
    total: int


class StrategyCreateRequest(TypedDict):
    """Strategy creation request structure"""

    title: str
    description: NotRequired[str]
    priority: NotRequired[int]
    due_date: NotRequired[ISODateString]
    owner_id: NotRequired[UserId]
    tags: NotRequired[list[str]]


class StrategyUpdateRequest(TypedDict):
    """Strategy update request structure (all fields optional)"""

    title: NotRequired[str]
    description: NotRequired[str]
    status: NotRequired[ActionStatus]
    priority: NotRequired[int]
    due_date: NotRequired[ISODateString]
    owner_id: NotRequired[UserId]
    tags: NotRequired[list[str]]


# ========================================
# Goal API Response Types
# ========================================


class GoalResponse(TypedDict):
    """Goal response structure for API endpoints"""

    id: GoalId
    title: str
    description: NotRequired[str]
    status: NotRequired[ActionStatus]
    time_horizon: NotRequired[Literal["annual", "quarterly", "long_term"]]
    target_value: NotRequired[float]
    current_value: NotRequired[float]
    unit: NotRequired[str]
    progress: NotRequired[float]
    created_at: ISODateString
    updated_at: ISODateString
    due_date: NotRequired[ISODateString]
    owner_id: NotRequired[UserId]
    strategies: NotRequired[list[StrategyResponse]]
    measures: NotRequired[list[dict[str, JSONValue]]]  # Measure types can be defined later


class GoalListResponse(TypedDict):
    """List of goals response structure"""

    goals: list[GoalResponse]
    total: int


class GoalCreateRequest(TypedDict):
    """Goal creation request structure"""

    title: str
    description: NotRequired[str]
    time_horizon: NotRequired[Literal["annual", "quarterly", "long_term"]]
    target_value: NotRequired[float]
    current_value: NotRequired[float]
    unit: NotRequired[str]
    due_date: NotRequired[ISODateString]
    owner_id: NotRequired[UserId]


class GoalUpdateRequest(TypedDict):
    """Goal update request structure (all fields optional)"""

    title: NotRequired[str]
    description: NotRequired[str]
    status: NotRequired[ActionStatus]
    time_horizon: NotRequired[Literal["annual", "quarterly", "long_term"]]
    target_value: NotRequired[float]
    current_value: NotRequired[float]
    unit: NotRequired[str]
    due_date: NotRequired[ISODateString]
    owner_id: NotRequired[UserId]


class GoalNoteResponse(TypedDict):
    """Goal note response structure"""

    id: str
    note: str
    attachments: NotRequired[list[str]]
    created_at: ISODateString
    created_by: UserId


class GoalNoteCreateRequest(TypedDict):
    """Goal note creation request structure"""

    note: str
    attachments: NotRequired[list[str]]


# ========================================
# Billing API Response Types
# ========================================


class SubscriptionStatusResponse(TypedDict):
    """Subscription status response structure"""

    active: bool
    tier: SubscriptionTier
    status: str
    customer_id: NotRequired[str]
    subscription_id: NotRequired[str]
    current_period_end: NotRequired[int]
    cancel_at_period_end: NotRequired[bool]


class StripeSubscriptionData(TypedDict):
    """Stripe subscription data structure for webhooks"""

    status: str
    tier: SubscriptionTier
    stripe_subscription_id: str
    current_period_start: NotRequired[int]
    current_period_end: NotRequired[int]
    cancel_at_period_end: bool


# ========================================
# Common Response Patterns
# ========================================


class DeleteResponse(TypedDict):
    """Standard delete operation response"""

    deleted: bool
    message: NotRequired[str]


class UpdatedResponse(TypedDict):
    """Standard update operation response"""

    updated: bool
    message: NotRequired[str]


# ========================================
# Review API Response Types
# ========================================


class ReviewResponse(TypedDict):
    """Review response structure"""

    id: str
    goal_id: GoalId
    review_type: Literal["weekly", "monthly", "quarterly", "annual"]
    content: str
    status: NotRequired[ActionStatus]
    created_at: ISODateString
    created_by: UserId


# ========================================
# Report API Response Types
# ========================================


class ReportResponse(TypedDict):
    """Report response structure"""

    report_type: str
    data: dict[str, JSONValue]  # Report data structure varies by type
    generated_at: ISODateString


# ========================================
# Realtime API Response Types
# ========================================


class ActivityResponse(TypedDict):
    """Activity response structure for realtime updates"""

    id: str
    text: str
    created_at: ISODateString
    created_by: UserId
    goal_id: NotRequired[GoalId]
