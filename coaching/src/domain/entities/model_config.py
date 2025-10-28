"""Model configuration entity for AI model management."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ModelPricing(BaseModel):
    """Pricing information for a model."""

    input_cost_per_1k_tokens: float = Field(..., description="Cost per 1000 input tokens in USD")
    output_cost_per_1k_tokens: float = Field(..., description="Cost per 1000 output tokens in USD")


class ModelConfig(BaseModel):
    """
    Configuration entity for AI models.

    Represents configurable settings for LLM models including
    pricing, limits, and operational status.

    Attributes:
        model_id: Unique identifier (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0")
        provider: Model provider (e.g., "anthropic", "openai")
        display_name: Human-readable name
        pricing: Cost per 1000 tokens (input/output)
        context_window: Maximum context window size
        max_tokens: Maximum output tokens
        is_active: Whether model is available for use
        supports_streaming: Whether model supports streaming responses
        metadata: Additional configuration data
    """


    model_id: str = Field(..., description="Unique model identifier")
    provider: str = Field(..., description="Model provider name")
    display_name: str = Field(..., description="Human-readable model name")
    pricing: ModelPricing = Field(..., description="Model pricing information")
    context_window: int = Field(..., description="Maximum context window size", gt=0)
    max_tokens: int = Field(..., description="Maximum output tokens", gt=0)
    is_active: bool = Field(default=True, description="Whether model is active")
    supports_streaming: bool = Field(default=False, description="Whether model supports streaming")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = ConfigDict(
        frozen=False,
        json_schema_extra={
            "example": {
                "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "provider": "anthropic",
                "display_name": "Claude 3.5 Sonnet",
                "pricing": {
                    "input_cost_per_1k_tokens": 0.003,
                    "output_cost_per_1k_tokens": 0.015,
                },
                "context_window": 200000,
                "max_tokens": 8192,
                "is_active": True,
                "supports_streaming": True,
                "metadata": {"description": "Latest Claude 3.5 Sonnet model"},
            }
        },
    )


__all__ = ["ModelConfig", "ModelPricing"]
