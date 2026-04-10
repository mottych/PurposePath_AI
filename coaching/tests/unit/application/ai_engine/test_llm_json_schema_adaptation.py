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


def _first_property_key_of_object_schema(obj: dict) -> str | None:
    props = obj.get("properties")
    if not isinstance(props, dict) or not props:
        return None
    return next(iter(props.keys()))


def test_openai_blocks_anyof_branches_have_distinct_first_keys() -> None:
    """OpenAI rejects anyOf when each object branch shares the same first key."""
    full = EmailInsightResponse.model_json_schema(by_alias=True)
    prepared = _prepare_like_engine(full, "EmailInsightResponse")
    adapted = adapt_json_schema_for_openai_structured_output(prepared)

    blocks = adapted.get("properties", {}).get("blocks")
    assert isinstance(blocks, dict)
    items = blocks.get("items")
    assert isinstance(items, dict)
    variants = items.get("anyOf") or items.get("oneOf")
    assert isinstance(variants, list) and len(variants) == 3

    first_keys: list[str] = []
    for branch in variants:
        assert isinstance(branch, dict)
        if "$ref" in branch:
            ref = branch["$ref"]
            assert ref.startswith("#/$defs/")
            def_name = ref.removeprefix("#/$defs/")
            defn = adapted.get("$defs", {}).get(def_name)
            assert isinstance(defn, dict)
            key = _first_property_key_of_object_schema(defn)
        else:
            key = _first_property_key_of_object_schema(branch)
        assert key is not None
        first_keys.append(key)

    assert len(set(first_keys)) == len(first_keys), f"duplicate first keys: {first_keys}"
