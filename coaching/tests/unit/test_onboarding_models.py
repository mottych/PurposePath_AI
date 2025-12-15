"""Unit tests for Onboarding Pydantic models (Issue #48)."""

import pytest
from coaching.src.api.models.onboarding import (
    OnboardingCoachingRequest,
    OnboardingCoachingResponse,
    OnboardingSuggestionRequest,
    OnboardingSuggestionResponse,
    ProductInfo,
    WebsiteScanRequest,
    WebsiteScanResponse,
)
from pydantic import ValidationError


@pytest.mark.unit
class TestOnboardingSuggestionRequest:
    """Test OnboardingSuggestionRequest model."""

    def test_valid_request_with_all_fields(self):
        """Test valid request with all fields."""
        # Arrange & Act
        request = OnboardingSuggestionRequest(
            kind="niche",
            current="My current niche",
            context={"businessName": "TechCorp", "industry": "Software"},
        )

        # Assert
        assert request.kind == "niche"
        assert request.current == "My current niche"
        assert request.context["businessName"] == "TechCorp"

    def test_valid_request_minimal_fields(self):
        """Test valid request with only required fields."""
        # Arrange & Act
        request = OnboardingSuggestionRequest(kind="ica")

        # Assert
        assert request.kind == "ica"
        assert request.current is None
        assert request.context == {}

    def test_valid_kinds(self):
        """Test all valid kind values."""
        # Arrange & Act & Assert
        for kind in ["niche", "ica", "valueProposition"]:
            request = OnboardingSuggestionRequest(kind=kind)
            assert request.kind == kind

    def test_invalid_kind_raises_error(self):
        """Test that invalid kind raises validation error."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            OnboardingSuggestionRequest(kind="invalid_kind")

        # Verify error message mentions pattern
        assert "String should match pattern" in str(exc_info.value)

    def test_empty_context(self):
        """Test with empty context dictionary."""
        # Arrange & Act
        request = OnboardingSuggestionRequest(kind="niche", context={})

        # Assert
        assert request.context == {}

    def test_context_with_list_values(self):
        """Test context with list values (products)."""
        # Arrange & Act
        request = OnboardingSuggestionRequest(
            kind="niche",
            context={
                "businessName": "Test",
                "products": ["Product A", "Product B"],
            },
        )

        # Assert
        assert isinstance(request.context["products"], list)
        assert len(request.context["products"]) == 2


@pytest.mark.unit
class TestOnboardingSuggestionResponse:
    """Test OnboardingSuggestionResponse model."""

    def test_valid_response(self):
        """Test valid suggestion response."""
        # Arrange & Act
        response = OnboardingSuggestionResponse(
            suggestions=["Suggestion 1", "Suggestion 2", "Suggestion 3"],
            reasoning="Based on your industry and products...",
        )

        # Assert
        assert len(response.suggestions) == 3
        assert response.suggestions[0] == "Suggestion 1"
        assert "industry" in response.reasoning

    def test_empty_suggestions_list(self):
        """Test response with empty suggestions list."""
        # Arrange & Act
        response = OnboardingSuggestionResponse(
            suggestions=[],
            reasoning="No suggestions available",
        )

        # Assert
        assert response.suggestions == []
        assert response.reasoning == "No suggestions available"

    def test_single_suggestion(self):
        """Test response with single suggestion."""
        # Arrange & Act
        response = OnboardingSuggestionResponse(
            suggestions=["Single suggestion"],
            reasoning="Only one suggestion fits",
        )

        # Assert
        assert len(response.suggestions) == 1

    def test_long_reasoning(self):
        """Test response with long reasoning text."""
        # Arrange
        long_reasoning = "A" * 1000  # 1000 character reasoning

        # Act
        response = OnboardingSuggestionResponse(
            suggestions=["Test"],
            reasoning=long_reasoning,
        )

        # Assert
        assert len(response.reasoning) == 1000


@pytest.mark.unit
class TestWebsiteScanRequest:
    """Test WebsiteScanRequest model."""

    def test_valid_https_url(self):
        """Test valid HTTPS URL."""
        # Arrange & Act
        request = WebsiteScanRequest(url="https://example.com")

        # Assert
        assert request.url == "https://example.com"

    def test_valid_http_url(self):
        """Test valid HTTP URL."""
        # Arrange & Act
        request = WebsiteScanRequest(url="http://example.com")

        # Assert
        assert request.url == "http://example.com"

    def test_url_with_path(self):
        """Test URL with path."""
        # Arrange & Act
        request = WebsiteScanRequest(url="https://example.com/about")

        # Assert
        assert request.url == "https://example.com/about"

    def test_url_with_query_params(self):
        """Test URL with query parameters."""
        # Arrange & Act
        request = WebsiteScanRequest(url="https://example.com?page=1&sort=asc")

        # Assert
        assert "page=1" in request.url

    def test_invalid_url_without_protocol(self):
        """Test that URL without http:// or https:// fails validation."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            WebsiteScanRequest(url="example.com")

        # Verify validation error
        assert "String should match pattern" in str(exc_info.value)

    def test_invalid_url_with_ftp(self):
        """Test that ftp:// URLs fail validation."""
        # Act & Assert
        with pytest.raises(ValidationError):
            WebsiteScanRequest(url="ftp://example.com")

    def test_empty_url_raises_error(self):
        """Test that empty URL raises validation error."""
        # Act & Assert
        with pytest.raises(ValidationError):
            WebsiteScanRequest(url="")


