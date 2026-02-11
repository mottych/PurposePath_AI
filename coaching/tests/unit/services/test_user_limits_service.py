import time
from unittest.mock import Mock, patch

import pytest
from coaching.src.services.user_limits_service import UserLimitsCache, UserLimitsService

pytestmark = pytest.mark.unit


class TestUserLimitsCache:
    """Test suite for UserLimitsCache."""

    def test_cache_set_and_get(self) -> None:
        """Test setting and getting limits."""
        cache = UserLimitsCache(ttl_seconds=60)
        user_id = "user1"
        token = "token1"
        limits = {"max_conversations": 10}

        cache.set(user_id, token, limits)
        result = cache.get(user_id, token)

        assert result == limits

    def test_cache_miss(self) -> None:
        """Test cache miss."""
        cache = UserLimitsCache()
        assert cache.get("user1", "token1") is None

    def test_cache_expiration(self) -> None:
        """Test cache expiration."""
        cache = UserLimitsCache(ttl_seconds=1)
        user_id = "user1"
        token = "token1"
        limits = {"max_conversations": 10}

        cache.set(user_id, token, limits)
        time.sleep(1.1)

        assert cache.get(user_id, token) is None

    def test_token_change_invalidates_cache(self) -> None:
        """Test that changing the token invalidates the cache."""
        cache = UserLimitsCache()
        user_id = "user1"
        token1 = "token1"
        token2 = "token2"
        limits = {"max_conversations": 10}

        cache.set(user_id, token1, limits)
        assert cache.get(user_id, token2) is None


class TestUserLimitsService:
    """Test suite for UserLimitsService."""

    @pytest.fixture
    def service(self) -> UserLimitsService:
        return UserLimitsService()

    @pytest.mark.asyncio
    async def test_get_user_limits_cached(self) -> None:
        """Test getting limits from cache."""
        service = UserLimitsService()
        user_id = "user1"
        token = "token1"
        limits = {"max_conversations": 10}

        # Pre-populate cache
        service._cache.set(user_id, token, limits)

        result = await service.get_user_limits(user_id, token)
        assert result == limits

    @pytest.mark.asyncio
    async def test_get_user_limits_api_call(self) -> None:
        """Test getting limits from API when cache is empty."""
        service = UserLimitsService()
        user_id = "user1"
        token = "token1"
        expected_limits = {"max_conversations": 10}
        api_response = {"success": True, "data": expected_limits}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = api_response

            # Make get return an awaitable
            async def async_get(*args, **kwargs):
                return mock_response

            mock_client.get.side_effect = async_get

            result = await service.get_user_limits(user_id, token)

            assert result == expected_limits
            # Verify cache was updated
            assert service._cache.get(user_id, token) == expected_limits

    @pytest.mark.asyncio
    async def test_get_user_limits_api_error(self) -> None:
        """Test handling API error."""
        service = UserLimitsService()
        user_id = "user1"
        token = "token1"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.__aenter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 500

            # Make get return an awaitable
            async def async_get(*args, **kwargs):
                return mock_response

            mock_client.get.side_effect = async_get

            # Should return default limits on error
            result = await service.get_user_limits(user_id, token)

            # Check that result contains default keys
            assert "goals" in result
            assert "users" in result
            assert "projects" in result
