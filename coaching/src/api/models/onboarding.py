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


# Onboarding review endpoint models (niche, ICA, value proposition)
class SuggestionVariation(BaseModel):
    """A suggested variation for an onboarding field."""

    text: str = Field(
        ...,
        description="The suggested text variation",
    )
    reasoning: str = Field(
        ...,
        description=(
            "Explanation of why this variation is recommended. "
            "Use newlines (\\n) to separate paragraphs for readability."
        ),
    )


class OnboardingReviewResponse(BaseModel):
    """Response from onboarding review endpoint (niche, ICA, value proposition).

    Used by topics: niche_review, ica_review, value_proposition_review
    """

    quality_review: str = Field(
        ...,
        alias="qualityReview",
        description=(
            "AI review of the current content quality with feedback. "
            "Use newlines (\\n) to separate sections like Overall Assessment, "
            "Strengths, Weaknesses, and Suggestions for readability."
        ),
    )
    suggestions: list[SuggestionVariation] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 suggested variations",
    )

    model_config = {"populate_by_name": True}


__all__ = [
    "OnboardingCoachingRequest",
    "OnboardingCoachingResponse",
    "OnboardingReviewResponse",
    "OnboardingSuggestionRequest",
    "OnboardingSuggestionResponse",
    "SuggestionVariation",
    "WebsiteScanRequest",
    "WebsiteScanResponse",
]
