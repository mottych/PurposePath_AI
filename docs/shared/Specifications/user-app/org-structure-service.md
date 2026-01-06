# Organizational Structure Service - API Specification

**Version:** 3.1  
**Last Updated:** January 4, 2026  
**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`

[← People Service](./people-service.md) | [Back to Index](./index.md)

> **📋 NOTE:** Admin Template endpoints have been moved to the [Admin Portal API Specification](../admin-portal/admin-api-specification.md#role-templates).

---

## Overview

The Organizational Structure module manages the organizational hierarchy through roles, positions, organization units, and their relationships. It provides the foundation for the accountability framework within PurposePath.

### Architecture Overview

The org structure is built on these key entities:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│     RoleType     │     │       Role       │     │OrganizationUnit- │
│    (Reference)   │────▶│    (Template)    │     │      Type        │
│                  │     │                  │     │   (Reference)    │
└──────────────────┘     └────────┬─────────┘     └────────┬─────────┘
                                  │                        │
                                  │                        ▼
                                  │              ┌──────────────────┐
                                  │              │ OrganizationUnit │
                                  │              │  (Department/    │
                                  │              │   Team/etc.)     │
                                  │              └────────┬─────────┘
                                  │                        │
                                  ▼                        │
                         ┌──────────────────┐              │
                         │     Position     │◀─────────────┘
                         │ (Instance of Role│
                         │  in an Org Unit) │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │      Person      │
                         │   (Occupant)     │
                         └──────────────────┘
```

### Key Concepts

- **Role**: A template defining responsibilities and accountability (e.g., "Software Engineer", "VP Sales")
- **RoleType**: Classification of roles (Executive, Management, Professional, Associate)
- **Position**: An instance of a role within an organization unit, optionally filled by a person
- **OrganizationUnit**: A logical grouping (Company, Division, Department, Team)
- **OrganizationUnitType**: Classification of organization units
- **Position Relationship**: Non-hierarchical connection between positions (Support, Advise, Collaborate, Mentor)
- **Reports To**: Hierarchical relationship defined on Position entity

### Frontend Implementation

- **Primary Client:** `accountClient` (axios instance)
- **Related Files:**
  - `src/services/roles-service.ts` - Role CRUD operations
  - `src/services/positions-service.ts` - Position management *(planned)*
  - `src/services/org-units-service.ts` - Organization unit management *(planned)*
  - `src/services/role-relationships-service.ts` - Reporting/collaboration structures
  - `src/services/org-chart-service.ts` - Organization chart visualization

---

## Roles Endpoints

### GET /api/roles

List all roles with filtering and pagination.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | `active` | Filter: `active`, `inactive`, `all` |
| vacant | boolean | - | Filter for vacant roles only |
| search | string | - | Search by name or code |
| page | number | 1 | Page number (1-based) |
| pageSize | number | 20 | Items per page (max 100) |
| sortBy | string | `name` | Sort field: `name`, `code`, `createdAt` |
| sortOrder | string | `asc` | Sort order: `asc`, `desc` |

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string (GUID)",
        "code": "string",
        "name": "string",
        "description": "string?",
        "roleTypeId": "string (GUID)",
        "roleType": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string"
        },
        "isActive": "boolean",
        "currentOccupant": {
          "id": "string (GUID)?",
          "name": "string?",
          "since": "string (ISO 8601)?"
        },
        "reportsTo": {
          "roleId": "string (GUID)?",
          "roleName": "string?"
        },
        "directReportsCount": "number",
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

### GET /api/roles/dropdown

Get simplified role list for dropdowns.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| includeVacant | boolean | true | Include vacant roles |
| excludeId | string (GUID) | - | Exclude specific role (for relationship forms) |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "code": "string",
      "name": "string",
      "occupantName": "string?",
      "isVacant": "boolean"
    }
  ]
}
```

---

### GET /api/roles/{id}

Get detailed role information.

**Path Parameters:**

- `id` - Role ID (GUID)

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
    "accountability": "string",
    "description": "string?",
    "roleTypeId": "string (GUID)",
    "roleType": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string",
      "isStretchRole": "boolean"
    },
    "isActive": "boolean",
    "currentOccupant": {
      "id": "string (GUID)?",
      "firstName": "string?",
      "lastName": "string?",
      "email": "string?",
      "title": "string?",
      "since": "string (ISO 8601)?",
      "isPrimaryRole": "boolean?"
    },
    "assignmentHistory": [
      {
        "personId": "string (GUID)",
        "personName": "string",
        "effectiveDate": "string (ISO 8601)",
        "terminationDate": "string (ISO 8601)?"
      }
    ],
    "reportsTo": {
      "roleId": "string (GUID)?",
      "roleCode": "string?",
      "roleName": "string?",
      "occupantName": "string?"
    },
    "directReports": [
      {
        "roleId": "string (GUID)",
        "roleCode": "string",
        "roleName": "string",
        "occupantName": "string?"
      }
    ],
    "relationships": [
      {
        "relationshipId": "string (GUID)",
        "direction": "from | to",
        "roleId": "string (GUID)",
        "roleCode": "string",
        "roleName": "string",
        "occupantName": "string?",
        "relationshipType": {
          "code": "string",
          "name": "string",
          "verb": "string"
        },
        "description": "string?"
      }
    ],
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
  "error": "Role not found",
  "code": "RESOURCE_NOT_FOUND",
  "details": {
    "resourceType": "Role",
    "resourceId": "guid"
  }
}
```

---

### POST /api/roles

Create a new role.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "code": "string",
  "name": "string",
  "accountability": "string",
  "description": "string?",
  "roleTypeId": "string (GUID)?",
  "reportsToRoleId": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| code | string | Yes | 2-20 chars, uppercase alphanumeric + underscore, unique within tenant |
