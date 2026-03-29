# PurposePath Squad Autonomous Development Target Workflow

**Status:** Proposed
**Owner:** Engineering Productivity / Squad Governance
**Version:** 0.1.0
**Last Updated:** 2026-03-27

## 1) Executive Summary
This document defines the target workflow for Squad-driven autonomous development in PurposePath. It is a label-driven, gate-governed lifecycle that combines autonomous execution with explicit human approval points for risk-bearing decisions.

The model is designed to be implementation-ready and auditable. It standardizes intake, routing, planning, implementation, QA validation, deployment, remediation, and escalation behavior.

### Locked Constraints (Normative)
1. Queue priority order is environment first, then priority, then age.
2. Human Gate 1 (design/plan) is mandatory.
3. Human Gate 1 rejection loops until approval.
4. Optional scope phase is allowed only for new features and must have no code work.
5. After design approval, failures route to implementation by default.
6. Return to design requires an explicit design-change signal.
7. Human Gate 2 occurs after QA deployment and is skippable by label, including production issues.
8. Production path is deploy production, then merge-down to preview, then dev.
9. Unrecoverable failure requires blocked label plus actionable human comment.
10. Waiting-human states are excluded from stall monitoring.

## 2) Goals and Non-Goals

### Goals
1. Provide a canonical end-to-end autonomous workflow with clear governance.
2. Eliminate ambiguity in label semantics and transition ownership.
3. Maximize autonomous throughput between required human decisions.
4. Ensure every transition is traceable, deterministic, and reversible where possible.
5. Support production and non-production lanes under one operating model.

### Non-Goals
1. Define service-level implementation details or business logic.
2. Replace architecture or coding standards.
3. Specify exact repository internals beyond workflow requirements.
4. Allow implicit gate bypass through side effects.

## 3) Human-Side Operating Model

### Human Responsibilities
1. Create issues with clear intent, acceptance criteria, and lane context.
2. Apply intake labels for type, environment, and priority.
3. Perform Human Gate 1 decision on plan/design.
4. Perform Human Gate 2 decision after QA deployment evidence unless skip label is used.
5. Resolve blocked escalations by selecting one remediation option.
6. Authorize exceptional risk decisions and record rationale.

### Label Timing by Human Action
1. Intake: apply squad plus type, env, and priority labels.
2. Optional scope phase: apply human:scope-validate only for new feature scoping.
3. Mandatory design gate: apply human:design-review for implementation-intended work.
4. Post-QA gate: apply human:deploy-validate unless go:skip-human-validation is active.
5. Exception path: apply blocked only when autonomous recovery is exhausted.

### Human Gate Outcomes
1. Gate 1 approve: go:design-approved and clear waiting-human label.
2. Gate 1 reject: go:changes-requested and re-enter pre-approval loop.
3. Gate 2 approve: go:deploy and proceed to lane deployment.
4. Gate 2 reject: go:review-failed and return to implementation.
5. Gate 2 skip: go:skip-human-validation, then proceed directly to deployment decision.

## 4) Squad-Side Operating Model

### Queueing and Ordering
1. Primary sort key: env.
2. Secondary sort key: priority.
3. Tertiary sort key: issue age.
4. Missing label hygiene is auto-flagged and corrected by policy.

### Routing
1. Intake router assigns squad ownership labels deterministically.
2. Route collisions resolve by governance first, then lane urgency, then specialty.
3. Route changes require state comment trace with reason.

### Planning
1. Squad generates a plan containing assumptions, risks, acceptance criteria, and validation strategy.
2. No implementation starts before go:design-approved.
3. Optional scope output is documentation-only and must not include code.

### Implementation
1. Design-approved issues enter implementation loop.
2. Squad runs build, tests, and quality checks.
3. Failure corrections default to implementation lane.
4. Design re-entry occurs only with explicit design-change signal.

### Review, Validation, Deployment, Remediation
1. Squad executes review and QA validation workflows.
2. After QA deployment evidence exists, Gate 2 decision path is evaluated.
3. Deploy actions follow lane policy.
4. Failures trigger bounded recovery attempts.
5. Unrecoverable failures escalate to blocked with actionable comment.

## 5) Canonical Lifecycle and State Machine Narrative

### Lifecycle Phases
1. Intake and triage.
2. Optional scope phase for new features, no code.
3. Human Gate 1 mandatory design/plan review.
4. Implementation and rework loops.
5. QA deployment and evidence collection.
6. Human Gate 2 (or approved skip path).
7. Deployment execution.
8. Production merge-down chain.
9. Close or blocked escalation.

