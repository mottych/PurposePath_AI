"""AsyncAPI document for EventBridge channels consumed by the coaching Lambda."""

from __future__ import annotations

from coaching.src.api.models.ai_job_kickoff import ApiAiJobRequestedDetail
from coaching.src.core.config_multitenant import Settings

JsonDict = dict[str, object]

_COACHING_ASYNCAPI_LAMBDA_ALIASES = frozenset({"coaching", "coaching-ai", "purposepath-coaching"})


def build_coaching_asyncapi(settings: Settings) -> JsonDict:
    """Return AsyncAPI 2.6 describing inbound EventBridge contracts for this service."""
    api_job_schema: JsonDict = ApiAiJobRequestedDetail.model_json_schema(
        ref_template="#/components/schemas/{model}"
    )
    defs_raw = api_job_schema.pop("$defs", None)
    extra_schemas: JsonDict = {}
    if isinstance(defs_raw, dict):
        for name, def_schema in defs_raw.items():
            if isinstance(def_schema, dict):
                extra_schemas[str(name)] = def_schema

    components: JsonDict = {
        "schemas": {
            "ApiAiJobRequestedDetail": api_job_schema,
            "AiJobCreatedDetail": {
                "type": "object",
                "description": "Detail for purposepath.ai / ai.job.created (async job execution).",
                "required": ["jobId", "tenantId"],
                "properties": {
                    "jobId": {"type": "string"},
                    "tenantId": {"type": "string"},
                    "eventType": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "AiMessageCreatedDetail": {
                "type": "object",
                "description": "Detail for purposepath.ai / ai.message.created (coaching message jobs).",
                "required": ["jobId", "tenantId"],
                "properties": {
                    "jobId": {"type": "string"},
                    "tenantId": {"type": "string"},
                    "eventType": {"type": "string"},
                    "data": {
                        "type": "object",
                        "properties": {"sessionId": {"type": "string"}},
                        "additionalProperties": True,
                    },
                },
                "additionalProperties": True,
            },
            "IntegrationSqlTemplateGenerateRequestedDetail": {
                "type": "object",
                "description": (
                    "Detail for purposepath.integration / integration.sql.template.generate.requested."
                ),
                "additionalProperties": True,
            },
            **extra_schemas,
        }
    }

    kickoff_source = settings.ai_kickoff_event_source
    kickoff_detail = settings.ai_kickoff_detail_type

    channels: dict[str, JsonDict] = {
        f"{kickoff_source}:{kickoff_detail}": {
            "description": (
                f"EventBridge rule target: source `{kickoff_source}`, detail-type `{kickoff_detail}`."
            ),
            "subscribe": {
                "operationId": "consumeApiAiJobRequested",
                "message": {
                    "name": "ApiAiJobRequested",
                    "title": "API async job kickoff",
                    "contentType": "application/json",
                    "payload": {"$ref": "#/components/schemas/ApiAiJobRequestedDetail"},
                },
            },
        },
        "purposepath.ai:ai.job.created": {
            "description": "Internal AI async job execution kickoff.",
            "subscribe": {
                "operationId": "consumeAiJobCreated",
                "message": {
                    "name": "AiJobCreated",
                    "contentType": "application/json",
                    "payload": {"$ref": "#/components/schemas/AiJobCreatedDetail"},
                },
            },
        },
        "purposepath.ai:ai.message.created": {
            "description": "Coaching message job execution.",
            "subscribe": {
                "operationId": "consumeAiMessageCreated",
                "message": {
                    "name": "AiMessageCreated",
                    "contentType": "application/json",
                    "payload": {"$ref": "#/components/schemas/AiMessageCreatedDetail"},
                },
            },
        },
        "purposepath.integration:integration.sql.template.generate.requested": {
            "description": "Integration-driven SQL template generation request.",
            "subscribe": {
                "operationId": "consumeIntegrationSqlTemplateGenerateRequested",
                "message": {
                    "name": "IntegrationSqlTemplateGenerateRequested",
                    "contentType": "application/json",
                    "payload": {
                        "$ref": "#/components/schemas/IntegrationSqlTemplateGenerateRequestedDetail"
                    },
                },
            },
        },
    }

    info: JsonDict = {
        "title": "PurposePath AI Coaching — EventBridge consumption",
        "version": "1.0.0",
        "description": (
            "Async contracts for events delivered to the coaching Lambda (EventBridge). "
            f"Resolved domain event bus name: `{settings.resolved_domain_event_bus_name}`."
        ),
    }

    document: JsonDict = {
        "asyncapi": "2.6.0",
        "info": info,
        "defaultContentType": "application/json",
        "channels": channels,
        "components": components,
    }
    return document


def is_coaching_asyncapi_query_ok(lambda_scope: str | None) -> bool:
    """Return True if optional `lambda` query matches this service (parity with admin AsyncAPI)."""
    if lambda_scope is None or lambda_scope.strip() == "":
        return True
    return lambda_scope.strip().lower() in _COACHING_ASYNCAPI_LAMBDA_ALIASES
