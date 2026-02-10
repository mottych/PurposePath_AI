"""API request and response models.

This module provides Pydantic models for API layer, separate from domain models.
These models handle serialization, validation, and API contracts.
"""

from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
    AlignmentScore,
    MeasureAnalysisRequest,
    MeasureAnalysisResponse,
    MeasureRecommendation,
    OperationsAnalysisRequest,
    OperationsAnalysisResponse,
    StrategyAnalysisRequest,
    StrategyAnalysisResponse,
    StrategyRecommendation,
)
from coaching.src.api.models.auth import UserContext
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
    "MeasureAnalysisRequest",
    "MeasureAnalysisResponse",
    "MeasureRecommendation",
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
