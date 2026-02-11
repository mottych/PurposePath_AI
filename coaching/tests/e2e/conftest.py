"""Pytest configuration for E2E tests.

E2E tests require:
- Real AWS credentials configured
- Deployed API endpoint (AWS Lambda)
- Real LLM provider access (Bedrock, OpenAI, Google Vertex)

Environment Variables:
- E2E_API_URL: The deployed API URL (default: direct Lambda API Gateway URL)
- E2E_AUTH_TOKEN: Optional - if not set, will login automatically
- E2E_TEST_EMAIL: Login email (default: motty@purposepath.ai)
- E2E_TEST_PASSWORD: Login password (required if E2E_AUTH_TOKEN not set)

Default URLs (Direct API Gateway, not custom domain):
- Coaching API: https://q2tt1svtza.execute-api.us-east-1.amazonaws.com
- Account API: https://wc99xync24.execute-api.us-east-1.amazonaws.com/api/v1
"""

import os
from typing import Any

import httpx
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

    Default is the deployed dev environment on AWS.
    Uses the direct Lambda/API Gateway URL (not custom domain due to SSL issues).
    """
    # Default to direct API Gateway URL for coaching API
    # Custom domain has SSL certificate issues, so use direct URL
    default_url = "https://q2tt1svtza.execute-api.us-east-1.amazonaws.com"
    url = os.getenv("E2E_API_URL", default_url)
    logger.info("E2E tests will run against", url=url)
    return url


@pytest.fixture(scope="session")
def account_api_url() -> str:
    """Get Account API URL for authentication."""
    # Direct API Gateway URL for account API
    default_url = "https://wc99xync24.execute-api.us-east-1.amazonaws.com/api/v1"
    return os.getenv("E2E_ACCOUNT_API_URL", default_url)


def _get_auth_token_from_login(account_url: str) -> dict[str, Any]:
    """
    Login to get authentication token.

    Uses credentials from environment variables:
    - E2E_TEST_EMAIL: Login email
    - E2E_TEST_PASSWORD: Login password

    Returns:
        Dict with access_token, user_id, and tenant_id
    """
    email = os.getenv("E2E_TEST_EMAIL", "motty@purposepath.ai")
    password = os.getenv("E2E_TEST_PASSWORD")

    if not password:
        raise ValueError(
            "E2E_TEST_PASSWORD environment variable required for automatic login. "
            "Set E2E_AUTH_TOKEN directly to skip login."
        )

    logger.info("Logging in to get auth token", email=email, account_url=account_url)

    # Direct API Gateway URLs use valid AWS SSL certificates
    with httpx.Client(verify=True, timeout=30.0) as client:
        response = client.post(
            f"{account_url}/auth/login",
            json={"email": email, "password": password},
        )

        if response.status_code != 200:
            raise ValueError(f"Login failed with status {response.status_code}: {response.text}")

        data = response.json()
        response_data = data.get("data", {})
        # API returns camelCase: accessToken, not access_token
        access_token = response_data.get("accessToken") or response_data.get("access_token")

        if not access_token:
            raise ValueError(f"No access_token in login response: {data}")

        user_data = response_data.get("user", {}) or {}
        # Handle both camelCase and snake_case field names
        user_id = user_data.get("id") or user_data.get("user_id") or user_data.get("userId")
        tenant_id = user_data.get("tenantId") or user_data.get("tenant_id")

        logger.info(
            "Login successful",
            email=email,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        return {
            "access_token": access_token,
            "user_id": user_id,
            "tenant_id": tenant_id,
        }


# Cache for auth data to avoid multiple logins
_auth_data_cache: dict[str, Any] | None = None


@pytest.fixture(scope="session")
def e2e_auth_data(account_api_url: str) -> dict[str, Any]:
    """
    Get authentication data (token, user_id, tenant_id).

    Will use E2E_AUTH_TOKEN if set, otherwise login automatically.
    """
    global _auth_data_cache

    if _auth_data_cache is not None:
        return _auth_data_cache

    # Check for direct token first
    token = os.getenv("E2E_AUTH_TOKEN")
    if token:
        logger.info("Using E2E_AUTH_TOKEN from environment")
        _auth_data_cache = {
            "access_token": token,
            "user_id": os.getenv("E2E_USER_ID", "unknown"),
            "tenant_id": os.getenv("E2E_TENANT_ID", "unknown"),
        }
        return _auth_data_cache

    # Login to get token
    try:
        _auth_data_cache = _get_auth_token_from_login(account_api_url)
        return _auth_data_cache
    except ValueError as e:
        pytest.skip(str(e))
        return {}  # Never reached, but keeps type checker happy


@pytest.fixture(scope="session")
def e2e_auth_token(e2e_auth_data: dict[str, Any]) -> str:
    """
    Get authentication token for E2E tests.

    Will login automatically if E2E_AUTH_TOKEN not set.
    """
    return e2e_auth_data["access_token"]


@pytest.fixture
async def e2e_client(api_base_url: str, e2e_auth_token: str) -> AsyncClient:
    """Create authenticated async HTTP client for E2E tests against deployed AWS."""
    logger.info("Creating E2E client", base_url=api_base_url)
    async with AsyncClient(
        base_url=api_base_url,
        headers={
            "Authorization": f"Bearer {e2e_auth_token}",
            "Content-Type": "application/json",
        },
        timeout=300.0,  # 5 minutes for LLM calls
        verify=True,  # Verify SSL for production
    ) as client:
        yield client


@pytest.fixture(scope="session")
def e2e_tenant_id(e2e_auth_data: dict[str, Any]) -> str:
    """Get test tenant ID from auth data."""
    return e2e_auth_data.get("tenant_id", "unknown")


@pytest.fixture(scope="session")
def e2e_user_id(e2e_auth_data: dict[str, Any]) -> str:
    """Get test user ID from auth data."""
    return e2e_auth_data.get("user_id", "unknown")


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
        pytest.skip(
            "AWS credentials not configured or invalid. Configure AWS CLI or set credentials."
        )


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

    pytest.skip(
        "OPENAI_API_KEY not configured. Set environment variable or configure in AWS Secrets Manager."
    )


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

    pytest.skip(
        "Google Cloud credentials not configured. Set GOOGLE_APPLICATION_CREDENTIALS or configure in AWS Secrets Manager."
    )


__all__ = [
    "account_api_url",
    "api_base_url",
    "aws_region",
    "check_aws_credentials",
    "check_google_credentials",
    "check_openai_credentials",
    "e2e_auth_data",
    "e2e_auth_token",
    "e2e_client",
    "e2e_tenant_id",
    "e2e_user_id",
]
