"""Configuration management for the coaching module."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Environment
    stage: str = "dev"
    aws_region: str = "us-east-1"
    log_level: str = "INFO"

    # DynamoDB
    dynamodb_table: str = "truenorth-coaching-conversations-dev"
    dynamodb_endpoint: str | None = None

    # S3
    prompts_bucket: str = Field(
        default="purposepath-coaching-prompts-dev", validation_alias="PROMPTS_BUCKET"
    )

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str | None = None
    redis_db: int = 0
    redis_ssl: bool = False

    # Bedrock
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_region: str = "us-east-1"

    # API Configuration
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:8081",
            "https://app.purposepath.com",
            "https://purposepath.com",
        ],
        validation_alias="CORS_ORIGINS",
    )

    # Session Configuration
    session_ttl_hours: int = 24
    conversation_ttl_days: int = 30

    # LLM Configuration
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2000
    llm_timeout_seconds: int = 30

    # Memory Management
    max_conversation_memory: int = 4000

    # Business API Configuration
    business_api_base_url: str = Field(
        default="https://api.dev.purposepath.app/account/api/v1",
        validation_alias="BUSINESS_API_BASE_URL",
    )
    business_api_timeout: int = Field(
        default=30,
        validation_alias="BUSINESS_API_TIMEOUT",
    )
    business_api_max_retries: int = Field(
        default=3,
        validation_alias="BUSINESS_API_MAX_RETRIES",
    )


@lru_cache
def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Global settings instance
settings = get_settings()
