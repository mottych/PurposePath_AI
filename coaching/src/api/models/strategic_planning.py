"""Strategic Planning AI Response Models.

Response models for strategic planning AI topics:
- alignment_check: Goal alignment with business foundation
- strategy_suggestions: Strategy recommendations
- kpi_recommendations: KPI suggestions
- action_suggestions: Action plan recommendations

These models match the specifications in Issue #182.
"""

from pydantic import BaseModel, Field

# =============================================================================
# AlignmentCheck Response Models
# =============================================================================


class AlignmentBreakdown(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


class AlignmentCheckData(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


class AlignmentCheckResponse(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


# =============================================================================
# StrategySuggestions Response Models
# =============================================================================


class StrategySuggestion(BaseModel):
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
    suggested_kpis: list[str] = Field(
        default_factory=list,
        alias="suggestedKpis",
        max_length=3,
        description="Brief KPI names to track this strategy (0-3 items)",
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True


class StrategySuggestionsData(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


class StrategySuggestionsResponseV2(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


# =============================================================================
# KPIRecommendations Response Models
# =============================================================================


class SuggestedTarget(BaseModel):
    """Suggested target for a KPI."""

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


class KPIRecommendation(BaseModel):
    """Individual KPI recommendation."""

    name: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="KPI name",
    )
    description: str = Field(
        ...,
        min_length=20,
        max_length=300,
        description="What this KPI measures",
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
    kpi_type: str = Field(
        ...,
        alias="type",
        description="KPI type: 'quantitative', 'qualitative', or 'binary'",
        pattern="^(quantitative|qualitative|binary)$",
    )
    reasoning: str = Field(
        ...,
        min_length=50,
        max_length=300,
        description="Why this KPI is recommended",
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
        description="How to measure this KPI",
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
        description="Whether this should be the primary KPI",
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True


class KPIRecommendationsData(BaseModel):
    """Data payload for KPI recommendations response."""

    recommendations: list[KPIRecommendation] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="List of KPI recommendations (1-5 items)",
    )
    analysis_notes: str = Field(
        ...,
        alias="analysisNotes",
        min_length=50,
        max_length=300,
        description="Meta-commentary on the recommendations",
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True


class KPIRecommendationsResponseV2(BaseModel):
    """Response for kpi_recommendations topic.

    Recommends KPIs for measuring goal or strategy success.
    Note: Named V2 to distinguish from existing KPIRecommendationsResponse.
    """

    topic_id: str = Field(
        default="kpi_recommendations",
        description="Topic identifier",
    )
    success: bool = Field(
        default=True,
        description="Whether the request succeeded",
    )
    data: KPIRecommendationsData = Field(
        ...,
        description="KPI recommendations",
    )
    schema_ref: str = Field(
        default="KPIRecommendationsResponseV2",
        description="Reference to this schema",
    )

    class Config:
        """Pydantic config."""

        populate_by_name = True


# =============================================================================
# ActionSuggestions Response Models
# =============================================================================


class ActionSuggestion(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


class ActionSuggestionsData(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


class ActionSuggestionsResponse(BaseModel):
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

    class Config:
        """Pydantic config."""

        populate_by_name = True


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
