# Unified Email Notification System - Design and Implementation Plan

Version: 0.2 (Draft)
Date: March 31, 2026
Status: Draft for Review

## 1. Purpose

Define the target architecture and phased implementation plan for a unified email notification system based on:

- code-first notification registry as source of truth
- deterministic template parameter enrichment
- consistent policy gate, rendering, delivery, and auditing

This design is based on:

- approved requirements in docs/shared/Requirements/unified-email-system-requirements.md
- current C# implementation behavior
- Python template-processor reference patterns from pp_ai

## 2. As-Is Capability Summary (Observed)

### 2.1 Notification Definitions

- Code registry exists in PurposePath.Domain/Constants/NotificationEvents.cs.
- Runtime also uses persisted notification event definitions via repository/table.
- Missing definition is bootstrapped from registry into persisted store during enqueue.

### 2.2 Trigger and Processing

- NotificationService enqueues notification requests and publishes async event.
- NotificationProcessor resolves event definition by event type, renders template, sends email, writes audit.

### 2.3 Policy and Preference Behavior

- Mandatory and preference category exist in code registry.
- Preference suppression is implemented in BillingNotificationService for billing flows.
- Policy behavior is not yet uniformly centralized for all notification families.

### 2.4 Template Resolution and Merge

- NotificationProcessor path: DB-first by category/name with file fallback renderer support.
- Direct SES service path: DB-first with break-glass inline fallback for certain account/auth templates.
- Parameter enrichment exists for email insight variables; broader generic enrichment contract is not yet explicit for all notifications.

### 2.5 Admin Capabilities

- Admin template CRUD/test/preview/analytics endpoints exist.
- No admin endpoint currently lists registry notifications with template mapping and template existence state.

## 3. Design Goals

1. Single source of truth for notification identities and contracts.
2. Keep admin template management practical without hidden IDs.
3. Standardize enrichment and validation behavior before render.
4. Preserve operational resilience and auditability.
5. Keep recipient strategy explicit and extensible.

## 4. Target Architecture

## 4.1 Notification Registry (Code-First)

Define a canonical registry entry per notification with:

- notification_id
- name
- description
- category
- template_id
- is_mandatory
- required_parameters
- optional_parameters
- preference_category (optional)
- recipient_strategy (new: active_user | tenant_owner | both)

Rules:

- registry is authoritative for notification identity and contract
- unknown notification_id cannot be processed
- runtime cannot create new notification definitions

## 4.2 Persisted Config Boundary

Persisted data can exist only as override state for existing registry IDs.

Allowed override classes:

- is_active
- reply_to behavior
- approved operational toggles

Disallowed:

- new notification IDs not in registry
- divergent parameter contract independent of registry

## 4.3 Unified Runtime Pipeline

1. Trigger layer calls unified enqueue with notification_id and payload.
2. Policy gate resolves registry entry and validates mandatory/optional preference behavior.
3. Recipient resolver computes destination(s) from recipient_strategy.
4. Template resolver gets template by registry template_id.
5. Template parameter processor computes final parameter set:
   - payload-provided values
   - backend enrichment
   - AI enrichment when required
6. Parameter validator enforces required merge parameters and required processing-only parameters.
7. Renderer merges template (Razor/Blazor).
8. Sender dispatches via SES.
9. Audit writer records request, decision, send outcome, and correlation metadata.

## 4.4 Template Parameter Processor Contract

Adopt Python-proven concepts:

- parse template placeholders to determine required runtime values
- resolve only parameters actually used by template
- group enrichment by retrieval method to minimize calls
- execute each retrieval method once, extract many values by extraction path
- apply defaults where valid
- return missing required list with structured warnings

C# target equivalent components:

- TemplateParameterProcessor
- ParameterRegistry (definition metadata)
- RetrievalMethodRegistry (grouped enrichment methods)
- ParameterExtractionResult (parameters, missing_required, warnings)

## 4.5 AI Insight Integration

AI insight remains a parameterized enrichment path, not a notification-definition source.

- Notification registry can indicate AI-dependent parameters.
- Enrichment coordinator calls AI service only when those parameters are needed.
- Existing fallback behavior is preserved: template-only send when insight unavailable/invalid.

