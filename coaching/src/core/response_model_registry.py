"""Response Model Registry - Mapping of model names to Pydantic classes.

This module provides a central registry for resolving response model names
(stored as strings in TopicDefinition) to actual Pydantic model classes.

Used by the generic AI execute endpoint to:
1. Validate AI responses against expected schemas
2. Return JSON schemas for documentation
3. Support dynamic response model resolution
"""

from typing import Any

import structlog
from coaching.src.api.models.analysis import (
    AlignmentAnalysisResponse,
    AlignmentExplanationResponse,
    AlignmentSuggestionsResponse,
    MeasureRecommendationsResponse,
    OperationsAnalysisResponse,
)
from coaching.src.api.models.business_data import BusinessMetricsResponse
from coaching.src.api.models.conversations import (
    ConversationResponse,
    MessageResponse,
)
from coaching.src.api.models.onboarding import (
    OnboardingCoachingResponse,
    OnboardingReviewResponse,
    OnboardingSuggestionResponse,
    WebsiteScanResponse,
)
from coaching.src.api.models.operations import (
    OptimizedActionPlanResponse,
    PrioritizationResponse,
    SchedulingResponse,
    StrategicAlignmentResponse,
)
from coaching.src.api.models.strategic_planning import (
    ActionSuggestionsResponse,
    AlignmentCheckResponse,
    MeasureRecommendationsResponseV2,
    StrategySuggestionsResponseV2,
)
from coaching.src.api.models.strategy_suggestions import (
    StrategySuggestionsResponse,
)
from pydantic import BaseModel

logger = structlog.get_logger()


# Central registry mapping response model names to classes
# Key: String name as stored in EndpointDefinition.response_model
# Value: Actual Pydantic BaseModel class
RESPONSE_MODEL_REGISTRY: dict[str, type[BaseModel]] = {
    # === Onboarding & Business Intelligence ===
    "WebsiteScanResponse": WebsiteScanResponse,
    # Note: OnboardingSuggestionsResponse maps to OnboardingSuggestionResponse (singular)
    "OnboardingSuggestionsResponse": OnboardingSuggestionResponse,
    "OnboardingCoachingResponse": OnboardingCoachingResponse,
    "OnboardingReviewResponse": OnboardingReviewResponse,
    "BusinessMetricsResponse": BusinessMetricsResponse,
    # === Conversations ===
    "ConversationResponse": ConversationResponse,
    "MessageResponse": MessageResponse,
    # === Strategic Planning ===
    "StrategySuggestionsResponse": StrategySuggestionsResponse,
    "MeasureRecommendationsResponse": MeasureRecommendationsResponse,
    "AlignmentAnalysisResponse": AlignmentAnalysisResponse,
    "AlignmentExplanationResponse": AlignmentExplanationResponse,
    "AlignmentSuggestionsResponse": AlignmentSuggestionsResponse,
    # Strategic Planning AI Topics (Issue #182)
    "AlignmentCheckResponse": AlignmentCheckResponse,
    "StrategySuggestionsResponseV2": StrategySuggestionsResponseV2,
    "MeasureRecommendationsResponseV2": MeasureRecommendationsResponseV2,
    "ActionSuggestionsResponse": ActionSuggestionsResponse,
    # === Operations AI (Active endpoints only) ===
    "OptimizedActionPlanResponse": OptimizedActionPlanResponse,
    "StrategicAlignmentResponse": StrategicAlignmentResponse,
    "OperationsAnalysisResponse": OperationsAnalysisResponse,
    # Note: PrioritizationSuggestionsResponse maps to PrioritizationResponse
    "PrioritizationSuggestionsResponse": PrioritizationResponse,
    # Note: SchedulingSuggestionsResponse maps to SchedulingResponse
    "SchedulingSuggestionsResponse": SchedulingResponse,
    # === Placeholder for inactive/future endpoints ===
    # The following models are referenced in endpoint_registry but endpoints are inactive:
    # - InsightsResponse
    # - RootCauseSuggestionsResponse
    # - SwotAnalysisResponse
    # - FiveWhysQuestionsResponse
    # - ActionSuggestionsResponse
    # - IssueCategoryResponse
    # - ImpactAssessmentResponse
    # - ActionStrategicContextResponse
    # - SuggestedConnectionsResponse
    # - UpdateConnectionsResponse
    # - CreateIssueResponse, CreateActionResponse, CompleteActionResponse, CloseIssueResponse
    # - IssueStatusResponse, RelatedActionsResponse
    # - UpdateMeasureResponse, CalculateMeasureResponse, MeasureHistoryResponse
    # - MeasureImpactResponse, ActionMeasureImpactResponse, SyncMeasuresResponse
    # - MeasureConflictsResponse, ResolveConflictResponse
    # - CascadeUpdateResponse
    # - TopicStrategicContextResponse, GoalAlignmentResponse, MeasurePerformanceResponse
}


def get_response_model(model_name: str) -> type[BaseModel] | None:
    """Get response model class by name.

    Args:
        model_name: Name of the response model (e.g., "WebsiteScanResponse")

    Returns:
        Pydantic model class if found, None otherwise
    """
    return RESPONSE_MODEL_REGISTRY.get(model_name)


def get_response_schema(model_name: str) -> dict[str, Any] | None:
    """Get JSON schema for a response model.

    Args:
        model_name: Name of the response model

    Returns:
        JSON schema dict if model found, None otherwise
    """
    model = RESPONSE_MODEL_REGISTRY.get(model_name)
    if model is None:
        return None
    return model.model_json_schema()


def list_available_schemas() -> list[str]:
    """List all available response model names.

    Returns:
        Sorted list of registered model names
    """
    return sorted(RESPONSE_MODEL_REGISTRY.keys())


def is_model_registered(model_name: str) -> bool:
    """Check if a response model is registered.

    Args:
        model_name: Name of the response model

    Returns:
        True if model is in registry, False otherwise
    """
    return model_name in RESPONSE_MODEL_REGISTRY
