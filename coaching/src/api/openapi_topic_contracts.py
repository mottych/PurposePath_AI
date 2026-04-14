"""Derive per-topic OpenAPI fragments from existing topic/response registries (no new registry)."""

from __future__ import annotations

from typing import Any

from coaching.src.core.constants import TopicCategory, TopicType
from coaching.src.core.response_model_registry import get_response_model, is_model_registered
from coaching.src.core.topic_registry import TOPIC_REGISTRY, get_parameters_for_topic

X_PURPOSEPATH_TOPIC_CONTRACTS = "x-purposepath-topic-contracts"


def _safe_topic_suffix(topic_id: str) -> str:
    return topic_id.replace("-", "_").replace(".", "_")


def _json_schema_primitive_type(param_type: str) -> str:
    t = param_type.lower().strip()
    if t in ("string", "str"):
        return "string"
    if t in ("integer", "int"):
        return "integer"
    if t in ("number", "float", "double"):
        return "number"
    if t in ("boolean", "bool"):
        return "boolean"
    if t in ("array", "list"):
        return "array"
    if t in ("object", "dict", "map"):
        return "object"
    return "string"


def build_execute_parameters_schema(topic_id: str) -> dict[str, Any]:
    """JSON Schema object for `GenericAIRequest.parameters` for this topic."""
    params = get_parameters_for_topic(topic_id, include_enrichment_keys=True)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for p in params:
        desc = p.get("description") or ""
        properties[p["name"]] = {
            "type": _json_schema_primitive_type(p["type"]),
            "description": desc,
        }
        if p.get("required"):
            required.append(p["name"])
    safe = _safe_topic_suffix(topic_id)
    return {
        "type": "object",
        "title": f"ExecuteParameters_{safe}",
        "description": (
            f"Expected `parameters` object for POST /ai/execute when `topic_id` is `{topic_id}`."
        ),
        "properties": properties,
        "required": required,
        "additionalProperties": True,
    }


def _ensure_response_model_schema(model_name: str, components: dict[str, Any]) -> str | None:
    """Inline Pydantic JSON Schema into components; return $ref or None."""
    model_cls = get_response_model(model_name)
    if model_cls is None:
        return None
    root_key = f"PurposePathModel__{model_name}"
    if root_key in components:
        return f"#/components/schemas/{root_key}"

    schema = model_cls.model_json_schema(
        ref_template="#/components/schemas/PurposePathModel__{model}"
    )
    defs_raw = schema.pop("$defs", None)
    if isinstance(defs_raw, dict):
        for def_name, def_body in defs_raw.items():
            k = f"PurposePathModel__{def_name}"
            if k not in components and isinstance(def_body, dict):
                components[k] = def_body
    components[root_key] = schema
    return f"#/components/schemas/{root_key}"


def _placeholder_for_json_schema_type(json_type: str) -> Any:
    if json_type == "string":
        return ""
    if json_type == "integer":
        return 0
    if json_type == "number":
        return 0.0
    if json_type == "boolean":
        return False
    if json_type == "array":
        return []
    if json_type == "object":
        return {}
    return ""


def _example_parameters_object(topic_id: str) -> dict[str, Any]:
    """Minimal example `parameters` using required fields only."""
    params = get_parameters_for_topic(topic_id, include_enrichment_keys=True)
    out: dict[str, Any] = {}
    for p in params:
        if not p.get("required"):
            continue
        jt = _json_schema_primitive_type(p["type"])
        out[p["name"]] = _placeholder_for_json_schema_type(jt)
    return out


def _example_async_envelope(
    topic_id: str, category: TopicCategory, activity: dict[str, Any]
) -> dict[str, Any]:
    return {
        "eventId": "00000000-0000-4000-8000-000000000001",
        "requestId": "00000000-0000-4000-8000-000000000002",
        "occurredAtUtc": "2026-04-14T12:00:00Z",
        "sourceService": "PurposePath_Web",
        "schemaVersion": "2.0",
        "correlationId": "00000000-0000-4000-8000-000000000003",
        "idempotencyKey": "example-idempotency-key",
        "retryAttempt": 0,
        "tenantId": "00000000-0000-4000-8000-000000000010",
        "userId": "00000000-0000-4000-8000-000000000011",
        "topicCategory": category.value,
        "topicId": topic_id,
        "eventSignal": "user_requested",
        "locale": "en-US",
        "timezone": "UTC",
        "activityData": activity,
        "authContext": {
            "serviceToken": "<service-token>",
            "expiresAtUtc": "2026-04-14T12:15:00Z",
            "issuer": "PurposePath_Api",
            "tokenType": "service_enrichment",
        },
    }