## 4.6 Admin Experience Model

Admin UI becomes notification-first while preserving template CRUD.

Required read endpoint capability:

- list registry notifications with template mapping and template existence status

Admin actions:

- open notification
- edit existing mapped template
- create missing mapped template
- test/preview template

Admin cannot create new notification IDs.

## 5. Python Reference Mapping

Reference source: pp_ai coaching template processor pattern.

Boundary clarification:

- Python project (pp_ai) is the AI-side implementation and prompt orchestration runtime.
- This C# design is for backend email notification processing and delivery.

Patterns to carry over:

1. Registry-defined parameter metadata and retrieval methods.
2. Template-first parameter extraction (resolve only what template uses).
3. Retrieval grouping by method to reduce duplicate external calls.
4. Structured extraction result with missing_required and warnings.
5. Separation between endpoint-required parameters and registry parameter definitions.

Known differences to preserve:

- Python template processor produces rendered LLM prompts; C# pipeline produces rendered email content.
- Python enrichment obtains business context via API calls; C# enrichment should use application handlers/services directly (no internal loopback through HTTP APIs).
- Python does not perform AI enrichment as a downstream dependency; C# notification pipeline includes optional AI insight enrichment as part of email parameter resolution.
- C# email pipeline uses Razor/Blazor rendering, not Jinja.
- Notification dispatch policy and auditing in C# must remain first-class.

## 6. Implementation Plan (Phased)

## Phase 1 - Contract and Registry Consolidation

Deliverables:

- Canonical NotificationRegistry contract shape (including recipient_strategy)
- Explicit persisted override boundary documentation and guard rules
- Unified registry accessor abstraction used by enqueue path

Acceptance:

- unknown notification_id rejected early
- persisted records cannot introduce out-of-registry IDs

## Phase 2 - Notification Catalog API for Admin

Deliverables:

- Admin read endpoint to list all registry notifications with:
  - notification_id, name, description, category, template_id
  - template_exists
  - effective_active_state

Acceptance:

- admin can navigate notification-to-template maintenance without hidden IDs

## Phase 3 - Unified Policy Gate

Deliverables:

- Central policy gate used by all notification families
- Mandatory/preference behavior consistently applied across flows
- Recipient strategy resolution for active_user, tenant_owner, both

Acceptance:

- billing and non-billing flows use same policy contract
- recipient selection behavior is deterministic and tested

## Phase 4 - Generic Template Parameter Processor

Deliverables:

- C# TemplateParameterProcessor with registry + retrieval methods
- Template placeholder extraction and grouped enrichment
- Enrichment execution through internal application handlers/services (no internal HTTP loopback to local APIs)
- Required parameter validation with clear error outcomes

Acceptance:

- processor resolves payload + backend + AI parameters deterministically
- missing required parameters fail before render

## Phase 5 - Renderer and Sender Integration

Deliverables:

- Processor integrated into notification send pipeline before merge
- SES sender receives finalized rendered subject/body and delivery metadata
- Audit includes policy decision, parameter resolution status, and send result

Acceptance:

- end-to-end send path fully auditable
- fallback decisions preserved and explicit

## Phase 6 - Stabilization and Cutover

Deliverables:

- parity tests and regression suite
- deprecation of obsolete configuration paths not aligned with registry-first model
- runbook and rollback notes

Acceptance:

- pre-agreed validation checklist passes in dev/staging
- cutover readiness artifact updated

## 7. Test Strategy

1. Unit tests

- registry validation and contract enforcement
- policy gate rules
- parameter extraction and enrichment grouping
- recipient strategy selection

2. Integration tests

- enqueue to processor to renderer to sender path
- AI enrichment fallback behavior
- admin notification catalog endpoint

3. Contract tests

- admin endpoint response schema
- notification processing decision metadata consistency

## 8. Risks and Mitigations

1. Risk: policy divergence across old/new paths.
Mitigation: central policy gate with shared tests and route-level adoption checklist.

2. Risk: enrichment latency.
Mitigation: grouped retrieval methods, bounded timeouts, deterministic fallback behavior.

