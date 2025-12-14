"""E2E tests for Bedrock models requiring inference profiles.

These tests verify that the inference profile resolution works correctly
for newer Claude models that require region-prefixed model IDs.
"""

import pytest
from coaching.src.domain.ports.llm_provider_port import LLMMessage
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_claude_35_sonnet_v2_inference_profile(check_aws_credentials: None) -> None:
    """
    Test Claude 3.5 Sonnet v2 which requires inference profiles.

    This model previously failed with:
    ValidationException: Invocation of model ID anthropic.claude-3-5-sonnet-20241022-v2:0
    with on-demand throughput isn't supported.

    The BedrockLLMProvider should automatically convert this to the inference
    profile format: us.anthropic.claude-3-5-sonnet-20241022-v2:0
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client, region="us-east-1")

    messages = [LLMMessage(role="user", content="What is 2+2? Reply with just the number.")]

    # This should work now with inference profile auto-resolution
    response = await provider.generate(
        messages=messages,
        model="anthropic.claude-3-5-sonnet-20241022-v2:0",  # Base model ID
        temperature=0.5,
        max_tokens=50,
    )

    assert response.content
    assert "4" in response.content
    assert response.model == "anthropic.claude-3-5-sonnet-20241022-v2:0"
    assert response.provider == "bedrock"
    assert response.usage["total_tokens"] > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_claude_35_sonnet_v2_with_explicit_prefix(check_aws_credentials: None) -> None:
    """
    Test Claude 3.5 Sonnet v2 with explicit inference profile prefix.

    When the model ID already has a region prefix, it should be used as-is.
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client, region="us-east-1")

    messages = [LLMMessage(role="user", content="What is the capital of France? One word only.")]

    response = await provider.generate(
        messages=messages,
        model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",  # Explicit prefix
        temperature=0.5,
        max_tokens=50,
    )

    assert response.content
    assert "paris" in response.content.lower()
    assert response.provider == "bedrock"
