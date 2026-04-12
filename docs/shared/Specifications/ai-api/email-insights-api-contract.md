# Email Insights AI API Contract Specification

**Version:** 2.4  
**Last Updated:** April 9, 2026  
**Status:** Approved for Full Cutover  
**Scope:** Generic `email_insight` topics

[← Back to Specifications Index](../README.md)

---

## Revision Log

- 2026-04-09 - v2.4 - Added normative terminal EventBridge wire contract, terminal idempotency/ordering rules, and service-token auth contract for API fallback endpoints
- 2026-04-09 - v2.3 - Enforced transport-mode isolation: EventBridge mode is terminal-event-driven only; API polling is allowed only in API fallback mode
- 2026-04-08 - v2.2 - Added dual transport contract (EventBridge-first kickoff with API fallback) while keeping payload schema unchanged
- 2026-04-08 - v2.1 - Document server-side enrichment parameters for `goal_created_email_insight` (foundation + goal-scoped strategies/measures)
- 2026-03-27 - v2.0 - Full-cutover generic topic contract with required service token for enrichment API calls
- 2026-03-25 - v1.0 - Initial approved contract for activity-driven email insights v1 pilot

---

## 1. Overview

This specification defines the contract between backend orchestration and AI topic execution for generic activity-driven email insights.

It covers:

- Generic trigger request contract
- Transport contract (EventBridge-first with API fallback)
- Cross-system naming contract
- Service token and enrichment authorization contract
- AI payload schema contract
- Runtime validation/degradation rules
- Fallback reason/detail taxonomy for deterministic behavior

---

## 2. Contract Boundaries

- This is a **contract specification**, not an implementation guide.
- Email rendering and delivery remain backend-owned.
- AI output is structured content only; no raw HTML fragments.
- This contract is a full-cutover model and does not preserve pilot compatibility aliases.

---

## 3. Topic and Routing Contract

- `topicCategory`: `email_insight`.
- `topicId`: canonical AI insight topic identifier for the email insight request.
- `eventSignal`: business event signal that mapped this request to the configured topic.
- Routing rule: backend resolves `topicId` from registry/config and sends it explicitly to AI execution.
- No goal-only or pilot-only topic assumptions are permitted in this contract.

### 3.1 Canonical Naming Contract

Cross-system request/response naming between PurposePath_Api and PurposePath_AI is fixed to this specification. Deprecated aliases are out of scope for v2.0.

### 3.2 Transport Contract (Dual Method)

This specification supports two kickoff transports for the same logical request contract:

1. EventBridge-first kickoff (primary)
- Backend publishes the canonical request envelope to EventBridge for AI async execution kickoff.

2. API kickoff (fallback)
- Backend calls `POST /ai/execute-async` with the same canonical request envelope.

Transport invariants:
- Contract fields and semantics are identical across both methods.
- Validation, idempotency, correlation, and payload mapping behavior are identical across both methods.
- Response/result handling into template variables is identical across both methods.

Transport-mode isolation rules (normative):
- EventBridge mode and API mode are distinct execution modes and must not be mixed in a single attempt.
- If EventBridge kickoff publish succeeds, backend remains in EventBridge mode and waits for terminal completion through EventBridge terminal events.
- API job-status polling is disallowed in EventBridge mode.
- API fallback mode starts with API kickoff (`POST /ai/execute-async`) and owns API polling for that fallback attempt only.

### 3.3 EventBridge Kickoff Handshake (Normative Fields)

For EventBridge-first kickoff, the event detail payload must carry the canonical trigger contract fields from Section 4 plus the following transport metadata:

- `jobId` (string, required): requested async job identifier used for downstream status tracking.
- `eventType` (string, required): business event type associated with the request.
- `kickoffTransport` (string, required): `eventbridge`.

Event routing identity contract for EventBridge kickoff events:

