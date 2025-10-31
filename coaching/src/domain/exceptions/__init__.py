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

__all__ = [
    "AnalysisNotFound",
    "AnalysisTimeout",
    "ConversationCompletionError",
    "ConversationNotActive",
    # Conversation Exceptions
    "ConversationNotFound",
    "ConversationTTLExpired",
    # Base
    "DomainException",
    "EnrichmentFailed",
    "InsufficientDataForAnalysis",
    # Analysis Exceptions
    "InvalidAnalysisRequest",
    "InvalidMessageContent",
    "InvalidPhaseTransition",
    "UnsupportedAnalysisType",
]
