"""Constants for the coaching module."""

from enum import Enum


class CoachingTopic(str, Enum):
    """Available coaching topics."""

    CORE_VALUES = "core_values"
    PURPOSE = "purpose"
    VISION = "vision"
    GOALS = "goals"


class ConversationStatus(str, Enum):
    """Conversation status values."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ConversationPhase(str, Enum):
    """Conversation phases."""

    INTRODUCTION = "introduction"
    EXPLORATION = "exploration"
    DEEPENING = "deepening"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    COMPLETION = "completion"


class MessageRole(str, Enum):
    """Message roles in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""

    ALIGNMENT = "alignment"
    STRATEGY = "strategy"
    KPI = "kpi"
    SWOT = "swot"
    ROOT_CAUSE = "root_cause"
    ACTION_PLAN = "action_plan"
    GOAL_BREAKDOWN = "goal_breakdown"


# Default LLM models for each topic
DEFAULT_LLM_MODELS = {
    CoachingTopic.CORE_VALUES: "anthropic.claude-3-sonnet-20240229-v1:0",
    CoachingTopic.PURPOSE: "anthropic.claude-3-sonnet-20240229-v1:0",
    CoachingTopic.VISION: "anthropic.claude-3-haiku-20240307-v1:0",
    CoachingTopic.GOALS: "anthropic.claude-3-haiku-20240307-v1:0",
}

# Progress weights for each phase
PHASE_PROGRESS_WEIGHTS = {
    ConversationPhase.INTRODUCTION: 0.1,
    ConversationPhase.EXPLORATION: 0.3,
    ConversationPhase.DEEPENING: 0.5,
    ConversationPhase.SYNTHESIS: 0.7,
    ConversationPhase.VALIDATION: 0.9,
    ConversationPhase.COMPLETION: 1.0,
}

# Minimum requirements for phase advancement
PHASE_REQUIREMENTS = {
    ConversationPhase.EXPLORATION: {
        "min_responses": 1,
        "min_time_seconds": 0,
    },
    ConversationPhase.DEEPENING: {
        "min_responses": 3,
        "min_categories_explored": 2,
        "min_time_seconds": 300,
    },
    ConversationPhase.SYNTHESIS: {
        "min_responses": 5,
        "min_insights": 3,
        "min_time_seconds": 600,
    },
    ConversationPhase.VALIDATION: {
        "min_responses": 7,
        "min_insights": 5,
        "min_time_seconds": 900,
    },
    ConversationPhase.COMPLETION: {
        "min_responses": 10,
        "min_insights": 7,
        "min_time_seconds": 1200,
    },
}
