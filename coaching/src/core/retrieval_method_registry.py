"""Retrieval Method Registry - Defines methods for fetching parameter data.

This module provides a registry of callable methods that can retrieve
parameter data from various sources. Parameters reference these methods
by name, allowing the template processor to:

1. Group parameters by retrieval method
2. Call each method only ONCE regardless of how many params it provides
3. Extract individual parameter values from the method's response

Usage:
    from coaching.src.core.retrieval_method_registry import (
        RETRIEVAL_METHODS,
        get_retrieval_method,
        register_retrieval_method,
    )

    # Get a registered method
    method = get_retrieval_method("get_business_foundation")
    data = await method(context)

    # Register a new method
    @register_retrieval_method("my_method")
    async def my_method(context: RetrievalContext) -> dict[str, Any]:
        ...
"""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import structlog
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

logger = structlog.get_logger()


@dataclass
class RetrievalContext:
    """Context passed to retrieval methods.

    Contains all information a retrieval method might need to fetch data.

    Attributes:
        client: BusinessApiClient for API calls
        tenant_id: Current tenant identifier
        user_id: Current user identifier
        payload: Original request payload (for extracting IDs like goal_id)
    """

    client: BusinessApiClient
    tenant_id: str
    user_id: str
    payload: dict[str, Any]


# Type alias for retrieval method functions
RetrievalMethodFunc = Callable[[RetrievalContext], Coroutine[Any, Any, dict[str, Any]]]


@dataclass(frozen=True)
class RetrievalMethodDefinition:
    """Definition of a retrieval method.

    Attributes:
        name: Unique identifier for the method
        description: Human-readable description
        provides_params: Tuple of parameter names this method can provide
        requires_from_payload: Parameters that must be in payload for this method
    """

    name: str
    description: str
    provides_params: tuple[str, ...]
    requires_from_payload: tuple[str, ...] = ()


# Registry storing method definitions and their implementations
_RETRIEVAL_METHOD_DEFINITIONS: dict[str, RetrievalMethodDefinition] = {}
RETRIEVAL_METHODS: dict[str, RetrievalMethodFunc] = {}


def register_retrieval_method(
    name: str,
    description: str,
    provides_params: tuple[str, ...],
    requires_from_payload: tuple[str, ...] = (),
) -> Callable[[RetrievalMethodFunc], RetrievalMethodFunc]:
    """Decorator to register a retrieval method.

    Args:
        name: Unique identifier for the method
        description: Human-readable description
        provides_params: Parameters this method can provide
        requires_from_payload: Parameters needed from payload to call this method

    Returns:
        Decorator function
    """

    def decorator(func: RetrievalMethodFunc) -> RetrievalMethodFunc:
        _RETRIEVAL_METHOD_DEFINITIONS[name] = RetrievalMethodDefinition(
            name=name,
            description=description,
            provides_params=provides_params,
            requires_from_payload=requires_from_payload,
        )
        RETRIEVAL_METHODS[name] = func
        return func

    return decorator


def get_retrieval_method(name: str) -> RetrievalMethodFunc | None:
    """Get a retrieval method by name.

    Args:
        name: Method identifier

    Returns:
        The retrieval method function, or None if not found
    """
    return RETRIEVAL_METHODS.get(name)


def get_retrieval_method_definition(name: str) -> RetrievalMethodDefinition | None:
    """Get a retrieval method definition by name.

    Args:
        name: Method identifier

    Returns:
        The method definition, or None if not found
    """
    return _RETRIEVAL_METHOD_DEFINITIONS.get(name)


def list_retrieval_methods() -> list[RetrievalMethodDefinition]:
    """List all registered retrieval method definitions.

    Returns:
        List of all method definitions
    """
    return list(_RETRIEVAL_METHOD_DEFINITIONS.values())


# =============================================================================
# REGISTERED RETRIEVAL METHODS
# =============================================================================


