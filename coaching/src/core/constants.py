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
    - measure_system: Measure-specific operations with scoring thresholds
    """

    CONVERSATION_COACHING = "conversation_coaching"
    SINGLE_SHOT = "single_shot"
    MEASURE_SYSTEM = "measure_system"


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

    # Single Measure from Traction Service
    MEASURE = "measure"

    # All Measures list from Traction Service
    MEASURES = "measures"

    # Action item from Traction Service
    ACTION = "action"

    # Issue from Traction Service
    ISSUE = "issue"

    # User profile data from Account Service
    USER = "user"

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
    MEASURE = "measure"
    SWOT = "swot"
    ROOT_CAUSE = "root_cause"
    ACTION_PLAN = "action_plan"
    GOAL_BREAKDOWN = "goal_breakdown"


class TierLevel(str, Enum):
    """Subscription tier levels for topic and LLM access control.

    Determines:
    1. Which topics are accessible (topics have a tier_level)
    2. Which LLM model to use (topics have basic_model_code and premium_model_code)

    Access Rules:
    - FREE: Can access only Free topics, uses basic_model_code
    - BASIC: Can access Free + Basic topics, uses basic_model_code
    - PREMIUM: Can access Free + Basic + Premium topics, uses premium_model_code
    - ULTIMATE: Can access all topics (Free + Basic + Premium + Ultimate), uses premium_model_code
    """

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ULTIMATE = "ultimate"

    @classmethod
    def can_access_topic(cls, user_tier: "TierLevel", topic_tier: "TierLevel") -> bool:
        """Check if a user tier can access a topic tier.

        Args:
            user_tier: User's subscription tier
            topic_tier: Topic's tier level requirement

        Returns:
            bool: True if user can access the topic
        """
        tier_hierarchy = {
            cls.FREE: [cls.FREE],
            cls.BASIC: [cls.FREE, cls.BASIC],
            cls.PREMIUM: [cls.FREE, cls.BASIC, cls.PREMIUM],
            cls.ULTIMATE: [cls.FREE, cls.BASIC, cls.PREMIUM, cls.ULTIMATE],
        }
        return topic_tier in tier_hierarchy.get(user_tier, [])

    def uses_premium_model(self) -> bool:
        """Check if this tier uses premium LLM model.

        Returns:
            bool: True if tier uses premium_model_code, False if uses basic_model_code
        """
        return self in (TierLevel.PREMIUM, TierLevel.ULTIMATE)


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
