"""Topic Seeding Service - Automated topic initialization and updates.

This service handles seeding all topics from the endpoint registry and seed data
into DynamoDB and S3, enabling consistent topic configuration and easy updates.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog
from coaching.src.core.topic_registry import list_all_topics
from coaching.src.core.topic_seed_data import TopicSeedData, get_seed_data_for_topic
from coaching.src.domain.entities.llm_topic import LLMTopic, PromptInfo
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage

logger = structlog.get_logger()


# Backwards compatibility alias for tests
def list_all_endpoints(active_only: bool = True) -> list[Any]:
    """List all endpoints (backwards compatibility alias)."""
    return list_all_topics(active_only=active_only)


@dataclass
class SeedingResult:
    """Results of topic seeding operation.

    Attributes:
        created: Topic IDs that were newly created
        updated: Topic IDs that were updated
        skipped: Topic IDs that were skipped (already exist, no force update)
        deactivated: Topic IDs that were deactivated (orphaned)
        errors: List of (topic_id, error_message) tuples for failed operations
    """

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    deactivated: list[str] = field(default_factory=list)
    errors: list[tuple[str, str]] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        """Total number of topics processed."""
        return len(self.created) + len(self.updated) + len(self.skipped)

    @property
    def success_count(self) -> int:
        """Number of successful operations."""
        return len(self.created) + len(self.updated)

    @property
    def failure_count(self) -> int:
        """Number of failed operations."""
        return len(self.errors)

    @property
    def is_successful(self) -> bool:
        """Whether seeding completed without errors."""
        return self.failure_count == 0


@dataclass
class ValidationReport:
    """Validation report for topic configurations.

    Attributes:
        missing_topics: Endpoint definitions without seed data
        orphaned_topics: Topics in DB without endpoint definitions
        missing_prompts: Topics missing S3 prompts
        invalid_parameters: Topics with invalid parameter schemas
        is_valid: Whether all validations passed
    """

    missing_topics: list[str] = field(default_factory=list)
    orphaned_topics: list[str] = field(default_factory=list)
    missing_prompts: list[str] = field(default_factory=list)
    invalid_parameters: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Whether all validations passed."""
        return (
            not self.missing_topics
            and not self.orphaned_topics
            and not self.missing_prompts
            and not self.invalid_parameters
        )


