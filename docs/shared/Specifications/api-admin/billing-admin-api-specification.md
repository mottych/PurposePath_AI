# Billing Admin API Specification

**Version:** 1.2  
**Status:** Ready for implementation  
**Last Updated:** April 12, 2026  
**Base URL:** `{REACT_APP_ADMIN_API_URL}/admin/api/v1/billing`

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| Apr 12, 2026 | 1.2 | Clarified billing price-tier/discount applicability targeting semantics: `targetType`/`targetId` matrix, optional `scheduleId` for category targets, specific-over-category precedence, and temporary `coaching` no-op behavior. |
| Apr 12, 2026 | 1.1 | Confirmed clean-cut billing implementation: legacy admin `/discount-codes` controller path removed; canonical discount operations remain under `/billing/discount-codes`. |
| Mar 23, 2026 | 1.0 | Initial billing admin API specification. |

---

## Overview

This document defines the admin portal billing contract used by the admin repository, the backend repository, and any operational tooling that manages billing catalog, pricing, tenant billing overrides, and audit workflows.

This specification covers:

- Feature catalog metadata and feature set management
- Plan lifecycle, visibility, designation, and pricing management
- Payment schedule and extension definition management
- Price tier and discount code management
- Tenant-level price tier assignments, hidden-plan assignments, and feature overrides
- Billing settings and audit access

This document is derived from the canonical machine-readable contract in `docs/shared/Specifications/api-fe/billing-backend-openapi.yaml`.

---

## Authentication and Headers

All endpoints require admin authorization.

```http
Authorization: Bearer {adminAccessToken}
Content-Type: application/json
```

All mutating endpoints require:

```http
Idempotency-Key: {unique-request-key}
```

### Authorization Rule

- Caller must satisfy the admin authorization policy
- All write operations are audit-relevant and must preserve correlation context for downstream logging

---

## Common Conventions

### Response Envelope

All endpoints return `ApiResponse<T>`.

### Pagination

Query parameters:

- `page`: minimum `1`, default `1`
- `limit`: minimum `1`, maximum `200`, default `20`

### Core Enums

- `ResourceStatus`: `draft | active | inactive | archived`
- `PlanVisibility`: `published | hidden`
- `DurationType`: `timed | perpetual`
- `FeatureValueType`: `boolean | numeric | tier`
- `PriceAdjustmentType`: `percent | amount | override`
- `PriceTierApplicabilityMode`: `tenantAssigned | discountDriven | both`
- `PriceFallbackBehavior`: `useBasePrice | rejectIfMissing`
- `DiscountEligibilityType`: `newUsers | renewals | referrals | specificDomain | specificTenant | listMatching`
- `PlanDesignationType`: `trial | fallback`
- `OverrideValueType`: `boolean | numeric | tier`

### Validation Behavior

- `409 Conflict`: returned when the request collides with current billing state or an effective-dated uniqueness invariant
- `422 Unprocessable Entity`: returned when the payload is structurally valid but violates billing validation rules

Conflict diagnostics use:

- `error.details.conflicts[]`

Validation diagnostics use:

- `error.details.validationErrors[]`

---

## Endpoint Index

### Feature Metadata and Feature Sets

- `GET /feature-catalog`
- `GET /feature-sets`
- `POST /feature-sets`
- `GET /feature-sets/{featureSetId}`
- `PATCH /feature-sets/{featureSetId}`
- `DELETE /feature-sets/{featureSetId}`
- `POST /feature-sets/{featureSetId}/activate`
- `POST /feature-sets/{featureSetId}/deactivate`

### Plans and Designations

- `GET /plans`
- `POST /plans`
- `GET /plans/{planId}`
- `PATCH /plans/{planId}`
- `DELETE /plans/{planId}`
- `POST /plans/{planId}/archive`
- `POST /plans/{planId}/restore`
- `POST /plans/{planId}/publish`
- `POST /plans/{planId}/hide`
- `POST /plans/{planId}/set-trial`
- `DELETE /plans/trial-designation`
- `POST /plans/{planId}/set-fallback`
- `DELETE /plans/fallback-designation`
- `PUT /plans/{planId}/schedules/{scheduleId}/price`

### Payment Schedules

- `GET /payment-schedules`
- `POST /payment-schedules`
- `GET /payment-schedules/{scheduleId}`
- `PATCH /payment-schedules/{scheduleId}`
- `DELETE /payment-schedules/{scheduleId}`
- `POST /payment-schedules/{scheduleId}/activate`
- `POST /payment-schedules/{scheduleId}/deactivate`

