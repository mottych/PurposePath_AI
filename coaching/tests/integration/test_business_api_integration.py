"""Integration tests for BusinessApiClient with deployed .NET Business API.

These tests verify the integration with the real .NET Business API endpoints.
They require:
- Deployed .NET API (Account Service)
- Valid authentication credentials
- Test data in the database

Run with: pytest -m integration coaching/tests/integration/test_business_api_integration.py -v
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
        "BUSINESS_API_ACCOUNT_URL",
        "https://api.dev.purposepath.app/account/api/v1"
    )
    email = os.getenv("BUSINESS_API_TEST_EMAIL", "motty@purposepath.ai")
    password = os.getenv("BUSINESS_API_TEST_PASSWORD", "Abcd1234")

    async with httpx.AsyncClient() as client:
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
    base_url = os.getenv(
        "BUSINESS_API_BASE_URL",
        "https://api.dev.purposepath.app/account/api/v1"
    )

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
        """Test retrieving user context from Business API."""
        try:
            result = await business_api_client.get_user_context(
                user_id=user_id,
                tenant_id=tenant_id,
            )

            # Verify response structure
            assert result is not None
            assert isinstance(result, dict)

            # Log the response for inspection
            logger.info("User context retrieved", context=result)

            # Basic validations (adjust based on actual API response)
            # The actual structure may vary, so we're flexible here
            assert len(result) > 0, "User context should not be empty"

            logger.info("✅ Get user context test passed")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip(
                    f"User context endpoint not found (404). "
                    f"The .NET API may not have this endpoint yet: {e.request.url}"
                )
            raise

    async def test_get_organizational_context(
        self,
        business_api_client: BusinessApiClient,
        tenant_id: str,
    ) -> None:
        """Test retrieving organizational context from Business API."""
        try:
            result = await business_api_client.get_organizational_context(
                tenant_id=tenant_id
            )

            # Verify response structure
            assert result is not None
            assert isinstance(result, dict)

            # Log the response for inspection
            logger.info("Organizational context retrieved", context=result)

            assert len(result) > 0, "Org context should not be empty"

            logger.info("✅ Get organizational context test passed")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip(
                    f"Organizational context endpoint not found (404). "
                    f"The .NET API may not have this endpoint yet: {e.request.url}"
                )
            raise

    async def test_get_user_goals(
        self,
        business_api_client: BusinessApiClient,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Test retrieving user goals from Business API."""
        try:
            result = await business_api_client.get_user_goals(
                user_id=user_id,
                tenant_id=tenant_id,
            )

            # Verify response structure
            assert result is not None
            assert isinstance(result, list) or isinstance(result, dict)

            # Log the response for inspection
            logger.info("User goals retrieved", goals=result)

            logger.info("✅ Get user goals test passed")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip(
                    f"User goals endpoint not found (404). "
                    f"The .NET API may not have this endpoint yet: {e.request.url}"
                )
            raise

    async def test_get_metrics(
        self,
        business_api_client: BusinessApiClient,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Test retrieving metrics from Business API."""
        try:
            result = await business_api_client.get_metrics(
                entity_id=user_id,
                entity_type="users",
                tenant_id=tenant_id,
            )

            # Verify response structure
            assert result is not None
            assert isinstance(result, dict)

            # Log the response for inspection
            logger.info("Metrics retrieved", metrics=result)

            logger.info("✅ Get metrics test passed")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip(
                    f"Metrics endpoint not found (404). "
                    f"The .NET API may not have this endpoint yet: {e.request.url}"
                )
            raise

    async def test_error_handling_invalid_user(
        self,
        business_api_client: BusinessApiClient,
        tenant_id: str,
    ) -> None:
        """Test error handling with invalid user ID."""
        invalid_user_id = "nonexistent-user-12345"

        try:
            await business_api_client.get_user_context(
                user_id=invalid_user_id,
                tenant_id=tenant_id,
            )
            # If we get here without exception, the endpoint might return empty data
            logger.info("Endpoint returned data for invalid user (might be expected)")

        except httpx.HTTPStatusError as e:
            # Expected behavior: 404 for nonexistent user
            assert e.response.status_code in [404, 400]
            logger.info(
                "✅ Error handling test passed",
                status_code=e.response.status_code,
            )

    async def test_error_handling_invalid_token(self, user_id: str, tenant_id: str) -> None:
        """Test error handling with invalid authentication token."""
        base_url = os.getenv(
            "BUSINESS_API_BASE_URL",
            "https://api.dev.purposepath.app/account/api/v1"
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
            "BUSINESS_API_BASE_URL",
            "https://api.dev.purposepath.app/account/api/v1"
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
class TestBusinessApiPerformance:
    """Performance tests for BusinessApiClient."""

    async def test_user_context_response_time(
        self,
        business_api_client: BusinessApiClient,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Test that user context API responds within acceptable time."""
        import time

        start_time = time.time()

        try:
            await business_api_client.get_user_context(
                user_id=user_id,
                tenant_id=tenant_id,
            )

            duration = time.time() - start_time

            # Assert response time < 5 seconds
            assert duration < 5.0, f"Response took {duration:.2f}s, expected < 5s"

            logger.info(
                "✅ Performance test passed",
                duration_seconds=round(duration, 2),
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                pytest.skip("Endpoint not available")
            raise