- `source` (string, required): backend-configured source identity.
- `detail-type` (string, required): backend-configured AI kickoff detail type.
- `eventBusName` (string, required): backend-configured EventBridge bus name.

### 3.3.1 Routing Identity Defaults and Source of Truth (Normative)

To prevent cross-repo drift, the routing identity values below are normative defaults for PurposePath_Api and PurposePath_AI:

- `source`: `purposepath.api`
- `detail-type`: `ai.job.requested`
- `eventBusName`: `purposepath-domain-events-{env}`

Environment baseline (current contract default):

| Environment | source | detail-type | eventBusName |
|-------------|--------|-------------|--------------|
| dev | `purposepath.api` | `ai.job.requested` | `purposepath-domain-events-dev` |
| staging | `purposepath.api` (unless jointly overridden) | `ai.job.requested` (unless jointly overridden) | `purposepath-domain-events-staging` (unless jointly overridden) |
| prod | `purposepath.api` (unless jointly overridden) | `ai.job.requested` (unless jointly overridden) | `purposepath-domain-events-prod` (unless jointly overridden) |

Override rule (normative):

- Any environment-specific override must be defined in shared deployment configuration used by both API and AI infrastructure.
- API publisher configuration and AI EventBridge rule configuration must be changed together in the same release plan.
- If an override is introduced, this specification must be updated in the same change set to keep this document authoritative.

AI-side EventBridge consumers must treat `source` + `detail-type` as routing keys and `detail` as the canonical request envelope (plus transport metadata above).

Correlation and idempotency handshake contract:

- `requestId` is required kickoff request identity and is carried as explicit field in trigger detail.
- `eventId` is kickoff message identity for event lineage and telemetry.
- `correlationId` is end-to-end trace identity and must propagate unchanged through job lifecycle events.
- `idempotencyKey` is duplicate-protection identity and must be honored across kickoff methods.

Status expectation contract:

- `jobId` is the status lookup identity for asynchronous completion checks.
- Terminal status semantics (`completed`, `failed`, `cancelled`, `timed_out`) remain identical across transport methods.
- Insight payload extraction semantics remain identical across transport methods.

### 3.4 EventBridge Kickoff Wire Format (Normative)

The backend publishes one EventBridge entry per kickoff request.

EventBridge entry identity fields:

- `source` maps to configured `AiService:EventBridgeSource`.
- `detail-type` maps to configured `AiService:EventBridgeDetailType`.
- `eventBusName` maps to configured `AiService:EventBridgeEventBusName`.

Default runtime values in current NotificationProcessor implementation:

- `AiService:EventBridgeSource = purposepath.api`
- `AiService:EventBridgeDetailType = ai.job.requested`
- `AiService:EventBridgeEventBusName = purposepath-domain-events-{env}`

EventBridge `detail` JSON is the canonical trigger envelope from Section 4 plus transport fields from Section 3.3. Minimum required shape:

```json
{
   "eventId": "uuid",
   "requestId": "notification-request-uuid",
   "occurredAtUtc": "2026-04-09T13:00:00.0000000Z",
   "sourceService": "PurposePath.NotificationProcessor.Lambda",
   "schemaVersion": "2.0",
   "correlationId": "corr-123",
   "idempotencyKey": "req-123:goal_created_email_insight:uuid",
   "retryAttempt": 0,
   "tenantId": "tenant-1",
   "userId": "user-1",
   "topicCategory": "email_insight",
   "topicId": "goal_created_email_insight",
   "eventSignal": "goal_created_email_insight",
   "locale": "en-US",
   "timezone": "UTC",
   "activityData": {
      "goal_id": "goal-1"
   },
   "authContext": {
      "serviceToken": "opaque-token",
      "expiresAtUtc": "2026-04-09T13:05:00Z",
      "issuer": "purposepath-api",
      "tokenType": "service_enrichment"
   },
   "jobId": "job-uuid",
   "eventType": "goal_created_email_insight",
   "kickoffTransport": "eventbridge"
}
```