| name | string | Yes | 1-100 characters |
| accountability | string | Yes | 1-500 characters, describes what this role is accountable for |
| description | string | No | Max 2000 characters (detailed responsibilities, can include markdown) |
| roleTypeId | GUID | No | Must be valid RoleType ID. Defaults to "Professional" type if not specified. |
| reportsToRoleId | GUID | No | Must be valid active role |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "name": "string",
    "accountability": "string",
    "description": "string?",
    "roleTypeId": "string (GUID)",
    "roleType": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "isActive": true,
    "currentOccupant": null,
    "reportsTo": null,
    "directReports": [],
    "createdAt": "string (ISO 8601)",
    "createdBy": "string (GUID)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Role code already exists",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "code"
  }
}
```

---

### PUT /api/roles/{id}

Update an existing role.

**Path Parameters:**

- `id` - Role ID (GUID)

**Request:**

```json
{
  "name": "string?",
  "accountability": "string?",
  "description": "string?",
  "reportsToRoleId": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | No | 1-100 characters |
| accountability | string | No | 1-500 characters, describes what this role is accountable for |
| description | string | No | Max 2000 characters (detailed responsibilities) |
| reportsToRoleId | GUID | No | Must be active role, cannot create circular reference, set to `null` to remove |

**Notes:**

- `code` cannot be changed after creation
- Setting `reportsToRoleId` to `null` removes the reporting relationship (makes role a top-level role)
- Backend validates no circular references when changing reportsTo
- Non-hierarchical relationships (SUPPORT, ADVISE, etc.) managed via separate endpoints

**Response:**

```json
{
  "success": true,
  "data": "RoleResponse (full object)"
}
```

---

### DELETE /api/roles/{id}

Soft delete a role.

**Path Parameters:**

- `id` - Role ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

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
  "error": "Cannot delete role with active assignment",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "occupantId": "guid",
    "occupantName": "John Smith"
  }
}
```

```json
{
  "success": false,
  "error": "Cannot delete role with direct reports",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "directReportsCount": 5
  }
}
```

---

### POST /api/roles/{id}/activate

Reactivate a deactivated role.

**Path Parameters:**

- `id` - Role ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "isActive": true
  }
}
```

---

### POST /api/roles/{id}/deactivate

Deactivate a role (unassigns person, removes from hierarchy).

**Path Parameters:**

- `id` - Role ID (GUID)

**Request (Optional):**

```json
{
  "cascadeDirectReports": "boolean?",
  "newParentRoleId": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| cascadeDirectReports | boolean | No | If true, deactivate all direct reports |
| newParentRoleId | GUID | No | Reassign direct reports to this role |

**Default Behavior (when no options provided):**

- Direct reports' `reportsToRoleId` is set to `null` (they become top-level roles)
- The deactivated role's person assignment is terminated (if any)
- All relationships (SUPPORT, ADVISE, etc.) involving this role are removed

**Response:**

```json
{
  "success": true,
  "data": {
    "deactivated": true,
    "personUnassigned": "boolean",
    "relationshipsRemoved": "number",
    "directReportsHandled": {
      "reassignedTo": "string (GUID)?",
      "deactivatedCount": "number?"
    }
  }
}
```

---

## Role Relationships Endpoints

### GET /api/role-relationships

List all role relationships.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| type | string | - | Filter by type: `reportsTo`, `collaboratesWith` |
| roleId | GUID | - | Get relationships for specific role |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "fromRole": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string",
        "occupantName": "string?"
      },
      "toRole": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string",
        "occupantName": "string?"
      },
      "relationshipType": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string"
      },
      "description": "string?",
      "createdAt": "string (ISO 8601)"
    }
  ]
}
```

---

### POST /api/role-relationships

Create a role relationship.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "fromRoleId": "string (GUID)",
  "toRoleId": "string (GUID)",
  "relationshipTypeCode": "string",
  "description": "string?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| fromRoleId | GUID | Yes | Must be active role |
| toRoleId | GUID | Yes | Must be active role, different from fromRoleId |
| relationshipTypeCode | string | Yes | Valid relationship type code (e.g., `SUPPORT`, `ADVISE`, `COLLABORATE`, `MENTOR`) |
| description | string | No | Max 500 chars |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "fromRole": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "toRole": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "relationshipType": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "description": "string?",
    "createdAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Relationship already exists between these roles with this type",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "existingRelationshipId": "guid"
  }
}
```

```json
{
  "success": false,
  "error": "Relationship type does not allow multiple relationships",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "relationshipTypeCode": "MENTOR",
    "existingRelationshipId": "guid"
  }
}
```

---

### PUT /api/role-relationships/{id}

Update a relationship (description only).

**Path Parameters:**

- `id` - Relationship ID (GUID)

**Request:**

```json
{
  "description": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": "RoleRelationshipResponse"
}
```

---

### DELETE /api/role-relationships/{id}

Delete a role relationship.

**Path Parameters:**

- `id` - Relationship ID (GUID)

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

### GET /api/role-relationship-types

List available relationship types.

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
      "code": "SUPPORT",
      "name": "Support",
      "forwardVerb": "supports",
      "reverseVerb": "is supported by",
      "allowsMultiple": true,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "ADVISE",
      "name": "Advise",
      "forwardVerb": "advises",
      "reverseVerb": "is advised by",
      "allowsMultiple": true,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "COLLABORATE",
      "name": "Collaborate",
      "forwardVerb": "collaborates with",
      "reverseVerb": "collaborates with",
      "allowsMultiple": true,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "MENTOR",
      "name": "Mentor",
      "forwardVerb": "mentors",
      "reverseVerb": "is mentored by",
      "allowsMultiple": true,
      "isActive": true,
      "isSystem": true
    }
  ]
}
```

**Notes:**

- `isSystem` indicates seeded types that cannot be deleted
- `forwardVerb` used when displaying "Role A {forwardVerb} Role B"
- `reverseVerb` used when displaying "Role B {reverseVerb} Role A"

---

### GET /api/role-relationship-types/{id}

Get relationship type details.

**Path Parameters:**

- `id` - RelationshipType ID (GUID)

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
    "forwardVerb": "string",
    "reverseVerb": "string",
    "allowsMultiple": "boolean",
    "isActive": "boolean",
    "isSystem": "boolean",
    "usageCount": "number",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

---

### POST /api/role-relationship-types

