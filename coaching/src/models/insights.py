"""Data models for insights feature."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InsightCategory(str, Enum):
    """Categories for business insights."""

    STRATEGY = "strategy"
    OPERATIONS = "operations"
    FINANCE = "finance"
    MARKETING = "marketing"
    LEADERSHIP = "leadership"
    TECHNOLOGY = "technology"


class KISSCategory(str, Enum):
    """KISS framework categories for actionable insights."""

    KEEP = "keep"  # What's working well, continue doing
    IMPROVE = "improve"  # What needs optimization
    START = "start"  # What should be initiated
    STOP = "stop"  # What's misaligned or counterproductive


class InsightPriority(str, Enum):
    """Priority levels for insights."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class InsightStatus(str, Enum):
    """Status of an insight."""

    ACTIVE = "active"
    DISMISSED = "dismissed"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SuggestedAction(BaseModel):
    """A suggested action for an insight."""

    title: str = Field(..., description="Action title")
    description: str = Field(..., description="Detailed action description")
    effort: str = Field(..., description="Effort level: low, medium, high")
    impact: str = Field(..., description="Expected impact: low, medium, high")
    order: int = Field(default=1, description="Display order", ge=1)


class Insight(BaseModel):
    """Core insight data model."""

    id: str = Field(..., description="Unique insight identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    title: str = Field(..., min_length=5, max_length=200, description="Insight title")
    description: str = Field(
        ..., min_length=20, max_length=2000, description="Detailed description"
    )
    category: InsightCategory = Field(..., description="Insight category")
    priority: InsightPriority = Field(..., description="Priority level")
    kiss_category: KISSCategory | None = Field(
        default=None, description="KISS framework category (Keep, Improve, Start, Stop)"
    )
    alignment_impact: str | None = Field(
        default=None,
        max_length=500,
        description="How this affects purpose/values alignment and business outcomes",
    )
    status: InsightStatus = Field(default=InsightStatus.ACTIVE, description="Current status")
    suggested_actions: list[SuggestedAction] = Field(
        default_factory=list, description="List of suggested actions"
    )
    data_sources: list[str] = Field(
        default_factory=list,
        description="Data sources used (e.g., 'goals', 'performance_score')",
    )
    confidence_score: float = Field(
        default=0.8, ge=0.0, le=1.0, description="AI confidence in this insight"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When insight was generated",
    )
    expires_at: datetime = Field(..., description="When insight expires (24hr TTL)")
    acknowledged_at: datetime | None = Field(
        default=None, description="When insight was acknowledged"
    )
    dismissed_at: datetime | None = Field(default=None, description="When insight was dismissed")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def is_expired(self) -> bool:
        """Check if insight has expired."""
        return datetime.now(UTC) > self.expires_at

    def is_active(self) -> bool:
        """Check if insight is active (not dismissed/completed)."""
        return self.status in [InsightStatus.ACTIVE, InsightStatus.IN_PROGRESS]


class BusinessDataContext(BaseModel):
    """Aggregated business data for insight generation."""

    tenant_id: str = Field(..., description="Tenant identifier")
    foundation: dict[str, Any] = Field(default_factory=dict, description="Business foundation data")
    goals: list[dict[str, Any]] = Field(default_factory=list, description="Goals data")
    strategies: list[dict[str, Any]] = Field(default_factory=list, description="Strategies data")
    measures: list[dict[str, Any]] = Field(default_factory=list, description="Measures data")
    goal_stats: dict[str, Any] = Field(default_factory=dict, description="Goal statistics")
    performance_score: dict[str, Any] = Field(
        default_factory=dict, description="Performance metrics"
    )
    recent_actions: list[dict[str, Any]] = Field(default_factory=list, description="Recent actions")
    open_issues: list[dict[str, Any]] = Field(default_factory=list, description="Open issues")
    collected_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When data was collected",
    )

    def has_sufficient_data(self) -> bool:
        """Check if we have enough data to generate insights."""
        # At minimum need foundation or goals data
        return bool(self.foundation or self.goals)

    def get_data_source_summary(self) -> dict[str, int]:
        """Get summary of available data sources."""
        return {
            "foundation": 1 if self.foundation else 0,
            "goals": len(self.goals),
            "strategies": len(self.strategies),
            "measures": len(self.measures),
            "goal_stats": 1 if self.goal_stats else 0,
            "performance_score": 1 if self.performance_score else 0,
            "recent_actions": len(self.recent_actions),
            "open_issues": len(self.open_issues),
        }


class GeneratedInsights(BaseModel):
    """Container for LLM-generated insights."""

    insights: list[Insight] = Field(..., description="Generated insights")
    generation_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Generation metadata (model, tokens, cost)"
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Generation timestamp",
    )


class InsightsCacheEntry(BaseModel):
    """Cache entry for insights."""

    tenant_id: str = Field(..., description="Tenant identifier")
    insights: list[Insight] = Field(..., description="Cached insights")
    cached_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When cached",
    )
    expires_at: datetime = Field(..., description="Cache expiration")
    cache_key: str = Field(..., description="DynamoDB cache key")

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now(UTC) > self.expires_at


__all__ = [
    "BusinessDataContext",
    "GeneratedInsights",
    "Insight",
    "InsightCategory",
    "InsightPriority",
    "InsightStatus",
    "InsightsCacheEntry",
    "KISSCategory",
    "SuggestedAction",
]
