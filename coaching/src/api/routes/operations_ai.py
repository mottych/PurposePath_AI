"""Operations AI API routes for strategic planning (Issues #63 & #64)."""

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.operations import (
    ActionPlanRequest,
    ActionPlanResponse,
    PrioritizationRequest,
    PrioritizationResponse,
    RootCauseRequest,
    RootCauseResponse,
    SchedulingRequest,
    SchedulingResponse,
    StrategicAlignmentRequest,
    StrategicAlignmentResponse,
)
from coaching.src.application.analysis.operations_ai_service import OperationsAIService
from coaching.src.application.llm.llm_service import LLMApplicationService
from coaching.src.core.config_multitenant import settings
from coaching.src.infrastructure.llm.bedrock_provider import BedrockLLMProvider
from fastapi import APIRouter, Depends, HTTPException, status

from shared.services.aws_helpers import get_bedrock_client

logger = structlog.get_logger()
router = APIRouter(prefix="/operations", tags=["operations", "ai"])


async def get_operations_ai_service() -> OperationsAIService:
    """Get Operations AI service with LLM integration."""
    bedrock_client = get_bedrock_client(settings.bedrock_region)
    bedrock_provider = BedrockLLMProvider(
        bedrock_client=bedrock_client,
        region=settings.bedrock_region,
    )
    llm_service = LLMApplicationService(llm_provider=bedrock_provider)
    return OperationsAIService(llm_service=llm_service)


@router.post(
    "/strategic-alignment",
    response_model=StrategicAlignmentResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_strategic_alignment(
    request: StrategicAlignmentRequest,
    user: UserContext = Depends(get_current_user),
    operations_service: OperationsAIService = Depends(get_operations_ai_service),
) -> StrategicAlignmentResponse:
    """Analyze strategic alignment between actions and business goals."""
    try:
        logger.info(
            "Analyzing strategic alignment", user_id=user.user_id, action_count=len(request.actions)
        )
        actions = [action.model_dump() for action in request.actions]
        goals = [goal.model_dump() for goal in request.goals]
        business_foundation = request.business_foundation.model_dump()
        analysis = await operations_service.analyze_strategic_alignment(
            actions, goals, business_foundation
        )
        return StrategicAlignmentResponse(success=True, data=analysis)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Strategic alignment failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate analysis"
        ) from e


@router.post(
    "/prioritization-suggestions",
    response_model=PrioritizationResponse,
    status_code=status.HTTP_200_OK,
)
async def suggest_prioritization(
    request: PrioritizationRequest,
    user: UserContext = Depends(get_current_user),
    operations_service: OperationsAIService = Depends(get_operations_ai_service),
) -> PrioritizationResponse:
    """Generate AI-powered action prioritization suggestions."""
    try:
        logger.info(
            "Generating prioritization", user_id=user.user_id, action_count=len(request.actions)
        )
        actions = [action.model_dump() for action in request.actions]
        business_context = request.businessContext.model_dump()
        suggestions = await operations_service.suggest_prioritization(actions, business_context)
        return PrioritizationResponse(success=True, data=suggestions)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Prioritization failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


@router.post(
    "/scheduling-suggestions", response_model=SchedulingResponse, status_code=status.HTTP_200_OK
)
async def suggest_scheduling(
    request: SchedulingRequest,
    user: UserContext = Depends(get_current_user),
    operations_service: OperationsAIService = Depends(get_operations_ai_service),
) -> SchedulingResponse:
    """Generate optimized scheduling suggestions for actions."""
    try:
        logger.info(
            "Generating scheduling", user_id=user.user_id, action_count=len(request.actions)
        )
        actions = [action.model_dump() for action in request.actions]
        constraints = request.constraints.model_dump()
        schedules = await operations_service.optimize_scheduling(actions, constraints)
        return SchedulingResponse(success=True, data=schedules)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Scheduling failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


@router.post(
    "/root-cause-suggestions", response_model=RootCauseResponse, status_code=status.HTTP_200_OK
)
async def suggest_root_cause_methods(
    request: RootCauseRequest,
    user: UserContext = Depends(get_current_user),
    operations_service: OperationsAIService = Depends(get_operations_ai_service),
) -> RootCauseResponse:
    """Suggest root cause analysis methods with AI guidance (Issue #64)."""
    try:
        logger.info(
            "Suggesting root cause methods", user_id=user.user_id, issue_title=request.issueTitle
        )
        issue = request.model_dump(exclude={"context"})
        context = request.context.model_dump()
        suggestions = await operations_service.suggest_root_cause_methods(issue, context)
        return RootCauseResponse(success=True, data=suggestions)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Root cause suggestions failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


@router.post(
    "/action-suggestions", response_model=ActionPlanResponse, status_code=status.HTTP_200_OK
)
async def generate_action_plan(
    request: ActionPlanRequest,
    user: UserContext = Depends(get_current_user),
    operations_service: OperationsAIService = Depends(get_operations_ai_service),
) -> ActionPlanResponse:
    """Generate AI-powered action plan to address an issue (Issue #64)."""
    try:
        logger.info("Generating action plan", user_id=user.user_id, issue_title=request.issue.title)
        issue = request.issue.model_dump()
        constraints = request.constraints.model_dump()
        context = request.context.model_dump()
        actions = await operations_service.generate_action_plan(issue, constraints, context)
        return ActionPlanResponse(success=True, data=actions)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except Exception as e:
        logger.error("Action plan failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate action plan",
        ) from e


__all__ = ["router"]
