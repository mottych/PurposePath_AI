"""Unit tests for LLMConfigurationService."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from coaching.src.domain.entities.llm_config.llm_configuration import LLMConfiguration
from coaching.src.services.llm_configuration_service import (
    ConfigurationNotFoundError,
    InvalidConfigurationError,
    LLMConfigurationService,
)


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create mock configuration repository."""
    return MagicMock()


@pytest.fixture
def mock_cache() -> MagicMock:
    """Create mock cache service."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def service(mock_repository: MagicMock, mock_cache: MagicMock) -> LLMConfigurationService:
    """Create LLMConfigurationService with mocks."""
    return LLMConfigurationService(
        configuration_repository=mock_repository,
        cache_service=mock_cache,
    )


@pytest.fixture
def service_no_cache(mock_repository: MagicMock) -> LLMConfigurationService:
    """Create LLMConfigurationService without cache."""
    return LLMConfigurationService(
        configuration_repository=mock_repository,
        cache_service=None,
    )


@pytest.fixture
def sample_config() -> LLMConfiguration:
    """Create sample configuration."""
    return LLMConfiguration(
        config_id="cfg_test123",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="tmpl_test456",
        model_code="CLAUDE_3_5_SONNET",
        tier="premium",
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        is_active=True,
        effective_from=datetime.utcnow() - timedelta(days=1),
        effective_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="admin",
    )


@pytest.fixture
def default_config() -> LLMConfiguration:
    """Create default configuration (tier=None)."""
    return LLMConfiguration(
        config_id="cfg_default",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="tmpl_default",
        model_code="CLAUDE_3_5_SONNET",
        tier=None,
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        is_active=True,
        effective_from=datetime.utcnow() - timedelta(days=1),
        effective_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="admin",
    )


# ===========================
# Test: Service Initialization
# ===========================


@pytest.mark.unit
def test_service_initialization(mock_repository: MagicMock, mock_cache: MagicMock) -> None:
    """Test service initializes correctly."""
    service = LLMConfigurationService(
        configuration_repository=mock_repository,
        cache_service=mock_cache,
    )

    assert service.repository == mock_repository
    assert service.cache == mock_cache


@pytest.mark.unit
def test_service_initialization_without_cache(mock_repository: MagicMock) -> None:
    """Test service initializes without cache."""
    service = LLMConfigurationService(
        configuration_repository=mock_repository,
        cache_service=None,
    )

    assert service.repository == mock_repository
    assert service.cache is None


# ===========================
# Test: Resolve Configuration
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_tier_specific(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test resolving tier-specific configuration."""
    mock_repository.list_all = AsyncMock(return_value=[sample_config])

    result = await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")

    assert result == sample_config
    mock_repository.list_all.assert_called_once_with(interaction_code="ALIGNMENT_ANALYSIS")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_fallback_to_default(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    default_config: LLMConfiguration,
) -> None:
    """Test fallback to default config when tier-specific not found."""
    mock_repository.list_all = AsyncMock(return_value=[default_config])

    result = await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")

    assert result == default_config
    assert result.tier is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_not_found(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
) -> None:
    """Test error when no configuration found."""
    mock_repository.list_all = AsyncMock(return_value=[])

    with pytest.raises(ConfigurationNotFoundError) as exc_info:
        await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")

    assert exc_info.value.interaction_code == "ALIGNMENT_ANALYSIS"
    assert exc_info.value.tier == "premium"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_from_cache(
    service: LLMConfigurationService,
    mock_cache: MagicMock,
    mock_repository: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test configuration resolved from cache."""
    mock_cache.get = AsyncMock(return_value=sample_config.model_dump())

    result = await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")

    assert result.config_id == sample_config.config_id
    # Repository should not be called
    mock_repository.list_all.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_caches_result(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    mock_cache: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test configuration is cached after resolution."""
    mock_repository.list_all = AsyncMock(return_value=[sample_config])

    await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")

    mock_cache.set.assert_called_once()
    call_args = mock_cache.set.call_args
    assert "llm_config:ALIGNMENT_ANALYSIS:premium" in str(call_args)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_invalid_interaction(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
) -> None:
    """Test error when interaction code is invalid."""
    # Create config with invalid interaction
    invalid_config = LLMConfiguration(
        config_id="cfg_invalid",
        interaction_code="INVALID_CODE",
        template_id="tmpl_test",
        model_code="CLAUDE_3_5_SONNET",
        tier=None,
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        is_active=True,
        effective_from=datetime.utcnow(),
        effective_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="admin",
    )
    mock_repository.list_all = AsyncMock(return_value=[invalid_config])

    with pytest.raises(InvalidConfigurationError) as exc_info:
        await service.resolve_configuration("INVALID_CODE", None)

    assert exc_info.value.config_id == "cfg_invalid"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_invalid_model(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
) -> None:
    """Test error when model code is invalid."""
    invalid_config = LLMConfiguration(
        config_id="cfg_invalid_model",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="tmpl_test",
        model_code="INVALID_MODEL",
        tier=None,
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        is_active=True,
        effective_from=datetime.utcnow(),
        effective_until=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by="admin",
    )
    mock_repository.list_all = AsyncMock(return_value=[invalid_config])

    with pytest.raises(InvalidConfigurationError) as exc_info:
        await service.resolve_configuration("ALIGNMENT_ANALYSIS", None)

    assert exc_info.value.config_id == "cfg_invalid_model"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_inactive_filtered(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test inactive configurations are filtered out."""
    sample_config.is_active = False
    mock_repository.list_all = AsyncMock(return_value=[sample_config])

    with pytest.raises(ConfigurationNotFoundError):
        await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_effective_date_future(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test configs with future effective_from are filtered."""
    sample_config.effective_from = datetime.utcnow() + timedelta(days=1)
    mock_repository.list_all = AsyncMock(return_value=[sample_config])

    with pytest.raises(ConfigurationNotFoundError):
        await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_configuration_effective_date_expired(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test configs with past effective_until are filtered."""
    sample_config.effective_until = datetime.utcnow() - timedelta(days=1)
    mock_repository.list_all = AsyncMock(return_value=[sample_config])

    with pytest.raises(ConfigurationNotFoundError):
        await service.resolve_configuration("ALIGNMENT_ANALYSIS", "premium")


# ===========================
# Test: Get Configuration by ID
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_configuration_by_id_found(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    sample_config: LLMConfiguration,
) -> None:
    """Test getting configuration by ID when it exists."""
    mock_repository.get_by_id = AsyncMock(return_value=sample_config)

    result = await service.get_configuration_by_id("cfg_test123")

    assert result == sample_config
    mock_repository.get_by_id.assert_called_once_with("cfg_test123")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_configuration_by_id_not_found(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
) -> None:
    """Test getting configuration by ID when it doesn't exist."""
    mock_repository.get_by_id = AsyncMock(return_value=None)

    result = await service.get_configuration_by_id("nonexistent")

    assert result is None


# ===========================
# Test: List Configurations
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_configurations_for_interaction(
    service: LLMConfigurationService,
    mock_repository: MagicMock,
    sample_config: LLMConfiguration,
    default_config: LLMConfiguration,
) -> None:
    """Test listing all configurations for an interaction."""
    mock_repository.list_all = AsyncMock(return_value=[sample_config, default_config])

    result = await service.list_configurations_for_interaction("ALIGNMENT_ANALYSIS")

    assert len(result) == 2
    assert sample_config in result
    assert default_config in result


# ===========================
# Test: Cache Invalidation
# ===========================


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalidate_cache(
    service: LLMConfigurationService,
    mock_cache: MagicMock,
) -> None:
    """Test cache invalidation."""
    await service.invalidate_cache("ALIGNMENT_ANALYSIS", "premium")

    mock_cache.delete.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_invalidate_cache_no_cache_service(
    service_no_cache: LLMConfigurationService,
) -> None:
    """Test cache invalidation when no cache service."""
    # Should not raise error
    await service_no_cache.invalidate_cache("ALIGNMENT_ANALYSIS", "premium")


# ===========================
# Test: Cache Key Generation
# ===========================


@pytest.mark.unit
def test_cache_key_generation_with_tier(service: LLMConfigurationService) -> None:
    """Test cache key generation with tier."""
    key = service._get_cache_key("ALIGNMENT_ANALYSIS", "premium")
    assert key == "llm_config:ALIGNMENT_ANALYSIS:premium"


@pytest.mark.unit
def test_cache_key_generation_without_tier(service: LLMConfigurationService) -> None:
    """Test cache key generation without tier (default)."""
    key = service._get_cache_key("ALIGNMENT_ANALYSIS", None)
    assert key == "llm_config:ALIGNMENT_ANALYSIS:default"
