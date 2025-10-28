"""Coaching AI API routes for strategic planning assistance (Issue #62)."""

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.models.analysis import (
    AlignmentExplanationRequest,
    AlignmentExplanationResponse,
    AlignmentSuggestionsRequest,
    AlignmentSuggestionsResponse,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.application.analysis.alignment_service import AlignmentAnalysisService
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.config_multitenant import settings
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from fastapi import APIRouter, Depends, HTTPException, status

from shared.services.aws_helpers import get_bedrock_client

logger = structlog.get_logger()
router = APIRouter(prefix="/coaching", tags=["coaching", "ai"])


async def get_alignment_service() -> AlignmentAnalysisService:
    """Get Alignment Analysis Service with LLM integration."""
    bedrock_client = get_bedrock_client(settings.bedrock_region)
    bedrock_provider = BedrockLLMProvider(
        bedrock_client=bedrock_client,
        region=settings.bedrock_region,
    )
    llm_service = LLMApplicationService(llm_provider=bedrock_provider)
    return AlignmentAnalysisService(llm_service=llm_service)


@router.post(
    "/alignment-explanation",
    response_model=AlignmentExplanationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_explanation(
    request: AlignmentExplanationRequest,
    user: UserContext = Depends(get_current_user),
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> AlignmentExplanationResponse:
    """Generate AI-powered explanation of alignment score (Issue #62)."""
    try:
        logger.info(
            "Generating alignment explanation", user_id=user.user_id, score=request.alignmentScore
        )
        goal_data = request.goal.model_dump()
        foundation_data = request.businessFoundation.model_dump()
        explanation = await alignment_service.get_detailed_explanation(
            alignment_score=request.alignmentScore,
            goal=goal_data,
            business_foundation=foundation_data,
        )
        return AlignmentExplanationResponse(success=True, explanation=explanation)
    except Exception as e:
        logger.error("Alignment explanation failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation",
        ) from e


@router.post(
    "/alignment-suggestions",
    response_model=AlignmentSuggestionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_suggestions(
    request: AlignmentSuggestionsRequest,
    user: UserContext = Depends(get_current_user),
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> AlignmentSuggestionsResponse:
    """Generate AI-powered suggestions to improve alignment (Issue #62)."""
    try:
        logger.info(
            "Generating alignment suggestions", user_id=user.user_id, score=request.alignmentScore
        )
        goal_data = request.goal.model_dump()
        foundation_data = request.businessFoundation.model_dump()
        suggestions = await alignment_service.get_improvement_suggestions(
            alignment_score=request.alignmentScore,
            goal=goal_data,
            business_foundation=foundation_data,
        )
        return AlignmentSuggestionsResponse(success=True, suggestions=suggestions)
    except Exception as e:
        logger.error("Alignment suggestions failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


__all__ = ["router"]
