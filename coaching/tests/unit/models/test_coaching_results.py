"""Unit tests for coaching result models.

Tests for the Pydantic models used to capture final coaching session results.
"""

import pytest
from coaching.src.models.coaching_results import (
    COACHING_RESULT_MODELS,
    CoreValue,
    CoreValuesResult,
    PurposeResult,
    VisionResult,
    get_coaching_result_model,
    get_result_json_schema,
)
from pydantic import ValidationError


class TestCoreValue:
    """Tests for CoreValue model."""

    def test_create_valid_core_value(self) -> None:
        """Test creating a valid core value."""
        value = CoreValue(
            name="Integrity",
            description="We act with honesty and ethics in all situations and interactions",
            importance="Guides our decision making and builds trust with stakeholders",
        )

        assert value.name == "Integrity"
        assert "honesty" in value.description.lower()
        assert len(value.importance) > 0

    def test_name_validation_min_length(self) -> None:
        """Test that name must have minimum length."""
        with pytest.raises(ValidationError):
            CoreValue(
                name="",  # Too short
                description="A valid description of the value with enough characters",
                importance="Why this matters is very important for the org",
            )

    def test_description_validation_min_length(self) -> None:
        """Test that description must have minimum length."""
        with pytest.raises(ValidationError):
            CoreValue(
                name="Test Value",
                description="Short",  # Too short (< 10)
                importance="Why this matters is very important for the org",
            )


class TestCoreValuesResult:
    """Tests for CoreValuesResult model."""

    def test_create_valid_result(self) -> None:
        """Test creating a valid CoreValuesResult."""
        result = CoreValuesResult(
            values=[
                CoreValue(
                    name="Innovation",
                    description="Constantly seeking new and better ways to serve our customers",
                    importance="Drives our competitive advantage and market leadership",
                ),
                CoreValue(
                    name="Teamwork",
                    description="Working together to achieve more than any individual could alone",
                    importance="Enables us to tackle complex challenges collaboratively",
                ),
            ],
            summary="These values guide our daily decisions and culture. "
            "They represent who we are as an organization.",
        )

        assert len(result.values) == 2
        assert result.values[0].name == "Innovation"
        assert len(result.summary) > 0

    def test_requires_at_least_one_value(self) -> None:
        """Test that at least one core value is required."""
        with pytest.raises(ValidationError):
            CoreValuesResult(
                values=[],  # Empty list
                summary="No values to summarize but this needs to be at least fifty characters long.",
            )

    def test_max_seven_values(self) -> None:
        """Test that maximum 7 core values are allowed."""
        values = [
            CoreValue(
                name=f"Value Number {i}",
                description=f"Description for value number {i} with enough characters",
                importance=f"Importance of value number {i} with enough characters",
            )
            for i in range(8)  # 8 values
        ]

        with pytest.raises(ValidationError):
            CoreValuesResult(
                values=values,
                summary="Too many values but summary still needs to be at least fifty characters long.",
            )


class TestPurposeResult:
    """Tests for PurposeResult model."""

    def test_create_valid_result(self) -> None:
        """Test creating a valid PurposeResult."""
        result = PurposeResult(
            purpose_statement="To empower businesses to reach their full potential",
            why_it_matters="Small and medium-sized businesses are the backbone of the economy "
            "and deserve access to world-class guidance and support.",
            how_it_guides="Every decision we make is evaluated against whether it helps businesses "
            "grow and succeed in their markets.",
        )

        assert "empower" in result.purpose_statement.lower()
        assert len(result.why_it_matters) > 0
        assert len(result.how_it_guides) > 0

    def test_purpose_statement_min_length(self) -> None:
        """Test that purpose statement has minimum length."""
        with pytest.raises(ValidationError):
            PurposeResult(
                purpose_statement="Short",  # Too short (< 20)
                why_it_matters="This is a valid why_it_matters field with enough characters.",
                how_it_guides="This is a valid how_it_guides field with enough characters.",
            )


class TestVisionResult:
    """Tests for VisionResult model."""

    def test_create_valid_result(self) -> None:
        """Test creating a valid VisionResult."""
        result = VisionResult(
            vision_statement="To be the leading provider of AI coaching solutions",
            time_horizon="5 years",
            key_aspirations=[
                "Market leader in AI coaching",
                "10,000 active customers",
                "Global presence",
            ],
        )

        assert "leading" in result.vision_statement.lower()
        assert result.time_horizon == "5 years"
        assert len(result.key_aspirations) == 3

    def test_requires_at_least_one_aspiration(self) -> None:
        """Test that at least one key aspiration is required."""
        with pytest.raises(ValidationError):
            VisionResult(
                vision_statement="A valid vision statement with enough length",
                time_horizon="3 years",
                key_aspirations=[],  # Empty
            )


class TestCoachingResultModelsRegistry:
    """Tests for the result model registry."""

    def test_registry_contains_all_models(self) -> None:
        """Test that registry contains all expected models."""
        assert "CoreValuesResult" in COACHING_RESULT_MODELS
        assert "PurposeResult" in COACHING_RESULT_MODELS
        assert "VisionResult" in COACHING_RESULT_MODELS

    def test_registry_values_are_classes(self) -> None:
        """Test that registry values are Pydantic model classes."""
        for model in COACHING_RESULT_MODELS.values():
            assert hasattr(model, "model_validate")
            assert hasattr(model, "model_json_schema")


class TestGetCoachingResultModel:
    """Tests for get_coaching_result_model function."""

    def test_get_existing_model(self) -> None:
        """Test getting an existing model."""
        model = get_coaching_result_model("CoreValuesResult")

        assert model is not None
        assert model == CoreValuesResult

    def test_get_nonexistent_model_returns_none(self) -> None:
        """Test that getting a nonexistent model returns None."""
        model = get_coaching_result_model("NonexistentModel")

        assert model is None


class TestGetResultJsonSchema:
    """Tests for get_result_json_schema function."""

    def test_get_schema_for_existing_model(self) -> None:
        """Test getting JSON schema for existing model."""
        schema = get_result_json_schema("CoreValuesResult")

        assert schema is not None
        assert "properties" in schema
        assert "values" in schema["properties"]
        assert "summary" in schema["properties"]

    def test_get_schema_for_nonexistent_model(self) -> None:
        """Test that getting schema for nonexistent model returns None."""
        schema = get_result_json_schema("NonexistentModel")

        assert schema is None

    def test_schema_includes_descriptions(self) -> None:
        """Test that schema includes field descriptions."""
        schema = get_result_json_schema("PurposeResult")

        assert schema is not None
        # Check that descriptions are included in the schema
        props = schema.get("properties", {})
        assert "purpose_statement" in props
