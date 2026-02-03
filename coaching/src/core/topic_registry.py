"""Topic Registry - Central mapping of all API endpoints to topic configurations.

This module provides the definitive mapping between HTTP endpoints and their
corresponding LLM topic configurations, enabling a unified, topic-driven
architecture where endpoint behavior is configured through topic metadata
rather than hardcoded service classes.

Parameter source information is defined here per-endpoint since the same
parameter may come from different sources depending on the endpoint context.

For conversation coaching topics, use TemplateType to define the required templates.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TypedDict

from coaching.src.core.constants import (
    ParameterSource,
    PromptType,
    TierLevel,
    TopicCategory,
    TopicType,
)


class TemplateType(str, Enum):
    """Template types for coaching conversations.

    Templates are stored in S3 and loaded by the CoachingSessionService.
    Each conversation topic can define multiple templates for different phases.
    """

    SYSTEM = "system"  # System prompt (AI persona, rules, context)
    INITIATION = "initiation"  # First turn prompt for new sessions
    RESUME = "resume"  # Resume conversation prompt for existing sessions
    EXTRACTION = "extraction"  # Auto-generated from result_model for extraction


class ParameterInfo(TypedDict):
    """Type-safe dict for parameter info returned by get_parameters_for_topic."""

    name: str
    type: str
    required: bool
    description: str | None


@dataclass(frozen=True)
class ParameterRef:
    """Reference to a parameter with its source for a specific endpoint.

    The same parameter (e.g., "goal") may come from different sources in
    different endpoints - REQUEST body in one, fetched from GOAL service
    in another. This dataclass captures that per-endpoint source mapping.

    Attributes:
        name: Parameter name (must exist in PARAMETER_REGISTRY)
        source: Where to retrieve this parameter for this endpoint
        source_path: JSON path to extract value from source response
        required: Override for whether this param is required in this endpoint
    """

    name: str
    source: ParameterSource
    source_path: str = ""
    required: bool | None = None  # None means use default from PARAMETER_REGISTRY


# Shorthand helpers for creating ParameterRefs
def _req(name: str, path: str = "") -> ParameterRef:
    """Create a REQUEST source parameter reference (required by default)."""
    return ParameterRef(name=name, source=ParameterSource.REQUEST, source_path=path or name)


def _opt_req(name: str, path: str = "") -> ParameterRef:
    """Create an optional REQUEST source parameter reference."""
    return ParameterRef(
        name=name, source=ParameterSource.REQUEST, source_path=path or name, required=False
    )


def _onb(name: str, path: str = "") -> ParameterRef:
    """Create an ONBOARDING source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.ONBOARDING, source_path=path or name)


def _web(name: str, path: str = "") -> ParameterRef:
    """Create a WEBSITE source parameter reference (from URL scraping)."""
    return ParameterRef(name=name, source=ParameterSource.WEBSITE, source_path=path or name)


def _goal(name: str, path: str = "") -> ParameterRef:
    """Create a GOAL source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.GOAL, source_path=path)


def _goals(name: str, path: str = "") -> ParameterRef:
    """Create a GOALS source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.GOALS, source_path=path)


def _measure(name: str, path: str = "") -> ParameterRef:
    """Create a MEASURE source parameter reference (from get_measure_by_id)."""
    return ParameterRef(name=name, source=ParameterSource.MEASURE, source_path=path)


def _measures(name: str, path: str = "") -> ParameterRef:
    """Create a MEASURES source parameter reference (from get_measures_summary)."""
    return ParameterRef(name=name, source=ParameterSource.MEASURES, source_path=path)


def _strategy(name: str, path: str = "") -> ParameterRef:
    """Create a STRATEGY source parameter reference (from get_strategy_by_id)."""
    return ParameterRef(
        name=name, source=ParameterSource.GOAL, source_path=path
    )  # Reuse GOAL source


def _strategies(name: str, path: str = "") -> ParameterRef:
    """Create a STRATEGIES source parameter reference (from get_all_strategies)."""
    return ParameterRef(
        name=name, source=ParameterSource.GOALS, source_path=path
    )  # Reuse GOALS source


def _people(name: str, path: str = "") -> ParameterRef:
    """Create a PEOPLE source parameter reference (from get_people)."""
    return ParameterRef(
        name=name, source=ParameterSource.USER, source_path=path
    )  # Reuse USER source


def _departments(name: str, path: str = "") -> ParameterRef:
    """Create a DEPARTMENTS source parameter reference (from get_departments)."""
    return ParameterRef(
        name=name, source=ParameterSource.USER, source_path=path
    )  # Reuse USER source


def _action(name: str, path: str = "") -> ParameterRef:
    """Create an ACTION source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.ACTION, source_path=path)


def _issue(name: str, path: str = "") -> ParameterRef:
    """Create an ISSUE source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.ISSUE, source_path=path)


def _user(name: str, path: str = "") -> ParameterRef:
    """Create a USER source parameter reference (from user profile)."""
    return ParameterRef(name=name, source=ParameterSource.USER, source_path=path or name)


def _conv(name: str, path: str = "") -> ParameterRef:
    """Create a CONVERSATION source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.CONVERSATION, source_path=path)


def _comp(name: str, path: str = "") -> ParameterRef:
    """Create a COMPUTED source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.COMPUTED, source_path=path)


