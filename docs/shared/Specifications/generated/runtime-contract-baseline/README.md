# Runtime Contract Baseline

This folder stores tracked baseline exports of the runtime-generated contract endpoints for PurposePath API services.

These files are not the contract source of truth.

- Canonical source of truth: deployed runtime OpenAPI and AsyncAPI endpoints.
- Purpose of this folder: provide a version-controlled baseline snapshot, inventory manifest, and reproducible export workflow for issue 960 and follow-on validation work.

## Artifact Location

- Baseline root: `docs/shared/Specifications/generated/runtime-contract-baseline/`
- Inventory manifest: `docs/shared/Specifications/generated/runtime-contract-baseline/inventory.manifest.json`
- OpenAPI exports: `docs/shared/Specifications/generated/runtime-contract-baseline/openapi/`
- AsyncAPI exports: `docs/shared/Specifications/generated/runtime-contract-baseline/asyncapi/`

## Generation Commands

Default dev export:

```powershell
npm run contracts:export
```

Custom base URL export:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/contracts/Export-ContractBaseline.ps1 -BaseUrl "https://api.staging.purposepath.app"
```

Dry-run export plan:

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/contracts/Export-ContractBaseline.ps1 -WhatIf
```

## Inventory Rules

- HTTP contract exports are mirrored directly from the existing runtime `/openapi/v1.json` endpoints.
- Async contract exports are mirrored directly from the existing Admin `/contracts/asyncapi` endpoints.
- Billing and notification async surfaces are intentionally exported through the Admin async contract endpoint because that is the currently approved runtime exposure.
- Coaching runtime contracts are intentionally excluded because they are owned by PurposePath_AI and remain canonical in that separate repository/runtime surface.
- Realtime WebSocket behavior is not exported in this baseline because it is not currently represented by the OpenAPI or Admin AsyncAPI runtime endpoints.