"""Pydantic models for onboarding AI endpoints."""

from pydantic import BaseModel, Field


# Suggestions endpoint models
class OnboardingSuggestionRequest(BaseModel):
    """Request for AI suggestions during onboarding."""

    kind: str = Field(
        ...,
        description="Type of suggestion: niche, ica, or valueProposition",
        pattern="^(niche|ica|valueProposition)$",
    )
    current: str | None = Field(
        None,
        description="Current draft text (optional)",
    )
    context: dict[str, str | list[str]] = Field(
        default_factory=dict,
        description="Business context for suggestions",
    )


class OnboardingSuggestionResponse(BaseModel):
    """Response with AI suggestions."""

    suggestions: list[str] = Field(
        ...,
        description="AI-generated suggestions",
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why these suggestions fit",
    )


# Website scan endpoint models
class WebsiteScanRequest(BaseModel):
    """Request to scan a website."""

    url: str = Field(
        ...,
        description="Website URL to scan",
        pattern=r"^https?://",
    )


class WebsiteScanResponse(BaseModel):
    """Response from website scan."""

    business_name: str = Field(
        ...,
        alias="businessName",
        description="Extracted business name",
    )
    industry: str = Field(
        ...,
        description="Detected industry",
    )
    description: str = Field(
        ...,
        description="Business description",
    )
    products: list[str] = Field(
        default_factory=list,
        description="Detected products/services",
    )
    target_market: str = Field(
        ...,
        alias="targetMarket",
        description="Target market/audience",
    )
    suggested_niche: str = Field(
        ...,
        alias="suggestedNiche",
        description="AI-suggested niche",
    )

    model_config = {"populate_by_name": True}


# Coaching endpoint models
class OnboardingCoachingRequest(BaseModel):
    """Request for onboarding coaching assistance."""

    topic: str = Field(
        ...,
        description="Onboarding topic: coreValues, purpose, or vision",
        pattern="^(coreValues|purpose|vision)$",
    )
    message: str = Field(
        ...,
        min_length=1,
        description="User's question or request for help",
    )
    context: dict[str, str] = Field(
        default_factory=dict,
        description="Business context",
    )


class OnboardingCoachingResponse(BaseModel):
    """Response from onboarding coach."""

    response: str = Field(
        ...,
        description="AI coach's response",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggested values/statements",
    )


__all__ = [
    "OnboardingCoachingRequest",
    "OnboardingCoachingResponse",
    "OnboardingSuggestionRequest",
    "OnboardingSuggestionResponse",
    "WebsiteScanRequest",
    "WebsiteScanResponse",
]
