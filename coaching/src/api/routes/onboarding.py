"""Onboarding AI API routes - migrated to topic-driven architecture (Issue #113).

This module provides AI-powered onboarding endpoints using the unified
topic-driven architecture. All endpoints now route through GenericAIHandler
which uses UnifiedAIEngine for consistent prompt management and AI processing.

Migration Status:
- suggestions/onboarding: Migrated to topic-driven (onboarding_suggestions topic)
- website/scan: Migrated to topic-driven (website_scan topic)
- coaching/onboarding: Migrated to topic-driven (onboarding_coaching topic)
"""

import structlog
from coaching.src.api.auth import get_current_user
from coaching.src.api.dependencies.ai_engine import get_generic_handler
from coaching.src.api.handlers.generic_ai_handler import GenericAIHandler
from coaching.src.api.models.auth import UserContext
from coaching.src.api.models.onboarding import (
    OnboardingCoachingRequest,
    OnboardingCoachingResponse,
    OnboardingSuggestionRequest,
    OnboardingSuggestionResponse,
    WebsiteScanRequest,
    WebsiteScanResponse,
)
from fastapi import APIRouter, Depends, status

logger = structlog.get_logger()
router = APIRouter(tags=["onboarding", "ai"])


@router.post(
    "/api/coaching/suggestions/onboarding",
    response_model=OnboardingSuggestionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_onboarding_suggestions(
    request: OnboardingSuggestionRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> OnboardingSuggestionResponse:
    """Get AI suggestions for onboarding fields using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'onboarding_suggestions' topic for consistent prompt management.

    Provides intelligent suggestions for niche, ICA, or value proposition
    based on business context.
    """
    logger.info("Generating onboarding suggestions", user_id=user.user_id, kind=request.kind)

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/suggestions/onboarding",
        request_body=request,
        user_context=user,
        response_model=OnboardingSuggestionResponse,
    )


@router.post(
    "/api/coaching/website/scan",
    response_model=WebsiteScanResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_website(
    request: WebsiteScanRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> WebsiteScanResponse:
    """Scan website to extract business information using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'website_scan' topic for consistent prompt management.

    Uses web scraping and AI to extract business details from a website
    for auto-filling onboarding forms.
    """
    logger.info("Scanning website", user_id=user.user_id, url=request.url)

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/website/scan",
        request_body=request,
        user_context=user,
        response_model=WebsiteScanResponse,
    )


@router.post(
    "/api/coaching/coaching/onboarding",
    response_model=OnboardingCoachingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_onboarding_coaching(
    request: OnboardingCoachingRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> OnboardingCoachingResponse:
    """Get AI coaching assistance for onboarding topics using topic-driven architecture.

    Migrated to unified topic-driven architecture (Issue #113).
    Uses 'onboarding_coaching' topic for consistent prompt management.

    Provides interactive coaching help for core values, purpose, or vision.
    """
    logger.info("Providing onboarding coaching", user_id=user.user_id, topic=request.topic)

    return await handler.handle_single_shot(
        http_method="POST",
        endpoint_path="/coaching/onboarding",
        request_body=request,
        user_context=user,
        response_model=OnboardingCoachingResponse,
    )


__all__ = ["router"]