### Transition Rules
1. Human Gate 1 is always required.
2. Human Gate 1 rejection loops until approved.
3. Post-design failures route to implementation by default.
4. Return to design requires explicit design-change signal.
5. Waiting-human states are excluded from stall logic.
6. All transitions must be idempotent and auditable.

### Narrative of Failure Handling
1. Failure detected after design approval.
2. Classify failure class.
3. Route to implementation unless explicit design-change signal exists.
4. Retry bounded transient remediations where allowed.
5. Escalate to blocked with actionable comment if unrecoverable.

## 6) Label Taxonomy, Semantics, and Mutual Exclusivity

### Namespaces
1. squad and squad:owner labels.
2. go decision labels.
3. human gate labels.
4. env labels.
5. priority labels.
6. type labels.
7. release labels.
8. blocked.

### Semantics
1. squad indicates queue participation; squad:owner indicates active ownership.
2. go labels represent lifecycle decisions and state progression.
3. human labels represent waiting gates requiring human decision.
4. env labels define lane and urgency context.
5. priority labels define urgency class.
6. type labels define work category.
7. release labels define target train.
8. blocked indicates autonomous recovery has been exhausted.

### Exclusivity Rules
1. go labels are mutually exclusive.
2. human labels are mutually exclusive.
3. priority labels are mutually exclusive.
4. type labels are mutually exclusive.
5. release labels are mutually exclusive.
6. env labels should normally be singular and validated by policy.
7. blocked is additive but must include escalation comment.

## 7) Native Squad Support Mapping: 0.9 Direction vs Repo Adaptation

### Expected Native in Squad 0.9 Direction
1. Label-based routing and ownership.
2. State transition automation.
3. Human wait/resume handling.
4. Basic autonomous stall heartbeat.
5. PR and validation loop orchestration.

### Repo-Specific Adaptation Needed
1. Strict queue ordering by env, priority, age.
2. Optional scope phase gating only for new features and no-code rule.
3. Explicit design-change signal for design re-entry.
4. Gate 2 skip policy and required audit trace.
5. Production deploy then merge-down enforcement.
6. Blocked escalation comment contract.
7. Stall exclusion policy for waiting-human states.

## 8) Required Workflow Adjustments for This Repo

### Intake and Routing Automation
1. Add deterministic queue sorter using env, priority, age.
2. Add required-label completeness validation at intake.
3. Add lane-defaulting logic for missing env labels with explicit warning.

### Gate Automation
1. Enforce mandatory Gate 1 before implementation assignment.
2. Implement Gate 1 reject loop as a persistent waiting cycle.
3. Add explicit design-change signal detector to permit design re-entry.

### Implementation Loop Automation
1. Route all post-design failures to implementation by default.
2. Add failure-class tagging for trend analysis.
3. Add bounded retry policy for transient checks.

### QA and Deploy Automation
1. Require QA deployment evidence before Gate 2 evaluation.
2. Implement Gate 2 skip behavior via go:skip-human-validation.
3. Enforce production-first deployment path and merge-down chain to preview then dev.

### Escalation and Stall Automation
1. Add unrecoverable-failure detector that applies blocked.
2. Post actionable escalation comment automatically on blocked transition.
3. Exclude waiting-human states from stall alerts and timers.

## 9) Recovery and Blocked Escalation Policy

### Recovery Strategy
1. Classify each failure as transient, deterministic, dependency, or governance.
2. Retry transient failures with bounded attempts and backoff.
3. Route deterministic failures to implementation correction path.
4. Route governance failures to relevant human gate.

### Unrecoverable Failure Escalation
1. Apply blocked when recovery bounds are exceeded.
2. Post actionable comment including summary, attempts, and options.
3. Include recommended next action with urgency and impact.
4. Keep issue in blocked until human selects recovery path.

### Actionable Escalation Comment Requirements
1. Failure class and plain-language impact.
2. Timestamped recovery attempts.
3. At least two remediation options.
4. Explicit requested human decision.

## 10) Stall Monitoring Policy (Active Squad States Only)

### Monitored States
1. Active implementation.
2. Active validation.
3. Active deployment.

### Excluded from Stall Detection
1. Any human gate waiting state.
2. blocked while awaiting human response.
3. Initial grace window immediately after state transition.

### Escalation Levels
1. Threshold 1: reminder with context snapshot.
2. Threshold 2: reroute to coordinating role.
3. Threshold 3: escalate to human owner with recommendation.

## 11) Production vs Non-Production Lane Details

### Production Lane
1. Highest queue precedence via env-first ordering.
2. Mandatory Gate 1 design approval.
3. QA evidence and Gate 2 decision still apply, with optional skip label.
4. Deploy to production when approved.
5. Mandatory merge-down chain: production to preview to dev.

