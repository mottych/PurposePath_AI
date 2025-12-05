from __future__ import annotations

from typing import cast

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.onboarding import (
    OnboardingSuggestionRequest,
    OnboardingSuggestionResponse,
)
from fastapi import APIRouter, Depends
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post("/onboarding", response_model=ApiResponse[OnboardingSuggestionResponse])
async def suggest_onboarding(
    request: OnboardingSuggestionRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> ApiResponse[OnboardingSuggestionResponse]:
    """Generate onboarding suggestions based on user input.

    Migrated to unified topic-driven architecture.
    Uses 'onboarding_suggestions' topic.

    Args:
        request: Request containing suggestion type and current value
        user: Authenticated user context
        handler: Generic AI handler

    Returns:
        ApiResponse containing suggestion text
    """
    logger.info("Generating onboarding suggestions", user_id=user.user_id, kind=request.kind)

    result = await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/suggestions/onboarding",
        request_body=request,
        user_context=user,
        response_model=OnboardingSuggestionResponse,
    )

    return ApiResponse(success=True, data=cast(OnboardingSuggestionResponse, result))
