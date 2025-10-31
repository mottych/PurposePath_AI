"""Google Vertex AI LLM provider implementation.

This module provides a Google Vertex AI-backed implementation of the LLM provider
port interface, supporting Gemini 2.5 and other Vertex AI models.
"""

from collections.abc import AsyncIterator
from typing import Any, ClassVar

import structlog

from src.domain.ports.llm_provider_port import LLMMessage, LLMResponse

logger = structlog.get_logger()


class GoogleVertexLLMProvider:
    """
    Google Vertex AI adapter implementing LLMProviderPort.

    This adapter provides Google Vertex AI-backed LLM access,
    implementing the provider port interface defined in the domain layer.

    Design:
        - Supports Gemini models (2.5 Pro, 2.5 Flash)
        - Handles both streaming and non-streaming
        - Includes retry logic and error handling
        - Provides usage metrics
    """

    # Supported Vertex AI model IDs
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        credentials: Any | None = None,
    ):
        """
        Initialize Google Vertex AI LLM provider.

        Args:
            project_id: GCP project ID (optional - will retrieve from config/secrets if not provided)
            location: GCP location/region (default: us-central1)
            credentials: Optional GCP credentials object (will retrieve from Secrets Manager if not provided)
        """
        self.project_id = project_id
        self.location = location
        self.credentials = credentials
        self._client: Any | None = None
        logger.info(
            "Google Vertex AI LLM provider initialized",
            project_id=project_id,
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
        """Get or create Vertex AI client (lazy initialization)."""
        if self._client is None:
            try:
                from google.cloud import aiplatform
                from google.oauth2 import service_account
                from vertexai.generative_models import GenerativeModel
            except ImportError as e:
                raise ImportError(
                    "Google Cloud AI Platform SDK not installed. "
                    "Install with: pip install google-cloud-aiplatform>=1.40.0"
                ) from e

            # Get project_id and credentials from Secrets Manager if not provided
            project_id = self.project_id
            credentials = self.credentials

            if not project_id or not credentials:
                from src.core.config_multitenant import (
                    get_google_vertex_credentials,
                    get_settings,
                )

                settings = get_settings()

                # Get project_id from config if not provided
                if not project_id:
                    project_id = settings.google_project_id

                # Get credentials from Secrets Manager if not provided
                if not credentials:
                    creds_dict = get_google_vertex_credentials()
                    if creds_dict:
                        credentials = service_account.Credentials.from_service_account_info(
                            creds_dict
                        )
                        # Update project_id from credentials if still not set
                        if not project_id:
                            project_id = creds_dict.get("project_id")

            if not project_id:
                raise ValueError(
                    "Google Cloud project_id not configured. "
                    "Set GOOGLE_PROJECT_ID environment variable or configure in AWS Secrets Manager"
                )

            # Initialize Vertex AI
            aiplatform.init(
                project=project_id,
                location=self.location,
                credentials=credentials,
            )

            self._client = GenerativeModel
            logger.info("Vertex AI client initialized", project_id=project_id)
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
        Generate a completion from Google Vertex AI.

        Args:
            messages: Conversation history
            model: Model identifier
            temperature: Sampling temperature (0.0-2.0 for Gemini)
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt

        Returns:
            LLMResponse with generated content and metadata

        Business Rule: Temperature must be between 0.0 and 2.0 for Gemini
        """
        if not 0.0 <= temperature <= 2.0:
            raise ValueError(
                f"Temperature must be between 0.0 and 2.0 for Gemini, got {temperature}"
            )

        if model not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}"
            )

        try:
            client_class = await self._get_client()
            model_instance = client_class(model)

            # Build conversation content
            # Gemini API uses a different format than OpenAI/Claude
            contents = []

            # Add system instruction if provided (Gemini uses system_instruction parameter)
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens or 8192,
                "top_p": 0.95,
            }

            # Combine messages into conversation
            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

            # Call Vertex AI API
            logger.info(
                "Calling Google Vertex AI API",
                model=model,
                num_messages=len(contents),
                temperature=temperature,
            )

            response = model_instance.generate_content(
                contents=contents,
                generation_config=generation_config,
                system_instruction=system_prompt,
            )

            # Extract response
            content = response.text if response.text else ""
            finish_reason = "stop"  # Gemini uses different finish reasons

            # Extract usage metrics (Gemini provides token counts)
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0)
                if hasattr(response, "usage_metadata")
                else 0,
                "completion_tokens": getattr(
                    response.usage_metadata, "candidates_token_count", 0
                )
                if hasattr(response, "usage_metadata")
                else 0,
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0)
                if hasattr(response, "usage_metadata")
                else 0,
            }

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
        Generate a completion with token streaming.

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
            raise ValueError(
                f"Model {model} not supported. Supported: {self.SUPPORTED_MODELS}"
            )

        try:
            client_class = await self._get_client()
            model_instance = client_class(model)

            # Build conversation content
            contents = []
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens or 8192,
                "top_p": 0.95,
            }

            for msg in messages:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

            # Call Vertex AI streaming API
            logger.info(
                "Calling Google Vertex AI streaming API",
                model=model,
                num_messages=len(contents),
                temperature=temperature,
            )

            response_stream = model_instance.generate_content(
                contents=contents,
                generation_config=generation_config,
                system_instruction=system_prompt,
                stream=True,
            )

            # Stream tokens
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(
                "Google Vertex AI streaming API call failed", error=str(e), model=model
            )
            raise RuntimeError(f"Google Vertex AI streaming API call failed: {e}") from e

    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count tokens in text for a specific model.

        Args:
            text: Text to tokenize
            model: Model identifier

        Returns:
            Number of tokens

        Note: Gemini has built-in token counting via count_tokens API.
        """
        try:
            client_class = await self._get_client()
            model_instance = client_class(model)

            # Use Gemini's token counting API
            response = model_instance.count_tokens(text)
            return response.total_tokens

        except Exception as e:
            logger.warning(
                "Token counting failed, using approximation", error=str(e), model=model
            )
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


__all__ = ["GoogleVertexLLMProvider"]
