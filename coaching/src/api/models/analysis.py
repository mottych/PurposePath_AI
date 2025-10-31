"""API models for analysis endpoints.

This module provides Pydantic models for analysis-related API requests and responses,
including alignment, strategy, KPI, and operational analysis endpoints.
"""

from datetime import datetime
from typing import Any

from src.core.constants import AnalysisType
from pydantic import BaseModel, Field, field_validator

# Request Models


class AlignmentAnalysisRequest(BaseModel):
    """Request to analyze alignment between goals and purpose/values.

    This model validates alignment analysis requests.
    Note: user_id and tenant_id are extracted from JWT token.
    """

    text_to_analyze: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Text content to analyze for alignment",
        examples=["Our Q1 goals focus on increasing revenue and expanding market share..."],
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context for analysis",
        examples=[
            {
                "purpose": "To democratize access to quality education",
                "core_values": ["Integrity", "Innovation", "Impact"],
            }
        ],
    )

    @field_validator("text_to_analyze")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate text content."""
        if not v.strip():
            raise ValueError("Text to analyze cannot be empty")
        return v.strip()


class StrategyAnalysisRequest(BaseModel):
    """Request to analyze strategy effectiveness and recommendations.

    This model validates strategy analysis requests.
    Note: user_id and tenant_id are extracted from JWT token.
    """

    current_strategy: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Current strategy description",
        examples=["We plan to grow through partnerships and content marketing..."],
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Business context for strategy analysis",
        examples=[
            {
                "industry": "EdTech",
                "market_size": "Mid-sized",
                "target_audience": "K-12 educators",
            }
        ],
    )


class KPIAnalysisRequest(BaseModel):
    """Request to analyze KPI effectiveness and recommendations.

    This model validates KPI analysis requests.
    Note: user_id and tenant_id are extracted from JWT token.
    """

    current_kpis: list[str] = Field(
        ...,
        min_length=1,
        description="List of current KPIs",
        examples=[["Monthly Recurring Revenue", "Customer Acquisition Cost", "Net Promoter Score"]],
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Business context for KPI analysis",
        examples=[
            {
                "business_goals": ["Increase revenue", "Improve customer satisfaction"],
                "current_challenges": ["High churn rate", "Low brand awareness"],
            }
        ],
    )

    @field_validator("current_kpis")
    @classmethod
    def validate_kpis(cls, v: list[str]) -> list[str]:
        """Validate KPI list."""
        if not v:
            raise ValueError("At least one KPI must be provided")
        return [kpi.strip() for kpi in v if kpi.strip()]


class OperationsAnalysisRequest(BaseModel):
    """Request for operational analysis (SWOT, root cause, action plan).

    This model validates operational analysis requests.
    Note: user_id and tenant_id are extracted from JWT token.
    """

    analysis_type: str = Field(
        ...,
        description="Type of operational analysis",
        examples=["swot", "root_cause", "action_plan"],
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Description of situation/problem",
        examples=["We're experiencing declining customer retention..."],
    )
    context: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional operational context",
    )

    @field_validator("analysis_type")
    @classmethod
    def validate_analysis_type(cls, v: str) -> str:
        """Validate analysis type."""
        valid_types = {"swot", "root_cause", "action_plan"}
        if v.lower() not in valid_types:
            raise ValueError(f"analysis_type must be one of: {', '.join(valid_types)}")
        return v.lower()


# Response Models


class AlignmentScore(BaseModel):
    """Alignment score component."""

    overall_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall alignment score (0-100)",
        examples=[85.5],
    )
    purpose_alignment: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Alignment with purpose",
        examples=[90.0],
    )
    values_alignment: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Alignment with core values",
        examples=[82.0],
    )
    goal_clarity: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Clarity of goals",
        examples=[88.0],
    )


class AlignmentAnalysisResponse(BaseModel):
    """Response for alignment analysis.

    This model provides comprehensive alignment analysis results.
    """

    analysis_id: str = Field(
        ...,
        description="Unique identifier for this analysis",
        examples=["anls_abc123"],
    )
    analysis_type: AnalysisType = Field(
        ...,
        description="Type of analysis performed",
    )
    scores: AlignmentScore = Field(
        ...,
        description="Alignment scores",
    )
    overall_assessment: str = Field(
        ...,
        description="Summary assessment",
        examples=["Your goals show strong alignment with your stated purpose and values..."],
    )
    strengths: list[str] = Field(
        ...,
        description="Identified strengths",
        examples=[["Clear connection to purpose", "Value-driven objectives"]],
    )
    misalignments: list[str] = Field(
        default_factory=list,
        description="Identified misalignments or gaps",
        examples=[["Some goals lack specific success metrics"]],
    )
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Recommendations for improvement",
        examples=[
            [
                {
                    "action": "Add specific metrics to revenue goals",
                    "priority": "high",
                    "rationale": "Clear metrics improve accountability",
                }
            ]
        ],
    )
    created_at: datetime = Field(
        ...,
        description="Analysis timestamp",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )


class StrategyRecommendation(BaseModel):
    """Strategy recommendation component."""

    category: str = Field(
        ...,
        description="Recommendation category",
        examples=["Market Expansion", "Product Development", "Customer Retention"],
    )
    recommendation: str = Field(
        ...,
        description="Specific recommendation",
        examples=["Consider partnering with complementary platforms to expand reach"],
    )
    priority: str = Field(
        ...,
        description="Priority level",
        examples=["high", "medium", "low"],
    )
    rationale: str = Field(
        ...,
        description="Reasoning behind recommendation",
        examples=["Partnerships can accelerate growth with lower customer acquisition costs"],
    )
    estimated_impact: str = Field(
        ...,
        description="Expected impact description",
        examples=["Could increase reach by 30-50% within 6 months"],
    )


class StrategyAnalysisResponse(BaseModel):
    """Response for strategy analysis.

    This model provides strategy effectiveness analysis and recommendations.
    """

    analysis_id: str = Field(..., description="Analysis identifier")
    analysis_type: AnalysisType = Field(..., description="Analysis type")
    effectiveness_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Strategy effectiveness score",
        examples=[75.0],
    )
    overall_assessment: str = Field(
        ...,
        description="Summary assessment",
    )
    strengths: list[str] = Field(
        ...,
        description="Strategy strengths",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Strategy weaknesses or gaps",
    )
    opportunities: list[str] = Field(
        default_factory=list,
        description="Identified opportunities",
    )
    recommendations: list[StrategyRecommendation] = Field(
        default_factory=list,
        description="Strategic recommendations",
    )
    created_at: datetime = Field(..., description="Analysis timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class KPIRecommendation(BaseModel):
    """KPI recommendation component."""

    kpi_name: str = Field(..., description="Recommended KPI name")
    description: str = Field(..., description="What this KPI measures")
    rationale: str = Field(..., description="Why this KPI is important")
    target_range: str | None = Field(default=None, description="Suggested target range")
    measurement_frequency: str = Field(
        default="monthly",
        description="How often to measure",
    )


class KPIAnalysisResponse(BaseModel):
    """Response for KPI analysis.

    This model provides KPI effectiveness analysis and recommendations.
    """

    analysis_id: str = Field(..., description="Analysis identifier")
    analysis_type: AnalysisType = Field(..., description="Analysis type")
    kpi_effectiveness_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall KPI effectiveness score",
    )
    overall_assessment: str = Field(..., description="Summary assessment")
    current_kpi_analysis: list[dict[str, Any]] = Field(
        ...,
        description="Analysis of current KPIs",
    )
    missing_kpis: list[str] = Field(
        default_factory=list,
        description="Important KPIs that are missing",
    )
    recommended_kpis: list[KPIRecommendation] = Field(
        default_factory=list,
        description="Recommended KPIs to add",
    )
    created_at: datetime = Field(..., description="Analysis timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class OperationsAnalysisResponse(BaseModel):
    """Response for operational analysis (SWOT, root cause, action plan).

    This model provides operational analysis results.
    """

    analysis_id: str = Field(..., description="Analysis identifier")
    analysis_type: AnalysisType = Field(..., description="Analysis type")
    specific_analysis_type: str = Field(
        ...,
        description="Specific operational analysis type",
        examples=["swot", "root_cause", "action_plan"],
    )
    findings: dict[str, Any] = Field(
        ...,
        description="Analysis findings (structure varies by type)",
        examples=[
            {
                "strengths": ["Strong brand", "Loyal customer base"],
                "weaknesses": ["Limited marketing budget"],
                "opportunities": ["Growing market segment"],
                "threats": ["New competitors entering market"],
            }
        ],
    )
    recommendations: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Actionable recommendations",
    )
    priority_actions: list[str] = Field(
        default_factory=list,
        description="High-priority actions",
    )
    created_at: datetime = Field(..., description="Analysis timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


__all__ = [
    # Requests
    "AlignmentAnalysisRequest",
    "AlignmentAnalysisResponse",
    # Responses
    "AlignmentScore",
    "KPIAnalysisRequest",
    "KPIAnalysisResponse",
    "KPIRecommendation",
    "OperationsAnalysisRequest",
    "OperationsAnalysisResponse",
    "StrategyAnalysisRequest",
    "StrategyAnalysisResponse",
    "StrategyRecommendation",
]
