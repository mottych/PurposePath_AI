"""Provider-specific JSON Schema adaptation for LLM structured output.

Pydantic ``model_json_schema()`` emits ``oneOf`` for discriminated unions (e.g.
``EmailInsightResponse.blocks``). OpenAI strict structured outputs reject
``oneOf`` in some positions (e.g. under ``items``) with ``invalid_json_schema``.

This module adapts already-prepared schemas (e.g. after
``additionalProperties: false`` normalization) for each provider's accepted
dialect without changing the application-level Pydantic models: API responses
are still validated with the original models after generation.

References:
- https://platform.openai.com/docs/guides/structured_outputs
- https://ai.google.dev/gemini-api/docs/structured-output
"""

from __future__ import annotations

import copy
from typing import Any


def adapt_json_schema_for_openai_structured_output(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of ``schema`` adjusted for OpenAI Responses API strict JSON schema.

    - Recursively renames ``oneOf`` to ``anyOf`` (union of object shapes).
    - Strips ``discriminator`` (OpenAI strict mode does not use Pydantic's discriminator metadata).

    Args:
        schema: Schema already passed through strict OpenAI prep (e.g.
            ``UnifiedAIEngine._prepare_schema_for_structured_output``).

    Returns:
        Adapted schema safe to pass as ``text.format.schema`` with strict mode.
    """
    adapted = copy.deepcopy(schema)
    _transform_openai_inplace(adapted)
    return adapted


def adapt_json_schema_for_vertex_response_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy of ``schema`` adjusted for Vertex Gemini ``response_schema``.

    Uses the same ``oneOf`` → ``anyOf`` normalization as OpenAI for union blocks;
    Gemini's JSON schema subset also commonly rejects or mishandles ``oneOf`` in
    array ``items``. If Google diverges, split logic here.

    Args:
        schema: Schema after ``_prepare_schema_for_structured_output`` (or equivalent).

    Returns:
        Adapted schema for ``GenerateContentConfig.response_schema``.
    """
    adapted = copy.deepcopy(schema)
    _transform_openai_inplace(adapted)
    return adapted


def _transform_openai_inplace(node: Any) -> None:
    """Recursively apply OpenAI/Gemini-friendly union transforms in place."""
    if isinstance(node, dict):
        if "oneOf" in node:
            node["anyOf"] = node.pop("oneOf")
        node.pop("discriminator", None)

        defs = node.get("$defs")
        if isinstance(defs, dict):
            for defn in defs.values():
                _transform_openai_inplace(defn)

        for key, value in node.items():
            if key == "$defs":
                continue
            if isinstance(value, dict):
                _transform_openai_inplace(value)
            elif isinstance(value, list):
                for item in value:
                    _transform_openai_inplace(item)
    elif isinstance(node, list):
        for item in node:
            _transform_openai_inplace(item)
