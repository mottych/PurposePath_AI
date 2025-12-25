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


class ProductInfo(BaseModel):
    """Product or service information extracted from website."""

    id: str = Field(
        ...,
        description="Unique identifier (lowercase, hyphenated)",
    )
    name: str = Field(
        ...,
        description="Product or service name",
    )
    problem: str = Field(
        ...,
        description="Problem this product/service solves",
    )


class WebsiteScanCompanyProfile(BaseModel):
    """Company profile details extracted from the website."""

    company_name: str = Field(..., description="Public-facing company name")
    legal_name: str = Field(..., description="Registered legal entity name")
    tagline: str = Field(..., description="Marketing tagline or headline")
    overview: str = Field(..., description="One-paragraph business overview")


class WebsiteScanTargetMarket(BaseModel):
    """Target market insights."""

    primary_audience: str = Field(..., description="Primary audience or buyer persona")
    segments: list[str] = Field(..., description="Market segments served")
    pain_points: list[str] = Field(..., description="Key pain points addressed")


class WebsiteScanOffers(BaseModel):
    """Products and offers highlighted on the site."""

    primary_product: str = Field(..., description="Main product or offer")
    categories: list[str] = Field(..., description="Product/solution categories")
    features: list[str] = Field(..., description="Notable features or capabilities")
    differentiators: list[str] = Field(..., description="Differentiators vs competitors")


class WebsiteScanTestimonial(BaseModel):
    """Customer testimonial snippet."""

    quote: str = Field(..., description="Customer quote")
    attribution: str = Field(..., description="Attribution for the quote")


class WebsiteScanCredibility(BaseModel):
    """Signals that build trust."""

    notable_clients: list[str] = Field(..., description="List of notable clients")
    testimonials: list[WebsiteScanTestimonial] = Field(
        default_factory=list, description="Testimonials pulled from the site"
    )


class WebsiteScanSupportingAsset(BaseModel):
    """Supporting asset promoted on the page."""

    label: str = Field(..., description="Display label for the asset")
    url: str = Field(..., description="URL to the asset")


class WebsiteScanConversion(BaseModel):
    """Conversion-oriented content from the site."""

    primary_cta_text: str = Field(..., description="Primary call-to-action text")
    primary_cta_url: str = Field(..., description="Primary call-to-action URL")
    supporting_assets: list[WebsiteScanSupportingAsset] = Field(
        default_factory=list, description="Supporting assets for conversion"
    )


class WebsiteScanResponse(BaseModel):
    """Data payload for website_scan topic results (no wrappers)."""

    scan_id: str = Field(..., description="Unique identifier for this scan run")
    captured_at: str = Field(..., description="ISO8601 timestamp when the scan was captured")
    source_url: str = Field(..., description="URL that was scanned")
    company_profile: WebsiteScanCompanyProfile
    target_market: WebsiteScanTargetMarket
    offers: WebsiteScanOffers
    credibility: WebsiteScanCredibility
    conversion: WebsiteScanConversion


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
    "WebsiteScanCompanyProfile",
    "WebsiteScanConversion",
    "WebsiteScanCredibility",
    "WebsiteScanOffers",
    "WebsiteScanRequest",
    "WebsiteScanResponse",
    "WebsiteScanTargetMarket",
]
