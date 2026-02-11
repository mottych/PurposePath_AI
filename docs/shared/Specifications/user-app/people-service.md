# People & Organizational Structure - Backend Integration Specifications (Part 1: People)

**Version:** 2.0  
**Last Updated:** December 26, 2025  
**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}` (People & Auth endpoints)  
**Default (Localhost):** `http://localhost:8001` (Account)

[← Back to Index](./index.md) | [Part 2: Organizational Structure →](./org-structure-service.md)

## Changelog

| Version | Date | Changes |
|---------|------|----------|
| 2.0 | December 26, 2025 | **BREAKING:** Converted all JSON properties from snake_case to camelCase to match C#/.NET implementation (e.g., `person_id` → `personId`, `first_name` → `firstName`). Query parameters also converted to camelCase. This matches ASP.NET Core default JSON serialization. |
| 1.1 | December 23, 2025 | Migrated People endpoints from Traction service to Account service |
| 1.0 | December 21, 2025 | Initial version |

---

## Overview

The People module manages all person records within a tenant, including employees, consultants, vendors, and other stakeholders. This module also handles Person Types, Tags, and the User-Person linking that enables work item assignments.

### Frontend Implementation

- **Primary Client:** `accountClient` (axios instance) ⚠️ *Changed from tractionClient*
- **Related Files:**
  - `src/services/people-service.ts` - Person CRUD operations
  - `src/services/person-types-service.ts` - Person type management
  - `src/services/person-tags-service.ts` - Tag management

### Key Concepts

- **Person**: Any individual related to the business (may or may not have system access)
- **User**: A Person with PurposePath login credentials
- **PersonType**: Category defining relationship to business (Employee, Vendor, etc.)
- **Tag**: Flexible label for grouping/filtering people
- **Assignable**: Flag indicating if a person can receive work assignments

### Email Verification

A Person's `isEmailVerified` flag is set to `true` when:
1. They accept a user invitation and create their account (primary flow)
2. They complete email verification during password reset

There is no explicit `POST /people/{id}/verify-email` endpoint. Email verification is implicitly handled through the user invitation acceptance flow.

---

## Authentication Changes

### POST /auth/login

User authentication with username/password.

**⚠️ BREAKING CHANGE:** Login now uses `username` instead of `email`.

**Request:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| username | string | Yes | 3-50 characters |
| password | string | Yes | Min 8 characters |

**Response:**

```json
{
  "success": true,
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
    "user": {
      "userId": "string (GUID)",
      "username": "string",
      "personId": "string (GUID)",
      "tenantId": "string (GUID)",
      "avatarUrl": "string?",
      "createdAt": "string (ISO 8601)",
      "updatedAt": "string (ISO 8601)",
      "status": "active | inactive | locked",
      "preferences": {}
    },
    "person": {
      "id": "string (GUID)",
      "firstName": "string",
      "lastName": "string",
      "email": "string?",
      "phone": "string?",
      "title": "string?"
    },
    "tenant": {
      "id": "string (GUID)",
      "name": "string"
    }
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Invalid username or password",
  "code": "INVALID_CREDENTIALS"
}
```

```json
{
  "success": false,
  "error": "Account is locked",
  "code": "ACCOUNT_LOCKED",
  "details": {
    "lockedUntil": "2025-12-22T10:30:00Z"
  }
}
```

**Frontend Handling:**

- Stores `accessToken` → `localStorage.accessToken`
- Stores `refreshToken` → `localStorage.refreshToken`
- Stores `tenant.id` → `localStorage.tenantId`
- Person data available for profile display

---

### POST /auth/forgot-username

Request username reminder via email.

**Request:**