### Extensions

- `GET /extensions`
- `POST /extensions`
- `GET /extensions/{extensionDefinitionId}`
- `PATCH /extensions/{extensionDefinitionId}`
- `DELETE /extensions/{extensionDefinitionId}`
- `POST /extensions/{extensionDefinitionId}/activate`
- `POST /extensions/{extensionDefinitionId}/deactivate`
- `PUT /extensions/{extensionDefinitionId}/plans/{planId}/schedules/{scheduleId}/price`

### Price Tiers and Discount Codes

- `GET /price-tiers`
- `POST /price-tiers`
- `GET /price-tiers/{priceTierId}`
- `PATCH /price-tiers/{priceTierId}`
- `DELETE /price-tiers/{priceTierId}`
- `POST /price-tiers/{priceTierId}/activate`
- `POST /price-tiers/{priceTierId}/deactivate`
- `GET /tenants/{tenantId}/price-tier-assignment`
- `PUT /tenants/{tenantId}/price-tier-assignment`
- `DELETE /tenants/{tenantId}/price-tier-assignment`
- `GET /discount-codes`
- `POST /discount-codes`
- `GET /discount-codes/{discountCodeId}`
- `PATCH /discount-codes/{discountCodeId}`
- `DELETE /discount-codes/{discountCodeId}`
- `POST /discount-codes/{discountCodeId}/activate`
- `POST /discount-codes/{discountCodeId}/deactivate`

### Tenant Assignments, Overrides, Settings, and Audit

- `GET /tenants/{tenantId}/hidden-plan-assignment`
- `POST /tenants/{tenantId}/hidden-plan-assignment`
- `DELETE /tenants/{tenantId}/hidden-plan-assignment`
- `GET /tenants/{tenantId}/overrides`
- `POST /tenants/{tenantId}/overrides`
- `GET /tenants/{tenantId}/overrides/{overrideId}`
- `PATCH /tenants/{tenantId}/overrides/{overrideId}`
- `DELETE /tenants/{tenantId}/overrides/{overrideId}`
- `POST /tenants/{tenantId}/overrides/{overrideId}/end`
- `GET /settings`
- `PATCH /settings`
- `GET /tenants/{tenantId}/audit`
- `GET /audit`

---

## Feature Metadata and Feature Sets

### GET /feature-catalog

Returns the canonical feature registry used by the admin UI to drive form options and validation messaging.

**Response:** `ApiResponse<FeatureCatalog>`

Each `items[]` entry includes:

- `featureKey`
- `displayName`
- `description`
- `valueType`: `boolean | numeric | tier`
- `additiveOnly`: boolean
- `categories[]`
- `unitLabel`
- `minNumericValue`
- `maxNumericValue`
- `tierOptions[]`
- `allowedUsageScopes[]`: `featureSet | extension | tenantOverride`

### GET /feature-sets

Returns paginated feature set definitions.

**Query Parameters:**

- `status`: `draft | active | inactive | archived`
- `includeArchived`: boolean, default `false`
- `page`, `limit`

### POST /feature-sets

Creates a feature set.

**Request:** `CreateFeatureSetRequest`

```json
{
  "name": "Professional Base Capabilities",
  "description": "Core feature set for professional plans",
  "components": [
    {
      "featureKey": "prioritySupport",
      "valueType": "boolean",
      "booleanValue": true
    },
    {
      "featureKey": "teamMembers",
      "valueType": "numeric",
      "numericValue": 25
    }
  ]
}
```

**Constraints:**

- `name`: required string
- `components[]`: required
- `components[].valueType`: must match the provided value field

### PATCH /feature-sets/{featureSetId}

Updates `name`, `description`, or `components`.

### DELETE /feature-sets/{featureSetId}

Hard delete allowed only when the feature set is not referenced by any plan.

### POST /feature-sets/{featureSetId}/activate and /deactivate

Changes the feature set lifecycle state.

---

## Plan Management

### GET /plans

Returns paginated plan list.

**Query Parameters:**

- `visibility`: `published | hidden`
- `status`: `draft | active | inactive | archived`
- `includeArchived`: boolean, default `false`
- `page`, `limit`

### POST /plans

Creates a plan.

**Request:** `CreatePlanRequest`