AI-side consumer requirements:

- Treat `detail.topicCategory`, `detail.topicId`, and `detail.eventSignal` as authoritative routing context.
- Use `detail.jobId` as the async status identity for terminal completion updates.
- Preserve `correlationId`, `idempotencyKey`, and `eventId` in AI-side telemetry and status lifecycle records.

### 3.5 API Kickoff Wire Format (Fallback Contract)

Fallback kickoff request body is byte-for-byte the same canonical trigger envelope (Section 4) without EventBridge transport identity fields (`source`, `detail-type`, `eventBusName`).

API kickoff response contract (minimum):

```json
{
   "data": {
      "jobId": "job-uuid"
   }
}
```

The backend also accepts `data.job_id` as an implementation-tolerant alias, but AI service contract output should use canonical `data.jobId`.

### 3.6 Job Status Wire Contract (API Fallback Mode)

For API fallback mode, backend status polling expects:

```json
{
   "data": {
      "status": "completed|failed|cancelled|timed_out|running|queued",
      "result": {
         "schemaVersion": "1.0.0",
         "title": "...",
         "summary": "...",
         "blocks": [],
         "generationMeta": {}
      }
   }
}
```

Status contract notes (API fallback mode):

- `data.status` is required.
- `data.result` is required only when `status=completed`.
- On `completed`, missing or empty `result` is treated as non-recoverable completion without payload (no API fallback).
- On status request HTTP failure or missing `data.status`, backend handles failure according to API fallback retry/timeout policy.

Fallback trigger contract:

- API fallback may be activated when EventBridge kickoff publish fails, or when EventBridge terminal SLA expires according to backend policy.
- API fallback must reuse canonical request semantics and preserve correlation/idempotency lineage.

Mode transition rule:
- API fallback activation must create a new attempt in API mode. API-mode polling must not execute while backend is in EventBridge mode.

Network requirement for fallback:
- API fallback requires outbound HTTPS connectivity on port 443 from backend runtime to the AI API host.

### 3.7 Terminal EventBridge Wire Contract (Normative)

When EventBridge kickoff succeeds, completion is delivered only through terminal EventBridge events.

Terminal routing identity:

- `source` (required): `purposepath.ai`
- `detail-type` (required): `ai.job.completed` or `ai.job.failed`
- `eventBusName` (required): shared domain event bus for environment (for example, `purposepath-domain-events-dev`)

Terminal detail required fields:

- `schemaVersion` (string, required): `2.4`
- `eventId` (string, required): terminal message identity
- `occurredAtUtc` (string date-time, required)
- `sourceService` (string, required)
- `status` (string, required): `completed` or `failed`
- `jobId` (string, required)
- `requestId` (string, required): notification request identity used by API consumer
- `kickoffEventId` (string, required): original kickoff request event identity
- `tenantId` (string, required)
- `userId` (string, required)
- `correlationId` (string, required)
- `idempotencyKey` (string, required)
- `topicCategory` (string, required): `email_insight`
- `topicId` (string, required)
- `eventSignal` (string, required)
- `kickoffTransport` (string, required): `eventbridge`
- `executionMode` (string, required): `eventbridge_terminal`
- `data` (object, required)

Terminal completed payload shape:

- `data.result` (object, required): must satisfy Section 5 `purposepath.email-insight.v1` payload contract

Terminal failed payload shape:

- `data.errorCode` (string, required)
- `data.error` (string, required)

Normative completed example:

