# Contract Validation - issue 634 audit logs route no contract change

## Scope
- Issue/PR: #634 / #860
- Files checked:
  - Services/PurposePath.Admin.Lambda/Controllers/AuditLogsController.cs
  - Tests/PurposePath.Admin.Lambda.Tests/Controllers/AuditLogsControllerRouteTests.cs

## Contract Impact
- Contract impact: none
- Endpoints reviewed:
  - GET /audit-logs/action-types
  - GET /audit-logs/{id}

## Verification
- Request payload unchanged: yes
- Response payload unchanged: yes
- Validation/error behavior unchanged: yes
- Route contract unchanged from spec intent: yes (`id` is GUID-constrained per spec)
- Spec references:
  - docs/shared/Specifications/api-admin/admin-api-specification.md (Audit Logs section)

## Notes
- Change constrained the route template from `{id}` to `{id:guid}` to avoid literal path collision with `action-types`.
- This is a routing hardening fix that preserves the documented API contract and behavior.
