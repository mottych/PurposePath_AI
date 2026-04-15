"""Tests for dev-only runtime contract endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from coaching.src.api.main import create_app
from coaching.src.core.config_multitenant import Settings


def _settings(stage: str) -> Settings:
    """Build settings with a specific STAGE (validation alias)."""
    return Settings.model_validate({"STAGE": stage})


def test_dev_exposes_openapi_swagger_asyncapi() -> None:
    app = create_app(_settings("dev"))
    client = TestClient(app)
    r_openapi = client.get("/api/v1/openapi/v1.json")
    assert r_openapi.status_code == 200
    body = r_openapi.json()
    assert body.get("openapi") is not None
    assert "PurposePath AI Coaching API" in (body.get("info") or {}).get("title", "")

    r_swagger = client.get("/api/v1/swagger")
    assert r_swagger.status_code == 200
    assert b"swagger-ui" in r_swagger.content.lower()

    r_async = client.get("/api/v1/contracts/asyncapi")
    assert r_async.status_code == 200
    assert r_async.json().get("asyncapi") == "2.6.0"


def test_dev_asyncapi_lambda_query_unknown_returns_404() -> None:
    app = create_app(_settings("dev"))
    client = TestClient(app)
    r = client.get("/api/v1/contracts/asyncapi", params={"lambda": "unknown-service"})
    assert r.status_code == 404


def test_prod_omits_contract_routes() -> None:
    app = create_app(_settings("prod"))
    client = TestClient(app)
    assert client.get("/api/v1/openapi/v1.json").status_code == 404
    assert client.get("/api/v1/swagger").status_code == 404
    assert client.get("/api/v1/contracts/asyncapi").status_code == 404


def test_root_lists_contract_links_only_in_dev() -> None:
    dev_client = TestClient(create_app(_settings("dev")))
    dev_body = dev_client.get("/").json()
    assert "openapi" in dev_body
    assert "swagger" in dev_body
    assert "asyncapi" in dev_body

    prod_client = TestClient(create_app(_settings("prod")))
    prod_body = prod_client.get("/").json()
    assert "openapi" not in prod_body
    assert "swagger" not in prod_body
    assert "asyncapi" not in prod_body
