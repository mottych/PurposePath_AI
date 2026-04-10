"""Tests for provider-specific JSON Schema adaptation (#309)."""

from __future__ import annotations

from coaching.src.application.ai_engine.llm_json_schema_adaptation import (
    adapt_json_schema_for_openai_structured_output,
    adapt_json_schema_for_vertex_response_schema,
)
from coaching.src.application.ai_engine.unified_ai_engine import UnifiedAIEngine
from coaching.src.models.responses import EmailInsightResponse


def _prepare_like_engine(schema: dict, model_name: str) -> dict:
    """Mirror UnifiedAIEngine._prepare_schema_for_structured_output without full engine."""
    engine = UnifiedAIEngine.__new__(UnifiedAIEngine)
    return engine._prepare_schema_for_structured_output(schema, model_name)


def test_openai_adaptation_replaces_oneof_with_anyof_for_email_insight() -> None:
    full = EmailInsightResponse.model_json_schema(by_alias=True)
    prepared = _prepare_like_engine(full, "EmailInsightResponse")
    assert "oneOf" in str(prepared) or any(
        isinstance(v, dict) and "oneOf" in v for v in prepared.get("$defs", {}).values()
    )

    adapted = adapt_json_schema_for_openai_structured_output(prepared)
    dumped = str(adapted)
    assert "oneOf" not in dumped
    assert "anyOf" in dumped


def test_openai_adaptation_removes_discriminator() -> None:
    full = EmailInsightResponse.model_json_schema(by_alias=True)
    prepared = _prepare_like_engine(full, "EmailInsightResponse")
    adapted = adapt_json_schema_for_openai_structured_output(prepared)
    assert "discriminator" not in str(adapted)


def test_vertex_adapter_matches_openai_union_handling() -> None:
    full = EmailInsightResponse.model_json_schema(by_alias=True)
    prepared = _prepare_like_engine(full, "EmailInsightResponse")
    v = adapt_json_schema_for_vertex_response_schema(prepared)
    assert "oneOf" not in str(v)
    assert "anyOf" in str(v)


def test_unified_engine_adapt_routes_by_provider() -> None:
    full = EmailInsightResponse.model_json_schema(by_alias=True)
    prepared = _prepare_like_engine(full, "EmailInsightResponse")
    o = UnifiedAIEngine._adapt_structured_schema_for_llm_provider(prepared, "openai")
    g = UnifiedAIEngine._adapt_structured_schema_for_llm_provider(prepared, "google_vertex")
    b = UnifiedAIEngine._adapt_structured_schema_for_llm_provider(prepared, "bedrock")
    assert o is not None and "anyOf" in str(o)
    assert g is not None and "anyOf" in str(g)
    assert b == prepared


def test_adapt_none_returns_none() -> None:
    assert UnifiedAIEngine._adapt_structured_schema_for_llm_provider(None, "openai") is None