```json
{
   "schemaVersion": "2.4",
   "eventId": "terminal-event-uuid",
   "occurredAtUtc": "2026-04-09T13:10:00.0000000Z",
   "sourceService": "PurposePath.AI",
   "status": "completed",
   "jobId": "job-uuid",
   "requestId": "notification-request-uuid",
   "kickoffEventId": "kickoff-event-uuid",
   "tenantId": "tenant-1",
   "userId": "user-1",
   "correlationId": "corr-123",
   "idempotencyKey": "requestId:topicId:attempt-uuid",
   "topicCategory": "email_insight",
   "topicId": "goal_created_email_insight",
   "eventSignal": "goal_created_email_insight",
   "kickoffTransport": "eventbridge",
   "executionMode": "eventbridge_terminal",
   "data": {
      "result": {
         "schemaVersion": "1.0.0",
         "title": "string",
         "summary": "string",
         "blocks": [],
         "generationMeta": {
            "modelId": "string",
            "promptVersion": "string",
            "traceId": "string",
            "generatedAtUtc": "2026-04-09T13:09:59.0000000Z",
            "topicId": "goal_created_email_insight"
         }
      }
   }
}
```

Normative failed example:

```json
{
   "schemaVersion": "2.4",
   "eventId": "terminal-event-uuid",
   "occurredAtUtc": "2026-04-09T13:10:00.0000000Z",
   "sourceService": "PurposePath.AI",
   "status": "failed",
   "jobId": "job-uuid",
   "requestId": "notification-request-uuid",
   "kickoffEventId": "kickoff-event-uuid",
   "tenantId": "tenant-1",
   "userId": "user-1",
   "correlationId": "corr-123",
   "idempotencyKey": "requestId:topicId:attempt-uuid",
   "topicCategory": "email_insight",
   "topicId": "goal_created_email_insight",
   "eventSignal": "goal_created_email_insight",
   "kickoffTransport": "eventbridge",
   "executionMode": "eventbridge_terminal",
   "data": {
      "errorCode": "ENRICHMENT_AUTH_FORBIDDEN",
      "error": "Service token rejected by enrichment API"
   }
}
```

### 3.8 Terminal Idempotency and Ordering Contract

Terminal processing behavior is deterministic and first-wins:

- Finalization identity is `requestId`.
- Duplicate terminal deliveries (same request/job/status) must be ignored idempotently.
- Conflicting late terminals after finalization must not reopen processing.
- Consumers should emit telemetry for duplicate and conflict terminal deliveries.

Fallback SLA contract:

- EventBridge terminal wait is bounded by `AiService:EventBridgeTerminalSlaMs`.
- On SLA expiry without terminal event, backend may start a new API fallback attempt.
- API fallback attempt uses API kickoff and API polling exclusively.

---

## 4. Trigger Request Contract

The trigger request payload defined below is canonical and transport-agnostic. It applies equally to EventBridge-first and API-fallback kickoff paths.

### 4.1 Required Fields

- `eventId` (string, required): Unique request event identifier.
- `requestId` (string, required): Notification request identity used for terminal correlation.
- `occurredAtUtc` (string date-time, required): Request timestamp.
- `sourceService` (string, required): Originating backend service.
- `schemaVersion` (string, required): Request schema version.
- `correlationId` (string, required): Distributed trace correlation.
- `idempotencyKey` (string, required): Duplicate protection key.
- `retryAttempt` (integer, required): Current retry count.
- `tenantId` (string, required): Tenant context.
- `userId` (string, required): User context.
- `topicCategory` (string, required): Must be `email_insight`.
- `topicId` (string, required): Resolved AI insight topic.
- `eventSignal` (string, required): Business event signal that selected the topic.
- `locale` (string, required): Locale code.
- `timezone` (string, required): Time zone identifier.
- `activityData` (object, required): Topic input context payload.
- `authContext` (object, required): Service-token authorization context for enrichment calls.

### 4.2 Optional Fields

- `causationId` (string, optional): Parent causation reference.
- `metadata` (object, optional): Non-contractual extensibility metadata.

### 4.3 Required `authContext` Fields

- `serviceToken` (string, required): Backend-issued short-lived bearer token.
- `expiresAtUtc` (string date-time, required): Token expiry timestamp.
- `issuer` (string, required): Token issuer identifier.
- `tokenType` (string, required): Must be `service_enrichment`.

### 4.4 Authorization Behavior

