"""Lambda handler - imports from src.api.main."""

from src.api.main import handler

# Re-export for Lambda
__all__ = ["handler"]
