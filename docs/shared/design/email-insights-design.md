# Email Insights Design (v1 Pilot)

**Version:** 1.0  
**Date:** March 25, 2026  
**Status:** Approved for Implementation  
**Pilot Topic:** `goal_created_email_insight`

---

## Executive Summary

PurposePath will extend its existing email notification system with AI-generated insight content triggered by user activity in the frontend.  
The v1 pilot introduces one topic, `goal_created_email_insight`, and uses the current email template pipeline plus a new structured AI content contract.

The design intentionally keeps:

- **Email rendering and delivery ownership in backend**
- **Prompt/topic authoring in the existing AI admin topic workflow**
- **Strong safety controls and deterministic fallback behavior**

---

## Goals

- Deliver timely, personalized insight emails after key user actions.
- Reuse existing topic-driven AI execution and admin prompt configuration.
- Keep AI output safe, deterministic, and embeddable in current templates.
- Prevent AI failures from blocking email delivery.

---

## Non-Goals (v1)

- Building a new standalone email rendering engine in AI service.
- Supporting arbitrary rich content types beyond `paragraph`, `list`, `cta`.
- Replacing existing system transactional emails.
- Introducing nested template models for AI content.

---

## Design Principles

1. **Topic-centric routing:** event signal maps directly to AI `topicId`.
2. **Backend-owned rendering:** AI returns structured content, never raw HTML fragments.
3. **Fail-open email delivery:** if AI fails, template-only email still sends.
4. **Deterministic safety:** schema checks, normalization, limits, sanitization, and stable fallback taxonomy.
5. **Operational observability:** telemetry for every fallback and degradation path.

---

## High-Level Architecture

1. Frontend activity occurs (example: goal created).
2. Backend emits activity event with explicit user and tenant context.
3. Backend triggers AI topic execution using `topicId` (same as event signal).
4. AI returns structured payload (`purposepath.email-insight.v1`).
5. Backend applies pre-sanitization and filtering rules.
6. Backend validates sanitized payload, enforces limits, renders HTML/text fragments.
7. Backend merges rendered insight variables into existing email template.
8. Email is delivered using current backend email pipeline.

---

## Ownership Boundaries

### AI Service

- Topic category and topic definitions (`email_insight` topics).
- Prompt lifecycle through existing admin topic prompt workflow.
- Structured JSON output for email insight content.
- Prompt-level style and forbidden-content guidance.

### Backend Service

- Event ingestion and orchestration.
- Sanitization/filtering/validation/normalization and limits enforcement.
- HTML/text rendering from semantic blocks.
- Template merge and delivery.
- Retry, fallback, and telemetry.

---

## Topic and Event Model

- **Topic category:** `email_insight`
- **Topic signal:** `topicId` equals event signal
- **Pilot topic:** `goal_created_email_insight`
- **Event required fields:**
  - `eventId`
  - `occurredAtUtc`
  - `sourceService`
  - `schemaVersion`
  - `correlationId`
  - `idempotencyKey`
  - `retryAttempt`
  - `tenantId`
  - `userId`
  - `topicId`
  - `locale`
  - `timezone`
  - `activityData`
- **Optional:** `causationId`

---

## AI Payload Contract Summary

AI payload schema: `purposepath.email-insight.v1`

- Required fields: `schemaVersion`, `title`, `summary`, `blocks`, `generationMeta`
- Optional field: `confidence`
- Allowed block types (v1): `paragraph`, `list`, `cta`
- `confidence` may be numeric (`0..1`) or enum (`low|medium|high`)

---

## Normative Runtime Processing Order (Locked)

1. Parse AI response as exactly one JSON object, else deterministic fallback.
2. Pre-sanitize tolerant optional fields:
   - Invalid `confidence` is removed/suppressed (non-fatal).
3. Pre-filter blocks:
   - Keep only `paragraph | list | cta`.
   - Drop unknown block types with telemetry.
4. CTA gate on each kept CTA block:
   - Parse URI (if present), then enforce https-only.
   - Invalid/non-https URL drops CTA block only with telemetry.
5. If no blocks remain after filtering/dropping:
   - Degrade to template-only send with deterministic reason/detail.
6. Run strict schema validation on sanitized payload.
7. Normalize text and enforce post-normalization limits.
8. Render backend-owned HTML/text fragments and send email.

---

## Normalization and Limits (Locked)

Normalization algorithm used for all length checks:

1. Trim leading/trailing whitespace.
2. Collapse repeated whitespace to single spaces.
3. Remove control characters except newline.
4. Normalize line breaks to `\n`.

Limits:

- `title <= 120`
- `summary <= 500`
- `max blocks = 6`
- `paragraph <= 600`
- `list items <= 6`
- `list item <= 180`
- `combinedInsightLength <= 2000`

`combinedInsightLength` scope:

- normalized `title`
- normalized `summary`
- normalized `paragraph.text`
- normalized `list.items[]`
- normalized `cta.label`
- normalized `cta.action`

---

## Template Variable Mapping (v1 Flat Model)

- `insight_enabled`
- `insight_title`
- `insight_summary`
- `insight_html`
- `insight_text`
- `insight_cta_label` (optional)
- `insight_cta_url` (optional)
- `insight_confidence_label` (optional)

---

## Fallback and Telemetry Taxonomy

Canonical schema-major fallback (locked):

- `fallbackReason = AI_SCHEMA_VERSION_UNSUPPORTED`
- `fallbackDetail = unsupported_major`

Locked CTA invalid URL fallback path:

- `fallbackReason = AI_SCHEMA_VALIDATION_FAILED`
- `fallbackDetail = cta_url_not_https_or_invalid`

Additional deterministic fallback scenarios include:

- malformed JSON
- empty/unsupported usable block set
- strict schema validation failure
- limit exceeded
- timeout or unknown execution failure

---

## Safety and Compliance Controls

- AI output must be JSON-only (no markdown, code fences, HTML/XML in fields).
- Prompt-level forbidden-content constraints are required.
- Backend remains authoritative for validation and rendering safety.
- Unknown or invalid optional fields should degrade gracefully when safe.

---

## Pilot Acceptance Criteria

- Processing order implemented exactly as locked.
- Schema validation performed after pre-sanitization/filtering.
- Confidence absence/invalid is non-fatal.
- CTA invalid URL degrades CTA only when other content remains.
- Zero usable block case degrades to template-only send.
- Canonical schema-major fallback reason/detail emitted.
- Preview/test/prod render parity validated.
- End-to-end flow validated for `goal_created_email_insight`.

---

## Implementation Readiness

This design is approved by both AI and backend review for v1 pilot execution.
