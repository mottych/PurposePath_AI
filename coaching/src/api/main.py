"""Main FastAPI application with Phase 7 architecture."""

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from coaching.src.api.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RateLimitingMiddleware,
)
from coaching.src.api.routes import (
    admin,
    analysis,
    business_data,
    coaching_ai,
    conversations,
    health,
    insights,
    multitenant_conversations,
    operations_ai,
    suggestions,
    topics,
    website,
)
from coaching.src.core.config_multitenant import settings
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from starlette.middleware.base import BaseHTTPMiddleware

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class CORSPreflightMiddleware(BaseHTTPMiddleware):
    """Middleware to handle CORS preflight OPTIONS requests early.

    This middleware ensures OPTIONS requests get CORS headers without
    going through authentication or other middleware that might reject them.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle OPTIONS requests immediately."""
        # Let CORSMiddleware handle the response
        # This just ensures we log pre-flight requests for debugging
        if request.method == "OPTIONS":
            logger.debug(
                "CORS preflight request",
                path=request.url.path,
                origin=request.headers.get("origin"),
            )

        response = await call_next(request)
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting PurposePath AI Coaching API", stage=settings.stage, version="2.0.0")
    yield
    logger.info("Shutting down PurposePath AI Coaching API")


app = FastAPI(
    title="PurposePath AI Coaching API",
    description="AI-powered coaching platform for personal and professional development",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add middleware in correct order - CORS must be last (runs first)
app.add_middleware(RateLimitingMiddleware, default_capacity=100, default_refill_rate=10.0)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(CORSPreflightMiddleware)

# CORS middleware must be added LAST so it runs FIRST in the middleware chain
# This ensures CORS headers are added before any authentication or error handling
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.purposepath\.app|http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
        "X-Api-Key",
        "X-Tenant-Id",
        "X-User-Id",
    ],
    expose_headers=[
        "X-Request-Id",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
    max_age=3600,
)

# Include routers
app.include_router(conversations.router, prefix=f"{settings.api_prefix}")
app.include_router(analysis.router, prefix=f"{settings.api_prefix}")
app.include_router(health.router, prefix=f"{settings.api_prefix}/health", tags=["health"])
app.include_router(admin.router, prefix=f"{settings.api_prefix}")
app.include_router(insights.router, prefix=f"{settings.api_prefix}/insights", tags=["insights"])
app.include_router(
    multitenant_conversations.router,
    prefix=f"{settings.api_prefix}/multitenant/conversations",
    tags=["multitenant", "conversations"],
)
app.include_router(
    business_data.router,
    prefix=f"{settings.api_prefix}/multitenant/conversations",
    tags=["business-data", "multitenant"],
)
app.include_router(coaching_ai.router, prefix=f"{settings.api_prefix}")
app.include_router(operations_ai.router, prefix=f"{settings.api_prefix}")
app.include_router(
    suggestions.router, prefix=f"{settings.api_prefix}/suggestions", tags=["suggestions"]
)
app.include_router(topics.router, prefix=f"{settings.api_prefix}")
app.include_router(website.router, prefix=f"{settings.api_prefix}/website", tags=["website"])


@app.get("/", tags=["root"], response_model=dict[str, str])
async def root() -> dict[str, str]:
    """API root endpoint."""
    return {
        "name": "PurposePath AI Coaching API",
        "version": "2.0.0",
        "stage": settings.stage,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.api_prefix}/health",
    }


handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting development server")
    uvicorn.run(
        "coaching.src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
