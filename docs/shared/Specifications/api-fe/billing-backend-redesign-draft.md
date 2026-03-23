# Backend Billing Redesign Draft

Version: 1.0  
Audience: Backend, Frontend, Product  
Status: Proposed design draft for review

## 1. Scope and Decisions

This document defines the backend redesign for plans, subscriptions, and billing based on the requirements in `docs/shared/Requirements/Plans and Subscriptions/plans-requirements.md`.

Hard decisions for this redesign:
- App-driven lifecycle is the source of truth for subscription state.
- Payment providers execute charges and send events, but provider state does not replace domain state.
- Provider webhooks are hosted by billing service provider endpoints, not in account API.
- Clean rewrite is preferred over legacy adaptation where model mismatch exists.
- No backward compatibility constraints for old subscription/billing endpoints.

## 2. Architecture Overview

```mermaid
flowchart LR
  subgraph apiHosts [APIHosts]
    accountApi[AccountAPI]
    adminApi[AdminAPI]
    billingWebhookApi[BillingProviderWebhookAPI]
  end

  subgraph appLayer [ApplicationLayer]
    catalogUC[CatalogUseCases]
    subscriptionUC[SubscriptionUseCases]
    billingUC[BillingCycleUseCases]
    entitlementUC[EntitlementUseCases]
    auditUC[AuditUseCases]
  end

  subgraph domainLayer [DomainLayer]
    planCatalog[PlanCatalog]
    tenantSubscription[TenantSubscription]
    billingPolicy[BillingPolicies]
    entitlementPolicy[EntitlementPolicies]
    auditLog[BillingAuditLog]
  end

  subgraph infraLayer [InfrastructureLayer]
    repositories[RepositoryAdapters]
    stripeGateway[StripeGateway]
    webhookParser[ProviderWebhookParsers]
    outbox[OutboxAndEventDispatcher]
    notificationGateway[NotificationGateway]
  end

  accountApi --> subscriptionUC
  accountApi --> entitlementUC
  adminApi --> catalogUC
  adminApi --> subscriptionUC
  billingWebhookApi --> billingUC

  catalogUC --> planCatalog
  subscriptionUC --> tenantSubscription
  billingUC --> billingPolicy
  entitlementUC --> entitlementPolicy
  auditUC --> auditLog

  appLayer --> repositories
  billingUC --> stripeGateway
  billingWebhookApi --> webhookParser
  appLayer --> outbox
  outbox --> notificationGateway
```

## 3. Canonical API Contract

Base URL shape:
- Account API: `{accountBaseUrl}/api/v1`
- Admin API: `{adminBaseUrl}/api/v1`
- Billing webhook API: `{billingBaseUrl}` (provider endpoints)

Shared conventions:
- JSON camelCase.
- Response envelope: `ApiResponse<T>`.
- Time values in UTC ISO-8601.
- Owner endpoints require tenant owner authorization.
- Admin endpoints require admin policy authorization.
- Mutating endpoints require `Idempotency-Key` for retry-safe execution.

### 3.1 Owner Billing Endpoints (Account API)

#### GET `/billing/subscription/current`
- Purpose: Return active subscription, lifecycle flags, next billing action, and selected schedule.
- Auth: Tenant owner only.
- Response shape (data):
  - `tenantId`, `subscriptionId`, `plan`, `status`, `isTrial`, `autoRenew`
  - `effectiveDate`, `terminationDate`, `inGracePeriod`, `gracePeriodEndDate`
  - `paymentSchedule`, `activeExtensions[]`, `nextChargePreview`

#### GET `/billing/plans/catalog`
- Purpose: Return published plans, schedules, extensions, and pricing overlays applicable to tenant.
- Auth: Any authenticated tenant user (read-only); non-owner still cannot mutate billing.
- Query:
  - `includeCurrentPlan=true|false`
  - `schedule=<scheduleCode>`
- Response:
  - `plans[]` with `featureSummary`, `limitsSummary`, `availableSchedules[]`, `availableExtensions[]`

