# Notification Email Processing - Design and Implementation Plan

Version: 1.1
Date: April 8, 2026
Status: Design Baseline

## 1. Design Goals

- One canonical processing pipeline for all notification emails.
- Clear component boundaries with single responsibility.
- Registry-first dynamic behavior (notification and parameter contracts).
- Resolver-method abstraction so AI and DB resolvers are interchangeable to orchestration.
- Clean code target: remove stale/deprecated/backward-compat paths once cutover is complete.

## 2. Component Model

### 2.1 Notification Event Processor

Function:
Orchestrates end-to-end lifecycle for a notification request.

Responsibilities:
- load notification contract
- validate publisher input contract
- coordinate template resolution
- coordinate merge
- invoke send and audit
- emit lifecycle telemetry

Non-responsibilities:
- no parameter-specific retrieval logic
- no template rendering logic
- no provider-specific delivery logic

### 2.2 Notification Registry

Function:
Defines notification-level contract and behavior.

Responsibilities:
- notification identity and metadata
- canonical publisher parameters (typed NotificationEventParameter)
- canonical template parameters (typed NotificationEventParameter)
- delivery/policy metadata required at notification level

Non-responsibilities:
- no resolver implementation
- no parameter extraction behavior

Current implementation notes:
- Notification contracts are defined as NotificationEvent records in PurposePath.Domain/Constants/NotificationEvent.cs.
- NotificationEvents.GetAll() returns canonicalized contracts from static definitions through EnsureSplitContract.
- EnsureSplitContract derives required publisher inputs from template-parameter resolution method requirements.

### 2.3 Parameter Registry

Function:
Defines parameter-level contract.

Responsibilities:
- parameter name
- resolver method binding (NotificationResolutionMethod)

Non-responsibilities:
- no notification-specific mandatory/optional assignment
- no resolver execution
- no method input requirement definitions

Current implementation notes:
- Canonical parameter definitions live in PurposePath.Domain/Constants/NotificationParameters.cs as NotificationParameter objects.
- NotificationParameters.All is the canonical source and is projected into runtime TemplateParameterRegistry.

### 2.4 Resolver Methods Registry

Function:
Catalogs and executes resolver methods.

Responsibilities:
- resolver method metadata (method key + required input parameters)
- grouped resolver invocation orchestration support
- normalized resolver output contract
- method-level failure classification for fallback decisions

Resolver categories:
- internal data resolvers (application/domain repository access)
- AI enrichment resolver (existing email insight payload pipeline)

Current baseline method keys:
- payload_passthrough
- business_foundation_by_tenant
- goal_by_id
- subscription_by_tenant
- email_insight_payload

`email_insight_payload` required method inputs:
- tenantId
- userId
- topicId (business topic reference)

AI orchestration metadata and envelope generation are handled by an intermediate AI orchestration service that receives business inputs + resolved AI topic id, calls AI execution, waits for completion, and returns normalized LLM payload for template-variable mapping.

Mapping policy:
 - Contract normalization is applied once into a canonical in-memory catalog of ensured split contracts, and both `GetAll` and `GetByEventType` query that same catalog.
 - Runtime split-contract accessors and catalog normalization are strict (no compatibility fallback).
 - Static notification definitions must declare split contract fields at source, and normalization consumes those split fields directly.
 - Parameter-to-method bindings are owned by canonical parameter registry; method input requirements are owned by canonical resolution methods registry.
 - Lambda runtime registries (TemplateParameterRegistry and TemplateRetrievalMethodRegistry) must remain aligned with canonical domain registries.
 - Non-passthrough method keys must have concrete runtime resolver implementations.

Current reusable retrieval sources:
- business_foundation_by_tenant -> IBusinessFoundationRepository
- goal_by_id -> IGoalRepository
- subscription_by_tenant -> ISubscriptionRepository + ISubscriptionTierRepository
- email_insight_payload -> EmailInsightPayloadPipeline
- email_insight_payload orchestration -> EmailInsightOrchestrator

Non-responsibilities:
- no template rendering or send operations
- no notification-level contract definition

### 2.5 Template Resolver

Function:
Builds the final render-parameter set from template usage and contracts.

Responsibilities:
- parse template placeholders
- validate mandatory template contract presence
- identify missing used parameters
- group by resolver method
- execute grouped resolvers
- map outputs using parameter key binding
- return resolved parameters plus warnings/missing-required details

Non-responsibilities:
- no rendering
- no delivery

### 2.6 Template Merge

Function:
Render final subject/body from template and parameters.

Responsibilities:
- run existing Razor merge process
- produce final render output contract

Non-responsibilities:
- no data retrieval
- no send logic

