"""Model pricing configuration for LLM token cost calculation.

This module provides pricing information for different LLM models
and utilities to calculate costs based on token usage.
"""

from typing import Any, Optional

# Pricing per 1,000 tokens in USD (as of October 2024)
# Source: https://aws.amazon.com/bedrock/pricing/
MODEL_PRICING: dict[str, dict[str, float]] = {
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "input": 0.003,  # $3.00 per 1M tokens
        "output": 0.015,  # $15.00 per 1M tokens
    },
    "anthropic.claude-3-5-sonnet-20240620-v1:0": {
        "input": 0.003,  # $3.00 per 1M tokens
        "output": 0.015,  # $15.00 per 1M tokens
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "input": 0.00025,  # $0.25 per 1M tokens
        "output": 0.00125,  # $1.25 per 1M tokens
    },
    "anthropic.claude-3-opus-20240229-v1:0": {
        "input": 0.015,  # $15.00 per 1M tokens
        "output": 0.075,  # $75.00 per 1M tokens
    },
    "anthropic.claude-3-sonnet-20240229-v1:0": {
        "input": 0.003,  # $3.00 per 1M tokens
        "output": 0.015,  # $15.00 per 1M tokens
    },
}


def get_model_pricing(model_id: str) -> dict[str, float]:
    """
    Get pricing information for a specific model.

    Args:
        model_id: Model identifier (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")

    Returns:
        dict with "input" and "output" pricing per 1K tokens
        Returns zero pricing if model not found

    Example:
        >>> pricing = get_model_pricing("anthropic.claude-3-haiku-20240307-v1:0")
        >>> pricing["input"]
        0.00025
    """
    return MODEL_PRICING.get(model_id, {"input": 0.0, "output": 0.0})


def calculate_cost(input_tokens: int, output_tokens: int, model_id: str) -> float:
    """
    Calculate the cost for token usage based on model pricing.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_id: Model identifier

    Returns:
        Cost in USD, rounded to 6 decimal places

    Example:
        >>> cost = calculate_cost(1000, 500, "anthropic.claude-3-haiku-20240307-v1:0")
        >>> cost
        0.000875
    """
    pricing = get_model_pricing(model_id)

    # Calculate cost per 1K tokens
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]

    total_cost = input_cost + output_cost

    # Round to 6 decimal places for precision
    return round(total_cost, 6)


def get_available_models() -> list[str]:
    """
    Get list of all models with configured pricing.

    Returns:
        List of model identifiers
    """
    return list(MODEL_PRICING.keys())


def get_model_info(model_id: str) -> Optional[dict[str, Any]]:
    """
    Get detailed information about a model.

    Args:
        model_id: Model identifier

    Returns:
        Dictionary with model details or None if not found
    """
    if model_id not in MODEL_PRICING:
        return None

    pricing = MODEL_PRICING[model_id]

    return {
        "model_id": model_id,
        "provider": "Anthropic",
        "pricing_per_1k_tokens": pricing,
        "pricing_per_1m_tokens": {
            "input": pricing["input"] * 1000,
            "output": pricing["output"] * 1000,
        },
    }


__all__ = [
    "MODEL_PRICING",
    "get_model_pricing",
    "calculate_cost",
    "get_available_models",
    "get_model_info",
]
