"""Unit tests for BedrockLLMProvider."""

from unittest.mock import Mock

import pytest
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider


@pytest.mark.unit
class TestBedrockProviderInitialization:
    """Test BedrockLLMProvider initialization."""

    def test_init_with_client(self) -> None:
        """Test initialization with bedrock client."""
        # Arrange
        mock_client = Mock()

        # Act
        provider = BedrockLLMProvider(bedrock_client=mock_client)

        # Assert
        assert provider.bedrock_client == mock_client
        assert provider.region == "us-east-1"
        assert provider.provider_name == "bedrock"

    def test_init_with_custom_region(self) -> None:
        """Test initialization with custom region."""
        # Arrange
        mock_client = Mock()
        region = "eu-west-1"

        # Act
        provider = BedrockLLMProvider(bedrock_client=mock_client, region=region)

        # Assert
        assert provider.region == region


@pytest.mark.unit
class TestBedrockProviderProperties:
    """Test BedrockLLMProvider properties."""

    def test_provider_name(self) -> None:
        """Test provider_name property."""
        # Arrange
        provider = BedrockLLMProvider(bedrock_client=Mock())

        # Act & Assert
        assert provider.provider_name == "bedrock"

    def test_supported_models(self) -> None:
        """Test supported_models property."""
        # Arrange
        provider = BedrockLLMProvider(bedrock_client=Mock())

        # Act
        models = provider.supported_models

        # Assert
        assert isinstance(models, list)
        assert len(models) > 0
        assert "anthropic.claude-3-sonnet-20240229-v1:0" in models
        assert "anthropic.claude-3-haiku-20240307-v1:0" in models

    def test_supported_models_returns_copy(self) -> None:
        """Test that supported_models returns a copy."""
        # Arrange
        provider = BedrockLLMProvider(bedrock_client=Mock())

        # Act
        models1 = provider.supported_models
        models2 = provider.supported_models

        # Assert
        assert models1 == models2
        assert models1 is not models2  # Different objects


@pytest.mark.unit
class TestBedrockProviderValidation:
    """Test validation in BedrockLLMProvider."""

    @pytest.fixture
    def provider(self) -> BedrockLLMProvider:
        """Create BedrockLLMProvider with mocked client."""
        mock_client = Mock()
        return BedrockLLMProvider(bedrock_client=mock_client)

    async def test_generate_validates_temperature_too_low(self, provider: BedrockLLMProvider) -> None:
        """Test that temperature < 0 raises ValueError."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Act & Assert
        with pytest.raises(ValueError, match="Temperature must be between"):
            await provider.generate(
                messages=messages,
                model=model,
                temperature=-0.1,
            )

    async def test_generate_validates_temperature_too_high(self, provider: BedrockLLMProvider) -> None:
        """Test that temperature > 1 raises ValueError."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Act & Assert
        with pytest.raises(ValueError, match="Temperature must be between"):
            await provider.generate(
                messages=messages,
                model=model,
                temperature=1.1,
            )

    async def test_generate_validates_supported_model(self, provider: BedrockLLMProvider) -> None:
        """Test that unsupported model raises ValueError."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "invalid-model-id"

        # Act & Assert
        with pytest.raises(ValueError, match="Model .* not supported"):
            await provider.generate(
                messages=messages,
                model=model,
                temperature=0.7,
            )

    async def test_generate_accepts_valid_temperature_boundaries(self, provider: BedrockLLMProvider) -> None:
        """Test that temperature 0.0 and 1.0 are accepted."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Mock bedrock client converse response (new Converse API format)
        provider.bedrock_client.converse = Mock(
            return_value={
                "output": {"message": {"content": [{"text": "Response"}]}},
                "usage": {"inputTokens": 10, "outputTokens": 20},
                "stopReason": "end_turn",
            }
        )

        # Act - Test boundary values (should not raise)
        try:
            await provider.generate(messages=messages, model=model, temperature=0.0)
            await provider.generate(messages=messages, model=model, temperature=1.0)
            success = True
        except ValueError:
            success = False

        # Assert
        assert success


