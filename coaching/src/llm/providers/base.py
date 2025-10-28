"""
Base provider interface for LangChain integration.

Defines the abstract base class and common types for all AI providers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """Supported AI provider types."""

    BEDROCK = "bedrock"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ProviderConfig(BaseModel):
    """Configuration for AI provider initialization."""

    provider_type: ProviderType = Field(..., description="Type of provider")
    model_name: str = Field(..., description="Model identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Response creativity")
    max_tokens: int | None = Field(default=None, gt=0, description="Max response length")
    top_p: float | None = Field(default=None, ge=0.0, le=1.0, description="Nucleus sampling")

    # Provider-specific configurations
    region_name: str | None = Field(default=None, description="AWS region for Bedrock")
    api_key: str | None = Field(default=None, description="Direct API key")
    base_url: str | None = Field(default=None, description="Custom API endpoint")

    # Advanced settings
    streaming: bool = Field(default=False, description="Enable streaming responses")
    timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, config: ProviderConfig):
        """Initialize provider with configuration."""
        self.config = config
        self._client: BaseChatModel | None = None

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Get the provider type."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """Get list of supported model names."""
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client."""
        pass

    @abstractmethod
    async def get_client(self) -> BaseChatModel:
        """Get the LangChain chat model client."""
        pass

    @abstractmethod
    async def invoke(self, messages: list[BaseMessage]) -> str:
        """Invoke the model with messages and return response."""
        pass

    @abstractmethod
    async def stream(self, messages: list[BaseMessage]) -> Any:
        """Stream model responses."""
        pass

    @abstractmethod
    async def validate_model(self, model_name: str) -> bool:
        """Validate if model is supported and accessible."""
        pass

    @abstractmethod
    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""
        pass

    async def cleanup(self) -> None:
        """Clean up provider resources.

        Default implementation does nothing. Override if cleanup is needed.
        """
        # Concrete default implementation - subclasses can override
        return None

    def __repr__(self) -> str:
        """String representation of provider."""
        return (
            f"{self.__class__.__name__}(type={self.provider_type}, model={self.config.model_name})"
        )


# Legacy interface compatibility - will be deprecated in future versions
class LLMProvider(BaseProvider):
    """Legacy interface for backward compatibility."""

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> str:
        """Generate a response from the LLM (legacy interface)."""
        # Convert to LangChain format and delegate to new interface
        from langchain_core.messages import HumanMessage, SystemMessage

        lc_messages: list[BaseMessage] = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))

        for msg in messages:
            lc_messages.append(HumanMessage(content=msg.get("content", "")))

        return await self.invoke(lc_messages)

    async def analyze_text(self, text: str, analysis_prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze text using the LLM (legacy interface)."""
        from langchain_core.messages import HumanMessage

        prompt = f"{analysis_prompt}\n\nText to analyze:\n{text}"
        response = await self.invoke([HumanMessage(content=prompt)])

        # Return as dict for compatibility
        return {"analysis": response, "input_text": text}

    def count_tokens(self, text: str) -> int:
        """Count tokens in text (legacy interface)."""
        # Simple estimation - override in specific providers for accuracy
        return int(len(text.split()) * 1.3)  # Rough token estimation

    def format_messages(
        self, messages: list[dict[str, str]], system_prompt: str
    ) -> list[dict[str, str]]:
        """Format messages for the provider (legacy interface)."""
        formatted = []

        # Add system prompt
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})

        # Add conversation messages
        formatted.extend(messages)

        return formatted
