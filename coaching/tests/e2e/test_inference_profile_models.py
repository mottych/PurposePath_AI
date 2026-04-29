"""E2E tests for Bedrock models requiring inference profiles.

These tests verify that the inference profile resolution works correctly
for newer Claude models that require region-prefixed model IDs.
"""

import pytest

from coaching.src.domain.ports.llm_provider_port import LLMMessage
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider

CLAUDE_SONNET_45_BASE = "anthropic.claude-sonnet-4-5-20250929-v1:0"
CLAUDE_SONNET_45_US_PROFILE = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_claude_sonnet_45_inference_profile(check_aws_credentials: None) -> None:
    """
    Test Claude Sonnet 4.5 which requires inference profiles.

    The BedrockLLMProvider should automatically convert the base model ID to the
    regional inference profile format.
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client, region="us-east-1")

    messages = [LLMMessage(role="user", content="What is 2+2? Reply with just the number.")]

    # This should work now with inference profile auto-resolution
    response = await provider.generate(
        messages=messages,
        model=CLAUDE_SONNET_45_BASE,
        temperature=0.5,
        max_tokens=50,
    )

    assert response.content
    assert "4" in response.content
    assert response.model == CLAUDE_SONNET_45_BASE
    assert response.provider == "bedrock"
    assert response.usage["total_tokens"] > 0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_claude_sonnet_45_with_explicit_prefix(check_aws_credentials: None) -> None:
    """
    Test Claude Sonnet 4.5 with explicit inference profile prefix.

    When the model ID already has a region prefix, it should be used as-is.
    """
    import boto3

    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    provider = BedrockLLMProvider(bedrock_client=bedrock_client, region="us-east-1")

    messages = [LLMMessage(role="user", content="What is the capital of France? One word only.")]

    response = await provider.generate(
        messages=messages,
        model=CLAUDE_SONNET_45_US_PROFILE,
        temperature=0.5,
        max_tokens=50,
    )

    assert response.content
    assert "paris" in response.content.lower()
    assert response.provider == "bedrock"
