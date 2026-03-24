# Billing Frontend API Specification

**Version:** 1.0  
**Status:** Ready for implementation  
**Last Updated:** March 23, 2026  
**Base URL:** `{REACT_APP_ACCOUNT_API_URL}/account/api/v1/billing`

---

## Overview

This document is the human-readable frontend contract for the redesigned user-facing billing experience. It is intended for the frontend repository, the backend repository, and the admin repository when coordinating end-user subscription flows.

This specification covers:

- Tenant-visible subscription summary and current billing state
- Published plan catalog, schedule, and extension browsing
- Preview and confirm flows for priced subscription changes
- Owner-only payment method and payment history operations
- Tenant-visible audit and entitlement reads

This document is derived from the canonical machine-readable contract in `docs/shared/Specifications/api-fe/billing-backend-openapi.yaml`.

---

## Authentication and Roles

### Required Headers

All endpoints require:

```http
Authorization: Bearer {accessToken}
Content-Type: application/json
```

### Role Model

- `tenant_user`: Any authenticated user within the tenant
- `tenant_owner`: Authenticated tenant owner with billing management rights

### Role Rules

- `GET /subscription/summary`, `GET /plans/catalog`, and `GET /entitlements/effective` are available to `tenant_user` and `tenant_owner`
- All mutating billing endpoints are owner-only
- Payment history, payment method management, and tenant-visible billing audit are owner-only

### Idempotency

All mutating endpoints require:

```http
Idempotency-Key: {unique-request-key}
```

The same key must not be reused with a different payload.

---

## Common Patterns

### Response Envelope

All success and error responses use `ApiResponse<T>`:

```json
{
  "success": true,
  "message": null,
  "data": {},
  "error": null
}
```

Error responses use:

```json
{
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "BILLING_VALIDATION_FAILED",
    "message": "One or more billing validation rules were not satisfied.",
    "correlationId": "uuid",
    "details": {}
  }
}
```

### Pagination

Paginated endpoints use:

```http
?page=1&limit=20
```

Constraints:

- `page`: minimum `1`, default `1`
- `limit`: minimum `1`, maximum `200`, default `20`

### Time and Money

- All timestamps are UTC ISO-8601 date-times
- Money objects use:

```json
{ "amount": 49.99, "currency": "USD" }
```

### Important Enums

- `accessState`: `full | fallback | blocked`
- `effectiveMode`: `immediate | nextCycle`
- `paymentResult.status`: `succeeded | requiresAction | failed`
- `paymentResult.nextAction.nextActionType`: `none | redirect | useStripeSdk | providerAction`
- `paymentHistory.status`: `succeeded | pending | failed | refunded | partiallyRefunded`

---

## Endpoint Index

### Tenant Read Endpoints

- `GET /subscription/summary`
- `GET /plans/catalog`
- `GET /entitlements/effective`

### Owner Billing Endpoints

- `GET /subscription/current`
- `POST /subscription/preview-change`
- `POST /subscription/confirm-change`
- `POST /subscription/cancel`
- `POST /subscription/reactivate`
- `GET /subscription/extensions`
- `POST /subscription/extensions`
- `DELETE /subscription/extensions/{extensionSelectionId}`
- `GET /payment-method`
- `POST /payment-method/setup-intent`
- `POST /payment-method/confirm`
- `GET /payment-history`
- `GET /payment-history/{paymentId}`
- `GET /payment-history/{paymentId}/receipt`
- `GET /audit`

---

## Tenant Read Endpoints

### GET /subscription/summary

Lightweight plan summary for shared tenant UI such as navigation, profile shell, and non-owner views.

**Role:** `tenant_user`, `tenant_owner`

**Response:** `ApiResponse<SubscriptionSummary>`

```json
{
  "success": true,
  "data": {
    "tenantId": "uuid",
    "planId": "uuid",
    "planName": "Professional Annual",
    "planDisplayName": "Professional",
    "accessState": "full",
    "isTrial": false
  }
}
```

