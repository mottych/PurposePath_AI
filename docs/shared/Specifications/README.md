# Shared Specifications Index

## Purpose

`docs/shared/Specifications/` contains cross-repository API and integration specifications synchronized by the shared-docs workflow.

Generated machine-readable API contracts are now the canonical contract source of truth:

- `docs/contracts/openapi/account.openapi.json`
- `docs/contracts/openapi/admin.openapi.json`
- `docs/contracts/openapi/integration.openapi.json`
- `docs/contracts/openapi/traction.openapi.json`
- `docs/contracts/asyncapi/integration.asyncapi.yaml`

## How to Add or Modify Specifications

Use the canonical workflow guide:

- `docs/shared/guides/specification-change-guide.md`

## Folder Map

- `api-fe/`: User-facing frontend API specifications.
- `api-admin/`: Admin portal API specifications.
- `ai-fe/`: AI/coaching integration specifications for frontend use.
- `ai-api/`: AI service API contracts and payload specifications.
- `ai-admin/`: AI/admin related specifications.
- `integration/`: Async and cross-system integration contracts.
- `archive/`: Superseded historical specs kept for traceability.

### Billing Specifications

- Thin workflow context (frontend): `docs/shared/Specifications/api-fe/billing-frontend-api-specification.md`
- Thin workflow context (admin): `docs/shared/Specifications/api-admin/billing-admin-api-specification.md`
- Legacy machine-readable migration source: `docs/shared/Specifications/api-fe/billing-backend-openapi.yaml`

### AI API Specifications

- Email insights contract (v1 pilot): `docs/shared/Specifications/ai-api/email-insights-api-contract.md`

## Working Rules

- OpenAPI/AsyncAPI artifacts under `docs/contracts/` are source of truth for endpoint/interface contracts.
- Specs in this folder are thin non-contract documents for workflow, semantics, and operational context.
- Contract changes must follow the specification change workflow and regenerate artifacts in `docs/contracts/`.
- Keep section README/index documents updated when adding or moving files.

## Related References

- `docs/shared/guides/specification-change-guide.md`
- `docs/shared/guides/api-naming-conventions.md`
- `.github/COPILOT_RULES.md`
- `docs/shared/process/squad/workflow-governance.md`
