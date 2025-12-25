# Organizational Structure Service - API Specification

**Version:** 1.2  
**Created:** December 21, 2025  
**Updated:** December 23, 2025  
**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`

> **⚠️ MIGRATION NOTE (v1.1):** Roles and Org Chart endpoints have been migrated from Traction service to Account service. Update frontend clients to use `accountClient` instead of `tractionClient`.

> **📋 NOTE:** Admin Template endpoints have been moved to the [Admin Portal API Specification](../admin-portal/admin-api-specification.md#role-templates).

[← People Service](./people-service.md) | [Back to Index](./index.md)

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
| page_size | number | 20 | Items per page (max 100) |
| sort_by | string | `name` | Sort field: `name`, `code`, `created_at` |
| sort_order | string | `asc` | Sort order: `asc`, `desc` |

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
        "is_active": "boolean",
        "current_occupant": {
          "id": "string (GUID)?",
          "name": "string?",
          "since": "string (ISO 8601)?"
        },
        "reports_to": {
          "role_id": "string (GUID)?",
          "role_name": "string?"
        },
        "direct_reports_count": "number",
        "created_at": "string (ISO 8601)",
        "updated_at": "string (ISO 8601)?"
      }
    ],
    "pagination": {
      "page": "number",
      "page_size": "number",
      "total_items": "number",
      "total_pages": "number"
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
| include_vacant | boolean | true | Include vacant roles |
| exclude_id | string (GUID) | - | Exclude specific role (for relationship forms) |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "code": "string",
      "name": "string",
      "occupant_name": "string?",
      "is_vacant": "boolean"
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
    "is_active": "boolean",
    "current_occupant": {
      "id": "string (GUID)?",
      "first_name": "string?",
      "last_name": "string?",
      "email": "string?",
      "title": "string?",
      "since": "string (ISO 8601)?",
      "is_primary_role": "boolean?"
    },
    "assignment_history": [
      {
        "person_id": "string (GUID)",
        "person_name": "string",
        "effective_date": "string (ISO 8601)",
        "termination_date": "string (ISO 8601)?"
      }
    ],
    "reports_to": {
      "role_id": "string (GUID)?",
      "role_code": "string?",
      "role_name": "string?",
      "occupant_name": "string?"
    },
    "direct_reports": [
      {
        "role_id": "string (GUID)",
        "role_code": "string",
        "role_name": "string",
        "occupant_name": "string?"
      }
    ],
    "relationships": [
      {
        "relationship_id": "string (GUID)",
        "direction": "from | to",
        "role_id": "string (GUID)",
        "role_code": "string",
        "role_name": "string",
        "occupant_name": "string?",
        "relationship_type": {
          "code": "string",
          "name": "string",
          "verb": "string"
        },
        "description": "string?"
      }
    ],
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)?",
    "created_by": "string (GUID)",
    "updated_by": "string (GUID)?"
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
    "resource_type": "Role",
    "resource_id": "guid"
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
  "reports_to_role_id": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| code | string | Yes | 2-20 chars, uppercase alphanumeric + underscore, unique within tenant |
| name | string | Yes | 1-100 characters |
| accountability | string | Yes | 1-500 characters, describes what this role is accountable for |
| description | string | No | Max 2000 characters (detailed responsibilities, can include markdown) |
| reports_to_role_id | GUID | No | Must be valid active role |

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
    "is_active": true,
    "current_occupant": null,
    "reports_to": [],
    "direct_reports": [],
    "collaborates_with": [],
    "created_at": "string (ISO 8601)",
    "created_by": "string (GUID)"
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
  "reports_to_role_id": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| name | string | No | 1-100 characters |
| accountability | string | No | 1-500 characters, describes what this role is accountable for |
| description | string | No | Max 2000 characters (detailed responsibilities) |
| reports_to_role_id | GUID | No | Must be active role, cannot create circular reference, set to `null` to remove |

**Notes:**

- `code` cannot be changed after creation
- Setting `reports_to_role_id` to `null` removes the reporting relationship (makes role a top-level role)
- Backend validates no circular references when changing reports_to
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
    "occupant_id": "guid",
    "occupant_name": "John Smith"
  }
}
```

