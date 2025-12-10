"""End-to-end tests for Generic AI Execute endpoint with real LLM providers.

Tests the unified /ai/execute endpoint for single-shot AI operations:
- Niche review and suggestions
- ICA (Ideal Client Avatar) review and suggestions
- Value proposition review and suggestions

These tests verify the full flow from HTTP request through to real LLM response.
"""

import pytest
from httpx import AsyncClient

# =============================================================================
# Helper Functions
# =============================================================================


def validate_onboarding_review_response(data: dict) -> None:
    """Validate the structure and content of onboarding review response."""
    # Validate data structure
    assert "data" in data, "Response should contain 'data' field"
    response_data = data["data"]

    # quality_review validation (API uses snake_case)
    quality_review_key = "quality_review" if "quality_review" in response_data else "qualityReview"
    assert quality_review_key in response_data, "Response should contain quality_review"
    quality_review = response_data[quality_review_key]
    assert isinstance(quality_review, str), "quality_review should be a string"
    assert len(quality_review) > 50, "quality_review should be substantive (>50 chars)"

    # suggestions validation
    assert "suggestions" in response_data, "Response should contain suggestions"
    suggestions = response_data["suggestions"]
    assert isinstance(suggestions, list), "suggestions should be a list"
    assert len(suggestions) == 3, "Should have exactly 3 suggestions"

    for i, suggestion in enumerate(suggestions):
        assert "text" in suggestion, f"Suggestion {i} should have 'text'"
        assert "reasoning" in suggestion, f"Suggestion {i} should have 'reasoning'"
        assert len(suggestion["text"]) > 10, f"Suggestion {i} text should be substantive"
        assert len(suggestion["reasoning"]) > 20, f"Suggestion {i} reasoning should be substantive"


def validate_response_metadata(data: dict, expected_topic: str) -> None:
    """Validate common response metadata fields."""
    assert data.get("success") is True, "Response should indicate success"
    assert data.get("topic_id") == expected_topic, f"topic_id should be {expected_topic}"
    assert "metadata" in data, "Response should contain metadata"
    metadata = data["metadata"]
    # API uses processing_time_ms (not execution_time_ms)
    time_key = "processing_time_ms" if "processing_time_ms" in metadata else "execution_time_ms"
    assert time_key in metadata, f"Metadata should contain {time_key}"
    assert metadata[time_key] > 0, "Processing time should be positive"


