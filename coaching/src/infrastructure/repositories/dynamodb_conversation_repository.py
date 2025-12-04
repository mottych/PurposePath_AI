"""DynamoDB implementation of ConversationRepositoryPort.

This module provides a DynamoDB-backed implementation of the conversation
repository port interface, handling persistence and retrieval of conversations.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from boto3.dynamodb.conditions import Attr, Key
from coaching.src.core.constants import ConversationStatus
from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.value_objects.conversation_context import ConversationContext
from coaching.src.domain.value_objects.message import Message

logger = structlog.get_logger()


class DynamoDBConversationRepository:
    """
    DynamoDB adapter implementing ConversationRepositoryPort.

    This adapter provides DynamoDB-backed persistence for conversations,
    implementing the repository port interface defined in the domain layer.

    Design:
        - Maps domain entities to/from DynamoDB items
        - Enforces multi-tenant isolation
        - Handles TTL for automatic cleanup
        - Includes observability hooks
    """

    def __init__(
        self,
        dynamodb_resource: Any,  # boto3.resources.base.ServiceResource
        table_name: str,
    ):
        """
        Initialize DynamoDB conversation repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name for conversations
        """
        self.dynamodb = dynamodb_resource
        self.table = self.dynamodb.Table(table_name)
        logger.info("DynamoDB conversation repository initialized", table_name=table_name)

    async def save(self, conversation: Conversation) -> None:
        """
        Persist a conversation to DynamoDB.

        Args:
            conversation: Conversation entity to persist

        Business Rule: Conversations are stored with 30-day TTL for automatic cleanup
        """
        try:
            item = self._to_dynamodb_item(conversation)
            self.table.put_item(Item=item)

            logger.info(
                "Conversation saved",
                conversation_id=conversation.conversation_id,
                user_id=conversation.user_id,
                status=conversation.status.value,
            )
        except Exception as e:
            logger.error(
                "Failed to save conversation",
                conversation_id=conversation.conversation_id,
                error=str(e),
            )
            raise

    async def get_by_id(
        self, conversation_id: ConversationId, tenant_id: TenantId | None = None
    ) -> Conversation | None:
        """
        Retrieve a conversation by ID.

        Args:
            conversation_id: Unique conversation identifier
            tenant_id: Optional tenant ID for multi-tenant isolation

        Returns:
            Conversation entity if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={"conversation_id": conversation_id})

            if "Item" not in response:
                logger.debug("Conversation not found", conversation_id=conversation_id)
                return None

            item = response["Item"]

            # Enforce tenant isolation if tenant_id provided
            if tenant_id and item.get("tenant_id") != tenant_id:
                logger.warning(
                    "Tenant isolation violation attempt",
                    conversation_id=conversation_id,
                    requested_tenant=tenant_id,
                    actual_tenant=item.get("tenant_id"),
                )
                return None

            conversation = self._from_dynamodb_item(item)
            logger.debug("Conversation retrieved", conversation_id=conversation_id)
            return conversation

        except Exception as e:
            logger.error(
                "Failed to retrieve conversation",
                conversation_id=conversation_id,
                error=str(e),
            )
            raise

    async def get_by_user(
        self,
        user_id: UserId,
        tenant_id: TenantId | None = None,
        limit: int = 10,
        active_only: bool = False,
    ) -> list[Conversation]:
        """
        Retrieve conversations for a specific user.

        Args:
            user_id: User identifier
            tenant_id: Optional tenant ID for multi-tenant isolation
            limit: Maximum number of conversations to return
            active_only: If True, only return active conversations

        Returns:
            List of conversation entities (ordered by most recent first)
        """
        try:
            # Build query expression
            key_condition = Key("user_id").eq(user_id)

            # Add tenant filter if provided
            filter_expression: Any = None
            if tenant_id:
                filter_expression = Attr("tenant_id").eq(tenant_id)

            if active_only:
                status_filter = Attr("status").eq(ConversationStatus.ACTIVE.value)
                filter_expression = (
                    status_filter if not filter_expression else filter_expression & status_filter
                )

            # Query with GSI on user_id
            query_params: dict[str, Any] = {
                "IndexName": "user_id-index",
                "KeyConditionExpression": key_condition,
                "Limit": limit,
                "ScanIndexForward": False,  # Most recent first
            }

            if filter_expression:
                query_params["FilterExpression"] = filter_expression

            response = self.table.query(**query_params)

            conversations = [self._from_dynamodb_item(item) for item in response.get("Items", [])]

            logger.debug(
                "Conversations retrieved for user",
                user_id=user_id,
                count=len(conversations),
                active_only=active_only,
            )

            return conversations

        except Exception as e:
            logger.error("Failed to retrieve conversations for user", user_id=user_id, error=str(e))
            raise

    async def delete(
        self, conversation_id: ConversationId, tenant_id: TenantId | None = None
    ) -> bool:
        """
        Delete a conversation (soft delete by marking as ABANDONED).

        Args:
            conversation_id: Unique conversation identifier
            tenant_id: Optional tenant ID for multi-tenant isolation

        Returns:
            True if conversation was deleted, False if not found

        Business Rule: Soft delete is preferred; mark as ABANDONED instead of hard delete
        """
        try:
            # Get conversation first to enforce tenant isolation
            conversation = await self.get_by_id(conversation_id, tenant_id)

            if not conversation:
                return False

            # Soft delete: Update status to ABANDONED
            self.table.update_item(
                Key={"conversation_id": conversation_id},
                UpdateExpression="SET #status = :status, updated_at = :updated_at",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": ConversationStatus.ABANDONED.value,
                    ":updated_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.info("Conversation deleted (soft)", conversation_id=conversation_id)
            return True

        except Exception as e:
            logger.error(
                "Failed to delete conversation", conversation_id=conversation_id, error=str(e)
            )
            raise

    async def exists(
        self, conversation_id: ConversationId, tenant_id: TenantId | None = None
    ) -> bool:
        """
        Check if a conversation exists.

        Args:
            conversation_id: Unique conversation identifier
            tenant_id: Optional tenant ID for multi-tenant isolation

        Returns:
            True if conversation exists, False otherwise
        """
        conversation = await self.get_by_id(conversation_id, tenant_id)
        return conversation is not None

    async def get_active_count(self, user_id: UserId, tenant_id: TenantId | None = None) -> int:
        """
        Get count of active conversations for a user.

        Args:
            user_id: User identifier
            tenant_id: Optional tenant ID for multi-tenant isolation

        Returns:
            Number of active conversations
        """
        conversations = await self.get_by_user(
            user_id=user_id, tenant_id=tenant_id, active_only=True, limit=100
        )
        return len(conversations)

    def _to_dynamodb_item(self, conversation: Conversation) -> dict[str, Any]:
        """
        Convert domain entity to DynamoDB item.

        Args:
            conversation: Conversation domain entity

        Returns:
            DynamoDB item dictionary
        """
        # Calculate TTL (30 days from now)
        ttl = int((datetime.now(UTC) + timedelta(days=30)).timestamp())

        return {
            "conversation_id": conversation.conversation_id,
            "user_id": conversation.user_id,
            "tenant_id": conversation.tenant_id,
            "topic": conversation.topic,
            "status": conversation.status.value,
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in conversation.messages
            ],
            "context": conversation.context.model_dump(),
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "completed_at": (
                conversation.completed_at.isoformat() if conversation.completed_at else None
            ),
            "metadata": conversation.metadata,
            "ttl": ttl,
        }

    def _from_dynamodb_item(self, item: dict[str, Any]) -> Conversation:
        """
        Convert DynamoDB item to domain entity.

        Args:
            item: DynamoDB item dictionary

        Returns:
            Conversation domain entity
        """
        # Parse messages
        messages = [
            Message(
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["timestamp"]),
                metadata=msg.get("metadata", {}),
            )
            for msg in item.get("messages", [])
        ]

        # Parse context
        context_data = item.get("context", {})
        context = ConversationContext(**context_data)

        # Parse timestamps
        created_at = datetime.fromisoformat(item["created_at"])
        updated_at = datetime.fromisoformat(item["updated_at"])
        completed_at = (
            datetime.fromisoformat(item["completed_at"]) if item.get("completed_at") else None
        )

        return Conversation(
            conversation_id=item["conversation_id"],
            user_id=item["user_id"],
            tenant_id=item["tenant_id"],
            topic=item["topic"],
            status=item["status"],
            messages=messages,
            context=context,
            created_at=created_at,
            updated_at=updated_at,
            completed_at=completed_at,
            metadata=item.get("metadata", {}),
        )


__all__ = ["DynamoDBConversationRepository"]
