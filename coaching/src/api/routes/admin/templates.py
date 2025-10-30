"""Admin API routes for prompt template management."""

from datetime import UTC, datetime

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_prompt_repository
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.constants import CoachingTopic
from coaching.src.domain.entities.prompt_template import PromptTemplate
from coaching.src.infrastructure.repositories.s3_prompt_repository import S3PromptRepository
from coaching.src.models.admin_requests import (
    CreateTemplateVersionRequest,
    SetLatestVersionRequest,
    UpdateTemplateRequest,
)
from coaching.src.models.admin_responses import (
    PromptTemplateDetail,
    PromptTemplateVersionsResponse,
    TemplateVersionInfo,
)
from coaching.src.services.audit_log_service import AuditLogService
from coaching.src.services.template_validation_service import (
    TemplateValidationError,
    TemplateValidationService,
)
from fastapi import APIRouter, Body, Depends, HTTPException, Path

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
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            ) from e

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
                createdAt=datetime.now(UTC),  # Placeholder
                lastModified=datetime.now(UTC),  # Placeholder
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
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            ) from e

        # Get template from repository
        template = await prompt_repo.get_by_topic(coaching_topic, version)

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found for topic '{topic}' version '{version}'",
            )

        # Convert to response format
        # Map domain entity to admin response model
        response_data = PromptTemplateDetail(
            templateId=template.template_id,
            topic=template.topic.value,
            version=version,
            systemPrompt=template.system_prompt,
            userPromptTemplate=template.template_text,
            model="default-model",  # Model comes from LLMConfiguration, not template
            parameters={var: "" for var in template.variables},
            metadata={"phase": template.phase.value, "name": template.name},
            createdAt=template.created_at,
            lastModified=template.updated_at,
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


@router.post(
    "/prompts/{topic}/versions",
    response_model=ApiResponse[PromptTemplateDetail],
    status_code=201,
)
async def create_template_version(
    topic: str = Path(..., description="Coaching topic identifier"),
    request: CreateTemplateVersionRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[PromptTemplateDetail]:
    """
    Create a new prompt template version.

    This endpoint creates a new version of a template, either by copying
    an existing version or by providing complete template content.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `topic`: Coaching topic identifier

    **Request Body:**
    - `version`: New version identifier
    - `source_version`: Optional version to copy from (defaults to 'latest')
    - `system_prompt`: System prompt (if not copying)
    - `user_prompt_template`: User prompt template (if not copying)
    - `model`: AI model (if not copying)
    - `parameters`: Template parameters (if not copying)
    - `reason`: Optional reason for creation

    **Returns:**
    - Created template details
    """
    logger.info(
        "Creating template version",
        topic=topic,
        version=request.version,
        source_version=request.source_version,
        admin_user_id=context.user_id,
    )

    validation_service = TemplateValidationService()
    audit_service = AuditLogService()

    try:
        # Validate topic
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            ) from e

        # Validate version format
        try:
            validation_service.validate_version_format(request.version)
        except TemplateValidationError as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid version format: {e.message}",
            ) from e

        # Check if version already exists
        existing = await prompt_repo.exists(coaching_topic, request.version)
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Version '{request.version}' already exists for topic '{topic}'",
            )

        # Determine if copying or creating from scratch
        if request.system_prompt is not None:
            # Creating from scratch - validate all required fields
            if not request.user_prompt_template or not request.model:
                raise HTTPException(
                    status_code=400,
                    detail="system_prompt, user_prompt_template, and model are required when creating from scratch",
                )

            # Validate template content
            try:
                validation_service.validate_template(
                    topic=coaching_topic,
                    system_prompt=request.system_prompt,
                    user_prompt_template=request.user_prompt_template,
                    model=request.model,
                    parameters=request.parameters,
                )
            except TemplateValidationError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Template validation failed: {e.message}",
                ) from e

            # Create new template entity
            # Map admin request to domain entity
            from coaching.src.core.constants import ConversationPhase
            from coaching.src.core.types import TemplateId
            template = PromptTemplate(
                template_id=TemplateId(f"{topic}_{request.version}"),
                name=f"{topic}_template",
                topic=coaching_topic,
                phase=ConversationPhase.INTRODUCTION,  # Default phase
                system_prompt=request.system_prompt or "You are an AI coaching assistant.",
                template_text=request.user_prompt_template or "",
                variables=list(request.parameters.keys()) if request.parameters else [],
                version=1,
            )

            # Save to repository
            await prompt_repo.save(template, request.version)

            # Log audit event
            await audit_service.log_template_created(
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                topic=topic,
                version=request.version,
                source_version=None,
            )

        else:
            # Copying from existing version
            source_version = request.source_version or "latest"

            # Get source template
            source_template = await prompt_repo.get_by_topic(coaching_topic, source_version)
            if not source_template:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source version '{source_version}' not found for topic '{topic}'",
                )

            # Create new version from source
            template = await prompt_repo.create_new_version(
                topic=coaching_topic,
                source_version=source_version,
                new_version=request.version,
            )

            # Log audit event
            await audit_service.log_template_created(
                user_id=context.user_id,
                tenant_id=context.tenant_id,
                topic=topic,
                version=request.version,
                source_version=source_version,
            )

        # Build response
        # Map domain entity to admin response model
        response_data = PromptTemplateDetail(
            templateId=template.template_id,
            topic=template.topic.value,
            version=request.version,
            systemPrompt=template.system_prompt,
            userPromptTemplate=template.template_text,
            model="default-model",  # Model comes from LLMConfiguration, not template
            parameters={var: "" for var in template.variables},
            metadata={"phase": template.phase.value, "name": template.name},
            createdAt=template.created_at,
            lastModified=template.updated_at,
        )

        logger.info(
            "Template version created",
            topic=topic,
            version=request.version,
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create template version",
            topic=topic,
            version=request.version,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to create template version: {e!s}",
        )