### Non-Production Lane
1. Ordered after production by priority then age.
2. Mandatory Gate 1 design approval.
3. Gate 2 after QA evidence, with optional skip label.
4. Deploy by lane strategy and release target policy.

### Shared Invariants Across Lanes
1. Default failure route after design approval is implementation.
2. Design re-entry requires explicit design-change signal.
3. Unrecoverable failures must use blocked escalation policy.

## 12) Governance and Safety Constraints
1. No code implementation before go:design-approved.
2. Scope phase is allowed only for new features and no code changes.
3. Every state transition must be auditable via labels and comments.
4. Label namespace exclusivity must be enforced by automation.
5. Human gate outcomes must be explicit labels, not inferred state.
6. Production flow must include merge-down to preview then dev.
7. blocked transitions must include actionable human guidance.
8. Waiting-human states are not stalled and must not trigger stall alerts.

## 13) Metrics and Observability

### Throughput Metrics
1. Intake to deploy lead time by env.
2. Time in Gate 1 and Gate 2.
3. Queue wait by env and priority.
4. Rework loop count per issue.

### Quality and Reliability Metrics
1. Validation pass/fail rate by lane.
2. Failure class distribution.
3. Recovery success rate before blocked escalation.
4. Post-deploy defect correlation against skip-human-validation usage.

### Governance Metrics
1. Gate compliance rate.
2. Label hygiene violations and auto-correction counts.
3. Production merge-down completion latency.
4. blocked aging and resolution outcomes.

### Observability Requirements
1. Transition actor and timestamp.
2. Transition cause and previous state.
3. Gate decision evidence links.
4. Deployment and validation artifact references.

## 14) Implementation Roadmap in Phases with Acceptance Criteria

### Phase 1: Baseline Governance
Scope:
1. Namespace exclusivity enforcement.
2. Mandatory Gate 1 enforcement.
3. Queue sort by env, priority, age.

Acceptance Criteria:
1. No implementation starts without Gate 1 approval.
2. Conflicting labels are auto-resolved.
3. Queue order is deterministic and reproducible.

### Phase 2: Lifecycle Loop Control
Scope:
1. Optional scope phase for new features only.
2. Default post-design failure route to implementation.
3. Explicit design-change signal path to design.

Acceptance Criteria:
1. Scope phase contains no code activity.
2. Failures after design approval return to implementation by default.
3. Design re-entry occurs only when explicit signal exists.

### Phase 3: QA Gate and Deployment Semantics
Scope:
1. Gate 2 after QA deployment with skip label support.
2. Production deploy plus merge-down enforcement.
3. blocked escalation with actionable comment.

Acceptance Criteria:
1. Deploy decisions have gate evidence or skip evidence.
2. Production promotions always show merge-down trace.
3. Unrecoverable failures always include blocked plus actionable options.

### Phase 4: Monitoring and Hardening
Scope:
1. Stall monitor active-state-only behavior.
2. Failure taxonomy metrics and dashboards.
3. Policy reporting and governance audits.

Acceptance Criteria:
1. Waiting-human states generate zero stall alerts.
2. Recovery and blocked trends are measurable.
3. Governance compliance report is produced on schedule.

## 15) Risks and Mitigation

### Risk 1: Label drift and invalid combinations
Mitigation:
1. Enforce exclusivity with automation.
2. Add periodic reconciliation jobs.

### Risk 2: Gate skip abuse increases regression risk
Mitigation:
1. Require rationale on skip usage.
2. Track skip frequency and correlate with defects.

### Risk 3: Gate 1 decision latency slows throughput
Mitigation:
1. Define response SLO for Gate 1.
2. Standardize plan format to reduce review friction.

### Risk 4: Merge-down misses after production deploy
Mitigation:
1. Automate merge-down as completion requirement.
2. Alert if merge-down is incomplete within policy window.

### Risk 5: blocked backlog grows without action
Mitigation:
1. Add blocked aging alerts and owner escalation.
2. Require actionable option set in escalation comments.

## 16) Decision Log and Open Decisions

### Confirmed Decisions
1. Queue order is env first, priority second, age third.
2. Human Gate 1 is mandatory and reject-looped until approval.
3. Optional scope phase is feature-only and no-code.
4. Post-design failures route to implementation by default.
5. Design re-entry requires explicit design-change signal.
6. Human Gate 2 occurs after QA deployment and can be skipped by label.
7. Production path is deploy production then merge-down to preview then dev.
8. Unrecoverable failure requires blocked plus actionable human comment.
9. Waiting-human states are excluded from stall monitoring.

### Open Decisions
1. Exact non-production env precedence when multiple env classes are used.
2. Standard retry bounds by failure class.
3. Canonical label name for design-change signal.
4. Authorization policy for skip-human-validation in production cases.
5. Gate 1 and Gate 2 response SLO targets.
6. Minimum evidence bundle for blocked escalation comments.