#### POST `/billing/subscription/preview-change`
- Purpose: Dry-run plan/schedule/extension change with downgrade validation and cost summary.
- Auth: Tenant owner only.
- Request:
  - `targetPlanId`, `targetScheduleId`, `extensionSelections[]`, `discountCode`
- Response:
  - `effectiveMode` (`immediate` or `nextCycle`)
  - `lineItems[]` (charges, credits, extension deltas)
  - `totalDueNow`
  - `downgradeWarnings[]`
  - `blockingViolations[]`
  - `validationSnapshotId` (for confirm replay safety)

#### POST `/billing/subscription/confirm-change`
- Purpose: Execute change from a preview snapshot with payment authorization.
- Auth: Tenant owner only.
- Request:
  - `validationSnapshotId`, `paymentMethodToken`, `confirmationToken`
- Response:
  - `subscription`
  - `paymentResult` (`succeeded`, `requiresAction`, `failed`)
  - `receiptId` (if charged)

#### POST `/billing/subscription/cancel`
- Purpose: Disable auto-renew; subscription stays active until termination.
- Auth: Tenant owner only.
- Request:
  - `reason` (optional)
- Response:
  - updated subscription state (`autoRenew=false`)

#### POST `/billing/subscription/reactivate`
- Purpose: Re-enable auto-renew before termination date or recover during grace (if payment succeeds).
- Auth: Tenant owner only.
- Request:
  - `paymentMethodToken` (optional unless needed for immediate payment)
- Response:
  - updated subscription state

#### GET `/billing/subscription/extensions`
- Purpose: Return active extension selections and available extension catalog for current plan.
- Auth: Tenant owner only.

#### POST `/billing/subscription/extensions`
- Purpose: Add/update extension quantities; immediate prorated charge.
- Auth: Tenant owner only.
- Request:
  - `extensionSelections[]` (`extensionDefinitionId`, `quantity`)
- Response:
  - updated extension state, `totalDueNow`, optional `receiptId`

#### DELETE `/billing/subscription/extensions/{extensionSelectionId}`
- Purpose: Remove extension selection effective next billing cycle (no refund).
- Auth: Tenant owner only.
- Response:
  - `effectiveRemovalDate`

#### GET `/billing/payment-method`
- Purpose: Return masked method details and expiration status.
- Auth: Tenant owner only.
- Response:
  - `brand`, `last4`, `expMonth`, `expYear`, `isExpiringSoon`

#### POST `/billing/payment-method/setup-intent`
- Purpose: Create provider setup session/token for safe card update.
- Auth: Tenant owner only.
- Response:
  - provider-specific setup client token

#### POST `/billing/payment-method/confirm`
- Purpose: Confirm and attach payment method to tenant billing profile.
- Auth: Tenant owner only.
- Request:
  - provider confirmation payload/token
- Response:
  - updated masked method

#### GET `/billing/payment-history`
- Purpose: Return payment list for subscription.
- Auth: Tenant owner only.
- Query:
  - `page`, `limit`, `from`, `to`
- Response:
  - `items[]` with payment date, amount, period covered, method last4, status

#### GET `/billing/payment-history/{paymentId}/receipt`
- Purpose: Return receipt metadata and downloadable file URL.
- Auth: Tenant owner only.
- Response:
  - `receiptId`, `downloadUrl`, `expiresAtUtc`

#### GET `/billing/entitlements/effective`
- Purpose: Return effective features/limits after plan + extensions + overrides.
- Auth: Authenticated tenant user.

### 3.2 Admin Billing Endpoints (Admin API)

#### Feature sets
- `GET /admin/billing/feature-sets`
- `GET /admin/billing/feature-sets/{featureSetId}`
- `POST /admin/billing/feature-sets`
- `PATCH /admin/billing/feature-sets/{featureSetId}`
- `DELETE /admin/billing/feature-sets/{featureSetId}`

#### Plans
- `GET /admin/billing/plans`
- `GET /admin/billing/plans/{planId}`
- `POST /admin/billing/plans`
- `PATCH /admin/billing/plans/{planId}`
- `DELETE /admin/billing/plans/{planId}`
- `POST /admin/billing/plans/{planId}/publish`
- `POST /admin/billing/plans/{planId}/hide`
- `POST /admin/billing/plans/{planId}/set-trial`
- `POST /admin/billing/plans/{planId}/set-fallback`