@router.put(
    "/prompts/{topic}/{version}",
    response_model=ApiResponse[PromptTemplateDetail],
)
async def update_template(
    topic: str = Path(..., description="Coaching topic identifier"),
    version: str = Path(..., description="Template version"),
    request: UpdateTemplateRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[PromptTemplateDetail]:
    """
    Update an existing prompt template.

    This endpoint updates specific fields of an existing template version.
    Only provided fields will be updated.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `topic`: Coaching topic identifier
    - `version`: Template version to update

    **Request Body:**
    - `system_prompt`: Updated system prompt (optional)
    - `user_prompt_template`: Updated user prompt template (optional)
    - `model`: Updated AI model (optional)
    - `parameters`: Updated parameters (optional)
    - `metadata`: Updated metadata (optional)
    - `reason`: Optional reason for update

    **Returns:**
    - Updated template details
    """
    logger.info(
        "Updating template",
        topic=topic,
        version=version,
        admin_user_id=context.user_id,
    )

    audit_service = AuditLogService()

    try:
        # Validate topic
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            ) from e

        # Get existing template
        existing_template = await prompt_repo.get_by_topic(coaching_topic, version)
        if not existing_template:
            raise HTTPException(
                status_code=404,
                detail=f"Template not found for topic '{topic}' version '{version}'",
            )

        # Track changes for audit log
        changes: dict[str, str] = {}

        # Map admin request to domain entity updates
        # Domain entity has: system_prompt, template_text, variables, name, phase
        # Admin API has: system_prompt, user_prompt_template, model, parameters, metadata
        # Model comes from LLMConfiguration, not stored in template

        updated_system_prompt = request.system_prompt or existing_template.system_prompt
        updated_template_text = request.user_prompt_template or existing_template.template_text
        updated_variables = (
            list(request.parameters.keys()) if request.parameters is not None
            else existing_template.variables
        )

        # Track what changed
        if request.system_prompt and request.system_prompt != existing_template.system_prompt:
            changes["system_prompt"] = "updated"
        if request.user_prompt_template and request.user_prompt_template != existing_template.template_text:
            changes["template_text"] = "updated"
        if request.parameters is not None:
            changes["parameters"] = "updated"
        if request.model:
            changes["model"] = "noted (comes from LLMConfiguration, not template)"
        if request.metadata is not None:
            changes["metadata"] = "noted (stored in template metadata field)"

        if not changes:
            raise HTTPException(
                status_code=400,
                detail="No changes provided. At least one field must be updated.",
            )

        # Validate updated template (skip for now - validation service expects old interface)
        # TODO: Update validation service to work with domain entity

        # Create updated template entity with domain model
        updated_template = PromptTemplate(
            template_id=existing_template.template_id,
            name=existing_template.name,
            topic=coaching_topic,
            phase=existing_template.phase,
            system_prompt=updated_system_prompt,
            template_text=updated_template_text,
            variables=updated_variables,
            version=existing_template.version,
            is_active=existing_template.is_active,
            created_at=existing_template.created_at,
            updated_at=datetime.now(UTC),
        )

        # Delete old version and save new (S3 doesn't support in-place updates)
        await prompt_repo.delete(coaching_topic, version)
        await prompt_repo.save(updated_template, version)

        # If this was the latest version, reset the marker
        latest_marker = await prompt_repo._get_latest_version_marker(coaching_topic)
        if latest_marker == version:
            await prompt_repo.set_latest(coaching_topic, version)

        # Log audit event
        await audit_service.log_template_updated(
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            topic=topic,
            version=version,
            changes=changes,
            reason=request.reason,
        )

        # Build response - map domain entity back to admin API model
        response_data = PromptTemplateDetail(
            templateId=updated_template.template_id,
            topic=updated_template.topic.value,
            version=version,
            systemPrompt=updated_template.system_prompt,
            userPromptTemplate=updated_template.template_text,
            model="default-model",  # Model comes from LLMConfiguration, not template
            parameters={var: "" for var in updated_template.variables},
            metadata={"phase": updated_template.phase.value, "name": updated_template.name},
            createdAt=updated_template.created_at,
            lastModified=updated_template.updated_at,
        )

        logger.info(
            "Template updated",
            topic=topic,
            version=version,
            changes=list(changes.keys()),
            admin_user_id=context.user_id,
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update template",
            topic=topic,
            version=version,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to update template: {e!s}",
        )