```json
{
  "name": "Professional Annual",
  "description": "Annual professional plan",
  "featureSetId": "uuid",
  "durationType": "timed",
  "visibility": "published",
  "gracePeriodDays": 7,
  "trialDurationDays": 14,
  "paymentSchedules": [
    {
      "scheduleId": "uuid",
      "scheduleCode": "annual",
      "monthsCovered": 12,
      "price": { "amount": 499.00, "currency": "USD" },
      "effectiveStartDateUtc": "2026-01-01T00:00:00Z"
    }
  ]
}
```

**Required fields:**

- `name`
- `description`
- `featureSetId` (UUID)
- `durationType`
- `visibility`

### PATCH /plans/{planId}

Updatable fields:

- `name`
- `description`
- `featureSetId`
- `visibility`
- `gracePeriodDays`
- `trialDurationDays`
- `status`

### DELETE /plans/{planId}

Hard delete only before any subscription has ever used the plan.

### POST /plans/{planId}/archive and /restore

Moves a plan into or out of archived state.

### POST /plans/{planId}/publish and /hide

Controls self-service visibility.

### POST /plans/{planId}/set-trial

Designates the single global trial plan.

**Validation:**

- returns `422` if the plan is not eligible for trial use
- if another trial designation exists, it is replaced with the new plan designation

### DELETE /plans/trial-designation

Clears the current trial designation.

### POST /plans/{planId}/set-fallback

Designates the single global fallback plan.

### DELETE /plans/fallback-designation

Clears the current fallback designation.

### PUT /plans/{planId}/schedules/{scheduleId}/price

Upserts an effective-dated plan price.

**Request:** `UpsertPlanSchedulePriceRequest`

```json
{
  "price": { "amount": 59.00, "currency": "USD" },
  "effectiveStartDateUtc": "2026-05-01T00:00:00Z",
  "effectiveEndDateUtc": null
}
```

**Validation:**

- `price`: required `MoneyInput`
- `effectiveStartDateUtc`: required UTC date-time
- overlapping effective windows return `409`

---

## Payment Schedule Management

### POST /payment-schedules

**Request:** `CreatePaymentScheduleRequest`

```json
{
  "code": "annual",
  "name": "Annual",
  "monthsCovered": 12
}
```

**Constraints:**

- `code`: required string
- `name`: required string
- `monthsCovered`: integer, minimum `1`

### PATCH /payment-schedules/{scheduleId}

Updatable fields:

- `name`
- `monthsCovered` (minimum `1`)
- `status`

### DELETE /payment-schedules/{scheduleId}

Hard delete allowed only when the schedule is unused.

### POST /payment-schedules/{scheduleId}/activate and /deactivate

Toggles lifecycle state.

---

## Extension Management

### POST /extensions

Creates an extension definition.

**Request:** `CreateExtensionDefinitionRequest`

```json
{
  "planId": "uuid",
  "name": "Extra Team Member Seat",
  "description": "Adds one additional active seat",
  "featureKey": "teamMembers",
  "unitValue": 1,
  "unitLabel": "seat",
  "maxQuantity": 50,
  "schedulePrices": [
    {
      "planId": "uuid",
      "scheduleId": "uuid",
      "price": { "amount": 9.00, "currency": "USD" },
      "effectiveStartDateUtc": "2026-01-01T00:00:00Z"
    }
  ]
}
```

**Required fields:**

- `planId`
- `name`
- `featureKey`
- `unitValue`
- `unitLabel`

### PATCH /extensions/{extensionDefinitionId}

Updatable fields:

- `name`
- `description`
- `unitValue`
- `unitLabel`
- `maxQuantity`
- `status`

### PUT /extensions/{extensionDefinitionId}/plans/{planId}/schedules/{scheduleId}/price

Upserts effective-dated extension pricing using `UpsertExtensionPriceRequest`.

### DELETE /extensions/{extensionDefinitionId}

Hard delete only before the extension has ever been attached to a subscription.

### POST /extensions/{extensionDefinitionId}/activate and /deactivate

Toggles lifecycle state.

---

## Price Tier Management

### POST /price-tiers

Creates a price tier definition.

**Request:** `CreatePriceTierRequest`

Required fields:

- `code`
- `name`
- `applicabilityMode`: `tenantAssigned | discountDriven | both`
- `fallbackBehavior`: `useBasePrice | rejectIfMissing`
- `lines[]`

Each `lines[]` item contains:

