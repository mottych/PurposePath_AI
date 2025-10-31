"""Conversation domain exceptions.

This module contains all exceptions related to conversation operations
and business rule violations.
"""

from typing import Any

from src.core.constants import ConversationPhase, ConversationStatus
from src.domain.exceptions.base_exception import DomainException


class ConversationNotFound(DomainException):
    """
    Raised when a requested conversation does not exist.

    This is typically a 404 equivalent in the domain layer.
    """

    def __init__(self, conversation_id: str, tenant_id: str | None = None) -> None:
        """
        Initialize exception.

        Args:
            conversation_id: ID of the conversation that was not found
            tenant_id: Optional tenant ID for multi-tenant context
        """
        context: dict[str, Any] = {"conversation_id": conversation_id}
        if tenant_id:
            context["tenant_id"] = tenant_id

        super().__init__(
            message=f"Conversation '{conversation_id}' not found",
            code="CONVERSATION_NOT_FOUND",
            context=context,
        )


class InvalidPhaseTransition(DomainException):
    """
    Raised when attempting an invalid conversation phase transition.

    Business Rule: Phases must progress sequentially, no backward transitions allowed.
    """

    def __init__(
        self,
        conversation_id: str,
        current_phase: ConversationPhase,
        target_phase: ConversationPhase,
        reason: str | None = None,
    ) -> None:
        """
        Initialize exception.

        Args:
            conversation_id: ID of the conversation
            current_phase: Current phase of the conversation
            target_phase: Phase that was attempted
            reason: Optional specific reason why transition is invalid
        """
        message = f"Cannot transition from {current_phase.value} to {target_phase.value}" + (
            f": {reason}" if reason else ""
        )

        super().__init__(
            message=message,
            code="INVALID_PHASE_TRANSITION",
            context={
                "conversation_id": conversation_id,
                "current_phase": current_phase.value,
                "target_phase": target_phase.value,
                "reason": reason,
            },
        )


class ConversationNotActive(DomainException):
    """
    Raised when attempting to modify a conversation that is not active.

    Business Rule: Only active conversations can receive new messages or updates.
    """

    def __init__(
        self, conversation_id: str, current_status: ConversationStatus, operation: str
    ) -> None:
        """
        Initialize exception.

        Args:
            conversation_id: ID of the conversation
            current_status: Current status of the conversation
            operation: The operation that was attempted
        """
        super().__init__(
            message=f"Cannot {operation} conversation in {current_status.value} status",
            code="CONVERSATION_NOT_ACTIVE",
            context={
                "conversation_id": conversation_id,
                "current_status": current_status.value,
                "operation": operation,
            },
        )


class InvalidMessageContent(DomainException):
    """
    Raised when message content fails validation.

    Business Rule: Messages must meet minimum quality standards.
    """

    def __init__(
        self, conversation_id: str, validation_errors: list[str], content_length: int = 0
    ) -> None:
        """
        Initialize exception.

        Args:
            conversation_id: ID of the conversation
            validation_errors: List of specific validation failures
            content_length: Length of the invalid content
        """
        super().__init__(
            message=f"Invalid message content: {', '.join(validation_errors)}",
            code="INVALID_MESSAGE_CONTENT",
            context={
                "conversation_id": conversation_id,
                "validation_errors": validation_errors,
                "content_length": content_length,
            },
        )


class ConversationTTLExpired(DomainException):
    """
    Raised when attempting to access a conversation past its TTL.

    Business Rule: Conversations have a time-to-live for cleanup.
    """

    def __init__(self, conversation_id: str, expired_at: str) -> None:
        """
        Initialize exception.

        Args:
            conversation_id: ID of the conversation
            expired_at: ISO format timestamp when conversation expired
        """
        super().__init__(
            message=f"Conversation expired at {expired_at}",
            code="CONVERSATION_TTL_EXPIRED",
            context={
                "conversation_id": conversation_id,
                "expired_at": expired_at,
            },
        )


class ConversationCompletionError(DomainException):
    """
    Raised when conversation cannot be marked complete due to unmet criteria.

    Business Rule: Conversations must meet all completion criteria.
    """

    def __init__(
        self, conversation_id: str, missing_requirements: list[str], progress: float = 0.0
    ) -> None:
        """
        Initialize exception.

        Args:
            conversation_id: ID of the conversation
            missing_requirements: List of unmet completion requirements
            progress: Current completion progress percentage
        """
        super().__init__(
            message=f"Conversation cannot be completed: {', '.join(missing_requirements)}",
            code="CONVERSATION_COMPLETION_ERROR",
            context={
                "conversation_id": conversation_id,
                "missing_requirements": missing_requirements,
                "progress_percentage": progress,
            },
        )


__all__ = [
    "ConversationCompletionError",
    "ConversationNotActive",
    "ConversationNotFound",
    "ConversationTTLExpired",
    "InvalidMessageContent",
    "InvalidPhaseTransition",
]
