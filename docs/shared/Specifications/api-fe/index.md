# PurposePath API-FE Specification Index

## Status

This index now tracks thin semantic specifications only.

## Canonical Contract Sources

For all endpoint-level contract details, use the deployed runtime contract endpoints:
- Account: `https://{api-host}/account/api/v1/openapi/v1.json`
- Admin: `https://{api-host}/admin/api/v1/openapi/v1.json`
- Integration: `https://{api-host}/integration/api/v1/openapi/v1.json`
- Traction: `https://{api-host}/traction/api/v1/openapi/v1.json`
- Async contracts: `https://{api-host}/admin/api/v1/contracts/asyncapi?lambda={scope}`

## Thin Spec Documents (Non-Contract Context)

- `./account-api.md`
- `./billing-frontend-api-specification.md`
- `./business-foundation-api.md`
- `./dashboard-service.md`
- `./org-structure-service.md`
- `./traction-service/actions-api.md`
- `./traction-service/alignment-api.md`
- `./traction-service/dashboard-reports-activities-api.md`
- `./traction-service/goals-api.md`
- `./traction-service/insights-api.md`
- `./traction-service/integration-service.md`
- `./traction-service/issues-api.md`
- `./traction-service/measure-data-api.md`
- `./traction-service/measure-links-api.md`
- `./traction-service/measures-api.md`
- `./traction-service/strategies-api.md`

## Authoring Rule

Do not duplicate request/response shapes, endpoint inventories, or status-code matrices in these thin docs. Keep only workflow/state/business semantics and operational notes that are not representable in OpenAPI/AsyncAPI.
