# Goals API Specification

**Controller:** `GoalsController`  
**Base Route:** `/goals`  
**Version:** 7.1  
**Last Updated:** December 27, 2025

[← Back to API Index](./README.md)

---

## Overview

The Goals API manages the complete lifecycle of business goals, including creation, updates, status transitions, strategies, and activity tracking.

**Endpoints:** 14 total
- 3 CRUD operations (List, Create, Get, Update, Delete)
- 3 status transitions (Close, Activate, Pause)
- 2 activity endpoints (Get activity, Add activity)
- 1 notes endpoint
- 1 statistics endpoint
- 2 Measure endpoints (Set Measure threshold, Get available Measures)
- 2 strategy endpoints (Create strategy, Update strategy)

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. List Goals

**GET** `/goals`

Retrieve a filtered, paginated list of goals.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | number | No | 1 | Page number (1-indexed) |
| `pageSize` | number | No | 20 | Items per page (max 100) |
| `sortBy` | string | No | "createdAt" | Sort field: "name", "status", "startDate", "targetDate", "createdAt" |
| `sortOrder` | string | No | "desc" | Sort direction: "asc" or "desc" |
| `status` | string | No | - | Filter by status: "draft", "active", "paused", "completed", "cancelled" |
| `personId` | string (UUID) | No | - | Filter by assigned person |
| `type` | string | No | - | Filter by goal type |
| `searchTerm` | string | No | - | Search in goal name and description |

#### Response 200

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Increase Revenue by 25%",
        "description": "Achieve 25% revenue growth through new markets",
        "status": "active",
        "type": "annual",
        "targetDate": "2025-12-31T23:59:59.999Z",
        "startDate": "2025-01-01T00:00:00.000Z",
        "completionDate": null,
        "progress": 42.5,
        "owner": {
          "id": "user-123",
          "firstName": "John",
          "lastName": "Doe",
          "email": "john@example.com"
        },
        "strategiesCount": 3,
        "measuresCount": 5,
        "actionsCount": 12,
        "issuesCount": 2,
        "createdAt": "2025-01-01T00:00:00.000Z",
        "updatedAt": "2025-12-20T15:30:00.000Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 45,
      "totalPages": 3
    }
  },
  "error": null,
  "timestamp": "2025-12-23T10:30:00.000Z"
}
```

---

### 2. Create Goal

**POST** `/goals`

Create a new goal.

#### Request Body

```json
{
  "name": "Increase Revenue by 25%",
  "description": "Achieve 25% revenue growth through new markets and product expansion",
  "type": "annual",
  "targetDate": "2025-12-31T23:59:59.999Z",
  "startDate": "2025-01-01T00:00:00.000Z",
  "ownerId": "user-123",
  "status": "draft"
}
```

#### Request Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `name` | string | Yes | 1-200 chars | Goal name |
| `description` | string | No | Max 2000 chars | Detailed description |
| `type` | string | Yes | See enum below | Goal type/timeframe |
| `targetDate` | string (ISO 8601) | Yes | Future date | Target completion date |
| `startDate` | string (ISO 8601) | No | Defaults to today | Goal start date |
| `ownerId` | string (UUID) | Yes | Must exist | Responsible person ID |
| `status` | string | No | Default: "draft" | Initial status |

**Type Enum:**
- `annual` - Year-long goal
- `quarterly` - 3-month goal
- `monthly` - 30-day goal
- `custom` - Custom timeframe

**Status Enum:**
- `draft` - Being planned
- `active` - In progress
- `paused` - Temporarily stopped
- `completed` - Successfully finished
- `cancelled` - Abandoned

#### Response 201

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Increase Revenue by 25%",
    "description": "Achieve 25% revenue growth through new markets and product expansion",
    "status": "draft",
    "type": "annual",
    "targetDate": "2025-12-31T23:59:59.999Z",
    "startDate": "2025-01-01T00:00:00.000Z",
    "completionDate": null,
    "progress": 0,
    "owner": {
      "id": "user-123",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com"
    },
    "createdAt": "2025-12-23T10:30:00.000Z",
    "updatedAt": "2025-12-23T10:30:00.000Z",
    "createdBy": "user-123",
    "tenantId": "tenant-456"
  },
  "error": null,
  "timestamp": "2025-12-23T10:30:00.000Z"
}
```

---

### 3. Get Goal Details

**GET** `/goals/{id}`

