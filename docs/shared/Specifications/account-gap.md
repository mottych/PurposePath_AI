# Account Service Gap Specification

**Version:** 1.0  
**Status:** Pending Implementation  
**Last Updated:** December 30, 2025  
**Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`

---

## Overview

This document specifies additional Account Service endpoints not yet covered in `account-api.md` or `business-foundation-api.md`. These endpoints handle authentication confirmations, subscription management, billing, onboarding, and tenant settings.

---

## Authentication Endpoints

### POST /auth/resend-confirmation

Resend email confirmation link.

**Query Parameters:**

- `email` - Email address to resend confirmation to

**Special Headers:** 

- `X-Frontend-Base-Url: {window.location.origin}` (optional, improves email link accuracy)

**Response:**

```json
{
  "success": true
}
```

**Status Codes:**

- `200` - Confirmation email sent
- `400` - Invalid email or user not found
- `429` - Rate limited (too many requests)
- `500` - Email sending failed

---

## Subscription Management Endpoints

### GET /subscription/tiers

Get all available subscription tiers with pricing (dynamic).

**Headers Required:**

- `Authorization: Bearer {accessToken}` (optional for unauthenticated discovery)
- `X-Tenant-Id: {tenantId}` (optional)

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "features": ["goals", "operations", "reports"],
      "limits": {
        "goals": 10,
        "kpis": 50,
        "actions": null
      },
      "pricing": {
        "monthly": 29.99,
        "yearly": 299.99
      },
      "supportedFrequencies": ["monthly", "yearly"],
      "isActive": true
    }
  ]
}
```

**Notes:**

- Pricing is dynamic and may change
- `supportedFrequencies` indicates which billing cycles are available
- If tier only supports monthly, `yearly` will be `null`
- Both monthly and yearly subscriptions can be cancelled anytime

**Status Codes:**

- `200` - Success
- `500` - Server error

---

### GET /user/subscription

Get current user's subscription details with tier information.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "userId": "string",
    "tier": {
      "id": "string",
      "name": "string",
      "features": ["string"],
      "limits": {},
      "supportedFrequencies": ["monthly", "yearly"]
    },
    "frequency": "monthly|yearly",
    "status": "string",
    "isActive": true,
    "currentPeriodStart": "2025-10-01T00:00:00Z",
    "currentPeriodEnd": "2025-11-01T00:00:00Z",
    "expirationDate": "string?",
    "cancelAtPeriodEnd": false,
    "autoRenewal": true,
    "price": 29.99,
    "currency": "USD",
    "isTrial": false,
    "trialEndDate": "string?",
    "trialExtendedBy": "string?",
    "trialExtensionReason": "string?"
  }
}
```

**Status Codes:**

- `200` - Success
- `401` - Unauthorized
- `404` - Subscription not found

---

### POST /user/subscription

Create new subscription (for users without active subscription).

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "tierId": "string",
  "frequency": "monthly|yearly",
  "promoCode": "string?",
  "paymentMethodId": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "string",
      "userId": "string",
      "tier": {
        "id": "string",
        "name": "string",
        "features": ["string"],
        "limits": {},
        "supportedFrequencies": ["monthly", "yearly"]
      },
      "frequency": "monthly|yearly",
      "status": "string",
      "isActive": true,
      "currentPeriodStart": "string (ISO 8601)",
      "currentPeriodEnd": "string (ISO 8601)",
      "price": "number",
      "currency": "string",
      "isTrial": "boolean"
    },
    "requiresPaymentConfirmation": false,
    "clientSecret": "string?"
  }
}
```

**Notes:**

- `paymentMethodId` from Stripe Elements payment collection
- `clientSecret` returned if payment requires additional 3D Secure confirmation
- Backend handles Stripe payment processing

**Status Codes:**

- `201` - Subscription created
- `400` - Invalid request
- `401` - Unauthorized
- `409` - Subscription already exists

---

### DELETE /user/subscription