def enrich_openapi_schema(schema: dict[str, Any], *, api_prefix: str) -> None:
    """Mutate an OpenAPI 3 schema dict: components, extension, and request examples."""
    components = schema.setdefault("components", {}).setdefault("schemas", {})
    topics_out: list[dict[str, Any]] = []
    examples_execute: dict[str, Any] = {}
    examples_async: dict[str, Any] = {}

    single_shot_topics = sorted(
        (
            t
            for t in TOPIC_REGISTRY.values()
            if t.is_active and t.topic_type == TopicType.SINGLE_SHOT
        ),
        key=lambda x: x.topic_id,
    )

    for tdef in single_shot_topics:
        tid = tdef.topic_id
        safe = _safe_topic_suffix(tid)

        param_schema = build_execute_parameters_schema(tid)
        param_key = f"PurposePathExecuteParameters__{safe}"
        components[param_key] = param_schema

        activity_key = f"PurposePathExecuteAsyncActivityData__{safe}"
        components[activity_key] = {
            **param_schema,
            "title": f"ExecuteAsyncActivityData_{safe}",
            "description": (
                f"Expected `activityData` for POST /ai/execute-async when `topicId` is `{tid}` "
                f"(same keys as sync `parameters` for this topic)."
            ),
        }

        resp_ref: str | None = None
        if tdef.response_model and is_model_registered(tdef.response_model):
            resp_ref = _ensure_response_model_schema(tdef.response_model, components)

        topics_out.append(
            {
                "topicId": tid,
                "category": tdef.category.value,
                "execute": {
                    "parametersSchemaRef": f"#/components/schemas/{param_key}",
                    "responseDataSchemaRef": resp_ref,
                    "responseModelName": tdef.response_model or None,
                },
                "executeAsync": {
                    "activityDataSchemaRef": f"#/components/schemas/{activity_key}",
                },
            }
        )

        ex_params = _example_parameters_object(tid)
        desc = tdef.description or ""
        short_desc = (desc[:280] + "…") if len(desc) > 280 else desc
        examples_execute[tid] = {
            "summary": f"topic_id={tid}",
            "description": short_desc,
            "value": {"topic_id": tid, "parameters": ex_params},
        }
        examples_async[tid] = {
            "summary": f"topicId={tid}",
            "description": short_desc,
            "value": _example_async_envelope(tid, tdef.category, ex_params),
        }

    schema[X_PURPOSEPATH_TOPIC_CONTRACTS] = {
        "version": "1.0.0",
        "description": (
            "Machine-readable index of single-shot topics. "
            "Use `parametersSchemaRef` / `activityDataSchemaRef` for client payloads; "
            "`responseDataSchemaRef` matches the shape of `GenericAIResponse.data` when "
            "`schema_ref` equals `responseModelName`. "
            "Also see named `examples` on POST /ai/execute and POST /ai/execute-async."
        ),
        "topics": topics_out,
    }

    paths = schema.get("paths", {})
    exec_path = f"{api_prefix}/ai/execute"
    async_path = f"{api_prefix}/ai/execute-async"

    if exec_path in paths and "post" in paths[exec_path]:
        rb = paths[exec_path]["post"].setdefault("requestBody", {})
        content = rb.setdefault("content", {}).setdefault("application/json", {})
        content["examples"] = examples_execute

    if async_path in paths and "post" in paths[async_path]:
        rb = paths[async_path]["post"].setdefault("requestBody", {})
        content = rb.setdefault("content", {}).setdefault("application/json", {})
        content["examples"] = examples_async
