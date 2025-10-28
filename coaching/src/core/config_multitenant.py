"""Multitenant configuration management for the coaching module."""

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with multitenant support."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Environment
    stage: str = Field(default="dev", validation_alias="STAGE")
    aws_region: str = Field(default="us-east-1", validation_alias="AWS_REGION")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    application_name: str = Field(default="PurposePath")

    # JWT Authentication (for token validation)
    jwt_secret_arn: str | None = Field(default=None, validation_alias="JWT_SECRET_ARN")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "purposepath"

    # DynamoDB Tables (Multitenant)
    conversations_table: str = Field(
        default="purposepath-conversations-dev", validation_alias="CONVERSATIONS_TABLE"
    )
    coaching_sessions_table: str = Field(
        default="purposepath-coaching-sessions-dev", validation_alias="COACHING_SESSIONS_TABLE"
    )
    business_data_table: str = Field(
        default="purposepath-business-data-dev", validation_alias="BUSINESS_DATA_TABLE"
    )
    user_preferences_table: str = Field(
        default="purposepath-user-preferences-dev", validation_alias="USER_PREFERENCES_TABLE"
    )
    dynamodb_endpoint: str | None = None

    # S3
    prompts_bucket: str = Field(
        default="purposepath-coaching-prompts-dev", validation_alias="PROMPTS_BUCKET"
    )

    # Redis/ElastiCache
    redis_cluster_endpoint: str | None = Field(
        default=None, validation_alias="REDIS_CLUSTER_ENDPOINT"
    )
    redis_host: str = Field(default="localhost", validation_alias="REDIS_HOST")
    redis_port: int = Field(default=6379, validation_alias="REDIS_PORT")
    redis_password: str | None = Field(default=None, validation_alias="REDIS_PASSWORD")
    redis_db: int = 0
    redis_ssl: bool = Field(default=True, validation_alias="REDIS_SSL")

    # Bedrock
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0", validation_alias="BEDROCK_MODEL_ID"
    )
    bedrock_region: str = Field(default="us-east-1", validation_alias="BEDROCK_REGION")

    # API Configuration
    api_prefix: str = "/api/v1"
    business_api_base_url: str = Field(
        default="https://api.dev.purposepath.app/account/api/v1",
        validation_alias="BUSINESS_API_BASE_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "https://purposepath.app",
            "https://www.purposepath.app",
        ],
        validation_alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    cors_allow_headers: list[str] = ["*"]

    # Session Configuration
    session_ttl_hours: int = 24
    conversation_ttl_days: int = 30

    # LLM Configuration
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout_seconds: int = 30

    # Multi-Provider Configuration (Issue #82)
    default_llm_provider: str = Field(default="bedrock", validation_alias="DEFAULT_LLM_PROVIDER")
    fallback_llm_providers: list[str] = Field(
        default_factory=lambda: ["anthropic", "openai"],
        validation_alias="FALLBACK_LLM_PROVIDERS",
    )

    # Provider API Keys (optional - for direct API access)
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")

    # Memory Management
    max_conversation_memory: int = 4000

    # Coaching Topics and Business Data Integration
    coaching_topics: dict[str, dict[str, Any]] = {
        "core_values": {
            "title": "Core Values Discovery",
            "description": "Discover and refine your organization's core values",
            "business_data_field": "core_values",
            "max_sessions_per_user": 5,
        },
        "purpose": {
            "title": "Purpose Definition",
            "description": "Define your organization's purpose statement",
            "business_data_field": "purpose",
            "max_sessions_per_user": 3,
        },
        "vision": {
            "title": "Vision Creation",
            "description": "Create a compelling vision for your organization",
            "business_data_field": "vision",
            "max_sessions_per_user": 3,
        },
        "goals": {
            "title": "Strategic Goals",
            "description": "Set and align strategic goals",
            "business_data_field": "goals",
            "max_sessions_per_user": 10,
        },
    }

    # Business Data Update Settings
    auto_update_business_data: bool = True
    require_outcome_approval: bool = False  # Set to True for enterprise customers
    outcome_confidence_threshold: float = 0.8  # AI confidence threshold for auto-updates


@lru_cache
def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Global settings instance
settings = get_settings()
