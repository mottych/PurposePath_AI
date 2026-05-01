# Contract Validation - issue 1051 billing audit display fields

## Scope
- Issue: #1051
- Files checked:
  - Services/PurposePath.Account.Lambda/Controllers/BillingOwnerController.cs
  - Services/PurposePath.Account.Lambda/DTOs/Responses/BillingOwnerResponses.cs
  - Services/PurposePath.Account.Lambda/Mappings/BillingOwnerMappingProfile.cs
  - PurposePath.Application/Results/Billing/BillingAdminResults.cs
  - PurposePath.Application/Services/BillingOwnerWorkflowService.cs
  - Tests/PurposePath.Account.Lambda.Tests/Controllers/BillingOwnerControllerTests.cs
  - Tests/PurposePath.Application.Tests/Services/BillingOwnerWorkflowServiceTests.cs

## Contract Impact
- Response contract changed additively for the owner billing audit endpoint.
- Endpoint reviewed:
  - GET /account/api/v1/billing/audit
- Added response fields per audit item:
  - `displayName`
  - `displayMessage`
  - `actorDisplayName`
  - `planDisplayName`
  - `paymentMethodLabel`

## Verification
- Route, HTTP method, pagination shape, and existing technical audit fields remain unchanged.
- New fields are additive and nullable-safe for backward compatibility.
- Owner audit shaping now resolves user-friendly actor names, plan names, and payment method labels from existing repositories and audit metadata.
- When enrichment cannot resolve a related entity, the endpoint falls back to plain-English text derived from the audit event and description.

## Notes
- Live contract source for runtime verification remains the code-first OpenAPI endpoint: https://dev.purposepath.app/account/api/v1/openapi/v1.json
- This change is intentionally limited to the account owner audit response. Admin audit contracts were not expanded in this issue.