@dataclass(frozen=True)
class TopicDefinition:
    """Definition of a topic and its configuration.

    Topics are routed to endpoints based on TopicType:
    - SINGLE_SHOT → /ai/execute or /ai/execute-async
    - CONVERSATION_COACHING → /ai/coaching/*

    endpoint_path and http_method are optional and only used for legacy routes.

    Attributes:
        topic_id: Topic identifier in DynamoDB (e.g., "alignment_check")
        topic_type: Type of topic (conversation_coaching, single_shot, measure_system)
        category: Grouping category for organization (enum)
        description: Human-readable description of topic purpose
        tier_level: Subscription tier required to access this topic
        response_model: Response model class name (e.g., "AlignmentAnalysisResponse")
        endpoint_path: API path (optional, for legacy routes only)
        http_method: HTTP method (optional, for legacy routes only)
        is_active: Whether topic is currently active and routable
        allowed_prompt_types: List of prompt types this topic can use
        parameter_refs: Parameter references with source info for this topic
        templates: Template S3 keys by type (for conversation topics)
        result_model: Pydantic model class name for extraction output (for conversation topics)
    """

    topic_id: str
    topic_type: TopicType
    category: TopicCategory
    description: str
    tier_level: TierLevel = TierLevel.FREE  # Default to FREE tier
    response_model: str = ""
    endpoint_path: str | None = None  # Optional for conversation topics
    http_method: str | None = None  # Optional for conversation topics
    is_active: bool = True
    allowed_prompt_types: tuple[PromptType, ...] = field(
        default_factory=lambda: (PromptType.SYSTEM, PromptType.USER)
    )
    parameter_refs: tuple[ParameterRef, ...] = field(default_factory=tuple)
    templates: dict[TemplateType, str] = field(default_factory=dict)  # S3 keys by template type
    result_model: str | None = None  # Pydantic model for extraction


