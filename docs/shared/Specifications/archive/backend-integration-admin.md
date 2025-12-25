# Backend Integration Specification - Admin Portal

This document provides a comprehensive specification of all backend API endpoints used by the PurposePath Admin Portal (excluding the coaching service).

**Base URL:** `https://api.dev.purposepath.app/admin/api/v1`  
**Coaching API Base URL:** `https://api.dev.purposepath.app/coaching/api/v1/admin` (for AI/Topic endpoints)

**Authentication:** All endpoints require `Authorization: Bearer {access_token}` header  
**CSRF Protection:** State-changing operations (POST, PUT, PATCH, DELETE) require `X-CSRF-Token: {csrf_token}` header

---

## Table of Contents

1. [Authentication](#authentication)
2. [Subscribers](#subscribers)
3. [Subscriptions](#subscriptions)
4. [Discount Codes](#discount-codes)
5. [Plans](#plans)
6. [Features](#features)
7. [Users](#users)
8. [Settings](#settings)
9. [Email Templates](#email-templates)
10. [Audit Logs](#audit-logs)
11. [AI/Topic Management](#aitopic-management)
12. [LLM Management](#llm-management)

---

## Authentication

### POST /auth/validate

Validates Google OAuth token and returns admin user information with backend JWT tokens.

**Request Body:**
```json
{
  "googleAccessToken": "string (JWT ID token from Google)",
  "email": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "email": "string",
    "name": "string",
    "isPortalAdmin": true,
    "lastLoginAt": "string (ISO 8601)"
  },
  "accessToken": "string (JWT access token)",
  "refreshToken": "string (JWT refresh token)",
  "expiresIn": 3600
}
```

**Constraints:**
- User must be a member of the "Portal Admins" Google Group
- Returns 403 if user is not authorized

---

### POST /auth/refresh

Refreshes an expired access token using a refresh token.

**Request Body:**
```json
{
  "refreshToken": "string"
}
```

**Response:**
```json
{
  "success": true,
  "accessToken": "string",
  "refreshToken": "string (optional, new refresh token if rotated)",
  "expiresIn": 3600
}
```

**Constraints:**
- Refresh token must be valid and not expired
- Returns 401 if refresh token is invalid

---

### POST /auth/logout

Logs out the current user (client-side only, no backend call required).

---

## Subscribers

### GET /subscribers

Get paginated list of subscribers with optional filtering.

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `pageSize` (number, default: 50) - Items per page
- `search` (string, optional) - Search by business name, owner name, or email
- `tier` (string, optional) - Filter by subscription tier
- `status` (string, optional) - Filter by subscription status: `active`, `inactive`, `trial`, `expired`
- `renewalFrequency` (string, optional) - Filter by billing frequency: `monthly`, `yearly`

**Response:**
```json
{
  "items": [
    {
      "tenantId": "string",
      "businessName": "string",
      "contactName": "string | null",
      "contactEmail": "string | null",
      "subscription": {
        "status": "string",
        "tier": "string",
        "frequency": "string",
        "currentPeriodStart": "string (ISO 8601)",
        "currentPeriodEnd": "string (ISO 8601)",
        "isTrialing": boolean,
        "trialEndDate": "string (ISO 8601) | null"
      } | null,
      "createdAt": "string (ISO 8601)",
      "lastActivityAt": "string (ISO 8601) | null"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 100,
    "totalPages": 2
  }
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### GET /subscribers/:tenantId

Get detailed information for a specific subscriber.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Response:**
```json
{
  "tenant": {
    "id": "string",
    "businessName": "string",
    "website": "string",
    "address": {
      "street": "string",
      "city": "string",
      "state": "string",
      "postalCode": "string",
      "country": "string"
    },
    "createdAt": "string (ISO 8601)"
  },
  "owner": {
    "id": "string",
    "name": "string",
    "email": "string",
    "phone": "string"
  },
  "subscription": {
    "id": "string",
    "status": "active | inactive | trial | expired",
    "tier": "string",
    "frequency": "monthly | yearly",
    "currentPeriodStart": "string (ISO 8601)",
    "currentPeriodEnd": "string (ISO 8601)",
    "isTrialing": boolean,
    "trialEndDate": "string (ISO 8601) | null",
    "price": number,
    "currency": "string",
    "billingProvider": "string",
    "providerSubscriptionId": "string",
    "autoRenewal": boolean
  },
  "usage": {
    "goals": number,
    "kpis": number,
    "actions": number,
    "strategies": number,
    "attachments": number,
    "reports": number
  },
  "features": ["string"],
  "tenantSpecificFeatures": [
    {
      "feature": "string",
      "grantedAt": "string (ISO 8601)",
      "grantedBy": "string",
      "expiresAt": "string (ISO 8601) | null",
      "reason": "string"
    }
  ]
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

## Subscriptions

### POST /subscriptions/:tenantId/extend-trial

Extend trial period for a tenant.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Request Body:**
```json
{
  "newTrialEndDate": "string (ISO 8601)",
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `newTrialEndDate` must be in the future
- `reason` is required for audit purposes

---

### POST /subscriptions/:tenantId/apply-discount

Apply a discount to a subscription.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Request Body:**
```json
{
  "discountType": "percentage | fixed_amount",
  "discountValue": number,
  "duration": {
    "startDate": "string (ISO 8601)",
    "endDate": "string (ISO 8601) | null"
  },
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `discountType`: `percentage` (0-100) or `fixed_amount` (positive number)
- `reason` is required for audit purposes

---

### POST /subscriptions/:tenantId/extend-billing

Extend billing period for a subscription.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Request Body:**
```json
{
  "newPeriodEndDate": "string (ISO 8601)",
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `newPeriodEndDate` must be in the future
- `reason` is required for audit purposes

---

### POST /subscriptions/:tenantId/grant-feature

Grant an ad-hoc feature to a tenant.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Request Body:**
```json
{
  "featureName": "string",
  "expiresWithPlan": boolean,
  "customExpirationDate": "string (ISO 8601) | null",
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `featureName` must be a valid feature
- If `expiresWithPlan` is true, `customExpirationDate` is ignored
- `reason` is required for audit purposes

---

### POST /subscriptions/:tenantId/designate-test

Designate a tenant as a test account.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Request Body:**
```json
{
  "accountType": "demo | test",
  "unlimitedAccess": boolean,
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `reason` is required for audit purposes

---

### GET /subscriptions/:tenantId/audit-log

Get audit log for subscription changes.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `pageSize` (number, default: 20) - Items per page

**Response:**
```json
{
  "entries": [
    {
      "id": "string",
      "adminEmail": "string",
      "action": "string",
      "targetType": "string",
      "targetId": "string",
      "tenantId": "string",
      "tenantName": "string",
      "details": {},
      "timestamp": "string (ISO 8601)",
      "ipAddress": "string",
      "userAgent": "string"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalCount": 50
  }
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

## Discount Codes

### GET /discount-codes

Get paginated list of discount codes.

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `pageSize` (number, default: 50) - Items per page
- `search` (string, optional) - Search by code name or description
- `status` (string, optional) - Filter by status: `active`, `inactive`, `all`
- `discountType` (string, optional) - Filter by type: `percentage`, `fixed_amount`, `all`
- `applicability` (string, optional) - Filter by applicability: `new_tenants`, `renewals`, `all`

**Response:**
```json
{
  "items": [
    {
      "id": "string",
      "codeName": "string",
      "description": "string",
      "discountType": "percentage | fixed_amount",
      "discountValue": number,
      "applicability": "new_tenants | renewals | all",
      "applicableTiers": ["string"],
      "isSystemWide": boolean,
      "tenantRestrictions": ["string"],
      "isActive": boolean,
      "expiresAt": "string (ISO 8601) | null",
      "usageCount": number,
      "usageLimit": number | null,
      "createdAt": "string (ISO 8601)",
      "createdBy": "string",
      "lastUsedAt": "string (ISO 8601) | null"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 100,
    "totalPages": 2
  }
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### GET /discount-codes/:id

Get discount code by ID.

**Path Parameters:**
- `id` (string, required) - Discount code identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "codeName": "string",
    "description": "string",
    "discountType": "percentage | fixed_amount",
    "discountValue": number,
    "applicability": "new_tenants | renewals | all",
    "applicableTiers": ["string"],
    "isSystemWide": boolean,
    "tenantRestrictions": ["string"],
    "isActive": boolean,
    "expiresAt": "string (ISO 8601) | null",
    "usageCount": number,
    "usageLimit": number | null,
    "createdAt": "string (ISO 8601)",
    "createdBy": "string",
    "lastUsedAt": "string (ISO 8601) | null"
  }
}
```

---

### GET /discount-codes/:id/usage

Get usage history for a discount code.

**Path Parameters:**
- `id` (string, required) - Discount code identifier

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `pageSize` (number, default: 50) - Items per page

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "tenantId": "string",
        "tenantName": "string",
        "usedAt": "string (ISO 8601)",
        "originalAmount": number,
        "discountAmount": number,
        "finalAmount": number
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 50,
      "totalCount": 100,
      "totalPages": 2
    }
  }
}
```

---

### POST /discount-codes

Create a new discount code.

**Request Body:**
```json
{
  "codeName": "string",
  "description": "string",
  "discountType": "percentage | fixed_amount",
  "discountValue": number,
  "applicability": "new_tenants | renewals | all",
  "applicableTiers": ["string"],
  "isSystemWide": boolean,
  "tenantRestrictions": ["string"],
  "expiresAt": "string (ISO 8601) | null",
  "usageLimit": number | null,
  "isActive": boolean
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "codeName": "string",
    "description": "string",
    "discountType": "percentage | fixed_amount",
    "discountValue": number,
    "applicability": "new_tenants | renewals | all",
    "applicableTiers": ["string"],
    "isSystemWide": boolean,
    "tenantRestrictions": ["string"],
    "isActive": boolean,
    "expiresAt": "string (ISO 8601) | null",
    "usageCount": 0,
    "usageLimit": number | null,
    "createdAt": "string (ISO 8601)",
    "createdBy": "string",
    "lastUsedAt": null
  }
}
```

**Constraints:**
- `codeName` must be unique
- `discountType`: `percentage` (0-100) or `fixed_amount` (positive number)
- `discountValue` must be positive

---

### PATCH /discount-codes/:id

Update an existing discount code.

**Path Parameters:**
- `id` (string, required) - Discount code identifier

**Request Body:** (All fields optional)
```json
{
  "codeName": "string",
  "description": "string",
  "discountType": "percentage | fixed_amount",
  "discountValue": number,
  "applicability": "new_tenants | renewals | all",
  "applicableTiers": ["string"],
  "isSystemWide": boolean,
  "tenantRestrictions": ["string"],
  "expiresAt": "string (ISO 8601) | null",
  "usageLimit": number | null,
  "isActive": boolean
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "codeName": "string",
    "description": "string",
    "discountType": "percentage | fixed_amount",
    "discountValue": number,
    "applicability": "new_tenants | renewals | all",
    "applicableTiers": ["string"],
    "isSystemWide": boolean,
    "tenantRestrictions": ["string"],
    "isActive": boolean,
    "expiresAt": "string (ISO 8601) | null",
    "usageCount": number,
    "usageLimit": number | null,
    "createdAt": "string (ISO 8601)",
    "createdBy": "string",
    "lastUsedAt": "string (ISO 8601) | null"
  }
}
```

---

### POST /discount-codes/:id/enable

Enable a discount code.

**Path Parameters:**
- `id` (string, required) - Discount code identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "isActive": true,
    ...
  }
}
```

---

### POST /discount-codes/:id/disable

Disable a discount code.

**Path Parameters:**
- `id` (string, required) - Discount code identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "isActive": false,
    ...
  }
}
```

---

### DELETE /discount-codes/:id

Delete a discount code.

**Path Parameters:**
- `id` (string, required) - Discount code identifier

**Response:** 204 No Content

---

### POST /discount-codes/validate

Validate a discount code for a tenant.

**Request Body:**
```json
{
  "codeName": "string",
  "tenantId": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": boolean,
    "reason": "string (optional)",
    "code": {
      "id": "string",
      "codeName": "string",
      ...
    } | null
  }
}
```

---

## Plans

### GET /plans

Get paginated list of subscription plans/tiers.

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `pageSize` (number, default: 50) - Items per page
- `search` (string, optional) - Search by name or display name
- `status` (string, optional) - Filter by status: `active`, `grandfathered`, `inactive`, `all`

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string",
        "name": "string",
        "displayName": "string",
        "description": "string",
        "featureCount": number,
        "limits": {
          "goals": number | null,
          "kpis": number | null,
          "actions": number | null,
          "strategies": number | null,
          "attachments": number | null,
          "reports": number | null
        },
        "pricing": {
          "monthlyPrice": number,
          "yearlyPrice": number,
          "currency": "string"
        },
        "supportedFrequencies": ["monthly", "yearly"],
        "isActive": boolean,
        "isGrandfathered": boolean,
        "allowNewSubscriptions": boolean,
        "sortOrder": number,
        "usageStats": null,
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 50,
      "totalCount": 100,
      "totalPages": 2
    }
  }
}
```

---

### GET /plans/:id

Get plan by ID.

**Path Parameters:**
- `id` (string, required) - Plan identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "displayName": "string",
    "description": "string",
    "featureCount": number,
    "limits": {
      "goals": number | null,
      "kpis": number | null,
      "actions": number | null,
      "strategies": number | null,
      "attachments": number | null,
      "reports": number | null
    },
    "pricing": {
      "monthlyPrice": number,
      "yearlyPrice": number,
      "currency": "string"
    },
    "supportedFrequencies": ["monthly", "yearly"],
    "isActive": boolean,
    "isGrandfathered": boolean,
    "allowNewSubscriptions": boolean,
    "sortOrder": number,
    "usageStats": null,
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

---

### POST /plans

Create a new plan.

**Request Body:**
```json
{
  "name": "string",
  "displayName": "string",
  "description": "string",
  "features": ["string"],
  "limits": {
    "goals": number | null,
    "kpis": number | null,
    "actions": number | null,
    "strategies": number | null,
    "attachments": number | null,
    "reports": number | null
  },
  "pricing": {
    "monthlyPrice": number,
    "yearlyPrice": number,
    "currency": "string"
  },
  "supportedFrequencies": ["monthly", "yearly"],
  "isActive": boolean,
  "allowNewSubscriptions": boolean
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "displayName": "string",
    "description": "string",
    "featureCount": number,
    "limits": {},
    "pricing": {},
    "supportedFrequencies": [],
    "isActive": boolean,
    "isGrandfathered": false,
    "allowNewSubscriptions": boolean,
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Constraints:**
- `name` must be unique
- `pricing.monthlyPrice` and `pricing.yearlyPrice` must be non-negative
- `pricing.currency` defaults to "USD"

---

### PATCH /plans/:id

Update an existing plan.

**Path Parameters:**
- `id` (string, required) - Plan identifier

**Request Body:** (All fields optional)
```json
{
  "name": "string",
  "displayName": "string",
  "description": "string",
  "features": ["string"],
  "limits": {
    "goals": number | null,
    "kpis": number | null,
    "actions": number | null,
    "strategies": number | null,
    "attachments": number | null,
    "reports": number | null
  },
  "pricing": {
    "monthlyPrice": number,
    "yearlyPrice": number,
    "currency": "string"
  },
  "supportedFrequencies": ["monthly", "yearly"],
  "isActive": boolean,
  "allowNewSubscriptions": boolean
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "displayName": "string",
    "description": "string",
    "featureCount": number,
    "limits": {},
    "pricing": {},
    "supportedFrequencies": [],
    "isActive": boolean,
    "isGrandfathered": boolean,
    "allowNewSubscriptions": boolean,
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

---

### POST /plans/:id/deactivate

Deactivate a plan.

**Path Parameters:**
- `id` (string, required) - Plan identifier

**Request Body:**
```json
{
  "reason": "string",
  "grandfatherExisting": boolean,
  "migrationTierId": "string (optional)",
  "effectiveDate": "string (ISO 8601)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "isActive": false,
    "isGrandfathered": boolean,
    ...
  }
}
```

**Constraints:**
- `reason` is required
- `effectiveDate` must be in the future
- If `grandfatherExisting` is true, existing subscribers keep the plan

---

### POST /plans/:id/validate

Validate plan updates against existing subscriber usage.

**Path Parameters:**
- `id` (string, required) - Plan identifier

**Request Body:** (Same as PATCH /plans/:id)

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": boolean,
    "errors": ["string"],
    "affectedSubscribers": number
  }
}
```

---

### GET /plans/:id/affected-subscribers

Get affected subscribers count for plan deactivation.

**Path Parameters:**
- `id` (string, required) - Plan identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "count": number,
    "subscribers": ["string (tenantId)"]
  }
}
```

---

### DELETE /plans/:id

Delete a plan (only if no subscribers).

**Path Parameters:**
- `id` (string, required) - Plan identifier

**Response:** 204 No Content

**Constraints:**
- Plan must have no active subscribers

---

## Features

### GET /features

Get all available features.

**Response:**
```json
{
  "success": true,
  "data": {
    "features": [
      {
        "name": "string",
        "displayName": "string",
        "description": "string",
        "category": "string",
        "isCore": boolean
      }
    ]
  }
}
```

---

### GET /features/tiers

Get all subscription tiers with their features (for feature matrix).

**Response:**
```json
{
  "success": true,
  "data": {
    "tiers": [
      {
        "id": "string",
        "name": "string",
        "displayName": "string",
        "features": ["string"],
        "isActive": boolean
      }
    ]
  }
}
```

---

### PUT /features/tiers/:tierId

Update features for a specific tier.

**Path Parameters:**
- `tierId` (string, required) - Tier identifier

**Request Body:**
```json
{
  "features": ["string"]
}
```

**Response:** 204 No Content

**Constraints:**
- Core features cannot be disabled
- All features must be valid feature names

---

### POST /features/tiers/:tierId/validate

Validate tier feature update.

**Path Parameters:**
- `tierId` (string, required) - Tier identifier

**Request Body:**
```json
{
  "features": ["string"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": boolean,
    "errors": ["string"],
    "warnings": ["string"]
  }
}
```

---

### GET /features/tenants/:tenantId/grants

Get tenant-specific feature grants.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "feature": "string",
      "grantedAt": "string (ISO 8601)",
      "grantedBy": "string",
      "expiresAt": "string (ISO 8601) | null",
      "reason": "string"
    }
  ]
}
```

---

### POST /features/tenants/:tenantId/grants

Add a feature grant to a specific tenant.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Request Body:**
```json
{
  "feature": "string",
  "expiresAt": "string (ISO 8601) | null",
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "feature": "string",
    "grantedAt": "string (ISO 8601)",
    "grantedBy": "string",
    "expiresAt": "string (ISO 8601) | null",
    "reason": "string"
  }
}
```

---

### DELETE /features/tenants/:tenantId/grants/:feature

Remove a feature grant from a specific tenant.

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier
- `feature` (string, required) - Feature name

**Request Body:**
```json
{
  "reason": "string"
}
```

**Response:** 204 No Content

---

### GET /features/tenants/:tenantId/effective

Get effective features for a tenant (tier + tenant-specific).

**Path Parameters:**
- `tenantId` (string, required) - Tenant identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "tierFeatures": ["string"],
    "tenantFeatures": ["string"],
    "effectiveFeatures": ["string"]
  }
}
```

---

## Users

### GET /users

Get paginated list of users with optional filtering.

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `pageSize` (number, default: 50) - Items per page
- `search` (string, optional) - Search by email, first name, or last name
- `tenantId` (string, optional) - Filter by tenant
- `status` (string, optional) - Filter by status: `active`, `inactive`, `locked`

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string",
        "email": "string",
        "firstName": "string",
        "lastName": "string",
        "tenantId": "string",
        "tenantName": "string",
        "status": "active | inactive | locked",
        "emailVerified": boolean,
        "lastLoginAt": "string (ISO 8601)",
        "createdAt": "string (ISO 8601)",
        "failedLoginAttempts": number,
        "isLocked": boolean
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 50,
      "totalCount": 100,
      "totalPages": 2
    }
  }
}
```

---

### GET /users/:userId

Get detailed information for a specific user including activity history.

**Path Parameters:**
- `userId` (string, required) - User identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "email": "string",
    "firstName": "string",
    "lastName": "string",
    "tenantId": "string",
    "tenantName": "string",
    "status": "active | inactive | locked",
    "emailVerified": boolean,
    "lastLoginAt": "string (ISO 8601)",
    "createdAt": "string (ISO 8601)",
    "failedLoginAttempts": number,
    "isLocked": boolean,
    "activityHistory": {
      "loginHistory": [
        {
          "timestamp": "string (ISO 8601)",
          "ipAddress": "string",
          "userAgent": "string",
          "success": boolean
        }
      ],
      "featureUsage": [
        {
          "feature": "string",
          "usageCount": number,
          "lastUsedAt": "string (ISO 8601)"
        }
      ],
      "subscriptionChanges": [
        {
          "timestamp": "string (ISO 8601)",
          "changeType": "string",
          "details": "string",
          "performedBy": "string"
        }
      ]
    }
  }
}
```

---

### POST /users/:userId/unlock

Unlock a user account (reset failed login attempts).

**Path Parameters:**
- `userId` (string, required) - User identifier

**Request Body:**
```json
{
  "reason": "string",
  "notifyUser": boolean
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `reason` is required for audit purposes

---

### POST /users/:userId/suspend

Suspend a user account.

**Path Parameters:**
- `userId` (string, required) - User identifier

**Request Body:**
```json
{
  "reason": "string",
  "notifyUser": boolean
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `reason` is required for audit purposes

---

### POST /users/:userId/reactivate

Reactivate a suspended user account.

**Path Parameters:**
- `userId` (string, required) - User identifier

**Request Body:**
```json
{
  "reason": "string",
  "notifyUser": boolean
}
```

**Response:**
```json
{
  "success": true,
  "data": null
}
```

**Constraints:**
- `reason` is required for audit purposes

---

## Settings

### GET /settings

Get all settings with optional filtering.

**Query Parameters:**
- `category` (string, optional) - Filter by category: `authentication`, `email`, `billing`, `system`
- `search` (string, optional) - Search by key or description

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "key": "string",
      "value": "string",
      "dataType": "boolean | string | number | json",
      "category": "authentication | email | billing | system",
      "description": "string",
      "defaultValue": "string",
      "isActive": boolean,
      "lastModifiedAt": "string (ISO 8601)",
      "lastModifiedBy": "string"
    }
  ]
}
```

---

### GET /settings/:key

Get a specific setting by key.

**Path Parameters:**
- `key` (string, required) - Setting key

**Response:**
```json
{
  "success": true,
  "data": {
    "key": "string",
    "value": "string",
    "dataType": "boolean | string | number | json",
    "category": "authentication | email | billing | system",
    "description": "string",
    "defaultValue": "string",
    "isActive": boolean,
    "lastModifiedAt": "string (ISO 8601)",
    "lastModifiedBy": "string"
  }
}
```

---

### PATCH /settings/:key

Update a setting value.

**Path Parameters:**
- `key` (string, required) - Setting key

**Request Body:**
```json
{
  "value": "string",
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "key": "string",
    "value": "string",
    "dataType": "boolean | string | number | json",
    "category": "authentication | email | billing | system",
    "description": "string",
    "defaultValue": "string",
    "isActive": boolean,
    "lastModifiedAt": "string (ISO 8601)",
    "lastModifiedBy": "string"
  }
}
```

**Constraints:**
- `value` must match the `dataType` (boolean, string, number, or valid JSON)
- `reason` is required for audit purposes

---

### POST /settings/:key/validate

Validate a setting value before updating.

**Path Parameters:**
- `key` (string, required) - Setting key

**Request Body:**
```json
{
  "value": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": boolean,
    "errors": ["string"]
  }
}
```

---

### POST /settings/:key/reset

Reset a setting to its default value.

**Path Parameters:**
- `key` (string, required) - Setting key

**Request Body:**
```json
{
  "reason": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "key": "string",
    "value": "string (default value)",
    "dataType": "boolean | string | number | json",
    "category": "authentication | email | billing | system",
    "description": "string",
    "defaultValue": "string",
    "isActive": boolean,
    "lastModifiedAt": "string (ISO 8601)",
    "lastModifiedBy": "string"
  }
}
```

**Constraints:**
- `reason` is required for audit purposes

---

## Email Templates

### GET /email-templates

Get all email templates.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "key": "string",
      "subject": "string",
      "bodyHtml": "string",
      "bodyText": "string",
      "fromEmail": "string",
      "fromName": "string",
      "placeholders": ["string"],
      "category": "authentication | billing | notifications",
      "isActive": boolean,
      "lastModifiedAt": "string (ISO 8601)",
      "lastModifiedBy": "string"
    }
  ]
}
```

