"""Error handling middleware for API (Phase 7).

This middleware provides centralized error handling, transforming
domain exceptions into appropriate HTTP responses with proper status
codes and error messages.
"""

import structlog
from coaching.src.domain.exceptions.base_exception import DomainException
from coaching.src.domain.exceptions.conversation_exceptions import (
    ConversationNotActive,
    ConversationNotFound,
)
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class ErrorHandlingMiddleware(BaseHTTPMiddleware):  # type: ignore[misc]
    """Middleware to handle exceptions and return appropriate HTTP responses.

    Note: BaseHTTPMiddleware exists at runtime but type stubs are incomplete.

    This middleware catches exceptions raised during request processing
    and converts them to structured JSON error responses with appropriate
    HTTP status codes.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        """Process request and handle any exceptions.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from handler or error response
        """
        try:
            response = await call_next(request)
            return response

        except ConversationNotFound as e:
            logger.warning(
                "Conversation not found",
                conversation_id=str(e.context.get("conversation_id")),
                tenant_id=str(e.context.get("tenant_id")),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "conversation_not_found",
                    "message": str(e),
                    "conversation_id": e.context.get("conversation_id"),
                },
            )

        except ConversationNotActive as e:
            logger.warning(
                "Conversation not active",
                conversation_id=str(e.context.get("conversation_id")),
                current_status=e.context.get("current_status"),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "conversation_not_active",
                    "message": str(e),
                    "conversation_id": e.context.get("conversation_id"),
                    "current_status": e.context.get("current_status"),
                },
            )

        except DomainException as e:
            logger.warning(
                "Domain exception",
                error_code=e.code,
                error=str(e),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": e.code.lower(),
                    "message": e.message,
                    "context": e.context,
                },
            )

        except (ValidationError, RequestValidationError) as e:
            logger.warning(
                "Request validation error",
                errors=str(e),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "validation_error",
                    "message": "Request validation failed",
                    "details": e.errors() if hasattr(e, "errors") else str(e),
                },
            )

        except PermissionError as e:
            logger.warning(
                "Permission denied",
                error=str(e),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "permission_denied",
                    "message": str(e),
                },
            )

        except ValueError as e:
            logger.warning(
                "Value error",
                error=str(e),
                path=request.url.path,
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "invalid_request",
                    "message": str(e),
                },
            )

        except Exception as e:
            logger.error(
                "Unhandled exception in API",
                error=str(e),
                error_type=type(e).__name__,
                path=request.url.path,
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "internal_server_error",
                    "message": "An unexpected error occurred. Please try again later.",
                },
            )


__all__ = ["ErrorHandlingMiddleware"]
