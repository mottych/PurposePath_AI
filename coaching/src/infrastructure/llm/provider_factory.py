"""LLM Provider Factory for dynamic multi-provider model selection.

This module provides a factory for creating and caching LLM providers based on
model configuration from MODEL_REGISTRY. It enables the system to dynamically
select the correct provider (Bedrock, OpenAI, Google Vertex, etc.) based on
the model code specified in topic configuration.

Design:
    - Singleton caching per provider type (not per model)
    - Model code resolution to actual model name
    - Lazy initialization of providers
    - Provider-specific credential validation

Architecture:
    Infrastructure layer component following Clean Architecture.
    Uses providers from the same layer and models from core layer.

Usage:
    factory = LLMProviderFactory(settings)
    provider, model_name = factory.get_provider_for_model("GPT_5_MINI")
    response = await provider.generate(messages, model=model_name, ...)

Related Issues:
    - Issue #136: Implement LLM Provider Factory
    - Issue #75: Add support for Claude 4/4.5, GPT-5, and Gemini 2.5 models
"""

from typing import Any

import structlog
from coaching.src.core.config_multitenant import (
    Settings,
    get_google_vertex_credentials,
    get_openai_api_key,
)
from coaching.src.core.llm_models import (
    MODEL_REGISTRY,
    LLMProvider,
    SupportedModel,
    get_model,
)
from coaching.src.infrastructure.llm.exceptions import (
    ModelNotAvailableError,
    ModelNotFoundError,
    ProviderNotConfiguredError,
)

logger = structlog.get_logger(__name__)


