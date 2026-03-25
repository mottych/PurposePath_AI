# Email Insights AI API Contract Specification

**Version:** 1.0  
**Last Updated:** March 25, 2026  
**Status:** Approved for v1 Pilot  
**Scope:** `goal_created_email_insight`

[← Back to Specifications Index](../README.md)

---

## Revision Log

- 2026-03-25 - v1.0 - Initial approved contract for activity-driven email insights v1 pilot

---

## 1. Overview

This specification defines the contract between backend orchestration and AI topic execution for activity-driven email insights.

It covers:

- Event trigger contract
- AI payload schema contract
- Runtime validation/degradation rules
- Fallback reason/detail taxonomy for deterministic behavior

---

## 2. Contract Boundaries

- This is a **contract specification**, not an implementation guide.
- Email rendering and delivery remain backend-owned.
- AI output is structured content only; no raw HTML fragments.

---

## 3. Topic and Routing Contract

- `topicCategory`: `email_insight`
- `topicId`: event signal (for v1 pilot: `goal_created_email_insight`)
- Routing rule: event topic signal maps directly to AI topic execution.

---

## 4. Trigger Event Contract

### 4.1 Required Fields

- `eventId` (string, required): Unique event identifier.
- `occurredAtUtc` (string date-time, required): Event timestamp.
- `sourceService` (string, required): Originating service.
- `schemaVersion` (string, required): Event schema version.
- `correlationId` (string, required): Distributed trace correlation.
- `idempotencyKey` (string, required): Duplicate protection key.
- `retryAttempt` (integer, required): Current retry count.
- `tenantId` (string, required): Tenant context.
- `userId` (string, required): User context.
- `topicId` (string, required): AI topic signal.
- `locale` (string, required): Locale code.
- `timezone` (string, required): Time zone identifier.
- `activityData` (object, required): Trigger-specific payload.

### 4.2 Optional Fields

- `causationId` (string, optional): Parent causation reference.

---

## 5. AI Output Payload Contract (`purposepath.email-insight.v1`)

### 5.1 Payload Requirements

- Must be exactly one JSON object.
- Must not include prose outside JSON.
- Must not include markdown/code fences/HTML/XML in text fields.

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

---

## 10. Pilot Acceptance Criteria (Contract-Level)

- Processing order implemented exactly as specified.
- Strict validation occurs only after pre-sanitization and pre-filtering.
- Confidence invalid/missing does not fail send.
- CTA invalid URL degrades CTA block only when other blocks remain.
- Zero usable blocks degrades to template-only behavior.
- Locked fallback taxonomy values are emitted as specified.
- Preview/test/prod parity is verified for identical sanitized payloads.
