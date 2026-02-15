"""AWS Bedrock LLM provider implementation using Converse API.

This module provides an AWS Bedrock-backed implementation of the LLM provider
port interface, supporting Claude and other Bedrock models.

Uses the Converse API for:
- Unified interface across all Bedrock models
- Better streaming support
- Native tool/function calling
- Prompt caching support (cache_control blocks)

Prompt Caching:
    For Claude models, system prompts are cached using cache_control blocks.
    This reduces processing time for repeated system prompts (e.g., coaching prompts)
    by up to 80% on subsequent requests within the cache TTL.

    Cache requirements:
    - Claude 3.5 Sonnet+ or Claude 3.5 Haiku+
    - Minimum 1024 tokens (2048 for Claude 3.5 Haiku)
    - Cache TTL: 5 minutes (extended on cache hit)

    See: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-caching.html

Note on Inference Profiles:
    Newer Claude models (Claude 3.5 Sonnet v2+, Claude Sonnet 4.5, Claude Opus 4.5)
    require inference profiles instead of direct model IDs. These are region-prefixed
    model identifiers (e.g., "us.anthropic.claude-3-5-sonnet-20241022-v2:0").

    See: https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles.html
"""

import asyncio
from collections.abc import AsyncIterator
from typing import Any, ClassVar

import structlog
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMResponse

logger = structlog.get_logger()

# Models that require inference profiles (region-prefixed identifiers)
# These cannot be invoked with direct model IDs
INFERENCE_PROFILE_MODELS: set[str] = {
    "anthropic.claude-3-5-haiku-20241022-v1:0",  # Claude 3.5 Haiku
    "anthropic.claude-3-5-sonnet-20241022-v2:0",  # Claude 3.5 Sonnet v2
    "anthropic.claude-sonnet-4-5-20250929-v1:0",  # Claude Sonnet 4.5
    "anthropic.claude-opus-4-5-20251101-v1:0",  # Claude Opus 4.5
}

# Models that support prompt caching via cache_control blocks
# Requires minimum token count: 1024 tokens for most, 2048 for Haiku
CACHE_SUPPORTED_MODELS: set[str] = {
    # Claude 3.5 Sonnet v2 (direct and inference profiles)
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "eu.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
    # Claude 3.5 Haiku (direct and inference profiles)
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    "eu.anthropic.claude-3-5-haiku-20241022-v1:0",
    "apac.anthropic.claude-3-5-haiku-20241022-v1:0",
    # Claude Sonnet 4.5
    "anthropic.claude-sonnet-4-5-20250929-v1:0",
    "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "eu.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "apac.anthropic.claude-sonnet-4-5-20250929-v1:0",
    # Claude Opus 4.5
    "anthropic.claude-opus-4-5-20251101-v1:0",
    "us.anthropic.claude-opus-4-5-20251101-v1:0",
    "eu.anthropic.claude-opus-4-5-20251101-v1:0",
    "apac.anthropic.claude-opus-4-5-20251101-v1:0",
    # Claude 3 Haiku (requires 2048+ tokens)
    "anthropic.claude-3-haiku-20240307-v1:0",
}

