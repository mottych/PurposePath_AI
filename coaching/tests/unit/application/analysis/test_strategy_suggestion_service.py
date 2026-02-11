from unittest.mock import Mock

import pytest
from coaching.src.application.analysis.strategy_suggestion_service import StrategySuggestionService
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.constants import AnalysisType


class TestStrategySuggestionService:
    @pytest.fixture
    def mock_llm_service(self):
        return Mock(spec=LLMApplicationService)

    @pytest.fixture
    def service(self, mock_llm_service):
        return StrategySuggestionService(llm_service=mock_llm_service)

    def test_get_analysis_type(self, service):
        """Test that the correct analysis type is returned."""
        assert service.get_analysis_type() == AnalysisType.STRATEGY

    def test_build_prompt_full_context(self, service):
        """Test building prompt with full context provided."""
        context = {
            "goal_intent": "Increase market share by 20%",
            "business_context": {
                "vision": "To be the best",
                "purpose": "Serve customers",
                "coreValues": ["Integrity", "Innovation"],
                "targetMarket": "SMEs",
                "valueProposition": "Affordable quality",
                "industry": "Tech",
                "businessType": "B2B",
            },
            "existing_strategies": ["Social media marketing"],
            "constraints": {
                "budget": 50000,
                "timeline": "6 months",
                "resources": ["Marketing team", "External consultant"],
            },
        }

        prompt = service.build_prompt(context)

        assert "Increase market share by 20%" in prompt
        assert "To be the best" in prompt
        assert "Integrity, Innovation" in prompt
        assert "Social media marketing" in prompt
        assert "Budget: $50,000" in prompt
        assert "Timeline: 6 months" in prompt
        assert "Marketing team, External consultant" in prompt

    def test_build_prompt_minimal_context(self, service):
        """Test building prompt with minimal context."""
        context = {"goal_intent": "Grow revenue"}

        prompt = service.build_prompt(context)

        assert "Grow revenue" in prompt
        assert "Vision: Not defined" in prompt
        assert "None currently in place" in prompt
        # Constraints section should be empty or minimal
        assert "Resource Constraints" not in prompt

    def test_parse_response_valid_json(self, service):
        """Test parsing a valid JSON response."""
        valid_json = """
        {
            "suggestions": [
                {
                    "title": "Expand Sales Team",
                    "description": "Hire 5 new sales reps",
                    "rationale": "Direct sales needed",
                    "difficulty": "medium",
                    "timeframe": "3 months",
                    "expectedImpact": "high",
                    "prerequisites": ["Budget approval"],
                    "estimatedCost": 100000,
                    "requiredResources": ["HR", "Sales Manager"]
                }
            ],
            "confidence": 0.9,
            "reasoning": "Solid plan"
        }
        """
        result = service.parse_response(valid_json)

        assert result["confidence"] == 0.9
        assert len(result["suggestions"]) == 1
        assert result["suggestions"][0]["title"] == "Expand Sales Team"

    def test_parse_response_markdown_json(self, service):
        """Test parsing JSON wrapped in markdown code blocks."""
        markdown_json = """
        ```json
        {
            "suggestions": [
                {
                    "title": "Strategy A",
                    "description": "Desc A",
                    "rationale": "Rationale A",
                    "difficulty": "low",
                    "timeframe": "1 month",
                    "expectedImpact": "medium"
                }
            ],
            "confidence": 0.8,
            "reasoning": "Good"
        }
        ```
        """
        result = service.parse_response(markdown_json)
        assert result["confidence"] == 0.8
        assert result["suggestions"][0]["title"] == "Strategy A"

    def test_parse_response_missing_required_field(self, service):
        """Test parsing response missing top-level required field."""
        invalid_json = '{"suggestions": []}'

        with pytest.raises(ValueError, match="Missing required field: confidence"):
            service.parse_response(invalid_json)

    def test_parse_response_empty_suggestions(self, service):
        """Test parsing response with empty suggestions list."""
        invalid_json = """
        {
            "suggestions": [],
            "confidence": 0.5,
            "reasoning": "None"
        }
        """
        with pytest.raises(ValueError, match="At least one suggestion is required"):
            service.parse_response(invalid_json)

    def test_parse_response_invalid_suggestion_structure(self, service):
        """Test parsing response with invalid suggestion structure."""
        invalid_json = """
        {
            "suggestions": [
                {
                    "title": "Incomplete Strategy"
                }
            ],
            "confidence": 0.5,
            "reasoning": "Bad"
        }
        """
        with pytest.raises(ValueError, match="Suggestion 0 missing required field"):
            service.parse_response(invalid_json)

    def test_parse_response_invalid_json_syntax(self, service):
        """Test parsing invalid JSON syntax."""
        invalid_json = "{ not valid json }"

        with pytest.raises(ValueError, match="Invalid JSON response"):
            service.parse_response(invalid_json)

    def test_parse_response_defaults_and_validation(self, service):
        """Test default values and validation for difficulty/impact."""
        json_response = """
        {
            "suggestions": [
                {
                    "title": "Test Strategy",
                    "description": "Desc",
                    "rationale": "Rat",
                    "difficulty": "invalid_diff",
                    "timeframe": "1m",
                    "expectedImpact": "invalid_impact"
                }
            ],
            "confidence": 1.5,
            "reasoning": "Reason"
        }
        """
        result = service.parse_response(json_response)

        suggestion = result["suggestions"][0]
        assert suggestion["difficulty"] == "medium"  # Defaulted
        assert suggestion["expectedImpact"] == "medium"  # Defaulted
        assert suggestion["prerequisites"] == []  # Defaulted
        assert suggestion["estimatedCost"] is None  # Defaulted
        assert result["confidence"] == 1.0  # Capped
