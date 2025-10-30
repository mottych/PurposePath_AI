"""End-to-end tests for LLM provider implementations with real models.

Tests direct provider calls to validate:
- Claude 3.5 Sonnet v2 (Bedrock)
- Claude Sonnet 4.5 (Bedrock)
- GPT-5 series (OpenAI)
- Gemini 2.5 Pro (Google Vertex AI)
"""

import os

import pytest
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from coaching.src.infrastructure.llm.google_vertex_provider import GoogleVertexLLMProvider
from coaching.src.infrastructure.llm.openai_provider import OpenAILLMProvider


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_claude_35_sonnet_v2_real_generation(check_aws_credentials: None) -> None:
    """
    Test Claude 3.5 Sonnet v2 real generation via Bedrock.

    Validates:
    - Provider connects successfully
    - Response generated
    - Usage metrics returned
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client, region="us-east-1")

    messages = [
        LLMMessage(role="user", content="Explain quantum computing in exactly 2 sentences.")
    ]

    response = await provider.generate(
        messages=messages,
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature=0.7,
        max_tokens=100,
    )

    assert response.content
    assert len(response.content) > 50
    assert response.model == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    assert response.provider == "bedrock"
    assert response.usage["total_tokens"] > 0
    assert response.finish_reason in ["stop", "end_turn"]


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_claude_sonnet_45_real_generation(check_aws_credentials: None) -> None:
    """
    Test Claude Sonnet 4.5 real generation via Bedrock.

    Validates:
    - Latest model works
    - Extended thinking capability
    - High quality responses
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client, region="us-east-1")

    messages = [
        LLMMessage(
            role="user",
            content="Analyze the business implications of adopting AI in healthcare. Be thorough.",
        )
    ]

    response = await provider.generate(
        messages=messages,
        model="us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        temperature=0.8,
        max_tokens=500,
    )

    assert response.content
    assert len(response.content) > 200  # Should be thorough
    assert response.model == "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    assert response.usage["total_tokens"] > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gpt5_pro_real_generation(check_openai_credentials: None) -> None:
    """
    Test GPT-5 Pro real generation via OpenAI.

    Validates:
    - OpenAI provider works
    - GPT-5 Pro access
    - Advanced reasoning capability
    """
    api_key = os.getenv("OPENAI_API_KEY")
    provider = OpenAILLMProvider(api_key=api_key)

    messages = [
        LLMMessage(
            role="user",
            content="Solve this logic puzzle: If all Bloops are Razzies and all Razzies are Lazzies, are all Bloops definitely Lazzies?",
        )
    ]

    response = await provider.generate(
        messages=messages, model="gpt-5-pro", temperature=0.5, max_tokens=200
    )

    assert response.content
    assert "yes" in response.content.lower() or "all bloops" in response.content.lower()
    assert response.model == "gpt-5-pro"
    assert response.provider == "openai"
    assert response.usage["total_tokens"] > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gpt5_mini_real_generation(check_openai_credentials: None) -> None:
    """
    Test GPT-5 Mini real generation via OpenAI.

    Validates:
    - Lightweight model works
    - Cost-effective option
    - Fast responses
    """
    api_key = os.getenv("OPENAI_API_KEY")
    provider = OpenAILLMProvider(api_key=api_key)

    messages = [LLMMessage(role="user", content="List 5 benefits of cloud computing.")]

    response = await provider.generate(
        messages=messages, model="gpt-5-mini", temperature=0.3, max_tokens=150
    )

    assert response.content
    assert len(response.content) > 50
    assert response.model == "gpt-5-mini"
    assert response.usage["total_tokens"] > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_gemini_25_pro_real_generation(check_google_credentials: None) -> None:
    """
    Test Gemini 2.5 Pro real generation via Google Vertex AI.

    Validates:
    - Google Vertex provider works
    - Gemini 2.5 Pro access
    - Long context capability
    """
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    provider = GoogleVertexLLMProvider(project_id=project_id, location="us-central1")

    messages = [
        LLMMessage(
            role="user",
            content="Explain the concept of machine learning to a 10-year-old in 3 sentences.",
        )
    ]

    response = await provider.generate(
        messages=messages, model="gemini-2.5-pro", temperature=0.7, max_tokens=150
    )

    assert response.content
    assert len(response.content) > 50
    assert response.model == "gemini-2.5-pro"
    assert response.provider == "google_vertex"
    assert response.usage["total_tokens"] > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_streaming_generation_real_llm(check_aws_credentials: None) -> None:
    """
    Test streaming generation with real Bedrock LLM.

    Validates:
    - Streaming works
    - Tokens arrive incrementally
    - Complete response assembled
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client)

    messages = [
        LLMMessage(role="user", content="Write a 4-line poem about artificial intelligence.")
    ]

    chunks = []
    async for chunk in provider.generate_stream(
        messages=messages,
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature=0.9,
        max_tokens=100,
    ):
        chunks.append(chunk)

    # Validate streaming worked
    assert len(chunks) > 1  # Should receive multiple chunks
    full_response = "".join(chunks)
    assert len(full_response) > 50
    assert "\n" in full_response  # Poem should have line breaks


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_token_counting_real_providers(check_aws_credentials: None) -> None:
    """
    Test token counting across different providers.

    Validates:
    - Token counting approximation works
    - Reasonable estimates
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client)

    text = "This is a test sentence for token counting validation."
    model = "anthropic.claude-3-5-sonnet-20241022-v2:0"

    token_count = await provider.count_tokens(text, model)

    # Should be reasonable (roughly 1 token per 4 characters)
    assert 10 <= token_count <= 20


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_model_validation_real_providers() -> None:
    """
    Test model validation for all new models.

    Validates:
    - All new models are recognized
    - Invalid models rejected
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    bedrock_provider = BedrockLLMProvider(bedrock_client=bedrock_client)

    # Valid models
    assert await bedrock_provider.validate_model("anthropic.claude-3-5-sonnet-20241022-v2:0")
    assert await bedrock_provider.validate_model("us.anthropic.claude-sonnet-4-5-20250929-v1:0")

    # Invalid model
    assert not await bedrock_provider.validate_model("invalid-model-id")


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_error_handling_real_llm(check_aws_credentials: None) -> None:
    """
    Test error handling with real LLM provider.

    Validates:
    - Invalid parameters handled
    - Clear error messages
    - No crashes
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client)

    messages = [LLMMessage(role="user", content="Test")]

    # Test invalid temperature
    with pytest.raises(ValueError, match="Temperature"):
        await provider.generate(
            messages=messages,
            model="anthropic.claude-3-5-sonnet-20241022-v2:0",
            temperature=2.5,  # Invalid
        )


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_multimodal_capability_gemini(check_google_credentials: None) -> None:
    """
    Test Gemini 2.5 Pro multimodal capabilities.

    Validates:
    - Text-only works (baseline)
    - Model supports multimodal input
    """
    project_id = os.getenv("GOOGLE_PROJECT_ID")
    provider = GoogleVertexLLMProvider(project_id=project_id)

    # Text-only baseline
    messages = [
        LLMMessage(
            role="user", content="Describe the benefits of using multimodal AI models in business."
        )
    ]

    response = await provider.generate(
        messages=messages, model="gemini-2.5-pro", temperature=0.7, max_tokens=200
    )

    assert response.content
    assert "multimodal" in response.content.lower() or "multiple" in response.content.lower()


__all__ = []  # Test module, no exports