```json
{
  "success": false,
  "error": "Cannot delete role with direct reports",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "direct_reports_count": 5
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
    "is_active": true
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
  "cascade_direct_reports": "boolean?",
  "new_parent_role_id": "string (GUID)?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| cascade_direct_reports | boolean | No | If true, deactivate all direct reports |
| new_parent_role_id | GUID | No | Reassign direct reports to this role |

**Default Behavior (when no options provided):**

- Direct reports' `reports_to_role_id` is set to `null` (they become top-level roles)
- The deactivated role's person assignment is terminated (if any)
- All relationships (SUPPORT, ADVISE, etc.) involving this role are removed

**Response:**

```json
{
  "success": true,
  "data": {
    "deactivated": true,
    "person_unassigned": "boolean",
    "relationships_removed": "number",
    "direct_reports_handled": {
      "reassigned_to": "string (GUID)?",
      "deactivated_count": "number?"
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
| type | string | - | Filter by type: `reports_to`, `collaborates_with` |
| role_id | GUID | - | Get relationships for specific role |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "from_role": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string",
        "occupant_name": "string?"
      },
      "to_role": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string",
        "occupant_name": "string?"
      },
      "relationship_type": {
        "id": "string (GUID)",
        "code": "string",
        "name": "string"
      },
      "description": "string?",
      "created_at": "string (ISO 8601)"
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
  "from_role_id": "string (GUID)",
  "to_role_id": "string (GUID)",
  "relationship_type_code": "string",
  "description": "string?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| from_role_id | GUID | Yes | Must be active role |
| to_role_id | GUID | Yes | Must be active role, different from from_role_id |
| relationship_type_code | string | Yes | Valid relationship type code (e.g., `SUPPORT`, `ADVISE`, `COLLABORATE`, `MENTOR`) |
| description | string | No | Max 500 chars |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "from_role": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "to_role": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "relationship_type": {
      "id": "string (GUID)",
      "code": "string",
      "name": "string"
    },
    "description": "string?",
    "created_at": "string (ISO 8601)"
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
    "existing_relationship_id": "guid"
  }
}
```

```json
{
  "success": false,
  "error": "Relationship type does not allow multiple relationships",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "relationship_type_code": "MENTOR",
    "existing_relationship_id": "guid"
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
| include_inactive | boolean | false | Include inactive types |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string (GUID)",
      "code": "SUPPORT",
      "name": "Support",
      "forward_verb": "supports",
      "reverse_verb": "is supported by",
      "allows_multiple": true,
      "is_active": true,
      "is_system": true
    },
    {
      "id": "string (GUID)",
      "code": "ADVISE",
      "name": "Advise",
      "forward_verb": "advises",
      "reverse_verb": "is advised by",
      "allows_multiple": true,
      "is_active": true,
      "is_system": true
    },
    {
      "id": "string (GUID)",
      "code": "COLLABORATE",
      "name": "Collaborate",
      "forward_verb": "collaborates with",
      "reverse_verb": "collaborates with",
      "allows_multiple": true,
      "is_active": true,
      "is_system": true
    },
    {
      "id": "string (GUID)",
      "code": "MENTOR",
      "name": "Mentor",
      "forward_verb": "mentors",
      "reverse_verb": "is mentored by",
      "allows_multiple": true,
      "is_active": true,
      "is_system": true
    }
  ]
}
```

**Notes:**

- `is_system` indicates seeded types that cannot be deleted
- `forward_verb` used when displaying "Role A {forward_verb} Role B"
- `reverse_verb` used when displaying "Role B {reverse_verb} Role A"

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
    "forward_verb": "string",
    "reverse_verb": "string",
    "allows_multiple": "boolean",
    "is_active": "boolean",
    "is_system": "boolean",
    "usage_count": "number",
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)?"
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
  "forward_verb": "string",
  "reverse_verb": "string",
  "allows_multiple": "boolean?"
}
```

