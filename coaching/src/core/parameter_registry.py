"""Parameter Registry - Centralized parameter definitions for prompt templates.

This module defines all parameters that can be used in prompt templates.
Parameter source information is defined per-endpoint in endpoint_registry.py
since the same parameter may come from different sources in different contexts.

Usage:
    from coaching.src.core.parameter_registry import (
        PARAMETER_REGISTRY,
        get_parameter,
        list_all_parameters,
    )

    # Get a specific parameter definition
    param = get_parameter("business_foundation")
"""

from dataclasses import dataclass
from typing import Any

from coaching.src.core.constants import ParameterType


@dataclass(frozen=True)
class ParameterDefinition:
    """Definition of a parameter for prompt templates.

    Note: Source information is defined per-endpoint in endpoint_registry.py,
    not here, because the same parameter may come from different sources
    depending on the endpoint context.

    Attributes:
        name: Parameter name used in templates (e.g., {parameter_name})
        param_type: Data type of the parameter
        required: Whether the parameter is required by default
        description: Human-readable description
        default: Default value if not provided (only for optional params)
    """

    name: str
    param_type: ParameterType
    required: bool = True
    description: str = ""
    default: Any = None


# =============================================================================
# PARAMETER REGISTRY
# =============================================================================
# Parameter definitions - source is specified per-endpoint in endpoint_registry.py

