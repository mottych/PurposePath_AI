"""Strip a leading URL path prefix before routing (custom domain API mapping)."""

from __future__ import annotations

import structlog
from coaching.src.core.config_multitenant import settings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger()


def normalize_path_after_prefix(*, path: str, prefix: str) -> str:
    """Return path with a single leading prefix segment removed, or path unchanged."""
    p = prefix.strip().rstrip("/")
    if not p or not path.startswith("/"):
        return path
    if path == p:
        return "/"
    prefix_with_slash = f"{p}/"
    if path.startswith(prefix_with_slash):
        return path[len(p) :] or "/"
    return path


class StripPathPrefixMiddleware(BaseHTTPMiddleware):
    """Remove HTTP_PATH_STRIP_PREFIX from scope path (e.g. /coaching from mapped API)."""

    async def dispatch(self, request: Request, call_next) -> Response:
        raw = (settings.http_path_strip_prefix or "").strip()
        if not raw:
            return await call_next(request)

        path = request.url.path
        new_path = normalize_path_after_prefix(path=path, prefix=raw)
        if new_path != path:
            request.scope["path"] = new_path
            if "raw_path" in request.scope:
                request.scope["raw_path"] = new_path.encode("latin-1")
            logger.debug(
                "http_path_strip_prefix",
                stripped_prefix=raw,
                original_path=path,
                routed_path=new_path,
            )

        return await call_next(request)
