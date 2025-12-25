"""Admin API routes for topic management (Enhanced for Issue #113).

Endpoint Usage Status:
- GET /topics: USED BY Admin - TopicList, TopicFilters
- GET /topics/{topic_id}: USED BY Admin - TopicMetadataEditor, ParameterManager
- PUT /topics/{topic_id}: USED BY Admin - TopicMetadataEditor, ParameterManager
- GET /topics/{topic_id}/prompts/{prompt_type}: USED BY Admin - PromptEditorDialog
- POST /topics/{topic_id}/prompts: USED BY Admin - PromptEditorDialog (create)
- PUT /topics/{topic_id}/prompts/{prompt_type}: USED BY Admin - PromptEditorDialog (update)
- DELETE /topics/{topic_id}/prompts/{prompt_type}: USED BY Admin - PromptEditorDialog (delete)

DEPRECATED (defined but not called by Admin UI):
- POST /topics: create new topic - UI doesn't call
- DELETE /topics/{topic_id}: delete topic - UI doesn't call
- POST /topics/validate: validate topic - UI doesn't call
- POST /topics/{topic_id}/test: test topic - UI doesn't call
"""

import time
from dataclasses import replace
from datetime import UTC, datetime
from typing import Annotated, Any

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import (
    get_s3_prompt_storage,
    get_topic_repository,
)
from coaching.src.api.dependencies.ai_engine import (
    create_template_processor,
    get_jwt_token,
    get_unified_ai_engine,
)
from coaching.src.api.models.auth import UserContext
from coaching.src.application.ai_engine.response_serializer import SerializationError
from coaching.src.application.ai_engine.unified_ai_engine import (
    ParameterValidationError,
    PromptRenderError,
    TopicNotFoundError,
    UnifiedAIEngine,
    UnifiedAIEngineError,
)
from coaching.src.core.constants import TopicType
from coaching.src.core.response_model_registry import get_response_model
from coaching.src.core.topic_registry import (
    ENDPOINT_REGISTRY,
    get_endpoint_by_topic_id,
    get_parameters_for_topic,
)
from coaching.src.domain.entities.llm_topic import LLMTopic
from coaching.src.domain.entities.llm_topic import PromptInfo as DomainPromptInfo
from coaching.src.domain.exceptions.topic_exceptions import (
    InvalidModelConfigurationError,
)
from coaching.src.models.admin_topics import (
    ConversationConfig,
    CreatePromptRequest,
    CreatePromptResponse,
    CreateTopicRequest,
    CreateTopicResponse,
    DeletePromptResponse,
    DeleteTopicResponse,
    ParameterDefinition,
    PromptContentResponse,
    PromptInfo,
    TemplateStatus,
    TemplateSummary,
    TopicDetail,
    TopicListResponse,
    TopicSummary,
    UpdatePromptRequest,
    UpdatePromptResponse,
    UpdateTopicRequest,
    UpsertTopicResponse,
    ValidateTopicRequest,
    ValidationResult,
)
from coaching.src.repositories.topic_repository import TopicRepository
from coaching.src.services.s3_prompt_storage import S3PromptStorage
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, Field

logger = structlog.get_logger()

router = APIRouter(prefix="/topics", tags=["Admin - Topics"])


# Helper functions


def _map_topic_to_summary(
    topic: LLMTopic, from_database: bool = True, allowed_prompt_types: list[str] | None = None
) -> TopicSummary:
    """Map domain LLMTopic to API TopicSummary.

    Args:
        topic: The LLMTopic entity
        from_database: Whether the topic came from DB (True) or registry default (False)
        allowed_prompt_types: List of allowed prompt types from endpoint registry
    """
    # Get defined prompt types from the topic's prompts
    defined_prompt_types = {p.prompt_type for p in topic.prompts}

    # Build templates array with is_defined indicator
    templates = [
        TemplateSummary(prompt_type=pt, is_defined=(pt in defined_prompt_types))
        for pt in (allowed_prompt_types or [])
    ]

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
        from_database=from_database,
        templates=templates,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        created_by=topic.created_by,
    )


