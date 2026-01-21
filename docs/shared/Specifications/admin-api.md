# Admin API Specification

**Version:** 1.0  
**Status:** Verified Against Implementation  
**Last Updated:** December 30, 2025  
**Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`

---

## Overview

The Admin API provides administrative capabilities for managing user subscriptions, trial extensions, discount codes, and tenant ownership.

**Authentication Required:** Admin role (JWT with "Admin" role claim)

---

## Admin Tenant Management Endpoints

### PUT /admin/tenants/{tenantId}/owner

Change the owner of a tenant (admin only).

**Path Parameters:**

- `tenantId` (string, GUID) - The tenant ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "newOwnerPersonId": "string (GUID)"
}
```

**Request Validation:**

- `newOwnerPersonId`: Required, must be a valid GUID
- Person must exist and belong to the tenant
- Person must be linked to an active user account
- New owner must be different from current owner (if any)

**Response:**

```json
{
  "success": true,
  "data": {
    "tenantId": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Example Tenant",
    "ownerUserId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "updatedAt": "2026-01-21T15:30:00Z"
  }
}
```

**Status Codes:**

- `200 OK` - Tenant owner changed successfully
- `400 Bad Request` - Invalid request or validation error
  - Invalid tenant ID format
  - Invalid person ID format
  - Person not linked to user account
  - User not active
  - Person doesn't belong to tenant
  - New owner same as current owner
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Tenant or person not found

**Error Response Example:**

```json
{
  "success": false,
  "error": "Person must be linked to an active user account"
}
```

**Notes:**

- The endpoint accepts a `personId` (not `userId`) because the admin portal works with people records
- Backend validates that the person is linked to an active user and resolves the user ID automatically
- Person must belong to the same tenant whose owner is being changed
- User linked to the person must be in Active status
- Operation is logged for audit purposes
- Can change owner even if owner was already set (unlike initial owner setup)

**Implementation:**

- Controller: `TenantManagementController.ChangeTenantOwner()`
- Command: `ChangeTenantOwnerCommand`
- Handler: `ChangeTenantOwnerCommandHandler`
- Domain: `Tenant.ChangeOwner(UserId)`

---

## Admin Subscriber Management Endpoints

### GET /admin/subscribers

Get paginated list of subscribers (tenants with subscriptions) with filtering and sorting.

**Query Parameters:**

