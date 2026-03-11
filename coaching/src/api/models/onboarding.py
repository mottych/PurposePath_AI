"""Pydantic models for onboarding AI endpoints."""

import datetime
import re
from urllib.parse import urlparse

from pydantic import BaseModel, Field, model_validator

_DEFAULT_SCAN_ID = "scan_generated"
_MAX_DESCRIPTION_LENGTH = 320
_MAX_LOCATION_LENGTH = 120


def _first_non_empty(mapping: dict[str, object], keys: tuple[str, ...]) -> object | None:
    """Return the first meaningful value from a set of aliases."""
    for key in keys:
        value = mapping.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
            continue
        return value
    return None


def _collapse_ws(value: str) -> str:
    """Collapse repeated whitespace while preserving plain text content."""
    return " ".join(value.split()).strip()


def _normalize_business_description(value: object) -> str:
    """Keep description concise to avoid dumping large scraped payloads."""
    if not isinstance(value, str):
        return ""

    compact = _collapse_ws(value)
    if not compact:
        return ""

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", compact) if part.strip()]
    if sentences:
        selected: list[str] = []
        current_length = 0
        for sentence in sentences:
            next_length = current_length + len(sentence) + (1 if selected else 0)
            if selected and next_length > _MAX_DESCRIPTION_LENGTH:
                break
            selected.append(sentence)
            current_length = next_length
            if len(selected) >= 3:
                break
        if selected:
            return " ".join(selected)

    return compact[:_MAX_DESCRIPTION_LENGTH].rstrip()


def _normalize_location(value: object) -> str | None:
    """Normalize location-like values into short display text."""
    if not isinstance(value, str):
        return None

    compact = _collapse_ws(value)
    if not compact:
        return None

    return compact[:_MAX_LOCATION_LENGTH].rstrip()


def _normalize_year(value: object) -> int | None:
    """Extract and validate a founded year from mixed input formats."""
    current_year = datetime.datetime.now(datetime.UTC).year
    if isinstance(value, int):
        return value if 1800 <= value <= current_year + 1 else None
    if isinstance(value, float):
        as_int = int(value)
        return as_int if 1800 <= as_int <= current_year + 1 else None
    if isinstance(value, str):
        match = re.search(r"\b(18|19|20)\d{2}\b", value)
        if not match:
            return None
        parsed = int(match.group(0))
        return parsed if 1800 <= parsed <= current_year + 1 else None
    return None


def _name_from_url(url: str) -> str:
    """Build a readable business-name fallback from source URL."""
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    if not host:
        return ""
    primary = host.split(".")[0].replace("-", " ").replace("_", " ").strip()
    return primary.title()


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


class WebsiteScanBusinessProfile(BaseModel):
    """Business profile information aligned with BusinessFoundation.profile."""

    business_name: str = Field(..., description="Public-facing company name")
    business_description: str = Field(..., description="1-3 sentence business overview")
    industry: str | None = Field(None, description="Primary industry classification")
    year_founded: int | None = Field(None, description="Year the company was founded")
    headquarters_location: str | None = Field(None, description="City, State or City, Country")
    website: str = Field(..., description="Company website URL")

    @model_validator(mode="before")
    @classmethod
    def _normalize_profile_aliases(cls, data: object) -> object:
        """Support legacy and alternate property names for profile fields."""
        if not isinstance(data, dict):
            return data

        profile_data = dict(data)

        business_name = _first_non_empty(
            profile_data,
            ("business_name", "businessName", "company_name", "companyName", "name"),
        )
        business_description = _first_non_empty(
            profile_data,
            ("business_description", "businessDescription", "description", "about", "summary"),
        )
        industry = _first_non_empty(
            profile_data,
            ("industry", "primary_industry", "primaryIndustry", "sector", "businessIndustry"),
        )
        year_founded = _first_non_empty(
            profile_data,
            ("year_founded", "yearFounded", "founded", "foundedYear", "established"),
        )
        headquarters = _first_non_empty(
            profile_data,
            (
                "headquarters_location",
                "headquartersLocation",
                "business_address",
                "businessAddress",
                "address",
                "location",
                "hq",
                "hqLocation",
            ),
        )
        website = _first_non_empty(profile_data, ("website", "source_url", "sourceUrl", "url"))

        if isinstance(business_name, str):
            profile_data["business_name"] = _collapse_ws(business_name)
        if business_description is not None:
            profile_data["business_description"] = _normalize_business_description(business_description)
        if isinstance(industry, str):
            profile_data["industry"] = _collapse_ws(industry)

        normalized_year = _normalize_year(year_founded)
        if normalized_year is not None:
            profile_data["year_founded"] = normalized_year

        normalized_location = _normalize_location(headquarters)
        if normalized_location:
            profile_data["headquarters_location"] = normalized_location

        if isinstance(website, str):
            profile_data["website"] = website

        return profile_data


