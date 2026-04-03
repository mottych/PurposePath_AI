# Unified Email System - Epic and Child Issue Templates

Use these templates to create one epic and six implementation issues with direct traceability to UES requirements in:

- docs/shared/design/unified-email-system-design.md

## Epic Template

Title:

Epic: Unified Email Notification System - Registry-First Pipeline and Traceable Delivery

Body:

## Objective
Implement the unified email notification architecture with code-first notification registry, deterministic enrichment and rendering, centralized policy gating, and auditable SES delivery.

## Scope
- Registry-first notification identity and contract enforcement
- Admin notification catalog visibility for template maintenance
- Centralized policy and recipient strategy handling
- Generic template parameter processor with backend + AI enrichment
- Integrated render/send/audit pipeline
- Stabilization and cutover verification

## Out of Scope
- Cadence/frequency modeling
- Escalation modeling
- Locale policy expansion

## Requirement Baseline (Atomic IDs)
- UES-001..UES-022 (see design traceability matrix)

## Child Issues
- Phase 1: Contract and Registry Consolidation
- Phase 2: Notification Catalog API for Admin
- Phase 3: Unified Policy Gate
- Phase 4: Generic Template Parameter Processor
- Phase 5: Renderer and Sender Integration
- Phase 6: Stabilization and Cutover

## Success Criteria
- All child issues complete with mapped UES acceptance criteria and test evidence
- End-to-end notification flow validated against registry-first requirements
- Cutover readiness evidence updated and approved

## Working Rules
- Every child issue must reference implemented UES IDs
- Every child issue must include validation evidence
- No child issue may introduce runtime creation of notification IDs

---

## Child Issue 1 - Phase 1

Title:

Unified Email Phase 1: Contract and Registry Consolidation

Body:

## Goal
Consolidate notification contract authority around code registry and enforce ID validity/override boundaries.

## Requirement IDs
- UES-001
- UES-002
- UES-003
- UES-004

## Deliverables
- Canonical notification registry contract model finalized
- Runtime guardrails for unknown notification_id
- Persisted override boundary rules enforced for registry-known IDs only
- Documentation update for effective config resolution rules

## Acceptance Criteria
- Unknown notification_id is rejected before enqueue
- Persisted config cannot define out-of-registry IDs
- Effective notification configuration resolution is deterministic and documented

## Validation Evidence Required
- Unit tests for registry ID validation
- Unit/integration tests for override boundary enforcement
- Contract notes documenting no API breakage unless explicitly approved

## Dependencies
- None (foundational)

---

## Child Issue 2 - Phase 2

Title:

Unified Email Phase 2: Admin Notification Catalog Endpoint

Body:

## Goal
Expose a read endpoint for admin UI to list all registry notifications with template mapping and existence state.

## Requirement IDs
- UES-021
- UES-022

## Deliverables
- Admin endpoint returning notification catalog from registry perspective (`GET /notifications/catalog` — see `docs/shared/Specifications/api-admin/admin-api-specification.md` v2.4)
- Response includes: notification_id, name, description, category, template_id, template_exists, effective_active_state
- API documentation and response schema examples

## Acceptance Criteria
- Admin can view notification catalog without knowing hidden template IDs
- Endpoint output reflects registry-defined notifications and current template existence state

## Validation Evidence Required
- Endpoint contract tests
- Integration test showing catalog and template existence mapping
- Documentation update in shared specs

## Dependencies
- Phase 1 completed

---

## Child Issue 3 - Phase 3

Title:

Unified Email Phase 3: Central Policy Gate and Recipient Strategy

Body:

## Goal
Centralize mandatory/preference behavior and implement recipient strategy (active_user, tenant_owner, both).

## Requirement IDs
- UES-005
- UES-006
- UES-007
- UES-008

## Deliverables
- Shared policy gate used across notification families
- Recipient strategy resolution integrated with dispatch
- Policy decision outcomes structured for downstream audit

## Acceptance Criteria
- Mandatory notifications bypass optional preference suppression
- Non-mandatory notifications honor preference category checks
- Recipient strategy resolves deterministic recipient set

## Validation Evidence Required
- Unit tests for policy gate rules
- Integration tests for recipient strategy behavior
- Regression checks across billing and non-billing flows

## Dependencies
- Phase 1 completed

---

## Child Issue 4 - Phase 4

Title:

Unified Email Phase 4: Generic Template Parameter Processor

Body:

## Goal
Introduce generic parameter processor for payload/backend/AI enrichment with strict required-parameter validation.

## Requirement IDs
- UES-009
- UES-010
- UES-011
- UES-012
- UES-013
- UES-015
- UES-016
- UES-017

## Deliverables
- Template placeholder extraction and parameter requirement resolution
- Retrieval method grouping for efficient enrichment execution
- Internal enrichment through application handlers/services only (no internal HTTP loopback)
- Deterministic missing-required behavior before rendering
- AI insight parameter enrichment path integration with fallback behavior

## Acceptance Criteria
- Only template-used parameters are enriched
- Required parameters unresolved -> fail before render
- Backend enrichment uses internal service/handler calls
- AI insight fallback/degradation behavior remains deterministic and auditable

## Validation Evidence Required
- Unit tests for extraction/grouping/validation
- Integration tests for payload + backend + AI enrichment mix
- Failure-path tests for missing required parameters and AI fallback

## Dependencies
- Phase 1 completed
- Phase 3 recommended

---

## Child Issue 5 - Phase 5

Title:

Unified Email Phase 5: Render, Send, and Audit Integration

Body:

## Goal
Integrate processor output into render/send pipeline and finalize end-to-end audit consistency.

## Requirement IDs
- UES-014
- UES-018
- UES-019
- UES-020

## Deliverables
- End-to-end pipeline wiring: policy -> enrichment -> render -> SES send -> audit
- Structured decision metadata persisted with send outcomes
- Correlation propagation verified across pipeline stages

## Acceptance Criteria
- Rendered content produced by backend Razor/Blazor merge engine
- SES send executes with expected delivery metadata
- Audit records include decision and outcome details with correlation continuity

## Validation Evidence Required
- Integration tests for full processing path
- Audit persistence assertions
- Regression tests for fallback decisions

## Dependencies
- Phase 3 completed
- Phase 4 completed

---

## Child Issue 6 - Phase 6

Title:

Unified Email Phase 6: Stabilization, Regression, and Cutover Readiness

Body:

## Goal
Harden, validate, and prepare cutover with full traceability evidence.

## Requirement IDs
- All UES IDs (verification and hardening)

## Deliverables
- Full regression validation suite execution
- Cutover readiness artifact updates
- Deprecated/obsolete path retirement plan and rollback notes

## Acceptance Criteria
- All UES IDs mapped to passing tests or documented approved exceptions
- Dev/staging readiness evidence complete and reviewable
- Cutover package approved for execution planning

## Validation Evidence Required
- Build/test results
- Requirement-to-test mapping table
- Updated cutover readiness artifact and docs links

## Dependencies
- Phases 1-5 completed

---

## Per-Issue Checklist (Copy into each issue)

- [ ] Requirement IDs listed and complete
- [ ] Deliverables aligned to listed requirement IDs
- [ ] Acceptance criteria are testable
- [ ] Validation evidence section completed
- [ ] API/doc updates included where relevant
- [ ] No out-of-scope behavior introduced