Create a custom relationship type.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "code": "string",
  "name": "string",
  "forwardVerb": "string",
  "reverseVerb": "string",
  "allowsMultiple": "boolean?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| code | string | Yes | 2-20 chars, uppercase alphanumeric + underscore, unique within tenant |
| name | string | Yes | 1-50 characters |
| forwardVerb | string | Yes | 1-50 characters (e.g., "manages") |
| reverseVerb | string | Yes | 1-50 characters (e.g., "is managed by") |
| allowsMultiple | boolean | No | Default: true |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "name": "string",
    "forwardVerb": "string",
    "reverseVerb": "string",
    "allowsMultiple": "boolean",
    "isActive": true,
    "isSystem": false,
    "createdAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Relationship type code already exists",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "code"
  }
}
```

---

### PUT /api/role-relationship-types/{id}

Update a relationship type.

**Path Parameters:**

- `id` - RelationshipType ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "name": "string?",
  "forwardVerb": "string?",
  "reverseVerb": "string?",
  "allowsMultiple": "boolean?"
}
```

**Notes:**

- `code` cannot be changed after creation
- System types (`isSystem = true`) can have name/verbs updated but not deleted

**Response:**

```json
{
  "success": true,
  "data": "RelationshipTypeResponse"
}
```

---

### DELETE /api/role-relationship-types/{id}

Deactivate a relationship type.

**Path Parameters:**

- `id` - RelationshipType ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

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
  "error": "Cannot delete system relationship type",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "isSystem": true
  }
}
```

```json
{
  "success": false,
  "error": "Cannot delete relationship type with existing relationships",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "usageCount": 5
  }
}
```

---

## Role Types Endpoints

Role Types provide classification categories for roles (Executive, Management, Professional, Associate).

### GET /api/role-types

List available role types.

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
      "code": "EXECUTIVE",
      "name": "Executive",
      "description": "C-level and senior leadership roles with strategic decision-making authority",
      "isStretchRole": false,
      "displayOrder": 1,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "MANAGEMENT",
      "name": "Management",
      "description": "Directors, VPs, and managers with team leadership responsibilities",
      "isStretchRole": false,
      "displayOrder": 2,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "PROFESSIONAL",
      "name": "Professional",
      "description": "Individual contributors with specialized expertise",
      "isStretchRole": false,
      "displayOrder": 3,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "ASSOCIATE",
      "name": "Associate",
      "description": "Entry-level and support roles",
      "isStretchRole": false,
      "displayOrder": 4,
      "isActive": true,
      "isSystem": true
    }
  ]
}
```

**Notes:**

- `isSystem` indicates seeded types that cannot be deleted
- `isStretchRole` indicates extended responsibility positions (not full-time)
- `displayOrder` is used for sorting in UI dropdowns

---

### GET /api/role-types/{id}

Get role type details.

**Path Parameters:**

- `id` - RoleType ID (GUID)

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
    "isStretchRole": "boolean",
    "displayOrder": "number",
    "isActive": "boolean",
    "isSystem": "boolean",
    "usageCount": "number",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

---

### POST /api/role-types

Create a custom role type.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "code": "string",
  "name": "string",
  "description": "string?",
  "isStretchRole": "boolean?",
  "displayOrder": "number?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| code | string | Yes | 2-20 chars, uppercase alphanumeric + underscore, unique within tenant |
| name | string | Yes | 1-50 characters |
| description | string | No | Max 500 characters |
| isStretchRole | boolean | No | Default: false |
| displayOrder | number | No | Auto-assigned if not provided |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "name": "string",
    "description": "string?",
    "isStretchRole": "boolean",
    "displayOrder": "number",
    "isActive": true,
    "isSystem": false,
    "createdAt": "string (ISO 8601)"
  }
}
```

---

### PUT /api/role-types/{id}

Update a role type.

**Path Parameters:**

- `id` - RoleType ID (GUID)

**Request:**

```json
{
  "name": "string?",
  "description": "string?",
  "isStretchRole": "boolean?",
  "displayOrder": "number?"
}
```

**Notes:**

- `code` cannot be changed after creation
- System types (`isSystem = true`) can have name/description updated but not deleted

---

### DELETE /api/role-types/{id}

Deactivate a role type.

**Path Parameters:**

- `id` - RoleType ID (GUID)

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot delete system role type",
  "code": "BUSINESS_RULE_VIOLATION"
}
```

```json
{
  "success": false,
  "error": "Cannot delete role type with existing roles",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "usageCount": 5
  }
}
```

---

## Organization Unit Types Endpoints

Organization Unit Types classify organizational units (Company, Division, Department, Team, Project).

### GET /api/organization-unit-types