@pytest.mark.unit
class TestProductInfo:
    """Test ProductInfo model."""

    def test_valid_product_info(self):
        """Test valid ProductInfo creation."""
        # Arrange & Act
        product = ProductInfo(
            id="crm-software",
            name="CRM Software",
            problem="Helps manage customer relationships",
        )

        # Assert
        assert product.id == "crm-software"
        assert product.name == "CRM Software"
        assert product.problem == "Helps manage customer relationships"

    def test_missing_required_field(self):
        """Test ProductInfo requires all fields."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ProductInfo(id="test", name="Test")  # Missing problem


@pytest.mark.unit
class TestWebsiteScanResponse:
    """Test WebsiteScanResponse model."""

    def test_valid_response_with_all_fields(self):
        """Test valid response with all fields."""
        # Arrange & Act
        response = WebsiteScanResponse(
            products=[
                ProductInfo(id="crm", name="CRM Software", problem="Customer management"),
                ProductInfo(id="analytics", name="Analytics", problem="Data insights"),
            ],
            niche="B2B SaaS for mid-market enterprises",
            ica="Mid-sized businesses seeking growth, 50-500 employees, tech-savvy leadership",
            value_proposition="Streamline operations with AI-powered automation",
        )

        # Assert
        assert len(response.products) == 2
        assert response.products[0].name == "CRM Software"
        assert response.niche == "B2B SaaS for mid-market enterprises"
        assert "mid-sized" in response.ica.lower()
        assert response.value_proposition == "Streamline operations with AI-powered automation"

    def test_products_as_dicts(self):
        """Test that products can be provided as dicts."""
        # Arrange - Using dicts for products
        data = {
            "products": [
                {"id": "product-1", "name": "Product One", "problem": "Solves problem A"},
            ],
            "niche": "Test niche",
            "ica": "Test ICA",
            "value_proposition": "Test value prop",
        }

        # Act
        response = WebsiteScanResponse(**data)

        # Assert
        assert len(response.products) == 1
        assert isinstance(response.products[0], ProductInfo)
        assert response.products[0].id == "product-1"

    def test_empty_products_list(self):
        """Test response with empty products list."""
        # Arrange & Act
        response = WebsiteScanResponse(
            products=[],
            niche="Test niche",
            ica="Test ICA",
            value_proposition="Test value prop",
        )

        # Assert
        assert response.products == []

    def test_many_products(self):
        """Test response with many products."""
        # Arrange
        products = [
            ProductInfo(id=f"product-{i}", name=f"Product {i}", problem=f"Problem {i}")
            for i in range(20)
        ]

        # Act
        response = WebsiteScanResponse(
            products=products,
            niche="Manufacturing niche",
            ica="Industrial buyers",
            value_proposition="Quality manufacturing",
        )

        # Assert
        assert len(response.products) == 20


@pytest.mark.unit
class TestOnboardingCoachingRequest:
    """Test OnboardingCoachingRequest model."""

    def test_valid_request_with_all_fields(self):
        """Test valid coaching request."""
        # Arrange & Act
        request = OnboardingCoachingRequest(
            topic="coreValues",
            message="How do I define my core values?",
            context={"businessName": "TechCorp", "industry": "Software"},
        )

        # Assert
        assert request.topic == "coreValues"
        assert request.message == "How do I define my core values?"
        assert request.context["businessName"] == "TechCorp"

    def test_valid_topics(self):
        """Test all valid topic values."""
        # Arrange & Act & Assert
        for topic in ["coreValues", "purpose", "vision"]:
            request = OnboardingCoachingRequest(
                topic=topic,
                message="Test message",
            )
            assert request.topic == topic

    def test_invalid_topic_raises_error(self):
        """Test that invalid topic raises validation error."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            OnboardingCoachingRequest(
                topic="invalid_topic",
                message="Test",
            )

        assert "String should match pattern" in str(exc_info.value)

    def test_empty_message_raises_error(self):
        """Test that empty message raises validation error."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            OnboardingCoachingRequest(
                topic="coreValues",
                message="",
            )

        # Verify min_length constraint
        assert "at least 1 character" in str(exc_info.value)

    def test_minimal_request(self):
        """Test request with minimal fields."""
        # Arrange & Act
        request = OnboardingCoachingRequest(
            topic="purpose",
            message="Help me define my purpose",
        )

        # Assert
        assert request.topic == "purpose"
        assert request.message == "Help me define my purpose"
        assert request.context == {}

    def test_long_message(self):
        """Test request with very long message."""
        # Arrange
        long_message = "A" * 5000

        # Act
        request = OnboardingCoachingRequest(
            topic="vision",
            message=long_message,
        )

        # Assert
        assert len(request.message) == 5000


@pytest.mark.unit
class TestOnboardingCoachingResponse:
    """Test OnboardingCoachingResponse model."""

    def test_valid_response_with_all_fields(self):
        """Test valid coaching response."""
        # Arrange & Act
        response = OnboardingCoachingResponse(
            response="Here's guidance on defining core values...",
            suggestions=["Integrity", "Innovation", "Excellence"],
        )

        # Assert
        assert "guidance" in response.response
        assert len(response.suggestions) == 3
        assert "Integrity" in response.suggestions

    def test_response_with_no_suggestions(self):
        """Test response with empty suggestions list."""
        # Arrange & Act
        response = OnboardingCoachingResponse(
            response="Consider the following...",
            suggestions=[],
        )

        # Assert
        assert response.response == "Consider the following..."
        assert response.suggestions == []

    def test_minimal_response(self):
        """Test response with minimal fields."""
        # Arrange & Act
        response = OnboardingCoachingResponse(
            response="Short response",
        )

        # Assert
        assert response.response == "Short response"
        assert response.suggestions == []

    def test_long_response_text(self):
        """Test response with very long response text."""
        # Arrange
        long_response = "A" * 10000

        # Act
        response = OnboardingCoachingResponse(
            response=long_response,
            suggestions=["Value 1", "Value 2"],
        )

        # Assert
        assert len(response.response) == 10000

    def test_many_suggestions(self):
        """Test response with many suggestions."""
        # Arrange
        many_suggestions = [f"Value {i}" for i in range(15)]

        # Act
        response = OnboardingCoachingResponse(
            response="Here are many values to consider",
            suggestions=many_suggestions,
        )

        # Assert
        assert len(response.suggestions) == 15


@pytest.mark.unit
class TestOnboardingModelsEdgeCases:
    """Test edge cases across all models."""

    def test_suggestion_request_with_none_current(self):
        """Test SuggestionRequest explicitly None current."""
        # Arrange & Act
        request = OnboardingSuggestionRequest(kind="niche", current=None)

        # Assert
        assert request.current is None

    def test_scan_response_with_special_characters(self):
        """Test WebsiteScanResponse with special characters."""
        # Arrange & Act
        response = WebsiteScanResponse(
            products=[
                ProductInfo(id="product-a-b", name="Product A & B", problem="Problem A & B"),
            ],
            niche="IT & Services consulting",
            ica="B2B & B2C hybrid customers",
            value_proposition="We provide IT services & consulting",
        )

        # Assert
        assert "&" in response.niche
        assert "&" in response.ica

    def test_coaching_request_with_multiline_message(self):
        """Test CoachingRequest with multiline message."""
        # Arrange
        multiline_message = """This is a multiline message.

        It has multiple paragraphs.

        And different sections."""

        # Act
        request = OnboardingCoachingRequest(
            topic="purpose",
            message=multiline_message,
        )

        # Assert
        assert "\n" in request.message
        assert "multiple paragraphs" in request.message

    def test_model_serialization(self):
        """Test that models can be serialized to dict."""
        # Arrange
        request = OnboardingSuggestionRequest(
            kind="ica",
            current="Current ICA",
            context={"test": "value"},
        )

        # Act
        data = request.model_dump()

        # Assert
        assert isinstance(data, dict)
        assert data["kind"] == "ica"
        assert data["current"] == "Current ICA"

    def test_model_json_serialization(self):
        """Test that models can be serialized to JSON."""
        # Arrange
        response = OnboardingSuggestionResponse(
            suggestions=["A", "B"],
            reasoning="Test reasoning",
        )

        # Act
        json_str = response.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "suggestions" in json_str
        assert "reasoning" in json_str