#### Payment schedules
- `GET /admin/billing/payment-schedules`
- `POST /admin/billing/payment-schedules`
- `PATCH /admin/billing/payment-schedules/{scheduleId}`
- `DELETE /admin/billing/payment-schedules/{scheduleId}`

#### Extensions
- `GET /admin/billing/extensions`
- `POST /admin/billing/extensions`
- `PATCH /admin/billing/extensions/{extensionDefinitionId}`
- `DELETE /admin/billing/extensions/{extensionDefinitionId}`

#### Price tiers and discount codes
- `GET /admin/billing/price-tiers`
- `POST /admin/billing/price-tiers`
- `PATCH /admin/billing/price-tiers/{priceTierId}`
- `DELETE /admin/billing/price-tiers/{priceTierId}`
- `GET /admin/billing/discount-codes`
- `POST /admin/billing/discount-codes`
- `PATCH /admin/billing/discount-codes/{discountCodeId}`
- `DELETE /admin/billing/discount-codes/{discountCodeId}`

#### Tenant overrides and audit
- `POST /admin/billing/tenants/{tenantId}/overrides`
- `PATCH /admin/billing/tenants/{tenantId}/overrides/{overrideId}`
- `DELETE /admin/billing/tenants/{tenantId}/overrides/{overrideId}`
- `GET /admin/billing/tenants/{tenantId}/audit`

#### Billing settings
- `GET /admin/billing/settings`
- `PATCH /admin/billing/settings`
- Fields:
  - `retryDelayDays` (default 3)
  - `maxAutomaticAttemptsPerCycle` (fixed to 2 for this phase)
  - notification policy toggles required by legal/compliance

### 3.3 Provider Webhook Endpoints (Billing Service)

- `POST /billing/providers/stripe/webhooks`
- Reserved path pattern for future providers: `POST /billing/providers/{provider}/webhooks`

Rules:
- No account API webhook endpoints.
- Signature verification is provider-specific and mandatory.
- Webhook handlers are idempotent by provider event id.
- Webhook handlers append domain audit records and trigger internal commands only.

### 3.4 Error Contract

Standard error payload:
- `code` (stable machine code)
- `message` (human-readable)
- `details` (field errors or business diagnostics)
- `correlationId`

Billing-specific codes:
- `BILLING_OWNER_REQUIRED`
- `BILLING_PLAN_CHANGE_BLOCKED`
- `BILLING_PAYMENT_METHOD_REQUIRED`
- `BILLING_PAYMENT_FAILED`
- `BILLING_IDEMPOTENCY_CONFLICT`
- `BILLING_WEBHOOK_SIGNATURE_INVALID`
- `BILLING_WEBHOOK_EVENT_DUPLICATE`
- `BILLING_DISCOUNT_INELIGIBLE`
- `BILLING_PRICE_TIER_CONFLICT`

## 4. Domain Contexts, Aggregates, Invariants

### 4.1 Contexts

- Catalog context:
  - `FeatureSet`, `Plan`, `PaymentSchedule`, `PlanPrice`, `ExtensionDefinition`, `ExtensionPrice`, `PriceTier`, `DiscountCode`.
- Subscription context:
  - `TenantSubscription`, `SubscriptionExtensionSelection`, `SubscriptionOverride`.
- Billing context:
  - `BillingTransaction`, `InvoiceSnapshot`, `PaymentMethodSnapshot`, `ProviderCustomerLink`, `ProviderSubscriptionLink`.
- Audit context:
  - immutable `BillingAuditRecord`.

### 4.2 Core invariants

- Exactly one tenant owner per tenant.
- At most one active subscription per tenant for any time interval.
- Only one trial plan and one fallback plan can be designated globally at a time.
- Overrides are additive only; never reduce a base capability.
- Prices must resolve deterministically: discount code or tenant tier overlay, then base fallback.
- State transitions must be valid against lifecycle rules (no ad-hoc status jumps).
- Billing cycle calculations always use UTC.

