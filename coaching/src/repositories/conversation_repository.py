"""Repository for conversation data persistence."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, TypedDict, cast

import structlog
from boto3.dynamodb.conditions import Attr, ConditionBase, Key

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBServiceResource
    from mypy_boto3_dynamodb.service_resource import Table

from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.core.exceptions import ConversationNotFoundCompatError
from coaching.src.domain.value_objects.message import Message
from coaching.src.models.conversation import Conversation, ConversationContext

from shared.types.common import JSONDict

logger = structlog.get_logger()

# Type aliases for conversation repository
ConversationContextDict = JSONDict
LLMConfigDict = JSONDict
MessageMetadataDict = dict[str, str]
BusinessContextDict = JSONDict
UserPreferencesDict = JSONDict
ProgressMarkersDict = JSONDict


class MessageItemDict(TypedDict):
    """DynamoDB message item structure"""

    role: str
    content: str
    timestamp: str
    metadata: MessageMetadataDict


class ContextItemDict(TypedDict, total=False):
    """DynamoDB context item structure"""

    phase: str
    identified_values: list[str]
    key_insights: list[str]
    progress_markers: ProgressMarkersDict
    categories_explored: list[str]
    response_count: int
    deepening_count: int
    tenant_id: str | None
    session_id: str | None
    business_context: BusinessContextDict
    user_preferences: UserPreferencesDict
    language: str


class ConversationItemDict(TypedDict):
    """DynamoDB conversation item structure"""

    conversation_id: str
    timestamp: str
    user_id: str
    topic: str
    status: str
    messages: list[MessageItemDict]
    context: ContextItemDict
    llm_config: LLMConfigDict
    created_at: str
    updated_at: str
    completed_at: str | None
    paused_at: str | None
    ttl: int | None


class ConversationRepository:
    """Repository for managing conversation data in DynamoDB."""

    def __init__(
        self,
        dynamodb_resource: DynamoDBServiceResource,
        table_name: str,
        tenant_id: str | None = None,
    ):
        """Initialize conversation repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name
            tenant_id: Optional tenant ID for multitenant support
        """
        self.dynamodb: DynamoDBServiceResource = dynamodb_resource
        self.table: Table = self.dynamodb.Table(table_name)
        self.tenant_id = tenant_id

    async def create(
        self,
        user_id: str,
        topic: str,
        initial_message: str,
        llm_config: LLMConfigDict | None = None,
        context: ConversationContextDict | None = None,
    ) -> Conversation:
        """Create a new conversation.

        Args:
            user_id: User identifier
            topic: Conversation topic
            initial_message: Initial AI message
            llm_config: LLM configuration
            context: Optional context data for multitenant support

        Returns:
            Created conversation
        """
        conversation_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC)

        # Create conversation context with multitenant data
        conversation_context = ConversationContext()
        if context:
            # Set multitenant context fields from provided context with proper casting
            conversation_context.tenant_id = cast(str | None, context.get("tenant_id"))
            conversation_context.session_id = cast(str | None, context.get("session_id"))
            conversation_context.business_context = cast(
                BusinessContextDict, context.get("business_context", {})
            )
            conversation_context.user_preferences = cast(
                UserPreferencesDict, context.get("user_preferences", {})
            )
            conversation_context.language = cast(str, context.get("language", "en"))

        # Create conversation object
        conversation = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            topic=topic,
            status=ConversationStatus.ACTIVE,
            context=conversation_context,
            llm_config=llm_config or {},
            created_at=timestamp,
            updated_at=timestamp,
            ttl=int((timestamp + timedelta(days=30)).timestamp()),
        )

        # Add initial message
        conversation.add_message(role=MessageRole.ASSISTANT, content=initial_message)

        # Save to DynamoDB
        item = self._conversation_to_item(conversation)
        self.table.put_item(Item=cast(dict[str, Any], item))

        logger.info(
            "Conversation created", conversation_id=conversation_id, user_id=user_id, topic=topic
        )

        return conversation

    async def get(self, conversation_id: str) -> Conversation | None:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        try:
            # Query with conversation_id and latest timestamp
            response = self.table.query(
                KeyConditionExpression=Key("conversation_id").eq(conversation_id),
                ScanIndexForward=False,  # Get latest first
                Limit=1,
            )

            if response["Items"]:
                item = cast(ConversationItemDict, response["Items"][0])
                return self._item_to_conversation(item)

            return None

        except Exception as e:
            logger.error(
                "Error fetching conversation", conversation_id=conversation_id, error=str(e)
            )
            return None

    async def update(self, conversation: Conversation) -> None:
        """Update a conversation.

        Args:
            conversation: Conversation to update
        """
        conversation.updated_at = datetime.now(UTC)

        # Convert to DynamoDB item
        item = self._conversation_to_item(conversation)

        # Save to DynamoDB
        self.table.put_item(Item=cast(dict[str, Any], item))

        logger.info("Conversation updated", conversation_id=conversation.conversation_id)

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: dict[str, str] | None = None,
        tokens: dict[str, int] | None = None,
        cost: float | None = None,
        model_id: str | None = None,
    ) -> None:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation identifier
            role: Message role
            content: Message content
            metadata: Optional metadata
            tokens: Token usage dict with 'input', 'output', 'total' keys
            cost: Calculated cost in USD for this message
            model_id: LLM model identifier used
        """
        # Get conversation
        conversation = await self.get(conversation_id)

        if not conversation:
            raise ConversationNotFoundCompatError(conversation_id)

        # Add message with token tracking
        conversation.add_message(
            role=MessageRole(role),
            content=content,
            metadata=metadata,
            tokens=tokens,
            cost=cost,
            model_id=model_id,
        )

        # Update conversation
        await self.update(conversation)

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 20,
        status: str | None = None,
        tenant_id: str | None = None,
        topic: str | None = None,
    ) -> list[Conversation]:
        """List conversations for a user.

        Args:
            user_id: User identifier
            limit: Maximum number of results
            status: Optional status filter
            tenant_id: Optional tenant ID filter for multitenant support
            topic: Optional topic filter

        Returns:
            List of conversations
        """
        try:
            # Build query parameters
            kwargs: dict[str, Any] = {
                "IndexName": "user-conversations-index",
                "KeyConditionExpression": Key("user_id").eq(user_id),
                "ScanIndexForward": False,  # Most recent first
                "Limit": limit,
            }

            # Build filter expressions
            filter_expressions: list[ConditionBase] = []

            if status:
                filter_expressions.append(Attr("status").eq(status))

            if tenant_id:
                filter_expressions.append(Attr("context.tenant_id").eq(tenant_id))

            if topic:
                filter_expressions.append(Attr("topic").eq(topic))

            # Combine filter expressions
            if filter_expressions:
                if len(filter_expressions) == 1:
                    kwargs["FilterExpression"] = filter_expressions[0]
                else:
                    # Combine multiple filters with AND
                    combined_filter: ConditionBase = filter_expressions[0]
                    for expr in filter_expressions[1:]:
                        combined_filter = combined_filter & expr
                    kwargs["FilterExpression"] = combined_filter

            response = self.table.query(**kwargs)

            conversations: list[Conversation] = []
            items = cast(list[ConversationItemDict], response["Items"])
            for item in items:
                conv = self._item_to_conversation(item)
                if conv:
                    conversations.append(conv)

            return conversations

        except Exception as e:
            logger.error("Error listing user conversations", user_id=user_id, error=str(e))
            return []

    async def delete(self, conversation_id: str) -> None:
        """Delete (mark as abandoned) a conversation.

        Args:
            conversation_id: Conversation identifier
        """
        conversation = await self.get(conversation_id)

        if conversation:
            conversation.status = ConversationStatus.ABANDONED
            conversation.updated_at = datetime.now(UTC)
            await self.update(conversation)

    def _conversation_to_item(self, conversation: Conversation) -> ConversationItemDict:
        """Convert conversation to DynamoDB item.

        Args:
            conversation: Conversation object

        Returns:
            DynamoDB item
        """
        return {
            "conversation_id": conversation.conversation_id,
            "timestamp": conversation.updated_at.isoformat(),
            "user_id": conversation.user_id,
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
            "context": {
                "identified_values": conversation.context.identified_values,
                "key_insights": conversation.context.key_insights,
                "progress_markers": conversation.context.progress_markers,
                "categories_explored": conversation.context.categories_explored,
                "response_count": conversation.context.response_count,
                "deepening_count": conversation.context.deepening_count,
                "tenant_id": conversation.context.tenant_id,
                "session_id": conversation.context.session_id,
                "business_context": conversation.context.business_context,
                "user_preferences": conversation.context.user_preferences,
                "language": conversation.context.language,
            },
            "llm_config": conversation.llm_config,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "completed_at": (
                conversation.completed_at.isoformat() if conversation.completed_at else None
            ),
            "paused_at": conversation.paused_at.isoformat() if conversation.paused_at else None,
            "ttl": conversation.ttl,
        }

    def _item_to_conversation(self, item: ConversationItemDict) -> Conversation | None:
        """Convert DynamoDB item to conversation.

        Args:
            item: DynamoDB item

        Returns:
            Conversation object
        """
        try:
            # Parse messages
            messages: list[Message] = []
            message_list = item.get("messages", [])
            for msg_data in message_list:
                messages.append(
                    Message(
                        role=MessageRole(msg_data["role"]),
                        content=msg_data["content"],
                        timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                        metadata=msg_data.get("metadata", {}),
                    )
                )

            # Parse context
            context_data = item.get("context", {})
            context = ConversationContext(
                identified_values=context_data.get("identified_values", []),
                key_insights=context_data.get("key_insights", []),
                progress_markers=context_data.get("progress_markers", {}),
                categories_explored=context_data.get("categories_explored", []),
                response_count=context_data.get("response_count", 0),
                deepening_count=context_data.get("deepening_count", 0),
                tenant_id=context_data.get("tenant_id"),
                session_id=context_data.get("session_id"),
                business_context=context_data.get("business_context", {}),
                user_preferences=context_data.get("user_preferences", {}),
                language=context_data.get("language", "en"),
            )

            # Create conversation
            conversation = Conversation(
                conversation_id=item["conversation_id"],
                user_id=item["user_id"],
                topic=item["topic"],
                status=ConversationStatus(item["status"]),
                messages=messages,
                context=context,
                llm_config=item.get("llm_config", {}),
                created_at=datetime.fromisoformat(item["created_at"]),
                updated_at=datetime.fromisoformat(item["updated_at"]),
                completed_at=(
                    datetime.fromisoformat(item["completed_at"]) if item["completed_at"] else None
                ),
                paused_at=(
                    datetime.fromisoformat(item["paused_at"]) if item["paused_at"] else None
                ),
                ttl=item.get("ttl"),
            )

            return conversation

        except Exception as e:
            logger.error(
                "Error parsing conversation item", error=str(e), item_id=item.get("conversation_id")
            )
            return None
