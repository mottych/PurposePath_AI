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
    # Try to get credentials using boto3 (works with env vars, config files, and IAM roles)
    try:
        import boto3
        sts = boto3.client("sts")
        sts.get_caller_identity()
        # If we get here, credentials are valid
    except Exception:
        pytest.skip("AWS credentials not configured or invalid. Configure AWS CLI or set credentials.")


@pytest.fixture(scope="session")
def check_openai_credentials() -> None:
    """Verify OpenAI credentials are configured."""
    # Try to get from environment variable first
    if os.getenv("OPENAI_API_KEY"):
        return

    # Try to get from AWS Secrets Manager
    try:
        from coaching.src.core.config_multitenant import get_openai_api_key
        api_key = get_openai_api_key()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            return
    except Exception:
        pass

    pytest.skip("OPENAI_API_KEY not configured. Set environment variable or configure in AWS Secrets Manager.")


@pytest.fixture(scope="session")
def check_google_credentials() -> None:
    """Verify Google Cloud credentials are configured."""
    # Try environment variables first
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_PROJECT_ID"):
        return

    # Try to get from AWS Secrets Manager
    try:
        from coaching.src.core.config_multitenant import get_google_vertex_credentials
        creds_dict = get_google_vertex_credentials()
        if creds_dict and creds_dict.get("project_id"):
            return
    except Exception:
        pass

    pytest.skip("Google Cloud credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS or configure in AWS Secrets Manager.")


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