**Guaranteed fields:**

- `tenantId`: UUID
- `planId`: UUID
- `planName`: internal or canonical plan name
- `planDisplayName`: frontend display label
- `accessState`: `full | fallback | blocked`
- `isTrial`: boolean

### GET /plans/catalog

Returns the self-service catalog visible to authenticated tenant users.

**Role:** `tenant_user`, `tenant_owner`

**Query Parameters:**

- `includeCurrentPlan` (boolean, optional)
- `schedule` (string, optional)

**Response:** `ApiResponse<PlanCatalog>`

Each catalog item includes:

- `plan`
- `featureSummary`
- `limitsSummary`
- `availableSchedules[]`
- `availableExtensions[]`
- `trialRestrictions`

**Plan constraints:**

- `visibility`: `published | hidden`
- `status`: `draft | active | inactive | archived`
- `durationType`: `timed | perpetual`

### GET /entitlements/effective

Returns the tenant's effective features and limits after base plan, extensions, and overrides are resolved.

**Role:** `tenant_user`, `tenant_owner`

**Response:** `ApiResponse<EffectiveEntitlements>`

```json
{
  "success": true,
  "data": {
    "features": {
      "prioritySupport": true,
      "customBranding": true
    },
    "limits": {
      "teamMembers": 25,
      "goals": 100
    }
  }
}
```

---

## Owner Subscription Endpoints

### GET /subscription/current

Returns the full owner-facing billing view.

**Role:** `tenant_owner`

**Response:** `ApiResponse<SubscriptionCurrent>`

**Key fields:**

- `tenantId`, `subscriptionId`
- `plan`
- `status`
- `isTrial`
- `autoRenew`
- `effectiveDate`
- `terminationDate`
- `inGracePeriod`
- `gracePeriodEndDate`
- `paymentSchedule`
- `activeExtensions[]`
- `accessState`
- `pendingChangeSummary`
- `trialUpgradeBanner`

### POST /subscription/preview-change

Calculates the billing and entitlement impact of a plan, schedule, and extension mutation without committing it.

**Role:** `tenant_owner`

**Request:** `PreviewSubscriptionChangeRequest`

```json
{
  "targetPlanId": "uuid",
  "targetScheduleId": "uuid",
  "discountCode": "SPRING2026",
  "extensionSelections": [
    {
      "extensionDefinitionId": "uuid",
      "quantity": 2
    }
  ]
}
```

**Constraints:**

- `targetPlanId`: required UUID
- `targetScheduleId`: required UUID
- `extensionSelections[].quantity`: integer, minimum `1`

**Response:** `ApiResponse<SubscriptionChangePreview>`

Key fields:

- `effectiveMode`: `immediate | nextCycle`
- `validationSnapshotId`: required for confirm
- `totalDueNow`: `Money`
- `lineItems[]`
- `downgradeWarnings[]`
- `blockingViolations[]`
- `discountApplication`: `none | tenantPriceTier | discountCode | discountCodeRejected`
- `effectivePriceTierId`
- `scheduledStartDateUtc`

#### Downgrade Warning Payload

Each `downgradeWarnings[]` or `blockingViolations[]` item contains:

- `featureKey`
- `featureName`
- `currentUsage`
- `newLimit`
- `overageAmount`
- `severity`: `info | warning | blocking`
- `blocked`: boolean
- `recommendedAction`
- `recommendedActionTarget`

`recommendedActionTarget.targetType` enum:

- `billingSettings`
- `usageDashboard`
- `memberManagement`
- `contentManagement`
- `extensionCatalog`
- `route`
- `url`

### POST /subscription/confirm-change

Commits a previously previewed mutation.

**Role:** `tenant_owner`

**Request:** `ConfirmSubscriptionChangeRequest`

