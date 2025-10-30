"""Pytest configuration for E2E tests.

E2E tests require:
- Real AWS credentials configured
- Deployed API endpoint or local server running
- Real LLM provider access (Bedrock, OpenAI, Google Vertex)
"""

import os
from typing import Any

import pytest
import structlog
from httpx import AsyncClient

logger = structlog.get_logger()


def pytest_configure(config: Any) -> None:
    """Register E2E marker."""
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end test (requires deployed environment and real AI providers)",
    )


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """
    Get API base URL from environment.

    For local testing: http://localhost:8000
    For deployed: https://api.purposepath.com
    """
    url = os.getenv("E2E_API_URL", "http://localhost:8000")
    logger.info("E2E tests will run against", url=url)
    return url


@pytest.fixture(scope="session")
def e2e_auth_token() -> str:
    """
    Get authentication token for E2E tests.

    Set via E2E_AUTH_TOKEN environment variable.
    """
    token = os.getenv("E2E_AUTH_TOKEN")
    if not token:
        pytest.skip("E2E_AUTH_TOKEN environment variable not set")
    return token


@pytest.fixture
async def e2e_client(api_base_url: str, e2e_auth_token: str) -> AsyncClient:
    """Create authenticated async HTTP client for E2E tests."""
    async with AsyncClient(
        base_url=api_base_url,
        headers={
            "Authorization": f"Bearer {e2e_auth_token}",
            "Content-Type": "application/json",
        },
        timeout=300.0,  # 5 minutes for LLM calls
    ) as client:
        yield client


@pytest.fixture(scope="session")
def e2e_tenant_id() -> str:
    """Get test tenant ID for E2E tests."""
    tenant_id = os.getenv("E2E_TENANT_ID", "test_tenant_e2e")
    return tenant_id


@pytest.fixture(scope="session")
def e2e_user_id() -> str:
    """Get test user ID for E2E tests."""
    user_id = os.getenv("E2E_USER_ID", "test_user_e2e")
    return user_id


@pytest.fixture(scope="session")
def aws_region() -> str:
    """Get AWS region for E2E tests."""
    region = os.getenv("AWS_REGION", "us-east-1")
    return region


@pytest.fixture(scope="session")
def check_aws_credentials() -> None:
    """Verify AWS credentials are configured."""
    if not os.getenv("AWS_PROFILE") and not (
        os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    ):
        pytest.skip("AWS credentials not configured. Set AWS_PROFILE or AWS credentials.")


@pytest.fixture(scope="session")
def check_openai_credentials() -> None:
    """Verify OpenAI credentials are configured."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not configured")


@pytest.fixture(scope="session")
def check_google_credentials() -> None:
    """Verify Google Cloud credentials are configured."""
    if not os.getenv("GOOGLE_PROJECT_ID"):
        pytest.skip("GOOGLE_PROJECT_ID not configured for Vertex AI")


__all__ = [
    "api_base_url",
    "aws_region",
    "check_aws_credentials",
    "check_google_credentials",
    "check_openai_credentials",
    "e2e_auth_token",
    "e2e_client",
    "e2e_tenant_id",
    "e2e_user_id",
]
