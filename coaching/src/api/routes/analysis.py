"""Analysis API routes for business coaching (Phase 7).

This module provides REST API endpoints for various analysis types:
- Alignment analysis (goals vs purpose/values)
- Strategy analysis (effectiveness and recommendations)
- KPI analysis (metric effectiveness)
- Operational analysis (SWOT, root cause, action plans)
"""

from datetime import datetime

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies_v2 import (
    get_alignment_service,
    get_kpi_service,
    get_strategy_service,
)
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
from coaching.src.api.models.auth import UserContext
from coaching.src.application.analysis.alignment_service import AlignmentAnalysisService
from coaching.src.application.analysis.kpi_service import KPIAnalysisService
from coaching.src.application.analysis.strategy_service import StrategyAnalysisService
from coaching.src.core.constants import AnalysisType
from coaching.src.core.types import AnalysisRequestId, TenantId, UserId
from fastapi import APIRouter, Depends, HTTPException, status

logger = structlog.get_logger()
router = APIRouter(prefix="/analysis", tags=["analysis"])


# Alignment Analysis Routes


@router.post("/alignment", response_model=AlignmentAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_alignment(
    request: AlignmentAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
) -> AlignmentAnalysisResponse:
    """Analyze alignment between goals/actions and purpose/values.

    This endpoint analyzes how well the provided text (goals, actions, plans)
    aligns with the user's stated purpose and core values.

    **Authentication**: Bearer token required

    Args:
        request: Alignment analysis request with text and context
        user: Authenticated user context
        alignment_service: Alignment analysis service

    Returns:
        AlignmentAnalysisResponse with scores and recommendations

    Raises:
        HTTPException 400: If request is invalid
        HTTPException 500: If analysis fails
    """
    try:
        logger.info(
            "Starting alignment analysis",
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            text_length=len(request.text_to_analyze),
        )

        # Prepare analysis context
        analysis_context = {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "current_actions": request.text_to_analyze,
            **request.context,
        }

        # Perform analysis
        result = await alignment_service.analyze(analysis_context)

        logger.info(
            "Alignment analysis completed",
            user_id=user.user_id,
            overall_score=result.get("alignment_score", 0),
        )

        # Build response
        return AlignmentAnalysisResponse(
            analysis_id=AnalysisRequestId(f"anls_{datetime.utcnow().timestamp()}"),
            analysis_type=AnalysisType.ALIGNMENT,
            scores=AlignmentScore(
                overall_score=result.get("alignment_score", 0.0),
                purpose_alignment=result.get("purpose_alignment", 0.0),
                values_alignment=result.get("values_alignment", 0.0),
                goal_clarity=result.get("goal_clarity", 0.0),
            ),
            overall_assessment=result.get("overall_assessment", "Analysis complete"),
            strengths=result.get("strengths", []),
            misalignments=result.get("misalignments", []),
            recommendations=result.get("recommendations", []),
            created_at=datetime.utcnow(),
            metadata={
                "user_id": user.user_id,
                "tenant_id": user.tenant_id,
                "analysis_version": "1.0",
            },
        )

    except ValueError as e:
        logger.warning(
            "Invalid alignment analysis request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Alignment analysis failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform alignment analysis",
        ) from e


# Strategy Analysis Routes


@router.post("/strategy", response_model=StrategyAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_strategy(
    request: StrategyAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    strategy_service: StrategyAnalysisService = Depends(get_strategy_service),
) -> StrategyAnalysisResponse:
    """Analyze business strategy effectiveness.

    This endpoint evaluates the provided strategy and provides recommendations
    for improvement based on best practices and the user's context.

    **Authentication**: Bearer token required

    Args:
        request: Strategy analysis request
        user: Authenticated user context
        strategy_service: Strategy analysis service

    Returns:
        StrategyAnalysisResponse with assessment and recommendations

    Raises:
        HTTPException 400: If request is invalid
        HTTPException 500: If analysis fails
    """
    try:
        logger.info(
            "Starting strategy analysis",
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            strategy_length=len(request.current_strategy),
        )

        # Prepare analysis context
        analysis_context = {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "current_strategy": request.current_strategy,
            **request.context,
        }

        # Perform analysis
        result = await strategy_service.analyze(analysis_context)

        logger.info(
            "Strategy analysis completed",
            user_id=user.user_id,
            effectiveness_score=result.get("effectiveness_score", 0),
        )

        # Build recommendations
        recommendations = []
        for rec in result.get("recommendations", []):
            recommendations.append(
                StrategyRecommendation(
                    category=rec.get("category", "General"),
                    recommendation=rec.get("recommendation", ""),
                    priority=rec.get("priority", "medium"),
                    rationale=rec.get("rationale", ""),
                    estimated_impact=rec.get("estimated_impact", "To be determined"),
                )
            )

        # Build response
        return StrategyAnalysisResponse(
            analysis_id=AnalysisRequestId(f"anls_{datetime.utcnow().timestamp()}"),
            analysis_type=AnalysisType.STRATEGY,
            effectiveness_score=result.get("effectiveness_score", 0.0),
            overall_assessment=result.get("overall_assessment", "Analysis complete"),
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            opportunities=result.get("opportunities", []),
            recommendations=recommendations,
            created_at=datetime.utcnow(),
            metadata={
                "user_id": user.user_id,
                "tenant_id": user.tenant_id,
                "analysis_version": "1.0",
            },
        )

    except ValueError as e:
        logger.warning(
            "Invalid strategy analysis request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Strategy analysis failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform strategy analysis",
        ) from e


# KPI Analysis Routes


@router.post("/kpi", response_model=KPIAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_kpis(
    request: KPIAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    kpi_service: KPIAnalysisService = Depends(get_kpi_service),
) -> KPIAnalysisResponse:
    """Analyze KPI effectiveness and provide recommendations.

    This endpoint evaluates the user's current KPIs and suggests improvements
    or additional metrics based on business goals and industry best practices.

    **Authentication**: Bearer token required

    Args:
        request: KPI analysis request
        user: Authenticated user context
        kpi_service: KPI analysis service

    Returns:
        KPIAnalysisResponse with analysis and recommendations

    Raises:
        HTTPException 400: If request is invalid
        HTTPException 500: If analysis fails
    """
    try:
        logger.info(
            "Starting KPI analysis",
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            kpi_count=len(request.current_kpis),
        )

        # Prepare analysis context
        analysis_context = {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "current_kpis": request.current_kpis,
            **request.context,
        }

        # Perform analysis
        result = await kpi_service.analyze(analysis_context)

        logger.info(
            "KPI analysis completed",
            user_id=user.user_id,
            effectiveness_score=result.get("kpi_effectiveness_score", 0),
        )

        # Build recommended KPIs
        recommended_kpis = []
        for kpi in result.get("recommended_kpis", []):
            recommended_kpis.append(
                KPIRecommendation(
                    kpi_name=kpi.get("kpi_name", ""),
                    description=kpi.get("description", ""),
                    rationale=kpi.get("rationale", ""),
                    target_range=kpi.get("target_range"),
                    measurement_frequency=kpi.get("measurement_frequency", "monthly"),
                )
            )

        # Build response
        return KPIAnalysisResponse(
            analysis_id=AnalysisRequestId(f"anls_{datetime.utcnow().timestamp()}"),
            analysis_type=AnalysisType.KPI,
            kpi_effectiveness_score=result.get("kpi_effectiveness_score", 0.0),
            overall_assessment=result.get("overall_assessment", "Analysis complete"),
            current_kpi_analysis=result.get("current_kpi_analysis", []),
            missing_kpis=result.get("missing_kpis", []),
            recommended_kpis=recommended_kpis,
            created_at=datetime.utcnow(),
            metadata={
                "user_id": user.user_id,
                "tenant_id": user.tenant_id,
                "analysis_version": "1.0",
            },
        )

    except ValueError as e:
        logger.warning(
            "Invalid KPI analysis request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "KPI analysis failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform KPI analysis",
        ) from e


# Operational Analysis Routes


@router.post("/operations", response_model=OperationsAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def analyze_operations(
    request: OperationsAnalysisRequest,
    user: UserContext = Depends(get_current_user),
    # Note: Operations analysis might use different services based on type
    alignment_service: AlignmentAnalysisService = Depends(get_alignment_service),
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
        alignment_service: Analysis service (placeholder, would use appropriate service)

    Returns:
        OperationsAnalysisResponse with findings and recommendations

    Raises:
        HTTPException 400: If request is invalid or analysis type not supported
        HTTPException 500: If analysis fails
    """
    try:
        logger.info(
            "Starting operations analysis",
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            analysis_type=request.analysis_type,
        )

        # Prepare analysis context
        analysis_context = {
            "user_id": user.user_id,
            "tenant_id": user.tenant_id,
            "analysis_type": request.analysis_type,
            "description": request.description,
            **request.context,
        }

        # TODO: Route to appropriate service based on analysis_type
        # For now, using a placeholder implementation
        
        # Simulate SWOT analysis
        if request.analysis_type == "swot":
            findings = {
                "strengths": ["Clear vision", "Dedicated team"],
                "weaknesses": ["Limited budget", "Market competition"],
                "opportunities": ["Growing market segment", "Strategic partnerships"],
                "threats": ["Economic uncertainty", "Regulatory changes"],
            }
        elif request.analysis_type == "root_cause":
            findings = {
                "problem": request.description,
                "root_causes": ["Insufficient process documentation", "Communication gaps"],
                "contributing_factors": ["High workload", "Tool limitations"],
            }
        elif request.analysis_type == "action_plan":
            findings = {
                "goal": request.description,
                "action_items": [
                    {"action": "Define clear objectives", "timeline": "Week 1", "owner": "Leadership"},
                    {"action": "Gather stakeholder input", "timeline": "Week 2", "owner": "Team"},
                ],
            }
        else:
            raise ValueError(f"Unsupported analysis type: {request.analysis_type}")

        logger.info(
            "Operations analysis completed",
            user_id=user.user_id,
            analysis_type=request.analysis_type,
        )

        # Build response
        return OperationsAnalysisResponse(
            analysis_id=AnalysisRequestId(f"anls_{datetime.utcnow().timestamp()}"),
            analysis_type=AnalysisType.OPERATIONS,
            specific_analysis_type=request.analysis_type,
            findings=findings,
            recommendations=[
                {
                    "action": "Review findings with team",
                    "priority": "high",
                    "timeline": "Within 1 week",
                },
            ],
            priority_actions=["Address critical gaps first", "Build on existing strengths"],
            created_at=datetime.utcnow(),
            metadata={
                "user_id": user.user_id,
                "tenant_id": user.tenant_id,
                "analysis_version": "1.0",
            },
        )

    except ValueError as e:
        logger.warning(
            "Invalid operations analysis request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Operations analysis failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform operations analysis",
        ) from e


__all__ = ["router"]