---

### GET /email-templates/:key

Get a single email template by key.

**Path Parameters:**
- `key` (string, required) - Template key

**Response:**
```json
{
  "success": true,
  "data": {
    "key": "string",
    "subject": "string",
    "bodyHtml": "string",
    "bodyText": "string",
    "fromEmail": "string",
    "fromName": "string",
    "placeholders": ["string"],
    "category": "authentication | billing | notifications",
    "isActive": boolean,
    "lastModifiedAt": "string (ISO 8601)",
    "lastModifiedBy": "string"
  }
}
```

---

### PUT /email-templates/:key

Update an email template.

**Path Parameters:**
- `key` (string, required) - Template key

**Request Body:**
```json
{
  "subject": "string",
  "bodyHtml": "string",
  "bodyText": "string",
  "fromEmail": "string",
  "fromName": "string",
  "reason": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "key": "string",
    "subject": "string",
    "bodyHtml": "string",
    "bodyText": "string",
    "fromEmail": "string",
    "fromName": "string",
    "placeholders": ["string"],
    "category": "authentication | billing | notifications",
    "isActive": boolean,
    "lastModifiedAt": "string (ISO 8601)",
    "lastModifiedBy": "string"
  }
}
```

**Constraints:**
- Templates use RazorLight syntax for variables (e.g., `@Model.VariableName`)
- `bodyHtml` and `bodyText` are required
- `fromEmail` must be a valid email address

