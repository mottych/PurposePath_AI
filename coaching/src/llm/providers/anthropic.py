"""
Anthropic provider implementation for LangChain integration.

Direct integration with Anthropic's Claude API through LangChain.
"""

from typing import Any, ClassVar

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage

from .base import BaseProvider, ProviderType

logger = structlog.get_logger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic provider using LangChain integration."""

    # Supported Anthropic models
    SUPPORTED_MODELS: ClassVar[list[str]] = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]

    @property
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        return ProviderType.ANTHROPIC

    @property
    def supported_models(self) -> list[str]:
        """Get list of supported model names."""
        return self.SUPPORTED_MODELS.copy()

    async def initialize(self) -> None:
        """Initialize the Anthropic client."""
        try:
            # Use configured model or default to Claude 3.5 Sonnet
            model_name = self.config.model_name or "claude-3-5-sonnet-20241022"
            logger.info("Initializing Anthropic provider", model=model_name)

            # Create ChatAnthropic client with explicit parameters using exact field names
            from typing import Any

            from pydantic import SecretStr

            # Build kwargs only for non-None values
            kwargs: dict[str, Any] = {
                "model_name": model_name,
            }

            if self.config.api_key:
                kwargs["api_key"] = SecretStr(self.config.api_key)
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            if self.config.temperature is not None:
                kwargs["temperature"] = self.config.temperature
            if self.config.max_tokens:
                kwargs["max_tokens_to_sample"] = self.config.max_tokens
            if self.config.timeout:
                kwargs["timeout"] = self.config.timeout
            if self.config.max_retries:
                kwargs["max_retries"] = self.config.max_retries

            self._client = ChatAnthropic(**kwargs)

            logger.info("Anthropic provider initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Anthropic provider", error=str(e))
            raise

    async def get_client(self) -> BaseChatModel:
        """Get the LangChain chat model client."""
        if self._client is None:
            await self.initialize()
        if self._client is None:
            raise RuntimeError("Failed to initialize Anthropic client")
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
            logger.error(
                "Error invoking Anthropic model", error=str(e), model=self.config.model_name
            )
            raise

    async def stream(self, messages: list[BaseMessage]) -> Any:
        """Stream model responses."""
        try:
            client = await self.get_client()
            async for chunk in client.astream(messages):
                yield chunk.content

        except Exception as e:
            logger.error(
                "Error streaming from Anthropic model", error=str(e), model=self.config.model_name
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
            kwargs: dict[str, Any] = {"model_name": model_name}
            if self.config.api_key:
                kwargs["api_key"] = SecretStr(self.config.api_key)
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            kwargs["max_tokens_to_sample"] = 10  # Small token limit for test

            test_client = ChatAnthropic(**kwargs)

            test_message = [HumanMessage(content="Hello")]
            await test_client.ainvoke(test_message)
            return True

        except Exception as e:
            logger.warning("Unable to validate Anthropic model", model=model_name, error=str(e))
            return False

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""
        return {
            "model_id": self.config.model_name,
            "provider": "anthropic",
            "api_base": self.config.base_url or "https://api.anthropic.com",
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "streaming": self.config.streaming,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
        }

    async def cleanup(self) -> None:
        """Clean up Anthropic resources."""
        logger.info("Cleaning up Anthropic provider")
        self._client = None
