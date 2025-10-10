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
        - CRUD support: Full create, read, update, delete operations for admin UI
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

    async def save(self, template: PromptTemplate, version: str) -> None:
        """
        Save a prompt template with a specific version.

        Args:
            template: The prompt template entity to save
            version: Version identifier for this template

        Raises:
            ValueError: If version format is invalid
            RepositoryError: If save operation fails

        Business Rule: Saving creates a new immutable version
        Business Rule: Existing versions cannot be overwritten
        """
        ...

    async def delete(self, topic: CoachingTopic, version: str) -> bool:
        """
        Delete a specific version of a prompt template.

        Args:
            topic: The coaching topic
            version: Version identifier to delete

        Returns:
            True if deleted, False if version not found

        Business Rule: Cannot delete the "latest" marked version without reassignment
        Business Rule: Deletion is permanent (no soft delete)
        """
        ...

    async def set_latest(self, topic: CoachingTopic, version: str) -> None:
        """
        Mark a specific version as the "latest" for a topic.

        Args:
            topic: The coaching topic
            version: Version identifier to mark as latest

        Raises:
            ValueError: If version does not exist

        Business Rule: Only one version can be "latest" at a time
        Business Rule: Latest version is used when version="latest" in queries
        """
        ...

    async def create_new_version(
        self, topic: CoachingTopic, source_version: str, new_version: str
    ) -> PromptTemplate:
        """
        Create a new version by copying an existing version.

        Args:
            topic: The coaching topic
            source_version: Version to copy from
            new_version: New version identifier

        Returns:
            The newly created template

        Raises:
            ValueError: If source version doesn't exist or new version already exists

        Business Rule: Useful for creating draft versions from production templates
        """
        ...


__all__ = ["PromptRepositoryPort"]
