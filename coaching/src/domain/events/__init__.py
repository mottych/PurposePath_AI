"""Domain events package.

This package contains all domain events for the coaching system,
supporting event sourcing and observability patterns.
"""

from coaching.src.domain.events.analysis_events import (
    AnalysisCompleted,
    AnalysisFailed,
    AnalysisRequested,
)
from coaching.src.domain.events.base_event import DomainEvent
from coaching.src.domain.events.conversation_events import (
    ConversationCompleted,
    ConversationInitiated,
    ConversationPaused,
    ConversationResumed,
    MessageAdded,
    PhaseTransitioned,
)

__all__ = [
    # Base
    "DomainEvent",
    # Conversation Events
    "ConversationInitiated",
    "MessageAdded",
    "PhaseTransitioned",
    "ConversationCompleted",
    "ConversationPaused",
    "ConversationResumed",
    # Analysis Events
    "AnalysisRequested",
    "AnalysisCompleted",
    "AnalysisFailed",
]