@router.post(
    "/prompts/{topic}/{version}/set-latest",
    response_model=ApiResponse[dict[str, str]],
)
async def set_latest_version(
    topic: str = Path(..., description="Coaching topic identifier"),
    version: str = Path(..., description="Version to set as latest"),
    request: SetLatestVersionRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[dict[str, str]]:
    """
    Set a specific version as the latest for a topic.

    This endpoint marks a version as "latest", which will be used
    when users request templates without specifying a version.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `topic`: Coaching topic identifier
    - `version`: Version to activate as latest

    **Request Body:**
    - `reason`: Optional reason for activation

    **Returns:**
    - Confirmation with previous and new latest versions
    """
    logger.info(
        "Setting latest version",
        topic=topic,
        version=version,
        admin_user_id=context.user_id,
    )

    audit_service = AuditLogService()

    try:
        # Validate topic
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            ) from e

        # Get previous latest version
        previous_latest = await prompt_repo._get_latest_version_marker(coaching_topic)

        # Set new latest version (this will validate that version exists)
        try:
            await prompt_repo.set_latest(coaching_topic, version)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=str(e),
            ) from e

        # Log audit event
        await audit_service.log_version_activated(
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            topic=topic,
            new_version=version,
            previous_version=previous_latest,
            reason=request.reason,
        )

        logger.info(
            "Latest version set",
            topic=topic,
            version=version,
            previous_version=previous_latest,
            admin_user_id=context.user_id,
        )

        return ApiResponse(
            success=True,
            data={
                "message": f"Version '{version}' is now the latest for topic '{topic}'",
                "topic": topic,
                "new_latest": version,
                "previous_latest": previous_latest or "none",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to set latest version",
            topic=topic,
            version=version,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to set latest version: {e!s}",
        )


@router.delete(
    "/prompts/{topic}/{version}",
    response_model=ApiResponse[dict[str, str]],
)
async def delete_template_version(
    topic: str = Path(..., description="Coaching topic identifier"),
    version: str = Path(..., description="Version to delete"),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    prompt_repo: S3PromptRepository = Depends(get_prompt_repository),
) -> ApiResponse[dict[str, str]]:
    """
    Delete a specific template version.

    This endpoint permanently removes a template version from storage.
    Safety checks prevent deletion of the active "latest" version.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `topic`: Coaching topic identifier
    - `version`: Version to delete

    **Returns:**
    - Confirmation of deletion

    **Safety Rules:**
    - Cannot delete version marked as "latest"
    - Must set another version as latest before deleting
    - Returns 404 if version doesn't exist
    - Returns 409 if trying to delete latest version
    """
    logger.info(
        "Deleting template version",
        topic=topic,
        version=version,
        admin_user_id=context.user_id,
    )

    audit_service = AuditLogService()

    try:
        # Validate topic
        try:
            coaching_topic = CoachingTopic(topic)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown coaching topic: {topic}",
            ) from e

        # Attempt to delete
        try:
            deleted = await prompt_repo.delete(coaching_topic, version)
        except ValueError as e:
            # This happens when trying to delete the latest version
            raise HTTPException(
                status_code=409,
                detail=str(e),
            ) from e

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Version '{version}' not found for topic '{topic}'",
            )

        # Log audit event
        await audit_service.log_template_deleted(
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            topic=topic,
            version=version,
        )

        logger.info(
            "Template version deleted",
            topic=topic,
            version=version,
            admin_user_id=context.user_id,
        )

        return ApiResponse(
            success=True,
            data={
                "message": f"Version '{version}' deleted successfully",
                "topic": topic,
                "version": version,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete template version",
            topic=topic,
            version=version,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to delete template version: {e!s}",
        )


__all__ = ["router"]
