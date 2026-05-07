# Contract Validation - issue-960-contract-baseline

## Scope
- Issue/PR: #960
- Files checked:
  - docs/shared/Specifications/README.md
  - docs/shared/Specifications/generated/runtime-contract-baseline/README.md
  - docs/shared/Specifications/generated/runtime-contract-baseline/inventory.manifest.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/openapi/account-v1.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/openapi/admin-v1.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/openapi/integration-v1.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/openapi/traction-v1.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/asyncapi/all.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/asyncapi/integration.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/asyncapi/billing.json
  - docs/shared/Specifications/generated/runtime-contract-baseline/asyncapi/notification.json
  - scripts/contracts/Export-ContractBaseline.ps1
  - package.json

## Contract Impact
- Contract impact: none
- Endpoints reviewed:
  - GET /account/api/v1/openapi/v1.json
  - GET /admin/api/v1/openapi/v1.json
  - GET /integration/api/v1/openapi/v1.json
  - GET /traction/api/v1/openapi/v1.json
  - GET /admin/api/v1/contracts/asyncapi?lambda=all
  - GET /admin/api/v1/contracts/asyncapi?lambda=integration
  - GET /admin/api/v1/contracts/asyncapi?lambda=billing
  - GET /admin/api/v1/contracts/asyncapi?lambda=notification

## Verification
- Request payload unchanged: yes
- Response payload unchanged: yes
- Validation/error behavior unchanged: yes
- Spec references:
  - docs/shared/Specifications/README.md
  - .github/COPILOT_RULES.md

## Notes
- Issue 960 was completed by adding a tracked baseline export workflow around the existing runtime contract endpoints rather than redesigning those endpoints.
- `npm run contracts:export` and `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/contracts/Export-ContractBaseline.ps1` both resolve the approved baseline inventory.
- Coaching runtime contracts are intentionally excluded from this baseline because they are owned by PurposePath_AI and remain canonical in that separate repository/runtime surface.
- Billing and notification async contract artifacts are intentionally exported through the Admin async contract endpoint because that is the currently approved runtime exposure.