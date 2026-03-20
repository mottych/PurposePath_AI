# Squad Label State Machine

## Purpose

This document is the single source of truth for issue workflow states driven by label namespaces in repositories running Squad, especially:
- `squad` and `squad:*`
- `go:*`
- `release:*`
- `type:*`
- `priority:*`
- `env:*`
- `human:*`

It also includes related operational states that directly affect coding-agent wait/resume flow.

## Scope

This state machine describes issue lifecycle behavior across the standard Squad files:
- `.github/workflows/squad-triage.yml`
- `.github/workflows/squad-issue-assign.yml`
- `.github/workflows/squad-state-transitions.yml`
- `.github/workflows/squad-copilot-delivery-loop.yml`
- `.github/workflows/squad-label-enforce.yml`
- `.github/workflows/squad-heartbeat.yml`
- `.github/workflows/sync-squad-labels.yml`
- `.github/workflows/squad-copilot-qa-loop.yml`
- `.github/workflows/squad-workflow-boundary-guard.yml`
- `.squad/agents/*.md`
- `.squad/routing.md`
- `.squad/team.md`

## Ownership Model

- Primary transition engine: GitHub workflow adapters operating on label events.
- Workflow role: enforce label-state progression, routing handoff, and wait/resume mechanics.
- Source of truth for behavior: this state machine plus the corresponding `.github/workflows/squad-*.yml` implementations.
- Source of truth for team composition/routing metadata: `squad.config.ts` and generated `.squad/` artifacts.

## Namespace Rules

- `go:*` labels are mutually exclusive (enforced automatically).
- `release:*` labels are mutually exclusive (enforced automatically).
- `type:*` labels are mutually exclusive (enforced automatically).
- `priority:*` labels are mutually exclusive (enforced automatically).
- `env:*` labels are environment context signals (not mutually exclusive with other namespaces).
- `human:*` labels are explicit human-gate signals and are mutually exclusive (one open gate at a time).
- `bug` and `feedback` are high-signal standalone labels managed by sync workflow.
- `squad` is inbox/triage entry; `squad:*` is assignment/routing.

## State Catalog

### Squad Namespace

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `squad` | Issue enters squad triage inbox | Manual (user/automation) | Label added to issue | `squad-triage.yml` must evaluate assignment and add one `squad:*` label |
| `squad:lead` | Routed to lead for coordination/triage path | Automatic or manual | Triage selects lead path, or manual correction | Lead performs triage/design/hotfix coordination and decides next routing |
| `squad:reviewer` | Routed to reviewer | Automatic or manual | Routing/assignment decision | Reviewer handles review gates and can drive promote/fail outcomes |
| `squad:quality-reviewer` | Routed to quality reviewer | Automatic or manual | Quality/architecture gap path | Quality reviewer diagnoses and drives correction workflow |
| `squad:copilot` | Routed to coding agent | Automatic or manual | Triage/lead routes coding work to Copilot | `squad-issue-assign.yml` assigns coding agent and starts implementation |

### Go Namespace

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `go:needs-research` | Default triage verdict: investigation required | Automatic by triage or manual by lead | Added by `squad-triage.yml` or lead research hold decision | Gather missing evidence, then transition to approved/design/hotfix/no path |
| `go:yes` | Approved to implement (legacy/governance path) | Manual | Explicit approval decision | Ensure release target exists; `squad-label-enforce.yml` auto-adds `release:backlog` if missing |
| `go:no` | Not pursuing implementation | Manual | Explicit reject/defer decision | Any `release:*` labels are removed automatically |
| `go:scope-approved` | Scope approved, proceed to design | Manual gate per team/lead process | @mottych scope confirmation | Advance to design and decomposition path |
| `go:design-approved` | Design approved, proceed to implementation sub-issues | Manual gate per team/lead process | @mottych design confirmation | Create/route implementation issues |
| `go:review-ready` | Implementation complete and ready for reviewer validation stage | Lead/implementor/manual | Code complete and local/unit validation done | Route to reviewer validation lane and auto-post implementation handoff summary on issue |
| `go:skip-human-validation` | Explicit approval to skip human deploy-validation gate | Manual gate per team/lead process | @mottych risk acceptance decision | Bypass `human:deploy-validate` and move to deploy decision |
| `go:deploy` | Deployment authorized to target environment (dev or prod) | Manual/role-driven gate | Validation complete and owner acknowledgement | Execute deployment/promotion workflow for target environment |
| `go:review-failed` | CI/review/deploy failed; needs correction | Manual/role-driven or automation-linked operations | Failure diagnostics/reopen flow | Reopen corrective work, fix issue, re-run validation; auto-post short failure findings summary on issue |
| `go:changes-requested` | Human reviewer requested changes before approval | Manual/role-driven gate | Review feedback requiring implementation updates | Return to implementation loop; auto-post failure/change summary on issue |

