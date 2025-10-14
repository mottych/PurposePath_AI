"""Main FastAPI application for the coaching module."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from coaching.src.api.middleware.logging import LoggingMiddleware
from coaching.src.api.routes import (
    coaching,
    conversations,
    health,
    insights,
    multitenant_conversations,
    suggestions,
    website,
)
from coaching.src.core.config_multitenant import settings
from coaching.src.core.exceptions import CoachingError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    """Application lifespan manager."""
    # Startup
    logger.info("Starting TrueNorth Coaching API", stage=settings.stage)
    yield
    # Shutdown
    logger.info("Shutting down TrueNorth Coaching API")


# Create FastAPI application
app = FastAPI(
    title="TrueNorth AI Coaching API",
    description="AI-powered coaching module for personal and professional development",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)


# Exception handlers with ApiResponse envelope
@app.exception_handler(CoachingError)
async def coaching_exception_handler(request: Request, exc: CoachingError) -> JSONResponse:
    """Handle coaching-specific exceptions with ApiResponse envelope."""
    logger.error(
        "Coaching exception",
        error=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "data": None,
            "message": None,
            "error": f"{exc.message} (Code: {exc.error_code})",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions with ApiResponse envelope."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": None,
            "error": "An internal error occurred",
        },
    )


# Include routers
app.include_router(
    conversations.router,
    prefix=f"{settings.api_prefix}/conversations",
    tags=["conversations"],
)

app.include_router(
    health.router,
    prefix=f"{settings.api_prefix}/health",
    tags=["health"],
)

app.include_router(
    multitenant_conversations.router,
    prefix=f"{settings.api_prefix}/multitenant/conversations",
    tags=["multitenant-conversations"],
)

app.include_router(
    insights.router,
    prefix=f"{settings.api_prefix}/insights",
    tags=["insights"],
)

app.include_router(
    suggestions.router,
    prefix=f"{settings.api_prefix}/suggestions",
    tags=["suggestions"],
)

app.include_router(
    website.router,
    prefix=f"{settings.api_prefix}/website",
    tags=["website"],
)

app.include_router(
    coaching.router,
    prefix=f"{settings.api_prefix}/coaching",
    tags=["coaching"],
)


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": "TrueNorth AI Coaching API",
        "version": "1.0.0",
        "stage": settings.stage,
        "docs": "/docs",
    }


# Create Lambda handler
handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
