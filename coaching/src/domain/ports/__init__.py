"""Domain ports package.

This package contains port interfaces (protocols) that define contracts
for infrastructure implementations, following the Hexagonal Architecture pattern.
"""

from coaching.src.domain.ports.conversation_repository_port import ConversationRepositoryPort
from coaching.src.domain.ports.llm_provider_port import (
    LLMMessage,
    LLMProviderPort,
    LLMResponse,
)
from coaching.src.domain.ports.prompt_repository_port import PromptRepositoryPort

__all__ = [
    "ConversationRepositoryPort",
    "LLMMessage",
    "LLMProviderPort",
    "LLMResponse",
    "PromptRepositoryPort",
]
