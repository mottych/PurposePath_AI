"""
LangChain provider management for PurposePath Coaching Service.

This module provides a unified interface for managing multiple AI providers:
- AWS Bedrock (Claude, Titan, Cohere)
- Anthropic (Claude Direct API)
- OpenAI (GPT models)

Architecture:
- BaseProvider: Abstract interface for all providers
- ProviderManager: Factory and lifecycle management
- Provider Implementations: Specific provider integrations
"""

from .anthropic import AnthropicProvider
from .base import BaseProvider, ProviderConfig, ProviderType
from .bedrock import BedrockProvider
from .manager import ProviderManager, provider_manager
from .openai import OpenAIProvider

__all__ = [
    "AnthropicProvider",
    "BaseProvider",
    "BedrockProvider",
    "OpenAIProvider",
    "ProviderConfig",
    "ProviderManager",
    "ProviderType",
    "provider_manager",
]