class TopicSeedingService:
    """Service for seeding topics from registry to DynamoDB and S3.

    Handles automated topic initialization, updates, and validation
    to ensure endpoint registry and topic storage remain synchronized.
    """

    def __init__(
        self,
        *,
        topic_repo: TopicRepository,
        s3_storage: S3PromptStorage,
        default_created_by: str = "system_seeder",
    ) -> None:
        """Initialize topic seeding service.

        Args:
            topic_repo: Repository for topic CRUD operations
            s3_storage: Storage service for prompt content
            default_created_by: Default creator identifier for seeded topics
        """
        self.topic_repo = topic_repo
        self.s3_storage = s3_storage
        self.default_created_by = default_created_by

    async def seed_all_topics(
        self,
        *,
        force_update: bool = False,
        dry_run: bool = False,
    ) -> SeedingResult:
        """Seed all topics from endpoint registry and seed data.

        Args:
            force_update: Update existing topics even if they exist
            dry_run: Don't make changes, just report what would happen

        Returns:
            SeedingResult with created/updated/skipped/deactivated counts and errors
        """
        result = SeedingResult()

        logger.info(
            "Starting topic seeding",
            force_update=force_update,
            dry_run=dry_run,
        )

        # Get all active endpoints
        endpoints = list_all_topics(active_only=False)

        # Seed each endpoint's topic
        for endpoint in endpoints:
            topic_id = endpoint.topic_id

            try:
                # Get seed data
                seed_data = get_seed_data_for_topic(topic_id)
                if seed_data is None:
                    error_msg = f"No seed data found for topic {topic_id}"
                    logger.warning(error_msg, topic_id=topic_id)
                    result.errors.append((topic_id, error_msg))
                    continue

                # Check if topic exists
                existing_topic = await self.topic_repo.get(topic_id=topic_id)

                if existing_topic is None:
                    # Create new topic
                    if not dry_run:
                        await self._create_topic_from_seed(seed_data=seed_data)
                    result.created.append(topic_id)
                    logger.info(
                        "Topic created" if not dry_run else "Topic would be created",
                        topic_id=topic_id,
                        dry_run=dry_run,
                    )

                elif force_update:
                    # Update existing topic
                    if not dry_run:
                        await self._update_topic_from_seed(
                            existing_topic=existing_topic,
                            seed_data=seed_data,
                        )
                    result.updated.append(topic_id)
                    logger.info(
                        "Topic updated" if not dry_run else "Topic would be updated",
                        topic_id=topic_id,
                        dry_run=dry_run,
                    )

                else:
                    # Skip (already exists, no force update)
                    result.skipped.append(topic_id)
                    logger.debug("Topic skipped (already exists)", topic_id=topic_id)

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    "Failed to seed topic",
                    topic_id=topic_id,
                    error=error_msg,
                    exc_info=True,
                )
                result.errors.append((topic_id, error_msg))

        # Deactivate orphaned topics
        if not dry_run:
            deactivated = await self.deactivate_orphaned_topics(dry_run=dry_run)
            result.deactivated.extend(deactivated)

        logger.info(
            "Topic seeding completed",
            created=len(result.created),
            updated=len(result.updated),
            skipped=len(result.skipped),
            deactivated=len(result.deactivated),
            errors=len(result.errors),
            dry_run=dry_run,
        )

        return result

    async def seed_topic(
        self,
        *,
        topic_id: str,
        force_update: bool = False,
    ) -> bool:
        """Seed a single topic.

        Args:
            topic_id: Topic identifier to seed
            force_update: Update if already exists

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get seed data
            seed_data = get_seed_data_for_topic(topic_id)
            if seed_data is None:
                logger.error("No seed data found for topic", topic_id=topic_id)
                return False

            # Check if exists
            existing_topic = await self.topic_repo.get(topic_id=topic_id)

            if existing_topic is None:
                # Create new
                await self._create_topic_from_seed(seed_data=seed_data)
                logger.info("Topic created", topic_id=topic_id)
                return True

            elif force_update:
                # Update existing
                await self._update_topic_from_seed(
                    existing_topic=existing_topic,
                    seed_data=seed_data,
                )
                logger.info("Topic updated", topic_id=topic_id)
                return True

            else:
                logger.info("Topic already exists (use force_update=True)", topic_id=topic_id)
                return True

        except Exception as e:
            logger.error("Failed to seed topic", topic_id=topic_id, error=str(e), exc_info=True)
            return False

    async def deactivate_orphaned_topics(
        self,
        *,
        dry_run: bool = False,
    ) -> list[str]:
        """Deactivate topics that no longer have endpoints.

        Args:
            dry_run: Don't make changes, just report what would happen

        Returns:
            List of deactivated topic IDs
        """
        deactivated = []

        # Get all topics from DB
        all_topics = await self.topic_repo.list_all(include_inactive=False)

        # Get all endpoint topic IDs
        endpoints = list_all_topics(active_only=False)
        endpoint_topic_ids = {endpoint.topic_id for endpoint in endpoints}

        # Find orphaned topics
        for topic in all_topics:
            if topic.topic_id not in endpoint_topic_ids:
                if not dry_run:
                    # Soft delete (set is_active=False)
                    await self.topic_repo.delete(topic_id=topic.topic_id, hard_delete=False)

                deactivated.append(topic.topic_id)
                logger.info(
                    "Orphaned topic deactivated" if not dry_run else "Topic would be deactivated",
                    topic_id=topic.topic_id,
                    dry_run=dry_run,
                )

        return deactivated

    async def validate_topics(self) -> ValidationReport:
        """Validate all topics against endpoint registry.

        Checks:
        - All endpoints have topics
        - All topics have endpoints (or are orphaned)
        - All prompts exist in S3
        - All parameter schemas are valid

        Returns:
            ValidationReport with validation results
        """
        report = ValidationReport()

        # Get all endpoints and topics
        endpoints = list_all_topics(active_only=False)
        all_topics = await self.topic_repo.list_all(include_inactive=False)
        endpoint_topic_ids = {endpoint.topic_id for endpoint in endpoints}

        # Check for missing topics (endpoints without seed data)
        for endpoint in endpoints:
            seed_data = get_seed_data_for_topic(endpoint.topic_id)
            if seed_data is None:
                report.missing_topics.append(endpoint.topic_id)

        # Check for orphaned topics (topics without endpoints)
        for topic in all_topics:
            if topic.topic_id not in endpoint_topic_ids:
                report.orphaned_topics.append(topic.topic_id)

        # Check for missing prompts in S3
        for topic in all_topics:
            for prompt_info in topic.prompts:
                prompt_content = await self.s3_storage.get_prompt(
                    topic_id=topic.topic_id,
                    prompt_type=prompt_info.prompt_type,
                )
                if prompt_content is None:
                    report.missing_prompts.append(f"{topic.topic_id}:{prompt_info.prompt_type}")

        # Note: Parameter validation now uses PARAMETER_REGISTRY and TOPIC_REGISTRY
        # instead of topic.allowed_parameters

        logger.info(
            "Topic validation completed",
            missing_topics=len(report.missing_topics),
            orphaned_topics=len(report.orphaned_topics),
            missing_prompts=len(report.missing_prompts),
            invalid_parameters=len(report.invalid_parameters),
            is_valid=report.is_valid,
        )

        return report

    async def _create_topic_from_seed(
        self,
        *,
        seed_data: TopicSeedData,
    ) -> LLMTopic:
        """Create a new topic from seed data.

        Args:
            seed_data: Topic seed data configuration

        Returns:
            Created LLMTopic entity
        """
        now = datetime.now(UTC)

        # Create topic entity
        topic = LLMTopic(
            topic_id=seed_data.topic_id,
            topic_name=seed_data.topic_name,
            topic_type=seed_data.topic_type,
            category=seed_data.category,
            is_active=True,
            model_code=seed_data.model_code,
            temperature=seed_data.temperature,
            max_tokens=seed_data.max_tokens,
            top_p=seed_data.top_p,
            frequency_penalty=seed_data.frequency_penalty,
            presence_penalty=seed_data.presence_penalty,
            prompts=[],  # Will be added after S3 upload
            created_at=now,
            updated_at=now,
            description=seed_data.description,
            display_order=seed_data.display_order,
            created_by=self.default_created_by,
        )

        # Save prompts to S3
        prompts = []

        # System prompt
        if seed_data.default_system_prompt:
            system_key = await self.s3_storage.save_prompt(
                topic_id=seed_data.topic_id,
                prompt_type="system",
                content=seed_data.default_system_prompt,
            )
            prompts.append(
                PromptInfo(
                    prompt_type="system",
                    s3_bucket=self.s3_storage.bucket_name,
                    s3_key=system_key,
                    updated_at=now,
                    updated_by=self.default_created_by,
                )
            )

        # User prompt
        if seed_data.default_user_prompt:
            user_key = await self.s3_storage.save_prompt(
                topic_id=seed_data.topic_id,
                prompt_type="user",
                content=seed_data.default_user_prompt,
            )
            prompts.append(
                PromptInfo(
                    prompt_type="user",
                    s3_bucket=self.s3_storage.bucket_name,
                    s3_key=user_key,
                    updated_at=now,
                    updated_by=self.default_created_by,
                )
            )

        topic.prompts = prompts

        # Create in DynamoDB
        created_topic = await self.topic_repo.create(topic=topic)

        return created_topic

    async def _update_topic_from_seed(
        self,
        *,
        existing_topic: LLMTopic,
        seed_data: TopicSeedData,
    ) -> LLMTopic:
        """Update an existing topic from seed data.

        Args:
            existing_topic: Existing topic entity
            seed_data: New seed data configuration

        Returns:
            Updated LLMTopic entity
        """
        now = datetime.now(UTC)

        # Update configuration (preserve existing created_at and created_by)
        existing_topic.topic_name = seed_data.topic_name
        existing_topic.topic_type = seed_data.topic_type
        existing_topic.category = seed_data.category
        existing_topic.description = seed_data.description
        existing_topic.model_code = seed_data.model_code
        existing_topic.temperature = seed_data.temperature
        existing_topic.max_tokens = seed_data.max_tokens
        existing_topic.top_p = seed_data.top_p
        existing_topic.frequency_penalty = seed_data.frequency_penalty
        existing_topic.presence_penalty = seed_data.presence_penalty
        existing_topic.display_order = seed_data.display_order
        existing_topic.updated_at = now

        # Note: Parameters are now managed in PARAMETER_REGISTRY and TOPIC_REGISTRY
        # No need to update allowed_parameters on the topic entity

        # Update prompts in S3 (if they have content)
        prompts = existing_topic.prompts.copy()

        # Update system prompt
        if seed_data.default_system_prompt:
            system_key = await self.s3_storage.save_prompt(
                topic_id=seed_data.topic_id,
                prompt_type="system",
                content=seed_data.default_system_prompt,
            )
            # Update or add system prompt info
            system_prompt = existing_topic.get_prompt(prompt_type="system")
            if system_prompt:
                system_prompt.updated_at = now
                system_prompt.updated_by = self.default_created_by
            else:
                prompts.append(
                    PromptInfo(
                        prompt_type="system",
                        s3_bucket=self.s3_storage.bucket_name,
                        s3_key=system_key,
                        updated_at=now,
                        updated_by=self.default_created_by,
                    )
                )

        # Update user prompt
        if seed_data.default_user_prompt:
            user_key = await self.s3_storage.save_prompt(
                topic_id=seed_data.topic_id,
                prompt_type="user",
                content=seed_data.default_user_prompt,
            )
            # Update or add user prompt info
            user_prompt = existing_topic.get_prompt(prompt_type="user")
            if user_prompt:
                user_prompt.updated_at = now
                user_prompt.updated_by = self.default_created_by
            else:
                prompts.append(
                    PromptInfo(
                        prompt_type="user",
                        s3_bucket=self.s3_storage.bucket_name,
                        s3_key=user_key,
                        updated_at=now,
                        updated_by=self.default_created_by,
                    )
                )

        existing_topic.prompts = prompts

        # Update in DynamoDB
        updated_topic = await self.topic_repo.update(topic=existing_topic)

        return updated_topic


__all__ = [
    "SeedingResult",
    "TopicSeedingService",
    "ValidationReport",
]