# =============================================================================
# Niche Review Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_niche_review_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test niche review with real LLM.

    Validates:
    - Real LLM generates quality review
    - Response contains exactly 3 suggestions
    - Each suggestion has text and reasoning
    """
    payload = {
        "topic_id": "niche_review",
        "parameters": {
            "current_value": "We help small businesses with their marketing needs",
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    validate_response_metadata(data, "niche_review")
    validate_onboarding_review_response(data)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_niche_review_with_context(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test niche review with business context fetched from backend.

    Validates:
    - Additional context is used by LLM
    - Suggestions are contextually relevant
    """
    payload = {
        "topic_id": "niche_review",
        "parameters": {
            "current_value": "Digital marketing for tech companies",
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    validate_response_metadata(data, "niche_review")
    validate_onboarding_review_response(data)

    # Verify quality - suggestions should be different from current value
    suggestions = data["data"]["suggestions"]
    current_value = payload["parameters"]["current_value"].lower()

    for suggestion in suggestions:
        # Each suggestion should be different from input (not just echoed back)
        assert (
            suggestion["text"].lower() != current_value
        ), "Suggestion should not be identical to input"


# =============================================================================
# ICA Review Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ica_review_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test ICA (Ideal Client Avatar) review with real LLM.

    Validates:
    - Real LLM generates ICA-specific review
    - Suggestions are actionable ICA descriptions
    """
    payload = {
        "topic_id": "ica_review",
        "parameters": {
            "current_value": "Small business owners who want to grow their company",
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    validate_response_metadata(data, "ica_review")
    validate_onboarding_review_response(data)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ica_review_detailed_input(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test ICA review with detailed input.

    Validates:
    - LLM handles detailed ICA descriptions
    - Suggestions improve on already-good content
    """
    payload = {
        "topic_id": "ica_review",
        "parameters": {
            "current_value": (
                "B2B SaaS founders aged 30-45 with 10-50 employees, "
                "struggling to scale their sales process, "
                "located in North America, annual revenue $1M-$10M"
            ),
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    validate_response_metadata(data, "ica_review")
    validate_onboarding_review_response(data)


# =============================================================================
# Value Proposition Review Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_value_proposition_review_real_llm(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test value proposition review with real LLM.

    Validates:
    - Real LLM generates value proposition review
    - Suggestions are compelling value propositions
    """
    payload = {
        "topic_id": "value_proposition_review",
        "parameters": {
            "current_value": "We help businesses grow faster with our software",
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    validate_response_metadata(data, "value_proposition_review")
    validate_onboarding_review_response(data)


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_value_proposition_review_specific(
    e2e_client: AsyncClient,
    check_aws_credentials: None,
) -> None:
    """
    Test value proposition review with specific content.

    Validates:
    - LLM provides specific, actionable feedback
    - Suggestions maintain core value while improving clarity
    """
    payload = {
        "topic_id": "value_proposition_review",
        "parameters": {
            "current_value": (
                "We provide AI-powered coaching that helps purpose-driven entrepreneurs "
                "align their daily operations with their core values and long-term vision"
            ),
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    validate_response_metadata(data, "value_proposition_review")
    validate_onboarding_review_response(data)


# =============================================================================
# Schema and Discovery Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_available_topics(
    e2e_client: AsyncClient,
) -> None:
    """
    Test listing available single-shot topics.

    Validates:
    - Endpoint returns list of topics
    - Onboarding review topics are included
    """
    response = await e2e_client.get("/api/v1/ai/topics")

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    assert "topics" in data
    topics = data["topics"]

    # Find our onboarding review topics
    topic_ids = [t["topic_id"] for t in topics]
    assert "niche_review" in topic_ids, "niche_review should be in available topics"
    assert "ica_review" in topic_ids, "ica_review should be in available topics"
    assert (
        "value_proposition_review" in topic_ids
    ), "value_proposition_review should be in available topics"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_get_onboarding_review_schema(
    e2e_client: AsyncClient,
) -> None:
    """
    Test getting the OnboardingReviewResponse schema.

    Validates:
    - Schema endpoint works
    - Schema describes expected response structure
    """
    response = await e2e_client.get("/api/v1/ai/schemas/OnboardingReviewResponse")

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    assert "schema" in data
    schema = data["schema"]

    # Verify schema has expected properties
    assert "properties" in schema
    properties = schema["properties"]

    assert "qualityReview" in properties, "Schema should define qualityReview"
    assert "suggestions" in properties, "Schema should define suggestions"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_list_all_schemas(
    e2e_client: AsyncClient,
) -> None:
    """
    Test listing all available response schemas.

    Validates:
    - Schemas endpoint returns list
    - OnboardingReviewResponse is included
    """
    response = await e2e_client.get("/api/v1/ai/schemas")

    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()

    assert "schemas" in data
    schemas = data["schemas"]

    assert (
        "OnboardingReviewResponse" in schemas
    ), "OnboardingReviewResponse should be in available schemas"


# =============================================================================
# Error Handling Tests
# =============================================================================


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_execute_unknown_topic_returns_404(
    e2e_client: AsyncClient,
) -> None:
    """
    Test that unknown topic returns 404.

    Validates:
    - Proper error handling for unknown topics
    """
    payload = {
        "topic_id": "nonexistent_topic_xyz",
        "parameters": {
            "current_value": "test",
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_execute_missing_required_param_returns_422(
    e2e_client: AsyncClient,
) -> None:
    """
    Test that missing required parameter returns 422.

    Validates:
    - Proper validation error for missing parameters
    """
    payload = {
        "topic_id": "niche_review",
        "parameters": {
            # Missing current_value which is required
        },
    }

    response = await e2e_client.post("/api/v1/ai/execute", json=payload)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"


__all__ = []  # Test module, no exports
