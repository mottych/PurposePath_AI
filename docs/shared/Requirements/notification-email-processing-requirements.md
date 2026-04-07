# Notification Email Processing - Requirements (Stakeholder Ready)

Version: 1.0
Date: April 7, 2026
Status: Approved Requirements Baseline

## 1. Purpose

PurposePath needs one consistent way to generate, enrich, render, send, and audit all system emails.
This requirements document defines the end-to-end operating model in plain language.

The model supports:
- regular notification emails
- AI-enriched notification emails
- consistent behavior across domains (billing, strategy, engagement, and future domains)

This document is requirements-only. It does not prescribe implementation classes or code structure.

## 2. Business Outcome

The system must provide a reliable email engine that is:
- dynamic: new notifications can be added without custom processing code per topic
- flexible: supports both non-AI and AI-enriched messages
- robust: fault tolerant with deterministic behavior
- observable: clear lifecycle and outcome visibility
- auditable: complete send and decision traceability

## 3. Core Operating Model

### 3.1 Publisher Request

A caller requests an email by sending:
- notification identifier
- payload with required input values for that notification

Example:
- notification: late payment
- required input values: tenant id, plan id

### 3.2 Notification Registry

The notification registry is the source of truth for notification-level contracts.
For each notification, it defines:
- notification identity and metadata
- required publisher input values
- template parameters allowed for this notification
- mandatory template parameters
- optional template parameters

### 3.3 Parameter Registry

Every template parameter must be defined in a parameter registry.
For each parameter, the registry defines:
- parameter name
- resolver method key used to fetch/build value

Multiple parameters may share one resolver method.
One resolver method may return a structured object that satisfies several parameters.

### 3.4 Retrieval Method Registry

Resolver methods are defined in a dedicated retrieval method registry.
For each retrieval method, the registry defines:
- method key
- required input parameters for invoking that method

Method input requirements must be defined once at method level, not duplicated for each parameter bound to that method.

Current baseline method catalog:
- payload_passthrough: value must be present in publisher payload
- business_foundation_by_tenant: value resolved from business foundation by tenantId
- goal_by_id: value resolved from goal repository by tenantId and topicId
- subscription_by_tenant: value resolved from subscription and tier repositories by tenantId
- email_insight_payload: value resolved from email insight payload pipeline

For `email_insight_payload`, required method inputs are business-context inputs only:
- tenantId
- userId
- topicId (business topic reference, for example goalId/issueId depending on AI topic adapter)

AI orchestration envelope metadata (eventId/correlationId/idempotency/retry/schema/source/locale/timezone/activityData/topic routing/auth envelope) is generated and managed inside the AI orchestration layer, not by parameter registry contracts.

Current enrichment mapping baseline:
- business_name -> business_foundation_by_tenant
- goal_title, goal_intent, goal_created_date -> goal_by_id
- plan_name, billing_frequency, amount, currency, next_billing_date -> subscription_by_tenant
- insight_enabled, insight_title, insight_summary, insight_html, insight_text, insight_cta_label, insight_cta_url, insight_confidence_label -> email_insight_payload

All other registered notification parameters default to payload_passthrough unless explicitly mapped to an enrichment method.
Payload passthrough usage for notification template parameters must be governed by an explicit test whitelist.

### 3.5 Notification Contract Rule

Notification entries must explicitly declare required publisher inputs.
Those required publisher inputs must include all required method inputs derived from the notification's template parameter set.

The derivation rule is:
- collect all required and optional template parameters for the notification
- map each parameter to a retrieval method through parameter registry
- union required method inputs from retrieval method registry
- ensure notification required publisher inputs include that union

Implementation governance rule:
- maintain a declarative parameter-to-required-input mapping table in notification registry code
- avoid imperative conditional chains for derived-input mapping logic

Notification catalog contract publication rule:
- registry read operations must expose explicit split contracts for all notifications
- consumers must not depend on fallback behavior from legacy RequiredParameters/OptionalParameters fields
- registry contract normalization should be performed once and exposed through a single canonical catalog used by all read APIs
- split-contract accessors and catalog normalization should read explicit split fields only, with no legacy-field fallback behavior
- static notification definitions should declare split fields at source (`RequiredPublisherParameters`, `RequiredTemplateParameters`, `OptionalTemplateParameters`) so normalization does not rely on legacy fields

### 3.6 Resolver Methods

Resolver methods are grouped retrieval operations.
They resolve missing parameter values and return normalized results.

Resolver method types include:
- internal data resolvers (using backend handlers/services)
- AI resolver (using existing event bridge interaction already implemented in backend)

From the processor perspective, all resolver methods are handled the same way.

### 3.7 Template Processing and Rendering

The processing flow must be:
1. load template for notification
2. detect parameters used in template
3. validate mandatory template parameters are represented
4. determine used parameters that still have no value
5. group missing parameters by resolver method
6. execute resolver methods by group
7. map resolver outputs to parameter values
8. validate final required values for rendering
9. merge template with resolved values
10. send email and record audit trail

## 4. AI Enrichment Requirements

AI enrichment is a resolver method, not a separate template processor mode.

Required behavior:
- template processing remains resolver-agnostic
- AI integration details stay inside AI resolver and existing backend AI orchestration components
- AI results are returned in the same parameter-value contract used by all resolver methods
- if AI enrichment fails for optional content, fallback behavior must still support safe email delivery

## 5. New Notification Onboarding Requirements

To add a notification:
1. ensure needed parameters exist in parameter registry, or add them
2. assign each new parameter to a resolver method
3. define or verify retrieval method required inputs in retrieval method registry
4. define notification required publisher input values (must include method-derived required inputs)
5. define notification mandatory and optional template parameters
6. author template using approved parameters through admin template management

No custom per-notification runtime branch should be required for standard onboarding.

## 6. Reliability and Fault Tolerance Requirements

The system must:
- enforce idempotent processing for repeated requests
- fail fast on missing mandatory contracts
- allow controlled fallback for optional enrichment failures
- use deterministic decision outcomes with explicit reason codes
- preserve processing continuity where business-safe

## 7. Observability and Audit Requirements

The system must provide:
- stage-level lifecycle visibility (validate, resolve, merge, send, audit)
- structured logs with correlation identifiers
- metrics for resolver success/failure/latency and send outcomes
- auditable record of policy decisions and final delivery status

## 8. Separation of Responsibilities (Functional)

The engine must maintain these responsibility boundaries:
- notification event processor: orchestration and control flow
- template resolver: parameter detection, resolution coordination, and validation
- template merge: content rendering only
- send and audit: delivery and immutable outcome records
- notification registry: notification-level contracts
- parameter registry: parameter-level contracts
- resolver methods: value retrieval/building

## 9. Out of Scope

This requirements baseline does not define:
- class names or folder layout
- specific technology implementations beyond existing platform commitments
- deployment steps and rollout choreography

Those are covered in design and implementation planning.

## 10. Acceptance Criteria

The process is considered compliant when:
- any notification is processed through one unified flow
- required publisher inputs are validated by notification contract
- method-required inputs are normalized in retrieval method registry and enforced by contract tests
- all non-passthrough retrieval methods are backed by concrete resolver implementations in processing runtime
- template parameter contracts are enforced consistently
- missing values are resolved by grouped resolver execution
- AI enrichment behaves as a standard resolver method
- rendering, send, and audit complete with deterministic outcomes
- fallback behavior is explicit, safe, and observable
