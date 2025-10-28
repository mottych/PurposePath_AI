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

    display_name: str | None = Field(
        None,
        description="Human-readable model name",
        min_length=1,
        max_length=200,
    )
    is_active: bool | None = Field(
        None,
        description="Whether model is active",
    )
    input_cost_per_1k_tokens: float | None = Field(
        None,
        description="Cost per 1000 input tokens in USD",
        ge=0,
    )
    output_cost_per_1k_tokens: float | None = Field(
        None,
        description="Cost per 1000 output tokens in USD",
        ge=0,
    )
    context_window: int | None = Field(
        None,
        description="Maximum context window size",
        gt=0,
    )
    max_tokens: int | None = Field(
        None,
        description="Maximum output tokens",
        gt=0,
    )
    supports_streaming: bool | None = Field(
        None,
        description="Whether model supports streaming",
    )
    metadata: dict[str, Any] | None = Field(
        None,
        description="Additional metadata",
    )
    reason: str | None = Field(
        None,
        description="Reason for configuration update",
        max_length=500,
    )

    model_config = {"populate_by_name": True}


__all__ = [
    "CreateTemplateVersionRequest",
    "SetLatestVersionRequest",
    "UpdateModelConfigRequest",
    "UpdateTemplateRequest",
]
