"""Structured logging configuration for production observability."""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

import structlog


def _json_serializer(obj: Any, **kwargs: Any) -> str:
    """Custom JSON serializer that handles datetime objects.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string
    """

    def default(o: Any) -> Any:
        """Handle non-JSON-serializable objects."""
        if isinstance(o, datetime):
            return o.isoformat()
        # Let the default encoder raise TypeError for other unsupported types
        raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")

    return json.dumps(obj, default=default, **kwargs)


def configure_logging(
    level: str | None = None,
    json_logs: bool | None = None,
    service_name: str = "purposepath-coaching",
) -> None:
    """
    Configure structured logging with structlog.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to use JSON formatting (defaults to True for prod/staging)
        service_name: Service name to include in logs
    """
    # Determine log level
    stage = os.getenv("STAGE", "dev")
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO" if stage != "dev" else "DEBUG")

    # Determine JSON formatting
    if json_logs is None:
        json_logs = stage in ["staging", "prod", "production"]

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Shared processors for all configurations
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    # Add service metadata
    structlog.contextvars.bind_contextvars(
        service=service_name,
        environment=stage,
    )

    # Configure processors based on environment
    processors: list[Any]
    if json_logs:
        # JSON formatting for production/staging
        processors = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(serializer=_json_serializer),
        ]
    else:
        # Console formatting for development
        processors = [
            *shared_processors,
            structlog.processors.ExceptionPrettyPrinter(),
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically module name)

    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


__all__ = ["configure_logging", "get_logger"]
