# Organizational Structure Service - API Specification

**Version:** 2.0  
**Last Updated:** December 26, 2025  
**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`

[← People Service](./people-service.md) | [Back to Index](./index.md)

## Changelog

| Version | Date | Changes |
|---------|------|----------|
| 2.0 | December 26, 2025 | **BREAKING:** Converted all JSON properties from snake_case to camelCase to match C#/.NET implementation (e.g., `role_id` → `roleId`, `reports_to` → `reportsTo`). Query parameters also converted to camelCase. This matches ASP.NET Core default JSON serialization. |
| 1.2 | December 23, 2025 | Moved admin template endpoints to Admin Portal specification |
| 1.1 | December 21, 2025 | Migrated endpoints from Traction service to Account service |
| 1.0 | December 21, 2025 | Initial version |

> **📋 NOTE:** Admin Template endpoints have been moved to the [Admin Portal API Specification](../admin-portal/admin-api-specification.md#role-templates).

---

## Overview

The Organizational Structure module manages roles, role relationships (reporting/collaboration), and organization charts. It provides the foundation for the accountability framework within PurposePath.

### Frontend Implementation

- **Primary Client:** `accountClient` (axios instance) ⚠️ *Changed from tractionClient*
- **Related Files:**
  - `src/services/roles-service.ts` - Role CRUD operations
  - `src/services/role-relationships-service.ts` - Reporting/collaboration structures
  - `src/services/org-chart-service.ts` - Organization chart visualization

### Key Concepts

- **Role**: A defined position/function within the organization
- **Role Relationship**: Non-hierarchical connection between roles (Support, Advise, Collaborate, Mentor)
- **Reports To**: Hierarchical relationship defined on Role entity (not a relationship type)
- **Org Chart**: Hierarchical visualization of role relationships

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
    "isActive": true,
    "currentOccupant": null,
    "reportsTo": [],
    "directReports": [],
    "collaboratesWith": [],
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

## Organization Chart Endpoints

### GET /api/org-chart

Get complete org chart tree structure.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| rootRoleId | GUID | - | Start tree from specific role |
| maxDepth | number | 10 | Maximum hierarchy depth |
| includeVacant | boolean | true | Include vacant positions |
| includeInactive | boolean | false | Include inactive roles |

**Response:**

```json
{
  "success": true,
  "data": {
    "tree": [
      {
        "role": {
          "id": "string (GUID)",
          "code": "string",
          "name": "string"
        },
        "occupant": {
          "id": "string (GUID)?",
          "name": "string?",
          "title": "string?",
          "avatarUrl": "string?"
        },
        "isVacant": "boolean",
        "depth": "number",
        "children": [
          "recursive RoleNode"
        ]
      }
    ],
    "totalRoles": "number",
    "totalVacant": "number",
    "maxDepth": "number"
  }
}
```

**Notes:**

- Top-level roles (no reportsTo) are roots of separate trees
- If `rootRoleId` specified, returns single tree starting from that role

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

### Template Categories

| Code | Name | Description |
|------|------|-------------|
| STARTUP | Startup | Basic structure for small companies |
| SMB | Small/Medium Business | Expanded structure with departments |
| ENTERPRISE | Enterprise | Comprehensive multi-level hierarchy |
| EOS | EOS® | Entrepreneurial Operating System structure |
| SCALING | Scaling Up | Based on Scaling Up methodology |

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
| GET | `/api/role-relationships` | List relationships |
| POST | `/api/role-relationships` | Create relationship |
| PUT | `/api/role-relationships/{id}` | Update relationship |
| DELETE | `/api/role-relationships/{id}` | Delete relationship |
| GET | `/api/role-relationship-types` | List relationship types |
| GET | `/api/role-relationship-types/{id}` | Get relationship type details |
| POST | `/api/role-relationship-types` | Create relationship type |
| PUT | `/api/role-relationship-types/{id}` | Update relationship type |
| DELETE | `/api/role-relationship-types/{id}` | Delete relationship type |
| GET | `/api/org-chart` | Get org chart tree |
| GET | `/api/org-chart/flat` | Get flat org chart |
| GET | `/api/org-chart/role/{id}/subtree` | Get role subtree |
| POST | `/api/roles/preview-template` | Preview template application |
| POST | `/api/roles/apply-template` | Apply template |

> **Note:** Role Templates management (Admin Portal) is documented in [admin-api-specification.md](../admin-portal/admin-api-specification.md)

---

**Document End**

[← Part 1: People](./people-service.md) | [Back to Index](./index.md)
