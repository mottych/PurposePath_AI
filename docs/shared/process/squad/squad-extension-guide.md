# Squad Extension Guide (SDK-First)

## Purpose

This guide defines the recommended way to extend Squad in this repository using the current Squad documentation model:
- SDK-first orchestration
- tool-driven state transitions
- HookPipeline-style governance boundaries
- lightweight GitHub workflow adapters

Use this guide before adding new labels, workflows, routing rules, or orchestration behavior.

## Principles

- Keep business transitions in Squad orchestration, not in GitHub workflow scripts.
- Treat `.squad/` and `squad.config.ts` as the source of truth.
- Keep `.github/workflows/squad-*.yml` focused on adapters:
  - label sync and exclusivity
  - assignment handoff
  - wait/resume notification loops
- Use CI guards to prevent drift back to workflow-side transition ownership.

## Where To Extend

### 1) Routing and Orchestration Logic

Primary files:
- `squad.config.ts`
- `.squad/skills/*/SKILL.md`
- generated `.squad/routing.md` and `.squad/agents/*/charter.md` (output only)

What belongs here:
- new state transition rules
- gate behavior (`go:*`, `human:*` progression)
- which agent owns which transition
- reviewer/quality guardrails tied to decisions

Workflow:
1. Edit `squad.config.ts` and/or relevant skills.
2. Run `squad build`.
3. Review generated `.squad/` files.
4. Run `squad doctor`.

### 2) Governance and Safety Controls

Primary mechanism:
- Hook-style enforcement boundaries and CI guard workflows.

Repository controls:
- `.github/workflows/squad-workflow-boundary-guard.yml`
- `.github/workflows/squad-state-doc-guard.yml`

What belongs here:
- preventing forbidden transition logic from moving into workflows
- requiring documentation updates when state logic changes
- enforcing boundary and documentation hygiene

### 3) Label Infrastructure

Primary files:
- `.github/workflows/sync-squad-labels.yml`
- `.github/workflows/squad-label-enforce.yml`

What belongs here:
- creating/updating label catalogs
- namespace mutual exclusivity (`go:`, `release:`, `type:`, `priority:`, `human:`)
- convenience automation (for example `release:backlog` when `go:yes` is applied)

What does not belong here:
- design/scope rework transitions
- parsing issue comments to reopen human gates
- business-state transitions that should be agent-driven

## Extension Patterns

### Add a New Label Namespace

1. Add labels to `.github/workflows/sync-squad-labels.yml`.
2. Add exclusivity/normalization in `.github/workflows/squad-label-enforce.yml` if needed.
3. Add transition semantics in:
   - `squad.config.ts`
   - `.squad/skills/*/SKILL.md`
4. Update `docs/shared/process/squad/SQUAD_LABEL_STATE_MACHINE.md`.
5. Run `squad build` and `squad doctor`.

### Add a New Transition (Example: new go gate)

1. Update routing/charter intent in `squad.config.ts`.
2. Update or create a skill in `.squad/skills/` for execution behavior.
3. Regenerate with `squad build`.
4. Keep GitHub workflow changes minimal and adapter-only.
5. Add/update CI boundary guards if transition could be reintroduced in workflow scripts.

### Add a New Agent Responsibility

1. Update `squad.config.ts` agent charter and routing rules.
2. Run `squad build`.
3. Verify generated `.squad/agents/*/charter.md` and `.squad/routing.md`.
4. Update state machine docs when lifecycle ownership changes.

## Health Validation Checklist

Run these commands after each extension:

```bash
squad build
squad doctor
squad status
```

Then validate repository consistency:
- State-machine doc reflects new behavior.
- Boundary guards still pass.
- Workflows remain adapter-only.

## Anti-Patterns

Avoid these patterns:
- Restoring human gates from workflow-side issue-comment parsing.
- Removing/adding `go:*` transition labels inside Q&A workflows.
- Encoding primary business state machine logic in `.github/workflows/squad-*.yml`.
- Editing generated `.squad/routing.md` directly instead of `squad.config.ts`.

## Repository-Specific Boundary

In this repo, the intended split is:
- Tool-first orchestration: `squad.config.ts` + skills + generated `.squad` artifacts.
- Workflow adapters only: triage trigger, assignment trigger, label sync/enforce, Q&A pause/resume.
- CI enforcement of this split: `squad-workflow-boundary-guard.yml`.

## References

- Squad README (SDK-first orchestration and tool model)
- Squad docs (`docs/sdk-first-mode.md`, migration guide)
- `docs/shared/process/squad/SQUAD_LABEL_STATE_MACHINE.md`
