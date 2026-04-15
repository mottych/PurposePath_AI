"""Dev-only runtime OpenAPI, Swagger UI, and AsyncAPI contract endpoints (unauthenticated)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, FastAPI, Query, Request, status
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

from coaching.src.api.contracts.coaching_asyncapi import (
    build_coaching_asyncapi,
    is_coaching_asyncapi_query_ok,
)
from coaching.src.core.config_multitenant import Settings


def register_runtime_contract_routes(application: FastAPI, cfg: Settings) -> None:
    """Attach contract routes under ``cfg.api_prefix`` (caller must ensure stage is dev)."""
    prefix = cfg.api_prefix
    router = APIRouter(prefix=prefix, tags=["contracts"], include_in_schema=False)

    @router.get(
        "/openapi/v1.json",
        summary="OpenAPI document",
    )
    async def openapi_v1_json() -> JSONResponse:
        return JSONResponse(application.openapi())

    @router.get(
        "/swagger",
        summary="Swagger UI",
        response_class=HTMLResponse,
    )
    async def swagger_ui(request: Request) -> HTMLResponse:
        root_path = request.scope.get("root_path", "") or ""
        openapi_url = f"{root_path}{prefix}/openapi/v1.json"
        return get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{application.title} — Swagger UI",
        )

    @router.get(
        "/contracts/asyncapi",
        summary="AsyncAPI document (EventBridge consumption)",
    )
    async def asyncapi_contract(
        lambda_scope: Annotated[str | None, Query(alias="lambda")] = None,
    ) -> JSONResponse:
        if not is_coaching_asyncapi_query_ok(lambda_scope):
            return JSONResponse(
                {"detail": "Unknown lambda scope for coaching AsyncAPI."},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        return JSONResponse(build_coaching_asyncapi(cfg))

    application.include_router(router)
