"""Core type definitions for the coaching domain.

This module provides strongly-typed domain identifiers using NewType for
compile-time type safety while maintaining string runtime behavior.

All domain IDs should use these types to ensure type safety across the application.
"""

from typing import NewType
from uuid import uuid4

# Domain ID Types
# These use NewType for compile-time type safety while remaining strings at runtime
ConversationId = NewType("ConversationId", str)
"""Unique identifier for a coaching conversation."""

TemplateId = NewType("TemplateId", str)
"""Unique identifier for a prompt template."""

PromptTemplateId = TemplateId
"""Alias for TemplateId - used for prompt templates."""

AnalysisRequestId = NewType("AnalysisRequestId", str)
"""Unique identifier for an analysis request."""

UserId = NewType("UserId", str)
"""Unique identifier for a user."""

TenantId = NewType("TenantId", str)
"""Unique identifier for a tenant/organization."""

MessageId = NewType("MessageId", str)
"""Unique identifier for a message within a conversation."""

SessionId = NewType("SessionId", str)
"""Unique identifier for a coaching session."""


# ID Factory Functions
def create_conversation_id() -> ConversationId:
    """
    Create a new unique conversation identifier.

    Returns:
        ConversationId: A new unique conversation ID

    Example:
        >>> conv_id = create_conversation_id()
        >>> print(conv_id)
        'conv_123e4567-e89b-12d3-a456-426614174000'
    """
    return ConversationId(f"conv_{uuid4()}")


def create_template_id() -> TemplateId:
    """
    Create a new unique template identifier.

    Returns:
        TemplateId: A new unique template ID

    Example:
        >>> template_id = create_template_id()
        >>> print(template_id)
        'tmpl_123e4567-e89b-12d3-a456-426614174000'
    """
    return TemplateId(f"tmpl_{uuid4()}")


def create_analysis_request_id() -> AnalysisRequestId:
    """
    Create a new unique analysis request identifier.

    Returns:
        AnalysisRequestId: A new unique analysis request ID

    Example:
        >>> req_id = create_analysis_request_id()
        >>> print(req_id)
        'anls_123e4567-e89b-12d3-a456-426614174000'
    """
    return AnalysisRequestId(f"anls_{uuid4()}")


def create_user_id(raw_id: str) -> UserId:
    """
    Create a user identifier from a raw string.

    Args:
        raw_id: The raw user ID string

    Returns:
        UserId: A strongly-typed user ID

    Example:
        >>> user_id = create_user_id("user_123")
        >>> print(user_id)
        'user_123'
    """
    return UserId(raw_id)


def create_tenant_id(raw_id: str) -> TenantId:
    """
    Create a tenant identifier from a raw string.

    Args:
        raw_id: The raw tenant ID string

    Returns:
        TenantId: A strongly-typed tenant ID

    Example:
        >>> tenant_id = create_tenant_id("tenant_456")
        >>> print(tenant_id)
        'tenant_456'
    """
    return TenantId(raw_id)


def create_message_id() -> MessageId:
    """
    Create a new unique message identifier.

    Returns:
        MessageId: A new unique message ID

    Example:
        >>> msg_id = create_message_id()
        >>> print(msg_id)
        'msg_123e4567-e89b-12d3-a456-426614174000'
    """
    return MessageId(f"msg_{uuid4()}")


def create_session_id() -> SessionId:
    """
    Create a new unique session identifier.

    Returns:
        SessionId: A new unique session ID

    Example:
        >>> session_id = create_session_id()
        >>> print(session_id)
        'sess_123e4567-e89b-12d3-a456-426614174000'
    """
    return SessionId(f"sess_{uuid4()}")


__all__ = [
    "AnalysisRequestId",
    # Types
    "ConversationId",
    "MessageId",
    "SessionId",
    "TemplateId",
    "TenantId",
    "UserId",
    "create_analysis_request_id",
    # Factory functions
    "create_conversation_id",
    "create_message_id",
    "create_session_id",
    "create_template_id",
    "create_tenant_id",
    "create_user_id",
]
