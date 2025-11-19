"""Admin API routes for AI model and topic management."""

from typing import Any

import structlog
from coaching.src.api.dependencies import get_model_config_service
from coaching.src.api.middleware.admin_auth import require_admin_access
from coaching.src.core.llm_models import LLMProvider, list_models
from coaching.src.models.admin_requests import UpdateModelConfigRequest
from coaching.src.models.admin_responses import (
    LLMModelInfo,
    LLMModelsResponse,
)
from coaching.src.services.audit_log_service import AuditLogService
from coaching.src.services.model_config_service import ModelConfigService
from fastapi import APIRouter, Body, Depends, HTTPException, Path

from shared.models.multitenant import RequestContext
from shared.models.schemas import ApiResponse

logger = structlog.get_logger()
router = APIRouter()


@router.get("/models", response_model=ApiResponse[LLMModelsResponse])
async def list_ai_models(
    provider: str | None = None,
    active_only: bool = True,
    capability: str | None = None,
    context: RequestContext = Depends(require_admin_access),
) -> ApiResponse[LLMModelsResponse]:
    """
    Get all supported LLM models from MODEL_REGISTRY.

    This endpoint returns configuration for all AI models available in the system,
    including pricing, capabilities, and active status. Data is sourced from
    MODEL_REGISTRY in coaching/src/core/llm_models.py.

    **Permissions Required:** ADMIN_ACCESS

    **Query Parameters:**
    - provider: Filter by provider (bedrock, anthropic, openai)
    - active_only: Only return active models (default: true)
    - capability: Filter by capability (chat, analysis, streaming, function_calling, vision)

    **Returns:**
    - List of available LLM models
    - List of unique providers
    - Total count of models
    """
    logger.info(
        "Fetching LLM models from MODEL_REGISTRY",
        admin_user_id=context.user_id,
        provider=provider,
        active_only=active_only,
        capability=capability,
    )

    try:
        # Convert provider string to enum if provided
        provider_enum = None
        if provider:
            try:
                provider_enum = LLMProvider(provider.lower())
            except ValueError:
                valid_providers = [p.value for p in LLMProvider]
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider '{provider}'. Valid providers: {valid_providers}",
                ) from None

        # Get models from MODEL_REGISTRY
        registry_models = list_models(
            provider=provider_enum,
            active_only=active_only,
            capability=capability,
        )

        # Convert to response format
        model_infos = [
            LLMModelInfo(
                code=model.code,
                provider=model.provider.value,
                modelName=model.model_name,
                version=model.version,
                capabilities=model.capabilities,
                maxTokens=model.max_tokens,
                costPer1kTokens=model.cost_per_1k_tokens,
                isActive=model.is_active,
            )
            for model in registry_models
        ]

        # Get unique providers
        unique_providers = sorted({model.provider.value for model in registry_models})

        response_data = LLMModelsResponse(
            models=model_infos,
            providers=unique_providers,
            totalCount=len(model_infos),
        )

        logger.info(
            "LLM models retrieved from MODEL_REGISTRY",
            admin_user_id=context.user_id,
            total_count=len(model_infos),
            providers=unique_providers,
        )

        return ApiResponse(success=True, data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing LLM models", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list LLM models") from e


@router.put("/models/{model_id}", response_model=ApiResponse[dict[str, Any]])
async def update_model_configuration(
    model_id: str = Path(..., description="Unique model identifier"),
    request: UpdateModelConfigRequest = Body(...),
    context: RequestContext = Depends(require_admin_access),
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
