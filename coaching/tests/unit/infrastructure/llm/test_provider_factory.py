"""Unit tests for LLM Provider Factory.

Tests for the LLMProviderFactory which enables dynamic multi-provider
model selection based on MODEL_REGISTRY configuration.
"""

from unittest.mock import MagicMock, patch

import pytest
from coaching.src.core.config_multitenant import Settings
from coaching.src.core.llm_models import MODEL_REGISTRY, LLMProvider
from coaching.src.infrastructure.llm.exceptions import (
    ModelNotAvailableError,
    ModelNotFoundError,
    ProviderNotConfiguredError,
)
from coaching.src.infrastructure.llm.provider_factory import (
    LLMProviderFactory,
    get_provider_factory,
)


@pytest.fixture
def mock_settings() -> MagicMock:
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.bedrock_region = "us-east-1"
    settings.openai_api_key = None
    settings.anthropic_api_key = None
    settings.google_project_id = None
    settings.google_vertex_location = "us-central1"
    return settings


@pytest.fixture
def mock_bedrock_client() -> MagicMock:
    """Create mock Bedrock client."""
    return MagicMock()


@pytest.fixture
def factory(mock_settings: MagicMock, mock_bedrock_client: MagicMock) -> LLMProviderFactory:
    """Create factory with mock dependencies."""
    return LLMProviderFactory(
        settings=mock_settings,
        bedrock_client=mock_bedrock_client,
    )


class TestLLMProviderFactoryInit:
    """Test factory initialization."""

    def test_init_creates_empty_provider_cache(
        self, mock_settings: MagicMock, mock_bedrock_client: MagicMock
    ) -> None:
        """Test that factory initializes with empty provider cache."""
        factory = LLMProviderFactory(
            settings=mock_settings,
            bedrock_client=mock_bedrock_client,
        )
        assert factory._providers == {}
        assert factory._settings == mock_settings

    def test_init_accepts_bedrock_client(
        self, mock_settings: MagicMock, mock_bedrock_client: MagicMock
    ) -> None:
        """Test that factory accepts injected bedrock client."""
        factory = LLMProviderFactory(
            settings=mock_settings,
            bedrock_client=mock_bedrock_client,
        )
        assert factory._bedrock_client == mock_bedrock_client


class TestGetProviderForModel:
    """Test get_provider_for_model method."""

    def test_get_provider_for_bedrock_model_returns_provider_and_model_name(
        self, factory: LLMProviderFactory
    ) -> None:
        """Test that Bedrock models return correct provider and model name."""
        # Claude models are Bedrock-based
        provider, model_name = factory.get_provider_for_model("CLAUDE_3_5_SONNET_V2")

        assert provider is not None
        assert model_name == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert provider.provider_name == "bedrock"

    def test_get_provider_for_model_caches_provider(self, factory: LLMProviderFactory) -> None:
        """Test that providers are cached and reused."""
        # First call creates provider
        provider1, _ = factory.get_provider_for_model("CLAUDE_3_5_SONNET_V2")

        # Second call should return same provider
        provider2, _ = factory.get_provider_for_model("CLAUDE_3_SONNET")

        assert provider1 is provider2
        assert len(factory._providers) == 1

    def test_get_provider_for_unknown_model_raises_error(self, factory: LLMProviderFactory) -> None:
        """Test that unknown model codes raise ModelNotFoundError."""
        with pytest.raises(ModelNotFoundError) as exc_info:
            factory.get_provider_for_model("UNKNOWN_MODEL")

        assert exc_info.value.model_code == "UNKNOWN_MODEL"
        assert "CLAUDE_3_5_SONNET" in exc_info.value.available_models

    def test_get_provider_for_inactive_model_raises_error(
        self, factory: LLMProviderFactory
    ) -> None:
        """Test that inactive models raise ModelNotAvailableError."""
        # GPT_5_PRO is marked as inactive in MODEL_REGISTRY
        with pytest.raises(ModelNotAvailableError) as exc_info:
            factory.get_provider_for_model("GPT_5_PRO")

        assert exc_info.value.model_code == "GPT_5_PRO"
        assert "inactive" in exc_info.value.reason.lower()

    @patch("coaching.src.infrastructure.llm.provider_factory.get_openai_api_key")
    def test_get_provider_for_openai_model_with_api_key(
        self,
        mock_get_api_key: MagicMock,
        factory: LLMProviderFactory,
    ) -> None:
        """Test that OpenAI models work when API key is configured."""
        mock_get_api_key.return_value = "sk-test-key"

        provider, model_name = factory.get_provider_for_model("GPT_5_MINI")

        assert provider is not None
        assert model_name == "gpt-5-mini"
        assert provider.provider_name == "openai"

    @patch("coaching.src.infrastructure.llm.provider_factory.get_openai_api_key")
    def test_get_provider_for_openai_model_without_api_key_raises_error(
        self,
        mock_get_api_key: MagicMock,
        factory: LLMProviderFactory,
    ) -> None:
        """Test that OpenAI models raise error without API key."""
        mock_get_api_key.return_value = None

        with pytest.raises(ProviderNotConfiguredError) as exc_info:
            factory.get_provider_for_model("GPT_5_MINI")

        assert exc_info.value.provider == "openai"
        assert "OPENAI_API_KEY" in exc_info.value.missing_config


class TestGetModelInfo:
    """Test get_model_info method."""

    def test_get_model_info_returns_model_config(self, factory: LLMProviderFactory) -> None:
        """Test that model info is returned correctly."""
        model_info = factory.get_model_info("CLAUDE_3_5_SONNET_V2")

        assert model_info.code == "CLAUDE_3_5_SONNET_V2"
        assert model_info.provider == LLMProvider.BEDROCK
        assert model_info.model_name == "anthropic.claude-3-5-sonnet-20241022-v2:0"

    def test_get_model_info_unknown_model_raises_error(self, factory: LLMProviderFactory) -> None:
        """Test that unknown model codes raise ModelNotFoundError."""
        with pytest.raises(ModelNotFoundError):
            factory.get_model_info("UNKNOWN_MODEL")