# Central registry of all topics with their configurations
# Key format: topic_id (e.g., "website_scan", "niche_review", "core_values")
TOPIC_REGISTRY: dict[str, TopicDefinition] = {
    # ========== Section 1: Onboarding & Business Intelligence (4 endpoints) ==========
    "website_scan": TopicDefinition(
        topic_id="website_scan",
        endpoint_path="/website/scan",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="WebsiteScanResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="Scan a website and extract business information",
        is_active=True,
        parameter_refs=(
            _req("website_url"),  # Input from frontend (passed to retrieval method)
            _web("website_content"),  # Resolved by get_website_content
            _web("website_title"),  # Resolved by get_website_content
            _web("meta_description"),  # Resolved by get_website_content
        ),
    ),
    "onboarding_suggestions": TopicDefinition(
        topic_id="onboarding_suggestions",
        endpoint_path="/suggestions/onboarding",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="OnboardingSuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="Generate onboarding suggestions based on scanned website",
        is_active=True,
        parameter_refs=(
            _req("website_data"),
            _onb("business_context"),
        ),
    ),
    "onboarding_coaching": TopicDefinition(
        topic_id="onboarding_coaching",
        endpoint_path="/coaching/onboarding",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="OnboardingCoachingResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="AI coaching for onboarding process",
        is_active=True,
        parameter_refs=(
            _req("stage"),
            _conv("context"),
        ),
    ),
    "business_metrics": TopicDefinition(
        topic_id="business_metrics",
        endpoint_path="/multitenant/conversations/business-data",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="BusinessMetricsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="Retrieve business metrics and data for coaching context",
        is_active=True,
        parameter_refs=(
            _comp("tenant_id"),
            _comp("user_id"),
            _req("metrics_type"),
        ),
    ),
    # Onboarding Review Topics (accessed via /ai/execute unified endpoint)
    # current_value is optional - users can get suggestions without a draft
    "niche_review": TopicDefinition(
        topic_id="niche_review",
        endpoint_path=None,  # Uses unified /ai/execute endpoint
        http_method=None,  # Uses unified /ai/execute endpoint
        response_model="OnboardingReviewResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="Review and suggest variations for business niche",
        is_active=True,
        parameter_refs=(
            _opt_req("current_value"),
            _onb("onboarding_ica"),
            _onb("onboarding_value_proposition"),
            _onb("onboarding_products"),
            _onb("onboarding_business_name"),
        ),
    ),
    # current_value is optional - users can get suggestions without a draft
    "ica_review": TopicDefinition(
        topic_id="ica_review",
        endpoint_path=None,  # Uses unified /ai/execute endpoint
        http_method=None,  # Uses unified /ai/execute endpoint
        response_model="OnboardingReviewResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="Review and suggest variations for Ideal Client Avatar (ICA)",
        is_active=True,
        parameter_refs=(
            _opt_req("current_value"),
            _onb("onboarding_niche"),
            _onb("onboarding_value_proposition"),
            _onb("onboarding_products"),
            _onb("onboarding_business_name"),
        ),
    ),
    # current_value is optional - users can get suggestions without a draft
    "value_proposition_review": TopicDefinition(
        topic_id="value_proposition_review",
        endpoint_path=None,  # Uses unified /ai/execute endpoint
        http_method=None,  # Uses unified /ai/execute endpoint
        response_model="OnboardingReviewResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="Review and suggest variations for value proposition",
        is_active=True,
        parameter_refs=(
            _opt_req("current_value"),
            _onb("onboarding_niche"),
            _onb("onboarding_ica"),
            _onb("onboarding_products"),
            _onb("onboarding_business_name"),
        ),
    ),
    # ========== Section 2: Insights Generation (1 endpoint) ==========
    "insights_generation": TopicDefinition(
        topic_id="insights_generation",
        endpoint_path="/insights/generate",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="PaginatedInsightResponse",  # Returns PaginatedResponse[InsightResponse]
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.INSIGHTS,
        description="Generate leadership insights using KISS framework (Keep, Improve, Start, Stop) based on current business state, measures, and purpose alignment",
        is_active=True,
        parameter_refs=(
            # Optional filters for pagination and filtering
            _opt_req("page"),  # Page number (default: 1)
            _opt_req("page_size"),  # Items per page (default: 20)
            _opt_req("category"),  # Filter by category (strategy, operations, etc.)
            _opt_req("priority"),  # Filter by priority (critical, high, medium, low)
            _opt_req("status"),  # Filter by status (active, dismissed, etc.)
            # Auto-enriched business data for AI analysis
            _opt_req(
                "business_foundation"
            ),  # Complete foundation data (vision, purpose, values, etc.)
            _opt_req("goals"),  # All tenant goals with progress
            _opt_req("strategies"),  # All tenant strategies
            _opt_req("measures"),  # All measures/KPIs with progress
            _opt_req("actions"),  # All action items
            _opt_req("issues"),  # All open issues
        ),
    ),
    # ========== Section 4: Strategic Planning AI (5 endpoints) ==========
    "strategy_suggestions": TopicDefinition(
        topic_id="strategy_suggestions",
        endpoint_path="/coaching/strategy-suggestions",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="StrategySuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Generate strategic planning suggestions for a specific goal, including review of existing strategies",
        is_active=True,
        parameter_refs=(
            # Enrichment key (required in API request, NOT for templates):
            _req("goal_id"),  # Used by get_goal_by_id to fetch goal data
            # Template parameters (auto-enriched, FOR template use):
            _goal("goal_title"),  # Auto-enriched from goal
            _goal("goal_description"),  # Auto-enriched from goal
            _goal("goal_intent"),  # Auto-enriched from goal
            _onb("vision"),  # Auto-enriched from business_foundation
            _onb("purpose"),  # Auto-enriched from business_foundation
            _onb("core_values"),  # Auto-enriched from business_foundation
            _strategies("existing_strategies_for_goal"),  # Auto-enriched and formatted
            # Optional request parameters:
            _opt_req("business_context"),  # Optional: additional business context
            _opt_req("constraints"),  # Optional: constraints for strategy generation
        ),
    ),
    "measure_recommendations": TopicDefinition(
        topic_id="measure_recommendations",
        endpoint_path="/coaching/measure-recommendations",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="MeasureRecommendationsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Recommend catalog measures for a goal or strategy, with suggested owner assignment",
        is_active=True,
        parameter_refs=(
            _req("goal_id"),  # Required: goal_id or strategy_id
            _opt_req(
                "strategy_id"
            ),  # Optional: if provided, recommend measures for specific strategy
            _goal("goal"),  # Auto-enriched from goal_id
            _strategies(
                "strategies"
            ),  # Auto-enriched: all strategies (filter by goal_id in template)
            _onb("business_context"),  # Auto-enriched: business foundation
            _measures("existing_measures"),  # Auto-enriched: existing measures
            ParameterRef(
                name="measure_catalog",
                source=ParameterSource.MEASURES,
                source_path="measure_catalog",
            ),  # Auto-enriched: measure catalog
            ParameterRef(
                name="catalog_measures",
                source=ParameterSource.MEASURES,
                source_path="catalog_measures",
            ),  # Auto-enriched: catalog measures list
            ParameterRef(
                name="tenant_custom_measures",
                source=ParameterSource.MEASURES,
                source_path="tenant_custom_measures",
            ),  # Auto-enriched: tenant custom measures
            _people("roles"),  # Auto-enriched: all roles
            _people("positions"),  # Auto-enriched: all positions
            _people("people"),  # Auto-enriched: all people
        ),
    ),
    "alignment_check": TopicDefinition(
        topic_id="alignment_check",
        endpoint_path="/coaching/alignment-check",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="AlignmentCheckResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Calculate alignment score between goal and business foundation",
        is_active=True,
        parameter_refs=(
            # Enrichment key (required in API request, NOT for templates):
            _req("goal_id"),  # Used by get_goal_by_id to fetch goal data
            # Template parameters (auto-enriched, FOR template use):
            _goal("goalIntent"),  # Auto-enriched from goal
            _onb("businessName"),  # Auto-enriched from business_foundation
            _onb("vision"),  # Auto-enriched from business_foundation
            _onb("purpose"),  # Auto-enriched from business_foundation
            _onb("coreValues"),  # Auto-enriched from business_foundation
            _strategies("strategies_for_goal"),  # Auto-enriched and formatted
        ),
    ),
    "alignment_explanation": TopicDefinition(
        topic_id="alignment_explanation",
        endpoint_path="/coaching/alignment-explanation",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="AlignmentExplanationResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Explain alignment score calculation",
        is_active=True,
        parameter_refs=(
            _comp("alignment_score"),
            _goal("goal"),
            _onb("business_foundation"),
        ),
    ),
    "alignment_suggestions": TopicDefinition(
        topic_id="alignment_suggestions",
        endpoint_path="/coaching/alignment-suggestions",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="AlignmentSuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Suggest improvements to increase alignment",
        is_active=True,
        parameter_refs=(
            _comp("alignment_score"),
            _goal("goal"),
            _onb("business_foundation"),
        ),
    ),
    # ========== Section 5: Operations AI (9 endpoints) ==========
    "root_cause_suggestions": TopicDefinition(
        topic_id="root_cause_suggestions",
        endpoint_path="/operations/root-cause-suggestions",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="RootCauseSuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Suggest root causes for operational issues",
        is_active=True,
        parameter_refs=(
            _issue("issue"),
            _onb("context", "business_context"),
        ),
    ),
    "swot_analysis": TopicDefinition(
        topic_id="swot_analysis",
        endpoint_path="/operations/swot-analysis",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="SwotAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Generate SWOT analysis for operations",
        is_active=False,
        parameter_refs=(
            _req("subject"),
            _onb("context", "business_context"),
        ),
    ),
    "five_whys_questions": TopicDefinition(
        topic_id="five_whys_questions",
        endpoint_path="/operations/five-whys-questions",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="FiveWhysQuestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Generate Five Whys analysis questions",
        is_active=False,
        parameter_refs=(
            _issue("issue"),
            _req("depth"),
        ),
    ),
    "action_suggestions": TopicDefinition(
        topic_id="action_suggestions",
        endpoint_path="/operations/action-suggestions",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="ActionSuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Suggest actions for a goal or specific strategy",
        is_active=True,
        parameter_refs=(
            _req("goal_id"),  # Required: goal to generate actions for
            _opt_req(
                "strategy_id"
            ),  # Optional: if provided, generate actions for specific strategy only
            _goal("goal"),  # Auto-enriched from goal_id
            _strategy("strategy"),  # Auto-enriched from strategy_id (if provided)
            _strategies("strategies"),  # Auto-enriched: all strategies for goal
            _onb("business_foundation"),  # Auto-enriched: business foundation
        ),
    ),
    "optimize_action_plan": TopicDefinition(
        topic_id="optimize_action_plan",
        endpoint_path="/operations/optimize-action-plan",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="OptimizedActionPlanResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Optimize action plan for better execution",
        is_active=True,
        parameter_refs=(
            _req("current_plan"),
            _req("optimization_goals"),
        ),
    ),
    "prioritization_suggestions": TopicDefinition(
        topic_id="prioritization_suggestions",
        endpoint_path="/operations/prioritization-suggestions",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="PrioritizationSuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Suggest prioritization of operational tasks",
        is_active=True,
        parameter_refs=(
            _req("tasks"),
            _req("criteria"),
        ),
    ),
    "scheduling_suggestions": TopicDefinition(
        topic_id="scheduling_suggestions",
        endpoint_path="/operations/scheduling-suggestions",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="SchedulingSuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Suggest optimal scheduling for tasks",
        is_active=True,
        parameter_refs=(
            _req("tasks"),
            _req("resources"),
            _req("constraints"),
        ),
    ),
    "categorize_issue": TopicDefinition(
        topic_id="categorize_issue",
        endpoint_path="/operations/categorize-issue",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="IssueCategoryResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Categorize operational issue by type and severity",
        is_active=False,
        parameter_refs=(_issue("issue"),),
    ),
    "assess_impact": TopicDefinition(
        topic_id="assess_impact",
        endpoint_path="/operations/assess-impact",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="ImpactAssessmentResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Assess business impact of operational issue",
        is_active=False,
        parameter_refs=(
            _issue("issue"),
            _onb("business_context"),
        ),
    ),
    # ========== Section 6: Operations-Strategic Integration (22 endpoints) ==========
    "action_strategic_context": TopicDefinition(
        topic_id="action_strategic_context",
        endpoint_path="/operations/actions/{action_id}/strategic-context",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="ActionStrategicContextResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get strategic context for a specific action",
        is_active=False,
        parameter_refs=(
            _req("action_id"),
            _action("action_details"),
        ),
    ),
    "suggest_connections": TopicDefinition(
        topic_id="suggest_connections",
        endpoint_path="/operations/actions/suggest-connections",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="SuggestedConnectionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Suggest strategic connections for actions",
        is_active=False,
        parameter_refs=(
            _action("action"),
            _onb("strategic_context"),
        ),
    ),
    "update_connections": TopicDefinition(
        topic_id="update_connections",
        endpoint_path="/operations/actions/{action_id}/connections",  # Legacy route
        http_method="PUT",  # Legacy route
        response_model="UpdateConnectionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Update strategic connections for an action",
        is_active=False,
        parameter_refs=(
            _req("action_id"),
            _req("connections"),
        ),
    ),
    "create_issue_from_action": TopicDefinition(
        topic_id="create_issue_from_action",
        endpoint_path="/operations/issues/create-from-action",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CreateIssueResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Create an issue from an incomplete action",
        is_active=False,
        parameter_refs=(
            _action("action"),
            _onb("context", "business_context"),
        ),
    ),
    "create_action_from_issue": TopicDefinition(
        topic_id="create_action_from_issue",
        endpoint_path="/operations/actions/create-from-issue",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CreateActionResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Create action items from an issue",
        is_active=False,
        parameter_refs=(
            _issue("issue"),
            _req("action_data"),
        ),
    ),
    "complete_action": TopicDefinition(
        topic_id="complete_action",
        endpoint_path="/operations/actions/{action_id}/complete",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CompleteActionResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Complete an action and update related items",
        is_active=False,
        parameter_refs=(
            _req("action_id"),
            _req("completion_data"),
        ),
    ),
    "close_issue": TopicDefinition(
        topic_id="close_issue",
        endpoint_path="/operations/issues/{issue_id}/close",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CloseIssueResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Close an issue and update related items",
        is_active=False,
        parameter_refs=(
            _req("issue_id"),
            _req("closure_data"),
        ),
    ),
    "issue_status": TopicDefinition(
        topic_id="issue_status",
        endpoint_path="/operations/issues/{issue_id}/status",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="IssueStatusResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get comprehensive status of an issue",
        is_active=False,
        parameter_refs=(
            _req("issue_id"),
            _issue("issue_status", "status"),
        ),
    ),
    "issue_related_actions": TopicDefinition(
        topic_id="issue_related_actions",
        endpoint_path="/operations/issues/{issue_id}/related-actions",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="RelatedActionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get actions related to an issue",
        is_active=False,
        parameter_refs=(
            _req("issue_id"),
            _issue("issue_details"),
        ),
    ),
    "update_measure": TopicDefinition(
        topic_id="update_measure",
        endpoint_path="/operations/measures/{measure_id}/update",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="UpdateMeasureResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Update a measure value with audit trail",
        is_active=False,
        parameter_refs=(
            _req("measure_id"),
            _req("update_data"),
        ),
    ),
    "calculate_measure": TopicDefinition(
        topic_id="calculate_measure",
        endpoint_path="/operations/measures/{measure_id}/calculate",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CalculateMeasureResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Calculate measure value from linked data",
        is_active=False,
        parameter_refs=(
            _req("measure_id"),
            _measure("measure_id", "id"),
        ),
    ),
    "measure_history": TopicDefinition(
        topic_id="measure_history",
        endpoint_path="/operations/measures/{measure_id}/history",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="MeasureHistoryResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get historical values for a measure",
        is_active=False,
        parameter_refs=(
            _req("measure_id"),
            _req("time_range"),
        ),
    ),
    "measure_impact": TopicDefinition(
        topic_id="measure_impact",
        endpoint_path="/operations/measures/{measure_id}/impact",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="MeasureImpactResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Analyze measure impact on strategic goals",
        is_active=False,
        parameter_refs=(
            _req("measure_id"),
            _measures("related_measures"),
        ),
    ),
    "action_measure_impact": TopicDefinition(
        topic_id="action_measure_impact",
        endpoint_path="/operations/actions/{action_id}/measure-impact",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="ActionMeasureImpactResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Calculate impact of action completion on measures",
        is_active=False,
        parameter_refs=(
            _req("action_id"),
            _action("action_details"),
            _measures("related_measures"),
        ),
    ),
    "sync_measures_to_strategy": TopicDefinition(
        topic_id="sync_measures_to_strategy",
        endpoint_path="/operations/measures/sync-to-strategy",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="SyncMeasuresResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Sync operational measures to strategic planning",
        is_active=False,
        parameter_refs=(
            _req("measure_updates"),
            _onb("strategy"),
        ),
    ),
    "detect_measure_conflicts": TopicDefinition(
        topic_id="detect_measure_conflicts",
        endpoint_path="/operations/measures/detect-conflicts",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="MeasureConflictsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Detect conflicts between operational and strategic measures",
        is_active=False,
        parameter_refs=(
            _measures("operational_measures"),
            _measures("strategic_measures"),
        ),
    ),
    "resolve_measure_conflict": TopicDefinition(
        topic_id="resolve_measure_conflict",
        endpoint_path="/operations/measures/resolve-conflict",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="ResolveConflictResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Resolve a detected measure conflict",
        is_active=False,
        parameter_refs=(
            _req("conflict_id"),
            _req("conflict_details"),
        ),
    ),
    "operations_strategic_alignment": TopicDefinition(
        topic_id="operations_strategic_alignment",
        endpoint_path="/operations/strategic-alignment",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="StrategicAlignmentResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get alignment status between operations and strategy",
        is_active=False,
        parameter_refs=(
            _onb("strategy"),
            _onb("operations"),
        ),
    ),
    "cascade_action_update": TopicDefinition(
        topic_id="cascade_action_update",
        endpoint_path="/operations/actions/cascade-update",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CascadeUpdateResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Cascade action updates to related items",
        is_active=False,
        parameter_refs=(
            _req("action_id"),
            _req("update_data"),
        ),
    ),
    "cascade_issue_update": TopicDefinition(
        topic_id="cascade_issue_update",
        endpoint_path="/operations/issues/cascade-update",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CascadeUpdateResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Cascade issue updates to related items",
        is_active=False,
        parameter_refs=(
            _req("issue_id"),
            _req("update_data"),
        ),
    ),
    "cascade_measure_update": TopicDefinition(
        topic_id="cascade_measure_update",
        endpoint_path="/operations/measures/{measure_id}/cascade-update",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="CascadeUpdateResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Cascade measure updates to related strategic items",
        is_active=False,
        parameter_refs=(
            _req("measure_id"),
            _req("update_value"),
        ),
    ),
    # ========== Section 7: Analysis Endpoints (4 endpoints) ==========
    "topic_strategic_context": TopicDefinition(
        topic_id="topic_strategic_context",
        endpoint_path="/admin/topics/{topic_id}/strategic-context",  # Legacy route
        http_method="GET",  # Legacy route
        response_model="TopicStrategicContextResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Get strategic context for admin topic management",
        is_active=False,
        parameter_refs=(
            _req("topic"),
            _req("context_type"),
        ),
    ),
    "alignment_analysis": TopicDefinition(
        topic_id="alignment_analysis",
        endpoint_path="/analysis/goal-alignment",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="GoalAlignmentResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Analyze goal alignment with business foundation",
        is_active=True,
        parameter_refs=(
            _goal("goal"),
            _onb("business_foundation"),
        ),
    ),
    "measure_analysis": TopicDefinition(
        topic_id="measure_analysis",
        endpoint_path="/analysis/measure-performance",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="MeasurePerformanceResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Analyze measure performance trends",
        is_active=True,
        parameter_refs=(
            _measures("measures"),
            _req("performance_data"),
        ),
    ),
    "operations_analysis": TopicDefinition(
        topic_id="operations_analysis",
        endpoint_path="/analysis/operations",  # Legacy route
        http_method="POST",  # Legacy route
        response_model="OperationsAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Perform operational analysis (SWOT, root cause, etc.)",
        is_active=True,
        parameter_refs=(
            _req("operations_data"),
            _req("analysis_type"),
        ),
    ),
    # ========== Section 8: Coaching Conversations (3 endpoints) ==========
    # Multi-turn coaching conversations with session management.
    # These use the generic coaching engine with conversation_config settings.
    "core_values": TopicDefinition(
        topic_id="core_values",
        endpoint_path=None,  # Uses unified /ai/coaching endpoint
        http_method=None,  # Uses unified /ai/coaching endpoint
        response_model="CoreValuesResult",
        topic_type=TopicType.CONVERSATION_COACHING,
        category=TopicCategory.ONBOARDING,
        description="Discover and articulate your organization's authentic core values through guided coaching.",
        is_active=True,
        allowed_prompt_types=(
            PromptType.SYSTEM,
            PromptType.INITIATION,
            PromptType.RESUME,
            PromptType.EXTRACTION,
        ),
        # Core values are personal beliefs - minimal context needed
        # user_name from user profile, company_name optional from onboarding
        parameter_refs=(
            _user("user_name"),
            _onb("company_name", "company_name"),
        ),
    ),
    "purpose": TopicDefinition(
        topic_id="purpose",
        endpoint_path=None,  # Uses unified /ai/coaching endpoint
        http_method=None,  # Uses unified /ai/coaching endpoint
        response_model="PurposeResult",
        topic_type=TopicType.CONVERSATION_COACHING,
        category=TopicCategory.ONBOARDING,
        description="Define your organization's deeper purpose and reason for existing through guided coaching.",
        is_active=True,
        allowed_prompt_types=(
            PromptType.SYSTEM,
            PromptType.INITIATION,
            PromptType.RESUME,
            PromptType.EXTRACTION,
        ),
        # Purpose needs business context and core values (if completed)
        parameter_refs=(
            _user("user_name"),
            _onb("company_name", "company_name"),
            _onb("core_values", "core_values"),
            _onb("onboarding_niche", "onboarding_niche"),
            _onb("onboarding_ica", "onboarding_ica"),
            _onb("onboarding_value_proposition", "onboarding_value_proposition"),
            _onb("onboarding_products", "onboarding_products"),
        ),
    ),
    "vision": TopicDefinition(
        topic_id="vision",
        endpoint_path=None,  # Uses unified /ai/coaching endpoint
        http_method=None,  # Uses unified /ai/coaching endpoint
        response_model="VisionResult",
        topic_type=TopicType.CONVERSATION_COACHING,
        category=TopicCategory.ONBOARDING,
        description="Craft a compelling vision for your organization's future through guided coaching.",
        is_active=True,
        allowed_prompt_types=(
            PromptType.SYSTEM,
            PromptType.INITIATION,
            PromptType.RESUME,
            PromptType.EXTRACTION,
        ),
        # Vision builds on values and purpose, needs full foundation context
        parameter_refs=(
            _req("user_name"),
            _onb("company_name", "company_name"),
            _onb("core_values", "core_values"),
            _onb("purpose", "purpose"),  # Updated from mission_statement
            _onb("onboarding_niche", "onboarding_niche"),
            _onb("onboarding_ica", "onboarding_ica"),
            _onb("onboarding_value_proposition", "onboarding_value_proposition"),
            _onb("onboarding_products", "onboarding_products"),
        ),
    ),
}