---

## Audit Logs

### GET /audit-logs

Get paginated audit logs with optional filtering.

**Query Parameters:**
- `adminEmail` (string, optional) - Filter by admin email
- `actionType` (string, optional) - Filter by action type
- `tenantId` (string, optional) - Filter by tenant
- `startDate` (string, optional) - Start date (ISO 8601)
- `endDate` (string, optional) - End date (ISO 8601)
- `page` (number, default: 1) - Page number
- `pageSize` (number, default: 50) - Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "string",
      "adminEmail": "string",
      "action": "string",
      "targetType": "string",
      "targetId": "string",
      "tenantId": "string",
      "tenantName": "string",
      "details": {},
      "timestamp": "string (ISO 8601)",
      "ipAddress": "string",
      "userAgent": "string"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 100,
    "totalPages": 2
  }
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### GET /audit-logs/:id

Get a single audit log entry by ID.

**Path Parameters:**
- `id` (string, required) - Audit log entry identifier

**Response:**
```json
{
  "id": "string",
  "adminEmail": "string",
  "action": "string",
  "targetType": "string",
  "targetId": "string",
  "tenantId": "string",
  "tenantName": "string",
  "details": {},
  "timestamp": "string (ISO 8601)",
  "ipAddress": "string",
  "userAgent": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### GET /audit-logs/export

Export audit logs to CSV.

**Query Parameters:** (Same as GET /audit-logs)

**Response:** CSV file (Content-Type: text/csv)

---

### GET /audit-logs/action-types

Get available action types for filtering.

**Response:**
```json
["string"]
```

**Note:** Response is returned directly as an array, not wrapped in `ApiResponse`.

---

## AI/Topic Management

**Base URL:** `https://api.dev.purposepath.app/coaching/api/v1/admin`