class TestIsProviderConfigured:
    """Test is_provider_configured method."""

    def test_bedrock_always_configured(self, factory: LLMProviderFactory) -> None:
        """Test that Bedrock is always considered configured (uses IAM)."""
        assert factory.is_provider_configured(LLMProvider.BEDROCK) is True

    @patch("coaching.src.infrastructure.llm.provider_factory.get_openai_api_key")
    def test_openai_configured_with_api_key(
        self,
        mock_get_api_key: MagicMock,
        factory: LLMProviderFactory,
    ) -> None:
        """Test OpenAI is configured when API key is available."""
        mock_get_api_key.return_value = "sk-test-key"
        assert factory.is_provider_configured(LLMProvider.OPENAI) is True

    @patch("coaching.src.infrastructure.llm.provider_factory.get_openai_api_key")
    def test_openai_not_configured_without_api_key(
        self,
        mock_get_api_key: MagicMock,
        factory: LLMProviderFactory,
    ) -> None:
        """Test OpenAI is not configured without API key."""
        mock_get_api_key.return_value = None
        assert factory.is_provider_configured(LLMProvider.OPENAI) is False

    def test_anthropic_not_configured_without_api_key(
        self, factory: LLMProviderFactory, mock_settings: MagicMock
    ) -> None:
        """Test Anthropic is not configured without API key."""
        mock_settings.anthropic_api_key = None
        assert factory.is_provider_configured(LLMProvider.ANTHROPIC) is False


class TestClearCache:
    """Test cache clearing functionality."""

    def test_clear_cache_removes_all_providers(self, factory: LLMProviderFactory) -> None:
        """Test that clear_cache removes all cached providers."""
        # First get a provider to populate cache
        factory.get_provider_for_model("CLAUDE_3_5_SONNET_V2")
        assert len(factory._providers) > 0

        # Clear cache
        factory.clear_cache()

        assert factory._providers == {}


class TestProviderCreation:
    """Test individual provider creation methods."""

    def test_create_bedrock_provider_uses_injected_client(
        self, factory: LLMProviderFactory, mock_bedrock_client: MagicMock
    ) -> None:
        """Test that Bedrock provider uses injected client."""
        provider, _ = factory.get_provider_for_model("CLAUDE_3_5_SONNET_V2")

        # Verify the provider was created with the injected client
        assert provider.bedrock_client == mock_bedrock_client

    @patch("coaching.src.infrastructure.llm.provider_factory.get_openai_api_key")
    def test_create_openai_provider_with_api_key(
        self,
        mock_get_api_key: MagicMock,
        factory: LLMProviderFactory,
    ) -> None:
        """Test OpenAI provider creation with API key."""
        mock_get_api_key.return_value = "sk-test-key"

        provider, _ = factory.get_provider_for_model("GPT_5_MINI")

        assert provider.provider_name == "openai"
        assert provider.api_key == "sk-test-key"

    @patch("coaching.src.infrastructure.llm.provider_factory.get_google_vertex_credentials")
    @patch.dict("os.environ", {"GOOGLE_APPLICATION_CREDENTIALS": ""}, clear=False)
    def test_create_google_vertex_provider_without_credentials_raises_error(
        self,
        mock_get_creds: MagicMock,
        factory: LLMProviderFactory,
        mock_settings: MagicMock,
    ) -> None:
        """Test Google Vertex provider raises error without credentials."""
        mock_get_creds.return_value = None
        mock_settings.google_project_id = None

        with pytest.raises(ProviderNotConfiguredError) as exc_info:
            factory.get_provider_for_model("GEMINI_2_5_PRO")

        assert exc_info.value.provider == "google_vertex"


class TestModelRegistryIntegration:
    """Test integration with MODEL_REGISTRY."""

    def test_all_active_models_have_valid_provider(self, factory: LLMProviderFactory) -> None:
        """Test that all active models in registry can resolve to a provider type."""
        for code, model in MODEL_REGISTRY.items():
            if model.is_active:
                # Should not raise error for provider type validation
                # (may raise ProviderNotConfiguredError for non-Bedrock without credentials)
                try:
                    provider_type = model.provider
                    assert provider_type in LLMProvider
                except Exception:
                    pytest.fail(f"Model {code} has invalid provider type")

    def test_bedrock_models_resolve_correctly(self, factory: LLMProviderFactory) -> None:
        """Test that all Bedrock models resolve to Bedrock provider."""
        bedrock_models = [
            code
            for code, model in MODEL_REGISTRY.items()
            if model.provider == LLMProvider.BEDROCK and model.is_active
        ]

        for model_code in bedrock_models:
            provider, model_name = factory.get_provider_for_model(model_code)
            assert provider.provider_name == "bedrock"
            # Model names can have regional prefixes (us., eu., apac.)
            assert any(
                prefix in model_name
                for prefix in ("anthropic.", "meta.", "amazon.", "us.", "eu.", "apac.")
            )


class TestModuleLevelSingleton:
    """Test module-level get_provider_factory function."""

    def test_get_provider_factory_returns_singleton(self) -> None:
        """Test that get_provider_factory returns singleton instance."""
        # Reset module-level singleton
        import coaching.src.infrastructure.llm.provider_factory as factory_module

        factory_module._factory_instance = None

        factory1 = get_provider_factory()
        factory2 = get_provider_factory()

        assert factory1 is factory2

        # Clean up
        factory_module._factory_instance = None
