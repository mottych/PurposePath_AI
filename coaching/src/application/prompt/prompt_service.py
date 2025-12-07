"""Prompt application service.

This service orchestrates prompt template management use cases,
supporting both end-user consumption and admin UI management.
"""

import structlog
from coaching.src.core.constants import CoachingTopic
from coaching.src.core.types import PromptTemplateId
from coaching.src.domain.entities.prompt_template import PromptTemplate
from coaching.src.domain.ports.prompt_repository_port import PromptRepositoryPort

logger = structlog.get_logger()


class PromptApplicationService:
    """
    Application service for prompt template management.

    This service implements prompt-related use cases for both:
    - End users: Retrieve templates for coaching conversations
    - Admin users: CRUD operations for template management

    Design Principles:
        - Dependency injection (depends on ports)
        - Separate read and write use cases
        - Version management built-in
        - Cache-friendly operations
    """

    def __init__(self, prompt_repository: PromptRepositoryPort):
        """
        Initialize prompt application service.

        Args:
            prompt_repository: Repository for prompt template persistence
        """
        self.repository = prompt_repository
        logger.info("Prompt application service initialized")

    # ========== Read Operations (End User) ==========

    async def get_template_for_topic(
        self, topic: CoachingTopic, version: str = "latest"
    ) -> PromptTemplate | None:
        """
        Get prompt template for a coaching topic.

        Use Case: Retrieve template for conversation (end user)

        Args:
            topic: The coaching topic
            version: Template version (default: "latest")

        Returns:
            PromptTemplate if found, None otherwise
        """
        template = await self.repository.get_by_topic(topic, version)

        if template:
            logger.debug(
                "Template retrieved",
                topic=topic.value,
                version=version,
                template_id=template.template_id,
            )
        else:
            logger.warning("Template not found", topic=topic.value, version=version)

        return template

    async def get_template_by_id(self, template_id: PromptTemplateId) -> PromptTemplate | None:
        """
        Get prompt template by ID.

        Use Case: Direct template retrieval by ID

        Args:
            template_id: Unique template identifier

        Returns:
            PromptTemplate if found, None otherwise
        """
        template = await self.repository.get_by_id(template_id)

        if template:
            logger.debug("Template retrieved by ID", template_id=template_id)
        else:
            logger.warning("Template not found by ID", template_id=template_id)

        return template

    async def list_template_versions(self, topic: CoachingTopic) -> list[str]:
        """
        List all available versions for a topic.

        Use Case: Display version history (admin UI)

        Args:
            topic: The coaching topic

        Returns:
            List of version strings (newest first)
        """
        versions = await self.repository.list_versions(topic)

        logger.debug("Template versions listed", topic=topic.value, count=len(versions))

        return versions  # type: ignore[no-any-return]

    async def template_exists(self, topic: CoachingTopic, version: str = "latest") -> bool:
        """
        Check if a template exists.

        Use Case: Validation before using template

        Args:
            topic: The coaching topic
            version: Template version

        Returns:
            True if exists, False otherwise
        """
        exists = await self.repository.exists(topic, version)

        logger.debug(
            "Template existence checked", topic=topic.value, version=version, exists=exists
        )

        return exists  # type: ignore[no-any-return]

    # ========== Write Operations (Admin UI) ==========

    async def create_template(self, template: PromptTemplate, version: str) -> None:
        """
        Create a new prompt template version.

        Use Case: Admin creates new template version

        Args:
            template: The prompt template entity
            version: Version identifier

        Raises:
            ValueError: If version already exists or format invalid
        """
        try:
            await self.repository.save(template, version)

            logger.info(
                "Template created",
                topic=template.topic.value,
                version=version,
                template_id=template.template_id,
            )

        except ValueError as e:
            logger.error(
                "Template creation failed",
                topic=template.topic.value,
                version=version,
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Template creation failed",
                topic=template.topic.value,
                version=version,
                error=str(e),
            )
            raise

    async def update_template(self, template: PromptTemplate, version: str) -> None:
        """
        Update template (creates new version - templates are immutable).

        Use Case: Admin updates template (actually creates new version)

        Args:
            template: The updated prompt template entity
            version: New version identifier

        Raises:
            ValueError: If version already exists

        Note: Templates are immutable, so "update" creates a new version
        """
        await self.create_template(template, version)

        logger.info(
            "Template updated (new version created)",
            topic=template.topic.value,
            version=version,
        )

    async def delete_template_version(self, topic: CoachingTopic, version: str) -> bool:
        """
        Delete a specific template version.

        Use Case: Admin deletes old/unused template version

        Args:
            topic: The coaching topic
            version: Version to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If trying to delete "latest" version

        Business Rule: Cannot delete latest version without reassignment
        """
        try:
            deleted = await self.repository.delete(topic, version)

            if deleted:
                logger.info("Template version deleted", topic=topic.value, version=version)
            else:
                logger.warning(
                    "Template version not found for deletion", topic=topic.value, version=version
                )

            return deleted  # type: ignore[no-any-return]

        except ValueError as e:
            logger.error(
                "Cannot delete template version", topic=topic.value, version=version, error=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "Template deletion failed", topic=topic.value, version=version, error=str(e)
            )
            raise

    async def set_latest_version(self, topic: CoachingTopic, version: str) -> None:
        """
        Mark a version as the latest/production version.

        Use Case: Admin promotes version to production

        Args:
            topic: The coaching topic
            version: Version to mark as latest

        Raises:
            ValueError: If version doesn't exist
        """
        try:
            await self.repository.set_latest(topic, version)

            logger.info("Latest version updated", topic=topic.value, version=version)

        except ValueError as e:
            logger.error(
                "Cannot set latest version", topic=topic.value, version=version, error=str(e)
            )
            raise
        except Exception as e:
            logger.error(
                "Set latest version failed", topic=topic.value, version=version, error=str(e)
            )
            raise

    async def create_draft_from_version(
        self, topic: CoachingTopic, source_version: str, draft_version: str
    ) -> PromptTemplate:
        """
        Create a draft version by copying an existing version.

        Use Case: Admin creates draft for editing from production template

        Args:
            topic: The coaching topic
            source_version: Version to copy from (e.g., "v2.0")
            draft_version: New draft version (e.g., "v2.1-draft")

        Returns:
            The newly created draft template

        Raises:
            ValueError: If source doesn't exist or draft already exists

        Typical workflow:
        1. create_draft_from_version("goals", "v2.0", "v2.1-draft")
        2. Admin edits draft in UI
        3. create_template(edited_template, "v2.1")
        4. set_latest_version("goals", "v2.1")
        """
        try:
            new_template = await self.repository.create_new_version(
                topic, source_version, draft_version
            )

            logger.info(
                "Draft template created",
                topic=topic.value,
                source=source_version,
                draft=draft_version,
            )

            return new_template

        except ValueError as e:
            logger.error(
                "Draft creation failed",
                topic=topic.value,
                source=source_version,
                draft=draft_version,
                error=str(e),
            )
            raise
        except Exception as e:
            logger.error(
                "Draft creation failed",
                topic=topic.value,
                source=source_version,
                draft=draft_version,
                error=str(e),
            )
            raise


__all__ = ["PromptApplicationService"]
