from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from coaching.src.llm.providers.base import ProviderConfig, ProviderType
from coaching.src.llm.providers.bedrock import BedrockProvider


@pytest.fixture
def provider_config():
    return ProviderConfig(
        provider_type=ProviderType.BEDROCK,
        model_name="anthropic.claude-3-sonnet-20240229-v1:0",
        region_name="us-east-1",
        api_key="test-key",
    )


@pytest.fixture
def mock_boto3():
    with patch("boto3.Session") as mock:
        yield mock


@pytest.fixture
def mock_chat_bedrock():
    with patch("coaching.src.llm.providers.bedrock.ChatBedrock") as mock:
        yield mock


@pytest.mark.asyncio
async def test_initialize(provider_config, mock_boto3, mock_chat_bedrock):
    provider = BedrockProvider(provider_config)
    await provider.initialize()
    assert provider._client is not None
    mock_chat_bedrock.assert_called()


@pytest.mark.asyncio
async def test_invoke(provider_config, mock_boto3, mock_chat_bedrock):
    provider = BedrockProvider(provider_config)
    await provider.initialize()

    mock_llm = mock_chat_bedrock.return_value
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content="Test response"))

    response = await provider.invoke([])

    assert response == "Test response"
    mock_llm.ainvoke.assert_called()


@pytest.mark.asyncio
async def test_stream(provider_config, mock_chat_bedrock):
    provider = BedrockProvider(provider_config)
    await provider.initialize()

    mock_llm = mock_chat_bedrock.return_value

    # Mock astream to return an async iterator
    async def async_generator():
        yield MagicMock(content="Chunk 1")
        yield MagicMock(content="Chunk 2")

    mock_llm.astream.return_value = async_generator()

    chunks = []
    async for chunk in provider.stream([]):
        chunks.append(chunk)

    assert chunks == ["Chunk 1", "Chunk 2"]


@pytest.mark.asyncio
async def test_validate_model_supported(provider_config):
    provider = BedrockProvider(provider_config)

    with patch("boto3.Session") as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_client.list_foundation_models.return_value = {
            "modelSummaries": [{"modelId": "anthropic.claude-3-sonnet-20240229-v1:0"}]
        }

        is_valid = await provider.validate_model("anthropic.claude-3-sonnet-20240229-v1:0")
        assert is_valid is True


@pytest.mark.asyncio
async def test_validate_model_unsupported(provider_config):
    provider = BedrockProvider(provider_config)
    is_valid = await provider.validate_model("unsupported-model")
    assert is_valid is False


@pytest.mark.asyncio
async def test_get_model_info(provider_config):
    provider = BedrockProvider(provider_config)

    with patch("boto3.Session") as mock_session:
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client

        mock_client.get_foundation_model.return_value = {
            "modelDetails": {"modelName": "Claude 3 Sonnet", "providerName": "Anthropic"}
        }

        info = await provider.get_model_info()
        assert info["model_name"] == "Claude 3 Sonnet"
        assert info["provider_name"] == "Anthropic"


@pytest.mark.asyncio
async def test_cleanup(provider_config):
    provider = BedrockProvider(provider_config)
    await provider.initialize()
    assert provider._client is not None

    await provider.cleanup()
    assert provider._client is None


def test_count_tokens(provider_config):
    provider = BedrockProvider(provider_config)
    # Mock tokenizer
    provider.tokenizer = MagicMock()
    provider.tokenizer.encode.return_value = [1, 2, 3]

    count = provider.count_tokens("test text")
    assert count == 3
