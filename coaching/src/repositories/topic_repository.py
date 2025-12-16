"""Repository for LLM topic data persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import structlog
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource
    from mypy_boto3_dynamodb.service_resource import Table

from coaching.src.core.topic_registry import ENDPOINT_REGISTRY
from coaching.src.domain.entities.llm_topic import LLMTopic, PromptInfo
from coaching.src.domain.exceptions.topic_exceptions import (
    DuplicateTopicError,
    PromptNotFoundError,
    TopicNotFoundError,
    TopicUpdateError,
)

logger = structlog.get_logger()


class TopicRepository:
    """Repository for managing LLM topics in DynamoDB.

    Provides CRUD operations for topics with proper error handling,
    type safety, and logging. Supports querying by topic type using GSI.

    Business Rules:
        - topic_id must be unique
        - Soft deletes by default (set is_active=false)
        - Hard deletes available for data removal requests
    """

    def __init__(
        self,
        *,
        dynamodb_resource: DynamoDBServiceResource,
        table_name: str,
    ) -> None:
        """Initialize topic repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name
        """
        self.dynamodb: DynamoDBServiceResource = dynamodb_resource
        self.table: Table = self.dynamodb.Table(table_name)

    async def get(self, *, topic_id: str) -> LLMTopic | None:
        """Get topic by ID.

        Args:
            topic_id: Topic identifier

        Returns:
            LLMTopic if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={"topic_id": topic_id})

            if "Item" not in response:
                logger.debug("Topic not found", topic_id=topic_id)
                return None

            item = cast(dict[str, Any], response["Item"])
            topic = LLMTopic.from_dynamodb_item(item)

            logger.debug("Topic retrieved", topic_id=topic_id, topic_type=topic.topic_type)
            return topic

        except Exception as e:
            logger.error("Failed to get topic", topic_id=topic_id, error=str(e))
            raise TopicUpdateError(topic_id=topic_id, reason=f"Retrieval failed: {e}") from e

    async def list_all(self, *, include_inactive: bool = False) -> list[LLMTopic]:
        """List all topics.

        Args:
            include_inactive: Whether to include inactive topics

        Returns:
            List of topics
        """
        try:
            if include_inactive:
                response = self.table.scan()
            else:
                response = self.table.scan(FilterExpression=Attr("is_active").eq(True))

            items = cast(list[dict[str, Any]], response.get("Items", []))
            topics = [LLMTopic.from_dynamodb_item(item) for item in items]

            logger.info(
                "Topics listed",
                count=len(topics),
                include_inactive=include_inactive,
            )
            return topics

        except Exception as e:
            logger.error("Failed to list topics", error=str(e))
            raise

    async def list_all_with_enum_defaults(
        self, *, include_inactive: bool = False
    ) -> list[LLMTopic]:
        """List all topics, merging enum defaults with database records.

        Returns topics from the database first, then adds any enum values
        that are not yet configured in the database. This ensures all
        defined topics are always visible to admins, even if not yet
        configured in DynamoDB.

        Args:
            include_inactive: Whether to include inactive topics in results

        Returns:
            List of topics with endpoint registry defaults merged with DB records
        """
        try:
            import sys

            print(
                f"[DEBUG] list_all_with_enum_defaults - include_inactive={include_inactive}",
                file=sys.stderr,
                flush=True,
            )
            print(
                f"[DEBUG] ENDPOINT_REGISTRY count: {len(ENDPOINT_REGISTRY)}",
                file=sys.stderr,
                flush=True,
            )

            logger.info("list_all_with_enum_defaults called", include_inactive=include_inactive)
            logger.info("ENDPOINT_REGISTRY count", count=len(ENDPOINT_REGISTRY))

            # Get existing topics from database
            db_topics = await self.list_all(include_inactive=include_inactive)
            logger.info(
                "db_topics retrieved", count=len(db_topics), ids=[t.topic_id for t in db_topics]
            )
            logger.error(
                "DEBUG: db_topics count",
                count=len(db_topics),
                ids=[t.topic_id for t in db_topics],
            )

            # Build set of topic IDs already in database
            existing_ids = {topic.topic_id for topic in db_topics}
            logger.info("existing_ids", ids=list(existing_ids))

            # Create default topics from endpoint registry for any not in database
            default_topics = [
                LLMTopic.create_default_from_endpoint(endpoint_def)
                for endpoint_def in ENDPOINT_REGISTRY.values()
                if endpoint_def.topic_id not in existing_ids
            ]
            logger.info(
                "default_topics created from registry",
                count=len(default_topics),
                ids=[t.topic_id for t in default_topics],
            )

            # Filter defaults by is_active if requested
            if not include_inactive:
                before_filter = len(default_topics)
                default_topics = [t for t in default_topics if t.is_active]
                logger.info("filtered_defaults", before=before_filter, after=len(default_topics))

            # Merge and sort by display_order
            all_topics = db_topics + default_topics
            all_topics.sort(key=lambda t: t.display_order)

            logger.info(
                "Topics listed with enum defaults",
                db_count=len(db_topics),
                default_count=len(default_topics),
                total_count=len(all_topics),
                include_inactive=include_inactive,
            )

            return all_topics

        except Exception as e:
            logger.error("Failed to list topics with enum defaults", error=str(e))
            raise

    async def list_by_type(
        self, *, topic_type: str, include_inactive: bool = False
    ) -> list[LLMTopic]:
        """List topics filtered by type using GSI.

        Args:
            topic_type: Topic type to filter by
            include_inactive: Whether to include inactive topics

        Returns:
            List of topics matching the type
        """
        try:
            if include_inactive:
                response = self.table.query(
                    IndexName="topic_type-index",
                    KeyConditionExpression=Key("topic_type").eq(topic_type),
                )
            else:
                response = self.table.query(
                    IndexName="topic_type-index",
                    KeyConditionExpression=Key("topic_type").eq(topic_type),
                    FilterExpression=Attr("is_active").eq(True),
                )

            items = cast(list[dict[str, Any]], response.get("Items", []))
            topics = [LLMTopic.from_dynamodb_item(item) for item in items]

            logger.info(
                "Topics queried by type",
                topic_type=topic_type,
                count=len(topics),
                include_inactive=include_inactive,
            )
            return topics

        except Exception as e:
            logger.error(
                "Failed to query topics by type",
                topic_type=topic_type,
                error=str(e),
            )
            raise

    async def create(self, *, topic: LLMTopic) -> LLMTopic:
        """Create new topic.

        Args:
            topic: Topic entity to create

        Returns:
            Created topic

        Raises:
            DuplicateTopicError: If topic_id already exists
        """
        # Check for duplicate
        existing = await self.get(topic_id=topic.topic_id)
        if existing is not None:
            raise DuplicateTopicError(topic_id=topic.topic_id)

        try:
            item = topic.to_dynamodb_item()
            self.table.put_item(Item=item)

            logger.info(
                "Topic created",
                topic_id=topic.topic_id,
                topic_type=topic.topic_type,
                prompt_count=len(topic.prompts),
            )
            return topic

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ConditionalCheckFailedException":
                raise DuplicateTopicError(topic_id=topic.topic_id) from e
            logger.error("Failed to create topic", topic_id=topic.topic_id, error=str(e))
            raise TopicUpdateError(topic_id=topic.topic_id, reason=f"Creation failed: {e}") from e

    async def update(self, *, topic: LLMTopic) -> LLMTopic:
        """Update existing topic.

        Args:
            topic: Topic entity with updates

        Returns:
            Updated topic

        Raises:
            TopicNotFoundError: If topic does not exist
        """
        # Verify topic exists
        existing = await self.get(topic_id=topic.topic_id)
        if existing is None:
            raise TopicNotFoundError(topic_id=topic.topic_id)

        try:
            # Update timestamp
            topic.updated_at = datetime.now(UTC)

            item = topic.to_dynamodb_item()
            self.table.put_item(Item=item)

            logger.info(
                "Topic updated",
                topic_id=topic.topic_id,
                is_active=topic.is_active,
            )
            return topic

        except Exception as e:
            logger.error("Failed to update topic", topic_id=topic.topic_id, error=str(e))
            raise TopicUpdateError(topic_id=topic.topic_id, reason=f"Update failed: {e}") from e

    async def delete(self, *, topic_id: str, hard_delete: bool = False) -> bool:
        """Delete topic (soft delete by default).

        Args:
            topic_id: Topic identifier
            hard_delete: If True, permanently delete; if False, set is_active=false

        Returns:
            True if deleted successfully

        Raises:
            TopicNotFoundError: If topic does not exist
        """
        topic = await self.get(topic_id=topic_id)
        if topic is None:
            raise TopicNotFoundError(topic_id=topic_id)

        try:
            if hard_delete:
                # Permanent deletion
                self.table.delete_item(Key={"topic_id": topic_id})
                logger.info("Topic hard deleted", topic_id=topic_id)
            else:
                # Soft delete
                topic.is_active = False
                topic.updated_at = datetime.now(UTC)
                await self.update(topic=topic)
                logger.info("Topic soft deleted", topic_id=topic_id)

            return True

        except Exception as e:
            logger.error(
                "Failed to delete topic",
                topic_id=topic_id,
                hard_delete=hard_delete,
                error=str(e),
            )
            raise TopicUpdateError(topic_id=topic_id, reason=f"Delete failed: {e}") from e

    async def add_prompt(
        self,
        *,
        topic_id: str,
        prompt_info: PromptInfo,
    ) -> LLMTopic:
        """Add or update a prompt in the topic's prompts array.

        If a prompt with the same prompt_type exists, it will be updated.
        Otherwise, a new prompt will be added.

        Args:
            topic_id: Topic identifier
            prompt_info: Prompt information to add/update

        Returns:
            Updated topic

        Raises:
            TopicNotFoundError: If topic does not exist
        """
        topic = await self.get(topic_id=topic_id)
        if topic is None:
            raise TopicNotFoundError(topic_id=topic_id)

        try:
            # Remove existing prompt of same type if present
            topic.prompts = [p for p in topic.prompts if p.prompt_type != prompt_info.prompt_type]

            # Add new/updated prompt
            topic.prompts.append(prompt_info)
            topic.updated_at = datetime.now(UTC)

            # Save updated topic
            await self.update(topic=topic)

            logger.info(
                "Prompt added to topic",
                topic_id=topic_id,
                prompt_type=prompt_info.prompt_type,
            )
            return topic

        except Exception as e:
            logger.error(
                "Failed to add prompt",
                topic_id=topic_id,
                prompt_type=prompt_info.prompt_type,
                error=str(e),
            )
            raise TopicUpdateError(topic_id=topic_id, reason=f"Add prompt failed: {e}") from e

    async def remove_prompt(
        self,
        *,
        topic_id: str,
        prompt_type: str,
    ) -> LLMTopic:
        """Remove a prompt from the topic's prompts array.

        Args:
            topic_id: Topic identifier
            prompt_type: Type of prompt to remove

        Returns:
            Updated topic

        Raises:
            TopicNotFoundError: If topic does not exist
            PromptNotFoundError: If prompt type does not exist in topic
        """
        topic = await self.get(topic_id=topic_id)
        if topic is None:
            raise TopicNotFoundError(topic_id=topic_id)

        # Check if prompt exists
        if not topic.has_prompt(prompt_type=prompt_type):
            raise PromptNotFoundError(topic_id=topic_id, prompt_type=prompt_type)

        try:
            # Remove prompt
            topic.prompts = [p for p in topic.prompts if p.prompt_type != prompt_type]
            topic.updated_at = datetime.now(UTC)

            # Save updated topic
            await self.update(topic=topic)

            logger.info(
                "Prompt removed from topic",
                topic_id=topic_id,
                prompt_type=prompt_type,
            )
            return topic

        except Exception as e:
            logger.error(
                "Failed to remove prompt",
                topic_id=topic_id,
                prompt_type=prompt_type,
                error=str(e),
            )
            raise TopicUpdateError(topic_id=topic_id, reason=f"Remove prompt failed: {e}") from e


__all__ = ["TopicRepository"]