def _map_topic_to_detail(
    topic: LLMTopic,
    from_database: bool = True,
    allowed_prompt_types: list[str] | None = None,
    response_schema: dict[str, Any] | None = None,
) -> TopicDetail:
    """Map domain LLMTopic to API TopicDetail.

    Args:
        topic: The LLMTopic entity
        from_database: Whether the topic came from DB (True) or registry default (False)
        allowed_prompt_types: List of allowed prompt types from endpoint registry
        response_schema: JSON schema for the response model (when include_schema=true)
    """
    # Create a lookup of defined prompts by type
    defined_prompts = {p.prompt_type: p for p in topic.prompts}

    # Build template status for all allowed prompt types
    template_status_list: list[TemplateStatus] = []
    for prompt_type in allowed_prompt_types or []:
        if prompt_type in defined_prompts:
            p = defined_prompts[prompt_type]
            template_status_list.append(
                TemplateStatus(
                    prompt_type=prompt_type,
                    is_defined=True,
                    s3_bucket=p.s3_bucket,
                    s3_key=p.s3_key,
                    updated_at=p.updated_at,
                    updated_by=p.updated_by,
                )
            )
        else:
            template_status_list.append(
                TemplateStatus(
                    prompt_type=prompt_type,
                    is_defined=False,
                    s3_bucket=None,
                    s3_key=None,
                    updated_at=None,
                    updated_by=None,
                )
            )

    # Build conversation_config only for conversation_coaching topics
    conversation_config: ConversationConfig | None = None
    if topic.topic_type == "conversation_coaching":
        # Get from additional_config or use defaults
        config_data = topic.additional_config or {}
        conversation_config = ConversationConfig(
            max_messages_to_llm=config_data.get("max_messages_to_llm", 30),
            inactivity_timeout_minutes=config_data.get("inactivity_timeout_minutes", 30),
            session_ttl_days=config_data.get("session_ttl_days", 14),
            estimated_messages=config_data.get("estimated_messages", 20),
        )

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
        from_database=from_database,
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
        template_status=template_status_list,
        allowed_parameters=[
            ParameterDefinition(
                name=p["name"],
                type=p["type"],
                required=p["required"],
                description=p.get("description"),
            )
            for p in get_parameters_for_topic(topic.topic_id)
        ],
        conversation_config=conversation_config,
        response_schema=response_schema,
        created_at=topic.created_at,
        updated_at=topic.updated_at,
        created_by=topic.created_by,
    )


# Endpoints


def _get_allowed_prompt_types(topic_id: str) -> list[str]:
    """Get allowed prompt types for a topic from the endpoint registry.

    For topics defined in the registry, returns only the prompt types
    explicitly allowed by the EndpointDefinition.

    For custom topics not in the registry, returns all valid PromptType
    values to allow full flexibility.
    """
    from coaching.src.core.constants import PromptType

    endpoint_def = get_endpoint_by_topic_id(topic_id)
    if endpoint_def:
        # Topic is in registry - use its allowed prompt types
        return [pt.value for pt in endpoint_def.allowed_prompt_types]
    # Custom topic not in registry - allow all valid prompt types
    return [pt.value for pt in PromptType]


