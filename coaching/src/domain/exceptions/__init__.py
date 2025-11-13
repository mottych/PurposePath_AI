"""Domain exceptions package.

This package contains all domain-specific exceptions for the coaching system,
providing structured error handling and clear business rule violations.
"""

from src.domain.exceptions.analysis_exceptions import (
    AnalysisNotFound,
    AnalysisTimeout,
    EnrichmentFailed,
    InsufficientDataForAnalysis,
    InvalidAnalysisRequest,
    UnsupportedAnalysisType,
)
from src.domain.exceptions.base_exception import DomainException
from src.domain.exceptions.conversation_exceptions import (
    ConversationCompletionError,
    ConversationNotActive,
    ConversationNotFound,
    ConversationTTLExpired,
    InvalidMessageContent,
    InvalidPhaseTransition,
)
from src.domain.exceptions.topic_exceptions import (
    DuplicateTopicError,
    InvalidParameterDefinitionError,
    InvalidTopicTypeError,
    PromptNotFoundError,
    S3StorageError,
    TopicNotFoundError,
    TopicUpdateError,
)

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
