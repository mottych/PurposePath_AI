"""Unit tests for model pricing calculations."""

import pytest
from coaching.src.infrastructure.llm.model_pricing import (
    MODEL_PRICING,
    calculate_cost,
    get_available_models,
    get_model_info,
    get_model_pricing,
)


@pytest.mark.unit
class TestGetModelPricing:
    """Test get_model_pricing function."""

    def test_get_pricing_for_existing_model(self):
        """Test getting pricing for a known model."""
        # Arrange
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

        # Act
        pricing = get_model_pricing(model_id)

        # Assert
        assert "input" in pricing
        assert "output" in pricing
        assert pricing["input"] == 0.00025
        assert pricing["output"] == 0.00125

    def test_get_pricing_for_sonnet_model(self):
        """Test pricing for Claude Sonnet model."""
        # Arrange
        model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        # Act
        pricing = get_model_pricing(model_id)

        # Assert
        assert pricing["input"] == 0.003
        assert pricing["output"] == 0.015

    def test_get_pricing_for_unknown_model_returns_zero(self):
        """Test that unknown models return zero pricing."""
        # Arrange
        model_id = "unknown-model-id"

        # Act
        pricing = get_model_pricing(model_id)

        # Assert
        assert pricing["input"] == 0.0
        assert pricing["output"] == 0.0


@pytest.mark.unit
class TestCalculateCost:
    """Test calculate_cost function."""

    def test_calculate_cost_with_haiku(self):
        """Test cost calculation for Haiku model."""
        # Arrange
        input_tokens = 1000
        output_tokens = 500
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        # Input: 1000/1000 * 0.00025 = 0.00025
        # Output: 500/1000 * 0.00125 = 0.000625
        # Total: 0.000875
        assert cost == pytest.approx(0.000875, rel=1e-9)

    def test_calculate_cost_with_sonnet(self):
        """Test cost calculation for Sonnet model."""
        # Arrange
        input_tokens = 2000
        output_tokens = 1000
        model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        # Input: 2000/1000 * 0.003 = 0.006
        # Output: 1000/1000 * 0.015 = 0.015
        # Total: 0.021
        assert cost == pytest.approx(0.021, rel=1e-9)

    def test_calculate_cost_with_opus(self):
        """Test cost calculation for Opus model (most expensive)."""
        # Arrange
        input_tokens = 1000
        output_tokens = 1000
        model_id = "anthropic.claude-3-opus-20240229-v1:0"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        # Input: 1000/1000 * 0.015 = 0.015
        # Output: 1000/1000 * 0.075 = 0.075
        # Total: 0.090
        assert cost == pytest.approx(0.090, rel=1e-9)

    def test_calculate_cost_with_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        # Arrange
        input_tokens = 0
        output_tokens = 0
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        assert cost == 0.0

    def test_calculate_cost_with_unknown_model_returns_zero(self):
        """Test that cost is zero for unknown models."""
        # Arrange
        input_tokens = 1000
        output_tokens = 500
        model_id = "unknown-model"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        assert cost == 0.0

    def test_cost_rounding_precision(self):
        """Test that cost is rounded to 6 decimal places."""
        # Arrange
        input_tokens = 333  # Will create repeating decimal
        output_tokens = 666
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        # Should have at most 6 decimal places
        cost_str = f"{cost:.10f}"
        assert len(cost_str.split(".")[1].rstrip("0")) <= 6


@pytest.mark.unit
class TestGetAvailableModels:
    """Test get_available_models function."""

    def test_get_available_models_returns_list(self):
        """Test that available models returns a list."""
        # Act
        models = get_available_models()

        # Assert
        assert isinstance(models, list)
        assert len(models) > 0

    def test_get_available_models_contains_expected_models(self):
        """Test that available models includes expected model IDs."""
        # Act
        models = get_available_models()

        # Assert
        assert "anthropic.claude-3-haiku-20240307-v1:0" in models
        assert "anthropic.claude-3-5-sonnet-20241022-v2:0" in models
        assert "anthropic.claude-3-opus-20240229-v1:0" in models

    def test_available_models_count(self):
        """Test that we have pricing for expected number of models."""
        # Act
        models = get_available_models()

        # Assert
        assert len(models) == len(MODEL_PRICING)


@pytest.mark.unit
class TestGetModelInfo:
    """Test get_model_info function."""

    def test_get_info_for_existing_model(self):
        """Test getting detailed info for existing model."""
        # Arrange
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

        # Act
        info = get_model_info(model_id)

        # Assert
        assert info is not None
        assert info["model_id"] == model_id
        assert info["provider"] == "Anthropic"
        assert "pricing_per_1k_tokens" in info
        assert "pricing_per_1m_tokens" in info

    def test_get_info_includes_pricing_formats(self):
        """Test that model info includes both 1K and 1M pricing."""
        # Arrange
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"

        # Act
        info = get_model_info(model_id)

        # Assert
        assert info is not None
        # Per 1K tokens
        assert info["pricing_per_1k_tokens"]["input"] == 0.00025
        assert info["pricing_per_1k_tokens"]["output"] == 0.00125
        # Per 1M tokens
        assert info["pricing_per_1m_tokens"]["input"] == 0.25
        assert info["pricing_per_1m_tokens"]["output"] == 1.25

    def test_get_info_for_unknown_model_returns_none(self):
        """Test that unknown models return None."""
        # Arrange
        model_id = "unknown-model"

        # Act
        info = get_model_info(model_id)

        # Assert
        assert info is None


@pytest.mark.unit
class TestModelPricingIntegration:
    """Integration tests for model pricing."""

    def test_cost_calculation_matches_expected_real_world_usage(self):
        """Test realistic token usage scenario."""
        # Arrange - Typical coaching conversation
        input_tokens = 1500  # Conversation history + new message
        output_tokens = 800  # AI response
        model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        # Input: 1.5K * $0.003 = $0.0045
        # Output: 0.8K * $0.015 = $0.012
        # Total: $0.0165
        expected_cost = 0.0165
        assert cost == pytest.approx(expected_cost, rel=1e-9)

    def test_high_volume_cost_calculation(self):
        """Test cost for high-volume usage."""
        # Arrange - Large conversation
        input_tokens = 10000
        output_tokens = 5000
        model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

        # Act
        cost = calculate_cost(input_tokens, output_tokens, model_id)

        # Assert
        # Input: 10K * $0.003 = $0.030
        # Output: 5K * $0.015 = $0.075
        # Total: $0.105
        expected_cost = 0.105
        assert cost == pytest.approx(expected_cost, rel=1e-9)
