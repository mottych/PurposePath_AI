from __future__ import annotations

from typing import cast

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies.ai_engine import (
    create_template_processor,
    get_generic_handler,
    get_jwt_token,
)
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.onboarding import (
    OnboardingSuggestionRequest,
    OnboardingSuggestionResponse,
)
from fastapi import APIRouter, Depends
from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.post("/onboarding", response_model=ApiResponse[OnboardingSuggestionResponse])
async def suggest_onboarding(
    request: OnboardingSuggestionRequest,
    context: RequestContext = Depends(get_current_context),
    handler: GenericAIHandler = Depends(get_generic_handler),
    jwt_token: str | None = Depends(get_jwt_token),
) -> ApiResponse[OnboardingSuggestionResponse]:
    """Generate onboarding suggestions based on user input.

    Migrated to unified topic-driven architecture.
    Uses 'onboarding_suggestions' topic.

    Args:
        request: Request containing suggestion type and current value
        context: Authenticated request context
        handler: Generic AI handler

    Returns:
        ApiResponse containing suggestion text
    """
    logger.info("Generating onboarding suggestions", user_id=context.user_id, kind=request.kind)

    # Convert RequestContext to UserContext for handler
    user_context = UserContext(user_id=context.user_id, tenant_id=context.tenant_id)

    template_processor = create_template_processor(jwt_token) if jwt_token else None

    result = await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/suggestions/onboarding",
        request_body=request,
        user_context=user_context,
        response_model=OnboardingSuggestionResponse,
        template_processor=template_processor,
    )

    return ApiResponse(success=True, data=cast(OnboardingSuggestionResponse, result))
