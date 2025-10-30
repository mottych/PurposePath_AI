"""Integration tests for LLM Configuration service with repository layer."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.services.llm_configuration_service import (
    ConfigurationNotFoundError,
    InvalidConfigurationError,
    LLMConfigurationService,
)

from shared.models.multitenant import RequestContext, SubscriptionTier, UserRole


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Mock configuration repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_cache() -> MagicMock:
    """Mock cache service."""
    cache = MagicMock()
    cache.get.return_value = None  # No cached value by default
    return cache


@pytest.fixture
def request_context() -> RequestContext:
    """Sample request context."""
    return RequestContext(
        user_id="test_user_123",
        tenant_id="test_tenant_123",
        role=UserRole.MEMBER,
        subscription_tier=SubscriptionTier.PROFESSIONAL,
    )


@pytest.fixture
def service(
    mock_repository: AsyncMock,
    mock_cache: MagicMock,
) -> LLMConfigurationService:
    """Create service with mocked dependencies."""
    return LLMConfigurationService(
        configuration_repository=mock_repository,
        cache_service=mock_cache,
    )


@pytest.fixture
def premium_config() -> LLMConfiguration:
    """Sample premium tier configuration."""
    return LLMConfiguration(
        config_id="config_premium_123",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="template_123",
        model_code="CLAUDE_3_SONNET",
        tier="premium",
        temperature=0.7,
        max_tokens=4096,
        is_active=True,
        created_by="admin_123",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        effective_from=datetime.utcnow() - timedelta(days=1),
    )


@pytest.fixture
def default_config() -> LLMConfiguration:
    """Sample default configuration (tier=None)."""
    return LLMConfiguration(
        config_id="config_default_123",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="template_default_123",
        model_code="CLAUDE_3_HAIKU",
        tier=None,  # Default for all tiers
        temperature=0.5,
        max_tokens=2048,
        is_active=True,
        created_by="admin_123",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        effective_from=datetime.utcnow() - timedelta(days=1),
    )


class TestConfigurationResolutionIntegration:
    """Integration tests for configuration resolution with tier fallback."""

    @pytest.mark.asyncio
    async def test_resolve_with_tier_specific_config(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        request_context: RequestContext,
        premium_config: LLMConfiguration,
    ) -> None:
        """Test resolving configuration with tier-specific config available."""
        # Setup: Repository returns tier-specific config
        mock_repository.get_active_configuration_for_interaction.return_value = premium_config

        # Execute
        config = await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            context=request_context,
        )

        # Verify: Got the tier-specific config
        assert config.config_id == "config_premium_123"
        assert config.tier == "premium"
        assert config.model_code == "CLAUDE_3_SONNET"

        # Verify repository called with correct tier
        mock_repository.get_active_configuration_for_interaction.assert_called_once()
        call_kwargs = mock_repository.get_active_configuration_for_interaction.call_args.kwargs
        assert call_kwargs["interaction_code"] == "ALIGNMENT_ANALYSIS"
        assert call_kwargs["tier"] == "premium"

    @pytest.mark.asyncio
    async def test_resolve_fallback_to_default_config(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        request_context: RequestContext,
        default_config: LLMConfiguration,
    ) -> None:
        """Test tier fallback when tier-specific config not found."""
        # Setup: First call returns None (no tier-specific), second call returns default
        mock_repository.get_active_configuration_for_interaction.side_effect = [
            None,  # No premium config
            default_config,  # Has default config
        ]

        # Execute
        config = await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            context=request_context,
        )

        # Verify: Got the default config
        assert config.config_id == "config_default_123"
        assert config.tier is None
        assert config.model_code == "CLAUDE_3_HAIKU"

        # Verify repository called twice (tier, then default)
        assert mock_repository.get_active_configuration_for_interaction.call_count == 2

    @pytest.mark.asyncio
    async def test_resolve_raises_error_when_no_config_found(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        request_context: RequestContext,
    ) -> None:
        """Test error raised when no configuration exists."""
        # Setup: Repository returns None for both tier and default
        mock_repository.get_active_configuration_for_interaction.return_value = None

        # Execute & Verify
        with pytest.raises(ConfigurationNotFoundError) as exc_info:
            await service.resolve_configuration(
                interaction_code="ALIGNMENT_ANALYSIS",
                context=request_context,
            )

        assert exc_info.value.interaction_code == "ALIGNMENT_ANALYSIS"
        assert exc_info.value.tier == "premium"

    @pytest.mark.asyncio
    async def test_resolve_validates_interaction_registry(
        self,
        service: LLMConfigurationService,
        request_context: RequestContext,
    ) -> None:
        """Test validation against interaction registry."""
        # Execute & Verify: Invalid interaction code
        with pytest.raises(ValueError) as exc_info:
            await service.resolve_configuration(
                interaction_code="INVALID_INTERACTION",
                context=request_context,
            )

        assert "not in registry" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_resolve_validates_model_registry(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        request_context: RequestContext,
    ) -> None:
        """Test validation of model code against model registry."""
        # Setup: Config with invalid model
        invalid_config = LLMConfiguration(
            config_id="config_invalid_123",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="INVALID_MODEL_CODE",  # Not in registry
            tier="premium",
            temperature=0.7,
            max_tokens=4096,
            is_active=True,
            created_by="admin_123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            effective_from=datetime.utcnow(),
        )

        mock_repository.get_active_configuration_for_interaction.return_value = invalid_config

        # Execute & Verify
        with pytest.raises(InvalidConfigurationError) as exc_info:
            await service.resolve_configuration(
                interaction_code="ALIGNMENT_ANALYSIS",
                context=request_context,
            )

        assert exc_info.value.config_id == "config_invalid_123"
        assert "model" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_resolve_caches_configuration(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        mock_cache: MagicMock,
        request_context: RequestContext,
        premium_config: LLMConfiguration,
    ) -> None:
        """Test that resolved configurations are cached."""
        # Setup
        mock_repository.get_active_configuration_for_interaction.return_value = premium_config

        # Execute
        await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            context=request_context,
        )

        # Verify: Cache was set
        assert mock_cache.set.called
        cache_key = mock_cache.set.call_args[0][0]
        assert "ALIGNMENT_ANALYSIS" in cache_key
        assert "premium" in cache_key

    @pytest.mark.asyncio
    async def test_resolve_uses_cached_configuration(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        mock_cache: MagicMock,
        request_context: RequestContext,
        premium_config: LLMConfiguration,
    ) -> None:
        """Test that cached configurations are reused."""
        # Setup: Cache returns config
        mock_cache.get.return_value = premium_config.model_dump()

        # Execute
        config = await service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            context=request_context,
        )

        # Verify: Got cached config, repository not called
        assert config.config_id == "config_premium_123"
        mock_repository.get_active_configuration_for_interaction.assert_not_called()


class TestConfigurationByIdIntegration:
    """Integration tests for getting configuration by ID."""

    @pytest.mark.asyncio
    async def test_get_configuration_by_id_success(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        premium_config: LLMConfiguration,
    ) -> None:
        """Test getting configuration by ID successfully."""
        # Setup
        mock_repository.get.return_value = premium_config

        # Execute
        config = await service.get_configuration_by_id("config_premium_123")

        # Verify
        assert config is not None
        assert config.config_id == "config_premium_123"
        mock_repository.get.assert_called_once_with("config_premium_123")

    @pytest.mark.asyncio
    async def test_get_configuration_by_id_not_found(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
    ) -> None:
        """Test getting nonexistent configuration returns None."""
        # Setup
        mock_repository.get.return_value = None

        # Execute
        config = await service.get_configuration_by_id("nonexistent")

        # Verify
        assert config is None


class TestListConfigurationsIntegration:
    """Integration tests for listing configurations."""

    @pytest.mark.asyncio
    async def test_list_configurations_for_interaction(
        self,
        service: LLMConfigurationService,
        mock_repository: AsyncMock,
        premium_config: LLMConfiguration,
        default_config: LLMConfiguration,
    ) -> None:
        """Test listing configurations for an interaction."""
        # Setup
        mock_repository.list_all.return_value = [premium_config, default_config]

        # Execute
        configs = await service.list_configurations_for_interaction("ALIGNMENT_ANALYSIS")

        # Verify
        assert len(configs) == 2
        mock_repository.list_all.assert_called_once_with(interaction_code="ALIGNMENT_ANALYSIS")


class TestCacheInvalidationIntegration:
    """Integration tests for cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_cache_calls_cache_service(
        self,
        service: LLMConfigurationService,
        mock_cache: MagicMock,
    ) -> None:
        """Test cache invalidation calls cache service."""
        # Execute
        await service.invalidate_cache(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier="professional",
        )

        # Verify: Cache delete was called
        assert mock_cache.delete.called


__all__ = []  # Test module, no exports
