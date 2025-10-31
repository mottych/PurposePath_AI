"""Domain events package.

This package contains all domain events for the coaching system,
supporting event sourcing and observability patterns.
"""

from src.domain.events.analysis_events import (
    AnalysisCompleted,
    AnalysisFailed,
    AnalysisRequested,
)
from src.domain.events.base_event import DomainEvent
from src.domain.events.conversation_events import (
    ConversationCompleted,
    ConversationInitiated,
    ConversationPaused,
    ConversationResumed,
    MessageAdded,
    PhaseTransitioned,
)

__all__ = [
    "AnalysisCompleted",
    "AnalysisFailed",
    # Analysis Events
    "AnalysisRequested",
    "ConversationCompleted",
    # Conversation Events
    "ConversationInitiated",
    "ConversationPaused",
    "ConversationResumed",
    # Base
    "DomainEvent",
    "MessageAdded",
    "PhaseTransitioned",
]