### Hotfix Flag (Warning)

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `hotfix` | Production fix warning flag | Automatic or manual | Existing prod/hotfix signals or explicit decision | Use hotfix workflow from production baseline (`main`) and validate on preprod before production |

### Environment Namespace

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `env:dev` | Work targets dev environment | Manual or triage context | Environment scoping decision | Keep validation/deploy plan aligned to dev scope |
| `env:prod` | Issue affects production environment | Manual or triage context | Incident/production-impact signal | Force lead hotfix path consideration; may add `hotfix` |

### Release Namespace

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `release:backlog` | Not yet targeted to a version | Automatic/manual | Added directly or auto-added for `go:yes` when release target missing | Keep in backlog until explicit release target is chosen |
| `release:v0.4.0` | Targeted for v0.4.0 | Manual | Release planning decision | Deliver within v0.4.0 scope |
| `release:v0.5.0` | Targeted for v0.5.0 | Manual | Release planning decision | Deliver within v0.5.0 scope |
| `release:v0.6.0` | Targeted for v0.6.0 | Manual | Release planning decision | Deliver within v0.6.0 scope |
| `release:v1.0.0` | Targeted for v1.0.0 | Manual | Release planning decision | Deliver within v1.0.0 scope |

### Type Namespace

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `type:feature` | New capability | Manual/triage | Feature work intake | Lead-guided feature/design path before implementation |
| `type:enhancement` | Improvement to existing capability | Manual/triage | Enhancement intake | Lead-guided enhancement path before implementation |
| `type:bug` | Defect fix | Manual/triage | Bug report intake | Route to implementation and validation flow |
| `type:spike` | Research/investigation only | Manual/triage | Uncertain scope/approach | Produce findings and implementation recommendation |
| `type:docs` | Documentation work | Manual/triage | Docs update intake | Route docs scope through review/validation flow |
| `type:chore` | Maintenance/refactor/cleanup | Manual/triage | Maintenance request | Route operational work through normal approvals |
| `type:epic` | Parent issue for decomposition | Manual | Epic planning decision | Decompose into sub-issues and track overall progress |

### Priority Namespace

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `priority:p0` | Blocking release | Manual | Critical priority decision | Expedite triage, assignment, and validation |
| `priority:p1` | Current sprint priority | Manual | Sprint planning decision | Schedule for current sprint execution |
| `priority:p2` | Next sprint priority | Manual | Sprint planning decision | Schedule for near-term backlog execution |

### High-Signal Standalone Labels

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `bug` | High-visibility defect signal | Manual/intake | Defect identified | Use with `type:bug` where applicable for urgency visibility |
| `feedback` | High-visibility user feedback signal | Manual/intake | Feedback report identified | Ensure triage captures user-impact context |

### Related Operational Labels (Non-go/squad, but state-critical)

| Label | Meaning | Set By | Trigger | What Must Happen In This State |
|---|---|---|---|---|
| `human:needs-info` | Waiting for reporter/owner input | Manual or automatic | Clarification required, or Copilot question detected in `squad-copilot-qa-loop.yml` | Owner responds; Q&A loop removes label and resumes agent work |

