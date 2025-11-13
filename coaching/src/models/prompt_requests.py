"""Request models for prompt admin API endpoints."""

from typing import Any

from pydantic import BaseModel, Field


class ParameterDefinitionRequest(BaseModel):
    """Parameter definition in API requests."""

    name: str = Field(
        ...,
        pattern=r"^[a-z_][a-z0-9_]*$",
        min_length=2,
        max_length=64,
        description="Parameter name in snake_case",
    )
    type: str = Field(
        ...,
        pattern=r"^(string|number|boolean|array|object)$",
        description="Parameter data type",
    )
    required: bool = Field(..., description="Whether parameter is required")
    description: str | None = Field(None, max_length=500, description="Parameter description")
    default: Any = Field(None, description="Default value if not provided")


class TopicConfigRequest(BaseModel):
    """Topic configuration for LLM settings."""

    default_model: str = Field(
        ..., min_length=1, max_length=128, description="Default LLM model identifier"
    )
    supports_streaming: bool = Field(..., description="Whether topic supports streaming responses")
    max_turns: int | None = Field(None, ge=1, le=100, description="Maximum conversation turns")
    temperature: float | None = Field(None, ge=0.0, le=1.0, description="LLM temperature setting")
    max_tokens: int | None = Field(None, gt=0, le=100000, description="Maximum tokens per response")


class CreateTopicRequest(BaseModel):
    """Request to create a new topic."""

    topic_id: str = Field(
        ...,
        pattern=r"^[a-z0-9_]+$",
        min_length=3,
        max_length=64,
        description="Unique topic identifier in snake_case",
    )
    topic_name: str = Field(
        ..., min_length=3, max_length=128, description="Human-readable topic name"
    )
    topic_type: str = Field(
        ...,
        pattern=r"^kpi_system$",
        description="Topic type (only kpi_system allowed via API)",
    )
    category: str = Field(
        ...,
        pattern=r"^(coaching|analysis|strategy|kpi)$",
        description="Topic category for grouping",
    )
    description: str | None = Field(None, max_length=1000, description="Detailed topic description")
    allowed_parameters: list[ParameterDefinitionRequest] = Field(
        ..., description="List of allowed parameters for this topic"
    )
    config: TopicConfigRequest = Field(..., description="LLM configuration settings")
    display_order: int = Field(default=100, ge=0, le=9999, description="Sort order for UI display")
    is_active: bool = Field(default=True, description="Whether topic is active and available")


class UpdateTopicRequest(BaseModel):
    """Request to update topic metadata (partial update)."""

    topic_name: str | None = Field(None, min_length=3, max_length=128, description="New topic name")
    description: str | None = Field(None, max_length=1000, description="New description")
    allowed_parameters: list[ParameterDefinitionRequest] | None = Field(
        None, description="Updated parameter definitions"
    )
    config: TopicConfigRequest | None = Field(None, description="Updated configuration settings")
    display_order: int | None = Field(None, ge=0, le=9999, description="New display order")
    is_active: bool | None = Field(None, description="New active status")


class CreatePromptRequest(BaseModel):
    """Request to create or update prompt content."""

    content: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Markdown prompt content with {{parameter}} placeholders",
    )


__all__ = [
    "CreatePromptRequest",
    "CreateTopicRequest",
    "ParameterDefinitionRequest",
    "TopicConfigRequest",
    "UpdateTopicRequest",
]
