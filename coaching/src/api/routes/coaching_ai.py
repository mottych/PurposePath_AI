"""Coaching AI API routes - migrated to topic-driven architecture (Issue #113).

================================================================================
DEPRECATED - This entire file is dead code.
================================================================================
Migration: These endpoints were designed for Phase 2 but never integrated with frontend.
Usage: No frontend callers exist.
Status: Safe to remove.
================================================================================

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
from coaching.src.api.dependencies.ai_engine import (
    create_template_processor,
    get_generic_handler,
    get_jwt_token,
)
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
    AlignmentExplanationResponse,
    AlignmentSuggestionsResponse,
    MeasureRecommendationsRequest,
    MeasureRecommendationsResponse,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.onboarding import (
    OnboardingCoachingRequest,
    OnboardingCoachingResponse,
)
from coaching.src.api.models.strategic_planning import (
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
    jwt_token: str | None = Depends(get_jwt_token),
) -> OnboardingCoachingResponse:
    """Get AI coaching assistance for onboarding topics using topic-driven architecture.

    Migrated to unified topic-driven architecture.
    Uses 'onboarding_coaching' topic.
    """
    logger.info("Providing onboarding coaching", user_id=user.user_id, topic=request.topic)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        OnboardingCoachingResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/onboarding",
            request_body=request,
            user_context=user,
            response_model=OnboardingCoachingResponse,
            template_processor=template_processor,
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
    jwt_token: str | None = Depends(get_jwt_token),
) -> AlignmentAnalysisResponse:
    """Check alignment using topic-driven architecture.

    Uses 'alignment_check' topic.
    """
    logger.info("Checking alignment", user_id=user.user_id)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        AlignmentAnalysisResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/alignment-check",
            request_body=request,
            user_context=user,
            response_model=AlignmentAnalysisResponse,
            template_processor=template_processor,
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
    jwt_token: str | None = Depends(get_jwt_token),
) -> AlignmentExplanationResponse:
    """Generate AI-powered alignment explanation using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'alignment_explanation' topic for consistent prompt management.
    """
    logger.info("Generating alignment explanation", user_id=user.user_id)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        AlignmentExplanationResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/alignment-explanation",
            request_body=request,
            user_context=user,
            response_model=AlignmentExplanationResponse,
            template_processor=template_processor,
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
    jwt_token: str | None = Depends(get_jwt_token),
) -> AlignmentSuggestionsResponse:
    """Generate AI-powered alignment suggestions using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'alignment_suggestions' topic for consistent prompt management.
    """
    logger.info("Generating alignment suggestions", user_id=user.user_id)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        AlignmentSuggestionsResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/alignment-suggestions",
            request_body=request,
            user_context=user,
            response_model=AlignmentSuggestionsResponse,
            template_processor=template_processor,
        ),
    )


@router.post(
    "/kpi-recommendations",
    response_model=MeasureRecommendationsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_kpi_recommendations(
    request: MeasureRecommendationsRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
    jwt_token: str | None = Depends(get_jwt_token),
) -> MeasureRecommendationsResponse:
    """Generate Measure recommendations using topic-driven architecture.

    Uses 'kpi_recommendations' topic.
    """
    logger.info("Generating KPI recommendations", user_id=user.user_id)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        MeasureRecommendationsResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/kpi-recommendations",
            request_body=request,
            user_context=user,
            response_model=MeasureRecommendationsResponse,
            template_processor=template_processor,
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
    jwt_token: str | None = Depends(get_jwt_token),
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
        goal_intent=request.goal_intent[:100] if request.goal_intent else None,
    )

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    # Use generic handler with direct response model
    response_data = cast(
        StrategySuggestionsResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/coaching/strategy-suggestions",
            request_body=request,
            user_context=user,
            response_model=StrategySuggestionsResponse,
            template_processor=template_processor,
        ),
    )

    logger.info(
        "Strategy suggestions generated successfully",
        user_id=user.user_id,
        suggestion_count=len(response_data.suggestions),
    )

    return ApiResponse(success=True, data=response_data)


__all__ = ["router"]