# =============================================================================
# TOPIC INDEX - O(1) lookup by topic_id
# =============================================================================

# Build reverse index: topic_id -> endpoint_key for O(1) lookup
# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_endpoint_definition(method: str, path: str) -> TopicDefinition | None:
    """Get topic definition by endpoint path (for legacy routes only).

    This function only works for topics that have endpoint_path and http_method set.
    Unified endpoints (/ai/execute, /ai/coaching/*) don't use this.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: Endpoint path (e.g., "/coaching/alignment-check")

    Returns:
        TopicDefinition if found, None otherwise
    """
    method_upper = method.upper()
    for topic in TOPIC_REGISTRY.values():
        if topic.endpoint_path == path and topic.http_method == method_upper:
            return topic
    return None


def list_topics_by_category(category: TopicCategory) -> list[TopicDefinition]:
    """Get all topics in a specific category.

    Args:
        category: TopicCategory enum value

    Returns:
        List of TopicDefinition objects in the category
    """
    return [topic for topic in TOPIC_REGISTRY.values() if topic.category == category]


def list_topics_by_topic_type(topic_type: TopicType) -> list[TopicDefinition]:
    """Get all topics of a specific topic type.

    Args:
        topic_type: TopicType enum value

    Returns:
        List of TopicDefinition objects of that type
    """
    return [topic for topic in TOPIC_REGISTRY.values() if topic.topic_type == topic_type]


