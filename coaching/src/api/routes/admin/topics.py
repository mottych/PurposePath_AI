"""Admin API routes for topic management."""

from datetime import UTC, datetime
from typing import Annotated

from coaching.src.api.dependencies import get_current_context, get_topic_repository
from coaching.src.api.models.auth import UserContext
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.entities.llm_topic import ParameterDefinition as DomainParameter
from coaching.src.domain.entities.llm_topic import PromptInfo as DomainPromptInfo
from coaching.src.domain.exceptions.topic_exceptions import (
    InvalidModelConfigurationError,
)
from coaching.src.models.admin_topics import (
    CreatePromptRequest,
    CreatePromptResponse,
    CreateTopicRequest,
    CreateTopicResponse,
    DeletePromptResponse,
    DeleteTopicResponse,
    ModelInfo,
    ModelsListResponse,
    ParameterDefinition,
    PromptContentResponse,
    PromptInfo,
    TopicDetail,
    TopicListResponse,
    TopicSummary,
    UpdatePromptRequest,
    UpdatePromptResponse,
    UpdateTopicRequest,
    UpdateTopicResponse,
    ValidateTopicRequest,
    ValidationResult,
)
from coaching.src.repositories.topic_repository import TopicRepository
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from structlog import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/topics", tags=["Admin - Topics"])


# Helper functions


def _map_topic_to_summary(topic: LLMTopic) -> TopicSummary:
    """Map domain LLMTopic to API TopicSummary."""
    return TopicSummary(
        topic_id=topic.topic_id,
        topic_name=topic.topic_name,
        category=topic.category,
        topic_type=topic.topic_type,
        model_code=topic.model_code,
        temperature=topic.temperature,
        max_tokens=topic.max_tokens,
        is_active=topic.is_active,
        description=topic.description,
        display_order=topic.display_order,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        created_by=topic.created_by,
    )


def _map_topic_to_detail(topic: LLMTopic) -> TopicDetail:
    """Map domain LLMTopic to API TopicDetail."""
    return TopicDetail(
        topic_id=topic.topic_id,
        topic_name=topic.topic_name,
        category=topic.category,
        topic_type=topic.topic_type,
        description=topic.description,
        model_code=topic.model_code,
        temperature=topic.temperature,
        max_tokens=topic.max_tokens,
        top_p=topic.top_p,
        frequency_penalty=topic.frequency_penalty,
        presence_penalty=topic.presence_penalty,
        is_active=topic.is_active,
        display_order=topic.display_order,
        prompts=[
            PromptInfo(
                prompt_type=p.prompt_type,
                s3_bucket=p.s3_bucket,
                s3_key=p.s3_key,
                updated_at=p.updated_at,
                updated_by=p.updated_by,
            )
            for p in topic.prompts
        ],
        allowed_parameters=[
            ParameterDefinition(
                name=p.name,
                type=p.type,
                required=p.required,
                description=p.description,
            )
            for p in topic.allowed_parameters
        ],
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        created_by=topic.created_by,
    )


# Endpoints


@router.get("", response_model=TopicListResponse)
async def list_topics(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
    category: str | None = None,
    topic_type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    repository: TopicRepository = Depends(get_topic_repository),
    _user: UserContext = Depends(get_current_context),
) -> TopicListResponse:
    """List all topics with optional filtering.

    Requires admin:topics:read permission.
    """
    try:
        # Get all topics
        all_topics = await repository.get_all_topics()

        # Apply filters
        filtered = all_topics
        if category:
            filtered = [t for t in filtered if t.category == category]
        if topic_type:
            filtered = [t for t in filtered if t.topic_type == topic_type]
        if is_active is not None:
            filtered = [t for t in filtered if t.is_active == is_active]
        if search:
            search_lower = search.lower()
            filtered = [
                t
                for t in filtered
                if search_lower in t.topic_name.lower()
                or (t.description and search_lower in t.description.lower())
            ]

        # Sort by display_order, then topic_name
        filtered.sort(key=lambda t: (t.display_order, t.topic_name))

        # Paginate
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_topics = filtered[start:end]

        return TopicListResponse(
            topics=[_map_topic_to_summary(t) for t in page_topics],
            total=total,
            page=page,
            page_size=page_size,
            has_more=end < total,
        )

    except Exception as e:
        logger.error("Failed to list topics", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list topics",
        ) from e