- `page` (number, default: 1) - Page number (1-based)
- `pageSize` (number, default: 50) - Items per page (1-100)
- `search` (string, optional) - Search by tenant name or email (case-insensitive partial match)
- `status` (string, optional) - Filter by subscription status ("Active", "Trialing", "PastDue", "Canceled", "Expired")
- `tier` (string, optional) - Filter by subscription tier ID (GUID)
- `renewalFrequency` (string, optional) - Filter by billing frequency ("Monthly", "Yearly")
- `sortBy` (string, default: "CreatedAt") - Sort field ("Name", "CreatedAt", "Status", "TierId", "Frequency")
- `sortOrder` (string, default: "Descending") - Sort direction ("Ascending", "Descending")

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "items": [
    {
      "tenantId": "550e8400-e29b-41d4-a716-446655440000",
      "businessName": "Acme Corporation",
      "contactName": "John Doe",
      "contactEmail": "john.doe@acme.com",
      "owner": {
        "userId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "personId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "name": "Jane Smith",
        "email": "jane.smith@acme.com"
      },
      "subscription": {
        "subscriptionId": "123e4567-e89b-12d3-a456-426614174000",
        "status": "Active",
        "currentTier": {
          "id": "tier-professional",
          "name": "professional",
          "displayName": "Professional"
        },
        "billingInfo": {
          "frequency": "Monthly",
          "monthlyRecurringRevenue": 99.99,
          "currentPeriodStart": "2025-12-01T00:00:00Z",
          "currentPeriodEnd": "2026-01-01T00:00:00Z",
          "nextBillingDate": "2026-01-01T00:00:00Z"
        }
      },
      "usage": {
        "goalsCount": 12,
        "goalsLimit": 50,
        "measuresCount": 35,
        "measuresLimit": 200,
        "actionsCount": 87,
        "actionsLimit": null,
        "usersCount": 5
      },
      "createdAt": "2025-10-01T12:00:00Z",
      "lastActivityAt": "2025-12-30T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 150,
    "totalPages": 3
  }
}
```

**Field Descriptions:**

- `owner`: Optional. The designated owner of the tenant (set via PUT /admin/tenants/{tenantId}/owner)
  - `userId`: User ID of the owner
  - `personId`: Person ID of the owner
  - `name`: Full name of the owner (from Person record)
  - `email`: Email address of the owner (from Person record)
  - Will be `null` if no owner has been explicitly assigned

**Status Codes:**

- `200 OK` - Success
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token

**Notes:**

- Requires admin authentication
- Returns only tenants that have active subscriptions
- Contact info represents the primary/first active user in the tenant
- Owner info represents the explicitly designated owner (may differ from contact)
- Last activity is determined by the most recent user login

**Implementation:**

- Controller: `AdminController.GetSubscribers()`
- Query: `GetSubscribersQuery`
- Handler: `GetSubscribersQueryHandler`

---

### GET /admin/subscribers/{tenantId}

Get comprehensive details about a specific subscriber including payment history, users, and audit logs.

**Path Parameters:**

- `tenantId` (string, GUID) - The tenant ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "businessName": "Acme Corporation",
  "contactName": "John Doe",
  "contactEmail": "john.doe@acme.com",
  "owner": {
    "userId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "personId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Jane Smith",
    "email": "jane.smith@acme.com"
  },
  "subscription": {
    "subscriptionId": "123e4567-e89b-12d3-a456-426614174000",
    "status": "Active",
    "currentTier": {
      "id": "tier-professional",
      "name": "professional",
      "displayName": "Professional"
    },
    "billingInfo": {
      "frequency": "Monthly",
      "monthlyRecurringRevenue": 99.99,
      "currentPeriodStart": "2025-12-01T00:00:00Z",
      "currentPeriodEnd": "2026-01-01T00:00:00Z",
      "nextBillingDate": "2026-01-01T00:00:00Z"
    },
    "lifetimeValue": 599.94,
    "totalPayments": 6
  },
  "users": [
    {
      "userId": "user-1",
      "email": "john.doe@acme.com",
      "firstName": "John",
      "lastName": "Doe",
      "status": "Active",
      "role": "User",
      "createdAt": "2025-10-01T12:00:00Z",
      "lastLoginAt": "2025-12-30T15:30:00Z"
    }
  ],
  "paymentHistory": [
    {
      "paymentId": "payment-123",
      "amount": 99.99,
      "currency": "USD",
      "status": "Succeeded",
      "paymentMethod": "Card",
      "createdAt": "2025-12-01T00:00:00Z",
      "invoiceUrl": "https://stripe.com/invoices/..."
    }
  ],
  "recentAudit": [
    {
      "action": "owner_changed",
      "resourceType": "Tenant",
      "resourceId": "550e8400-e29b-41d4-a716-446655440000",
      "userId": "admin-123",
      "userName": "Admin User",
      "timestamp": "2025-12-28T10:00:00Z",
      "details": "Changed owner to Jane Smith"
    }
  ],
  "usage": {
    "goalsCount": 12,
    "goalsLimit": 50,
    "measuresCount": 35,
    "measuresLimit": 200,
    "actionsCount": 87,
    "actionsLimit": null,
    "usersCount": 5,
    "storageUsed": 1024.5,
    "storageLimit": 10240,
    "apiCallsThisMonth": 1523,
    "featureUsage": {
      "coaching": 45,
      "traction": 120
    }
  },
  "createdAt": "2025-10-01T12:00:00Z",
  "lastActivityAt": "2025-12-30T15:30:00Z",
  "subscriptionHistory": [],
  "featureGrants": [],
  "supportTickets": []
}
```

**Field Descriptions:**

- `owner`: Optional. The designated owner of the tenant (set via PUT /admin/tenants/{tenantId}/owner)
  - `userId`: User ID of the owner
  - `personId`: Person ID of the owner
  - `name`: Full name of the owner (from Person record)
  - `email`: Email address of the owner (from Person record)
  - Will be `null` if no owner has been explicitly assigned

**Status Codes:**

- `200 OK` - Success
- `400 Bad Request` - Invalid tenant ID format
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant not found

