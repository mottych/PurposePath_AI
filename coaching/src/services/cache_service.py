"""Cache service for managing Redis operations."""

import json
from datetime import timedelta
from typing import Any

import structlog

from src.core.config import settings

logger = structlog.get_logger()


class CacheService:
    """Service for Redis caching operations."""

    def __init__(self, redis_client: Any, key_prefix: str = ""):
        """Initialize cache service.

        Args:
            redis_client: Redis client instance
            key_prefix: Optional prefix to namespace keys (e.g., per-tenant)
        """
        self.redis = redis_client
        self.key_prefix = key_prefix or ""
        self.default_ttl = timedelta(hours=settings.session_ttl_hours)

    def _k(self, key: str) -> str:
        return f"{self.key_prefix}{key}" if self.key_prefix else key

    async def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            value = self.redis.get(self._k(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: Any, ttl: timedelta | None = None) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live

        Returns:
            True if successful
        """
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(value, default=str)
            return bool(self.redis.setex(self._k(key), ttl, serialized))
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        try:
            return bool(self.redis.delete(self._k(key)))
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False

    async def get_conversation_memory(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation memory from cache.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Memory data or None
        """
        key = f"memory:{conversation_id}"
        return await self.get(key)

    async def save_conversation_memory(
        self, conversation_id: str, memory_data: dict[str, Any]
    ) -> bool:
        """Save conversation memory to cache.

        Args:
            conversation_id: Conversation identifier
            memory_data: Memory data

        Returns:
            True if successful
        """
        key = f"memory:{conversation_id}"
        return await self.set(key, memory_data)

    async def get_session_data(self, conversation_id: str) -> dict[str, Any] | None:
        """Get session data from cache.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Session data or None
        """
        key = f"session:{conversation_id}"
        return await self.get(key)

    async def save_session_data(self, conversation_id: str, session_data: dict[str, Any]) -> bool:
        """Save session data to cache.

        Args:
            conversation_id: Conversation identifier
            session_data: Session data

        Returns:
            True if successful
        """
        key = f"session:{conversation_id}"
        return await self.set(key, session_data)
