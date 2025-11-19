"""Coaching AI API routes for strategic planning assistance (Issue #62)."""

import uuid
from datetime import UTC, datetime

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
    AlignmentScore,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.strategy_suggestions import (
    StrategySuggestion,
    StrategySuggestionsRequest,
    StrategySuggestionsResponse,
)
from coaching.src.application.analysis.alignment_service import AlignmentAnalysisService
from coaching.src.application.analysis.strategy_suggestion_service import (
    StrategySuggestionService,
)
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.config_multitenant import settings
from coaching.src.core.constants import AnalysisType
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from fastapi import APIRouter, Depends, HTTPException, status

from shared.models.schemas import ApiResponse
from shared.services.aws_helpers import get_bedrock_client

logger = structlog.get_logger()
router = APIRouter(prefix="/coaching", tags=["coaching", "ai"])


async def get_llm_service() -> LLMApplicationService:
    """Get LLM Application Service with Bedrock provider."""
    bedrock_client = get_bedrock_client(settings.bedrock_region)
    bedrock_provider = BedrockLLMProvider(
        bedrock_client=bedrock_client,
        region=settings.bedrock_region,
    )
    return LLMApplicationService(llm_provider=bedrock_provider)


async def get_alignment_service() -> AlignmentAnalysisService:
    """Get Alignment Analysis Service with LLM integration."""
    llm_service = await get_llm_service()
    return AlignmentAnalysisService(llm_service=llm_service)


async def get_strategy_service() -> StrategySuggestionService:
    """Get Strategy Suggestion Service with LLM integration."""
    llm_service = await get_llm_service()
    return StrategySuggestionService(llm_service=llm_service)


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
        logger.info("Generating alignment analysis", user_id=user.user_id)
        analysis_result = await alignment_service.analyze(
            context={
                "user_id": user.user_id,
                "current_actions": request.text_to_analyze,
                **request.context,
            }
        )

        # Transform service result to response model
        return AlignmentAnalysisResponse(
            analysis_id=f"anls_{uuid.uuid4().hex[:12]}",
            analysis_type=AnalysisType.ALIGNMENT,
            scores=AlignmentScore(
                overall_score=float(analysis_result.get("alignment_score", 0)),
                purpose_alignment=float(analysis_result.get("alignment_score", 0)),
                values_alignment=float(analysis_result.get("alignment_score", 0)),
                goal_clarity=float(analysis_result.get("alignment_score", 0)),
            ),
            overall_assessment=analysis_result.get("overall_assessment", ""),
            strengths=analysis_result.get("strengths", []),
            misalignments=[m.get("area", "") for m in analysis_result.get("misalignments", [])],
            recommendations=analysis_result.get("recommendations", []),
            created_at=datetime.now(UTC),
            metadata={"user_id": user.user_id},
        )
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
        logger.info("Generating alignment analysis with suggestions", user_id=user.user_id)
        analysis_result = await alignment_service.analyze(
            context={
                "user_id": user.user_id,
                "current_actions": request.text_to_analyze,
                **request.context,
            }
        )

        # Transform service result to response model
        return AlignmentAnalysisResponse(
            analysis_id=f"anls_{uuid.uuid4().hex[:12]}",
            analysis_type=AnalysisType.ALIGNMENT,
            scores=AlignmentScore(
                overall_score=float(analysis_result.get("alignment_score", 0)),
                purpose_alignment=float(analysis_result.get("alignment_score", 0)),
                values_alignment=float(analysis_result.get("alignment_score", 0)),
                goal_clarity=float(analysis_result.get("alignment_score", 0)),
            ),
            overall_assessment=analysis_result.get("overall_assessment", ""),
            strengths=analysis_result.get("strengths", []),
            misalignments=[m.get("area", "") for m in analysis_result.get("misalignments", [])],
            recommendations=analysis_result.get("recommendations", []),
            created_at=datetime.now(UTC),
            metadata={"user_id": user.user_id},
        )
    except Exception as e:
        logger.error("Alignment suggestions failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


@router.post(
    "/strategy-suggestions",
    response_model=ApiResponse[StrategySuggestionsResponse],
    status_code=status.HTTP_200_OK,
)
async def get_strategy_suggestions(
    request: StrategySuggestionsRequest,
    user: UserContext = Depends(get_current_user),
    strategy_service: StrategySuggestionService = Depends(get_strategy_service),
) -> ApiResponse[StrategySuggestionsResponse]:
    """Get AI-generated strategy recommendations for a goal (Issue #107).

    This endpoint matches the specification in backend-integration-coaching-service.md.
    Generates strategy suggestions based on goal intent, business context, and constraints
    using real LLM analysis.
    """
    try:
        logger.info(
            "Generating strategy suggestions with LLM",
            user_id=user.user_id,
            goal_intent=request.goal_intent[:100],
        )

        # Use strategy service to generate real AI recommendations
        analysis_result = await strategy_service.analyze(
            context={
                "user_id": user.user_id,
                "goal_intent": request.goal_intent,
                "business_context": request.business_context,
                "existing_strategies": request.existing_strategies,
                "constraints": request.constraints,
            }
        )

        # Transform service result to response model
        suggestions = [
            StrategySuggestion(
                title=s["title"],
                description=s["description"],
                rationale=s["rationale"],
                difficulty=s["difficulty"],
                timeframe=s["timeframe"],
                expected_impact=s["expectedImpact"],
                prerequisites=s.get("prerequisites", []),
                estimated_cost=s.get("estimatedCost"),
                required_resources=s.get("requiredResources", []),
            )
            for s in analysis_result["suggestions"]
        ]

        logger.info(
            "Strategy suggestions generated successfully",
            user_id=user.user_id,
            suggestion_count=len(suggestions),
            confidence=analysis_result["confidence"],
        )

        response_data = StrategySuggestionsResponse(
            suggestions=suggestions,
            confidence=analysis_result["confidence"],
            reasoning=analysis_result["reasoning"],
        )

        return ApiResponse(success=True, data=response_data)

    except ValueError as e:
        logger.warning(
            "Invalid strategy suggestion request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Strategy suggestions failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate strategy suggestions",
        ) from e


__all__ = ["router"]