**Notes:**

- Requires admin authentication
- Returns comprehensive subscriber information for admin dashboard
- Includes last 20 payment history entries
- Includes last 50 audit log entries
- Contact info represents the primary/first active user
- Owner info represents the explicitly designated owner

**Implementation:**

- Controller: `AdminController.GetSubscriberDetails()`
- Query: `GetSubscriberDetailsQuery`
- Handler: `GetSubscriberDetailsQueryHandler`

---

## Admin Trial Management Endpoints

### PUT /admin/users/{userId}/subscription/trial/extend

Extend trial subscription for a user (admin only).

**Path Parameters:**

- `userId` - User ID to extend trial for

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "newExpirationDate": "2025-12-01T00:00:00Z",
  "reason": "Customer success initiative",
  "extendedBy": "adminUserId"
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
      "currentPeriodStart": "2025-10-01T00:00:00Z",
      "currentPeriodEnd": "2025-11-01T00:00:00Z",
      "expirationDate": "string?",
      "cancelAtPeriodEnd": false,
      "autoRenewal": true,
      "price": 29.99,
      "currency": "USD",
      "isTrial": true,
      "trialEndDate": "2025-12-01T00:00:00Z",
      "trialExtendedBy": "adminUserId",
      "trialExtensionReason": "Customer success initiative"
    },
    "previousExpirationDate": "2025-11-13T00:00:00Z",
    "newExpirationDate": "2025-12-01T00:00:00Z"
  }
}
```

**Status Codes:**

- `200 OK` - Trial extended successfully
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - User not found

**Notes:**

- Requires admin authentication
- Can extend both active and expired trials
- Logged for audit purposes

---

### GET /admin/users/{userId}/subscription/trial/history

Get trial extension history for a user (admin only).

**Path Parameters:**

- `userId` - User ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "userId": "string",
      "previousExpirationDate": "string (ISO 8601)",
      "newExpirationDate": "string (ISO 8601)",
      "extendedBy": "string (Admin User ID)",
      "reason": "string",
      "extendedAt": "string (ISO 8601)"
    }
  ]
}
```

**Status Codes:**

- `200 OK` - Success
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - User not found

---

## Discount Code Management Endpoints

**Base Path:** `/admin/discount-codes`

### GET /admin/discount-codes

Get paginated list of discount codes with optional filtering and sorting.

**Query Parameters:**

- `page` (number, default: 1) - Page number (1-based)
- `pageSize` (number, default: 20) - Items per page (1-100)
- `status` (string, optional) - Filter by status ("active", "inactive", "expired", or null for all)
- `search` (string, optional) - Search by discount code (case-insensitive partial match)
- `sortBy` (string, default: "createdAt") - Sort field ("createdAt", "code", "redemptions", "expiresAt")
- `sortOrder` (string, default: "desc") - Sort direction ("asc" or "desc")

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string (GUID)",
        "code": "string",
        "description": "string",
        "discountType": "percentage | fixed",
        "value": "number",
        "durationInCycles": "number",
        "isActive": "boolean",
        "expiresAt": "string (ISO 8601)?",
        "currentRedemptions": "number",
        "maxRedemptions": "number",
        "applicableTiers": ["string"],
        "applicableFrequencies": ["string"],
        "isOneTimeUsePerTenant": "boolean",
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)"
      }
    ],
    "pagination": {
      "page": "number",
      "pageSize": "number",
      "totalCount": "number",
      "totalPages": "number",
      "hasNext": "boolean",
      "hasPrevious": "boolean"
    }
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Invalid query parameters
- `401` - Unauthorized (missing or invalid admin token)

---

### GET /admin/discount-codes/{id}

Get comprehensive details of a specific discount code.

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "description": "string",
    "discountType": "percentage | fixed",
    "value": "number",
    "durationInCycles": "number",
    "isActive": "boolean",
    "expiresAt": "string (ISO 8601)?",
    "currentRedemptions": "number",
    "maxRedemptions": "number",
    "applicableTiers": ["string"],
    "applicableFrequencies": ["string"],
    "isOneTimeUsePerTenant": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Invalid discount code ID format
- `401` - Unauthorized
- `404` - Discount code not found

---

### POST /admin/discount-codes

