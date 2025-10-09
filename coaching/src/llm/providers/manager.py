"""
Provider manager for LangChain integration.

Handles lifecycle management, factory creation, and coordination of AI providers.
"""

import asyncio
from typing import Any, Dict, List, Optional

import structlog

from .base import BaseProvider, ProviderConfig, ProviderType

logger = structlog.get_logger(__name__)


class ProviderManager:
    """Manages multiple AI providers and their lifecycles."""

    def __init__(self) -> None:
        """Initialize the provider manager."""
        self._providers: Dict[str, BaseProvider] = {}
        self._default_provider: Optional[str] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider manager."""
        if self._initialized:
            return

        logger.info("Initializing provider manager")

        # Initialize all registered providers
        init_tasks = []
        for provider_id, provider in self._providers.items():
            logger.info(
                "Initializing provider",
                provider_id=provider_id,
                provider_type=provider.provider_type,
            )
            init_tasks.append(provider.initialize())

        if init_tasks:
            await asyncio.gather(*init_tasks, return_exceptions=True)

        self._initialized = True
        logger.info("Provider manager initialized", provider_count=len(self._providers))

    async def add_provider(
        self, provider_id: str, provider_type: str, config_dict: Dict[str, Any]
    ) -> None:
        """Add a new provider with convenience method (backward compatible).

        Args:
            provider_id: Unique identifier for the provider
            provider_type: Type of provider ('bedrock', 'anthropic', 'openai')
            config_dict: Provider configuration dictionary
        """
        # Convert string provider_type to enum
        try:
            provider_type_enum = ProviderType(provider_type)
        except ValueError:
            raise ValueError(f"Invalid provider type: {provider_type}")

        # Build ProviderConfig from dict
        config_data = {
            "provider_type": provider_type_enum,
            **config_dict,
        }

        # Map common fields
        if "client" in config_data:
            # For Bedrock, client is passed separately but not in config
            config_data.pop("client")

        if "region" in config_data and "region_name" not in config_data:
            config_data["region_name"] = config_data.pop("region")

        # Create ProviderConfig object
        config = ProviderConfig(**config_data)

        # Call register_provider
        await self.register_provider(provider_id, config)

    async def register_provider(self, provider_id: str, config: ProviderConfig) -> None:
        """Register a new provider with the manager.

        Args:
            provider_id: Unique identifier for the provider
            config: Provider configuration
        """
        if provider_id in self._providers:
            logger.warning("Provider already registered, replacing", provider_id=provider_id)

        try:
            # Create provider instance
            provider = await self._create_provider(config)

            # Store provider
            self._providers[provider_id] = provider

            # Set as default if it's the first one
            if self._default_provider is None:
                self._default_provider = provider_id

            # Initialize if manager is already initialized
            if self._initialized:
                await provider.initialize()

            logger.info(
                "Provider registered", provider_id=provider_id, provider_type=config.provider_type
            )

        except Exception as e:
            logger.error("Failed to register provider", provider_id=provider_id, error=str(e))
            raise

    async def _create_provider(self, config: ProviderConfig) -> BaseProvider:
        """Create a provider instance based on configuration.

        Args:
            config: Provider configuration

        Returns:
            Provider instance
        """
        from .anthropic import AnthropicProvider
        from .bedrock import BedrockProvider
        from .openai import OpenAIProvider

        if config.provider_type == ProviderType.BEDROCK:
            return BedrockProvider(config)
        elif config.provider_type == ProviderType.ANTHROPIC:
            return AnthropicProvider(config)
        elif config.provider_type == ProviderType.OPENAI:
            return OpenAIProvider(config)
        else:
            raise ValueError(f"Unsupported provider type: {config.provider_type}")

    def get_provider(self, provider_id: Optional[str] = None) -> BaseProvider:
        """Get a provider by ID.

        Args:
            provider_id: Provider identifier. If None, returns default provider.

        Returns:
            Provider instance

        Raises:
            KeyError: If provider not found
            ValueError: If no providers registered
        """
        if not self._providers:
            raise ValueError("No providers registered")

        if provider_id is None:
            provider_id = self._default_provider

        if provider_id not in self._providers:
            raise KeyError(f"Provider not found: {provider_id}")

        return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Get list of registered provider IDs.

        Returns:
            List of provider IDs
        """
        return list(self._providers.keys())

    def get_provider_info(self, provider_id: Optional[str] = None) -> Dict[str, str]:
        """Get information about a provider.

        Args:
            provider_id: Provider identifier. If None, returns default provider info.

        Returns:
            Provider information
        """
        provider = self.get_provider(provider_id)
        return {
            "provider_id": provider_id or self._default_provider or "unknown",
            "provider_type": provider.provider_type.value,
            "model_name": provider.config.model_name,
            "temperature": str(provider.config.temperature),
            "max_tokens": str(provider.config.max_tokens) if provider.config.max_tokens else "none",
        }

    async def set_default_provider(self, provider_id: str) -> None:
        """Set the default provider.

        Args:
            provider_id: Provider identifier

        Raises:
            KeyError: If provider not found
        """
        if provider_id not in self._providers:
            raise KeyError(f"Provider not found: {provider_id}")

        self._default_provider = provider_id
        logger.info("Default provider updated", provider_id=provider_id)

    async def remove_provider(self, provider_id: str) -> None:
        """Remove a provider from the manager.

        Args:
            provider_id: Provider identifier

        Raises:
            KeyError: If provider not found
        """
        if provider_id not in self._providers:
            raise KeyError(f"Provider not found: {provider_id}")

        provider = self._providers[provider_id]

        # Cleanup provider resources
        try:
            await provider.cleanup()
        except Exception as e:
            logger.warning("Error during provider cleanup", provider_id=provider_id, error=str(e))

        # Remove from registry
        del self._providers[provider_id]

        # Update default if necessary
        if self._default_provider == provider_id:
            self._default_provider = list(self._providers.keys())[0] if self._providers else None

        logger.info("Provider removed", provider_id=provider_id)

    async def cleanup(self) -> None:
        """Clean up all providers."""
        logger.info("Cleaning up provider manager")

        cleanup_tasks = []
        for provider_id, provider in self._providers.items():
            logger.info("Cleaning up provider", provider_id=provider_id)
            cleanup_tasks.append(provider.cleanup())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        self._providers.clear()
        self._default_provider = None
        self._initialized = False

        logger.info("Provider manager cleanup complete")

    def __repr__(self) -> str:
        """String representation of provider manager."""
        return (
            f"ProviderManager(providers={len(self._providers)}, default={self._default_provider})"
        )


# Global provider manager instance
provider_manager = ProviderManager()
