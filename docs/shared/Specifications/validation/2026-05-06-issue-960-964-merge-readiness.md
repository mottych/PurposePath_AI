# Merge Readiness - Issue 960 Through 964

## Current Branch State
- Branch: `feature/issue-960-openapi-asyncapi-baseline`
- Default branch: `dev`
- Divergence from `dev` at time of validation: `0 ahead / 0 behind`
- PR status: no open PR exists for this branch
- Important: all issue 960-964 work is currently uncommitted local workspace state

## Completed Branch-Level Work
- Runtime contract baseline export workflow added for issue 960.
- Generated runtime baseline artifacts added under `docs/shared/Specifications/generated/runtime-contract-baseline/`.
- Shared spec/governance cleanup completed for issues 962 and 963.
- Executable governance validation added for issue 964.
- Issue 961 verified as already satisfied by existing code-first OpenAPI generation and current exported runtime artifacts.

## Validation Evidence

### Contract Validation
- `npm run contracts:audit` -> pass
- `npm run contracts:validate` -> pass

### Solution Validation
- `build-solution` task -> pass
- solution test execution -> pass (`3081 passed / 0 failed`)

### Workspace Health
- VS Code problems check -> no current file errors

## Known Non-Blocking Warnings
- Existing `NU1902` warnings remain on Pulumi infrastructure projects for OpenTelemetry packages.
- These warnings did not block build or tests and were not introduced by the issue 960-964 contract-governance changes.

## Files Driving This Merge
- `package.json`
- `scripts/contracts/Export-ContractBaseline.ps1`
- `scripts/contracts/Test-ContractGovernance.ps1`
- `scripts/contracts/Validate-ContractBaseline.ps1`
- `docs/shared/Specifications/README.md`
- `docs/shared/Specifications/api-fe/common-patterns.md`
- `docs/shared/guides/api-naming-conventions.md`
- `docs/shared/guides/billing-first-time-enable.md`
- `docs/shared/Requirements/unified-email-epic-issue-templates.md`
- `docs/validation/billing-rollout-validation-matrix.md`
- `docs/shared/Specifications/generated/runtime-contract-baseline/`
- `docs/shared/Specifications/validation/2026-04-28-issue-960-contract-baseline.md`
- `docs/shared/Specifications/validation/2026-05-06-issues-961-964-contract-governance.md`

## Remaining Workflow Gates
1. Create a commit containing the validated local workspace changes.
2. Open a PR from `feature/issue-960-openapi-asyncapi-baseline` into `dev`.
3. Merge into `dev` through the approved workflow.
4. Capture deployed `dev` validation / QA evidence.
5. Complete Human Gate 2 after deployment evidence exists.
6. Only then close the issues and delete the branch.

## Constraint
- This repository's Squad workflow does not allow declaring completion, closing the issues, or deleting the branch from issue-branch evidence alone.