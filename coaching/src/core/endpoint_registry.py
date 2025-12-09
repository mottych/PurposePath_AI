"""Endpoint Registry - Central mapping of all API endpoints to topic configurations.

This module provides the definitive mapping between HTTP endpoints and their
corresponding LLM topic configurations, enabling a unified, topic-driven
architecture where endpoint behavior is configured through topic metadata
rather than hardcoded service classes.

Parameter source information is defined here per-endpoint since the same
parameter may come from different sources depending on the endpoint context.
"""

from dataclasses import dataclass, field
from typing import TypedDict

from coaching.src.core.constants import ParameterSource, PromptType, TopicCategory, TopicType


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
    """Create a REQUEST source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.REQUEST, source_path=path or name)


def _onb(name: str, path: str = "") -> ParameterRef:
    """Create an ONBOARDING source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.ONBOARDING, source_path=path or name)


def _goal(name: str, path: str = "") -> ParameterRef:
    """Create a GOAL source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.GOAL, source_path=path)


def _goals(name: str, path: str = "") -> ParameterRef:
    """Create a GOALS source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.GOALS, source_path=path)


def _kpi(name: str, path: str = "") -> ParameterRef:
    """Create a KPI source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.KPI, source_path=path)


def _kpis(name: str, path: str = "") -> ParameterRef:
    """Create a KPIS source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.KPIS, source_path=path)


def _action(name: str, path: str = "") -> ParameterRef:
    """Create an ACTION source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.ACTION, source_path=path)


def _issue(name: str, path: str = "") -> ParameterRef:
    """Create an ISSUE source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.ISSUE, source_path=path)