### GET /topics

Get all topics with optional filtering.

**Query Parameters:**
- `page` (number, optional) - Page number
- `page_size` (number, optional) - Items per page
- `category` (string, optional) - Filter by category
- `topic_type` (string, optional) - Filter by type: `coaching`, `assessment`, `analysis`, `kpi`
- `is_active` (boolean, optional) - Filter by active status
- `search` (string, optional) - Search by topic name or description

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "topic": "string",
      "displayName": "string",
      "description": "string (optional)",
      "versionCount": number,
      "latestVersion": "string"
    }
  ]
}
```

---

### GET /topics/:topic_id

Get a single topic by ID with full details including prompts.

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier

**Response:**
```json
{
  "topic_id": "string",
  "topic_name": "string",
  "category": "string",
  "topic_type": "coaching | assessment | analysis | kpi",
  "description": "string (optional)",
  "model_code": "string",
  "temperature": number,
  "max_tokens": number,
  "top_p": number (optional),
  "frequency_penalty": number (optional),
  "presence_penalty": number (optional),
  "is_active": boolean,
  "display_order": number,
  "prompts": [
    {
      "prompt_type": "system | user | assistant",
      "s3_bucket": "string",
      "s3_key": "string",
      "updated_at": "string (ISO 8601)",
      "updated_by": "string"
    }
  ],
  "allowed_parameters": [
    {
      "name": "string",
      "type": "string | number | boolean | array | object",
      "required": boolean,
      "description": "string (optional)",
      "default": "string | number | boolean | array | object (optional)"
    }
  ],
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "created_by": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### POST /topics

Create a new topic (only for KPI topics).

**Request Body:**
```json
{
  "topic_id": "string",
  "topic_name": "string",
  "category": "string",
  "topic_type": "kpi",
  "description": "string (optional)",
  "model_code": "string",
  "temperature": number,
  "max_tokens": number,
  "top_p": number (optional),
  "frequency_penalty": number (optional),
  "presence_penalty": number (optional),
  "is_active": boolean (optional, default: true),
  "display_order": number (optional),
  "allowed_parameters": [
    {
      "name": "string",
      "type": "string | number | boolean | array | object",
      "required": boolean,
      "description": "string (optional)",
      "default": "string | number | boolean | array | object (optional)"
    }
  ]
}
```

**Response:**
```json
{
  "topic_id": "string",
  "created_at": "string (ISO 8601)",
  "message": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

**Constraints:**
- Only `topic_type: "kpi"` topics can be created via API
- `topic_id` must be unique
- `temperature` must be between 0.0 and 2.0
- `max_tokens` must be positive

---

### PUT /topics/:topic_id

Update topic metadata (excluding prompts).

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier

**Request Body:** (All fields optional)
```json
{
  "topic_name": "string",
  "description": "string",
  "model_code": "string",
  "temperature": number,
  "max_tokens": number,
  "top_p": number,
  "frequency_penalty": number,
  "presence_penalty": number,
  "is_active": boolean,
  "display_order": number,
  "allowed_parameters": [
    {
      "name": "string",
      "type": "string | number | boolean | array | object",
      "required": boolean,
      "description": "string (optional)",
      "default": "string | number | boolean | array | object (optional)"
    }
  ]
}
```

**Response:**
```json
{
  "topic_id": "string",
  "updated_at": "string (ISO 8601)",
  "message": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### DELETE /topics/:topic_id

Delete a topic (soft delete by default, hard delete if specified).

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier

**Query Parameters:**
- `hard_delete` (boolean, optional, default: false) - If true, permanently delete

**Response:**
```json
{
  "topic_id": "string",
  "deleted_at": "string (ISO 8601)",
  "message": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### GET /topics/:topic_id/prompts/:prompt_type

Get prompt content for a specific topic and prompt type.

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier
- `prompt_type` (string, required) - Prompt type: `system`, `user`, `assistant`

**Response:**
```json
{
  "topic_id": "string",
  "prompt_type": "system | user | assistant",
  "content": "string",
  "s3_key": "string",
  "updated_at": "string (ISO 8601)",
  "updated_by": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### POST /topics/:topic_id/prompts

Create a new prompt for a topic.

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier

**Request Body:**
```json
{
  "prompt_type": "system | user | assistant",
  "content": "string"
}
```

**Response:**
```json
{
  "topic_id": "string",
  "prompt_type": "system | user | assistant",
  "s3_key": "string",
  "created_at": "string (ISO 8601)",
  "message": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### PUT /topics/:topic_id/prompts/:prompt_type

Update an existing prompt for a topic.

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier
- `prompt_type` (string, required) - Prompt type: `system`, `user`, `assistant`

**Request Body:**
```json
{
  "content": "string",
  "commit_message": "string (optional)"
}
```

**Response:**
```json
{
  "topic_id": "string",
  "prompt_type": "system | user | assistant",
  "s3_key": "string",
  "updated_at": "string (ISO 8601)",
  "version": "string (optional)",
  "message": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### DELETE /topics/:topic_id/prompts/:prompt_type

Delete a prompt from a topic.

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier
- `prompt_type` (string, required) - Prompt type: `system`, `user`, `assistant`

**Response:** 204 No Content

---

### GET /models

Get available models for topic configuration.

**Response:**
```json
{
  "models": [
    {
      "model_code": "string",
      "model_name": "string",
      "provider": "string",
      "capabilities": ["string"],
      "context_window": number,
      "max_output_tokens": number,
      "cost_per_input_million": number,
      "cost_per_output_million": number,
      "is_active": boolean
    }
  ]
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### POST /topics/validate

Validate topic configuration before saving.

**Request Body:**
```json
{
  "topic_id": "string",
  "topic_name": "string",
  "category": "string",
  "topic_type": "coaching | assessment | analysis | kpi",
  "model_code": "string",
  "temperature": number,
  "max_tokens": number,
  "prompts": [
    {
      "prompt_type": "system | user | assistant",
      "content": "string"
    }
  ] (optional),
  "allowed_parameters": [
    {
      "name": "string",
      "type": "string | number | boolean | array | object",
      "required": boolean,
      "description": "string (optional)",
      "default": "string | number | boolean | array | object (optional)"
    }
  ] (optional)
}
```

**Response:**
```json
{
  "valid": boolean,
  "errors": [
    {
      "field": "string",
      "message": "string",
      "code": "string"
    }
  ] (optional),
  "warnings": [
    {
      "field": "string",
      "message": "string",
      "code": "string"
    }
  ] (optional),
  "suggestions": ["string"] (optional)
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### POST /topics/:topic_id/clone

Clone an existing topic.

**Path Parameters:**
- `topic_id` (string, required) - Source topic identifier

**Request Body:**
```json
{
  "new_topic_id": "string",
  "new_topic_name": "string",
  "copy_prompts": boolean (optional, default: true),
  "is_active": boolean (optional, default: false)
}
```

**Response:**
```json
{
  "topic_id": "string",
  "cloned_from": "string",
  "created_at": "string (ISO 8601)",
  "message": "string"
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### GET /topics/:topic_id/stats

Get usage statistics for a topic.

**Path Parameters:**
- `topic_id` (string, required) - Topic identifier

**Query Parameters:**
- `start_date` (string, optional) - Start date (ISO 8601)
- `end_date` (string, optional) - End date (ISO 8601)

**Response:**
```json
{
  "topic_id": "string",
  "period": {
    "start": "string (ISO 8601)",
    "end": "string (ISO 8601)"
  },
  "usage": {
    "total_conversations": number,
    "active_conversations": number,
    "completed_conversations": number,
    "average_messages_per_conversation": number,
    "total_tokens_used": number,
    "estimated_cost": number
  },
  "performance": {
    "average_conversation_duration_minutes": number,
    "completion_rate": number,
    "user_satisfaction_rating": number
  }
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

### PATCH /topics/bulk

Bulk update multiple topics.

**Request Body:**
```json
{
  "topic_ids": ["string"],
  "updates": {
    "topic_name": "string (optional)",
    "description": "string (optional)",
    "model_code": "string (optional)",
    "temperature": number (optional),
    "max_tokens": number (optional),
    "top_p": number (optional),
    "frequency_penalty": number (optional),
    "presence_penalty": number (optional),
    "is_active": boolean (optional),
    "display_order": number (optional),
    "allowed_parameters": [] (optional)
  }
}
```

**Response:**
```json
{
  "updated": number,
  "results": [
    {
      "topic_id": "string",
      "success": boolean,
      "error": "string (optional)"
    }
  ]
}
```

**Note:** Response is returned directly, not wrapped in `ApiResponse`.

---

## LLM Management

### LLM Interactions

**Base URL:** `https://api.dev.purposepath.app/coaching/api/v1/admin`

### GET /interactions

Get list of all LLM interactions with optional filtering.

**Query Parameters:**
- `page` (number, optional) - Page number
- `page_size` (number, optional) - Items per page
- `category` (string, optional) - Filter by category
- `is_active` (boolean, optional) - Filter by active status
- `search` (string, optional) - Search by interaction name or description

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "code": "string",
        "name": "string",
        "description": "string",
        "category": "string",
        "parameters": [
          {
            "name": "string",
            "type": "string",
            "required": boolean,
            "description": "string",
            "default": "string (optional)"
          }
        ],
        "is_active": boolean,
        "configurations_count": number
      }
    ],
    "total": number,
    "page": number,
    "page_size": number
  }
}
```

---

### GET /interactions/:code

Get detailed information about a specific interaction.

**Path Parameters:**
- `code` (string, required) - Interaction code

**Response:**
```json
{
  "success": true,
  "data": {
    "code": "string",
    "name": "string",
    "description": "string",
    "category": "string",
    "parameters": [
      {
        "name": "string",
        "type": "string",
        "required": boolean,
        "description": "string",
        "default": "string (optional)"
      }
    ],
    "is_active": boolean,
    "configurations": [
      {
        "id": "string",
        "interaction_code": "string",
        "template_topic": "string",
        "template_version": "string",
        "model_code": "string",
        "tier": "string",
        "is_active": boolean
      }
    ]
  }
}
```

---

### POST /interactions/:code/check-compatibility

Check template compatibility with interaction.

**Path Parameters:**
- `code` (string, required) - Interaction code

**Request Body:**
```json
{
  "template_id": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "compatible": boolean,
    "issues": [
      {
        "type": "string",
        "message": "string",
        "severity": "error | warning"
      }
    ],
    "missing_parameters": ["string"],
    "extra_parameters": ["string"]
  }
}
```

---

### LLM Models

**Base URL:** `https://api.dev.purposepath.app/admin/api/v1`

### GET /llm/models

Get list of all LLM models with optional filtering.

**Query Parameters:**
- `page` (number, optional) - Page number
- `page_size` (number, optional) - Items per page
- `provider` (string, optional) - Filter by provider
- `active_only` (boolean, optional) - Filter by active status
- `search` (string, optional) - Search by model name

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "code": "string",
        "name": "string",
        "provider": "string",
        "capabilities": ["string"],
        "context_window": number,
        "max_output_tokens": number,
        "cost_per_1k_tokens": number,
        "is_active": boolean
      }
    ],
    "total": number,
    "page": number,
    "page_size": number
  }
}
```

---

### GET /llm/models/:code

Get detailed information about a specific model.

**Path Parameters:**
- `code` (string, required) - Model code

**Response:**
```json
{
  "success": true,
  "data": {
    "code": "string",
    "name": "string",
    "provider": "string",
    "capabilities": ["string"],
    "context_window": number,
    "max_output_tokens": number,
    "cost_per_1k_tokens": number,
    "is_active": boolean,
    "requirements": [
      {
        "capability": "string",
        "description": "string"
      }
    ]
  }
}
```

---

### GET /llm/models/:code/performance

Get performance metrics for a model.

**Path Parameters:**
- `code` (string, required) - Model code

**Query Parameters:**
- `start_date` (string, optional) - Start date (ISO 8601)
- `end_date` (string, optional) - End date (ISO 8601)

**Response:**
```json
{
  "success": true,
  "data": {
    "code": "string",
    "period": {
      "start": "string (ISO 8601)",
      "end": "string (ISO 8601)"
    },
    "usage": {
      "total_requests": number,
      "total_tokens": number,
      "average_tokens_per_request": number,
      "estimated_cost": number
    },
    "performance": {
      "average_response_time_ms": number,
      "success_rate": number,
      "error_rate": number
    }
  }
}
```

---

### LLM Templates

**Base URL:** `https://api.dev.purposepath.app/coaching/api/v1/admin`

