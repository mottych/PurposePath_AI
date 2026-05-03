# Contract Validation - issue 1052 billing confirm-change no contract change

## Scope
- Issue: #1052
- Files checked:
  - Services/PurposePath.Account.Lambda/Controllers/BillingOwnerController.cs
  - PurposePath.Application/Services/BillingOwnerWorkflowService.cs
  - PurposePath.Infrastructure/Repositories/DynamoDbBillingPaymentRepository.cs
  - infrastructure/pulumi/Program.cs

## Contract Impact
- Contract impact: none
- Endpoints reviewed:
  - POST /account/api/v1/billing/subscription/confirm-change

## Verification
- Request payload unchanged: yes
- Response payload unchanged: yes
- Validation/error behavior unchanged by source: yes
- Spec references:
  - docs/shared/Specifications/validation/README.md

## Notes
- Live contract source previously reviewed in triage: https://api.dev.purposepath.app/account/api/v1/openapi/v1.json
- The issue was caused by dev infrastructure drift: the required DynamoDB table `purposepath-billing-payments-dev` was missing even though the shared Pulumi program already defined `billing-payments` for each stack.
- The repair was applied through the owning source-controlled infrastructure path with `pulumi up --stack dev` in `infrastructure/pulumi`, which created the missing table without changing controller, DTO, validator, status-code, or response-shape behavior.
- Post-repair validation confirmed the table exists and is `ACTIVE`, and a follow-up `pulumi preview --stack dev` reported `123 unchanged`.
- The follow-on charge-path hardening keeps `POST /account/api/v1/billing/subscription/confirm-change` on its existing `200` payment-result contract by routing charge-boundary exceptions through the already-supported `failed` payment semantic instead of surfacing a generic controller `500` after the pending payment has been persisted.
- No request fields, response fields, documented endpoint metadata, or controller mappings changed as part of the charge-path hardening slice.