@register_retrieval_method(
    name="get_business_foundation",
    description="Retrieves complete business foundation with 6 strategic pillars",
    provides_params=(
        # Full foundation object
        "business_foundation",
        # Profile (Pillar 1)
        "business_name",
        "company_name",
        "business_description",
        "industry",
        "sub_industry",
        "company_stage",
        "company_size",
        "revenue_range",
        "year_founded",
        "geographic_focus",
        "headquarters_location",
        "website",
        # Identity (Pillar 2)
        "vision",
        "vision_timeframe",
        "purpose",
        "who_we_serve",
        "core_values",
        # Target Market (Pillar 3)
        "niche_statement",
        "market_size",
        "growth_trend",
        "market_characteristics",
        "icas",  # Ideal Customer Avatars
        # Products & Services (Pillar 4)
        "products",
        # Value Proposition (Pillar 5)
        "unique_selling_proposition",
        "key_differentiators",
        "competitive_advantages",
        "brand_promise",
        "positioning_statement",
        # Business Model (Pillar 6)
        "business_model_types",
        "revenue_streams",
        "pricing_strategy",
        "key_partnerships",
        "distribution_channels",
    ),
)
async def get_business_foundation(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve complete business foundation data with 6 strategic pillars.

    Returns:
        Flattened dictionary with:
        - business_foundation: Full raw response
        - Profile fields (business_name, industry, company_stage, etc.)
        - Identity fields (vision, purpose, core_values, etc.)
        - Market fields (niche_statement, icas, etc.)
        - Products array
        - Proposition fields (unique_selling_proposition, key_differentiators, etc.)
        - Model fields (business_model_types, revenue_streams, etc.)
    """
    try:
        logger.debug(
            "retrieval_method.get_business_foundation",
            tenant_id=context.tenant_id,
        )
        data = await context.client.get_business_foundation(context.tenant_id)

        # Flatten the nested structure for parameter extraction
        result: dict[str, Any] = {
            "business_foundation": data,  # Keep full object available
        }

        # Extract Profile (Pillar 1)
        profile = data.get("profile", {})
        result["business_name"] = profile.get("businessName", "")
        result["company_name"] = profile.get("businessName", "")  # Alias
        result["business_description"] = profile.get("businessDescription", "")
        result["industry"] = profile.get("industry", "")
        result["sub_industry"] = profile.get("subIndustry", "")
        result["company_stage"] = profile.get("companyStage", "")
        result["company_size"] = profile.get("companySize", "")
        result["revenue_range"] = profile.get("revenueRange", "")
        result["year_founded"] = profile.get("yearFounded")
        result["geographic_focus"] = profile.get("geographicFocus", [])
        result["headquarters_location"] = profile.get("headquartersLocation", "")
        result["website"] = profile.get("website", "")

        # Extract Identity (Pillar 2)
        identity = data.get("identity", {})
        result["vision"] = identity.get("vision", "")
        result["vision_timeframe"] = identity.get("visionTimeframe", "")
        result["purpose"] = identity.get("purpose", "")
        result["who_we_serve"] = identity.get("whoWeServe", "")
        result["core_values"] = identity.get("values", [])

        # Extract Target Market (Pillar 3)
        market = data.get("market", {})
        result["niche_statement"] = market.get("nicheStatement", "")
        result["market_size"] = market.get("marketSize", "")
        result["growth_trend"] = market.get("growthTrend", "")
        result["market_characteristics"] = market.get("characteristics", [])
        result["icas"] = market.get("icas", [])

        # Extract Products (Pillar 4)
        result["products"] = data.get("products", [])

        # Extract Value Proposition (Pillar 5)
        proposition = data.get("proposition", {})
        result["unique_selling_proposition"] = proposition.get("uniqueSellingProposition", "")
        result["key_differentiators"] = proposition.get("keyDifferentiators", [])
        result["competitive_advantages"] = proposition.get("competitiveAdvantages", [])
        result["brand_promise"] = proposition.get("brandPromise", "")
        result["positioning_statement"] = proposition.get("positioningStatement", "")

        # Extract Business Model (Pillar 6)
        model = data.get("model", {})
        result["business_model_types"] = model.get("types", [])
        result["revenue_streams"] = model.get("revenueStreams", [])
        result["pricing_strategy"] = model.get("pricingStrategy", "")
        result["key_partnerships"] = model.get("keyPartnerships", [])
        result["distribution_channels"] = model.get("distributionChannels", [])

        return result

    except Exception as e:
        logger.error(
            "retrieval_method.get_business_foundation.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {}


@register_retrieval_method(
    name="get_user_context",
    description="Retrieves user profile and context information",
    provides_params=(
        "user_name",
        "user_email",
        "user_role",
        "user_department",
        "user_position",
    ),
)
async def get_user_context(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve user context and profile data."""
    try:
        logger.debug(
            "retrieval_method.get_user_context",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
        )
        data = await context.client.get_user_context(context.user_id, context.tenant_id)
        # Remap to expected parameter names
        # Use first_name for user_name (more natural for LLM greeting)
        return {
            "user_name": data.get("first_name", "") or data.get("name", ""),
            "user_email": data.get("email", ""),
            "user_role": data.get("role", ""),
            "user_department": data.get("department", ""),
            "user_position": data.get("position", ""),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_user_context.failed",
            error=str(e),
            user_id=context.user_id,
        )
        return {}


@register_retrieval_method(
    name="get_goal_by_id",
    description="Retrieves details for a specific goal",
    provides_params=(
        "goal",
        "goal_name",
        "goal_description",
        "goal_status",
        "goal_type",
        "goal_progress",
        "goal_start_date",
        "goal_end_date",
        "goal_owner_id",
        "goal_owner_name",
    ),
    requires_from_payload=("goal_id",),
)
async def get_goal_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific goal by ID from payload using direct API call."""
    goal_id = context.payload.get("goal_id")
    if not goal_id:
        logger.warning("retrieval_method.get_goal_by_id.missing_goal_id")
        return {}

    try:
        logger.debug(
            "retrieval_method.get_goal_by_id",
            goal_id=goal_id,
            tenant_id=context.tenant_id,
        )
        # Direct API call to get goal by ID
        goal = await context.client.get_goal_by_id(goal_id, context.tenant_id)
        if not goal:
            logger.warning("retrieval_method.get_goal_by_id.not_found", goal_id=goal_id)
            return {}

        return {
            "goal": goal,
            "goal_name": goal.get("name", ""),
            "goal_description": goal.get("description", ""),
            "goal_status": goal.get("status", ""),
            "goal_type": goal.get("type", ""),  # annual, quarterly, monthly
            "goal_progress": goal.get("progress", 0),
            "goal_start_date": goal.get("startDate", ""),
            "goal_end_date": goal.get("endDate", ""),
            "goal_owner_id": goal.get("ownerId", ""),
            "goal_owner_name": goal.get("ownerName", ""),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_goal_by_id.failed",
            error=str(e),
            goal_id=goal_id,
        )
        return {}


@register_retrieval_method(
    name="get_all_goals",
    description="Retrieves all goals for the user",
    provides_params=("goals", "goals_count", "goals_summary"),
)
async def get_all_goals(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all goals for the current user."""
    try:
        logger.debug(
            "retrieval_method.get_all_goals",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
        )
        goals = await context.client.get_user_goals(context.user_id, context.tenant_id)
        goals_list = list(goals)
        return {
            "goals": goals_list,
            "goals_count": len(goals_list),
            "goals_summary": _summarize_goals(goals_list),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_all_goals.failed",
            error=str(e),
            user_id=context.user_id,
        )
        return {"goals": [], "goals_count": 0, "goals_summary": ""}


# NOTE: get_goal_stats and get_performance_score removed - endpoints don't exist
# Goal statistics can be derived from get_all_goals results
# Performance metrics will be computed from measures summary data


@register_retrieval_method(
    name="get_measure_by_id",
    description="Retrieves measure/KPI details for a specific measure",
    provides_params=(
        "measure",
        "measure_name",
        "measure_description",
        "measure_unit",
        "measure_direction",
        "measure_type",
        "measure_category",
        "measure_current_value",
        "measure_owner_id",
        "measure_owner_name",
    ),
    requires_from_payload=("measure_id",),
)
async def get_measure_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific measure by ID using direct API call."""
    measure_id = context.payload.get("measure_id") or context.payload.get("kpi_id")
    if not measure_id:
        logger.warning("retrieval_method.get_measure_by_id.missing_measure_id")
        return {}

    try:
        logger.debug(
            "retrieval_method.get_measure_by_id",
            measure_id=measure_id,
            tenant_id=context.tenant_id,
        )
        measure = await context.client.get_measure_by_id(measure_id, context.tenant_id)
        if not measure:
            logger.warning("retrieval_method.get_measure_by_id.not_found", measure_id=measure_id)
            return {}

        return {
            "measure": measure,
            "measure_name": measure.get("name", ""),
            "measure_description": measure.get("description", ""),
            "measure_unit": measure.get("unit", ""),
            "measure_direction": measure.get("direction", ""),  # up, down, maintain
            "measure_type": measure.get("type", ""),
            "measure_category": measure.get("category", ""),
            "measure_current_value": measure.get("currentValue"),
            "measure_owner_id": measure.get("ownerId", ""),
            "measure_owner_name": measure.get("ownerName", ""),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_measure_by_id.failed",
            error=str(e),
            measure_id=measure_id,
            tenant_id=context.tenant_id,
        )
        return {}


# Alias for backward compatibility
@register_retrieval_method(
    name="get_kpi_by_id",
    description="Deprecated: Use get_measure_by_id. Retrieves KPI details",
    provides_params=(
        "kpi",
        "kpi_name",
        "kpi_value",
        "kpi_target",
        "kpi_unit",
    ),
    requires_from_payload=("kpi_id",),
)
async def get_kpi_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Deprecated: Use get_measure_by_id instead."""
    result = await get_measure_by_id(context)
    # Map new fields to old names for backward compatibility
    return {
        "kpi": result.get("measure", {}),
        "kpi_name": result.get("measure_name", ""),
        "kpi_value": result.get("measure_current_value", 0),
        "kpi_target": 0,  # Targets now come from measure links
        "kpi_unit": result.get("measure_unit", ""),
    }


@register_retrieval_method(
    name="get_measures",
    description="Retrieves all measures for the tenant",
    provides_params=("measures", "measures_count"),
)
async def get_measures(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all measures for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_measures",
            tenant_id=context.tenant_id,
        )
        measures = await context.client.get_measures(context.tenant_id)
        return {
            "measures": measures,
            "measures_count": len(measures),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_measures.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {"measures": [], "measures_count": 0}


# Alias for backward compatibility
@register_retrieval_method(
    name="get_kpis_list",
    description="Deprecated: Use get_measures. Retrieves all KPIs",
    provides_params=("kpis_list",),
)
async def get_kpis_list(context: RetrievalContext) -> dict[str, Any]:
    """Deprecated: Use get_measures instead."""
    result = await get_measures(context)
    return {"kpis_list": result.get("measures", [])}


@register_retrieval_method(
    name="get_action_by_id",
    description="Retrieves details for a specific action item",
    provides_params=(
        "action",
        "action_title",
        "action_description",
        "action_status",
        "action_priority",
        "action_due_date",
        "action_start_date",
        "action_assigned_to",
        "action_progress",
        "action_estimated_hours",
        "action_actual_hours",
        "action_connections",
    ),
    requires_from_payload=("action_id",),
)
async def get_action_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific action by ID using direct API call."""
    action_id = context.payload.get("action_id")
    if not action_id:
        logger.warning("retrieval_method.get_action_by_id.missing_action_id")
        return {}

    try:
        logger.debug(
            "retrieval_method.get_action_by_id",
            action_id=action_id,
            tenant_id=context.tenant_id,
        )
        # Direct API call
        action = await context.client.get_action_by_id(action_id, context.tenant_id)
        if not action:
            logger.warning("retrieval_method.get_action_by_id.not_found", action_id=action_id)
            return {}

        return {
            "action": action,
            "action_title": action.get("title", ""),
            "action_description": action.get("description", ""),
            "action_status": action.get("status", ""),
            "action_priority": action.get("priority", ""),
            "action_due_date": action.get("dueDate", ""),
            "action_start_date": action.get("startDate", ""),
            "action_assigned_to": action.get("assignedPersonName", ""),
            "action_progress": action.get("progress", 0),
            "action_estimated_hours": action.get("estimatedHours", 0),
            "action_actual_hours": action.get("actualHours", 0),
            "action_connections": action.get("connections", {}),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_action_by_id.failed",
            error=str(e),
            action_id=action_id,
        )
        return {}


@register_retrieval_method(
    name="get_all_actions",
    description="Retrieves all recent actions",
    provides_params=("actions", "actions_count", "pending_actions_count", "actions_by_status"),
)
async def get_all_actions(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all actions for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_all_actions",
            tenant_id=context.tenant_id,
        )
        actions = await context.client.get_actions(context.tenant_id)
        actions_list = list(actions)

        # Group by status
        by_status: dict[str, list] = {}
        pending_count = 0
        for a in actions_list:
            status = a.get("status", "unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(a)
            if status in ("not_started", "in_progress"):
                pending_count += 1

        return {
            "actions": actions_list,
            "actions_count": len(actions_list),
            "pending_actions_count": pending_count,
            "actions_by_status": by_status,
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_all_actions.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {
            "actions": [],
            "actions_count": 0,
            "pending_actions_count": 0,
            "actions_by_status": {},
        }


@register_retrieval_method(
    name="get_issue_by_id",
    description="Retrieves details for a specific issue",
    provides_params=(
        "issue",
        "issue_title",
        "issue_description",
        "issue_status_config_id",
        "issue_type_config_id",
        "issue_priority",
        "issue_impact",
        "issue_assigned_to",
        "issue_reporter",
        "issue_due_date",
        "issue_estimated_hours",
        "issue_connections",
        "issue_tags",
    ),
    requires_from_payload=("issue_id",),
)
async def get_issue_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific issue by ID using direct API call."""
    issue_id = context.payload.get("issue_id")
    if not issue_id:
        logger.warning("retrieval_method.get_issue_by_id.missing_issue_id")
        return {}

    try:
        logger.debug(
            "retrieval_method.get_issue_by_id",
            issue_id=issue_id,
            tenant_id=context.tenant_id,
        )
        # Direct API call
        issue = await context.client.get_issue_by_id(issue_id, context.tenant_id)
        if not issue:
            logger.warning("retrieval_method.get_issue_by_id.not_found", issue_id=issue_id)
            return {}

        return {
            "issue": issue,
            "issue_title": issue.get("title", ""),
            "issue_description": issue.get("description", ""),
            "issue_status_config_id": issue.get("statusConfigId", ""),
            "issue_type_config_id": issue.get("typeConfigId", ""),
            "issue_priority": issue.get("priority", ""),
            "issue_impact": issue.get("impact", ""),
            "issue_assigned_to": issue.get("assignedPersonName", ""),
            "issue_reporter": issue.get("reporterName", ""),
            "issue_due_date": issue.get("dueDate", ""),
            "issue_estimated_hours": issue.get("estimatedHours", 0),
            "issue_connections": issue.get("connections", {}),
            "issue_tags": issue.get("tags", []),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_issue_by_id.failed",
            error=str(e),
            issue_id=issue_id,
        )
        return {}


@register_retrieval_method(
    name="get_all_issues",
    description="Retrieves all open issues",
    provides_params=("issues", "issues_count", "critical_issues_count"),
)
async def get_all_issues(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all issues for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_all_issues",
            tenant_id=context.tenant_id,
        )
        issues = await context.client.get_issues(context.tenant_id)
        issues_list = list(issues)
        critical = [i for i in issues_list if i.get("priority") == "critical"]
        return {
            "issues": issues_list,
            "issues_count": len(issues_list),
            "critical_issues_count": len(critical),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_all_issues.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {"issues": [], "issues_count": 0, "critical_issues_count": 0}


# =============================================================================
# NEW RETRIEVAL METHODS (Phase 3)
# =============================================================================


@register_retrieval_method(
    name="get_strategy_by_id",
    description="Retrieves details for a specific strategy",
    provides_params=(
        "strategy",
        "strategy_name",
        "strategy_description",
        "strategy_status",
        "strategy_type",
        "strategy_progress",
        "strategy_start_date",
        "strategy_end_date",
        "strategy_owner_id",
        "strategy_owner_name",
        "strategy_goal_id",
        "strategy_alignment_score",
        "strategy_alignment_explanation",
    ),
    requires_from_payload=("strategy_id",),
)
async def get_strategy_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific strategy by ID using direct API call."""
    strategy_id = context.payload.get("strategy_id")
    if not strategy_id:
        logger.warning("retrieval_method.get_strategy_by_id.missing_strategy_id")
        return {}

    try:
        logger.debug(
            "retrieval_method.get_strategy_by_id",
            strategy_id=strategy_id,
            tenant_id=context.tenant_id,
        )
        strategy = await context.client.get_strategy_by_id(strategy_id, context.tenant_id)
        if not strategy:
            logger.warning("retrieval_method.get_strategy_by_id.not_found", strategy_id=strategy_id)
            return {}

        return {
            "strategy": strategy,
            "strategy_name": strategy.get("name", ""),
            "strategy_description": strategy.get("description", ""),
            "strategy_status": strategy.get("status", ""),
            "strategy_type": strategy.get("type", ""),  # initiative, project, etc.
            "strategy_progress": strategy.get("progress", 0),
            "strategy_start_date": strategy.get("startDate", ""),
            "strategy_end_date": strategy.get("endDate", ""),
            "strategy_owner_id": strategy.get("ownerId", ""),
            "strategy_owner_name": strategy.get("ownerName", ""),
            "strategy_goal_id": strategy.get("goalId", ""),
            "strategy_alignment_score": strategy.get("alignmentScore"),
            "strategy_alignment_explanation": strategy.get("alignmentExplanation", ""),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_strategy_by_id.failed",
            error=str(e),
            strategy_id=strategy_id,
        )
        return {}


@register_retrieval_method(
    name="get_all_strategies",
    description="Retrieves all strategies for the tenant",
    provides_params=(
        "strategies",
        "strategies_count",
        "strategies_by_status",
        "strategies_by_type",
    ),
)
async def get_all_strategies(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all strategies for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_all_strategies",
            tenant_id=context.tenant_id,
        )
        strategies = await context.client.get_strategies(context.tenant_id)
        strategies_list = list(strategies)

        # Group by status
        by_status: dict[str, list] = {}
        for s in strategies_list:
            status = s.get("status", "unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(s)

        # Group by type
        by_type: dict[str, list] = {}
        for s in strategies_list:
            stype = s.get("type", "unknown")
            if stype not in by_type:
                by_type[stype] = []
            by_type[stype].append(s)

        return {
            "strategies": strategies_list,
            "strategies_count": len(strategies_list),
            "strategies_by_status": by_status,
            "strategies_by_type": by_type,
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_all_strategies.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {
            "strategies": [],
            "strategies_count": 0,
            "strategies_by_status": {},
            "strategies_by_type": {},
        }


@register_retrieval_method(
    name="get_measures_summary",
    description="Retrieves comprehensive measures summary with progress and statistics",
    provides_params=(
        "measures_summary",
        "measures",
        "measures_count",
        "measures_health_score",
        "measures_status_breakdown",
        "measures_category_breakdown",
        "measures_owner_breakdown",
        "measures_by_status",
        "at_risk_measures",
    ),
)
async def get_measures_summary(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve comprehensive measures summary - optimization endpoint.

    This single call provides all measures with:
    - Full measure details
    - Progress per goal/strategy link
    - Summary statistics
    - Health score
    - Trend data
    """
    try:
        logger.debug(
            "retrieval_method.get_measures_summary",
            tenant_id=context.tenant_id,
        )
        data = await context.client.get_measures_summary(context.tenant_id)

        measures = data.get("measures", [])
        summary = data.get("summary", {})

        # Group measures by status
        by_status: dict[str, list] = {}
        at_risk = []
        for m in measures:
            status = m.get("status", "unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(m)
            if status in ("at_risk", "behind"):
                at_risk.append(m)

        return {
            "measures_summary": data,
            "measures": measures,
            "measures_count": len(measures),
            "measures_health_score": data.get("healthScore", 0),
            "measures_status_breakdown": summary.get("byStatus", {}),
            "measures_category_breakdown": summary.get("byCategory", []),
            "measures_owner_breakdown": summary.get("byOwner", []),
            "measures_by_status": by_status,
            "at_risk_measures": at_risk,
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_measures_summary.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {
            "measures_summary": {},
            "measures": [],
            "measures_count": 0,
            "measures_health_score": 0,
            "measures_status_breakdown": {},
            "measures_category_breakdown": [],
            "measures_owner_breakdown": [],
            "measures_by_status": {},
            "at_risk_measures": [],
        }


@register_retrieval_method(
    name="get_people",
    description="Retrieves all people (team members) for the tenant",
    provides_params=(
        "people",
        "people_count",
        "people_by_department",
    ),
)
async def get_people(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all team members for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_people",
            tenant_id=context.tenant_id,
        )
        people = await context.client.get_people(context.tenant_id)
        people_list = list(people)

        # Group by department
        by_department: dict[str, list] = {}
        for p in people_list:
            dept = p.get("departmentName", "Unassigned")
            if dept not in by_department:
                by_department[dept] = []
            by_department[dept].append(p)

        return {
            "people": people_list,
            "people_count": len(people_list),
            "people_by_department": by_department,
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_people.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {"people": [], "people_count": 0, "people_by_department": {}}


@register_retrieval_method(
    name="get_person_by_id",
    description="Retrieves details for a specific person",
    provides_params=(
        "person",
        "person_name",
        "person_email",
        "person_role",
        "person_department",
        "person_position",
    ),
    requires_from_payload=("person_id",),
)
async def get_person_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific person by ID."""
    person_id = context.payload.get("person_id")
    if not person_id:
        logger.warning("retrieval_method.get_person_by_id.missing_person_id")
        return {}

    try:
        logger.debug(
            "retrieval_method.get_person_by_id",
            person_id=person_id,
            tenant_id=context.tenant_id,
        )
        person = await context.client.get_person_by_id(person_id, context.tenant_id)
        if not person:
            logger.warning("retrieval_method.get_person_by_id.not_found", person_id=person_id)
            return {}

        return {
            "person": person,
            "person_name": person.get("name", ""),
            "person_email": person.get("email", ""),
            "person_role": person.get("role", ""),
            "person_department": person.get("departmentName", ""),
            "person_position": person.get("positionName", ""),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_person_by_id.failed",
            error=str(e),
            person_id=person_id,
        )
        return {}


@register_retrieval_method(
    name="get_departments",
    description="Retrieves all departments for the tenant",
    provides_params=("departments", "departments_count"),
)
async def get_departments(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all departments for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_departments",
            tenant_id=context.tenant_id,
        )
        departments = await context.client.get_departments(context.tenant_id)
        return {
            "departments": departments,
            "departments_count": len(departments),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_departments.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {"departments": [], "departments_count": 0}


@register_retrieval_method(
    name="get_positions",
    description="Retrieves all positions for the tenant",
    provides_params=("positions", "positions_count"),
)
async def get_positions(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all positions for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_positions",
            tenant_id=context.tenant_id,
        )
        positions = await context.client.get_positions(context.tenant_id)
        return {
            "positions": positions,
            "positions_count": len(positions),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_positions.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {"positions": [], "positions_count": 0}


@register_retrieval_method(
    name="get_onboarding_data",
    description="Retrieves onboarding data including niche, ICA, value proposition, and products",
    provides_params=(
        "onboarding_niche",
        "onboarding_ica",
        "onboarding_value_proposition",
        "onboarding_products",
        "onboarding_business_name",
    ),
)
async def get_onboarding_data(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve onboarding data from Account Service.

    Extracts step3 data (niche, ica, valueProposition) and products list.
    """
    try:
        logger.debug(
            "retrieval_method.get_onboarding_data",
            tenant_id=context.tenant_id,
        )
        data = await context.client.get_onboarding_data()

        # Extract step3 data
        step3 = data.get("step3", {}) or {}
        products = data.get("products", []) or []

        # Format products as list of dicts with name and problem
        formatted_products = [
            {"name": p.get("name", ""), "problem": p.get("problem", "")}
            for p in products
            if p.get("name")
        ]

        return {
            "onboarding_niche": step3.get("niche", ""),
            "onboarding_ica": step3.get("ica", ""),
            "onboarding_value_proposition": step3.get("valueProposition", ""),
            "onboarding_products": formatted_products,
            "onboarding_business_name": data.get("businessName", ""),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_onboarding_data.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {
            "onboarding_niche": "",
            "onboarding_ica": "",
            "onboarding_value_proposition": "",
            "onboarding_products": [],
            "onboarding_business_name": "",
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def _summarize_goals(goals: list[dict[str, Any]]) -> str:
    """Create a brief summary of goals for context."""
    if not goals:
        return "No goals defined yet."

    by_status: dict[str, int] = {}
    for goal in goals:
        status = goal.get("status", "unknown")
        by_status[status] = by_status.get(status, 0) + 1

    parts = [f"{count} {status}" for status, count in by_status.items()]
    return f"{len(goals)} goals: " + ", ".join(parts)


# =============================================================================
# WEBSITE CONTENT RETRIEVAL
# =============================================================================


@register_retrieval_method(
    name="get_website_content",
    description="Fetches and extracts content from a website URL",
    provides_params=(
        "website_content",
        "website_title",
        "meta_description",
    ),
    requires_from_payload=("website_url",),
)
async def get_website_content(context: RetrievalContext) -> dict[str, Any]:
    """Fetch and extract content from a website URL.

    This retrieval method:
    1. Gets the website_url from the request payload
    2. Fetches and parses the HTML content
    3. Extracts text, title, and meta description
    4. Returns them for use in prompt templates

    The actual scraping logic is delegated to WebsiteAnalysisService utilities.
    """
    import re
    from urllib.parse import urlparse

    import html2text
    import requests
    from bs4 import BeautifulSoup

    url = context.payload.get("website_url")
    if not url:
        logger.warning("retrieval_method.get_website_content.missing_url")
        return {
            "website_content": "",
            "website_title": "",
            "meta_description": "",
        }

    try:
        logger.debug("retrieval_method.get_website_content", url=url)

        # Validate URL
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        if not parsed.netloc:
            raise ValueError("URL must include a domain name")

        # Security: Block localhost and internal IPs
        blocked_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "[::]", "169.254"]
        if any(host in parsed.netloc.lower() for host in blocked_hosts):
            raise ValueError("Cannot analyze local or internal URLs")

        # Fetch website content
        headers = {
            "User-Agent": "PurposePathBot/1.0 (Business Analysis; +https://purposepath.app)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "close",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15,
            allow_redirects=True,
            verify=True,
        )
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        # Extract title
        title_tag = soup.find("title")
        website_title = title_tag.get_text().strip() if title_tag else ""

        # Extract meta description
        meta_desc = soup.find("meta", {"name": "description"})
        if not meta_desc:
            meta_desc = soup.find("meta", {"property": "og:description"})
        meta_content = meta_desc.get("content") if meta_desc else None
        meta_description = meta_content.strip() if isinstance(meta_content, str) else ""

        # Remove non-content elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()

        # Convert to text
        html_converter = html2text.HTML2Text()
        html_converter.ignore_links = False
        html_converter.ignore_images = True
        html_converter.ignore_emphasis = False
        text = html_converter.handle(str(soup))

        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +", " ", text)
        text = text.strip()

        # Truncate if too long (50k chars max)
        max_content_length = 50000
        if len(text) > max_content_length:
            text = text[:max_content_length] + "\n\n[Content truncated...]"

        logger.info(
            "retrieval_method.get_website_content.success",
            url=url,
            title=website_title,
            content_length=len(text),
        )

        return {
            "website_content": text,
            "website_title": website_title,
            "meta_description": meta_description,
        }

    except requests.Timeout:
        logger.error("retrieval_method.get_website_content.timeout", url=url)
        return {
            "website_content": "",
            "website_title": "",
            "meta_description": "",
        }
    except requests.RequestException as e:
        logger.error("retrieval_method.get_website_content.request_failed", url=url, error=str(e))
        return {
            "website_content": "",
            "website_title": "",
            "meta_description": "",
        }
    except Exception as e:
        logger.error("retrieval_method.get_website_content.failed", url=url, error=str(e))
        return {
            "website_content": "",
            "website_title": "",
            "meta_description": "",
        }


__all__: list[str] = [
    "RETRIEVAL_METHODS",
    "RetrievalContext",
    "RetrievalMethodDefinition",
    "RetrievalMethodFunc",
    "get_retrieval_method",
    "get_retrieval_method_definition",
    "list_retrieval_methods",
    "register_retrieval_method",
]
