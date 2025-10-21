"""Admin API routes for prompt template management."""

from datetime import datetime, timezone

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_prompt_repository
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.constants import CoachingTopic
from coaching.src.infrastructure.repositories.s3_prompt_repository import S3PromptRepository
from coaching.src.models.admin_responses import (
    PromptTemplateDetail,
    PromptTemplateVersionsResponse,
    TemplateVersionInfo,
)
from fastapi import APIRouter, Depends, HTTPException, Path

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get(
    "/prompts/{topic}/versions",
    response_model=ApiResponse[PromptTemplateVersionsResponse],
)
async def list_template_versions(
    topic: str = Path(..., description="Coaching topic identifier"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[PromptTemplateVersionsResponse]:
    """
    Get all versions of prompt templates for a specific topic.

    This endpoint lists all available versions of templates for the specified
    coaching topic, including metadata about each version.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `topic`: Coaching topic identifier (e.g., "goal_alignment")

    **Returns:**
    - List of all template versions
    - Latest version marker
    - Version metadata (creation time, size, etc.)
    """
    logger.info("Fetching template versions", topic=topic, admin_user_id=context.user_id)

    try:
        # Validate topic
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            )

        # Get versions from repository
        versions = await prompt_repo.list_versions(coaching_topic)

        if not versions:
            logger.warning("No versions found for topic", topic=topic)
            return ApiResponse(
                success=True,
                data=PromptTemplateVersionsResponse(
                    topic=topic,
                    versions=[],
                    latestVersion="",
                ),
            )

        # Get latest version marker
        latest_version_marker = await prompt_repo._get_latest_version_marker(coaching_topic)
        latest_version = latest_version_marker if latest_version_marker else versions[0]

        # Build version info list
        version_infos = []
        for version in versions:
            # In a real implementation, we'd get actual metadata from S3
            # For now, create placeholder data
            version_info = TemplateVersionInfo(
                version=version,
                isLatest=(version == latest_version),
                createdAt=datetime.now(timezone.utc),  # Placeholder
                lastModified=datetime.now(timezone.utc),  # Placeholder
                sizeBytes=0,  # Placeholder
            )
            version_infos.append(version_info)

        response_data = PromptTemplateVersionsResponse(
            topic=topic,
            versions=version_infos,
            latestVersion=latest_version,
        )

        logger.info(
            "Template versions retrieved",
            topic=topic,
            version_count=len(versions),
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch template versions",
            topic=topic,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to retrieve template versions for topic: {topic}",
        )


@router.get(
    "/prompts/{topic}/{version}",
    response_model=ApiResponse[PromptTemplateDetail],
)
async def get_template_content(
    topic: str = Path(..., description="Coaching topic identifier"),
    version: str = Path(..., description="Template version"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[PromptTemplateDetail]:
    """
    Get detailed prompt template content for editing.

    This endpoint retrieves the full content of a specific template version,
    including system prompts, user prompt templates, and parameters.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `topic`: Coaching topic identifier
    - `version`: Template version (or "latest")

    **Returns:**
    - Complete template content
    - Template configuration and parameters
    - Metadata
    """
    logger.info(
        "Fetching template content",
        topic=topic,
        version=version,
        admin_user_id=context.user_id,
    )

    try:
        # Validate topic
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            )

        # Get template from repository
        template = await prompt_repo.get_by_topic(coaching_topic, version)

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found for topic '{topic}' version '{version}'",
            )

        # Convert to response format
        response_data = PromptTemplateDetail(
            templateId=template.template_id,
            topic=template.topic.value,
            version=version,
            systemPrompt=template.system_prompt,
            userPromptTemplate=template.user_prompt_template,
            model=template.model,
            parameters=template.parameters,
            metadata=template.metadata,
            createdAt=datetime.now(timezone.utc),  # Placeholder
            lastModified=datetime.now(timezone.utc),  # Placeholder
        )

        logger.info(
            "Template content retrieved",
            topic=topic,
            version=version,
            template_id=template.template_id,
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to fetch template content",
            topic=topic,
            version=version,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to retrieve template content for topic '{topic}' version '{version}'",
        )


__all__ = ["router"]
