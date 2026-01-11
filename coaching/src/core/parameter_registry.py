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
# KPI Parameters (from get_kpi_by_id or get_kpis_list)
# -----------------------------------------------------------------------------
_register(
    ParameterDefinition(
        name="kpi_id",
        param_type=ParameterType.STRING,
        description="The unique identifier of a KPI.",
    )
)

_register(
    ParameterDefinition(
        name="kpi",
        param_type=ParameterType.DICT,
        description="Complete KPI data.",
        retrieval_method="get_kpi_by_id",
        extraction_path="",
    )
)

_register(
    ParameterDefinition(
        name="kpi_name",
        param_type=ParameterType.STRING,
        description="The name of the KPI.",
        default="",
        retrieval_method="get_kpi_by_id",
        extraction_path="name",
    )
)

_register(
    ParameterDefinition(
        name="kpi_value",
        param_type=ParameterType.FLOAT,
        description="The current value of the KPI.",
        default=0.0,
        retrieval_method="get_kpi_by_id",
        extraction_path="value",
    )
)

_register(
    ParameterDefinition(
        name="kpi_target",
        param_type=ParameterType.FLOAT,
        description="The target value of the KPI.",
        default=0.0,
        retrieval_method="get_kpi_by_id",
        extraction_path="target",
    )
)

_register(
    ParameterDefinition(
        name="kpi_unit",
        param_type=ParameterType.STRING,
        description="The unit of measurement for the KPI.",
        default="",
        retrieval_method="get_kpi_by_id",
        extraction_path="unit",
    )
)

_register(
    ParameterDefinition(
        name="kpis_list",
        param_type=ParameterType.LIST,
        description="List of all KPIs for the user.",
        default=[],
        retrieval_method="get_kpis_list",
        extraction_path="",
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
        extraction_path="due_date",
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
