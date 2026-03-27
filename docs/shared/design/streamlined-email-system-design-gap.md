# Streamlined Email System Design and Gap Analysis

## 1) Design Goals and Constraints

### Goals
- Provide one coherent email architecture across authentication, billing/notifications, invitations, and AI-insight enrichment.
- Preserve domain boundaries: orchestration in Application, integration in Infrastructure/Lambda adapters, no controller-level business logic.
- Enforce deterministic behavior for mandatory emails (security/compliance) vs optional emails (engagement/marketing).
- Ensure tenant-safe, auditable, and observable delivery with actionable failure telemetry.
- Support template governance with clear source-of-truth and controlled fallback behavior.

### Constraints from Existing System
- Multi-path email system already exists: direct send path and event-driven notification path.
- AWS SES is the active outbound channel and must remain the initial delivery provider.
- Notification event definitions and template identifiers are already persisted and consumed by runtime paths.
- Existing user preferences capture notification intent but are not consistently enforced at send time.
- AI-insight payload processing already has strict schema/limit guards and fallback semantics that must be retained.

### Non-Goals
- No per-class implementation design.
- No provider migration proposal (SES replacement) in this draft.
- No endpoint contract changes in this document.

## 2) As-Is Architecture Summary (from current code)

### A. Direct Send Path (synchronous application-triggered)
- Auth and account flows call IEmailService directly (registration verification, resend verification, password reset, invitation, username/identity changes).
- Infrastructure implementation is SesEmailService, which:
  - Tries to render template from DynamoDB-backed email templates via RazorLight.
  - Falls back to inline hardcoded HTML/text when template is missing or render fails.
- This path includes significant inline content fallback for resilience, but behavior is inconsistent by scenario:
  - Some failures are swallowed (best-effort) and processing continues.
  - Other failures are propagated.

### B. Event-Driven Notification Path (async)
- Application NotificationService validates event definition + required parameters, persists NotificationRequest, publishes NotificationEnqueuedEvent via EventBridge publisher.
- Notification Processor Lambda receives EventBridge payload, resolves/normalizes parameters, renders template, sends via SES, writes NotificationAudit.
- Notification event schema enforcement exists for AI-insight event preconditions.

### C. AI-Insight Email Path
- Goal-created insight email event type is treated specially:
  - Required orchestration parameters are validated at enqueue stage.
  - Notification Processor runs insight payload through EmailInsightPayloadPipeline.
  - Pipeline enforces JSON shape, schema major version, strict validation, normalization, limits, HTTPS CTA policy.
- Fallback semantics exist:
  - Template-only fallback for invalid payloads (insight disabled variables).
  - Telemetry-only degradation for recoverable issues (example: CTA URL dropped).