```json
{
  "email": "string"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| email | string | Yes | Valid email format |

**Response (Always 200 to prevent email enumeration):**

```json
{
  "success": true,
  "message": "If the email is associated with any accounts, instructions have been sent."
}
```

**Backend Behavior:**

1. Find all Persons with verified email matching input
2. For each Person linked to a User, include the username
3. Send email listing all associated usernames and tenant names
4. Always return success (even if email not found)

---

### PUT /user/username

Change current user's username.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "newUsername": "string",
  "currentPassword": "string"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| newUsername | string | Yes | 3-50 chars, alphanumeric + `.` `_` `-` `@`, must start with alphanumeric |
| currentPassword | string | Yes | Current password for verification |

**Response:**

```json
{
  "success": true,
  "data": {
    "username": "string",
    "previousUsername": "string",
    "nextChangeAllowedAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Username is already taken",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "newUsername"
  }
}
```

```json
{
  "success": false,
  "error": "Username can only be changed once every 30 days",
  "code": "RATE_LIMIT_EXCEEDED",
  "details": {
    "nextChangeAllowedAt": "2025-01-15T10:30:00Z"
  }
}
```

```json
{
  "success": false,
  "error": "Invalid current password",
  "code": "INVALID_CREDENTIALS"
}
```

**Business Rules:**

- Username must be globally unique (case-insensitive)
- Maximum one change per 30 days
- Previous username reserved for 90 days (cannot be claimed by others)
- Email notification sent to linked Person's email

---

## People Endpoints

### GET /people

List people with filtering and pagination.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | `active` | Filter: `active`, `inactive`, `all` |
| isAssignable | boolean | - | Filter by assignable flag |
| personTypeId | string (GUID) | - | Filter by person type |
| tags | string | - | Comma-separated tag GUIDs (any match) |
| search | string | - | Search by name, email, or title |
| page | number | 1 | Page number (1-based) |
| pageSize | number | 20 | Items per page (max 100) |
| sortBy | string | `name` | Sort field: `name`, `createdAt`, `type` |
| sortOrder | string | `asc` | Sort order: `asc`, `desc` |

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string (GUID)",
        "firstName": "string",
        "lastName": "string",
        "email": "string?",
        "isEmailVerified": "boolean",
        "phone": "string?",
        "title": "string?",
        "personType": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string"
        },
        "isActive": "boolean",
        "isAssignable": "boolean",
        "primaryRole": {
          "id": "string (GUID)",
          "name": "string"
        },
        "tags": [
          {
            "id": "string (GUID)",
            "name": "string"
          }
        ],
        "hasSystemAccess": "boolean",
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)?"
      }
    ],
    "pagination": {
      "page": "number",
      "pageSize": "number",
      "totalItems": "number",
      "totalPages": "number"
    }
  }
}
```

---

### GET /people/assignable

Get list of people available for work assignment dropdowns.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| tags | string | - | Comma-separated tag GUIDs (any match) |
| personTypeId | string (GUID) | - | Filter by person type |
| search | string | - | Search by name |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "name": "string",
      "title": "string?",
      "primaryRole": "string?",
      "isCurrentUser": "boolean"
    }
  ]
}
```

**Notes:**

- Returns only people where `isActive = true` AND `isAssignable = true`
- `isCurrentUser` is `true` if this Person is linked to the authenticated User
- Sorted alphabetically by name, with current user first

---

### GET /people/{id}

Get detailed person information.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "firstName": "string",
    "lastName": "string",
    "email": "string?",
    "isEmailVerified": "boolean",
    "phone": "string?",
    "title": "string?",
    "personType": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "isActive": "boolean",
    "isAssignable": "boolean",
    "notes": "string?",
    "tags": [
      {
        "id": "string (GUID)",
        "name": "string"
      }
    ],
    "roles": [
      {
        "id": "string (GUID)",
        "roleId": "string (GUID)",
        "roleCode": "string",
        "roleName": "string",
        "isPrimary": "boolean",
        "effectiveDate": "string (ISO 8601)",
        "terminationDate": "string (ISO 8601)?"
      }
    ],
    "linkedUserId": "string (GUID)?",
    "hasSystemAccess": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?",
    "createdBy": "string (GUID)",
    "updatedBy": "string (GUID)?"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Person not found",
  "code": "RESOURCE_NOT_FOUND",
  "details": {
    "resourceType": "Person",
    "resourceId": "guid"
  }
}
```

---

### POST /people

