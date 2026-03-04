# Integration Async Contracts (Backend) - AI + CData

**Version:** 2.0.0  
**Date:** March 1, 2026  
**Scope:** Backend Integration contracts only (no frontend coaching UX guidance)

## Purpose

This document is the backend contract source of truth for asynchronous Integration orchestration between:

- Integration Service (backend)
- AI template generation service
- CData execution path

It defines event schemas, lifecycle transitions, retryability semantics, idempotency, and tenant/security constraints.

## Cross-References

- Frontend/user-facing Integration service behavior: [../api-fe/traction-service/integration-service.md](../api-fe/traction-service/integration-service.md)
- Legacy coaching async frontend spec: [async-coaching-message-events.md](async-coaching-message-events.md)
- Architecture/process standards: [../../../standards/DEVELOPMENT_GUIDELINES.md](../../../standards/DEVELOPMENT_GUIDELINES.md)

---

## Event Contracts

### SQL Template Generation - Requested

- Detail type: `integration.sql.template.generate.requested`
- Source: `purposepath.integration`
- Envelope: `EventBridgeEnvelope<SqlTemplateGenerationRequestedDetail>`
- Contract version: `1.2`

Required identity fields in `detail`:

- `tenantId`
- `measureIntegrationId`
- `generationId`
- `idempotencyKey` (format: `tenant:{tenantId}|measureIntegration:{integrationId}|generation:{generationId}`)

### SQL Template Generation - Completed

- Detail type: `integration.sql.template.generate.completed`
- Source: `purposepath.integration.ai`
- Envelope: `EventBridgeEnvelope<SqlTemplateGenerationCompletedDetail>`

Behavior:

- Marks integration template generation state as `Completed`
- Stores generated template and template hash
- Clears last generation error metadata

### SQL Template Generation - Failed

- Detail type: `integration.sql.template.generate.failed`
- Source: `purposepath.integration.ai`
- Envelope: `EventBridgeEnvelope<SqlTemplateGenerationFailedDetail>`

Behavior:

- Marks integration template generation state as `Failed`
- Persists deterministic generation error metadata (`errorCode`, `errorStage`, `message`)

---

## Execution Queue Contracts

### Execution Requested (SQS)

Contract: `MeasureExecutionRequestMessage`

Required identity fields:

- `executionId`
- `integrationId`
- `tenantId`

### Execution Result (SQS)

Contract: `MeasureExecutionResultMessage`

Failure classification fields:

- `retryable` (bool)
- `failureClass` (`RETRYABLE`, `NON_RETRYABLE`, `CIRCUIT_BREAKER`)
- `errorCode` (deterministic string)
- `errorMessage` (sanitized)

Current deterministic classes:

- Retryable transient failures (`failureClass=RETRYABLE`)
- Non-retryable contract/auth/resource failures (`failureClass=NON_RETRYABLE`)
- Circuit-breaker state (`failureClass=CIRCUIT_BREAKER`) when explicitly emitted

---

## Lifecycle and Terminal Rules

### SQL Template Generation Lifecycle

Allowed lifecycle states:

- `Pending`
- `Requested`
- `Completed`
- `Failed`

Rules:

1. Exactly one terminal outcome per `(measureIntegrationId, generationId)` identity.
2. Duplicate terminal event with same terminal state is idempotent and ignored.
3. Conflicting terminal event for same generation id (e.g., completed then failed) is rejected.
4. Tenant mismatch between event and aggregate is rejected.

### Execution Lifecycle

Execution outcomes are processed idempotently by `executionId` and `dataSource`:

1. Duplicate execution results are ignored.
2. Retryable failures schedule retry.
3. Non-retryable failures block auto-execution.
4. Circuit-breaker opens after repeated retryable failures and blocks auto-execution.

---

## Retryability Semantics

### Template Generation Failed Contract

For `SqlTemplateGenerationFailedDetail`:

- `retryable=true` requires `retryAfterSeconds > 0`
- `retryable=false` requires `retryAfterSeconds = null`
- `errorCode` and `errorStage` must be from canonical constant sets

### Execution Result Contract

`retryable` and `failureClass` must agree semantically:

- `RETRYABLE` -> `retryable=true`
- `NON_RETRYABLE` -> `retryable=false`
- `CIRCUIT_BREAKER` -> terminal block/no auto-retry

---

## Deterministic Error Taxonomy

### Template Generation

Canonical values are defined in `SqlTemplateGenerationContractConstants`:

- Error codes: `SQL_POLICY_VIOLATION`, `SQL_VALIDATION_FAILED`, `SCHEMA_DISCOVERY_FAILED`, `MCP_TOOL_ERROR`, `AI_OUTPUT_INVALID`, `CDATA_AUTH_INVALID`, `CDATA_CONNECTION_NOT_FOUND`, `CDATA_RATE_LIMITED`, `INTERNAL_UNHANDLED`
- Error stages: `DISCOVER`, `GENERATE`, `VALIDATE`, `REPAIR`, `PUBLISH`

### Execution Processing

Deterministic execution error codes include:

- `EXECUTION_ARGUMENT_INVALID`
- `EXECUTION_CONTRACT_INVALID`
- `EXECUTION_RESOURCE_NOT_FOUND`
- `EXECUTION_INVALID_OPERATION`
- `EXECUTION_TRANSIENT`
- `EXECUTION_FAILED`
- `CDATA_AUTH_INVALID`

---

## Security and Tenant Isolation

1. Tenant identity is validated before applying terminal events.
2. Credentials must not be published in events.
3. Logs and emitted failure messages must be sanitized for sensitive tokens/secrets.
4. Connection/auth failures are represented by deterministic error codes, not raw secret payloads.

---

## Implementation Verification Checklist

- [x] Event schemas implementation-verified in code and tests
- [x] Terminal dedupe and conflicting terminal behavior covered in unit tests
- [x] Retryable/non-retryable semantics validated for failed template events
- [x] Execution failure class represented explicitly in queue contract
- [x] API parity fields for lifecycle/error observability exposed in active integration response
- [x] Cross-reference added to frontend integration-service specification

---

## Notes

- This file intentionally excludes frontend coaching-specific guidance.
- Frontend/client behavior belongs in [../api-fe/traction-service/integration-service.md](../api-fe/traction-service/integration-service.md).
