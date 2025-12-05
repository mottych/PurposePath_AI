"""Lambda handler - imports from coaching.src.api.main."""

from coaching.src.api.main import lambda_handler as handler

# Re-export for Lambda
__all__ = ["handler"]
