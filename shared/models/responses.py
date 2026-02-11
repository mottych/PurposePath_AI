"""API response models for all endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, computed_field

from .base import BaseResponseModel, PaginatedResponse
from .domain import (
    ActionStatus,
    DecisionType,
    IssueType,
    Priority,
    ReviewType,
    TimeHorizon,
)


# Issue Response Models
class IssueResponse(BaseResponseModel):
    """Response model for a single issue."""

    id: str = Field(..., description="Unique issue identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., description="Issue title")
    description: str | None = Field(None, description="Detailed description")

    # Classification
    issue_type: IssueType = Field(..., description="Type of issue")
    status: ActionStatus = Field(..., description="Current status")
    priority: Priority = Field(..., description="Priority level")

    # Relationships
    goal_id: str | None = Field(None, description="Associated goal ID")
    owner_id: str | None = Field(None, description="Assigned owner user ID")
    reporter_id: str | None = Field(None, description="User who reported the issue")

    # Tracking
    tags: list[str] = Field(default_factory=list, description="Issue tags")
    due_date: datetime | None = Field(None, description="Due date")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    # Effort tracking
    estimated_effort: int | None = Field(None, description="Estimated effort in hours")
    actual_effort: int | None = Field(None, description="Actual effort in hours")

    # Root Cause Analysis
    root_cause_analysis: dict[str, Any] | None = Field(None, description="RCA data")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @computed_field
    def is_overdue(self) -> bool:
        """Check if issue is overdue."""
        if not self.due_date or self.status == ActionStatus.COMPLETED:
            return False
        return datetime.now() > self.due_date

    @computed_field
    def effort_variance(self) -> float | None:
        """Calculate effort variance (actual vs estimated)."""
        if self.estimated_effort is None or self.actual_effort is None:
            return None
        if self.estimated_effort == 0:
            return 0.0
        return ((self.actual_effort - self.estimated_effort) / self.estimated_effort) * 100


class IssueListResponse(BaseResponseModel):
    """Response model for listing issues."""

    issues: list[IssueResponse] = Field(..., description="List of issues")
    total: int = Field(..., description="Total number of issues matching filters")


class IssueSummary(BaseResponseModel):
    """Summary response for issue lists."""

    id: str = Field(..., description="Issue ID")
    title: str = Field(..., description="Issue title")
    issue_type: IssueType = Field(..., description="Type of issue")
    status: ActionStatus = Field(..., description="Current status")
    priority: Priority = Field(..., description="Priority level")
    owner_id: str | None = Field(None, description="Assigned owner user ID")
    due_date: datetime | None = Field(None, description="Due date")
    created_at: datetime = Field(..., description="Creation timestamp")

    @computed_field
    def is_overdue(self) -> bool:
        """Check if issue is overdue."""
        if not self.due_date or self.status == ActionStatus.COMPLETED:
            return False
        return datetime.now() > self.due_date


# Goal Response Models
class GoalResponse(BaseResponseModel):
    """Response model for a single goal."""

    id: str = Field(..., description="Unique goal identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., description="Goal title")
    description: str | None = Field(None, description="Detailed description")

    # Classification
    status: ActionStatus = Field(..., description="Current status")
    time_horizon: TimeHorizon = Field(..., description="Time horizon")

    # Measurement
    target_value: float | None = Field(None, description="Target value for the goal")
    current_value: float | None = Field(None, description="Current progress value")
    unit: str | None = Field(None, description="Unit of measurement")

    # Relationships
    owner_id: str | None = Field(None, description="Goal owner user ID")
    parent_goal_id: str | None = Field(None, description="Parent goal ID")

    # Tracking
    tags: list[str] = Field(default_factory=list, description="Goal tags")
    due_date: datetime | None = Field(None, description="Target completion date")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    # Goal details
    success_criteria: list[str] = Field(default_factory=list, description="Success criteria")
    obstacles: list[str] = Field(default_factory=list, description="Identified obstacles")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @computed_field
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.target_value is None or self.current_value is None:
            return 0.0
        if self.target_value == 0:
            return 100.0 if self.current_value > 0 else 0.0
        return min(100.0, max(0.0, (self.current_value / self.target_value) * 100))

    @computed_field
    def is_overdue(self) -> bool:
        """Check if goal is overdue."""
        if not self.due_date or self.status == ActionStatus.COMPLETED:
            return False
        return datetime.now() > self.due_date


class GoalListResponse(BaseResponseModel):
    """Response model for listing goals."""

    goals: list[GoalResponse] = Field(..., description="List of goals")
    total: int = Field(..., description="Total number of goals matching filters")


class GoalSummary(BaseResponseModel):
    """Summary response for goal lists."""

    id: str = Field(..., description="Goal ID")
    title: str = Field(..., description="Goal title")
    status: ActionStatus = Field(..., description="Current status")
    time_horizon: TimeHorizon = Field(..., description="Time horizon")
    progress_percentage: float = Field(..., description="Progress percentage")
    owner_id: str | None = Field(None, description="Goal owner user ID")
    due_date: datetime | None = Field(None, description="Target completion date")
    created_at: datetime = Field(..., description="Creation timestamp")


# Strategy Response Models
class StrategyResponse(BaseResponseModel):
    """Response model for a single strategy."""

    id: str = Field(..., description="Unique strategy identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., description="Strategy title")
    description: str | None = Field(None, description="Detailed description")

    # Relationships
    goal_id: str = Field(..., description="Associated goal ID")
    owner_id: str | None = Field(None, description="Strategy owner user ID")

    # Classification
    status: ActionStatus = Field(..., description="Current status")
    priority: Priority = Field(..., description="Priority level")

    # Tracking
    tags: list[str] = Field(default_factory=list, description="Strategy tags")
    due_date: datetime | None = Field(None, description="Target completion date")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    # Strategy details
    success_metrics: list[str] = Field(default_factory=list, description="Success metrics")
    resources_required: list[str] = Field(default_factory=list, description="Required resources")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class StrategyListResponse(BaseResponseModel):
    """Response model for listing strategies."""

    strategies: list[StrategyResponse] = Field(..., description="List of strategies")
    total: int = Field(..., description="Total number of strategies matching filters")


# Measure Response Models
class MeasureResponse(BaseResponseModel):
    """Response model for a single Measure."""

    id: str = Field(..., description="Unique Measure identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    name: str = Field(..., description="Measure name")
    description: str | None = Field(None, description="Measure description")

    # Measurement
    current_value: float = Field(..., description="Current Measure value")
    target_value: float | None = Field(None, description="Target Measure value")
    unit: str = Field(..., description="Unit of measurement")

    # Relationships
    goal_id: str | None = Field(None, description="Associated goal ID")
    owner_id: str | None = Field(None, description="Measure owner user ID")

    # Configuration
    measurement_frequency: str = Field(..., description="Measurement frequency")
    data_source: str | None = Field(None, description="Source of Measure data")
    calculation_method: str | None = Field(None, description="Calculation method")

    # Tracking
    last_measured: datetime | None = Field(None, description="Last measurement date")
    trend: str | None = Field(None, description="Trend direction")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    @computed_field
    def achievement_percentage(self) -> float:
        """Calculate achievement percentage against target."""
        if self.target_value is None or self.target_value == 0:
            return 0.0
        return min(100.0, max(0.0, (self.current_value / self.target_value) * 100))


class MeasureListResponse(BaseResponseModel):
    """Response model for listing Measures."""

    measures: list[MeasureResponse] = Field(..., description="List of Measures")
    total: int = Field(..., description="Total number of Measures matching filters")


# Review Response Models
class ReviewResponse(BaseResponseModel):
    """Response model for a single review."""

    id: str = Field(..., description="Unique review identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., description="Review title")
    review_type: ReviewType = Field(..., description="Type of review")
    content: str = Field(..., description="Review content")

    # Relationships
    goal_id: str | None = Field(None, description="Associated goal ID")
    reviewer_id: str = Field(..., description="User who conducted the review")

    # Review data
    status: ActionStatus = Field(..., description="Review status")
    review_date: datetime = Field(..., description="Date of the review")
    next_review_date: datetime | None = Field(None, description="Next scheduled review")

    # Outcomes
    key_insights: list[str] = Field(default_factory=list, description="Key insights")
    action_items: list[str] = Field(default_factory=list, description="Action items")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations")

    # Metadata
    participants: list[str] = Field(default_factory=list, description="Participants")
    attachments: list[str] = Field(default_factory=list, description="Attached documents")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ReviewListResponse(BaseResponseModel):
    """Response model for listing reviews."""

    reviews: list[ReviewResponse] = Field(..., description="List of reviews")
    total: int = Field(..., description="Total number of reviews matching filters")


# Decision Response Models
class DecisionResponse(BaseResponseModel):
    """Response model for a single decision."""

    id: str = Field(..., description="Unique decision identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., description="Decision title")
    description: str = Field(..., description="Decision description")
    decision_type: DecisionType = Field(..., description="Type of decision")

    # Decision process
    decision_maker_id: str = Field(..., description="Primary decision maker user ID")
    stakeholders: list[str] = Field(default_factory=list, description="Stakeholder user IDs")
    decision_date: datetime | None = Field(None, description="When decision was made")

    # Decision details
    options_considered: list[str] = Field(default_factory=list, description="Options considered")
    rationale: str | None = Field(None, description="Decision rationale")
    expected_outcomes: list[str] = Field(default_factory=list, description="Expected outcomes")

    # Status and tracking
    status: ActionStatus = Field(..., description="Implementation status")
    implementation_date: datetime | None = Field(None, description="Implementation date")
    review_date: datetime | None = Field(None, description="Review date")

    # Impact tracking
    actual_outcomes: list[str] = Field(default_factory=list, description="Actual outcomes")
    success_rating: int | None = Field(None, description="Success rating (1-5)")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class DecisionListResponse(BaseResponseModel):
    """Response model for listing decisions."""

    decisions: list[DecisionResponse] = Field(..., description="List of decisions")
    total: int = Field(..., description="Total number of decisions matching filters")


# Activity Response Models
class ActivityResponse(BaseResponseModel):
    """Response model for a single activity."""

    id: str = Field(..., description="Unique activity identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    text: str = Field(..., description="Activity description")
    activity_type: str = Field(..., description="Type of activity")

    # Relationships
    user_id: str = Field(..., description="User who performed the activity")
    goal_id: str | None = Field(None, description="Associated goal ID")
    issue_id: str | None = Field(None, description="Associated issue ID")

    # Metadata
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional activity data")
    is_system_generated: bool = Field(..., description="Whether system generated")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ActivityListResponse(BaseResponseModel):
    """Response model for listing activities."""

    activities: list[ActivityResponse] = Field(..., description="List of activities")
    total: int = Field(..., description="Total number of activities matching filters")


# Report Response Models
class ReportResponse(BaseResponseModel):
    """Response model for a single report."""

    id: str = Field(..., description="Unique report identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., description="Report title")
    report_type: str = Field(..., description="Type of report")

    # Report data
    data: dict[str, Any] = Field(..., description="Report data")
    parameters: dict[str, str] = Field(default_factory=dict, description="Report parameters")

    # Generation info
    generated_by_id: str = Field(..., description="User who generated the report")
    generated_at: datetime = Field(..., description="Generation timestamp")

    # Status
    status: str = Field(..., description="Report generation status")
    format: str = Field(..., description="Report format")

    # Metadata
    description: str | None = Field(None, description="Report description")
    tags: list[str] = Field(default_factory=list, description="Report tags")
    expires_at: datetime | None = Field(None, description="Report expiration date")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ReportListResponse(BaseResponseModel):
    """Response model for listing reports."""

    reports: list[ReportResponse] = Field(..., description="List of reports")
    total: int = Field(..., description="Total number of reports matching filters")


# Specialized Response Models
class DashboardSummary(BaseResponseModel):
    """Dashboard summary response."""

    total_goals: int = Field(..., description="Total number of goals")
    active_goals: int = Field(..., description="Number of active goals")
    completed_goals: int = Field(..., description="Number of completed goals")
    overdue_goals: int = Field(..., description="Number of overdue goals")

    total_issues: int = Field(..., description="Total number of issues")
    open_issues: int = Field(..., description="Number of open issues")
    critical_issues: int = Field(..., description="Number of critical issues")

    recent_activities: list[ActivityResponse] = Field(..., description="Recent activities")

    # Performance metrics
    goals_completion_rate: float = Field(..., description="Goals completion rate percentage")
    average_issue_resolution_time: float | None = Field(
        None, description="Average resolution time in hours"
    )


class BulkOperationResponse(BaseResponseModel):
    """Response for bulk operations."""

    total_requested: int = Field(..., description="Total items requested for operation")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: list[str] = Field(
        default_factory=list, description="Error messages for failed operations"
    )
    updated_ids: list[str] = Field(
        default_factory=list, description="IDs of successfully updated items"
    )


class HealthCheckResponse(BaseResponseModel):
    """Health check response."""

    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str | None = Field(None, description="Service version")
    service: str = Field(..., description="Service name")
    dependencies: dict[str, str] = Field(default_factory=dict, description="Dependency status")


class MetricsResponse(BaseResponseModel):
    """Metrics and analytics response."""

    metric_type: str = Field(..., description="Type of metrics")
    time_period: str = Field(..., description="Time period for metrics")
    data_points: list[dict[str, Any]] = Field(..., description="Metric data points")
    summary: dict[str, str] = Field(default_factory=dict, description="Summary statistics")
    generated_at: datetime = Field(..., description="Metrics generation timestamp")


# Note and Attachment Responses
class NoteResponse(BaseResponseModel):
    """Response for notes."""

    id: str = Field(..., description="Note ID")
    note: str = Field(..., description="Note content")
    attachments: list[str] = Field(default_factory=list, description="Attachment IDs")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="User who created the note")


class AttachmentResponse(BaseResponseModel):
    """Response for file attachments."""

    id: str = Field(..., description="Attachment ID")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    size: int = Field(..., description="File size in bytes")
    url: str | None = Field(None, description="Access URL")
    created_at: datetime = Field(..., description="Upload timestamp")
    created_by: str = Field(..., description="User who uploaded the file")


# Plan and Action Response Models
class ActionResponse(BaseResponseModel):
    """Response model for a single action."""

    action_id: str = Field(..., description="Unique action identifier")
    goal_id: str = Field(..., description="Associated goal ID")
    milestone_id: str | None = Field(None, description="Associated milestone ID")
    title: str = Field(..., description="Action title")
    status: str | None = Field(None, description="Current status")
    column: str | None = Field(None, description="Kanban column")
    owner_id: str | None = Field(None, description="Assigned owner user ID")
    due_date: datetime | None = Field(None, description="Due date")
    tag: str | None = Field(None, description="Action tag")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MilestoneResponse(BaseResponseModel):
    """Response model for a single milestone."""

    milestone_id: str = Field(..., description="Unique milestone identifier")
    goal_id: str = Field(..., description="Associated goal ID")
    title: str = Field(..., description="Milestone title")
    start_date: datetime | None = Field(None, description="Start date")
    due_date: datetime | None = Field(None, description="Due date")
    status: str | None = Field(None, description="Current status")
    dependencies: list[str] = Field(default_factory=list, description="Dependent milestone IDs")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PlanResponse(BaseResponseModel):
    """Response model for a goal plan with milestones and actions."""

    goal_id: str = Field(..., description="Goal identifier")
    # Pylance has intermittent resolution issues with these types despite proper definition
    milestones: list[MilestoneResponse] = Field(default_factory=list, description="Plan milestones")  # pyright: ignore[reportUnknownVariableType]
    actions: list[ActionResponse] = Field(default_factory=list, description="Plan actions")  # pyright: ignore[reportUnknownVariableType]
    total_milestones: int = Field(default=0, description="Total milestone count")
    total_actions: int = Field(default=0, description="Total action count")
    completion_percentage: float = Field(default=0.0, description="Overall completion percentage")


class DeleteResponse(BaseResponseModel):
    """Response model for delete operations."""

    deleted: bool = Field(..., description="Whether the delete was successful")
    resource_id: str | None = Field(None, description="ID of the deleted resource")
    message: str | None = Field(None, description="Success message")


class GoalNoteResponse(BaseResponseModel):
    """Response model for a goal note."""

    id: str = Field(..., description="Note identifier")
    note: str = Field(..., description="Note content")
    attachments: list[str] = Field(default_factory=list, description="Attachment IDs")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="User who created the note")


class TargetUpdateResponse(BaseResponseModel):
    """Response model for target updates."""

    updated: bool = Field(..., description="Whether the update was successful")
    target_count: int | None = Field(None, description="Total number of targets")


class ProposalResponse(BaseResponseModel):
    """Response model for a goal proposal."""

    id: str = Field(..., description="Proposal identifier")
    title: str = Field(..., description="Proposal title")
    description: str | None = Field(None, description="Proposal description")
    rationale: str | None = Field(None, description="Rationale for proposal")
    estimated_impact: str | None = Field(None, description="Estimated impact")
    priority: Priority = Field(..., description="Proposal priority")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str = Field(..., description="User who created the proposal")


class MeasureReadingResponse(BaseResponseModel):
    """Response model for Measure reading operations."""

    period: str = Field(..., description="Reading period")
    adjusted_value: float = Field(..., description="Adjusted value")
    reason: str | None = Field(None, description="Reason for adjustment")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: str | None = Field(None, description="User who created the reading")


class MeasureLinkResponse(BaseResponseModel):
    """Response model for Measure-Goal link operations."""

    goal_id: str = Field(..., description="Goal identifier")
    measure_id: str = Field(..., description="Measure identifier")
    threshold_pct: float | None = Field(None, description="Threshold percentage")
    created_at: datetime = Field(..., description="Link creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Integrity and Alignment Response Models
class AlignmentDriversResponse(BaseResponseModel):
    """Response model for alignment drivers."""

    measure_performance: float = Field(
        ..., alias="measurePerformance", description="Measure performance score"
    )
    plan_health: float = Field(..., alias="planHealth", description="Plan health score")
    cadence_adherence: float = Field(
        ..., alias="cadenceAdherence", description="Cadence adherence score"
    )
    value_action_coherence: float = Field(
        ..., alias="valueActionCoherence", description="Value-action coherence score"
    )


class AlignmentScoreResponse(BaseResponseModel):
    """Response model for goal alignment score."""

    score: float = Field(..., description="Overall alignment score")
    drivers: AlignmentDriversResponse = Field(..., description="Individual driver scores")


class GoalAlignmentBreakdownResponse(BaseResponseModel):
    """Response model for individual goal alignment breakdown."""

    goal_id: str = Field(..., description="Goal identifier")
    title: str = Field(..., description="Goal title")
    score: float = Field(..., description="Goal alignment score")
    drivers: AlignmentDriversResponse = Field(..., description="Driver scores for this goal")


class AlignmentCalculationResponse(BaseResponseModel):
    """Response model for alignment calculation across all goals."""

    overall_score: float = Field(..., description="Overall alignment score across all goals")
    goals: list[GoalAlignmentBreakdownResponse] = Field(
        ..., description="Per-goal alignment breakdown"
    )


class IntegrityAlertResponse(BaseResponseModel):
    """Response model for integrity alerts."""

    alert_id: str = Field(..., description="Alert identifier")
    goal_id: str = Field(..., description="Related goal identifier")
    alert_type: str | None = Field(None, description="Type of integrity alert")
    message: str | None = Field(None, description="Alert message")
    severity: str | None = Field(None, description="Alert severity level")
    justification: str | None = Field(None, description="Justification if resolved")
    resolved_at: datetime | None = Field(None, description="Resolution timestamp")
    resolved_by: str | None = Field(None, description="User who resolved the alert")
    created_at: datetime | None = Field(None, description="Alert creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")


# Paginated versions using the new base classes
IssuesPaginatedResponse = PaginatedResponse[IssueSummary]
GoalsPaginatedResponse = PaginatedResponse[GoalSummary]
StrategiesPaginatedResponse = PaginatedResponse[StrategyResponse]
MeasuresPaginatedResponse = PaginatedResponse[MeasureResponse]
ReviewsPaginatedResponse = PaginatedResponse[ReviewResponse]
DecisionsPaginatedResponse = PaginatedResponse[DecisionResponse]
ActivitiesPaginatedResponse = PaginatedResponse[ActivityResponse]
ReportsPaginatedResponse = PaginatedResponse[ReportResponse]
ActionsPaginatedResponse = PaginatedResponse[ActionResponse]
