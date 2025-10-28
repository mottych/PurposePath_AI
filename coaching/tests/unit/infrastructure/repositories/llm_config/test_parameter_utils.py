"""Unit tests for parameter utility functions."""

from coaching.src.infrastructure.repositories.llm_config.parameter_utils import (
    extract_template_parameters,
    validate_parameter_match,
)


class TestExtractTemplateParameters:
    """Tests for extract_template_parameters function."""

    def test_extract_simple_parameters(self) -> None:
        """Test extracting simple parameters from template."""
        template = "Goal: {goal_text}\nPurpose: {purpose}\nValues: {values}"
        params = extract_template_parameters(template)

        assert set(params) == {"goal_text", "purpose", "values"}
        assert params == sorted(params)  # Should be sorted

    def test_extract_parameters_with_spaces(self) -> None:
        """Test extraction handles spaces in placeholders."""
        template = "Goal: { goal_text }\nPurpose: {purpose}"
        params = extract_template_parameters(template)

        assert set(params) == {"goal_text", "purpose"}

    def test_extract_duplicate_parameters(self) -> None:
        """Test that duplicate parameters are deduplicated."""
        template = "First: {goal}\nSecond: {goal}\nThird: {goal}"
        params = extract_template_parameters(template)

        assert params == ["goal"]  # Only one instance

    def test_extract_no_parameters(self) -> None:
        """Test extraction from template with no parameters."""
        template = "This is a static template with no parameters"
        params = extract_template_parameters(template)

        assert params == []

    def test_extract_mixed_formatting(self) -> None:
        """Test extraction with various parameter formats."""
        template = "{param1} text {param2} more {param3}"
        params = extract_template_parameters(template)

        assert set(params) == {"param1", "param2", "param3"}


class TestValidateParameterMatch:
    """Tests for validate_parameter_match function."""

    def test_validate_all_required_present(self) -> None:
        """Test validation passes when all required present."""
        is_valid, details = validate_parameter_match(
            template_params=["goal", "purpose", "values"],
            required_params=["goal", "purpose", "values"],
            optional_params=[],
        )

        assert is_valid is True
        assert details["missing_required"] == []
        assert details["unsupported_used"] == []
        assert details["is_valid"] is True

    def test_validate_missing_required(self) -> None:
        """Test validation fails when required parameter missing."""
        is_valid, details = validate_parameter_match(
            template_params=["goal", "values"],
            required_params=["goal", "purpose", "values"],
            optional_params=[],
        )

        assert is_valid is False
        assert "purpose" in details["missing_required"]
        assert details["is_valid"] is False

    def test_validate_unsupported_used(self) -> None:
        """Test validation fails when unsupported parameter used."""
        is_valid, details = validate_parameter_match(
            template_params=["goal", "purpose", "invalid_param"],
            required_params=["goal", "purpose"],
            optional_params=[],
        )

        assert is_valid is False
        assert "invalid_param" in details["unsupported_used"]

    def test_validate_optional_allowed(self) -> None:
        """Test validation passes with optional parameters."""
        is_valid, details = validate_parameter_match(
            template_params=["goal", "purpose", "context"],
            required_params=["goal", "purpose"],
            optional_params=["context", "constraints"],
        )

        assert is_valid is True
        assert details["missing_required"] == []
        assert details["unsupported_used"] == []

    def test_validate_details_structure(self) -> None:
        """Test that validation details have correct structure."""
        is_valid, details = validate_parameter_match(
            template_params=["goal"],
            required_params=["goal"],
            optional_params=["context"],
        )

        assert "template_parameters" in details
        assert "required_parameters" in details
        assert "optional_parameters" in details
        assert "missing_required" in details
        assert "unsupported_used" in details
        assert "is_valid" in details

        assert details["template_parameters"] == ["goal"]
        assert details["required_parameters"] == ["goal"]
        assert details["optional_parameters"] == ["context"]

    def test_validate_mixed_errors(self) -> None:
        """Test validation with both missing and unsupported parameters."""
        is_valid, details = validate_parameter_match(
            template_params=["goal", "invalid"],
            required_params=["goal", "purpose"],
            optional_params=[],
        )

        assert is_valid is False
        assert "purpose" in details["missing_required"]
        assert "invalid" in details["unsupported_used"]


__all__ = []  # Test module, no exports
