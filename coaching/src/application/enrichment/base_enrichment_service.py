"""Base enrichment service.

This module provides the abstract base for enrichment services,
defining common patterns for adding context to analysis requests.
"""

from abc import ABC, abstractmethod
from typing import Any

import structlog
from src.infrastructure.cache.in_memory_cache import InMemoryCache

logger = structlog.get_logger()


class BaseEnrichmentService(ABC):
    """
    Abstract base class for enrichment services.

    Enrichment services add business context to analysis requests,
    pulling data from external sources and caching for performance.

    Design Principles:
        - Template Method pattern
        - Caching for performance
        - Graceful degradation on failures
        - Timeout protection
        - Mock-friendly for testing
    """

    def __init__(self, cache: InMemoryCache | None = None, cache_ttl: int = 3600):
        """
        Initialize base enrichment service.

        Args:
            cache: Optional cache implementation (defaults to in-memory)
            cache_ttl: Cache TTL in seconds (default: 1 hour)
        """
        self.cache = cache or InMemoryCache(default_ttl=cache_ttl)
        self.cache_ttl = cache_ttl
        logger.info(f"{self.__class__.__name__} initialized with caching")

    @abstractmethod
    def get_enrichment_type(self) -> str:
        """
        Get the enrichment type identifier.

        Returns:
            Enrichment type string

        Implemented by subclasses.
        """
        pass

    @abstractmethod
    async def fetch_enrichment_data(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Fetch enrichment data from external sources.

        Args:
            context: Request context with identifiers

        Returns:
            Enrichment data

        Implemented by subclasses to fetch type-specific data.
        Must handle errors gracefully and return partial data if needed.
        """
        pass

    def build_cache_key(self, context: dict[str, Any]) -> str:
        """
        Build cache key from context.

        Args:
            context: Request context

        Returns:
            Cache key string

        Can be overridden for custom cache key logic.
        """
        enrichment_type = self.get_enrichment_type()
        user_id = context.get("user_id", "unknown")
        tenant_id = context.get("tenant_id", "unknown")

        return f"enrichment:{enrichment_type}:{tenant_id}:{user_id}"

    async def enrich(self, context: dict[str, Any], use_cache: bool = True) -> dict[str, Any]:
        """
        Enrich context with additional data (Template Method).

        This is the main entry point for enrichment.

        Workflow:
        1. Build cache key
        2. Check cache if enabled
        3. Fetch data if cache miss
        4. Cache result
        5. Return enriched context

        Args:
            context: Base context to enrich
            use_cache: Whether to use caching

        Returns:
            Enriched context with additional data

        Note: Never fails - returns original context on error
        """
        enrichment_type = self.get_enrichment_type()

        try:
            logger.info("Enrichment started", enrichment_type=enrichment_type)

            # Build cache key
            cache_key = self.build_cache_key(context)

            # Check cache
            if use_cache:
                cached_data = await self.cache.get(cache_key)
                if cached_data:
                    logger.info("Enrichment cache hit", enrichment_type=enrichment_type)
                    return {**context, **cached_data}

            # Fetch enrichment data
            enrichment_data = await self.fetch_enrichment_data(context)

            # Cache result
            if use_cache and enrichment_data:
                await self.cache.set(cache_key, enrichment_data, ttl=self.cache_ttl)

            # Merge with original context
            enriched_context = {**context, **enrichment_data}

            logger.info(
                "Enrichment completed",
                enrichment_type=enrichment_type,
                keys_added=len(enrichment_data),
            )

            return enriched_context

        except Exception as e:
            # Graceful degradation - return original context
            logger.error(
                "Enrichment failed, returning original context",
                enrichment_type=enrichment_type,
                error=str(e),
            )
            return context


__all__ = ["BaseEnrichmentService"]
