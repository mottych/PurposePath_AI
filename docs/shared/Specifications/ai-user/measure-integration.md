# Measure Integration AI Contract Specification

**Version:** 1.2  
**Last Updated:** February 17, 2026  
**Status:** Final (Contract Locked)

---

## Purpose

This document defines the **message contract only** between:
- PurposePath integration backend
- AI SQL-template generation backend

It specifies event names, payload schemas, enums, and behavioral guarantees.

---

## Scope

Included:
- EventBridge event contract for SQL template generation
- Required and optional payload fields
- Canonical enums
- Cross-event compatibility rules
- Deterministic/idempotency guarantees

Excluded (out of scope):
- Internal implementation details of either system
- Storage design, class design, repositories, handlers
- Runtime infrastructure topology
- Deployment details

---

## Event Set

1. `integration.sql.template.generate.requested`
2. `integration.sql.template.generate.completed`
3. `integration.sql.template.generate.failed`

---

## 1) Common EventBridge Envelope (All Events)

### Required
- `version`
- `id`
- `detail-type`
- `source`
- `time`
- `detail` (object)

### Recommended
- `account`
- `region`
- `resources`

---

## 2) Common Detail Identity Block (All Events)

### Required
- `eventVersion` (string, current: `"1.2"`)
- `provider` (string, current expected value: `"cdata"`)
- `correlationId` (uuid)
- `generationId` (uuid)
- `tenantId` (uuid)
- `measureIntegrationId` (uuid)
- `idempotencyKey` (string)
- `definition.version` (int)
- `definition.hash` (`sha256:*`)

### Recommended
- `catalogMeasureId` (uuid)
- `measureId` (uuid)

---

## 3) Requested Event Contract

### Event Identity
- `detail-type = integration.sql.template.generate.requested`
- `source = purposepath.integration`

### Required `detail` fields
- Common Detail Identity Block
- `system.connectionId`
- `system.cdataConnectionId`
- `intent.templateDefinition`
- `intent.resolvedPeriodWindowStrategy`
- `intent.resolvedContext` (object)
- `parameterModel.allowed` (list)
- `parameterModel.values` (list; may be empty)
- `generationControl.regenerationRequired` (bool)
- `sqlPolicy.dialect`
- `sqlPolicy.bindPlaceholderStyle` (required convention, e.g. `@name`)
- `sqlPolicy.mustUseParameterizedTemplate` (bool)
- `sqlPolicy.forbidden` (list)
- `sqlPolicy.maxRows` (int)
- `sqlPolicy.maxRowsSemantics = FINAL_RESULT_SET_ROWS`

### Recommended `detail` fields
- `system.workspace`
- `attempt`
- `maxAttempts`
- `requestedAtUtc`
- `timeZone`
- `schemaSnapshotVersion` or `metadataFingerprint`
- `runtimeBindingsExpected` (string[])

---

## 4) Completed Event Contract

### Event Identity
- `detail-type = integration.sql.template.generate.completed`
- `source = purposepath.integration.ai`

### Required `detail` fields
- Common Detail Identity Block
- `status = success`
- `system.connectionId`
- `system.cdataConnectionId` (if available)
- `system.workspace` (required when execution context used workspace)
- `sqlTemplate` (parameterized; no user-value interpolation)
- `sqlTemplateHash` (`sha256:*`)
- `parameterBindingsSchema` (map: name -> type)
- `appliedParameters` (string[])
- `ignoredParameters` (array of `{ name, reason }`)
- `validated = true`
- `validation.method`
- `validation.attemptCount`
- `generationMetadata.durationMs`
- `generationMetadata.toolCalls`

### Recommended `detail` fields
- `queryArtifactRef`
- `model`
- `tokensUsed`
- `validationDurationMs`
- `sqlPolicyVersion`

---

## 5) Failed Event Contract

### Event Identity
- `detail-type = integration.sql.template.generate.failed`
- `source = purposepath.integration.ai`

### Required `detail` fields
- Common Detail Identity Block
- `status = failed`
- `system.connectionId`
- `system.cdataConnectionId` (if available)
- `system.workspace` (required when execution context used workspace)
- `errorCode` (enum)
- `errorStage` (enum)
- `retryable` (bool)
- `message` (sanitized)
- `durationMs`
- `attemptCount`

### Optional `detail` fields
- `retryAfterSeconds` (int or null)
- `cdataErrorCode`
- `validationFailures` (array of `{ code, message }`)

---

## 6) Canonical Enums

### `errorCode`
- `SQL_POLICY_VIOLATION`
- `SQL_VALIDATION_FAILED`
- `SCHEMA_DISCOVERY_FAILED`
- `MCP_TOOL_ERROR`
- `AI_OUTPUT_INVALID`
- `CDATA_AUTH_INVALID`
- `CDATA_CONNECTION_NOT_FOUND`
- `CDATA_RATE_LIMITED`
- `INTERNAL_UNHANDLED`

### `errorStage`
- `DISCOVER`
- `GENERATE`
- `VALIDATE`
- `REPAIR`
- `PUBLISH`

### `ignoredParameters[].reason`
- `NOT_NEEDED_FOR_QUERY_SHAPE`
- `UNSUPPORTED_BY_SOURCE_SCHEMA`
- `INVALID_OPERATOR_FOR_PARAMETER`
- `NULL_NOT_ALLOWED`
- `TYPE_MISMATCH`
- `OUT_OF_POLICY`

