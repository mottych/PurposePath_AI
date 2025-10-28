"""In-memory cache implementation for testing and development.

This module provides a simple in-memory cache for conversation data,
useful for testing and local development.
"""

import time
from datetime import timedelta
from typing import Any

import structlog

logger = structlog.get_logger()


class InMemoryCache:
    """
    Simple in-memory cache for testing and development.

    Design:
        - Dictionary-based storage
        - TTL-based expiration
        - Thread-safe operations
        - No persistence (data lost on restart)
    """

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize in-memory cache.

        Args:
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self._cache: dict[str, tuple[Any, float]] = {}  # key -> (value, expiry_time)
        self.default_ttl = default_ttl
        logger.info("In-memory cache initialized", default_ttl=default_ttl)

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            logger.debug("Cache miss", key=key)
            return None

        value, expiry = self._cache[key]

        # Check expiration
        if time.time() > expiry:
            # Expired, remove and return None
            del self._cache[key]
            logger.debug("Cache expired", key=key)
            return None

        logger.debug("Cache hit", key=key)
        return value

    async def set(
        self, key: str, value: Any, ttl: int | None = None, ttl_delta: timedelta | None = None
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (overrides default)
            ttl_delta: TTL as timedelta (alternative to ttl)

        Returns:
            True (always successful in memory)
        """
        # Determine TTL
        ttl_seconds = int(ttl_delta.total_seconds()) if ttl_delta else ttl or self.default_ttl

        # Calculate expiry time
        expiry = time.time() + ttl_seconds

        # Store with expiry
        self._cache[key] = (value, expiry)

        logger.debug("Cache set", key=key, ttl=ttl_seconds)
        return True

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug("Cache delete", key=key, deleted=True)
            return True

        logger.debug("Cache delete", key=key, deleted=False)
        return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists and not expired, False otherwise
        """
        # Use get to check existence and expiry
        value = await self.get(key)
        return value is not None

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Key pattern (supports * wildcards)

        Returns:
            Number of keys deleted
        """
        # Convert pattern to regex-like matching
        import re

        regex_pattern = pattern.replace("*", ".*")
        pattern_re = re.compile(f"^{regex_pattern}$")

        # Find matching keys
        matching_keys = [key for key in self._cache if pattern_re.match(key)]

        # Delete matching keys
        for key in matching_keys:
            del self._cache[key]

        logger.info("Cache pattern cleared", pattern=pattern, count=len(matching_keys))
        return len(matching_keys)

    def clear_all(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info("Cache cleared", count=count)


__all__ = ["InMemoryCache"]
