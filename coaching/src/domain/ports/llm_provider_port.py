"""LLM provider port interface.

This module defines the protocol (interface) for LLM providers,
allowing different implementations (Bedrock, Anthropic, OpenAI, etc.)
to be used interchangeably via the Strategy pattern.
"""

from collections.abc import AsyncIterator
from typing import Protocol

from pydantic import BaseModel


class LLMMessage(BaseModel):
    """Message for LLM conversation."""

    role: str  # "user", "assistant", "system"
    content: str


class LLMResponse(BaseModel):
    """Response from LLM provider."""

    content: str
    model: str
    usage: dict[str, int]  # {"prompt_tokens": X, "completion_tokens": Y, "total_tokens": Z}
    finish_reason: str  # "stop", "length", "content_filter", etc.
    provider: str


class LLMProviderPort(Protocol):
    """
    Port interface for LLM providers.

    This protocol defines the contract for LLM provider implementations,
    supporting the Strategy pattern for provider interchangeability.

    Design Principles:
        - Provider-agnostic: Works with any LLM API
        - Async streaming: Supports real-time token streaming
        - Observable: Includes usage metrics and metadata
        - Error-resilient: Clear error handling contract
    """

    @property
    def provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            Provider identifier (e.g., "bedrock", "anthropic", "openai")

        Business Rule: Provider names must be unique and lowercase
        """
        ...

    @property
    def supported_models(self) -> list[str]:
        """
        Get list of supported models for this provider.

        Returns:
            List of model identifiers

        Business Rule: Model IDs should match the provider's naming convention
        """
        ...

    async def generate(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (None = provider default)
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMProviderError: If generation fails
            ModelNotSupportedError: If model is not supported
            RateLimitError: If rate limit is exceeded
            TimeoutError: If request times out

        Business Rule: Temperature must be between 0.0 and 1.0
        """
        ...

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
            max_tokens: Maximum tokens to generate (None = provider default)
            system_prompt: Optional system prompt

        Yields:
            Token strings as they are generated

        Raises:
            LLMProviderError: If generation fails
            ModelNotSupportedError: If model is not supported
            RateLimitError: If rate limit is exceeded
            TimeoutError: If request times out

        Business Rule: Must yield tokens incrementally for real-time UX
        """
        ...
        # Required for async iterator protocol
        yield ""

    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text for a specific model.

        Args:
            text: Text to tokenize
            model: Model identifier (tokenization varies by model)

        Returns:
            Number of tokens

        Business Rule: Token counts must match provider's tokenization
        """
        ...

    async def validate_model(self, model: str) -> bool:
        """
        Validate if a model is supported and available.

        Args:
            model: Model identifier to validate

        Returns:
            True if model is supported and available

        Business Rule: Should check both support and current availability
        """
        ...


__all__ = ["LLMMessage", "LLMProviderPort", "LLMResponse"]
