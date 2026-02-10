# Actions API Specification

**Version:** 7.2  
**Last Updated:** February 9, 2026  
**Base Path:** `/operations/actions`  
**Controller:** `ActionsController.cs`

## Overview

The Actions API manages action items (tasks/to-dos) within the PurposePath traction system. Actions can be linked to goals, strategies, and issues to track execution and progress.

### Key Features
- Complete CRUD operations for action items
- Status management (not_started, in_progress, completed, blocked, cancelled)
- Priority levels (low, medium, high, critical)
- Link actions to goals, strategies, and issues
- Advanced filtering and pagination
- Progress tracking with estimated/actual hours
- Assignment to team members

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. List Actions

Retrieve actions with advanced filtering and pagination.

**Endpoint:** `GET /operations/actions`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `status` | enum | No | Filter by status: `not_started`, `in_progress`, `completed`, `blocked`, `cancelled` |
| `priority` | enum | No | Filter by priority: `low`, `medium`, `high`, `critical` |
| `assignedPersonId` | string (GUID) | No | Filter by assignee |
| `goalIds` | string (CSV) | No | Comma-separated goal IDs to filter by |
| `strategyIds` | string (CSV) | No | Comma-separated strategy IDs |
| `issueIds` | string (CSV) | No | Comma-separated issue IDs |
| `startDate` | datetime (ISO 8601) | No | Filter actions starting after this date |
| `endDate` | datetime (ISO 8601) | No | Filter actions due before this date |
| `search` | string | No | Case-insensitive search in title, description, tags, and assignee name |
| `page` | int | No | Page number (default: 1) |
| `limit` | int | No | Items per page (default: 50, max: 100) |
| `sort` | string | No | Sort field: `dueDate`, `startDate`, `priority`, `status`, `createdAt`, `title` |
| `order` | string | No | Sort order: `asc` or `desc` (default: `asc`) |

#### Request Example

