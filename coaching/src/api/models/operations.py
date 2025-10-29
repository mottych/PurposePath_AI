"""API models for Operations AI endpoints (Issue #63 & #64).

This module provides Pydantic models for Operations AI endpoints including:
- Strategic alignment analysis
- Action prioritization suggestions
- Scheduling optimization suggestions
- Root cause analysis suggestions
- Action plan generation
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Strategic Alignment Models (Issue #63)
# ============================================================================


class ActionInput(BaseModel):
    """Action item for alignment analysis."""

    id: str = Field(..., description="Unique action identifier")
    title: str = Field(..., min_length=1, max_length=500, description="Action title")
    description: str = Field(..., min_length=1, max_length=5000, description="Action description")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Current priority level"
    )
    status: str = Field(..., description="Current status")


class GoalInput(BaseModel):
    """Goal for alignment analysis."""

    id: str = Field(..., description="Unique goal identifier")
    intent: str = Field(..., min_length=1, description="Goal intent/description")
    strategies: list[str] = Field(default_factory=list, description="Associated strategies")


class BusinessFoundationInput(BaseModel):
    """Business foundation context."""

    vision: str = Field(..., min_length=1, description="Company vision")
    purpose: str = Field(..., min_length=1, description="Company purpose")
    core_values: list[str] = Field(..., min_length=1, alias="coreValues", description="Core values")


class StrategicAlignmentRequest(BaseModel):
    """Request for strategic alignment analysis."""

    actions: list[ActionInput] = Field(
        ..., min_length=1, max_length=100, description="Actions to analyze"
    )
    goals: list[GoalInput] = Field(..., min_length=1, max_length=50, description="Business goals")
    business_foundation: BusinessFoundationInput = Field(
        ..., alias="businessFoundation", description="Business foundation context"
    )

    @field_validator("actions")
    @classmethod
    def validate_actions(cls, v: list[ActionInput]) -> list[ActionInput]:
        """Validate actions list."""
        if not v:
            raise ValueError("At least one action is required")
        return v


class StrategicConnection(BaseModel):
    """Connection between action and goal."""

    goal_id: str = Field(..., alias="goalId", description="Goal identifier")
    goal_title: str = Field(..., alias="goalTitle", description="Goal title/intent")
    alignment_score: int = Field(
        ..., alias="alignmentScore", ge=0, le=100, description="Alignment score (0-100)"
    )
    impact: Literal["low", "medium", "high", "critical"] = Field(..., description="Impact level")


class ActionAlignmentAnalysis(BaseModel):
    """Alignment analysis for a single action."""

    action_id: str = Field(..., alias="actionId", description="Action identifier")
    alignment_score: int = Field(
        ..., alias="alignmentScore", ge=0, le=100, description="Overall alignment score"
    )
    strategic_connections: list[StrategicConnection] = Field(
        ..., alias="strategicConnections", description="Connections to goals"
    )
    recommendations: list[str] = Field(..., description="Improvement recommendations")


class StrategicAlignmentResponse(BaseModel):
    """Response for strategic alignment analysis."""

    success: bool = Field(default=True, description="Request success status")
    data: dict[str, Any] = Field(..., description="Alignment analysis data")


# ============================================================================
# Prioritization Models (Issue #63)
# ============================================================================


class PrioritizationActionInput(BaseModel):
    """Action for prioritization analysis."""

    id: str = Field(..., description="Unique action identifier")
    title: str = Field(..., min_length=1, description="Action title")
    current_priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., alias="currentPriority", description="Current priority"
    )
    due_date: str | None = Field(None, alias="dueDate", description="Due date (ISO format)")
    impact: str | None = Field(None, description="Expected impact description")
    effort: str | None = Field(None, description="Required effort description")
    status: str = Field(..., description="Current status")
    linked_goals: list[str] = Field(
        alias="linkedGoals", default_factory=list, description="Linked goal IDs"
    )


class BusinessContext(BaseModel):
    """Business context for prioritization."""

    current_goals: list[str] = Field(
        alias="currentGoals", default_factory=list, description="Current business goals"
    )
    constraints: list[str] = Field(default_factory=list, description="Business constraints")
    urgent_deadlines: list[str] = Field(
        alias="urgentDeadlines", default_factory=list, description="Urgent deadlines"
    )


class PrioritizationRequest(BaseModel):
    """Request for action prioritization suggestions."""

    actions: list[PrioritizationActionInput] = Field(
        ..., min_length=1, max_length=200, description="Actions to prioritize"
    )
    business_context: BusinessContext = Field(
        ..., alias="businessContext", description="Business context for prioritization"
    )


class PrioritizationSuggestion(BaseModel):
    """Prioritization suggestion for an action."""

    action_id: str = Field(..., alias="actionId", description="Action identifier")
    suggested_priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., alias="suggestedPriority", description="Suggested priority level"
    )
    current_priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., alias="currentPriority", description="Current priority level"
    )
    reasoning: str = Field(..., description="Reasoning for suggestion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    urgency_factors: list[str] = Field(
        ..., alias="urgencyFactors", description="Factors contributing to urgency"
    )
    impact_factors: list[str] = Field(
        ..., alias="impactFactors", description="Factors contributing to impact"
    )
    recommended_action: Literal["escalate", "maintain", "de-prioritize"] = Field(
        ..., alias="recommendedAction", description="Recommended action"
    )
    estimated_business_value: int | None = Field(
        None,
        alias="estimatedBusinessValue",
        description="Estimated business value in currency units",
    )


class PrioritizationResponse(BaseModel):
    """Response for prioritization suggestions."""

    success: bool = Field(default=True, description="Request success status")
    data: list[PrioritizationSuggestion] = Field(..., description="Prioritization suggestions")


# ============================================================================
# Scheduling Models (Issue #63)
# ============================================================================


class SchedulingActionInput(BaseModel):
    """Action for scheduling optimization."""

    id: str = Field(..., description="Unique action identifier")
    title: str = Field(..., min_length=1, description="Action title")
    estimated_duration: int = Field(
        ..., alias="estimatedDuration", gt=0, description="Estimated duration in hours"
    )
    dependencies: list[str] = Field(default_factory=list, description="Action IDs this depends on")
    assigned_to: str | None = Field(None, alias="assignedTo", description="Assigned person/team ID")
    current_start_date: str | None = Field(
        None, alias="currentStartDate", description="Current start date"
    )
    current_due_date: str | None = Field(
        None, alias="currentDueDate", description="Current due date"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Priority level"
    )


class CriticalDeadline(BaseModel):
    """Critical deadline constraint."""

    date: str = Field(..., description="Deadline date (ISO format)")
    description: str = Field(..., description="Deadline description")


class TeamAvailability(BaseModel):
    """Team member availability."""

    person_id: str = Field(..., alias="personId", description="Person/team member identifier")
    hours_per_week: int = Field(
        ..., alias="hoursPerWeek", gt=0, le=168, description="Available hours per week"
    )
    unavailable_dates: list[str] = Field(
        default_factory=list, alias="unavailableDates", description="Unavailable dates (ISO format)"
    )


class SchedulingConstraints(BaseModel):
    """Scheduling constraints."""

    team_capacity: int = Field(
        ..., alias="teamCapacity", gt=0, description="Total team capacity in hours"
    )
    critical_deadlines: list[CriticalDeadline] = Field(
        default_factory=list, alias="criticalDeadlines", description="Critical deadlines"
    )
    team_availability: list[TeamAvailability] = Field(
        default_factory=list, alias="teamAvailability", description="Team availability"
    )


class SchedulingRequest(BaseModel):
    """Request for scheduling suggestions."""

    actions: list[SchedulingActionInput] = Field(
        ..., min_length=1, max_length=100, description="Actions to schedule"
    )
    constraints: SchedulingConstraints = Field(..., description="Scheduling constraints")


class AlternativeSchedule(BaseModel):
    """Alternative schedule option."""

    start_date: str = Field(..., alias="startDate", description="Alternative start date")
    due_date: str = Field(..., alias="dueDate", description="Alternative due date")
    rationale: str = Field(..., description="Rationale for this alternative")


class SchedulingSuggestion(BaseModel):
    """Scheduling suggestion for an action."""

    action_id: str = Field(..., alias="actionId", description="Action identifier")
    suggested_start_date: str = Field(
        ..., alias="suggestedStartDate", description="Suggested start date"
    )
    suggested_due_date: str = Field(..., alias="suggestedDueDate", description="Suggested due date")
    reasoning: str = Field(..., description="Reasoning for schedule")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    dependencies: list[str] = Field(..., description="Dependencies that influenced schedule")
    resource_considerations: list[str] = Field(
        ..., alias="resourceConsiderations", description="Resource considerations"
    )
    risks: list[str] = Field(..., description="Identified risks")
    alternative_schedules: list[AlternativeSchedule] = Field(
        default_factory=list, description="Alternative scheduling options"
    )


class SchedulingResponse(BaseModel):
    """Response for scheduling suggestions."""

    success: bool = Field(default=True, description="Request success status")
    data: list[SchedulingSuggestion] = Field(..., description="Scheduling suggestions")


# ============================================================================
# Root Cause Analysis Models (Issue #64)
# ============================================================================


class IssueContext(BaseModel):
    """Context for an issue requiring root cause analysis."""

    reported_by: str | None = Field(
        None, alias="reportedBy", description="Person who reported the issue"
    )
    date_reported: str | None = Field(
        None, alias="dateReported", description="Date issue was reported"
    )
    related_actions: list[str] = Field(
        alias="relatedActions", default_factory=list, description="Related action IDs"
    )
    affected_areas: list[str] = Field(
        alias="affectedAreas", default_factory=list, description="Business areas affected"
    )


class RootCauseRequest(BaseModel):
    """Request for root cause analysis suggestions."""

    issue_title: str = Field(
        ..., alias="issueTitle", min_length=1, max_length=200, description="Issue title"
    )
    issue_description: str = Field(
        ..., min_length=10, max_length=5000, description="Detailed issue description"
    )
    business_impact: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Business impact level"
    )
    context: IssueContext = Field(
        default_factory=lambda: IssueContext(reportedBy=None, dateReported=None), description="Additional context"
    )


class RootCauseMethodSuggestion(BaseModel):
    """Suggestion for a root cause analysis method."""

    method: Literal["five_whys", "fishbone", "swot", "pareto"] = Field(
        ..., description="Analysis method"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in this method's applicability"
    )
    suggestions: dict[str, Any] = Field(..., description="Method-specific suggestions")
    reasoning: str = Field(..., description="Why this method is recommended")


class RootCauseResponse(BaseModel):
    """Response for root cause analysis suggestions."""

    success: bool = Field(default=True, description="Request success status")
    data: list[RootCauseMethodSuggestion] = Field(..., description="Root cause method suggestions")


# ============================================================================
# Action Plan Suggestions Models (Issue #64)
# ============================================================================


class ActionIssue(BaseModel):
    """Issue for which to generate action plan."""

    title: str = Field(..., min_length=1, description="Issue title")
    description: str = Field(..., min_length=10, description="Issue description")
    impact: Literal["low", "medium", "high", "critical"] = Field(..., description="Business impact")
    root_cause: str | None = Field(None, alias="rootCause", description="Identified root cause")


class ActionConstraints(BaseModel):
    """Constraints for action plan generation."""

    timeline: str | None = Field(None, description="Timeline constraint")
    budget: int | None = Field(None, ge=0, description="Budget constraint")
    available_resources: list[str] = Field(
        alias="availableResources", default_factory=list, description="Available resources"
    )


class ActionPlanContext(BaseModel):
    """Context for action plan generation."""

    related_goals: list[str] = Field(
        alias="relatedGoals", default_factory=list, description="Related business goals"
    )
    current_actions: list[str] = Field(
        alias="currentActions", default_factory=list, description="Current ongoing actions"
    )
    business_priorities: list[str] = Field(
        default_factory=list, description="Current business priorities"
    )


class ActionPlanRequest(BaseModel):
    """Request for action plan suggestions."""

    issue: ActionIssue = Field(..., description="Issue to address")
    constraints: ActionConstraints = Field(
        default_factory=lambda: ActionConstraints(timeline=None, budget=None), description="Constraints"
    )
    context: ActionPlanContext = Field(
        default_factory=lambda: ActionPlanContext(), description="Business context"
    )


class ActionSuggestion(BaseModel):
    """A suggested action for the plan."""

    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Detailed action description")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Action priority"
    )
    estimated_duration: int = Field(
        ..., alias="estimatedDuration", gt=0, description="Estimated hours"
    )
    estimated_cost: int | None = Field(
        None, alias="estimatedCost", ge=0, description="Estimated cost"
    )
    assignment_suggestion: str | None = Field(
        None, alias="assignmentSuggestion", description="Who should be assigned"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Dependencies on other actions"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this action")
    reasoning: str = Field(..., description="Why this action is recommended")
    expected_outcome: str = Field(..., alias="expectedOutcome", description="Expected result")
    risks: list[str] = Field(default_factory=list, description="Identified risks")


class ActionPlanResponse(BaseModel):
    """Response for action plan suggestions."""

    success: bool = Field(default=True, description="Request success status")
    data: list[ActionSuggestion] = Field(..., description="Action suggestions")


__all__ = [
    "ActionAlignmentAnalysis",
    "ActionConstraints",
    # Strategic Alignment
    "ActionInput",
    # Action Plan Suggestions (Issue #64)
    "ActionIssue",
    "ActionPlanContext",
    "ActionPlanRequest",
    "ActionPlanResponse",
    "ActionSuggestion",
    "AlternativeSchedule",
    "BusinessContext",
    "BusinessFoundationInput",
    "CriticalDeadline",
    "GoalInput",
    # Root Cause Analysis (Issue #64)
    "IssueContext",
    # Prioritization
    "PrioritizationActionInput",
    "PrioritizationRequest",
    "PrioritizationResponse",
    "PrioritizationSuggestion",
    "RootCauseMethodSuggestion",
    "RootCauseRequest",
    "RootCauseResponse",
    # Scheduling
    "SchedulingActionInput",
    "SchedulingConstraints",
    "SchedulingRequest",
    "SchedulingResponse",
    "SchedulingSuggestion",
    "StrategicAlignmentRequest",
    "StrategicAlignmentResponse",
    "StrategicConnection",
    "TeamAvailability",
]
