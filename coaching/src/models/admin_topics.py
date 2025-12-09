"""Request and response models for admin topic management API."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Request Models


class CreateTopicRequest(BaseModel):
    """Request to create a new topic."""

    topic_id: str = Field(..., min_length=3, max_length=50, description="Unique topic identifier")
    topic_name: str = Field(..., min_length=3, max_length=100, description="Display name")
    category: str = Field(..., min_length=3, max_length=50, description="Topic category")
    topic_type: str = Field(..., description="Topic type")
    description: str | None = Field(None, max_length=500, description="Topic description")
    model_code: str = Field(..., description="LLM model code")
    temperature: float = Field(..., ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int = Field(..., gt=0, description="Maximum tokens")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Top-p sampling")
    frequency_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    is_active: bool = Field(False, description="Whether topic is active")
    display_order: int = Field(100, description="Display order")

    @field_validator("topic_id")
    @classmethod
    def validate_topic_id(cls, v: str) -> str:
        """Validate topic_id is snake_case."""
        if not v.islower() or not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("topic_id must be lowercase snake_case")
        return v

    @field_validator("topic_type")
    @classmethod
    def validate_topic_type(cls, v: str) -> str:
        """Validate topic_type is one of allowed values."""
        allowed = {"conversation_coaching", "single_shot", "kpi_system"}
        if v not in allowed:
            raise ValueError(f"topic_type must be one of: {', '.join(allowed)}")
        return v


class UpdateTopicRequest(BaseModel):
    """Request to update an existing topic."""

    topic_name: str | None = Field(None, min_length=3, max_length=100, description="Display name")
    description: str | None = Field(None, max_length=500, description="Topic description")
    model_code: str | None = Field(None, description="LLM model code")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="Top-p sampling")
    frequency_penalty: float | None = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float | None = Field(None, ge=-2.0, le=2.0, description="Presence penalty")
    is_active: bool | None = Field(None, description="Whether topic is active")
    display_order: int | None = Field(None, description="Display order")


class CreatePromptRequest(BaseModel):
    """Request to create a new prompt."""

    prompt_type: str = Field(..., description="Prompt type (system, user, assistant)")
    content: str = Field(..., min_length=1, max_length=50000, description="Prompt markdown content")

    @field_validator("prompt_type")
    @classmethod
    def validate_prompt_type(cls, v: str) -> str:
        """Validate prompt_type is one of allowed values."""
        allowed = {"system", "user", "assistant"}
        if v not in allowed:
            raise ValueError(f"prompt_type must be one of: {', '.join(allowed)}")
        return v


class UpdatePromptRequest(BaseModel):
    """Request to update prompt content."""

    content: str = Field(..., min_length=1, max_length=50000, description="Prompt markdown content")
    commit_message: str | None = Field(None, max_length=200, description="Optional commit message")


class ValidateTopicRequest(BaseModel):
    """Request to validate topic configuration."""

    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Display name")
    category: str = Field(..., description="Topic category")
    topic_type: str = Field(..., description="Topic type")
    model_code: str = Field(..., description="LLM model code")
    temperature: float = Field(..., description="Model temperature")
    max_tokens: int = Field(..., description="Maximum tokens")
    prompts: list[dict[str, str]] = Field(default_factory=list, description="Prompts to validate")


# Response Models


class PromptInfo(BaseModel):
    """Information about a prompt."""

    prompt_type: str = Field(..., description="Prompt type")
    s3_bucket: str = Field(..., description="S3 bucket name")
    s3_key: str = Field(..., description="S3 object key")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    updated_by: str | None = Field(None, description="User who last updated")


class ParameterDefinition(BaseModel):
    """Definition of an allowed parameter."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    required: bool = Field(..., description="Whether parameter is required")
    description: str | None = Field(None, description="Parameter description")


class TemplateSummary(BaseModel):
    """Summary of a prompt template for list view."""

    prompt_type: str = Field(..., description="Prompt type (system, user, assistant)")
    is_defined: bool = Field(..., description="Whether this prompt has been uploaded to S3")


class TemplateStatus(BaseModel):
    """Full status of a prompt template for detail view."""

    prompt_type: str = Field(..., description="Prompt type (system, user, assistant)")
    is_defined: bool = Field(..., description="Whether this prompt has been uploaded to S3")
    s3_bucket: str | None = Field(None, description="S3 bucket if defined")
    s3_key: str | None = Field(None, description="S3 key if defined")
    updated_at: datetime | None = Field(None, description="Last update if defined")
    updated_by: str | None = Field(None, description="Last updater if defined")