def list_all_topics(active_only: bool = True) -> list[TopicDefinition]:
    """Get all registered topics.

    Args:
        active_only: If True, only return active topics

    Returns:
        List of all TopicDefinition objects
    """
    topics = list(TOPIC_REGISTRY.values())
    if active_only:
        topics = [t for t in topics if t.is_active]
    return topics


def get_response_model_name_for_topic(topic_id: str) -> str | None:
    """Get the response model name for a topic.

    Args:
        topic_id: Topic identifier

    Returns:
        Response model name string if found, None otherwise
    """
    topic = get_topic_by_topic_id(topic_id)
    if topic is None:
        return None
    return topic.response_model


def get_topic_for_endpoint(method: str, path: str) -> str | None:
    """Get topic ID for an endpoint.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: Endpoint path

    Returns:
        Topic ID string if found, None otherwise
    """
    endpoint = get_endpoint_definition(method, path)
    return endpoint.topic_id if endpoint else None


def get_topic_by_topic_id(topic_id: str) -> TopicDefinition | None:
    """Get topic definition by topic_id (O(1) lookup).

    Args:
        topic_id: Topic identifier

    Returns:
        TopicDefinition if found, None otherwise
    """
    return TOPIC_REGISTRY.get(topic_id)


def get_parameter_refs_for_topic(topic_id: str) -> tuple[ParameterRef, ...]:
    """Get parameter references for a topic.

    Args:
        topic_id: Topic identifier

    Returns:
        Tuple of ParameterRef objects, empty tuple if topic not found
    """
    topic = get_topic_by_topic_id(topic_id)
    if topic is None:
        return ()
    return topic.parameter_refs


