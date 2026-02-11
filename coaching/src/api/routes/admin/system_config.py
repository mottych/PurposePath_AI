"""Admin API routes for system configuration management.

Endpoint Usage:
- GET /admin/system/default-models: Get current default model codes
- PUT /admin/system/default-models: Update default model codes (requires admin)
"""

from typing import Any

import structlog
from coaching.src.api.auth import get_current_context
from coaching.src.api.models.auth import UserContext
from coaching.src.core.llm_models import MODEL_REGISTRY
from coaching.src.services.parameter_store_service import get_parameter_store_service
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger()

router = APIRouter(prefix="/system", tags=["Admin - System Configuration"])


class DefaultModelsResponse(BaseModel):
    """Response model for default model configuration."""

    basic_model_code: str = Field(description="Default model code for Free/Basic tier topics")
    premium_model_code: str = Field(
        description="Default model code for Premium/Ultimate tier topics"
    )
    source: str = Field(description="Configuration source (parameter_store or fallback)")


class UpdateDefaultModelsRequest(BaseModel):
    """Request model for updating default models."""

    basic_model_code: str = Field(
        description="Model code for Free/Basic tier (e.g., CLAUDE_3_5_SONNET_V2)",
        min_length=1,
        max_length=100,
    )
    premium_model_code: str = Field(
        description="Model code for Premium/Ultimate tier (e.g., CLAUDE_OPUS_4_5)",
        min_length=1,
        max_length=100,
    )


class UpdateDefaultModelsResponse(BaseModel):
    """Response model for default models update."""

    success: bool
    message: str
    basic_model_code: str
    premium_model_code: str


@router.get("/default-models", response_model=DefaultModelsResponse)
async def get_default_models(
    _user: UserContext = Depends(get_current_context),
) -> DefaultModelsResponse:
    """Get current default model codes from Parameter Store.

    Returns the default model codes used for topic creation fallback.
    Indicates whether values come from Parameter Store or hardcoded fallback.

    Requires admin:system:read permission.
    """
    try:
        param_service = get_parameter_store_service()
        basic_model, premium_model = param_service.get_default_models()

        # Try to determine source (Parameter Store vs fallback)
        # We check by trying to get from SSM directly
        try:
            import boto3

            ssm_client = boto3.client("ssm", region_name=param_service.region)
            ssm_client.get_parameter(Name=f"{param_service.parameter_prefix}/models/default_basic")
            source = "parameter_store"
        except Exception:
            source = "fallback"

        return DefaultModelsResponse(
            basic_model_code=basic_model,
            premium_model_code=premium_model,
            source=source,
        )

    except Exception as e:
        logger.error("Failed to get default models", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve default models",
        ) from e


@router.put("/default-models", response_model=UpdateDefaultModelsResponse)
async def update_default_models(
    request: UpdateDefaultModelsRequest,
    user: UserContext = Depends(get_current_context),
) -> UpdateDefaultModelsResponse:
    """Update default model codes in Parameter Store.

    Updates the default model codes used as fallback for topic creation.
    Values are stored in AWS Systems Manager Parameter Store and cached
    with 5-minute TTL for performance.

    Validates that model codes exist in MODEL_REGISTRY before updating.

    Requires admin:system:write permission.
    """
    try:
        # Validate model codes exist in MODEL_REGISTRY
        if request.basic_model_code not in MODEL_REGISTRY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid basic_model_code: '{request.basic_model_code}'. "
                f"Must be one of: {', '.join(sorted(MODEL_REGISTRY.keys()))}",
            )

        if request.premium_model_code not in MODEL_REGISTRY:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid premium_model_code: '{request.premium_model_code}'. "
                f"Must be one of: {', '.join(sorted(MODEL_REGISTRY.keys()))}",
            )

        # Update Parameter Store
        param_service = get_parameter_store_service()
        success = param_service.update_default_models(
            basic_model_code=request.basic_model_code,
            premium_model_code=request.premium_model_code,
            updated_by=user.user_id,
        )

        if success:
            logger.info(
                "Default models updated",
                basic_model=request.basic_model_code,
                premium_model=request.premium_model_code,
                updated_by=user.user_id,
            )

            return UpdateDefaultModelsResponse(
                success=True,
                message="Default models updated successfully. New topics will use these models.",
                basic_model_code=request.basic_model_code,
                premium_model_code=request.premium_model_code,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update Parameter Store",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update default models",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update default models",
        ) from e


@router.get("/available-models")
async def list_available_models(
    _user: UserContext = Depends(get_current_context),
) -> dict[str, Any]:
    """List all available model codes from MODEL_REGISTRY.

    Returns model codes with their provider, capabilities, and active status.
    Useful for admins to see valid values for default model configuration.

    Requires admin:system:read permission.
    """

    try:
        models = []
        for code, model in MODEL_REGISTRY.items():
            models.append(
                {
                    "code": code,
                    "model_name": model.model_name,
                    "provider": model.provider.value,
                    "version": model.version,
                    "is_active": model.is_active,
                    "capabilities": model.capabilities,
                    "cost_per_1k_tokens": model.cost_per_1k_tokens,
                }
            )

        # Sort by provider, then by code
        models.sort(key=lambda m: (m["provider"], m["code"]))

        return {
            "models": models,
            "total": len(models),
            "active": sum(1 for m in models if m["is_active"]),
            "inactive": sum(1 for m in models if not m["is_active"]),
        }

    except Exception as e:
        logger.error("Failed to list available models", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list available models",
        ) from e
