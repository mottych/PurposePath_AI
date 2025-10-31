"""Lambda handler - imports from src.api.main."""

from src.api.main import handler  # noqa: F401

# Re-export for Lambda
__all__ = ["handler"]
