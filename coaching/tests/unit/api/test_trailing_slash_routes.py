"""Regression: avoid 307 redirects that drop API Gateway path prefixes (issue #320).

Starlette builds redirect ``Location`` from ``URL(scope=...)`` without prepending
``root_path``, so registering both ``""`` and ``"/"`` avoids redirects for health URLs.
"""

from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient


def test_dual_register_empty_and_slash_path_returns_200_without_redirect() -> None:
    """Mirrors admin health routing: prefix + ``@router.get('')`` + ``@router.get('/')``."""
    app = FastAPI()
    router = APIRouter(prefix="/api/v1/admin/health")

    @router.get("")
    @router.get("/")
    async def _health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    client = TestClient(app, base_url="https://api.dev.purposepath.app")
    without = client.get("/api/v1/admin/health", follow_redirects=False)
    with_slash = client.get("/api/v1/admin/health/", follow_redirects=False)
    assert without.status_code == 200
    assert with_slash.status_code == 200
