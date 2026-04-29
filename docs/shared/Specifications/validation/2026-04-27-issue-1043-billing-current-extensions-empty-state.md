# Contract Validation - issue 1043 billing current/extensions empty state

## Scope
- Issue: #1043
- Files checked:
  - Services/PurposePath.Account.Lambda/Controllers/BillingOwnerController.cs
  - PurposePath.Application/Services/BillingOwnerWorkflowService.cs
  - PurposePath.Infrastructure/Repositories/DynamoDbBillingSubscriptionRepository.cs
  - Tests/PurposePath.Account.Lambda.Tests/Controllers/BillingOwnerControllerTests.cs
  - Tests/PurposePath.Application.Tests/Services/BillingOwnerWorkflowServiceTests.cs

## Contract Impact
- OpenAPI metadata now explicitly documents 401, 403, and 500 responses for the touched read endpoints.
- No route change and no error-contract change to represent missing billing state as 404.
- Endpoints reviewed:
  - GET /account/api/v1/billing/subscription/current
  - GET /account/api/v1/billing/subscription/extensions

## Verification
- Missing current subscription is returned as a successful empty-state payload.
- Missing extensions are returned as empty collections.
- Billing subscription reads now use strongly consistent DynamoDB scans so a just-confirmed plan is visible to immediate follow-up `current` and `extensions` reads.
- Runtime endpoint-not-found remains distinct from absent billing state.

## Notes
- Live contract source reviewed: https://api.dev.purposepath.app/account/api/v1/openapi/v1.json
- Confirm-change code was reviewed separately. The likely cause of the original post-confirm miss was eventual consistency in the subscription repository scan path, which is now mitigated by strongly consistent reads.