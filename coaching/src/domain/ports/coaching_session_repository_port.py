"""Coaching session repository port interface.

This module defines the protocol (interface) for coaching session persistence,
following the design in docs/Specifications/conversation_coaching_design.md.

The port supports session conflict detection (Issue #157) through the
get_active_for_user_topic method which enables blocking different users
from initiating sessions for the same topic when one is already active.
"""

from typing import Protocol

from coaching.src.core.types import SessionId, TenantId, UserId
from coaching.src.domain.entities.coaching_session import CoachingSession


class CoachingSessionRepositoryPort(Protocol):
    """
    Port interface for coaching session persistence.

    This protocol defines the contract for coaching session repository
    implementations. Implementations must be async and support multi-tenancy.

    Design Principles:
        - Async-first: All operations are async for scalability
        - Multi-tenant: Tenant isolation is enforced on all operations
        - Domain-centric: Uses domain entities, not DTOs
        - Infrastructure-agnostic: No implementation details

    Key Features:
        - Session CRUD operations
        - User+Topic session lookup (for conflict detection)
        - Session expiration handling
    """

    # =========================================================================
    # Create Operations
    # =========================================================================

    async def create(self, session: CoachingSession) -> CoachingSession:
        """
        Create a new coaching session.

        Args:
            session: The coaching session entity to create

        Returns:
            The created session with any server-generated fields populated

        Raises:
            SessionConflictError: If an active session already exists
                for the same user+topic combination (Issue #157)
            RepositoryError: If persistence fails

        Business Rule: Only one active session per user+topic is allowed
        """
        ...

    async def save(self, session: CoachingSession) -> None:
        """
        Save (create or update) a coaching session.

        This is a convenience method that handles both create and update.
        Used by the service layer for simpler code.

        Args:
            session: The coaching session entity to save

        Raises:
            RepositoryError: If persistence fails
        """
        ...

    # =========================================================================
    # Read Operations
    # =========================================================================

    async def get_by_id(self, session_id: SessionId, tenant_id: TenantId) -> CoachingSession | None:
        """
        Retrieve a session by ID with tenant isolation.

        Args:
            session_id: Unique session identifier
            tenant_id: Tenant ID for multi-tenant isolation

        Returns:
            CoachingSession entity if found and belongs to tenant, None otherwise

        Business Rule: Tenant isolation MUST be enforced
        """
        ...

    async def get_by_id_for_tenant(self, session_id: str, tenant_id: str) -> CoachingSession | None:
        """
        Retrieve a session by ID with tenant isolation (string parameters).

        Convenience method that accepts string parameters instead of typed IDs.

        Args:
            session_id: Unique session identifier (string)
            tenant_id: Tenant ID for multi-tenant isolation (string)

        Returns:
            CoachingSession entity if found and belongs to tenant, None otherwise

        Business Rule: Tenant isolation MUST be enforced
        """
        ...

    async def get_active_for_user_topic(
        self, user_id: UserId, topic_id: str, tenant_id: TenantId
    ) -> CoachingSession | None:
        """
        Get active session for user+topic combination.

        This method is critical for implementing session conflict detection
        (Issue #157). It enables:
        - Resuming an existing session instead of creating a new one
        - Blocking different users from the same topic when session is active

        Args:
            user_id: User identifier
            topic_id: Coaching topic identifier (e.g., "core_values")
            tenant_id: Tenant ID for multi-tenant isolation

        Returns:
            Active CoachingSession if found, None otherwise

        Business Rule:
            - Returns session with status ACTIVE or PAUSED
            - Should use GSI for efficient lookup:
              pk=USER#{user_id}#TOPIC#{topic_id}, sk=TENANT#{tenant_id}
        """
        ...

    async def get_active_by_tenant_topic(
        self, tenant_id: str, topic_id: str
    ) -> CoachingSession | None:
        """
        Get any active session for a topic within a tenant (string parameters).

        Used for conflict detection when a different user tries to
        initiate a session for a topic that already has an active session.

        Args:
            tenant_id: Tenant ID for multi-tenant isolation (string)
            topic_id: Coaching topic identifier

        Returns:
            Active CoachingSession for the topic if any exists, None otherwise

        Business Rule:
            - Returns any session with status ACTIVE or PAUSED
            - Used to implement Issue #157 conflict blocking
        """
        ...

    async def get_active_for_topic(
        self, topic_id: str, tenant_id: TenantId
    ) -> CoachingSession | None:
        """
        Get any active session for a topic within a tenant (typed parameters).

        Used for conflict detection when a different user tries to
        initiate a session for a topic that already has an active session.

        Args:
            topic_id: Coaching topic identifier
            tenant_id: Tenant ID for multi-tenant isolation

        Returns:
            Active CoachingSession for the topic if any exists, None otherwise

        Business Rule:
            - Returns any session with status ACTIVE or PAUSED
            - Used to implement Issue #157 conflict blocking
        """
        ...

    # =========================================================================
    # Update Operations
    # =========================================================================

    async def update(self, session: CoachingSession) -> CoachingSession:
        """
        Update an existing session.

        Args:
            session: The session entity with updated fields

        Returns:
            The updated session

        Raises:
            SessionNotFoundError: If session doesn't exist
            RepositoryError: If update fails

        Business Rule: Only non-terminal sessions can be updated
        """
        ...

    async def mark_expired(self, session_id: SessionId, tenant_id: TenantId) -> bool:
        """
        Mark a session as expired.

        This is used by background processes to clean up stale sessions
        that have exceeded their expiration time or idle timeout.

        Args:
            session_id: Session identifier to expire
            tenant_id: Tenant ID for isolation

        Returns:
            True if session was marked expired, False if not found or already terminal

        Business Rule:
            - Only ACTIVE or PAUSED sessions can be expired
            - Sets status to ABANDONED
        """
        ...

    # =========================================================================
    # List Operations
    # =========================================================================

    async def get_expired_sessions(
        self, tenant_id: TenantId, limit: int = 100
    ) -> list[CoachingSession]:
        """
        Get sessions that have exceeded their expiration or idle timeout.

        Used by background cleanup processes.

        Args:
            tenant_id: Tenant ID for isolation
            limit: Maximum number of sessions to return

        Returns:
            List of expired sessions (may be empty)

        Business Rule:
            - Returns sessions where:
              - expires_at < now, OR
              - last_activity_at + idle_timeout_minutes < now
            - Only returns ACTIVE or PAUSED sessions
        """
        ...

    async def list_by_user(
        self,
        user_id: UserId,
        tenant_id: TenantId,
        include_completed: bool = False,
        limit: int = 20,
    ) -> list[CoachingSession]:
        """
        List sessions for a specific user.

        Args:
            user_id: User identifier
            tenant_id: Tenant ID for isolation
            include_completed: Whether to include COMPLETED sessions
            limit: Maximum number of sessions to return

        Returns:
            List of sessions ordered by created_at descending

        Business Rule:
            - CANCELLED and ABANDONED sessions are never included
            - Results ordered by most recent first
        """
        ...

    async def list_by_tenant_user(
        self,
        tenant_id: str,
        user_id: str,
        include_completed: bool = False,
        limit: int = 20,
    ) -> list[CoachingSession]:
        """
        List sessions for a specific tenant and user (string parameters).

        Convenience method that accepts string parameters.

        Args:
            tenant_id: Tenant ID for isolation (string)
            user_id: User identifier (string)
            include_completed: Whether to include COMPLETED sessions
            limit: Maximum number of sessions to return

        Returns:
            List of sessions ordered by created_at descending

        Business Rule:
            - CANCELLED and ABANDONED sessions are never included
            - Results ordered by most recent first
        """
        ...

    # =========================================================================
    # Delete Operations
    # =========================================================================

    async def delete(self, session_id: SessionId, tenant_id: TenantId) -> bool:
        """
        Delete a session (hard delete).

        Generally, sessions should expire naturally via TTL. This method
        is for administrative cleanup or user-initiated deletion.

        Args:
            session_id: Session identifier
            tenant_id: Tenant ID for isolation

        Returns:
            True if session was deleted, False if not found

        Business Rule: Use TTL-based expiration for normal cleanup
        """
        ...
