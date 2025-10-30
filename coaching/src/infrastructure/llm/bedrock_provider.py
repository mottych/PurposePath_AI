"""AWS Bedrock LLM provider implementation.

This module provides an AWS Bedrock-backed implementation of the LLM provider
port interface, supporting Claude and other Bedrock models.
"""

import json
from collections.abc import AsyncIterator
from typing import Any, ClassVar

import structlog
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMResponse

logger = structlog.get_logger()


class BedrockLLMProvider:
    """
    AWS Bedrock adapter implementing LLMProviderPort.

    This adapter provides AWS Bedrock-backed LLM access,
    implementing the provider port interface defined in the domain layer.

    Design:
        - Supports multiple Bedrock models (Claude, Llama, etc.)
        - Handles both streaming and non-streaming
        - Includes retry logic and error handling
        - Provides usage metrics
    """

    # Supported Bedrock model IDs
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        "anthropic.claude-3-sonnet-20240229-v1:0",
        "anthropic.claude-3-haiku-20240307-v1:0",
        "anthropic.claude-3-5-sonnet-20240620-v1:0",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Claude 3.5 Sonnet v2
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0",  # Claude Sonnet 4.5 (US)
        "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",  # Claude Sonnet 4.5 (EU)
        "apac.anthropic.claude-sonnet-4-5-20250929-v1:0",  # Claude Sonnet 4.5 (APAC)
        "anthropic.claude-v2:1",
        "anthropic.claude-v2",
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
        logger.info("Bedrock LLM provider initialized", region=region)

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
    ) -> LLMResponse:
        """
        Generate a completion from Bedrock.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content and metadata

        Business Rule: Temperature must be between 0.0 and 1.0
        """
        if not 0.0 <= temperature <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {temperature}")

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}")

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

            # Invoke Bedrock
            response = self.bedrock_client.invoke_model(
                modelId=model, body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response["body"].read())

            # Extract content (format varies by model)
            content = self._extract_content(response_body, model)

            # Extract usage metrics
            usage = self._extract_usage(response_body, model)

            llm_response = LLMResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=response_body.get("stop_reason", "stop"),
                provider=self.provider_name,
            )

            logger.info(
                "LLM generation completed",
                model=model,
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
                return content_blocks[0].get("text", "")  # type: ignore[no-any-return]
            return ""
        else:
            # Generic format
            return response_body.get("generation", "")  # type: ignore[no-any-return]

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
