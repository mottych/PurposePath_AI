"""Unit tests for OnboardingService (Issue #37 - Sample Test)."""

from unittest.mock import AsyncMock

import pytest
from coaching.src.services.onboarding_service import OnboardingService


@pytest.mark.unit
class TestOnboardingService:
    """Test onboarding service business logic."""

    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        service = AsyncMock()
        service.generate_single_shot_analysis = AsyncMock(
            return_value={"response": "1. Suggestion one\n2. Suggestion two\n3. Suggestion three"}
        )
        return service

    @pytest.fixture
    def onboarding_service(self, mock_llm_service):
        """Create onboarding service with mocked dependencies."""
        return OnboardingService(llm_service=mock_llm_service)

    async def test_get_suggestions_niche_success(self, onboarding_service, mock_llm_service):
        """Test successful niche suggestion generation."""
        # Arrange
        kind = "niche"
        context = {
            "businessName": "TechCorp",
            "industry": "Software",
            "products": ["CRM", "Analytics"],
        }

        # Act
        result = await onboarding_service.get_suggestions(
            kind=kind,
            context=context,
        )

        # Assert
        assert "suggestions" in result
        assert "reasoning" in result
        assert isinstance(result["suggestions"], list)
        assert len(result["suggestions"]) > 0
        mock_llm_service.generate_single_shot_analysis.assert_called_once()

    async def test_get_suggestions_with_current_draft(self, onboarding_service):
        """Test suggestions generation with existing draft."""
        # Arrange
        kind = "valueProposition"
        current = "We help businesses grow"
        context = {"businessName": "GrowthCo"}

        # Act
        result = await onboarding_service.get_suggestions(
            kind=kind,
            current=current,
            context=context,
        )

        # Assert
        assert result["suggestions"]
        assert result["reasoning"]

    async def test_get_coaching_core_values(self, onboarding_service, mock_llm_service):
        """Test coaching for core values topic."""
        # Arrange
        mock_llm_service.generate_single_shot_analysis.return_value = {
            "response": 'Consider "Integrity" and "Innovation" as core values for your business.'
        }
        topic = "coreValues"
        message = "How do I define core values?"
        context = {"businessName": "ValueCo"}

        # Act
        result = await onboarding_service.get_coaching(
            topic=topic,
            message=message,
            context=context,
        )

        # Assert
        assert "response" in result
        assert "suggestions" in result
        assert result["response"]
        assert isinstance(result["suggestions"], list)

    async def test_scan_website_success(self, onboarding_service, mock_llm_service):
        """Test successful website scanning."""
        # Arrange
        url = "https://example.com"
        mock_analysis_result = {
            "products": [
                {"id": "product-1", "name": "Test Product", "problem": "Solves test problem"}
            ],
            "niche": "Test niche description",
            "ica": "Test ideal customer",
            "value_proposition": "Test value proposition",
        }

        # Mock the website_analysis_service.analyze_website method
        onboarding_service.website_analysis_service.analyze_website = AsyncMock(
            return_value=mock_analysis_result
        )

        # Act
        result = await onboarding_service.scan_website(url)

        # Assert
        assert "businessName" in result
        assert "industry" in result
        assert "description" in result
        assert "products" in result
        assert "targetMarket" in result
        assert "suggestedNiche" in result
        assert result["businessName"] == "Example"
        assert result["products"] == ["Test Product"]
        assert result["description"] == "Test value proposition"
        assert result["targetMarket"] == "Test ideal customer"
        assert result["suggestedNiche"] == "Test niche description"

    async def test_parse_suggestions_from_response(self, onboarding_service):
        """Test internal suggestion parsing logic."""
        # Arrange
        response = """
        1. First suggestion text here
        2. Second suggestion with more details
        3. Third comprehensive suggestion
        """

        # Act
        suggestions = onboarding_service._parse_suggestions(response)

        # Assert
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
        assert all(len(s) > 20 for s in suggestions)  # Minimum length check

    async def test_extract_suggestions_from_coaching_with_quotes(self, onboarding_service):
        """Test extracting suggestions from coaching response with quoted text."""
        # Arrange
        response = 'Consider "Excellence" and "Customer Focus" as values.'
        topic = "coreValues"

        # Act
        suggestions = onboarding_service._extract_suggestions_from_coaching(response, topic)

        # Assert
        assert "Excellence" in suggestions
        assert "Customer Focus" in suggestions

    async def test_get_suggestions_empty_context(self, onboarding_service):
        """Test suggestions generation with minimal context."""
        # Arrange
        kind = "ica"

        # Act
        result = await onboarding_service.get_suggestions(kind=kind, context={})

        # Assert
        assert result["suggestions"]
        assert result["reasoning"]
        # Should handle empty context gracefully


@pytest.mark.unit
class TestOnboardingServiceEdgeCases:
    """Test edge cases and error scenarios."""

    @pytest.fixture
    def onboarding_service(self):
        """Create service with mocked LLM."""
        mock_llm = AsyncMock()
        mock_llm.generate_single_shot_analysis = AsyncMock(return_value={"response": ""})
        return OnboardingService(llm_service=mock_llm)

    async def test_empty_llm_response_has_fallback(self, onboarding_service):
        """Test that empty LLM response provides fallback."""
        # Arrange
        kind = "niche"

        # Act
        result = await onboarding_service.get_suggestions(kind=kind)

        # Assert
        assert result["suggestions"]
        assert len(result["suggestions"]) > 0
        # Should provide fallback message

    async def test_coaching_with_empty_message(self, onboarding_service):
        """Test coaching handles edge cases gracefully."""
        # This test documents expected behavior
        # In production, validation should catch this at API layer
        topic = "purpose"
        message = ""

        # Act
        result = await onboarding_service.get_coaching(topic=topic, message=message)

        # Assert
        assert "response" in result
        # Service should handle gracefully even with empty message