PARAMETER_REGISTRY: dict[str, ParameterDefinition] = {
    # =========================================================================
    # REQUEST/INPUT PARAMETERS
    # =========================================================================
    "url": ParameterDefinition(
        name="url",
        param_type=ParameterType.STRING,
        required=True,
        description="Website URL to scan",
    ),
    "scan_depth": ParameterDefinition(
        name="scan_depth",
        param_type=ParameterType.STRING,
        required=False,
        description="Scan depth: basic, standard, or comprehensive",
        default="standard",
    ),
    "topic": ParameterDefinition(
        name="topic",
        param_type=ParameterType.STRING,
        required=True,
        description="Conversation topic",
    ),
    "stage": ParameterDefinition(
        name="stage",
        param_type=ParameterType.STRING,
        required=True,
        description="Onboarding stage",
    ),
    "metrics_type": ParameterDefinition(
        name="metrics_type",
        param_type=ParameterType.STRING,
        required=False,
        description="Types of metrics to retrieve",
        default="all",
    ),
    "data_sources": ParameterDefinition(
        name="data_sources",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Sources of data for insights generation",
    ),
    "insight_types": ParameterDefinition(
        name="insight_types",
        param_type=ParameterType.ARRAY,
        required=False,
        description="Types of insights to generate",
    ),
    "time_range": ParameterDefinition(
        name="time_range",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Time range for analysis",
    ),
    "market_context": ParameterDefinition(
        name="market_context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Market context information",
    ),
    "website_data": ParameterDefinition(
        name="website_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Scanned website data",
    ),
    "depth": ParameterDefinition(
        name="depth",
        param_type=ParameterType.INTEGER,
        required=False,
        description="Analysis depth level",
        default=5,
    ),
    "constraints": ParameterDefinition(
        name="constraints",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Resource or operational constraints",
    ),
    "current_plan": ParameterDefinition(
        name="current_plan",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Current action plan to optimize",
    ),
    "optimization_goals": ParameterDefinition(
        name="optimization_goals",
        param_type=ParameterType.ARRAY,
        required=False,
        description="Goals for optimization",
    ),
    "tasks": ParameterDefinition(
        name="tasks",
        param_type=ParameterType.ARRAY,
        required=True,
        description="List of tasks to prioritize or schedule",
    ),
    "criteria": ParameterDefinition(
        name="criteria",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Prioritization criteria",
    ),
    "resources": ParameterDefinition(
        name="resources",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Available resources",
    ),
    "subject": ParameterDefinition(
        name="subject",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Subject for SWOT analysis",
    ),
    "user_message": ParameterDefinition(
        name="user_message",
        param_type=ParameterType.STRING,
        required=True,
        description="User's input message",
    ),
    "include_summary": ParameterDefinition(
        name="include_summary",
        param_type=ParameterType.BOOLEAN,
        required=False,
        description="Whether to include conversation summary",
        default=True,
    ),
    "context_type": ParameterDefinition(
        name="context_type",
        param_type=ParameterType.STRING,
        required=False,
        description="Type of strategic context to retrieve",
        default="full",
    ),
    "action_data": ParameterDefinition(
        name="action_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Data for creating an action",
    ),
    "completion_data": ParameterDefinition(
        name="completion_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Action completion data",
    ),
    "closure_data": ParameterDefinition(
        name="closure_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Issue closure data",
    ),
    "update_data": ParameterDefinition(
        name="update_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="KPI update data",
    ),
    "update_value": ParameterDefinition(
        name="update_value",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Value for KPI update",
    ),
    "kpi_updates": ParameterDefinition(
        name="kpi_updates",
        param_type=ParameterType.ARRAY,
        required=True,
        description="KPI updates to sync",
    ),
    "connections": ParameterDefinition(
        name="connections",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Strategic connections to update",
    ),
    "conflict_id": ParameterDefinition(
        name="conflict_id",
        param_type=ParameterType.STRING,
        required=True,
        description="KPI conflict identifier",
    ),
    "conflict_details": ParameterDefinition(
        name="conflict_details",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Details of KPI conflict",
    ),
    "analysis_type": ParameterDefinition(
        name="analysis_type",
        param_type=ParameterType.STRING,
        required=True,
        description="Type of analysis to perform",
    ),
    "operations_data": ParameterDefinition(
        name="operations_data",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Operations data for analysis",
    ),
    "performance_data": ParameterDefinition(
        name="performance_data",
        param_type=ParameterType.OBJECT,
        required=False,
        description="KPI performance data",
    ),
    # =========================================================================
    # BUSINESS FOUNDATION PARAMETERS
    # =========================================================================
    "business_foundation": ParameterDefinition(
        name="business_foundation",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Complete business foundation object",
    ),
    "niche": ParameterDefinition(
        name="niche",
        param_type=ParameterType.STRING,
        required=False,
        description="Business niche/market segment",
    ),
    "ica": ParameterDefinition(
        name="ica",
        param_type=ParameterType.STRING,
        required=False,
        description="Ideal Customer Avatar",
    ),
    "value_proposition": ParameterDefinition(
        name="value_proposition",
        param_type=ParameterType.STRING,
        required=False,
        description="Business value proposition",
    ),
    "core_values": ParameterDefinition(
        name="core_values",
        param_type=ParameterType.ARRAY,
        required=False,
        description="List of core values",
    ),
    "purpose": ParameterDefinition(
        name="purpose",
        param_type=ParameterType.STRING,
        required=False,
        description="Business purpose statement",
    ),
    "vision": ParameterDefinition(
        name="vision",
        param_type=ParameterType.STRING,
        required=False,
        description="Business vision statement",
    ),
    "business_context": ParameterDefinition(
        name="business_context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Additional business context",
    ),
    "current_strategy": ParameterDefinition(
        name="current_strategy",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Current business strategy",
    ),
    "strategic_context": ParameterDefinition(
        name="strategic_context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Full strategic planning context",
    ),
    "strategy": ParameterDefinition(
        name="strategy",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Business strategy for analysis",
    ),
    "operations": ParameterDefinition(
        name="operations",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Operations data for alignment analysis",
    ),
    # =========================================================================
    # GOAL PARAMETERS
    # =========================================================================
    "goal": ParameterDefinition(
        name="goal",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Single goal object",
    ),
    "goals": ParameterDefinition(
        name="goals",
        param_type=ParameterType.ARRAY,
        required=True,
        description="List of all goals",
    ),
    # =========================================================================
    # KPI PARAMETERS
    # =========================================================================
    "kpi_id": ParameterDefinition(
        name="kpi_id",
        param_type=ParameterType.STRING,
        required=True,
        description="KPI identifier",
    ),
    "kpis": ParameterDefinition(
        name="kpis",
        param_type=ParameterType.ARRAY,
        required=True,
        description="List of all KPIs",
    ),
    "existing_kpis": ParameterDefinition(
        name="existing_kpis",
        param_type=ParameterType.ARRAY,
        required=False,
        description="List of existing KPIs",
    ),
    "related_kpis": ParameterDefinition(
        name="related_kpis",
        param_type=ParameterType.ARRAY,
        required=True,
        description="KPIs related to an action",
    ),
    "operational_kpis": ParameterDefinition(
        name="operational_kpis",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Operational KPIs for conflict detection",
    ),
    "strategic_kpis": ParameterDefinition(
        name="strategic_kpis",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Strategic KPIs for sync/conflict detection",
    ),
    # =========================================================================
    # ACTION PARAMETERS
    # =========================================================================
    "action": ParameterDefinition(
        name="action",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Action item object",
    ),
    "action_id": ParameterDefinition(
        name="action_id",
        param_type=ParameterType.STRING,
        required=True,
        description="Action identifier",
    ),
    "action_details": ParameterDefinition(
        name="action_details",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Detailed action information",
    ),
    # =========================================================================
    # ISSUE PARAMETERS
    # =========================================================================
    "issue": ParameterDefinition(
        name="issue",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Issue object",
    ),
    "issue_id": ParameterDefinition(
        name="issue_id",
        param_type=ParameterType.STRING,
        required=True,
        description="Issue identifier",
    ),
    "issue_details": ParameterDefinition(
        name="issue_details",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Detailed issue information",
    ),
    "issue_status": ParameterDefinition(
        name="issue_status",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Issue status information",
    ),
    "root_causes": ParameterDefinition(
        name="root_causes",
        param_type=ParameterType.ARRAY,
        required=False,
        description="Identified root causes for an issue",
    ),
    # =========================================================================
    # CONVERSATION PARAMETERS
    # =========================================================================
    "conversation_id": ParameterDefinition(
        name="conversation_id",
        param_type=ParameterType.STRING,
        required=True,
        description="Conversation identifier",
    ),
    "conversation_history": ParameterDefinition(
        name="conversation_history",
        param_type=ParameterType.ARRAY,
        required=True,
        description="Conversation message history",
    ),
    "context": ParameterDefinition(
        name="context",
        param_type=ParameterType.OBJECT,
        required=False,
        description="Current conversation context",
    ),
    # =========================================================================
    # COMPUTED/DERIVED PARAMETERS
    # =========================================================================
    "alignment_score": ParameterDefinition(
        name="alignment_score",
        param_type=ParameterType.OBJECT,
        required=True,
        description="Calculated alignment score",
    ),
    "tenant_id": ParameterDefinition(
        name="tenant_id",
        param_type=ParameterType.STRING,
        required=True,
        description="Tenant identifier (from auth context)",
    ),
    "user_id": ParameterDefinition(
        name="user_id",
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


def get_required_parameters() -> list[ParameterDefinition]:
    """Get all parameters that are required by default.

    Returns:
        List of required ParameterDefinition objects
    """
    return [param for param in PARAMETER_REGISTRY.values() if param.required]


def list_all_parameters() -> list[ParameterDefinition]:
    """Get all parameter definitions.

    Returns:
        List of all ParameterDefinition objects
    """
    return list(PARAMETER_REGISTRY.values())


def get_parameters_by_type(param_type: ParameterType) -> list[ParameterDefinition]:
    """Get all parameters of a specific type.

    Args:
        param_type: Parameter type to filter by

    Returns:
        List of ParameterDefinition objects of that type
    """
    return [param for param in PARAMETER_REGISTRY.values() if param.param_type == param_type]


__all__ = [
    "PARAMETER_REGISTRY",
    "ParameterDefinition",
    "get_parameter",
    "get_parameters_by_type",
    "get_required_parameters",
    "list_all_parameters",
]
