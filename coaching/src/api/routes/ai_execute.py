"""API routes for generic AI execution.

This module provides a single entry point for all single-shot AI operations,
accepting any registered topic_id and its parameters, validating them against
the endpoint registry, and returning dynamically-typed responses.

Endpoints:
    POST /ai/execute - Execute AI for any registered single-shot topic
        USED BY: FE - WebsiteScanPanel (website_scan), OnboardingReviews (niche_review, ica_review, value_proposition_review)
    GET /ai/schemas/{schema_name} - Get JSON schema for a response model
    GET /ai/topics - List all available single-shot topics
"""

import time
from typing import Any

import structlog
from coaching.src.api.dependencies.ai_engine import get_unified_ai_engine
from coaching.src.api.models.ai_execute import (
    GenericAIRequest,
    GenericAIResponse,
    ResponseMetadata,
    TopicInfo,
    TopicParameter,
)
from coaching.src.application.ai_engine.unified_ai_engine import (
    ParameterValidationError,
    PromptRenderError,
    TopicNotFoundError,
    UnifiedAIEngine,
)
from coaching.src.core.constants import TopicType
from coaching.src.core.response_model_registry import (
    get_response_model,
    get_response_schema,
    is_model_registered,
    list_available_schemas,
)
from coaching.src.core.topic_registry import (
    get_parameters_for_topic,
    get_required_parameter_names_for_topic,
    get_topic_by_topic_id,
    list_all_topics,
)
from fastapi import APIRouter, Depends, HTTPException, Path, status

logger = structlog.get_logger()

router = APIRouter(prefix="/ai", tags=["AI Execute"])


# Backwards compatibility alias for tests
def get_endpoint_by_topic_id(topic_id: str):
    """Get endpoint definition by topic_id (backwards compatibility alias)."""
    return get_topic_by_topic_id(topic_id)


