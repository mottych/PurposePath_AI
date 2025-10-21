"""Shared dependency injection utilities for FastAPI applications."""

from .typed_dependencies import (
    PermissionChecker,
    TypedRequestContext,
    TypedResponseBuilder,
    validate_request_body,
)

__all__ = [
    "PermissionChecker",
    "TypedRequestContext",
    "TypedResponseBuilder",
    "validate_request_body",
]
