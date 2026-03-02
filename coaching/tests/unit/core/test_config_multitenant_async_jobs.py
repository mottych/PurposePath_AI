"""Tests for multitenant config async jobs switch."""

from __future__ import annotations

import os

from coaching.src.core.config_multitenant import Settings


def test_async_jobs_enabled_default_true() -> None:
    """Async jobs should default to enabled unless explicitly disabled."""
    settings = Settings()
    assert settings.ai_async_jobs_enabled is True


def test_async_jobs_enabled_env_override_false() -> None:
    """Environment variable should disable async jobs when set to false."""
    os.environ["AI_ASYNC_JOBS_ENABLED"] = "false"
    try:
        settings = Settings()
        assert settings.ai_async_jobs_enabled is False
    finally:
        os.environ.pop("AI_ASYNC_JOBS_ENABLED", None)