# Minimum tokens required for caching (varies by model)
MIN_CACHE_TOKENS_DEFAULT = 1024
MIN_CACHE_TOKENS_HAIKU = 2048


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
        # Claude 3.5 Haiku (requires inference profile)
        "anthropic.claude-3-5-haiku-20241022-v1:0",
        "us.anthropic.claude-3-5-haiku-20241022-v1:0",
        "eu.anthropic.claude-3-5-haiku-20241022-v1:0",
        "apac.anthropic.claude-3-5-haiku-20241022-v1:0",
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
        "anthropic.claude-opus-4-5-20251101-v1:0",
        "us.anthropic.claude-opus-4-5-20251101-v1:0",
        "eu.anthropic.claude-opus-4-5-20251101-v1:0",
        "apac.anthropic.claude-opus-4-5-20251101-v1:0",
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
            # Build messages for Converse API
            converse_messages = self._build_converse_messages(messages)

            # Build inference config
            inference_config: dict[str, Any] = {
                "temperature": temperature,
                "maxTokens": max_tokens or 2048,
            }

            # Build request parameters
            request_params: dict[str, Any] = {
                "modelId": resolved_model,
                "messages": converse_messages,
                "inferenceConfig": inference_config,
            }

            # Add system prompt with caching if supported
            if system_prompt:
                request_params["system"] = self._build_system_with_cache(
                    system_prompt, resolved_model
                )

            # Use Converse API (async via run_in_executor)
            logger.debug(
                "Invoking Bedrock Converse API",
                original_model=model,
                resolved_model=resolved_model,
                cache_enabled=resolved_model in CACHE_SUPPORTED_MODELS,
            )

            # Run synchronous boto3 call in thread pool with graceful caching fallback
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None, lambda: self.bedrock_client.converse(**request_params)
                )
            except Exception as bedrock_error:
                # Handle AccessDeniedException for prompt caching
                error_msg = str(bedrock_error)
                if "AccessDeniedException" in error_msg and "prompt caching" in error_msg:
                    logger.warning(
                        "Prompt caching not available, retrying without cache",
                        model=resolved_model,
                        error=error_msg,
                    )
                    # Retry without caching - use simple system prompt format
                    if system_prompt:
                        request_params["system"] = [{"text": system_prompt}]

                    response = await loop.run_in_executor(
                        None, lambda: self.bedrock_client.converse(**request_params)
                    )
                else:
                    # Re-raise if not a caching-related error
                    raise

            # Extract content from Converse API response
            output = response.get("output", {})
            message = output.get("message", {})
            content_blocks = message.get("content", [])

            content = ""
            for block in content_blocks:
                if "text" in block:
                    content += block["text"]

            # Extract usage metrics from Converse API response
            usage_data = response.get("usage", {})
            usage = {
                "prompt_tokens": usage_data.get("inputTokens", 0),
                "completion_tokens": usage_data.get("outputTokens", 0),
                "total_tokens": usage_data.get("inputTokens", 0)
                + usage_data.get("outputTokens", 0),
            }

            # Extract stop reason
            stop_reason = response.get("stopReason", "end_turn")
            finish_reason_map = {
                "end_turn": "stop",
                "max_tokens": "length",
                "stop_sequence": "stop",
                "content_filtered": "content_filter",
            }
            finish_reason = finish_reason_map.get(stop_reason, stop_reason)

            llm_response = LLMResponse(
                content=content,
                model=model,  # Return original model code for consistency
                usage=usage,
                finish_reason=finish_reason,
                provider=self.provider_name,
            )

            # Log cache usage if available (Claude models report cache metrics)
            cache_read_tokens = usage_data.get("cacheReadInputTokens", 0)
            cache_write_tokens = usage_data.get("cacheCreationInputTokens", 0)
            if cache_read_tokens > 0 or cache_write_tokens > 0:
                usage["cache_read_tokens"] = cache_read_tokens
                usage["cache_write_tokens"] = cache_write_tokens
                logger.info(
                    "Prompt cache metrics",
                    model=model,
                    cache_read_tokens=cache_read_tokens,
                    cache_write_tokens=cache_write_tokens,
                )

            logger.info(
                "LLM generation completed via Converse API",
                model=model,
                resolved_model=resolved_model,
                tokens=usage.get("total_tokens", 0),
                cache_hit=cache_read_tokens > 0,
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
        Generate a completion with token streaming using Converse Stream API.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Yields:
            Token strings as they are generated
        """
        if not 0.0 <= temperature <= 1.0:
            raise ValueError(f"Temperature must be between 0.0 and 1.0, got {temperature}")

        # Resolve model ID to inference profile format if needed
        resolved_model = self._resolve_model_id(model)

        try:
            # Build messages for Converse API
            converse_messages = self._build_converse_messages(messages)

            # Build inference config
            inference_config: dict[str, Any] = {
                "temperature": temperature,
                "maxTokens": max_tokens or 2048,
            }

            # Build request parameters
            request_params: dict[str, Any] = {
                "modelId": resolved_model,
                "messages": converse_messages,
                "inferenceConfig": inference_config,
            }

            # Add system prompt with caching if supported
            if system_prompt:
                request_params["system"] = self._build_system_with_cache(
                    system_prompt, resolved_model
                )

            logger.debug(
                "Starting Bedrock Converse Stream",
                original_model=model,
                resolved_model=resolved_model,
            )

            # Use Converse Stream API with graceful caching fallback
            # Run in thread pool since boto3 is synchronous
            loop = asyncio.get_event_loop()
            try:
                response = await loop.run_in_executor(
                    None, lambda: self.bedrock_client.converse_stream(**request_params)
                )
            except Exception as bedrock_error:
                # Handle AccessDeniedException for prompt caching
                error_msg = str(bedrock_error)
                if "AccessDeniedException" in error_msg and "prompt caching" in error_msg:
                    logger.warning(
                        "Prompt caching not available for streaming, retrying without cache",
                        model=resolved_model,
                        error=error_msg,
                    )
                    # Retry without caching - use simple system prompt format
                    if system_prompt:
                        request_params["system"] = [{"text": system_prompt}]

                    response = await loop.run_in_executor(
                        None, lambda: self.bedrock_client.converse_stream(**request_params)
                    )
                else:
                    # Re-raise if not a caching-related error
                    raise

            # Process streaming response
            stream = response.get("stream")
            if stream:
                for event in stream:
                    if "contentBlockDelta" in event:
                        delta = event["contentBlockDelta"].get("delta", {})
                        if "text" in delta:
                            yield delta["text"]

        except Exception as e:
            logger.error("Bedrock streaming failed", model=model, error=str(e))
            raise RuntimeError(f"Bedrock streaming failed: {e}") from e

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

    def _build_converse_messages(
        self,
        messages: list[LLMMessage],
    ) -> list[dict[str, Any]]:
        """Build messages in Converse API format.

        The Converse API uses a unified message format:
        [{"role": "user|assistant", "content": [{"text": "..."}]}]
        """
        converse_messages: list[dict[str, Any]] = []

        for msg in messages:
            # Map role (system messages should be passed via system parameter)
            role = msg.role if msg.role in ("user", "assistant") else "user"

            converse_messages.append({"role": role, "content": [{"text": msg.content}]})

        return converse_messages

    def _build_system_with_cache(
        self,
        system_prompt: str,
        resolved_model: str,
    ) -> list[dict[str, Any]]:
        """Build system prompt block with cache_control for supported models.

        For Claude models that support caching, adds cache_control with ephemeral
        type to the system prompt. This enables prompt caching for the system prompt,
        reducing processing time for repeated prompts by up to 80%.

        Cache requirements:
        - Model must be in CACHE_SUPPORTED_MODELS
        - System prompt must meet minimum token threshold
        - Cache TTL is 5 minutes, extended on each cache hit

        Args:
            system_prompt: The system prompt text
            resolved_model: The resolved model ID (with inference profile if applicable)

        Returns:
            List of system content blocks for Converse API
        """
        # Check if model supports caching
        if resolved_model not in CACHE_SUPPORTED_MODELS:
            return [{"text": system_prompt}]

        # Estimate token count (rough estimate: 4 chars per token)
        estimated_tokens = len(system_prompt) // 4

        # Get minimum cache tokens for model type
        min_tokens = (
            MIN_CACHE_TOKENS_HAIKU
            if "haiku" in resolved_model.lower()
            else MIN_CACHE_TOKENS_DEFAULT
        )

        # Only add cache_control if prompt meets minimum token requirement
        if estimated_tokens < min_tokens:
            logger.debug(
                "System prompt below cache threshold",
                estimated_tokens=estimated_tokens,
                min_tokens=min_tokens,
                model=resolved_model,
            )
            return [{"text": system_prompt}]

        # Add cache_control block for caching
        # Note: cachePoint must be a separate element, not mixed with text
        logger.debug(
            "Adding cache_control to system prompt",
            estimated_tokens=estimated_tokens,
            model=resolved_model,
        )
        return [
            {"text": system_prompt},
            {"cachePoint": {"type": "default"}},
        ]


__all__ = ["BedrockLLMProvider"]