def get_required_parameter_names_for_topic(topic_id: str) -> set[str]:
    """Get names of required parameters for a topic.

    A parameter is required if its ParameterRef.required is True,
    or if required is None and source is REQUEST (request params default to required).

    Args:
        topic_id: Topic identifier

    Returns:
        Set of required parameter names, empty set if topic not found
    """
    param_refs = get_parameter_refs_for_topic(topic_id)
    required_names: set[str] = set()

    for ref in param_refs:
        # If explicitly set, use that
        if ref.required is True or (ref.required is None and ref.source == ParameterSource.REQUEST):
            required_names.add(ref.name)

    return required_names


def get_parameters_for_topic(
    topic_id: str, *, include_enrichment_keys: bool = False
) -> list[ParameterInfo]:
    """Get basic parameter info for a topic (for API responses).

    Returns parameter definitions with basic info only (name, type, required, description).
    This is used for GET /admin/topics responses where full retrieval details are not needed.

    By default, excludes enrichment keys (REQUEST source params with no retrieval_method)
    which are required in API payloads but not used in templates.

    Args:
        topic_id: Topic identifier
        include_enrichment_keys: If True, include REQUEST params without retrieval_method.
            Default False for admin UI (template designers don't need to see enrichment keys).

    Returns:
        List of ParameterInfo dicts with name, type, required, description.
        Empty list if topic not found.
    """
    from coaching.src.core.parameter_registry import PARAMETER_REGISTRY

    param_refs = get_parameter_refs_for_topic(topic_id)
    required_names = get_required_parameter_names_for_topic(topic_id)

    result: list[ParameterInfo] = []
    for ref in param_refs:
        param_def = PARAMETER_REGISTRY.get(ref.name)

        # Filter out enrichment keys unless explicitly requested
        if not include_enrichment_keys:
            # Enrichment keys are REQUIRED REQUEST params with no retrieval_method
            # Optional REQUEST params (business_context, constraints) are for templates
            is_required = ref.name in required_names
            if (
                ref.source == ParameterSource.REQUEST
                and param_def
                and not param_def.retrieval_method
                and is_required
            ):
                continue  # Skip enrichment keys like goal_id, url, measure_id

        if param_def:
            result.append(
                ParameterInfo(
                    name=param_def.name,
                    type=param_def.param_type.value,
                    required=ref.name in required_names,
                    description=param_def.description,
                )
            )
        else:
            # Parameter not in registry - include with minimal info
            result.append(
                ParameterInfo(
                    name=ref.name,
                    type="string",
                    required=ref.name in required_names,
                    description="",
                )
            )

    return result