Retrieve detailed information about a specific goal, including strategies, Measures, and metrics.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Response 200

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Increase Revenue by 25%",
    "description": "Achieve 25% revenue growth through new markets",
    "status": "active",
    "type": "annual",
    "targetDate": "2025-12-31T23:59:59.999Z",
    "startDate": "2025-01-01T00:00:00.000Z",
    "completionDate": null,
    "progress": 42.5,
    "owner": {
      "id": "user-123",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com",
      "role": "CEO"
    },
    "strategies": [
      {
        "id": "strat-001",
        "name": "Expand to APAC Markets",
        "description": "Enter 5 new markets in Asia-Pacific region",
        "order": 1,
        "status": "active",
        "progress": 60,
        "measuresCount": 3,
        "createdAt": "2025-01-15T00:00:00.000Z"
      }
    ],
    "measures": [
      {
        "id": "measure-001",
        "name": "Monthly Recurring Revenue",
        "unit": "USD",
        "currentValue": 125000,
        "targetValue": 150000,
        "progress": 83.3,
        "status": "on_track",
        "isPrimary": true
      }
    ],
    "statistics": {
      "strategiesCount": 3,
      "measuresCount": 5,
      "actionsCount": 12,
      "openIssuesCount": 2,
      "completedActionsCount": 8,
      "overallHealth": "on_track"
    },
    "recentActivity": [
      {
        "id": "act-001",
        "type": "measure_updated",
        "description": "MRR updated to $125,000",
        "createdAt": "2025-12-22T15:30:00.000Z",
        "createdBy": {
          "firstName": "Jane",
          "lastName": "Smith"
        }
      }
    ],
    "createdAt": "2025-01-01T00:00:00.000Z",
    "updatedAt": "2025-12-20T15:30:00.000Z",
    "createdBy": "user-123",
    "tenantId": "tenant-456"
  },
  "error": null,
  "timestamp": "2025-12-23T10:30:00.000Z"
}
```

---

### 4. Update Goal

**PUT** `/goals/{id}`

Update an existing goal's properties.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Request Body

```json
{
  "name": "Increase Revenue by 30%",
  "description": "Updated target to 30% growth",
  "targetDate": "2025-12-31T23:59:59.999Z",
  "ownerId": "user-456"
}
```

#### Request Fields

All fields are optional (only include fields to update):

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | string | 1-200 chars | Goal name |
| `description` | string | Max 2000 chars | Description |
| `type` | string | See enum | Goal type |
| `targetDate` | string (ISO 8601) | Future date | Target date |
| `startDate` | string (ISO 8601) | - | Start date |
| `ownerId` | string (UUID) | Must exist | Owner ID |

**Note:** Status is updated via dedicated endpoints (activate, pause, close)

#### Response 200

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Increase Revenue by 30%",
    "description": "Updated target to 30% growth",
    "status": "active",
    "type": "annual",
    "targetDate": "2025-12-31T23:59:59.999Z",
    "startDate": "2025-01-01T00:00:00.000Z",
    "progress": 42.5,
    "owner": {
      "id": "user-456",
      "firstName": "Jane",
      "lastName": "Smith"
    },
    "updatedAt": "2025-12-23T10:35:00.000Z"
  },
  "error": null,
  "timestamp": "2025-12-23T10:35:00.000Z"
}
```

---

### 5. Delete Goal

**DELETE** `/goals/{id}`

Permanently delete a goal and all associated data (strategies, Measure links, activities).

⚠️ **Warning:** This operation cannot be undone. Consider closing instead.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Response 200

```json
{
  "success": true,
  "data": {
    "message": "Goal deleted successfully"
  },
  "error": null,
  "timestamp": "2025-12-23T10:40:00.000Z"
}
```

---

### 6. Close Goal

**POST** `/goals/{id}:close`

Close a goal marking it as completed or cancelled.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Request Body

```json
{
  "finalStatus": "completed",
  "notes": "Successfully achieved 30% revenue growth"
}
```

#### Request Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `finalStatus` | string | Yes | "completed" or "cancelled" | Final status |
| `notes` | string | No | Max 1000 chars | Closing notes |

#### Response 200

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "completionDate": "2025-12-23T10:45:00.000Z",
    "progress": 100,
    "finalNotes": "Successfully achieved 30% revenue growth"
  },
  "error": null,
  "timestamp": "2025-12-23T10:45:00.000Z"
}
```

---

### 7. Activate Goal

**POST** `/goals/{id}:activate`

Activate a goal, transitioning from draft or paused status to active.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Request Body

```json
{}
```

No body required (empty object or omit).

#### Response 200

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "active",
    "activatedAt": "2025-12-23T10:50:00.000Z"
  },
  "error": null,
  "timestamp": "2025-12-23T10:50:00.000Z"
}
```

