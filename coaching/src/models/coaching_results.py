"""Result models for coaching conversations.

This module defines the structured output models that represent
the final results from coaching conversations. These models are
used to serialize LLM outputs when a coaching session completes.

Each coaching topic has its own result model with topic-specific fields.
The models are registered in COACHING_RESULT_MODELS for dynamic resolution.
"""

from typing import Literal

from pydantic import BaseModel, Field

# =============================================================================
# Core Values Coaching Result
# =============================================================================


class CoreValue(BaseModel):
    """A single core value identified during coaching.

    Attributes:
        name: The name of the value (e.g., "Integrity", "Innovation")
        description: What this value means to the organization
        importance: Why this value matters and how it guides decisions
    """

    name: str = Field(..., min_length=1, max_length=100, description="Value name")
    description: str = Field(
        ..., min_length=10, max_length=500, description="What this value means"
    )
    importance: str = Field(
        ..., min_length=10, max_length=500, description="Why this value matters"
    )


class CoreValuesResult(BaseModel):
    """Final result from core values coaching session.

    Contains the list of identified core values and a summary
    of the coaching conversation.

    Attributes:
        values: List of 3-5 core values identified
        summary: Overall summary of the values and how they connect
    """

    values: list[CoreValue] = Field(
        ..., min_length=1, max_length=7, description="List of identified core values"
    )
    summary: str = Field(
        ..., min_length=50, max_length=1000, description="Summary of the core values"
    )


# =============================================================================
# Purpose Coaching Result
# =============================================================================


class PurposeResult(BaseModel):
    """Final result from purpose coaching session.

    Contains the organization's purpose statement and supporting context.

    Attributes:
        purpose_statement: The articulated purpose statement
        why_it_matters: Explanation of why this purpose is meaningful
        how_it_guides: How this purpose guides organizational decisions
    """

    purpose_statement: str = Field(
        ..., min_length=20, max_length=500, description="The organization's purpose statement"
    )
    why_it_matters: str = Field(
        ..., min_length=50, max_length=1000, description="Why this purpose is meaningful"
    )
    how_it_guides: str = Field(
        ..., min_length=50, max_length=1000, description="How purpose guides decisions"
    )


# =============================================================================
# Vision Coaching Result
# =============================================================================


class VisionResult(BaseModel):
    """Final result from vision coaching session.

    Contains the organization's vision statement and aspirations.

    Attributes:
        vision_statement: The articulated vision statement
        time_horizon: The time frame for this vision (e.g., "5 years", "10 years")
        key_aspirations: List of key aspirations that make up the vision
    """

    vision_statement: str = Field(
        ..., min_length=20, max_length=500, description="The organization's vision statement"
    )
    time_horizon: str = Field(
        ..., min_length=1, max_length=50, description="Time frame for the vision"
    )
    key_aspirations: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Key aspirations that comprise the vision",
    )


# =============================================================================
# Goal Creation Coaching Result
# =============================================================================


class GoalActionResult(BaseModel):
    """Action item planned for a goal strategy."""

    title: str = Field(..., min_length=3, max_length=200, description="Action title")
    assignee: str = Field(..., min_length=1, max_length=120, description="Person accountable")
    due_date: str = Field(..., min_length=1, max_length=50, description="Due date or milestone")
    priority: str = Field(..., min_length=1, max_length=20, description="Priority level")
    success_criteria: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="How success for this action is evaluated",
    )


class GoalMeasureResult(BaseModel):
    """Measure selected to track strategy progress."""

    name: str = Field(..., min_length=1, max_length=120, description="Measure name")
    measure_type: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Measure type (leading, lagging, custom, catalog)",
    )
    unit: str = Field(..., min_length=1, max_length=30, description="Measure unit")
    target_value: str = Field(..., min_length=1, max_length=100, description="Target value")
    cadence: str = Field(..., min_length=1, max_length=40, description="Review cadence")


class GoalStrategyResult(BaseModel):
    """Strategy with linked actions and measures."""

    strategy_name: str = Field(..., min_length=3, max_length=200, description="Strategy name")
    strategy_description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="How this strategy advances the goal",
    )
    actions: list[GoalActionResult] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Planned actions for this strategy",
    )
    measures: list[GoalMeasureResult] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Measures used to track this strategy",
    )


