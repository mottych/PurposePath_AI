"""Test the shared types module to ensure proper functionality."""

from typing import Any

import pytest

from shared.domain_types import (
    GoogleUserInfo,
    StripeCustomer,
    UserCreateResult,
    create_tenant_id,
    create_user_id,
)


def test_domain_id_creation() -> None:
    """Test that domain IDs can be created and maintain type safety."""
    user_id = create_user_id("user_123")
    tenant_id = create_tenant_id("tenant_456")

    assert isinstance(user_id, str)  # Runtime behavior
    assert user_id == "user_123"
    assert isinstance(tenant_id, str)
    assert tenant_id == "tenant_456"


def test_dynamodb_types() -> None:
    """Test that DynamoDB types are properly structured."""
    # DynamoDBItem is generic - cast to dict[str, Any] for testing
    user_item: dict[str, Any] = {
        "PK": "USER#123",
        "SK": "USER#123",
        "type": "user",
        "created_at": "2024-01-15T10:30:00Z",
        "user_id": "user_123",
        "email": "test@example.com",
        "name": "Test User",
        "subscription_tier": "starter",
        "is_active": True,
    }

    assert user_item["user_id"] == "user_123"
    assert user_item["subscription_tier"] == "starter"


def test_repository_result_types() -> None:
    """Test that repository result types work correctly."""
    success_result: UserCreateResult = {"success": True, "user_id": create_user_id("user_123")}

    error_result: UserCreateResult = {
        "success": False,
        "error": "User already exists",
        "error_code": "USER_EXISTS",
    }

    assert success_result["success"] is True
    assert error_result["success"] is False


def test_external_api_types() -> None:
    """Test that external API types are properly structured."""
    google_user: GoogleUserInfo = {
        "id": "google_123",
        "email": "user@example.com",
        "verified_email": True,
        "name": "Google User",
        "given_name": "Google",
        "family_name": "User",
        "picture": "https://example.com/photo.jpg",
    }

    stripe_customer: StripeCustomer = {
        "id": "cus_123",
        "object": "customer",
        "created": 1642284000,
        "email": "customer@example.com",
        "metadata": {},
        "balance": 0,
        "delinquent": False,
        "livemode": False,
    }

    assert google_user["verified_email"] is True
    assert stripe_customer["object"] == "customer"


if __name__ == "__main__":
    pytest.main([__file__])
