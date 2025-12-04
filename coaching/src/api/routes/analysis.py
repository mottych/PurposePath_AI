"""Analysis API routes for business coaching (Phase 7).

This module provides REST API endpoints for various analysis types:
- Alignment analysis (goals vs purpose/values)
- Strategy analysis (effectiveness and recommendations)
- KPI analysis (metric effectiveness)
- Operational analysis (SWOT, root cause, action plans)
"""

from typing import cast

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.analysis import (
    AlignmentAnalysisRequest,
    AlignmentAnalysisResponse,
    KPIAnalysisRequest,
    KPIAnalysisResponse,
    OperationsAnalysisRequest,
    OperationsAnalysisResponse,
    StrategyAnalysisRequest,
    StrategyAnalysisResponse,
)
from coaching.src.api.models.auth import UserContext
from fastapi import APIRouter, Depends, status

logger = structlog.get_logger()
router = APIRouter(prefix="/analysis", tags=["analysis"])


# Alignment Analysis Routes


@router.post("/alignment", response_model=AlignmentAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_alignment(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> AlignmentAnalysisResponse:
    """Analyze alignment between goals/actions and purpose/values.

    This endpoint analyzes how well the provided text (goals, actions, plans)
    aligns with the user's stated purpose and core values.

    **Authentication**: Bearer token required

    Args:
        request: Alignment analysis request with text and context
        user: Authenticated user context
        handler: Generic AI handler

    Returns:
        AlignmentAnalysisResponse with scores and recommendations
    """
    logger.info(
        "Starting alignment analysis",
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        text_length=len(request.text_to_analyze),
    )

    return cast(
        AlignmentAnalysisResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/analysis/alignment",
            request_body=request,
            user_context=user,
            response_model=AlignmentAnalysisResponse,
        ),
    )


# Strategy Analysis Routes


@router.post("/strategy", response_model=StrategyAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_strategy(
    request: StrategyAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> StrategyAnalysisResponse:
    """Analyze business strategy effectiveness.

    This endpoint evaluates the provided strategy and provides recommendations
    for improvement based on best practices and the user's context.

    **Authentication**: Bearer token required

    Args:
        request: Strategy analysis request
        user: Authenticated user context
        handler: Generic AI handler

    Returns:
        StrategyAnalysisResponse with assessment and recommendations
    """
    logger.info(
        "Starting strategy analysis",
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        strategy_length=len(request.current_strategy),
    )

    return cast(
        StrategyAnalysisResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/analysis/strategy",
            request_body=request,
            user_context=user,
            response_model=StrategyAnalysisResponse,
        ),
    )


# KPI Analysis Routes


@router.post("/kpi", response_model=KPIAnalysisResponse, status_code=status.HTTP_200_OK)
async def analyze_kpis(
    request: KPIAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> KPIAnalysisResponse:
    """Analyze KPI effectiveness and provide recommendations.

    This endpoint evaluates the user's current KPIs and suggests improvements
    or additional metrics based on business goals and industry best practices.

    **Authentication**: Bearer token required

    Args:
        request: KPI analysis request
        user: Authenticated user context
        handler: Generic AI handler

    Returns:
        KPIAnalysisResponse with analysis and recommendations
    """
    logger.info(
        "Starting KPI analysis",
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        kpi_count=len(request.current_kpis),
    )

    return cast(
        KPIAnalysisResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/analysis/kpi",
            request_body=request,
            user_context=user,
            response_model=KPIAnalysisResponse,
        ),
    )


# Operational Analysis Routes


@router.post(
    "/operations", response_model=OperationsAnalysisResponse, status_code=status.HTTP_200_OK
)
async def analyze_operations(
    request: OperationsAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> OperationsAnalysisResponse:
    """Perform operational analysis (SWOT, root cause, action plan).

    This endpoint provides various operational analysis types to help with
    business decision-making and problem-solving.

    **Authentication**: Bearer token required

    **Analysis Types**:
    - `swot`: SWOT analysis (Strengths, Weaknesses, Opportunities, Threats)
    - `root_cause`: Root cause analysis for problems
    - `action_plan`: Action plan generation

    Args:
        request: Operations analysis request
        user: Authenticated user context
        handler: Generic AI handler

    Returns:
        OperationsAnalysisResponse with findings and recommendations
    """
    logger.info(
        "Starting operations analysis",
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        analysis_type=request.analysis_type,
    )

    return cast(
        OperationsAnalysisResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/analysis/operations",
            request_body=request,
            user_context=user,
            response_model=OperationsAnalysisResponse,
        ),
    )


__all__ = ["router"]
