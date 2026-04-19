"""Tests for OpenAPI enrichment from topic/response registries."""

from __future__ import annotations

from typing import Any

from coaching.src.api.main import create_app
from coaching.src.api.openapi_topic_contracts import (
    X_PURPOSEPATH_TOPIC_CONTRACTS,
    build_execute_parameters_schema,
    enrich_openapi_schema,
)
from coaching.src.core.config_multitenant import Settings


def _settings(stage: str) -> Settings:
    return Settings.model_validate({"STAGE": stage})


def test_build_execute_parameters_schema_website_scan() -> None:
    schema = build_execute_parameters_schema("website_scan")
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "website_url" in schema["properties"] or "url" in schema["properties"]


def test_dev_openapi_includes_topic_contract_extension() -> None:
    app = create_app(_settings("dev"))
    spec = app.openapi()
    block = spec.get(X_PURPOSEPATH_TOPIC_CONTRACTS)
    assert isinstance(block, dict)
    assert block.get("version") == "2.0.0"
    topics = block.get("topics")
    assert isinstance(topics, list)
    assert any(t.get("topicId") == "website_scan" for t in topics)

    ws = next(t for t in topics if t.get("topicId") == "website_scan")
    assert ws["topicType"] == "single_shot"
    assert ws["execute"]["parametersSchemaRef"].startswith("#/components/schemas/")
    assert ws["execute"]["responseDataSchemaRef"] is not None
    assert ws["executeAsync"]["activityDataSchemaRef"].startswith("#/components/schemas/")

    goals = next(t for t in topics if t.get("topicId") == "goals")
    assert goals["topicType"] == "conversation_coaching"
    assert goals["conversation"]["startContextSchemaRef"].startswith("#/components/schemas/")
    assert goals["conversation"]["resultDataSchemaRef"] is not None
    assert goals["conversation"]["resultModelName"] == "GoalCreationResult"

    comps = spec["components"]["schemas"]
    assert "PurposePathExecuteParameters__website_scan" in comps
    assert "PurposePathModel__WebsiteScanResponse" in comps
    assert "PurposePathCoachingStartContext__goals" in comps
    assert "PurposePathCoachingModel__GoalCreationResult" in comps


def test_dev_openapi_execute_endpoints_have_named_examples() -> None:
    app = create_app(_settings("dev"))
    spec = app.openapi()
    execute = spec["paths"]["/api/v1/ai/execute"]["post"]["requestBody"]["content"][
        "application/json"
    ]
    assert "examples" in execute
    assert "website_scan" in execute["examples"]
    assert execute["examples"]["website_scan"]["value"]["topic_id"] == "website_scan"

    async_body = spec["paths"]["/api/v1/ai/execute-async"]["post"]["requestBody"]["content"][
        "application/json"
    ]
    assert "examples" in async_body
    assert async_body["examples"]["website_scan"]["value"]["topicId"] == "website_scan"

    coaching_start = spec["paths"]["/api/v1/ai/coaching/start"]["post"]["requestBody"]["content"][
        "application/json"
    ]
    assert "examples" in coaching_start
    assert "goals" in coaching_start["examples"]
    assert coaching_start["examples"]["goals"]["value"]["topic_id"] == "goals"


def test_prod_openapi_omits_topic_enrichment() -> None:
    app = create_app(_settings("prod"))
    spec = app.openapi()
    assert X_PURPOSEPATH_TOPIC_CONTRACTS not in spec


def test_enrich_openapi_schema_no_paths_is_safe() -> None:
    base: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {"title": "t", "version": "1"},
        "paths": {},
    }
    enrich_openapi_schema(base, api_prefix="/api/v1")
    assert X_PURPOSEPATH_TOPIC_CONTRACTS in base