### `validationFailures[].code`
- `FORBIDDEN_TOKEN`
- `UNBOUND_PARAMETER`
- `PLACEHOLDER_STYLE_MISMATCH`
- `MAX_ROWS_EXCEEDED`
- `NON_DETERMINISTIC_RESULT_SHAPE`
- `SYNTAX_INVALID`
- `SCHEMA_OBJECT_NOT_FOUND`

---

## 7) Cross-Event Compatibility Rules

1. `definition.version` and `definition.hash` in terminal events must match the requested event.
2. `runtimeBindingsExpected` (if provided) must be a subset of terminal `parameterBindingsSchema` keys.
3. `sqlPolicy.bindPlaceholderStyle` must match placeholders used in emitted `sqlTemplate`.
4. `appliedParameters` + `ignoredParameters[].name` should represent all provided parameter values considered by the generator.

---

## 8) Behavioral Guarantees

1. **Idempotency:** at most one terminal event per `generationId`.
2. **Terminal guarantee:** exactly one of completed/failed for a given `generationId`.
3. **Security:** no credentials or secrets in events/logs.
4. **Validation gate:** completed event requires `validated = true`.
5. **Parameterization:** SQL template must not interpolate user values.
6. **Policy semantics:** `maxRows` refers to **final result set rows**, not scanned source rows.

---

## 9) Minimal Payload Skeletons

### Requested (`detail`)
```json
{
  "eventVersion": "1.2",
  "provider": "cdata",
  "correlationId": "uuid",
  "generationId": "uuid",
  "tenantId": "uuid",
  "measureIntegrationId": "uuid",
  "idempotencyKey": "string",
  "definition": { "version": 1, "hash": "sha256:..." },
  "system": {
    "connectionId": "uuid",
    "cdataConnectionId": "string",
    "workspace": "default"
  },
  "intent": {
    "templateDefinition": "Calculate ... in {TIME_PERIOD} ...",
    "resolvedPeriodWindowStrategy": "MONTHLY_CALENDAR",
    "resolvedContext": {}
  },
  "parameterModel": {
    "allowed": [],
    "values": []
  },
  "generationControl": {
    "regenerationRequired": true
  },
  "sqlPolicy": {
    "dialect": "cdata-sql",
    "bindPlaceholderStyle": "@name",
    "mustUseParameterizedTemplate": true,
    "forbidden": ["DDL", "DELETE", "UPDATE", "INSERT"],
    "maxRows": 1,
    "maxRowsSemantics": "FINAL_RESULT_SET_ROWS"
  },
  "runtimeBindingsExpected": ["startDate", "endDate"]
}
```

### Completed (`detail`)
```json
{
  "eventVersion": "1.2",
  "provider": "cdata",
  "correlationId": "uuid",
  "generationId": "uuid",
  "tenantId": "uuid",
  "measureIntegrationId": "uuid",
  "idempotencyKey": "string",
  "definition": { "version": 1, "hash": "sha256:..." },
  "system": {
    "connectionId": "uuid",
    "cdataConnectionId": "string",
    "workspace": "default"
  },
  "status": "success",
  "sqlTemplate": "SELECT ... @startDate ...",
  "sqlTemplateHash": "sha256:...",
  "parameterBindingsSchema": {
    "startDate": "DateTime",
    "endDate": "DateTime"
  },
  "appliedParameters": ["customerClass"],
  "ignoredParameters": [
    { "name": "currencyCode", "reason": "NOT_NEEDED_FOR_QUERY_SHAPE" }
  ],
  "validated": true,
  "validation": {
    "method": "dryRun",
    "attemptCount": 1
  },
  "generationMetadata": {
    "durationMs": 1234,
    "toolCalls": 3
  }
}
```

### Failed (`detail`)
```json
{
  "eventVersion": "1.2",
  "provider": "cdata",
  "correlationId": "uuid",
  "generationId": "uuid",
  "tenantId": "uuid",
  "measureIntegrationId": "uuid",
  "idempotencyKey": "string",
  "definition": { "version": 1, "hash": "sha256:..." },
  "system": {
    "connectionId": "uuid",
    "cdataConnectionId": "string",
    "workspace": "default"
  },
  "status": "failed",
  "errorCode": "SQL_VALIDATION_FAILED",
  "errorStage": "VALIDATE",
  "retryable": false,
  "retryAfterSeconds": null,
  "message": "sanitized message",
  "durationMs": 987,
  "attemptCount": 1,
  "cdataErrorCode": null,
  "validationFailures": [
    { "code": "MAX_ROWS_EXCEEDED", "message": "..." }
  ]
}
```

---

## 10) Contract Authority

For AI/backend integration, this document is the source of truth for message shape and semantics.

---

## 11) Deprecated Event Mapping (Migration Note)

The following event names are deprecated and must not be used for new integrations:

| Deprecated Event | V1.2 Replacement |
|---|---|
| `integration.measure.read.requested` | `integration.sql.template.generate.requested` |
| `integration.measure.read.completed` | `integration.sql.template.generate.completed` |
| `integration.measure.read.failed` | `integration.sql.template.generate.failed` |

Additional note:
- `integration.measure.read.skipped` has no direct V1.2 equivalent in this SQL-template generation contract and remains out of scope unless explicitly reintroduced in a future contract version.
