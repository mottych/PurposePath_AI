"""Service for fetching and caching user limits from Account API."""

import time
from typing import Any

import httpx
import structlog
from coaching.src.core.config_multitenant import get_settings

logger = structlog.get_logger(__name__)


class UserLimitsCache:
    """Cache for user limits with token-aware invalidation."""

    def __init__(self, ttl_seconds: int = 300):  # 5 minutes default
        """Initialize cache.

        Args:
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self._cache: dict[str, tuple[dict[str, Any], float, str]] = {}  # user_id -> (limits, timestamp, token_hash)
        self._ttl = ttl_seconds

    def get(self, user_id: str, token: str) -> dict[str, Any] | None:
        """Get cached limits for user if valid.

        Args:
            user_id: User identifier
            token: Current JWT token

        Returns:
            Cached limits or None if expired or token changed
        """
        if user_id not in self._cache:
            return None

        limits, timestamp, cached_token_hash = self._cache[user_id]
        current_time = time.time()
        token_hash = hash(token)

        # Invalidate if token changed or expired
        if token_hash != cached_token_hash or (current_time - timestamp) > self._ttl:
            del self._cache[user_id]
            return None

        return limits

    def set(self, user_id: str, token: str, limits: dict[str, Any]) -> None:
        """Cache limits for user.

        Args:
            user_id: User identifier
            token: Current JWT token
            limits: User limits data
        """
        self._cache[user_id] = (limits, time.time(), hash(token))

    def clear(self, user_id: str | None = None) -> None:
        """Clear cache for specific user or all users.

        Args:
            user_id: Optional user to clear, or None to clear all
        """
        if user_id:
            self._cache.pop(user_id, None)
        else:
            self._cache.clear()


class UserLimitsService:
    """Service for fetching user limits from Account API."""

    def __init__(self, account_api_base_url: str | None = None, cache_ttl: int = 300):
        """Initialize service.

        Args:
            account_api_base_url: Base URL for Account API
            cache_ttl: Cache time-to-live in seconds
        """
        settings = get_settings()
        self._base_url = account_api_base_url or settings.account_api_url or "https://api.dev.purposepath.app"
        self._cache = UserLimitsCache(ttl_seconds=cache_ttl)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    async def get_user_limits(self, user_id: str, token: str) -> dict[str, Any]:
        """Fetch user limits from Account API with caching.

        Args:
            user_id: User identifier
            token: JWT token for authorization

        Returns:
            User limits data

        Raises:
            HTTPException: If API call fails
        """
        # Check cache first
        cached = self._cache.get(user_id, token)
        if cached is not None:
            logger.debug("User limits cache hit", user_id=user_id)
            return cached

        # Fetch from Account API
        try:
            client = await self._get_client()
            url = f"{self._base_url}/account/api/v1/users/me/limits"

            logger.info("Fetching user limits from Account API", url=url, user_id=user_id)

            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code == 200:
                response_data = response.json()
                # Account API returns {"success": true, "data": {...}}
                if response_data.get("success") and "data" in response_data:
                    limits = response_data["data"]
                    self._cache.set(user_id, token, limits)
                    logger.info("User limits fetched successfully", user_id=user_id, limits=limits)
                    return limits
                else:
                    logger.warning("Unexpected response format from Account API", response=response_data)
                    return self._get_default_limits()
            else:
                logger.warning(
                    "Failed to fetch user limits",
                    status_code=response.status_code,
                    response=response.text[:200],
                    user_id=user_id,
                )
                # Return default limits on failure
                return self._get_default_limits()

        except Exception as e:
            logger.error("Error fetching user limits", error=str(e), user_id=user_id)
            # Return default limits on error
            return self._get_default_limits()

    def _get_default_limits(self) -> dict[str, Any]:
        """Get default limits for users when API is unavailable.

        Returns:
            Default limits dictionary matching Account API structure
        """
        return {
            "goals": 10,
            "users": 100,
            "projects": 5,
            "api_calls_per_month": 10000,
            "storage_mb": 1000,
        }

    def check_limit(self, limits: dict[str, Any], limit_name: str, current_usage: int) -> bool:
        """Check if current usage is within limit.

        Args:
            limits: User limits dictionary
            limit_name: Name of the limit to check (e.g., "goals", "projects")
            current_usage: Current usage count

        Returns:
            True if within limit, False if exceeded
        """
        limit_value = limits.get(limit_name, 0)
        return current_usage < limit_value

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Global instance
_user_limits_service: UserLimitsService | None = None


def get_user_limits_service() -> UserLimitsService:
    """Get singleton user limits service.

    Returns:
        UserLimitsService instance
    """
    global _user_limits_service
    if _user_limits_service is None:
        _user_limits_service = UserLimitsService()
    return _user_limits_service