async def _get_or_create_topic_from_registry(
    topic_id: str,
    repository: TopicRepository,
    user_id: str,
) -> LLMTopic | None:
    """Get topic from DB or auto-create from registry if not in DB.

    This implements the auto-upsert pattern: if a topic exists in the endpoint
    registry but not in the database, create it from registry defaults.

    Args:
        topic_id: Topic identifier
        repository: Topic repository
        user_id: User ID for audit trail

    Returns:
        LLMTopic if found or created, None if topic doesn't exist anywhere
    """
    # First try database
    topic = await repository.get(topic_id=topic_id)
    if topic:
        return topic

    # Not in DB - check if it's in the registry
    endpoint_def = get_endpoint_by_topic_id(topic_id)
    if not endpoint_def:
        # Topic doesn't exist anywhere
        return None

    # Create from registry defaults
    now = datetime.now(UTC)
    new_topic = LLMTopic.create_default_from_endpoint(endpoint_def)
    # Set audit fields
    new_topic = replace(
        new_topic,
        created_at=now,
        updated_at=now,
        created_by=user_id,
    )

    await repository.create(topic=new_topic)
    logger.info(
        "Topic auto-created from registry",
        topic_id=topic_id,
        created_by=user_id,
    )

    return new_topic


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

    Returns topics from both database and registry defaults, with from_database
    field indicating the source.

    Requires admin:topics:read permission.
    """
    try:
        logger.info("list_topics called", page=page, page_size=page_size, category=category)

        # Get DB topics and registry defaults separately
        db_topics = await repository.list_all(include_inactive=True)
        db_topic_ids = {topic.topic_id for topic in db_topics}

        # Create defaults for topics not in DB
        from coaching.src.domain.entities.llm_topic import LLMTopic

        registry_topics = [
            LLMTopic.create_default_from_endpoint(endpoint_def)
            for endpoint_def in ENDPOINT_REGISTRY.values()
            if endpoint_def.topic_id not in db_topic_ids
        ]

        # Combine all topics
        all_topics = db_topics + registry_topics

        logger.info(
            "topics_retrieved", count=len(all_topics), topics=[t.topic_id for t in all_topics]
        )

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

        logger.info("topics_paginated", total=total, page_count=len(page_topics))

        # Map topics with from_database indicator and allowed_prompt_types
        return TopicListResponse(
            topics=[
                _map_topic_to_summary(
                    t,
                    from_database=(t.topic_id in db_topic_ids),
                    allowed_prompt_types=_get_allowed_prompt_types(t.topic_id),
                )
                for t in page_topics
            ],
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
    include_schema: Annotated[
        bool,
        Query(description="Include JSON schema of the response model for template design"),
    ] = False,
    repository: TopicRepository = Depends(get_topic_repository),
    _user: UserContext = Depends(get_current_context),
) -> TopicDetail:
    """Get detailed information about a specific topic.

    If the topic exists in the database, returns the database configuration.
    If not found in database, falls back to endpoint registry defaults.

    When include_schema=true, includes the JSON schema of the expected response
    model in the response. This is useful for template authors to understand
    what output fields their prompts should generate.

    Requires admin:topics:read permission.
    """
    from coaching.src.core.response_model_registry import get_response_schema

    try:
        # First, try to get from database
        topic = await repository.get(topic_id=topic_id)

        # Get allowed prompt types from registry (used for both DB and default)
        allowed_prompt_types = _get_allowed_prompt_types(topic_id)

        # Get response schema if requested
        response_schema: dict[str, Any] | None = None
        if include_schema:
            # Get response model name from endpoint registry
            endpoint_def = get_endpoint_by_topic_id(topic_id)
            if endpoint_def:
                response_schema = get_response_schema(endpoint_def.response_model)

        if topic:
            # Topic found in database
            return _map_topic_to_detail(
                topic,
                from_database=True,
                allowed_prompt_types=allowed_prompt_types,
                response_schema=response_schema,
            )

        # Topic not in database, try to get from registry
        endpoint_def = get_endpoint_by_topic_id(topic_id)
        if not endpoint_def:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found in database or registry",
            )

        # Create default topic from registry
        default_topic = LLMTopic.create_default_from_endpoint(endpoint_def)
        return _map_topic_to_detail(
            default_topic,
            from_database=False,
            allowed_prompt_types=allowed_prompt_types,
            response_schema=response_schema,
        )

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
        existing = await repository.get(topic_id=request.topic_id)
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
            prompts=[],
            created_at=now,
            updated_at=now,
            description=request.description,
            display_order=request.display_order,
            created_by=user.user_id,
        )

        # Validate
        # topic.validate() # Validated in __post_init__

        # Save
        await repository.create(topic=topic)

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


@router.put("/{topic_id}", response_model=UpsertTopicResponse)
async def upsert_topic(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    request: UpdateTopicRequest,
    response: Response,
    user: UserContext = Depends(get_current_context),
    repository: TopicRepository = Depends(get_topic_repository),
) -> UpsertTopicResponse:
    """Create or update a topic (UPSERT).

    If the topic exists, it will be updated with the provided fields.
    If the topic doesn't exist, it will be created using registry defaults
    (if available) merged with the provided fields.

    Returns:
        - 201 Created: If the topic was created
        - 200 OK: If the topic was updated

    Requires admin:topics:write permission.
    """
    try:
        now = datetime.now(UTC)

        # Try to get existing topic
        existing_topic = await repository.get(topic_id=topic_id)

        if existing_topic:
            # UPDATE existing topic
            updates: dict[str, Any] = {}
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

            # Handle conversation_config for coaching topics
            if (
                request.conversation_config is not None
                and existing_topic.topic_type == "conversation_coaching"
            ):
                # Merge with existing additional_config
                additional_config = dict(existing_topic.additional_config or {})
                additional_config.update(request.conversation_config.model_dump())
                updates["additional_config"] = additional_config

            updates["updated_at"] = now
            updated_topic = replace(existing_topic, **updates)
            await repository.update(topic=updated_topic)

            logger.info(
                "Topic updated",
                topic_id=topic_id,
                updated_by=user.user_id,
                updates=list(updates.keys()),
            )

            response.status_code = status.HTTP_200_OK
            return UpsertTopicResponse(
                topic_id=topic_id,
                created=False,
                timestamp=now,
                message="Topic updated successfully",
            )

        else:
            # CREATE new topic - try to get defaults from registry
            endpoint_def = get_endpoint_by_topic_id(topic_id)

            if endpoint_def:
                # Use registry defaults as base
                base_topic = LLMTopic.create_default_from_endpoint(endpoint_def)
                # Override with request values
                new_topic = replace(
                    base_topic,
                    topic_name=request.topic_name or base_topic.topic_name,
                    description=(
                        request.description
                        if request.description is not None
                        else base_topic.description
                    ),
                    model_code=request.model_code or base_topic.model_code,
                    temperature=(
                        request.temperature
                        if request.temperature is not None
                        else base_topic.temperature
                    ),
                    max_tokens=(
                        request.max_tokens
                        if request.max_tokens is not None
                        else base_topic.max_tokens
                    ),
                    top_p=request.top_p if request.top_p is not None else base_topic.top_p,
                    frequency_penalty=(
                        request.frequency_penalty
                        if request.frequency_penalty is not None
                        else base_topic.frequency_penalty
                    ),
                    presence_penalty=(
                        request.presence_penalty
                        if request.presence_penalty is not None
                        else base_topic.presence_penalty
                    ),
                    is_active=(
                        request.is_active if request.is_active is not None else base_topic.is_active
                    ),
                    display_order=(
                        request.display_order
                        if request.display_order is not None
                        else base_topic.display_order
                    ),
                    additional_config=(
                        request.conversation_config.model_dump()
                        if request.conversation_config is not None
                        and endpoint_def.topic_type.value == "conversation_coaching"
                        else base_topic.additional_config
                    ),
                    created_at=now,
                    updated_at=now,
                    created_by=user.user_id,
                )
            else:
                # No registry entry - require topic_name at minimum
                if not request.topic_name:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Topic '{topic_id}' not found in registry. "
                        "topic_name is required to create a new topic.",
                    )

                # Create with defaults and provided values
                new_topic = LLMTopic(
                    topic_id=topic_id,
                    topic_name=request.topic_name,
                    category="custom",
                    topic_type="single_shot",
                    description=request.description,
                    display_order=(
                        request.display_order if request.display_order is not None else 100
                    ),
                    is_active=request.is_active if request.is_active is not None else False,
                    model_code=request.model_code or "claude-3-5-sonnet-20241022",
                    temperature=request.temperature if request.temperature is not None else 0.7,
                    max_tokens=request.max_tokens if request.max_tokens is not None else 2000,
                    top_p=request.top_p if request.top_p is not None else 1.0,
                    frequency_penalty=(
                        request.frequency_penalty if request.frequency_penalty is not None else 0.0
                    ),
                    presence_penalty=(
                        request.presence_penalty if request.presence_penalty is not None else 0.0
                    ),
                    prompts=[],
                    created_at=now,
                    updated_at=now,
                    created_by=user.user_id,
                )

            await repository.create(topic=new_topic)

            logger.info(
                "Topic created via upsert",
                topic_id=topic_id,
                created_by=user.user_id,
                from_registry=endpoint_def is not None,
            )

            response.status_code = status.HTTP_201_CREATED
            return UpsertTopicResponse(
                topic_id=topic_id,
                created=True,
                timestamp=now,
                message="Topic created successfully",
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
        topic = await repository.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_id}' not found",
            )

        now = datetime.now(UTC)

        if hard_delete:
            # Hard delete - permanently remove
            await repository.delete(topic_id=topic_id, hard_delete=True)
            logger.info("Topic hard deleted", topic_id=topic_id, deleted_by=user.user_id)
            raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="")
        else:
            # Soft delete - mark as inactive
            updated_topic = replace(topic, is_active=False, updated_at=now)
            await repository.update(topic=updated_topic)

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
    s3_storage: S3PromptStorage = Depends(get_s3_prompt_storage),
    _user: UserContext = Depends(get_current_context),
) -> PromptContentResponse:
    """Get prompt content for editing.

    Requires admin:topics:read permission.
    """
    try:
        # Get topic - for GET, we don't auto-create, just check if exists in DB
        topic = await repository.get(topic_id=topic_id)
        if not topic:
            # Check if it exists in registry (for better error message)
            endpoint_def = get_endpoint_by_topic_id(topic_id)
            if endpoint_def:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Topic '{topic_id}' exists in registry but has no prompts saved yet. "
                    "Create a prompt first using POST.",
                )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Topic '{topic_id}' not found in database or registry",
            )

        # Find prompt
        prompt = next((p for p in topic.prompts if p.prompt_type == prompt_type), None)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt type '{prompt_type}' not found for topic '{topic_id}'",
            )

        # Get content from S3
        content = await s3_storage.get_prompt(topic_id=topic_id, prompt_type=prompt_type)

        return PromptContentResponse(
            topic_id=topic_id,
            prompt_type=prompt_type,
            content=content or "",
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
    s3_storage: S3PromptStorage = Depends(get_s3_prompt_storage),
) -> UpdatePromptResponse:
    """Update prompt content.

    If the topic exists in the endpoint registry but not in the database,
    it will be auto-created from registry defaults before updating the prompt.

    Requires admin:topics:write permission.
    """
    try:
        # Validate prompt_type is a valid PromptType enum value
        from coaching.src.core.constants import PromptType

        valid_types = {pt.value for pt in PromptType}
        if prompt_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid prompt type '{prompt_type}'. Valid types: {', '.join(sorted(valid_types))}",
            )

        # Validate prompt type is allowed for this topic
        allowed_types = _get_allowed_prompt_types(topic_id)
        if prompt_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Prompt type '{prompt_type}' is not allowed for topic '{topic_id}'. "
                f"Allowed types: {', '.join(allowed_types)}",
            )

        # Get topic from DB or auto-create from registry
        topic = await _get_or_create_topic_from_registry(
            topic_id=topic_id,
            repository=repository,
            user_id=user.user_id,
        )
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Topic '{topic_id}' not found in database or registry",
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
        await s3_storage.save_prompt(
            topic_id=topic_id,
            prompt_type=prompt_type,
            content=request.content,
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

        updated_topic = replace(topic, prompts=updated_prompts, updated_at=now)
        await repository.update(topic=updated_topic)

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
    s3_storage: S3PromptStorage = Depends(get_s3_prompt_storage),
) -> CreatePromptResponse:
    """Create a new prompt for a topic.

    If the topic exists in the endpoint registry but not in the database,
    it will be auto-created from registry defaults before adding the prompt.

    Requires admin:topics:write permission.
    """
    try:
        # Get topic from DB or auto-create from registry
        topic = await _get_or_create_topic_from_registry(
            topic_id=topic_id,
            repository=repository,
            user_id=user.user_id,
        )
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Topic '{topic_id}' not found in database or registry",
            )

        # Validate prompt type is allowed for this topic
        allowed_types = _get_allowed_prompt_types(topic_id)
        if request.prompt_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Prompt type '{request.prompt_type}' is not allowed for topic '{topic_id}'. "
                f"Allowed types: {', '.join(allowed_types)}",
            )

        # Check if prompt type already exists
        if any(p.prompt_type == request.prompt_type for p in topic.prompts):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Prompt type '{request.prompt_type}' already exists for topic '{topic_id}'",
            )

        # Upload content to S3
        now = datetime.now(UTC)
        s3_key = await s3_storage.save_prompt(
            topic_id=topic_id,
            prompt_type=request.prompt_type,
            content=request.content,
        )
        s3_bucket = s3_storage.bucket_name

        # Add prompt to topic
        new_prompt = DomainPromptInfo(
            prompt_type=request.prompt_type,
            s3_bucket=s3_bucket,
            s3_key=s3_key,
            updated_at=now,
            updated_by=user.user_id,
        )

        updated_topic = replace(
            topic,
            prompts=[*topic.prompts, new_prompt],
            updated_at=now,
        )
        await repository.update(topic=updated_topic)

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
    s3_storage: S3PromptStorage = Depends(get_s3_prompt_storage),
) -> DeletePromptResponse:
    """Delete a prompt from a topic.

    Requires admin:topics:delete permission.
    """
    try:
        # Get topic - for DELETE, topic must exist in DB (can't delete what doesn't exist)
        topic = await repository.get(topic_id=topic_id)
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Topic '{topic_id}' not found in database",
            )

        # Find prompt
        prompt = next((p for p in topic.prompts if p.prompt_type == prompt_type), None)
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prompt type '{prompt_type}' not found for topic '{topic_id}'",
            )

        # Delete from S3
        await s3_storage.delete_prompt(topic_id=topic_id, prompt_type=prompt_type)

        # Remove from topic
        updated_prompts = [p for p in topic.prompts if p.prompt_type != prompt_type]
        updated_topic = replace(topic, prompts=updated_prompts, updated_at=datetime.now(UTC))
        await repository.update(topic=updated_topic)

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
    # Get parameters from registry for this topic
    registry_params = get_parameters_for_topic(request.topic_id)
    if registry_params and request.prompts:
        param_names = {p["name"] for p in registry_params}
        for prompt in request.prompts:
            content = prompt.get("content", "")
            # Simple check for {param_name} patterns
            import re

            used_params = set(re.findall(r"\\{(\\w+)\\}", content))
            unused = param_names - used_params
            if unused:
                suggestions.append(
                    f"Parameters {unused} are defined in registry but not used in {prompt.get('prompt_type')} prompt"
                )

    return ValidationResult(
        valid=len(errors) == 0,
        warnings=warnings,
        suggestions=suggestions,
        errors=errors,
    )


# ========== New Endpoints for Issue #113 ==========


class LLMRunMetadata(BaseModel):
    """Metadata about the LLM invocation for a test run."""

    provider: str
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None


class TopicTestRequest(BaseModel):
    """Request model for testing a topic."""

    parameters: dict[str, Any] = Field(default_factory=dict)
    allow_inactive: bool = False


class TopicTestResponse(BaseModel):
    """Response model for topic testing including rendered prompts."""

    success: bool
    topic_id: str
    rendered_system_prompt: str | None = None
    rendered_user_prompt: str | None = None
    enriched_parameters: dict[str, Any] | None = None
    response: dict[str, Any] | None = None
    response_model: str | None = None
    response_schema: dict[str, Any] | None = None
    llm_metadata: LLMRunMetadata | None = None
    execution_time_ms: float
    error: str | None = None


def _serialize_response_payload(response: BaseModel | Any) -> dict[str, Any]:
    """Serialize response payload to a dictionary for API responses."""

    if isinstance(response, BaseModel):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    return {"value": response}


@router.post("/{topic_id}/test", response_model=TopicTestResponse)
async def test_topic(
    topic_id: Annotated[str, Path(description="Topic identifier")],
    request: TopicTestRequest,
    user: UserContext = Depends(get_current_context),
    unified_engine: UnifiedAIEngine = Depends(get_unified_ai_engine),
    jwt_token: str | None = Depends(get_jwt_token),
) -> TopicTestResponse:
    """Test a topic by rendering prompts, enriching parameters, and executing the LLM.

    Returns rendered system/user prompts, enriched parameters, serialized AI response,
    and LLM metadata to help admins validate templates before rollout.
    """

    start_time = time.time()

    endpoint_def = get_endpoint_by_topic_id(topic_id)
    if endpoint_def is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic not found: {topic_id}",
        )

    if endpoint_def.topic_type != TopicType.SINGLE_SHOT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Topic {topic_id} is type {endpoint_def.topic_type.value}, "
                "only single-shot topics are supported for template testing"
            ),
        )

    response_model_cls = get_response_model(endpoint_def.response_model)
    if response_model_cls is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Response model not configured: {endpoint_def.response_model}",
        )

    try:
        template_processor = create_template_processor(jwt_token) if jwt_token else None

        debug_context = await unified_engine.execute_single_shot_debug(
            topic_id=topic_id,
            parameters=request.parameters,
            response_model=response_model_cls,
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            template_processor=template_processor,
            allow_inactive=request.allow_inactive,
        )

        execution_time = (time.time() - start_time) * 1000

        logger.info(
            "Topic test successful",
            topic_id=topic_id,
            execution_time_ms=execution_time,
        )

        return TopicTestResponse(
            success=True,
            topic_id=topic_id,
            rendered_system_prompt=debug_context.rendered_system_prompt,
            rendered_user_prompt=debug_context.rendered_user_prompt,
            enriched_parameters=debug_context.enriched_parameters,
            response=_serialize_response_payload(debug_context.serialized_response),
            response_model=debug_context.response_model_name,
            response_schema=debug_context.response_schema,
            llm_metadata=LLMRunMetadata(
                provider=debug_context.llm_response.provider,
                model=debug_context.llm_response.model,
                usage=debug_context.llm_response.usage,
                finish_reason=debug_context.llm_response.finish_reason,
            ),
            execution_time_ms=execution_time,
        )

    except TopicNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic configuration not found: {e.topic_id}",
        ) from e
    except ParameterValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required parameters: {', '.join(e.missing_params)}",
        ) from e
    except PromptRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render {e.prompt_type} prompt",
        ) from e
    except SerializationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serialize AI response for {e.response_model}",
        ) from e
    except UnifiedAIEngineError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI processing failed",
        ) from e
    except Exception as e:
        logger.error(
            "Topic test failed",
            topic_id=topic_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e
