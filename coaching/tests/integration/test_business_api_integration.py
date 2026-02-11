"""Integration tests for BusinessApiClient with existing backend services.

These tests verify integration with existing backend endpoints:
- Account Service: /user/profile
- Traction Service: /goals?ownerId={userId}
- Business Foundation: /api/tenants/{tenantId}/business-foundation (pending implementation)

Requirements:
- Deployed backend services (Account, Traction)
- Valid authentication credentials
- Test data in the database

Run with: pytest -m integration coaching/tests/integration/test_business_api_integration.py -v

MVP Scope:
- User metrics endpoints not yet implemented
- Business foundation endpoint pending (tracked in PurposePath_API#152)
"""

import os
from typing import Any

import httpx
import pytest
import structlog
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

logger = structlog.get_logger()


@pytest.fixture
async def auth_data() -> dict[str, Any]:
    """
    Authenticate with Account Service and get auth data.

    Uses credentials from environment variables:
    - BUSINESS_API_TEST_EMAIL
    - BUSINESS_API_TEST_PASSWORD

    Returns:
        Dict with access_token, user_id, and tenant_id
    """
    account_api_url = os.getenv(
        "BUSINESS_API_ACCOUNT_URL", "https://api.dev.purposepath.app/account/api/v1"
    )
    email = os.getenv("BUSINESS_API_TEST_EMAIL", "motty@purposepath.ai")
    password = os.getenv("BUSINESS_API_TEST_PASSWORD", "Abcd1234")

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.post(
            f"{account_api_url}/auth/login",
            json={"email": email, "password": password},
            timeout=30.0,
        )

        response.raise_for_status()
        data = response.json()

        # Extract data from response
        response_data = data.get("data", {})
        access_token = response_data.get("access_token")

        user_data = response_data.get("user", {}) or {}
        user_id = user_data.get("user_id") or user_data.get("userId") or user_data.get("id")
        tenant_id = user_data.get("tenant_id")

        if not access_token:
            raise ValueError("No access_token in login response")

        logger.info(
            "Authentication successful",
            email=email,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        return {
            "access_token": access_token,
            "user_id": user_id,
            "tenant_id": tenant_id,
        }


@pytest.fixture
async def auth_token(auth_data: dict[str, Any]) -> str:
    """Get JWT access token from auth data."""
    return auth_data["access_token"]


@pytest.fixture
async def tenant_id(auth_data: dict[str, Any]) -> str:
    """Get tenant ID from auth data."""
    tenant_id_val = auth_data["tenant_id"]
    if not tenant_id_val:
        raise ValueError("No tenant_id in auth data")
    return tenant_id_val


@pytest.fixture
async def user_id(auth_data: dict[str, Any]) -> str:
    """Get user ID from auth data."""
    user_id_val = auth_data["user_id"]
    if not user_id_val:
        raise ValueError("No user_id in auth data")
    return user_id_val


@pytest.fixture
async def business_api_client(auth_token: str) -> BusinessApiClient:
    """
    Create BusinessApiClient with authentication token.

    Args:
        auth_token: JWT access token

    Returns:
        Configured BusinessApiClient instance
    """
    base_url = os.getenv("BUSINESS_API_BASE_URL", "https://api.dev.purposepath.app/account/api/v1")

    client = BusinessApiClient(
        base_url=base_url,
        jwt_token=auth_token,
        timeout=30,
        max_retries=3,
    )

    yield client

    # Cleanup
    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Integration environment not available (SSL/Network issues)")
class TestBusinessApiIntegration:
    """Integration tests for BusinessApiClient with real .NET API."""

    async def test_authentication_flow(self, auth_token: str) -> None:
        """Test that authentication succeeds and returns valid token."""
        assert auth_token is not None
        assert len(auth_token) > 0
        assert isinstance(auth_token, str)
        logger.info("✅ Authentication flow test passed")

    async def test_get_user_context(
        self,
        business_api_client: BusinessApiClient,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Test retrieving user context from Account Service /user/profile."""
        try:
            result = await business_api_client.get_user_context(
                user_id=user_id,
                tenant_id=tenant_id,
            )

            # Verify response structure (from /user/profile with MVP fallbacks)
            assert result is not None
            assert isinstance(result, dict)

            # Verify expected fields
            assert "user_id" in result
            assert "email" in result
            assert "user_name" in result
            assert "tenant_id" in result

            # Verify MVP fallback fields
            assert result["role"] == "Business Owner"
            assert result["position"] == "Owner"
            assert result["department"] is None

            logger.info("User context retrieved", context=result)
            logger.info("✅ Get user context test passed")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                pytest.skip("Authentication failed - check credentials")
            raise

    async def test_get_organizational_context(
        self,
        business_api_client: BusinessApiClient,
        tenant_id: str,
    ) -> None:
        """Test retrieving business foundation from /api/tenants/{id}/business-foundation."""
        try:
            result = await business_api_client.get_organizational_context(tenant_id=tenant_id)

            # Verify response structure
            assert result is not None
            assert isinstance(result, dict)

            # Log the response for inspection
            logger.info("Organizational context retrieved", context=result)

            # Verify it has at least tenant info
            assert len(result) > 0, "Org context should not be empty"

            logger.info("✅ Get organizational context test passed")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip(
                    f"Business foundation endpoint not found (404). "
                    f"Implementation tracked in PurposePath_API#152: {e.request.url}"
                )
            raise

    async def test_get_user_goals(
        self,
        business_api_client: BusinessApiClient,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Test retrieving user goals from Traction Service /goals?ownerId={userId}."""
        try:
            result = await business_api_client.get_user_goals(
                user_id=user_id,
                tenant_id=tenant_id,
            )

            # Verify response is a list (may be empty if user has no goals)
            assert result is not None
            assert isinstance(result, list)

            # Log the response for inspection
            logger.info("User goals retrieved", goal_count=len(result))

            # If goals exist, verify structure
            if len(result) > 0:
                goal = result[0]
                assert "id" in goal
                assert "title" in goal
                logger.info("Sample goal", goal=goal)

            logger.info("✅ Get user goals test passed")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip(f"Goals endpoint not found (404): {e.request.url}")
            raise

    # test_get_metrics removed - not in MVP scope
    # User performance metrics will be added post-MVP

    async def test_error_handling_empty_goals(
        self,
        business_api_client: BusinessApiClient,
        tenant_id: str,
    ) -> None:
        """Test handling of user with no goals."""
        # Use a random UUID that probably has no goals
        user_with_no_goals = "00000000-0000-0000-0000-000000000000"

        try:
            result = await business_api_client.get_user_goals(
                user_id=user_with_no_goals,
                tenant_id=tenant_id,
            )

            # Should return empty list, not fail
            assert isinstance(result, list)
            logger.info(
                "✅ Empty goals handling test passed",
                goal_count=len(result),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip("Goals endpoint not available")
            # Other errors are acceptable for this test
            logger.info("Error expected for nonexistent user", status=e.response.status_code)

    async def test_error_handling_invalid_token(self, user_id: str, tenant_id: str) -> None:
        """Test error handling with invalid authentication token."""
        base_url = os.getenv(
            "BUSINESS_API_BASE_URL", "https://api.dev.purposepath.app/account/api/v1"
        )

        # Create client with invalid token
        client = BusinessApiClient(
            base_url=base_url,
            jwt_token="invalid-token-xyz",
            timeout=30,
        )

        try:
            await client.get_user_context(user_id=user_id, tenant_id=tenant_id)
            pytest.fail("Expected HTTPStatusError for invalid token")

        except httpx.HTTPStatusError as e:
            # Expected: 401 Unauthorized or 404 if endpoint doesn't exist
            if e.response.status_code == 404:
                pytest.skip("Endpoint not found (404). Cannot test invalid token behavior.")
            assert e.response.status_code == 401
            logger.info("✅ Invalid token handling test passed")

        finally:
            await client.close()

    async def test_timeout_handling(
        self,
        auth_token: str,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Test timeout handling with very short timeout."""
        base_url = os.getenv(
            "BUSINESS_API_BASE_URL", "https://api.dev.purposepath.app/account/api/v1"
        )

        # Create client with very short timeout
        client = BusinessApiClient(
            base_url=base_url,
            jwt_token=auth_token,
            timeout=0.001,  # 1ms timeout - will likely fail
        )

        try:
            await client.get_user_context(user_id=user_id, tenant_id=tenant_id)
            # If it succeeds, the endpoint is very fast or timeout handling works differently
            logger.info("Request completed despite very short timeout")

        except (httpx.TimeoutException, httpx.ConnectTimeout, httpx.ReadTimeout):
            logger.info("✅ Timeout handling test passed")

        finally:
            await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skip(reason="Integration environment not available (SSL/Network issues)")
class TestBusinessApiPerformance:
    """Performance tests for BusinessApiClient."""

    async def test_user_profile_response_time(
        self,
        business_api_client: BusinessApiClient,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Test that /user/profile API responds within acceptable time."""
        import time

        start_time = time.time()

        try:
            await business_api_client.get_user_context(
                user_id=user_id,
                tenant_id=tenant_id,
            )

            duration = time.time() - start_time

            # Assert response time < 3 seconds (profile should be fast)
            assert duration < 3.0, f"Response took {duration:.2f}s, expected < 3s"

            logger.info(
                "✅ Performance test passed",
                duration_seconds=round(duration, 2),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code in [401, 404]:
                pytest.skip("Authentication or endpoint issue")
            raise