3. Risk: hidden coupling to persisted event definitions.
Mitigation: enforce registry ID validation and override boundary guards.

4. Risk: admin confusion during transition.
Mitigation: notification catalog endpoint and notification-first admin UX.

## 9. Scope Notes

In scope now:

- recipient_strategy support (active_user, tenant_owner, both)

Out of scope now:

- cadence/frequency modeling
- escalation modeling
- locale policy expansion

## 10. Next Step

After design approval, create an epic and child issues for each phase above, with acceptance criteria and validation evidence requirements per issue.

## 11. Atomic Requirements (EARS Format)

This section translates the unified-email requirements into atomic, testable statements.

### 11.1 Registry and Identity

- UES-001 (Ubiquitous): The system shall define notification identities and contracts in a single code registry.
- UES-002 (Unwanted behavior): If a notification_id is not present in the code registry, then the system shall reject the request before enqueue.
- UES-003 (Ubiquitous): The system shall not create new notification types from persisted runtime data.
- UES-004 (State-driven): While reading persisted notification configuration, the system shall only apply overrides for IDs that exist in the code registry.

### 11.2 Trigger, Policy, and Recipient

- UES-005 (Event-driven): When a caller requests notification dispatch, the system shall require notification_id and runtime context payload.
- UES-006 (State-driven): While a notification is marked mandatory, the system shall bypass optional preference suppression.
- UES-007 (State-driven): While a notification is not mandatory, the system shall evaluate user preference category before enqueue/send.
- UES-008 (Ubiquitous): The system shall resolve recipients based on registry-defined recipient_strategy values (active_user, tenant_owner, both).

### 11.3 Template and Enrichment

- UES-009 (Ubiquitous): The system shall resolve template_id from the notification registry definition.
- UES-010 (Ubiquitous): The system shall extract template placeholders and resolve only parameters required by the template.
- UES-011 (Ubiquitous): The system shall resolve parameters from payload, backend enrichment, and AI enrichment where configured.
- UES-012 (Ubiquitous): The system shall execute backend enrichment via internal application handlers/services, not local HTTP API loopback.
- UES-013 (Unwanted behavior): If required merge parameters are unresolved, then the system shall fail before template rendering.
- UES-014 (Ubiquitous): The system shall render final content using the backend Razor/Blazor email merge engine.

### 11.4 AI Insight

- UES-015 (Event-driven): When a template requires AI insight parameters, the system shall invoke AI enrichment as a parameter source.
- UES-016 (Ubiquitous): The system shall treat AI insight as enrichment input and not as a separate notification-definition source.
- UES-017 (Unwanted behavior): If AI enrichment fails or returns unusable insight, then the system shall execute deterministic fallback behavior and continue according to notification policy.

### 11.5 Delivery, Audit, and Admin

- UES-018 (Ubiquitous): The system shall send email through AWS SES.
- UES-019 (Ubiquitous): The system shall persist audit/telemetry records for policy decision and send outcome.
- UES-020 (Ubiquitous): The system shall preserve correlation metadata across trigger, processing, and delivery.
- UES-021 (Ubiquitous): The system shall provide an admin read endpoint listing registry notifications with template mapping and template existence state.
- UES-022 (Ubiquitous): The system shall allow admin template maintenance without allowing runtime creation of new notification IDs.

## 12. Requirements-to-Plan Traceability

This matrix maps atomic requirements to implementation phases.

| Requirement IDs | Planned Phase(s) |
|---|---|
| UES-001, UES-002, UES-003, UES-004 | Phase 1 |
| UES-021, UES-022 | Phase 2 |
| UES-005, UES-006, UES-007, UES-008 | Phase 3 |
| UES-009, UES-010, UES-011, UES-012, UES-013, UES-015, UES-016, UES-017 | Phase 4 |
| UES-014, UES-018, UES-019, UES-020 | Phase 5 |
| All UES requirements (verification and hardening) | Phase 6 |

## 13. Requirement Verification Approach

For each UES requirement, implementation issues must include:

- explicit acceptance criteria referencing the UES IDs
- test evidence mapped to each UES ID
- any approved deviations documented with rationale and follow-up action