### Automation Boundary

- `squad-triage.yml` handles initial intake to lead-owned design/requirements gates.
- `squad-state-transitions.yml` handles cross-gate transitions (`go:*`, `human:*`) including Copilot routing, rework loops, deploy gating, and close-on-deploy behavior.
- `squad-copilot-delivery-loop.yml` handles Copilot PR auto-merge arming plus deployment outcome sync to `go:review-ready` or `go:review-failed`.
- `squad-copilot-delivery-loop.yml` also watches failed Copilot PR validation workflow runs and applies `go:review-failed` automatically to resume implementation.
- `squad-copilot-qa-loop.yml` handles Copilot clarification wait/resume (`human:needs-info`) during implementation.
- `squad-label-enforce.yml` handles namespace exclusivity and release-target hygiene.
- `squad-workflow-boundary-guard.yml` enforces architecture constraints defined in this repository.
- `squad-heartbeat.yml` periodically checks open `squad:copilot` issues for inactivity and posts a stall-watch alert comment that mentions the owner.

### Human Namespace (Explicit Human Gates)

| Label | Meaning | Set By | Trigger | Auto-clear Condition |
|---|---|---|---|---|
| `human:needs-info` | Human response required before Copilot continues | Copilot Q&A automation/lead/manual | Copilot asks a clarifying question | Removed when owner responds in issue thread |
| `human:design-review` | Human design review is required | Lead/automation/manual | Design decision required | Removed when `go:design-approved` is applied |
| `human:scope-validate` | Human scope validation is required | Lead/automation/manual | Scope decision required | Removed when `go:scope-approved` is applied |
| `human:deploy-validate` | Human deployment validation gate is required | Lead/automation/manual | Validation evidence is ready in target environment (dev or preprod) | Removed when `go:deploy` or `go:skip-human-validation` is applied |

## Transition Map

## State Transition Diagram (STD)

Legend:
- `A:*` = Automation
- `L:*` = Lead
- `H:*` = Human gate
- `C:*` = Copilot
- `R:*` = Reviewer/CI
- `X:*` = Expert agents (optional)

### STD-1: Core Delivery Path (Compact)

```mermaid
flowchart TB
  subgraph Reporter[Reporter]
    I1[Add squad]
  end

  subgraph Auto[Automation]
    A1[Triage]
    A2[Assign Copilot]
  end

  subgraph Lead[Lead]
    L1[Research route]
    L2[Route implementation]
    L4[Route hotfix]
    L5[Close issue]
  end

  subgraph Human[Human Gate]
    H1[Approve scope and design]
    H2[Approve deploy gate]
  end

  subgraph Copilot[Copilot]
    C1[Implement and unit-test]
  end

  subgraph PostImpl[Post-Implementation Validators]
    V1[Security intent code review]
  end

  subgraph DeployAndRun[Deploy and Runtime Validators]
    D1[Deploy to dev or preprod]
    V2[E2E and performance validation]
  end

  subgraph Review[Deploy Decision]
    R2[Ready to deploy]
  end

  subgraph Outcome[Outcome]
    O1[Deploy flow]
    O2[Closed]
  end

  I1 -->|squad| A1
  A1 -->|squad:lead + go:needs-research| L1
  A1 -->|squad:copilot + go:needs-research| A2

  L1 -->|go:no| L5
  L1 -->|hotfix| L4
  L1 -->|human:design-review or human:scope-validate| H1
  H1 -->|go:scope-approved + go:design-approved| L2

  A2 -->|squad:copilot| C1
  L2 -->|squad:copilot| C1
  L4 -->|hotfix + squad:copilot| C1

  C1 -->|squad:reviewer + go:review-ready| V1
  V1 -->|go:review-failed| C1
  V1 -->|review passed| D1
  D1 -->|deploy complete| V2
  V2 -->|go:review-failed| C1
  V2 -->|go:skip-human-validation pre-set| R2
  V2 -->|human:deploy-validate| H2
  H2 -->|go:deploy| R2
  H2 -->|go:review-failed| C1
  R2 -->|go:deploy| O1
  L5 -->|close| O2

  %% Bright path coloring by transition family
  %% squad routing paths
  linkStyle 0,1,2,6,7,8 stroke:#ff2bd6,stroke-width:3px,color:#ff2bd6
  %% go decision and approval paths
  linkStyle 3,4,5,9,13,16,18 stroke:#ff7a00,stroke-width:3px,color:#ff7a00
  %% validator and deploy handoffs
  linkStyle 10,11,12,14,15 stroke:#00c2ff,stroke-width:3px,color:#00c2ff
  %% human deploy gate path
  linkStyle 17 stroke:#00d26a,stroke-width:3px,color:#00d26a
  %% close path
  linkStyle 19 stroke:#9aa0a6,stroke-width:3px,color:#9aa0a6
```

