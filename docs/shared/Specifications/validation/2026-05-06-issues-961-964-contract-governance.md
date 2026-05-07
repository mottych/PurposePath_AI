# Contract Governance Closure - Issues 961-964

## Scope
- Issues: #961, #962, #963, #964
- Epic context: runtime contract migration and thin-spec governance follow-on to epic #959

## Outcome Summary
- Issue 961: verified complete in the current codebase/runtime outputs.
- Issue 962: completed by removing remaining contract-heavy content from shared specification guidance.
- Issue 963: completed by retargeting live documentation references from thin spec files to runtime OpenAPI sources.
- Issue 964: completed by adding executable contract-governance validation and a composite validation entry point.

## Issue 961 Verification

Runtime OpenAPI generation is already configured in code for all repo-owned HTTP surfaces:
- Account Lambda exposes `openapi/{documentName}.json` and registers `AddSwaggerGen` with XML comments and bearer security definition.
- Admin Lambda exposes `openapi/{documentName}.json` and registers `AddSwaggerGen` with XML comments and bearer security definition.
- Integration Lambda exposes `openapi/{documentName}.json` and registers `AddSwaggerGen` with XML comments plus bearer/service-auth security definitions.
- Traction Lambda exposes `openapi/{documentName}.json` and registers `AddSwaggerGen` with XML comments and bearer security definition.

Tracked runtime baseline exports confirm the generated OpenAPI documents already include:
- operation summaries
- parameter descriptions
- request body descriptions
- response descriptions/status documentation
- security scheme declarations

Representative evidence was confirmed from the generated runtime baseline files under `docs/shared/Specifications/generated/runtime-contract-baseline/openapi/`.

## Issue 962 Changes

The remaining shared specification document with contract-shaped duplication, `docs/shared/Specifications/api-fe/common-patterns.md`, was reduced to a non-contract guide.

Removed from that file:
- direct endpoint inventory guidance for auth flows
- explicit token-refresh endpoint phrasing as contract source
- duplicated health endpoint route/payload/status sections

Retained in that file:
- shared client behavior patterns
- lifecycle expectations
- data-model conventions
- readiness/liveness semantic guidance

## Issue 963 Changes

Updated live documentation so contract truth points to runtime OpenAPI rather than thin spec files:
- `docs/shared/guides/api-naming-conventions.md`
- `docs/shared/guides/billing-first-time-enable.md`
- `docs/shared/Requirements/unified-email-epic-issue-templates.md`
- `docs/validation/billing-rollout-validation-matrix.md`

Per-service thin specs remain available only for non-contract workflow and semantic context.

## Issue 964 Validation Gates

Added executable validation assets:
- `scripts/contracts/Test-ContractGovernance.ps1`
- `scripts/contracts/Validate-ContractBaseline.ps1`
- npm scripts:
  - `npm run contracts:audit`
  - `npm run contracts:validate`

Validation behavior now includes:
- baseline manifest existence and JSON validity
- generated baseline artifact existence and JSON validity
- thin spec marker/canonical-source enforcement for repo-owned API spec files
- detection of legacy contract-doc guidance in live governance documents
- reproducibility check of the export workflow through `Export-ContractBaseline.ps1 -WhatIf`

## Validation Executed

- `npm run contracts:audit` → pass
- `npm run contracts:validate` → pass

## Contract Impact

- Contract impact: none
- Runtime endpoints remain the canonical source of truth.
- The work in issues 962-964 changes governance, references, and validation only; it does not change runtime contract shapes.