### 4.3 Policy services

- `ProrationPolicyService`
- `DowngradeValidationPolicyService`
- `EntitlementResolutionPolicyService`
- `GraceAndFallbackPolicyService`
- `RetrySchedulingPolicyService`
- `DiscountEligibilityPolicyService`

### 4.4 Aggregate command and event boundaries

`PlanCatalog` aggregate commands:
- `CreateFeatureSet`
- `UpdateFeatureSet`
- `CreatePlan`
- `PublishPlan`
- `SetTrialPlan`
- `SetFallbackPlan`
- `DefineSchedulePrice`
- `DefineExtensionPrice`
- `CreatePriceTier`
- `CreateDiscountCode`

`PlanCatalog` domain events:
- `FeatureSetCreated`
- `PlanPublished`
- `TrialPlanDesignated`
- `FallbackPlanDesignated`
- `PriceTierDefined`
- `DiscountCodeActivated`

`TenantSubscription` aggregate commands:
- `AssignTrialSubscription`
- `PreviewPlanChange`
- `ConfirmPlanChange`
- `CancelAutoRenew`
- `ReactivateAutoRenew`
- `ApplyExtensionSelection`
- `RemoveExtensionSelection`
- `EnterGracePeriod`
- `ApplyFallbackPlan`
- `RecoverFromGrace`

`TenantSubscription` domain events:
- `SubscriptionActivated`
- `SubscriptionRenewed`
- `SubscriptionPlanChanged`
- `SubscriptionCancelled`
- `SubscriptionReactivated`
- `SubscriptionEnteredGrace`
- `SubscriptionRecoveredFromGrace`
- `SubscriptionFallbackApplied`
- `SubscriptionAccessBlocked`

`BillingAuditLog` aggregate commands:
- `AppendAuditRecord`

`BillingAuditLog` domain events:
- `AuditRecordAppended`

## 5. Billing Lifecycle and Orchestration

### 5.1 State machine

```mermaid
stateDiagram-v2
  [*] --> ActiveTrial
  ActiveTrial --> ActivePaid : payAndSelectPlan
  ActiveTrial --> InactiveGrace : trialExpiresNoSelection
  ActivePaid --> ActivePaidCancelled : cancelAutoRenew
  ActivePaidCancelled --> ActivePaid : reactivateBeforeTermination
  ActivePaid --> InactiveGrace : paymentFailedTwiceAndTerminationPassed
  ActivePaidCancelled --> InactiveExpired : terminationReached
  InactiveGrace --> ActivePaid : paymentRecovered
  InactiveGrace --> InactiveExpired : graceElapsedNoPayment
  InactiveExpired --> ActivePaid : newPaidEnrollment
```

### 5.2 Orchestrated jobs

- Month-start billing run (UTC day 1):
  - select due subscriptions for current date by schedule.
  - attempt charge for plan + active extensions.
  - persist transaction and append audit event.
  - emit notifications.
- Retry run:
  - execute first-failure retries after configurable delay.
  - max two automatic attempts per cycle.
- Grace transition run:
  - move to grace when eligibility rules match.
  - apply fallback or block access after grace end.
- Expiration warning jobs:
  - trial expiration notifications (7d and 1d).
  - schedule expiration reminders.
  - payment method expiration warning (14d).

Deterministic due-subscription selector:
- A subscription is due in month `M` when:
  - `autoRenew=true`
  - status is billable (`activePaid` or `inactiveGrace` recovery candidate)
  - `monthsBetween(anchorMonth, M) % scheduleMonths == 0`
- `anchorMonth` is the first full billing month after paid enrollment.
- First enrollment proration always covers enrollment date through month end in UTC.

Retry and grace timeline policy:
- Attempt 1 at due timestamp.
- Attempt 2 at `attempt1 + retryDelayDays`.
- If attempt 2 fails:
  - when `now >= terminationDateUtc`, transition to `inactiveGrace`.
  - compute `gracePeriodEndDate = terminationDateUtc + graceDays`.