---

### 8. Pause Goal

**POST** `/goals/{id}:pause`

Temporarily pause an active goal.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Request Body

```json
{
  "reason": "Waiting for budget approval"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `reason` | string | No | Reason for pausing |

#### Response 200

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "paused",
    "pausedAt": "2025-12-23T10:55:00.000Z",
    "pauseReason": "Waiting for budget approval"
  },
  "error": null,
  "timestamp": "2025-12-23T10:55:00.000Z"
}
```

---

### 9. Get Goal Activity

**GET** `/goals/{id}/activity`

Retrieve activity feed for a goal (updates, changes, comments).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `page` | number | No | 1 | Page number |
| `pageSize` | number | No | 20 | Items per page |
| `types` | string | No | - | Comma-separated activity types to filter |

**Activity Types:**
- `goal_created`, `goal_updated`, `goal_status_changed`
- `strategy_added`, `strategy_updated`, `strategy_removed`
- `measure_linked`, `measure_unlinked`, `measure_updated`
- `comment_added`, `note_added`

#### Response 200

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "activity-001",
        "type": "measure_updated",
        "entityType": "measure",
        "entityId": "measure-001",
        "description": "MRR updated from $120,000 to $125,000",
        "metadata": {
          "measureName": "Monthly Recurring Revenue",
          "previousValue": 120000,
          "newValue": 125000
        },
        "createdAt": "2025-12-22T15:30:00.000Z",
        "createdBy": {
          "id": "user-123",
          "firstName": "John",
          "lastName": "Doe"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 156,
      "totalPages": 8
    }
  },
  "error": null,
  "timestamp": "2025-12-23T11:00:00.000Z"
}
```

---

### 10. Add Goal Activity

**POST** `/goals/{id}/activity`

Add a manual activity entry (comment, note, update).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Request Body

```json
{
  "type": "comment",
  "content": "Updated strategy based on Q4 results",
  "metadata": {
    "relatedStrategyId": "strat-001"
  }
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Activity type: "comment", "note", "update" |
| `content` | string | Yes | Activity content (max 2000 chars) |
| `metadata` | object | No | Additional structured data |

#### Response 201

```json
{
  "success": true,
  "data": {
    "id": "activity-002",
    "type": "comment",
    "content": "Updated strategy based on Q4 results",
    "createdAt": "2025-12-23T11:05:00.000Z",
    "createdBy": {
      "id": "user-123",
      "firstName": "John",
      "lastName": "Doe"
    }
  },
  "error": null,
  "timestamp": "2025-12-23T11:05:00.000Z"
}
```

---

### 11. Add Goal Note

**POST** `/goals/{id}/notes`

Add a note to a goal (similar to activity but specifically for notes).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string (UUID) | Goal identifier |

#### Request Body

```json
{
  "content": "Meeting scheduled with stakeholders for Jan 15",
  "category": "planning"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | Yes | Note content (max 5000 chars) |
| `category` | string | No | Note category for organization |

#### Response 201

```json
{
  "success": true,
  "data": {
    "id": "note-001",
    "content": "Meeting scheduled with stakeholders for Jan 15",
    "category": "planning",
    "createdAt": "2025-12-23T11:10:00.000Z",
    "createdBy": {
      "id": "user-123",
      "firstName": "John",
      "lastName": "Doe"
    }
  },
  "error": null,
  "timestamp": "2025-12-23T11:10:00.000Z"
}
```

---

### 12. Get Goal Statistics

**GET** `/goals/stats`

Get aggregated statistics across all goals for the tenant.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `type` | string | No | Filter by goal type |
| `ownerId` | string (UUID) | No | Filter by owner |

#### Response 200

```json
{
  "success": true,
  "data": {
    "totalGoals": 45,
    "byStatus": {
      "draft": 5,
      "active": 30,
      "paused": 3,
      "completed": 5,
      "cancelled": 2
    },
    "byType": {
      "annual": 20,
      "quarterly": 15,
      "monthly": 10
    },
    "averageProgress": 52.3,
    "onTrackCount": 25,
    "atRiskCount": 8,
    "offTrackCount": 2,
    "totalMeasures": 125,
    "totalStrategies": 89,
    "totalActions": 456
  },
  "error": null,
  "timestamp": "2025-12-23T11:15:00.000Z"
}
```

---

### 13. Set Measure Threshold

**POST** `/goals/{goalId}/measures/{measureId}:setThreshold`

Set a threshold percentage for a Measure linked to a goal.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `goalId` | string (UUID) | Goal identifier |
| `measureId` | string (UUID) | Measure identifier |

#### Request Body

```json
{
  "thresholdPct": 85.0
}
```

#### Request Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `thresholdPct` | number | Yes | 0-100 | Threshold percentage |

**Threshold Behavior:**
- Measure shows warning when progress falls below this percentage
- Used for status calculations (on_track, at_risk, off_track)
- Typical values: 80-90%

#### Response 200

```json
{
  "success": true,
  "data": {
    "goalId": "550e8400-e29b-41d4-a716-446655440000",
    "measureId": "measure-001",
    "thresholdPct": 85.0,
    "updatedAt": "2025-12-23T11:20:00.000Z"
  },
  "error": null,
  "timestamp": "2025-12-23T11:20:00.000Z"
}
```

---

### 14. Get Available Measures

**GET** `/goals/{goalId}/available-measures`

Retrieve all Measures available for linking to a specific goal, including:
- Catalog Measures (predefined industry-standard Measures)
- Tenant custom Measures (organization-specific Measures)

Each Measure includes usage statistics showing how many goals are currently using it and whether the specified goal is already using it.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `goalId` | string (UUID) | Goal identifier |

#### Response 200

```json
{
  "success": true,
  "data": {
    "catalogMeasures": [
      {
        "id": "catalog-001",
        "name": "Monthly Recurring Revenue",
        "description": "Total predictable revenue from subscriptions",
        "category": "Financial",
        "unit": "USD",
        "direction": "increase",
        "type": "leading",
        "valueType": "currency",
        "aggregationType": "sum",
        "aggregationPeriod": "monthly",
        "calculationMethod": "Sum of all active subscription values",
        "isIntegrationEnabled": true,
        "usageInfo": {
          "goalCount": 3,
          "isUsedByThisGoal": false
        }
      }
    ],
    "tenantCustomMeasures": [
      {
        "id": "custom-measure-001",
        "name": "Customer Satisfaction Score",
        "description": "Average CSAT from post-purchase surveys",
        "category": "Customer Experience",
        "unit": "score",
        "direction": "increase",
        "type": "lagging",
        "valueType": "percentage",
        "aggregationType": "average",
        "aggregationPeriod": "monthly",
        "calculationMethod": "Average of all survey responses",
        "measureCatalogId": null,
        "isIntegrationEnabled": false,
        "createdAt": "2025-01-15T10:00:00.000Z",
        "createdBy": "user-123",
        "usageInfo": {
          "goalCount": 1,
          "isUsedByThisGoal": true
        }
      }
    ]
  },
  "error": null,
  "timestamp": "2025-12-23T11:30:00.000Z"
}
```

#### Response Fields

**Catalog Measure:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | string (UUID) | Measure catalog entry ID |
| `name` | string | Measure display name |
| `description` | string | What the Measure measures |
| `category` | string | Business category (Financial, Operations, Customer, etc.) |
| `unit` | string | Measurement unit (USD, %, count, score, etc.) |
| `direction` | string | `"increase"` or `"decrease"` - desired trend |
| `type` | string | `"leading"` or `"lagging"` indicator |
| `valueType` | string | `"number"`, `"currency"`, `"percentage"`, `"boolean"` |
| `aggregationType` | string | `"sum"`, `"average"`, `"max"`, `"min"`, `"count"`, `"latest"` |
| `aggregationPeriod` | string | `"daily"`, `"weekly"`, `"monthly"`, `"quarterly"`, `"annually"` |
| `calculationMethod` | string | How the Measure is calculated |
| `isIntegrationEnabled` | boolean | Whether external integrations can populate this Measure |
| `usageInfo` | object | Usage statistics for this Measure |

**Tenant Custom Measure:**
| Field | Type | Description |
|-------|------|-------------|
| All fields from Catalog Measure | - | Same as above |
| `measureCatalogId` | string (UUID) or null | Reference to catalog Measure if based on template |
| `createdAt` | string (ISO 8601) | When the custom Measure was created |
| `createdBy` | string (UUID) | User who created the custom Measure |

**Usage Info:**
| Field | Type | Description |
|-------|------|-------------|
| `goalCount` | number | Number of goals currently using this Measure |
| `isUsedByThisGoal` | boolean | Whether the specified goal is already using this Measure |

#### Use Cases

1. **Measure Selection Dialog**: Display available Measures when user wants to link Measure to goal
2. **Prevent Duplicates**: Show `isUsedByThisGoal` to prevent linking same Measure twice
3. **Popular Measures**: Sort by `goalCount` to show most commonly used Measures
4. **Filter by Category**: Group Measures by category for better UX

#### Error Responses

**404 Not Found**
```json
{
  "success": false,
  "data": null,
  "error": "Goal not found",
  "timestamp": "2025-12-23T11:30:00.000Z"
}
```

**400 Bad Request**
```json
{
  "success": false,
  "data": null,
  "error": "Invalid goal ID format",
  "timestamp": "2025-12-23T11:30:00.000Z"
}
```

#### Notes

- Returns both catalog Measures (predefined) and tenant custom Measures
- Usage statistics updated in real-time
- Only returns Measures accessible to the tenant
- Catalog Measures are read-only; tenant custom Measures can be modified
- Use [Measure Links API](./measure-links-api.md) to actually link a Measure to the goal
- For new (unpersisted) goals, use `GET /goals/available-measures` (see Measures API) to fetch the catalog without a goalId

---

## Error Responses

### 400 Bad Request

```json
{
  "success": false,
  "data": null,
  "error": "Invalid goal ID format",
  "timestamp": "2025-12-23T11:25:00.000Z"
}
```

### 404 Not Found

```json
{
  "success": false,
  "data": null,
  "error": "Goal not found",
  "timestamp": "2025-12-23T11:25:00.000Z"
}
```

### 422 Unprocessable Entity

```json
{
  "success": false,
  "data": null,
  "error": "Cannot activate goal that is already active",
  "timestamp": "2025-12-23T11:25:00.000Z"
}
```

---

## Business Rules

### Goal Status Transitions

Valid transitions:
- `draft` → `active`, `cancelled`
- `active` → `paused`, `completed`, `cancelled`
- `paused` → `active`, `cancelled`
- `completed` - Terminal state (no transitions)
- `cancelled` - Terminal state (no transitions)

### Deletion Rules

- Cannot delete goal with active linked Measures
- Cannot delete goal with open issues
- Deleting goal also deletes: strategies, activity history, notes
- Deleting goal unlinks: Measures (Measure instances remain), actions, people

### Validation Rules

- Goal name: 1-200 characters, required
- Description: max 2000 characters
- Target date: must be in future
- Start date: must be before target date
- Owner: must be valid person in tenant
- Type: must be valid enum value

---

## Examples

### Frontend Usage (TypeScript)

```typescript
import { traction } from '@/services/traction';

// List active goals
const { data } = await traction.get('/goals', {
  params: { status: 'active', pageSize: 10 }
});

// Create new goal
const newGoal = await traction.post('/goals', {
  name: 'Increase Revenue by 25%',
  description: 'Achieve 25% revenue growth',
  type: 'annual',
  targetDate: '2025-12-31T23:59:59.999Z',
  ownerId: currentUser.id,
  status: 'draft'
});

// Activate goal
await traction.post(`/goals/${goalId}:activate`);

// Close goal
await traction.post(`/goals/${goalId}:close`, {
  finalStatus: 'completed',
  notes: 'Successfully achieved target'
});
```

---

## Related APIs

- [Strategies API](./strategies-api.md) - Manage goal strategies
- [Measure Links API](./measure-links-api.md) - Link Measures to goals
- [Actions API](./actions-api.md) - Link actions to goals
- [Activities API](./activities-api.md) - Activity feeds

---

## Changelog

### v7.1 (December 27, 2025)
- **Restored** `/goals/{goalId}/available-measures` endpoint (Issue #413)
- Updated to work with new `IMeasureLinkRepository` architecture
- Added comprehensive documentation with usage examples
- Endpoint now supports unified Measure linking for Goals, Strategies, and People

### v7.0 (December 23, 2025)
- Removed deprecated `/goals/{goalId}/measures:link` endpoint
- Removed deprecated `/goals/{goalId}/measures:unlink` endpoint  
- ~~Removed deprecated `/goals/{goalId}/available-measures` endpoint~~ (Restored in v7.1)
- Measure operations moved to dedicated `/measure-links` API
- Added comprehensive documentation with examples

### v6.0 (December 21, 2025)
- Added Measure linking endpoints (now deprecated)
- Added activity endpoints
- Added statistics endpoint
