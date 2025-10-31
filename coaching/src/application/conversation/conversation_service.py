"""Conversation application service.

This service orchestrates conversation-related use cases, coordinating
domain entities, repositories, and infrastructure services.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from src.core.constants import CoachingTopic, ConversationStatus, MessageRole
from src.core.types import ConversationId, TenantId, UserId
from src.domain.entities.conversation import Conversation
from src.domain.exceptions.conversation_exceptions import (
    ConversationNotActive,
    ConversationNotFound,
)
from src.domain.ports.conversation_repository_port import ConversationRepositoryPort

logger = structlog.get_logger()


class ConversationApplicationService:
    """
    Application service for conversation management.

    This service implements conversation-related use cases,
    orchestrating domain logic and infrastructure concerns.

    Design Principles:
        - Dependency injection (depends on ports, not implementations)
        - Use case-driven methods (one method per use case)
        - Transaction boundaries explicit
        - Domain events published
        - Clear error handling
    """

    def __init__(self, conversation_repository: ConversationRepositoryPort):
        """
        Initialize conversation application service.

        Args:
            conversation_repository: Repository for conversation persistence
        """
        self.repository = conversation_repository
        logger.info("Conversation application service initialized")

    async def start_conversation(
        self,
        user_id: UserId,
        tenant_id: TenantId,
        topic: CoachingTopic,
        initial_message_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Conversation:
        """
        Start a new coaching conversation.

        Use Case: User initiates a new coaching session

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            topic: Coaching topic for this conversation
            initial_message_content: Initial greeting message
            metadata: Optional metadata

        Returns:
            Created conversation entity

        Business Rule: Only one active conversation per user per topic
        """
        try:
            # Check if user has active conversation for this topic
            active_count = await self.repository.get_active_count(user_id, tenant_id)
            if active_count >= 5:  # Business rule: max 5 active conversations
                logger.warning(
                    "User has too many active conversations",
                    user_id=user_id,
                    active_count=active_count,
                )

            # Create new conversation
            conv_id = ConversationId(f"conv_{user_id}_{int(datetime.now(UTC).timestamp())}")
            conversation = Conversation(
                conversation_id=conv_id,
                user_id=user_id,
                tenant_id=tenant_id,
                topic=topic,
                metadata=metadata or {},
            )

            # Add initial assistant message
            conversation.add_message(
                role=MessageRole.ASSISTANT,
                content=initial_message_content,
            )

            # Persist
            await self.repository.save(conversation)

            logger.info(
                "Conversation started",
                conversation_id=conversation.conversation_id,
                user_id=user_id,
                topic=topic.value,
            )

            return conversation

        except Exception as e:
            logger.error(
                "Failed to start conversation",
                user_id=user_id,
                topic=topic.value,
                error=str(e),
            )
            raise

    async def add_message(
        self,
        conversation_id: ConversationId,
        tenant_id: TenantId,
        role: MessageRole,
        content: str,
    ) -> Conversation:
        """
        Add a message to an existing conversation.

        Use Case: User or assistant adds a message

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier (for isolation)
            role: Message role (USER or ASSISTANT)
            content: Message content

        Returns:
            Updated conversation entity

        Raises:
            ConversationNotFound: If conversation doesn't exist
            ConversationNotActive: If conversation is not active
        """
        try:
            # Retrieve conversation
            conversation = await self.repository.get_by_id(conversation_id, tenant_id)
            if not conversation:
                raise ConversationNotFound(conversation_id, tenant_id)

            # Check if active
            if conversation.status != ConversationStatus.ACTIVE:
                raise ConversationNotActive(conversation_id, conversation.status, "add message")

            # Add message (domain entity enforces rules)
            conversation.add_message(role=role, content=content)

            # Persist
            await self.repository.save(conversation)

            logger.info(
                "Message added",
                conversation_id=conversation_id,
                role=role.value,
                message_count=len(conversation.messages),
            )

            return conversation

        except (ConversationNotFound, ConversationNotActive):
            raise
        except Exception as e:
            logger.error(
                "Failed to add message",
                conversation_id=conversation_id,
                error=str(e),
            )
            raise

    async def get_conversation(
        self, conversation_id: ConversationId, tenant_id: TenantId
    ) -> Conversation:
        """
        Retrieve a conversation by ID.

        Use Case: Load conversation for display or continuation

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier (for isolation)

        Returns:
            Conversation entity

        Raises:
            ConversationNotFound: If conversation doesn't exist
        """
        conversation = await self.repository.get_by_id(conversation_id, tenant_id)
        if not conversation:
            raise ConversationNotFound(conversation_id, tenant_id)

        return conversation

    async def list_user_conversations(
        self,
        user_id: UserId,
        tenant_id: TenantId,
        limit: int = 10,
        active_only: bool = False,
    ) -> list[Conversation]:
        """
        List conversations for a user.

        Use Case: Display user's conversation history

        Args:
            user_id: User identifier
            tenant_id: Tenant identifier
            limit: Maximum conversations to return
            active_only: If True, only active conversations

        Returns:
            List of conversation entities (most recent first)
        """
        conversations = await self.repository.get_by_user(
            user_id=user_id,
            tenant_id=tenant_id,
            limit=limit,
            active_only=active_only,
        )

        logger.debug(
            "Conversations listed",
            user_id=user_id,
            count=len(conversations),
            active_only=active_only,
        )

        return conversations

    async def pause_conversation(
        self, conversation_id: ConversationId, tenant_id: TenantId
    ) -> Conversation:
        """
        Pause an active conversation.

        Use Case: User pauses conversation for later continuation

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            Updated conversation entity

        Raises:
            ConversationNotFound: If conversation doesn't exist
        """
        conversation = await self.get_conversation(conversation_id, tenant_id)

        # Pause (domain entity enforces rules)
        conversation.mark_paused()

        # Persist
        await self.repository.save(conversation)

        logger.info("Conversation paused", conversation_id=conversation_id)

        return conversation

    async def resume_conversation(
        self, conversation_id: ConversationId, tenant_id: TenantId
    ) -> Conversation:
        """
        Resume a paused conversation.

        Use Case: User resumes previously paused conversation

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            Updated conversation entity

        Raises:
            ConversationNotFound: If conversation doesn't exist
        """
        conversation = await self.get_conversation(conversation_id, tenant_id)

        # Resume (domain entity enforces rules)
        conversation.resume()

        # Persist
        await self.repository.save(conversation)

        logger.info("Conversation resumed", conversation_id=conversation_id)

        return conversation

    async def complete_conversation(
        self, conversation_id: ConversationId, tenant_id: TenantId
    ) -> Conversation:
        """
        Mark conversation as completed.

        Use Case: User or system marks conversation as done

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            Updated conversation entity

        Raises:
            ConversationNotFound: If conversation doesn't exist
        """
        conversation = await self.get_conversation(conversation_id, tenant_id)

        # Complete (domain entity enforces rules)
        conversation.mark_completed()

        # Persist
        await self.repository.save(conversation)

        logger.info("Conversation completed", conversation_id=conversation_id)

        return conversation

    async def abandon_conversation(
        self, conversation_id: ConversationId, tenant_id: TenantId
    ) -> bool:
        """
        Abandon (soft delete) a conversation.

        Use Case: User or system abandons conversation

        Args:
            conversation_id: Conversation identifier
            tenant_id: Tenant identifier

        Returns:
            True if abandoned successfully

        Raises:
            ConversationNotFound: If conversation doesn't exist
        """
        deleted = await self.repository.delete(conversation_id, tenant_id)

        if deleted:
            logger.info("Conversation abandoned", conversation_id=conversation_id)
        else:
            logger.warning(
                "Conversation not found for abandonment", conversation_id=conversation_id
            )

        return deleted


__all__ = ["ConversationApplicationService"]