class WebsiteScanCoreIdentity(BaseModel):
    """Core identity hints aligned with BusinessFoundation.identity."""

    vision_hint: str | None = Field(
        None, description="Inferred vision or long-term aspiration from website content"
    )
    purpose_hint: str | None = Field(None, description="Inferred purpose or mission statement")
    inferred_values: list[str] = Field(
        default_factory=list,
        description="Core values inferred from company culture, about us, or values sections",
    )


class WebsiteScanTargetMarket(BaseModel):
    """Target market insights aligned with BusinessFoundation.market."""

    niche_statement: str = Field(..., description="Target market or niche description")
    segments: list[str] = Field(
        default_factory=list, description="Specific market segments or customer types"
    )
    pain_points: list[str] = Field(default_factory=list, description="Key pain points addressed")


class WebsiteScanProduct(BaseModel):
    """Product or service information aligned with BusinessFoundation.products."""

    name: str = Field(..., description="Product or service name")
    description: str | None = Field(None, description="Product description")
    problem_solved: str = Field(..., description="Problem this product/service solves")
    key_features: list[str] = Field(
        default_factory=list, description="Key features or capabilities"
    )


class WebsiteScanValueProposition(BaseModel):
    """Value proposition aligned with BusinessFoundation.proposition."""

    unique_selling_proposition: str | None = Field(
        None, description="Main unique selling proposition or headline"
    )
    key_differentiators: list[str] = Field(
        default_factory=list, description="Key differentiators vs competitors"
    )
    proof_points: list[str] = Field(
        default_factory=list,
        description="Social proof, testimonials, metrics, or achievements",
    )


class WebsiteScanResponse(BaseModel):
    """Data payload for website_scan topic results aligned with BusinessFoundation structure."""

    scan_id: str = Field(..., description="Unique identifier for this scan run")
    captured_at: str = Field(..., description="ISO8601 timestamp when the scan was captured")
    source_url: str = Field(..., description="URL that was scanned")
    business_profile: WebsiteScanBusinessProfile
    core_identity: WebsiteScanCoreIdentity
    target_market: WebsiteScanTargetMarket
    products: list[WebsiteScanProduct] = Field(
        default_factory=list, description="Products or services offered"
    )
    value_proposition: WebsiteScanValueProposition

    @model_validator(mode="before")
    @classmethod
    def _normalize_legacy_payload(cls, data: object) -> object:
        """Accept both legacy flat payloads and canonical nested structure."""
        if not isinstance(data, dict):
            return data

        normalized = dict(data)

        # Preserve canonical shape when present, but support legacy root keys.
        profile_obj = normalized.get("business_profile")
        if isinstance(profile_obj, dict):
            profile = dict(profile_obj)
        elif isinstance(profile_obj, BaseModel):
            profile = profile_obj.model_dump()
        else:
            profile = {}

        legacy_profile = normalized.get("business_info")
        if isinstance(legacy_profile, dict):
            profile = {**legacy_profile, **profile}

        root_profile_aliases = {
            "business_name": _first_non_empty(
                normalized, ("business_name", "businessName", "company_name", "companyName", "name")
            ),
            "business_description": _first_non_empty(
                normalized, ("business_description", "businessDescription", "description", "about")
            ),
            "industry": _first_non_empty(
                normalized, ("industry", "primary_industry", "primaryIndustry", "sector")
            ),
            "year_founded": _first_non_empty(
                normalized, ("year_founded", "yearFounded", "founded", "foundedYear")
            ),
            "headquarters_location": _first_non_empty(
                normalized,
                (
                    "headquarters_location",
                    "headquartersLocation",
                    "business_address",
                    "businessAddress",
                    "address",
                    "location",
                ),
            ),
        }
        for key, value in root_profile_aliases.items():
            if value is not None and key not in profile:
                profile[key] = value

        source_url = _first_non_empty(
            normalized, ("source_url", "sourceUrl", "website_url", "websiteUrl", "url")
        )
        if isinstance(source_url, str):
            normalized["source_url"] = source_url
            profile.setdefault("website", source_url)

        if profile:
            if not profile.get("business_name") and isinstance(source_url, str):
                fallback_name = _name_from_url(source_url)
                if fallback_name:
                    profile["business_name"] = fallback_name
            normalized["business_profile"] = profile

        # Backward-compatible defaults for required envelope fields.
        if not normalized.get("scan_id"):
            normalized["scan_id"] = _DEFAULT_SCAN_ID
        if not normalized.get("captured_at"):
            normalized["captured_at"] = datetime.datetime.now(datetime.UTC).isoformat()

        return normalized


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


