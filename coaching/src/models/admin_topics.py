"""Request and response models for admin topic management API."""

from datetime import datetime
from typing import Literal

from coaching.src.core.constants import PromptType, TierLevel
from pydantic import BaseModel, Field, field_validator

# Conversation Config (for coaching topics only)


class ConversationConfig(BaseModel):
    """Configuration settings for conversation coaching topics.

    Only applicable when topic_type is 'conversation_coaching'.
    These settings control the behavior of multi-turn coaching sessions.
    """

    max_messages_to_llm: int = Field(
        default=30,
        ge=5,
        le=100,
        description="Maximum messages to include in LLM context (sliding window)",
    )
    inactivity_timeout_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Minutes of inactivity before session auto-pauses",
    )
    session_ttl_days: int = Field(
        default=14,
        ge=1,
        le=90,
        description="Days to keep paused/completed sessions before deletion",
    )
    max_turns: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Maximum conversation turns (0 = unlimited)",
    )


# Request Models


class CreateTopicRequest(BaseModel):
    """Request to create a new topic."""

    topic_id: str = Field(..., min_length=3, max_length=50, description="Unique topic identifier")
    topic_name: str = Field(..., min_length=3, max_length=100, description="Display name")
    category: str = Field(..., min_length=3, max_length=50, description="Topic category")
    topic_type: str = Field(..., description="Topic type")
    description: str | None = Field(None, max_length=500, description="Topic description")
    tier_level: TierLevel = Field(
        TierLevel.FREE, description="Subscription tier required to access"
    )
    basic_model_code: str = Field(..., description="LLM model for Free/Basic tiers")
    premium_model_code: str = Field(..., description="LLM model for Premium/Ultimate tiers")
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
    tier_level: TierLevel | None = Field(None, description="Subscription tier required to access")
    basic_model_code: str | None = Field(None, description="LLM model for Free/Basic tiers")
    premium_model_code: str | None = Field(None, description="LLM model for Premium/Ultimate tiers")
    temperature: float | None = Field(None, ge=0.0, le=2.0, description="Model temperature")
    max_tokens: int | None = Field(None, gt=0, description="Maximum tokens")
    top_p: float | None = Field(None, ge=0.0, le=1.0, description="Top-p sampling")
    frequency_penalty: float | None = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float | None = Field(None, ge=-2.0, le=2.0, description="Presence penalty")
    is_active: bool | None = Field(None, description="Whether topic is active")
    display_order: int | None = Field(None, description="Display order")
    # Conversation config - only applicable for conversation_coaching topics
    conversation_config: ConversationConfig | None = Field(
        None,
        description="Conversation settings (only for conversation_coaching topics)",
    )


