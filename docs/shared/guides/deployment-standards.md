# Deployment Standards

## Objective

Define required deployment behavior and infrastructure change policy.

This guide is repository-agnostic. Repository-specific deployment commands, stack details, and environment tooling belong in local docs.

## IaC Policy

- Use the repository-approved IaC system as the source of truth for infrastructure changes.
- Do not create, update, or delete production infrastructure manually in cloud consoles/CLI.
- Infrastructure definitions must be versioned in the repository.

## Operational Constraints

- Default delivery path is GitHub CI/CD workflows.
- Local/manual deployment is exception-only and must be justified in issue/PR notes.
- Never create/update/delete AWS resources manually outside IaC and workflows.

## Environment Flow

- `dev` for continuous integration and early validation.
- `staging` for release candidate validation.
- `master` for production release.

## Production Hotfix Promotion Flow (Mandatory)

1. Start from `master` on a `hotfix/*` branch.
2. Push `hotfix/*` to trigger preprod deployment workflow.
3. Validate in preprod before any production promotion.
4. Promote the same validated commit/artifact to production (no rebuild drift).
5. If preprod validation fails, fix in hotfix branch and repeat validation.
6. After production success, merge-down in sequence:
	- `master -> staging -> dev`

## Deployment Requirements

- CI workflows are the default deployment path.
- Manual deployment is exception-only and must be documented in the issue/PR.
- Rollback path must be known before production release.

## Preprod Validation Controls

- Health checks and targeted regression checks are required.
- Scheduled workloads (billing/integration) must be environment-toggle controlled.
- Secrets sync/bootstrap and seed operations must be idempotent.
- Do not proceed to production until preprod validation is successful and confirmed.

## Rollback and Incident Handling

- Rollback path must be documented and executable before production deployment.
- If production promotion fails, execute rollback playbook immediately.
- Record failure, rollback decision, and follow-up remediation issue.

## Pre-Release Checks

- Build and test gates are green.
- Required secrets/config are present and validated.
- Migration or data-impact risks are documented.

## Cross References

- Delivery workflow and quality gates: `docs/shared/guides/workflow-governance.md`
- Repository-specific deployment details: local deployment docs under `docs/local/`
