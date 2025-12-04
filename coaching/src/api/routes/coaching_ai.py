"""Coaching AI API routes - migrated to topic-driven architecture (Issue #113).

This module provides AI-powered strategic planning endpoints using the unified
topic-driven architecture. All endpoints now route through GenericAIHandler
which uses UnifiedAIEngine for consistent prompt management and AI processing.

Migration Status:
- alignment-explanation: Migrated to topic-driven (alignment_explanation topic)
- alignment-suggestions: Migrated to topic-driven (alignment_suggestions topic)
- strategy-suggestions: Migrated to topic-driven (strategy_suggestions topic)
"""

from typing import cast

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
    AlignmentExplanationResponse,
    AlignmentSuggestionsResponse,
    KPIRecommendationsRequest,
    KPIRecommendationsResponse,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.onboarding import (
    OnboardingCoachingRequest,
    OnboardingCoachingResponse,
)
from coaching.src.api.models.strategy_suggestions import (
    StrategySuggestionsRequest,
    StrategySuggestionsResponse,
)
from fastapi import APIRouter, Depends, status

from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/coaching", tags=["coaching", "ai"])


@router.post(
    "/onboarding",
    response_model=OnboardingCoachingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_onboarding_coaching(
    request: OnboardingCoachingRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> OnboardingCoachingResponse:
    """Get AI coaching assistance for onboarding topics using topic-driven architecture.

    Migrated to unified topic-driven architecture.
    Uses 'onboarding_coaching' topic.
    """
    logger.info("Providing onboarding coaching", user_id=user.user_id, topic=request.topic)

    return cast(
        OnboardingCoachingResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/onboarding",
            request_body=request,
            user_context=user,
            response_model=OnboardingCoachingResponse,
        ),
    )


@router.post(
    "/alignment-check",
    response_model=AlignmentAnalysisResponse,
    status_code=status.HTTP_200_OK,
)
async def check_alignment(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> AlignmentAnalysisResponse:
    """Check alignment using topic-driven architecture.

    Uses 'alignment_check' topic.
    """
    logger.info("Checking alignment", user_id=user.user_id)

    return cast(
        AlignmentAnalysisResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/alignment-check",
            request_body=request,
            user_context=user,
            response_model=AlignmentAnalysisResponse,
        ),
    )


@router.post(
    "/alignment-explanation",
    response_model=AlignmentExplanationResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_explanation(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> AlignmentExplanationResponse:
    """Generate AI-powered alignment explanation using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'alignment_explanation' topic for consistent prompt management.
    """
    logger.info("Generating alignment explanation", user_id=user.user_id)

    return cast(
        AlignmentExplanationResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/alignment-explanation",
            request_body=request,
            user_context=user,
            response_model=AlignmentExplanationResponse,
        ),
    )


@router.post(
    "/alignment-suggestions",
    response_model=AlignmentSuggestionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_alignment_suggestions(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> AlignmentSuggestionsResponse:
    """Generate AI-powered alignment suggestions using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'alignment_suggestions' topic for consistent prompt management.
    """
    logger.info("Generating alignment suggestions", user_id=user.user_id)

    return cast(
        AlignmentSuggestionsResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/alignment-suggestions",
            request_body=request,
            user_context=user,
            response_model=AlignmentSuggestionsResponse,
        ),
    )


@router.post(
    "/kpi-recommendations",
    response_model=KPIRecommendationsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_kpi_recommendations(
    request: KPIRecommendationsRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> KPIRecommendationsResponse:
    """Generate KPI recommendations using topic-driven architecture.

    Uses 'kpi_recommendations' topic.
    """
    logger.info("Generating KPI recommendations", user_id=user.user_id)

    return cast(
        KPIRecommendationsResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/kpi-recommendations",
            request_body=request,
            user_context=user,
            response_model=KPIRecommendationsResponse,
        ),
    )


@router.post(
    "/strategy-suggestions",
    response_model=ApiResponse[StrategySuggestionsResponse],
    status_code=status.HTTP_200_OK,
)
async def get_strategy_suggestions(
    request: StrategySuggestionsRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> ApiResponse[StrategySuggestionsResponse]:
    """Get AI-generated strategy recommendations using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'strategy_suggestions' topic for consistent prompt management.

    Generates strategy suggestions based on goal intent, business context, and constraints
    using the UnifiedAIEngine with prompts stored in S3.
    """
    logger.info(
        "Generating strategy suggestions",
        user_id=user.user_id,
        goal_intent=request.goal_intent[:100],
    )

    # Use generic handler with direct response model
    response_data = cast(
        StrategySuggestionsResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/strategy-suggestions",
            request_body=request,
            user_context=user,
            response_model=StrategySuggestionsResponse,
        ),
    )

    logger.info(
        "Strategy suggestions generated successfully",
        user_id=user.user_id,
        suggestion_count=len(response_data.suggestions),
    )

    return ApiResponse(success=True, data=response_data)


__all__ = ["router"]