@router.get("/{topic_id}", response_model=TopicDetail)
async def get_topic(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    repository: TopicRepository = Depends(get_topic_repository),
    _user: UserContext = Depends(get_current_context),
) -> TopicDetail:
    """Get detailed information about a specific topic.

    Requires admin:topics:read permission.
    """
    try:
        topic = await repository.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        return _map_topic_to_detail(topic)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get topic", topic_id=topic_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get topic",
        ) from e


@router.post("", response_model=CreateTopicResponse, status_code=status.HTTP_201_CREATED)
async def create_topic(
    request: CreateTopicRequest,
    user: UserContext = Depends(get_current_context),
    repository: TopicRepository = Depends(get_topic_repository),
) -> CreateTopicResponse:
    """Create a new topic.

    Requires admin:topics:write permission.
    """
    try:
        # Check if topic already exists
        existing = await repository.get_topic_by_id(request.topic_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Topic '{request.topic_id}' already exists",
            )

        # Create domain entity
        now = datetime.now(UTC)
        topic = LLMTopic(
            topic_id=request.topic_id,
            topic_name=request.topic_name,
            topic_type=request.topic_type,
            category=request.category,
            is_active=request.is_active,
            model_code=request.model_code,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            allowed_parameters=[
                DomainParameter(
                    name=p["name"],
                    type=p["type"],
                    required=p.get("required", False),
                    description=p.get("description"),
                )
                for p in request.allowed_parameters
            ],
            prompts=[],
            created_at=now,
            updated_at=now,
            description=request.description,
            display_order=request.display_order,
            created_by=user.user_id,
        )

        # Validate
        topic.validate()

        # Save
        await repository.create_topic(topic)

        logger.info(
            "Topic created",
            topic_id=topic.topic_id,
            created_by=user.user_id,
        )

        return CreateTopicResponse(
            topic_id=topic.topic_id,
            created_at=topic.created_at,
            message="Topic created successfully. Upload prompts to activate.",
        )

    except HTTPException:
        raise
    except InvalidModelConfigurationError as e:
        logger.warning("Invalid topic configuration", topic_id=request.topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(
            "Failed to create topic",
            topic_id=request.topic_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create topic",
        ) from e


@router.put("/{topic_id}", response_model=UpdateTopicResponse)
async def update_topic(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    request: UpdateTopicRequest,
    user: UserContext = Depends(get_current_context),
    repository: TopicRepository = Depends(get_topic_repository),
) -> UpdateTopicResponse:
    """Update an existing topic.

    Requires admin:topics:write permission.
    """
    try:
        # Get existing topic
        topic = await repository.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Update fields
        updates = {}
        if request.topic_name is not None:
            updates["topic_name"] = request.topic_name
        if request.description is not None:
            updates["description"] = request.description
        if request.model_code is not None:
            updates["model_code"] = request.model_code
        if request.temperature is not None:
            updates["temperature"] = request.temperature
        if request.max_tokens is not None:
            updates["max_tokens"] = request.max_tokens
        if request.top_p is not None:
            updates["top_p"] = request.top_p
        if request.frequency_penalty is not None:
            updates["frequency_penalty"] = request.frequency_penalty
        if request.presence_penalty is not None:
            updates["presence_penalty"] = request.presence_penalty
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.display_order is not None:
            updates["display_order"] = request.display_order
        if request.allowed_parameters is not None:
            updates["allowed_parameters"] = [
                DomainParameter(
                    name=p["name"],
                    type=p["type"],
                    required=p.get("required", False),
                    description=p.get("description"),
                )
                for p in request.allowed_parameters
            ]

        updates["updated_at"] = datetime.now(UTC)

        # Update topic
        updated_topic = topic.update(**updates)
        updated_topic.validate()

        await repository.update_topic(updated_topic)

        logger.info(
            "Topic updated",
            topic_id=topic_id,
            updated_by=user.user_id,
            updates=list(updates.keys()),
        )

        return UpdateTopicResponse(
            topic_id=topic_id,
            updated_at=updated_topic.updated_at,
            message="Topic updated successfully",
        )

    except HTTPException:
        raise
    except InvalidModelConfigurationError as e:
        logger.warning("Invalid topic configuration", topic_id=topic_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error("Failed to update topic", topic_id=topic_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update topic",
        ) from e


@router.delete("/{topic_id}", response_model=DeleteTopicResponse)
async def delete_topic(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    hard_delete: bool = Query(False, description="Permanently delete if true"),
    user: UserContext = Depends(get_current_context),
    repository: TopicRepository = Depends(get_topic_repository),
) -> DeleteTopicResponse:
    """Delete a topic (soft delete by default).

    Requires admin:topics:delete permission.
    """
    try:
        # Get existing topic
        topic = await repository.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        now = datetime.now(UTC)

        if hard_delete:
            # Hard delete - permanently remove
            await repository.delete_topic(topic_id)
            logger.info("Topic hard deleted", topic_id=topic_id, deleted_by=user.user_id)
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="")
        else:
            # Soft delete - mark as inactive
            updated_topic = topic.update(is_active=False, updated_at=now)
            await repository.update_topic(updated_topic)

            logger.info("Topic deactivated", topic_id=topic_id, deactivated_by=user.user_id)

            return DeleteTopicResponse(
                topic_id=topic_id,
                deleted_at=now,
                message="Topic deactivated successfully",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete topic", topic_id=topic_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete topic",
        ) from e


@router.get("/{topic_id}/prompts/{prompt_type}", response_model=PromptContentResponse)
async def get_prompt_content(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    prompt_type: Annotated[str, Path(description="Prompt type")],
    repository: TopicRepository = Depends(get_topic_repository),
    _user: UserContext = Depends(get_current_context),
) -> PromptContentResponse:
    """Get prompt content for editing.

    Requires admin:topics:read permission.
    """
    try:
        # Get topic
        topic = await repository.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Find prompt
        prompt = next((p for p in topic.prompts if p.prompt_type == prompt_type), None)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt type '{prompt_type}' not found for topic '{topic_id}'",
            )

        # Get content from S3
        content = await repository.get_prompt_content(prompt.s3_bucket, prompt.s3_key)

        return PromptContentResponse(
            topic_id=topic_id,
            prompt_type=prompt_type,
            content=content,
            s3_key=prompt.s3_key,
            updated_at=prompt.updated_at,
            updated_by=prompt.updated_by,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get prompt content",
            topic_id=topic_id,
            prompt_type=prompt_type,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get prompt content",
        ) from e