### GET /templates

Get list of all templates with optional filtering.

**Query Parameters:**
- `page` (number, optional) - Page number
- `page_size` (number, optional) - Items per page
- `topic` (string, optional) - Filter by topic
- `is_active` (boolean, optional) - Filter by active status
- `search` (string, optional) - Search by template name

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "topic": "string",
        "display_name": "string",
        "latest_version": "string",
        "version_count": number,
        "is_active": boolean
      }
    ],
    "total": number,
    "page": number,
    "page_size": number
  }
}
```

---

### GET /templates/:topic/versions

Get all versions of a template topic.

**Path Parameters:**
- `topic` (string, required) - Template topic

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "string",
    "display_name": "string",
    "versions": [
      {
        "version": "string",
        "is_latest": boolean,
        "is_active": boolean,
        "created_at": "string (ISO 8601)",
        "last_modified": "string (ISO 8601)",
        "created_by": "string",
        "description": "string (optional)"
      }
    ]
  }
}
```

---

### GET /templates/:topic/versions/:version

Get specific version of a template.

**Path Parameters:**
- `topic` (string, required) - Template topic
- `version` (number, required) - Version number

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "string",
    "version": "string",
    "is_latest": boolean,
    "is_active": boolean,
    "content": "string",
    "parameters": [
      {
        "name": "string",
        "type": "string",
        "required": boolean,
        "description": "string",
        "usage": {
          "count": number,
          "locations": ["string"]
        }
      }
    ],
    "created_at": "string (ISO 8601)",
    "last_modified": "string (ISO 8601)",
    "created_by": "string",
    "description": "string (optional)"
  }
}
```

---

### GET /templates/:topic/latest

Get latest version of a template topic.

**Path Parameters:**
- `topic` (string, required) - Template topic

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "string",
    "version": "string",
    "is_latest": true,
    "is_active": boolean,
    "content": "string",
    "parameters": [],
    "created_at": "string (ISO 8601)",
    "last_modified": "string (ISO 8601)",
    "created_by": "string",
    "description": "string (optional)"
  }
}
```

