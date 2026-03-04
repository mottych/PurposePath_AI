# Measure Integration - Requirements Document

**Version:** 1.0  
**Last Updated:** February 17, 2026  
**Status:** Draft for Validation  
**Ownership Model:** Shared between PurposePath backend project and AI backend project  
**Primary Scope:** Contract and architecture requirements for AI-driven SQL template generation and measure integration lifecycle

---

## Table of Contents

1. [Intent and Objectives](#1-intent-and-objectives)
2. [Scope](#2-scope)
3. [Source Artifacts and Traceability](#3-source-artifacts-and-traceability)
4. [Architecture Requirements](#4-architecture-requirements)
5. [Contract Requirements (AI ↔ Integration)](#5-contract-requirements-ai--integration)
6. [Functional Requirements](#6-functional-requirements)
7. [Security Requirements](#7-security-requirements)
8. [Performance and Reliability Requirements](#8-performance-and-reliability-requirements)
9. [Cost Estimate](#9-cost-estimate)
10. [Completion and Validation Checklist](#10-completion-and-validation-checklist)
11. [Shared Delivery Governance](#11-shared-delivery-governance)

---

## 1. Intent and Objectives

### 1.1 Intent
Establish a clear, testable, and contract-first integration model between PurposePath and AI services for SQL template generation, measure data retrieval orchestration, and deterministic publication of measure outcomes.

### 1.2 Objectives
1. Define a stable, versioned event contract between systems.
2. Ensure deterministic and idempotent processing from generation request to terminal outcome.
3. Separate business intent, system constraints, and runtime lifecycle responsibilities.
4. Improve reliability, observability, and governance without coupling to implementation details.
5. Provide measurable completion criteria aligned with epic and issue scope.

---

## 2. Scope

### 2.1 In Scope
- Contract requirements for EventBridge events used for SQL template generation.
- Requirements for intent resolution hierarchy and parameter semantics.
- Requirements for idempotency, terminal outcome guarantees, and replay safety.
- Security, performance, and operational design constraints.
- Cost model and expected cost controls.

### 2.2 Out of Scope
- Internal code structure, class design, and framework-specific implementation.
- Infrastructure-as-code templates or deployment runbooks.
- UI behavior details.
- Non-integration AI topics unrelated to SQL template generation.

---

## 3. Source Artifacts and Traceability

This requirements document consolidates scope and decisions from the following planning artifacts:

- Epic #665: Measure integration refactor epic
- Issue #666: Architecture and contract baseline
- Issue #667: Schema and data model changes
- Issue #668: Connection model and provider-facing metadata alignment
- Issue #669: Payload and event contract implementation scope
- Issue #670: Worker/orchestration behavior and idempotency
- Issue #671: API/EventBridge specification alignment
- Issue #672: Legacy cleanup and deprecation scope
- Issue #673: Validation, rollout, and completion criteria

> Requirement IDs in this document map to one or more of these issues for completion tracking.

This document is also a shared contract artifact for the AI backend project. The AI project may track equivalent scope with separate issue IDs in a different repository.

**Traceability rule:** requirement completion is considered final only when linked backend-side and AI-side tracking artifacts are both marked complete.

---

## 4. Architecture Requirements

### 4.1 Architectural Principles
**AR-001** Contract-first design: all cross-system interactions must be defined by versioned contracts prior to release.

**AR-002** Separation of concerns:
- business intent definition
- system-specific constraints
- runtime lifecycle and state
must remain logically distinct.

**AR-003** Deterministic processing: identical inputs and definition versions must produce reproducible contract outcomes.

**AR-004** Backward-compatible evolution: contract changes must be versioned and non-breaking by default.

### 4.2 Logical Architecture Boundaries
**AR-010** The integration domain must expose a dedicated contract surface for SQL template generation events.

**AR-011** AI systems must consume request events and emit exactly one terminal event per generation cycle.

**AR-012** Runtime state and terminal outcome identity must be keyed by a stable generation identity.

**AR-013** Solution design must conform to `.github/DEVELOPMENT_GUIDELINES.md` architectural boundaries:
- controllers remain boundary-only and delegate via MediatR
- domain layer remains pure and free of infrastructure concerns
- contracts/interfaces required by domain are defined in domain-facing boundaries
- cross-layer dependencies must follow Clean Architecture direction

**AR-014** Any architecture deviation from `.github/DEVELOPMENT_GUIDELINES.md` must be explicitly documented, risk-assessed, and approved before release.

### 4.3 Intent and Parameter Architecture
**AR-020** Intent precedence must be:
1. measure-level override intent (when present)
2. catalog-level canonical intent

**AR-021** System-level configuration defines allowed parameter schema and constraints, not business intent text.

**AR-022** Runtime integration state owns lifecycle metadata (definition version/hash, regeneration state, generation outcomes).

---

## 5. Contract Requirements (AI ↔ Integration)

### 5.1 Contract Version and Event Set
**CR-001** Contract version 1.2 is the baseline for inter-system event exchange in scope.

**CR-002** Required event types:
- integration.sql.template.generate.requested
- integration.sql.template.generate.completed
- integration.sql.template.generate.failed

### 5.2 Envelope and Identity
**CR-010** Every event must contain the standard EventBridge envelope fields.

**CR-011** Every event detail must include a common identity block containing event version, provider, correlation identity, generation identity, tenant identity, integration identity, idempotency key, and canonical definition version/hash.

**CR-012** Definition identity must exist in a single canonical location in the payload.

### 5.3 Requested Event Requirements
**CR-020** Requested events must provide:
- resolved intent template and period-window strategy
- source/system connection context needed for contract execution
- allowed parameter schema and selected parameter values
- regeneration flag
- SQL policy constraints, including required placeholder style and max rows semantics

**CR-021** The contract must define max rows as final result-set row count.

### 5.4 Completed Event Requirements
**CR-030** Completed events must provide:
- success status
- parameterized SQL template
- template hash
- binding schema
- explicit applied parameters list
- explicit ignored parameters list with enum reason
- validation outcome data
- generation timing metadata

**CR-031** Completed events must include provider and traceability connection fields for downstream diagnostics.

### 5.5 Failed Event Requirements
**CR-040** Failed events must provide:
- failed status
- stable error code and error stage enums
- retryability flag
- sanitized failure message
- attempt and duration fields

**CR-041** Failed events must support optional retry-after, provider error code, and structured validation failures.

### 5.6 Enum Governance
**CR-050** Error codes, error stages, ignored parameter reasons, and validation failure codes must be governed by canonical enums.

**CR-051** Enum changes require versioned contract governance and compatibility review.

### 5.7 Compatibility Rules
**CR-060** Terminal events must return the same definition version/hash from the requested event.

**CR-061** Runtime binding expectations (if present) must be compatible with emitted parameter binding schema.

**CR-062** SQL placeholder style in emitted template must match policy-defined style.

---

## 6. Functional Requirements

### 6.1 Lifecycle and Regeneration
**FR-001** The system must initiate SQL template generation when structural query-shaping changes are detected.

**FR-002** Value-only parameter changes must not require template regeneration by default.

**FR-003** Regeneration state must be explicit in request contract.

### 6.2 Idempotency and Terminal Behavior
**FR-010** At most one terminal event may exist for a generation identity.

**FR-011** Exactly one terminal outcome (completed or failed) must be produced per generation identity.

**FR-012** Duplicate or replayed terminal events must be safely recognized and handled without data corruption.

### 6.3 Validation and Policy Enforcement
**FR-020** Completion is valid only when policy and validation checks pass.

**FR-021** SQL templates must remain parameterized and must not interpolate user-provided values.

**FR-022** Forbidden operation policy must be enforced before successful terminal publication.

### 6.4 Traceability and Auditability
**FR-030** Contract events must support end-to-end correlation via correlation and generation identities.

**FR-031** Contract events must include sufficient context for post-incident diagnosis without requiring implementation-specific logs.

---

## 7. Security Requirements

### 7.1 Data Protection
**SR-001** Event payloads and logs must not expose credentials, secrets, or raw sensitive tokens.

**SR-002** Failure diagnostics must include only sanitized fields approved for cross-system transport.

### 7.2 Access and Trust Boundaries
**SR-010** Producer and consumer trust boundaries must be explicit and validated through contract version controls.

**SR-011** Event sources and detail types must be constrained to authorized producer identities.

**SR-012** Tenant isolation is mandatory: every contract event and lifecycle transition must be scoped and validated by tenant identity so cross-tenant access, processing, or publication cannot occur.

**SR-013** Tenant identity used for processing must be consistent across request and terminal events; identity mismatch must result in rejection.

### 7.3 Integrity and Non-Repudiation
**SR-020** Definition hash and template hash must be used for integrity checks across systems.

**SR-021** Terminal event acceptance must verify identity consistency with originating request.

---

## 8. Performance and Reliability Requirements

### 8.1 Performance Targets
**PR-001** Generation workflows should complete within an operational target window appropriate for asynchronous orchestration (target: low-seconds to low-minutes under nominal load).

**PR-002** Contract validation overhead should remain small relative to total generation latency.

### 8.2 Reliability Targets
**PR-010** Terminal event delivery reliability target: 99.9%+ successful terminal publication under normal operating conditions.

**PR-011** Transient failure handling must support bounded retries with explicit retryability semantics.

**PR-012** Non-retryable failures must fail fast with stable error taxonomy.

### 8.3 Observability Requirements
**PR-020** Metrics and logs must support tracking for:
- generation throughput
- success/failure rates
- retry rates
- terminal latency distribution
- contract validation failures

**PR-021** Observability signals must be keyed by generation and correlation identity.

---

## 9. Cost Estimate

### 9.1 Estimation Approach
This estimate is a planning-level range based on expected event volume, AI generation frequency, and validation overhead. It is not a billing commitment.

### 9.2 Cost Drivers
1. Event traffic volume (request + terminal events)
2. AI generation and validation calls per generation cycle
3. Retry frequency on transient failures
4. Storage and retention for lifecycle metadata and audit traces
5. Observability ingestion and retention

### 9.3 Relative Cost Profile (Planning)
- **Low volume rollout:** low operational cost profile
- **Moderate scale rollout:** moderate profile driven mostly by AI generation invocations
- **High scale rollout:** AI + observability become primary contributors; retry discipline materially affects cost

### 9.4 Cost Control Requirements
**CO-001** Regeneration must only occur when required by structural changes.

**CO-002** Retry policy must differentiate transient from permanent failures to prevent waste.

**CO-003** Event payloads should include only contract-required fields to control transport and storage overhead.

**CO-004** Retention windows for diagnostics and traces must be policy-driven and periodically reviewed.

### 9.5 Baseline Monthly Planning Range (for validation, non-binding)
Assumptions:
- 10k to 100k generation cycles per month
- 2-3 events per cycle
- low retry rate under healthy operation

Planning range:
- **Lower bound:** hundreds of USD/month
- **Mid range:** low thousands USD/month
- **Upper planning bound:** several thousands USD/month at higher volume/observability settings

> Final budget should be re-estimated after pilot telemetry is collected.

---

## 10. Completion and Validation Checklist

Use this section to validate delivery against requirements and epic/issue scope.

### 10.1 Contract Completion
- [ ] V1.2 event set published and approved
- [ ] Canonical identity and definition fields verified across all events
- [ ] Enum governance accepted and documented
- [ ] Payload compatibility rules validated

### 10.2 Security Completion
- [ ] No secrets in event payloads/logs
- [ ] Sanitized diagnostics policy verified
- [ ] Source and event-type authorization constraints validated
- [ ] Tenant isolation controls validated (including mismatch rejection scenarios)

### 10.2.1 Architecture Compliance Completion
- [ ] Design review confirms conformance to `.github/DEVELOPMENT_GUIDELINES.md`
- [ ] Layer-boundary checklist completed (controller/application/domain/infrastructure responsibilities)
- [ ] No unapproved architecture deviations remain open

### 10.3 Reliability Completion
- [ ] Exactly-one-terminal guarantee validated
- [ ] Idempotency behavior validated under replay
- [ ] Retry behavior validated against transient/non-transient classes

### 10.4 Performance Completion
- [ ] End-to-end latency benchmarked
- [ ] Throughput and error-rate SLOs measured
- [ ] Validation overhead assessed and acceptable

### 10.5 Cost Completion
- [ ] Pilot telemetry collected for actual event and AI volume
- [ ] Monthly run-rate estimate updated from real data
- [ ] Cost controls verified (regeneration gating, retry discipline, retention policy)

### 10.6 Cross-Project Completion
- [ ] PurposePath issue mapping is complete and current
- [ ] AI project issue mapping is complete and current
- [ ] Contract version agreement is explicit in both projects
- [ ] No requirement marked done unless both project issue tracks are complete

---

## 11. Shared Delivery Governance

### 11.1 Governance Requirements
**GD-001** Every requirement in this document must map to both:
- one or more PurposePath project issues
- one or more AI project issues

**GD-002** Contract versions must remain synchronized across both projects before release.

**GD-003** Contract-breaking changes require explicit approval in both project tracks.

**GD-004** Completion status must be evaluated using the stricter state:
- if either project shows incomplete, requirement remains incomplete.

### 11.2 Change-Control Requirements
**GD-010** Any payload field addition/removal or enum change must be recorded as a versioned contract change request.

**GD-011** Cross-project traceability tables must be updated in the same review cycle as contract changes.

**GD-012** Contract examples and requirements text must remain semantically consistent across shared docs.

---

## Appendix A - Requirement-to-Issue Mapping

| Requirement Area | Primary Issues |
|---|---|
| Contract baseline and semantics | #666, #669, #671 |
| Schema and model alignment | #667, #668 |
| Orchestration behavior and idempotency | #670 |
| Cleanup/deprecation | #672 |
| Validation and rollout | #673 |
| Program-level tracking | #665 |

---

## Appendix B - Requirement IDs Summary

- Architecture: AR-001..AR-022
- Contract: CR-001..CR-062
- Functional: FR-001..FR-031
- Security: SR-001..SR-021
- Performance/Reliability: PR-001..PR-021
- Cost: CO-001..CO-004

---

## Appendix C - Cross-Project Issue Mapping (Template)

| Requirement Area | PurposePath Issues | AI Project Issues |
|---|---|---|
| Contract baseline and semantics | #666, #669, #671 | PurposePath_AI #243 |
| Schema and model alignment | #667, #668 | PurposePath_AI #243 |
| Orchestration behavior and idempotency | #670 | PurposePath_AI #243 |
| Cleanup/deprecation | #672 | PurposePath_AI #243 |
| Validation and rollout | #673 | PurposePath_AI #243 |
| Program-level tracking | #665 | PurposePath_AI #243 |

> Current AI-side tracking anchor is `PurposePath_AI #243`. If the AI team splits work into child issues, replace each row with the specific child issue IDs.
