"""Domain exceptions package.

This package contains all domain-specific exceptions for the coaching system,
providing structured error handling and clear business rule violations.
"""

from coaching.src.domain.exceptions.analysis_exceptions import (
    AnalysisNotFound,
    AnalysisTimeout,
    EnrichmentFailed,
    InsufficientDataForAnalysis,
    InvalidAnalysisRequest,
    UnsupportedAnalysisType,
)
from coaching.src.domain.exceptions.base_exception import DomainException
from coaching.src.domain.exceptions.conversation_exceptions import (
    ConversationCompletionError,
    ConversationNotActive,
    ConversationNotFound,
    ConversationTTLExpired,
    InvalidMessageContent,
    InvalidPhaseTransition,
)

__all__ = [
    # Base
    "DomainException",
    # Conversation Exceptions
    "ConversationNotFound",
    "InvalidPhaseTransition",
    "ConversationNotActive",
    "InvalidMessageContent",
    "ConversationTTLExpired",
    "ConversationCompletionError",
    # Analysis Exceptions
    "InvalidAnalysisRequest",
    "EnrichmentFailed",
    "AnalysisNotFound",
    "UnsupportedAnalysisType",
    "AnalysisTimeout",
    "InsufficientDataForAnalysis",
]