@router.post(
    "/execute",
    response_model=GenericAIResponse,
    summary="Execute AI for any registered single-shot topic",
    description="""
Execute AI for any registered single-shot topic.

This endpoint provides a single entry point for all single-shot AI operations.
It validates the topic exists, is active, and is a single-shot type (not conversation),
then validates required parameters and executes via UnifiedAIEngine.

**Response Structure:**
- `data` field contains the topic-specific response payload
- Use `schema_ref` to look up the expected structure via GET /ai/schemas/{schema_ref}

**Example Request:**
```json
{
    "topic_id": "website_scan",
    "parameters": {
        "url": "https://example.com",
        "scan_depth": 2
    }
}
```
""",
    responses={
        200: {"description": "AI execution completed successfully"},
        400: {
            "description": "Invalid request - topic inactive or wrong type",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Topic website_scan is type conversation_coaching, "
                        "use conversation endpoints for conversation topics"
                    }
                }
            },
        },
        404: {
            "description": "Topic not found",
            "content": {
                "application/json": {"example": {"detail": "Topic not found: unknown_topic"}}
            },
        },
        422: {
            "description": "Missing required parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Missing required parameters for topic website_scan: ['url']"
                    }
                }
            },
        },
        500: {
            "description": "Internal server error",
            "content": {
                "application/json": {
                    "example": {"detail": "Response model not configured: WebsiteScanResponse"}
                }
            },
        },
    },
)
async def execute_ai(
    request: GenericAIRequest,
    engine: UnifiedAIEngine = Depends(get_unified_ai_engine),
) -> GenericAIResponse:
    """Execute AI for any registered single-shot topic.

    Validates topic exists in registry, validates parameters,
    executes via UnifiedAIEngine, and returns validated response.

    Args:
        request: Generic AI request with topic_id and parameters
        engine: UnifiedAIEngine instance from dependency injection

    Returns:
        GenericAIResponse with AI-generated data and metadata

    Raises:
        HTTPException: Various status codes for validation and execution errors
    """
    start_time = time.time()

    logger.info(
        "ai_execute.started",
        topic_id=request.topic_id,
        param_count=len(request.parameters),
    )

    # Step 1: Validate topic exists and is active
    endpoint = get_topic_by_topic_id(request.topic_id)
    if endpoint is None:
        logger.warning("ai_execute.topic_not_found", topic_id=request.topic_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic not found: {request.topic_id}",
        )

    if not endpoint.is_active:
        logger.warning("ai_execute.topic_inactive", topic_id=request.topic_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic is not active: {request.topic_id}",
        )

    # Step 2: Validate topic is single-shot (not conversation)
    if endpoint.topic_type != TopicType.SINGLE_SHOT:
        logger.warning(
            "ai_execute.wrong_topic_type",
            topic_id=request.topic_id,
            topic_type=endpoint.topic_type.value,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topic {request.topic_id} is type {endpoint.topic_type.value}, "
            "use conversation endpoints for conversation topics",
        )

    # Step 3: Validate required parameters
    required_params = get_required_parameter_names_for_topic(request.topic_id)
    missing = [p for p in required_params if p not in request.parameters]
    if missing:
        logger.warning(
            "ai_execute.missing_parameters",
            topic_id=request.topic_id,
            missing=missing,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required parameters for topic {request.topic_id}: {missing}",
        )

    # Step 4: Get response model for validation
    response_model = get_response_model(endpoint.response_model)
    if response_model is None:
        logger.error(
            "ai_execute.response_model_not_configured",
            topic_id=request.topic_id,
            response_model=endpoint.response_model,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response model not configured: {endpoint.response_model}",
        )

    # Step 5: Execute via UnifiedAIEngine
    try:
        result = await engine.execute_single_shot(
            topic_id=request.topic_id,
            parameters=request.parameters,
            response_model=response_model,
        )
    except TopicNotFoundError as e:
        logger.error("ai_execute.engine_topic_not_found", topic_id=e.topic_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic configuration not found: {e.topic_id}",
        ) from e
    except ParameterValidationError as e:
        logger.error(
            "ai_execute.engine_parameter_error",
            topic_id=e.topic_id,
            missing_params=e.missing_params,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Parameter validation failed: {e.reason}",
        ) from e
    except PromptRenderError as e:
        logger.error(
            "ai_execute.prompt_render_error",
            topic_id=e.topic_id,
            prompt_type=e.prompt_type,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prompt rendering failed: {e.reason}",
        ) from e
    except Exception as e:
        logger.exception(
            "ai_execute.unexpected_error",
            topic_id=request.topic_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI execution failed: {e!s}",
        ) from e

    processing_time = int((time.time() - start_time) * 1000)

    logger.info(
        "ai_execute.completed",
        topic_id=request.topic_id,
        processing_time_ms=processing_time,
        result_type=type(result).__name__,
    )

    # Step 6: Return generic response with validated data
    return GenericAIResponse(
        topic_id=request.topic_id,
        success=True,
        data=result.model_dump(),
        schema_ref=endpoint.response_model,
        metadata=ResponseMetadata(
            model=endpoint.response_model,  # Could also get from LLM response
            tokens_used=0,  # TODO: Get from engine response when available
            processing_time_ms=processing_time,
            finish_reason="stop",
        ),
    )


@router.get(
    "/schemas/{schema_name}",
    response_model=dict[str, Any],
    summary="Get JSON schema for a response model",
    description="""
Get the JSON schema for a response model, enabling frontend developers
to discover expected response structures.

Use the `schema_ref` field from GenericAIResponse to look up schemas.

**Example:** GET /ai/schemas/WebsiteScanResponse
""",
    responses={
        200: {"description": "JSON schema for the response model"},
        404: {
            "description": "Schema not found",
            "content": {
                "application/json": {"example": {"detail": "Schema not found: UnknownResponse"}}
            },
        },
    },
)
async def get_schema(
    schema_name: str = Path(
        ...,
        description="Name of the response model schema",
        examples=["WebsiteScanResponse", "AlignmentAnalysisResponse"],
    ),
) -> dict[str, Any]:
    """Get JSON schema for a response model.

    Use this to discover the expected response structure for a topic.

    Args:
        schema_name: Name of the response model

    Returns:
        JSON schema dictionary

    Raises:
        HTTPException: 404 if schema not found
    """
    schema = get_response_schema(schema_name)
    if schema is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schema not found: {schema_name}",
        )
    return schema