Create a new person.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "firstName": "string",
  "lastName": "string",
  "email": "string?",
  "phone": "string?",
  "title": "string?",
  "personTypeId": "string (GUID)",
  "isAssignable": "boolean?",
  "notes": "string?",
  "tags": ["string (GUID)"]
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| firstName | string | Yes | 1-100 characters |
| lastName | string | Yes | 1-100 characters |
| email | string | No* | Valid email format, unique within tenant |
| phone | string | No | Max 20 characters |
| title | string | No | Max 100 characters |
| personTypeId | GUID | Yes | Must exist and be active |
| isAssignable | boolean | No | Defaults from PersonType.isAssignableByDefault |
| notes | string | No | Max 2000 characters |
| tags | GUID[] | No | Must be valid tag IDs |

*Email is required if person will be linked to a User.

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "firstName": "string",
    "lastName": "string",
    "email": "string?",
    "isEmailVerified": false,
    "phone": "string?",
    "title": "string?",
    "personType": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "isActive": true,
    "isAssignable": "boolean",
    "notes": "string?",
    "tags": [],
    "roles": [],
    "linkedUserId": null,
    "hasSystemAccess": false,
    "createdAt": "string (ISO 8601)",
    "createdBy": "string (GUID)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Email is already in use within this tenant",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "email"
  }
}
```

```json
{
  "success": false,
  "error": "Person type not found or inactive",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "personTypeId"
  }
}
```

---

### PUT /people/{id}

Update an existing person.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "firstName": "string?",
  "lastName": "string?",
  "email": "string?",
  "phone": "string?",
  "title": "string?",
  "personTypeId": "string (GUID)?",
  "isAssignable": "boolean?",
  "notes": "string?"
}
```

**Notes:**

- All fields are optional (partial update)
- Cannot update `isActive` via this endpoint (use activate/deactivate)
- Tags managed via separate endpoints

**Response:**

```json
{
  "success": true,
  "data": "PersonResponse (full object)"
}
```

---

### DELETE /people/{id}

Soft delete (deactivate) a person. Optionally reassign their work items to another person.

**Path Parameters:**

- `id` - Person ID (GUID)

**Query Parameters:**

- `reassignTo` - Optional: Person ID (GUID) to reassign work items to

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "message": "Person deactivated successfully",
  "data": {
    "id": "string (GUID)",
    "firstName": "string",
    "lastName": "string",
    "displayName": "string",
    "email": "string?",
    "phone": "string?",
    "title": "string?",
    "personType": {
      "id": "string (GUID)",
      "name": "string"
    },
    "isAssignable": false,
    "isPrimary": false,
    "notes": "string?",
    "status": "inactive",
    "linkedUserId": "string (GUID)?",
    "isEmailVerified": false,
    "tags": ["string (GUID)"],
    "roleAssignments": [],
    "createdBy": "string (GUID)",
    "createdAt": "string (ISO 8601)",
    "updatedBy": "string (GUID)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

- **404 Not Found** - Person not found
- **400 Bad Request** - Invalid person ID format, invalid reassignTo ID, or deactivation failed
- **500 Internal Server Error** - Server error

---

### POST /people/{id}/activate

Reactivate a deactivated person.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "message": "Person activated successfully",
  "data": {
    "id": "string (GUID)",
    "firstName": "string",
    "lastName": "string",
    "displayName": "string",
    "email": "string?",
    "phone": "string?",
    "title": "string?",
    "personType": {
      "id": "string (GUID)",
      "name": "string"
    },
    "isAssignable": true,
    "isPrimary": false,
    "notes": "string?",
    "status": "active",
    "linkedUserId": "string (GUID)?",
    "isEmailVerified": false,
    "tags": ["string (GUID)"],
    "roleAssignments": [],
    "createdBy": "string (GUID)",
    "createdAt": "string (ISO 8601)",
    "updatedBy": "string (GUID)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

- **404 Not Found** - Person not found
- **400 Bad Request** - Invalid person ID format or activation failed
- **500 Internal Server Error** - Server error

---

### POST /people/{id}/link-user

Link a person to an existing user account.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "userId": "string (GUID)"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "personId": "string (GUID)",
    "userId": "string (GUID)",
    "linkedAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Person is already linked to a user",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "existingUserId": "guid"
  }
}
```

```json
{
  "success": false,
  "error": "User is already linked to another person",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "existingPersonId": "guid"
  }
}
```

```json
{
  "success": false,
  "error": "Person must have a verified email to be linked to a user",
  "code": "VALIDATION_ERROR"
}
```

---

### POST /people/{id}/tags

Add tags to a person.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "tagIds": ["string (GUID)"]
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "tags": [
      {
        "id": "string (GUID)",
        "name": "string",
        "assignedAt": "string (ISO 8601)"
      }
    ]
  }
}
```

