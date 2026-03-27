# Email Insights AI API Contract Specification

**Version:** 2.0  
**Last Updated:** March 27, 2026  
**Status:** Approved for Full Cutover  
**Scope:** Generic `email_insight` topics

[← Back to Specifications Index](../README.md)

---

## Revision Log

- 2026-03-27 - v2.0 - Full-cutover generic topic contract with required service token for enrichment API calls
- 2026-03-25 - v1.0 - Initial approved contract for activity-driven email insights v1 pilot

---

## 1. Overview

This specification defines the contract between backend orchestration and AI topic execution for generic activity-driven email insights.

It covers:

- Generic trigger request contract
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

---

## 4. Trigger Request Contract

### 4.1 Required Fields

- `eventId` (string, required): Unique request event identifier.
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

---

## 5. AI Output Payload Contract (`purposepath.email-insight.v1`)

### 5.1 Payload Requirements

- Must be exactly one JSON object.
- Must not include prose outside JSON.
- Must not include markdown/code fences/HTML/XML in text fields.
- Must be topic-agnostic and valid for any approved `email_insight` topic.

### 5.2 Field Contract

- `schemaVersion` (string, required): Semver string.
- `title` (string, required): Length 1..120.
- `summary` (string, required): Length 1..500.
- `blocks` (array, required): 1..6 items.
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

- `paragraph.text`: `1..600`
- `list.items`: `1..6`
- `list.items[]`: `1..180`
- `cta.label`: `1..80`
- `cta.action`: `1..120`
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
7. Normalize text and enforce all post-normalization limits.
8. Backend renders final HTML/text insight fragments and proceeds with email send.

Token and enrichment execution behavior is also normative:

1. AI receives `authContext.serviceToken` and uses it when calling backend enrichment APIs.
2. AI treats token as opaque bearer value.
3. If enrichment API auth fails, AI returns deterministic execution failure path (Section 8.4).

---

## 7. Normalization and Limit Enforcement

### 7.1 Normalization Algorithm

All length checks use normalized text:

1. Trim leading/trailing whitespace.
2. Collapse repeated whitespace to single spaces.
3. Remove control characters except newline.
4. Normalize line breaks to `\n`.

### 7.2 Limits

- `title <= 120`
- `summary <= 500`
- `max blocks = 6`
- `paragraph <= 600`
- `list items <= 6`
- `list item <= 180`
- `combinedInsightLength <= 2000`

`combinedInsightLength`:

- normalized `title`
- normalized `summary`
- normalized `paragraph.text`
- normalized `list.items[]`
- normalized `cta.label`
- normalized `cta.action`

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
- limit exceeded
- timeout
- unknown execution failure

### 8.4 Required Auth/Enrichment Failure Paths

The system must emit deterministic reason/detail values for:

- missing service token
- expired service token
- invalid token
- insufficient token scope/claims
- enrichment API authorization failure

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
- Processing order implemented exactly as specified.
- Strict validation occurs only after pre-sanitization and pre-filtering.
- Confidence invalid/missing does not fail send.
- CTA invalid URL degrades CTA block only when other blocks remain.
- Zero usable blocks degrades to deterministic fallback behavior.
- Locked fallback taxonomy values are emitted as specified.
- Preview/test/prod parity is verified for identical sanitized payloads.
