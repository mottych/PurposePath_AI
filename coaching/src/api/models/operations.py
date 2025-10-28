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
    coreValues: list[str] = Field(..., min_items=1, description="Core values")


class StrategicAlignmentRequest(BaseModel):
    """Request for strategic alignment analysis."""

    actions: list[ActionInput] = Field(
        ..., min_items=1, max_items=100, description="Actions to analyze"
    )
    goals: list[GoalInput] = Field(..., min_items=1, max_items=50, description="Business goals")
    businessFoundation: BusinessFoundationInput = Field(
        ..., description="Business foundation context"
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

    goalId: str = Field(..., description="Goal identifier")
    goalTitle: str = Field(..., description="Goal title/intent")
    alignmentScore: int = Field(..., ge=0, le=100, description="Alignment score (0-100)")
    impact: Literal["low", "medium", "high", "critical"] = Field(..., description="Impact level")


class ActionAlignmentAnalysis(BaseModel):
    """Alignment analysis for a single action."""

    actionId: str = Field(..., description="Action identifier")
    alignmentScore: int = Field(..., ge=0, le=100, description="Overall alignment score")
    strategicConnections: list[StrategicConnection] = Field(..., description="Connections to goals")
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
    currentPriority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Current priority"
    )
    dueDate: str | None = Field(None, description="Due date (ISO format)")
    impact: str | None = Field(None, description="Expected impact description")
    effort: str | None = Field(None, description="Required effort description")
    status: str = Field(..., description="Current status")
    linkedGoals: list[str] = Field(default_factory=list, description="Linked goal IDs")


class BusinessContext(BaseModel):
    """Business context for prioritization."""

    currentGoals: list[str] = Field(default_factory=list, description="Current business goals")
    constraints: list[str] = Field(default_factory=list, description="Business constraints")
    urgentDeadlines: list[str] = Field(default_factory=list, description="Urgent deadlines")


class PrioritizationRequest(BaseModel):
    """Request for action prioritization suggestions."""

    actions: list[PrioritizationActionInput] = Field(
        ..., min_items=1, max_items=200, description="Actions to prioritize"
    )
    businessContext: BusinessContext = Field(..., description="Business context for prioritization")


class PrioritizationSuggestion(BaseModel):
    """Prioritization suggestion for an action."""

    actionId: str = Field(..., description="Action identifier")
    suggestedPriority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Suggested priority level"
    )
    currentPriority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Current priority level"
    )
    reasoning: str = Field(..., description="Reasoning for suggestion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    urgencyFactors: list[str] = Field(..., description="Factors contributing to urgency")
    impactFactors: list[str] = Field(..., description="Factors contributing to impact")
    recommendedAction: Literal["escalate", "maintain", "de-prioritize"] = Field(
        ..., description="Recommended action"
    )
    estimatedBusinessValue: int | None = Field(
        None, description="Estimated business value in currency units"
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
    estimatedDuration: int = Field(..., gt=0, description="Estimated duration in hours")
    dependencies: list[str] = Field(default_factory=list, description="Action IDs this depends on")
    assignedTo: str | None = Field(None, description="Assigned person/team ID")
    currentStartDate: str | None = Field(None, description="Current start date")
    currentDueDate: str | None = Field(None, description="Current due date")
    priority: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Priority level"
    )


class CriticalDeadline(BaseModel):
    """Critical deadline constraint."""

    date: str = Field(..., description="Deadline date (ISO format)")
    description: str = Field(..., description="Deadline description")


class TeamAvailability(BaseModel):
    """Team member availability."""

    personId: str = Field(..., description="Person/team member identifier")
    hoursPerWeek: int = Field(..., gt=0, le=168, description="Available hours per week")
    unavailableDates: list[str] = Field(
        default_factory=list, description="Unavailable dates (ISO format)"
    )


class SchedulingConstraints(BaseModel):
    """Scheduling constraints."""

    teamCapacity: int = Field(..., gt=0, description="Total team capacity in hours")
    criticalDeadlines: list[CriticalDeadline] = Field(
        default_factory=list, description="Critical deadlines"
    )
    teamAvailability: list[TeamAvailability] = Field(
        default_factory=list, description="Team availability"
    )


class SchedulingRequest(BaseModel):
    """Request for scheduling suggestions."""

    actions: list[SchedulingActionInput] = Field(
        ..., min_items=1, max_items=100, description="Actions to schedule"
    )
    constraints: SchedulingConstraints = Field(..., description="Scheduling constraints")


class AlternativeSchedule(BaseModel):
    """Alternative schedule option."""

    startDate: str = Field(..., description="Alternative start date")
    dueDate: str = Field(..., description="Alternative due date")
    rationale: str = Field(..., description="Rationale for this alternative")


class SchedulingSuggestion(BaseModel):
    """Scheduling suggestion for an action."""

    actionId: str = Field(..., description="Action identifier")
    suggestedStartDate: str = Field(..., description="Suggested start date")
    suggestedDueDate: str = Field(..., description="Suggested due date")
    reasoning: str = Field(..., description="Reasoning for schedule")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    dependencies: list[str] = Field(..., description="Dependencies that influenced schedule")
    resourceConsiderations: list[str] = Field(..., description="Resource considerations")
    risks: list[str] = Field(..., description="Identified risks")
    alternativeSchedules: list[AlternativeSchedule] = Field(
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

    reportedBy: str | None = Field(None, description="Person who reported the issue")
    dateReported: str | None = Field(None, description="Date issue was reported")
    relatedActions: list[str] = Field(default_factory=list, description="Related action IDs")
    affectedAreas: list[str] = Field(default_factory=list, description="Business areas affected")


class RootCauseRequest(BaseModel):
    """Request for root cause analysis suggestions."""

    issueTitle: str = Field(..., min_length=1, max_length=200, description="Issue title")
    issueDescription: str = Field(
        ..., min_length=10, max_length=5000, description="Detailed issue description"
    )
    businessImpact: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Business impact level"
    )
    context: IssueContext = Field(
        default_factory=lambda: IssueContext(), description="Additional context"
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
    rootCause: str | None = Field(None, description="Identified root cause")


class ActionConstraints(BaseModel):
    """Constraints for action plan generation."""

    timeline: str | None = Field(None, description="Timeline constraint")
    budget: int | None = Field(None, ge=0, description="Budget constraint")
    availableResources: list[str] = Field(default_factory=list, description="Available resources")


class ActionPlanContext(BaseModel):
    """Context for action plan generation."""

    relatedGoals: list[str] = Field(default_factory=list, description="Related business goals")
    currentActions: list[str] = Field(default_factory=list, description="Current ongoing actions")
    businessPriorities: list[str] = Field(
        default_factory=list, description="Current business priorities"
    )


class ActionPlanRequest(BaseModel):
    """Request for action plan suggestions."""

    issue: ActionIssue = Field(..., description="Issue to address")
    constraints: ActionConstraints = Field(
        default_factory=lambda: ActionConstraints(), description="Constraints"
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
    estimatedDuration: int = Field(..., gt=0, description="Estimated hours")
    estimatedCost: int | None = Field(None, ge=0, description="Estimated cost")
    assignmentSuggestion: str | None = Field(None, description="Who should be assigned")
    dependencies: list[str] = Field(
        default_factory=list, description="Dependencies on other actions"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this action")
    reasoning: str = Field(..., description="Why this action is recommended")
    expectedOutcome: str = Field(..., description="Expected result")
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
