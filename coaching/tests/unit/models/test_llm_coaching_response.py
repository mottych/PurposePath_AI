"""Unit tests for LLM coaching response model and parsing."""

import pytest
from coaching.src.models.llm_coaching_response import (
    AUTO_COMPLETION_CONFIDENCE_THRESHOLD,
    LLMCoachingResponse,
    parse_llm_coaching_response,
    should_auto_complete,
)


class TestLLMCoachingResponse:
    """Tests for LLMCoachingResponse model."""

    def test_basic_response_creation(self) -> None:
        """Test creating a basic response with required fields."""
        response = LLMCoachingResponse(message="Hello, how can I help?")

        assert response.message == "Hello, how can I help?"
        assert response.is_final is False
        assert response.result is None
        assert response.confidence == 0.0

    def test_completion_response_creation(self) -> None:
        """Test creating a completion response with all fields."""
        result = {
            "values": [{"name": "Integrity", "description": "...", "importance": "..."}],
            "summary": "Your core values are...",
        }
        response = LLMCoachingResponse(
            message="Thank you for this session!",
            is_final=True,
            result=result,
            confidence=0.92,
        )

        assert response.message == "Thank you for this session!"
        assert response.is_final is True
        assert response.result == result
        assert response.confidence == 0.92

    def test_confidence_validation_min(self) -> None:
        """Test that confidence below 0 is rejected."""
        with pytest.raises(ValueError):
            LLMCoachingResponse(message="Test", confidence=-0.1)

    def test_confidence_validation_max(self) -> None:
        """Test that confidence above 1 is rejected."""
        with pytest.raises(ValueError):
            LLMCoachingResponse(message="Test", confidence=1.1)

    def test_message_required(self) -> None:
        """Test that message is required."""
        with pytest.raises(ValueError):
            LLMCoachingResponse(message="")  # type: ignore

    def test_message_min_length(self) -> None:
        """Test that empty message is rejected."""
        with pytest.raises(ValueError):
            LLMCoachingResponse(message="")


class TestParseLLMCoachingResponse:
    """Tests for parse_llm_coaching_response function."""

    def test_parse_valid_json_normal_response(self) -> None:
        """Test parsing valid JSON for normal conversation."""
        raw = '{"message": "Tell me more about that.", "is_final": false, "result": null, "confidence": 0.0}'

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == "Tell me more about that."
        assert parsed.is_final is False
        assert parsed.result is None
        assert parsed.confidence == 0.0

    def test_parse_valid_json_completion_response(self) -> None:
        """Test parsing valid JSON for completion."""
        raw = """
        {
            "message": "Thank you for this wonderful session!",
            "is_final": true,
            "result": {
                "values": [
                    {"name": "Integrity", "description": "Being honest", "importance": "Guides decisions"}
                ],
                "summary": "Your core value is integrity."
            },
            "confidence": 0.92
        }
        """

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == "Thank you for this wonderful session!"
        assert parsed.is_final is True
        assert parsed.result is not None
        assert len(parsed.result["values"]) == 1
        assert parsed.confidence == 0.92

    def test_parse_json_in_markdown_block(self) -> None:
        """Test parsing JSON wrapped in markdown code block."""
        raw = """
```json
{
    "message": "Here are my thoughts...",
    "is_final": false,
    "result": null,
    "confidence": 0.0
}
```
"""

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == "Here are my thoughts..."
        assert parsed.is_final is False

    def test_parse_json_in_generic_markdown_block(self) -> None:
        """Test parsing JSON in generic code block (no language specified)."""
        raw = """
```
{"message": "Testing", "is_final": false, "result": null, "confidence": 0.0}
```
"""

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == "Testing"
        assert parsed.is_final is False

    def test_fallback_for_plain_text_response(self) -> None:
        """Test graceful handling of non-JSON responses."""
        raw = "This is a plain text response without any JSON structure."

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == raw
        assert parsed.is_final is False
        assert parsed.result is None
        assert parsed.confidence == 0.0

    def test_fallback_for_invalid_json(self) -> None:
        """Test fallback for malformed JSON."""
        raw = '{"message": "incomplete json'

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == raw
        assert parsed.is_final is False

    def test_fallback_for_json_array(self) -> None:
        """Test fallback when JSON is an array instead of object."""
        raw = '["item1", "item2"]'

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == raw
        assert parsed.is_final is False

    def test_parse_with_extra_whitespace(self) -> None:
        """Test parsing JSON with leading/trailing whitespace."""
        raw = """

        {"message": "Trimmed correctly", "is_final": false, "result": null, "confidence": 0.0}

        """

        parsed = parse_llm_coaching_response(raw)

        assert parsed.message == "Trimmed correctly"


class TestShouldAutoComplete:
    """Tests for should_auto_complete function."""

    def test_auto_complete_when_all_conditions_met(self) -> None:
        """Test auto-completion triggers when all conditions are met."""
        response = LLMCoachingResponse(
            message="Session complete!",
            is_final=True,
            result={"values": []},
            confidence=0.85,
        )

        assert should_auto_complete(response) is True

    def test_no_auto_complete_when_not_final(self) -> None:
        """Test no auto-completion when is_final is False."""
        response = LLMCoachingResponse(
            message="Continuing...",
            is_final=False,
            result={"values": []},
            confidence=0.9,
        )

        assert should_auto_complete(response) is False

    def test_no_auto_complete_when_confidence_too_low(self) -> None:
        """Test no auto-completion when confidence below threshold."""
        response = LLMCoachingResponse(
            message="Maybe done?",
            is_final=True,
            result={"values": []},
            confidence=0.5,  # Below 0.7 threshold
        )

        assert should_auto_complete(response) is False

    def test_no_auto_complete_when_result_is_none(self) -> None:
        """Test no auto-completion when result is None."""
        response = LLMCoachingResponse(
            message="Done but no result",
            is_final=True,
            result=None,
            confidence=0.9,
        )

        assert should_auto_complete(response) is False

    def test_auto_complete_at_exact_threshold(self) -> None:
        """Test auto-completion at exactly the threshold."""
        response = LLMCoachingResponse(
            message="At threshold",
            is_final=True,
            result={"data": "value"},
            confidence=AUTO_COMPLETION_CONFIDENCE_THRESHOLD,
        )

        assert should_auto_complete(response) is True

    def test_no_auto_complete_just_below_threshold(self) -> None:
        """Test no auto-completion just below threshold."""
        response = LLMCoachingResponse(
            message="Just below",
            is_final=True,
            result={"data": "value"},
            confidence=AUTO_COMPLETION_CONFIDENCE_THRESHOLD - 0.01,
        )

        assert should_auto_complete(response) is False

    def test_auto_complete_with_empty_dict_result(self) -> None:
        """Test auto-completion with empty dict as result (valid result)."""
        response = LLMCoachingResponse(
            message="Empty result",
            is_final=True,
            result={},
            confidence=0.8,
        )

        # Empty dict is truthy for 'is not None' check
        assert should_auto_complete(response) is True


class TestAutoCompletionConfidenceThreshold:
    """Tests for the confidence threshold constant."""

    def test_threshold_value(self) -> None:
        """Test the threshold is set to expected value."""
        assert AUTO_COMPLETION_CONFIDENCE_THRESHOLD == 0.7

    def test_threshold_is_reasonable(self) -> None:
        """Test threshold is in reasonable range."""
        assert 0.5 <= AUTO_COMPLETION_CONFIDENCE_THRESHOLD <= 0.9
