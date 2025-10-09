"""Prompt repository port interface.

This module defines the protocol (interface) for prompt template persistence,
allowing different storage implementations (S3, filesystem, database, etc.)
to be used interchangeably.
"""

from typing import Protocol

from coaching.src.core.constants import CoachingTopic
from coaching.src.core.types import PromptTemplateId
from coaching.src.domain.entities.prompt_template import PromptTemplate


class PromptRepositoryPort(Protocol):
    """
    Port interface for prompt template persistence.

    This protocol defines the contract for prompt template repository implementations.
    Implementations must support versioning and caching.

    Design Principles:
        - Async-first: All operations are async
        - Versioned: Templates have versions for controlled rollouts
        - Cacheable: Templates can be cached for performance
        - Immutable: Templates are read-only after creation
    """

    async def get_by_topic(
        self, topic: CoachingTopic, version: str = "latest"
    ) -> PromptTemplate | None:
        """
        Retrieve a prompt template by topic and version.

        Args:
            topic: The coaching topic
            version: Template version (default: "latest")

        Returns:
            PromptTemplate entity if found, None otherwise

        Business Rule: "latest" version should resolve to the most recent stable version
        """
        ...

    async def get_by_id(self, template_id: PromptTemplateId) -> PromptTemplate | None:
        """
        Retrieve a prompt template by its unique ID.

        Args:
            template_id: Unique template identifier

        Returns:
            PromptTemplate entity if found, None otherwise

        Business Rule: Template IDs are globally unique across all versions
        """
        ...

    async def list_versions(self, topic: CoachingTopic) -> list[str]:
        """
        List all available versions for a topic.

        Args:
            topic: The coaching topic

        Returns:
            List of version strings, ordered from newest to oldest

        Business Rule: Results must be ordered by version timestamp (newest first)
        """
        ...

    async def exists(self, topic: CoachingTopic, version: str = "latest") -> bool:
        """
        Check if a prompt template exists.

        Args:
            topic: The coaching topic
            version: Template version (default: "latest")

        Returns:
            True if template exists, False otherwise

        Business Rule: "latest" version should resolve before checking existence
        """
        ...


__all__ = ["PromptRepositoryPort"]
