"""Constants for the coaching module."""

from enum import Enum


class CoachingTopic(str, Enum):
    """Available coaching topics."""

    CORE_VALUES = "core_values"
    PURPOSE = "purpose"
    VISION = "vision"
    GOALS = "goals"


class TopicType(str, Enum):
    """Type of topic determining conversation behavior.

    - conversation_coaching: Multi-turn coaching conversations with phases
    - single_shot: One-time analysis or generation requests
    - kpi_system: KPI-specific operations with scoring thresholds
    """

    CONVERSATION_COACHING = "conversation_coaching"
    SINGLE_SHOT = "single_shot"
    KPI_SYSTEM = "kpi_system"


class TopicCategory(str, Enum):
    """Logical grouping of topics by functional area.

    Categories align with API route groupings and business domains.
    """

    ONBOARDING = "onboarding"
    CONVERSATION = "conversation"
    INSIGHTS = "insights"
    STRATEGIC_PLANNING = "strategic_planning"
    OPERATIONS_AI = "operations_ai"
    OPERATIONS_STRATEGIC_INTEGRATION = "operations_strategic_integration"
    ANALYSIS = "analysis"


class PromptType(str, Enum):
    """Types of prompts in a prompt template.

    - system: System-level instructions for the LLM
    - user: User message templates
    - assistant: Pre-filled assistant response templates
    - function: Function/tool call definitions
    - initiation: Instructions for starting a coaching conversation
    - resume: Instructions for resuming a paused coaching conversation
    - extraction: Instructions for extracting final results from coaching
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    # Coaching-specific prompt types
    INITIATION = "initiation"
    RESUME = "resume"
    EXTRACTION = "extraction"


class ParameterType(str, Enum):
    """Data types for parameters in prompt templates."""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ParameterSource(str, Enum):
    """Source of parameter data for prompt templates.

    Parameters are grouped by source to enable efficient batch retrieval.
    One API call is made per source group, then individual values extracted.
    """

    # Request-provided parameters (from API call)
    REQUEST = "request"

    # Onboarding data from Account Service
    ONBOARDING = "onboarding"

    # Website content from URL scraping
    WEBSITE = "website"

    # Single goal from Traction Service
    GOAL = "goal"

    # All goals list from Traction Service
    GOALS = "goals"

    # Single KPI from Traction Service
    KPI = "kpi"

    # All KPIs list from Traction Service
    KPIS = "kpis"

    # Action item from Traction Service
    ACTION = "action"

    # Issue from Traction Service
    ISSUE = "issue"

    # Conversation context (computed from current conversation)
    CONVERSATION = "conversation"

    # Computed values derived from other parameters
    COMPUTED = "computed"


class ConversationStatus(str, Enum):
    """Conversation status values."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
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
