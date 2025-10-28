"""Middleware modules for API request processing.

This package provides middleware for:
- Logging: Request/response logging with request IDs
- Error handling: Centralized exception handling
- Rate limiting: Token bucket rate limiting
"""

from coaching.src.api.middleware.error_handling import ErrorHandlingMiddleware
from coaching.src.api.middleware.logging import LoggingMiddleware
from coaching.src.api.middleware.rate_limiting import RateLimitingMiddleware

__all__ = ["ErrorHandlingMiddleware", "LoggingMiddleware", "RateLimitingMiddleware"]
