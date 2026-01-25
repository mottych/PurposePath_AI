"""Strategic Planning AI Response Models.

Response models for strategic planning AI topics:
- alignment_check: Goal alignment with business foundation
- strategy_suggestions: Strategy recommendations
- measure_recommendations: Measure suggestions
- action_suggestions: Action plan recommendations

These models match the specifications in Issue #182.
"""

from pydantic import BaseModel, ConfigDict, Field


class StrategicPlanningBaseModel(BaseModel):
    """Shared config for strategic planning response models."""

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# AlignmentCheck Response Models
# =============================================================================


class AlignmentBreakdown(StrategicPlanningBaseModel):
    """Breakdown of alignment scores by component."""

    vision_alignment: int = Field(
        ...,
        alias="visionAlignment",
        ge=0,
        le=100,
        description="Alignment with company vision (0-100)",
    )
    purpose_alignment: int = Field(
        ...,
        alias="purposeAlignment",
        ge=0,
        le=100,
        description="Alignment with company purpose (0-100)",
    )
    values_alignment: int = Field(
        ...,
        alias="valuesAlignment",
        ge=0,
        le=100,
        description="Alignment with core values (0-100)",
    )


class AlignmentCheckData(StrategicPlanningBaseModel):
    """Data payload for alignment check response."""

    alignment_score: int = Field(
        ...,
        alias="alignmentScore",
        ge=0,
        le=100,
        description="Overall alignment score (0-100)",
    )
    explanation: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="Human-readable explanation of the alignment",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Actionable improvement suggestions (0-3 items)",
    )
    breakdown: AlignmentBreakdown = Field(
        ...,
        description="Breakdown of alignment scores by component",
    )


class AlignmentCheckResponse(StrategicPlanningBaseModel):
    """Response for alignment_check topic.

    Calculates how well a goal aligns with organization's vision, purpose, and values.
    """

    topic_id: str = Field(
        default="alignment_check",
        description="Topic identifier",
    )
    success: bool = Field(
        default=True,
        description="Whether the request succeeded",
    )
    data: AlignmentCheckData = Field(
        ...,
        description="Alignment check results",
    )
    schema_ref: str = Field(
        default="AlignmentCheckResponse",
        description="Reference to this schema",
    )


# =============================================================================
# StrategySuggestions Response Models
# =============================================================================


class StrategySuggestion(StrategicPlanningBaseModel):
    """Individual strategy suggestion."""

    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Strategy title",
    )
    description: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="Detailed strategy description",
    )
    reasoning: str = Field(
        ...,
        min_length=50,
        max_length=300,
        description="Why this strategy makes sense for the goal",
    )
    alignment_score: int = Field(
        ...,
        alias="alignmentScore",
        ge=0,
        le=100,
        description="How well this strategy aligns with business foundation",
    )
    suggested_measures: list[str] = Field(
        default_factory=list,
        alias="suggestedMeasures",
        max_length=3,
        description="Brief Measure names to track this strategy (0-3 items)",
    )


class StrategySuggestionsData(StrategicPlanningBaseModel):
    """Data payload for strategy suggestions response."""

    suggestions: list[StrategySuggestion] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of strategy suggestions (1-5 items)",
    )
    analysis_notes: str = Field(
        ...,
        alias="analysisNotes",
        min_length=50,
        max_length=300,
        description="Meta-commentary on the suggestions",
    )


class StrategySuggestionsResponseV2(StrategicPlanningBaseModel):
    """Response for strategy_suggestions topic.

    Generates suggested strategies for achieving a goal.
    Note: Named V2 to distinguish from existing StrategySuggestionsResponse.
    """

    topic_id: str = Field(
        default="strategy_suggestions",
        description="Topic identifier",
    )
    success: bool = Field(
        default=True,
        description="Whether the request succeeded",
    )
    data: StrategySuggestionsData = Field(
        ...,
        description="Strategy suggestions",
    )
    schema_ref: str = Field(
        default="StrategySuggestionsResponseV2",
        description="Reference to this schema",
    )


# =============================================================================
# KPIRecommendations Response Models
# =============================================================================


class SuggestedTarget(StrategicPlanningBaseModel):
    """Suggested target for a Measure."""

    value: float = Field(
        ...,
        description="Target value",
    )
    timeframe: str = Field(
        ...,
        description="Timeframe for achieving target (e.g., 'Q4 2025')",
    )
    rationale: str = Field(
        ...,
        description="Rationale for this target",
    )


