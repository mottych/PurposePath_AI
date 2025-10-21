"""Repository method return type definitions for PurposePath API.

Specific TypedDict classes for repository method returns per user architectural decision.
Provides strong typing for data access layer operations.
"""

from typing import Generic, NotRequired, TypedDict, TypeVar

from .aws import DynamoDBItem, JSONValue
from .common import ActionId, ConversationId, GoalId, ISODateString, SessionId, TenantId, UserId

# ========================================
# Generic Repository Result Types
# ========================================

T = TypeVar("T")


class RepositoryResult(TypedDict, Generic[T]):
    """Generic repository operation result"""

    success: bool
    data: NotRequired[T]
    error: NotRequired[str]
    error_code: NotRequired[str]


class PaginatedRepositoryResult(TypedDict, Generic[T]):
    """Generic paginated repository result"""

    success: bool
    items: NotRequired[list[T]]
    total_count: NotRequired[int]
    page_size: NotRequired[int]
    next_token: NotRequired[str]
    error: NotRequired[str]
    error_code: NotRequired[str]


# ========================================
# User Repository Return Types
# ========================================


class UserCreateResult(TypedDict):
    """Result from user creation operation"""

    success: bool
    user_id: NotRequired[UserId]
    user: NotRequired[DynamoDBItem]
    error: NotRequired[str]
    error_code: NotRequired[str]


class UserGetResult(TypedDict):
    """Result from user retrieval operation"""

    success: bool
    user: NotRequired[DynamoDBItem]
    found: bool
    error: NotRequired[str]
    error_code: NotRequired[str]


class UserUpdateResult(TypedDict):
    """Result from user update operation"""

    success: bool
    user: NotRequired[DynamoDBItem]
    updated_fields: NotRequired[list[str]]
    error: NotRequired[str]
    error_code: NotRequired[str]


class UserDeleteResult(TypedDict):
    """Result from user deletion operation"""

    success: bool
    deleted_user_id: NotRequired[UserId]
    error: NotRequired[str]
    error_code: NotRequired[str]


class UserListResult(TypedDict):
    """Result from user listing operation"""

    success: bool
    users: NotRequired[list[DynamoDBItem]]
    total_count: NotRequired[int]
    next_token: NotRequired[str]
    error: NotRequired[str]
    error_code: NotRequired[str]


# ========================================
# Conversation Repository Return Types
# ========================================


class ConversationCreateResult(TypedDict):
    """Result from conversation creation operation"""

    success: bool
    conversation_id: NotRequired[ConversationId]
    conversation: NotRequired[DynamoDBItem]
    error: NotRequired[str]
    error_code: NotRequired[str]


class ConversationGetResult(TypedDict):
    """Result from conversation retrieval operation"""

    success: bool
    conversation: NotRequired[DynamoDBItem]
    found: bool
    error: NotRequired[str]
    error_code: NotRequired[str]


class ConversationUpdateResult(TypedDict):
    """Result from conversation update operation"""

    success: bool
    conversation: NotRequired[DynamoDBItem]
    updated_fields: NotRequired[list[str]]
    error: NotRequired[str]
    error_code: NotRequired[str]


class ConversationListResult(TypedDict):
    """Result from conversation listing operation"""

    success: bool
    conversations: NotRequired[list[DynamoDBItem]]
    total_count: NotRequired[int]
    next_token: NotRequired[str]
    error: NotRequired[str]
    error_code: NotRequired[str]


# ========================================
# Business Data Repository Return Types
# ========================================


class BusinessDataCreateResult(TypedDict):
    """Result from business data creation operation"""

    success: bool
    tenant_id: NotRequired[TenantId]
    data: NotRequired[DynamoDBItem]
    error: NotRequired[str]
    error_code: NotRequired[str]


class BusinessDataGetResult(TypedDict):
    """Result from business data retrieval operation"""

    success: bool
    data: NotRequired[DynamoDBItem]
    found: bool
    error: NotRequired[str]
    error_code: NotRequired[str]


class BusinessDataUpdateResult(TypedDict):
    """Result from business data update operation"""

    success: bool
    data: NotRequired[DynamoDBItem]
    updated_fields: NotRequired[list[str]]
    error: NotRequired[str]
    error_code: NotRequired[str]


