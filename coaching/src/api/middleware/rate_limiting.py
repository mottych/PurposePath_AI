"""Rate limiting middleware for API (Phase 7).

This middleware implements token bucket rate limiting to protect
the API from abuse and ensure fair resource allocation.
"""

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

import structlog
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class TokenBucket:
    """Token bucket implementation for rate limiting.

    Uses the token bucket algorithm to allow bursts while enforcing
    a long-term rate limit.
    """

    def __init__(self, capacity: int, refill_rate: float):
        """Initialize token bucket.

        Args:
            capacity: Maximum number of tokens (burst size)
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        # Refill tokens based on elapsed time
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = int(
            min(
                self.capacity,
                self.tokens + (elapsed * self.refill_rate),
            )
        )
        self.last_refill = now

        # Try to consume
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False


class RateLimitingMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Middleware to enforce rate limits on API requests.

    Rate limits are applied per user (extracted from auth token).
    Different endpoints can have different rate limits.
    
    Note: BaseHTTPMiddleware exists at runtime but type stubs are incomplete.
    """

    def __init__(
        self,
        app: Any,
        default_capacity: int = 100,
        default_refill_rate: float = 10.0,
        endpoint_limits: dict[str, tuple[int, float]] | None = None,
    ):
        """Initialize rate limiting middleware.

        Args:
            app: FastAPI application
            default_capacity: Default burst capacity (requests)
            default_refill_rate: Default refill rate (requests/second)
            endpoint_limits: Per-endpoint limits {path_prefix: (capacity, rate)}
        """
        super().__init__(app)
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.endpoint_limits = endpoint_limits or {}

        # Store buckets per user
        # Format: {user_id: {endpoint_prefix: TokenBucket}}
        self.buckets: dict[str, dict[str, TokenBucket]] = defaultdict(dict)

        logger.info(
            "Rate limiting middleware initialized",
            default_capacity=default_capacity,
            default_refill_rate=default_refill_rate,
            endpoint_limits=list(self.endpoint_limits.keys()),
        )

    def get_bucket(self, user_id: str, endpoint: str) -> TokenBucket:
        """Get or create token bucket for user and endpoint.

        Args:
            user_id: User identifier
            endpoint: Endpoint path

        Returns:
            TokenBucket for this user/endpoint combination
        """
        # Find matching endpoint limit
        capacity = self.default_capacity
        refill_rate = self.default_refill_rate

        for prefix, (ep_capacity, ep_rate) in self.endpoint_limits.items():
            if endpoint.startswith(prefix):
                capacity = ep_capacity
                refill_rate = ep_rate
                break

        # Get or create bucket
        if endpoint not in self.buckets[user_id]:
            self.buckets[user_id][endpoint] = TokenBucket(capacity, refill_rate)

        return self.buckets[user_id][endpoint]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request with rate limiting.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from handler or rate limit error
        """
        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Skip rate limiting for unauthenticated requests (they'll be rejected by auth)
        if not user_id:
            return await call_next(request)

        # Get endpoint path
        endpoint = request.url.path

        # Get bucket and try to consume token
        bucket = self.get_bucket(user_id, endpoint)

        if not bucket.consume():
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                endpoint=endpoint,
                method=request.method,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                },
                headers={
                    "Retry-After": "60",  # Suggest retry after 60 seconds
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(bucket.capacity)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket.tokens))

        return response


__all__ = ["RateLimitingMiddleware", "TokenBucket"]