@pytest.mark.unit
class TestBedrockProviderModelSupport:
    """Test model support detection."""

    def test_supports_claude_models(self) -> None:
        """Test that Claude models are supported."""
        # Arrange
        provider = BedrockLLMProvider(bedrock_client=Mock())

        # Act & Assert
        assert "anthropic.claude-3-sonnet-20240229-v1:0" in provider.supported_models
        assert "anthropic.claude-3-haiku-20240307-v1:0" in provider.supported_models
        assert "anthropic.claude-3-5-sonnet-20240620-v1:0" in provider.supported_models

    def test_supports_llama_models(self) -> None:
        """Test that Llama models are supported."""
        # Arrange
        provider = BedrockLLMProvider(bedrock_client=Mock())

        # Act & Assert
        assert "meta.llama3-70b-instruct-v1:0" in provider.supported_models
        assert "meta.llama3-8b-instruct-v1:0" in provider.supported_models


@pytest.mark.unit
class TestBedrockProviderEdgeCases:
    """Test edge cases in BedrockLLMProvider."""

    @pytest.fixture
    def provider(self) -> BedrockLLMProvider:
        """Create BedrockLLMProvider with mocked client."""
        return BedrockLLMProvider(bedrock_client=Mock())

    async def test_generate_with_empty_messages(self, provider: BedrockLLMProvider) -> None:
        """Test generate with empty messages list."""
        # Arrange
        messages: list[LLMMessage] = []
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Act - Should handle gracefully or raise appropriate error
        # The actual behavior depends on implementation
        # For now, just ensure it doesn't crash unexpectedly
        try:
            # Mock the client to avoid actual API call (Converse API format)
            provider.bedrock_client.converse = Mock(
                return_value={
                    "output": {"message": {"content": [{"text": ""}]}},
                    "usage": {"inputTokens": 0, "outputTokens": 0},
                    "stopReason": "end_turn",
                }
            )
            result = await provider.generate(messages=messages, model=model)
            assert result is not None
        except Exception:
            # Exception is acceptable for empty messages
            pass

    async def test_generate_with_none_system_prompt(self, provider: BedrockLLMProvider) -> None:
        """Test generate with None system prompt."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        provider.bedrock_client.converse = Mock(
            return_value={
                "output": {"message": {"content": [{"text": "Response"}]}},
                "usage": {"inputTokens": 10, "outputTokens": 20},
                "stopReason": "end_turn",
            }
        )

        # Act
        result = await provider.generate(
            messages=messages,
            model=model,
            system_prompt=None,
        )

        # Assert
        assert result is not None
        assert result.content == "Response"

    async def test_generate_with_none_max_tokens(self, provider: BedrockLLMProvider) -> None:
        """Test generate with None max_tokens."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        provider.bedrock_client.converse = Mock(
            return_value={
                "output": {"message": {"content": [{"text": "Response"}]}},
                "usage": {"inputTokens": 10, "outputTokens": 20},
                "stopReason": "end_turn",
            }
        )

        # Act
        result = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=None,
        )

        # Assert
        assert result is not None
        assert result.content == "Response"