---

### POST /templates

Create new template version.

**Request Body:**
```json
{
  "topic": "string",
  "content": "string",
  "description": "string (optional)",
  "parameters": [
    {
      "name": "string",
      "type": "string",
      "required": boolean,
      "description": "string",
      "default": "string (optional)"
    }
  ] (optional)
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "string",
    "version": "string",
    "is_latest": boolean,
    "is_active": boolean,
    "content": "string",
    "parameters": [],
    "created_at": "string (ISO 8601)",
    "last_modified": "string (ISO 8601)",
    "created_by": "string",
    "description": "string (optional)"
  }
}
```

---

### PUT /templates/:topic/versions/:version

Update existing template version.

**Path Parameters:**
- `topic` (string, required) - Template topic
- `version` (number, required) - Version number

**Request Body:**
```json
{
  "content": "string",
  "description": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "string",
    "version": "string",
    "is_latest": boolean,
    "is_active": boolean,
    "content": "string",
    "parameters": [],
    "created_at": "string (ISO 8601)",
    "last_modified": "string (ISO 8601)",
    "created_by": "string",
    "description": "string (optional)"
  }
}
```

---

### DELETE /templates/:topic/versions/:version

Delete template version.

**Path Parameters:**
- `topic` (string, required) - Template topic
- `version` (number, required) - Version number