### D. Template Storage/Rendering Split (current)
- DynamoDB template repository and admin management exist for template entities and metadata.
- Notification Processor Lambda renders from local filesystem .cshtml templates in its Templates folder.
- Legacy file-based EmailTemplateRegistry runtime dependency has been retired from active DI/runtime paths (#780).
- Data seeder for new EmailTemplate schema is effectively placeholder (manual migration pending).

### E. Preferences, Suppression, and Audit/Observability (current)
- User preferences model includes granular notification flags (Email, Marketing, CoachingReminders, TeamUpdates, SystemNotifications).
- Preferences update handlers exist and persist user preferences.
- No unified send-time policy gate applies preferences/suppression consistently across direct and async paths.
- NotificationAudit captures sent artifact details and SES message id for event-driven path.
- Logging is present in all major services; selected CloudWatch alarms exist for Notification Processor Lambda.

### F. #776 Direct Template Source/Fallback Update
- Direct runtime template resolution in `SesEmailService` is explicitly DB-first.
- Template resolution decisions are now logged with auditable fields:
  - `EventType`
  - `TemplateName`
  - `Category`
  - `Source` (`database` or `break_glass_fallback`)
  - `FallbackReason` (`DB_TEMPLATE_NOT_FOUND_OR_RENDER_FAILED`)
- Invitation email flow now attempts DB template rendering before fallback.
- Notification Processor AI-insight and HTML workflow behavior is preserved in this slice.

### I. #780 Legacy Runtime Retirement
- Removed runtime DI registration for file-based `EmailTemplateRegistry`.
- Removed obsolete file-based registry contract/implementation files from active code path.
- Consolidated duplicated direct/billing inline fallback bodies into one emergency break-glass fallback builder in `SesEmailService`.
- External contracts remain unchanged; fallback now emits a single canonical source marker (`break_glass_fallback`) while preserving mandatory-delivery continuity.

### G. #777 Admin Send Config + Analytics Contract Update
- Email template analytics endpoint no longer returns hardcoded placeholder payloads.
- Analytics now resolves from repository-backed template metrics over a rolling 30-day window with:
  - aggregate counts (`sent`, `delivered`, `opened`, `clicked`, `bounced`, `unsubscribed`)
  - computed rates (`delivery`, `open`, `click`, `bounce`, `unsubscribe`)
  - timeline points sourced from persisted daily analytics rows.

### H. #778 AI Insight Dispatch + Audit Contract Alignment
- AI insight resolver now returns structured processing telemetry for contract-aligned audit enrichment.
- Notification processor preserves existing insight fallback/degradation behavior while appending insight metadata to `decision_reason` when present:
  - `insight_state`
  - `insight_reason`
  - `insight_detail`
- No endpoint/payload API contract changes were introduced; alignment is implemented within existing audit fields.

## 3) Target Architecture (components, responsibilities, data contracts)

### A. Unified Email Orchestration Model
- Introduce a single Email Dispatch Policy layer used by both direct and event-driven paths.
- Classify each email as one of:
  - Mandatory: security/compliance/critical account continuity (not user-optional).
  - Optional: marketing/engagement/reminder classes (subject to user preference + suppression).
- All email requests pass through the same policy decision contract before rendering/sending.

### B. Component Responsibilities
- Application layer:
  - Emit canonical EmailDispatchRequest (or NotificationRequest for async) with event type and business context only.
  - Never embed provider-specific concerns.
- Policy engine (shared service, callable from both paths):
  - Resolve channel eligibility from user preferences + global suppression + event classification.
  - Return Decision = Send | Suppress with reason code.
- Template service:
  - Single source of truth for templates (DynamoDB-backed), versioned by template key and locale.
  - Controlled fallback chain with explicit policy and telemetry.
- Delivery adapter:
  - SES send, provider response capture, retry contract, idempotency handling.
- Audit + observability:
  - Record decision, render source, send outcome, and fallback/suppression reason in one audit model.

### C. Target Data Contracts
- Event definition contract should include:
  - EventType, Category, TemplateId, RequiredParameters, OptionalParameters,
  - DeliveryPolicyClass (Mandatory|Optional),
  - PreferenceGate (which user preference flag applies),
  - DefaultReplyTo metadata.
- Dispatch request contract should include:
  - TenantId, UserId, RecipientEmail, EventType, Parameters, CorrelationId, IdempotencyKey.
- Audit contract should include:
  - Decision (Sent/Suppressed/Failed), DecisionReason, TemplateSource (DB/Fallback), FallbackReason,
  - SES MessageId, RetryCount, timestamps, pipeline degradation metadata.

## 4) End-to-End Flows (normal, insight, fallback, suppression)

### A. Normal Flow
1. Producer emits notification or direct dispatch request.
2. Policy engine evaluates mandatory/optional + preferences/suppression.
3. If allowed, template service resolves active template version.
4. Renderer produces subject/html/text.
5. SES adapter sends and returns provider message id.
6. Unified audit record stored with correlation and outcome.

### B. Insight Flow
1. Event type indicates insight-enabled scenario.
2. Required orchestration fields validated.
3. Insight payload pipeline sanitizes/validates/normalizes payload.
4. Template variables mapper emits insight_enabled and flattened content variables.
5. Render + send continues when valid; degradation metadata logged if partial adaptation occurred.
6. Audit stores insight processing state and fallback/degradation details.

### C. Fallback Flow
1. Primary template resolution/render fails.
2. Controlled fallback policy executes (fallback template key, not arbitrary hardcoded body except break-glass).
3. Send continues if fallback allowed.
4. Audit records fallback type and reason code.

### D. Suppression Flow
1. Policy engine identifies optional email blocked by preference or suppression list.
2. No provider call made.
3. Suppression audit entry stored with reason and decision timestamp.
4. Metrics increment suppression counters by event type and reason.

## 5) Gap Analysis Table (Current, Target, Gap, Priority, Proposed Change)

| Current | Target | Gap | Priority | Proposed Change |
|---|---|---|---|---|
| Direct path and async path enforce different rules and have inconsistent failure semantics. | One policy-controlled dispatch model for all paths. | Behavior divergence causes unpredictable outcomes and operational complexity. | P0 | Introduce shared Email Dispatch Policy service and route both paths through it. |
| User notification preferences are collected but not centrally enforced at send-time for notification events. | Mandatory vs optional policy with enforceable preference gates. | Optional emails can be sent without user intent checks. | P0 | Add event-level policy metadata and a preference/suppression evaluation step before send. |
| Notification Processor stores audit but does not update NotificationRequest lifecycle state in the processor path. | Request lifecycle transitions tracked end-to-end (pending/processing/sent/failed/suppressed). | Queue/request state and audit can drift; retry semantics are unclear. | P0 | Inject NotificationRequest repository in processor and mark final state with retry metadata. |
| Template source is fragmented (DynamoDB templates, Lambda filesystem templates, legacy file registry, inline code fallback). | Single authoritative template source with controlled fallback chain. | Governance and consistency risk; high maintenance overhead. | P0 | Consolidate runtime rendering onto DB templates + versioned fallback templates; deprecate legacy registry and most inline templates. |
| Notification Processor Pulumi event rule pattern appears misaligned with published event source/detail-type conventions. | Route reliably from publisher to processor in all environments. | Potential event delivery mismatch or brittle environment-specific behavior. | P0 | Align EventBridge source/detail-type contract via shared constants (`NotificationEventBridgeContract`) and add contract tests that fail on routing drift. |
| AI insight fallback/degradation now persists in audit decision metadata, but metric surfacing remains limited. | Insight-specific metrics and audit fields for fallback/degradation rates. | Audit traceability improved, but aggregated operational trend visibility is still incomplete. | P1 | Add structured metric emission and aggregate reporting by fallback reason/detail for pilot monitoring. |
| Analytics repository supports unsubscribe/open/click counters, but admin analytics endpoint remains placeholder-style in service layer. | Actual analytics surfaced from recorded events and unified audit telemetry. | Limited operational/business visibility. | P1 | Implement analytics query service over template analytics + audit records; retire placeholder response. |
| Seeding/migration for new email template schema is incomplete (manual migration TODO). | Reproducible template bootstrap and promotion workflow across environments. | Drift risk between environments; onboarding friction. | P1 | Add canonical seed/migration pipeline for template schema and publish runbook. |
| Inline hardcoded fallback contains links/content that may drift from product routes/brand policy. | Fallback templates managed and versioned centrally. | Content drift and compliance risk. | P2 | Replace inline fallback bodies with managed fallback templates and emergency-only minimal hardcoded fallback. |
| Preference model supports granular categories, but event-definition mapping to those categories is not explicit. | Each event explicitly mapped to preference domain and mandatory flag. | Incomplete policy traceability. | P2 | Extend notification event definition schema with preference key mapping and mandatory marker. |

## 6) Cutover Plan (dev/staging/prod, legacy removal)

### Phase A: Dev hardening
- Implement shared policy gate and wire it in both direct and async paths.
- Add explicit request lifecycle updates in Notification Processor.
- Align EventBridge routing contract and validate with automated integration tests.
- Add structured telemetry for fallback/suppression decisions.

Exit criteria:
- All critical email scenarios deliver through policy gate.
- Lifecycle status and audit are coherent for each request id.
- Producer-to-processor routing test is green.

### Phase B: Staging dual-run and parity validation
- Run template resolution in dual mode (new source primary, legacy fallback observable).
- Compare send outcomes, fallback rates, and suppression decisions.
- Validate AI-insight payload outcomes and degradation distributions.

Exit criteria:
- No critical regression in mandatory mail delivery.
- Fallback and suppression metrics within expected bands.
- Operational dashboards and alerts ready.

### Phase C: Prod progressive rollout
- Gradual rollout by event category (auth -> invitation -> billing -> insights/engagement).
- Keep rollback switch to legacy behavior per event category for limited time.
- Monitor error/fallback/suppression signals and SES delivery health.

Exit criteria:
- Stable mandatory delivery SLO.
- No unresolved P0 incidents for at least one full billing cycle.

### Legacy removal
- Remove file-based EmailTemplateRegistry runtime dependency.
- Remove redundant inline template paths except break-glass emergency skeleton.
- Remove placeholder analytics endpoint behavior after real analytics release.

## 7) Risks and Mitigations

- Risk: Mandatory emails accidentally suppressed by policy bugs.
  - Mitigation: Hard policy invariants and test matrix asserting mandatory emails bypass user-optional suppression.

- Risk: Event routing mismatch causes silent notification drops.
  - Mitigation: Contract tests at IaC + runtime smoke checks and DLQ alerting.

- Risk: Template migration introduces render/runtime failures.
  - Mitigation: Template compile/preview validation pipeline and staged dual-run comparison.

- Risk: Insight payload quality regressions increase fallback rate.
  - Mitigation: Threshold alarms on fallback reason codes and weekly review of degradation trends.

- Risk: Operational blindness across split audit/analytics signals.
  - Mitigation: Unified audit schema and dashboard combining send, suppress, fallback, and provider metrics.

## 8) Suggested implementation phases

1. Foundation and policy
- Add event policy metadata and shared dispatch policy service.
- Enforce policy in both direct and async email entry points.

2. Lifecycle and observability
- Update NotificationRequest statuses in processor.
- Add structured audit fields for decision/fallback/degradation/suppression.
- Add metrics and alarms for fallback and suppression reasons.

3. Template unification
- Consolidate template runtime to one source-of-truth.
- Replace inline fallbacks with managed fallback templates.
- Complete template seed/migration tooling.

4. Analytics and admin completion
- Replace placeholder analytics responses with real aggregated data.
- Add operational dashboards and runbooks.

5. Legacy retirement
- Remove deprecated template registry and obsolete paths.
- Clean feature flags and fallback switches after stabilization window.

## 11) Issue 780 Legacy Retirement Delta

- Runtime legacy registry path retired:
  - Removed file-based registry DI registration and obsolete registry files from active runtime.
- Inline fallback path retirement:
  - Replaced duplicated per-scenario inline fallback bodies with a centralized break-glass fallback skeleton.
  - Template decision telemetry now records fallback source as `break_glass_fallback`.
- Contract protection:
  - No endpoint or payload contract changes introduced in this slice.

## 9) Issue 773 Kickoff Delta

- Event definition schema now includes policy metadata fields used at enqueue validation:
  - delivery_policy_class: mandatory | preference_gated | unrestricted
  - preference_gate: required when delivery_policy_class is preference_gated
- Enqueue flow now validates policy metadata and rejects invalid definitions with actionable errors.
- Enqueue flow now validates category/type mapping for known domains:
  - payment.*, billing.*, trial.* => billing category
  - auth.*, authentication.* => authentication category

## 10) Issue 779 Documentation and Validation Evidence Delta

This section records the documentation and objective validation evidence required for streamlined email cutover governance.

### Documentation alignment completed

- Requirements alignment:
  - `docs/shared/Requirements/email-insights-requirements.md` now includes cutover governance controls for policy transparency, contract alignment, and evidence expectations.
- API spec alignment:
  - `docs/shared/Specifications/api-admin/admin-api-specification.md` analytics contract now matches repository-backed metrics/rates/timeline response shape used by the admin email templates API.
- Validation evidence artifact:
  - `docs/shared/Specifications/validation/2026-03-27-streamlined-email-cutover-readiness.md` captures command-level evidence and contract impact notes.

### Cutover evidence checklist (dev/staging gate input)

1. Direct path template source/fallback evidence
- Verify `SesEmailService` logs include:
  - `Source=database|inline_fallback`
  - `FallbackReason=DB_TEMPLATE_NOT_FOUND_OR_RENDER_FAILED`

2. Async insight audit enrichment evidence
- Verify notification processor appends insight telemetry metadata to decision reason context:
  - `insight_state`
  - `insight_reason`
  - `insight_detail`

3. Admin analytics contract evidence
- Verify `GET /email-templates/{id}/analytics` returns period, metrics, rates, and timeline data sourced from repository analytics.

4. Focused validation command evidence
- Build and targeted tests are documented in the validation artifact and linked in issue completion notes.
