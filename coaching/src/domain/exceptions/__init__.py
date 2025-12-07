"""Domain exceptions package.

This package contains all domain-specific exceptions for the coaching system,
providing structured error handling and clear business rule violations.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Import for type checking only to avoid circular imports
    from coaching.src.domain.exceptions.analysis_exceptions import (
        AnalysisNotFound,
        AnalysisTimeout,
        EnrichmentFailed,
        InsufficientDataForAnalysis,
        InvalidAnalysisRequest,
        UnsupportedAnalysisType,
    )
    from coaching.src.domain.exceptions.base_exception import DomainError, DomainException
    from coaching.src.domain.exceptions.conversation_exceptions import (
        ConversationCompletionError,
        ConversationNotActive,
        ConversationNotFound,
        ConversationTTLExpired,
        InvalidMessageContent,
        InvalidPhaseTransition,
    )
    from coaching.src.domain.exceptions.topic_exceptions import (
        DuplicateTopicError,
        InvalidParameterDefinitionError,
        InvalidTopicTypeError,
        PromptNotFoundError,
        S3StorageError,
        TopicNotFoundError,
        TopicUpdateError,
    )
else:
    # Runtime imports - lazy to avoid circular dependency issues
    import sys

    def __getattr__(name: str) -> type:
        """Lazy import exceptions at runtime."""
        if name in _EXCEPTION_MAP:
            module_name, class_name = _EXCEPTION_MAP[name]
            module = __import__(module_name, fromlist=[class_name])
            return getattr(module, class_name)
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    _EXCEPTION_MAP = {
        "DomainException": ("coaching.src.domain.exceptions.base_exception", "DomainException"),
        "DomainError": ("coaching.src.domain.exceptions.base_exception", "DomainError"),
        "AnalysisNotFound": (
            "coaching.src.domain.exceptions.analysis_exceptions",
            "AnalysisNotFound",
        ),
        "AnalysisTimeout": (
            "coaching.src.domain.exceptions.analysis_exceptions",
            "AnalysisTimeout",
        ),
        "EnrichmentFailed": (
            "coaching.src.domain.exceptions.analysis_exceptions",
            "EnrichmentFailed",
        ),
        "InsufficientDataForAnalysis": (
            "coaching.src.domain.exceptions.analysis_exceptions",
            "InsufficientDataForAnalysis",
        ),
        "InvalidAnalysisRequest": (
            "coaching.src.domain.exceptions.analysis_exceptions",
            "InvalidAnalysisRequest",
        ),
        "UnsupportedAnalysisType": (
            "coaching.src.domain.exceptions.analysis_exceptions",
            "UnsupportedAnalysisType",
        ),
        "ConversationCompletionError": (
            "coaching.src.domain.exceptions.conversation_exceptions",
            "ConversationCompletionError",
        ),
        "ConversationNotActive": (
            "coaching.src.domain.exceptions.conversation_exceptions",
            "ConversationNotActive",
        ),
        "ConversationNotFound": (
            "coaching.src.domain.exceptions.conversation_exceptions",
            "ConversationNotFound",
        ),
        "ConversationTTLExpired": (
            "coaching.src.domain.exceptions.conversation_exceptions",
            "ConversationTTLExpired",
        ),
        "InvalidMessageContent": (
            "coaching.src.domain.exceptions.conversation_exceptions",
            "InvalidMessageContent",
        ),
        "InvalidPhaseTransition": (
            "coaching.src.domain.exceptions.conversation_exceptions",
            "InvalidPhaseTransition",
        ),
        "DuplicateTopicError": (
            "coaching.src.domain.exceptions.topic_exceptions",
            "DuplicateTopicError",
        ),
        "InvalidParameterDefinitionError": (
            "coaching.src.domain.exceptions.topic_exceptions",
            "InvalidParameterDefinitionError",
        ),
        "InvalidTopicTypeError": (
            "coaching.src.domain.exceptions.topic_exceptions",
            "InvalidTopicTypeError",
        ),
        "PromptNotFoundError": (
            "coaching.src.domain.exceptions.topic_exceptions",
            "PromptNotFoundError",
        ),
        "S3StorageError": ("coaching.src.domain.exceptions.topic_exceptions", "S3StorageError"),
        "TopicNotFoundError": (
            "coaching.src.domain.exceptions.topic_exceptions",
            "TopicNotFoundError",
        ),
        "TopicUpdateError": ("coaching.src.domain.exceptions.topic_exceptions", "TopicUpdateError"),
    }

__all__ = [
    # Analysis Exceptions
    "AnalysisNotFound",
    "AnalysisTimeout",
    # Conversation Exceptions
    "ConversationCompletionError",
    "ConversationNotActive",
    "ConversationNotFound",
    "ConversationTTLExpired",
    # Base
    "DomainException",
    # Topic Exceptions
    "DuplicateTopicError",
    "EnrichmentFailed",
    "InsufficientDataForAnalysis",
    "InvalidAnalysisRequest",
    "InvalidMessageContent",
    "InvalidParameterDefinitionError",
    "InvalidPhaseTransition",
    "InvalidTopicTypeError",
    "PromptNotFoundError",
    "S3StorageError",
    "TopicNotFoundError",
    "TopicUpdateError",
    "UnsupportedAnalysisType",
]
