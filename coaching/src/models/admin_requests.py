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


class ValidateTemplateRequest(BaseModel):
    """Request to validate a template before saving."""

    system_prompt: str = Field(
        ..., description="System prompt content", min_length=10, max_length=5000
    )
    user_prompt_template: str = Field(
        ..., description="User prompt template", min_length=10, max_length=5000
    )
    parameters: dict[str, dict[str, str]] = Field(
        ...,
        description="Template parameters with display_name and description",
    )

    model_config = {"populate_by_name": True}


class TestTemplateRequest(BaseModel):
    """Request to test a template with sample parameter values."""

    parameters: dict[str, str] = Field(..., description="Parameter values for testing")

    model_config = {"populate_by_name": True}


class ValidateConfigurationRequest(BaseModel):
    """Request to validate a configuration before creation."""

    interaction_code: str = Field(..., description="Interaction code")
    template_id: str = Field(..., description="Template ID")
    model_code: str = Field(..., description="Model code")
    tier: str | None = Field(None, description="Optional tier restriction")

    model_config = {"populate_by_name": True}


class CreateConfigurationRequest(BaseModel):
    """Request to create a new LLM configuration."""

    interaction_code: str = Field(..., description="Interaction code", alias="interactionCode")
    template_id: str = Field(
        ..., description="Template ID (format: topic/version)", alias="templateId"
    )
    model_code: str = Field(..., description="Model code", alias="modelCode")
    tier: str | None = Field(None, description="Optional tier restriction")
    temperature: float = Field(0.7, description="LLM temperature (0.0-2.0)", ge=0.0, le=2.0)
    max_tokens: int = Field(2000, description="Max output tokens", gt=0, alias="maxTokens")
    top_p: float = Field(1.0, description="Top-p sampling (0.0-1.0)", ge=0.0, le=1.0, alias="topP")
    frequency_penalty: float = Field(
        0.0, description="Frequency penalty (-2.0-2.0)", ge=-2.0, le=2.0, alias="frequencyPenalty"
    )
    presence_penalty: float = Field(
        0.0, description="Presence penalty (-2.0-2.0)", ge=-2.0, le=2.0, alias="presencePenalty"
    )
    effective_from: str | None = Field(
        None, description="Effective from date (ISO format)", alias="effectiveFrom"
    )
    effective_until: str | None = Field(
        None, description="Effective until date (ISO format)", alias="effectiveUntil"
    )

    model_config = {"populate_by_name": True}


class UpdateConfigurationRequest(BaseModel):
    """Request to update an existing configuration."""

    template_id: str | None = Field(
        None, description="Template ID (topic/version)", alias="templateId"
    )
    model_code: str | None = Field(None, description="Model code", alias="modelCode")
    temperature: float | None = Field(None, description="LLM temperature", ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, description="Max output tokens", gt=0, alias="maxTokens")
    top_p: float | None = Field(None, description="Top-p sampling", ge=0.0, le=1.0, alias="topP")
    frequency_penalty: float | None = Field(
        None, description="Frequency penalty", ge=-2.0, le=2.0, alias="frequencyPenalty"
    )
    presence_penalty: float | None = Field(
        None, description="Presence penalty", ge=-2.0, le=2.0, alias="presencePenalty"
    )
    effective_from: str | None = Field(
        None, description="Effective from date", alias="effectiveFrom"
    )
    effective_until: str | None = Field(
        None, description="Effective until date", alias="effectiveUntil"
    )

    model_config = {"populate_by_name": True}


__all__ = [
    "CreateConfigurationRequest",
    "CreateTemplateVersionRequest",
    "SetLatestVersionRequest",
    "TestTemplateRequest",
    "UpdateConfigurationRequest",
    "UpdateModelConfigRequest",
    "UpdateTemplateRequest",
    "ValidateConfigurationRequest",
    "ValidateTemplateRequest",
]
