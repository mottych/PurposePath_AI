"""Google Vertex AI LLM provider implementation using google-genai SDK.

This module provides a Google Vertex AI-backed implementation of the LLM provider
port interface, supporting Gemini 2.5+ and other Vertex AI models.

Migration from deprecated vertexai.generative_models to google.genai SDK:
- Uses native async support via client.aio.* methods
- Proper streaming with generate_content_stream()
- Context caching for system prompts via client.caches.create()
- Full feature parity with modern Gemini capabilities

Context Caching:
    Gemini supports context caching for system prompts and static content.
    This reduces processing time and costs for repeated prompts.

    Cache requirements:
    - Minimum 32,000 tokens of content to cache
    - Cache TTL: configurable (default 1 hour, max 24 hours)
    - Supported on Gemini 1.5+ and 2.0+ models

    See: https://cloud.google.com/vertex-ai/generative-ai/docs/context-caching

Reference: https://cloud.google.com/vertex-ai/generative-ai/docs/deprecations/genai-vertexai-sdk
"""

from collections.abc import AsyncIterator
from typing import Any, ClassVar

import structlog
from coaching.src.domain.ports.llm_provider_port import LLMMessage, LLMResponse

logger = structlog.get_logger()

# Minimum tokens required for Gemini context caching
# Gemini requires 32,000+ tokens for caching to be beneficial
MIN_CACHE_TOKENS_GEMINI = 32000

# Default cache TTL in seconds (1 hour)
DEFAULT_CACHE_TTL_SECONDS = 3600

# Models that support context caching
CACHE_SUPPORTED_MODELS_GEMINI: set[str] = {
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
}


