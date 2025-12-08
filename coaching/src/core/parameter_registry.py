"""Parameter Registry - Centralized parameter definitions for prompt templates.

This module defines all parameters that can be used in prompt templates,
organized by their data source for efficient batch retrieval.

Usage:
    from coaching.src.core.parameter_registry import (
        PARAMETER_REGISTRY,
        get_parameters_by_source,
        get_parameter,
    )

    # Get all parameters from a source
    onboarding_params = get_parameters_by_source(ParameterSource.ONBOARDING)

    # Get a specific parameter definition
    param = get_parameter("business_foundation")
"""

from dataclasses import dataclass
from typing import Any

from coaching.src.core.constants import ParameterSource, ParameterType


@dataclass(frozen=True)
class ParameterDefinition:
    """Definition of a parameter for prompt templates.

    Attributes:
        name: Parameter name used in templates (e.g., {parameter_name})
        source: Data source for this parameter
        source_path: JSON path to extract value from source response
        param_type: Data type of the parameter
        required: Whether the parameter is required
        description: Human-readable description
        default: Default value if not provided (only for optional params)
    """

    name: str
    source: ParameterSource
    source_path: str
    param_type: ParameterType
    required: bool = True
    description: str = ""
    default: Any = None


# =============================================================================
# PARAMETER REGISTRY
# =============================================================================
# All 61 parameters organized by source for efficient batch retrieval

