"""Operations AI API routes - migrated to topic-driven architecture (Issue #113).

================================================================================
DEPRECATED - This entire file is dead code.
================================================================================
Migration: These endpoints were designed for Phase 2 but never integrated with frontend.
Usage: No frontend callers exist.
Status: Safe to remove.
================================================================================

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

from typing import cast

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies.ai_engine import (
    create_template_processor,
    get_generic_handler,
    get_jwt_token,
)
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.operations import (
    ActionPlanRequest,
    ActionPlanResponse,
    OptimizedActionPlanResponse,
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
    jwt_token: str | None = Depends(get_jwt_token),
) -> StrategicAlignmentResponse:
    """Analyze strategic alignment using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'strategic_alignment' topic for consistent prompt management.
    """
    logger.info(
        "Analyzing strategic alignment", user_id=user.user_id, action_count=len(request.actions)
    )

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        StrategicAlignmentResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/operations/strategic-alignment",
            request_body=request,
            user_context=user,
            response_model=StrategicAlignmentResponse,
            template_processor=template_processor,
        ),
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
    jwt_token: str | None = Depends(get_jwt_token),
) -> PrioritizationResponse:
    """Generate prioritization suggestions using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'prioritization_suggestions' topic for consistent prompt management.
    """
    logger.info(
        "Generating prioritization", user_id=user.user_id, action_count=len(request.actions)
    )

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        PrioritizationResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/operations/prioritization-suggestions",
            request_body=request,
            user_context=user,
            response_model=PrioritizationResponse,
            template_processor=template_processor,
        ),
    )


@router.post(
    "/scheduling-suggestions", response_model=SchedulingResponse, status_code=status.HTTP_200_OK
)
async def suggest_scheduling(
    request: SchedulingRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
    jwt_token: str | None = Depends(get_jwt_token),
) -> SchedulingResponse:
    """Generate scheduling suggestions using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'scheduling_suggestions' topic for consistent prompt management.
    """
    logger.info("Generating scheduling", user_id=user.user_id, action_count=len(request.actions))

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        SchedulingResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/operations/scheduling-suggestions",
            request_body=request,
            user_context=user,
            response_model=SchedulingResponse,
            template_processor=template_processor,
        ),
    )


@router.post(
    "/root-cause-suggestions", response_model=RootCauseResponse, status_code=status.HTTP_200_OK
)
async def suggest_root_cause_methods(
    request: RootCauseRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
    jwt_token: str | None = Depends(get_jwt_token),
) -> RootCauseResponse:
    """Suggest root cause methods using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'root_cause_suggestions' topic for consistent prompt management.
    """
    logger.info(
        "Suggesting root cause methods", user_id=user.user_id, issue_title=request.issue_title
    )

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        RootCauseResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/operations/root-cause-suggestions",
            request_body=request,
            user_context=user,
            response_model=RootCauseResponse,
            template_processor=template_processor,
        ),
    )


@router.post(
    "/action-suggestions", response_model=ActionPlanResponse, status_code=status.HTTP_200_OK
)
async def generate_action_plan(
    request: ActionPlanRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
    jwt_token: str | None = Depends(get_jwt_token),
) -> ActionPlanResponse:
    """Generate action plan using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'action_suggestions' topic for consistent prompt management.
    """
    logger.info("Generating action plan", user_id=user.user_id, issue_title=request.issue.title)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        ActionPlanResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/operations/action-suggestions",
            request_body=request,
            user_context=user,
            response_model=ActionPlanResponse,
            template_processor=template_processor,
        ),
    )


@router.post(
    "/optimize-action-plan",
    response_model=OptimizedActionPlanResponse,
    status_code=status.HTTP_200_OK,
)
async def optimize_action_plan(
    request: ActionPlanRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
    jwt_token: str | None = Depends(get_jwt_token),
) -> OptimizedActionPlanResponse:
    """Optimize action plan using topic-driven architecture.

    Uses 'optimize_action_plan' topic.
    """
    logger.info("Optimizing action plan", user_id=user.user_id, issue_title=request.issue.title)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    return cast(
        OptimizedActionPlanResponse,
        await handler.handle_single_shot(
            http_method="POST",
            endpoint_path="/operations/optimize-action-plan",
            request_body=request,
            user_context=user,
            response_model=OptimizedActionPlanResponse,
            template_processor=template_processor,
        ),
    )


__all__ = ["router"]
