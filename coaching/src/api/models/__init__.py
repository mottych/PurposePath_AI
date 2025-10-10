"""API request and response models.

This module provides Pydantic models for API layer, separate from domain models.
These models handle serialization, validation, and API contracts.
"""

from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
    AlignmentScore,
    KPIAnalysisRequest,
    KPIAnalysisResponse,
    KPIRecommendation,
    OperationsAnalysisRequest,
    OperationsAnalysisResponse,
    StrategyAnalysisRequest,
    StrategyAnalysisResponse,
    StrategyRecommendation,
)
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
    # Auth models
    "UserContext",
    # Conversation models
    "InitiateConversationRequest",
    "MessageRequest",
    "PauseConversationRequest",
    "CompleteConversationRequest",
    "ConversationResponse",
    "MessageResponse",
    "ConversationDetailResponse",
    "ConversationListResponse",
    # Analysis models
    "AlignmentAnalysisRequest",
    "AlignmentAnalysisResponse",
    "AlignmentScore",
    "StrategyAnalysisRequest",
    "StrategyAnalysisResponse",
    "StrategyRecommendation",
    "KPIAnalysisRequest",
    "KPIAnalysisResponse",
    "KPIRecommendation",
    "OperationsAnalysisRequest",
    "OperationsAnalysisResponse",
]
