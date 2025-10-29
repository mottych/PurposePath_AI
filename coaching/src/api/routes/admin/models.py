"""Admin API routes for AI model and topic management."""

from typing import Any

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.dependencies import get_model_config_service
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.constants import CoachingTopic
from coaching.src.models.admin_requests import UpdateModelConfigRequest
from coaching.src.models.admin_responses import (
    AIModelInfo,
    AIModelsResponse,
    AIProviderInfo,
    CoachingTopicInfo,
    ModelCostInfo,
)
from coaching.src.services.audit_log_service import AuditLogService
from coaching.src.services.model_config_service import ModelConfigService
from fastapi import APIRouter, Body, Depends, HTTPException, Path

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/models", response_model=ApiResponse[AIModelsResponse])
async def list_ai_models(
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
) -> ApiResponse[AIModelsResponse]:
    """
    Get all supported LLM providers and their available models.

    This endpoint returns configuration for all AI models available in the system,
    including pricing, capabilities, and active status.

    **Permissions Required:** ADMIN_ACCESS

    **Returns:**
    - List of providers with their models
    - Default provider and model configuration
    - Model capabilities and pricing information
    """
    logger.info("Fetching AI models list", admin_user_id=context.user_id)

    try:
        # Define available models (in production, this could come from config/database)
        models = [
            AIModelInfo(
                id="anthropic.claude-3-5-sonnet-20241022-v2:0",
                name="Claude 3.5 Sonnet",
                provider="Anthropic",
                version="20241022-v2",
                capabilities=["text_generation", "conversation", "analysis"],
                maxTokens=200000,
                costPer1kTokens=ModelCostInfo(input=0.003, output=0.015),
                isActive=True,
                isDefault=True,
            ),
            AIModelInfo(
                id="anthropic.claude-3-haiku-20240307-v1:0",
                name="Claude 3 Haiku",
                provider="Anthropic",
                version="20240307-v1",
                capabilities=["text_generation", "conversation"],
                maxTokens=200000,
                costPer1kTokens=ModelCostInfo(input=0.00025, output=0.00125),
                isActive=True,
                isDefault=False,
            ),
        ]

        provider = AIProviderInfo(
            name="bedrock",
            displayName="Amazon Bedrock",
            isActive=True,
            models=models,
        )

        response_data = AIModelsResponse(
            providers=[provider],
            defaultProvider="bedrock",
            defaultModel="anthropic.claude-3-5-sonnet-20241022-v2:0",
        )

        logger.info(
            "AI models list retrieved",
            admin_user_id=context.user_id,
            provider_count=1,
            model_count=len(models),
        )

        return ApiResponse(success=True, data=response_data)

    except Exception as e:
        logger.error("Error listing AI models", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list AI models") from e


@router.get("/topics", response_model=ApiResponse[list[CoachingTopicInfo]])
async def list_coaching_topics(
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
) -> ApiResponse[list[CoachingTopicInfo]]:
    """
    Get all available coaching topics that have prompt templates.

    This endpoint lists all coaching topics configured in the system,
    along with metadata about their template versions.

    **Permissions Required:** ADMIN_ACCESS

    **Returns:**
    - List of coaching topics
    - Version counts and latest version information
    """
    logger.info("Fetching coaching topics", admin_user_id=context.user_id)

    try:
        # Map CoachingTopic enum to response format
        topics = []
        for topic in CoachingTopic:
            # Create topic info with friendly display names
            display_names = {
                CoachingTopic.CORE_VALUES: "Core Values",
                CoachingTopic.PURPOSE: "Purpose",
                CoachingTopic.VISION: "Vision",
                CoachingTopic.GOALS: "Goals",
            }

            descriptions = {
                CoachingTopic.CORE_VALUES: "Discover and clarify personal core values",
                CoachingTopic.PURPOSE: "Define life and business purpose",
                CoachingTopic.VISION: "Articulate vision for the future",
                CoachingTopic.GOALS: "Set aligned and achievable goals",
            }

            topic_info = CoachingTopicInfo(
                topic=topic.value,
                displayName=display_names.get(topic, topic.value.replace("_", " ").title()),
                description=descriptions.get(topic, f"Templates for {topic.value}"),
                versionCount=1,  # Placeholder - would query S3 in real implementation
                latestVersion="1.0.0",  # Placeholder
            )
            topics.append(topic_info)

        logger.info(
            "Coaching topics retrieved",
            admin_user_id=context.user_id,
            topic_count=len(topics),
        )

        return ApiResponse(success=True, data=topics)

    except Exception as e:
        logger.error("Failed to fetch coaching topics", error=str(e), admin_user_id=context.user_id)
        return ApiResponse(
            success=False,
            data=[],
            error="Failed to retrieve coaching topics",
        )


@router.put("/models/{model_id}", response_model=ApiResponse[dict[str, Any]])
async def update_model_configuration(
    model_id: str = Path(..., description="Unique model identifier"),
    request: UpdateModelConfigRequest = Body(...),
    context: RequestContext = Depends(get_current_context),
    _admin: RequestContext = Depends(require_admin_access),
    model_config_service: ModelConfigService = Depends(get_model_config_service),
) -> ApiResponse[dict[str, Any]]:
    """
    Update configuration for a specific AI model.

    This endpoint allows admins to modify model settings including
    pricing, operational status, and other parameters.

    **Permissions Required:** ADMIN_ACCESS

    **Parameters:**
    - `modelId`: Unique model identifier

    **Request Body:** (all fields optional)
    - `display_name`: Human-readable model name
    - `is_active`: Whether model is available for use
    - `input_cost_per_1k_tokens`: Cost per 1000 input tokens
    - `output_cost_per_1k_tokens`: Cost per 1000 output tokens
    - `context_window`: Maximum context window size
    - `max_tokens`: Maximum output tokens
    - `supports_streaming`: Whether model supports streaming
    - `metadata`: Additional configuration data
    - `reason`: Reason for configuration change

    **Returns:**
    - Confirmation of update with changed fields
    """
    logger.info(
        "Updating model configuration",
        model_id=model_id,
        admin_user_id=context.user_id,
    )

    audit_service = AuditLogService()

    try:
        # Build updates dictionary (exclude None values and reason)
        updates = {}
        request_dict = request.model_dump(exclude_none=True)

        # Remove reason from updates (it's for audit only)
        reason = request_dict.pop("reason", None)

        # Track what changed
        changes: dict[str, str] = {}

        for key, value in request_dict.items():
            updates[key] = value
            changes[key] = f"updated to {value}"

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="No updates provided. At least one field must be changed.",
            )

        # Update the configuration
        try:
            await model_config_service.update_config(model_id, updates)
        except ValueError as e:
            raise HTTPException(
                status_code=404,
                detail=str(e),
            ) from e

        # Log audit event
        await audit_service.log_model_updated(
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            model_id=model_id,
            changes=changes,
            reason=reason,
        )

        logger.info(
            "Model configuration updated",
            model_id=model_id,
            updated_fields=list(updates.keys()),
            admin_user_id=context.user_id,
        )

        return ApiResponse(
            success=True,
            data={
                "message": f"Model '{model_id}' configuration updated successfully",
                "model_id": model_id,
                "updated_fields": list(updates.keys()),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update model configuration",
            model_id=model_id,
            error=str(e),
            admin_user_id=context.user_id,
        )
        return ApiResponse(
            success=False,
            data=None,
            error=f"Failed to update model configuration: {e!s}",
        )


__all__ = ["router"]