```http
GET /operations/actions?status=in_progress&priority=high&assignedPersonId=person-123&search=pricing&page=1&limit=20&sort=startDate&order=asc
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "success": true,
    "data": [
      {
        "id": "action-123e4567-e89b-12d3-a456-426614174000",
        "tenantId": "tenant-123",
        "title": "Launch new pricing page",
        "description": "Design and deploy updated pricing page with new tier structure",
        "status": "in_progress",
        "priority": "high",
        "startDate": "2025-12-20T00:00:00Z",
        "dueDate": "2025-12-31T00:00:00Z",
        "dateEntered": "2025-12-15T10:00:00Z",
        "assignedPersonId": "person-123",
        "assignedPersonName": "John Doe",
        "progress": 65,
        "estimatedHours": 40,
        "actualHours": 28,
        "tags": ["marketing", "website", "Q4"],
        "connections": {
          "goalIds": ["goal-001"],
          "strategyIds": ["strategy-002"],
          "issueIds": []
        },
        "createdAt": "2025-12-15T10:00:00Z",
        "updatedAt": "2025-12-23T14:30:00Z",
        "createdBy": "user-001",
        "modifiedBy": "user-002",
        "isDeleted": false
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "totalPages": 3,
      "hasNextPage": true,
      "hasPreviousPage": false
    }
  },
  "error": null
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (GUID) | Unique action identifier |
| `tenantId` | string | Organization identifier |
| `title` | string | Action title/summary (max 200 chars) |
| `description` | string | Detailed description (max 2000 chars) |
| `status` | enum | Current status (see Status enum below) |
| `priority` | enum | Priority level (see Priority enum below) |
| `startDate` | datetime | When action should start |
| `dueDate` | datetime | When action is due |
| `dateEntered` | datetime | When action was originally entered (may differ from createdAt) |
| `assignedPersonId` | string (GUID) | Person responsible for this action |
| `assignedPersonName` | string | Name of assigned person (read-only) |
| `progress` | int | Completion percentage (0-100) |
| `estimatedHours` | decimal | Estimated effort in hours |
| `actualHours` | decimal | Actual time spent in hours |
| `tags` | string[] | Tags for categorization/filtering |
| `connections` | object | Related entities (goals, strategies, issues) |
| `createdAt` | datetime | When action was created |
| `updatedAt` | datetime | Last update timestamp |
| `createdBy` | string (GUID) | User who created the action |
| `modifiedBy` | string (GUID) | User who last modified the action |
| `isDeleted` | boolean | Soft delete flag |

#### Status Enum

```typescript
enum ActionStatus {
  NotStarted = "not_started",    // Planned but not begun
  InProgress = "in_progress",    // Currently being worked on
  Completed = "completed",       // Finished successfully
  Blocked = "blocked",           // Blocked by dependency/issue
  Cancelled = "cancelled"        // Cancelled/abandoned
}
```

#### Priority Enum

```typescript
enum Priority {
  Low = "low",           // Can wait
  Medium = "medium",     // Standard priority
  High = "high",         // Important, time-sensitive
  Critical = "critical"  // Urgent, must be done ASAP
}
```

---

### 2. Create Action

Create a new action item.

**Endpoint:** `POST /operations/actions`

#### Request Body

```json
{
  "title": "Launch new pricing page",
  "description": "Design and deploy updated pricing page with new tier structure",
  "startDate": "2025-12-20T00:00:00Z",
  "dueDate": "2025-12-31T00:00:00Z",
  "priority": "high",
  "status": "in_progress",
  "progress": 25,
  "assignedPersonId": "person-123",
  "estimatedHours": 40,
  "tags": ["marketing", "website", "Q4"],
  "dateEntered": "2025-12-15T10:00:00Z",
  "connections": {
    "goalIds": ["goal-001"],
    "strategyIds": ["strategy-002"],
    "issueIds": []
  }
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | **Yes** | Action title (max 200 chars) |
| `description` | string | No | Detailed description (max 2000 chars) |
| `startDate` | datetime (ISO 8601) | **Yes** | Start date |
| `dueDate` | datetime (ISO 8601) | **Yes** | Due date |
| `priority` | enum | **Yes** | `low`, `medium`, `high`, `critical` |
| `status` | enum | No | Initial status: `not_started`, `in_progress`, `completed`, `blocked`, `cancelled` (defaults to `not_started`) |
| `progress` | int | No | Initial progress percentage (0-100, defaults to 0) |
| `assignedPersonId` | string (GUID) | **Yes** | Person responsible |
| `estimatedHours` | decimal | No | Estimated effort in hours |
| `tags` | string[] | No | Tags for categorization |
| `dateEntered` | datetime | No | Original entry date (defaults to now) |
| `connections` | object | No | Link to goals, strategies, issues |
| `connections.goalIds` | string[] | No | Goal IDs to link |
| `connections.strategyIds` | string[] | No | Strategy IDs to link |
| `connections.issueIds` | string[] | No | Issue IDs to link |

#### Response

**Status:** `200 OK` (Note: Should be 201 Created per REST standards)

```json
{
  "success": true,
  "data": {
    "id": "action-new-123",
    "tenantId": "tenant-123",
    "title": "Launch new pricing page",
    "description": "Design and deploy updated pricing page with new tier structure",
    "status": "in_progress",
    "priority": "high",
    "startDate": "2025-12-20T00:00:00Z",
    "dueDate": "2025-12-31T00:00:00Z",
    "assignedPersonId": "person-123",
    "assignedPersonName": "John Doe",
    "progress": 25,
    "estimatedHours": 40,
    "actualHours": 0,
    "tags": ["marketing", "website", "Q4"],
    "connections": {
      "goalIds": ["goal-001"],
      "strategyIds": ["strategy-002"],
      "issueIds": []
    },
    "createdAt": "2025-12-23T16:45:00Z",
    "updatedAt": "2025-12-23T16:45:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Default status:** New actions default to `not_started` status if not provided
- **Default progress:** New actions default to 0% progress if not provided
- **Completed actions:** If status is `completed`, progress is automatically set to 100% regardless of provided value
- **Progress validation:** Progress must be between 0 and 100 (inclusive)
- **Date validation:** `dueDate` must be after `startDate`
- **Person validation:** `assignedPersonId` must exist in tenant
- **Connections:** Goals, strategies, issues are linked after action creation
- **Invalid connection IDs:** Invalid GUID formats are filtered out (action still created)

---

### 3. Get Action

Retrieve details of a specific action.

**Endpoint:** `GET /operations/actions/{actionId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "action-123",
    "title": "Launch new pricing page",
    "status": "in_progress",
    "priority": "high",
    "progress": 65,
    "estimatedHours": 40,
    "actualHours": 28,
    "connections": {
      "goalIds": ["goal-001"],
      "strategyIds": ["strategy-002"],
      "issueIds": []
    }
  },
  "error": null
}
```

#### Error Responses

**Status:** `404 Not Found`
```json
{
  "success": false,
  "data": null,
  "error": "Action not found"
}
```

---

### 4. Update Action Status

Update only the status of an action.

**Endpoint:** `PUT /operations/actions/{actionId}/status`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Request Body

```json
{
  "status": "completed",
  "reason": "All tasks completed successfully",
  "actualHours": 35
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `status` | enum | **Yes** | New status: `not_started`, `in_progress`, `completed`, `blocked`, `cancelled` |
| `reason` | string | No | Reason for status change (recommended) |
| `actualHours` | decimal | No | Actual hours spent (usually provided when marking completed) |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "action-123",
    "status": "completed",
    "actualHours": 35,
    "progress": 100,
    "updatedAt": "2025-12-23T17:00:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Auto-progress:** Completing an action automatically sets `progress` to 100
- **Blocked actions:** Can include `reason` to explain blocker
- **Status transitions:** Any status can transition to any other status (no restrictions)

---

### 5. Update Action

Update action details (title, description, dates, priority, etc.).

**Endpoint:** `PUT /operations/actions/{actionId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Request Body

```json
{
  "title": "Launch new pricing page (revised)",
  "description": "Updated scope: Include testimonials section",
  "startDate": "2025-12-20T00:00:00Z",
  "dueDate": "2026-01-10T00:00:00Z",
  "priority": "high",
  "status": "in_progress",
  "progress": 75,
  "assignedPersonId": "person-456",
  "estimatedHours": 50,
  "actualHours": 32,
  "tags": ["marketing", "website", "Q4", "testimonials"]
}
```

#### Request Fields

All fields are optional. Only provided fields will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Updated title |
| `description` | string | Updated description |
| `startDate` | datetime | Updated start date |
| `dueDate` | datetime | Updated due date |
| `priority` | enum | Updated priority |
| `status` | enum | Updated status |
| `progress` | int | Updated progress (0-100) |
| `assignedPersonId` | string (GUID) | Reassign to different person |
| `estimatedHours` | decimal | Updated estimate |
| `actualHours` | decimal | Updated actual hours |
| `tags` | string[] | Updated tags |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "action-123",
    "title": "Launch new pricing page (revised)",
    "description": "Updated scope: Include testimonials section",
    "dueDate": "2026-01-10T00:00:00Z",
    "priority": "high",
    "status": "in_progress",
    "progress": 75,
    "assignedPersonId": "person-456",
    "updatedAt": "2025-12-23T17:15:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Partial updates:** Only provided fields are updated
- **Status handling:** Status updates trigger separate command internally
- **Progress updates:** Progress updates trigger separate command internally
- **Reassignment:** Changing `assignedPersonId` triggers reassignment logic

---

### 6. Delete Action

Soft delete an action.

**Endpoint:** `DELETE /operations/actions/{actionId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "deletedActionId": "action-123",
    "deletedAt": "2025-12-23T17:30:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Soft delete:** Action is marked as deleted but preserved in database
- **Relationships:** Connections to goals/strategies/issues are also soft deleted
- **Historical data:** All historical tracking is preserved

---

### 7. Link Action to Goals

Link an action to one or more goals.

**Endpoint:** `PUT /operations/actions/{actionId}/goals`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Request Body

```json
{
  "goalIds": ["goal-001", "goal-002"]
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `goalIds` | string[] (GUID) | **Yes** | Goal IDs to link (replaces existing links) |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "action-123",
    "connections": {
      "goalIds": ["goal-001", "goal-002"],
      "strategyIds": ["strategy-002"],
      "issueIds": []
    }
  },
  "error": null
}
```

#### Business Rules

- **Replace behavior:** Replaces existing goal links (not additive)
- **Multi-goal:** Actions can be linked to multiple goals
- **Validation:** All goal IDs must exist in tenant

---

### 8. Link Action to Strategies

Link an action to one or more strategies.

**Endpoint:** `PUT /operations/actions/{actionId}/strategies`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Request Body

```json
{
  "strategyIds": ["strategy-001", "strategy-002"]
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `strategyIds` | string[] (GUID) | **Yes** | Strategy IDs to link (replaces existing links) |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "action-123",
    "connections": {
      "goalIds": ["goal-001"],
      "strategyIds": ["strategy-001", "strategy-002"],
      "issueIds": []
    }
  },
  "error": null
}
```

#### Business Rules

- **Replace behavior:** Replaces existing strategy links (not additive)
- **Multi-strategy:** Actions can be linked to multiple strategies

---

### 9. Link Action to Issues

Link an action to one or more issues.

**Endpoint:** `PUT /operations/actions/{actionId}/issues`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Request Body

```json
{
  "issueIds": ["issue-001", "issue-002"]
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `issueIds` | string[] (GUID) | **Yes** | Issue IDs to link (replaces existing links, empty array clears links) |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "action-123",
    "connections": {
      "goalIds": ["goal-001"],
      "strategyIds": ["strategy-002"],
      "issueIds": ["issue-001", "issue-002"]
    }
  },
  "error": null
}
```

#### Business Rules

- **Replace behavior:** Replaces existing issue links (not additive)
- **Multi-issue:** Actions can be linked to multiple issues
- **Empty array support:** Passing an empty array (`[]`) clears all issue connections
- **Validation:** All issue IDs must be valid GUIDs

---

### 10. Remove All Relationships

Remove all connections (goals, strategies, issues) from an action.

**Endpoint:** `DELETE /operations/actions/{actionId}/relationships`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actionId` | string (GUID) | **Yes** | Action identifier |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "action-123",
    "connections": {
      "goalIds": [],
      "strategyIds": [],
      "issueIds": []
    }
  },
  "error": null
}
```

#### Business Rules

- **Complete removal:** Removes all goal, strategy, and issue connections
- **Action preserved:** The action itself is not deleted, only relationships

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "data": null,
  "error": "Error message here"
}
```

### Common Error Codes

| Code | Scenario | Message Example |
|------|----------|-----------------|
| 400 | Invalid GUID format | "Invalid actionId format 'abc'. Must be a valid GUID." |
| 400 | Invalid enum value | "Invalid status value 'pending'. Allowed values: not_started, in_progress, completed, blocked, cancelled" |
| 400 | Invalid date format | "Invalid dueDate format '12/31/2025'. Must be a valid ISO 8601 date." |
| 400 | Date logic error | "DueDate must be after StartDate" |
| 401 | Missing/invalid token | "Unauthorized" |
| 403 | Insufficient permissions | "Access denied to this action" |
| 404 | Action not found | "Action not found" |
| 422 | Validation failure | "Title cannot be empty" |
| 500 | Server error | "Internal server error" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
import { traction } from './traction';

// List actions with filters
const actions = await traction.get<GetActionsResponse>('/operations/actions', {
  params: {
    status: 'in_progress',
    priority: 'high',
    assignedPersonId: 'person-123',
    page: 1,
    limit: 20
  }
});

// Create action with connections
const newAction = await traction.post<ActionResponse>('/operations/actions', {
  title: 'Launch new feature',
  description: 'Complete feature development and QA',
  startDate: '2025-12-20T00:00:00Z',
  dueDate: '2025-12-31T00:00:00Z',
  priority: 'high',
  assignedPersonId: 'person-123',
  estimatedHours: 40,
  tags: ['feature', 'Q4'],
  connections: {
    goalIds: ['goal-001'],
    strategyIds: ['strategy-002']
  }
});

// Update action status
await traction.put(`/operations/actions/${actionId}/status`, {
  status: 'completed',
  reason: 'All tasks completed',
  actualHours: 38
});

// Update action details
await traction.put(`/operations/actions/${actionId}`, {
  title: 'Updated title',
  dueDate: '2026-01-15T00:00:00Z',
  progress: 80
});

// Link to goals
await traction.put(`/operations/actions/${actionId}/goals`, {
  goalIds: ['goal-001', 'goal-002']
});

// Link to issues
await traction.put(`/operations/actions/${actionId}/issues`, {
  issueIds: ['issue-001', 'issue-002']
});

// Clear issue links (empty array)
await traction.put(`/operations/actions/${actionId}/issues`, {
  issueIds: []
});

// Delete action
await traction.delete(`/operations/actions/${actionId}`);
```

---

## Related APIs

- **[Goals API](./goals-api.md)** - Manage goals that actions support
- **[Strategies API](./strategies-api.md)** - Strategies that actions implement
- **[Issues API](./issues-api.md)** - Issues that actions resolve
- **[People API](./people-api.md)** - People assigned to actions

---

## Changelog

### v7.2 (February 9, 2026)
- ✅ Added `search` query parameter to List Actions endpoint for searching title, description, tags, and assignee name
- ✅ Added `startDate` as a sort option (previously supported in backend but not exposed in API)
- 📝 Enhanced filtering capabilities with case-insensitive substring search

### v7.1 (February 6, 2026)
- ✅ Added endpoint #9: `PUT /operations/actions/{actionId}/issues` - Link action to issues
- 📝 Added support for empty array to clear issue connections
- 📝 Updated endpoint count from 9 to 10 endpoints
- 📝 Renumbered "Remove All Relationships" from #9 to #10

### v7.0 (December 23, 2025)
- ✅ Documented all 9 endpoints with complete examples
- 📝 Complete request/response structures for all operations
- 📝 Advanced filtering with multiple parameters
- 📝 Status and priority enums with descriptions
- 📝 Connection/relationship management endpoints
- 📝 Business rules and validation constraints
- 📝 Frontend TypeScript usage examples
- 📝 Error handling with specific codes

### v6.0 (Previous)
- Initial action management endpoints

---

**[← Back to Traction Service Index](./README.md)**