---

### DELETE /people/{id}/tags/{tagId}

Remove a tag from a person.

**Path Parameters:**

- `id` - Person ID (GUID)
- `tagId` - Tag ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true
}
```

---

## Person Roles Endpoints

### GET /people/{id}/roles

Get person's current role assignments.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "role": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string"
      },
      "isPrimary": "boolean",
      "effectiveDate": "string (ISO 8601)",
      "terminationDate": null
    }
  ]
}
```

---

### GET /people/{id}/roles/history

Get person's complete role assignment history.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "current": [
      {
        "id": "string (GUID)",
        "role": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string"
        },
        "isPrimary": "boolean",
        "effectiveDate": "string (ISO 8601)"
      }
    ],
    "historical": [
      {
        "id": "string (GUID)",
        "role": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string"
        },
        "isPrimary": "boolean",
        "effectiveDate": "string (ISO 8601)",
        "terminationDate": "string (ISO 8601)"
      }
    ]
  }
}
```

---

### POST /people/{id}/roles

Assign a role to a person.

**Path Parameters:**

- `id` - Person ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "roleId": "string (GUID)",
  "isPrimary": "boolean?",
  "effectiveDate": "string (ISO 8601)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| roleId | GUID | Yes | Must be active role |
| isPrimary | boolean | No | Default: `true` if first role, else `false` |
| effectiveDate | ISO 8601 | No | Default: current date |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "role": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "isPrimary": "boolean",
    "effectiveDate": "string (ISO 8601)",
    "previousOccupantTerminated": "boolean"
  }
}
```

**Notes:**

- If role already has an occupant, their assignment is auto-terminated
- `previousOccupantTerminated` indicates if this happened

**Error Responses:**

```json
{
  "success": false,
  "error": "Person is not active",
  "code": "BUSINESS_RULE_VIOLATION"
}
```

```json
{
  "success": false,
  "error": "Role not found or inactive",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "roleId"
  }
}
```

---

### PUT /people/{id}/roles/{roleId}/primary

Set a role as the person's primary role.

**Path Parameters:**

- `id` - Person ID (GUID)
- `roleId` - Role ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "previousPrimaryRoleId": "string (GUID)?",
    "newPrimaryRoleId": "string (GUID)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Person is not assigned to this role",
  "code": "VALIDATION_ERROR"
}
```

---

### DELETE /people/{id}/roles/{roleId}

Unassign a role from a person.

**Path Parameters:**

- `id` - Person ID (GUID)
- `roleId` - Role ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| terminationDate | ISO 8601 | now | When assignment ends |

**Response:**

```json
{
  "success": true,
  "data": {
    "terminated": true,
    "terminationDate": "string (ISO 8601)",
    "wasPrimary": "boolean",
    "newPrimaryRoleId": "string (GUID)?"
  }
}
```

**Notes:**

- If this was the primary role and person has other roles, frontend should prompt to select new primary

---

## Person Types Endpoints

### GET /person-types

List all person types for the tenant.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| includeInactive | boolean | false | Include inactive types |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "code": "string",
      "name": "string",
      "description": "string?",
      "isAssignableByDefault": "boolean",
      "displayOrder": "number",
      "isActive": "boolean",
      "createdAt": "string (ISO 8601)",
      "updatedAt": "string (ISO 8601)?"
    }
  ]
}
```