def _conv(name: str, path: str = "") -> ParameterRef:
    """Create a CONVERSATION source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.CONVERSATION, source_path=path)


def _comp(name: str, path: str = "") -> ParameterRef:
    """Create a COMPUTED source parameter reference."""
    return ParameterRef(name=name, source=ParameterSource.COMPUTED, source_path=path)


@dataclass(frozen=True)
class EndpointDefinition:
    """Definition of an API endpoint and its topic configuration.

    Attributes:
        endpoint_path: API path (e.g., "/coaching/alignment-check")
        http_method: HTTP method ("GET", "POST", "PUT", "DELETE")
        topic_id: Topic identifier in DynamoDB (e.g., "alignment_check")
        response_model: Response model class name (e.g., "AlignmentAnalysisResponse")
        topic_type: Type of topic (conversation_coaching, single_shot, kpi_system)
        category: Grouping category for organization (enum)
        description: Human-readable description of endpoint purpose
        is_active: Whether endpoint is currently active and routable
        allowed_prompt_types: List of prompt types this endpoint can use
        parameter_refs: Parameter references with source info for this endpoint
    """

    endpoint_path: str
    http_method: str
    topic_id: str
    response_model: str
    topic_type: TopicType
    category: TopicCategory
    description: str
    is_active: bool = True
    allowed_prompt_types: tuple[PromptType, ...] = field(
        default_factory=lambda: (PromptType.SYSTEM, PromptType.USER)
    )
    parameter_refs: tuple[ParameterRef, ...] = field(default_factory=tuple)


# Central registry of all endpoints mapped to topics
# Key format: "{HTTP_METHOD}:{path}"
ENDPOINT_REGISTRY: dict[str, EndpointDefinition] = {
    # ========== Section 1: Onboarding & Business Intelligence (4 endpoints) ==========
    "POST:/website/scan": EndpointDefinition(
        endpoint_path="/website/scan",
        http_method="POST",
        topic_id="website_scan",
        response_model="WebsiteScanResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ONBOARDING,
        description="Scan a website and extract business information",
        is_active=True,
        parameter_refs=(
            _req("url"),
            _req("scan_depth"),
        ),
    ),
    "POST:/suggestions/onboarding": EndpointDefinition(
        endpoint_path="/suggestions/onboarding",
        http_method="POST",
        topic_id="onboarding_suggestions",
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
    "POST:/coaching/onboarding": EndpointDefinition(
        endpoint_path="/coaching/onboarding",
        http_method="POST",
        topic_id="onboarding_coaching",
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
    "GET:/multitenant/conversations/business-data": EndpointDefinition(
        endpoint_path="/multitenant/conversations/business-data",
        http_method="GET",
        topic_id="business_metrics",
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
    # ========== Section 2: Conversation API (3 endpoints) ==========
    "POST:/conversations/initiate": EndpointDefinition(
        endpoint_path="/conversations/initiate",
        http_method="POST",
        topic_id="conversation_initiate",
        response_model="ConversationResponse",
        topic_type=TopicType.CONVERSATION_COACHING,
        category=TopicCategory.CONVERSATION,
        description="Initiate a new coaching conversation",
        is_active=True,
        parameter_refs=(
            _req("topic"),
            _onb("context", "business_context"),
        ),
    ),
    "POST:/conversations/{conversation_id}/message": EndpointDefinition(
        endpoint_path="/conversations/{conversation_id}/message",
        http_method="POST",
        topic_id="conversation_message",
        response_model="MessageResponse",
        topic_type=TopicType.CONVERSATION_COACHING,
        category=TopicCategory.CONVERSATION,
        description="Send a message in an active conversation",
        is_active=True,
        parameter_refs=(
            _conv("conversation_history", "messages"),
            _req("user_message"),
            _conv("context"),
        ),
    ),
    "GET:/conversations/{conversation_id}": EndpointDefinition(
        endpoint_path="/conversations/{conversation_id}",
        http_method="GET",
        topic_id="conversation_retrieve",
        response_model="ConversationResponse",
        topic_type=TopicType.CONVERSATION_COACHING,
        category=TopicCategory.CONVERSATION,
        description="Retrieve conversation details and history",
        is_active=True,
        parameter_refs=(
            _conv("conversation_id", "id"),
            _req("include_summary"),
        ),
    ),
    # ========== Section 3: Insights Generation (1 endpoint) ==========
    "POST:/insights/generate": EndpointDefinition(
        endpoint_path="/insights/generate",
        http_method="POST",
        topic_id="insights_generation",
        response_model="InsightsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.INSIGHTS,
        description="Generate business insights from coaching data",
        is_active=True,
        parameter_refs=(
            _req("data_sources"),
            _req("insight_types"),
            _req("time_range"),
        ),
    ),
    # ========== Section 4: Strategic Planning AI (5 endpoints) ==========
    "POST:/coaching/strategy-suggestions": EndpointDefinition(
        endpoint_path="/coaching/strategy-suggestions",
        http_method="POST",
        topic_id="strategy_suggestions",
        response_model="StrategySuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Generate strategic planning suggestions",
        is_active=True,
        parameter_refs=(
            _onb("business_foundation"),
            _onb("current_strategy"),
            _req("market_context"),
        ),
    ),
    "POST:/coaching/kpi-recommendations": EndpointDefinition(
        endpoint_path="/coaching/kpi-recommendations",
        http_method="POST",
        topic_id="kpi_recommendations",
        response_model="KPIRecommendationsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Recommend KPIs based on business goals",
        is_active=True,
        parameter_refs=(
            _goals("goals"),
            _onb("business_context"),
            _kpis("existing_kpis"),
        ),
    ),
    "POST:/coaching/alignment-check": EndpointDefinition(
        endpoint_path="/coaching/alignment-check",
        http_method="POST",
        topic_id="alignment_check",
        response_model="AlignmentAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.STRATEGIC_PLANNING,
        description="Calculate alignment score between goal and business foundation",
        is_active=True,
        parameter_refs=(
            _goal("goal"),
            _onb("business_foundation"),
        ),
    ),
    "POST:/coaching/alignment-explanation": EndpointDefinition(
        endpoint_path="/coaching/alignment-explanation",
        http_method="POST",
        topic_id="alignment_explanation",
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
    "POST:/coaching/alignment-suggestions": EndpointDefinition(
        endpoint_path="/coaching/alignment-suggestions",
        http_method="POST",
        topic_id="alignment_suggestions",
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
    "POST:/operations/root-cause-suggestions": EndpointDefinition(
        endpoint_path="/operations/root-cause-suggestions",
        http_method="POST",
        topic_id="root_cause_suggestions",
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
    "POST:/operations/swot-analysis": EndpointDefinition(
        endpoint_path="/operations/swot-analysis",
        http_method="POST",
        topic_id="swot_analysis",
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
    "POST:/operations/five-whys-questions": EndpointDefinition(
        endpoint_path="/operations/five-whys-questions",
        http_method="POST",
        topic_id="five_whys_questions",
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
    "POST:/operations/action-suggestions": EndpointDefinition(
        endpoint_path="/operations/action-suggestions",
        http_method="POST",
        topic_id="action_suggestions",
        response_model="ActionSuggestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Suggest actions to resolve operational issues",
        is_active=True,
        parameter_refs=(
            _issue("issue"),
            _issue("root_causes", "root_causes"),
            _req("constraints"),
        ),
    ),
    "POST:/operations/optimize-action-plan": EndpointDefinition(
        endpoint_path="/operations/optimize-action-plan",
        http_method="POST",
        topic_id="optimize_action_plan",
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
    "POST:/operations/prioritization-suggestions": EndpointDefinition(
        endpoint_path="/operations/prioritization-suggestions",
        http_method="POST",
        topic_id="prioritization_suggestions",
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
    "POST:/operations/scheduling-suggestions": EndpointDefinition(
        endpoint_path="/operations/scheduling-suggestions",
        http_method="POST",
        topic_id="scheduling_suggestions",
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
    "POST:/operations/categorize-issue": EndpointDefinition(
        endpoint_path="/operations/categorize-issue",
        http_method="POST",
        topic_id="categorize_issue",
        response_model="IssueCategoryResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Categorize operational issue by type and severity",
        is_active=False,
        parameter_refs=(_issue("issue"),),
    ),
    "POST:/operations/assess-impact": EndpointDefinition(
        endpoint_path="/operations/assess-impact",
        http_method="POST",
        topic_id="assess_impact",
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
    "GET:/operations/actions/{action_id}/strategic-context": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/strategic-context",
        http_method="GET",
        topic_id="action_strategic_context",
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
    "POST:/operations/actions/suggest-connections": EndpointDefinition(
        endpoint_path="/operations/actions/suggest-connections",
        http_method="POST",
        topic_id="suggest_connections",
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
    "PUT:/operations/actions/{action_id}/connections": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/connections",
        http_method="PUT",
        topic_id="update_connections",
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
    "POST:/operations/issues/create-from-action": EndpointDefinition(
        endpoint_path="/operations/issues/create-from-action",
        http_method="POST",
        topic_id="create_issue_from_action",
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
    "POST:/operations/actions/create-from-issue": EndpointDefinition(
        endpoint_path="/operations/actions/create-from-issue",
        http_method="POST",
        topic_id="create_action_from_issue",
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
    "POST:/operations/actions/{action_id}/complete": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/complete",
        http_method="POST",
        topic_id="complete_action",
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
    "POST:/operations/issues/{issue_id}/close": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/close",
        http_method="POST",
        topic_id="close_issue",
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
    "GET:/operations/issues/{issue_id}/status": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/status",
        http_method="GET",
        topic_id="issue_status",
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
    "GET:/operations/issues/{issue_id}/related-actions": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/related-actions",
        http_method="GET",
        topic_id="issue_related_actions",
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
    "POST:/operations/kpis/{kpi_id}/update": EndpointDefinition(
        endpoint_path="/operations/kpis/{kpi_id}/update",
        http_method="POST",
        topic_id="update_kpi",
        response_model="UpdateKPIResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Update a KPI value with audit trail",
        is_active=False,
        parameter_refs=(
            _req("kpi_id"),
            _req("update_data"),
        ),
    ),
    "POST:/operations/kpis/{kpi_id}/calculate": EndpointDefinition(
        endpoint_path="/operations/kpis/{kpi_id}/calculate",
        http_method="POST",
        topic_id="calculate_kpi",
        response_model="CalculateKPIResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Calculate KPI value from linked data",
        is_active=False,
        parameter_refs=(
            _req("kpi_id"),
            _kpi("kpi_id", "id"),
        ),
    ),
    "GET:/operations/kpis/{kpi_id}/history": EndpointDefinition(
        endpoint_path="/operations/kpis/{kpi_id}/history",
        http_method="GET",
        topic_id="kpi_history",
        response_model="KPIHistoryResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get historical values for a KPI",
        is_active=False,
        parameter_refs=(
            _req("kpi_id"),
            _req("time_range"),
        ),
    ),
    "GET:/operations/kpis/{kpi_id}/impact": EndpointDefinition(
        endpoint_path="/operations/kpis/{kpi_id}/impact",
        http_method="GET",
        topic_id="kpi_impact",
        response_model="KPIImpactResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Analyze KPI impact on strategic goals",
        is_active=False,
        parameter_refs=(
            _req("kpi_id"),
            _kpis("related_kpis"),
        ),
    ),
    "POST:/operations/actions/{action_id}/kpi-impact": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/kpi-impact",
        http_method="POST",
        topic_id="action_kpi_impact",
        response_model="ActionKPIImpactResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Calculate impact of action completion on KPIs",
        is_active=False,
        parameter_refs=(
            _req("action_id"),
            _action("action_details"),
            _kpis("related_kpis"),
        ),
    ),
    "POST:/operations/kpis/sync-to-strategy": EndpointDefinition(
        endpoint_path="/operations/kpis/sync-to-strategy",
        http_method="POST",
        topic_id="sync_kpis_to_strategy",
        response_model="SyncKPIsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Sync operational KPIs to strategic planning",
        is_active=False,
        parameter_refs=(
            _req("kpi_updates"),
            _onb("strategy"),
        ),
    ),
    "GET:/operations/kpis/detect-conflicts": EndpointDefinition(
        endpoint_path="/operations/kpis/detect-conflicts",
        http_method="GET",
        topic_id="detect_kpi_conflicts",
        response_model="KPIConflictsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Detect conflicts between operational and strategic KPIs",
        is_active=False,
        parameter_refs=(
            _kpis("operational_kpis"),
            _kpis("strategic_kpis"),
        ),
    ),
    "POST:/operations/kpis/resolve-conflict": EndpointDefinition(
        endpoint_path="/operations/kpis/resolve-conflict",
        http_method="POST",
        topic_id="resolve_kpi_conflict",
        response_model="ResolveConflictResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Resolve a detected KPI conflict",
        is_active=False,
        parameter_refs=(
            _req("conflict_id"),
            _req("conflict_details"),
        ),
    ),
    "GET:/operations/strategic-alignment": EndpointDefinition(
        endpoint_path="/operations/strategic-alignment",
        http_method="GET",
        topic_id="operations_strategic_alignment",
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
    "POST:/operations/actions/cascade-update": EndpointDefinition(
        endpoint_path="/operations/actions/cascade-update",
        http_method="POST",
        topic_id="cascade_action_update",
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
    "POST:/operations/issues/cascade-update": EndpointDefinition(
        endpoint_path="/operations/issues/cascade-update",
        http_method="POST",
        topic_id="cascade_issue_update",
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
    "POST:/operations/kpis/{kpi_id}/cascade-update": EndpointDefinition(
        endpoint_path="/operations/kpis/{kpi_id}/cascade-update",
        http_method="POST",
        topic_id="cascade_kpi_update",
        response_model="CascadeUpdateResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Cascade KPI updates to related strategic items",
        is_active=False,
        parameter_refs=(
            _req("kpi_id"),
            _req("update_value"),
        ),
    ),
    # ========== Section 7: Analysis Endpoints (4 endpoints) ==========
    "GET:/admin/topics/{topic_id}/strategic-context": EndpointDefinition(
        endpoint_path="/admin/topics/{topic_id}/strategic-context",
        http_method="GET",
        topic_id="topic_strategic_context",
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
    "POST:/analysis/goal-alignment": EndpointDefinition(
        endpoint_path="/analysis/goal-alignment",
        http_method="POST",
        topic_id="alignment_analysis",
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
    "POST:/analysis/kpi-performance": EndpointDefinition(
        endpoint_path="/analysis/kpi-performance",
        http_method="POST",
        topic_id="kpi_analysis",
        response_model="KPIPerformanceResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Analyze KPI performance trends",
        is_active=True,
        parameter_refs=(
            _kpis("kpis"),
            _req("performance_data"),
        ),
    ),
    "POST:/analysis/operations": EndpointDefinition(
        endpoint_path="/analysis/operations",
        http_method="POST",
        topic_id="operations_analysis",
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
}


# =============================================================================
# TOPIC INDEX - O(1) lookup by topic_id
# =============================================================================

# Build reverse index: topic_id -> endpoint_key for O(1) lookup
TOPIC_INDEX: dict[str, str] = {
    endpoint.topic_id: key for key, endpoint in ENDPOINT_REGISTRY.items()
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_endpoint_definition(method: str, path: str) -> EndpointDefinition | None:
    """Get endpoint definition by HTTP method and path.

    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        path: Endpoint path (e.g., "/coaching/alignment-check")

    Returns:
        EndpointDefinition if found, None otherwise
    """
    key = f"{method.upper()}:{path}"
    return ENDPOINT_REGISTRY.get(key)


def list_endpoints_by_category(category: TopicCategory) -> list[EndpointDefinition]:
    """Get all endpoints in a specific category.

    Args:
        category: TopicCategory enum value

    Returns:
        List of EndpointDefinition objects in the category
    """
    return [endpoint for endpoint in ENDPOINT_REGISTRY.values() if endpoint.category == category]


def list_endpoints_by_topic_type(topic_type: TopicType) -> list[EndpointDefinition]:
    """Get all endpoints of a specific topic type.

    Args:
        topic_type: TopicType enum value

    Returns:
        List of EndpointDefinition objects of that type
    """
    return [
        endpoint for endpoint in ENDPOINT_REGISTRY.values() if endpoint.topic_type == topic_type
    ]


def list_all_endpoints(active_only: bool = True) -> list[EndpointDefinition]:
    """Get all registered endpoints.

    Args:
        active_only: If True, only return active endpoints

    Returns:
        List of all EndpointDefinition objects
    """
    endpoints = list(ENDPOINT_REGISTRY.values())
    if active_only:
        endpoints = [e for e in endpoints if e.is_active]
    return endpoints


def get_response_model_name_for_topic(topic_id: str) -> str | None:
    """Get the response model name for a topic.

    Args:
        topic_id: Topic identifier

    Returns:
        Response model name string if found, None otherwise
    """
    endpoint = get_endpoint_by_topic_id(topic_id)
    if endpoint is None:
        return None
    return endpoint.response_model


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


def get_endpoint_by_topic_id(topic_id: str) -> EndpointDefinition | None:
    """Get endpoint definition by topic ID.

    Uses TOPIC_INDEX for O(1) lookup.

    Args:
        topic_id: Topic identifier

    Returns:
        EndpointDefinition if found, None otherwise
    """
    endpoint_key = TOPIC_INDEX.get(topic_id)
    if endpoint_key is None:
        return None
    return ENDPOINT_REGISTRY.get(endpoint_key)


def get_parameter_refs_for_topic(topic_id: str) -> tuple[ParameterRef, ...]:
    """Get parameter references for a topic.

    Args:
        topic_id: Topic identifier

    Returns:
        Tuple of ParameterRef objects, empty tuple if topic not found
    """
    endpoint = get_endpoint_by_topic_id(topic_id)
    if endpoint is None:
        return ()
    return endpoint.parameter_refs


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


def get_parameters_for_topic(topic_id: str) -> list[ParameterInfo]:
    """Get basic parameter info for a topic (for API responses).

    Returns parameter definitions with basic info only (name, type, required, description).
    This is used for GET /admin/topics responses where full retrieval details are not needed.

    Args:
        topic_id: Topic identifier

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
    endpoint: EndpointDefinition,
) -> dict[ParameterSource, list[ParameterRef]]:
    """Group an endpoint's parameters by their source.

    This enables efficient batch retrieval - one API call per source.

    Args:
        endpoint: EndpointDefinition to process

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

    for key, endpoint in ENDPOINT_REGISTRY.items():
        # Check for duplicate topic usage (conversation topics can be reused)
        if endpoint.topic_type != TopicType.CONVERSATION_COACHING:
            if endpoint.topic_id in topic_usage:
                topic_usage[endpoint.topic_id].append(key)
            else:
                topic_usage[endpoint.topic_id] = [key]

        # Check for invalid HTTP methods
        if endpoint.http_method.upper() not in valid_methods:
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
            - kpi_system_endpoints: Number of KPI system endpoints
            - endpoints_by_category: Count per category
    """
    all_endpoints = list_all_endpoints(active_only=False)
    active_endpoints = [e for e in all_endpoints if e.is_active]
    inactive_endpoints = [e for e in all_endpoints if not e.is_active]
    conversation_endpoints = [
        e for e in all_endpoints if e.topic_type == TopicType.CONVERSATION_COACHING
    ]
    single_shot_endpoints = [e for e in all_endpoints if e.topic_type == TopicType.SINGLE_SHOT]
    kpi_system_endpoints = [e for e in all_endpoints if e.topic_type == TopicType.KPI_SYSTEM]

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
        "kpi_system_endpoints": len(kpi_system_endpoints),
        **{f"category_{cat}": count for cat, count in categories.items()},
    }


__all__ = [
    "ENDPOINT_REGISTRY",
    "TOPIC_INDEX",
    "EndpointDefinition",
    "ParameterInfo",
    "ParameterRef",
    "get_endpoint_by_topic_id",
    "get_endpoint_definition",
    "get_parameter_refs_for_topic",
    "get_parameters_by_source_for_endpoint",
    "get_parameters_for_topic",
    "get_registry_statistics",
    "get_required_parameter_names_for_topic",
    "get_response_model_name_for_topic",
    "get_topic_for_endpoint",
    "list_all_endpoints",
    "list_endpoints_by_category",
    "list_endpoints_by_topic_type",
    "validate_registry",
]