Cancel user subscription.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "reason": "string?",
  "cancelAtPeriodEnd": true
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "string",
      "userId": "string",
      "status": "string",
      "isActive": false,
      "cancelAtPeriodEnd": "boolean",
      "currentPeriodEnd": "string (ISO 8601)",
      "expirationDate": "string (ISO 8601)"
    },
    "cancelEffectiveDate": "2025-11-01T00:00:00Z"
  }
}
```

**Notes:**

- If `cancelAtPeriodEnd` is `true`, cancellation at end of billing period
- If `false`, immediate cancellation
- User retains access until `cancelEffectiveDate`

**Status Codes:**

- `200` - Success
- `400` - Invalid request
- `401` - Unauthorized
- `404` - Subscription not found

---

### POST /subscription/promo/validate

Validate promo code and calculate discounted price.

**Request:**

```json
{
  "promoCode": "string",
  "tierId": "string",
  "frequency": "monthly|yearly"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "isValid": true,
    "discount": {
      "type": "percentage|fixed",
      "value": 20,
      "duration": "once|repeating|forever",
      "durationInMonths": 6
    },
    "newPrice": 23.99
  }
}
```

**Status Codes:**

- `200` - Valid or invalid code (both return 200 with isValid flag)
- `400` - Invalid request format
- `401` - Unauthorized

---

### POST /subscription/trial/start

Start trial subscription without payment method.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "tierId": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "string",
      "userId": "string",
      "tier": {
        "id": "string",
        "name": "string",
        "features": ["string"],
        "limits": {}
      },
      "status": "active",
      "isActive": true,
      "isTrial": true,
      "trialEndDate": "2025-11-13T00:00:00Z",
      "price": 0,
      "currency": "USD"
    },
    "trialEndDate": "2025-11-13T00:00:00Z"
  }
}
```

**Notes:**

- Trial duration determined by backend configuration (typically 14 days)
- User can upgrade to paid during or after trial

**Status Codes:**

- `201` - Trial created
- `400` - Invalid request
- `401` - Unauthorized
- `409` - Trial already active or subscription exists

---

## Billing Endpoints

### POST /billing/payment-intent

Create Stripe payment intent for subscription setup.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "tierId": "string",
  "frequency": "monthly|yearly",
  "promoCode": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "clientSecret": "pi_xxx_secret_xxx",
    "amount": 2999,
    "currency": "usd"
  }
}
```

**Notes:**

- Amount in cents (2999 = $29.99)
- `clientSecret` used with Stripe Elements for payment collection
- Amount reflects tier pricing with promo code discount applied

**Status Codes:**

- `200` - Payment intent created
- `400` - Invalid request
- `401` - Unauthorized
- `500` - Stripe API error

---

### POST /billing/webhook

Handle Stripe webhooks (internal, not called by frontend).

**Headers Required:**

- `Stripe-Signature: t=...,v1=...` (Stripe signature verification)

**Request Body:**

```json
{
  "id": "evt_xxxxx",
  "object": "event",
  "type": "payment_intent.succeeded|charge.refunded|customer.subscription.updated",
  "data": {
    "object": {}
  }
}
```

**Response:**

```json
{
  "success": true,
  "received": true
}
```

**Notes:**

- Backend-only endpoint
- Handles async payment confirmations, failures, subscription updates
- Updates subscription status based on Stripe events
- Not called directly by frontend

**Status Codes:**

- `200` - Webhook processed
- `400` - Invalid webhook signature
- `500` - Processing error

---

### PUT /user/subscription/auto-renewal

Update auto-renewal setting for subscription.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "autoRenewal": true
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "string",
      "userId": "string",
      "autoRenewal": true,
      "currentPeriodEnd": "string (ISO 8601)",
      "updatedAt": "string (ISO 8601)"
    }
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Invalid request
- `401` - Unauthorized
- `404` - Subscription not found

---

## Onboarding Endpoints

### GET /business/onboarding

Get current user's onboarding data.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "businessName": "string",
    "website": "string?",
    "address": {
      "street": "string",
      "city": "string",
      "state": "string",
      "zip": "string",
      "country": "string"
    },
    "products": [
      {
        "id": "string",
        "name": "string",
        "problem": "string"
      }
    ],
    "step3": {
      "niche": "string",
      "ica": "string",
      "valueProposition": "string"
    },
    "step4": {
      "coreValues": ["string"],
      "coreValuesStatus": "Not started|In progress|Completed",
      "purpose": "string",
      "purposeStatus": "Not started|In progress|Completed",
      "vision": "string",
      "visionStatus": "Not started|In progress|Completed"
    }
  }
}
```

**Status Codes:**

- `200` - Success
- `401` - Unauthorized
- `404` - Onboarding not found

---

### PUT /business/onboarding