### STD-2: Exception Loops (Compact)

```mermaid
flowchart TB
  subgraph Copilot[Copilot]
    C1[Implement]
    C2[Ask question]
    C3[Continue]
  end

  subgraph Auto[Automation]
    A1[Set human:needs-info]
    A2[Clear human:needs-info and resume]
  end

  subgraph Human[Human Gate]
    H1[Answer question]
  end

  subgraph Review[Reviewer CI]
    R1[Validation review]
    R2[Mark failed]
  end

  subgraph Lead[Lead]
    L1[Re-route fix]
  end

  C1 -->|human:needs-info| C2
  C2 -->|human:needs-info| A1
  A1 -->|notify owner| H1
  H1 -->|answer in issue| A2
  A2 -->|squad:copilot| C3
  C3 -->|ready for review| R1

  C1 -->|ready for review| R1
  R1 -->|go:review-failed| R2
  R2 -->|reopen fix loop| L1
  L1 -->|go:review-failed + squad:copilot| C1

  %% Bright path coloring
  %% needs-info loop
  linkStyle 0,1,2,3,4 stroke:#00c2ff,stroke-width:3px,color:#00c2ff
  %% normal review handoff
  linkStyle 5,6 stroke:#00d26a,stroke-width:3px,color:#00d26a
  %% failure loop
  linkStyle 7,8,9 stroke:#ff3b30,stroke-width:3px,color:#ff3b30
```

### Primary Flow (Standard)

1. `squad` added
2. `squad-triage.yml` assigns `squad:*` and adds `go:needs-research`
3. Lead triage/research resolves unknowns
4. Transition to approval states (`go:scope-approved`, `go:design-approved`) based on scope
5. Route execution to `squad:copilot` or squad member
6. After implementation, run post-implementation validators (security, intent alignment, code review)
7. Deploy to validation environment (dev or preprod), then run E2E + performance checks
8. If `go:skip-human-validation` is pre-set, bypass human deploy gate; otherwise use `human:deploy-validate`
9. On successful decision -> `go:deploy`
10. On failure -> `go:review-failed` and correction loop

### Hotfix Flow

1. `squad` + prod/hotfix signals
2. `squad-triage.yml`/lead ensures `hotfix`
3. Lead hotfix triage and approval gate
4. Implement and validate hotfix path
5. Promote and backmerge per governance

### Copilot Q&A Wait/Resume Flow

1. Issue in `squad:copilot`
2. Copilot comment with question-like content
3. `squad-copilot-qa-loop.yml` adds `human:needs-info` and notifies owner
4. Owner replies in issue
5. `squad-copilot-qa-loop.yml` removes `human:needs-info` and re-assigns Copilot
6. Implementation resumes

## Additional Actors (Extensions)

### Expert Agents (security, performance, domain specialists)

- Pattern: add the member to `.squad/team.md`.
- Routing label: `squad:{member}` is created automatically by `sync-squad-labels.yml`.
- Integration point: Lead can route specific review/analysis steps to expert agents before returning work to implementation/review lanes.
- Typical examples:
  - `squad:security` for threat-model or permission boundary checks
  - `squad:performance` for load/perf profiling and optimization guidance