@router.put("/{topic_id}/prompts/{prompt_type}", response_model=UpdatePromptResponse)
async def update_prompt_content(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    prompt_type: Annotated[str, Path(description="Prompt type")],
    request: UpdatePromptRequest,
    user: UserContext = Depends(get_current_context),
    repository: TopicRepository = Depends(get_topic_repository),
) -> UpdatePromptResponse:
    """Update prompt content.

    Requires admin:topics:write permission.
    """
    try:
        # Get topic
        topic = await repository.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Find prompt
        prompt = next((p for p in topic.prompts if p.prompt_type == prompt_type), None)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt type '{prompt_type}' not found for topic '{topic_id}'",
            )

        # Update content in S3
        now = datetime.now(UTC)
        await repository.update_prompt_content(
            prompt.s3_bucket,
            prompt.s3_key,
            request.content,
        )

        # Update prompt metadata in topic
        updated_prompts = [
            (
                DomainPromptInfo(
                    prompt_type=p.prompt_type,
                    s3_bucket=p.s3_bucket,
                    s3_key=p.s3_key,
                    updated_at=now,
                    updated_by=user.user_id,
                )
                if p.prompt_type == prompt_type
                else p
            )
            for p in topic.prompts
        ]

        updated_topic = topic.update(prompts=updated_prompts, updated_at=now)
        await repository.update_topic(updated_topic)

        logger.info(
            "Prompt updated",
            topic_id=topic_id,
            prompt_type=prompt_type,
            updated_by=user.user_id,
            commit_message=request.commit_message,
        )

        return UpdatePromptResponse(
            topic_id=topic_id,
            prompt_type=prompt_type,
            s3_key=prompt.s3_key,
            updated_at=now,
            version=None,  # Could implement versioning later
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
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prompt",
        ) from e


