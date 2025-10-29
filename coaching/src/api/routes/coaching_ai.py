"""Coaching AI API routes for strategic planning assistance (Issue #62)."""

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
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
    response_model=AlignmentAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_explanation(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> AlignmentAnalysisResponse:
    """Generate AI-powered alignment analysis (Issue #62)."""
    try:
        logger.info(
            "Generating alignment analysis", user_id=user.user_id
        )
        analysis_result = await alignment_service.analyze(
            context={
                "user_id": user.user_id,
                "current_actions": request.text_to_analyze,
                **request.context,
            }
        )
        return AlignmentAnalysisResponse(success=True, data=analysis_result)
    except Exception as e:
        logger.error("Alignment explanation failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate explanation",
        ) from e


@router.post(
    "/alignment-suggestions",
    response_model=AlignmentAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_suggestions(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> AlignmentAnalysisResponse:
    """Generate AI-powered alignment analysis with suggestions (Issue #62)."""
    try:
        logger.info(
            "Generating alignment analysis with suggestions", user_id=user.user_id
        )
        analysis_result = await alignment_service.analyze(
            context={
                "user_id": user.user_id,
                "current_actions": request.text_to_analyze,
                **request.context,
            }
        )
        return AlignmentAnalysisResponse(success=True, data=analysis_result)
    except Exception as e:
        logger.error("Alignment suggestions failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


__all__ = ["router"]