**Response:** 204 No Content

---

### POST /templates/:topic/versions/:version/set-latest

Set a version as the latest.

**Path Parameters:**
- `topic` (string, required) - Template topic
- `version` (number, required) - Version number

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "string",
    "version": "string",
    "is_latest": true,
    ...
  }
}
```

---

### POST /templates/:topic/versions/:version/test

Test template with sample parameters.

**Path Parameters:**
- `topic` (string, required) - Template topic
- `version` (number, required) - Version number

**Request Body:**
```json
{
  "parameters": {
    "key": "value"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "result": "string",
    "tokens_used": number,
    "estimated_cost": number
  }
}
```

---

### GET /templates/:topic/versions/:version/parameters

Get parameter analysis for a template.

**Path Parameters:**
- `topic` (string, required) - Template topic
- `version` (number, required) - Version number

**Response:**
```json
{
  "success": true,
  "data": {
    "parameters": [
      {
        "name": "string",
        "type": "string",
        "required": boolean,
        "description": "string",
        "usage": {
          "count": number,
          "locations": ["string"]
        }
      }
    ],
    "missing_required": ["string"],
    "unused": ["string"]
  }
}
```

---

### POST /templates/:topic/versions/:version/validate-compatibility

Validate template compatibility with interaction.

**Path Parameters:**
- `topic` (string, required) - Template topic
- `version` (number, required) - Version number

**Request Body:**
```json
{
  "interaction_code": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "compatible": boolean,
    "issues": [
      {
        "type": "string",
        "message": "string",
        "severity": "error | warning"
      }
    ],
    "missing_parameters": ["string"],
    "extra_parameters": ["string"]
  }
}
```

---

### LLM Configurations

**Base URL:** `https://api.dev.purposepath.app/admin/api/v1`

### GET /llm/configurations

Get list of all configurations with optional filtering.

**Query Parameters:**
- `page` (number, optional) - Page number
- `page_size` (number, optional) - Items per page
- `interaction_code` (string, optional) - Filter by interaction code
- `tier` (string, optional) - Filter by subscription tier
- `is_active` (boolean, optional) - Filter by active status
- `search` (string, optional) - Search by configuration name

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string",
        "interaction_code": "string",
        "template_topic": "string",
        "template_version": "string",
        "model_code": "string",
        "tier": "string",
        "is_active": boolean,
        "created_at": "string (ISO 8601)",
        "updated_at": "string (ISO 8601)"
      }
    ],
    "total": number,
    "page": number,
    "page_size": number
  }
}
```

---

### GET /llm/configurations/:id

Get detailed information about a specific configuration.

**Path Parameters:**
- `id` (string, required) - Configuration identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "interaction_code": "string",
    "template_topic": "string",
    "template_version": "string",
    "model_code": "string",
    "tier": "string",
    "is_active": boolean,
    "model_parameters": {
      "temperature": number,
      "max_tokens": number,
      "top_p": number (optional),
      "frequency_penalty": number (optional),
      "presence_penalty": number (optional)
    },
    "conflicts": [
      {
        "type": "string",
        "message": "string",
        "severity": "error | warning"
      }
    ],
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)"
  }
}
```

---

### POST /llm/configurations

Create a new configuration.

**Request Body:**
```json
{
  "interaction_code": "string",
  "template_topic": "string",
  "template_version": "string",
  "model_code": "string",
  "tier": "string",
  "model_parameters": {
    "temperature": number,
    "max_tokens": number,
    "top_p": number (optional),
    "frequency_penalty": number (optional),
    "presence_penalty": number (optional)
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "interaction_code": "string",
    "template_topic": "string",
    "template_version": "string",
    "model_code": "string",
    "tier": "string",
    "is_active": false,
    "model_parameters": {},
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)"
  }
}
```

**Constraints:**
- `interaction_code` must be valid
- `template_topic` and `template_version` must exist
- `model_code` must be valid and active
- `tier` must be a valid subscription tier

---

### PUT /llm/configurations/:id

Update an existing configuration.

**Path Parameters:**
- `id` (string, required) - Configuration identifier

**Request Body:** (All fields optional)
```json
{
  "template_topic": "string",
  "template_version": "string",
  "model_code": "string",
  "tier": "string",
  "model_parameters": {
    "temperature": number,
    "max_tokens": number,
    "top_p": number (optional),
    "frequency_penalty": number (optional),
    "presence_penalty": number (optional)
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "interaction_code": "string",
    "template_topic": "string",
    "template_version": "string",
    "model_code": "string",
    "tier": "string",
    "is_active": boolean,
    "model_parameters": {},
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)"
  }
}
```

---

### DELETE /llm/configurations/:id

Delete a configuration.

**Path Parameters:**
- `id` (string, required) - Configuration identifier

**Query Parameters:**
- `permanent` (boolean, optional, default: false) - If true, permanently delete

**Response:** 204 No Content

---

### POST /llm/configurations/:id/activate

Activate a configuration.

**Path Parameters:**
- `id` (string, required) - Configuration identifier

**Request Body:** (Optional)
```json
{
  "resolve_conflicts": "override | skip | error",
  "reason": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "activated": boolean,
    "conflicts_resolved": number,
    "warnings": ["string"]
  }
}
```

---

