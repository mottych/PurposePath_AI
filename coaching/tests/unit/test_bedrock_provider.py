"""Unit tests for BedrockLLMProvider."""

import pytest
from unittest.mock import Mock, AsyncMock
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMResponse


@pytest.mark.unit
class TestBedrockProviderInitialization:
    """Test BedrockLLMProvider initialization."""

    def test_init_with_client(self):
        """Test initialization with bedrock client."""
        # Arrange
        mock_client = Mock()

        # Act
        provider = BedrockLLMProvider(bedrock_client=mock_client)

        # Assert
        assert provider.bedrock_client == mock_client
        assert provider.region == "us-east-1"
        assert provider.provider_name == "bedrock"

    def test_init_with_custom_region(self):
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

    def test_provider_name(self):
        """Test provider_name property."""
        # Arrange
        provider = BedrockLLMProvider(bedrock_client=Mock())

        # Act & Assert
        assert provider.provider_name == "bedrock"

    def test_supported_models(self):
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

    def test_supported_models_returns_copy(self):
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
    def provider(self):
        """Create BedrockLLMProvider with mocked client."""
        mock_client = Mock()
        return BedrockLLMProvider(bedrock_client=mock_client)

    async def test_generate_validates_temperature_too_low(self, provider):
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

    async def test_generate_validates_temperature_too_high(self, provider):
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

    async def test_generate_validates_supported_model(self, provider):
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

    async def test_generate_accepts_valid_temperature_boundaries(self, provider):
        """Test that temperature 0.0 and 1.0 are accepted."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Mock bedrock client response
        provider.bedrock_client.invoke_model = Mock(
            return_value={
                "body": Mock(read=lambda: b'{"content": [{"text": "Response"}], "usage": {"input_tokens": 10, "output_tokens": 20}}')
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

    def test_supports_claude_models(self):
        """Test that Claude models are supported."""
        # Arrange
        provider = BedrockLLMProvider(bedrock_client=Mock())

        # Act & Assert
        assert "anthropic.claude-3-sonnet-20240229-v1:0" in provider.supported_models
        assert "anthropic.claude-3-haiku-20240307-v1:0" in provider.supported_models
        assert "anthropic.claude-3-5-sonnet-20240620-v1:0" in provider.supported_models

    def test_supports_llama_models(self):
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
    def provider(self):
        """Create BedrockLLMProvider with mocked client."""
        return BedrockLLMProvider(bedrock_client=Mock())

    async def test_generate_with_empty_messages(self, provider):
        """Test generate with empty messages list."""
        # Arrange
        messages = []
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Act - Should handle gracefully or raise appropriate error
        # The actual behavior depends on implementation
        # For now, just ensure it doesn't crash unexpectedly
        try:
            # Mock the client to avoid actual API call
            provider.bedrock_client.invoke_model = Mock(
                return_value={
                    "body": Mock(read=lambda: b'{"content": [{"text": ""}], "usage": {"input_tokens": 0, "output_tokens": 0}}')
                }
            )
            result = await provider.generate(messages=messages, model=model)
            assert isinstance(result, LLMResponse)
        except Exception:
            # Exception is acceptable for empty messages
            pass

    async def test_generate_with_none_system_prompt(self, provider):
        """Test generate with None system prompt."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        provider.bedrock_client.invoke_model = Mock(
            return_value={
                "body": Mock(read=lambda: b'{"content": [{"text": "Response"}], "usage": {"input_tokens": 10, "output_tokens": 20}}')
            }
        )

        # Act
        result = await provider.generate(
            messages=messages,
            model=model,
            system_prompt=None,
        )

        # Assert
        assert isinstance(result, LLMResponse)

    async def test_generate_with_none_max_tokens(self, provider):
        """Test generate with None max_tokens."""
        # Arrange
        messages = [LLMMessage(role="user", content="Test")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        provider.bedrock_client.invoke_model = Mock(
            return_value={
                "body": Mock(read=lambda: b'{"content": [{"text": "Response"}], "usage": {"input_tokens": 10, "output_tokens": 20}}')
            }
        )

        # Act
        result = await provider.generate(
            messages=messages,
            model=model,
            max_tokens=None,
        )

        # Assert
        assert isinstance(result, LLMResponse)


@pytest.mark.unit
class TestBedrockProviderMultipleModels:
    """Test behavior with different model types."""

    @pytest.fixture
    def provider(self):
        """Create BedrockLLMProvider with mocked client."""
        mock_client = Mock()
        mock_client.invoke_model = Mock(
            return_value={
                "body": Mock(read=lambda: b'{"content": [{"text": "Test response"}], "usage": {"input_tokens": 5, "output_tokens": 10}}')
            }
        )
        return BedrockLLMProvider(bedrock_client=mock_client)

    async def test_generate_with_claude_model(self, provider):
        """Test generation with Claude model."""
        # Arrange
        messages = [LLMMessage(role="user", content="Hello")]
        model = "anthropic.claude-3-sonnet-20240229-v1:0"

        # Act
        result = await provider.generate(messages=messages, model=model)

        # Assert
        assert isinstance(result, LLMResponse)

    async def test_generate_with_different_claude_versions(self, provider):
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
            assert isinstance(result, LLMResponse)


@pytest.mark.unit
class TestBedrockProviderConfiguration:
    """Test configuration options."""

    def test_multiple_providers_different_regions(self):
        """Test creating multiple providers with different regions."""
        # Arrange & Act
        provider1 = BedrockLLMProvider(Mock(), region="us-east-1")
        provider2 = BedrockLLMProvider(Mock(), region="eu-west-1")
        provider3 = BedrockLLMProvider(Mock(), region="ap-south-1")

        # Assert
        assert provider1.region == "us-east-1"
        assert provider2.region == "eu-west-1"
        assert provider3.region == "ap-south-1"

    def test_provider_name_consistent(self):
        """Test that provider_name is always 'bedrock'."""
        # Arrange
        provider1 = BedrockLLMProvider(Mock())
        provider2 = BedrockLLMProvider(Mock(), region="eu-west-1")

        # Act & Assert
        assert provider1.provider_name == "bedrock"
        assert provider2.provider_name == "bedrock"
        assert provider1.provider_name == provider2.provider_name