- At grace end:
  - fallback plan exists: apply fallback subscription immediately.
  - fallback missing: mark tenant as access blocked and emit critical notification.

### 5.3 Proration and change logic

- Upgrade:
  - immediate plan switch.
  - charge delta now (`new prorated charge - current credit`).
- Downgrade:
  - schedule next-cycle activation.
  - no immediate charge/refund.
- Schedule-only change:
  - effective next cycle.
- Extension add:
  - immediate prorated charge.
- Extension remove:
  - effective next cycle, no refund.

Proration formula:
- `proratedAmount = fullPeriodPrice * (remainingDaysInCycle / totalDaysInCycle)`
- `deltaDueNow = max(0, proratedTarget + proratedExtensions - proratedCreditCurrent)`
- Downgrade where `proratedCreditCurrent > proratedTarget` never creates refund; credit is consumed by deferred effective date.

### 5.4 Downgrade enforcement outcomes

- If `activeUsers > maxUsers` then block plan change.
- If capacity features exceed target limits then warn and allow with deterministic disable policy:
  - keep first N by creation date.
  - disable remainder without deletion.
- Boolean/tier features change at effective date.
- Token consumables do not retrocharge; new cap enforced until next reset.

## 6. Provider Layer and Stripe Boundaries

### 6.1 Provider-neutral interfaces

Define provider-neutral contracts in domain/application:
- `IBillingProviderGateway`
- `IBillingWebhookVerifier`
- `IBillingWebhookTranslator`
- `IBillingPaymentMethodGateway`
- `IBillingReceiptGateway`

Provider-specific objects must stay in infrastructure.

