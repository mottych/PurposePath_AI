"""LLM application service.

This service orchestrates LLM interactions, abstracting provider details
and providing use-case specific methods for different LLM operations.
"""

from collections.abc import AsyncIterator
from typing import Any

import structlog

from src.domain.ports.llm_provider_port import (
    LLMMessage,
    LLMProviderPort,
    LLMResponse,
)

logger = structlog.get_logger()


class LLMApplicationService:
    """
    Application service for LLM orchestration.

    This service provides high-level LLM operations for different use cases,
    abstracting away provider-specific details.

    Design Principles:
        - Provider-agnostic (uses LLMProviderPort)
        - Use case-driven methods
        - Token tracking and metrics
        - Error handling and retries
        - Streaming support
    """

    def __init__(self, llm_provider: LLMProviderPort):
        """
        Initialize LLM application service.

        Args:
            llm_provider: LLM provider implementation
        """
        self.provider = llm_provider
        logger.info(
            "LLM application service initialized",
            provider=self.provider.provider_name,
        )

    async def generate_coaching_response(
        self,
        conversation_history: list[LLMMessage],
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate coaching response from conversation.

        Use Case: Generate coach response in conversation

        Args:
            conversation_history: List of conversation messages
            system_prompt: Optional system prompt for context
            model: Model to use (None = provider default)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            LLM response with content and metadata

        Business Rule: Temperature should be 0.5-0.8 for coaching (balanced creativity/consistency)
        """
        try:
            # Select model if not specified
            if not model:
                model = self._select_default_model()

            # Validate model
            if not await self.provider.validate_model(model):
                raise ValueError(
                    f"Model {model} not supported by provider {self.provider.provider_name}"
                )

            # Generate
            response = await self.provider.generate(
                messages=conversation_history,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )

            logger.info(
                "Coaching response generated",
                model=model,
                tokens=response.usage.get("total_tokens", 0),
                finish_reason=response.finish_reason,
            )

            return response

        except Exception as e:
            logger.error(
                "Failed to generate coaching response",
                model=model,
                error=str(e),
            )
            raise

    async def generate_analysis(
        self,
        analysis_prompt: str,
        context: dict[str, Any] | None = None,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """
        Generate one-shot analysis.

        Use Case: Generate analysis (alignment, strategy, SWOT, etc.)

        Args:
            analysis_prompt: The analysis prompt
            context: Additional context as key-value pairs
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            LLM response with analysis

        Business Rule: Lower temperature (0.2-0.4) for analysis (more deterministic)
        """
        try:
            # Select model
            if not model:
                model = self._select_default_model()

            # Build messages
            messages = [LLMMessage(role="user", content=analysis_prompt)]

            # Build system prompt with context
            system_prompt = None
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                system_prompt = f"Analysis Context:\n{context_str}"

            # Generate
            response = await self.provider.generate(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
            )

            logger.info(
                "Analysis generated",
                model=model,
                tokens=response.usage.get("total_tokens", 0),
            )

            return response

        except Exception as e:
            logger.error("Failed to generate analysis", model=model, error=str(e))
            raise

    async def generate_streaming_response(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Generate streaming response for real-time UX.

        Use Case: Stream response tokens for immediate user feedback

        Args:
            messages: Conversation messages
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Max tokens
            system_prompt: Optional system prompt

        Yields:
            Token strings as they're generated
        """
        try:
            if not model:
                model = self._select_default_model()

            logger.info("Starting streaming generation", model=model)

            async for token in self.provider.generate_stream(
                _messages=messages,
                _model=model,
                _temperature=temperature,
                _max_tokens=max_tokens,
                _system_prompt=system_prompt,
            ):
                yield token

        except Exception as e:
            logger.error("Streaming generation failed", model=model, error=str(e))
            raise

    async def count_message_tokens(
        self, messages: list[LLMMessage], model: str | None = None
    ) -> int:
        """
        Count tokens in messages.

        Use Case: Track token usage, enforce limits

        Args:
            messages: Messages to count
            model: Model for tokenization

        Returns:
            Total token count
        """
        if not model:
            model = self._select_default_model()

        # Combine all message content
        combined_text = " ".join([msg.content for msg in messages])

        token_count = await self.provider.count_tokens(combined_text, model)

        logger.debug("Tokens counted", model=model, count=token_count)

        return token_count

    async def validate_model_availability(self, model: str) -> bool:
        """
        Check if model is available.

        Use Case: Pre-flight check before generation

        Args:
            model: Model identifier

        Returns:
            True if available
        """
        is_valid = await self.provider.validate_model(model)

        logger.debug("Model validation", model=model, is_valid=is_valid)

        return is_valid

    def get_supported_models(self) -> list[str]:
        """
        Get list of supported models.

        Use Case: Display model options to users/admins

        Returns:
            List of model identifiers
        """
        return self.provider.supported_models

    def get_provider_name(self) -> str:
        """
        Get current provider name.

        Use Case: Diagnostics, logging

        Returns:
            Provider identifier
        """
        return self.provider.provider_name

    def _select_default_model(self) -> str:
        """
        Select default model based on provider.

        Returns:
            Default model identifier
        """
        models = self.provider.supported_models
        if not models:
            raise ValueError(f"No models available from provider {self.provider.provider_name}")

        # Return first model as default
        return models[0]


__all__ = ["LLMApplicationService"]
