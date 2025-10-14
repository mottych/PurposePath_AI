"""Unit tests for configuration management."""

import os

from coaching.src.core.config import Settings, get_settings


class TestSettings:
    """Test configuration settings."""

    def test_default_settings(self) -> None:
        """Test default configuration values."""
        settings = Settings()

        assert settings.stage == "dev"
        assert settings.aws_region == "us-east-1"
        assert settings.log_level == "INFO"
        assert settings.redis_port == 6379
        assert settings.api_prefix == "/api/v1"
        assert settings.session_ttl_hours == 24
        assert settings.conversation_ttl_days == 30

    def test_environment_override(self) -> None:
        """Test environment variable override."""
        # Set environment variable
        os.environ["STAGE"] = "test"
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["REDIS_PORT"] = "6380"

        try:
            settings = Settings()

            assert settings.stage == "test"
            assert settings.log_level == "DEBUG"
            assert settings.redis_port == 6380
        finally:
            # Clean up environment variables
            os.environ.pop("STAGE", None)
            os.environ.pop("LOG_LEVEL", None)
            os.environ.pop("REDIS_PORT", None)

    def test_get_settings_singleton(self) -> None:
        """Test that get_settings returns singleton."""
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2
