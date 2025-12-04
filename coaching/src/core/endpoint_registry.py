"""Endpoint Registry - Central mapping of all API endpoints to topic configurations.

This module provides the definitive mapping between HTTP endpoints and their
corresponding LLM topic configurations, enabling a unified, topic-driven
architecture where endpoint behavior is configured through topic metadata
rather than hardcoded service classes.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointDefinition:
    """Definition of an API endpoint and its topic configuration.

    Attributes:
        endpoint_path: API path (e.g., "/coaching/alignment-check")
        http_method: HTTP method ("GET", "POST", "PUT", "DELETE")
        topic_id: Topic identifier in DynamoDB (e.g., "alignment_check")
        response_model: Response model class name (e.g., "AlignmentAnalysisResponse")
        requires_conversation: Whether endpoint uses conversation flow vs single-shot
        category: Grouping category for organization
        description: Human-readable description of endpoint purpose
        is_active: Whether endpoint is currently active and routable
    """

    endpoint_path: str
    http_method: str
    topic_id: str
    response_model: str
    requires_conversation: bool
    category: str
    description: str
    is_active: bool = True


# Central registry of all endpoints mapped to topics
# Key format: "{HTTP_METHOD}:{path}"
ENDPOINT_REGISTRY: dict[str, EndpointDefinition] = {
    # ========== Section 1: Onboarding & Business Intelligence (4 endpoints) ==========
    "POST:/website/scan": EndpointDefinition(
        endpoint_path="/website/scan",
        http_method="POST",
        topic_id="website_scan",
        response_model="WebsiteScanResponse",
        requires_conversation=False,
        category="onboarding",
        description="Scan a website and extract business information",
        is_active=True,
    ),
    "POST:/suggestions/onboarding": EndpointDefinition(
        endpoint_path="/suggestions/onboarding",
        http_method="POST",
        topic_id="onboarding_suggestions",
        response_model="OnboardingSuggestionsResponse",
        requires_conversation=False,
        category="onboarding",
        description="Generate onboarding suggestions based on scanned website",
        is_active=True,
    ),
    "POST:/coaching/onboarding": EndpointDefinition(
        endpoint_path="/coaching/onboarding",
        http_method="POST",
        topic_id="onboarding_coaching",
        response_model="OnboardingCoachingResponse",
        requires_conversation=False,
        category="onboarding",
        description="AI coaching for onboarding process",
        is_active=True,
    ),
    "GET:/multitenant/conversations/business-data": EndpointDefinition(
        endpoint_path="/multitenant/conversations/business-data",
        http_method="GET",
        topic_id="business_metrics",
        response_model="BusinessMetricsResponse",
        requires_conversation=False,
        category="onboarding",
        description="Retrieve business metrics and data for coaching context",
        is_active=True,
    ),
    # ========== Section 2: Conversation API (3 endpoints) ==========
    "POST:/conversations/initiate": EndpointDefinition(
        endpoint_path="/conversations/initiate",
        http_method="POST",
        topic_id="conversation_initiate",
        response_model="ConversationResponse",
        requires_conversation=True,
        category="conversation",
        description="Initiate a new coaching conversation",
        is_active=True,
    ),
    "POST:/conversations/{conversation_id}/message": EndpointDefinition(
        endpoint_path="/conversations/{conversation_id}/message",
        http_method="POST",
        topic_id="conversation_message",
        response_model="MessageResponse",
        requires_conversation=True,
        category="conversation",
        description="Send a message in an active conversation",
        is_active=True,
    ),
    "GET:/conversations/{conversation_id}": EndpointDefinition(
        endpoint_path="/conversations/{conversation_id}",
        http_method="GET",
        topic_id="conversation_retrieve",
        response_model="ConversationResponse",
        requires_conversation=True,
        category="conversation",
        description="Retrieve conversation details and history",
        is_active=True,
    ),
    # ========== Section 3: Insights Generation (1 endpoint) ==========
    "POST:/insights/generate": EndpointDefinition(
        endpoint_path="/insights/generate",
        http_method="POST",
        topic_id="insights_generation",
        response_model="InsightsResponse",
        requires_conversation=False,
        category="insights",
        description="Generate business insights from coaching data",
        is_active=True,
    ),
    # ========== Section 4: Strategic Planning AI (5 endpoints) ==========
    "POST:/coaching/strategy-suggestions": EndpointDefinition(
        endpoint_path="/coaching/strategy-suggestions",
        http_method="POST",
        topic_id="strategy_suggestions",
        response_model="StrategySuggestionsResponse",
        requires_conversation=False,
        category="strategic_planning",
        description="Generate strategic planning suggestions",
        is_active=True,
    ),
    "POST:/coaching/kpi-recommendations": EndpointDefinition(
        endpoint_path="/coaching/kpi-recommendations",
        http_method="POST",
        topic_id="kpi_recommendations",
        response_model="KPIRecommendationsResponse",
        requires_conversation=False,
        category="strategic_planning",
        description="Recommend KPIs based on business goals",
        is_active=True,
    ),
    "POST:/coaching/alignment-check": EndpointDefinition(
        endpoint_path="/coaching/alignment-check",
        http_method="POST",
        topic_id="alignment_check",
        response_model="AlignmentAnalysisResponse",
        requires_conversation=False,
        category="strategic_planning",
        description="Calculate alignment score between goal and business foundation",
        is_active=True,
    ),
    "POST:/coaching/alignment-explanation": EndpointDefinition(
        endpoint_path="/coaching/alignment-explanation",
        http_method="POST",
        topic_id="alignment_explanation",
        response_model="AlignmentExplanationResponse",
        requires_conversation=False,
        category="strategic_planning",
        description="Explain alignment score calculation",
        is_active=True,
    ),
    "POST:/coaching/alignment-suggestions": EndpointDefinition(
        endpoint_path="/coaching/alignment-suggestions",
        http_method="POST",
        topic_id="alignment_suggestions",
        response_model="AlignmentSuggestionsResponse",
        requires_conversation=False,
        category="strategic_planning",
        description="Suggest improvements to increase alignment",
        is_active=True,
    ),
    # ========== Section 5: Operations AI (9 endpoints) ==========
    "POST:/operations/root-cause-suggestions": EndpointDefinition(
        endpoint_path="/operations/root-cause-suggestions",
        http_method="POST",
        topic_id="root_cause_suggestions",
        response_model="RootCauseSuggestionsResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Suggest root causes for operational issues",
        is_active=True,
    ),
    "POST:/operations/swot-analysis": EndpointDefinition(
        endpoint_path="/operations/swot-analysis",
        http_method="POST",
        topic_id="swot_analysis",
        response_model="SwotAnalysisResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Generate SWOT analysis for operations",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/five-whys-questions": EndpointDefinition(
        endpoint_path="/operations/five-whys-questions",
        http_method="POST",
        topic_id="five_whys_questions",
        response_model="FiveWhysQuestionsResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Generate Five Whys analysis questions",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/action-suggestions": EndpointDefinition(
        endpoint_path="/operations/action-suggestions",
        http_method="POST",
        topic_id="action_suggestions",
        response_model="ActionSuggestionsResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Suggest actions to resolve operational issues",
        is_active=True,
    ),
    "POST:/operations/optimize-action-plan": EndpointDefinition(
        endpoint_path="/operations/optimize-action-plan",
        http_method="POST",
        topic_id="optimize_action_plan",
        response_model="OptimizedActionPlanResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Optimize action plan for better execution",
        is_active=True,
    ),
    "POST:/operations/prioritization-suggestions": EndpointDefinition(
        endpoint_path="/operations/prioritization-suggestions",
        http_method="POST",
        topic_id="prioritization_suggestions",
        response_model="PrioritizationSuggestionsResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Suggest prioritization of operational tasks",
        is_active=True,
    ),
    "POST:/operations/scheduling-suggestions": EndpointDefinition(
        endpoint_path="/operations/scheduling-suggestions",
        http_method="POST",
        topic_id="scheduling_suggestions",
        response_model="SchedulingSuggestionsResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Suggest optimal scheduling for tasks",
        is_active=True,
    ),
    "POST:/operations/categorize-issue": EndpointDefinition(
        endpoint_path="/operations/categorize-issue",
        http_method="POST",
        topic_id="categorize_issue",
        response_model="IssueCategoryResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Categorize operational issue by type and severity",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/assess-impact": EndpointDefinition(
        endpoint_path="/operations/assess-impact",
        http_method="POST",
        topic_id="assess_impact",
        response_model="ImpactAssessmentResponse",
        requires_conversation=False,
        category="operations_ai",
        description="Assess business impact of operational issue",
        is_active=False,  # Missing - needs implementation
    ),
    # ========== Section 6: Operations-Strategic Integration (22 endpoints) ==========
    "GET:/operations/actions/{action_id}/strategic-context": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/strategic-context",
        http_method="GET",
        topic_id="action_strategic_context",
        response_model="ActionStrategicContextResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Get strategic context for a specific action",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/actions/suggest-connections": EndpointDefinition(
        endpoint_path="/operations/actions/suggest-connections",
        http_method="POST",
        topic_id="suggest_connections",
        response_model="SuggestedConnectionsResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Suggest strategic connections for actions",
        is_active=False,  # Missing - needs implementation
    ),
    "PUT:/operations/actions/{action_id}/connections": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/connections",
        http_method="PUT",
        topic_id="update_connections",
        response_model="UpdateConnectionsResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Update strategic connections for an action",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/actions/analyze-kpi-impact": EndpointDefinition(
        endpoint_path="/operations/actions/analyze-kpi-impact",
        http_method="POST",
        topic_id="analyze_kpi_impact",
        response_model="KPIImpactAnalysisResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Analyze KPI impact of proposed actions",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/kpi-updates": EndpointDefinition(
        endpoint_path="/operations/kpi-updates",
        http_method="POST",
        topic_id="record_kpi_update",
        response_model="KPIUpdateResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Record a KPI update event",
        is_active=False,  # Missing - needs implementation
    ),
    "GET:/operations/kpi-updates": EndpointDefinition(
        endpoint_path="/operations/kpi-updates",
        http_method="GET",
        topic_id="get_kpi_updates",
        response_model="KPIUpdateHistoryResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Get KPI update history",
        is_active=False,  # Missing - needs implementation
    ),
    "GET:/operations/issues/{issue_id}/strategic-context": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/strategic-context",
        http_method="GET",
        topic_id="issue_strategic_context",
        response_model="IssueStrategicContextResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Get strategic context for an operational issue",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/issues/{issue_id}/generate-actions": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/generate-actions",
        http_method="POST",
        topic_id="generate_actions_from_issue",
        response_model="GeneratedActionsResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Generate strategic actions from operational issue",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/strategic-alignment": EndpointDefinition(
        endpoint_path="/operations/strategic-alignment",
        http_method="POST",
        topic_id="operations_strategic_alignment",
        response_model="OperationsAlignmentResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Calculate strategic alignment of operations",
        is_active=True,  # Partially implemented
    ),
    "POST:/operations/actions/{action_id}/complete": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/complete",
        http_method="POST",
        topic_id="complete_action",
        response_model="ActionCompletionResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Mark action as complete with strategic impact",
        is_active=False,  # Missing - needs implementation
    ),
    "GET:/operations/actions/{action_id}/kpi-update-prompt": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/kpi-update-prompt",
        http_method="GET",
        topic_id="kpi_update_prompt",
        response_model="KPIUpdatePromptResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Get prompt for KPI update after action completion",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/actions/{action_id}/update-kpi": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/update-kpi",
        http_method="POST",
        topic_id="update_kpi_from_action",
        response_model="KPIUpdateResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Update KPI based on action completion",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/issues/{issue_id}/convert-to-actions": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/convert-to-actions",
        http_method="POST",
        topic_id="convert_issue_to_actions",
        response_model="ConvertedActionsResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Convert operational issue into actionable items",
        is_active=False,  # Missing - needs implementation
    ),
    "GET:/operations/issues/{issue_id}/closure-eligibility": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/closure-eligibility",
        http_method="GET",
        topic_id="check_closure_eligibility",
        response_model="ClosureEligibilityResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Check if issue is eligible for closure",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/issues/{issue_id}/close": EndpointDefinition(
        endpoint_path="/operations/issues/{issue_id}/close",
        http_method="POST",
        topic_id="close_issue",
        response_model="IssueClosureResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Close operational issue with strategic impact assessment",
        is_active=False,  # Missing - needs implementation
    ),
    "GET:/strategic/context": EndpointDefinition(
        endpoint_path="/strategic/context",
        http_method="GET",
        topic_id="strategic_context",
        response_model="StrategicContextResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Get comprehensive strategic planning context",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/actions/create-with-context": EndpointDefinition(
        endpoint_path="/operations/actions/create-with-context",
        http_method="POST",
        topic_id="create_action_with_context",
        response_model="ActionCreationResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Create action with full strategic context",
        is_active=False,  # Missing - needs implementation
    ),
    "GET:/operations/actions/{action_id}/relationships": EndpointDefinition(
        endpoint_path="/operations/actions/{action_id}/relationships",
        http_method="GET",
        topic_id="action_relationships",
        response_model="ActionRelationshipsResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Get strategic relationships for an action",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/kpi-sync/to-strategic-planning": EndpointDefinition(
        endpoint_path="/operations/kpi-sync/to-strategic-planning",
        http_method="POST",
        topic_id="kpi_sync_to_strategic",
        response_model="KPISyncResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Sync operational KPI updates to strategic planning",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/kpi-sync/from-strategic-planning": EndpointDefinition(
        endpoint_path="/operations/kpi-sync/from-strategic-planning",
        http_method="POST",
        topic_id="kpi_sync_from_strategic",
        response_model="KPISyncResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Sync strategic KPIs to operational tracking",
        is_active=False,  # Missing - needs implementation
    ),
    "GET:/operations/kpi-conflicts": EndpointDefinition(
        endpoint_path="/operations/kpi-conflicts",
        http_method="GET",
        topic_id="detect_kpi_conflicts",
        response_model="KPIConflictsResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Detect KPI conflicts between operations and strategy",
        is_active=False,  # Missing - needs implementation
    ),
    "POST:/operations/kpi-conflicts/{conflict_id}/resolve": EndpointDefinition(
        endpoint_path="/operations/kpi-conflicts/{conflict_id}/resolve",
        http_method="POST",
        topic_id="resolve_kpi_conflict",
        response_model="ConflictResolutionResponse",
        requires_conversation=False,
        category="operations_strategic_integration",
        description="Resolve KPI conflict with AI recommendations",
        is_active=False,  # Missing - needs implementation
    ),
    # ========== Section 7: Analysis API (4 endpoints) ==========
    "POST:/analysis/alignment": EndpointDefinition(
        endpoint_path="/analysis/alignment",
        http_method="POST",
        topic_id="alignment_analysis",
        response_model="AlignmentAnalysisResponse",
        requires_conversation=False,
        category="analysis",
        description="Analyze alignment between goals and purpose",
        is_active=True,
    ),
    "POST:/analysis/strategy": EndpointDefinition(
        endpoint_path="/analysis/strategy",
        http_method="POST",
        topic_id="strategy_analysis",
        response_model="StrategyAnalysisResponse",
        requires_conversation=False,
        category="analysis",
        description="Analyze business strategy effectiveness",
        is_active=True,
    ),
    "POST:/analysis/kpi": EndpointDefinition(
        endpoint_path="/analysis/kpi",
        http_method="POST",
        topic_id="kpi_analysis",
        response_model="KPIAnalysisResponse",
        requires_conversation=False,
        category="analysis",
        description="Analyze KPI effectiveness",
        is_active=True,
    ),
    "POST:/analysis/operations": EndpointDefinition(
        endpoint_path="/analysis/operations",
        http_method="POST",
        topic_id="operations_analysis",
        response_model="OperationsAnalysisResponse",
        requires_conversation=False,
        category="analysis",
        description="Perform operational analysis (SWOT, root cause, etc.)",
        is_active=True,
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


def list_endpoints_by_category(category: str) -> list[EndpointDefinition]:
    """Get all endpoints in a specific category.

    Args:
        category: Category name (e.g., "strategic_planning", "operations_ai")

    Returns:
        List of EndpointDefinition objects in the category
    """
    return [endpoint for endpoint in ENDPOINT_REGISTRY.values() if endpoint.category == category]


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
        if not endpoint.requires_conversation:
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
            - endpoints_by_category: Count per category
    """
    all_endpoints = list_all_endpoints(active_only=False)
    active_endpoints = [e for e in all_endpoints if e.is_active]
    inactive_endpoints = [e for e in all_endpoints if not e.is_active]
    conversation_endpoints = [e for e in all_endpoints if e.requires_conversation]
    single_shot_endpoints = [e for e in all_endpoints if not e.requires_conversation]

    categories: dict[str, int] = {}
    for endpoint in all_endpoints:
        categories[endpoint.category] = categories.get(endpoint.category, 0) + 1

    return {
        "total_endpoints": len(all_endpoints),
        "active_endpoints": len(active_endpoints),
        "inactive_endpoints": len(inactive_endpoints),
        "conversation_endpoints": len(conversation_endpoints),
        "single_shot_endpoints": len(single_shot_endpoints),
        **{f"category_{cat}": count for cat, count in categories.items()},
    }
