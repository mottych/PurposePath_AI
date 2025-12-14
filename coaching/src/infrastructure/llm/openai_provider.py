"""OpenAI LLM provider implementation.

This module provides an OpenAI-backed implementation of the LLM provider
port interface, supporting GPT-4o, GPT-5 series (including GPT-5 Pro), and other OpenAI models.

Uses the Responses API (/v1/responses) which supports all models including
GPT-5 Pro which is exclusive to this API.
"""

from collections.abc import AsyncIterator
from typing import Any, ClassVar

import structlog
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMResponse

logger = structlog.get_logger()


class OpenAILLMProvider:
    """
    OpenAI adapter implementing LLMProviderPort.

    This adapter provides OpenAI-backed LLM access using the Responses API,
    implementing the provider port interface defined in the domain layer.

    Design:
        - Uses Responses API (/v1/responses) for all models
        - Supports all OpenAI models including GPT-5 Pro (exclusive to Responses API)
        - Handles both streaming and non-streaming
        - Includes retry logic and error handling
        - Provides usage metrics
    """

    # Supported OpenAI model IDs
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        # GPT-4o Series
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        # GPT-5 Series
        "gpt-5-pro",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-5-chat",
        # GPT 5.2 Series (Latest - December 2025)
        "gpt-5.2",
        "gpt-5.2-pro",
    ]

    def __init__(self, api_key: str | None = None, organization: str | None = None):
        """
        Initialize OpenAI LLM provider.

        Args:
            api_key: OpenAI API key (optional - will retrieve from Secrets Manager if not provided)
            organization: Optional organization ID
        """
        self.api_key = api_key
        self.organization = organization
        self._client: Any | None = None
        logger.info("OpenAI LLM provider initialized")

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "openai"

    @property
    def supported_models(self) -> list[str]:
        """Get list of supported models."""
        return self.SUPPORTED_MODELS.copy()

    async def _get_client(self) -> Any:
        """Get or create OpenAI async client (lazy initialization)."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError as e:
                raise ImportError(
                    "OpenAI Python SDK not installed. " "Install with: pip install openai>=1.0.0"
                ) from e

            # Get API key from Secrets Manager if not provided
            api_key = self.api_key
            if not api_key:
                from coaching.src.core.config_multitenant import get_openai_api_key

                api_key = get_openai_api_key()
                if not api_key:
                    raise ValueError(
                        "OpenAI API key not configured. "
                        "Set OPENAI_API_KEY environment variable or configure AWS secret"
                    )

            self._client = AsyncOpenAI(
                api_key=api_key,
                organization=self.organization,
            )
            logger.info("OpenAI client initialized")
        return self._client

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
        Generate a completion from OpenAI using the Responses API.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0 for OpenAI)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt (passed as instructions)
            response_schema: Optional JSON schema for structured output enforcement

        Returns:
            LLMResponse with generated content and metadata

        Business Rule: Temperature must be between 0.0 and 2.0 for OpenAI
        """
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(
                f"Temperature must be between 0.0 and 2.0 for OpenAI, got {temperature}"
            )

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}")

        try:
            client = await self._get_client()

            # Build input for Responses API
            # Convert messages to the input format expected by Responses API
            input_items: list[dict[str, Any]] = []
            for msg in messages:
                input_items.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                    }
                )

            # Call OpenAI Responses API
            logger.info(
                "Calling OpenAI Responses API",
                model=model,
                num_messages=len(input_items),
                temperature=temperature,
                has_schema=response_schema is not None,
            )

            # Build API parameters
            params: dict[str, Any] = {
                "model": model,
                "input": input_items,
                "store": False,  # Don't store responses by default
            }

            # Add system prompt as instructions if provided
            if system_prompt:
                params["instructions"] = system_prompt

            # Add max_output_tokens if specified
            if max_tokens:
                params["max_output_tokens"] = max_tokens

            # Add structured output format if schema is provided
            # This ensures the model returns valid JSON matching the schema
            if response_schema:
                params["text"] = {
                    "format": {
                        "type": "json_schema",
                        "name": response_schema.get("title", "Response"),
                        "schema": response_schema,
                        "strict": True,  # Enforce strict schema validation
                    }
                }
                logger.debug(
                    "Using structured JSON output",
                    schema_name=response_schema.get("title", "Response"),
                )

            # GPT-5 Pro only supports high reasoning effort - don't set temperature
            # For other models, set temperature
            if model == "gpt-5-pro":
                # GPT-5 Pro has fixed reasoning settings, don't override
                pass
            elif model == "gpt-5-mini":
                # GPT-5 Mini only supports default temperature (1.0)
                pass
            else:
                params["temperature"] = temperature

            response = await client.responses.create(**params)

            # Extract response content from Responses API format
            content = ""
            if response.output:
                for output_item in response.output:
                    if output_item.type == "message":
                        for content_part in output_item.content:
                            if content_part.type == "output_text":
                                content += content_part.text

            # Determine finish reason from response status
            finish_reason = "stop" if response.status == "completed" else response.status

            # Check for errors
            if response.error:
                logger.warning(
                    "OpenAI response contains error",
                    error_code=response.error.code,
                    error_message=response.error.message,
                    model=model,
                )
                content = f"[Error: {response.error.message}]"

            # Debug log for empty responses
            if not content and response.usage and response.usage.output_tokens > 0:
                logger.warning(
                    "OpenAI returned empty content despite output tokens",
                    model=model,
                    output_tokens=response.usage.output_tokens,
                    status=response.status,
                )

            # Extract usage metrics
            usage = {
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            logger.info(
                "OpenAI Responses API call successful",
                model=model,
                usage=usage,
                finish_reason=finish_reason,
            )

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
                provider=self.provider_name,
            )

        except Exception as e:
            logger.error("OpenAI Responses API call failed", error=str(e), model=model)
            raise RuntimeError(f"OpenAI API call failed: {e}") from e

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Generate a completion with token streaming using Responses API.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0 for OpenAI)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Yields:
            Token strings as they are generated

        Business Rule: Must yield tokens incrementally for real-time UX
        """
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(
                f"Temperature must be between 0.0 and 2.0 for OpenAI, got {temperature}"
            )

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}")

        try:
            client = await self._get_client()

            # Build input for Responses API
            input_items: list[dict[str, Any]] = []
            for msg in messages:
                input_items.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                    }
                )

            # Call OpenAI Responses API with streaming
            logger.info(
                "Calling OpenAI Responses API (streaming)",
                model=model,
                num_messages=len(input_items),
                temperature=temperature,
            )

            # Build API parameters
            params: dict[str, Any] = {
                "model": model,
                "input": input_items,
                "store": False,
                "stream": True,
            }

            # Add system prompt as instructions if provided
            if system_prompt:
                params["instructions"] = system_prompt

            # Add max_output_tokens if specified
            if max_tokens:
                params["max_output_tokens"] = max_tokens

            # Set temperature for models that support it
            if model not in ("gpt-5-pro", "gpt-5-mini"):
                params["temperature"] = temperature

            # Use the streaming interface
            async with client.responses.stream(**params) as stream:
                async for event in stream:
                    # Handle different event types from Responses API streaming
                    if hasattr(event, "type"):
                        if (
                            event.type == "response.output_text.delta"
                            and hasattr(event, "delta")
                            and event.delta
                        ):
                            yield event.delta
                        elif (
                            event.type == "response.content_part.delta"
                            and hasattr(event, "delta")
                            and hasattr(event.delta, "text")
                        ):
                            yield event.delta.text

        except Exception as e:
            logger.error("OpenAI Responses API streaming failed", error=str(e), model=model)
            raise RuntimeError(f"OpenAI streaming API call failed: {e}") from e

    async def count_tokens(self, text: str, _model: str) -> int:
        """
        Count tokens in text for a specific model.

        Args:
            text: Text to tokenize
            _model: Model identifier (unused in approximation mode)

        Returns:
            Number of tokens

        Note: This is an approximation. For exact counts, use tiktoken library.
        """
        # Simple approximation: ~4 characters per token
        # For production, use tiktoken library for exact counts
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


__all__ = ["OpenAILLMProvider"]