### Scribe

- Scribe is a background/documentation actor and normally does not gate label transitions.
- Scribe may record status and outcomes, but should not block implementation, validation, or promotion decisions.

### Human Gate Trigger Rule

- Any open `human:*` label means human intervention is required.
- Resolution model:
  - `human:needs-info` -> owner answer -> resume Copilot
  - `human:design-review` -> `go:design-approved`
  - `human:scope-validate` -> `go:scope-approved`
  - `human:deploy-validate` -> `go:deploy` (or `go:skip-human-validation`)

### Design Rework Loop (`go:changes-requested`)

`go:changes-requested` returns the issue to lead-owned design review:

1. Reviewer applies `go:changes-requested`.
2. `squad-state-transitions.yml` ensures `squad:lead` and `human:design-review` are active.
3. Lead updates design direction and requests a new `go:design-approved` decision.
4. On `go:design-approved`, `squad-state-transitions.yml` routes back to `squad:copilot`.

## Automatic vs Manual Responsibility Matrix

| Transition Type | Automatic | Manual |
|---|---|---|
| Initial squad triage | Yes (`squad-triage.yml`) | Optional override by lead/owner |
| Member assignment from `squad:*` | Yes (`squad-issue-assign.yml`) | Manual reassign by label swap |
| Copilot PR merge progression | Yes (`squad-copilot-delivery-loop.yml` arms auto-merge for non-draft Copilot PRs) | Optional reviewer intervention |
| `go:*` exclusivity | Yes (`squad-label-enforce.yml`) | N/A |
| `release:*`, `type:*`, `priority:*`, `human:*` exclusivity | Yes (`squad-label-enforce.yml`) | N/A |
| Research hold (`go:needs-research`) | Yes (default) / manual hold | Lead/owner resolves and transitions |
| Design approval handoff (`go:design-approved`) | Yes (`squad-state-transitions.yml` routes to `squad:copilot` and assigns coding agent) | Human applies approval label |
| Design rework (`go:changes-requested`) | Yes (`squad-state-transitions.yml` restores `squad:lead` + `human:design-review`) | Human/reviewer applies changes-requested label |
| Post-merge deploy outcome (`Deploy to Dev` / `Deploy to Preprod`) | Yes (`squad-copilot-delivery-loop.yml` applies `go:review-ready` + `human:deploy-validate` on success, or `go:review-failed` on failure; if `go:skip-human-validation` is present, applies `go:review-ready` + `go:deploy`) | N/A |
| Review-ready deploy gate (`go:review-ready`) | Yes (retained via `squad-state-transitions.yml` for manual label path) | Human/reviewer can apply review-ready manually |
| Skip-human path (`go:skip-human-validation`) | Yes (`squad-state-transitions.yml` clears human gate and adds `go:deploy`) | Human applies skip label |
| Review failure loop (`go:review-failed`) | Yes (`squad-state-transitions.yml` routes back to `squad:copilot`) | Human/reviewer applies failure label |
| PR validation/check failure on Copilot branch | Yes (`squad-copilot-delivery-loop.yml` workflow-run recovery applies `go:review-failed`, posts failure summary, and tags `@copilot` to continue automatically) | Optional human override/comment |
| Deploy decision (`go:deploy`) | Yes (`squad-state-transitions.yml` closes non-prod issues or triggers production workflow) | Human/reviewer applies deploy label |
| Copilot wait/resume (`human:needs-info` loop) | Yes (`squad-copilot-qa-loop.yml`, and `squad-state-transitions.yml` for lead-phase clarification) | Owner replies to resume |
| Copilot inactivity visibility (assigned but quiet) | Yes (`squad-heartbeat.yml` stall-watch posts owner-mentioned alert comments with cooldown) | Optional owner nudge to wake Copilot |

## Workflow Label Inventory (Cleanup Safe List)

This inventory is derived from current workflow behavior and label-sync automation. Do not delete these labels unless workflows and this document are updated in the same change.

### Required Labels (Directly Used by Workflow Logic)