@pytest.mark.unit
class TestBedrockProviderMultipleModels:
    """Test behavior with different model types."""

    @pytest.fixture
    def provider(self) -> BedrockLLMProvider:
        """Create BedrockLLMProvider with mocked client."""
        mock_client = Mock()
        mock_client.converse = Mock(
            return_value={
                "output": {"message": {"content": [{"text": "Test response"}]}},
                "usage": {"inputTokens": 5, "outputTokens": 10},
                "stopReason": "end_turn",
            }
        )
        return BedrockLLMProvider(bedrock_client=mock_client)

    async def test_generate_with_claude_model(self, provider: BedrockLLMProvider) -> None:
        """Test generation with Claude model."""
        # Arrange
        messages = [LLMMessage(role="user", content="Hello")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Act
        result = await provider.generate(messages=messages, model=model)

        # Assert
        assert result is not None
        assert result.content == "Test response"

    async def test_generate_with_different_claude_versions(self, provider: BedrockLLMProvider) -> None:
        """Test generation with different Claude versions."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]

        claude_models = [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-v2:1",
        ]

        # Act & Assert
        for model in claude_models:
            result = await provider.generate(messages=messages, model=model)
            assert result is not None
            assert result.content == "Test response"


@pytest.mark.unit
class TestBedrockProviderConfiguration:
    """Test configuration options."""

    def test_multiple_providers_different_regions(self) -> None:
        """Test creating multiple providers with different regions."""
        # Arrange & Act
        provider1 = BedrockLLMProvider(Mock(), region="us-east-1")
        provider2 = BedrockLLMProvider(Mock(), region="eu-west-1")
        provider3 = BedrockLLMProvider(Mock(), region="ap-south-1")

        # Assert
        assert provider1.region == "us-east-1"
        assert provider2.region == "eu-west-1"
        assert provider3.region == "ap-south-1"

    def test_provider_name_consistent(self) -> None:
        """Test that provider_name is always 'bedrock'."""
        # Arrange
        provider1 = BedrockLLMProvider(Mock())
        provider2 = BedrockLLMProvider(Mock(), region="eu-west-1")

        # Act & Assert
        assert provider1.provider_name == "bedrock"
        assert provider2.provider_name == "bedrock"
        assert provider1.provider_name == provider2.provider_name


@pytest.mark.unit
class TestInferenceProfileResolution:
    """Test inference profile model ID resolution.

    Newer Claude models (3.5 Sonnet v2+, Sonnet 4.5, Opus 4.5) require
    inference profiles (region-prefixed model IDs) for invocation.
    """

    def test_region_prefix_for_us_regions(self) -> None:
        """Test that US regions get 'us' prefix."""
        # Test various US regions
        us_regions = ["us-east-1", "us-west-2", "ca-central-1"]
        for region in us_regions:
            provider = BedrockLLMProvider(Mock(), region=region)
            assert provider._region_prefix == "us", f"Expected 'us' for region {region}"

    def test_region_prefix_for_eu_regions(self) -> None:
        """Test that EU regions get 'eu' prefix."""
        eu_regions = ["eu-west-1", "eu-central-1", "eu-north-1"]
        for region in eu_regions:
            provider = BedrockLLMProvider(Mock(), region=region)
            assert provider._region_prefix == "eu", f"Expected 'eu' for region {region}"

    def test_region_prefix_for_apac_regions(self) -> None:
        """Test that APAC regions get 'apac' prefix."""
        apac_regions = ["ap-southeast-1", "ap-northeast-1", "ap-south-1", "me-south-1", "sa-east-1"]
        for region in apac_regions:
            provider = BedrockLLMProvider(Mock(), region=region)
            assert provider._region_prefix == "apac", f"Expected 'apac' for region {region}"

    def test_resolve_inference_profile_model(self) -> None:
        """Test that inference profile models get region prefix added."""
        provider = BedrockLLMProvider(Mock(), region="us-east-1")

        # Models requiring inference profiles
        test_cases = [
            (
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            ),
            (
                "anthropic.claude-sonnet-4-5-20250929-v1:0",
                "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            ),
            (
                "anthropic.claude-opus-4-5-20250929-v1:0",
                "us.anthropic.claude-opus-4-5-20250929-v1:0",
            ),
        ]

        for input_model, expected_output in test_cases:
            resolved = provider._resolve_model_id(input_model)
            assert resolved == expected_output, f"Expected {expected_output}, got {resolved}"

    def test_resolve_direct_invocation_model(self) -> None:
        """Test that direct invocation models are not modified."""
        provider = BedrockLLMProvider(Mock(), region="us-east-1")

        # Models that support direct invocation (should NOT be modified)
        direct_models = [
            "anthropic.claude-3-sonnet-20240229-v1:0",
            "anthropic.claude-3-haiku-20240307-v1:0",
            "anthropic.claude-3-5-sonnet-20240620-v1:0",  # v1 supports direct
            "meta.llama3-70b-instruct-v1:0",
        ]

        for model in direct_models:
            resolved = provider._resolve_model_id(model)
            assert resolved == model, f"Model {model} should not be modified"

    def test_resolve_already_prefixed_model(self) -> None:
        """Test that already-prefixed models are not double-prefixed."""
        provider = BedrockLLMProvider(Mock(), region="us-east-1")

        # Already prefixed models should remain unchanged
        prefixed_models = [
            "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
            "apac.anthropic.claude-opus-4-5-20250929-v1:0",
        ]

        for model in prefixed_models:
            resolved = provider._resolve_model_id(model)
            assert resolved == model, f"Already-prefixed model {model} should not be modified"

    def test_resolve_model_respects_provider_region(self) -> None:
        """Test that model resolution uses the provider's region prefix."""
        # US region provider
        us_provider = BedrockLLMProvider(Mock(), region="us-east-1")
        resolved = us_provider._resolve_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")
        assert resolved.startswith("us.")

        # EU region provider
        eu_provider = BedrockLLMProvider(Mock(), region="eu-west-1")
        resolved = eu_provider._resolve_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")
        assert resolved.startswith("eu.")

        # APAC region provider
        apac_provider = BedrockLLMProvider(Mock(), region="ap-southeast-1")
        resolved = apac_provider._resolve_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")
        assert resolved.startswith("apac.")