List available organization unit types.

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
      "code": "COMPANY",
      "name": "Company",
      "description": "Top-level organizational unit representing the entire company",
      "displayOrder": 1,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "DIVISION",
      "name": "Division",
      "description": "Major business unit or division within the company",
      "displayOrder": 2,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "DEPARTMENT",
      "name": "Department",
      "description": "Functional department within a division or company",
      "displayOrder": 3,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "TEAM",
      "name": "Team",
      "description": "Work team or unit within a department",
      "displayOrder": 4,
      "isActive": true,
      "isSystem": true
    },
    {
      "id": "string (GUID)",
      "code": "PROJECT",
      "name": "Project",
      "description": "Cross-functional project team",
      "displayOrder": 5,
      "isActive": true,
      "isSystem": true
    }
  ]
}
```

---

### GET /api/organization-unit-types/{id}

Get organization unit type details.

**Path Parameters:**

- `id` - OrganizationUnitType ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "name": "string",
    "description": "string?",
    "displayOrder": "number",
    "isActive": "boolean",
    "isSystem": "boolean",
    "usageCount": "number",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

---

### POST /api/organization-unit-types

Create a custom organization unit type.

**Request:**

```json
{
  "code": "string",
  "name": "string",
  "description": "string?",
  "displayOrder": "number?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| code | string | Yes | 2-20 chars, uppercase alphanumeric + underscore, unique within tenant |
| name | string | Yes | 1-50 characters |
| description | string | No | Max 500 characters |
| displayOrder | number | No | Auto-assigned if not provided |

---

### PUT /api/organization-unit-types/{id}

Update an organization unit type.

**Request:**

```json
{
  "name": "string?",
  "description": "string?",
  "displayOrder": "number?"
}
```

---

### DELETE /api/organization-unit-types/{id}

Deactivate an organization unit type.

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot delete system organization unit type",
  "code": "BUSINESS_RULE_VIOLATION"
}
```

---

## Organization Units Endpoints

Organization Units represent the logical structure of the organization (companies, divisions, departments, teams).

### GET /api/organization-units

List all organization units.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| parentId | GUID | - | Filter by parent unit (null for top-level) |
| typeId | GUID | - | Filter by organization unit type |
| includeInactive | boolean | false | Include inactive units |
| page | number | 1 | Page number |
| pageSize | number | 20 | Items per page |

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string (GUID)",
        "name": "string",
        "description": "string?",
        "organizationUnitType": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string"
        },
        "parentOrganizationUnitId": "string (GUID)?",
        "parentOrganizationUnitName": "string?",
        "unitLeadPersonId": "string (GUID)?",
        "unitLeadPersonName": "string?",
        "isActive": "boolean",
        "childrenCount": "number",
        "positionsCount": "number",
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

### GET /api/organization-units/tree

Get hierarchical tree of organization units.

**Response:**

```json
{
  "success": true,
  "data": {
    "rootNodes": [
      {
        "id": "string (GUID)",
        "name": "string",
        "organizationUnitType": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string"
        },
        "unitLeadPersonName": "string?",
        "positionsCount": "number",
        "depth": "number",
        "children": ["recursive OrgUnitNode"]
      }
    ]
  }
}
```

---

### GET /api/organization-units/{id}

Get organization unit details.

**Path Parameters:**

- `id` - OrganizationUnit ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "name": "string",
    "description": "string?",
    "organizationUnitType": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "parentOrganizationUnit": {
      "id": "string (GUID)?",
      "name": "string?"
    },
    "unitLeadPerson": {
      "id": "string (GUID)?",
      "displayName": "string?",
      "email": "string?"
    },
    "childUnits": [
      {
        "id": "string (GUID)",
        "name": "string",
        "typeCode": "string"
      }
    ],
    "positions": [
      {
        "id": "string (GUID)",
        "name": "string",
        "roleName": "string",
        "occupantName": "string?",
        "isVacant": "boolean"
      }
    ],
    "isActive": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

---

### POST /api/organization-units

Create an organization unit.

**Request:**

```json
{
  "name": "string",
  "description": "string?",
  "organizationUnitTypeId": "string (GUID)",
  "parentOrganizationUnitId": "string (GUID)?",
  "unitLeadPersonId": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | Yes | 1-100 characters |
| description | string | No | Max 500 characters |
| organizationUnitTypeId | GUID | Yes | Must be valid organization unit type |
| parentOrganizationUnitId | GUID | No | Must be valid active organization unit |
| unitLeadPersonId | GUID | No | Must be valid active person |

---

### PUT /api/organization-units/{id}

Update an organization unit.

**Request:**

```json
{
  "name": "string?",
  "description": "string?",
  "organizationUnitTypeId": "string (GUID)?",
  "parentOrganizationUnitId": "string (GUID)?",
  "unitLeadPersonId": "string (GUID)?"
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot set parent to self or child unit (circular reference)",
  "code": "CIRCULAR_REFERENCE"
}
```

---

### DELETE /api/organization-units/{id}

Deactivate an organization unit.

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot delete organization unit with child units",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "childUnitsCount": 3
  }
}
```

```json
{
  "success": false,
  "error": "Cannot delete organization unit with active positions",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "positionsCount": 5
  }
}
```

---

### GET /api/organization-units/dropdown

Get simplified organization unit list for dropdowns.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| typeId | GUID | - | Filter by organization unit type |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "name": "string",
      "typeCode": "string",
      "typeName": "string",
      "parentId": "string (GUID)?",
      "parentName": "string?",
      "depth": "number"
    }
  ]
}
```

---

### PUT /api/organization-units/{id}/status

Update organization unit status (activate/deactivate).

**Path Parameters:**