- `squad`
- `squad:copilot`
- `squad:{member}` (dynamic from roster)
- `go:needs-research`
- `go:yes`
- `go:no`
- `go:scope-approved`
- `go:design-approved`
- `go:review-ready`
- `go:skip-human-validation`
- `go:deploy`
- `go:review-failed`
- `go:changes-requested`
- `hotfix`
- `env:prod`
- `release:*` (at minimum one target or `release:backlog`)
- `type:*`
- `priority:*`
- `human:needs-info`
- `human:design-review`
- `human:scope-validate`
- `human:deploy-validate`

### Managed By Label Sync (Should Also Be Kept)

- `env:dev`
- `release:v0.4.0`
- `release:v0.5.0`
- `release:v0.6.0`
- `release:v1.0.0`
- `release:backlog`
- `type:feature`
- `type:enhancement`
- `type:bug`
- `type:spike`
- `type:docs`
- `type:chore`
- `type:epic`
- `priority:p0`
- `priority:p1`
- `priority:p2`
- `bug`
- `feedback`

### Legacy Compatibility (Do Not Recreate, But Recognize)

- `go:hotfix` is still read by triage/heartbeat as a backward-compatibility signal; `hotfix` is the canonical current label.

## Maintenance Contract (Required)

This document must be updated in the same change whenever label-state behavior changes in any of these files:
- `.github/workflows/squad-*.yml`
- `.github/workflows/sync-squad-labels.yml`
- `.squad/**/*.md`

Canonical path for all repos: `docs/shared/process/SQUAD_LABEL_STATE_MACHINE.md`.

If behavior changes and this document is not updated, workflow policy should fail the change.

## Last Updated

- 2026-03-19
- Enabled scheduled Ralph heartbeat and added Copilot stall-watch alerts in `squad-heartbeat.yml` to surface assigned-but-inactive `squad:copilot` issues via owner-mentioned comments.
- 2026-03-19
- Added automatic Copilot PR validation workflow-run failure recovery in `squad-copilot-delivery-loop.yml`: failed validation runs now auto-apply `go:review-failed`, post failure context on the linked issue, and explicitly tag `@copilot` to continue without manual wake-up.
- 2026-03-18
- Added `squad-copilot-delivery-loop.yml` for Copilot PR auto-merge arming and deployment outcome sync to `go:review-ready`/`go:review-failed`.
- Clarified that for dev/non-prod flow, successful deployment transitions to `human:deploy-validate` via `go:review-ready` automation.
- 2026-03-18
- Updated deploy outcome mapping: `squad-copilot-delivery-loop.yml` now applies `human:deploy-validate` directly on success (or `go:deploy` when `go:skip-human-validation` is set), avoiding chained workflow-trigger dependency.
- 2026-03-18
- Added `squad-state-transitions.yml` as transition adapter for design approval/rework loops, deploy gates, skip-human-validation path, and close-on-dev deploy behavior.
- Updated ownership and automation-boundary sections to reflect workflow-driven state transitions.
- 2026-03-13
- Added workflow-derived label inventory and documented missing namespaces/labels: `env:*`, `release:*`, `type:*`, `priority:*`, `go:changes-requested`, high-signal labels (`bug`, `feedback`), and legacy `go:hotfix` compatibility note.
- 2026-03-15
- Added automated design/scope rework loop for `go:changes-requested`: capture and clear active `human:design-review`/`human:scope-validate`, reassign Copilot for revision, then restore the correct human gate and clear `go:changes-requested` after revised proposal comment.
- 2026-03-13
- `squad-label-enforce.yml` now auto-posts issue-level transition summaries for `go:review-ready` and `go:review-failed`/`go:changes-requested`, including best-effort linked PR and failed-check context.
- 2026-03-13
- Guard workflows updated: `squad-state-doc-guard.yml` requires `pull-requests:read` for PR file enumeration and state-governance checks.
- 2026-03-12
- Includes Copilot Q&A wait/resume automation state (`squad-copilot-qa-loop.yml`)
