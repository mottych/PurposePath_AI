"""Onboarding AI API routes (Issue #48 Phase 3)."""

from typing import cast

import structlog
from src.api.auth import get_current_user
from src.api.models.auth import UserContext
from src.api.models.onboarding import (
    OnboardingCoachingRequest,
    OnboardingCoachingResponse,
    OnboardingSuggestionRequest,
    OnboardingSuggestionResponse,
    WebsiteScanRequest,
    WebsiteScanResponse,
)
from src.api.multitenant_dependencies import get_onboarding_service
from src.services.onboarding_service import OnboardingService
from fastapi import APIRouter, Depends, HTTPException, status

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
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingSuggestionResponse:
    """Get AI suggestions for onboarding fields.

    Provides intelligent suggestions for niche, ICA, or value proposition
    based on business context.

    **Authentication**: Bearer token required

    Args:
        request: Suggestion request with kind and context
        user: Authenticated user context
        service: Onboarding service

    Returns:
        AI-generated suggestions with reasoning

    Raises:
        HTTPException 400: If request is invalid
        HTTPException 500: If generation fails
    """
    try:
        logger.info(
            "Generating onboarding suggestions",
            user_id=user.user_id,
            kind=request.kind,
        )

        result = await service.get_suggestions(
            kind=request.kind,
            current=request.current,
            context=request.context,
        )

        logger.info(
            "Suggestions generated",
            user_id=user.user_id,
            count=len(result.get("suggestions", [])),
        )

        return OnboardingSuggestionResponse(
            suggestions=cast(list[str], result["suggestions"]),
            reasoning=cast(str, result["reasoning"]),
        )

    except ValueError as e:
        logger.warning(
            "Invalid suggestion request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Suggestion generation failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate suggestions",
        ) from e


@router.post(
    "/api/coaching/website/scan",
    response_model=WebsiteScanResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_website(
    request: WebsiteScanRequest,
    user: UserContext = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> WebsiteScanResponse:
    """Scan website to extract business information.

    Uses web scraping and AI to extract business details from a website
    for auto-filling onboarding forms.

    **Authentication**: Bearer token required

    **Note**: This endpoint is not yet fully implemented. Returns 501 Not Implemented.

    Args:
        request: Website scan request with URL
        user: Authenticated user context
        service: Onboarding service

    Returns:
        Extracted business information

    Raises:
        HTTPException 400: If URL is invalid
        HTTPException 501: Feature not implemented yet
        HTTPException 500: If scanning fails
    """
    try:
        logger.info(
            "Scanning website",
            user_id=user.user_id,
            url=request.url,
        )

        result = await service.scan_website(request.url)

        logger.info(
            "Website scanned",
            user_id=user.user_id,
        )

        # Construct response with proper type casts using alias names
        return WebsiteScanResponse(
            businessName=cast(str, result.get("businessName", "")),
            industry=cast(str, result.get("industry", "")),
            description=cast(str, result.get("description", "")),
            products=cast(list[str], result.get("products", [])),
            targetMarket=cast(str, result.get("targetMarket", "")),
            suggestedNiche=cast(str, result.get("suggestedNiche", "")),
        )

    except NotImplementedError as e:
        logger.info(
            "Website scan not implemented",
            user_id=user.user_id,
            url=request.url,
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e),
        ) from e
    except ValueError as e:
        logger.warning(
            "Invalid website scan request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Website scan failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to scan website",
        ) from e


@router.post(
    "/api/coaching/coaching/onboarding",
    response_model=OnboardingCoachingResponse,
    status_code=status.HTTP_200_OK,
)
async def get_onboarding_coaching(
    request: OnboardingCoachingRequest,
    user: UserContext = Depends(get_current_user),
    service: OnboardingService = Depends(get_onboarding_service),
) -> OnboardingCoachingResponse:
    """Get AI coaching assistance for onboarding topics.

    Provides interactive coaching help for core values, purpose, or vision.

    **Authentication**: Bearer token required

    Args:
        request: Coaching request with topic and message
        user: Authenticated user context
        service: Onboarding service

    Returns:
        AI coach response with suggestions

    Raises:
        HTTPException 400: If request is invalid
        HTTPException 500: If coaching fails
    """
    try:
        logger.info(
            "Providing onboarding coaching",
            user_id=user.user_id,
            topic=request.topic,
        )

        result = await service.get_coaching(
            topic=request.topic,
            message=request.message,
            context=request.context,
        )

        logger.info(
            "Coaching response generated",
            user_id=user.user_id,
        )

        return OnboardingCoachingResponse(
            response=cast(str, result["response"]),
            suggestions=cast(list[str], result.get("suggestions", [])),
        )

    except ValueError as e:
        logger.warning(
            "Invalid coaching request",
            user_id=user.user_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Coaching generation failed",
            user_id=user.user_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate coaching response",
        ) from e


__all__ = ["router"]