Recommended interface surface (conceptual C#):

```csharp
public interface IBillingProviderGateway
{
    Task<ProviderChargeResult> ChargeAsync(ProviderChargeCommand command, CancellationToken ct);
    Task<ProviderSetupIntentResult> CreateSetupIntentAsync(ProviderSetupIntentCommand command, CancellationToken ct);
    Task<ProviderSubscriptionReference> EnsureCustomerAndSubscriptionAsync(ProviderSubscriptionCommand command, CancellationToken ct);
    Task<ProviderReceiptResult> GetReceiptAsync(ProviderReceiptQuery query, CancellationToken ct);
}

public interface IBillingWebhookVerifier
{
    Task<WebhookVerificationResult> VerifyAsync(string provider, IDictionary<string, string> headers, string rawBody, CancellationToken ct);
}

public interface IBillingWebhookTranslator
{
    Task<ProviderEventEnvelope> TranslateAsync(string provider, string rawBody, CancellationToken ct);
}
```

### 6.2 Stripe adapter responsibilities

- Convert internal billing commands to Stripe API calls.
- Verify Stripe signature for Stripe endpoint only.
- Translate Stripe events into internal `ProviderEvent` commands.
- Never expose Stripe SDK types outside infrastructure layer.

Stripe event normalization map:
- `invoice.payment_succeeded` -> `PaymentCaptured`
- `invoice.payment_failed` -> `PaymentFailed`
- `customer.subscription.updated` -> `ProviderSubscriptionStateChanged`
- `customer.subscription.deleted` -> `ProviderSubscriptionCancelled`
- `charge.dispute.created` -> `PaymentDisputeOpened`
- payment method update events -> `PaymentMethodUpdatedByProvider`

### 6.3 Webhook processing pipeline

1. Receive provider webhook on provider endpoint.
2. Verify signature.
3. Compute idempotency key (`provider + eventId`).
4. Store receipt if not processed.
5. Translate provider payload to internal event.
6. Dispatch application command.
7. Persist resulting domain updates + audit.
8. Mark processed.

## 7. Data, Idempotency, Audit, Reconciliation

### 7.1 Persistence model (Dynamo-oriented conceptual tables)

- `BillingPlanCatalog`
- `BillingSubscription`
- `BillingSubscriptionScheduleChanges`
- `BillingExtensionSelections`
- `BillingOverrides`
- `BillingDiscountCodes`
- `BillingPriceTiers`
- `BillingTransactions`
- `BillingReceipts`
- `BillingPaymentMethods`
- `BillingProviderLinks`
- `BillingProcessedProviderEvents`
- `BillingAuditLog`
- `BillingOutbox`

Recommended key design:

| Table | Partition Key | Sort Key | Purpose |
| --- | --- | --- | --- |
| BillingPlanCatalog | `CATALOG#<entityType>` | `<entityId>#<version>` | Immutable or versioned catalog entities |
| BillingSubscription | `TENANT#<tenantId>` | `SUB#<subscriptionId>` | Subscription aggregate snapshots |
| BillingTransactions | `TENANT#<tenantId>` | `TXN#<timestampUtc>#<transactionId>` | Payment attempts and outcomes |
| BillingPaymentMethods | `TENANT#<tenantId>` | `PM#<paymentMethodId>` | Masked method metadata only |
| BillingProviderLinks | `TENANT#<tenantId>` | `PROVIDER#<provider>#<linkType>` | Customer/subscription external references |
| BillingProcessedProviderEvents | `PROVIDER#<provider>` | `EVENT#<eventId>` | Webhook idempotency and replay barrier |
| BillingAuditLog | `TENANT#<tenantId>` | `AUDIT#<timestampUtc>#<auditId>` | Immutable event trail |
| BillingOutbox | `STREAM#billing` | `OUTBOX#<timestampUtc>#<eventId>` | Asynchronous event dispatch queue |

Suggested GSIs:
- `GSI1` on `BillingSubscription` for status scans by due month.
- `GSI2` on `BillingTransactions` for provider reference lookup.
- `GSI3` on `BillingAuditLog` for event type and date filtering.

### 7.2 Idempotency model

- API mutations:
  - key: `tenantId + endpoint + idempotencyKey`.
  - store request hash + response hash + TTL.
  - reject key reuse on payload mismatch.
- Webhooks:
  - key: `provider + providerEventId`.
  - exact-once command execution semantics by processed-event record.
- Jobs:
  - key: `jobType + period + tenantId` execution ledger.

Conflict behavior:
- Same key + same payload hash -> return cached success response.
- Same key + different payload hash -> return `409 BILLING_IDEMPOTENCY_CONFLICT`.
- Expired key beyond TTL -> treat as new request.

### 7.3 Audit schema

Fields:
- `id`, `timestampUtc`, `tenantId`
- `actorType` (`tenant_owner`, `admin`, `system`)
- `actorId`
- `eventType`
- `description`
- `beforeState`, `afterState`
- `metadata` (provider ids, failure reasons, proration details, correlation id)

### 7.4 Reconciliation jobs

- Provider reconciliation:
  - compare provider transactions/subscriptions to internal transactions/subscriptions.
  - produce discrepancy report and corrective commands.
- Stuck status reconciliation:
  - detect subscriptions with inconsistent lifecycle flags and repair via deterministic rule engine.

Operational thresholds:
- Critical alert: any reconciliation mismatch that changes access state.
- Warning alert: monetary mismatch under configured threshold.
- Daily reconciliation summary report persisted for auditability.

## 8. Test Strategy

### 8.1 Test layers

- Domain tests:
  - invariants, lifecycle transitions, proration math, downgrade rules.
- Application tests:
  - use-case orchestration, idempotency rules, event handling.
- Infrastructure tests:
  - provider adapters, webhook verification/translation, repository mapping.
- Contract tests:
  - endpoint request/response schemas and error code stability.
- End-to-end tests:
  - owner workflows, admin catalog changes, webhook replay, retry/grace/fallback.

### 8.2 Mandatory scenario matrix

- Registration to trial subscription.
- Trial expiration without conversion.
- Mid-cycle upgrade with immediate charge.
- Downgrade with over-limit warnings and deterministic disable.
- Billing retry flow (first fail, second fail, grace).
- Recovery from grace with successful payment.
- Fallback plan application.
- Cancel/reactivate before termination.
- Payment method expiring notification.
- Duplicate webhook replay ignored idempotently.

### 8.3 Quality gates before cutover

- Contract gate:
  - 100 percent pass on endpoint schema contract tests for owner/admin endpoints.
- Domain gate:
  - 100 percent pass on lifecycle transition and proration policy tests.
- Reliability gate:
  - webhook idempotency replay tested for at least 10 duplicate deliveries per event type.
  - scheduled job re-run safety validated for same cycle window.
- Data gate:
  - reconciliation mismatch rate below agreed threshold for two consecutive dry-run cycles.

## 9. Legacy Component Deprecation and Replacement

### 9.1 Remove or retire

- Account webhook endpoint:
  - `Services/PurposePath.Account.Lambda/Controllers/BillingWebhookController.cs`
- Payment-confirmation-only path:
  - `PurposePath.Infrastructure/BillingProviders/StripePaymentConfirmationHandler.cs`
- Stripe-coupled domain contracts:
  - `PurposePath.Domain/Services/IStripeService.cs`
  - Stripe-named parts of `PurposePath.Domain/Services/IWebhookProcessingService.cs`
- Tier-centric assumptions that do not map to new catalog model:
  - `PurposePath.Domain/Entities/SubscriptionTier.cs` (replace with plan catalog model)

### 9.2 Replace with

- Billing-service provider webhook controllers/handlers only.
- Provider-neutral interfaces in domain/application.
- New catalog/subscription model aligned to feature sets, schedules, extensions, tiers, and discounts.
- Unified billing orchestration use cases and jobs.

### 9.3 Cutover phases and rollback

Phase A: Foundation deploy (dark mode)
- Deploy new domain/application/infrastructure paths disabled by feature flags.
- Keep legacy reads/writes active.

Phase B: Shadow execution
- Execute new billing calculations in parallel without side effects.
- Persist shadow outputs for comparison only.

Phase C: Controlled write cutover
- Enable new write paths for a pilot tenant cohort.
- Webhooks routed only to new billing-service provider endpoints.
- Legacy webhook path returns hard failure to prevent split processing.

Phase D: Full cutover
- Expand to all tenants.
- Disable legacy billing mutation endpoints.

Phase E: Decommission
- Remove retired components and cleanup config/secrets/routes.

Rollback policy:
- If critical severity access regression or monetary mismatch is detected:
  - disable new write feature flags immediately.
  - continue reads from last consistent snapshots.
  - replay failed operations from idempotent request/event logs after fix.

## 10. Implementation Epics and Issue Breakdown

### Epic 1: API and contract foundation
- Define request/response schemas for all owner/admin/provider endpoints.
- Implement auth and error contract enforcement.
- Add idempotency middleware for mutation endpoints.

### Epic 2: Catalog and pricing domain rewrite
- Build feature set/plan/schedule/extension aggregates.
- Implement price tiers and discount code rules.
- Build admin CRUD endpoints and validation.

### Epic 3: Subscription lifecycle engine
- Build subscription aggregate and state machine rules.
- Implement preview-confirm change workflow.
- Implement downgrade enforcement and entitlement resolution.

### Epic 4: Provider integration layer
- Implement provider-neutral interfaces.
- Implement Stripe adapter.
- Implement provider-specific webhook endpoint and translation pipeline.

### Epic 5: Billing orchestration and notifications
- Month-start billing runner, retries, grace/fallback.
- Notification events and channel delivery integration.
- Payment method expiration monitor.

### Epic 6: Audit, reconciliation, hardening
- Append-only audit implementation and queries.
- Reconciliation jobs.
- Observability and alerting for failed jobs/webhook anomalies.

### Epic 7: Test and cutover
- Build test matrix and automation.
- Run shadow verification on legacy data.
- Cutover and deprecate replaced legacy components.

## 11. Open Questions Requiring Product/Legal Sign-off

- Perpetual plan behavior: exact billing and lifecycle semantics when termination is null.
- Discount code combination policy: strict global lock or per-product lock while active.
- Dispute/chargeback policy: automated subscription suspension vs manual review queue.
- Price change notice policy defaults by schedule type and jurisdiction.
- Receipt storage policy: signed URL lifetime and retention obligations.

