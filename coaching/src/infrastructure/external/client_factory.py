"""Factory functions for creating external API clients."""

from src.core.config import get_settings
from src.infrastructure.external.business_api_client import BusinessApiClient


def create_business_api_client(jwt_token: str) -> BusinessApiClient:
    """
    Create configured BusinessApiClient instance.

    Factory function that creates a BusinessApiClient with configuration
    from application settings. This ensures consistent configuration across
    the application and supports dependency injection.

    Args:
        jwt_token: JWT authentication token from user session

    Returns:
        Configured BusinessApiClient instance

    Example:
        ```python
        # In FastAPI dependency
        async def get_business_client(token: str = Depends(get_jwt_token)):
            return create_business_api_client(token)

        # In application code
        client = create_business_api_client(user_jwt_token)
        user_context = await client.get_user_context(user_id, tenant_id)
        ```

    Configuration:
        Uses settings from environment variables:
        - BUSINESS_API_BASE_URL: Base URL for Business API
        - BUSINESS_API_TIMEOUT: Request timeout in seconds
        - BUSINESS_API_MAX_RETRIES: Maximum retry attempts
    """
    settings = get_settings()

    return BusinessApiClient(
        base_url=settings.business_api_base_url,
        jwt_token=jwt_token,
        timeout=settings.business_api_timeout,
        max_retries=settings.business_api_max_retries,
    )


__all__ = ["create_business_api_client"]
