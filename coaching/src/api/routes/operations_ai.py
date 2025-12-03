"""Operations AI API routes - migrated to topic-driven architecture (Issue #113).

This module provides AI-powered operations endpoints using the unified
topic-driven architecture. All endpoints now route through GenericAIHandler
which uses UnifiedAIEngine for consistent prompt management and AI processing.

Migration Status:
- strategic-alignment: Migrated to topic-driven (strategic_alignment topic)
- prioritization-suggestions: Migrated to topic-driven (prioritization_suggestions topic)
- scheduling-suggestions: Migrated to topic-driven (scheduling_suggestions topic)
- root-cause-suggestions: Migrated to topic-driven (root_cause_suggestions topic)
- action-suggestions: Migrated to topic-driven (action_suggestions topic)
"""

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
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
from fastapi import APIRouter, Depends, status

logger = structlog.get_logger()
router = APIRouter(prefix="/operations", tags=["operations", "ai"])


@router.post(
    "/strategic-alignment",
    response_model=StrategicAlignmentResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_strategic_alignment(
    request: StrategicAlignmentRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> StrategicAlignmentResponse:
    """Analyze strategic alignment using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'strategic_alignment' topic for consistent prompt management.
    """
    logger.info(
        "Analyzing strategic alignment", user_id=user.user_id, action_count=len(request.actions)
    )

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/operations/strategic-alignment",
        request_body=request,
        user_context=user,
        response_model=StrategicAlignmentResponse,
    )


@router.post(
    "/prioritization-suggestions",
    response_model=PrioritizationResponse,
    status_code=status.HTTP_200_OK,
)
async def suggest_prioritization(
    request: PrioritizationRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> PrioritizationResponse:
    """Generate prioritization suggestions using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'prioritization_suggestions' topic for consistent prompt management.
    """
    logger.info(
        "Generating prioritization", user_id=user.user_id, action_count=len(request.actions)
    )

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/operations/prioritization-suggestions",
        request_body=request,
        user_context=user,
        response_model=PrioritizationResponse,
    )


@router.post(
    "/scheduling-suggestions", response_model=SchedulingResponse, status_code=status.HTTP_200_OK
)
async def suggest_scheduling(
    request: SchedulingRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> SchedulingResponse:
    """Generate scheduling suggestions using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'scheduling_suggestions' topic for consistent prompt management.
    """
    logger.info("Generating scheduling", user_id=user.user_id, action_count=len(request.actions))

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/operations/scheduling-suggestions",
        request_body=request,
        user_context=user,
        response_model=SchedulingResponse,
    )


@router.post(
    "/root-cause-suggestions", response_model=RootCauseResponse, status_code=status.HTTP_200_OK
)
async def suggest_root_cause_methods(
    request: RootCauseRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> RootCauseResponse:
    """Suggest root cause methods using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'root_cause_suggestions' topic for consistent prompt management.
    """
    logger.info(
        "Suggesting root cause methods", user_id=user.user_id, issue_title=request.issue_title
    )

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/operations/root-cause-suggestions",
        request_body=request,
        user_context=user,
        response_model=RootCauseResponse,
    )


@router.post(
    "/action-suggestions", response_model=ActionPlanResponse, status_code=status.HTTP_200_OK
)
async def generate_action_plan(
    request: ActionPlanRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> ActionPlanResponse:
    """Generate action plan using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'action_suggestions' topic for consistent prompt management.
    """
    logger.info("Generating action plan", user_id=user.user_id, issue_title=request.issue.title)

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/operations/action-suggestions",
        request_body=request,
        user_context=user,
        response_model=ActionPlanResponse,
    )


__all__ = ["router"]
