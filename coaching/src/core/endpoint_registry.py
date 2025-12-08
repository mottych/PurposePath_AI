"""Endpoint Registry - Central mapping of all API endpoints to topic configurations.

This module provides the definitive mapping between HTTP endpoints and their
corresponding LLM topic configurations, enabling a unified, topic-driven
architecture where endpoint behavior is configured through topic metadata
rather than hardcoded service classes.
"""

from dataclasses import dataclass, field

from coaching.src.core.constants import PromptType, TopicCategory, TopicType


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
        parameter_refs: List of parameter names this endpoint uses (references PARAMETER_REGISTRY)
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
    parameter_refs: tuple[str, ...] = field(default_factory=tuple)


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
        parameter_refs=("url", "scan_depth"),
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
        parameter_refs=("website_data", "business_context"),
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
        parameter_refs=("stage", "context"),
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
        parameter_refs=("tenant_id", "user_id", "metrics_type"),
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
        parameter_refs=("topic", "context"),
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
        parameter_refs=("conversation_history", "user_message", "context"),
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
        parameter_refs=("conversation_id", "include_summary"),
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
        parameter_refs=("data_sources", "insight_types", "time_range"),
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
        parameter_refs=("business_foundation", "current_strategy", "market_context"),
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
        parameter_refs=("goals", "business_context", "existing_kpis"),
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
        parameter_refs=("goal", "business_foundation"),
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
        parameter_refs=("alignment_score", "goal", "business_foundation"),
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
        parameter_refs=("alignment_score", "goal", "business_foundation"),
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
        parameter_refs=("issue", "context"),
    ),
    "POST:/operations/swot-analysis": EndpointDefinition(
        endpoint_path="/operations/swot-analysis",
        http_method="POST",
        topic_id="swot_analysis",
        response_model="SwotAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Generate SWOT analysis for operations",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("subject", "context"),
    ),
    "POST:/operations/five-whys-questions": EndpointDefinition(
        endpoint_path="/operations/five-whys-questions",
        http_method="POST",
        topic_id="five_whys_questions",
        response_model="FiveWhysQuestionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Generate Five Whys analysis questions",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue", "depth"),
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
        parameter_refs=("issue", "root_causes", "constraints"),
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
        parameter_refs=("current_plan", "optimization_goals"),
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
        parameter_refs=("tasks", "criteria"),
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
        parameter_refs=("tasks", "resources", "constraints"),
    ),
    "POST:/operations/categorize-issue": EndpointDefinition(
        endpoint_path="/operations/categorize-issue",
        http_method="POST",
        topic_id="categorize_issue",
        response_model="IssueCategoryResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Categorize operational issue by type and severity",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue",),
    ),
    "POST:/operations/assess-impact": EndpointDefinition(
        endpoint_path="/operations/assess-impact",
        http_method="POST",
        topic_id="assess_impact",
        response_model="ImpactAssessmentResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_AI,
        description="Assess business impact of operational issue",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue", "business_context"),
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
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action_id", "action_details"),
    ),
    "POST:/operations/actions/suggest-connections": EndpointDefinition(
        endpoint_path="/operations/actions/suggest-connections",
        http_method="POST",
        topic_id="suggest_connections",
        response_model="SuggestedConnectionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Suggest strategic connections for actions",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action", "strategic_context"),
    ),
    "PUT:/operations/actions/{action_id}/connections": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/connections",
        http_method="PUT",
        topic_id="update_connections",
        response_model="UpdateConnectionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Update strategic connections for an action",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action_id", "connections"),
    ),
    "POST:/operations/actions/analyze-kpi-impact": EndpointDefinition(
        endpoint_path="/operations/actions/analyze-kpi-impact",
        http_method="POST",
        topic_id="analyze_kpi_impact",
        response_model="KPIImpactAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Analyze KPI impact of proposed actions",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action", "kpis"),
    ),
    "POST:/operations/kpi-updates": EndpointDefinition(
        endpoint_path="/operations/kpi-updates",
        http_method="POST",
        topic_id="record_kpi_update",
        response_model="KPIUpdateResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Record a KPI update event",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("kpi_id", "update_data"),
    ),
    "GET:/operations/kpi-updates": EndpointDefinition(
        endpoint_path="/operations/kpi-updates",
        http_method="GET",
        topic_id="get_kpi_updates",
        response_model="KPIUpdateHistoryResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get KPI update history",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("kpi_id", "time_range"),
    ),
    "GET:/operations/issues/{issue_id}/strategic-context": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/strategic-context",
        http_method="GET",
        topic_id="issue_strategic_context",
        response_model="IssueStrategicContextResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get strategic context for an operational issue",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue_id", "issue_details"),
    ),
    "POST:/operations/issues/{issue_id}/generate-actions": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/generate-actions",
        http_method="POST",
        topic_id="generate_actions_from_issue",
        response_model="GeneratedActionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Generate strategic actions from operational issue",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue_id", "issue_details", "strategic_context"),
    ),
    "POST:/operations/strategic-alignment": EndpointDefinition(
        endpoint_path="/operations/strategic-alignment",
        http_method="POST",
        topic_id="operations_strategic_alignment",
        response_model="OperationsAlignmentResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Calculate strategic alignment of operations",
        is_active=True,  # Partially implemented
        parameter_refs=("operations", "strategy"),
    ),
    "POST:/operations/actions/{action_id}/complete": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/complete",
        http_method="POST",
        topic_id="complete_action",
        response_model="ActionCompletionResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Mark action as complete with strategic impact",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action_id", "completion_data"),
    ),
    "GET:/operations/actions/{action_id}/kpi-update-prompt": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/kpi-update-prompt",
        http_method="GET",
        topic_id="kpi_update_prompt",
        response_model="KPIUpdatePromptResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get prompt for KPI update after action completion",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action_id", "action_details", "related_kpis"),
    ),
    "POST:/operations/actions/{action_id}/update-kpi": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/update-kpi",
        http_method="POST",
        topic_id="update_kpi_from_action",
        response_model="KPIUpdateResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Update KPI based on action completion",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action_id", "kpi_id", "update_value"),
    ),
    "POST:/operations/issues/{issue_id}/convert-to-actions": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/convert-to-actions",
        http_method="POST",
        topic_id="convert_issue_to_actions",
        response_model="ConvertedActionsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Convert operational issue into actionable items",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue_id", "issue_details"),
    ),
    "GET:/operations/issues/{issue_id}/closure-eligibility": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/closure-eligibility",
        http_method="GET",
        topic_id="check_closure_eligibility",
        response_model="ClosureEligibilityResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Check if issue is eligible for closure",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue_id", "issue_status"),
    ),
    "POST:/operations/issues/{issue_id}/close": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/close",
        http_method="POST",
        topic_id="close_issue",
        response_model="IssueClosureResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Close operational issue with strategic impact assessment",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("issue_id", "closure_data"),
    ),
    "GET:/strategic/context": EndpointDefinition(
        endpoint_path="/strategic/context",
        http_method="GET",
        topic_id="strategic_context",
        response_model="StrategicContextResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get comprehensive strategic planning context",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("tenant_id", "context_type"),
    ),
    "POST:/operations/actions/create-with-context": EndpointDefinition(
        endpoint_path="/operations/actions/create-with-context",
        http_method="POST",
        topic_id="create_action_with_context",
        response_model="ActionCreationResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Create action with full strategic context",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action_data", "strategic_context"),
    ),
    "GET:/operations/actions/{action_id}/relationships": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/relationships",
        http_method="GET",
        topic_id="action_relationships",
        response_model="ActionRelationshipsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Get strategic relationships for an action",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("action_id",),
    ),
    "POST:/operations/kpi-sync/to-strategic-planning": EndpointDefinition(
        endpoint_path="/operations/kpi-sync/to-strategic-planning",
        http_method="POST",
        topic_id="kpi_sync_to_strategic",
        response_model="KPISyncResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Sync operational KPI updates to strategic planning",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("kpi_updates",),
    ),
    "POST:/operations/kpi-sync/from-strategic-planning": EndpointDefinition(
        endpoint_path="/operations/kpi-sync/from-strategic-planning",
        http_method="POST",
        topic_id="kpi_sync_from_strategic",
        response_model="KPISyncResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Sync strategic KPIs to operational tracking",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("strategic_kpis",),
    ),
    "GET:/operations/kpi-conflicts": EndpointDefinition(
        endpoint_path="/operations/kpi-conflicts",
        http_method="GET",
        topic_id="detect_kpi_conflicts",
        response_model="KPIConflictsResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Detect KPI conflicts between operations and strategy",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("operational_kpis", "strategic_kpis"),
    ),
    "POST:/operations/kpi-conflicts/{conflict_id}/resolve": EndpointDefinition(
        endpoint_path="/operations/kpi-conflicts/{conflict_id}/resolve",
        http_method="POST",
        topic_id="resolve_kpi_conflict",
        response_model="ConflictResolutionResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.OPERATIONS_STRATEGIC_INTEGRATION,
        description="Resolve KPI conflict with AI recommendations",
        is_active=False,  # Missing - needs implementation
        parameter_refs=("conflict_id", "conflict_details"),
    ),
    # ========== Section 7: Analysis API (4 endpoints) ==========
    "POST:/analysis/alignment": EndpointDefinition(
        endpoint_path="/analysis/alignment",
        http_method="POST",
        topic_id="alignment_analysis",
        response_model="AlignmentAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Analyze alignment between goals and purpose",
        is_active=True,
        parameter_refs=("goal", "business_foundation"),
    ),
    "POST:/analysis/strategy": EndpointDefinition(
        endpoint_path="/analysis/strategy",
        http_method="POST",
        topic_id="strategy_analysis",
        response_model="StrategyAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Analyze business strategy effectiveness",
        is_active=True,
        parameter_refs=("strategy", "context"),
    ),
    "POST:/analysis/kpi": EndpointDefinition(
        endpoint_path="/analysis/kpi",
        http_method="POST",
        topic_id="kpi_analysis",
        response_model="KPIAnalysisResponse",
        topic_type=TopicType.SINGLE_SHOT,
        category=TopicCategory.ANALYSIS,
        description="Analyze KPI effectiveness",
        is_active=True,
        parameter_refs=("kpis", "performance_data"),
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
        parameter_refs=("operations_data", "analysis_type"),
    ),
}


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

    Args:
        topic_id: Topic identifier

    Returns:
        EndpointDefinition if found, None otherwise
    """
    for endpoint in ENDPOINT_REGISTRY.values():
        if endpoint.topic_id == topic_id:
            return endpoint
    return None


def validate_registry() -> dict[str, list[str]]:
    """Validate the endpoint registry for consistency.

    Returns:
        Dictionary with validation results:
            - duplicate_topics: List of topic IDs used by multiple endpoints
            - invalid_methods: List of invalid HTTP methods
            - missing_descriptions: List of endpoints without descriptions
    """
    validation_results: dict[str, list[str]] = {
        "duplicate_topics": [],
        "invalid_methods": [],
        "missing_descriptions": [],
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

    # Find duplicate topics
    validation_results["duplicate_topics"] = [
        f"{topic_id}: {', '.join(keys)}" for topic_id, keys in topic_usage.items() if len(keys) > 1
    ]

    return validation_results


# Statistics
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
