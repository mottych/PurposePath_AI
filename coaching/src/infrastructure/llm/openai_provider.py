"""OpenAI LLM provider implementation.

This module provides an OpenAI-backed implementation of the LLM provider
port interface, supporting GPT-4o, GPT-5, and other OpenAI models.
"""

from collections.abc import AsyncIterator
from typing import Any, ClassVar

import structlog
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMResponse

logger = structlog.get_logger()


class OpenAILLMProvider:
    """
    OpenAI adapter implementing LLMProviderPort.

    This adapter provides OpenAI-backed LLM access,
    implementing the provider port interface defined in the domain layer.

    Design:
        - Supports multiple OpenAI models (GPT-4o, GPT-5 series)
        - Handles both streaming and non-streaming
        - Includes retry logic and error handling
        - Provides usage metrics
    """

    # Supported OpenAI model IDs
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-5-pro",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-5-chat",
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
                from src.core.config_multitenant import get_openai_api_key

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
    ) -> LLMResponse:
        """
        Generate a completion from OpenAI.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0 for OpenAI)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

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

            # Build messages for OpenAI API
            api_messages = []

            # Add system prompt if provided
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})

            # Add conversation messages
            for msg in messages:
                api_messages.append({"role": msg.role, "content": msg.content})

            # Call OpenAI API
            logger.info(
                "Calling OpenAI API",
                model=model,
                num_messages=len(api_messages),
                temperature=temperature,
            )

            # Build API parameters based on model requirements
            params = {
                "model": model,
                "messages": api_messages,
            }

            # GPT-5 models have special requirements
            if model.startswith("gpt-5") or model.startswith("o1"):
                # Use max_completion_tokens instead of max_tokens
                params["max_completion_tokens"] = max_tokens

                # GPT-5 Mini only supports temperature=1.0 (default)
                if model == "gpt-5-mini":
                    # Don't set temperature - use default
                    pass
                else:
                    params["temperature"] = temperature
            else:
                # Older models use max_tokens and support custom temperature
                params["max_tokens"] = max_tokens
                params["temperature"] = temperature

            response = await client.chat.completions.create(**params)

            # Extract response
            message = response.choices[0].message
            content = message.content or ""

            # For newer models, check for refusal field
            if hasattr(message, "refusal") and message.refusal:
                logger.warning("OpenAI model refused request", refusal=message.refusal, model=model)
                content = f"[Model refused: {message.refusal}]"

            finish_reason = response.choices[0].finish_reason or "stop"

            # Debug log for empty responses
            if not content and response.usage and response.usage.completion_tokens > 0:
                logger.warning(
                    "OpenAI returned empty content despite completion tokens",
                    model=model,
                    completion_tokens=response.usage.completion_tokens,
                    finish_reason=finish_reason,
                    message_dict=message.model_dump()
                    if hasattr(message, "model_dump")
                    else str(message),
                )

            # Extract usage metrics
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            logger.info(
                "OpenAI API call successful",
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
            logger.error("OpenAI API call failed", error=str(e), model=model)
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
        Generate a completion with token streaming.

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

            # Build messages for OpenAI API
            api_messages = []

            # Add system prompt if provided
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})

            # Add conversation messages
            for msg in messages:
                api_messages.append({"role": msg.role, "content": msg.content})

            # Call OpenAI streaming API
            logger.info(
                "Calling OpenAI streaming API",
                model=model,
                num_messages=len(api_messages),
                temperature=temperature,
            )

            stream = await client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            # Stream tokens
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("OpenAI streaming API call failed", error=str(e), model=model)
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
