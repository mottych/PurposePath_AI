"""LLM provider-specific exceptions.

This module defines exceptions for LLM provider operations,
supporting clear error handling across different providers.
"""


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""

    def __init__(self, message: str, provider: str | None = None) -> None:
        """Initialize LLM provider exception.

        Args:
            message: Error message
            provider: Provider name that caused the error
        """
        self.provider = provider
        super().__init__(message)


class ProviderNotConfiguredError(LLMProviderError):
    """Raised when a provider's credentials are not configured.

    This occurs when attempting to use a provider (OpenAI, Google Vertex, etc.)
    without the required API keys or credentials being set.
    """

    def __init__(self, provider: str, missing_config: str) -> None:
        """Initialize provider not configured error.

        Args:
            provider: Provider name (e.g., "openai", "google_vertex")
            missing_config: Description of missing configuration
        """
        self.missing_config = missing_config
        super().__init__(
            f"Provider '{provider}' is not configured. Missing: {missing_config}",
            provider=provider,
        )


class ModelNotAvailableError(LLMProviderError):
    """Raised when a model is not available or has been disabled.

    This occurs when attempting to use a model that exists in the registry
    but has `is_active=False` or is otherwise unavailable.
    """

    def __init__(self, model_code: str, reason: str) -> None:
        """Initialize model not available error.

        Args:
            model_code: Model code from MODEL_REGISTRY
            reason: Reason why model is not available
        """
        self.model_code = model_code
        self.reason = reason
        super().__init__(f"Model '{model_code}' is not available: {reason}")


class ModelNotFoundError(LLMProviderError):
    """Raised when a model code is not found in the registry.

    This occurs when attempting to use a model_code that doesn't exist
    in MODEL_REGISTRY.
    """

    def __init__(self, model_code: str, available_models: list[str]) -> None:
        """Initialize model not found error.

        Args:
            model_code: Model code that was not found
            available_models: List of available model codes
        """
        self.model_code = model_code
        self.available_models = available_models
        super().__init__(
            f"Model '{model_code}' not found in registry. Available models: {available_models}"
        )


class ProviderGenerationError(LLMProviderError):
    """Raised when LLM generation fails at the provider level.

    This wraps provider-specific errors (API errors, rate limits, etc.)
    in a consistent exception type.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        original_error: Exception,
    ) -> None:
        """Initialize provider generation error.

        Args:
            provider: Provider name
            model: Model that was being used
            original_error: Original exception from provider
        """
        self.model = model
        self.original_error = original_error
        super().__init__(
            f"LLM generation failed with provider '{provider}' model '{model}': {original_error!s}",
            provider=provider,
        )


__all__ = [
    "LLMProviderError",
    "ModelNotAvailableError",
    "ModelNotFoundError",
    "ProviderGenerationError",
    "ProviderNotConfiguredError",
]
