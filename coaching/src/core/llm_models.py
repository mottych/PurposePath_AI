"""Registry of all supported LLM models and providers.

This module defines the code-based registry of supported LLM models with their
provider implementations. Each model must have a corresponding provider
implementation in the infrastructure layer.

Design:
    - Type-safe with dataclass and enums
    - Code-based (requires deployment for new models)
    - Direct reference to provider classes
    - Capability and cost tracking
    - Provider filtering support

Architecture:
    Core utility following Clean Architecture principles. No external dependencies.
"""

from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers."""

    BEDROCK = "bedrock"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE_VERTEX = "google_vertex"


@dataclass
class SupportedModel:
    """
    LLM model definition with provider implementation reference.

    Each model MUST have a corresponding provider implementation in the
    infrastructure layer. Adding new models requires code deployment.

    Attributes:
        code: Unique model code (e.g., "CLAUDE_3_SONNET")
        provider: LLM provider enum value
        model_name: Actual model identifier for API calls
        version: Model version string
        provider_class: Reference to provider class name (string for lazy loading)
        capabilities: List of supported capabilities
        max_tokens: Maximum tokens supported by model
        cost_per_1k_tokens: Cost per 1000 tokens (for tracking)
        is_active: Whether model is currently active/available
    """

    code: str
    provider: LLMProvider
    model_name: str
    version: str
    provider_class: str  # String reference to avoid circular imports
    capabilities: list[str]
    max_tokens: int
    cost_per_1k_tokens: float
    is_active: bool = True


# Registry of ALL supported models
# New models require code deployment
#
# Note on Bedrock Inference Profiles:
#   Newer Claude models (v2+) require inference profiles. The BedrockLLMProvider
#   automatically converts base model IDs to region-prefixed inference profiles.
#   You can specify either format in model_name:
#   - Base model ID: "anthropic.claude-3-5-sonnet-20241022-v2:0" (auto-converted)
#   - Explicit profile: "us.anthropic.claude-3-5-sonnet-20241022-v2:0" (used as-is)
MODEL_REGISTRY: dict[str, SupportedModel] = {
    # ==========================================================================
    # AWS Bedrock Claude Models
    # ==========================================================================
    "CLAUDE_3_SONNET": SupportedModel(
        code="CLAUDE_3_SONNET",
        provider=LLMProvider.BEDROCK,
        model_name="anthropic.claude-3-sonnet-20240229-v1:0",
        version="20240229",
        provider_class="BedrockLLMProvider",
        capabilities=["chat", "analysis", "streaming", "function_calling"],
        max_tokens=4096,
        cost_per_1k_tokens=0.003,
        is_active=True,
    ),
    "CLAUDE_3_HAIKU": SupportedModel(
        code="CLAUDE_3_HAIKU",
        provider=LLMProvider.BEDROCK,
        model_name="anthropic.claude-3-haiku-20240307-v1:0",
        version="20240307",
        provider_class="BedrockLLMProvider",
        capabilities=["chat", "analysis", "streaming"],
        max_tokens=4096,
        cost_per_1k_tokens=0.00025,
        is_active=True,
    ),
    "CLAUDE_3_5_SONNET": SupportedModel(
        code="CLAUDE_3_5_SONNET",
        provider=LLMProvider.BEDROCK,
        model_name="anthropic.claude-3-5-sonnet-20240620-v1:0",
        version="20240620",
        provider_class="BedrockLLMProvider",
        capabilities=["chat", "analysis", "streaming", "function_calling", "vision"],
        max_tokens=8192,
        cost_per_1k_tokens=0.003,
        is_active=True,
    ),
    # Claude 3.5 Sonnet v2 - Requires inference profile (auto-converted by provider)
    "CLAUDE_3_5_SONNET_V2": SupportedModel(
        code="CLAUDE_3_5_SONNET_V2",
        provider=LLMProvider.BEDROCK,
        model_name="anthropic.claude-3-5-sonnet-20241022-v2:0",
        version="20241022",
        provider_class="BedrockLLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "pdf_support",
            "extended_context",
        ],
        max_tokens=200000,
        cost_per_1k_tokens=0.003,
        is_active=True,
    ),
    # Claude Sonnet 4.5 - Requires inference profile (auto-converted by provider)
    "CLAUDE_SONNET_4_5": SupportedModel(
        code="CLAUDE_SONNET_4_5",
        provider=LLMProvider.BEDROCK,
        model_name="anthropic.claude-sonnet-4-5-20250929-v1:0",
        version="20250929",
        provider_class="BedrockLLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "pdf_support",
            "extended_context",
            "extended_thinking",
            "priority_tier",
        ],
        max_tokens=200000,
        cost_per_1k_tokens=0.004,
        is_active=True,
    ),
    # Claude Opus 4.5 - Requires inference profile (auto-converted by provider)
    "CLAUDE_OPUS_4_5": SupportedModel(
        code="CLAUDE_OPUS_4_5",
        provider=LLMProvider.BEDROCK,
        model_name="anthropic.claude-opus-4-5-20250929-v1:0",
        version="20250929",
        provider_class="BedrockLLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "pdf_support",
            "extended_context",
            "extended_thinking",
            "priority_tier",
            "advanced_reasoning",
        ],
        max_tokens=200000,
        cost_per_1k_tokens=0.015,  # Opus tier pricing
        is_active=True,
    ),
    # ==========================================================================
    # OpenAI GPT Models
    # ==========================================================================
    # GPT-4o Series
    "GPT_4O": SupportedModel(
        code="GPT_4O",
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o",
        version="4o",
        provider_class="OpenAILLMProvider",
        capabilities=["chat", "analysis", "streaming", "function_calling", "vision"],
        max_tokens=128000,
        cost_per_1k_tokens=0.005,
        is_active=True,
    ),
    "GPT_4O_MINI": SupportedModel(
        code="GPT_4O_MINI",
        provider=LLMProvider.OPENAI,
        model_name="gpt-4o-mini",
        version="4o-mini",
        provider_class="OpenAILLMProvider",
        capabilities=["chat", "analysis", "streaming", "function_calling"],
        max_tokens=128000,
        cost_per_1k_tokens=0.00015,
        is_active=True,
    ),
    # GPT-5 Series
    "GPT_5_PRO": SupportedModel(
        code="GPT_5_PRO",
        provider=LLMProvider.OPENAI,
        model_name="gpt-5-pro",
        version="5.0",
        provider_class="OpenAILLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "advanced_reasoning",
        ],
        max_tokens=128000,
        cost_per_1k_tokens=0.02,
        is_active=True,
    ),
    "GPT_5": SupportedModel(
        code="GPT_5",
        provider=LLMProvider.OPENAI,
        model_name="gpt-5",
        version="5.0",
        provider_class="OpenAILLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "reasoning",
        ],
        max_tokens=128000,
        cost_per_1k_tokens=0.015,
        is_active=True,
    ),
    "GPT_5_MINI": SupportedModel(
        code="GPT_5_MINI",
        provider=LLMProvider.OPENAI,
        model_name="gpt-5-mini",
        version="5.0",
        provider_class="OpenAILLMProvider",
        capabilities=["chat", "analysis", "streaming", "function_calling", "reasoning"],
        max_tokens=128000,
        cost_per_1k_tokens=0.00225,  # Avg of $0.25/1M input, $2.00/1M output
        is_active=True,
    ),
    "GPT_5_NANO": SupportedModel(
        code="GPT_5_NANO",
        provider=LLMProvider.OPENAI,
        model_name="gpt-5-nano",
        version="5.0",
        provider_class="OpenAILLMProvider",
        capabilities=["chat", "analysis", "streaming", "function_calling"],
        max_tokens=64000,
        cost_per_1k_tokens=0.001,
        is_active=True,
    ),
    # GPT 5.2 Series - Latest flagship models (December 2025)
    "GPT_5_2": SupportedModel(
        code="GPT_5_2",
        provider=LLMProvider.OPENAI,
        model_name="gpt-5.2",
        version="5.2",
        provider_class="OpenAILLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "advanced_reasoning",
            "agentic",
        ],
        max_tokens=256000,
        cost_per_1k_tokens=0.00788,  # Avg of $1.75/1M input, $14/1M output
        is_active=True,
    ),
    "GPT_5_2_PRO": SupportedModel(
        code="GPT_5_2_PRO",
        provider=LLMProvider.OPENAI,
        model_name="gpt-5.2-pro",
        version="5.2",
        provider_class="OpenAILLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "advanced_reasoning",
            "extended_context",
            "agentic",
        ],
        max_tokens=256000,
        cost_per_1k_tokens=0.0945,  # Avg of $21/1M input, $168/1M output
        is_active=True,
    ),
    # ==========================================================================
    # Google Vertex AI / Gemini Models
    # ==========================================================================
    "GEMINI_2_5_PRO": SupportedModel(
        code="GEMINI_2_5_PRO",
        provider=LLMProvider.GOOGLE_VERTEX,
        model_name="gemini-2.5-pro",
        version="2.5",
        provider_class="GoogleVertexLLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "long_context",
            "multimodal",
            "thinking",
        ],
        max_tokens=1048576,  # 1M input tokens
        cost_per_1k_tokens=0.00563,  # Avg of $1.25/1M input, $10/1M output (<=200k)
        is_active=True,
    ),
    "GEMINI_2_5_FLASH": SupportedModel(
        code="GEMINI_2_5_FLASH",
        provider=LLMProvider.GOOGLE_VERTEX,
        model_name="gemini-2.5-flash",
        version="2.5",
        provider_class="GoogleVertexLLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "long_context",
            "thinking",
        ],
        max_tokens=1048576,  # 1M input tokens
        cost_per_1k_tokens=0.0014,  # Avg of $0.30/1M input, $2.50/1M output
        is_active=True,
    ),
    "GEMINI_2_5_FLASH_LITE": SupportedModel(
        code="GEMINI_2_5_FLASH_LITE",
        provider=LLMProvider.GOOGLE_VERTEX,
        model_name="gemini-2.5-flash-lite",
        version="2.5",
        provider_class="GoogleVertexLLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "long_context",
        ],
        max_tokens=1048576,
        cost_per_1k_tokens=0.00025,  # Avg of $0.10/1M input, $0.40/1M output
        is_active=True,
    ),
    # Gemini 3 Pro - Latest generation (Preview - December 2025)
    "GEMINI_3_PRO": SupportedModel(
        code="GEMINI_3_PRO",
        provider=LLMProvider.GOOGLE_VERTEX,
        model_name="gemini-3-pro-preview",
        version="3.0",
        provider_class="GoogleVertexLLMProvider",
        capabilities=[
            "chat",
            "analysis",
            "streaming",
            "function_calling",
            "vision",
            "long_context",
            "multimodal",
            "advanced_reasoning",
            "agentic",
            "thought_signatures",
        ],
        max_tokens=1048576,  # 1M input, 64k output
        cost_per_1k_tokens=0.007,  # Avg of $2/1M input, $12/1M output (<=200k)
        is_active=True,
    ),
}


def get_model(code: str) -> SupportedModel:
    """
    Get model by code. Type-safe and guaranteed to exist.

    Args:
        code: Model code from MODEL_REGISTRY

    Returns:
        SupportedModel definition

    Raises:
        ValueError: If model code not found in registry
    """
    if code not in MODEL_REGISTRY:
        available = sorted(MODEL_REGISTRY.keys())
        raise ValueError(
            f"Unknown model code: '{code}'. "
            f"Available models: {available}. "
            f"To add new models, update coaching/src/core/llm_models.py"
        )
    return MODEL_REGISTRY[code]


def list_models(
    provider: LLMProvider | None = None,
    active_only: bool = True,
    capability: str | None = None,
) -> list[SupportedModel]:
    """
    List all models with optional filters.

    Args:
        provider: Optional provider filter
        active_only: Only return active models (default: True)
        capability: Optional capability filter (e.g., "function_calling")

    Returns:
        List of SupportedModel definitions matching filters
    """
    models = list(MODEL_REGISTRY.values())

    if active_only:
        models = [m for m in models if m.is_active]
    if provider:
        models = [m for m in models if m.provider == provider]
    if capability:
        models = [m for m in models if capability in m.capabilities]

    return models


def get_model_provider_class(code: str) -> str:
    """
    Get provider class name for model.

    Args:
        code: Model code

    Returns:
        Provider class name string for instantiation

    Raises:
        ValueError: If model not found
    """
    model = get_model(code)
    return model.provider_class


# Default model for generic coaching operations
# This is used when no specific model is configured for a topic
DEFAULT_MODEL_CODE = "CLAUDE_3_5_SONNET_V2"
DEFAULT_MODEL_ID = MODEL_REGISTRY[DEFAULT_MODEL_CODE].model_name


__all__ = [
    "DEFAULT_MODEL_CODE",
    "DEFAULT_MODEL_ID",
    "MODEL_REGISTRY",
    "LLMProvider",
    "SupportedModel",
    "get_model",
    "get_model_provider_class",
    "list_models",
]