---

### GET /person-types/{id}

Get person type details.

**Path Parameters:**

- `id` - PersonType ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "name": "string",
    "description": "string?",
    "isAssignableByDefault": "boolean",
    "displayOrder": "number",
    "isActive": "boolean",
    "personCount": "number",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

---

### POST /person-types

Create a new person type.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "code": "string",
  "name": "string",
  "description": "string?",
  "isAssignableByDefault": "boolean",
  "displayOrder": "number?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| code | string | Yes | 2-20 chars, uppercase alphanumeric + underscore, unique within tenant |
| name | string | Yes | 1-100 characters |
| description | string | No | Max 500 characters |
| isAssignableByDefault | boolean | Yes | - |
| displayOrder | number | No | Default: next available |

**Response:**

```json
{
  "success": true,
  "data": "PersonTypeResponse"
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Person type code already exists",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "code"
  }
}
```

---

### PUT /person-types/{id}

Update a person type.

**Path Parameters:**

- `id` - PersonType ID (GUID)

**Request:**

```json
{
  "name": "string?",
  "description": "string?",
  "isAssignableByDefault": "boolean?",
  "displayOrder": "number?"
}
```

**Notes:**

- `code` cannot be changed after creation
- Changes to `isAssignableByDefault` do not affect existing persons

**Response:**

```json
{
  "success": true,
  "data": "PersonTypeResponse"
}
```

---

### DELETE /person-types/{id}

Deactivate a person type.

**Path Parameters:**

- `id` - PersonType ID (GUID)

**Response:**

```json
{
  "success": true
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot delete person type with existing persons",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "personCount": 15
  }
}
```

---

## Person Tags Endpoints

### GET /api/person-tags

List all tags for the tenant.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "name": "string",
      "personCount": "number",
      "createdAt": "string (ISO 8601)"

---

### POST /person-types/{id}/activate

Reactivate a deactivated person type.

**Path Parameters:**

- `id` - PersonType ID (GUID)

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
    "name": "string",
    "description": "string?",
    "isAssignableByDefault": "boolean",
    "displayOrder": "number",
    "isActive": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

**Error Responses:**

- **404 Not Found** - Person type not found
- **400 Bad Request** - Invalid person type ID format or activation failed
- **500 Internal Server Error** - Server error
    }
  ]
}
```

---

### POST /api/person-tags

Create a new tag.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "name": "string"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | Yes | 1-50 characters, unique within tenant |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "name": "string",
    "createdAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Tag name already exists",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "name"
  }
}
```

---

### PUT /api/person-tags/{id}

Update a tag name.

**Path Parameters:**

- `id` - Tag ID (GUID)

**Request:**

```json
{
  "name": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "name": "string"
  }
}
```

---

### DELETE /api/person-tags/{id}

Delete a tag (cascade removes all person-tag assignments).

**Path Parameters:**

- `id` - Tag ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "assignmentsRemoved": "number"
  }
}
```

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_CREDENTIALS` | 401 | Wrong username/password |
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists (unique constraint) |
| `BUSINESS_RULE_VIOLATION` | 400 | Domain rule prevents operation |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `ACCOUNT_LOCKED` | 403 | User account is locked |

---

## Data Types Reference

### PersonStatus

```typescript
type PersonStatus = 'active' | 'inactive';
```

### Username Validation

```typescript
const USERNAME_REGEX = /^[a-zA-Z0-9][a-zA-Z0-9._@-]{2,49}$/;
const RESERVED_USERNAMES = ['admin', 'system', 'support', 'purposepath', 'help', 'info'];
```

### Default Person Types (Seeded)

| Code | Name | Assignable |
|------|------|------------|
| EMPLOYEE | Employee | Yes |
| CONSULTANT | Consultant | Yes |
| VENDOR | Vendor | No |
| PARTNER | Partner | No |
| ADVISOR | Advisor | No |
| BOARD | Board Member | No |

---

**Document End**

[← Back to Index](./index.md) | [Part 2: Organizational Structure →](./org-structure-service.md)