## Appendix A: Actionable Blocked Comment Template
Status: blocked
Failure class: transient | deterministic | dependency | governance
Summary: short impact-focused description
Attempts made:
1. Attempt one with result
2. Attempt two with result
3. Attempt three with result
Recommended options:
1. Option A with expected impact and risk
2. Option B with expected impact and risk
Requested human decision by: date/time

## Appendix B: Transition Validation Checklist
1. Exactly one active go label.
2. At most one active human label.
3. Exactly one active priority label.
4. Exactly one active type label.
5. At most one active release label.
6. Implementation states require prior go:design-approved.
7. Gate 2 requires QA evidence unless skip-human-validation is active.
8. Production completion requires merge-down trace to preview and dev.

## 17) Final V1 Baseline Decisions (Approved 2026-03-29)

This section is normative for implementation kickoff. If any earlier section conflicts with this section, this section wins for v1.

### 17.1 Workflow Scope for V1
1. Automated scope loop is disabled in v1.
2. Scope/discovery for new features is handled interactively outside automation.
3. Mandatory automation gates in v1:
1. Human Gate 1: design approval.
2. Human Gate 2: post-QA deployment validation, unless skipped by label.

### 17.2 Lane Selection Rule
1. Presence of `hotfix` means production lane.
2. Absence of `hotfix` means non-production lane.

### 17.3 Active State Caps (Configurable)
Balanced initial caps designed for throughput without overload:
1. `cap:implementing = 3`
2. `cap:validating = 3`
3. `cap:deploying-qa = 2`
4. `cap:deploying-prod = 1`

Cap behavior:
1. If next stage is eligible and cap is full, apply stage-specific pending label.
2. Dequeue on capacity using the standard order: hotfix first, then priority, then age.
3. Issues with `blocked` or any `human:*` label are excluded from cap counting.

### 17.4 Internal Pending Labels (Squad-Controlled)
Use these internal labels for queue smoothness:
1. `pending:implementing`
2. `pending:validating`
3. `pending:deploying-qa`
4. `pending:deploying-prod`

Rules:
1. Pending labels are internal orchestration signals, not manual operator controls.
2. Pending labels are cleared automatically when issue is admitted to active stage.

### 17.5 Validation Agent Chain (Pre-Deploy)
1. Validation chain is configurable (agents plus prompts), and may require rebuild/reload when changed.
2. Recommended v1 execution mode: hybrid.
1. Run validators sequentially by default for deterministic feedback.
2. Allow bounded parallel groups only for independent checks (max parallel validators per issue = 2).
3. Short-circuit to implementation on first fail.

Per-validator contract:
1. Validator outcome is `PASS`, `FAIL`, or `SKIP`.
2. Validator decides relevance; if not relevant, it emits `SKIP`.
3. Every validator must comment on every run (pass, fail, or skip).
4. `SKIP` is pass-equivalent for transition flow.
5. Any `FAIL` routes issue to implementation rework.

### 17.6 Failure Routing and Design Re-entry
1. After `go:design-approved`, all failures route to implementation by default.
2. Return to design requires explicit design-change signal (`go:changes-requested` in v1).

### 17.7 Human Labels and Blocked Ownership
1. `human:*` is the single family used for human-attention states.
2. Blocked issues must include:
1. `blocked`
2. `human:blocked`
3. Blocked ownership is human-owned (not lead-owned).

Blocked resolution signal:
1. Human adds a comment with chosen resume target.
2. Human applies `go:blocked-resolved`.
3. Automation removes `blocked` and `human:blocked`, then resumes from last active stage.
4. `go:blocked-resolved` is transient and auto-cleared after resume routing.

### 17.8 Retry Budgets (Configurable Defaults)
Recommended initial defaults:
1. Implementation rework attempts: 3
2. Validation rerun attempts: 2
3. QA deploy remediation attempts: 2
4. Production deploy remediation attempts: 2
5. Merge-down retries: 1 per hop
6. Global autonomous recovery ceiling: 8 attempts per issue lifecycle

Budget exhaustion transitions to blocked contract.

### 17.9 Human SLO and Reminder Policy
1. Design approval SLO: 24h.
2. QA validation SLO: 48h.
3. On SLO breach, add one reminder comment only (no repeated reminder spam).

### 17.10 Skip-Gate Policy (V1)
1. `go:skip-human-validation` can be applied by any actor authorized to apply labels.
2. Applies to both non-production and production lanes.
3. If skip label is present, there are no additional human gates after design approval.
4. For production lane, automation continues through deploy and merge-down until close or blocked.