### 2.7 Send and Audit

Function:
Deliver email and persist outcome evidence.

Responsibilities:
- send through configured provider (SES)
- persist audit with policy/decision metadata
- preserve correlation and idempotency trace

Non-responsibilities:
- no parameter resolution
- no rendering

## 3. End-to-End Sequence (New Components)

1. publisher submits notification id and payload
2. notification event processor loads notification registry entry
3. processor validates required publisher input
4. processor loads selected template
5. processor calls template resolver
6. template resolver extracts placeholders and validates mandatory template parameter contract
7. template resolver computes unresolved used parameters
8. template resolver groups unresolved parameters by resolver method
9. resolver methods registry provides method input requirements and executes grouped methods
10. template resolver maps method outputs to parameters and returns final parameter set
11. processor calls template merge to render final subject/body
12. processor calls send and audit to deliver and record outcomes
13. processor emits completion telemetry and returns terminal status

## 4. AI Integration Design

AI is implemented as a resolver method.

Rules:
- template resolver does not branch on AI specifics
- AI resolver encapsulates AI request/response handling
- existing backend AI event bridge contract handling is reused
- resolver returns values in common parameter-resolution output shape

This keeps AI as a plug-in enrichment mechanism, not a special-case pipeline.

## 5. Error Handling and Fault Tolerance

- mandatory contract failures: hard fail with explicit reason
- optional enrichment failures: warning + controlled fallback
- resolver-level timeout/retry/circuit protection
- deterministic final outcome states
- idempotent handling on duplicate request keys

## 6. Observability Design

Required telemetry domains:
- contract validation outcomes
- template resolution outcomes
- resolver method latency/success/failure
- merge success/failure
- send outcome and provider id
- audit persistence outcome

Required dimensions:
- notification id
- request id
- correlation id
- resolver method name
- decision/fallback reason code

## 7. Implementation Plan

### Phase 1: Canonical Contracts
- finalize notification registry schema
- finalize parameter registry schema
- finalize retrieval method registry schema (method key + required inputs)
- validate all existing notifications against new schemas

Implementation status note:
- Canonical object-based contracts are in place (NotificationEvent, NotificationParameter, NotificationResolutionMethod).
- Topic onboarding must now update domain registries first; runtime registries are projection/alignment layers.

### Phase 2: Registry Infrastructure
- implement registry access and startup validation
- enforce unknown-notification hard rejection
- enforce parameter-definition integrity checks
- enforce method-definition integrity checks
- enforce notification required publisher inputs include method-derived required inputs

### Phase 3: Template Resolver Engine
- implement placeholder extraction and mandatory checks
- implement missing-parameter detection
- implement grouped resolver execution
- implement extraction-path mapping and defaults

### Phase 4: Resolver Method Implementations
- implement DB/application resolvers using handlers/services directly
- implement AI resolver adapter over existing AI interaction path
- implement resolver-level resilience policies

### Phase 5: Pipeline Integration
- wire processor -> template resolver -> merge -> send/audit
- remove obsolete branching paths
- keep one canonical orchestration path

### Phase 6: Robustness and Observability
- add full structured telemetry and metrics
- add fault-injection tests for fallback and retry behavior
- validate deterministic outcomes under failure scenarios

### Phase 7: Cleanup and Cutover
- remove deprecated/backward-compat code paths
- remove stale contracts and unreachable logic
- update documentation references to canonical docs only

### Phase 8: Verification and Deployment
- run full test suite (unit + integration + targeted scenario tests)
- execute goal insight email scenario as representative AI test case
- deploy per environment gates with rollback readiness

## 8. Test Strategy (Minimum)

- contract tests for notification and parameter registries
- contract tests for retrieval method registry
- contract tests for notification required-input coverage vs. method-derived requirements
- contract tests that enrichment parameters are not mapped to payload_passthrough
- contract tests that payload_passthrough usage in notification template contracts is whitelist-governed
- contract tests that all non-passthrough method keys have concrete resolver implementations
- contract tests that notification catalog definitions expose explicit split contracts without fallback
- template resolver tests for grouping, mapping, missing-required behavior
- resolver tests for DB and AI methods
- integration tests for full processing with and without AI enrichment
- end-to-end scenario test for goal insight email

## 9. Clean Code Target-State Rules

- one pipeline, no duplicated legacy flows
- no backward-compat compatibility switches after cutover
- no stale/deprecated components left in active path
- registry-first extensibility for all future notifications

## 10. Delivery Artifacts

- canonical requirements document
- canonical design/plan document
- implementation issue(s) with phased task mapping
- dedicated test/review issue for goal insight scenario