- `targetType`: `planSchedule | extensionPlanSchedule | category`
- `targetId`
- `scheduleId`
- `adjustmentType`: `percent | amount | override`
- `percentOff`
- `amountOff`
- `overridePrice`

**Targeting semantics:**

- `targetType = planSchedule`
  - `targetId`: plan ID
  - `scheduleId`: required
- `targetType = extensionPlanSchedule`
  - `targetId`: extension definition ID
  - `scheduleId`: required
- `targetType = category`
  - `targetId`: `subscription | rider | coaching`
  - `scheduleId`: optional
  - when `scheduleId` is provided, the line applies only to that schedule

**Resolution behavior:**

- specific targets win over category targets (`planSchedule`/`extensionPlanSchedule` before `category`)
- `category = coaching` is currently a no-op in runtime pricing/discount resolution (reserved for future coaching billing support)

### PATCH /price-tiers/{priceTierId}

Updatable fields:

- `name`
- `description`
- `status`
- `applicabilityMode`
- `fallbackBehavior`
- `lines[]`

### DELETE /price-tiers/{priceTierId}

Hard delete only when the price tier has never been assigned or applied.

### POST /price-tiers/{priceTierId}/activate and /deactivate

Toggles lifecycle state.

### GET /tenants/{tenantId}/price-tier-assignment

Returns the current tenant-specific tier assignment.

### PUT /tenants/{tenantId}/price-tier-assignment

**Request:** `AssignTenantPriceTierRequest`

```json
{
  "priceTierId": "uuid",
  "effectiveStartDateUtc": "2026-04-01T00:00:00Z",
  "effectiveEndDateUtc": null,
  "reason": "Partner pricing migration"
}
```

**Validation:**

- `priceTierId`: required UUID
- `effectiveStartDateUtc`: required
- overlap or conflicting assignment returns `409`

### DELETE /tenants/{tenantId}/price-tier-assignment

Clears the current tier assignment.

---

## Discount Code Management

### POST /discount-codes

Creates a discount code.

**Request:** `CreateDiscountCodeRequest`

Required fields:

- `code`
- `name`
- `pricing`
- `repeatability`

Discount code payload supports:

- `validFromUtc`
- `validToUtc`
- `effectiveDuration.unit`: `days | months | billingCycles`
- `eligibility[]` using `DiscountEligibilityType`
- `applicability[]` using `DiscountApplicabilityTargetType`
- `repeatability.maxRedemptionsPerTenant`
- `repeatability.canCombineWithOtherDiscounts`
- `repeatability.blocksOtherDiscountsWhileActive`

`applicability[]` follows the same targeting semantics and precedence rules defined under price tier `lines[]`.

### PATCH /discount-codes/{discountCodeId}

Supports the same mutable fields plus `status`.

### DELETE /discount-codes/{discountCodeId}

Hard delete allowed only when the code has never been redeemed.

### POST /discount-codes/{discountCodeId}/activate and /deactivate

Toggles lifecycle state.

---

## Tenant Hidden Plan Assignments and Overrides

### GET /tenants/{tenantId}/hidden-plan-assignment

Returns the tenant hidden-plan assignment state for admin workflows.

**Response:** `ApiResponse<HiddenPlanAssignmentResponse>`

Key fields:

- `subscription`
- `hasActiveHiddenPlan`
- `hasPendingHiddenPlan`
- `assignmentState`: `active | pending | none`

### POST /tenants/{tenantId}/hidden-plan-assignment

Assigns a hidden plan to a tenant outside the self-service catalog.

**Request:** `AssignHiddenPlanRequest`

```json
{
  "planId": "uuid",
  "scheduleId": "uuid",
  "effectiveMode": "immediate",
  "extensionSelections": [
    { "extensionDefinitionId": "uuid", "quantity": 2 }
  ],
  "paymentBehavior": "preserveBillingAnchor",
  "reason": "Negotiated enterprise migration",
  "internalNote": "Approved by sales leadership"
}
```

**Required fields:**

- `planId`
- `scheduleId`
- `reason`

**Enums:**

- `effectiveMode`: `immediate | nextCycle`
- `paymentBehavior`: `chargeProratedDelta | preserveBillingAnchor | noImmediateCharge`

**Validation:**

- target plan must be hidden
- conflict returns `409`
- semantic validation failure returns `422`

### DELETE /tenants/{tenantId}/hidden-plan-assignment

Removes the tenant's hidden plan assignment.

