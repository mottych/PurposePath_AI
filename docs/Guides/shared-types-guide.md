# Shared Types System - Usage Guide

## Overview

The PurposePath API shared types system provides strongly-typed definitions for consistent typing across all services. This eliminates `dict[str, Any]` usage and improves type safety throughout the application.

## Architecture

The shared types system follows these architectural principles:

1. **Strong Typing with NewType**: Domain IDs use `NewType` for compile-time safety while maintaining string runtime behavior
2. **DynamoDB Inheritance Pattern**: All DynamoDB items inherit from `DynamoDBBaseItem` for unified operations
3. **Specific TypedDict for Repository Returns**: Repository methods return specific typed dictionaries instead of generic responses

## Directory Structure

```
shared/domain_types/
├── __init__.py          # Central re-export module
├── common.py            # Domain IDs, pagination, API responses
├── aws.py               # DynamoDB types and AWS service types
├── external.py          # Third-party API types (Stripe, Google, etc.)
└── repository.py        # Repository method return types
```

## Usage Examples

### Domain ID Types (Strong Typing)

```python
from shared.domain_types import UserId, TenantId, create_user_id

# Create strongly-typed IDs
user_id = create_user_id("user_12345")  # Type: UserId
tenant_id = create_tenant_id("tenant_67890")  # Type: TenantId

# Runtime behavior is still string
print(f"User: {user_id}")  # Works fine
user_data = get_user(user_id)  # Type-safe function calls
```

### DynamoDB Types (Inheritance Pattern)

```python
from shared.domain_types import DynamoDBUserItem, DynamoDBConversationItem

# All DynamoDB items share common fields via inheritance
user_item: DynamoDBUserItem = {
    # Base fields (inherited)
    "PK": "USER#123",
    "SK": "USER#123",
    "type": "user",
    "created_at": "2024-01-15T10:30:00Z",
    
    # User-specific fields
    "user_id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "subscription_tier": "professional",
    "is_active": True
}
```

### Repository Return Types (Specific TypedDict)

```python
from shared.domain_types import UserCreateResult, ConversationListResult

def create_user(user_data: dict) -> UserCreateResult:
    try:
        # ... creation logic ...
        return {
            "success": True,
            "user_id": create_user_id(new_user_id),
            "user": created_user_item
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": "CREATION_FAILED"
        }

def list_conversations(user_id: UserId) -> ConversationListResult:
    # ... query logic ...
    return {
        "success": True,
        "conversations": conversation_items,
        "total_count": len(conversation_items)
    }
```

### External API Types

```python
from shared.domain_types import StripeCustomer, GoogleUserInfo

def handle_stripe_webhook(customer_data: StripeCustomer):
    print(f"Customer: {customer_data['email']}")
    # Type-safe access to all Stripe customer fields

def process_google_auth(user_info: GoogleUserInfo):
    if user_info["verified_email"]:
        # Safe access with proper typing
        create_user_from_google(user_info)
```

## Benefits

### 1. Type Safety
- Compile-time checking prevents type errors
- IDE autocomplete and validation
- Clear API contracts between functions

### 2. Consistency
- Unified patterns across all services
- Standard response structures
- Predictable data shapes

### 3. Maintainability
- Centralized type definitions
- Easy to update and extend
- Self-documenting code

### 4. Developer Experience
- Clear error messages
- Better IDE support
- Reduced debugging time

## Migration Guide

### From Generic Types

**Before:**
```python
def get_user(user_id: str) -> dict[str, Any]:
    # Generic return type
    return {"user": {...}, "success": True}
```

**After:**
```python
from shared.domain_types import UserId, UserGetResult

def get_user(user_id: UserId) -> UserGetResult:
    # Strongly-typed return
    return {
        "success": True,
        "user": user_item,
        "found": True
    }
```

### From Dict Annotations

**Before:**
```python
user_data: dict[str, Any] = dynamodb_item
```

**After:**
```python
from shared.domain_types import DynamoDBUserItem

user_data: DynamoDBUserItem = dynamodb_item
```

## Available Type Categories

### Domain IDs
- `UserId`, `TenantId`, `ConversationId`
- `SessionId`, `GoalId`, `ActionId`
- `MessageId`, `StrategyId`

### DynamoDB Types
- `DynamoDBBaseItem` (inheritance base)
- `DynamoDBUserItem`, `DynamoDBConversationItem`
- `DynamoDBSessionItem`, `DynamoDBGoalItem`
- Query result types for each entity

### Repository Types
- Create, Get, Update, Delete, List results
- Bulk operation and transaction results
- Repository metadata types

### External API Types
- **Google**: `GoogleUserInfo`, `GoogleTokenInfo`
- **Stripe**: `StripeCustomer`, `StripeSubscription`, etc.
- **AWS**: `APIGatewayProxyEvent`, `LambdaContext`
- **OAuth**: Generic OAuth types

### Common Patterns
- `PaginationParams`, `PaginationMeta`
- `SuccessData`, `ErrorData`
- Status enums and type aliases

## Best Practices

### 1. Always Use Domain IDs
```python
# Good
def get_user(user_id: UserId) -> UserGetResult:

# Bad  
def get_user(user_id: str) -> dict[str, Any]:
```

### 2. Leverage Inheritance
```python
# All DynamoDB items should inherit from DynamoDBBaseItem
class CustomItem(DynamoDBBaseItem):
    custom_field: str
```

### 3. Specific Return Types
```python
# Use specific repository result types
def create_item(...) -> ItemCreateResult:
    return {"success": True, "item_id": new_id}
```

### 4. Import from Main Module
```python
# Good - use main module
from shared.domain_types import UserId, DynamoDBUserItem

# Avoid - direct submodule imports
from shared.domain_types.common import UserId
```

## Error Handling

The type system includes standardized error patterns:

```python
from shared.domain_types import UserCreateResult

def create_user(...) -> UserCreateResult:
    try:
        # ... logic ...
        return {"success": True, "user_id": user_id}
    except ValidationError:
        return {
            "success": False,
            "error": "Invalid user data",
            "error_code": "VALIDATION_ERROR"
        }
    except DuplicateError:
        return {
            "success": False,
            "error": "User already exists", 
            "error_code": "USER_EXISTS"
        }
```

## Future Enhancements

The shared types system is designed for extension:

1. **Additional Domain Types**: Easy to add new entity types
2. **Enhanced Validation**: Runtime validation decorators
3. **Serialization Helpers**: JSON serialization utilities
4. **API Documentation**: Auto-generated API docs from types

## Support

For questions or issues with the shared types system:

1. Check existing type definitions in `shared/domain_types/`
2. Review usage examples in this guide
3. Validate imports with: `python -c "from shared.domain_types import *"`
4. Refer to architectural decisions in issue #25