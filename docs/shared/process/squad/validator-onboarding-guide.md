# Squad Validator Onboarding Guide

This guide describes the minimum changes needed to add, remove, or rename a validator workflow without breaking Squad reroute automation.

## Why This Exists

Squad uses `.squad/workflow-config.json` as the validator source of truth, but GitHub `workflow_run` trigger lists are static YAML. This means both must stay aligned.

A drift guard in `squad-validator-chain.yml` now enforces alignment for:
- `.github/workflows/squad-validator-chain.yml`
- `.github/workflows/squad-copilot-delivery-loop.yml`

If they drift, the validator-chain workflow fails with an explicit mismatch message.

## Add A New Validator

1. Add the workflow name to `.squad/workflow-config.json`:
- `validatorChain.validators[]` as `{ "name": "<Workflow Name>", "enabled": true, "required": true|false }`
- `workflowRunTriggerAllowlist[]`

2. Add the exact same workflow name to `on.workflow_run.workflows` in both files:
- `.github/workflows/squad-validator-chain.yml`
- `.github/workflows/squad-copilot-delivery-loop.yml`

3. Keep templates in sync with active files:
- `.squad/templates/workflows/squad-validator-chain.yml`
- `.squad/templates/workflows/squad-copilot-delivery-loop.yml`

4. Push and verify:
- `Squad Validator Chain` succeeds.
- No drift error is reported.

## Remove Or Rename A Validator

1. Update `.squad/workflow-config.json` first.
2. Apply the same change in both active workflow trigger lists.
3. Mirror the same change to both template workflow files.
4. Push and verify `Squad Validator Chain` still passes.

## Naming Rules

- Workflow names are matched by display name, case-insensitive.
- Use exact workflow names to avoid confusion.
- Avoid duplicate names in config lists.

## Expected Failure Modes

If setup is incomplete, `Squad Validator Chain` fails with one of these patterns:
- Workflow trigger present in YAML but missing from config allowlist.
- Config allowlist entry missing from YAML triggers.
- Enabled validator missing from allowlist.

Treat those as configuration drift, not code defects.