class GoogleVertexLLMProvider:
    """
    Google Vertex AI adapter implementing LLMProviderPort.

    This adapter provides Google Vertex AI-backed LLM access using the new
    google-genai SDK (v1.56.0+), implementing the provider port interface
    defined in the domain layer.

    Design:
        - Uses google.genai.Client with vertexai=True for Vertex AI
        - Native async support via client.aio.* methods
        - Supports streaming via generate_content_stream()
        - Includes retry logic and error handling
        - Provides usage metrics

    Migration Note:
        This replaces the deprecated vertexai.generative_models module.
        The old module will be removed after June 24, 2026.
    """

    # Supported Vertex AI model IDs
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        # Gemini 3.x Series (latest - December 2025)
        "gemini-3-pro-preview",
        # Gemini 2.5 Series
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        # Gemini 2.0 Series
        "gemini-2.0-flash",
        "gemini-2.0-flash-001",
        "gemini-2.0-flash-lite",
        # Gemini 1.5 Series (legacy)
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        credentials: Any | None = None,
        enable_caching: bool = True,
    ):
        """
        Initialize Google Vertex AI LLM provider.

        Args:
            project_id: GCP project ID (optional - will retrieve from config/secrets if not provided)
            location: GCP location/region (default: us-central1)
            credentials: Optional GCP credentials object (will retrieve from Secrets Manager if not provided)
            enable_caching: Whether to enable context caching for system prompts (default: True)
        """
        self.project_id = project_id
        self.location = location
        self.credentials = credentials
        self.enable_caching = enable_caching
        self._client: Any | None = None
        self._initialized = False
        # Cache name registry: maps (model, system_prompt_hash) -> cache_name
        self._cache_registry: dict[tuple[str, str], str] = {}
        logger.info(
            "Google Vertex AI LLM provider initialized",
            project_id=project_id,
            enable_caching=enable_caching,
            location=location,
        )

    @property
    def provider_name(self) -> str:
        """Get the provider name."""
        return "google_vertex"

    @property
    def supported_models(self) -> list[str]:
        """Get list of supported models."""
        return self.SUPPORTED_MODELS.copy()

    async def _get_client(self) -> Any:
        """Get or create Vertex AI client (lazy initialization).

        Returns the google.genai.Client configured for Vertex AI.
        Uses client.aio for async operations.
        """
        if self._client is None:
            try:
                from google import genai
                from google.genai import types
            except ImportError as e:
                raise ImportError(
                    "Google Gen AI SDK not installed. "
                    "Install with: pip install google-genai>=1.56.0"
                ) from e

            # Get project_id and credentials from Secrets Manager if not provided
            project_id = self.project_id
            credentials = self.credentials

            from coaching.src.core.config_multitenant import (
                get_google_vertex_credentials,
                get_settings,
            )
            from google.oauth2 import service_account

            settings = get_settings()

            # Get project_id from config if not provided
            if not project_id:
                project_id = settings.google_project_id

            # Get credentials from Secrets Manager if not provided
            if not credentials:
                creds_dict = get_google_vertex_credentials()
                if creds_dict:
                    # For google-genai SDK, create service account credentials
                    # Vertex AI requires specific IAM roles on the service account:
                    # - roles/aiplatform.user (for Vertex AI API access)
                    # - roles/ml.developer (for ML operations)
                    creds_map: dict[str, Any] = creds_dict
                    credentials = service_account.Credentials.from_service_account_info(  # type: ignore[no-untyped-call]
                        creds_map,
                    )
                    # Update project_id from credentials if still not set
                    if not project_id:
                        project_id = creds_dict.get("project_id")

            # ALWAYS ensure credentials have the required OAuth scope for Vertex AI
            # This handles both: credentials passed via constructor AND loaded from secrets
            # The google-genai SDK requires cloud-platform scope for Vertex AI API access
            if credentials is not None and isinstance(credentials, service_account.Credentials):
                # Check if credentials already have required scope
                required_scope = "https://www.googleapis.com/auth/cloud-platform"
                if not credentials.scopes or required_scope not in credentials.scopes:
                    credentials = credentials.with_scopes([required_scope])
                    logger.debug(
                        "Added OAuth scope to credentials",
                        scope=required_scope,
                    )

            if not project_id:
                raise ValueError(
                    "Google Cloud project_id not configured. "
                    "Set GOOGLE_PROJECT_ID environment variable or configure in AWS Secrets Manager"
                )

            # Create google-genai client for Vertex AI
            # Using vertexai=True enables Vertex AI mode
            http_options = types.HttpOptions(api_version="v1")

            self._client = genai.Client(
                vertexai=True,
                project=project_id,
                location=self.location,
                credentials=credentials,
                http_options=http_options,
            )
            self._initialized = True
            logger.info("Google Gen AI client initialized for Vertex AI", project_id=project_id)

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
        Generate a completion from Google Vertex AI using async API.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0 for Gemini)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt
            response_schema: Optional JSON schema for structured output

        Returns:
            LLMResponse with generated content and metadata

        Business Rule: Temperature must be between 0.0 and 2.0 for Gemini
        """
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(
                f"Temperature must be between 0.0 and 2.0 for Gemini, got {temperature}"
            )

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}")

        try:
            from google.genai import types

            client = await self._get_client()

            # Build contents from messages
            # google-genai uses types.Content for multi-turn conversations
            contents: list[types.Content] = []

            for msg in messages:
                # Map roles: user -> user, assistant/system -> model
                role = "user" if msg.role == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)],
                    )
                )

            # Build generation config
            config_params: dict[str, Any] = {
                "temperature": temperature,
                "max_output_tokens": max_tokens or 8192,
                "top_p": 0.95,
            }

            # Add system instruction if provided
            if system_prompt:
                config_params["system_instruction"] = system_prompt

            # Add response schema for structured output if provided
            if response_schema:
                config_params["response_mime_type"] = "application/json"
                config_params["response_schema"] = response_schema

            config = types.GenerateContentConfig(**config_params)

            # Call Vertex AI API using async client
            logger.info(
                "Calling Google Vertex AI API (async)",
                model=model,
                num_messages=len(contents),
                temperature=temperature,
            )

            # Use client.aio for async operations
            response = await client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )

            # Extract response text
            content = response.text if response.text else ""

            # Extract finish reason
            finish_reason = "stop"  # default
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    gemini_reason = str(candidate.finish_reason)
                    # Map Gemini finish reasons to standard format
                    reason_map = {
                        "STOP": "stop",
                        "FinishReason.STOP": "stop",
                        "MAX_TOKENS": "length",
                        "FinishReason.MAX_TOKENS": "length",
                        "SAFETY": "content_filter",
                        "FinishReason.SAFETY": "content_filter",
                        "RECITATION": "content_filter",
                        "FinishReason.RECITATION": "content_filter",
                    }
                    finish_reason = reason_map.get(gemini_reason, gemini_reason.lower())

            # Extract usage metrics
            usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage_meta = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(usage_meta, "prompt_token_count", 0) or 0,
                    "completion_tokens": getattr(usage_meta, "candidates_token_count", 0) or 0,
                    "total_tokens": getattr(usage_meta, "total_token_count", 0) or 0,
                }

                # Log cache eligibility metrics
                # Note: Gemini requires 32,000+ tokens for context caching to be beneficial
                prompt_tokens = usage.get("prompt_tokens", 0)
                cache_eligible = (
                    self.enable_caching
                    and model in CACHE_SUPPORTED_MODELS_GEMINI
                    and prompt_tokens >= MIN_CACHE_TOKENS_GEMINI
                )
                if cache_eligible:
                    logger.info(
                        "Gemini context caching eligible",
                        model=model,
                        prompt_tokens=prompt_tokens,
                        min_required=MIN_CACHE_TOKENS_GEMINI,
                    )
                elif self.enable_caching and model in CACHE_SUPPORTED_MODELS_GEMINI:
                    logger.debug(
                        "Gemini context caching not eligible (below token threshold)",
                        model=model,
                        prompt_tokens=prompt_tokens,
                        min_required=MIN_CACHE_TOKENS_GEMINI,
                    )

            logger.info(
                "Google Vertex AI API call successful",
                model=model,
                usage=usage,
                finish_reason=finish_reason,
            )

            return LLMResponse(
                content=content,
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                provider=self.provider_name,
            )

        except Exception as e:
            logger.error("Google Vertex AI API call failed", error=str(e), model=model)
            raise RuntimeError(f"Google Vertex AI API call failed: {e}") from e

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        Generate a completion with token streaming using async API.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0 for Gemini)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Yields:
            Token strings as they are generated

        Business Rule: Must yield tokens incrementally for real-time UX
        """
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(
                f"Temperature must be between 0.0 and 2.0 for Gemini, got {temperature}"
            )

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}")

        try:
            from google.genai import types

            client = await self._get_client()

            # Build contents from messages
            contents: list[types.Content] = []

            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=msg.content)],
                    )
                )

            # Build generation config
            config_params: dict[str, Any] = {
                "temperature": temperature,
                "max_output_tokens": max_tokens or 8192,
                "top_p": 0.95,
            }

            if system_prompt:
                config_params["system_instruction"] = system_prompt

            config = types.GenerateContentConfig(**config_params)

            # Call Vertex AI streaming API using async client
            logger.info(
                "Calling Google Vertex AI streaming API (async)",
                model=model,
                num_messages=len(contents),
                temperature=temperature,
            )

            # Use client.aio.models.generate_content_stream for async streaming
            async for chunk in await client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error("Google Vertex AI streaming API call failed", error=str(e), model=model)
            raise RuntimeError(f"Google Vertex AI streaming API call failed: {e}") from e

    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text for a specific model.

        Args:
            text: Text to tokenize
            model: Model identifier

        Returns:
            Number of tokens

        Note: Uses google-genai SDK's count_tokens API.
        """
        try:
            client = await self._get_client()

            # Use the count_tokens API
            response = await client.aio.models.count_tokens(
                model=model,
                contents=text,
            )

            return int(response.total_tokens) if response.total_tokens else 0

        except Exception as e:
            logger.warning("Token counting failed, using approximation", error=str(e), model=model)
            # Fallback approximation: ~4 characters per token
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

    async def close(self) -> None:
        """Close the client and release resources.

        Should be called when the provider is no longer needed.
        """
        if self._client is not None:
            try:
                # Close async client resources
                await self._client.aio.close()
            except Exception as e:
                logger.warning("Error closing Google Gen AI client", error=str(e))
            finally:
                self._client = None
                self._initialized = False


__all__ = ["GoogleVertexLLMProvider"]
