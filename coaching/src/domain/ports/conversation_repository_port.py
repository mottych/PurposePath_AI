"""Conversation repository port interface.

This module defines the protocol (interface) for conversation persistence,
allowing different infrastructure implementations (DynamoDB, PostgreSQL, etc.)
to be used interchangeably.
"""

from typing import Protocol

from coaching.src.core.types import ConversationId, TenantId, UserId
from coaching.src.domain.entities.conversation import Conversation


class ConversationRepositoryPort(Protocol):
    """
    Port interface for conversation persistence.

    This protocol defines the contract for conversation repository implementations.
    Implementations must be async and support multi-tenancy.

    Design Principles:
        - Async-first: All operations are async for scalability
        - Multi-tenant: Support for tenant isolation
        - Domain-centric: Uses domain entities, not DTOs
        - Infrastructure-agnostic: No implementation details
    """

    async def save(self, conversation: Conversation) -> None:
        """
        Persist a conversation (create or update).

        Args:
            conversation: The conversation entity to persist

        Raises:
            RepositoryError: If persistence fails

        Business Rule: Conversations must be persisted atomically
        """
        ...

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

        Business Rule: Tenant isolation must be enforced when tenant_id is provided
        """
        ...

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
            List of conversation entities (may be empty)

        Business Rule: Results must be ordered by most recent first
        """
        ...

    async def delete(
        self, conversation_id: ConversationId, tenant_id: TenantId | None = None
    ) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Unique conversation identifier
            tenant_id: Optional tenant ID for multi-tenant isolation

        Returns:
            True if conversation was deleted, False if not found

        Business Rule: Soft delete is preferred; actual deletion is implementation-specific
        """
        ...

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

        Business Rule: Tenant isolation must be enforced when tenant_id is provided
        """
        ...

    async def get_active_count(self, user_id: UserId, tenant_id: TenantId | None = None) -> int:
        """
        Get count of active conversations for a user.

        Args:
            user_id: User identifier
            tenant_id: Optional tenant ID for multi-tenant isolation

        Returns:
            Number of active conversations

        Business Rule: Only counts conversations in ACTIVE status
        """
        ...


__all__ = ["ConversationRepositoryPort"]
