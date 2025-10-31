"""API request and response models.

This module provides Pydantic models for API layer, separate from domain models.
These models handle serialization, validation, and API contracts.
"""

from src.api.models.analysis import (
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
from src.api.models.auth import UserContext
from src.api.models.conversations import (
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
    # Analysis models
    "AlignmentAnalysisRequest",
    "AlignmentAnalysisResponse",
    "AlignmentScore",
    "CompleteConversationRequest",
    "ConversationDetailResponse",
    "ConversationListResponse",
    "ConversationResponse",
    # Conversation models
    "InitiateConversationRequest",
    "KPIAnalysisRequest",
    "KPIAnalysisResponse",
    "KPIRecommendation",
    "MessageRequest",
    "MessageResponse",
    "OperationsAnalysisRequest",
    "OperationsAnalysisResponse",
    "PauseConversationRequest",
    "StrategyAnalysisRequest",
    "StrategyAnalysisResponse",
    "StrategyRecommendation",
    # Auth models
    "UserContext",
]
