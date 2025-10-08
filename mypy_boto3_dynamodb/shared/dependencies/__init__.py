"""Shared dependency injection utilities for FastAPI applications."""

from .typed_dependencies import (
    PermissionChecker,
    TypedRateLimit,
    TypedRequestContext,
    TypedResponseBuilder,
    create_typed_dependency,
    get_typed_context,
    get_typed_goal,
    get_typed_strategy,
    typed_goal_validator,
    typed_strategy_validator,
    validate_request_body,
    with_typed_context,
)

__all__ = [
    "PermissionChecker",
    "TypedRateLimit",
    "TypedRequestContext",
    "TypedResponseBuilder",
    "create_typed_dependency",
    "get_typed_context",
    "get_typed_goal",
    "get_typed_strategy",
    "typed_goal_validator",
    "typed_strategy_validator",
    "validate_request_body",
    "with_typed_context",
]