class LLMProviderFactory:
    """Factory for creating and managing LLM providers.

    This factory handles:
    - Model code resolution to provider and model name
    - Provider instantiation with appropriate credentials
    - Provider caching (singleton per provider type)
    - Validation of model availability and provider configuration

    Attributes:
        _settings: Application settings for provider configuration
        _providers: Cache of instantiated provider instances
        _bedrock_client: Optional pre-injected Bedrock client for testing
    """

    def __init__(
        self,
        settings: Settings,
        bedrock_client: Any | None = None,
    ) -> None:
        """Initialize the LLM Provider Factory.

        Args:
            settings: Application settings with provider configuration
            bedrock_client: Optional Bedrock client (for dependency injection in tests)
        """
        self._settings = settings
        # Use Any to avoid Protocol parameter name compatibility issues
        self._providers: dict[LLMProvider, Any] = {}
        self._bedrock_client = bedrock_client
        logger.info("LLM Provider Factory initialized")

    def get_provider_for_model(
        self,
        model_code: str,
    ) -> tuple[Any, str]:
        """Get provider instance and resolved model name for a model code.

        This is the main entry point for model resolution. It:
        1. Looks up the model code in MODEL_REGISTRY
        2. Validates the model is active
        3. Gets or creates the appropriate provider
        4. Returns the provider and the actual model name for API calls

        Args:
            model_code: Model code from MODEL_REGISTRY (e.g., "GPT_5_MINI", "CLAUDE_3_5_SONNET")

        Returns:
            Tuple of (provider_instance, actual_model_name)
            - provider_instance: The LLM provider to use for generation
            - actual_model_name: The model identifier to pass to the provider API

        Raises:
            ModelNotFoundError: If model_code not in MODEL_REGISTRY
            ModelNotAvailableError: If model is inactive (is_active=False)
            ProviderNotConfiguredError: If provider credentials are not set
        """
        # Step 1: Lookup model in registry
        try:
            model_config = get_model(model_code)
        except ValueError as e:
            available_models = list(MODEL_REGISTRY.keys())
            logger.error(
                "Model not found in registry",
                model_code=model_code,
                available_models=available_models,
            )
            raise ModelNotFoundError(model_code, available_models) from e

        # Step 2: Validate model is active
        if not model_config.is_active:
            logger.warning(
                "Attempted to use inactive model",
                model_code=model_code,
                model_name=model_config.model_name,
            )
            raise ModelNotAvailableError(
                model_code=model_code,
                reason="Model is marked as inactive. Enable it in MODEL_REGISTRY.",
            )

        # Step 3: Get or create provider
        provider = self._get_or_create_provider(model_config.provider)

        logger.info(
            "Provider resolved for model",
            model_code=model_code,
            model_name=model_config.model_name,
            provider=model_config.provider.value,
        )

        return provider, model_config.model_name

    def get_model_info(self, model_code: str) -> SupportedModel:
        """Get model configuration from registry.

        Convenience method to access model metadata without creating a provider.

        Args:
            model_code: Model code from MODEL_REGISTRY

        Returns:
            SupportedModel configuration

        Raises:
            ModelNotFoundError: If model_code not in registry
        """
        try:
            return get_model(model_code)
        except ValueError as e:
            available_models = list(MODEL_REGISTRY.keys())
            raise ModelNotFoundError(model_code, available_models) from e

    def is_provider_configured(self, provider: LLMProvider) -> bool:
        """Check if a provider has required credentials configured.

        Args:
            provider: Provider type to check

        Returns:
            True if provider credentials are available
        """
        if provider == LLMProvider.BEDROCK:
            # Bedrock uses IAM roles, always considered configured
            return True
        elif provider == LLMProvider.OPENAI:
            return get_openai_api_key() is not None
        elif provider == LLMProvider.GOOGLE_VERTEX:
            # Check if credentials are available (env var or secrets manager)
            import os

            return (
                os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None
                or get_google_vertex_credentials() is not None
                or self._settings.google_project_id is not None
            )
        elif provider == LLMProvider.ANTHROPIC:
            return self._settings.anthropic_api_key is not None
        return False

    def _get_or_create_provider(
        self,
        provider_type: LLMProvider,
    ) -> Any:
        """Get cached provider or create new one.

        Providers are cached as singletons per provider type (not per model).
        This ensures efficient resource usage while supporting multiple models
        from the same provider.

        Args:
            provider_type: Type of provider to create

        Returns:
            LLM provider instance

        Raises:
            ProviderNotConfiguredError: If provider credentials missing
        """
        # Return cached provider if available
        if provider_type in self._providers:
            return self._providers[provider_type]

        # Create new provider
        provider = self._create_provider(provider_type)
        self._providers[provider_type] = provider

        logger.info(
            "Created new provider instance",
            provider_type=provider_type.value,
            cached_providers=[p.value for p in self._providers],
        )

        return provider

    def _create_provider(self, provider_type: LLMProvider) -> Any:
        """Create a new provider instance.

        Args:
            provider_type: Type of provider to create

        Returns:
            New LLM provider instance

        Raises:
            ProviderNotConfiguredError: If required credentials are missing
            ValueError: If provider type is unknown
        """
        if provider_type == LLMProvider.BEDROCK:
            return self._create_bedrock_provider()
        elif provider_type == LLMProvider.OPENAI:
            return self._create_openai_provider()
        elif provider_type == LLMProvider.GOOGLE_VERTEX:
            return self._create_google_vertex_provider()
        elif provider_type == LLMProvider.ANTHROPIC:
            # Anthropic direct API provider not yet implemented
            # Use Bedrock for Claude models instead
            raise ProviderNotConfiguredError(
                provider="anthropic",
                missing_config="Anthropic direct API provider not implemented. "
                "Use Bedrock for Claude models.",
            )
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    def _create_bedrock_provider(self) -> Any:
        """Create AWS Bedrock provider.

        Bedrock uses IAM roles for authentication, so no API key is needed.
        The boto3 client handles credential resolution automatically.

        Returns:
            BedrockLLMProvider instance
        """
        from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
        from shared.services.aws_helpers import get_bedrock_client

        # Use injected client or create new one
        bedrock_client = self._bedrock_client
        if bedrock_client is None:
            bedrock_client = get_bedrock_client(self._settings.bedrock_region)

        return BedrockLLMProvider(
            bedrock_client=bedrock_client,
            region=self._settings.bedrock_region,
        )

    def _create_openai_provider(self) -> Any:
        """Create OpenAI provider.

        Requires OpenAI API key from environment or AWS Secrets Manager.

        Returns:
            OpenAILLMProvider instance

        Raises:
            ProviderNotConfiguredError: If API key not configured
        """
        from coaching.src.infrastructure.llm.openai_provider import OpenAILLMProvider

        api_key = get_openai_api_key()
        if not api_key:
            raise ProviderNotConfiguredError(
                provider="openai",
                missing_config="OPENAI_API_KEY environment variable or AWS secret",
            )

        return OpenAILLMProvider(api_key=api_key)

    def _create_google_vertex_provider(self) -> Any:
        """Create Google Vertex AI provider.

        Requires either GOOGLE_APPLICATION_CREDENTIALS env var or
        credentials stored in AWS Secrets Manager.

        Returns:
            GoogleVertexLLMProvider instance

        Raises:
            ProviderNotConfiguredError: If credentials not configured
        """
        from coaching.src.infrastructure.llm.google_vertex_provider import (
            GoogleVertexLLMProvider,
        )

        credentials = get_google_vertex_credentials()
        project_id = self._settings.google_project_id

        # Check for GOOGLE_APPLICATION_CREDENTIALS env var (local dev)
        import os

        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            # Let Google SDK handle credentials
            return GoogleVertexLLMProvider(
                project_id=project_id,
                location=self._settings.google_vertex_location,
            )

        if credentials:
            return GoogleVertexLLMProvider(
                project_id=project_id,
                location=self._settings.google_vertex_location,
                credentials=credentials,
            )

        # If no credentials but project_id is set, try default credentials
        if project_id:
            return GoogleVertexLLMProvider(
                project_id=project_id,
                location=self._settings.google_vertex_location,
            )

        raise ProviderNotConfiguredError(
            provider="google_vertex",
            missing_config="GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_PROJECT_ID, or AWS secret",
        )

    # NOTE: Anthropic direct API provider not yet implemented.
    # Claude models should be accessed via Bedrock provider.
    # When implementing, uncomment and add:
    # def _create_anthropic_provider(self) -> Any:
    #     from coaching.src.infrastructure.llm.anthropic_provider import (
    #         AnthropicLLMProvider,
    #     )
    #     api_key = self._settings.anthropic_api_key
    #     if not api_key:
    #         raise ProviderNotConfiguredError(
    #             provider="anthropic",
    #             missing_config="ANTHROPIC_API_KEY environment variable",
    #         )
    #     return AnthropicLLMProvider(api_key=api_key)

    def clear_cache(self) -> None:
        """Clear the provider cache.

        Useful for testing or when credentials are updated.
        """
        self._providers.clear()
        logger.info("Provider cache cleared")


# Module-level singleton (initialized lazily)
_factory_instance: LLMProviderFactory | None = None


def get_provider_factory(settings: Settings | None = None) -> LLMProviderFactory:
    """Get or create the global LLMProviderFactory singleton.

    Args:
        settings: Optional settings override (uses default if not provided)

    Returns:
        Global LLMProviderFactory instance
    """
    global _factory_instance
    if _factory_instance is None:
        from coaching.src.core.config_multitenant import get_settings

        _factory_instance = LLMProviderFactory(settings or get_settings())
    return _factory_instance


__all__ = [
    "LLMProviderFactory",
    "get_provider_factory",
]
