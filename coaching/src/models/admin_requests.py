"""Request models for admin API endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class CreateTemplateVersionRequest(BaseModel):
    """Request to create a new template version."""

    version: str = Field(..., description="New version identifier", min_length=1, max_length=50)
    source_version: str | None = Field(
        None,
        description="Optional source version to copy from (defaults to 'latest')",
    )
    system_prompt: str | None = Field(
        None,
        description="System prompt content (if not copying)",
        min_length=10,
        max_length=50000,
    )
    user_prompt_template: str | None = Field(
        None,
        description="User prompt template (if not copying)",
        min_length=1,
        max_length=20000,
    )
    model: str | None = Field(
        None,
        description="Target AI model (if not copying)",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Template parameters (if not copying)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
    )
    reason: str | None = Field(
        None,
        description="Reason for creating this version",
        max_length=500,
    )

    model_config = {"populate_by_name": True}


class UpdateTemplateRequest(BaseModel):
    """Request to update an existing template."""

    system_prompt: str | None = Field(
        None,
        description="Updated system prompt content",
        min_length=10,
        max_length=50000,
    )
    user_prompt_template: str | None = Field(
        None,
        description="Updated user prompt template",
        min_length=1,
        max_length=20000,
    )
    model: str | None = Field(
        None,
        description="Updated target AI model",
    )
    parameters: dict[str, Any] | None = Field(
        None,
        description="Updated template parameters",
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description="Updated metadata",
    )
    reason: str | None = Field(
        None,
        description="Reason for this update",
        max_length=500,
    )

    model_config = {"populate_by_name": True}


class SetLatestVersionRequest(BaseModel):
    """Request to set a version as latest."""

    reason: str | None = Field(
        None,
        description="Reason for setting this version as latest",
        max_length=500,
    )

    model_config = {"populate_by_name": True}


class UpdateModelConfigRequest(BaseModel):
    """Request to update model configuration."""

    is_active: bool | None = Field(
        None,
        description="Whether model is active",
        alias="isActive",
    )
    is_default: bool | None = Field(
        None,
        description="Whether model is default",
        alias="isDefault",
    )
    cost_per_1k_tokens: dict[str, float] | None = Field(
        None,
        description="Token pricing (input/output)",
        alias="costPer1kTokens",
    )
    reason: str | None = Field(
        None,
        description="Reason for configuration update",
        max_length=500,
    )

    model_config = {"populate_by_name": True}


__all__ = [
    "CreateTemplateVersionRequest",
    "UpdateTemplateRequest",
    "SetLatestVersionRequest",
    "UpdateModelConfigRequest",
]