- Backend API issues the token and includes it in request payload.
- AI service must not mint, mutate, or re-sign the token.
- AI service forwards token to standard backend user-facing API endpoints for enrichment.
- Backend user-facing endpoints validate token through standard authentication/authorization components.

### 4.6 API Fallback Endpoint Auth Contract (Service Token)

For API fallback mode, backend calls both endpoints with the same service token from `authContext.serviceToken`:

- `POST /api/v1/ai/execute-async`
- `GET /api/v1/ai/jobs/{jobId}`

HTTP auth requirement:

- `Authorization: Bearer {serviceToken}`

Accepted service-token claims contract:

- token type claim identifies `service_enrichment`
- service role claim identifies non-user service principal (for example `role=service`)
- issuer claim is trusted by AI auth configuration
- audience claim includes AI API audience
- tenant claim is present and required for tenancy enforcement

Tenant isolation contract for `GET /api/v1/ai/jobs/{jobId}`:

- Endpoint may be called without user session when valid service token is present.
- AI must validate that token tenant claim matches tenant stored on the job record.
- Mismatch must return authorization failure.

### 4.5 Server-side enrichment (`goal_created_email_insight`)

Orchestrators still supply topic input primarily via `goal_id` (and standard user/tenant context) plus `authContext` for enrichment API calls. The AI coaching service resolves additional **template parameters** (not required in the trigger `activityData` payload) using the same retrieval stack as other single-shot topics, including:

- Business foundation: `vision`, `purpose`, `core_values`, `business_name`
- Goal: full `goal` record plus `goal_title`, `goal_description`, `goal_intent` where available
- Goal-scoped strategies: `existing_strategies_for_goal` (formatted list of strategies whose `goalId` matches `goal_id`)
- Goal-scoped measures: `measures_formatted_for_goal` (formatted list of measures linked via `goalId` or `connections.goalIds`)

Exact placeholder names and prompt wording live in topic seed data and deployed prompts; this section records **contractual expectation** that enrichment uses `goal_id` to scope strategies and measures.

---

## 5. AI Output Payload Contract (`purposepath.email-insight.v1`)

### 5.1 Payload Requirements

- Must be exactly one JSON object.
- Must not include prose outside JSON.
- Must not include markdown/code fences/HTML/XML in text fields.
- Must be topic-agnostic and valid for any approved `email_insight` topic.

### 5.2 Field Contract

- `schemaVersion` (string, required): Semver string.
- `title` (string, required).
- `summary` (string, required).
- `blocks` (array, required): at least one item.
- `confidence` (optional): Numeric `0..1` or enum `low|medium|high`.
- `generationMeta` (object, required): Metadata object.

`generationMeta` required fields:

- `modelId`
- `promptVersion`
- `traceId`
- `generatedAtUtc` (date-time)
- `topicId`

### 5.3 Block Contract (v1)

Allowed block types:

- `paragraph`
- `list`
- `cta`

Block constraints:

- `paragraph.text`: non-empty
- `list.items`: at least one item
- `list.items[]`: non-empty text
- `cta.label`: non-empty
- `cta.action`: non-empty
- `cta.url`: optional URI string (then https-only backend gate applies)

Unknown block types are non-fatal and handled by pre-validation filtering rules in Section 6.

---

## 6. Normative Runtime Contract Rules

Processing order is normative:

1. Parse AI response as exactly one JSON object, else deterministic fallback.
2. Pre-sanitize tolerant optional fields:
   - Invalid `confidence` is removed/suppressed (non-fatal).
3. Pre-filter blocks:
   - Keep only `paragraph | list | cta`.
   - Drop unknown block types with telemetry.
4. CTA URL gate per kept CTA block:
   - URI parse first, then enforce https-only.
   - Invalid/non-https URL drops CTA block only with telemetry.
5. If no blocks remain after filtering/dropping:
   - Degrade to template-only behavior with deterministic fallback reason/detail.