@router.get(
    "/schemas",
    response_model=list[str],
    summary="List all available response schemas",
    description="Get a list of all registered response model schema names.",
)
async def list_schemas() -> list[str]:
    """List all available response model schema names.

    Returns:
        Sorted list of schema names
    """
    return list_available_schemas()


@router.get(
    "/topics",
    response_model=list[TopicInfo],
    summary="List all available AI topics",
    description="""
List all available AI topics from both single-shot and coaching registries.

This endpoint aggregates topics from ENDPOINT_REGISTRY:
- **Single-shot topics**: Use POST /ai/execute
- **Coaching topics**: Use /ai/coaching/* endpoints

Each topic includes:
- topic_id: Topic identifier
- name: Display name
- description: What the topic does
- topic_type: 'single_shot' or 'coaching'
- response_model: Schema name for the response
- parameters: What parameters the topic accepts
- category: Organizational category

Use the `topic_type` field to determine which endpoint to use:
- `single_shot`: POST /ai/execute with topic_id and parameters
- `coaching`: POST /ai/coaching/start with topic_id to begin interactive session
""",
)
async def list_available_topics() -> list[TopicInfo]:
    """List all available AI topics from both registries.

    Aggregates single-shot topics from ENDPOINT_REGISTRY and
    coaching topics from ENDPOINT_REGISTRY (CONVERSATION_COACHING type).

    Returns:
        List of TopicInfo objects for all active topics
    """
    from coaching.src.core.parameter_registry import get_parameter_definition
    from coaching.src.services.coaching_session_service import list_coaching_topics

    topics: list[TopicInfo] = []

    # Add single-shot topics from ENDPOINT_REGISTRY
    for endpoint in list_all_topics(active_only=True):
        # Only include single-shot topics
        if endpoint.topic_type != TopicType.SINGLE_SHOT:
            continue

        # Only include topics with registered response models
        if not is_model_registered(endpoint.response_model):
            continue

        # Get parameter info
        params = get_parameters_for_topic(endpoint.topic_id)
        topic_params = [
            TopicParameter(
                name=p["name"],
                type=p["type"],
                required=p["required"],
                description=p.get("description"),
            )
            for p in params
        ]

        topics.append(
            TopicInfo(
                topic_id=endpoint.topic_id,
                name=(
                    endpoint.description.split(" - ")[0]
                    if " - " in endpoint.description
                    else endpoint.topic_id.replace("_", " ").title()
                ),
                description=endpoint.description,
                topic_type="single_shot",
                response_model=endpoint.response_model,
                parameters=topic_params,
                category=endpoint.category.value,
            )
        )

    # Add coaching topics from ENDPOINT_REGISTRY (CONVERSATION_COACHING type)
    for coaching_topic in list_coaching_topics():
        # Build parameter info from parameter_refs
        topic_params = []
        for param_ref in coaching_topic.parameter_refs:
            param_def = get_parameter_definition(param_ref.name)
            if param_def:
                # Use param_ref.required if set, otherwise infer from default
                # A parameter is required if it has no default value
                is_required = (
                    param_ref.required
                    if param_ref.required is not None
                    else (param_def.default is None)
                )
                topic_params.append(
                    TopicParameter(
                        name=param_ref.name,
                        type=param_def.param_type.value,
                        required=is_required,
                        description=param_def.description,
                    )
                )

        topics.append(
            TopicInfo(
                topic_id=coaching_topic.topic_id,
                name=coaching_topic.topic_id.replace("_", " ").title(),  # Derive name from topic_id
                description=coaching_topic.description,
                topic_type="coaching",
                response_model=coaching_topic.result_model or "",
                parameters=topic_params,
                category=coaching_topic.category.value,
            )
        )

    return topics
