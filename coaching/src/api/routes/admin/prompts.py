"""Admin API endpoints for topic and prompt management."""

import re
from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse
from src.api.dependencies import get_s3_prompt_storage, get_topic_repository
from src.api.middleware.admin_auth import require_admin_access
from src.domain.entities.llm_topic import LLMTopic, ParameterDefinition, PromptInfo
from src.domain.exceptions.topic_exceptions import (
    DuplicateTopicError,
    PromptNotFoundError,
    TopicNotFoundError,
)
from src.models.prompt_requests import (
    CreatePromptRequest,
    CreateTopicRequest,
    UpdateTopicRequest,
)
from src.models.prompt_responses import (
    ParameterDefinitionResponse,
    PromptDetailResponse,
    TopicResponse,
)
from src.repositories.topic_repository import TopicRepository
from src.services.s3_prompt_storage import S3PromptStorage

logger = structlog.get_logger()

router = APIRouter(prefix="/prompts", tags=["admin-prompts"])


# Helper functions


def parameter_to_response(param: ParameterDefinition) -> ParameterDefinitionResponse:
    """Convert domain parameter to response model."""
    return ParameterDefinitionResponse(
        name=param.name,
        type=param.type,
        required=param.required,
        description=param.description,
        default=param.default,
    )


def topic_to_response(topic: LLMTopic) -> TopicResponse:
    """Convert domain topic to response model."""
    return TopicResponse(
        topic_id=topic.topic_id,
        topic_name=topic.topic_name,
        topic_type=topic.topic_type,
        category=topic.category,
        description=topic.description,
        display_order=topic.display_order,
        is_active=topic.is_active,
        available_prompts=[p.prompt_type for p in topic.prompts],
        allowed_parameters=[parameter_to_response(p) for p in topic.allowed_parameters],
        config=topic.config,
        created_at=topic.created_at.isoformat(),
        created_by=topic.created_by,
        updated_at=topic.updated_at.isoformat(),
    )


def validate_prompt_parameters(
    content: str,
    allowed_parameters: list[ParameterDefinition],
) -> None:
    """
    Validate that all parameters used in content are in allowed_parameters.

    Args:
        content: Prompt content with {{parameter}} placeholders
        allowed_parameters: List of allowed parameter definitions

    Raises:
        HTTPException: 400 if validation fails with invalid parameters
    """
    # Extract parameters from content: {{parameter_name}}
    pattern = r"\{\{(\w+)\}\}"
    used_params = set(re.findall(pattern, content))

    allowed_param_names = {p.name for p in allowed_parameters}

    invalid_params = used_params - allowed_param_names
    if invalid_params:
        logger.warning(
            "Invalid parameters in prompt content",
            invalid_parameters=list(invalid_params),
            allowed_parameters=list(allowed_param_names),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PARAMETER",
                "message": f"Parameters {invalid_params} not in allowed_parameters",
                "invalid_parameters": list(invalid_params),
                "allowed_parameters": list(allowed_param_names),
            },
        )


# Topic management endpoints