6. Strict schema validation executes on the sanitized payload.
7. Normalize text and evaluate length/count guidance as non-fatal drift telemetry.
8. Backend renders final HTML/text insight fragments and proceeds with email send.

Token and enrichment execution behavior is also normative:

1. AI receives `authContext.serviceToken` and uses it when calling backend enrichment APIs.
2. AI treats token as opaque bearer value.
3. If enrichment API auth fails, AI returns deterministic execution failure path (Section 8.4).

Transport execution behavior is also normative:

1. EventBridge mode is terminal-event-driven and does not perform API polling.
2. API polling behavior is exclusive to API fallback mode.
3. Duplicate or delayed terminal outcomes across modes must be handled idempotently by backend.

---

## 7. Normalization and Length Guidance

### 7.1 Normalization Algorithm

All length checks use normalized text:

1. Trim leading/trailing whitespace.
2. Collapse repeated whitespace to single spaces.
3. Remove control characters except newline.
4. Normalize line breaks to `\n`.

### 7.2 Guidance Targets

- `title <= 120` (guidance target)
- `summary <= 500` (guidance target)
- `max blocks = 6` (guidance target)
- `paragraph <= 600` (guidance target)
- `list items <= 6` (guidance target)
- `list item <= 180` (guidance target)
- `combinedInsightLength <= 2000` (guidance target)

`combinedInsightLength`:

- normalized `title`
- normalized `summary`
- normalized `paragraph.text`
- normalized `list.items[]`
- normalized `cta.label`
- normalized `cta.action`

Guidance overrun must not, by itself, trigger template-only fallback when payload remains structurally valid and safe to render.

---

## 8. Fallback Reason/Detail Taxonomy (Contracted Values)

### 8.1 Canonical Schema-Major Fallback (Locked)

- `fallbackReason = AI_SCHEMA_VERSION_UNSUPPORTED`
- `fallbackDetail = unsupported_major`

### 8.2 Locked CTA URL Fallback Path

- `fallbackReason = AI_SCHEMA_VALIDATION_FAILED`
- `fallbackDetail = cta_url_not_https_or_invalid`

### 8.3 Additional Deterministic Paths

The system must emit deterministic reason/detail values for:

- malformed JSON parse failure
- payload empty after filtering
- schema validation failure
- timeout
- unknown execution failure

### 8.4 Required Auth/Enrichment Failure Paths

The system must emit deterministic reason/detail values for:

- missing service token
- expired service token
- invalid token
- insufficient token scope/claims
- enrichment API authorization failure
- service-token audience mismatch
- service-token issuer mismatch
- service-token tenant mismatch on job status access

---

## 9. Template Variable Contract (v1)

Backend provides these runtime variables:

- `insight_enabled`
- `insight_title`
- `insight_summary`
- `insight_html`
- `insight_text`
- `insight_cta_label` (optional)
- `insight_cta_url` (optional)
- `insight_confidence_label` (optional)

Variable semantics are topic-agnostic and apply to any approved `email_insight` topic.

---

## 10. Full-Cutover Acceptance Criteria (Contract-Level)

- Generic topic request model is implemented for `email_insight` topics.
- Canonical naming in this spec is used consistently across PurposePath_Api and PurposePath_AI.
- Service token is required in request and used for enrichment API calls.
- AI does not mint or alter tokens; backend remains auth authority.
- EventBridge primary path remains transport-pure (no API polling in EventBridge attempts).
- API fallback path remains transport-pure (API kickoff + API polling within API attempts).
- Processing order implemented exactly as specified.
- Strict validation occurs only after pre-sanitization and pre-filtering.
- Confidence invalid/missing does not fail send.
- CTA invalid URL degrades CTA block only when other blocks remain.
- Zero usable blocks degrades to deterministic fallback behavior.
- Locked fallback taxonomy values are emitted as specified.
- Preview/test/prod parity is verified for identical sanitized payloads.
