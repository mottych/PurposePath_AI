"""Unit tests for LLM Models Registry."""

import pytest
from coaching.src.core.llm_models import (
    MODEL_REGISTRY,
    LLMProvider,
    SupportedModel,
    get_model,
    get_model_provider_class,
    list_models,
)


class TestSupportedModel:
    """Tests for SupportedModel dataclass."""

    def test_model_creation(self) -> None:
        """Test creating a model definition."""
        model = SupportedModel(
            code="TEST_MODEL",
            provider=LLMProvider.BEDROCK,
            model_name="test.model-v1:0",
            version="v1",
            provider_class="TestProvider",
            capabilities=["chat", "analysis"],
            max_tokens=4096,
            cost_per_1k_tokens=0.001,
            is_active=True,
        )

        assert model.code == "TEST_MODEL"
        assert model.provider == LLMProvider.BEDROCK
        assert "chat" in model.capabilities
        assert model.is_active is True


class TestModelRegistry:
    """Tests for model registry functions."""

    def test_get_model_exists(self) -> None:
        """Test retrieving existing model from registry."""
        model = get_model("CLAUDE_3_SONNET")

        assert model.code == "CLAUDE_3_SONNET"
        assert model.provider == LLMProvider.BEDROCK
        assert model.provider_class == "BedrockLLMProvider"
        assert model.max_tokens > 0
        assert model.cost_per_1k_tokens > 0

    def test_get_model_not_found(self) -> None:
        """Test helpful error when model not in registry."""
        with pytest.raises(ValueError) as exc_info:
            get_model("INVALID_MODEL")

        error_msg = str(exc_info.value)
        assert "Unknown model code" in error_msg
        assert "INVALID_MODEL" in error_msg
        assert "Available models" in error_msg

    def test_list_models_all(self) -> None:
        """Test listing all models."""
        models = list_models(active_only=False)

        assert len(models) > 0
        assert all(isinstance(m, SupportedModel) for m in models)
        # Verify some expected models exist
        codes = [m.code for m in models]
        assert "CLAUDE_3_SONNET" in codes

    def test_list_models_active_only(self) -> None:
        """Test filtering to active models only."""
        active_models = list_models(active_only=True)

        assert len(active_models) > 0
        assert all(m.is_active for m in active_models)

    def test_list_models_by_provider(self) -> None:
        """Test filtering models by provider."""
        bedrock_models = list_models(provider=LLMProvider.BEDROCK)

        assert len(bedrock_models) > 0
        assert all(m.provider == LLMProvider.BEDROCK for m in bedrock_models)

    def test_list_models_by_capability(self) -> None:
        """Test filtering models by capability."""
        streaming_models = list_models(capability="streaming")

        assert len(streaming_models) > 0
        assert all("streaming" in m.capabilities for m in streaming_models)

    def test_list_models_combined_filters(self) -> None:
        """Test combining multiple filters."""
        models = list_models(provider=LLMProvider.BEDROCK, active_only=True, capability="chat")

        assert all(m.provider == LLMProvider.BEDROCK for m in models)
        assert all(m.is_active for m in models)
        assert all("chat" in m.capabilities for m in models)

    def test_get_model_provider_class(self) -> None:
        """Test getting provider class for model."""
        provider_class = get_model_provider_class("CLAUDE_3_SONNET")

        assert provider_class == "BedrockLLMProvider"
        assert len(provider_class) > 0

    def test_model_registry_completeness(self) -> None:
        """Test that all models in registry have required fields."""
        for code, model in MODEL_REGISTRY.items():
            # Verify all required fields present
            assert model.code == code
            assert isinstance(model.provider, LLMProvider)
            assert len(model.model_name) > 0
            assert len(model.version) > 0
            assert len(model.provider_class) > 0
            assert isinstance(model.capabilities, list)
            assert len(model.capabilities) > 0
            assert model.max_tokens > 0
            assert model.cost_per_1k_tokens >= 0

    def test_model_registry_no_duplicate_codes(self) -> None:
        """Test that model codes are unique."""
        codes = [m.code for m in MODEL_REGISTRY.values()]
        assert len(codes) == len(set(codes)), "Duplicate model codes found"

    def test_all_models_have_chat_capability(self) -> None:
        """Test that all models support chat (basic requirement)."""
        for model in MODEL_REGISTRY.values():
            assert "chat" in model.capabilities, f"Model {model.code} missing 'chat' capability"


__all__ = []  # Test module, no exports
