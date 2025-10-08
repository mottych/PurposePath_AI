"""Example usage of the PurposePath API shared types system.

This file demonstrates best practices for using the shared types
in real-world scenarios across different services.
"""

from typing import Any, cast

from shared.types import (  # Common patterns; External API types; Repository result types; Domain IDs
    ConversationListResult,
    DynamoDBItem,
    ErrorData,
    GoogleUserInfo,
    PaginationParams,
    StripeCustomer,
    SuccessData,
    TenantId,
    UserCreateResult,
    UserGetResult,
    UserId,
    create_conversation_id,
    create_tenant_id,
    create_user_id,
)

# ========================================
# Domain ID Usage Examples
# ========================================

def example_domain_ids() -> tuple[UserId, TenantId, str]:
    """Examples of strong typing with domain IDs."""

    # Create strongly-typed IDs
    user_id = create_user_id("usr_abc123")
    tenant_id = create_tenant_id("tnt_xyz789")
    conversation_id = create_conversation_id("conv_def456")

    # Type safety - these would cause mypy errors if types don't match
    process_user_data(user_id)  # ✅ Correct type
    # process_user_data(tenant_id)  # ❌ Would be mypy error

    return user_id, tenant_id, conversation_id


def process_user_data(user_id: UserId) -> None:
    """Function that requires specific UserId type."""
    print(f"Processing user: {user_id}")


# ========================================
# Repository Pattern Examples
# ========================================

class UserRepository:
    """Example repository using shared types."""

    def create_user(self, email: str, name: str, tenant_id: TenantId) -> UserCreateResult:
        """Create a new user with proper typed result."""
        try:
            # Simulate user creation
            user_id = create_user_id(f"usr_{email.split('@')[0]}")

            user_item = cast(DynamoDBItem, {
                "pk": f"USER#{user_id}",
                "sk": f"USER#{user_id}",
                "tenant_id": str(tenant_id),
                "created_at": "2024-01-15T10:30:00Z",
                "user_id": str(user_id),
                "email": email,
                "name": name,
                "subscription_tier": "starter",
                "is_active": True
            })

            # Simulate DynamoDB put_item
            # self.dynamodb.put_item(Item=user_item)

            return {
                "success": True,
                "user_id": user_id,
                "user": user_item
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "USER_CREATION_FAILED"
            }

    def get_user(self, user_id: UserId) -> UserGetResult:
        """Get user with typed result."""
        try:
            # Simulate DynamoDB get_item
            found = True  # Simulate found user

            if found:
                user_item = cast(DynamoDBItem, {
                    "pk": f"USER#{user_id}",
                    "sk": f"USER#{user_id}",
                    "created_at": "2024-01-15T10:30:00Z",
                    "user_id": str(user_id),
                    "email": "user@example.com",
                    "name": "John Doe",
                    "subscription_tier": "professional",
                    "is_active": True
                })

                return {
                    "success": True,
                    "user": user_item,
                    "found": True
                }
            else:
                return {
                    "success": True,
                    "found": False
                }

        except Exception as e:
            return {
                "success": False,
                "found": False,
                "error": str(e),
                "error_code": "USER_FETCH_FAILED"
            }


class ConversationRepository:
    """Example conversation repository."""

    def list_user_conversations(
        self,
        user_id: UserId,
        _params: PaginationParams
    ) -> ConversationListResult:
        """List conversations with pagination."""
        try:
            # Simulate DynamoDB query
            conversations: list[DynamoDBItem] = [
                cast(DynamoDBItem, {
                    "pk": f"USER#{user_id}",
                    "sk": "CONV#conv_123",
                    "created_at": "2024-01-15T10:30:00Z",
                    "conversation_id": "conv_123",
                    "user_id": str(user_id),
                    "topic": "Goal Setting",
                    "status": "active",
                    "messages": [],
                    "context": {}
                })
            ]

            return {
                "success": True,
                "conversations": conversations,
                "total_count": len(conversations)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_code": "CONVERSATION_LIST_FAILED"
            }


# ========================================
# External API Integration Examples
# ========================================

def handle_google_oauth(user_info: GoogleUserInfo) -> UserCreateResult:
    """Handle Google OAuth user creation."""
    if not user_info["verified_email"]:
        return {
            "success": False,
            "error": "Email not verified",
            "error_code": "EMAIL_NOT_VERIFIED"
        }

    # Create user from Google data
    repo = UserRepository()
    tenant_id = create_tenant_id("default_tenant")

    return repo.create_user(
        email=user_info["email"],
        name=user_info["name"],
        tenant_id=tenant_id
    )


def handle_stripe_customer(customer: StripeCustomer) -> SuccessData | ErrorData:
    """Handle Stripe customer webhook."""
    try:
        # Process customer data
        print(f"Customer {customer['id']}: {customer['email']}")

        if customer["delinquent"]:
            # Handle delinquent account
            pass

        return {
            "success": True,
            "message": "Customer processed successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": "STRIPE_PROCESSING_FAILED"
        }


# ========================================
# Service Layer Examples
# ========================================

class UserService:
    """Example service layer using typed repositories."""

    def __init__(self) -> None:
        self.user_repo = UserRepository()
        self.conversation_repo = ConversationRepository()

    def create_user_workflow(
        self,
        email: str,
        name: str,
        tenant_id: TenantId
    ) -> UserCreateResult:
        """Complete user creation workflow."""

        # Create user
        result = self.user_repo.create_user(email, name, tenant_id)

        if not result["success"]:
            return result

        # Additional setup could go here
        # - Send welcome email
        # - Create default conversation
        # - Initialize user preferences

        return result

    def get_user_dashboard_data(self, user_id: UserId) -> dict[str, Any]:
        """Get comprehensive user dashboard data."""

        # Get user info
        user_result = self.user_repo.get_user(user_id)
        if not user_result["success"] or not user_result.get("found"):
            return {"error": "User not found"}

        # Get conversations
        conv_result = self.conversation_repo.list_user_conversations(
            user_id,
            {"page": 1, "limit": 10}
        )

        return {
            "user": user_result.get("user"),
            "conversations": conv_result.get("conversations", []),
            "conversation_count": conv_result.get("total_count", 0)
        }


# ========================================
# Usage Examples
# ========================================

if __name__ == "__main__":
    # Example 1: Domain ID usage
    user_id, tenant_id, conversation_id = example_domain_ids()
    print(f"Created IDs: {user_id}, {tenant_id}, {conversation_id}")

    # Example 2: Repository usage
    repo = UserRepository()
    create_result = repo.create_user("john@example.com", "John Doe", tenant_id)
    print(f"User creation: {create_result['success']}")

    if create_result["success"] and "user_id" in create_result:
        get_result = repo.get_user(create_result["user_id"])
        print(f"User retrieval: {get_result['success']}")

    # Example 3: Service usage
    service = UserService()
    dashboard_data = service.get_user_dashboard_data(user_id)
    print(f"Dashboard data keys: {list(dashboard_data.keys())}")

    # Example 4: External API types
    google_user: GoogleUserInfo = {
        "id": "google_123",
        "email": "user@gmail.com",
        "verified_email": True,
        "name": "Google User",
        "given_name": "Google",
        "family_name": "User",
        "picture": "https://example.com/photo.jpg"
    }

    google_result = handle_google_oauth(google_user)
    print(f"Google OAuth: {google_result['success']}")