@router.post(
    "/{topic_id}/prompts", response_model=CreatePromptResponse, status_code=status.HTTP_201_CREATED
)
async def create_prompt(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    request: CreatePromptRequest,
    user: UserContext = Depends(get_current_context),
    repository: TopicRepository = Depends(get_topic_repository),
) -> CreatePromptResponse:
    """Create a new prompt for a topic.

    Requires admin:topics:write permission.
    """
    try:
        # Get topic
        topic = await repository.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Check if prompt type already exists
        if any(p.prompt_type == request.prompt_type for p in topic.prompts):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Prompt type '{request.prompt_type}' already exists for topic '{topic_id}'",
            )

        # Create S3 key
        s3_bucket = topic.prompts[0].s3_bucket if topic.prompts else "purposepath-prompts-prod"
        s3_key = f"prompts/{topic_id}/{request.prompt_type}.md"

        # Upload content to S3
        now = datetime.now(UTC)
        await repository.update_prompt_content(s3_bucket, s3_key, request.content)

        # Add prompt to topic
        new_prompt = DomainPromptInfo(
            prompt_type=request.prompt_type,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            updated_at=now,
            updated_by=user.user_id,
        )

        updated_topic = topic.update(
            prompts=[*topic.prompts, new_prompt],
            updated_at=now,
        )
        await repository.update_topic(updated_topic)

        logger.info(
            "Prompt created",
            topic_id=topic_id,
            prompt_type=request.prompt_type,
            created_by=user.user_id,
        )

        return CreatePromptResponse(
            topic_id=topic_id,
            prompt_type=request.prompt_type,
            s3_key=s3_key,
            created_at=now,
            message="Prompt created successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create prompt",
            topic_id=topic_id,
            prompt_type=request.prompt_type,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prompt",
        ) from e


@router.delete("/{topic_id}/prompts/{prompt_type}", response_model=DeletePromptResponse)
async def delete_prompt(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    prompt_type: Annotated[str, Path(description="Prompt type")],
    user: UserContext = Depends(get_current_context),
    repository: TopicRepository = Depends(get_topic_repository),
) -> DeletePromptResponse:
    """Delete a prompt from a topic.

    Requires admin:topics:delete permission.
    """
    try:
        # Get topic
        topic = await repository.get_topic_by_id(topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        # Find prompt
        prompt = next((p for p in topic.prompts if p.prompt_type == prompt_type), None)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt type '{prompt_type}' not found for topic '{topic_id}'",
            )

        # Delete from S3
        await repository.delete_prompt_content(prompt.s3_bucket, prompt.s3_key)

        # Remove from topic
        updated_prompts = [p for p in topic.prompts if p.prompt_type != prompt_type]
        updated_topic = topic.update(prompts=updated_prompts, updated_at=datetime.now(UTC))
        await repository.update_topic(updated_topic)

        logger.info(
            "Prompt deleted",
            topic_id=topic_id,
            prompt_type=prompt_type,
            deleted_by=user.user_id,
        )

        return DeletePromptResponse(message="Prompt deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete prompt",
            topic_id=topic_id,
            prompt_type=prompt_type,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete prompt",
        ) from e