class CreatePromptRequest(BaseModel):
    """Request to create a new prompt."""

    prompt_type: str = Field(
        ...,
        description=f"Prompt type. Valid values: {', '.join(pt.value for pt in PromptType)}",
    )
    content: str = Field(..., min_length=1, max_length=50000, description="Prompt markdown content")

    @field_validator("prompt_type")
    @classmethod
    def validate_prompt_type(cls, v: str) -> str:
        """Validate prompt_type is one of allowed PromptType enum values."""
        allowed = {pt.value for pt in PromptType}
        if v not in allowed:
            raise ValueError(f"prompt_type must be one of: {', '.join(sorted(allowed))}")
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
    tier_level: TierLevel = Field(TierLevel.FREE, description="Subscription tier required")
    basic_model_code: str = Field(..., description="LLM model for Free/Basic tiers")
    premium_model_code: str = Field(..., description="LLM model for Premium/Ultimate tiers")
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
    tier_level: str = Field(..., description="Subscription tier required to access")
    basic_model_code: str = Field(..., description="LLM model for Free/Basic tiers")
    premium_model_code: str = Field(..., description="LLM model for Premium/Ultimate tiers")
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
    tier_level: str = Field(..., description="Subscription tier required to access")
    basic_model_code: str = Field(..., description="LLM model for Free/Basic tiers")
    premium_model_code: str = Field(..., description="LLM model for Premium/Ultimate tiers")
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
    # Conversation config - only present for conversation_coaching topics
    conversation_config: ConversationConfig | None = Field(
        None,
        description="Conversation settings (only for conversation_coaching topics)",
    )
    # Response schema - only present when include_schema=true query param is set
    response_schema: dict[str, object] | None = Field(
        None,
        description="JSON schema of the expected response model (when include_schema=true)",
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


# Admin Health Check Models


class HealthIssue(BaseModel):
    """Health check issue or warning."""

    code: str = Field(..., description="Issue code")
    message: str = Field(..., description="Issue description")
    severity: Literal["critical", "warning"] = Field(..., description="Issue severity")


class HealthRecommendation(BaseModel):
    """Health check recommendation."""

    code: str = Field(..., description="Recommendation code")
    message: str = Field(..., description="Recommendation message")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority level")


class ServiceHealthStatus(BaseModel):
    """Health status for a specific service."""

    status: Literal["operational", "degraded", "down"] = Field(..., description="Service status")
    last_check: str = Field(..., description="Last check timestamp (ISO 8601)")
    response_time_ms: int = Field(..., description="Service response time in milliseconds")


class ServiceStatuses(BaseModel):
    """Health status for all monitored services."""

    configurations: ServiceHealthStatus = Field(..., description="LLM configurations service")
    templates: ServiceHealthStatus = Field(..., description="Prompt templates service")
    models: ServiceHealthStatus = Field(..., description="AI models service")


class AdminHealthResponse(BaseModel):
    """Response for admin health check endpoint."""

    overall_status: Literal["healthy", "warnings", "errors", "critical"] = Field(
        ..., description="Overall system health status"
    )
    validation_status: Literal["healthy", "warnings", "errors"] = Field(
        ..., description="Validation checks status"
    )
    last_validation: str = Field(..., description="Last validation timestamp (ISO 8601)")
    critical_issues: list[HealthIssue] = Field(
        default_factory=list, description="Critical issues requiring immediate attention"
    )
    warnings: list[HealthIssue] = Field(default_factory=list, description="Warnings to address")
    recommendations: list[HealthRecommendation] = Field(
        default_factory=list, description="System improvement recommendations"
    )
    service_status: ServiceStatuses = Field(..., description="Individual service health status")


# Admin Stats Models


class TrendDataPoint(BaseModel):
    """Single data point in a trend series."""

    date: str = Field(..., description="Date (ISO 8601)")
    value: int = Field(..., description="Value for this date")


class InteractionStats(BaseModel):
    """Statistics about LLM interactions."""

    total: int = Field(..., description="Total number of interactions")
    by_tier: dict[str, int] = Field(..., description="Interaction count by tier")
    by_model: dict[str, int] = Field(..., description="Interaction count by model")
    trend: list[TrendDataPoint] = Field(default_factory=list, description="Trend data over time")


class TemplateStats(BaseModel):
    """Statistics about prompt templates."""

    total: int = Field(..., description="Total number of templates")
    active: int = Field(..., description="Number of active templates")
    inactive: int = Field(..., description="Number of inactive templates")


class ModelStats(BaseModel):
    """Statistics about AI models."""

    total: int = Field(..., description="Total number of models")
    active: int = Field(..., description="Number of active models")
    utilization: dict[str, int] = Field(..., description="Usage count per model")


class AdminStatsResponse(BaseModel):
    """Response for admin stats dashboard endpoint."""

    interactions: InteractionStats = Field(..., description="Interaction statistics")
    templates: TemplateStats = Field(..., description="Template statistics")
    models: ModelStats = Field(..., description="Model statistics")
    system_health: AdminHealthResponse = Field(..., description="System health status")
    last_updated: str = Field(..., description="Last update timestamp (ISO 8601)")
