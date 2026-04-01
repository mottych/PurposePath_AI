# Unified Email Notification System - Requirements (Target State)

**Version:** 0.2 (Draft)  
**Date:** March 31, 2026  
**Status:** Draft for Review

---

## 1. Purpose

Define the target-state requirements for a unified email notification system with a single code-based notification registry, deterministic template/enrichment processing, and consistent delivery/audit behavior.

This document is requirements-only and intentionally precedes design.

---

## 2. Context and Drivers

- Align with the streamlined email refactor direction established in Epic #771.
- Remove ambiguity between code-defined notification events and persisted configuration sources.
- Enable admin template maintenance without allowing undefined runtime notification types.
- Preserve AI-insight capability as a parameterized enrichment path, not a separate notification model.

---

## 3. Source of Truth Requirements

### 3.1 Notification Definitions

- Notification definitions MUST be defined in a single code registry.
- No database table or external config source may define new notification types.
- A notification is valid only if present in the code registry.

### 3.2 Required Notification Definition Fields

Each notification definition MUST include:

- `notification_id` (stable unique identifier)
- `name` (display name)
- `description`
- `category`
- `template_id`
- `is_mandatory`
- `required_parameters`
- `optional_parameters`

### 3.3 Registry Integrity

- Registry identifiers MUST be unique and deterministic.
- Registry definitions MUST be backward-compatible unless explicitly versioned and approved.

---

## 4. Trigger and Dispatch Requirements

### 4.1 Trigger Contract

When an email notification is requested, the caller MUST provide:

- `notification_id`
- Core context inputs needed by runtime processing (for example tenant/user identifiers)
- Event-specific payload parameters

### 4.2 Registry Resolution

- Notification handler MUST resolve notification metadata from the code registry using `notification_id`.
- If `notification_id` is unknown, request MUST fail with explicit validation error.

### 4.3 Preference and Mandatory Policy

- If `is_mandatory = true`, notification MUST bypass optional preference suppression.
- If `is_mandatory = false`, notification handler MUST evaluate user notification preferences before send.

---

## 5. Template Processing Requirements

### 5.1 Template Selection

- Template processor MUST resolve template by `template_id` from the notification registry.
- Missing template behavior MUST be deterministic and auditable.

### 5.2 Parameter Resolution Model

Template processor MUST compute final merge parameters from three sources:

- Trigger-provided parameters
- Backend enrichment sources (database/services/handlers)
- AI enrichment source (when template/notification requires AI insight)

### 5.3 AI Insight as Parameterized Enrichment

- AI insight MUST be treated as parameter enrichment.
- AI insight is associated to AI topic system via parameter/config mapping, not as a separate notification-definition source.

### 5.4 Parameter Validation

- Processor MUST validate required template merge parameters before rendering.
- Some notification-required parameters may be enrichment-only and not directly referenced in template markup; these still MUST be validated for processing completeness.

### 5.5 Rendering

- Final merge MUST be executed by the existing Razor/Blazor template merge engine.
- Renderer input MUST include only resolved/validated parameters required by the template.

---

## 6. Delivery and Audit Requirements

### 6.1 Delivery

- Sending component MUST deliver through AWS SES.
- Sender MAY enrich delivery metadata required for transport/compliance (for example addressing metadata).

### 6.2 Auditing and Observability

- System MUST log notification lifecycle and send outcome.
- System MUST record decision metadata for policy outcomes (sent/suppressed/fallback/failure).
- System MUST preserve correlation identifiers across trigger, processing, and delivery stages.

---

## 7. Admin Maintenance Requirements

### 7.1 Allowed Admin Scope

- Admins MAY manage template content and metadata.
- Admins MUST NOT create new notification definitions at runtime.

### 7.2 Notification Catalog Visibility

- System MUST expose a read API for admin UI to list all registry-defined notifications with:
  - `notification_id`
  - `name`
  - `description`
  - `category`
  - `template_id`
  - template existence status

This requirement is mandatory for practical template maintenance.

---

## 8. Non-Goals

- Runtime creation of notification types from DB/admin UI.
- Multi-source definition ownership for notification identity.
- Replacing SES provider in this phase.

---

## 9. Acceptance Criteria

- Notification type catalog exists only in code registry.
- Unknown `notification_id` cannot be processed.
- Notification processing enforces mandatory vs preference policy.
- Template processing performs deterministic enrichment and required-parameter validation.
- AI insight executes as parameter enrichment path without introducing new notification-definition source.
- Admin can list all registry notifications and maintain associated templates without knowing hidden IDs.
- End-to-end send flow is auditable from trigger to SES outcome.

---

## 10. Migration and Compatibility Constraints

- Existing active notification IDs must remain stable during migration.
- Existing template IDs may continue, but mapping authority must be registry-defined.
- Legacy paths that derive notification identity from DB-only records must be retired or constrained to registry-backed entries.

---

## 11. Inputs Used to Draft This Requirement

- User-defined target workflow and architecture constraints (March 31, 2026).
- Epic #771 objective/scope and completion context.
- Existing shared docs for streamlined email cutover and email insights requirements.

---

## 12. Operating Model Clarification (Interim)

This section clarifies the intended model to carry into design:

- Notification identity and catalog come only from code registry.
- Admin cannot create new notification IDs/topics at runtime.
- Persisted configuration may exist only as overrides for existing registry IDs.
- Any persisted override MUST reference a valid registry ID.
- Template mapping authority remains registry-defined; overrides are allowed only where explicitly approved in design.

---

## 13. Capability Gap Analysis (Current vs Target)

This section captures capability-level gaps only. It does not prescribe implementation details.

### 13.1 Capability Matrix

| Capability | Target Requirement | Current State (Observed) | Gap Status |
|---|---|---|---|
| Notification source of truth | Single code registry defines notification catalog | Code registry exists, plus persisted event-definition store used at runtime | Partial |
| Runtime creation of notification types | Not allowed | Runtime persisted records can exist outside pure code-only governance model | Gap |
| Admin notification visibility | Admin can list all registry notifications with template mapping and existence status | No dedicated admin endpoint currently provides notification catalog view | Gap |
| Template maintenance UX | Notification-first maintenance flow is possible without hidden IDs | Existing admin flow is template-centric | Partial |
| Trigger contract | Trigger by `notification_id` + context payload | Event-driven trigger exists, but capability is not yet documented as strict notification-id contract for all flows | Partial |
| Mandatory vs preference gating | Mandatory bypass + optional preference suppression consistently enforced | Policy support exists for mandatory/preference categories, needs unified coverage confirmation across all notification types | Partial |
| Parameter enrichment model | Deterministic enrichment from trigger + backend + AI | Enrichment exists in parts; unified end-to-end capability contract is not yet explicitly standardized | Partial |
| Template parameter validation | Required parameter validation before merge and send | Validation exists but not yet represented as one unified capability contract with clear admin/runtime observability | Partial |
| Delivery and audit continuity | SES send + lifecycle and policy decision audit for all paths | Strong progress delivered in streamlined refactor, but unified requirements-level parity confirmation still needed | Partial |

### 13.2 In-Scope Gaps for Next Phase

- Define and approve the canonical admin capability to list notifications from registry perspective.
- Confirm the exact override boundary for persisted config associated with registry IDs.
- Standardize unified trigger/enrichment/validation capability contract across all email notification types.

### 13.3 Explicitly Out of Scope (Current Phase)

- Cadence/frequency policy modeling.
- Escalation policy modeling.
- Locale policy expansion beyond current behavior.

Recipient strategy remains candidate scope for next phase:

- `active_user`
- `tenant_owner`
- `both`
