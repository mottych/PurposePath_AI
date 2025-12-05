from unittest.mock import AsyncMock

import pytest
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMProviderPort, LLMResponse


@pytest.fixture
def mock_provider():
    provider = AsyncMock(spec=LLMProviderPort)
    provider.provider_name = "mock_provider"
    provider.supported_models = ["model-v1", "model-v2"]
    return provider


@pytest.fixture
def service(mock_provider):
    return LLMApplicationService(mock_provider)


@pytest.fixture
def messages():
    return [LLMMessage(role="user", content="Hello")]


@pytest.mark.asyncio
class TestLLMApplicationService:
    async def test_generate_coaching_response_success(self, service, mock_provider, messages):
        # Arrange
        mock_provider.validate_model.return_value = True
        mock_provider.generate.return_value = LLMResponse(
            content="Response",
            model="model-v1",
            usage={"total_tokens": 10},
            finish_reason="stop",
            provider="mock_provider",
        )

        # Act
        response = await service.generate_coaching_response(
            conversation_history=messages, model="model-v1"
        )

        # Assert
        assert response.content == "Response"
        mock_provider.validate_model.assert_called_with("model-v1")
        mock_provider.generate.assert_called_once()

    async def test_generate_coaching_response_default_model(self, service, mock_provider, messages):
        # Arrange
        mock_provider.validate_model.return_value = True
        mock_provider.generate.return_value = LLMResponse(
            content="Response",
            model="model-v1",
            usage={"total_tokens": 10},
            finish_reason="stop",
            provider="mock_provider",
        )

        # Act
        await service.generate_coaching_response(conversation_history=messages)

        # Assert
        mock_provider.validate_model.assert_called_with("model-v1")

    async def test_generate_coaching_response_invalid_model(self, service, mock_provider, messages):
        # Arrange
        mock_provider.validate_model.return_value = False

        # Act & Assert
        with pytest.raises(ValueError, match="Model invalid-model not supported"):
            await service.generate_coaching_response(
                conversation_history=messages, model="invalid-model"
            )

    async def test_generate_analysis_success(self, service, mock_provider):
        # Arrange
        mock_provider.generate.return_value = LLMResponse(
            content="Analysis",
            model="model-v1",
            usage={"total_tokens": 20},
            finish_reason="stop",
            provider="mock_provider",
        )

        # Act
        response = await service.generate_analysis(
            analysis_prompt="Analyze this", context={"key": "value"}
        )

        # Assert
        assert response.content == "Analysis"
        mock_provider.generate.assert_called_once()
        call_args = mock_provider.generate.call_args
        assert "Analysis Context:\nkey: value" in call_args.kwargs["system_prompt"]

    async def test_generate_streaming_response(self, service, mock_provider, messages):
        # Arrange
        async def stream_generator(*args, **kwargs):
            yield "chunk1"
            yield "chunk2"

        mock_provider.generate_stream.side_effect = stream_generator

        # Act
        chunks = []
        async for chunk in service.generate_streaming_response(messages=messages):
            chunks.append(chunk)

        # Assert
        assert chunks == ["chunk1", "chunk2"]
        mock_provider.generate_stream.assert_called_once()

    async def test_count_message_tokens(self, service, mock_provider, messages):
        # Arrange
        mock_provider.count_tokens.return_value = 5

        # Act
        count = await service.count_message_tokens(messages)

        # Assert
        assert count == 5
        mock_provider.count_tokens.assert_called_with("Hello", "model-v1")

    async def test_validate_model_availability(self, service, mock_provider):
        # Arrange
        mock_provider.validate_model.return_value = True

        # Act
        is_valid = await service.validate_model_availability("model-v1")

        # Assert
        assert is_valid is True
        mock_provider.validate_model.assert_called_with("model-v1")

    def test_get_supported_models(self, service, mock_provider):
        # Act
        models = service.get_supported_models()

        # Assert
        assert models == ["model-v1", "model-v2"]

    def test_get_provider_name(self, service, mock_provider):
        # Act
        name = service.get_provider_name()

        # Assert
        assert name == "mock_provider"

    def test_select_default_model_no_models(self, mock_provider):
        # Arrange
        mock_provider.supported_models = []
        service = LLMApplicationService(mock_provider)

        # Act & Assert
        with pytest.raises(ValueError, match="No models available"):
            service._select_default_model()
