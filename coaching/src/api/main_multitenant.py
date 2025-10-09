"""Main FastAPI application for the multitenant coaching module."""

from contextlib import asynccontextmanager
from datetime import timezone
from typing import Any, AsyncGenerator

import structlog
from coaching.src.api.middleware.logging import LoggingMiddleware
from coaching.src.api.routes import health, multitenant_conversations
from coaching.src.core.config_multitenant import settings
from coaching.src.core.exceptions import CoachingError
from fastapi import FastAPI, HTTPException, Request
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
    logger.info("Starting PurposePath Coaching API", stage=settings.stage)
    yield
    # Shutdown
    logger.info("Shutting down PurposePath Coaching API")


# Create FastAPI application
app = FastAPI(
    title="PurposePath AI Coaching API",
    description="Multitenant AI-powered coaching module for organizational development",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom logging middleware
app.add_middleware(LoggingMiddleware)


# Exception handlers
@app.exception_handler(CoachingError)
async def coaching_exception_handler(request: Request, exc: CoachingError) -> JSONResponse:
    """Handle coaching-specific exceptions."""
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
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details,
        },
    )


@app.exception_handler(PermissionError)
async def permission_exception_handler(request: Request, exc: PermissionError) -> JSONResponse:
    """Handle permission errors."""
    logger.warning(
        "Permission denied",
        error=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=403,
        content={
            "error": "Access denied",
            "error_code": "PERMISSION_DENIED",
            "details": str(exc),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with logging."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal error occurred",
            "error_code": "INTERNAL_ERROR",
        },
    )


# Include routers
app.include_router(
    multitenant_conversations.router,
    prefix=f"{settings.api_prefix}/conversations",
    tags=["conversations"],
)

app.include_router(
    health.router,
    prefix=f"{settings.api_prefix}/health",
    tags=["health"],
)


# Root endpoint
@app.get("/")
async def root() -> dict[str, Any]:
    """Root endpoint."""
    return {
        "name": "PurposePath AI Coaching API",
        "version": "2.0.0",
        "stage": settings.stage,
        "features": [
            "multitenant_architecture",
            "business_data_integration",
            "role_based_access_control",
            "coaching_session_outcomes",
        ],
        "docs": "/docs",
    }


# Health check with tenant validation
@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    from datetime import datetime

    return {
        "status": "healthy",
        "service": "coaching",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "multitenant": True,
    }


# Create Lambda handler
handler = Mangum(app, lifespan="off")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main_multitenant:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower(),
    )
