"""Response models for admin API endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# AI Model Management Responses


class ModelCostInfo(BaseModel):
    """Token cost information for a model."""

    input: float = Field(..., description="Cost per 1K input tokens in USD")
    output: float = Field(..., description="Cost per 1K output tokens in USD")


class AIModelInfo(BaseModel):
    """Information about an AI model."""

    id: str = Field(..., description="Unique model identifier")
    name: str = Field(..., description="Human-readable model name")
    provider: str = Field(..., description="Model provider (e.g., Anthropic)")
    version: str = Field(..., description="Model version")
    capabilities: list[str] = Field(..., description="Model capabilities")
    max_tokens: int = Field(..., description="Maximum context tokens", alias="maxTokens")
    cost_per_1k_tokens: ModelCostInfo = Field(
        ..., description="Token pricing", alias="costPer1kTokens"
    )
    is_active: bool = Field(..., description="Whether model is active", alias="isActive")
    is_default: bool = Field(..., description="Whether model is default", alias="isDefault")

    model_config = {"populate_by_name": True}


class AIProviderInfo(BaseModel):
    """Information about an AI provider."""

    name: str = Field(..., description="Provider identifier")
    display_name: str = Field(..., description="Human-readable name", alias="displayName")
    is_active: bool = Field(..., description="Whether provider is active", alias="isActive")
    models: list[AIModelInfo] = Field(..., description="Available models from this provider")

    model_config = {"populate_by_name": True}


class LLMModelInfo(BaseModel):
    """Information about an LLM model from MODEL_REGISTRY."""

    code: str = Field(..., description="Unique model code")
    provider: str = Field(..., description="Provider name")
    model_name: str = Field(
        ..., description="Full model identifier for API calls", alias="modelName"
    )
    version: str = Field(..., description="Model version")
    capabilities: list[str] = Field(..., description="Model capabilities")
    max_tokens: int = Field(..., description="Maximum tokens supported", alias="maxTokens")
    cost_per_1k_tokens: float = Field(
        ..., description="Cost per 1K tokens (USD)", alias="costPer1kTokens"
    )
    is_active: bool = Field(..., description="Whether model is active", alias="isActive")

    model_config = {"populate_by_name": True}


class LLMModelsResponse(BaseModel):
    """Response for listing LLM models from MODEL_REGISTRY."""

    models: list[LLMModelInfo] = Field(..., description="Available LLM models")
    providers: list[str] = Field(..., description="List of unique providers")
    total_count: int = Field(..., description="Total number of models", alias="totalCount")

    model_config = {"populate_by_name": True}


class AIModelsResponse(BaseModel):
    """Response for listing AI models (deprecated - use LLMModelsResponse)."""

    providers: list[AIProviderInfo] = Field(..., description="Available AI providers")
    default_provider: str = Field(..., description="Default provider", alias="defaultProvider")
    default_model: str = Field(..., description="Default model ID", alias="defaultModel")

    model_config = {"populate_by_name": True}


# Template Management Responses


class TemplateVersionInfo(BaseModel):
    """Information about a prompt template version."""

    version: str = Field(..., description="Version identifier")
    is_latest: bool = Field(..., description="Whether this is the latest version", alias="isLatest")
    created_at: datetime = Field(..., description="Creation timestamp", alias="createdAt")
    last_modified: datetime = Field(..., description="Last modification time", alias="lastModified")
    size_bytes: int = Field(..., description="Template size in bytes", alias="sizeBytes")

    model_config = {"populate_by_name": True}


class PromptTemplateVersionsResponse(BaseModel):
    """Response for listing template versions."""

    topic: str = Field(..., description="Coaching topic")
    versions: list[TemplateVersionInfo] = Field(..., description="Available versions")
    latest_version: str = Field(..., description="Current latest version", alias="latestVersion")

    model_config = {"populate_by_name": True}


class PromptTemplateDetail(BaseModel):
    """Detailed prompt template content."""

    template_id: str = Field(..., description="Template identifier", alias="templateId")
    topic: str = Field(..., description="Coaching topic")
    version: str = Field(..., description="Template version")
    system_prompt: str = Field(..., description="System prompt content", alias="systemPrompt")
    user_prompt_template: str = Field(
        ..., description="User prompt template", alias="userPromptTemplate"
    )
    model: str = Field(..., description="Target AI model")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp", alias="createdAt")
    last_modified: datetime = Field(..., description="Last modification time", alias="lastModified")

    model_config = {"populate_by_name": True}


# Conversation Management Responses


class ConversationSummary(BaseModel):
    """Summary information about a conversation."""

    conversation_id: str = Field(..., description="Conversation identifier", alias="conversationId")
    tenant_id: str = Field(..., description="Tenant identifier", alias="tenantId")
    user_id: str = Field(..., description="User identifier", alias="userId")
    topic: str = Field(..., description="Coaching topic")
    status: str = Field(..., description="Conversation status")
    message_count: int = Field(..., description="Number of messages", alias="messageCount")
    created_at: datetime = Field(..., description="Creation timestamp", alias="createdAt")
    last_activity: datetime = Field(..., description="Last activity time", alias="lastActivity")

    model_config = {"populate_by_name": True}


class ConversationMessage(BaseModel):
    """A single message in a conversation."""

    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(..., description="Message timestamp")
    tokens_used: int | None = Field(None, description="Tokens used", alias="tokensUsed")

    model_config = {"populate_by_name": True}


class ConversationDetail(BaseModel):
    """Detailed conversation information."""

    conversation_id: str = Field(..., description="Conversation identifier", alias="conversationId")
    tenant_id: str = Field(..., description="Tenant identifier", alias="tenantId")
    user_id: str = Field(..., description="User identifier", alias="userId")
    topic: str = Field(..., description="Coaching topic")
    status: str = Field(..., description="Conversation status")
    messages: list[ConversationMessage] = Field(..., description="Conversation messages")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp", alias="createdAt")
    last_activity: datetime = Field(..., description="Last activity time", alias="lastActivity")
    total_tokens: int = Field(..., description="Total tokens used", alias="totalTokens")

    model_config = {"populate_by_name": True}


# Topic Response


class CoachingTopicInfo(BaseModel):
    """Information about a coaching topic."""

    topic: str = Field(..., description="Topic identifier")
    display_name: str = Field(..., description="Human-readable name", alias="displayName")
    description: str = Field(..., description="Topic description")
    version_count: int = Field(..., description="Number of versions", alias="versionCount")
    latest_version: str = Field(..., description="Latest version", alias="latestVersion")

    model_config = {"populate_by_name": True}


# LLM Interactions Responses


class LLMInteractionInfo(BaseModel):
    """Information about an LLM interaction."""

    code: str = Field(..., description="Unique interaction code")
    description: str = Field(..., description="Human-readable description")
    category: str = Field(..., description="Interaction category")
    required_parameters: list[str] = Field(
        ..., description="Required parameters for this interaction", alias="requiredParameters"
    )
    optional_parameters: list[str] = Field(
        ..., description="Optional parameters for this interaction", alias="optionalParameters"
    )
    handler_class: str = Field(
        ..., description="Service class that handles this interaction", alias="handlerClass"
    )

    model_config = {"populate_by_name": True}


class ActiveConfigurationInfo(BaseModel):
    """Information about an active configuration."""

    config_id: str = Field(..., description="Configuration identifier", alias="configId")
    template_id: str = Field(..., description="Template identifier", alias="templateId")
    template_name: str = Field(..., description="Template name", alias="templateName")
    model_code: str = Field(..., description="Model code", alias="modelCode")
    tier: str | None = Field(None, description="Tier restriction (null = all tiers)")
    is_active: bool = Field(..., description="Whether configuration is active", alias="isActive")

    model_config = {"populate_by_name": True}


class LLMInteractionDetail(LLMInteractionInfo):
    """Detailed LLM interaction information including active configurations."""

    active_configurations: list[ActiveConfigurationInfo] = Field(
        default_factory=list,
        description="Active configurations for this interaction",
        alias="activeConfigurations",
    )

    model_config = {"populate_by_name": True}


class LLMInteractionsResponse(BaseModel):
    """Response for listing LLM interactions."""

    interactions: list[LLMInteractionInfo] = Field(..., description="Available LLM interactions")
    total_count: int = Field(..., description="Total number of interactions", alias="totalCount")

    model_config = {"populate_by_name": True}


__all__ = [
    "AIModelInfo",
    "AIModelsResponse",
    "AIProviderInfo",
    "ActiveConfigurationInfo",
    "CoachingTopicInfo",
    "ConversationDetail",
    "ConversationMessage",
    "ConversationSummary",
    "LLMInteractionDetail",
    "LLMInteractionInfo",
    "LLMInteractionsResponse",
    "LLMModelInfo",
    "LLMModelsResponse",
    "ModelCostInfo",
    "PromptTemplateDetail",
    "PromptTemplateVersionsResponse",
    "TemplateVersionInfo",
]
