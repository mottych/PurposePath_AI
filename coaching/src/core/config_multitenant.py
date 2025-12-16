"""Multitenant configuration management for the coaching module."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient

from pydantic import Field, field_validator
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
    jwt_secret: str | None = Field(default=None, validation_alias="JWT_SECRET")
    jwt_secret_name: str | None = Field(default=None, validation_alias="JWT_SECRET_NAME")
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = Field(
        default="https://api.dev.purposepath.app", validation_alias="JWT_ISSUER"
    )
    jwt_audience: str = Field(
        default="https://dev.purposepath.app", validation_alias="JWT_AUDIENCE"
    )

    def get_jwt_secret_name(self) -> str:
        """Get JWT secret name with environment suffix."""
        if self.jwt_secret_name:
            return self.jwt_secret_name
        return f"purposepath-jwt-secret-{self.stage}"

    # DynamoDB Table Names - computed from stage
    # Pattern: purposepath-{table}-{stage}
    @property
    def conversations_table(self) -> str:
        """Get conversations table name."""
        return f"purposepath-coaching-conversations-{self.stage}"

    @property
    def coaching_sessions_table(self) -> str:
        """Get coaching sessions table name."""
        return f"purposepath-coaching-sessions-{self.stage}"

    @property
    def business_data_table(self) -> str:
        """Get business data table name."""
        return f"purposepath-business-data-{self.stage}"

    @property
    def user_preferences_table(self) -> str:
        """Get user preferences table name."""
        return f"purposepath-user-preferences-{self.stage}"

    @property
    def llm_prompts_table(self) -> str:
        """Get LLM prompts table name."""
        return f"purposepath-llm-prompts-{self.stage}"

    @property
    def topics_table(self) -> str:
        """Get topics table name."""
        return f"purposepath-topics-{self.stage}"

    # Optional: Allow override via env var for local development
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
    account_api_url: str = Field(
        default="https://api.dev.purposepath.app",
        validation_alias="ACCOUNT_API_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "https://dev.purposepath.app",
            "https://staging.purposepath.app",
            "https://www.purposepath.app",
            "https://purposepath.app",
            "https://dev.admin.purposepath.app",
            "https://staging.admin.purposepath.app",
            "https://admin.purposepath.app",
        ],
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        """Parse CORS origins from JSON string or return as-is if already a list."""
        if isinstance(v, str):
            try:
                from typing import cast

                return cast(list[str], json.loads(v))
            except json.JSONDecodeError:
                # If not valid JSON, try splitting by comma
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        from typing import cast

        return cast(list[str], v)

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

    # Secrets Manager ARNs/Names for API Keys
    openai_api_key_secret: str | None = Field(
        default="purposepath/openai-api-key", validation_alias="OPENAI_API_KEY_SECRET"
    )
    google_vertex_credentials_secret: str | None = Field(
        default="purposepath/google-vertex-credentials",
        validation_alias="GOOGLE_VERTEX_CREDENTIALS_SECRET",
    )

    # Google Vertex AI Configuration (optional)
    google_project_id: str | None = Field(default=None, validation_alias="GOOGLE_PROJECT_ID")
    google_vertex_location: str = Field(
        default="us-central1", validation_alias="GOOGLE_VERTEX_LOCATION"
    )

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


def get_openai_api_key() -> str | None:
    """
    Get OpenAI API key from environment or AWS Secrets Manager.

    Priority:
    1. OPENAI_API_KEY environment variable
    2. AWS Secrets Manager (using configured secret name)

    Returns:
        API key string or None if not configured
    """
    settings = get_settings()

    # Check environment variable first
    if settings.openai_api_key:
        return settings.openai_api_key

    # Retrieve from Secrets Manager if configured
    if settings.openai_api_key_secret:
        try:
            from shared.services.aws_helpers import get_secretsmanager_client

            client: SecretsManagerClient = get_secretsmanager_client(settings.aws_region)
            response = client.get_secret_value(SecretId=settings.openai_api_key_secret)
            secret_value = response.get("SecretString")
            return secret_value if secret_value else None
        except Exception:
            # Log error but don't fail - allow None to be returned
            return None

    return None


def get_google_vertex_credentials() -> dict[str, Any] | None:
    """
    Get Google Vertex AI credentials from AWS Secrets Manager.

    Returns:
        Credentials dict (service account JSON) or None if not configured
    """
    import json

    settings = get_settings()

    # Check if GOOGLE_APPLICATION_CREDENTIALS env var is set (local dev)
    import os

    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        # Let Google SDK handle it
        return None

    # Retrieve from Secrets Manager if configured
    if settings.google_vertex_credentials_secret:
        try:
            import structlog
            from shared.services.aws_helpers import get_secretsmanager_client

            log = structlog.get_logger()

            client: SecretsManagerClient = get_secretsmanager_client(settings.aws_region)
            response = client.get_secret_value(SecretId=settings.google_vertex_credentials_secret)
            secret_value = response.get("SecretString")

            if secret_value:
                # Parse JSON credentials
                credentials_dict: dict[str, Any] = json.loads(secret_value)
                log.info(
                    "google_vertex_credentials.loaded",
                    project_id=credentials_dict.get("project_id"),
                    client_email=credentials_dict.get("client_email"),
                )
                return credentials_dict

            log.warning(
                "google_vertex_credentials.empty_secret",
                secret_id=settings.google_vertex_credentials_secret,
            )
            return None
        except Exception as e:
            import structlog

            log = structlog.get_logger()
            log.error("google_vertex_credentials.error", error=str(e), error_type=type(e).__name__)
            return None

    return None


@lru_cache
def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Global settings instance
settings = get_settings()
