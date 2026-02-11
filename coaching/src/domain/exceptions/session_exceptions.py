"""Session-specific domain exceptions.

This module defines exceptions related to coaching session operations,
following the design in docs/Specifications/conversation_coaching_design.md.

These exceptions are used by the CoachingSessionService and API layer
to handle session-related errors in a consistent, structured way.
"""

from typing import Any

from coaching.src.core.types import SessionId, TenantId, UserId
from coaching.src.domain.exceptions.base_exception import DomainError


class SessionNotFoundError(DomainError):
    """Raised when a session cannot be found.

    HTTP Status: 422
    Error Code: SESSION_NOT_FOUND
    """

    def __init__(
        self,
        session_id: SessionId | str,
        tenant_id: TenantId | str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SessionNotFoundError.

        Args:
            session_id: The session ID that was not found
            tenant_id: The tenant ID for the lookup
            context: Additional context data
        """
        ctx = context or {}
        ctx["session_id"] = str(session_id)
        if tenant_id:
            ctx["tenant_id"] = str(tenant_id)

        super().__init__(
            message=f"Session not found: {session_id}",
            code="SESSION_NOT_FOUND",
            context=ctx,
        )
        self.session_id = session_id
        self.tenant_id = tenant_id


class SessionExpiredError(DomainError):
    """Raised when attempting to access an expired session.

    HTTP Status: 410
    Error Code: SESSION_EXPIRED
    """

    def __init__(
        self,
        session_id: SessionId | str,
        expired_at: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SessionExpiredError.

        Args:
            session_id: The expired session ID
            expired_at: When the session expired
            context: Additional context data
        """
        ctx = context or {}
        ctx["session_id"] = str(session_id)
        if expired_at:
            ctx["expired_at"] = expired_at

        super().__init__(
            message=f"Session has expired: {session_id}",
            code="SESSION_EXPIRED",
            context=ctx,
        )
        self.session_id = session_id
        self.expired_at = expired_at


class SessionNotActiveError(DomainError):
    """Raised when attempting an operation on a non-active session.

    HTTP Status: 400
    Error Code: SESSION_NOT_ACTIVE
    """

    def __init__(
        self,
        session_id: SessionId | str,
        current_status: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SessionNotActiveError.

        Args:
            session_id: The session ID
            current_status: The current status of the session
            context: Additional context data
        """
        ctx = context or {}
        ctx["session_id"] = str(session_id)
        ctx["current_status"] = current_status

        super().__init__(
            message=f"Session is not active (status: {current_status}): {session_id}",
            code="SESSION_NOT_ACTIVE",
            context=ctx,
        )
        self.session_id = session_id
        self.current_status = current_status


class SessionAccessDeniedError(DomainError):
    """Raised when a user attempts to access a session they don't own.

    HTTP Status: 403
    Error Code: SESSION_ACCESS_DENIED
    """

    def __init__(
        self,
        session_id: SessionId | str,
        user_id: UserId | str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SessionAccessDeniedError.

        Args:
            session_id: The session ID
            user_id: The user attempting access
            context: Additional context data
        """
        ctx = context or {}
        ctx["session_id"] = str(session_id)
        ctx["user_id"] = str(user_id)

        super().__init__(
            message=f"User {user_id} does not have access to session {session_id}",
            code="SESSION_ACCESS_DENIED",
            context=ctx,
        )
        self.session_id = session_id
        self.user_id = user_id


class MaxTurnsReachedError(DomainError):
    """Raised when a session has reached its maximum turns limit.

    HTTP Status: 422
    Error Code: MAX_TURNS_REACHED
    """

    def __init__(
        self,
        session_id: SessionId | str,
        current_turn: int,
        max_turns: int,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MaxTurnsReachedError.

        Args:
            session_id: The session ID
            current_turn: Current turn number
            max_turns: Maximum allowed turns
            context: Additional context data
        """
        ctx = context or {}
        ctx["session_id"] = str(session_id)
        ctx["current_turn"] = current_turn
        ctx["max_turns"] = max_turns

        super().__init__(
            message=f"Session {session_id} has reached maximum turns ({current_turn}/{max_turns})",
            code="MAX_TURNS_REACHED",
            context=ctx,
        )
        self.session_id = session_id
        self.current_turn = current_turn
        self.max_turns = max_turns


class SessionConflictError(DomainError):
    """Raised when a session conflict occurs (e.g., different user has active session).

    This implements Issue #157 - blocking different users from accessing
    an active session for the same topic.

    For idempotent handling (Issue #179), includes optional existing_session
    to allow the service layer to resume instead of failing.

    HTTP Status: 409
    Error Code: SESSION_CONFLICT
    """

    def __init__(
        self,
        topic_id: str,
        tenant_id: TenantId | str,
        requesting_user_id: UserId | str,
        owning_user_id: UserId | str | None = None,
        existing_session: Any | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SessionConflictError.

        Args:
            topic_id: The topic ID with the conflict
            tenant_id: The tenant ID
            requesting_user_id: The user attempting to start a session
            owning_user_id: The user who owns the existing session
            existing_session: The existing session entity (for idempotent handling)
            context: Additional context data
        """
        ctx = context or {}
        ctx["topic_id"] = topic_id
        ctx["tenant_id"] = str(tenant_id)
        ctx["requesting_user_id"] = str(requesting_user_id)
        if owning_user_id:
            ctx["owning_user_id"] = str(owning_user_id)

        message = f"Session conflict: another user has an active session for topic {topic_id}"
        if owning_user_id:
            message = f"Session conflict: user {owning_user_id} has an active session for topic {topic_id}"

        super().__init__(
            message=message,
            code="SESSION_CONFLICT",
            context=ctx,
        )
        self.topic_id = topic_id
        self.tenant_id = tenant_id
        self.requesting_user_id = requesting_user_id
        self.owning_user_id = owning_user_id
        self.existing_session = existing_session


class SessionIdleTimeoutError(DomainError):
    """Raised when a session has exceeded its idle timeout.

    HTTP Status: 410
    Error Code: SESSION_IDLE_TIMEOUT
    """

    def __init__(
        self,
        session_id: SessionId | str,
        last_activity_at: str,
        idle_timeout_minutes: int,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize SessionIdleTimeoutError.

        Args:
            session_id: The session ID
            last_activity_at: When the last activity occurred
            idle_timeout_minutes: The idle timeout in minutes
            context: Additional context data
        """
        ctx = context or {}
        ctx["session_id"] = str(session_id)
        ctx["last_activity_at"] = last_activity_at
        ctx["idle_timeout_minutes"] = idle_timeout_minutes

        super().__init__(
            message=f"Session {session_id} has exceeded idle timeout ({idle_timeout_minutes} minutes)",
            code="SESSION_IDLE_TIMEOUT",
            context=ctx,
        )
        self.session_id = session_id
        self.last_activity_at = last_activity_at
        self.idle_timeout_minutes = idle_timeout_minutes


class ExtractionFailedError(DomainError):
    """Raised when extraction from conversation fails.

    HTTP Status: 500
    Error Code: EXTRACTION_FAILED
    """

    def __init__(
        self,
        session_id: SessionId | str,
        reason: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize ExtractionFailedError.

        Args:
            session_id: The session ID
            reason: Reason for the extraction failure
            context: Additional context data
        """
        ctx = context or {}
        ctx["session_id"] = str(session_id)
        ctx["reason"] = reason

        super().__init__(
            message=f"Failed to extract results from session {session_id}: {reason}",
            code="EXTRACTION_FAILED",
            context=ctx,
        )
        self.session_id = session_id
        self.reason = reason