# ========================================
# Session Repository Return Types
# ========================================


class SessionCreateResult(TypedDict):
    """Result from session creation operation"""

    success: bool
    session_id: NotRequired[SessionId]
    session: NotRequired[DynamoDBItem]
    error: NotRequired[str]
    error_code: NotRequired[str]


class SessionGetResult(TypedDict):
    """Result from session retrieval operation"""

    success: bool
    session: NotRequired[DynamoDBItem]
    found: bool
    error: NotRequired[str]
    error_code: NotRequired[str]


class SessionUpdateResult(TypedDict):
    """Result from session update operation"""

    success: bool
    session: NotRequired[DynamoDBItem]
    updated_fields: NotRequired[list[str]]
    error: NotRequired[str]
    error_code: NotRequired[str]


class SessionListResult(TypedDict):
    """Result from session listing operation"""

    success: bool
    sessions: NotRequired[list[DynamoDBItem]]
    total_count: NotRequired[int]
    next_token: NotRequired[str]
    error: NotRequired[str]
    error_code: NotRequired[str]


# ========================================
# Goal Repository Return Types
# ========================================


class GoalCreateResult(TypedDict):
    """Result from goal creation operation"""

    success: bool
    goal_id: NotRequired[GoalId]
    goal: NotRequired[DynamoDBItem]
    error: NotRequired[str]
    error_code: NotRequired[str]


class GoalGetResult(TypedDict):
    """Result from goal retrieval operation"""

    success: bool
    goal: NotRequired[DynamoDBItem]
    found: bool
    error: NotRequired[str]
    error_code: NotRequired[str]


class GoalUpdateResult(TypedDict):
    """Result from goal update operation"""

    success: bool
    goal: NotRequired[DynamoDBItem]
    updated_fields: NotRequired[list[str]]
    error: NotRequired[str]
    error_code: NotRequired[str]


class GoalListResult(TypedDict):
    """Result from goal listing operation"""

    success: bool
    goals: NotRequired[list[DynamoDBItem]]
    total_count: NotRequired[int]
    next_token: NotRequired[str]
    error: NotRequired[str]
    error_code: NotRequired[str]


# ========================================
# Action Repository Return Types
# ========================================


class ActionCreateResult(TypedDict):
    """Result from action creation operation"""

    success: bool
    action_id: NotRequired[ActionId]
    action: NotRequired[DynamoDBItem]
    error: NotRequired[str]
    error_code: NotRequired[str]


class ActionGetResult(TypedDict):
    """Result from action retrieval operation"""

    success: bool
    action: NotRequired[DynamoDBItem]
    found: bool
    error: NotRequired[str]
    error_code: NotRequired[str]


class ActionUpdateResult(TypedDict):
    """Result from action update operation"""

    success: bool
    action: NotRequired[DynamoDBItem]
    updated_fields: NotRequired[list[str]]
    error: NotRequired[str]
    error_code: NotRequired[str]


class ActionListResult(TypedDict):
    """Result from action listing operation"""

    success: bool
    actions: NotRequired[list[DynamoDBItem]]
    total_count: NotRequired[int]
    next_token: NotRequired[str]
    error: NotRequired[str]
    error_code: NotRequired[str]


# ========================================
# Multi-Entity Repository Return Types
# ========================================


class BulkOperationResult(TypedDict):
    """Result from bulk repository operations"""

    success: bool
    total_processed: NotRequired[int]
    successful_operations: NotRequired[int]
    failed_operations: NotRequired[int]
    errors: NotRequired[list[dict[str, str]]]
    details: NotRequired[list[dict[str, JSONValue]]]


class TransactionResult(TypedDict):
    """Result from transaction operations"""

    success: bool
    transaction_id: NotRequired[str]
    affected_items: NotRequired[list[str]]
    error: NotRequired[str]
    error_code: NotRequired[str]
    rollback_info: NotRequired[dict[str, JSONValue]]


# ========================================
# Repository Operation Metadata
# ========================================


class RepositoryMetadata(TypedDict):
    """Metadata for repository operations"""

    operation_id: str
    timestamp: ISODateString
    duration_ms: NotRequired[int]
    table_name: NotRequired[str]
    consumed_capacity: NotRequired[float]
    items_processed: NotRequired[int]
    cache_hit: NotRequired[bool]
