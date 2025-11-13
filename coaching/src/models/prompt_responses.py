"""Response models for prompt admin API endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class ParameterDefinitionResponse(BaseModel):
    """Parameter definition in API responses."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter data type")
    required: bool = Field(..., description="Whether parameter is required")
    description: str | None = Field(None, description="Parameter description")
    default: Any = Field(None, description="Default value")


class TopicResponse(BaseModel):
    """Topic response model for list and get operations."""

    topic_id: str = Field(..., description="Unique topic identifier")
    topic_name: str = Field(..., description="Human-readable topic name")
    topic_type: str = Field(..., description="Topic type")
    category: str = Field(..., description="Topic category")
    description: str | None = Field(None, description="Topic description")
    display_order: int = Field(..., description="Display order")
    is_active: bool = Field(..., description="Active status")
    available_prompts: list[str] = Field(
        ..., description="List of prompt types that exist for this topic"
    )
    allowed_parameters: list[ParameterDefinitionResponse] = Field(
        ..., description="Allowed parameters"
    )
    config: dict[str, Any] = Field(..., description="Topic configuration")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    created_by: str | None = Field(None, description="Creator user ID")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")


class PromptDetailResponse(BaseModel):
    """Prompt content response for get/edit operations."""

    topic_id: str = Field(..., description="Parent topic identifier")
    prompt_type: str = Field(..., description="Prompt type")
    content: str = Field(..., description="Markdown prompt content")
    allowed_parameters: list[ParameterDefinitionResponse] = Field(
        ..., description="Parameters available for this prompt"
    )
    s3_location: dict[str, str] = Field(..., description="S3 storage location (bucket, key)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")
    updated_by: str = Field(..., description="Last updater user ID")


__all__ = [
    "ParameterDefinitionResponse",
    "PromptDetailResponse",
    "TopicResponse",
]
