"""Main FastAPI application with Phase 7 architecture."""

import logging
import sys
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from mangum import Mangum
from starlette.middleware.base import BaseHTTPMiddleware

from coaching.src.api.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    RateLimitingMiddleware,
)
from coaching.src.api.routes import (
    admin,
    ai_execute,
    ai_execute_async,
    business_data,
    coaching_sessions,
    health,
    insights,
    multitenant_conversations,
)
from coaching.src.api.routes.runtime_contracts import register_runtime_contract_routes
from coaching.src.core.config_multitenant import Settings, get_settings

# Configure Python logging for Lambda - Lambda captures stderr
logging.basicConfig(
    format="%(levelname)s: %(message)s",
    stream=sys.stderr,
    level=logging.DEBUG,  # Allow all levels, structlog will filter
    force=True,
)

# Set root logger level to DEBUG
logging.getLogger().setLevel(logging.DEBUG)

# Configure structlog for Lambda CloudWatch
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),  # Human-readable output
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Test logging at startup
print("[STARTUP] Lambda handler loading", file=sys.stderr, flush=True)
logger.info("lambda_startup", message="FastAPI application initializing")


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


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application (supports injected settings for tests)."""
    cfg = app_settings if app_settings is not None else get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        """Application lifespan manager."""
        logger.info("Starting PurposePath AI Coaching API", stage=cfg.stage, version="2.0.0")
        yield
        logger.info("Shutting down PurposePath AI Coaching API")

    application = FastAPI(
        title="PurposePath AI Coaching API",
        description="AI-powered coaching platform for personal and professional development",
        version="2.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    application.state.settings = cfg

    # Add middleware in correct order - CORS must be last (runs first)
    application.add_middleware(
        RateLimitingMiddleware,  # type: ignore[arg-type, call-arg]
        default_capacity=100,
        default_refill_rate=10.0,
    )
    application.add_middleware(ErrorHandlingMiddleware)  # type: ignore[arg-type,call-arg]
    application.add_middleware(LoggingMiddleware)  # type: ignore[arg-type,call-arg]
    application.add_middleware(CORSPreflightMiddleware)  # type: ignore[arg-type,call-arg]

    # CORS middleware must be added LAST so it runs FIRST in the middleware chain
    # This ensures CORS headers are added before any authentication or error handling
    _cors_config: dict[str, Any] = {
        # Allow purposepath.app apex/subdomains, and local dev ports.
        "allow_origin_regex": (
            r"(^https://([a-zA-Z0-9-]+\.)*purposepath\.app$)|(^http://localhost:\d+$)"
        ),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        # Allow all request headers to prevent preflight breakage when frontend tooling
        # adds non-static headers (for example tracing/monitoring headers).
        "allow_headers": ["*"],
        "expose_headers": [
            "X-Request-Id",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset",
        ],
        "max_age": 3600,
    }
    application.add_middleware(CORSMiddleware, **_cors_config)  # type: ignore[arg-type]

    # Include routers
    application.include_router(health.router, prefix=f"{cfg.api_prefix}/health", tags=["health"])
    application.include_router(admin.router, prefix=f"{cfg.api_prefix}")
    application.include_router(
        insights.router, prefix=f"{cfg.api_prefix}/insights", tags=["insights"]
    )
    application.include_router(
        multitenant_conversations.router,
        prefix=f"{cfg.api_prefix}/multitenant/conversations",
        tags=["multitenant", "conversations"],
    )
    application.include_router(
        business_data.router,
        prefix=f"{cfg.api_prefix}/multitenant/conversations",
        tags=["business-data", "multitenant"],
    )
    application.include_router(ai_execute.router, prefix=f"{cfg.api_prefix}")
    application.include_router(coaching_sessions.router, prefix=f"{cfg.api_prefix}")
    application.include_router(ai_execute_async.router, prefix=f"{cfg.api_prefix}")

    if cfg.stage.lower() == "dev":
        register_runtime_contract_routes(application, cfg)

    def custom_openapi() -> dict[str, Any]:
        if application.openapi_schema:
            return application.openapi_schema
        openapi_schema = get_openapi(
            title=application.title,
            version=application.version,
            openapi_version=application.openapi_version,
            description=application.description,
            routes=application.routes,
        )
        if cfg.stage.lower() == "dev":
            from coaching.src.api.openapi_topic_contracts import enrich_openapi_schema

            enrich_openapi_schema(openapi_schema, api_prefix=cfg.api_prefix)
        application.openapi_schema = openapi_schema
        return application.openapi_schema

    application.openapi = custom_openapi  # type: ignore[method-assign]

    @application.get("/", tags=["root"], response_model=dict[str, str])
    async def root(request: Request) -> dict[str, str]:
        """API root endpoint."""
        s: Settings = request.app.state.settings
        payload: dict[str, str] = {
            "name": "PurposePath AI Coaching API",
            "version": "2.0.0",
            "stage": s.stage,
            "health": f"{s.api_prefix}/health",
        }
        if s.stage.lower() == "dev":
            payload["openapi"] = f"{s.api_prefix}/openapi/v1.json"
            payload["swagger"] = f"{s.api_prefix}/swagger"
            payload["asyncapi"] = f"{s.api_prefix}/contracts/asyncapi"
        return payload

    return application


app = create_app()

handler = Mangum(app, lifespan="off")


# Wrapper to add debug logging for Lambda
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler wrapper with debug logging.

    This handler routes events to the appropriate processor:
    - EventBridge events → eventbridge_handler (for async job execution)
    - API Gateway events → Mangum/FastAPI (for HTTP requests)
    """
    import sys

    from coaching.src.api.handlers import handle_eventbridge_event, is_eventbridge_event

    # Check if this is an EventBridge event
    if is_eventbridge_event(event):
        print(
            f"[LAMBDA_HANDLER] EventBridge event: {event.get('detail-type', 'unknown')}",
            file=sys.stderr,
            flush=True,
        )
        return handle_eventbridge_event(event, context)

    # Direct print to stderr - Lambda MUST capture this
    print(
        f"[LAMBDA_HANDLER] Event: {event.get('httpMethod', 'unknown')} {event.get('path', 'unknown')}",
        file=sys.stderr,
        flush=True,
    )

    # Call Mangum handler for API Gateway events
    response = handler(event, context)

    print(
        f"[LAMBDA_HANDLER] Response status: {response.get('statusCode', 'unknown')}",
        file=sys.stderr,
        flush=True,
    )

    return response


if __name__ == "__main__":
    import uvicorn

    _settings = get_settings()
    logger.info("Starting development server")
    uvicorn.run(
        "coaching.src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=_settings.log_level.lower(),
    )