Update onboarding data (partial or complete).

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "businessName": "string?",
  "website": "string?",
  "address": {
    "street": "string?",
    "city": "string?",
    "state": "string?",
    "zip": "string?",
    "country": "string?"
  },
  "products": [
    {
      "id": "string?",
      "name": "string",
      "problem": "string"
    }
  ],
  "step3": {
    "niche": "string?",
    "ica": "string?",
    "valueProposition": "string?"
  },
  "step4": {
    "coreValues": ["string"],
    "coreValuesStatus": "string",
    "purpose": "string",
    "purposeStatus": "string",
    "vision": "string",
    "visionStatus": "string"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "businessName": "string",
    "website": "string?",
    "address": { ... },
    "products": [ ... ],
    "step3": { ... },
    "step4": { ... }
  }
}
```

**Products Field Behavior (Smart Merge):**
- Products **with `id`**: Updates existing product
- Products **without `id`** (null/omitted): Creates new product with generated ID
- Products **not in array**: Deleted from business
- **Optional**: Can omit `products` field entirely to leave products unchanged

**Status Codes:**

- `200` - Success
- `400` - Invalid request
- `401` - Unauthorized
- `404` - Onboarding not found

---

### PUT /business/onboarding/products

Bulk update all products - replaces entire product list.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "products": [
    {
      "id": "string?",
      "name": "string",
      "problem": "string"
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "name": "string",
      "problem": "string"
    }
  ]
}
```

**Behavior (Smart Merge):**
- Products **with `id`**: Updates existing product
- Products **without `id`**: Creates new product with generated ID
- Products **not in array**: Deleted from business

**Use Case:** Replace entire products list in one transaction (e.g., onboarding form submission).

**Status Codes:**

- `200` - Success
- `400` - Invalid request
- `401` - Unauthorized
- `404` - Onboarding not found

---

## Business Foundation Endpoints

### PATCH /business/foundation

Update a single field of business foundation using field/value pattern.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "field": "string (required)",
  "value": "any (required)"
}
```

**Field Options:**

| Field | Value Type | Description |
|-------|-----------|-------------|
| `vision` | string | Long-term vision statement |
| `purpose` | string | Company purpose/mission |
| `coreValues` | string[] | Array of core value names |
| `valueProposition` | string | Unique value proposition |
| `businessName` | string | Company name |
| `targetMarket` | string | Target market description |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "tenantId": "string",
    "completionPercentage": "number",
    "field": "string",
    "value": "any",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Invalid field or value
- `401` - Unauthorized
- `404` - Business foundation not found

---

### GET /business/foundation/values/{id}

Get a specific core value by ID.

**Path Parameters:**

- `id` - Core value ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "tenantId": "string",
    "businessFoundationId": "string",
    "name": "string",
    "meaning": "string?",
    "implementation": "string?",
    "behaviors": ["string"],
    "displayOrder": "number",
    "isActive": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string? (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `401` - Unauthorized
- `404` - Core value not found

---

## Tenant Settings Endpoints

### GET /tenants/settings

Get current tenant settings (KPI configuration, etc).

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}` (auto-injected by frontend)

**Response:**

```json
{
  "success": true,
  "data": {
    "targetLineMode": "single" | "three"
  }
}
```

**Response Fields:**
- `targetLineMode` (string): KPI target line configuration
  - `"single"` - Only expected target line (default)
  - `"three"` - Expected, optimal, and minimal target lines

**Status Codes:**
- `200` - Success
- `401` - Unauthorized (missing/invalid token)
- `404` - Tenant not found
- `500` - Server error

---

### PUT /tenants/settings

Update current tenant settings.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}` (auto-injected by frontend)
- `Content-Type: application/json`

**Request:**

```json
{
  "targetLineMode": "single" | "three"
}
```

**Request Fields:**
- `targetLineMode` (string, required): Target line mode configuration
  - Valid values: `"single"` or `"three"`

**Response:**

```json
{
  "success": true,
  "data": {
    "targetLineMode": "single" | "three"
  }
}
```

**Business Rules:**
- Mode change does NOT affect existing KPI data
- Single mode: UI hides optimal/minimal target inputs
- Three mode: UI shows all three target inputs
- Charts always show expected line; optional lines only if data exists

**Status Codes:**
- `200` - Success
- `400` - Invalid request (missing field or invalid value)
- `401` - Unauthorized (missing/invalid token)
- `404` - Tenant not found
- `500` - Server error

---

## Error Responses

All Account Service endpoints follow the standard error format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `INVALID_CREDENTIALS` - Login failed
- `EMAIL_ALREADY_EXISTS` - Registration with existing email
- `INVALID_TOKEN` - Expired or invalid token
- `SUBSCRIPTION_LIMIT_REACHED` - User at subscription limit
- `PAYMENT_FAILED` - Payment processing error
- `PROMO_CODE_INVALID` - Invalid or expired promo code
- `UNAUTHORIZED` - User lacks required permissions

---

**Navigation:**

- [← Back to Index](./index.md)
- [Account API Specs →](./account-api.md)
- [Admin API Specs →](./admin-api.md)
- [Business Foundation Specs →](./business-foundation-api.md)