@router.get("", response_model=ApiResponse[list[TopicResponse]])
async def list_topics(
    topic_type: Annotated[str | None, Query(description="Filter by topic type")] = None,
    include_inactive: Annotated[bool, Query(description="Include inactive topics")] = False,
    repo: TopicRepository = Depends(get_topic_repository),
    _context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[list[TopicResponse]]:
    """
    List all topics, optionally filtered by type.

    - **topic_type**: Filter by conversation_coaching, single_shot, or kpi_system
    - **include_inactive**: Include topics marked as inactive

    Returns:
        List of topics with metadata and available prompts
    """
    try:
        if topic_type:
            topics = await repo.list_by_type(
                topic_type=topic_type, include_inactive=include_inactive
            )
        else:
            topics = await repo.list_all(include_inactive=include_inactive)

        response_data = [topic_to_response(t) for t in topics]

        logger.info(
            "Topics listed",
            count=len(response_data),
            topic_type=topic_type,
            include_inactive=include_inactive,
        )

        return ApiResponse(success=True, data=response_data)

    except Exception as e:
        logger.error("Failed to list topics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topics",
        ) from e


@router.post("", response_model=ApiResponse[TopicResponse], status_code=201)
async def create_topic(
    request: CreateTopicRequest = Body(...),
    repo: TopicRepository = Depends(get_topic_repository),
    context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[TopicResponse]:
    """
    Create a new KPI-system topic.

    Only kpi_system topics can be created via API.
    Coaching topics are seeded at deployment.

    Args:
        request: Topic creation request with metadata and configuration

    Returns:
        Created topic details

    Raises:
        409: Topic ID already exists
        400: Invalid request data
    """
    try:
        # Create topic entity
        now = datetime.now(UTC)
        topic = LLMTopic(
            topic_id=request.topic_id,
            topic_name=request.topic_name,
            topic_type=request.topic_type,
            category=request.category,
            description=request.description,
            is_active=request.is_active,
            allowed_parameters=[
                ParameterDefinition(
                    name=p.name,
                    type=p.type,
                    required=p.required,
                    description=p.description,
                    default=p.default,
                )
                for p in request.allowed_parameters
            ],
            prompts=[],  # Prompts added separately
            config=request.config.model_dump(),
            display_order=request.display_order,
            created_at=now,
            updated_at=now,
            created_by=context.user_id,
        )

        # Save to repository
        created_topic = await repo.create(topic=topic)

        logger.info(
            "Topic created",
            topic_id=created_topic.topic_id,
            created_by=context.user_id,
        )

        return ApiResponse(
            success=True,
            data=topic_to_response(created_topic),
            message="Topic created successfully",
        )

    except DuplicateTopicError as e:
        logger.warning("Topic ID already exists", topic_id=request.topic_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Topic ID '{request.topic_id}' already exists",
        ) from e
    except Exception as e:
        logger.error(
            "Failed to create topic",
            topic_id=request.topic_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create topic",
        ) from e


@router.get("/{topic_id}", response_model=ApiResponse[TopicResponse])
async def get_topic(
    topic_id: str = Path(..., description="Topic identifier"),
    repo: TopicRepository = Depends(get_topic_repository),
    _context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[TopicResponse]:
    """
    Get topic details by ID.

    Args:
        topic_id: Topic identifier

    Returns:
        Topic details with metadata and available prompts

    Raises:
        404: Topic not found
    """
    try:
        topic = await repo.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        return ApiResponse(success=True, data=topic_to_response(topic))

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get topic", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topic",
        ) from e


@router.put("/{topic_id}", response_model=ApiResponse[TopicResponse])
async def update_topic(
    topic_id: str = Path(..., description="Topic identifier"),
    request: UpdateTopicRequest = Body(...),
    repo: TopicRepository = Depends(get_topic_repository),
    _context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[TopicResponse]:
    """
    Update topic metadata (name, description, parameters, config).

    Only updates fields that are provided in the request.

    Args:
        topic_id: Topic identifier
        request: Partial update request

    Returns:
        Updated topic details

    Raises:
        404: Topic not found
        400: Invalid update data
    """
    try:
        # Get existing topic
        topic = await repo.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Update fields (only if provided)
        if request.topic_name is not None:
            topic.topic_name = request.topic_name
        if request.description is not None:
            topic.description = request.description
        if request.allowed_parameters is not None:
            topic.allowed_parameters = [
                ParameterDefinition(
                    name=p.name,
                    type=p.type,
                    required=p.required,
                    description=p.description,
                    default=p.default,
                )
                for p in request.allowed_parameters
            ]
        if request.config is not None:
            topic.config = request.config.model_dump()
        if request.display_order is not None:
            topic.display_order = request.display_order
        if request.is_active is not None:
            topic.is_active = request.is_active

        # Save
        updated_topic = await repo.update(topic=topic)

        logger.info("Topic updated", topic_id=topic_id)

        return ApiResponse(
            success=True,
            data=topic_to_response(updated_topic),
            message="Topic updated successfully",
        )

    except TopicNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic '{topic_id}' not found",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update topic", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update topic",
        ) from e


# Prompt content management endpoints


@router.get(
    "/{topic_id}/{prompt_type}",
    response_model=ApiResponse[PromptDetailResponse],
)
async def get_prompt_content(
    topic_id: str = Path(..., description="Topic identifier"),
    prompt_type: str = Path(..., description="Prompt type (system, user, assistant)"),
    repo: TopicRepository = Depends(get_topic_repository),
    storage: S3PromptStorage = Depends(get_s3_prompt_storage),
    _context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[PromptDetailResponse]:
    """
    Get prompt content for editing.

    Args:
        topic_id: Topic identifier
        prompt_type: Prompt type

    Returns:
        Prompt content with metadata

    Raises:
        404: Topic or prompt not found
    """
    try:
        # Get topic
        topic = await repo.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Get prompt info from topic
        prompt_info = topic.get_prompt(prompt_type=prompt_type)
        if not prompt_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt type '{prompt_type}' not found in topic '{topic_id}'",
            )

        # Get prompt content from S3
        content = await storage.get_prompt(topic_id=topic_id, prompt_type=prompt_type)
        if not content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt content not found in S3",
            )

        # Build response
        response = PromptDetailResponse(
            topic_id=topic_id,
            prompt_type=prompt_type,
            content=content,
            allowed_parameters=[parameter_to_response(p) for p in topic.allowed_parameters],
            s3_location={
                "bucket": storage.bucket_name,
                "key": f"prompts/{topic_id}/{prompt_type}.md",
            },
            updated_at=prompt_info.updated_at.isoformat(),
            updated_by=prompt_info.updated_by,
        )

        return ApiResponse(success=True, data=response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get prompt content",
            topic_id=topic_id,
            prompt_type=prompt_type,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt content",
        ) from e


@router.post(
    "/{topic_id}/{prompt_type}",
    response_model=ApiResponse[dict[str, str]],
    status_code=201,
)
async def create_prompt(
    topic_id: str = Path(..., description="Topic identifier"),
    prompt_type: str = Path(..., description="Prompt type (system, user, assistant)"),
    request: CreatePromptRequest = Body(...),
    repo: TopicRepository = Depends(get_topic_repository),
    storage: S3PromptStorage = Depends(get_s3_prompt_storage),
    context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[dict[str, str]]:
    """
    Create a new prompt for a topic.

    Args:
        topic_id: Topic identifier
        prompt_type: Prompt type
        request: Prompt content

    Returns:
        Created prompt metadata

    Raises:
        404: Topic not found
        400: Invalid parameters in content
    """
    try:
        # Validate topic exists
        topic = await repo.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Validate parameters in content
        validate_prompt_parameters(request.content, topic.allowed_parameters)

        # Save to S3
        s3_key = await storage.save_prompt(
            topic_id=topic_id,
            prompt_type=prompt_type,
            content=request.content,
        )

        # Add prompt to topic's prompts array
        now = datetime.now(UTC)
        prompt_info = PromptInfo(
            prompt_type=prompt_type,
            s3_bucket=storage.bucket_name,
            s3_key=s3_key,
            updated_at=now,
            updated_by=context.user_id,
        )
        await repo.add_prompt(topic_id=topic_id, prompt_info=prompt_info)

        logger.info(
            "Prompt created",
            topic_id=topic_id,
            prompt_type=prompt_type,
            created_by=context.user_id,
        )

        return ApiResponse(
            success=True,
            data={
                "topic_id": topic_id,
                "prompt_type": prompt_type,
                "s3_key": s3_key,
            },
            message="Prompt created successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create prompt",
            topic_id=topic_id,
            prompt_type=prompt_type,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prompt",
        ) from e


@router.put(
    "/{topic_id}/{prompt_type}",
    response_model=ApiResponse[dict[str, str]],
)
async def update_prompt(
    topic_id: str = Path(..., description="Topic identifier"),
    prompt_type: str = Path(..., description="Prompt type (system, user, assistant)"),
    request: CreatePromptRequest = Body(...),
    repo: TopicRepository = Depends(get_topic_repository),
    storage: S3PromptStorage = Depends(get_s3_prompt_storage),
    context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[dict[str, str]]:
    """
    Update existing prompt content.

    Overwrites existing content in S3 and updates metadata.

    Args:
        topic_id: Topic identifier
        prompt_type: Prompt type
        request: New prompt content

    Returns:
        Updated prompt metadata

    Raises:
        404: Topic or prompt not found
        400: Invalid parameters in content
    """
    try:
        # Validate topic exists
        topic = await repo.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Check prompt exists
        if not topic.has_prompt(prompt_type=prompt_type):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt type '{prompt_type}' not found in topic '{topic_id}'",
            )

        # Validate parameters in content
        validate_prompt_parameters(request.content, topic.allowed_parameters)

        # Save to S3 (overwrites existing)
        s3_key = await storage.save_prompt(
            topic_id=topic_id,
            prompt_type=prompt_type,
            content=request.content,
        )

        # Update prompt metadata in topic
        now = datetime.now(UTC)
        prompt_info = PromptInfo(
            prompt_type=prompt_type,
            s3_bucket=storage.bucket_name,
            s3_key=s3_key,
            updated_at=now,
            updated_by=context.user_id,
        )
        await repo.add_prompt(topic_id=topic_id, prompt_info=prompt_info)

        logger.info(
            "Prompt updated",
            topic_id=topic_id,
            prompt_type=prompt_type,
            updated_by=context.user_id,
        )

        return ApiResponse(
            success=True,
            data={
                "topic_id": topic_id,
                "prompt_type": prompt_type,
                "s3_key": s3_key,
            },
            message="Prompt updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update prompt",
            topic_id=topic_id,
            prompt_type=prompt_type,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prompt",
        ) from e


@router.delete(
    "/{topic_id}/{prompt_type}",
    response_model=ApiResponse[dict[str, str]],
)
async def delete_prompt(
    topic_id: str = Path(..., description="Topic identifier"),
    prompt_type: str = Path(..., description="Prompt type (system, user, assistant)"),
    repo: TopicRepository = Depends(get_topic_repository),
    storage: S3PromptStorage = Depends(get_s3_prompt_storage),
    context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[dict[str, str]]:
    """
    Delete prompt from topic and S3.

    Args:
        topic_id: Topic identifier
        prompt_type: Prompt type

    Returns:
        Deletion confirmation

    Raises:
        404: Topic or prompt not found
    """
    try:
        # Validate topic exists
        topic = await repo.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Delete from S3
        await storage.delete_prompt(topic_id=topic_id, prompt_type=prompt_type)

        # Remove from topic's prompts array
        await repo.remove_prompt(topic_id=topic_id, prompt_type=prompt_type)

        logger.info(
            "Prompt deleted",
            topic_id=topic_id,
            prompt_type=prompt_type,
            deleted_by=context.user_id,
        )

        return ApiResponse(
            success=True,
            data={"topic_id": topic_id, "prompt_type": prompt_type},
            message="Prompt deleted successfully",
        )

    except PromptNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt type '{prompt_type}' not found in topic '{topic_id}'",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete prompt",
            topic_id=topic_id,
            prompt_type=prompt_type,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete prompt",
        ) from e


__all__ = ["router"]
