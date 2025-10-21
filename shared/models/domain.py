"""Business domain models for PurposePath."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import BaseDomainModel, IdentifiedMixin, TenantScopedMixin


# Enums for domain entities
class ActionStatus(str, Enum):
    """Status values for actions, goals, and strategies."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    """Priority levels for issues and tasks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TimeHorizon(str, Enum):
    """Time horizons for goals and strategies."""

    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    LONG_TERM = "long_term"


class ReviewType(str, Enum):
    """Types of reviews."""

    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class IssueType(str, Enum):
    """Types of issues."""

    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"
    TASK = "task"
    BLOCKER = "blocker"


class DecisionType(str, Enum):
    """Types of decisions."""

    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    TACTICAL = "tactical"
    POLICY = "policy"


# Core Business Domain Models


class Issue(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Issue tracking entity."""

    title: str = Field(..., min_length=1, max_length=200, description="Issue title")
    description: str | None = Field(None, max_length=2000, description="Detailed description")

    # Classification
    issue_type: IssueType = Field(default=IssueType.TASK, description="Type of issue")
    status: ActionStatus = Field(default=ActionStatus.NOT_STARTED, description="Current status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")

    # Relationships
    goal_id: str | None = Field(None, description="Associated goal ID")
    owner_id: str | None = Field(None, description="Assigned owner user ID")
    reporter_id: str | None = Field(None, description="User who reported the issue")

    # Tracking
    tags: list[str] = Field(default_factory=list, description="Issue tags")
    due_date: datetime | None = Field(None, description="Due date")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    # Root Cause Analysis
    root_cause_analysis: dict[str, Any] | None = Field(None, description="RCA data")

    # Metadata
    estimated_effort: int | None = Field(None, ge=1, description="Estimated effort in hours")
    actual_effort: int | None = Field(None, ge=0, description="Actual effort in hours")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty after stripping."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class Goal(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Strategic goal entity."""

    title: str = Field(..., min_length=1, max_length=200, description="Goal title")
    description: str | None = Field(None, max_length=2000, description="Detailed description")

    # Classification
    status: ActionStatus = Field(default=ActionStatus.NOT_STARTED, description="Current status")
    time_horizon: TimeHorizon = Field(default=TimeHorizon.QUARTERLY, description="Time horizon")

    # Measurement
    target_value: float | None = Field(None, description="Target value for the goal")
    current_value: float | None = Field(None, description="Current progress value")
    unit: str | None = Field(None, max_length=50, description="Unit of measurement")

    # Relationships
    owner_id: str | None = Field(None, description="Goal owner user ID")
    parent_goal_id: str | None = Field(None, description="Parent goal ID for hierarchical goals")

    # Tracking
    tags: list[str] = Field(default_factory=list, description="Goal tags")
    due_date: datetime | None = Field(None, description="Target completion date")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    # Metadata
    success_criteria: list[str] = Field(default_factory=list, description="Success criteria")
    obstacles: list[str] = Field(default_factory=list, description="Identified obstacles")

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.target_value is None or self.current_value is None:
            return 0.0
        if self.target_value == 0:
            return 100.0 if self.current_value > 0 else 0.0
        return min(100.0, max(0.0, (self.current_value / self.target_value) * 100))

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty after stripping."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class Strategy(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Strategy entity for achieving goals."""

    title: str = Field(..., min_length=1, max_length=200, description="Strategy title")
    description: str | None = Field(None, max_length=2000, description="Detailed description")

    # Relationships
    goal_id: str = Field(..., description="Associated goal ID")
    owner_id: str | None = Field(None, description="Strategy owner user ID")

    # Classification
    status: ActionStatus = Field(default=ActionStatus.NOT_STARTED, description="Current status")
    priority: Priority = Field(default=Priority.MEDIUM, description="Priority level")

    # Tracking
    tags: list[str] = Field(default_factory=list, description="Strategy tags")
    due_date: datetime | None = Field(None, description="Target completion date")
    completed_at: datetime | None = Field(None, description="Completion timestamp")

    # Strategy details
    success_metrics: list[str] = Field(default_factory=list, description="Success metrics")
    resources_required: list[str] = Field(default_factory=list, description="Required resources")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty after stripping."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


class KPI(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Key Performance Indicator entity."""

    name: str = Field(..., min_length=1, max_length=100, description="KPI name")
    description: str | None = Field(None, max_length=1000, description="KPI description")

    # Measurement
    current_value: float = Field(..., description="Current KPI value")
    target_value: float | None = Field(None, description="Target KPI value")
    unit: str = Field(..., max_length=50, description="Unit of measurement")

    # Relationships
    goal_id: str | None = Field(None, description="Associated goal ID")
    owner_id: str | None = Field(None, description="KPI owner user ID")

    # Configuration
    measurement_frequency: str = Field(default="monthly", description="How often it's measured")
    data_source: str | None = Field(None, description="Source of KPI data")
    calculation_method: str | None = Field(None, description="How KPI is calculated")

    # Tracking
    last_measured: datetime | None = Field(None, description="Last measurement date")
    trend: str | None = Field(None, description="Trend direction (up, down, stable)")

    @property
    def achievement_percentage(self) -> float:
        """Calculate achievement percentage against target."""
        if self.target_value is None or self.target_value == 0:
            return 0.0
        return min(100.0, max(0.0, (self.current_value / self.target_value) * 100))


class Review(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Review entity for periodic assessments."""

    title: str = Field(..., min_length=1, max_length=200, description="Review title")
    review_type: ReviewType = Field(..., description="Type of review")
    content: str = Field(..., min_length=1, description="Review content")

    # Relationships
    goal_id: str | None = Field(None, description="Associated goal ID")
    reviewer_id: str = Field(..., description="User who conducted the review")

    # Review data
    status: ActionStatus = Field(default=ActionStatus.COMPLETED, description="Review status")
    review_date: datetime = Field(..., description="Date of the review")
    next_review_date: datetime | None = Field(None, description="Next scheduled review")

    # Outcomes
    key_insights: list[str] = Field(default_factory=list, description="Key insights from review")
    action_items: list[str] = Field(default_factory=list, description="Action items identified")
    recommendations: list[str] = Field(default_factory=list, description="Recommendations")

    # Metadata
    participants: list[str] = Field(default_factory=list, description="Review participants")
    attachments: list[str] = Field(default_factory=list, description="Attached documents")


class Decision(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Decision tracking entity."""

    title: str = Field(..., min_length=1, max_length=200, description="Decision title")
    description: str = Field(..., min_length=1, description="Decision description")
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
    status: ActionStatus = Field(
        default=ActionStatus.NOT_STARTED, description="Implementation status"
    )
    implementation_date: datetime | None = Field(None, description="Implementation date")
    review_date: datetime | None = Field(None, description="Review date")

    # Impact tracking
    actual_outcomes: list[str] = Field(default_factory=list, description="Actual outcomes")
    success_rating: int | None = Field(None, ge=1, le=5, description="Success rating (1-5)")


class Activity(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Activity/event tracking entity."""

    text: str = Field(..., min_length=1, max_length=500, description="Activity description")
    activity_type: str = Field(..., description="Type of activity")

    # Relationships
    user_id: str = Field(..., description="User who performed the activity")
    goal_id: str | None = Field(None, description="Associated goal ID")
    issue_id: str | None = Field(None, description="Associated issue ID")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional activity data")
    is_system_generated: bool = Field(default=False, description="Whether system generated")


class Report(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Report entity for analytics and insights."""

    title: str = Field(..., min_length=1, max_length=200, description="Report title")
    report_type: str = Field(..., description="Type of report")

    # Report data
    data: dict[str, Any] = Field(..., description="Report data")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Report parameters")

    # Generation info
    generated_by_id: str = Field(..., description="User who generated the report")
    generated_at: datetime = Field(..., description="Generation timestamp")

    # Status
    status: str = Field(default="completed", description="Report generation status")
    format: str = Field(default="json", description="Report format")

    # Metadata
    description: str | None = Field(None, description="Report description")
    tags: list[str] = Field(default_factory=list, description="Report tags")
    expires_at: datetime | None = Field(None, description="Report expiration date")
