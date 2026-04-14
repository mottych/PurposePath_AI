# Shared Specifications Index

## Purpose

`docs/shared/Specifications/` contains cross-repository API and integration specifications synchronized by the shared-docs workflow.

Deployed runtime contract endpoints are now the canonical contract source of truth:

- HTTP contracts: `https://{api-host}/{service}/api/v1/openapi/v1.json`
- Async contracts: `https://{api-host}/admin/api/v1/contracts/asyncapi?lambda={scope}`
- Thin docs in this folder remain synchronized for workflow, semantics, state, and operational context only.

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

### AI API Specifications

- Email insights contract (v1 pilot): `docs/shared/Specifications/ai-api/email-insights-api-contract.md`

## Working Rules

- Deployed OpenAPI/AsyncAPI endpoints are source of truth for endpoint/interface contracts.
- Specs in this folder are thin non-contract documents for workflow, semantics, and operational context.
- Contract changes must follow the specification change workflow and validate against the runtime endpoints for the affected environment.
- Keep section README/index documents updated when adding or moving files.

## Related References

- `docs/shared/guides/specification-change-guide.md`
- `docs/shared/guides/api-naming-conventions.md`
- `.github/COPILOT_RULES.md`
- `docs/shared/process/squad/workflow-governance.md`