- `id` - OrganizationUnit ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "status": "active | inactive"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "name": "string",
    "status": "active | inactive",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot deactivate organization unit with active child units",
  "code": "BUSINESS_RULE_VIOLATION"
}
```

---

## Positions Endpoints

Positions represent instances of roles within organization units, optionally filled by persons.

### GET /api/positions

List all positions.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | `active` | Filter: `active`, `inactive`, `vacant`, `all` |
| organizationUnitId | GUID | - | Filter by organization unit |
| roleId | GUID | - | Filter by role |
| personId | GUID | - | Filter by assigned person |
| search | string | - | Search by name |
| page | number | 1 | Page number |
| pageSize | number | 20 | Items per page |

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string (GUID)",
        "name": "string",
        "description": "string?",
        "specificAccountability": "string?",
        "role": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string",
          "roleTypeCode": "string"
        },
        "organizationUnit": {
          "id": "string (GUID)",
          "name": "string",
          "typeCode": "string"
        },
        "person": {
          "id": "string (GUID)?",
          "displayName": "string?",
          "email": "string?"
        },
        "reportsToPosition": {
          "id": "string (GUID)?",
          "name": "string?",
          "occupantName": "string?"
        },
        "status": "active | inactive | vacant",
        "directReportsCount": "number",
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

### GET /api/positions/{id}

Get position details.

**Path Parameters:**

- `id` - Position ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "name": "string",
    "description": "string?",
    "specificAccountability": "string?",
    "role": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string",
      "accountability": "string",
      "roleType": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string"
      }
    },
    "organizationUnit": {
      "id": "string (GUID)",
      "name": "string",
      "organizationUnitType": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string"
      }
    },
    "person": {
      "id": "string (GUID)?",
      "firstName": "string?",
      "lastName": "string?",
      "displayName": "string?",
      "email": "string?",
      "title": "string?"
    },
    "reportsToPosition": {
      "id": "string (GUID)?",
      "name": "string?",
      "roleName": "string?",
      "occupantName": "string?"
    },
    "directReports": [
      {
        "id": "string (GUID)",
        "name": "string",
        "roleName": "string",
        "occupantName": "string?",
        "status": "string"
      }
    ],
    "relationships": [
      {
        "relationshipId": "string (GUID)",
        "direction": "from | to",
        "positionId": "string (GUID)",
        "positionName": "string",
        "occupantName": "string?",
        "relationshipType": {
          "code": "string",
          "name": "string",
          "verb": "string"
        }
      }
    ],
    "status": "active | inactive | vacant",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

---

### POST /api/positions

Create a position.

**Request:**

```json
{
  "name": "string",
  "description": "string?",
  "specificAccountability": "string?",
  "roleId": "string (GUID)",
  "organizationUnitId": "string (GUID)",
  "personId": "string (GUID)?",
  "reportsToPositionId": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | Yes | 1-100 characters |
| description | string | No | Max 500 characters |
| specificAccountability | string | No | Max 500 characters (additional context beyond role accountability) |
| roleId | GUID | Yes | Must be valid active role |
| organizationUnitId | GUID | Yes | Must be valid active organization unit |
| personId | GUID | No | Must be valid active person |
| reportsToPositionId | GUID | No | Must be valid active position |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "name": "string",
    "status": "active | vacant",
    "role": { "id": "string", "name": "string" },
    "organizationUnit": { "id": "string", "name": "string" },
    "person": { "id": "string?", "displayName": "string?" },
    "reportsToPosition": { "id": "string?", "name": "string?" },
    "createdAt": "string (ISO 8601)"
  }
}
```

---

### PUT /api/positions/{id}

Update a position.

**Request:**

```json
{
  "name": "string",
  "roleId": "string (GUID)",
  "organizationUnitId": "string (GUID)",
  "description": "string?",
  "specificAccountability": "string?",
  "reportsToPositionId": "string (GUID)?"
}
```

**Notes:**

- `roleId` may be changed via this endpoint
- To change the person, use the assign/unassign endpoints

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot report to self",
  "code": "BUSINESS_RULE_VIOLATION"
}
```

```json
{
  "success": false,
  "error": "Would create circular reporting structure",
  "code": "CIRCULAR_REFERENCE"
}
```

---

### DELETE /api/positions/{id}

Deactivate a position.

**Error Responses:**

```json
{
  "success": false,
  "error": "Cannot delete position with direct reports",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "directReportsCount": 3
  }
}
```

---

### GET /api/positions/dropdown

Get simplified position list for dropdowns.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| organizationUnitId | GUID | - | Filter by organization unit |
| vacantOnly | boolean | false | Show only vacant positions |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "title": "string",
      "roleTypeCode": "string",
      "roleTypeName": "string",
      "organizationUnitId": "string (GUID)?",
      "organizationUnitName": "string?",
      "status": "active | inactive | vacant",
      "personId": "string (GUID)?",
      "personName": "string?"
    }
  ]
}
```

---

### GET /api/positions/tree

Get hierarchical position tree.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| rootPositionId | GUID | - | Start tree from specific position |
| organizationUnitId | GUID | - | Filter by organization unit |
| includeInactive | boolean | false | Include inactive positions |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "title": "string",
      "roleTypeCode": "string",
      "roleTypeName": "string",
      "organizationUnitId": "string (GUID)?",
      "organizationUnitName": "string?",
      "status": "active | inactive | vacant",
      "personId": "string (GUID)?",
      "personName": "string?",
      "reportsToId": "string (GUID)?",
      "depth": "number",
      "children": [/* recursive PositionTreeNode */]
    }
  ]
}
```

---

### POST /api/positions/{id}/assign

Assign a person to a position.

**Path Parameters:**

- `id` - Position ID (GUID)

**Request:**

```json
{
  "personId": "string (GUID)"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "positionId": "string (GUID)",
    "personId": "string (GUID)",
    "personName": "string",
    "status": "active",
    "assignedAt": "string (ISO 8601)"
  }
}
```

---

### POST /api/positions/{id}/unassign

Remove person from a position.

**Path Parameters:**

- `id` - Position ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "positionId": "string (GUID)",
    "status": "vacant",
    "unassignedAt": "string (ISO 8601)"
  }
}
```

---

### PUT /api/positions/{id}/status

Update position status.

**Request:**

```json
{
  "status": "active | inactive"
}
```

**Notes:**

- Setting to `inactive` will also unassign any person
- `vacant` status is automatic when no person is assigned

---

## Position Relationships Endpoints

Position Relationships define non-hierarchical connections between positions (Support, Advise, Collaborate, Mentor).

### GET /api/position-relationships

List all position relationships.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| positionId | GUID | - | Get relationships for specific position |
| typeCode | string | - | Filter by relationship type code |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "fromPosition": {
        "id": "string (GUID)",
        "name": "string",
        "roleName": "string",
        "occupantName": "string?"
      },
      "toPosition": {
        "id": "string (GUID)",
        "name": "string",
        "roleName": "string",
        "occupantName": "string?"
      },
      "relationshipType": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string",
        "forwardVerb": "string",
        "reverseVerb": "string"
      },
      "description": "string?",
      "createdAt": "string (ISO 8601)"
    }
  ]
}
```

---

### POST /api/position-relationships

Create a position relationship.

**Request:**