class GoalCreationResult(BaseModel):
    """Final aggregate output from guided goal creation coaching."""

    goal_title: str = Field(..., min_length=5, max_length=200, description="Goal title")
    goal_intent: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description="Goal intent statement",
    )
    alignment_summary: str = Field(
        ...,
        min_length=20,
        max_length=1000,
        description="Alignment to purpose, values, and vision",
    )
    strategies: list[GoalStrategyResult] = Field(
        ...,
        min_length=1,
        max_length=8,
        description="Strategies with actions and measures",
    )
    next_90_day_focus: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Priority focus items for the next 90 days",
    )


# =============================================================================
# Issue root cause coaching result (GitHub #132)
# =============================================================================


class IssueRootCauseActionItem(BaseModel):
    """Single recommended action from issue root cause coaching."""

    title: str = Field(..., min_length=1, max_length=300, description="Action title")
    description: str = Field(
        ...,
        min_length=10,
        max_length=4000,
        description="What to do, acceptance criteria, and dependencies",
    )
    due_date: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Due date (absolute) or proposed milestone date",
    )
    assignee: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Accountable owner (name or role/seat)",
    )
    priority: Literal["Critical", "High", "Medium", "Low"] = Field(
        ..., description="Execution priority for the action"
    )
    alignment_note: str = Field(
        ...,
        min_length=5,
        max_length=800,
        description="Which value, goal, or strategy this action supports",
    )


class IssueRootCauseCoachingResult(BaseModel):
    """Structured extraction payload after issue root cause coaching (GitHub #132)."""

    issue_one_sentence: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Clean one-sentence statement of the focal issue",
    )
    desired_outcome: str = Field(
        ...,
        min_length=10,
        max_length=1500,
        description="What success looks like when the issue is resolved",
    )
    relevant_business_context: str = Field(
        ...,
        min_length=20,
        max_length=8000,
        description="Purpose, values, goals/strategies, roles, and related open issues used",
    )
    technique_selected: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Diagnostic technique used (e.g. Five Whys, fishbone)",
    )
    technique_rationale: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Why this technique fits the issue",
    )
    symptoms: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Observable symptoms or surface problem",
    )
    contributing_factors: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Contributing factors between symptom and root cause",
    )
    root_cause: str = Field(
        ...,
        min_length=10,
        max_length=4000,
        description="Identified or best-hypothesis root cause",
    )
    evidence_and_reasoning: str = Field(
        ...,
        min_length=10,
        max_length=6000,
        description="Evidence, patterns, and reasoning for the root cause",
    )
    hypothesis_notes: str = Field(
        default="",
        max_length=2000,
        description="What remains uncertain or needs validation",
    )
    energy_pattern_current: str = Field(
        ...,
        min_length=5,
        max_length=800,
        description="Current energy pattern in plain language",
    )
    energy_shift_needed: str = Field(
        ...,
        min_length=5,
        max_length=800,
        description="Constructive shift for the leader or team",
    )
    recommended_actions: list[IssueRootCauseActionItem] = Field(
        ...,
        min_length=1,
        max_length=25,
        description="Smallest sufficient set of owned actions",
    )
    related_issues_to_track: list[str] = Field(
        default_factory=list,
        description="Parked or related issues to track separately",
    )
    risks_and_watchouts: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Execution risks or recurrence watchouts",
    )
    next_coaching_question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Single best next question if coaching continues",
    )


# =============================================================================
# Result Model Registry
# =============================================================================

COACHING_RESULT_MODELS: dict[str, type[BaseModel]] = {
    "CoreValuesResult": CoreValuesResult,
    "PurposeResult": PurposeResult,
    "VisionResult": VisionResult,
    "GoalCreationResult": GoalCreationResult,
    "IssueRootCauseCoachingResult": IssueRootCauseCoachingResult,
}
"""Registry mapping result model names to their Pydantic classes.

Used for dynamic resolution when serializing coaching session outputs.
"""


def get_coaching_result_model(model_name: str) -> type[BaseModel] | None:
    """Get a coaching result model class by name.

    Args:
        model_name: Name of the result model (e.g., "CoreValuesResult")

    Returns:
        The Pydantic model class, or None if not found
    """
    return COACHING_RESULT_MODELS.get(model_name)


def get_result_json_schema(model_name: str) -> dict[str, object] | None:
    """Get the JSON schema for a coaching result model.

    Used to provide schema information to the LLM for structured output.

    Args:
        model_name: Name of the result model

    Returns:
        JSON schema dict, or None if model not found
    """
    model = get_coaching_result_model(model_name)
    if model is None:
        return None
    return model.model_json_schema()
