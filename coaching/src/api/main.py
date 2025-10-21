"""Main FastAPI application with Phase 7 architecture.

This is the refactored main application that uses:
- Phase 4-6 application services
- New API models with Pydantic
- Auth-based context extraction
- Comprehensive middleware
- Structured error handling
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from coaching.src.api.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RateLimitingMiddleware,
)
from coaching.src.api.routes import analysis, conversations, health
from coaching.src.core.config_multitenant import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# Configure structured logging
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Handles startup and shutdown events for the application.
    """
    # Startup
    logger.info(
        "Starting PurposePath AI Coaching API",
        stage=settings.stage,
        version="2.0.0",
    )
    yield
    # Shutdown
    logger.info("Shutting down PurposePath AI Coaching API")


# Create FastAPI application
app = FastAPI(
    title="PurposePath AI Coaching API",
    description="""
    AI-powered coaching platform for personal and professional development.

    This API provides:
    - **Conversational coaching** - Interactive coaching sessions on core values, purpose, vision, and goals
    - **Alignment analysis** - Analyze how goals align with purpose and values
    - **Strategy analysis** - Evaluate strategy effectiveness and get recommendations
    - **KPI analysis** - Assess KPI effectiveness and get metric recommendations
    - **Operational analysis** - SWOT, root cause, and action plan analysis

    **Authentication**: All endpoints require Bearer token authentication.
    User and tenant context is extracted from JWT tokens.
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "conversations",
            "description": "Manage coaching conversations and sessions",
        },
        {
            "name": "analysis",
            "description": "Business and strategic analysis endpoints",
        },
        {
            "name": "health",
            "description": "Health check and system status",
        },
    ],
    lifespan=lifespan,
    contact={
        "name": "PurposePath Support",
        "url": "https://purposepath.ai/support",
        "email": "support@purposepath.ai",
    },
    license_info={
        "name": "Proprietary",
    },
)

# Add CORS middleware (first, so it wraps everything)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add rate limiting middleware (before error handling)
app.add_middleware(
    RateLimitingMiddleware,
    default_capacity=100,  # 100 requests burst
    default_refill_rate=10.0,  # 10 requests/second
    endpoint_limits={
        "/api/v1/analysis": (20, 1.0),  # Analysis limited to 20 burst, 1/sec
        "/api/v1/conversations/initiate": (10, 0.5),  # Initiate limited to 10 burst, 0.5/sec
    },
)

# Add error handling middleware
app.add_middleware(ErrorHandlingMiddleware)

# Add logging middleware (last, so it logs everything including errors)
app.add_middleware(LoggingMiddleware)


# Include routers
app.include_router(
    conversations.router,
    prefix=f"{settings.api_prefix}",
)

app.include_router(
    analysis.router,
    prefix=f"{settings.api_prefix}",
)

app.include_router(
    health.router,
    prefix=f"{settings.api_prefix}/health",
    tags=["health"],
)


# Root endpoint
@app.get("/", tags=["root"], response_model=dict[str, str])
async def root() -> dict[str, str]:
    """API root endpoint.

    Returns basic API information and links to documentation.
    """
    return {
        "name": "PurposePath AI Coaching API",
        "version": "2.0.0",
        "stage": settings.stage,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.api_prefix}/health",
    }


# Create Lambda handler
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
