import asyncio

import pytest
from coaching.src.infrastructure.cache.in_memory_cache import InMemoryCache

pytestmark = pytest.mark.unit


class TestInMemoryCache:
    """Test suite for InMemoryCache."""

    @pytest.fixture
    def cache(self) -> InMemoryCache:
        return InMemoryCache(default_ttl=60)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: InMemoryCache) -> None:
        """Test setting and getting a value."""
        await cache.set("key", "value")
        result = await cache.get("key")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache: InMemoryCache) -> None:
        """Test getting a key that doesn't exist."""
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache: InMemoryCache) -> None:
        """Test that values expire after TTL."""
        # Set with very short TTL
        await cache.set("key", "value", ttl=1)

        # Should exist immediately
        assert await cache.get("key") == "value"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be gone
        assert await cache.get("key") is None

    @pytest.mark.asyncio
    async def test_delete(self, cache: InMemoryCache) -> None:
        """Test deleting a value."""
        await cache.set("key", "value")
        await cache.delete("key")
        assert await cache.get("key") is None

    @pytest.mark.asyncio
    async def test_clear_all(self, cache: InMemoryCache) -> None:
        """Test clearing the cache."""
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")

        cache.clear_all()

        assert await cache.get("key1") is None
        assert await cache.get("key2") is None

    @pytest.mark.asyncio
    async def test_exists(self, cache: InMemoryCache) -> None:
        """Test checking if a key exists."""
        await cache.set("key", "value")
        assert await cache.exists("key") is True
        assert await cache.exists("nonexistent") is False
