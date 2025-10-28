"""Unit tests for LLM Interactions Registry."""

import pytest
from coaching.src.core.llm_interactions import (
    INTERACTION_REGISTRY,
    InteractionCategory,
    LLMInteraction,
    ParameterValidationError,
    get_interaction,
    list_interactions,
    validate_parameters,
)


class TestLLMInteraction:
    """Tests for LLMInteraction dataclass."""

    def test_validate_template_parameters_all_required_present(self) -> None:
        """Test validation passes when all required parameters present."""
        interaction = LLMInteraction(
            code="TEST_INTERACTION",
            description="Test interaction",
            category=InteractionCategory.ANALYSIS,
            required_parameters=["goal_text", "purpose"],
            optional_parameters=["context"],
            handler_class="TestService",
        )

        # Should not raise
        interaction.validate_template_parameters(["goal_text", "purpose"])

    def test_validate_template_parameters_missing_required(self) -> None:
        """Test validation fails when required parameter missing."""
        interaction = LLMInteraction(
            code="TEST_INTERACTION",
            description="Test interaction",
            category=InteractionCategory.ANALYSIS,
            required_parameters=["goal_text", "purpose"],
            optional_parameters=[],
            handler_class="TestService",
        )

        with pytest.raises(ParameterValidationError) as exc_info:
            interaction.validate_template_parameters(["goal_text"])

        assert "missing required parameters" in str(exc_info.value).lower()
        assert "purpose" in str(exc_info.value)

    def test_validate_template_parameters_unsupported_used(self) -> None:
        """Test validation fails when unsupported parameter used."""
        interaction = LLMInteraction(
            code="TEST_INTERACTION",
            description="Test interaction",
            category=InteractionCategory.ANALYSIS,
            required_parameters=["goal_text"],
            optional_parameters=[],
            handler_class="TestService",
        )

        with pytest.raises(ParameterValidationError) as exc_info:
            interaction.validate_template_parameters(["goal_text", "invalid_param"])

        assert "unsupported parameters" in str(exc_info.value).lower()
        assert "invalid_param" in str(exc_info.value)

    def test_validate_template_parameters_optional_allowed(self) -> None:
        """Test validation passes with optional parameters."""
        interaction = LLMInteraction(
            code="TEST_INTERACTION",
            description="Test interaction",
            category=InteractionCategory.ANALYSIS,
            required_parameters=["goal_text"],
            optional_parameters=["context", "constraints"],
            handler_class="TestService",
        )

        # Should not raise - optional parameters are allowed
        interaction.validate_template_parameters(["goal_text", "context"])

    def test_get_parameter_schema(self) -> None:
        """Test parameter schema generation."""
        interaction = LLMInteraction(
            code="TEST_INTERACTION",
            description="Test interaction",
            category=InteractionCategory.ANALYSIS,
            required_parameters=["goal_text", "purpose"],
            optional_parameters=["context"],
            handler_class="TestService",
        )

        schema = interaction.get_parameter_schema()

        assert schema["required"] == ["goal_text", "purpose"]
        assert schema["optional"] == ["context"]
        assert schema["all_parameters"] == ["goal_text", "purpose", "context"]


class TestInteractionRegistry:
    """Tests for interaction registry functions."""

    def test_get_interaction_exists(self) -> None:
        """Test retrieving existing interaction from registry."""
        interaction = get_interaction("ALIGNMENT_ANALYSIS")

        assert interaction.code == "ALIGNMENT_ANALYSIS"
        assert interaction.category == InteractionCategory.ANALYSIS
        assert len(interaction.required_parameters) > 0
        assert interaction.handler_class == "AlignmentAnalysisService"

    def test_get_interaction_not_found(self) -> None:
        """Test helpful error when interaction not in registry."""
        with pytest.raises(ValueError) as exc_info:
            get_interaction("INVALID_CODE")

        error_msg = str(exc_info.value)
        assert "Unknown interaction code" in error_msg
        assert "INVALID_CODE" in error_msg
        assert "Available interactions" in error_msg

    def test_list_interactions_all(self) -> None:
        """Test listing all interactions."""
        interactions = list_interactions()

        assert len(interactions) > 0
        assert all(isinstance(i, LLMInteraction) for i in interactions)
        # Verify some expected interactions exist
        codes = [i.code for i in interactions]
        assert "ALIGNMENT_ANALYSIS" in codes
        assert "COACHING_RESPONSE" in codes

    def test_list_interactions_by_category(self) -> None:
        """Test filtering interactions by category."""
        analysis = list_interactions(category=InteractionCategory.ANALYSIS)

        assert len(analysis) > 0
        assert all(i.category == InteractionCategory.ANALYSIS for i in analysis)

        coaching = list_interactions(category=InteractionCategory.COACHING)
        assert len(coaching) > 0
        assert all(i.category == InteractionCategory.COACHING for i in coaching)

    def test_validate_parameters_all_required_provided(self) -> None:
        """Test parameter validation with all required present."""
        # Should not raise
        validate_parameters(
            "ALIGNMENT_ANALYSIS",
            {"goal_text": "test", "purpose": "test", "values": "test"},
        )

    def test_validate_parameters_missing_required(self) -> None:
        """Test parameter validation with missing required."""
        with pytest.raises(ValueError) as exc_info:
            validate_parameters("ALIGNMENT_ANALYSIS", {"goal_text": "test"})

        error_msg = str(exc_info.value)
        assert "Missing required parameters" in error_msg
        assert "purpose" in error_msg or "values" in error_msg

    def test_interaction_registry_completeness(self) -> None:
        """Test that all interactions in registry have required fields."""
        for code, interaction in INTERACTION_REGISTRY.items():
            # Verify all required fields present
            assert interaction.code == code
            assert len(interaction.description) > 0
            assert isinstance(interaction.category, InteractionCategory)
            assert isinstance(interaction.required_parameters, list)
            assert isinstance(interaction.optional_parameters, list)
            assert len(interaction.handler_class) > 0

    def test_interaction_registry_no_duplicate_codes(self) -> None:
        """Test that interaction codes are unique."""
        codes = [i.code for i in INTERACTION_REGISTRY.values()]
        assert len(codes) == len(set(codes)), "Duplicate interaction codes found"


__all__ = []  # Test module, no exports
