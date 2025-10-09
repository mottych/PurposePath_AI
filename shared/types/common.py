"""Common type definitions and aliases for PurposePath API.

Strong typing with NewType for domain IDs and common patterns.
These provide type safety while maintaining runtime string behavior.
"""

from typing import Literal, NewType, TypeAlias, TypedDict

# ========================================
# Domain ID Types (Strong Typing with NewType)
# ========================================
# These provide compile-time type safety while maintaining string runtime behavior

UserId = NewType('UserId', str)
"""Strongly-typed user identifier"""

TenantId = NewType('TenantId', str)
"""Strongly-typed tenant identifier"""

ConversationId = NewType('ConversationId', str)
"""Strongly-typed conversation identifier"""

MessageId = NewType('MessageId', str)
"""Strongly-typed message identifier"""

SessionId = NewType('SessionId', str)
"""Strongly-typed coaching session identifier"""

GoalId = NewType('GoalId', str)
"""Strongly-typed goal identifier"""

ActionId = NewType('ActionId', str)
"""Strongly-typed action identifier"""

StrategyId = NewType('StrategyId', str)
"""Strongly-typed strategy identifier"""

# ========================================
# Common Data Patterns
# ========================================

ISODateString: TypeAlias = str
"""ISO 8601 formatted datetime string (e.g., '2024-01-15T10:30:00Z')"""

# JSON value types for type safety
JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]
"""Recursive JSON value type for type-safe JSON data"""

JSONDict: TypeAlias = dict[str, JSONValue]
"""Type-safe JSON dictionary for API responses and data serialization"""

# ========================================
# Pagination Patterns
# ========================================

class PaginationParams(TypedDict):
    """Standard pagination parameters"""
    page: int
    limit: int

class PaginationMeta(TypedDict):
    """Pagination metadata for responses"""
    page: int
    limit: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

# ========================================
# API Response Patterns
# ========================================

class SuccessData(TypedDict):
    """Success response structure"""
    success: Literal[True]
    message: str | None

class ErrorData(TypedDict):
    """Error response structure"""
    success: Literal[False]
    error: str
    error_code: str | None

# ========================================
# Status and State Types
# ========================================

SubscriptionTier: TypeAlias = Literal["starter", "professional", "enterprise"]
"""Valid subscription tier values"""

UserStatus: TypeAlias = Literal["active", "inactive", "suspended", "deleted"]
"""Valid user status values"""

ConversationStatus: TypeAlias = Literal["active", "completed", "paused", "archived"]
"""Valid conversation status values"""

ActionStatus: TypeAlias = Literal["not_started", "in_progress", "completed", "blocked"]
"""Valid action status values"""

# ========================================
# Utility Functions for Type Creation
# ========================================

def create_user_id(value: str) -> UserId:
    """Create a strongly-typed UserId from string"""
    return UserId(value)

def create_tenant_id(value: str) -> TenantId:
    """Create a strongly-typed TenantId from string"""
    return TenantId(value)

def create_conversation_id(value: str) -> ConversationId:
    """Create a strongly-typed ConversationId from string"""
    return ConversationId(value)

def create_session_id(value: str) -> SessionId:
    """Create a strongly-typed SessionId from string"""
    return SessionId(value)

def create_goal_id(value: str) -> GoalId:
    """Create a strongly-typed GoalId from string"""
    return GoalId(value)

def create_action_id(value: str) -> ActionId:
    """Create a strongly-typed ActionId from string"""
    return ActionId(value)

def create_strategy_id(value: str) -> StrategyId:
    """Create a strongly-typed StrategyId from string"""
    return StrategyId(value)
