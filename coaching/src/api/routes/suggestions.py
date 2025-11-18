from __future__ import annotations

from coaching.src.api.auth import get_current_context
from coaching.src.models.requests import OnboardingSuggestionRequest
from coaching.src.models.responses import OnboardingSuggestionResponse
from fastapi import APIRouter, Depends

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

router = APIRouter()


@router.post("/onboarding", response_model=ApiResponse[OnboardingSuggestionResponse])
async def suggest_onboarding(
    payload: OnboardingSuggestionRequest,
    _context: RequestContext = Depends(get_current_context),
) -> ApiResponse[OnboardingSuggestionResponse]:
    """Generate onboarding suggestions based on user input.

    Args:
        payload: Request containing suggestion type and current value
        _context: Authenticated user context (validated via dependency injection)

    Returns:
        ApiResponse containing suggestion text

    Raises:
        HTTPException 401: If authentication fails
    """
    # Authentication is enforced via _context dependency injection
    # Future enhancement: Use context for tenant-specific suggestions

    # Simple deterministic stub; can be replaced with Bedrock/LLM call
    base = {
        "niche": "Consider specializing in a focused segment to increase resonance.",
        "ica": "Define your ideal customer by role, pains, and goals.",
        "valueProposition": "We reduce time-to-insight by unifying siloed data and automating analysis.",
    }[payload.kind]

    suggestion = (
        base
        if not payload.current
        else f"{base} Based on your input, strengthen it around: '{payload.current}'."
    )

    response = OnboardingSuggestionResponse(suggestion=suggestion)
    return ApiResponse(success=True, data=response)