class IcaSuggestion(BaseModel):
    """Detailed ICA (Ideal Client Avatar) suggestion with comprehensive persona information."""

    title: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Descriptive title for this ICA persona",
    )
    demographics: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Age, gender, location, income, education, occupation, family status",
    )
    goals_aspirations: str = Field(
        ...,
        alias="goalsAspirations",
        min_length=20,
        max_length=500,
        description="What they want to achieve, their ambitions and desired outcomes",
    )
    pain_points: str = Field(
        ...,
        alias="painPoints",
        min_length=20,
        max_length=500,
        description="Problems, challenges, frustrations they face",
    )
    motivations: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="What drives them, their values and priorities",
    )
    common_objectives: str = Field(
        ...,
        alias="commonObjectives",
        min_length=20,
        max_length=500,
        description="Typical goals and milestones they're working toward",
    )
    where_to_find: str = Field(
        ...,
        alias="whereToFind",
        min_length=20,
        max_length=500,
        description="Where this persona can be found (online/offline channels, communities, platforms)",
    )
    buying_process: str = Field(
        ...,
        alias="buyingProcess",
        min_length=20,
        max_length=500,
        description="How they make purchasing decisions, research process, decision criteria",
    )

    model_config = {"populate_by_name": True}


class IcaReviewResponse(BaseModel):
    """Response from ICA review endpoint with detailed persona suggestions.

    Used by topic: ica_review
    """

    quality_review: str | None = Field(
        default=None,
        alias="qualityReview",
        description=(
            "AI review of the current ICA quality with feedback. "
            "Use newlines (\\n) to separate sections. "
            "This field is optional - null if no current_value was provided."
        ),
    )
    suggestions: list[IcaSuggestion] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 detailed ICA persona suggestions",
    )

    model_config = {"populate_by_name": True}


class OnboardingReviewResponse(BaseModel):
    """Response from onboarding review endpoint (niche review).

    Used by topics: niche_review
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


class ValuePropositionSuggestion(BaseModel):
    """Detailed value proposition suggestion with comprehensive business positioning."""

    usp_statement: str = Field(
        ...,
        alias="uspStatement",
        min_length=10,
        max_length=500,
        description="Unique Selling Proposition statement - the core value promise",
    )
    key_differentiators: list[str] = Field(
        ...,
        alias="keyDifferentiators",
        min_length=2,
        max_length=5,
        description="2-5 key differentiators that set the business apart from competitors",
    )
    customer_outcomes: list[str] = Field(
        ...,
        alias="customerOutcomes",
        min_length=2,
        max_length=5,
        description="2-5 specific outcomes or benefits customers can expect",
    )
    proof_points: list[str] = Field(
        ...,
        alias="proofPoints",
        min_length=2,
        max_length=7,
        description="2-7 short proof points (testimonials, metrics, achievements, credentials)",
    )
    brand_promise: str = Field(
        ...,
        alias="brandPromise",
        min_length=10,
        max_length=300,
        description="The brand promise - what the business commits to delivering consistently",
    )
    primary_competitor: str | None = Field(
        None,
        alias="primaryCompetitor",
        max_length=200,
        description="Primary competitor or competitive segment (if known/applicable)",
    )
    competitive_advantage: str = Field(
        ...,
        alias="competitiveAdvantage",
        min_length=10,
        max_length=400,
        description="Key competitive advantage that drives market differentiation",
    )
    market_position: str = Field(
        ...,
        alias="marketPosition",
        pattern="^(Market Leader|Challenger|Niche Player|Emerging)$",
        description="Market position: Market Leader, Challenger, Niche Player, or Emerging",
    )

    model_config = {"populate_by_name": True}


class ValuePropositionReviewResponse(BaseModel):
    """Response from value proposition review endpoint with detailed positioning suggestions.

    Used by topic: value_proposition_review
    """

    quality_review: str | None = Field(
        default=None,
        alias="qualityReview",
        description=(
            "AI review of the current value proposition quality with feedback. "
            "Use newlines (\\n) to separate sections. "
            "This field is null if no current_value was provided or if there's not enough information."
        ),
    )
    suggestions: list[ValuePropositionSuggestion] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 detailed value proposition suggestions",
    )
    insufficient_information: bool = Field(
        default=False,
        alias="insufficientInformation",
        description="True if there's not enough information to generate quality suggestions",
    )

    model_config = {"populate_by_name": True}


__all__ = [
    "IcaReviewResponse",
    "IcaSuggestion",
    "OnboardingCoachingRequest",
    "OnboardingCoachingResponse",
    "OnboardingReviewResponse",
    "OnboardingSuggestionRequest",
    "OnboardingSuggestionResponse",
    "SuggestionVariation",
    "ValuePropositionReviewResponse",
    "ValuePropositionSuggestion",
    "WebsiteScanBusinessProfile",
    "WebsiteScanCoreIdentity",
    "WebsiteScanProduct",
    "WebsiteScanRequest",
    "WebsiteScanResponse",
    "WebsiteScanTargetMarket",
    "WebsiteScanValueProposition",
]
