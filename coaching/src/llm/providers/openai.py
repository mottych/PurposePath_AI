"""
OpenAI provider implementation.

Direct integration with OpenAI's GPT models through LangChain.
"""

from typing import Any, ClassVar

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from .base import BaseProvider, ProviderType

logger = structlog.get_logger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI provider using LangChain integration."""

    # Supported OpenAI models
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-4",
        "gpt-4-32k",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
    ]

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.OPENAI

    @property
    def supported_models(self) -> list[str]:
        """Get list of supported model names."""
        return self.SUPPORTED_MODELS.copy()

    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            # Use configured model or default to GPT-4o-mini
            model_name = self.config.model_name or "gpt-4o-mini"
            logger.info("Initializing OpenAI provider", model=model_name)

            # Create ChatOpenAI client with explicit parameters using exact field names
            from typing import Any

            from pydantic import SecretStr

            # Build kwargs only for non-None values
            kwargs: dict[str, Any] = {
                "model": model_name,  # Using alias
            }

            if self.config.api_key:
                kwargs["api_key"] = SecretStr(self.config.api_key)  # Using alias
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url  # Using alias
            if self.config.temperature is not None:
                kwargs["temperature"] = self.config.temperature
            if self.config.max_tokens:
                kwargs["max_completion_tokens"] = self.config.max_tokens  # Using alias
            if self.config.timeout:
                kwargs["timeout"] = self.config.timeout  # Using alias
            if self.config.max_retries:
                kwargs["max_retries"] = self.config.max_retries

            self._client = ChatOpenAI(**kwargs)

            logger.info("OpenAI provider initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize OpenAI provider", error=str(e))
            raise

    async def get_client(self) -> BaseChatModel:
        """Get the LangChain chat model client."""
        if self._client is None:
            await self.initialize()
        if self._client is None:
            raise RuntimeError("Failed to initialize OpenAI client")
        return self._client

    async def invoke(self, messages: list[BaseMessage]) -> str:
        """Invoke the model with messages and return response."""
        try:
            client = await self.get_client()
            response = await client.ainvoke(messages)
            # Handle different response content types
            if isinstance(response.content, str):
                return response.content
            elif isinstance(response.content, list):
                # If content is a list, join string elements
                content_parts = []
                for part in response.content:
                    if isinstance(part, str):
                        content_parts.append(part)
                    elif isinstance(part, dict) and "text" in part:
                        content_parts.append(str(part["text"]))
                return "".join(content_parts)
            else:
                return str(response.content)

        except Exception as e:
            logger.error("Error invoking OpenAI model", error=str(e), model=self.config.model_name)
            raise

    async def stream(self, messages: list[BaseMessage]) -> Any:
        """Stream model responses."""
        try:
            client = await self.get_client()
            async for chunk in client.astream(messages):
                yield chunk.content

        except Exception as e:
            logger.error(
                "Error streaming from OpenAI model", error=str(e), model=self.config.model_name
            )
            raise

    async def validate_model(self, model_name: str) -> bool:
        """Validate if model is supported and accessible."""
        if model_name not in self.SUPPORTED_MODELS:
            return False

        try:
            # Test with a simple message
            from typing import Any

            from langchain_core.messages import HumanMessage
            from pydantic import SecretStr

            # Build kwargs only for non-None values
            kwargs: dict[str, Any] = {"model": model_name}  # Using alias
            if self.config.api_key:
                kwargs["api_key"] = SecretStr(self.config.api_key)  # Using alias
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url  # Using alias
            kwargs["max_completion_tokens"] = 10  # Small token limit for test, using alias

            test_client = ChatOpenAI(**kwargs)

            test_message = [HumanMessage(content="Hello")]
            await test_client.ainvoke(test_message)
            return True

        except Exception as e:
            logger.warning("Unable to validate OpenAI model", model=model_name, error=str(e))
            return False

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""
        return {
            "model_id": self.config.model_name,
            "provider": "openai",
            "api_base": self.config.base_url or "https://api.openai.com/v1",
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "streaming": self.config.streaming,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
        }

    async def cleanup(self) -> None:
        """Clean up OpenAI resources."""
        logger.info("Cleaning up OpenAI provider")
        self._client = None