```json
{
  "validationSnapshotId": "snapshot-id",
  "confirmationToken": "optional-provider-token",
  "paymentMethodToken": "optional-provider-payment-token"
}
```

**Constraints:**

- `validationSnapshotId`: required string from preview response

**Response:** `ApiResponse<SubscriptionChangeResult>`

Key fields:

- `subscription`: updated `SubscriptionCurrent`
- `paymentResult`

#### Payment Result

`paymentResult.status`:

- `succeeded`
- `failed`
- `requiresAction`

`requiresAction` always includes a typed `nextAction` variant.

Examples:

- `nextActionType = none`
- `nextActionType = redirect` with required `redirectUrl`
- `nextActionType = useStripeSdk` with required `clientSecret` and `paymentIntentId`
- `nextActionType = providerAction` with required `providerPayload`

### POST /subscription/cancel

Disables auto-renewal while preserving access through the end of the paid term.

**Role:** `tenant_owner`

**Request:**

```json
{ "reason": "Optional free-text reason" }
```

**Response:** updated `SubscriptionCurrent`

### POST /subscription/reactivate

Re-enables auto-renewal or recovers during grace when payment succeeds.

**Role:** `tenant_owner`

**Request:**

```json
{ "paymentMethodToken": "optional-provider-token" }
```

**Response:** updated `SubscriptionCurrent`

---

## Owner Extension Endpoints

### GET /subscription/extensions

Returns the active extension selections and the currently available extension catalog.

**Role:** `tenant_owner`

**Response:** `ApiResponse<ExtensionState>`

`activeExtensions[]` fields:

- `extensionSelectionId`
- `extensionDefinitionId`
- `name`
- `featureKey`
- `quantity`
- `unitValue`
- `unitLabel`
- `maxQuantity`
- `schedulePrice`
- `totalPrice`

### POST /subscription/extensions

Internal convenience endpoint for backend or non-UI orchestration. Frontend flows must not call this endpoint directly for priced extension changes.

**Role:** `tenant_owner`

**Required frontend rule:** use `POST /subscription/preview-change` followed by `POST /subscription/confirm-change` for all priced extension updates.

**Request:** `UpsertExtensionsRequest`

```json
{
  "extensionSelections": [
    { "extensionDefinitionId": "uuid", "quantity": 3 }
  ]
}
```

**Response:** `ApiResponse<ExtensionMutationResult>`

### DELETE /subscription/extensions/{extensionSelectionId}

Schedules an extension removal for the next billing cycle.

**Role:** `tenant_owner`

**Path Parameters:**

- `extensionSelectionId`: required UUID

**Response:**

```json
{
  "success": true,
  "data": {
    "extensionSelectionId": "uuid",
    "effectiveRemovalDate": "2026-04-01T00:00:00Z"
  }
}
```

---

## Owner Payment Method Endpoints

### GET /payment-method

Returns the masked stored payment instrument.

**Role:** `tenant_owner`

**Response:** `ApiResponse<PaymentMethod>`

Fields:

- `brand`
- `last4`
- `expMonth`
- `expYear`
- `isExpiringSoon`

### POST /payment-method/setup-intent

Starts a provider-hosted card setup flow.

**Role:** `tenant_owner`

**Header:** `Idempotency-Key`

**Response:** `ApiResponse<SetupIntentResponse>`

```json
{
  "success": true,
  "data": {
    "provider": "stripe",
    "clientToken": "provider-client-token"
  }
}
```

### POST /payment-method/confirm

Completes payment method attachment using the provider token produced by the setup flow.

**Role:** `tenant_owner`

**Request:**

```json
{ "providerToken": "provider-confirmation-token" }
```

**Response:** updated `PaymentMethod`

---

## Payment History and Receipt Endpoints

### GET /payment-history

Returns a paginated list of historical payments.

**Role:** `tenant_owner`

**Query Parameters:**

- `page`
- `limit`
- `from` (UTC date-time, optional)
- `to` (UTC date-time, optional)

