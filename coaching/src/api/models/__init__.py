"""API request and response models.

This module provides Pydantic models for API layer, separate from domain models.
These models handle serialization, validation, and API contracts.
"""

from coaching.src.api.models.conversations import (
    CompleteConversationRequest,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    InitiateConversationRequest,
    MessageRequest,
    MessageResponse,
    PauseConversationRequest,
)

__all__ = [
    # Conversation models
    "InitiateConversationRequest",
    "MessageRequest",
    "PauseConversationRequest",
    "CompleteConversationRequest",
    "ConversationResponse",
    "MessageResponse",
    "ConversationDetailResponse",
    "ConversationListResponse",
]