@router.get("/../../models", response_model=ModelsListResponse)
async def list_models(
    _user: UserContext = Depends(get_current_context),
) -> ModelsListResponse:
    """List available LLM models.

    Requires admin:topics:read permission.
    """
    # Hardcoded model list based on current Bedrock models
    models = [
        ModelInfo(
            model_code="claude-3-5-sonnet-20241022",
            model_name="Claude 3.5 Sonnet",
            provider="anthropic",
            capabilities=["chat", "function_calling"],
            context_window=200000,
            max_output_tokens=4096,
            cost_per_input_million=3.00,
            cost_per_output_million=15.00,
            is_active=True,
        ),
        ModelInfo(
            model_code="claude-3-5-haiku-20241022",
            model_name="Claude 3.5 Haiku",
            provider="anthropic",
            capabilities=["chat"],
            context_window=200000,
            max_output_tokens=4096,
            cost_per_input_million=0.80,
            cost_per_output_million=4.00,
            is_active=True,
        ),
        ModelInfo(
            model_code="anthropic.claude-3-sonnet-20240229-v1:0",
            model_name="Claude 3 Sonnet (Legacy)",
            provider="anthropic",
            capabilities=["chat"],
            context_window=200000,
            max_output_tokens=4096,
            cost_per_input_million=3.00,
            cost_per_output_million=15.00,
            is_active=True,
        ),
        ModelInfo(
            model_code="anthropic.claude-3-haiku-20240307-v1:0",
            model_name="Claude 3 Haiku (Legacy)",
            provider="anthropic",
            capabilities=["chat"],
            context_window=200000,
            max_output_tokens=4096,
            cost_per_input_million=0.25,
            cost_per_output_million=1.25,
            is_active=True,
        ),
    ]

    return ModelsListResponse(models=models)


@router.post("/validate", response_model=ValidationResult)
async def validate_topic_config(
    request: ValidateTopicRequest,
    _user: UserContext = Depends(get_current_context),
) -> ValidationResult:
    """Validate a topic configuration before saving.

    Requires admin:topics:read permission.
    """
    errors = []
    warnings = []
    suggestions = []

    # Validate topic_id format
    if not request.topic_id.islower() or not all(c.isalnum() or c == "_" for c in request.topic_id):
        errors.append(
            {
                "field": "topic_id",
                "message": "Topic ID must be lowercase snake_case",
                "code": "INVALID_FORMAT",
            }
        )

    # Validate temperature
    if request.temperature > 1.0:
        warnings.append(
            f"Temperature {request.temperature} is high; may produce less consistent results"
        )
    if request.temperature < 0.3:
        suggestions.append("Consider increasing temperature to 0.5-0.7 for more natural responses")

    # Validate max_tokens
    if request.max_tokens > 4000:
        warnings.append(f"max_tokens {request.max_tokens} exceeds typical model limits")

    # Validate prompts
    if request.prompts:
        for prompt in request.prompts:
            if len(prompt.get("content", "")) < 50:
                warnings.append(f"Prompt '{prompt.get('prompt_type')}' is very short")

    # Check parameter usage in prompts
    if request.allowed_parameters and request.prompts:
        param_names = {p["name"] for p in request.allowed_parameters}
        for prompt in request.prompts:
            content = prompt.get("content", "")
            # Simple check for {param_name} patterns
            import re

            used_params = set(re.findall(r"\{(\w+)\}", content))
            unused = param_names - used_params
            if unused:
                suggestions.append(
                    f"Parameters {unused} are defined but not used in {prompt.get('prompt_type')} prompt"
                )

    return ValidationResult(
        valid=len(errors) == 0,
        warnings=warnings,
        suggestions=suggestions,
        errors=errors,
    )