def get_parameters_by_source_for_endpoint(
    endpoint: TopicDefinition,
) -> dict[ParameterSource, list[ParameterRef]]:
    """Group an endpoint's parameters by their source.

    This enables efficient batch retrieval - one API call per source.

    Args:
        endpoint: TopicDefinition to process

    Returns:
        Dict mapping source to list of ParameterRef objects
    """
    result: dict[ParameterSource, list[ParameterRef]] = {}
    for param_ref in endpoint.parameter_refs:
        if param_ref.source not in result:
            result[param_ref.source] = []
        result[param_ref.source].append(param_ref)
    return result


def validate_registry() -> dict[str, list[str]]:
    """Validate the endpoint registry for consistency.

    Returns:
        Dictionary with validation results:
            - duplicate_topics: List of topic IDs used by multiple endpoints
            - invalid_methods: List of invalid HTTP methods
            - missing_descriptions: List of endpoints without descriptions
            - invalid_parameters: List of parameter refs not in PARAMETER_REGISTRY
    """
    from coaching.src.core.parameter_registry import PARAMETER_REGISTRY

    validation_results: dict[str, list[str]] = {
        "duplicate_topics": [],
        "invalid_methods": [],
        "missing_descriptions": [],
        "invalid_parameters": [],
    }

    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH"}
    topic_usage: dict[str, list[str]] = {}

    for key, endpoint in TOPIC_REGISTRY.items():
        # Check for duplicate topic usage (conversation topics can be reused)
        if endpoint.topic_type != TopicType.CONVERSATION_COACHING:
            if endpoint.topic_id in topic_usage:
                topic_usage[endpoint.topic_id].append(key)
            else:
                topic_usage[endpoint.topic_id] = [key]

        # Check for invalid HTTP methods (only if http_method is set)
        if endpoint.http_method and endpoint.http_method.upper() not in valid_methods:
            validation_results["invalid_methods"].append(f"{key}: {endpoint.http_method}")

        # Check for missing descriptions
        if not endpoint.description or len(endpoint.description.strip()) < 10:
            validation_results["missing_descriptions"].append(key)

        # Check for invalid parameter references
        for param_ref in endpoint.parameter_refs:
            if param_ref.name not in PARAMETER_REGISTRY:
                validation_results["invalid_parameters"].append(
                    f"{key}: {param_ref.name} not in PARAMETER_REGISTRY"
                )

    # Find duplicate topics
    validation_results["duplicate_topics"] = [
        f"{topic_id}: {', '.join(keys)}" for topic_id, keys in topic_usage.items() if len(keys) > 1
    ]

    return validation_results