```json
{
  "fromPositionId": "string (GUID)",
  "toPositionId": "string (GUID)",
  "relationshipTypeId": "string (GUID)",
  "description": "string?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| fromPositionId | GUID | Yes | Must be active position |
| toPositionId | GUID | Yes | Must be active position, different from fromPositionId |
| relationshipTypeId | GUID | Yes | Must be valid RoleRelationshipType ID |
| description | string | No | Max 500 characters |

---

### PUT /api/position-relationships/{id}

Update a position relationship.

**Request:**

```json
{
  "description": "string?"
}
```

---

### DELETE /api/position-relationships/{id}

Delete a position relationship.

**Response:**

```json
{
  "success": true
}
```

---

## Organization Chart Endpoints

### GET /api/org-chart

Get complete org chart tree structure.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| includeVacant | boolean | true | Include vacant positions |

**Response:**

```json
{
  "success": true,
  "data": {
    "rootNodes": [
      {
        "role": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string",
          "accountability": "string",
          "description": "string?",
          "isVacant": "boolean",
          "isActive": "boolean"
        },
        "assignedPersons": [
          {
            "id": "string (GUID)",
            "displayName": "string",
            "title": "string?",
            "email": "string?",
            "isPrimary": "boolean",
            "effectiveDate": "string (ISO 8601)"
          }
        ],
        "children": [
          "recursive RoleNode"
        ],
        "relationships": null,
        "depth": "number"
      }
    ],
    "totalRoles": "number",
    "totalPersons": "number",
    "vacantRoles": "number",
    "maxDepth": "number",
    "generatedAt": "string (ISO 8601)"
  }
}
```

**Notes:**

- Top-level roles (no reportsTo) are roots of separate trees
- `assignedPersons` is an array to support multiple people assigned to one role
- Empty array when role is vacant

---

### GET /api/org-chart/flat

Get flat list for table/grid display.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| includeVacant | boolean | true | Include vacant positions |
| includeInactive | boolean | false | Include inactive roles |
| sortBy | string | `hierarchy` | `hierarchy`, `name`, `code` |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "roleId": "string (GUID)",
      "roleCode": "string",
      "roleName": "string",
      "occupantId": "string (GUID)?",
      "occupantName": "string?",
      "reportsToRoleId": "string (GUID)?",
      "reportsToRoleName": "string?",
      "depth": "number",
      "path": "string",
      "isVacant": "boolean"
    }
  ]
}
```

**Notes:**

- `path` contains the hierarchy path (e.g., "CEO → VP Sales → Sales Manager")
- When sorted by hierarchy, children appear after parents

---

### GET /api/org-chart/role/{id}/subtree

Get subtree under a specific role.

**Path Parameters:**

- `id` - Role ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| maxDepth | number | 10 | Maximum depth from role |
| includeVacant | boolean | true | Include vacant positions |

**Response:**

```json
{
  "success": true,
  "data": {
    "root": "RoleNode",
    "totalDescendants": "number",
    "vacantCount": "number"
  }
}
```

---

### GET /api/org-chart/layouts/active

Get the current user's active org chart layout (node positions).

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "layoutId": "string (GUID)",
    "layoutName": "string",
    "isActive": true,
    "positions": [
      {
        "roleId": "string (GUID)",
        "positionX": "number",
        "positionY": "number"
      }
    ],
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

**Status Codes:**

- `200` - Success
- `404` - No active layout found

---

### GET /api/org-chart/layouts

