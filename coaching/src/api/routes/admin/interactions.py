"""Admin API routes for LLM interactions management."""

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.llm_interactions import (
    InteractionCategory,
    get_interaction,
    list_interactions,
)
from coaching.src.models.admin_responses import (
    ActiveConfigurationInfo,
    LLMInteractionDetail,
    LLMInteractionInfo,
    LLMInteractionsResponse,
)
from fastapi import APIRouter, Depends, HTTPException, Path, Query

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/interactions", response_model=ApiResponse[LLMInteractionsResponse])
async def list_llm_interactions(
    category: str | None = Query(None, description="Filter by category"),
    active_only: bool = Query(True, description="Only return active interactions"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
) -> ApiResponse[LLMInteractionsResponse]:
    """
    Get all available LLM interactions with their parameters.

    This endpoint returns all LLM interaction types defined in the system,
    including their required and optional parameters, category, and handler class.

    **Permissions Required:** ADMIN_ACCESS

    **Query Parameters:**
    - category: Filter by interaction category (analysis, coaching, operations, insights, onboarding)
    - active_only: Only return active interactions (default: true)

    **Returns:**
    - List of available LLM interactions
    - Total count of interactions
    """
    logger.info(
        "Fetching LLM interactions list",
        admin_user_id=context.user_id,
        category=category,
        active_only=active_only,
    )

    try:
        # Convert category string to enum if provided
        category_enum: InteractionCategory | None = None
        if category:
            try:
                category_enum = InteractionCategory(category.lower())
            except ValueError:
                valid_categories = [c.value for c in InteractionCategory]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category '{category}'. Valid categories: {valid_categories}",
                ) from None

        # Get interactions from registry
        interactions = list_interactions(category=category_enum)

        # Convert to response models
        interaction_infos = [
            LLMInteractionInfo(
                code=interaction.code,
                description=interaction.description,
                category=interaction.category.value,
                requiredParameters=interaction.required_parameters,
                optionalParameters=interaction.optional_parameters,
                handlerClass=interaction.handler_class,
            )
            for interaction in interactions
        ]

        response_data = LLMInteractionsResponse(
            interactions=interaction_infos,
            totalCount=len(interaction_infos),
        )

        logger.info(
            "LLM interactions list retrieved",
            admin_user_id=context.user_id,
            total_count=len(interaction_infos),
            category=category,
        )

        return ApiResponse(success=True, data=response_data)

    except Exception as e:
        logger.error("Error listing LLM interactions", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list LLM interactions") from e


@router.get("/interactions/{interaction_code}", response_model=ApiResponse[LLMInteractionDetail])
async def get_llm_interaction_details(
    interaction_code: str = Path(..., description="Interaction code"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
) -> ApiResponse[LLMInteractionDetail]:
    """
    Get detailed information about a specific LLM interaction.

    Returns interaction details including active configurations that use this interaction.

    **Permissions Required:** ADMIN_ACCESS

    **Path Parameters:**
    - interaction_code: Unique interaction code (e.g., "ALIGNMENT_ANALYSIS")

    **Returns:**
    - Interaction details including parameters
    - List of active configurations using this interaction
    """
    logger.info(
        "Fetching LLM interaction details",
        admin_user_id=context.user_id,
        interaction_code=interaction_code,
    )

    try:
        # Get interaction from registry
        interaction = get_interaction(interaction_code)

        # TODO: Fetch active configurations from configuration repository
        # For now, return empty list until configuration endpoints are implemented
        active_configurations: list[ActiveConfigurationInfo] = []

        response_data = LLMInteractionDetail(
            code=interaction.code,
            description=interaction.description,
            category=interaction.category.value,
            requiredParameters=interaction.required_parameters,
            optionalParameters=interaction.optional_parameters,
            handlerClass=interaction.handler_class,
            activeConfigurations=active_configurations,
        )

        logger.info(
            "LLM interaction details retrieved",
            admin_user_id=context.user_id,
            interaction_code=interaction_code,
        )

        return ApiResponse(success=True, data=response_data)

    except KeyError:
        logger.warning(
            "LLM interaction not found",
            admin_user_id=context.user_id,
            interaction_code=interaction_code,
        )
        raise HTTPException(
            status_code=404,
            detail=f"Interaction not found: {interaction_code}",
        ) from None
    except Exception as e:
        logger.error(
            "Error fetching LLM interaction details",
            error=str(e),
            interaction_code=interaction_code,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to fetch interaction details") from e
