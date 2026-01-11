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
        "goal_title",
        "goal_intent",
        "goal_status",
        "goal_horizon",
        "goal_strategies",
        "goal_kpis",
        "goal_progress",
    ),
    requires_from_payload=("goal_id",),
)
async def get_goal_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific goal by ID from payload."""
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
        # Get all goals and find the one we need
        goals = await context.client.get_user_goals(context.user_id, context.tenant_id)
        for goal in goals:
            if goal.get("id") == goal_id:
                return {
                    "goal": goal,
                    # Map new API fields: 'name' instead of 'title'
                    "goal_title": goal.get("name", ""),
                    "goal_intent": goal.get("description", ""),  # description maps to intent
                    "goal_status": goal.get("status", ""),
                    "goal_horizon": goal.get(
                        "type", ""
                    ),  # type maps to horizon (annual, quarterly, etc)
                    "goal_strategies": goal.get("strategies", []),
                    "goal_kpis": goal.get("kpis", []),
                    "goal_progress": goal.get("progress", 0),
                }
        logger.warning("retrieval_method.get_goal_by_id.not_found", goal_id=goal_id)
        return {}
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
    name="get_kpi_by_id",
    description="Retrieves KPI details for a specific KPI",
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
    """Retrieve a specific KPI by ID from payload."""
    kpi_id = context.payload.get("kpi_id")
    if not kpi_id:
        logger.warning("retrieval_method.get_kpi_by_id.missing_kpi_id")
        return {}

    try:
        logger.debug(
            "retrieval_method.get_kpi_by_id",
            kpi_id=kpi_id,
            tenant_id=context.tenant_id,
        )
        kpi = await context.client.get_kpi_by_id(kpi_id, context.tenant_id)
        return {
            "kpi": kpi,
            "name": kpi.get("name", ""),
            "value": kpi.get("currentValue", 0),
            "target": kpi.get("targetValue", 0),
            "unit": kpi.get("unit", ""),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_kpi_by_id.failed",
            error=str(e),
            kpi_id=kpi_id,
            tenant_id=context.tenant_id,
        )
        return {}


@register_retrieval_method(
    name="get_kpis_list",
    description="Retrieves all KPIs for the tenant",
    provides_params=("kpis_list",),
)
async def get_kpis_list(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all KPIs for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_kpis_list",
            tenant_id=context.tenant_id,
        )
        kpis = await context.client.get_kpis(context.tenant_id)
        return {"kpis_list": kpis}
    except Exception as e:
        logger.error(
            "retrieval_method.get_kpis_list.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {"kpis_list": []}


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
        "action_assigned_to",
    ),
    requires_from_payload=("action_id",),
)
async def get_action_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific action by ID from payload."""
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
        actions = await context.client.get_operations_actions(context.tenant_id)
        for action in actions:
            if action.get("id") == action_id:
                return {
                    "action": action,
                    "action_title": action.get("title", ""),
                    "action_description": action.get("description", ""),
                    "action_status": action.get("status", ""),
                    "action_priority": action.get("priority", ""),
                    # Map new API fields: 'dueDate' camelCase instead of snake_case
                    "action_due_date": action.get("dueDate", ""),
                    # Map new API fields: 'assignedPersonName' instead of 'assigned_to'
                    "action_assigned_to": action.get("assignedPersonName", ""),
                }
        logger.warning("retrieval_method.get_action_by_id.not_found", action_id=action_id)
        return {}
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
    provides_params=("actions", "actions_count", "pending_actions_count"),
)
async def get_all_actions(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve all actions for the tenant."""
    try:
        logger.debug(
            "retrieval_method.get_all_actions",
            tenant_id=context.tenant_id,
        )
        actions = await context.client.get_operations_actions(context.tenant_id)
        actions_list = list(actions)
        # Map new API fields: status values are snake_case (not_started, in_progress)
        pending = [a for a in actions_list if a.get("status") in ("not_started", "in_progress")]
        return {
            "actions": actions_list,
            "actions_count": len(actions_list),
            "pending_actions_count": len(pending),
        }
    except Exception as e:
        logger.error(
            "retrieval_method.get_all_actions.failed",
            error=str(e),
            tenant_id=context.tenant_id,
        )
        return {"actions": [], "actions_count": 0, "pending_actions_count": 0}


@register_retrieval_method(
    name="get_issue_by_id",
    description="Retrieves details for a specific issue",
    provides_params=(
        "issue",
        "issue_title",
        "issue_description",
        "issue_status",
        "issue_priority",
        "issue_business_impact",
        "issue_assigned_to",
    ),
    requires_from_payload=("issue_id",),
)
async def get_issue_by_id(context: RetrievalContext) -> dict[str, Any]:
    """Retrieve a specific issue by ID from payload."""
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
        issues = await context.client.get_operations_issues(context.tenant_id)
        for issue in issues:
            if issue.get("id") == issue_id:
                return {
                    "issue": issue,
                    "issue_title": issue.get("title", ""),
                    "issue_description": issue.get("description", ""),
                    # Map new API fields: uses statusConfigId, not simple 'status' string
                    "issue_status": issue.get("statusConfigId", ""),
                    "issue_priority": issue.get("priority", ""),
                    # Map new API fields: 'impact' instead of 'business_impact'
                    "issue_business_impact": issue.get("impact", ""),
                    # Map new API fields: 'assignedPersonName' instead of 'assigned_to'
                    "issue_assigned_to": issue.get("assignedPersonName", ""),
                }
        logger.warning("retrieval_method.get_issue_by_id.not_found", issue_id=issue_id)
        return {}
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
        issues = await context.client.get_operations_issues(context.tenant_id)
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