### POST /llm/configurations/:id/deactivate

Deactivate a configuration.

**Path Parameters:**
- `id` (string, required) - Configuration identifier

**Request Body:**
```json
{
  "reason": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "string",
    "is_active": false,
    ...
  }
}
```

---

### POST /llm/configurations/validate

Validate a configuration before creation or activation.

**Request Body:**
```json
{
  "interaction_code": "string",
  "template_topic": "string",
  "template_version": "string",
  "model_code": "string",
  "tier": "string",
  "model_parameters": {
    "temperature": number,
    "max_tokens": number,
    "top_p": number (optional),
    "frequency_penalty": number (optional),
    "presence_penalty": number (optional)
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": boolean,
    "errors": ["string"],
    "warnings": ["string"],
    "conflicts": [
      {
        "type": "string",
        "message": "string",
        "severity": "error | warning"
      }
    ]
  }
}
```

---

### POST /llm/configurations/bulk-deactivate

Bulk deactivate configurations based on filter.

**Request Body:**
```json
{
  "interaction_code": "string (optional)",
  "tier": "string (optional)",
  "template_topic": "string (optional)",
  "reason": "string (optional)"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deactivated": number,
    "results": [
      {
        "id": "string",
        "success": boolean,
        "error": "string (optional)"
      }
    ]
  }
}
```

---

### GET /llm/configurations/:id/dependencies

Check dependencies before deactivating or deleting.

**Path Parameters:**
- `id` (string, required) - Configuration identifier

**Response:**
```json
{
  "success": true,
  "data": {
    "has_dependencies": boolean,
    "dependencies": [
      {
        "type": "string",
        "id": "string",
        "description": "string"
      }
    ]
  }
}
```

---

### LLM Dashboard

**Base URL:** `https://api.dev.purposepath.app/admin/api/v1`

### GET /llm/dashboard/metrics

Get comprehensive dashboard metrics.

**Query Parameters:**
- `start_date` (string, optional) - Start date (ISO 8601)
- `end_date` (string, optional) - End date (ISO 8601)
- `tier` (string, optional) - Filter by tier
- `interaction_code` (string, optional) - Filter by interaction

**Response:**
```json
{
  "success": true,
  "data": {
    "overview": {
      "total_configurations": number,
      "active_configurations": number,
      "total_interactions": number,
      "total_templates": number
    },
    "configuration_metrics": {
      "total": number,
      "active": number,
      "inactive": number,
      "with_conflicts": number
    },
    "template_metrics": {
      "total_topics": number,
      "total_versions": number,
      "active_versions": number
    },
    "model_metrics": {
      "total_models": number,
      "active_models": number,
      "total_usage": number,
      "estimated_cost": number
    }
  }
}
```

---

### GET /llm/dashboard/trends

Get trend data for configurations.

**Query Parameters:**
- `period` (string, required) - Period: `day`, `week`, `month`
- `start_date` (string, optional) - Start date (ISO 8601)
- `end_date` (string, optional) - End date (ISO 8601)
- `tier` (string, optional) - Filter by tier
- `interaction_code` (string, optional) - Filter by interaction

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "date": "string (ISO 8601)",
      "configurations": number,
      "active_configurations": number,
      "usage": number,
      "cost": number
    }
  ]
}
```

---

### GET /llm/dashboard/health

Get system health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "overall_status": "healthy | degraded | down",
    "services": [
      {
        "name": "string",
        "status": "healthy | degraded | down",
        "last_check": "string (ISO 8601)"
      }
    ],
    "issues": [
      {
        "type": "string",
        "severity": "error | warning",
        "message": "string"
      }
    ],
    "recommendations": ["string"]
  }
}
```

---

### POST /llm/dashboard/validate-system

Trigger system validation.

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": boolean,
    "sections": [
      {
        "name": "string",
        "valid": boolean,
        "issues": [
          {
            "type": "string",
            "message": "string",
            "severity": "error | warning"
          }
        ]
      }
    ]
  }
}
```

---

### GET /llm/dashboard/quick-stats

Get quick stats for dashboard header.

**Response:**
```json
{
  "success": true,
  "data": {
    "active_configurations": number,
    "total_interactions": number,
    "total_templates": number,
    "system_health": "healthy | degraded | down"
  }
}
```

---

### GET /llm/dashboard/activity

Get activity feed.

**Query Parameters:**
- `page` (number, default: 1) - Page number
- `per_page` (number, default: 20) - Items per page
- `start_date` (string, optional) - Start date (ISO 8601)
- `end_date` (string, optional) - End date (ISO 8601)
- `tier` (string, optional) - Filter by tier
- `interaction_code` (string, optional) - Filter by interaction

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string",
        "type": "string",
        "description": "string",
        "timestamp": "string (ISO 8601)",
        "user": "string",
        "details": {}
      }
    ],
    "total": number,
    "page": number,
    "per_page": number
  }
}
```

---

## Common Response Structures

### ApiResponse<T>
```json
{
  "success": boolean,
  "data": T,
  "error": "string (optional)",
  "code": "string (optional)",
  "details": {} (optional)
}
```

### PaginatedResponse<T>
```json
{
  "items": T[],
  "pagination": {
    "page": number,
    "pageSize": number,
    "totalCount": number,
    "totalPages": number
  }
}
```

---

## Error Responses

All endpoints may return the following error responses:

**400 Bad Request:**
```json
{
  "success": false,
  "error": "Validation error message",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "error message"
  }
}
```

**401 Unauthorized:**
```json
{
  "success": false,
  "error": "Unauthorized",
  "code": "UNAUTHORIZED"
}
```

**403 Forbidden:**
```json
{
  "success": false,
  "error": "Forbidden",
  "code": "FORBIDDEN"
}
```

**404 Not Found:**
```json
{
  "success": false,
  "error": "Resource not found",
  "code": "NOT_FOUND"
}
```

**409 Conflict:**
```json
{
  "success": false,
  "error": "Conflict message",
  "code": "CONFLICT"
}
```

**422 Unprocessable Entity:**
```json
{
  "success": false,
  "error": "Validation error",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "error message"
  }
}
```

**500+ Server Errors:**
```json
{
  "success": false,
  "error": "Internal server error",
  "code": "INTERNAL_ERROR"
}
```

---

## Notes

1. **Response Wrapping:** Some endpoints return data directly (not wrapped in `ApiResponse`), while others wrap responses in `{ success: true, data: ... }`. This is noted for each endpoint.

2. **Date Formats:** All dates are in ISO 8601 format (e.g., `2024-01-15T10:30:00Z`).

3. **Pagination:** Default page size is typically 50, with options for 25, 50, 100, and 200 items per page.

4. **Authentication:** All endpoints require a valid JWT access token in the `Authorization` header. Token refresh should be handled automatically by the client.

5. **CSRF Protection:** State-changing operations (POST, PUT, PATCH, DELETE) require a CSRF token in the `X-CSRF-Token` header.

6. **Rate Limiting:** Request timeout is 30 seconds. Automatic retry with exponential backoff (max 3 retries) is implemented for transient failures.

---

## Version History

- **2024-01-XX:** Initial specification document created.

