"""Service for resolving LLM configurations with tier-based fallback logic.

This service handles configuration resolution for LLM interactions, implementing
tier-based fallback and validation of configuration references.
"""

from datetime import datetime, timedelta
from typing import cast

import structlog
from coaching.src.core.llm_interactions import get_interaction
from coaching.src.core.llm_models import get_model
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.infrastructure.repositories.llm_config.llm_configuration_repository import (
    LLMConfigurationRepository,
)
from coaching.src.services.cache_service import CacheService

logger = structlog.get_logger()


class ConfigurationNotFoundError(Exception):
    """Raised when no configuration can be resolved for an interaction."""

    def __init__(self, interaction_code: str, tier: str | None):
        """Initialize error with details."""
        self.interaction_code = interaction_code
        self.tier = tier
        tier_msg = f" for tier '{tier}'" if tier else ""
        super().__init__(f"No configuration found for interaction '{interaction_code}'{tier_msg}")


class InvalidConfigurationError(Exception):
    """Raised when configuration references are invalid."""

    def __init__(self, message: str, config_id: str):
        """Initialize error with details."""
        self.config_id = config_id
        super().__init__(f"Invalid configuration {config_id}: {message}")


class LLMConfigurationService:
    """
    Service for resolving LLM configurations.

    Implements tier-based configuration resolution with fallback logic:
    1. Try to find active config for interaction + specific tier
    2. Fall back to default config (tier=None) if tier-specific not found
    3. Validate all configuration references (interaction, model, template)
    4. Cache resolved configurations for performance

    Design:
        - Application Service Layer (Clean Architecture)
        - Orchestrates repository and validation logic
        - Implements business rules for config resolution
        - Caches resolved configurations (5-minute TTL)
    """

    CACHE_TTL = timedelta(minutes=5)

    def __init__(
        self,
        configuration_repository: LLMConfigurationRepository,
        cache_service: CacheService | None = None,
    ):
        """
        Initialize configuration service.

        Args:
            configuration_repository: Repository for LLM configurations
            cache_service: Optional cache service for performance
        """
        self.repository = configuration_repository
        self.cache = cache_service
        logger.info("LLM configuration service initialized")

    async def resolve_configuration(
        self,
        interaction_code: str,
        tier: str | None = None,
    ) -> LLMConfiguration:
        """
        Resolve configuration for an interaction with tier-based fallback.

        Resolution logic:
        1. Try tier-specific config (if tier provided)
        2. Fall back to default config (tier=None)
        3. Validate all references
        4. Cache result

        Args:
            interaction_code: Code from INTERACTION_REGISTRY
            tier: Optional user tier (e.g., "free", "premium", "enterprise")

        Returns:
            Resolved and validated LLMConfiguration

        Raises:
            ConfigurationNotFoundError: If no config found (even after fallback)
            InvalidConfigurationError: If config references are invalid
        """
        # Check cache first
        cache_key = self._get_cache_key(interaction_code, tier)
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug(
                    "Configuration resolved from cache",
                    interaction_code=interaction_code,
                    tier=tier,
                )
                # Cache returns Any, validate and reconstruct
                if isinstance(cached, dict):
                    return LLMConfiguration(**cached)
                # Fallback for pre-serialized objects
                return cast(LLMConfiguration, cached)

        logger.info(
            "Resolving configuration",
            interaction_code=interaction_code,
            tier=tier,
        )

        # Try tier-specific configuration first
        config = None
        if tier:
            config = await self._find_active_config(interaction_code, tier)
            if config:
                logger.debug(
                    "Found tier-specific configuration",
                    interaction_code=interaction_code,
                    tier=tier,
                    config_id=config.config_id,
                )

        # Fall back to default configuration (tier=None)
        if not config:
            config = await self._find_active_config(interaction_code, None)
            if config:
                logger.debug(
                    "Using default configuration (fallback)",
                    interaction_code=interaction_code,
                    tier=tier,
                    config_id=config.config_id,
                )

        # No configuration found
        if not config:
            logger.warning(
                "No configuration found",
                interaction_code=interaction_code,
                tier=tier,
            )
            raise ConfigurationNotFoundError(interaction_code, tier)

        # Validate configuration references
        self._validate_configuration(config)

        # Cache the resolved configuration
        if self.cache:
            await self.cache.set(
                cache_key,
                config.model_dump(),
                ttl=self.CACHE_TTL,
            )

        logger.info(
            "Configuration resolved successfully",
            interaction_code=interaction_code,
            tier=tier,
            config_id=config.config_id,
            model_code=config.model_code,
        )

        return config

    async def get_configuration_by_id(self, config_id: str) -> LLMConfiguration | None:
        """
        Get configuration by ID.

        Args:
            config_id: Configuration identifier

        Returns:
            Configuration if found, None otherwise
        """
        logger.debug("Getting configuration by ID", config_id=config_id)
        config = await self.repository.get_by_id(config_id)

        if config:
            logger.debug("Configuration found", config_id=config_id)
        else:
            logger.debug("Configuration not found", config_id=config_id)

        return config

    async def list_configurations_for_interaction(
        self, interaction_code: str
    ) -> list[LLMConfiguration]:
        """
        List all configurations for an interaction.

        Args:
            interaction_code: Interaction code

        Returns:
            List of configurations
        """
        logger.debug(
            "Listing configurations for interaction",
            interaction_code=interaction_code,
        )
        configs = await self.repository.list_all(interaction_code=interaction_code)
        return configs

    async def invalidate_cache(self, interaction_code: str, tier: str | None = None) -> None:
        """
        Invalidate cached configuration.

        Args:
            interaction_code: Interaction code
            tier: Optional tier
        """
        if not self.cache:
            return

        cache_key = self._get_cache_key(interaction_code, tier)
        await self.cache.delete(cache_key)

        logger.debug(
            "Configuration cache invalidated",
            interaction_code=interaction_code,
            tier=tier,
        )

    async def _find_active_config(
        self, interaction_code: str, tier: str | None
    ) -> LLMConfiguration | None:
        """
        Find active configuration for interaction + tier.

        Args:
            interaction_code: Interaction code
            tier: Tier (can be None for default)

        Returns:
            Active configuration if found, None otherwise
        """
        now = datetime.utcnow()

        # Get all configs for this interaction
        all_configs = await self.repository.list_all(interaction_code=interaction_code)

        # Filter for matching tier and active status
        matching_configs = [
            config
            for config in all_configs
            if config.tier == tier
            and config.is_active
            and config.effective_from <= now
            and (config.effective_until is None or config.effective_until >= now)
        ]

        if not matching_configs:
            return None

        # Return most recently updated if multiple found
        if len(matching_configs) > 1:
            logger.warning(
                "Multiple active configs found, using most recent",
                interaction_code=interaction_code,
                tier=tier,
                count=len(matching_configs),
            )
            matching_configs.sort(key=lambda c: c.updated_at, reverse=True)

        return matching_configs[0]

    def _validate_configuration(self, config: LLMConfiguration) -> None:
        """
        Validate configuration references exist in registries.

        Args:
            config: Configuration to validate

        Raises:
            InvalidConfigurationError: If validation fails
        """
        try:
            # Validate interaction exists
            get_interaction(config.interaction_code)
        except ValueError as e:
            raise InvalidConfigurationError(
                f"Invalid interaction_code: {e}",
                config.config_id,
            ) from e

        try:
            # Validate model exists
            get_model(config.model_code)
        except ValueError as e:
            raise InvalidConfigurationError(
                f"Invalid model_code: {e}",
                config.config_id,
            ) from e

        # Note: template_id validation requires TemplateMetadataRepository
        # which would create circular dependency if done here
        # Template validation should be done at configuration creation time

        logger.debug("Configuration validation passed", config_id=config.config_id)

    def _get_cache_key(self, interaction_code: str, tier: str | None) -> str:
        """
        Generate cache key for configuration.

        Args:
            interaction_code: Interaction code
            tier: Tier (can be None)

        Returns:
            Cache key string
        """
        tier_part = tier if tier else "default"
        return f"llm_config:{interaction_code}:{tier_part}"


__all__ = [
    "ConfigurationNotFoundError",
    "InvalidConfigurationError",
    "LLMConfigurationService",
]
