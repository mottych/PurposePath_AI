"""Redis cache implementation for conversation sessions.

This module provides a Redis-backed cache for conversation data,
improving performance by reducing database queries.
"""

import json
from datetime import timedelta
from typing import Any

import structlog

logger = structlog.get_logger()


class RedisCache:
    """
    Redis-backed cache for conversation sessions.

    Design:
        - TTL-based automatic expiration
        - JSON serialization for complex objects
        - Prefix-based key namespacing
        - Observability hooks
    """

    def __init__(self, redis_client: Any, key_prefix: str = "coaching:", default_ttl: int = 3600):
        """
        Initialize Redis cache.

        Args:
            redis_client: Redis client instance
            key_prefix: Prefix for all keys (default: "coaching:")
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_ttl = default_ttl
        logger.info("Redis cache initialized", prefix=key_prefix, default_ttl=default_ttl)

    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if found, None otherwise
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            value = self.redis.get(full_key)

            if value is None:
                logger.debug("Cache miss", key=key)
                return None

            # Deserialize JSON
            deserialized = json.loads(value)
            logger.debug("Cache hit", key=key)
            return deserialized

        except Exception as e:
            logger.error("Cache get failed", key=key, error=str(e))
            return None  # Fail gracefully

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
            True if successful, False otherwise
        """
        try:
            full_key = f"{self.key_prefix}{key}"

            # Serialize to JSON
            serialized = json.dumps(value)

            # Determine TTL
            ttl_seconds = int(ttl_delta.total_seconds()) if ttl_delta else ttl or self.default_ttl

            # Set with TTL
            self.redis.setex(full_key, ttl_seconds, serialized)

            logger.debug("Cache set", key=key, ttl=ttl_seconds)
            return True

        except Exception as e:
            logger.error("Cache set failed", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found or error
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            result = self.redis.delete(full_key)

            logger.debug("Cache delete", key=key, deleted=result > 0)
            return result > 0  # type: ignore[no-any-return]

        except Exception as e:
            logger.error("Cache delete failed", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        try:
            full_key = f"{self.key_prefix}{key}"
            return bool(self.redis.exists(full_key))

        except Exception as e:
            logger.error("Cache exists check failed", key=key, error=str(e))
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.

        Args:
            pattern: Key pattern (supports * wildcards)

        Returns:
            Number of keys deleted
        """
        try:
            full_pattern = f"{self.key_prefix}{pattern}"
            keys = self.redis.keys(full_pattern)

            if not keys:
                return 0

            deleted = self.redis.delete(*keys)
            logger.info("Cache pattern cleared", pattern=pattern, count=deleted)
            return deleted  # type: ignore[no-any-return]

        except Exception as e:
            logger.error("Cache pattern clear failed", pattern=pattern, error=str(e))
            return 0


__all__ = ["RedisCache"]