### POST /tenants/{tenantId}/overrides

Creates a tenant override.

**Request:** `CreateTenantOverrideRequest`

Required fields:

- `featureKey`
- `valueType`
- `effectiveStartDateUtc`

Value field must match `valueType`:

- `booleanValue` for `boolean`
- `numericValue` for `numeric`
- `tierValue` for `tier`

**Validation:**

- overrides are additive only
- overlap or state conflict returns `409`
- non-additive values return `422`

### PATCH /tenants/{tenantId}/overrides/{overrideId}

Updatable fields:

- `booleanValue`
- `numericValue`
- `tierValue`
- `effectiveStartDateUtc`
- `effectiveEndDateUtc`
- `reason`

### DELETE /tenants/{tenantId}/overrides/{overrideId}

Removes a future or immediately revocable override.

### POST /tenants/{tenantId}/overrides/{overrideId}/end

Schedules an override end time.

**Request:**

```json
{
  "effectiveEndDateUtc": "2026-06-01T00:00:00Z",
  "reason": "Promotional grant expired"
}
```

---

## Billing Settings

### GET /settings

Returns current billing platform settings.

### PATCH /settings

Updates platform-wide settings.

**Request:** `UpdateBillingSettingsRequest`

Fields:

- `retryDelayDays`
- `maxAutomaticAttemptsPerCycle`
- `cardExpiryWarningDays`
- `priceChangeNoticeMinimumDays`
- `annualRenewalReminderLeadWindowDays.minimum`
- `annualRenewalReminderLeadWindowDays.maximum`
- `notificationPolicies`

Validation floors and policy constraints:

- `retryDelayDays`: minimum `1`
- `maxAutomaticAttemptsPerCycle`: minimum `1`
- `cardExpiryWarningDays`: minimum `1`
- `priceChangeNoticeMinimumDays`: minimum `30`
- `annualRenewalReminderLeadWindowDays.minimum`: minimum `30`
- `annualRenewalReminderLeadWindowDays.maximum`: must be greater than or equal to `minimum`
- `notificationPolicies`: supports only `paymentFailure`, `cardExpiryWarning`, `priceChangeNotice`, `annualRenewalReminder`

---

## Audit Endpoints

### GET /tenants/{tenantId}/audit

Returns tenant-scoped billing audit entries.

**Query Parameters:**

- `page`, `limit`
- `eventType`
- `actorType`
- `from`
- `to`

### GET /audit

Returns cross-tenant audit search results.

**Query Parameters:**

- `tenantId`
- `eventType`
- `actorType`
- `actorId`
- `correlationId`
- `from`
- `to`
- `page`, `limit`

Each `BillingAuditRecord` includes:

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

- `200 OK`
- `201 Created`
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`
- `409 Conflict`
- `422 Unprocessable Entity`

### Common Billing Error Codes

- `BILLING_PLAN_DESIGNATION_CONFLICT`
- `BILLING_EFFECTIVE_DATE_OVERLAP`
- `BILLING_VALIDATION_FAILED`
- `BILLING_OVERRIDE_NOT_ADDITIVE`
- `BILLING_IDEMPOTENCY_CONFLICT`

### Conflict Shape

```json
{
  "success": false,
  "message": "Validation conflict",
  "error": {
    "code": "BILLING_EFFECTIVE_DATE_OVERLAP",
    "message": "The requested effective period overlaps an existing billing record.",
    "correlationId": "uuid",
    "details": {
      "category": "conflict",
      "conflicts": []
    }
  }
}
```

### Validation Failure Shape

```json
{
  "success": false,
  "message": "Validation failed",
  "error": {
    "code": "BILLING_VALIDATION_FAILED",
    "message": "One or more billing validation rules were not satisfied.",
    "correlationId": "uuid",
    "details": {
      "category": "validation",
      "validationErrors": []
    }
  }
}
```

---

## Implementation Rules

1. `billing-backend-openapi.yaml` remains the canonical machine-readable source of truth.
2. The admin portal must treat effective-dated pricing and assignment updates as conflict-sensitive and surface `409` diagnostics directly to operators.
3. Hidden plan assignment must never be exposed through self-service UX and always requires a reason.
4. Feature metadata from `GET /feature-catalog` should drive all admin forms for feature-set creation, extension authoring, and tenant override validation.
5. Admin clients must preserve and resend unique `Idempotency-Key` values for retry-safe mutations.