Get all org chart layouts for the current user.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "layouts": [
      {
        "layoutId": "string (GUID)",
        "layoutName": "string",
        "isActive": "boolean",
        "positionCount": "number",
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)?"
      }
    ]
  }
}
```

---

### POST /api/org-chart/layouts

Create a new layout or update an existing layout with node positions.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "layoutId": "string (GUID)?",
  "layoutName": "string",
  "positions": [
    {
      "roleId": "string (GUID)",
      "positionX": "number",
      "positionY": "number"
    }
  ],
  "setAsActive": "boolean"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| layoutId | GUID | No | If provided, updates existing layout. Must belong to current user. |
| layoutName | string | Yes | 1-100 characters |
| positions | array | Yes | Array of node positions |
| positions[].roleId | GUID | Yes | Must be valid role in tenant |
| positions[].positionX | number | Yes | X coordinate |
| positions[].positionY | number | Yes | Y coordinate |
| setAsActive | boolean | No | Default: false. If true, sets as active layout after save. |

**Response:**

```json
{
  "success": true,
  "data": {
    "layoutId": "string (GUID)",
    "layoutName": "string",
    "isActive": "boolean",
    "positions": [
      {
        "roleId": "string (GUID)",
        "positionX": "number",
        "positionY": "number"
      }
    ],
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

**Status Codes:**

- `201` - Created (new layout)
- `200` - OK (updated existing layout)
- `400` - Validation error
- `404` - Layout not found (when updating with layoutId)
- `403` - Layout does not belong to user

**Notes:**

- If `layoutId` is null, creates new layout
- If `layoutId` provided, updates existing layout (must belong to current user)
- First layout for user is automatically activated regardless of `setAsActive`
- When `setAsActive` is true, deactivates other layouts for the user

---

### PUT /api/org-chart/layouts/{layoutId}/activate

Set a specific layout as the active layout for the current user.

**Path Parameters:**

- `layoutId` - Layout ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "layoutId": "string (GUID)",
    "layoutName": "string",
    "isActive": true,
    "positions": [
      {
        "roleId": "string (GUID)",
        "positionX": "number",
        "positionY": "number"
      }
    ],
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

**Status Codes:**

- `200` - Success
- `404` - Layout not found
- `403` - Layout does not belong to user

**Notes:**

- Automatically deactivates any currently active layout for the user
- If layout is already active, returns success without changes

---

### DELETE /api/org-chart/layouts/{layoutId}

Delete a layout. Cannot delete the active layout.

**Path Parameters:**

- `layoutId` - Layout ID (GUID)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "message": "Layout deleted successfully"
}
```

**Status Codes:**

- `200` - Success
- `400` - Cannot delete active layout
- `404` - Layout not found
- `403` - Layout does not belong to user

**Notes:**

- Cannot delete a layout that is currently active
- To delete active layout, activate a different layout first

---

## Error Codes Reference

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists (unique constraint) |
| `BUSINESS_RULE_VIOLATION` | 400 | Domain rule prevents operation |
| `CIRCULAR_REFERENCE` | 400 | Would create circular hierarchy (reports_to only) |
| `ROLE_HAS_ASSIGNMENT` | 400 | Role has active person assignment |
| `ROLE_HAS_DIRECT_REPORTS` | 400 | Role has subordinate roles |

---

## Data Types Reference

### RoleStatus

```typescript
type RoleStatus = 'active' | 'inactive';
```

### PositionStatus

```typescript
type PositionStatus = 'active' | 'inactive' | 'vacant';
```

### RoleType

```typescript
interface RoleType {
  id: string;
  code: string;
  name: string;
  description: string | null;
  isStretchRole: boolean;  // Indicates extended responsibility, not full-time
  displayOrder: number;
  isActive: boolean;
  isSystem: boolean;       // System types cannot be deleted
}
```

### OrganizationUnitType

```typescript
interface OrganizationUnitType {
  id: string;
  code: string;
  name: string;
  description: string | null;
  displayOrder: number;
  isActive: boolean;
  isSystem: boolean;       // System types cannot be deleted
}
```

### OrganizationUnit

```typescript
interface OrganizationUnit {
  id: string;
  name: string;
  description: string | null;
  organizationUnitType: OrganizationUnitType;
  parentOrganizationUnitId: string | null;
  unitLeadPersonId: string | null;
  isActive: boolean;
}
```

### Position

```typescript
interface Position {
  id: string;
  name: string;
  description: string | null;
  specificAccountability: string | null;  // Additional context beyond role
  roleId: string;
  organizationUnitId: string;
  personId: string | null;
  reportsToPositionId: string | null;
  status: PositionStatus;
}
```

### PositionRelationship

```typescript
interface PositionRelationship {
  id: string;
  fromPositionId: string;
  toPositionId: string;
  relationshipTypeId: string;  // Uses RoleRelationshipType
  description: string | null;
  createdAt: string;
}
```

### RelationshipTypeCode

```typescript
// Seeded system types (cannot be deleted)
type SystemRelationshipTypeCode = 'SUPPORT' | 'ADVISE' | 'COLLABORATE' | 'MENTOR';

// Custom types are user-defined strings following code constraints
type RelationshipTypeCode = SystemRelationshipTypeCode | string;
```

### RelationshipType

```typescript
interface RelationshipType {
  id: string;
  code: string;
  name: string;
  forwardVerb: string;  // "supports", "advises", "mentors"
  reverseVerb: string;  // "is supported by", "is advised by", "is mentored by"
  allowsMultiple: boolean;
  isActive: boolean;
  isSystem: boolean;    // System types cannot be deleted
}
```

### RoleNode (Org Chart)

```typescript
interface RoleNode {
  role: {
    id: string;
    code: string;
    name: string;
    roleType: RoleType;
  };
  occupant: {
    id: string | null;
    name: string | null;
    title: string | null;
    avatarUrl: string | null;
  } | null;
  isVacant: boolean;
  depth: number;
  children: RoleNode[];
}
```

### PositionNode (Org Chart - Future)

```typescript
interface PositionNode {
  position: {
    id: string;
    name: string;
    roleName: string;
    roleTypeCode: string;
    organizationUnitName: string;
  };
  occupant: {
    id: string | null;
    name: string | null;
    title: string | null;
    avatarUrl: string | null;
  } | null;
  status: PositionStatus;
  depth: number;
  children: PositionNode[];
}
```

### Template Categories

| Code | Name | Description |
|------|------|-------------|
| STARTUP | Startup | Basic structure for small companies |
| SMB | Small/Medium Business | Expanded structure with departments |
| ENTERPRISE | Enterprise | Comprehensive multi-level hierarchy |
| EOS | EOS® | Entrepreneurial Operating System structure |
| SCALING | Scaling Up | Based on Scaling Up methodology |

---

## Seeded Role Types

| Code | Name | Description | Is Stretch Role |
|------|------|-------------|-----------------|
| EXECUTIVE | Executive | C-level and senior leadership roles | No |
| MANAGEMENT | Management | Directors, VPs, and managers | No |
| PROFESSIONAL | Professional | Individual contributors with expertise | No |
| ASSOCIATE | Associate | Entry-level and support roles | No |

---

## Seeded Organization Unit Types

| Code | Name | Description |
|------|------|-------------|
| COMPANY | Company | Top-level organizational unit |
| DIVISION | Division | Major business unit or division |
| DEPARTMENT | Department | Functional department |
| TEAM | Team | Work team or unit |
| PROJECT | Project | Cross-functional project team |

---

## Seeded Relationship Types

| Code | Name | Forward Verb | Reverse Verb | Allows Multiple |
|------|------|--------------|--------------|----------------|
| SUPPORT | Support | supports | is supported by | Yes |
| ADVISE | Advise | advises | is advised by | Yes |
| COLLABORATE | Collaborate | collaborates with | collaborates with | Yes |
| MENTOR | Mentor | mentors | is mentored by | Yes |

**Note:** "Reports To" is NOT a relationship type. Reporting hierarchy is defined directly on the Role entity via the `reportsToRoleId` field. This keeps the hierarchy simple and unidirectional.

---

## Frontend Implementation Notes

### Org Chart Visualization

```typescript
// React component with react-organizational-chart
import { Tree, TreeNode } from 'react-organizational-chart';

const OrgChartNode = ({ role, occupant, isVacant, children }) => (
  <TreeNode label={
    <div className={`org-node ${isVacant ? 'vacant' : ''}`}>
      <div className="role-name">{role.name}</div>
      {occupant ? (
        <div className="occupant">{occupant.name}</div>
      ) : (
        <div className="vacant-badge">Vacant</div>
      )}
    </div>
  }>
    {children.map(child => (
      <OrgChartNode key={child.role.id} {...child} />
    ))}
  </TreeNode>
);
```

### Circular Reference Prevention (Frontend - Reports To Only)

```typescript
// Before setting reportsToRoleId, check for cycles in the hierarchy
const wouldCreateCycle = (
  roleId: string, 
  newReportsToId: string, 
  roles: Role[]
): boolean => {
  const visited = new Set<string>();
  let current = newReportsToId;
  
  while (current) {
    if (current === roleId) return true; // Found cycle!
    if (visited.has(current)) break; // Already visited, no cycle to us
    visited.add(current);
    
    // Find what this role reports to
    const role = roles.find(r => r.id === current);
    current = role?.reportsToRoleId || '';
  }
  
  return false;
};

// Usage in form validation
const handleReportsToChange = (newReportsToId: string) => {
  if (wouldCreateCycle(editingRole.id, newReportsToId, allRoles)) {
    showError('This would create a circular reporting structure');
    return;
  }
  // Proceed with update...
};
```

**Note:** This validation only applies to `reportsToRoleId` on the Role entity. Role relationships (SUPPORT, ADVISE, etc.) are not hierarchical and don't need cycle detection.

---

## WebSocket Events (Future)

The following real-time events will be supported:

| Event | Payload | Description |
|-------|---------|-------------|
| `role.created` | RoleResponse | New role created |
| `role.updated` | RoleResponse | Role details changed |
| `role.deactivated` | { roleId } | Role deactivated |
| `role.assignment_changed` | { roleId, personId, action } | Person assigned/unassigned |
| `org_chart.updated` | - | Hierarchy changed |

---

## Complete API Index

### People Service (Part 1)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login with username/password |
| POST | `/auth/forgot-username` | Request username reminder |
| PUT | `/user/username` | Change username |
| GET | `/api/people` | List people |
| GET | `/api/people/assignable` | Get assignable people for dropdowns |
| GET | `/api/people/{id}` | Get person details |
| POST | `/api/people` | Create person |
| PUT | `/api/people/{id}` | Update person |
| DELETE | `/api/people/{id}` | Delete person |
| POST | `/api/people/{id}/activate` | Activate person |
| POST | `/api/people/{id}/deactivate` | Deactivate person |
| POST | `/api/people/{id}/link-user` | Link person to user |
| POST | `/api/people/{id}/tags` | Add tags |
| DELETE | `/api/people/{id}/tags/{tagId}` | Remove tag |
| GET | `/api/people/{id}/roles` | Get person's roles |
| GET | `/api/people/{id}/roles/history` | Get role history |
| POST | `/api/people/{id}/roles` | Assign role |
| PUT | `/api/people/{id}/roles/{roleId}/primary` | Set primary role |
| DELETE | `/api/people/{id}/roles/{roleId}` | Unassign role |
| GET | `/api/person-types` | List person types |
| GET | `/api/person-types/{id}` | Get person type |
| POST | `/api/person-types` | Create person type |
| PUT | `/api/person-types/{id}` | Update person type |
| DELETE | `/api/person-types/{id}` | Delete person type |
| GET | `/api/person-tags` | List tags |
| POST | `/api/person-tags` | Create tag |
| PUT | `/api/person-tags/{id}` | Update tag |
| DELETE | `/api/person-tags/{id}` | Delete tag |

### Organizational Structure (Part 2)

#### Roles

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/roles` | List roles |
| GET | `/api/roles/dropdown` | Get roles for dropdown |
| GET | `/api/roles/{id}` | Get role details |
| POST | `/api/roles` | Create role |
| PUT | `/api/roles/{id}` | Update role |
| DELETE | `/api/roles/{id}` | Delete role |
| POST | `/api/roles/{id}/activate` | Activate role |
| POST | `/api/roles/{id}/deactivate` | Deactivate role |

#### Role Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/role-types` | List role types |
| GET | `/api/role-types/{id}` | Get role type details |
| POST | `/api/role-types` | Create role type |
| PUT | `/api/role-types/{id}` | Update role type |
| DELETE | `/api/role-types/{id}` | Delete role type |

#### Role Relationships

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/role-relationships` | List relationships |
| POST | `/api/role-relationships` | Create relationship |
| PUT | `/api/role-relationships/{id}` | Update relationship |
| DELETE | `/api/role-relationships/{id}` | Delete relationship |

#### Role Relationship Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/role-relationship-types` | List relationship types |
| GET | `/api/role-relationship-types/{id}` | Get relationship type details |
| POST | `/api/role-relationship-types` | Create relationship type |
| PUT | `/api/role-relationship-types/{id}` | Update relationship type |
| DELETE | `/api/role-relationship-types/{id}` | Delete relationship type |

#### Organization Units

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organization-units` | List organization units |
| GET | `/api/organization-units/tree` | Get org unit hierarchy tree |
| GET | `/api/organization-units/dropdown` | Get simplified list for dropdowns |
| GET | `/api/organization-units/{id}` | Get organization unit details |
| POST | `/api/organization-units` | Create organization unit |
| PUT | `/api/organization-units/{id}` | Update organization unit |
| PUT | `/api/organization-units/{id}/status` | Update organization unit status |
| DELETE | `/api/organization-units/{id}` | Delete organization unit |

#### Organization Unit Types

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/organization-unit-types` | List org unit types |
| GET | `/api/organization-unit-types/{id}` | Get org unit type details |
| POST | `/api/organization-unit-types` | Create org unit type |
| PUT | `/api/organization-unit-types/{id}` | Update org unit type |
| DELETE | `/api/organization-unit-types/{id}` | Delete org unit type |

#### Positions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/positions` | List positions |
| GET | `/api/positions/dropdown` | Get simplified list for dropdowns |
| GET | `/api/positions/tree` | Get hierarchical position tree |
| GET | `/api/positions/{id}` | Get position details |
| POST | `/api/positions` | Create position |
| PUT | `/api/positions/{id}` | Update position |
| DELETE | `/api/positions/{id}` | Delete position |
| POST | `/api/positions/{id}/assign` | Assign person to position |
| POST | `/api/positions/{id}/unassign` | Remove person from position |
| PUT | `/api/positions/{id}/status` | Update position status |

#### Position Relationships

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/position-relationships` | List position relationships |
| POST | `/api/position-relationships` | Create position relationship |
| PUT | `/api/position-relationships/{id}` | Update position relationship |
| DELETE | `/api/position-relationships/{id}` | Delete position relationship |

#### Org Chart

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/org-chart` | Get org chart tree |
| GET | `/api/org-chart/flat` | Get flat org chart |
| GET | `/api/org-chart/role/{id}/subtree` | Get role subtree |
| POST | `/api/roles/preview-template` | Preview template application |
| POST | `/api/roles/apply-template` | Apply template |

> **Note:** Role Templates management (Admin Portal) is documented in [admin-api-specification.md](../admin-portal/admin-api-specification.md)

---

**Document End**

[← Part 1: People](./people-service.md) | [Back to Index](./index.md)