class TopicSummary(BaseModel):
    """Summary information about a topic."""

    topic_id: str = Field(..., description="Unique topic identifier")
    topic_name: str = Field(..., description="Display name")
    category: str = Field(..., description="Topic category")
    topic_type: str = Field(..., description="Topic type")
    model_code: str = Field(..., description="LLM model code")
    temperature: float = Field(..., description="Model temperature")
    max_tokens: int = Field(..., description="Maximum tokens")
    is_active: bool = Field(..., description="Whether topic is active")
    description: str | None = Field(None, description="Topic description")
    display_order: int = Field(..., description="Display order")
    from_database: bool = Field(
        ..., description="Whether topic data comes from database (True) or registry (False)"
    )
    templates: list[TemplateSummary] = Field(
        ..., description="Allowed templates with their definition status"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str | None = Field(None, description="Creator user ID")


class TopicDetail(BaseModel):
    """Detailed information about a topic including prompts."""

    topic_id: str = Field(..., description="Unique topic identifier")
    topic_name: str = Field(..., description="Display name")
    category: str = Field(..., description="Topic category")
    topic_type: str = Field(..., description="Topic type")
    description: str | None = Field(None, description="Topic description")
    model_code: str = Field(..., description="LLM model code")
    temperature: float = Field(..., description="Model temperature")
    max_tokens: int = Field(..., description="Maximum tokens")
    top_p: float = Field(..., description="Top-p sampling")
    frequency_penalty: float = Field(..., description="Frequency penalty")
    presence_penalty: float = Field(..., description="Presence penalty")
    is_active: bool = Field(..., description="Whether topic is active")
    display_order: int = Field(..., description="Display order")
    from_database: bool = Field(
        ..., description="Whether topic data comes from database (True) or registry (False)"
    )
    prompts: list[PromptInfo] = Field(..., description="Associated prompts (defined in S3)")
    template_status: list[TemplateStatus] = Field(
        ...,
        description="Status of all allowed templates - shows which are allowed and which are defined",
    )
    allowed_parameters: list[ParameterDefinition] = Field(
        ..., description="Allowed prompt parameters computed from endpoint registry"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str | None = Field(None, description="Creator user ID")


class TopicListResponse(BaseModel):
    """Response for listing topics."""

    topics: list[TopicSummary] = Field(..., description="List of topics")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    has_more: bool = Field(..., description="Whether more pages exist")


class CreateTopicResponse(BaseModel):
    """Response after creating a topic."""

    topic_id: str = Field(..., description="Created topic ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Success message")


class UpdateTopicResponse(BaseModel):
    """Response after updating a topic."""

    topic_id: str = Field(..., description="Updated topic ID")
    updated_at: datetime = Field(..., description="Update timestamp")
    message: str = Field(..., description="Success message")


class UpsertTopicResponse(BaseModel):
    """Response after upserting (create or update) a topic."""

    topic_id: str = Field(..., description="Topic ID")
    created: bool = Field(..., description="True if created, False if updated")
    timestamp: datetime = Field(..., description="Creation or update timestamp")
    message: str = Field(..., description="Success message")


class DeleteTopicResponse(BaseModel):
    """Response after deleting a topic."""

    topic_id: str = Field(..., description="Deleted topic ID")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    message: str = Field(..., description="Success message")


class PromptContentResponse(BaseModel):
    """Response with prompt content."""

    topic_id: str = Field(..., description="Topic identifier")
    prompt_type: str = Field(..., description="Prompt type")
    content: str = Field(..., description="Prompt markdown content")
    s3_key: str = Field(..., description="S3 object key")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    updated_by: str | None = Field(None, description="User who last updated")


class UpdatePromptResponse(BaseModel):
    """Response after updating a prompt."""

    topic_id: str = Field(..., description="Topic identifier")
    prompt_type: str = Field(..., description="Prompt type")
    s3_key: str = Field(..., description="S3 object key")
    updated_at: datetime = Field(..., description="Update timestamp")
    version: str | None = Field(None, description="Version identifier")
    message: str = Field(..., description="Success message")


class CreatePromptResponse(BaseModel):
    """Response after creating a prompt."""

    topic_id: str = Field(..., description="Topic identifier")
    prompt_type: str = Field(..., description="Prompt type")
    s3_key: str = Field(..., description="S3 object key")
    created_at: datetime = Field(..., description="Creation timestamp")
    message: str = Field(..., description="Success message")


class DeletePromptResponse(BaseModel):
    """Response after deleting a prompt."""

    message: str = Field(..., description="Success message")


class ModelInfo(BaseModel):
    """Information about an LLM model."""

    model_code: str = Field(..., description="Model code identifier")
    model_name: str = Field(..., description="Human-readable model name")
    provider: str = Field(..., description="Model provider")
    capabilities: list[str] = Field(..., description="Model capabilities")
    context_window: int = Field(..., description="Context window size")
    max_output_tokens: int = Field(..., description="Maximum output tokens")
    cost_per_input_million: float = Field(..., description="Cost per million input tokens (USD)")
    cost_per_output_million: float = Field(..., description="Cost per million output tokens (USD)")
    is_active: bool = Field(..., description="Whether model is active")


class ModelsListResponse(BaseModel):
    """Response for listing available models."""

    models: list[ModelInfo] = Field(..., description="Available models")


class ValidationResult(BaseModel):
    """Result of topic configuration validation."""

    valid: bool = Field(..., description="Whether configuration is valid")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    errors: list[dict[str, str]] = Field(default_factory=list, description="Validation errors")


class ValidationErrorDetail(BaseModel):
    """Detailed validation error."""

    field: str = Field(..., description="Field with error")
    message: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")


class ValidationErrorResponse(BaseModel):
    """Response for validation errors."""

    error: str = Field(..., description="Error message")
    validation_errors: list[ValidationErrorDetail] = Field(..., description="Detailed errors")
