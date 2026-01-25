"""
Pydantic request models for the PurposePath API.

This module provides request validation models for all API operations,
ensuring type safety and proper validation of incoming data.
"""

from datetime import datetime

from pydantic import Field, field_validator

from shared.models.base import BaseRequestModel
from shared.models.domain import (
    ActionStatus,
    DecisionType,
    IssueType,
    Priority,
    ReviewType,
    TimeHorizon,
)


class BulkDeleteRequest(BaseRequestModel):
    """Request to delete multiple items."""

    ids: list[str] = Field(min_length=1, max_length=100, description="Item IDs to delete")
    confirm: bool = Field(description="Confirmation required for bulk delete")
    reason: str | None = Field(default=None, max_length=500, description="Reason for bulk delete")


# User Preferences Request Models
class UserPreferencesUpdateRequest(BaseRequestModel):
    """Request to update user preferences."""

    notifications: dict[str, bool] | None = Field(
        default=None, description="Notification preferences"
    )
    timezone: str | None = Field(
        default=None, max_length=50, description="User timezone preference"
    )
    language: str | None = Field(
        default=None, max_length=10, description="User language preference"
    )
    theme: str | None = Field(default=None, description="UI theme preference")
    date_format: str | None = Field(default=None, description="Date format preference")
    time_format: str | None = Field(default=None, description="Time format preference")
    currency: str | None = Field(default=None, max_length=10, description="Currency preference")

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str | None) -> str | None:
        """Validate theme preference."""
        if v is not None and v not in ["light", "dark", "auto"]:
            raise ValueError("Theme must be 'light', 'dark', or 'auto'")
        return v

    @field_validator("time_format")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        """Validate time format preference."""
        if v is not None and v not in ["12h", "24h"]:
            raise ValueError("Time format must be '12h' or '24h'")
        return v

    class Config:
        extra = "allow"  # Allow additional preference fields


