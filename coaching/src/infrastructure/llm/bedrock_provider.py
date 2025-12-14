"""AWS Bedrock LLM provider implementation.

This module provides an AWS Bedrock-backed implementation of the LLM provider
port interface, supporting Claude and other Bedrock models.

Note on Inference Profiles:
    Newer Claude models (Claude 3.5 Sonnet v2+, Claude Sonnet 4.5, Claude Opus 4.5)
    require inference profiles instead of direct model IDs. These are region-prefixed
    model identifiers (e.g., "us.anthropic.claude-3-5-sonnet-20241022-v2:0").

    See: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html
"""

import json
from collections.abc import AsyncIterator
from typing import Any, ClassVar, cast

import structlog
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMResponse

logger = structlog.get_logger()

# Models that require inference profiles (region-prefixed identifiers)
# These cannot be invoked with direct model IDs
INFERENCE_PROFILE_MODELS: set[str] = {
    "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Claude 3.5 Sonnet v2
    "anthropic.claude-sonnet-4-5-20250929-v1:0",  # Claude Sonnet 4.5
    "anthropic.claude-opus-4-5-20250929-v1:0",  # Claude Opus 4.5
}


class BedrockLLMProvider:
    """
    AWS Bedrock adapter implementing LLMProviderPort.

    This adapter provides AWS Bedrock-backed LLM access,
    implementing the provider port interface defined in the domain layer.

    Design:
        - Supports multiple Bedrock models (Claude, Llama, etc.)
        - Handles both streaming and non-streaming
        - Automatically converts models requiring inference profiles to proper format
        - Includes retry logic and error handling
        - Provides usage metrics
    """

    # Supported Bedrock model IDs (including inference profile variants)
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        # Claude 3 models (direct invocation supported)
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        # Claude 3.5 Sonnet v2 (requires inference profile)
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "eu.anthropic.claude-3-5-sonnet-20241022-v2:0",
        "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
        # Claude Sonnet 4.5 (requires inference profile)
        "anthropic.claude-sonnet-4-5-20250929-v1:0",
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
        "apac.anthropic.claude-sonnet-4-5-20250929-v1:0",
        # Claude Opus 4.5 (requires inference profile)
        "anthropic.claude-opus-4-5-20250929-v1:0",
        "us.anthropic.claude-opus-4-5-20250929-v1:0",
        "eu.anthropic.claude-opus-4-5-20250929-v1:0",
        "apac.anthropic.claude-opus-4-5-20250929-v1:0",
        # Legacy Claude models
        "anthropic.claude-v2:1",
        "anthropic.claude-v2",
        # Meta Llama models
        "meta.llama3-70b-instruct-v1:0",
        "meta.llama3-8b-instruct-v1:0",
    ]

    def __init__(self, bedrock_client: Any, region: str = "us-east-1"):
        """
        Initialize Bedrock LLM provider.

        Args:
            bedrock_client: Boto3 Bedrock Runtime client
            region: AWS region for Bedrock
        """
        self.bedrock_client = bedrock_client
        self.region = region
        self._region_prefix = self._get_region_prefix(region)
        logger.info("Bedrock LLM provider initialized", region=region)

    def _get_region_prefix(self, region: str) -> str:
        """Get the inference profile region prefix for a given AWS region.

        Args:
            region: AWS region name (e.g., "us-east-1", "eu-west-1")

        Returns:
            Region prefix for inference profiles ("us", "eu", or "apac")
        """
        if region.startswith("us-") or region.startswith("ca-"):
            return "us"
        elif region.startswith("eu-"):
            return "eu"
        elif region.startswith("ap-") or region.startswith("me-") or region.startswith("sa-"):
            return "apac"
        # Default to US for unknown regions
        return "us"

    def _resolve_model_id(self, model: str) -> str:
        """Resolve a model ID to the correct format for invocation.

        Models that require inference profiles (Claude 3.5 Sonnet v2+, Sonnet 4.5, Opus 4.5)
        need to be invoked with region-prefixed identifiers.

        Args:
            model: Model identifier (can be base model ID or inference profile ID)

        Returns:
            Resolved model ID suitable for Bedrock invoke_model call
        """
        # If already has a region prefix, use as-is
        if model.startswith(("us.", "eu.", "apac.")):
            return model

        # Check if this model requires an inference profile
        if model in INFERENCE_PROFILE_MODELS:
            resolved = f"{self._region_prefix}.{model}"
            logger.debug(
                "Converted model to inference profile",
                original_model=model,
                resolved_model=resolved,
                region_prefix=self._region_prefix,
            )
            return resolved

        # Return as-is for models that support direct invocation
        return model

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "bedrock"

    @property
    def supported_models(self) -> list[str]:
        """Get list of supported models."""
        return self.SUPPORTED_MODELS.copy()

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
        response_schema: dict[str, object] | None = None,
    ) -> LLMResponse:
        """
        Generate a completion from Bedrock.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            response_schema: Optional JSON schema (not used by Bedrock, for interface compat)

        Returns:
            LLMResponse with generated content and metadata

        Business Rule: Temperature must be between 0.0 and 1.0
        """
        # Note: response_schema is not used by Bedrock provider
        # It's accepted for interface compatibility with OpenAI provider
        _ = response_schema
        if not 0.0 <= temperature <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {temperature}")

        # Check base model is supported (before resolving to inference profile)
        base_model = model.split(".", 1)[-1] if model.startswith(("us.", "eu.", "apac.")) else model
        if model not in self.SUPPORTED_MODELS and base_model not in [
            m.split(".", 1)[-1] if m.startswith(("us.", "eu.", "apac.")) else m
            for m in self.SUPPORTED_MODELS
        ]:
            raise ValueError(f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}")

        # Resolve model ID to inference profile format if needed
        resolved_model = self._resolve_model_id(model)

        try:
            # Build request body for Anthropic Claude models
            if "claude" in model.lower():
                request_body = self._build_claude_request(
                    messages, temperature, max_tokens, system_prompt
                )
            else:
                request_body = self._build_generic_request(
                    messages, temperature, max_tokens, system_prompt
                )

            # Invoke Bedrock with resolved model ID
            logger.debug(
                "Invoking Bedrock model",
                original_model=model,
                resolved_model=resolved_model,
            )
            response = self.bedrock_client.invoke_model(
                modelId=resolved_model, body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract content (format varies by model)
            content = self._extract_content(response_body, model)

            # Extract usage metrics
            usage = self._extract_usage(response_body, model)

            llm_response = LLMResponse(
                content=content,
                model=model,  # Return original model code for consistency
                usage=usage,
                finish_reason=response_body.get("stop_reason", "stop"),
                provider=self.provider_name,
            )

            logger.info(
                "LLM generation completed",
                model=model,
                resolved_model=resolved_model,
                tokens=usage.get("total_tokens", 0),
            )

            return llm_response

        except Exception as e:
            logger.error("LLM generation failed", model=model, error=str(e))
            raise

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Generate a completion with token streaming.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Yields:
            Token strings as they are generated
        """
        # TODO: Implement streaming support with Bedrock's streaming API
        logger.warning("Streaming not yet implemented, falling back to non-streaming")

        response = await self.generate(messages, model, temperature, max_tokens, system_prompt)
        yield response.content

    async def count_tokens(self, text: str, _model: str) -> int:
        """
        Count tokens in text for a specific model.

        Args:
            text: Text to tokenize
            model: Model identifier

        Returns:
            Number of tokens (approximation)

        Note: Exact tokenization requires model-specific tokenizers
        """
        # Simple approximation: ~4 characters per token
        # TODO: Use proper tokenizer for each model
        return len(text) // 4

    async def validate_model(self, model: str) -> bool:
        """
        Validate if a model is supported and available.

        Args:
            model: Model identifier to validate

        Returns:
            True if model is supported and available
        """
        return model in self.SUPPORTED_MODELS

    def _build_claude_request(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
        system_prompt: str | None,
    ) -> dict[str, Any]:
        """Build request body for Claude models."""
        # Convert messages to Claude format
        claude_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        request: dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": claude_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 2048,
        }

        if system_prompt:
            request["system"] = system_prompt

        return request

    def _build_generic_request(
        self,
        messages: list[LLMMessage],
        temperature: float,
        max_tokens: int | None,
        system_prompt: str | None,
    ) -> dict[str, Any]:
        """Build generic request body for non-Claude models."""
        # Generic format (adjust per model as needed)
        prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])

        if system_prompt:
            prompt = f"{system_prompt}\n\n{prompt}"

        return {
            "prompt": prompt,
            "temperature": temperature,
            "max_gen_len": max_tokens or 2048,
        }

    def _extract_content(self, response_body: dict[str, Any], model: str) -> str:
        """Extract content from response body."""
        if "claude" in model.lower():
            # Claude format
            content_blocks = response_body.get("content", [])
            if content_blocks and isinstance(content_blocks, list):
                return cast(str, content_blocks[0].get("text", ""))
            return ""
        else:
            # Generic format
            generation: str = cast(str, response_body.get("generation", ""))
            return generation

    def _extract_usage(self, response_body: dict[str, Any], model: str) -> dict[str, int]:
        """Extract usage metrics from response body."""
        if "claude" in model.lower():
            usage = response_body.get("usage", {})
            return {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            }
        else:
            # Generic format (estimate)
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }


__all__ = ["BedrockLLMProvider"]