class MeasureRecommendation(StrategicPlanningBaseModel):
    """Individual Measure recommendation."""

    name: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Measure name",
    )
    description: str = Field(
        ...,
        min_length=20,
        max_length=300,
        description="What this Measure measures",
    )
    unit: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unit of measurement (e.g., '%', 'USD', 'count')",
    )
    direction: str = Field(
        ...,
        description="Desired direction: 'up' or 'down'",
        pattern="^(up|down)$",
    )
    measure_type: str = Field(
        ...,
        alias="type",
        description="Measure type: 'quantitative', 'qualitative', or 'binary'",
        pattern="^(quantitative|qualitative|binary)$",
    )
    reasoning: str = Field(
        ...,
        min_length=50,
        max_length=300,
        description="Why this Measure is recommended",
    )
    suggested_target: SuggestedTarget | None = Field(
        default=None,
        alias="suggestedTarget",
        description="Optional suggested target",
    )
    measurement_approach: str = Field(
        ...,
        alias="measurementApproach",
        min_length=20,
        max_length=200,
        description="How to measure this Measure",
    )
    measurement_frequency: str = Field(
        ...,
        alias="measurementFrequency",
        description="Measurement frequency",
        pattern="^(daily|weekly|monthly|quarterly)$",
    )
    is_primary_candidate: bool = Field(
        default=False,
        alias="isPrimaryCandidate",
        description="Whether this should be the primary Measure",
    )
    catalog_measure_id: str | None = Field(
        default=None,
        alias="catalogMeasureId",
        description="ID of recommended catalog measure (if from catalog)",
    )
    suggested_owner_id: str | None = Field(
        default=None,
        alias="suggestedOwnerId",
        description="Suggested person ID to assign as measure owner",
    )
    suggested_owner_name: str | None = Field(
        default=None,
        alias="suggestedOwnerName",
        description="Suggested person name to assign as measure owner",
    )
    suggested_position_id: str | None = Field(
        default=None,
        alias="suggestedPositionId",
        description="Suggested position ID (optional, if position-based assignment)",
    )
    association_type: str | None = Field(
        default=None,
        alias="associationType",
        description="Whether measure is for 'goal' or 'strategy'",
        pattern="^(goal|strategy)$",
    )
    associated_entity_id: str | None = Field(
        default=None,
        alias="associatedEntityId",
        description="Goal ID or Strategy ID this measure is associated with",
    )


class MeasureRecommendationsData(StrategicPlanningBaseModel):
    """Data payload for Measure recommendations response."""

    recommendations: list[MeasureRecommendation] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of Measure recommendations (1-5 items)",
    )
    analysis_notes: str = Field(
        ...,
        alias="analysisNotes",
        min_length=50,
        max_length=300,
        description="Meta-commentary on the recommendations",
    )


class MeasureRecommendationsResponseV2(StrategicPlanningBaseModel):
    """Response for measure_recommendations topic.

    Recommends Measures for measuring goal or strategy success.
    Note: Named V2 to distinguish from existing MeasureRecommendationsResponse.
    """

    topic_id: str = Field(
        default="measure_recommendations",
        description="Topic identifier",
    )
    success: bool = Field(
        default=True,
        description="Whether the request succeeded",
    )
    data: MeasureRecommendationsData = Field(
        ...,
        description="Measure recommendations",
    )
    schema_ref: str = Field(
        default="MeasureRecommendationsResponseV2",
        description="Reference to this schema",
    )


# Renamed from KPIRecommendationsResponseV2
MeasureRecommendationsResponse = MeasureRecommendationsResponseV2


# =============================================================================
# ActionSuggestions Response Models
# =============================================================================


class ActionSuggestion(StrategicPlanningBaseModel):
    """Individual action suggestion."""

    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Action title",
    )
    description: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="Detailed action description",
    )
    reasoning: str = Field(
        ...,
        min_length=50,
        max_length=200,
        description="Why this action is important",
    )
    priority: str = Field(
        ...,
        description="Priority level",
        pattern="^(low|medium|high|critical)$",
    )
    estimated_duration: str = Field(
        ...,
        alias="estimatedDuration",
        description="Human-readable duration estimate (e.g., '2 weeks')",
    )
    suggested_owner_role: str | None = Field(
        default=None,
        alias="suggestedOwnerRole",
        description="Suggested role for ownership",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="Titles of prerequisite actions (0-3 items)",
    )
    sequence_order: int = Field(
        ...,
        alias="sequenceOrder",
        ge=1,
        description="Suggested execution order",
    )


class ActionSuggestionsData(StrategicPlanningBaseModel):
    """Data payload for action suggestions response."""

    suggestions: list[ActionSuggestion] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of action suggestions (1-10 items)",
    )
    analysis_notes: str = Field(
        ...,
        alias="analysisNotes",
        min_length=50,
        max_length=200,
        description="Meta-commentary on the suggestions",
    )
    timeline_estimate: str | None = Field(
        default=None,
        alias="timelineEstimate",
        description="Overall timeline estimate",
    )


class ActionSuggestionsResponse(StrategicPlanningBaseModel):
    """Response for action_suggestions topic.

    Suggests specific, actionable tasks to execute a strategy.
    """

    topic_id: str = Field(
        default="action_suggestions",
        description="Topic identifier",
    )
    success: bool = Field(
        default=True,
        description="Whether the request succeeded",
    )
    data: ActionSuggestionsData = Field(
        ...,
        description="Action suggestions",
    )
    schema_ref: str = Field(
        default="ActionSuggestionsResponse",
        description="Reference to this schema",
    )


__all__ = [
    "ActionSuggestion",
    "ActionSuggestionsData",
    "ActionSuggestionsResponse",
    "AlignmentBreakdown",
    "AlignmentCheckData",
    "AlignmentCheckResponse",
    "KPIRecommendation",
    "KPIRecommendationsData",
    "KPIRecommendationsResponseV2",
    "StrategySuggestion",
    "StrategySuggestionsData",
    "StrategySuggestionsResponseV2",
    "SuggestedTarget",
]
