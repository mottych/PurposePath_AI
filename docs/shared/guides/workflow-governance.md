# Workflow and Governance Standards

## Objective

Define how changes are planned, executed, reviewed, and closed.

This guide is repository-agnostic. Repository-specific implementation rules (for example language/framework architecture constraints) must be defined in local guides under `docs/local/guides/`.

## Mandatory Control Rules

- Never commit directly to `dev` or `master`.
- Never use git stash in normal workflow (`git stash`, `pop`, `apply`, `clear`).
- Keep one issue per branch; do not carry unrelated changes.
- Before switching branches, working tree must be clean (`git status --short`).
- Before starting a new issue, stash list must be empty.

## Work Intake

- Every implementation should be tied to a GitHub issue.
- Use issue labels/states to reflect progress.
- Keep status in issue comments instead of ad-hoc status documents.

## Step 1: Plan (Mandatory)

### Branch Check
1. For standard development issues:
	- `git checkout dev && git pull origin dev`
2. For production issues/hotfixes:
	- `git checkout master && git pull origin master`
3. Resolve conflicts before continuing.
4. Confirm clean state:
	- `git stash list` is empty.
	- `git status --short` is clean.

### Review and Approval
1. Read the issue fully and confirm scope.
2. Review related code, standards, and relevant specifications.
3. Create an implementation plan broken into small steps.
4. If ambiguity exists, ask for clarification and pause execution.
5. Present plan and wait for approval before coding.
6. Post approved plan as an issue comment with:
	- Issue Summary
	- Code References
	- Documentation References
	- Implementation Steps
	- Acceptance Criteria
	- Testing Plan
	- Assumptions

## Step 2: Create

### Development Issue Path
1. Create feature branch from `dev`:
	- `git checkout -b feature/issue-{NUMBER}-{description}`
2. Add `in-progress` label.
3. Implement according to the repository local architecture and coding guides.
4. Mandatory alignment check:
	- Ensure boundary rules from local guides are followed.
	- Ensure no layer violations are introduced.
5. If alignment/spec deviation is discovered, stop and raise correction path.

### Production Issue Path
1. Create hotfix branch from `master`:
	- `git checkout -b hotfix/issue-{NUMBER}-{description}`
2. Push branch immediately:
	- `git push -u origin hotfix/issue-{NUMBER}-{description}`
3. Add `in-progress` label.
4. Implement minimal-risk service restoration changes.

## Step 3: Test and Quality Gates

1. Build using the repository standard build command.
2. Fix all warnings and errors.
3. Run repository-required tests for affected scope and CI-required scope.
4. Ensure all required tests pass.
5. Remove temporary code, data, and files.
6. Update docs/spec/runbooks when behavior or workflow changes.

## Step 4: Deploy and Merge

### Development Issue Path
1. Stage and commit:
	- `git add -A`
	- `{type}(#{issue}): {description}`
2. Merge to `dev`:
	- `git checkout dev`
	- `git pull origin dev`
	- `git merge --no-ff feature/issue-{NUMBER}-{description}`
	- `git push origin dev`
3. Verify deployment workflow success.

### Production Issue Path
1. Validate in preprod first (mandatory).
2. Open PR `hotfix/* -> master` after successful preprod validation.
3. Promote same validated commit/artifact to production.
4. Complete merge-down sequence:
	- `master -> staging -> dev`

## Step 5: Close Issue

1. Delete branch after successful deployment/merge.
2. Post issue summary including root cause, fix, and validation evidence.
3. Remove `in-progress` label.
4. Close issue with state reason `completed`.

## Branching and PR

- Start feature branches from `dev`.
- Use issue-linked commit messages (for example `feat(#123): add endpoint`).
- Open PRs with clear scope, risks, and validation notes.

## Spec and Contract Guardrails

- Relevant specification is the source of truth for API contracts.
- Do not change endpoint contract (URL/method/payload/error format) without explicit approval.
- If code differs from approved spec, fix code to match spec by default.
- If spec is incomplete or ambiguous, stop and request clarification.
- If spec change is required, open a spec-change path and wait for approval.

## Quality Gates

- Build must pass without errors.
- Tests must pass for touched scope and required CI scope.
- Security and governance checks must pass before merge.

## Done Criteria

- Code merged via reviewed PR.
- Issue updated and closed with summary.
- Temporary artifacts removed.
- Relevant docs updated or linked.

## Cross References

- Deployment release policy: `docs/shared/guides/deployment-standards.md`
- Agent behavior and escalation: `docs/shared/guides/agent-operation-standard.md`
- Repository local architecture and coding rules: `docs/local/guides/`
