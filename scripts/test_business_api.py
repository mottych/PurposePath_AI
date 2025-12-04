"""
Standalone integration test script for BusinessApiClient.

This script can be run independently to test the Business API integration
without requiring pytest infrastructure.

Usage:
    python scripts/test_business_api.py

Environment Variables:
    BUSINESS_API_ACCOUNT_URL - Account Service URL (default: https://api.dev.purposepath.app/account/api/v1)
    BUSINESS_API_BASE_URL - Business API URL (default: same as Account URL)
    BUSINESS_API_TEST_EMAIL - Test user email (default: motty@purposepath.ai)
    BUSINESS_API_TEST_PASSWORD - Test user password (default: Abcd1234)
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx  # noqa: E402
import structlog  # noqa: E402

from coaching.src.infrastructure.external.business_api_client import BusinessApiClient  # noqa: E402
from shared.observability.logging import configure_logging  # noqa: E402

# Configure logging
configure_logging(level="INFO", json_logs=False)
logger = structlog.get_logger()


class BusinessApiTestRunner:
    """Test runner for Business API integration."""

    def __init__(self) -> None:
        """Initialize test runner with configuration."""
        self.account_api_url = os.getenv(
            "BUSINESS_API_ACCOUNT_URL", "https://api.dev.purposepath.app/account/api/v1"
        )
        self.business_api_url = os.getenv(
            "BUSINESS_API_BASE_URL",
            self.account_api_url,  # Default to same as account
        )
        self.email = os.getenv("BUSINESS_API_TEST_EMAIL", "motty@purposepath.ai")
        self.password = os.getenv("BUSINESS_API_TEST_PASSWORD", "Abcd1234")

        self.access_token: str | None = None
        self.user_id: str | None = None
        self.tenant_id: str | None = None
        self.client: BusinessApiClient | None = None

        logger.info(
            "Test runner initialized",
            account_api_url=self.account_api_url,
            business_api_url=self.business_api_url,
            email=self.email,
        )

    async def authenticate(self) -> None:
        """Authenticate with Account Service and get JWT token."""
        logger.info("Authenticating with Account Service...")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.account_api_url}/auth/login",
                    json={"email": self.email, "password": self.password},
                    timeout=30.0,
                )

                response.raise_for_status()
                data = response.json()

                # Extract tokens and user data
                response_data = data.get("data", {})
                self.access_token = response_data.get("access_token")

                user_data = response_data.get("user", {})
                self.user_id = user_data.get("user_id") or user_data.get("userId")

                tenant_data = response_data.get("tenant", {})
                self.tenant_id = tenant_data.get("id") or tenant_data.get("tenant_id")

                logger.info(
                    "✅ Authentication successful",
                    user_id=self.user_id,
                    tenant_id=self.tenant_id,
                    has_token=bool(self.access_token),
                )

            except httpx.HTTPStatusError as e:
                logger.error(
                    "❌ Authentication failed",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
                raise
            except Exception as e:
                logger.error("❌ Authentication error", error=str(e))
                raise

    async def initialize_client(self) -> None:
        """Initialize BusinessApiClient with authentication token."""
        if not self.access_token:
            raise ValueError("Must authenticate before initializing client")

        logger.info("Initializing BusinessApiClient...")

        self.client = BusinessApiClient(
            base_url=self.business_api_url,
            jwt_token=self.access_token,
            timeout=30,
            max_retries=3,
        )

        logger.info("✅ Client initialized")

    async def test_get_user_context(self) -> None:
        """Test get_user_context endpoint."""
        if not self.client or not self.user_id or not self.tenant_id:
            raise ValueError("Client not initialized or missing user/tenant ID")

        logger.info("Testing get_user_context...")

        try:
            result = await self.client.get_user_context(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
            )

            logger.info(
                "✅ get_user_context succeeded",
                result_keys=list(result.keys()) if isinstance(result, dict) else "non-dict",
                result=result,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    "⚠️  Endpoint not found (404)",
                    url=str(e.request.url),
                    message="The .NET API may not have this endpoint implemented yet",
                )
            else:
                logger.error(
                    "❌ get_user_context failed",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
                raise
        except Exception as e:
            logger.error("❌ get_user_context error", error=str(e))
            raise

    async def test_get_organizational_context(self) -> None:
        """Test get_organizational_context endpoint."""
        if not self.client or not self.tenant_id:
            raise ValueError("Client not initialized or missing tenant ID")

        logger.info("Testing get_organizational_context...")

        try:
            result = await self.client.get_organizational_context(tenant_id=self.tenant_id)

            logger.info(
                "✅ get_organizational_context succeeded",
                result_keys=list(result.keys()) if isinstance(result, dict) else "non-dict",
                result=result,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    "⚠️  Endpoint not found (404)",
                    url=str(e.request.url),
                    message="The .NET API may not have this endpoint implemented yet",
                )
            else:
                logger.error(
                    "❌ get_organizational_context failed",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
                raise
        except Exception as e:
            logger.error("❌ get_organizational_context error", error=str(e))
            raise

    async def test_get_user_goals(self) -> None:
        """Test get_user_goals endpoint."""
        if not self.client or not self.user_id or not self.tenant_id:
            raise ValueError("Client not initialized or missing user/tenant ID")

        logger.info("Testing get_user_goals...")

        try:
            result = await self.client.get_user_goals(
                user_id=self.user_id,
                tenant_id=self.tenant_id,
            )

            logger.info(
                "✅ get_user_goals succeeded",
                result_type=type(result).__name__,
                count=len(result) if isinstance(result, list | dict) else "unknown",
                result=result,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    "⚠️  Endpoint not found (404)",
                    url=str(e.request.url),
                    message="The .NET API may not have this endpoint implemented yet",
                )
            else:
                logger.error(
                    "❌ get_user_goals failed",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
                raise
        except Exception as e:
            logger.error("❌ get_user_goals error", error=str(e))
            raise

    async def test_get_metrics(self) -> None:
        """Test get_metrics endpoint."""
        if not self.client or not self.user_id or not self.tenant_id:
            raise ValueError("Client not initialized or missing user/tenant ID")

        logger.info("Testing get_metrics...")

        try:
            result = await self.client.get_metrics(
                entity_id=self.user_id,
                entity_type="users",
                tenant_id=self.tenant_id,
            )

            logger.info(
                "✅ get_metrics succeeded",
                result_keys=list(result.keys()) if isinstance(result, dict) else "non-dict",
                result=result,
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(
                    "⚠️  Endpoint not found (404)",
                    url=str(e.request.url),
                    message="The .NET API may not have this endpoint implemented yet",
                )
            else:
                logger.error(
                    "❌ get_metrics failed",
                    status_code=e.response.status_code,
                    response=e.response.text,
                )
                raise
        except Exception as e:
            logger.error("❌ get_metrics error", error=str(e))
            raise

    async def run_all_tests(self) -> None:
        """Run all integration tests."""
        try:
            logger.info("=" * 60)
            logger.info("BUSINESS API INTEGRATION TESTS")
            logger.info("=" * 60)

            # Step 1: Authenticate
            await self.authenticate()

            # Step 2: Initialize client
            await self.initialize_client()

            # Step 3: Run tests
            logger.info("\n" + "=" * 60)
            logger.info("Running API Tests")
            logger.info("=" * 60)

            await self.test_get_user_context()
            await self.test_get_organizational_context()
            await self.test_get_user_goals()
            await self.test_get_metrics()

            logger.info("\n" + "=" * 60)
            logger.info("🎉 ALL TESTS COMPLETED")
            logger.info("=" * 60)

        except Exception as e:
            logger.error("\n" + "=" * 60)
            logger.error("❌ TEST SUITE FAILED")
            logger.error("=" * 60)
            logger.error("Error", error=str(e))
            raise

        finally:
            # Cleanup
            if self.client:
                await self.client.close()
                logger.info("Client closed")


async def main() -> None:
    """Main entry point."""
    runner = BusinessApiTestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error("Tests failed", error=str(e))
        sys.exit(1)