PARAMETER_REGISTRY: dict[str, ParameterDefinition] = {
    # =========================================================================
    # REQUEST PARAMETERS (from API request body)
    # =========================================================================
    "url": ParameterDefinition(
        name="url",
        source=ParameterSource.REQUEST,
        source_path="url",
        param_type=ParameterType.STRING,
        required=True,
        description="Website URL to scan",
    ),
    "scan_depth": ParameterDefinition(
        name="scan_depth",
        source=ParameterSource.REQUEST,
        source_path="scan_depth",
        param_type=ParameterType.STRING,
        required=False,
        description="Scan depth: basic, standard, or comprehensive",
        default="standard",
    ),
    "topic": ParameterDefinition(
        name="topic",
        source=ParameterSource.REQUEST,
        source_path="topic",
        param_type=ParameterType.STRING,
        required=True,
        description="Conversation topic",
    ),
    "stage": ParameterDefinition(
        name="stage",
        source=ParameterSource.REQUEST,
        source_path="stage",
        param_type=ParameterType.STRING,
        required=True,
        description="Onboarding stage",
    ),
    "metrics_type": ParameterDefinition(
        name="metrics_type",
        source=ParameterSource.REQUEST,
        source_path="metrics_type",
        param_type=ParameterType.STRING,
        required=False,
        description="Types of metrics to retrieve",
        default="all",
    ),
    "data_sources": ParameterDefinition(
        name="data_sources",
        source=ParameterSource.REQUEST,
        source_path="data_sources",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Sources of data for insights generation",
    ),
    "insight_types": ParameterDefinition(
        name="insight_types",
        source=ParameterSource.REQUEST,
        source_path="insight_types",
        param_type=ParameterType.ARRAY,
        required=False,
        description="Types of insights to generate",
    ),
    "time_range": ParameterDefinition(
        name="time_range",
        source=ParameterSource.REQUEST,
        source_path="time_range",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Time range for analysis",
    ),
    "market_context": ParameterDefinition(
        name="market_context",
        source=ParameterSource.REQUEST,
        source_path="market_context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Market context information",
    ),
    "website_data": ParameterDefinition(
        name="website_data",
        source=ParameterSource.REQUEST,
        source_path="website_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Scanned website data",
    ),
    "depth": ParameterDefinition(
        name="depth",
        source=ParameterSource.REQUEST,
        source_path="depth",
        param_type=ParameterType.INTEGER,
        required=False,
        description="Analysis depth level",
        default=5,
    ),
    "constraints": ParameterDefinition(
        name="constraints",
        source=ParameterSource.REQUEST,
        source_path="constraints",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Resource or operational constraints",
    ),
    "current_plan": ParameterDefinition(
        name="current_plan",
        source=ParameterSource.REQUEST,
        source_path="current_plan",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Current action plan to optimize",
    ),
    "optimization_goals": ParameterDefinition(
        name="optimization_goals",
        source=ParameterSource.REQUEST,
        source_path="optimization_goals",
        param_type=ParameterType.ARRAY,
        required=False,
        description="Goals for optimization",
    ),
    "tasks": ParameterDefinition(
        name="tasks",
        source=ParameterSource.REQUEST,
        source_path="tasks",
        param_type=ParameterType.ARRAY,
        required=True,
        description="List of tasks to prioritize or schedule",
    ),
    "criteria": ParameterDefinition(
        name="criteria",
        source=ParameterSource.REQUEST,
        source_path="criteria",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Prioritization criteria",
    ),
    "resources": ParameterDefinition(
        name="resources",
        source=ParameterSource.REQUEST,
        source_path="resources",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Available resources",
    ),
    "subject": ParameterDefinition(
        name="subject",
        source=ParameterSource.REQUEST,
        source_path="subject",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Subject for SWOT analysis",
    ),
    "user_message": ParameterDefinition(
        name="user_message",
        source=ParameterSource.REQUEST,
        source_path="user_message",
        param_type=ParameterType.STRING,
        required=True,
        description="User's input message",
    ),
    "include_summary": ParameterDefinition(
        name="include_summary",
        source=ParameterSource.REQUEST,
        source_path="include_summary",
        param_type=ParameterType.BOOLEAN,
        required=False,
        description="Whether to include conversation summary",
        default=True,
    ),
    "context_type": ParameterDefinition(
        name="context_type",
        source=ParameterSource.REQUEST,
        source_path="context_type",
        param_type=ParameterType.STRING,
        required=False,
        description="Type of strategic context to retrieve",
        default="full",
    ),
    "action_data": ParameterDefinition(
        name="action_data",
        source=ParameterSource.REQUEST,
        source_path="action_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Data for creating an action",
    ),
    "completion_data": ParameterDefinition(
        name="completion_data",
        source=ParameterSource.REQUEST,
        source_path="completion_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Action completion data",
    ),
    "closure_data": ParameterDefinition(
        name="closure_data",
        source=ParameterSource.REQUEST,
        source_path="closure_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Issue closure data",
    ),
    "update_data": ParameterDefinition(
        name="update_data",
        source=ParameterSource.REQUEST,
        source_path="update_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="KPI update data",
    ),
    "update_value": ParameterDefinition(
        name="update_value",
        source=ParameterSource.REQUEST,
        source_path="update_value",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Value for KPI update",
    ),
    "kpi_updates": ParameterDefinition(
        name="kpi_updates",
        source=ParameterSource.REQUEST,
        source_path="kpi_updates",
        param_type=ParameterType.ARRAY,
        required=True,
        description="KPI updates to sync",
    ),
    "connections": ParameterDefinition(
        name="connections",
        source=ParameterSource.REQUEST,
        source_path="connections",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Strategic connections to update",
    ),
    "conflict_id": ParameterDefinition(
        name="conflict_id",
        source=ParameterSource.REQUEST,
        source_path="conflict_id",
        param_type=ParameterType.STRING,
        required=True,
        description="KPI conflict identifier",
    ),
    "conflict_details": ParameterDefinition(
        name="conflict_details",
        source=ParameterSource.REQUEST,
        source_path="conflict_details",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Details of KPI conflict",
    ),
    "analysis_type": ParameterDefinition(
        name="analysis_type",
        source=ParameterSource.REQUEST,
        source_path="analysis_type",
        param_type=ParameterType.STRING,
        required=True,
        description="Type of analysis to perform",
    ),
    "operations_data": ParameterDefinition(
        name="operations_data",
        source=ParameterSource.REQUEST,
        source_path="operations_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Operations data for analysis",
    ),
    "performance_data": ParameterDefinition(
        name="performance_data",
        source=ParameterSource.REQUEST,
        source_path="performance_data",
        param_type=ParameterType.OBJECT,
        required=False,
        description="KPI performance data",
    ),
    # =========================================================================
    # ONBOARDING PARAMETERS (from Account Service)
    # =========================================================================
    "business_foundation": ParameterDefinition(
        name="business_foundation",
        source=ParameterSource.ONBOARDING,
        source_path="business_foundation",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Complete business foundation object",
    ),
    "niche": ParameterDefinition(
        name="niche",
        source=ParameterSource.ONBOARDING,
        source_path="business_foundation.niche",
        param_type=ParameterType.STRING,
        required=False,
        description="Business niche/market segment",
    ),
    "ica": ParameterDefinition(
        name="ica",
        source=ParameterSource.ONBOARDING,
        source_path="business_foundation.ica",
        param_type=ParameterType.STRING,
        required=False,
        description="Ideal Customer Avatar",
    ),
    "value_proposition": ParameterDefinition(
        name="value_proposition",
        source=ParameterSource.ONBOARDING,
        source_path="business_foundation.value_proposition",
        param_type=ParameterType.STRING,
        required=False,
        description="Business value proposition",
    ),
    "core_values": ParameterDefinition(
        name="core_values",
        source=ParameterSource.ONBOARDING,
        source_path="business_foundation.core_values",
        param_type=ParameterType.ARRAY,
        required=False,
        description="List of core values",
    ),
    "purpose": ParameterDefinition(
        name="purpose",
        source=ParameterSource.ONBOARDING,
        source_path="business_foundation.purpose",
        param_type=ParameterType.STRING,
        required=False,
        description="Business purpose statement",
    ),
    "vision": ParameterDefinition(
        name="vision",
        source=ParameterSource.ONBOARDING,
        source_path="business_foundation.vision",
        param_type=ParameterType.STRING,
        required=False,
        description="Business vision statement",
    ),
    "business_context": ParameterDefinition(
        name="business_context",
        source=ParameterSource.ONBOARDING,
        source_path="business_context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Additional business context from onboarding",
    ),
    "current_strategy": ParameterDefinition(
        name="current_strategy",
        source=ParameterSource.ONBOARDING,
        source_path="current_strategy",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Current business strategy",
    ),
    "strategic_context": ParameterDefinition(
        name="strategic_context",
        source=ParameterSource.ONBOARDING,
        source_path="strategic_context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Full strategic planning context",
    ),
    "strategy": ParameterDefinition(
        name="strategy",
        source=ParameterSource.ONBOARDING,
        source_path="strategy",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Business strategy for analysis",
    ),
    "operations": ParameterDefinition(
        name="operations",
        source=ParameterSource.ONBOARDING,
        source_path="operations",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Operations data for alignment analysis",
    ),
    # =========================================================================
    # GOAL PARAMETERS (single goal from Traction Service)
    # =========================================================================
    "goal": ParameterDefinition(
        name="goal",
        source=ParameterSource.GOAL,
        source_path="",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Single goal object",
    ),
    # =========================================================================
    # GOALS PARAMETERS (all goals from Traction Service)
    # =========================================================================
    "goals": ParameterDefinition(
        name="goals",
        source=ParameterSource.GOALS,
        source_path="",
        param_type=ParameterType.ARRAY,
        required=True,
        description="List of all goals",
    ),
    "existing_kpis": ParameterDefinition(
        name="existing_kpis",
        source=ParameterSource.KPIS,
        source_path="",
        param_type=ParameterType.ARRAY,
        required=False,
        description="List of existing KPIs",
    ),
    # =========================================================================
    # KPI PARAMETERS (single KPI from Traction Service)
    # =========================================================================
    "kpi_id": ParameterDefinition(
        name="kpi_id",
        source=ParameterSource.KPI,
        source_path="id",
        param_type=ParameterType.STRING,
        required=True,
        description="KPI identifier",
    ),
    # =========================================================================
    # KPIS PARAMETERS (all KPIs from Traction Service)
    # =========================================================================
    "kpis": ParameterDefinition(
        name="kpis",
        source=ParameterSource.KPIS,
        source_path="",
        param_type=ParameterType.ARRAY,
        required=True,
        description="List of all KPIs",
    ),
    "related_kpis": ParameterDefinition(
        name="related_kpis",
        source=ParameterSource.KPIS,
        source_path="",
        param_type=ParameterType.ARRAY,
        required=True,
        description="KPIs related to an action",
    ),
    "operational_kpis": ParameterDefinition(
        name="operational_kpis",
        source=ParameterSource.KPIS,
        source_path="",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Operational KPIs for conflict detection",
    ),
    "strategic_kpis": ParameterDefinition(
        name="strategic_kpis",
        source=ParameterSource.KPIS,
        source_path="",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Strategic KPIs for sync/conflict detection",
    ),
    # =========================================================================
    # ACTION PARAMETERS (from Traction Service)
    # =========================================================================
    "action": ParameterDefinition(
        name="action",
        source=ParameterSource.ACTION,
        source_path="",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Action item object",
    ),
    "action_id": ParameterDefinition(
        name="action_id",
        source=ParameterSource.ACTION,
        source_path="id",
        param_type=ParameterType.STRING,
        required=True,
        description="Action identifier",
    ),
    "action_details": ParameterDefinition(
        name="action_details",
        source=ParameterSource.ACTION,
        source_path="",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Detailed action information",
    ),
    # =========================================================================
    # ISSUE PARAMETERS (from Traction Service)
    # =========================================================================
    "issue": ParameterDefinition(
        name="issue",
        source=ParameterSource.ISSUE,
        source_path="",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Issue object",
    ),
    "issue_id": ParameterDefinition(
        name="issue_id",
        source=ParameterSource.ISSUE,
        source_path="id",
        param_type=ParameterType.STRING,
        required=True,
        description="Issue identifier",
    ),
    "issue_details": ParameterDefinition(
        name="issue_details",
        source=ParameterSource.ISSUE,
        source_path="",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Detailed issue information",
    ),
    "issue_status": ParameterDefinition(
        name="issue_status",
        source=ParameterSource.ISSUE,
        source_path="status",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Issue status information",
    ),
    "root_causes": ParameterDefinition(
        name="root_causes",
        source=ParameterSource.ISSUE,
        source_path="root_causes",
        param_type=ParameterType.ARRAY,
        required=False,
        description="Identified root causes for an issue",
    ),
    # =========================================================================
    # CONVERSATION PARAMETERS (from current conversation context)
    # =========================================================================
    "conversation_id": ParameterDefinition(
        name="conversation_id",
        source=ParameterSource.CONVERSATION,
        source_path="id",
        param_type=ParameterType.STRING,
        required=True,
        description="Conversation identifier",
    ),
    "conversation_history": ParameterDefinition(
        name="conversation_history",
        source=ParameterSource.CONVERSATION,
        source_path="messages",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Conversation message history",
    ),
    "context": ParameterDefinition(
        name="context",
        source=ParameterSource.CONVERSATION,
        source_path="context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Current conversation context",
    ),
    # =========================================================================
    # COMPUTED PARAMETERS (derived from other data)
    # =========================================================================
    "alignment_score": ParameterDefinition(
        name="alignment_score",
        source=ParameterSource.COMPUTED,
        source_path="",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Calculated alignment score",
    ),
    "tenant_id": ParameterDefinition(
        name="tenant_id",
        source=ParameterSource.COMPUTED,
        source_path="",
        param_type=ParameterType.STRING,
        required=True,
        description="Tenant identifier (from auth context)",
    ),
    "user_id": ParameterDefinition(
        name="user_id",
        source=ParameterSource.COMPUTED,
        source_path="",
        param_type=ParameterType.STRING,
        required=True,
        description="User identifier (from auth context)",
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_parameter(name: str) -> ParameterDefinition | None:
    """Get a parameter definition by name.

    Args:
        name: Parameter name

    Returns:
        ParameterDefinition if found, None otherwise
    """
    return PARAMETER_REGISTRY.get(name)


def get_parameters_by_source(source: ParameterSource) -> list[ParameterDefinition]:
    """Get all parameters from a specific source.

    This enables efficient batch retrieval - one API call per source.

    Args:
        source: Parameter source (ONBOARDING, GOAL, etc.)

    Returns:
        List of ParameterDefinition objects for that source
    """
    return [param for param in PARAMETER_REGISTRY.values() if param.source == source]


def get_required_parameters() -> list[ParameterDefinition]:
    """Get all required parameters.

    Returns:
        List of required ParameterDefinition objects
    """
    return [param for param in PARAMETER_REGISTRY.values() if param.required]


def get_parameters_for_template(
    parameter_names: list[str],
) -> dict[ParameterSource, list[ParameterDefinition]]:
    """Get parameters grouped by source for a template.

    This is the primary method for efficient parameter retrieval.
    Returns parameters grouped by source so the caller can make
    one API call per source group.

    Args:
        parameter_names: List of parameter names used in template

    Returns:
        Dict mapping source to list of parameters from that source

    Example:
        >>> params = get_parameters_for_template(["goal", "business_foundation", "niche"])
        >>> # Returns: {
        >>> #   ParameterSource.GOAL: [goal_param],
        >>> #   ParameterSource.ONBOARDING: [business_foundation_param, niche_param]
        >>> # }
    """
    result: dict[ParameterSource, list[ParameterDefinition]] = {}

    for name in parameter_names:
        param = PARAMETER_REGISTRY.get(name)
        if param:
            if param.source not in result:
                result[param.source] = []
            result[param.source].append(param)

    return result


def list_all_parameters() -> list[ParameterDefinition]:
    """Get all parameter definitions.

    Returns:
        List of all ParameterDefinition objects
    """
    return list(PARAMETER_REGISTRY.values())


def get_parameter_names_by_source(source: ParameterSource) -> list[str]:
    """Get parameter names for a specific source.

    Args:
        source: Parameter source

    Returns:
        List of parameter names
    """
    return [param.name for param in get_parameters_by_source(source)]


__all__ = [
    "PARAMETER_REGISTRY",
    "ParameterDefinition",
    "get_parameter",
    "get_parameter_names_by_source",
    "get_parameters_by_source",
    "get_parameters_for_template",
    "get_required_parameters",
    "list_all_parameters",
]
