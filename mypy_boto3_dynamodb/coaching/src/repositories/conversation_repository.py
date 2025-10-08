"""Repository for conversation data persistence."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, TypedDict, cast

import structlog
from boto3.dynamodb.conditions import Attr, Key
from coaching.src.core.constants import ConversationPhase, ConversationStatus, MessageRole
from coaching.src.core.exceptions import ConversationNotFoundCompatError
from coaching.src.models.conversation import Conversation, ConversationContext, Message
from shared.types.common import JSONDict

logger = structlog.get_logger()

# Type aliases for conversation repository
ConversationContextDict = JSONDict
LLMConfigDict = JSONDict
MessageMetadataDict = Dict[str, str]
BusinessContextDict = JSONDict
UserPreferencesDict = JSONDict
ProgressMarkersDict = JSONDict
DynamoDBResource = object  # boto3.resources.base.ServiceResource


class MessageItemDict(TypedDict):
    """DynamoDB message item structure"""

    role: str
    content: str
    timestamp: str
    metadata: MessageMetadataDict


class ContextItemDict(TypedDict, total=False):
    """DynamoDB context item structure"""

    phase: str
    identified_values: List[str]
    key_insights: List[str]
    progress_markers: ProgressMarkersDict
    categories_explored: List[str]
    response_count: int
    deepening_count: int
    tenant_id: Optional[str]
    session_id: Optional[str]
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
    messages: List[MessageItemDict]
    context: ContextItemDict
    llm_config: LLMConfigDict
    created_at: str
    updated_at: str
    completed_at: Optional[str]
    paused_at: Optional[str]
    ttl: Optional[int]


class ConversationRepository:
    """Repository for managing conversation data in DynamoDB."""

    def __init__(
        self, dynamodb_resource: DynamoDBResource, table_name: str, tenant_id: Optional[str] = None
    ):
        """Initialize conversation repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name
            tenant_id: Optional tenant ID for multitenant support
        """
        self.dynamodb = dynamodb_resource  # type: ignore[misc] # AWS SDK boundary
        self.table = self.dynamodb.Table(table_name)  # type: ignore[misc] # AWS SDK boundary
        self.tenant_id = tenant_id

    async def create(
        self,
        user_id: str,
        topic: str,
        initial_message: str,
        llm_config: Optional[LLMConfigDict] = None,
        context: Optional[ConversationContextDict] = None,
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
        timestamp = datetime.now(timezone.utc)

        # Create conversation context with multitenant data
        conversation_context = ConversationContext()
        if context:  # type: ignore[misc] # Input dict boundary
            # Set multitenant context fields from provided context with proper casting
            conversation_context.tenant_id = cast(Optional[str], context.get("tenant_id"))  # type: ignore[misc] # Input dict boundary
            conversation_context.session_id = cast(Optional[str], context.get("session_id"))  # type: ignore[misc] # Input dict boundary
            conversation_context.business_context = cast(BusinessContextDict, context.get("business_context", {}))  # type: ignore[misc] # Input dict boundary
            conversation_context.user_preferences = cast(UserPreferencesDict, context.get("user_preferences", {}))  # type: ignore[misc] # Input dict boundary
            conversation_context.language = cast(str, context.get("language", "en"))  # type: ignore[misc] # Input dict boundary

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
        self.table.put_item(Item=item)  # type: ignore[misc] # AWS DynamoDB SDK

        logger.info(
            "Conversation created", conversation_id=conversation_id, user_id=user_id, topic=topic
        )

        return conversation

    async def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        try:
            # Query with conversation_id and latest timestamp
            response = self.table.query(  # type: ignore[misc] # AWS SDK boundary
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
        conversation.updated_at = datetime.now(timezone.utc)

        # Convert to DynamoDB item
        item = self._conversation_to_item(conversation)

        # Save to DynamoDB
        self.table.put_item(Item=item)  # type: ignore[misc] # AWS DynamoDB SDK

        logger.info("Conversation updated", conversation_id=conversation.conversation_id)

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add a message to a conversation.

        Args:
            conversation_id: Conversation identifier
            role: Message role
            content: Message content
            metadata: Optional metadata
        """
        # Get conversation
        conversation = await self.get(conversation_id)

        if not conversation:
            raise ConversationNotFoundCompatError(conversation_id)

        # Add message
        conversation.add_message(role=MessageRole(role), content=content, metadata=metadata)

        # Update conversation
        await self.update(conversation)

    async def list_by_user(
        self,
        user_id: str,
        limit: int = 20,
        status: Optional[str] = None,
        tenant_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> List[Conversation]:
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
            # Query using GSI
            kwargs: Dict[str, object] = {  # DynamoDB query parameters
                "IndexName": "user-conversations-index",
                "KeyConditionExpression": Key("user_id").eq(user_id),
                "ScanIndexForward": False,  # Most recent first
                "Limit": limit,
            }

            # Build filter expressions
            filter_expressions: List[object] = []  # DynamoDB condition expressions

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
                    combined_filter: object = filter_expressions[0]  # DynamoDB condition expression
                    for expr in filter_expressions[1:]:
                        combined_filter = combined_filter & expr  # type: ignore[misc] # DynamoDB condition boundary
                    kwargs["FilterExpression"] = combined_filter

            response = self.table.query(**kwargs)  # type: ignore[misc] # AWS DynamoDB SDK

            conversations: List[Conversation] = []
            items = cast(List[ConversationItemDict], response["Items"])
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
            conversation.updated_at = datetime.now(timezone.utc)
            await self.update(conversation)

    def _conversation_to_item(self, conversation: Conversation) -> ConversationItemDict:
        """Convert conversation to DynamoDB item.

        Args:
            conversation: Conversation object

        Returns:
            DynamoDB item
        """
        return {  # type: ignore[misc] # DynamoDB serialization boundary
            "conversation_id": conversation.conversation_id,
            "timestamp": conversation.updated_at.isoformat(),
            "user_id": conversation.user_id,
            "topic": conversation.topic,
            "status": conversation.status.value,
            "messages": [  # type: ignore[misc] # DynamoDB serialization boundary
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,  # type: ignore[misc] # DynamoDB serialization boundary
                }
                for msg in conversation.messages
            ],
            "context": {  # type: ignore[misc] # DynamoDB serialization boundary
                "phase": conversation.context.phase.value,
                "identified_values": conversation.context.identified_values,
                "key_insights": conversation.context.key_insights,
                "progress_markers": conversation.context.progress_markers,  # type: ignore[misc] # DynamoDB serialization boundary
                "categories_explored": conversation.context.categories_explored,
                "response_count": conversation.context.response_count,
                "deepening_count": conversation.context.deepening_count,
                "tenant_id": conversation.context.tenant_id,
                "session_id": conversation.context.session_id,
                "business_context": conversation.context.business_context,  # type: ignore[misc] # DynamoDB serialization boundary
                "user_preferences": conversation.context.user_preferences,  # type: ignore[misc] # DynamoDB serialization boundary
                "language": conversation.context.language,
            },
            "llm_config": conversation.llm_config,  # type: ignore[misc] # DynamoDB serialization boundary
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "completed_at": (
                conversation.completed_at.isoformat() if conversation.completed_at else None
            ),
            "paused_at": conversation.paused_at.isoformat() if conversation.paused_at else None,
            "ttl": conversation.ttl,
        }

    def _item_to_conversation(self, item: ConversationItemDict) -> Optional[Conversation]:
        """Convert DynamoDB item to conversation.

        Args:
            item: DynamoDB item

        Returns:
            Conversation object
        """
        try:
            # Parse messages
            messages: List[Message] = []
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
                phase=ConversationPhase(context_data.get("phase", "introduction")),
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
                    datetime.fromisoformat(item["completed_at"])
                    if item["completed_at"]  # type: ignore[misc] # DynamoDB item boundary
                    else None
                ),
                paused_at=(
                    datetime.fromisoformat(item["paused_at"])
                    if item["paused_at"]  # type: ignore[misc] # DynamoDB item boundary
                    else None
                ),
                ttl=item.get("ttl"),  # type: ignore[misc] # DynamoDB item boundary
            )

            return conversation

        except Exception as e:
            logger.error(
                "Error parsing conversation item", error=str(e), item_id=item.get("conversation_id")  # type: ignore[misc] # DynamoDB item boundary
            )
            return None
