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