def get_registry_statistics() -> dict[str, int]:
    """Get statistics about the endpoint registry.

    Returns:
        Dictionary with statistics:
            - total_endpoints: Total number of registered endpoints
            - active_endpoints: Number of active endpoints
            - inactive_endpoints: Number of inactive endpoints
            - conversation_endpoints: Number of conversation-based endpoints
            - single_shot_endpoints: Number of single-shot endpoints
            - measure_system_endpoints: Number of measure system endpoints
            - endpoints_by_category: Count per category
    """
    all_endpoints = list_all_topics(active_only=False)
    active_endpoints = [e for e in all_endpoints if e.is_active]
    inactive_endpoints = [e for e in all_endpoints if not e.is_active]
    conversation_endpoints = [
        e for e in all_endpoints if e.topic_type == TopicType.CONVERSATION_COACHING
    ]
    single_shot_endpoints = [e for e in all_endpoints if e.topic_type == TopicType.SINGLE_SHOT]
    measure_system_endpoints = [
        e for e in all_endpoints if e.topic_type == TopicType.MEASURE_SYSTEM
    ]

    categories: dict[str, int] = {}
    for endpoint in all_endpoints:
        cat_value = endpoint.category.value
        categories[cat_value] = categories.get(cat_value, 0) + 1

    return {
        "total_endpoints": len(all_endpoints),
        "active_endpoints": len(active_endpoints),
        "inactive_endpoints": len(inactive_endpoints),
        "conversation_endpoints": len(conversation_endpoints),
        "single_shot_endpoints": len(single_shot_endpoints),
        "measure_system_endpoints": len(measure_system_endpoints),
        **{f"category_{cat}": count for cat, count in categories.items()},
    }


# Backwards compatibility alias
ENDPOINT_REGISTRY = TOPIC_REGISTRY


__all__: list[str] = [
    "ENDPOINT_REGISTRY",  # Backwards compatibility
    "TOPIC_REGISTRY",
    "ParameterInfo",
    "ParameterRef",
    "TemplateType",
    "TopicDefinition",
    "TopicType",
    "get_endpoint_definition",
    "get_parameter_refs_for_topic",
    "get_parameters_by_source_for_endpoint",
    "get_parameters_for_topic",
    "get_registry_statistics",
    "get_required_parameter_names_for_topic",
    "get_response_model_name_for_topic",
    "get_topic_by_topic_id",
    "get_topic_for_endpoint",
    "list_all_topics",
    "list_topics_by_category",
    "list_topics_by_topic_type",
    "validate_registry",
]
