"""Strategy Suggestions API models matching specification."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrategySuggestionsBaseModel(BaseModel):
    """Shared config for strategy suggestion models."""

    model_config = ConfigDict(populate_by_name=True)


class StrategySuggestionsRequest(StrategySuggestionsBaseModel):
    """Request for AI-generated strategy recommendations.

    Matches specification in backend-integration-coaching-service.md line 199-217.
    """

    goal_intent: str = Field(
        ...,
        alias="goalIntent",
        min_length=5,
        max_length=500,
        description="The goal intent requiring strategies",
        examples=["Increase customer retention by 20%"],
    )

    business_context: dict[str, Any] = Field(
        ...,
        alias="businessContext",
        description="Business context for strategy generation",
        examples=[
            {
                "vision": "To be the leading provider in our industry",
                "purpose": "To help customers achieve their goals",
                "coreValues": ["Excellence", "Innovation", "Integrity"],
                "targetMarket": "Small to medium businesses",
                "valueProposition": "Comprehensive solutions with personal service",
                "businessName": "Sample Business",
                "industry": "Software",
                "businessType": "B2B SaaS",
                "currentChallenges": ["High churn", "Competition"],
            }
        ],
    )

    existing_strategies: list[str] = Field(
        default_factory=list,
        alias="existingStrategies",
        description="Current strategies already in place",
        examples=[["Focus on customer support", "Regular check-ins"]],
    )

    constraints: dict[str, Any] | None = Field(
        default=None,
        description="Resource constraints",
        examples=[
            {"budget": 50000, "timeline": "6 months", "resources": ["2 developers", "1 designer"]}
        ],
    )


class StrategySuggestion(StrategySuggestionsBaseModel):
    """Individual strategy suggestion."""

    title: str = Field(..., description="Strategy title")
    description: str = Field(..., description="Detailed strategy description")
    rationale: str = Field(..., description="Why this strategy makes sense")
    difficulty: str = Field(
        ...,
        description="Implementation difficulty",
        examples=["low", "medium", "high"],
    )
    timeframe: str = Field(..., description="Expected timeframe", examples=["2-3 months"])
    expected_impact: str = Field(
        ...,
        alias="expectedImpact",
        description="Expected impact level",
        examples=["low", "medium", "high"],
    )
    prerequisites: list[str] = Field(
        default_factory=list, description="Prerequisites for implementation"
    )
    estimated_cost: int | None = Field(
        default=None, alias="estimatedCost", description="Estimated cost in dollars"
    )
    required_resources: list[str] = Field(
        default_factory=list, alias="requiredResources", description="Required resources"
    )


class StrategySuggestionsResponse(StrategySuggestionsBaseModel):
    """Response containing strategy suggestions.

    Matches specification in backend-integration-coaching-service.md line 219-243.
    """

    suggestions: list[StrategySuggestion] = Field(..., description="List of strategy suggestions")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score for suggestions")
    reasoning: str = Field(..., description="Overall reasoning for suggestions")


__all__ = [
    "StrategySuggestion",
    "StrategySuggestionsRequest",
    "StrategySuggestionsResponse",
]