**Response:** `ApiResponse<PaymentHistory>`

Each `items[]` row includes:

- `paymentId`
- `paidAtUtc`
- `amount`
- `planName`
- `billingPeriod`
- `cardLast4`
- `status`

### GET /payment-history/{paymentId}

Returns row drill-in details for a specific payment.

**Role:** `tenant_owner`

**Path Parameters:**

- `paymentId`: required UUID

**Response:** `ApiResponse<PaymentHistoryDetail>`

Guaranteed fields:

- `paymentId`
- `status`: `succeeded | pending | failed | refunded | partiallyRefunded`
- `amount`
- `planName`
- `billingPeriod`
- `lineItems[]`
- `cardSnapshot`

Optional fields:

- `paidAtUtc`
- `providerStatus`: `processing | succeeded | requiresAction | failed | canceled | refunded`
- `providerFailureReason`
- `invoiceReference`
- `receiptReference`
- `providerReference`
- `retryContext`

### GET /payment-history/{paymentId}/receipt

Returns the receipt download metadata for a specific payment.

**Role:** `tenant_owner`

**Response:** `ApiResponse<ReceiptResponse>`

Fields:

- `receiptId`
- `downloadUrl`
- `expiresAtUtc`
- `planName`
- `billingPeriod`
- `cardLast4`
- `lineItems[]`

---

## Audit Endpoint

### GET /audit

Returns tenant-visible billing history.

**Role:** `tenant_owner`

**Query Parameters:**

- `page`
- `limit`
- `eventType` (optional)
- `from` (optional UTC date-time)
- `to` (optional UTC date-time)

**Response:** `ApiResponse<BillingAuditList>`

Each audit item includes:

- `id`
- `timestampUtc`
- `tenantId`
- `actorType`: `tenant_owner | admin | system`
- `actorId`
- `eventType`
- `description`
- `beforeState`
- `afterState`
- `metadata`

---

## Error Handling

### Common Status Codes

- `200 OK`: Read or mutation success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid structure or parameters
- `401 Unauthorized`: Missing or invalid bearer token
- `403 Forbidden`: Authenticated but caller lacks required role
- `404 Not Found`: Resource not found or not visible in tenant scope
- `409 Conflict`: Billing state conflict or effective-dated conflict
- `422 Unprocessable Entity`: Billing validation failure

### Billing-Specific Error Codes

- `BILLING_OWNER_REQUIRED`
- `BILLING_PLAN_CHANGE_BLOCKED`
- `BILLING_PAYMENT_METHOD_REQUIRED`
- `BILLING_PAYMENT_FAILED`
- `BILLING_IDEMPOTENCY_CONFLICT`
- `BILLING_DISCOUNT_INELIGIBLE`
- `BILLING_PRICE_TIER_CONFLICT`
- `BILLING_TRIAL_EXTENSION_NOT_ALLOWED`
- `BILLING_PRICE_CHANGE_NOTICE_REQUIRED`
- `BILLING_DISCOUNT_COMBINATION_BLOCKED`
- `BILLING_ACCESS_BLOCKED`
- `BILLING_VALIDATION_FAILED`

### 409 Conflict Diagnostics

Conflict diagnostics are returned in:

- `error.details.conflicts[]`

### 422 Validation Diagnostics

Validation diagnostics are returned in:

- `error.details.validationErrors[]`

---

## Frontend Implementation Rules

1. Frontend must treat `billing-backend-openapi.yaml` as the canonical machine contract and this document as the human-readable companion.
2. Non-owner plan display should use `GET /subscription/summary`.
3. All priced plan or extension changes must use preview then confirm.
4. Frontend must branch on `paymentResult.status`; when `requiresAction`, it must inspect the discriminated `nextAction` payload and handle the required fields for that variant.
5. Billing notification category preferences are configured through the existing notification settings API, not through this billing surface.