# Issue Request Models
class CreateIssueRequest(BaseRequestModel):
    """Request to create a new issue."""

    title: str = Field(min_length=1, max_length=200, description="Issue title")
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    issue_type: IssueType = Field(default=IssueType.TASK, description="Type of issue")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    goal_id: str | None = Field(default=None, description="Associated goal ID")
    owner_id: str | None = Field(default=None, description="Assigned owner user ID")
    tags: list[str] = Field(default_factory=lambda: [], max_length=10, description="Issue tags")
    due_date: datetime | None = Field(default=None, description="Due date")
    estimated_effort: int | None = Field(
        default=None, ge=1, le=1000, description="Estimated effort in hours"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty after stripping."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Validate and clean tags."""
        return [tag.strip() for tag in v if tag.strip()]


class UpdateIssueRequest(BaseRequestModel):
    """Request to update an existing issue."""

    title: str | None = Field(default=None, min_length=1, max_length=200, description="Issue title")
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    issue_type: IssueType | None = Field(default=None, description="Type of issue")
    status: ActionStatus | None = Field(default=None, description="Current status")
    priority: Priority | None = Field(default=None, description="Priority level")
    goal_id: str | None = Field(default=None, description="Associated goal ID")
    owner_id: str | None = Field(default=None, description="Assigned owner user ID")
    tags: list[str] | None = Field(default=None, max_length=10, description="Issue tags")
    due_date: datetime | None = Field(default=None, description="Due date")
    estimated_effort: int | None = Field(
        default=None, ge=1, le=1000, description="Estimated effort in hours"
    )
    actual_effort: int | None = Field(
        default=None, ge=0, le=1000, description="Actual effort in hours"
    )


class ListIssuesRequest(BaseRequestModel):
    """Request to list issues with filtering."""

    goal_id: str | None = Field(default=None, description="Filter by goal ID")
    status: ActionStatus | None = Field(default=None, description="Filter by status")
    priority: Priority | None = Field(default=None, description="Filter by priority")
    owner_id: str | None = Field(default=None, description="Filter by owner ID")
    issue_type: IssueType | None = Field(default=None, description="Filter by issue type")
    tags: list[str] | None = Field(default=None, description="Filter by tags (any match)")
    search: str | None = Field(
        default=None, max_length=100, description="Search in title/description"
    )


class RootCauseAnalysisRequest(BaseRequestModel):
    """Request to perform root cause analysis on an issue."""

    method: str = Field(default="5-whys", description="RCA method to use")
    root_causes: list[str] = Field(min_length=1, description="Identified root causes")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence level (0-1)")
    analysis_notes: str | None = Field(
        default=None, max_length=2000, description="Additional analysis notes"
    )


# Goal Request Models
class CreateGoalRequest(BaseRequestModel):
    """Request to create a new goal."""

    title: str = Field(min_length=3, max_length=200, description="Goal title")
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    time_horizon: TimeHorizon = Field(default=TimeHorizon.QUARTERLY, description="Time horizon")
    target_value: float | None = Field(default=None, description="Target value for the goal")
    current_value: float | None = Field(default=None, description="Current progress value")
    unit: str | None = Field(default=None, max_length=50, description="Unit of measurement")
    owner_id: str | None = Field(default=None, description="Goal owner user ID")
    parent_goal_id: str | None = Field(default=None, description="Parent goal ID")
    tags: list[str] = Field(default_factory=lambda: [], max_length=10, description="Goal tags")
    due_date: datetime | None = Field(default=None, description="Target completion date")
    success_criteria: list[str] = Field(default_factory=lambda: [], description="Success criteria")


class UpdateGoalRequest(BaseRequestModel):
    """Request to update an existing goal."""

    title: str | None = Field(default=None, min_length=1, max_length=200, description="Goal title")
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    status: ActionStatus | None = Field(default=None, description="Current status")
    time_horizon: TimeHorizon | None = Field(default=None, description="Time horizon")
    target_value: float | None = Field(default=None, description="Target value for the goal")
    current_value: float | None = Field(default=None, description="Current progress value")
    unit: str | None = Field(default=None, max_length=50, description="Unit of measurement")
    owner_id: str | None = Field(default=None, description="Goal owner user ID")
    tags: list[str] | None = Field(default=None, max_length=10, description="Goal tags")
    due_date: datetime | None = Field(default=None, description="Target completion date")
    success_criteria: list[str] | None = Field(default=None, description="Success criteria")
    obstacles: list[str] | None = Field(default=None, description="Identified obstacles")


class ListGoalsRequest(BaseRequestModel):
    """Request to list goals with filtering."""

    status: ActionStatus | None = Field(default=None, description="Filter by status")
    time_horizon: TimeHorizon | None = Field(default=None, description="Filter by time horizon")
    owner_id: str | None = Field(default=None, description="Filter by owner ID")
    parent_goal_id: str | None = Field(default=None, description="Filter by parent goal")
    tags: list[str] | None = Field(default=None, description="Filter by tags (any match)")
    search: str | None = Field(
        default=None, max_length=100, description="Search in title/description"
    )


# Strategy Request Models
class CreateStrategyRequest(BaseRequestModel):
    """Request to create a new strategy."""

    title: str = Field(min_length=1, max_length=200, description="Strategy title")
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    goal_id: str = Field(description="Associated goal ID")
    owner_id: str | None = Field(default=None, description="Strategy owner user ID")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")
    tags: list[str] = Field(default_factory=lambda: [], max_length=10, description="Strategy tags")
    due_date: datetime | None = Field(default=None, description="Target completion date")
    success_metrics: list[str] = Field(default_factory=lambda: [], description="Success metrics")
    resources_required: list[str] = Field(
        default_factory=lambda: [], description="Required resources"
    )
    dependencies: list[str] = Field(default_factory=lambda: [], description="Dependencies")


class UpdateStrategyRequest(BaseRequestModel):
    """Request to update an existing strategy."""

    title: str | None = Field(
        default=None, min_length=1, max_length=200, description="Strategy title"
    )
    description: str | None = Field(
        default=None, max_length=2000, description="Detailed description"
    )
    status: ActionStatus | None = Field(default=None, description="Current status")
    priority: Priority | None = Field(default=None, description="Priority level")
    owner_id: str | None = Field(default=None, description="Strategy owner user ID")
    tags: list[str] | None = Field(default=None, max_length=10, description="Strategy tags")
    due_date: datetime | None = Field(default=None, description="Target completion date")
    success_metrics: list[str] | None = Field(default=None, description="Success metrics")
    resources_required: list[str] | None = Field(default=None, description="Required resources")
    dependencies: list[str] | None = Field(default=None, description="Dependencies")


# Measure Request Models
class CreateMeasureRequest(BaseRequestModel):
    """Request to create a new Measure."""

    name: str = Field(min_length=1, max_length=100, description="Measure name")
    description: str | None = Field(default=None, max_length=1000, description="Measure description")
    current_value: float = Field(description="Current Measure value")
    target_value: float | None = Field(default=None, description="Target Measure value")
    unit: str = Field(max_length=50, description="Unit of measurement")
    goal_id: str | None = Field(default=None, description="Associated goal ID")
    owner_id: str | None = Field(default=None, description="Measure owner user ID")
    measurement_frequency: str = Field(default="monthly", description="Measurement frequency")
    data_source: str | None = Field(default=None, description="Source of Measure data")
    calculation_method: str | None = Field(default=None, description="Calculation method")


class UpdateMeasureRequest(BaseRequestModel):
    """Request to update an existing Measure."""

    name: str | None = Field(default=None, min_length=1, max_length=100, description="Measure name")
    description: str | None = Field(default=None, max_length=1000, description="Measure description")
    current_value: float | None = Field(default=None, description="Current Measure value")
    target_value: float | None = Field(default=None, description="Target Measure value")
    unit: str | None = Field(default=None, max_length=50, description="Unit of measurement")
    measurement_frequency: str | None = Field(default=None, description="Measurement frequency")
    data_source: str | None = Field(default=None, description="Source of Measure data")
    calculation_method: str | None = Field(default=None, description="Calculation method")


# Review Request Models
class CreateReviewRequest(BaseRequestModel):
    """Request to create a new review."""

    title: str = Field(min_length=1, max_length=200, description="Review title")
    review_type: ReviewType = Field(description="Type of review")
    content: str = Field(min_length=1, description="Review content")
    goal_id: str | None = Field(default=None, description="Associated goal ID")
    review_date: datetime = Field(description="Date of the review")
    next_review_date: datetime | None = Field(default=None, description="Next scheduled review")
    key_insights: list[str] = Field(default_factory=lambda: [], description="Key insights")
    action_items: list[str] = Field(default_factory=lambda: [], description="Action items")
    recommendations: list[str] = Field(default_factory=lambda: [], description="Recommendations")
    participants: list[str] = Field(default_factory=lambda: [], description="Participants")


class UpdateReviewRequest(BaseRequestModel):
    """Request to update an existing review."""

    title: str | None = Field(
        default=None, min_length=1, max_length=200, description="Review title"
    )
    content: str | None = Field(default=None, min_length=1, description="Review content")
    status: ActionStatus | None = Field(default=None, description="Review status")
    next_review_date: datetime | None = Field(default=None, description="Next scheduled review")
    key_insights: list[str] | None = Field(default=None, description="Key insights")
    action_items: list[str] | None = Field(default=None, description="Action items")
    recommendations: list[str] | None = Field(default=None, description="Recommendations")
    participants: list[str] | None = Field(default=None, description="Participants")


# Decision Request Models
class CreateDecisionRequest(BaseRequestModel):
    """Request to create a new decision."""

    title: str = Field(min_length=1, max_length=200, description="Decision title")
    description: str = Field(min_length=1, description="Decision description")
    decision_type: DecisionType = Field(description="Type of decision")
    stakeholders: list[str] = Field(default_factory=lambda: [], description="Stakeholder user IDs")
    options_considered: list[str] = Field(
        default_factory=lambda: [], description="Options considered"
    )
    rationale: str | None = Field(default=None, description="Decision rationale")
    expected_outcomes: list[str] = Field(
        default_factory=lambda: [], description="Expected outcomes"
    )
    implementation_date: datetime | None = Field(
        default=None, description="Planned implementation date"
    )
    review_date: datetime | None = Field(default=None, description="Planned review date")


class UpdateDecisionRequest(BaseRequestModel):
    """Request to update an existing decision."""

    title: str | None = Field(
        default=None, min_length=1, max_length=200, description="Decision title"
    )
    description: str | None = Field(default=None, min_length=1, description="Decision description")
    status: ActionStatus | None = Field(default=None, description="Implementation status")
    decision_date: datetime | None = Field(default=None, description="When decision was made")
    implementation_date: datetime | None = Field(default=None, description="Implementation date")
    review_date: datetime | None = Field(default=None, description="Review date")
    actual_outcomes: list[str] | None = Field(default=None, description="Actual outcomes")
    success_rating: int | None = Field(default=None, ge=1, le=5, description="Success rating (1-5)")


# Activity Request Models
class CreateActivityRequest(BaseRequestModel):
    """Request to create a new activity."""

    text: str = Field(min_length=1, max_length=500, description="Activity description")
    activity_type: str = Field(description="Type of activity")
    goal_id: str | None = Field(default=None, description="Associated goal ID")
    issue_id: str | None = Field(default=None, description="Associated issue ID")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional data")


# Report Request Models
class CreateReportRequest(BaseRequestModel):
    """Request to create a new report."""

    title: str = Field(min_length=1, max_length=200, description="Report title")
    report_type: str = Field(description="Type of report")
    parameters: dict[str, str] = Field(default_factory=dict, description="Report parameters")
    description: str | None = Field(default=None, description="Report description")
    tags: list[str] = Field(default_factory=lambda: [], max_length=10, description="Report tags")
    format: str = Field(default="json", description="Report format")
    expires_at: datetime | None = Field(default=None, description="Report expiration date")


# Note Request Models
class CreateNoteRequest(BaseRequestModel):
    """Request to create a new note."""

    note: str = Field(min_length=1, max_length=2000, description="Note content")
    attachments: list[str] = Field(default_factory=lambda: [], description="Attachment IDs")


# Goal-Related Request Models
class AddNoteRequest(BaseRequestModel):
    """Request to add a note to a goal."""

    note: str = Field(min_length=1, max_length=2000, description="Note content")
    attachments: list[str] = Field(
        default_factory=list, max_length=10, description="Attachment IDs"
    )

    @field_validator("note")
    @classmethod
    def validate_note(cls, v: str) -> str:
        """Ensure note is not empty after stripping."""
        if not v.strip():
            raise ValueError("Note cannot be empty")
        return v.strip()


class EditTargetsRequest(BaseRequestModel):
    """Request to edit goal targets."""

    target_type: str = Field(min_length=1, max_length=50, description="Type of target")
    value: float = Field(description="Target value")
    unit: str | None = Field(default=None, max_length=20, description="Unit of measurement")
    description: str | None = Field(default=None, max_length=500, description="Target description")


class CreateProposalRequest(BaseRequestModel):
    """Request to create a proposal for a goal."""

    title: str = Field(min_length=1, max_length=200, description="Proposal title")
    description: str | None = Field(
        default=None, max_length=2000, description="Proposal description"
    )
    rationale: str | None = Field(
        default=None, max_length=1000, description="Rationale for proposal"
    )
    estimated_impact: str | None = Field(
        default=None, max_length=500, description="Estimated impact"
    )
    priority: Priority = Field(default=Priority.MEDIUM, description="Proposal priority")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty after stripping."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class LinkMeasureRequest(BaseRequestModel):
    """Request to link a Measure to a goal."""

    measure_id: str = Field(min_length=1, description="Measure identifier to link")
    threshold_pct: float | None = Field(
        default=None, ge=0, le=100, description="Threshold percentage"
    )

    @field_validator("measure_id")
    @classmethod
    def validate_measure_id(cls, v: str) -> str:
        """Ensure Measure ID is not empty after stripping."""
        if not v.strip():
            raise ValueError("Measure ID cannot be empty")
        return v.strip()


# Action Status Update Request Model
class UpdateActionStatusRequest(BaseRequestModel):
    """Request to update action status."""

    status: str = Field(min_length=1, max_length=50, description="New status value")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Ensure status is not empty after stripping."""
        if not v.strip():
            raise ValueError("Status cannot be empty")
        return v.strip()


# Bulk Operation Request Models
class BulkUpdateStatusRequest(BaseRequestModel):
    """Request to update status for multiple items."""

    ids: list[str] = Field(min_length=1, max_length=100, description="Item IDs to update")
    status: ActionStatus = Field(description="New status for all items")
    reason: str | None = Field(default=None, max_length=500, description="Reason for bulk update")
