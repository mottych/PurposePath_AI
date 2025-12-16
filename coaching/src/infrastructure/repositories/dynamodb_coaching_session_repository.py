"""DynamoDB repository for coaching sessions.

This module provides a DynamoDB-backed repository for storing and
retrieving coaching session records with proper tenant isolation
and topic-based session enforcement.
"""

from datetime import UTC, datetime
from typing import Any

import structlog
from boto3.dynamodb.conditions import Key
from coaching.src.core.constants import ConversationStatus, MessageRole
from coaching.src.core.types import SessionId, TenantId, UserId
from coaching.src.domain.entities.coaching_session import (
    CoachingMessage,
    CoachingSession,
)

logger = structlog.get_logger()


class DynamoDBCoachingSessionRepository:
    """DynamoDB repository for coaching session persistence.

    This repository handles storing and retrieving coaching sessions
    in DynamoDB with the following features:
    - Tenant isolation on all queries
    - One active session per tenant per topic enforcement
    - TTL-based auto-cleanup
    - Efficient querying by tenant+topic

    Table Schema:
        - PK: session_id (String)
        - GSI1: tenant-topic-index (tenant_id, topic_id)
        - GSI2: tenant-user-index (tenant_id, user_id)
        - TTL: ttl (Number - Unix timestamp)

    Design:
        - Sessions use tenant-scoped GSI for efficient lookups
        - Active session per topic is enforced at application level
        - Completed/cancelled sessions have TTL for cleanup
    """

    # TTL duration for completed/cancelled sessions (14 days)
    COMPLETED_SESSION_TTL_DAYS = 14

    def __init__(
        self,
        dynamodb_resource: Any,  # boto3.resources.base.ServiceResource
        table_name: str,
    ) -> None:
        """Initialize DynamoDB coaching session repository.

        Args:
            dynamodb_resource: Boto3 DynamoDB resource
            table_name: DynamoDB table name for coaching sessions
        """
        self.dynamodb = dynamodb_resource
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name
        logger.info(
            "coaching_session_repository.initialized",
            table_name=table_name,
        )

    # =========================================================================
    # Core CRUD Operations
    # =========================================================================

    async def create(self, session: CoachingSession) -> CoachingSession:
        """Create a new coaching session.

        Args:
            session: CoachingSession entity to persist

        Returns:
            The created session

        Raises:
            ValueError: If an active session already exists for tenant+topic
        """
        # First, check for existing active session for this tenant+topic
        existing = await self.get_active_by_tenant_topic(
            tenant_id=str(session.tenant_id),
            topic_id=session.topic_id,
        )

        if existing is not None:
            raise ValueError(
                f"Active session already exists for tenant {session.tenant_id} "
                f"and topic {session.topic_id}. Session ID: {existing.session_id}"
            )

        try:
            item = self._to_dynamodb_item(session)
            self.table.put_item(Item=item)

            logger.info(
                "coaching_session.created",
                session_id=session.session_id,
                tenant_id=session.tenant_id,
                topic_id=session.topic_id,
                user_id=session.user_id,
            )
            return session

        except Exception as e:
            logger.error(
                "coaching_session.create_failed",
                session_id=session.session_id,
                error=str(e),
            )
            raise

    async def save(self, session: CoachingSession) -> None:
        """Save (update) a coaching session.

        Args:
            session: CoachingSession entity to persist
        """
        try:
            item = self._to_dynamodb_item(session)

            # Add TTL for terminal states
            if session.status in (
                ConversationStatus.COMPLETED,
                ConversationStatus.CANCELLED,
                ConversationStatus.ABANDONED,
            ):
                # Set TTL to 14 days from now
                ttl_timestamp = int(
                    datetime.now(UTC).timestamp() + (self.COMPLETED_SESSION_TTL_DAYS * 24 * 60 * 60)
                )
                item["ttl"] = ttl_timestamp

            self.table.put_item(Item=item)

            logger.info(
                "coaching_session.saved",
                session_id=session.session_id,
                tenant_id=session.tenant_id,
                status=session.status.value,
            )

        except Exception as e:
            logger.error(
                "coaching_session.save_failed",
                session_id=session.session_id,
                error=str(e),
            )
            raise

    async def get_by_id(
        self,
        session_id: SessionId,
        tenant_id: TenantId,
    ) -> CoachingSession | None:
        """Retrieve a coaching session by ID with tenant isolation.

        Args:
            session_id: Unique session identifier (typed)
            tenant_id: Tenant ID for multi-tenant isolation (typed)

        Returns:
            CoachingSession if found and belongs to tenant, None otherwise
        """
        return await self.get_by_id_for_tenant(str(session_id), str(tenant_id))

    async def _get_by_id_internal(self, session_id: str) -> CoachingSession | None:
        """Internal method to retrieve a coaching session by ID without tenant check.

        This is used internally by get_by_id_for_tenant which enforces isolation.

        Args:
            session_id: Unique session identifier

        Returns:
            CoachingSession if found, None otherwise
        """
        try:
            response = self.table.get_item(Key={"session_id": session_id})

            if "Item" not in response:
                logger.debug("coaching_session.not_found", session_id=session_id)
                return None

            session = self._from_dynamodb_item(response["Item"])
            logger.debug(
                "coaching_session.retrieved",
                session_id=session_id,
                status=session.status.value,
            )
            return session

        except Exception as e:
            logger.error(
                "coaching_session.get_failed",
                session_id=session_id,
                error=str(e),
            )
            raise

    async def get_by_id_for_tenant(
        self,
        session_id: str,
        tenant_id: str,
    ) -> CoachingSession | None:
        """Retrieve a coaching session by ID with tenant isolation.

        Args:
            session_id: Unique session identifier
            tenant_id: Tenant ID for isolation

        Returns:
            CoachingSession if found and belongs to tenant, None otherwise
        """
        session = await self._get_by_id_internal(session_id)

        if session is None:
            return None

        # Enforce tenant isolation
        if str(session.tenant_id) != tenant_id:
            logger.warning(
                "coaching_session.tenant_isolation_violation",
                session_id=session_id,
                requested_tenant=tenant_id,
                actual_tenant=str(session.tenant_id),
            )
            return None

        return session

    async def delete(self, session_id: SessionId, tenant_id: TenantId) -> bool:
        """Delete a coaching session with tenant isolation.

        Args:
            session_id: Session identifier (typed)
            tenant_id: Tenant ID for isolation (typed)

        Returns:
            True if deleted, False if not found or not owned by tenant
        """
        # First verify tenant ownership
        session = await self.get_by_id(session_id, tenant_id)
        if session is None:
            logger.debug(
                "coaching_session.delete_not_found_or_wrong_tenant",
                session_id=str(session_id),
                tenant_id=str(tenant_id),
            )
            return False

        try:
            self.table.delete_item(
                Key={"session_id": str(session_id)},
                ConditionExpression="attribute_exists(session_id)",
            )
            logger.info(
                "coaching_session.deleted",
                session_id=str(session_id),
                tenant_id=str(tenant_id),
            )
            return True

        except self.dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            logger.debug("coaching_session.delete_not_found", session_id=str(session_id))
            return False
        except Exception as e:
            logger.error(
                "coaching_session.delete_failed",
                session_id=str(session_id),
                error=str(e),
            )
            raise

    # =========================================================================
    # Query Operations
    # =========================================================================

    async def get_active_for_topic(
        self,
        topic_id: str,
        tenant_id: TenantId,
    ) -> CoachingSession | None:
        """Get any active session for a topic within a tenant (typed parameters).

        Used for conflict detection when a different user tries to
        initiate a session for a topic that already has an active session.

        Args:
            topic_id: Coaching topic identifier
            tenant_id: Tenant ID for multi-tenant isolation (typed)

        Returns:
            Active CoachingSession for the topic if any exists, None otherwise
        """
        return await self.get_active_by_tenant_topic(str(tenant_id), topic_id)

    async def get_active_by_tenant_topic(
        self,
        tenant_id: str,
        topic_id: str,
    ) -> CoachingSession | None:
        """Get the active session for a tenant and topic.

        This is the primary method for enforcing "one active session per topic"
        rule at the tenant level.

        Args:
            tenant_id: Tenant identifier
            topic_id: Coaching topic identifier

        Returns:
            Active CoachingSession if exists, None otherwise
        """
        try:
            # Query GSI for tenant+topic sessions
            response = self.table.query(
                IndexName="tenant-topic-index",
                KeyConditionExpression=(
                    Key("tenant_id").eq(tenant_id) & Key("topic_id").eq(topic_id)
                ),
            )

            # Find active session among results
            for item in response.get("Items", []):
                session = self._from_dynamodb_item(item)
                if session.status in (
                    ConversationStatus.ACTIVE,
                    ConversationStatus.PAUSED,
                ):
                    logger.debug(
                        "coaching_session.active_found",
                        session_id=session.session_id,
                        tenant_id=tenant_id,
                        topic_id=topic_id,
                        status=session.status.value,
                    )
                    return session

            logger.debug(
                "coaching_session.no_active_found",
                tenant_id=tenant_id,
                topic_id=topic_id,
            )
            return None

        except Exception as e:
            logger.error(
                "coaching_session.query_active_failed",
                tenant_id=tenant_id,
                topic_id=topic_id,
                error=str(e),
            )
            raise

    async def list_by_tenant_user(
        self,
        tenant_id: str,
        user_id: str,
        include_completed: bool = False,
        limit: int = 20,
    ) -> list[CoachingSession]:
        """List coaching sessions for a tenant's user.

        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            include_completed: Whether to include completed sessions
            limit: Maximum number of sessions to return

        Returns:
            List of CoachingSession entities
        """
        try:
            # Query GSI for tenant+user sessions
            response = self.table.query(
                IndexName="tenant-user-index",
                KeyConditionExpression=Key("tenant_id").eq(tenant_id),
                FilterExpression=Key("user_id").eq(user_id),
                ScanIndexForward=False,  # Most recent first
                Limit=limit * 2,  # Fetch extra for filtering
            )

            sessions: list[CoachingSession] = []
            for item in response.get("Items", []):
                session = self._from_dynamodb_item(item)

                # Filter by status if needed
                if not include_completed and session.status in (
                    ConversationStatus.COMPLETED,
                    ConversationStatus.CANCELLED,
                    ConversationStatus.ABANDONED,
                ):
                    continue

                sessions.append(session)

                if len(sessions) >= limit:
                    break

            logger.debug(
                "coaching_session.list_by_user",
                tenant_id=tenant_id,
                user_id=user_id,
                count=len(sessions),
            )
            return sessions

        except Exception as e:
            logger.error(
                "coaching_session.list_by_user_failed",
                tenant_id=tenant_id,
                user_id=user_id,
                error=str(e),
            )
            raise

    async def list_by_user(
        self,
        user_id: UserId,
        tenant_id: TenantId,
        include_completed: bool = False,
        limit: int = 20,
    ) -> list[CoachingSession]:
        """List sessions for a specific user (typed parameters).

        Args:
            user_id: User identifier (typed)
            tenant_id: Tenant ID for isolation (typed)
            include_completed: Whether to include COMPLETED sessions
            limit: Maximum number of sessions to return

        Returns:
            List of sessions ordered by created_at descending
        """
        return await self.list_by_tenant_user(
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            include_completed=include_completed,
            limit=limit,
        )

    async def list_by_tenant_topic(
        self,
        tenant_id: str,
        topic_id: str,
        limit: int = 20,
    ) -> list[CoachingSession]:
        """List coaching sessions for a tenant's topic.

        Args:
            tenant_id: Tenant identifier
            topic_id: Topic identifier
            limit: Maximum number of sessions to return

        Returns:
            List of CoachingSession entities
        """
        try:
            response = self.table.query(
                IndexName="tenant-topic-index",
                KeyConditionExpression=(
                    Key("tenant_id").eq(tenant_id) & Key("topic_id").eq(topic_id)
                ),
                ScanIndexForward=False,
                Limit=limit,
            )

            sessions = [self._from_dynamodb_item(item) for item in response.get("Items", [])]

            logger.debug(
                "coaching_session.list_by_topic",
                tenant_id=tenant_id,
                topic_id=topic_id,
                count=len(sessions),
            )
            return sessions

        except Exception as e:
            logger.error(
                "coaching_session.list_by_topic_failed",
                tenant_id=tenant_id,
                topic_id=topic_id,
                error=str(e),
            )
            raise

    async def get_active_for_user_topic(
        self,
        user_id: str,
        topic_id: str,
        tenant_id: str,
    ) -> CoachingSession | None:
        """Get active session for user+topic combination (Issue #157).

        This method enables:
        - Resuming an existing session instead of creating a new one
        - Detecting session conflicts when different users access same topic

        Args:
            user_id: User identifier
            topic_id: Coaching topic identifier
            tenant_id: Tenant ID for multi-tenant isolation

        Returns:
            Active CoachingSession if found, None otherwise
        """
        try:
            # Use user_topic_key GSI for efficient lookup
            user_topic_key = f"USER#{user_id}#TOPIC#{topic_id}"
            response = self.table.query(
                IndexName="user-topic-index",
                KeyConditionExpression=Key("user_topic_key").eq(user_topic_key),
                FilterExpression=Key("tenant_id").eq(tenant_id),
            )

            # Find active session among results
            for item in response.get("Items", []):
                session = self._from_dynamodb_item(item)
                if session.status in (
                    ConversationStatus.ACTIVE,
                    ConversationStatus.PAUSED,
                ):
                    logger.debug(
                        "coaching_session.user_topic_active_found",
                        session_id=session.session_id,
                        user_id=user_id,
                        topic_id=topic_id,
                        tenant_id=tenant_id,
                        status=session.status.value,
                    )
                    return session

            logger.debug(
                "coaching_session.user_topic_no_active_found",
                user_id=user_id,
                topic_id=topic_id,
                tenant_id=tenant_id,
            )
            return None

        except Exception as e:
            logger.error(
                "coaching_session.get_active_for_user_topic_failed",
                user_id=user_id,
                topic_id=topic_id,
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def update(self, session: CoachingSession) -> CoachingSession:
        """Update an existing coaching session.

        Args:
            session: CoachingSession entity with updated fields

        Returns:
            The updated session

        Raises:
            ValueError: If session doesn't exist
        """
        # Verify session exists
        existing = await self._get_by_id_internal(str(session.session_id))
        if existing is None:
            raise ValueError(f"Session not found: {session.session_id}")

        # Save the updated session
        await self.save(session)
        return session

    async def mark_expired(
        self,
        session_id: SessionId,
        tenant_id: TenantId,
    ) -> bool:
        """Mark a session as expired (typed parameters).

        Args:
            session_id: Session identifier to expire (typed)
            tenant_id: Tenant ID for isolation (typed)

        Returns:
            True if session was marked expired, False if not found or already terminal
        """
        return await self._mark_expired_internal(str(session_id), str(tenant_id))

    async def _mark_expired_internal(
        self,
        session_id: str,
        tenant_id: str,
    ) -> bool:
        """Internal method to mark a session as expired.

        Args:
            session_id: Session identifier to expire
            tenant_id: Tenant ID for isolation

        Returns:
            True if session was marked expired, False if not found or already terminal
        """
        session = await self.get_by_id_for_tenant(session_id, tenant_id)

        if session is None:
            return False

        # Only expire active or paused sessions
        if session.status not in (ConversationStatus.ACTIVE, ConversationStatus.PAUSED):
            logger.debug(
                "coaching_session.mark_expired_skipped",
                session_id=session_id,
                current_status=session.status.value,
            )
            return False

        # Mark as abandoned
        session.mark_expired()
        await self.save(session)

        logger.info(
            "coaching_session.marked_expired",
            session_id=session_id,
            tenant_id=tenant_id,
        )
        return True

    async def get_expired_sessions(
        self,
        tenant_id: TenantId,
        limit: int = 100,
    ) -> list[CoachingSession]:
        """Get sessions that have exceeded their expiration or idle timeout (typed).

        Used by background cleanup processes.

        Args:
            tenant_id: Tenant ID for isolation (typed)
            limit: Maximum number of sessions to return

        Returns:
            List of expired sessions
        """
        return await self._get_expired_sessions_internal(str(tenant_id), limit)

    async def _get_expired_sessions_internal(
        self,
        tenant_id: str,
        limit: int = 100,
    ) -> list[CoachingSession]:
        """Internal method to get expired sessions.

        Args:
            tenant_id: Tenant ID for isolation
            limit: Maximum number of sessions to return

        Returns:
            List of expired sessions
        """
        expired_sessions: list[CoachingSession] = []

        try:
            # Scan for active/paused sessions in this tenant
            # Note: In production, consider using DynamoDB Streams + Lambda
            response = self.table.query(
                IndexName="tenant-topic-index",
                KeyConditionExpression=Key("tenant_id").eq(tenant_id),
                FilterExpression="#status IN (:active, :paused)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":active": ConversationStatus.ACTIVE.value,
                    ":paused": ConversationStatus.PAUSED.value,
                },
            )

            for item in response.get("Items", []):
                session = self._from_dynamodb_item(item)

                # Check expiration
                if session.is_expired() or session.is_idle():
                    expired_sessions.append(session)
                    if len(expired_sessions) >= limit:
                        break

            logger.debug(
                "coaching_session.expired_sessions_found",
                tenant_id=tenant_id,
                count=len(expired_sessions),
            )
            return expired_sessions

        except Exception as e:
            logger.error(
                "coaching_session.get_expired_sessions_failed",
                tenant_id=tenant_id,
                error=str(e),
            )
            raise

    async def find_inactive_sessions(
        self,
        inactivity_threshold_minutes: int = 30,
    ) -> list[CoachingSession]:
        """Find active sessions that have exceeded inactivity threshold.

        Used by background job to auto-pause inactive sessions.

        Args:
            inactivity_threshold_minutes: Minutes of inactivity before flagging

        Returns:
            List of inactive sessions that should be paused
        """
        try:
            # Calculate threshold timestamp
            threshold_time = datetime.now(UTC).timestamp() - (inactivity_threshold_minutes * 60)

            # Scan for active sessions (this is less efficient but needed
            # since we don't have a GSI on status)
            # In production, consider using DynamoDB Streams + Lambda
            response = self.table.scan(
                FilterExpression=("#status = :active AND #last_activity < :threshold"),
                ExpressionAttributeNames={
                    "#status": "status",
                    "#last_activity": "last_activity_at",
                },
                ExpressionAttributeValues={
                    ":active": ConversationStatus.ACTIVE.value,
                    ":threshold": datetime.fromtimestamp(threshold_time, UTC).isoformat(),
                },
            )

            sessions = [self._from_dynamodb_item(item) for item in response.get("Items", [])]

            logger.info(
                "coaching_session.inactive_found",
                count=len(sessions),
                threshold_minutes=inactivity_threshold_minutes,
            )
            return sessions

        except Exception as e:
            logger.error(
                "coaching_session.find_inactive_failed",
                error=str(e),
            )
            raise

    # =========================================================================
    # Serialization
    # =========================================================================

    def _to_dynamodb_item(self, session: CoachingSession) -> dict[str, Any]:
        """Convert CoachingSession entity to DynamoDB item.

        Args:
            session: CoachingSession entity

        Returns:
            DynamoDB item dict
        """
        item: dict[str, Any] = {
            "session_id": str(session.session_id),
            "tenant_id": str(session.tenant_id),
            "topic_id": session.topic_id,
            "user_id": str(session.user_id),
            "status": session.status.value,
            "messages": [self._message_to_dict(m) for m in session.messages],
            "context": session.context,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "last_activity_at": session.last_activity_at.isoformat(),
            # Session limits (Issue #174)
            "max_turns": session.max_turns,
            "idle_timeout_minutes": session.idle_timeout_minutes,
            # GSI for user+topic lookup (Issue #157)
            "user_topic_key": f"USER#{session.user_id}#TOPIC#{session.topic_id}",
        }

        if session.completed_at is not None:
            item["completed_at"] = session.completed_at.isoformat()

        if session.expires_at is not None:
            item["expires_at"] = session.expires_at.isoformat()

        if session.extracted_result is not None:
            item["extracted_result"] = session.extracted_result

        if session.extraction_model is not None:
            item["extraction_model"] = session.extraction_model

        return item

    def _from_dynamodb_item(self, item: dict[str, Any]) -> CoachingSession:
        """Convert DynamoDB item to CoachingSession entity.

        Args:
            item: DynamoDB item dict

        Returns:
            CoachingSession entity
        """
        return CoachingSession(
            session_id=SessionId(item["session_id"]),
            tenant_id=TenantId(item["tenant_id"]),
            topic_id=item["topic_id"],
            user_id=UserId(item["user_id"]),
            status=ConversationStatus(item["status"]),
            messages=[self._dict_to_message(m) for m in item.get("messages", [])],
            context=item.get("context", {}),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            last_activity_at=datetime.fromisoformat(item["last_activity_at"]),
            completed_at=(
                datetime.fromisoformat(item["completed_at"]) if item.get("completed_at") else None
            ),
            # Session limits (Issue #174)
            max_turns=item.get("max_turns", 0),  # 0 = unlimited
            idle_timeout_minutes=item.get("idle_timeout_minutes", 30),
            expires_at=(
                datetime.fromisoformat(item["expires_at"]) if item.get("expires_at") else None
            ),
            # Results
            extracted_result=item.get("extracted_result"),
            extraction_model=item.get("extraction_model"),
        )

    def _message_to_dict(self, message: CoachingMessage) -> dict[str, Any]:
        """Convert CoachingMessage to dict for storage.

        Args:
            message: CoachingMessage instance

        Returns:
            Dictionary representation
        """
        return {
            "role": message.role.value,
            "content": message.content,
            "timestamp": message.timestamp.isoformat(),
            "metadata": message.metadata,
        }

    def _dict_to_message(self, data: dict[str, Any]) -> CoachingMessage:
        """Convert dict to CoachingMessage.

        Args:
            data: Dictionary with message data

        Returns:
            CoachingMessage instance
        """
        return CoachingMessage(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )
