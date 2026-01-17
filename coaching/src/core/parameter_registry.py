"""
Parameter Registry for Coaching Engine.

This module defines all parameters that can be used in coaching templates,
along with their types, defaults, and retrieval method directives.

Key concepts:
- ParameterDefinition: Defines a parameter's type, default, and how to retrieve it
- retrieval_method: Name of method in retrieval_method_registry to call for enrichment
- extraction_path: Path to extract specific value from retrieval method result

Note: The `required` attribute is NOT in ParameterDefinition - it varies per endpoint
and is defined in ParameterRef within endpoint_registry.py.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ParameterType(Enum):
    """Types of parameters supported in coaching templates."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    DATETIME = "datetime"


@dataclass(frozen=True)
class ParameterDefinition:
    """
    Definition of a parameter that can be used in coaching templates.

    Attributes:
        name: Unique identifier for the parameter.
        param_type: The data type of the parameter.
        description: Human-readable description of the parameter.
        default: Default value if not provided.
        retrieval_method: Name of method in retrieval_method_registry to call
            for enrichment when parameter is not in payload. None means parameter
            must be provided directly in request or has a static default.
        extraction_path: Dot-notation path to extract specific value from
            retrieval method result. Empty string means use full result.
    """

    name: str
    param_type: ParameterType
    description: str = ""
    default: Any = None
    retrieval_method: str | None = None
    extraction_path: str = ""


# =============================================================================
# PARAMETER REGISTRY
# =============================================================================
# All parameters that can be used in coaching templates.
# Organized by category for maintainability.
# =============================================================================

PARAMETER_REGISTRY: dict[str, ParameterDefinition] = {}


def _register(param: ParameterDefinition) -> ParameterDefinition:
    """Register a parameter definition."""
    PARAMETER_REGISTRY[param.name] = param
    return param


# -----------------------------------------------------------------------------
# User and Session Context Parameters
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="user_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of the user.",
    )
)

_register(
    ParameterDefinition(
        name="tenant_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of the tenant.",
    )
)

_register(
    ParameterDefinition(
        name="user_name",
        param_type=ParameterType.STRING,
        description="The display name of the user.",
        default="User",
        retrieval_method="get_user_context",
        extraction_path="user_name",
    )
)

_register(
    ParameterDefinition(
        name="session_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of the current session.",
    )
)

# -----------------------------------------------------------------------------
# Business Foundation Parameters (from get_business_foundation)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="business_foundation",
        param_type=ParameterType.DICT,
        description="Complete business foundation data for the tenant.",
        retrieval_method="get_business_foundation",
        extraction_path="",
    )
)

_register(
    ParameterDefinition(
        name="core_values",
        param_type=ParameterType.LIST,
        description="The core values of the business.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="core_values",
    )
)

# NOTE: mission_statement renamed to 'purpose', vision_statement renamed to 'vision'
# See new parameters below for updated naming

_register(
    ParameterDefinition(
        name="vision",
        param_type=ParameterType.STRING,
        description="The vision statement of the business.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="vision",
    )
)

_register(
    ParameterDefinition(
        name="purpose",
        param_type=ParameterType.STRING,
        description="The purpose/mission statement of the business.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="purpose",
    )
)

_register(
    ParameterDefinition(
        name="company_name",
        param_type=ParameterType.STRING,
        description="The name of the company.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="company_name",
    )
)

_register(
    ParameterDefinition(
        name="business_name",
        param_type=ParameterType.STRING,
        description="The business name (alias for company_name).",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="company_name",
    )
)

_register(
    ParameterDefinition(
        name="industry",
        param_type=ParameterType.STRING,
        description="The industry of the business.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="industry",
    )
)

# NOTE: target_audience replaced by 'icas' (Ideal Customer Avatars) array
_register(
    ParameterDefinition(
        name="icas",
        param_type=ParameterType.LIST,
        description="Ideal Customer Avatars (ICAs) for the business.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="icas",
    )
)

_register(
    ParameterDefinition(
        name="unique_value_proposition",
        param_type=ParameterType.STRING,
        description="The unique value proposition of the business.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="unique_value_proposition",
    )
)

# Business Profile (Pillar 1)
_register(
    ParameterDefinition(
        name="business_description",
        param_type=ParameterType.STRING,
        description="Description of the business.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="business_description",
    )
)

_register(
    ParameterDefinition(
        name="company_stage",
        param_type=ParameterType.STRING,
        description="Stage of the company (startup, growth, scale, mature).",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="company_stage",
    )
)

_register(
    ParameterDefinition(
        name="company_size",
        param_type=ParameterType.STRING,
        description="Size of the company (solo, micro, small, medium, large, enterprise).",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="company_size",
    )
)

_register(
    ParameterDefinition(
        name="revenue_range",
        param_type=ParameterType.STRING,
        description="Revenue range of the business.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="revenue_range",
    )
)

_register(
    ParameterDefinition(
        name="year_founded",
        param_type=ParameterType.INTEGER,
        description="Year the business was founded.",
        retrieval_method="get_business_foundation",
        extraction_path="year_founded",
    )
)

_register(
    ParameterDefinition(
        name="geographic_focus",
        param_type=ParameterType.LIST,
        description="Geographic focus areas (local, regional, national, global).",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="geographic_focus",
    )
)

_register(
    ParameterDefinition(
        name="website",
        param_type=ParameterType.STRING,
        description="Business website URL.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="website",
    )
)

# Business Identity (Pillar 2) - vision, purpose, core_values already defined above
_register(
    ParameterDefinition(
        name="vision_timeframe",
        param_type=ParameterType.STRING,
        description="Timeframe for the vision (e.g., 3-5 years).",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="vision_timeframe",
    )
)

_register(
    ParameterDefinition(
        name="who_we_serve",
        param_type=ParameterType.STRING,
        description="Description of who the business serves.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="who_we_serve",
    )
)

# Target Market (Pillar 3) - icas already defined above
_register(
    ParameterDefinition(
        name="niche_statement",
        param_type=ParameterType.STRING,
        description="The business niche statement.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="niche_statement",
    )
)

_register(
    ParameterDefinition(
        name="market_size",
        param_type=ParameterType.STRING,
        description="Estimated market size.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="market_size",
    )
)

_register(
    ParameterDefinition(
        name="growth_trend",
        param_type=ParameterType.STRING,
        description="Market growth trend.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="growth_trend",
    )
)

_register(
    ParameterDefinition(
        name="market_characteristics",
        param_type=ParameterType.LIST,
        description="Key market characteristics.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="market_characteristics",
    )
)

# Products & Services (Pillar 4)
_register(
    ParameterDefinition(
        name="products",
        param_type=ParameterType.LIST,
        description="List of products and services offered.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="products",
    )
)

# Value Proposition (Pillar 5) - unique_value_proposition already defined above
_register(
    ParameterDefinition(
        name="unique_selling_proposition",
        param_type=ParameterType.STRING,
        description="The unique selling proposition.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="unique_selling_proposition",
    )
)

_register(
    ParameterDefinition(
        name="key_differentiators",
        param_type=ParameterType.LIST,
        description="Key differentiators from competitors.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="key_differentiators",
    )
)

_register(
    ParameterDefinition(
        name="competitive_advantages",
        param_type=ParameterType.LIST,
        description="Competitive advantages.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="competitive_advantages",
    )
)

_register(
    ParameterDefinition(
        name="brand_promise",
        param_type=ParameterType.STRING,
        description="The brand promise.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="brand_promise",
    )
)

_register(
    ParameterDefinition(
        name="positioning_statement",
        param_type=ParameterType.STRING,
        description="The positioning statement.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="positioning_statement",
    )
)

# Business Model (Pillar 6)
_register(
    ParameterDefinition(
        name="business_model_types",
        param_type=ParameterType.LIST,
        description="Types of business models used.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="business_model_types",
    )
)

_register(
    ParameterDefinition(
        name="revenue_streams",
        param_type=ParameterType.LIST,
        description="Revenue streams for the business.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="revenue_streams",
    )
)

_register(
    ParameterDefinition(
        name="pricing_strategy",
        param_type=ParameterType.STRING,
        description="Pricing strategy.",
        default="",
        retrieval_method="get_business_foundation",
        extraction_path="pricing_strategy",
    )
)

_register(
    ParameterDefinition(
        name="key_partnerships",
        param_type=ParameterType.LIST,
        description="Key business partnerships.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="key_partnerships",
    )
)

_register(
    ParameterDefinition(
        name="distribution_channels",
        param_type=ParameterType.LIST,
        description="Distribution channels.",
        default=[],
        retrieval_method="get_business_foundation",
        extraction_path="distribution_channels",
    )
)

# NOTE: short_term_objectives, long_term_objectives, brand_voice, brand_personality
# removed - these fields no longer exist in the business foundation API.
# Use goals/strategies for objectives, and business model for brand context.

# -----------------------------------------------------------------------------
# Goal Parameters (from get_goal_by_id or get_goals_list)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="goal_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of a goal.",
    )
)

_register(
    ParameterDefinition(
        name="goal",
        param_type=ParameterType.DICT,
        description="Complete goal data.",
        retrieval_method="get_goal_by_id",
        extraction_path="",
    )
)

_register(
    ParameterDefinition(
        name="goal_title",
        param_type=ParameterType.STRING,
        description="The title of the goal.",
        default="",
        retrieval_method="get_goal_by_id",
        extraction_path="title",
    )
)

_register(
    ParameterDefinition(
        name="goal_description",
        param_type=ParameterType.STRING,
        description="The description of the goal.",
        default="",
        retrieval_method="get_goal_by_id",
        extraction_path="description",
    )
)

_register(
    ParameterDefinition(
        name="goal_status",
        param_type=ParameterType.STRING,
        description="The current status of the goal.",
        default="",
        retrieval_method="get_goal_by_id",
        extraction_path="status",
    )
)

_register(
    ParameterDefinition(
        name="goal_progress",
        param_type=ParameterType.FLOAT,
        description="Progress percentage of the goal.",
        default=0.0,
        retrieval_method="get_goal_by_id",
        extraction_path="progress",
    )
)

_register(
    ParameterDefinition(
        name="goal_due_date",
        param_type=ParameterType.DATETIME,
        description="The due date of the goal.",
        retrieval_method="get_goal_by_id",
        extraction_path="due_date",
    )
)

_register(
    ParameterDefinition(
        name="goals_list",
        param_type=ParameterType.LIST,
        description="List of all goals for the user.",
        default=[],
        retrieval_method="get_goals_list",
        extraction_path="",
    )
)

# -----------------------------------------------------------------------------
# Goal Aggregation Parameters (from get_all_goals)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="goals",
        param_type=ParameterType.LIST,
        description="List of all goals for the tenant.",
        default=[],
        retrieval_method="get_all_goals",
        extraction_path="goals",
    )
)

_register(
    ParameterDefinition(
        name="goals_count",
        param_type=ParameterType.INTEGER,
        description="Total number of goals.",
        default=0,
        retrieval_method="get_all_goals",
        extraction_path="goals_count",
    )
)

_register(
    ParameterDefinition(
        name="goals_summary",
        param_type=ParameterType.STRING,
        description="Summary of goals by status.",
        default="",
        retrieval_method="get_all_goals",
        extraction_path="goals_summary",
    )
)

# -----------------------------------------------------------------------------
# Strategy Parameters (from get_strategy_by_id or get_all_strategies)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="strategy_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of a strategy.",
    )
)

_register(
    ParameterDefinition(
        name="strategy",
        param_type=ParameterType.DICT,
        description="Complete strategy data.",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy",
    )
)

_register(
    ParameterDefinition(
        name="strategy_name",
        param_type=ParameterType.STRING,
        description="The name of the strategy.",
        default="",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_name",
    )
)

_register(
    ParameterDefinition(
        name="strategy_description",
        param_type=ParameterType.STRING,
        description="The description of the strategy.",
        default="",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_description",
    )
)

_register(
    ParameterDefinition(
        name="strategy_status",
        param_type=ParameterType.STRING,
        description="The current status of the strategy.",
        default="",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_status",
    )
)

_register(
    ParameterDefinition(
        name="strategy_type",
        param_type=ParameterType.STRING,
        description="The type of strategy (initiative, project, etc.).",
        default="",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_type",
    )
)

_register(
    ParameterDefinition(
        name="strategy_progress",
        param_type=ParameterType.FLOAT,
        description="Progress percentage of the strategy.",
        default=0.0,
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_progress",
    )
)

_register(
    ParameterDefinition(
        name="strategy_owner_name",
        param_type=ParameterType.STRING,
        description="Name of the strategy owner.",
        default="",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_owner_name",
    )
)

_register(
    ParameterDefinition(
        name="strategy_goal_id",
        param_type=ParameterType.STRING,
        description="ID of the goal this strategy supports.",
        default="",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_goal_id",
    )
)

_register(
    ParameterDefinition(
        name="strategy_alignment_score",
        param_type=ParameterType.FLOAT,
        description="AI-computed alignment score for the strategy.",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_alignment_score",
    )
)

_register(
    ParameterDefinition(
        name="strategy_alignment_explanation",
        param_type=ParameterType.STRING,
        description="AI explanation of strategy alignment.",
        default="",
        retrieval_method="get_strategy_by_id",
        extraction_path="strategy_alignment_explanation",
    )
)

# Strategy Aggregation Parameters
_register(
    ParameterDefinition(
        name="strategies",
        param_type=ParameterType.LIST,
        description="List of all strategies for the tenant.",
        default=[],
        retrieval_method="get_all_strategies",
        extraction_path="strategies",
    )
)

_register(
    ParameterDefinition(
        name="strategies_count",
        param_type=ParameterType.INTEGER,
        description="Total number of strategies.",
        default=0,
        retrieval_method="get_all_strategies",
        extraction_path="strategies_count",
    )
)

_register(
    ParameterDefinition(
        name="strategies_by_status",
        param_type=ParameterType.DICT,
        description="Strategies grouped by status.",
        default={},
        retrieval_method="get_all_strategies",
        extraction_path="strategies_by_status",
    )
)

# -----------------------------------------------------------------------------
# Measure Parameters (from get_measure_by_id or get_measures_summary)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="measure_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of a measure.",
    )
)

_register(
    ParameterDefinition(
        name="measure",
        param_type=ParameterType.DICT,
        description="Complete measure data.",
        retrieval_method="get_measure_by_id",
        extraction_path="measure",
    )
)

_register(
    ParameterDefinition(
        name="measure_name",
        param_type=ParameterType.STRING,
        description="The name of the measure.",
        default="",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_name",
    )
)

_register(
    ParameterDefinition(
        name="measure_description",
        param_type=ParameterType.STRING,
        description="The description of the measure.",
        default="",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_description",
    )
)

_register(
    ParameterDefinition(
        name="measure_unit",
        param_type=ParameterType.STRING,
        description="The unit of measurement.",
        default="",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_unit",
    )
)

_register(
    ParameterDefinition(
        name="measure_direction",
        param_type=ParameterType.STRING,
        description="Direction for improvement (up, down, maintain).",
        default="",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_direction",
    )
)

_register(
    ParameterDefinition(
        name="measure_type",
        param_type=ParameterType.STRING,
        description="Type of measure.",
        default="",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_type",
    )
)

_register(
    ParameterDefinition(
        name="measure_category",
        param_type=ParameterType.STRING,
        description="Category of the measure.",
        default="",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_category",
    )
)

_register(
    ParameterDefinition(
        name="measure_current_value",
        param_type=ParameterType.FLOAT,
        description="The current value of the measure.",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_current_value",
    )
)

_register(
    ParameterDefinition(
        name="measure_owner_name",
        param_type=ParameterType.STRING,
        description="Name of the measure owner.",
        default="",
        retrieval_method="get_measure_by_id",
        extraction_path="measure_owner_name",
    )
)

# Measures Summary Parameters (from get_measures_summary optimization endpoint)
_register(
    ParameterDefinition(
        name="measures_summary",
        param_type=ParameterType.DICT,
        description="Complete measures summary with all data.",
        default={},
        retrieval_method="get_measures_summary",
        extraction_path="measures_summary",
    )
)

_register(
    ParameterDefinition(
        name="measures",
        param_type=ParameterType.LIST,
        description="List of all measures with progress data.",
        default=[],
        retrieval_method="get_measures_summary",
        extraction_path="measures",
    )
)

_register(
    ParameterDefinition(
        name="measures_count",
        param_type=ParameterType.INTEGER,
        description="Total number of measures.",
        default=0,
        retrieval_method="get_measures_summary",
        extraction_path="measures_count",
    )
)

_register(
    ParameterDefinition(
        name="measures_health_score",
        param_type=ParameterType.FLOAT,
        description="Overall health score (0-100) for all measures.",
        default=0.0,
        retrieval_method="get_measures_summary",
        extraction_path="measures_health_score",
    )
)

_register(
    ParameterDefinition(
        name="measures_status_breakdown",
        param_type=ParameterType.DICT,
        description="Count of measures by status (on_track, at_risk, behind).",
        default={},
        retrieval_method="get_measures_summary",
        extraction_path="measures_status_breakdown",
    )
)

_register(
    ParameterDefinition(
        name="at_risk_measures",
        param_type=ParameterType.LIST,
        description="List of measures that are at risk or behind.",
        default=[],
        retrieval_method="get_measures_summary",
        extraction_path="at_risk_measures",
    )
)

# -----------------------------------------------------------------------------
# Action Parameters (from get_action_by_id)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="action_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of an action.",
    )
)

_register(
    ParameterDefinition(
        name="action",
        param_type=ParameterType.DICT,
        description="Complete action data.",
        retrieval_method="get_action_by_id",
        extraction_path="",
    )
)

_register(
    ParameterDefinition(
        name="action_title",
        param_type=ParameterType.STRING,
        description="The title of the action.",
        default="",
        retrieval_method="get_action_by_id",
        extraction_path="title",
    )
)

_register(
    ParameterDefinition(
        name="action_description",
        param_type=ParameterType.STRING,
        description="The description of the action.",
        default="",
        retrieval_method="get_action_by_id",
        extraction_path="description",
    )
)

_register(
    ParameterDefinition(
        name="action_status",
        param_type=ParameterType.STRING,
        description="The current status of the action.",
        default="",
        retrieval_method="get_action_by_id",
        extraction_path="status",
    )
)

_register(
    ParameterDefinition(
        name="action_due_date",
        param_type=ParameterType.DATETIME,
        description="The due date of the action.",
        retrieval_method="get_action_by_id",
        extraction_path="action_due_date",
    )
)

_register(
    ParameterDefinition(
        name="action_priority",
        param_type=ParameterType.STRING,
        description="The priority of the action (low, medium, high, critical).",
        default="",
        retrieval_method="get_action_by_id",
        extraction_path="action_priority",
    )
)

_register(
    ParameterDefinition(
        name="action_progress",
        param_type=ParameterType.INTEGER,
        description="Progress percentage of the action (0-100).",
        default=0,
        retrieval_method="get_action_by_id",
        extraction_path="action_progress",
    )
)

_register(
    ParameterDefinition(
        name="action_assigned_to",
        param_type=ParameterType.STRING,
        description="Name of person assigned to the action.",
        default="",
        retrieval_method="get_action_by_id",
        extraction_path="action_assigned_to",
    )
)

_register(
    ParameterDefinition(
        name="action_estimated_hours",
        param_type=ParameterType.FLOAT,
        description="Estimated hours for the action.",
        default=0.0,
        retrieval_method="get_action_by_id",
        extraction_path="action_estimated_hours",
    )
)

_register(
    ParameterDefinition(
        name="action_actual_hours",
        param_type=ParameterType.FLOAT,
        description="Actual hours spent on the action.",
        default=0.0,
        retrieval_method="get_action_by_id",
        extraction_path="action_actual_hours",
    )
)

_register(
    ParameterDefinition(
        name="action_connections",
        param_type=ParameterType.DICT,
        description="Linked goals, strategies, and issues for the action.",
        default={},
        retrieval_method="get_action_by_id",
        extraction_path="action_connections",
    )
)

# Action Aggregation Parameters
_register(
    ParameterDefinition(
        name="actions",
        param_type=ParameterType.LIST,
        description="List of all actions for the tenant.",
        default=[],
        retrieval_method="get_all_actions",
        extraction_path="actions",
    )
)

_register(
    ParameterDefinition(
        name="actions_count",
        param_type=ParameterType.INTEGER,
        description="Total number of actions.",
        default=0,
        retrieval_method="get_all_actions",
        extraction_path="actions_count",
    )
)

_register(
    ParameterDefinition(
        name="pending_actions_count",
        param_type=ParameterType.INTEGER,
        description="Number of actions not yet completed.",
        default=0,
        retrieval_method="get_all_actions",
        extraction_path="pending_actions_count",
    )
)

_register(
    ParameterDefinition(
        name="actions_by_status",
        param_type=ParameterType.DICT,
        description="Actions grouped by status.",
        default={},
        retrieval_method="get_all_actions",
        extraction_path="actions_by_status",
    )
)

# -----------------------------------------------------------------------------
# Issue Parameters (from get_issue_by_id)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="issue_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of an issue.",
    )
)

_register(
    ParameterDefinition(
        name="issue",
        param_type=ParameterType.DICT,
        description="Complete issue data.",
        retrieval_method="get_issue_by_id",
        extraction_path="",
    )
)

_register(
    ParameterDefinition(
        name="issue_title",
        param_type=ParameterType.STRING,
        description="The title of the issue.",
        default="",
        retrieval_method="get_issue_by_id",
        extraction_path="title",
    )
)

_register(
    ParameterDefinition(
        name="issue_description",
        param_type=ParameterType.STRING,
        description="The description of the issue.",
        default="",
        retrieval_method="get_issue_by_id",
        extraction_path="description",
    )
)

_register(
    ParameterDefinition(
        name="issue_priority",
        param_type=ParameterType.STRING,
        description="The priority of the issue.",
        default="",
        retrieval_method="get_issue_by_id",
        extraction_path="priority",
    )
)

_register(
    ParameterDefinition(
        name="issue_status",
        param_type=ParameterType.STRING,
        description="The current status of the issue.",
        default="",
        retrieval_method="get_issue_by_id",
        extraction_path="status",
    )
)

_register(
    ParameterDefinition(
        name="issue_impact",
        param_type=ParameterType.STRING,
        description="The business impact of the issue.",
        default="",
        retrieval_method="get_issue_by_id",
        extraction_path="issue_impact",
    )
)

_register(
    ParameterDefinition(
        name="issue_assigned_to",
        param_type=ParameterType.STRING,
        description="Name of person assigned to the issue.",
        default="",
        retrieval_method="get_issue_by_id",
        extraction_path="issue_assigned_to",
    )
)

_register(
    ParameterDefinition(
        name="issue_reporter",
        param_type=ParameterType.STRING,
        description="Name of person who reported the issue.",
        default="",
        retrieval_method="get_issue_by_id",
        extraction_path="issue_reporter",
    )
)

_register(
    ParameterDefinition(
        name="issue_tags",
        param_type=ParameterType.LIST,
        description="Tags associated with the issue.",
        default=[],
        retrieval_method="get_issue_by_id",
        extraction_path="issue_tags",
    )
)

_register(
    ParameterDefinition(
        name="issue_connections",
        param_type=ParameterType.DICT,
        description="Linked goals, strategies, and actions for the issue.",
        default={},
        retrieval_method="get_issue_by_id",
        extraction_path="issue_connections",
    )
)

# Issue Aggregation Parameters
_register(
    ParameterDefinition(
        name="issues",
        param_type=ParameterType.LIST,
        description="List of all issues for the tenant.",
        default=[],
        retrieval_method="get_all_issues",
        extraction_path="issues",
    )
)

_register(
    ParameterDefinition(
        name="issues_count",
        param_type=ParameterType.INTEGER,
        description="Total number of issues.",
        default=0,
        retrieval_method="get_all_issues",
        extraction_path="issues_count",
    )
)

_register(
    ParameterDefinition(
        name="critical_issues_count",
        param_type=ParameterType.INTEGER,
        description="Number of critical priority issues.",
        default=0,
        retrieval_method="get_all_issues",
        extraction_path="critical_issues_count",
    )
)

# -----------------------------------------------------------------------------
# People Parameters (from get_people or get_person_by_id)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="person_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of a person.",
    )
)

_register(
    ParameterDefinition(
        name="person",
        param_type=ParameterType.DICT,
        description="Complete person data.",
        retrieval_method="get_person_by_id",
        extraction_path="person",
    )
)

_register(
    ParameterDefinition(
        name="person_name",
        param_type=ParameterType.STRING,
        description="The name of the person.",
        default="",
        retrieval_method="get_person_by_id",
        extraction_path="person_name",
    )
)

_register(
    ParameterDefinition(
        name="person_email",
        param_type=ParameterType.STRING,
        description="The email of the person.",
        default="",
        retrieval_method="get_person_by_id",
        extraction_path="person_email",
    )
)

_register(
    ParameterDefinition(
        name="person_role",
        param_type=ParameterType.STRING,
        description="The role of the person.",
        default="",
        retrieval_method="get_person_by_id",
        extraction_path="person_role",
    )
)

_register(
    ParameterDefinition(
        name="person_department",
        param_type=ParameterType.STRING,
        description="The department of the person.",
        default="",
        retrieval_method="get_person_by_id",
        extraction_path="person_department",
    )
)

_register(
    ParameterDefinition(
        name="person_position",
        param_type=ParameterType.STRING,
        description="The position of the person.",
        default="",
        retrieval_method="get_person_by_id",
        extraction_path="person_position",
    )
)

# People Aggregation Parameters
_register(
    ParameterDefinition(
        name="people",
        param_type=ParameterType.LIST,
        description="List of all people in the organization.",
        default=[],
        retrieval_method="get_people",
        extraction_path="people",
    )
)

_register(
    ParameterDefinition(
        name="people_count",
        param_type=ParameterType.INTEGER,
        description="Total number of people.",
        default=0,
        retrieval_method="get_people",
        extraction_path="people_count",
    )
)

_register(
    ParameterDefinition(
        name="people_by_department",
        param_type=ParameterType.DICT,
        description="People grouped by department.",
        default={},
        retrieval_method="get_people",
        extraction_path="people_by_department",
    )
)

# -----------------------------------------------------------------------------
# Department Parameters (from get_departments)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="departments",
        param_type=ParameterType.LIST,
        description="List of all departments.",
        default=[],
        retrieval_method="get_departments",
        extraction_path="departments",
    )
)

_register(
    ParameterDefinition(
        name="departments_count",
        param_type=ParameterType.INTEGER,
        description="Total number of departments.",
        default=0,
        retrieval_method="get_departments",
        extraction_path="departments_count",
    )
)

# -----------------------------------------------------------------------------
# Position Parameters (from get_positions)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="positions",
        param_type=ParameterType.LIST,
        description="List of all positions.",
        default=[],
        retrieval_method="get_positions",
        extraction_path="positions",
    )
)

_register(
    ParameterDefinition(
        name="positions_count",
        param_type=ParameterType.INTEGER,
        description="Total number of positions.",
        default=0,
        retrieval_method="get_positions",
        extraction_path="positions_count",
    )
)

# Position Detail Parameters (from get_position_by_id)
_register(
    ParameterDefinition(
        name="position_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of a position.",
    )
)

_register(
    ParameterDefinition(
        name="position",
        param_type=ParameterType.DICT,
        description="Complete position data.",
        retrieval_method="get_position_by_id",
        extraction_path="position",
    )
)

_register(
    ParameterDefinition(
        name="position_name",
        param_type=ParameterType.STRING,
        description="The name of the position.",
        default="",
        retrieval_method="get_position_by_id",
        extraction_path="position_name",
    )
)

_register(
    ParameterDefinition(
        name="position_role_id",
        param_type=ParameterType.STRING,
        description="The role ID associated with the position.",
        default="",
        retrieval_method="get_position_by_id",
        extraction_path="position_role_id",
    )
)

_register(
    ParameterDefinition(
        name="position_role_name",
        param_type=ParameterType.STRING,
        description="The role name associated with the position.",
        default="",
        retrieval_method="get_position_by_id",
        extraction_path="position_role_name",
    )
)

_register(
    ParameterDefinition(
        name="position_organization_unit_id",
        param_type=ParameterType.STRING,
        description="The organization unit ID for the position.",
        default="",
        retrieval_method="get_position_by_id",
        extraction_path="position_organization_unit_id",
    )
)

_register(
    ParameterDefinition(
        name="position_person_id",
        param_type=ParameterType.STRING,
        description="The person ID assigned to the position.",
        default="",
        retrieval_method="get_position_by_id",
        extraction_path="position_person_id",
    )
)

# -----------------------------------------------------------------------------
# Role Parameters (from get_roles or get_role_by_id)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="role_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of a role.",
    )
)

_register(
    ParameterDefinition(
        name="roles",
        param_type=ParameterType.LIST,
        description="List of all roles.",
        default=[],
        retrieval_method="get_roles",
        extraction_path="roles",
    )
)

_register(
    ParameterDefinition(
        name="roles_count",
        param_type=ParameterType.INTEGER,
        description="Total number of roles.",
        default=0,
        retrieval_method="get_roles",
        extraction_path="roles_count",
    )
)

# -----------------------------------------------------------------------------
# Measure Catalog Parameters (from get_measure_catalog)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="measure_catalog",
        param_type=ParameterType.DICT,
        description="Complete measure catalog data (catalogMeasures and tenantCustomMeasures).",
        default={},
        retrieval_method="get_measure_catalog",
        extraction_path="measure_catalog",
    )
)

_register(
    ParameterDefinition(
        name="catalog_measures",
        param_type=ParameterType.LIST,
        description="List of available catalog measures from the measure library.",
        default=[],
        retrieval_method="get_measure_catalog",
        extraction_path="catalog_measures",
    )
)

_register(
    ParameterDefinition(
        name="tenant_custom_measures",
        param_type=ParameterType.LIST,
        description="List of tenant custom measures.",
        default=[],
        retrieval_method="get_measure_catalog",
        extraction_path="tenant_custom_measures",
    )
)

# -----------------------------------------------------------------------------
# Conversation Context Parameters (from get_conversation_context)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="conversation_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of the conversation.",
    )
)

# NOTE: Conversation context parameters (conversation_history, conversation_summary,
# previous_response) are NOT template parameters. They are handled differently:
# - conversation_history: Passed as messages to the LLM (not in system prompt)
# - conversation_summary: LLM generates this from history when needed (resume prompts)
# - previous_response: Available in message history
# These are passed via the LLM service's conversation_history parameter, not template rendering.

# -----------------------------------------------------------------------------
# User Input Parameters (typically provided directly in request)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="user_message",
        param_type=ParameterType.STRING,
        description="The user's current message or input.",
    )
)

_register(
    ParameterDefinition(
        name="user_input",
        param_type=ParameterType.STRING,
        description="Generic user input for analysis or processing.",
    )
)

_register(
    ParameterDefinition(
        name="topic",
        param_type=ParameterType.STRING,
        description="The current topic of discussion.",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="content_type",
        param_type=ParameterType.STRING,
        description="The type of content being processed.",
        default="",
    )
)

# -----------------------------------------------------------------------------
# Analysis Parameters
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="analysis_type",
        param_type=ParameterType.STRING,
        description="The type of analysis to perform.",
        default="general",
    )
)

_register(
    ParameterDefinition(
        name="context",
        param_type=ParameterType.DICT,
        description="Additional context for analysis or generation.",
        default={},
    )
)

_register(
    ParameterDefinition(
        name="constraints",
        param_type=ParameterType.LIST,
        description="Constraints or requirements for the output.",
        default=[],
    )
)

_register(
    ParameterDefinition(
        name="preferences",
        param_type=ParameterType.DICT,
        description="User preferences for output formatting or content.",
        default={},
    )
)

# -----------------------------------------------------------------------------
# Content Generation Parameters
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="content_title",
        param_type=ParameterType.STRING,
        description="Title for generated content.",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="content_description",
        param_type=ParameterType.STRING,
        description="Description or prompt for content generation.",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="target_length",
        param_type=ParameterType.INTEGER,
        description="Target length for generated content.",
        default=500,
    )
)

_register(
    ParameterDefinition(
        name="output_format",
        param_type=ParameterType.STRING,
        description="Desired format for output (e.g., markdown, json, text).",
        default="text",
    )
)

_register(
    ParameterDefinition(
        name="tone",
        param_type=ParameterType.STRING,
        description="Desired tone for generated content.",
        default="professional",
    )
)

_register(
    ParameterDefinition(
        name="style",
        param_type=ParameterType.STRING,
        description="Desired style for generated content.",
        default="",
    )
)

# -----------------------------------------------------------------------------
# Coaching-Specific Parameters
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="coaching_phase",
        param_type=ParameterType.STRING,
        description="Current phase of the coaching conversation.",
        default="discovery",
    )
)

_register(
    ParameterDefinition(
        name="coaching_topic",
        param_type=ParameterType.STRING,
        description="The specific coaching topic being discussed.",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="focus_area",
        param_type=ParameterType.STRING,
        description="The current focus area for coaching.",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="insights",
        param_type=ParameterType.LIST,
        description="Previous insights gathered during coaching.",
        default=[],
    )
)

_register(
    ParameterDefinition(
        name="recommendations",
        param_type=ParameterType.LIST,
        description="Previous recommendations made during coaching.",
        default=[],
    )
)

# -----------------------------------------------------------------------------
# Website Content Parameters
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="url",
        param_type=ParameterType.STRING,
        description="URL for website analysis or content retrieval.",
    )
)

_register(
    ParameterDefinition(
        name="scan_depth",
        param_type=ParameterType.STRING,
        description="Scan depth: basic, standard, or comprehensive.",
        default="standard",
    )
)

_register(
    ParameterDefinition(
        name="page_type",
        param_type=ParameterType.STRING,
        description="Type of website page (e.g., home, about, services).",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="section_type",
        param_type=ParameterType.STRING,
        description="Type of page section (e.g., hero, features, testimonials).",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="seo_keywords",
        param_type=ParameterType.LIST,
        description="SEO keywords to incorporate.",
        default=[],
    )
)

_register(
    ParameterDefinition(
        name="call_to_action",
        param_type=ParameterType.STRING,
        description="Desired call to action for the content.",
        default="",
    )
)

# -----------------------------------------------------------------------------
# Onboarding Review Parameters (from get_onboarding_data)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="current_value",
        param_type=ParameterType.STRING,
        description="The current draft value being reviewed (niche, ICA, or value proposition).",
        default="",
    )
)

_register(
    ParameterDefinition(
        name="onboarding_niche",
        param_type=ParameterType.STRING,
        description="The business niche from onboarding data.",
        default="",
        retrieval_method="get_onboarding_data",
        extraction_path="onboarding_niche",
    )
)

_register(
    ParameterDefinition(
        name="onboarding_ica",
        param_type=ParameterType.STRING,
        description="The Ideal Client Avatar (ICA) from onboarding data.",
        default="",
        retrieval_method="get_onboarding_data",
        extraction_path="onboarding_ica",
    )
)

_register(
    ParameterDefinition(
        name="onboarding_value_proposition",
        param_type=ParameterType.STRING,
        description="The value proposition from onboarding data.",
        default="",
        retrieval_method="get_onboarding_data",
        extraction_path="onboarding_value_proposition",
    )
)

_register(
    ParameterDefinition(
        name="onboarding_products",
        param_type=ParameterType.LIST,
        description="List of products/services with name and problem solved.",
        default=[],
        retrieval_method="get_onboarding_data",
        extraction_path="onboarding_products",
    )
)

_register(
    ParameterDefinition(
        name="onboarding_business_name",
        param_type=ParameterType.STRING,
        description="The business name from onboarding data.",
        default="",
        retrieval_method="get_onboarding_data",
        extraction_path="onboarding_business_name",
    )
)

# -----------------------------------------------------------------------------
# Website Content Parameters (from get_website_content)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="website_content",
        param_type=ParameterType.STRING,
        description="Extracted text content from a website.",
        default="",
        retrieval_method="get_website_content",
        extraction_path="website_content",
    )
)

_register(
    ParameterDefinition(
        name="website_title",
        param_type=ParameterType.STRING,
        description="Page title from website.",
        default="",
        retrieval_method="get_website_content",
        extraction_path="website_title",
    )
)

_register(
    ParameterDefinition(
        name="meta_description",
        param_type=ParameterType.STRING,
        description="Meta description from website.",
        default="",
        retrieval_method="get_website_content",
        extraction_path="meta_description",
    )
)

# -----------------------------------------------------------------------------
# Formatting and Metadata Parameters
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="language",
        param_type=ParameterType.STRING,
        description="Language for content generation.",
        default="en",
    )
)

_register(
    ParameterDefinition(
        name="locale",
        param_type=ParameterType.STRING,
        description="Locale for formatting and localization.",
        default="en-US",
    )
)

_register(
    ParameterDefinition(
        name="timestamp",
        param_type=ParameterType.DATETIME,
        description="Timestamp for the current operation.",
    )
)

_register(
    ParameterDefinition(
        name="request_id",
        param_type=ParameterType.STRING,
        description="Unique identifier for the current request.",
    )
)


# =============================================================================
# Helper Functions
# =============================================================================


def get_parameter_definition(name: str) -> ParameterDefinition | None:
    """
    Get a parameter definition by name.

    Args:
        name: The name of the parameter.

    Returns:
        The ParameterDefinition if found, None otherwise.
    """
    return PARAMETER_REGISTRY.get(name)


def get_parameters_by_retrieval_method(method: str) -> list[ParameterDefinition]:
    """
    Get all parameters that use a specific retrieval method.

    Args:
        method: The name of the retrieval method.

    Returns:
        List of ParameterDefinitions that use this retrieval method.
    """
    return [param for param in PARAMETER_REGISTRY.values() if param.retrieval_method == method]


def get_enrichable_parameters() -> list[ParameterDefinition]:
    """
    Get all parameters that can be enriched via retrieval methods.

    Returns:
        List of ParameterDefinitions that have a retrieval_method defined.
    """
    return [param for param in PARAMETER_REGISTRY.values() if param.retrieval_method is not None]


def get_all_parameter_names() -> list[str]:
    """
    Get a list of all registered parameter names.

    Returns:
        List of all parameter names in the registry.
    """
    return list(PARAMETER_REGISTRY.keys())


def validate_parameter_name(name: str) -> bool:
    """
    Check if a parameter name is registered.

    Args:
        name: The name to validate.

    Returns:
        True if the parameter exists in the registry.
    """
    return name in PARAMETER_REGISTRY