**Field Constraints:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| code | string | Yes | 2-20 chars, uppercase alphanumeric + underscore, unique within tenant |
| name | string | Yes | 1-50 characters |
| forward_verb | string | Yes | 1-50 characters (e.g., "manages") |
| reverse_verb | string | Yes | 1-50 characters (e.g., "is managed by") |
| allows_multiple | boolean | No | Default: true |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "name": "string",
    "forward_verb": "string",
    "reverse_verb": "string",
    "allows_multiple": "boolean",
    "is_active": true,
    "is_system": false,
    "created_at": "string (ISO 8601)"
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
  "forward_verb": "string?",
  "reverse_verb": "string?",
  "allows_multiple": "boolean?"
}
```

**Notes:**

- `code` cannot be changed after creation
- System types (`is_system = true`) can have name/verbs updated but not deleted

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
    "is_system": true
  }
}
```

```json
{
  "success": false,
  "error": "Cannot delete relationship type with existing relationships",
  "code": "BUSINESS_RULE_VIOLATION",
  "details": {
    "usage_count": 5
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
| root_role_id | GUID | - | Start tree from specific role |
| max_depth | number | 10 | Maximum hierarchy depth |
| include_vacant | boolean | true | Include vacant positions |

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
          "avatar_url": "string?"
        },
        "is_vacant": "boolean",
        "depth": "number",
        "children": [
          "recursive RoleNode"
        ]
      }
    ],
    "total_roles": "number",
    "total_vacant": "number",
    "max_depth": "number"
  }
}
```

**Notes:**

- Top-level roles (no reports_to) are roots of separate trees
- If `root_role_id` specified, returns single tree starting from that role

---

### GET /api/org-chart/flat

Get flat list for table/grid display.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| include_vacant | boolean | true | Include vacant positions |
| sort_by | string | `hierarchy` | `hierarchy`, `name`, `code` |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "role_id": "string (GUID)",
      "role_code": "string",
      "role_name": "string",
      "occupant_id": "string (GUID)?",
      "occupant_name": "string?",
      "reports_to_role_id": "string (GUID)?",
      "reports_to_role_name": "string?",
      "depth": "number",
      "path": "string",
      "is_vacant": "boolean"
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
| max_depth | number | 10 | Maximum depth from role |
| include_vacant | boolean | true | Include vacant positions |

**Response:**

```json
{
  "success": true,
  "data": {
    "root": "RoleNode",
    "total_descendants": "number",
    "vacant_count": "number"
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
  forward_verb: string;  // "supports", "advises", "mentors"
  reverse_verb: string;  // "is supported by", "is advised by", "is mentored by"
  allows_multiple: boolean;
  is_active: boolean;
  is_system: boolean;    // System types cannot be deleted
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
    avatar_url: string | null;
  } | null;
  is_vacant: boolean;
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

**Note:** "Reports To" is NOT a relationship type. Reporting hierarchy is defined directly on the Role entity via the `reports_to_role_id` field. This keeps the hierarchy simple and unidirectional.

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
// Before setting reports_to_role_id, check for cycles in the hierarchy
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
    current = role?.reports_to_role_id || '';
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

**Note:** This validation only applies to `reports_to_role_id` on the Role entity. Role relationships (SUPPORT, ADVISE, etc.) are not hierarchical and don't need cycle detection.

---

## WebSocket Events (Future)

The following real-time events will be supported:

| Event | Payload | Description |
|-------|---------|-------------|
| `role.created` | RoleResponse | New role created |
| `role.updated` | RoleResponse | Role details changed |
| `role.deactivated` | { role_id } | Role deactivated |
| `role.assignment_changed` | { role_id, person_id, action } | Person assigned/unassigned |
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