Create a new discount code.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "code": "string",
  "description": "string",
  "discountType": "percentage | fixed",
  "value": "number",
  "durationInCycles": "number",
  "maxRedemptions": "number?",
  "applicableTiers": ["string"]?,
  "applicableFrequencies": ["string"]?,
  "isOneTimeUsePerTenant": "boolean",
  "expiresAt": "string (ISO 8601)?"
}
```

**Validation Rules:**

- `code`: 4-20 characters, uppercase letters and numbers only
- `discountType`: "percentage" or "fixed"
- `value`: For percentage: 1-100 (inclusive), For fixed: > 0
- `durationInCycles`: Positive integer (number of billing cycles)
- `applicableTiers`: Valid values: ["starter", "professional", "enterprise"] or empty for all
- `applicableFrequencies`: Valid values: ["monthly", "annual"] or empty for all

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "description": "string",
    "discountType": "percentage | fixed",
    "value": "number",
    "durationInCycles": "number",
    "isActive": "boolean",
    "expiresAt": "string (ISO 8601)?",
    "currentRedemptions": "number",
    "maxRedemptions": "number",
    "applicableTiers": ["string"],
    "applicableFrequencies": ["string"],
    "isOneTimeUsePerTenant": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `201` - Created (includes Location header with resource URL)
- `400` - Validation error
- `401` - Unauthorized
- `409` - Conflict (discount code already exists)

---

### PATCH /admin/discount-codes/{id}

Update an existing discount code (partial update).

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "description": "string?",
  "maxRedemptions": "number?",
  "expiresAt": "string (ISO 8601)?",
  "applicableTiers": ["string"]?,
  "applicableFrequencies": ["string"]?,
  "isOneTimeUsePerTenant": "boolean?"
}
```

**Immutable Fields (cannot be updated):**

- `code` - Create new code instead
- `discountType` - Create new code instead
- `value` - Create new code instead
- `durationInCycles` - Create new code instead

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "description": "string",
    "discountType": "percentage | fixed",
    "value": "number",
    "durationInCycles": "number",
    "isActive": "boolean",
    "expiresAt": "string (ISO 8601)?",
    "currentRedemptions": "number",
    "maxRedemptions": "number",
    "applicableTiers": ["string"],
    "applicableFrequencies": ["string"],
    "isOneTimeUsePerTenant": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Validation error or attempting to update immutable fields
- `401` - Unauthorized
- `404` - Discount code not found

---

### POST /admin/discount-codes/{id}/enable

Enable a previously disabled discount code.

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "isActive": true,
    "expiresAt": "string (ISO 8601)?",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Code already active or expired
- `401` - Unauthorized
- `404` - Discount code not found

---

### POST /admin/discount-codes/{id}/disable

Disable an active discount code to prevent new redemptions.

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "isActive": false,
    "expiresAt": "string (ISO 8601)?",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Notes:**

- Existing redemptions remain unaffected
- Preserves redemption history and statistics
- Use this instead of DELETE for codes with redemptions

**Status Codes:**

- `200` - Success
- `400` - Code already inactive
- `401` - Unauthorized
- `404` - Discount code not found

---

### DELETE /admin/discount-codes/{id}

Delete a discount code permanently (only if never redeemed).

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```
204 No Content
```

**Restrictions:**

- Can ONLY delete codes with **zero redemptions** (`currentRedemptions = 0`)
- Codes with redemption history CANNOT be deleted (returns 409 Conflict)
- For codes with redemptions, use `POST /admin/discount-codes/{id}/disable` instead

**Status Codes:**

- `204` - No Content (successful deletion)
- `400` - Invalid discount code ID format
- `401` - Unauthorized
- `404` - Discount code not found
- `409` - Conflict (code has redemptions and cannot be deleted)

---

## Error Responses

All Admin API endpoints follow the standard error format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `UNAUTHORIZED` - User lacks admin role
- `INVALID_CODE_FORMAT` - Discount code doesn't meet format requirements
- `CODE_ALREADY_EXISTS` - Code is already in use
- `CODE_HAS_REDEMPTIONS` - Cannot delete code with existing redemptions
- `INVALID_REQUEST` - Malformed request or missing required fields

---

**Navigation:**

- [← Back to Index](./index.md)
