# Traction Service Backend Integration Specifications (v5)

**Version:** 5.0 - Complete Endpoint Documentation  
**Last Updated:** 2025-01-XX  
**Service Base URL:** `{REACT_APP_TRACTION_API_URL}`  
**Default (Localhost):** `http://localhost:8002`

[← Back to Index](./backend-integration-index.md)

---

## Document Overview

This specification documents **ALL** Traction API endpoints currently called by the frontend application. Each endpoint includes:

- Complete URL path
- HTTP method
- Full request payload structure (with nested objects expanded)
- Full response payload structure (with nested objects expanded)
- Data constraints (enums, validation rules, expected values)
- Query parameters
- Path parameters

**Important Notes:**

- Routes do NOT include `/api` prefix - base URL already contains full path
- All dates are ISO 8601 format strings (e.g., `"2025-01-15T10:30:00Z"`)
- Frontend uses camelCase for field names
- Backend may use PascalCase for some fields (noted in transformations)
- Nested response structures: `response.data.data?.data || response.data.data || response.data`
- All endpoints require authentication via `Authorization: Bearer {token}` header
- All endpoints require `X-Tenant-Id` header for multi-tenancy

---

## Complete API Index

### Goals Management (8 endpoints)
1. `POST /goals` - Create goal
2. `GET /goals` - List goals
3. `GET /goals/{id}` - Get goal details
4. `PUT /goals/{id}` - Update goal
5. `DELETE /goals/{id}` - Delete goal
6. `POST /goals/{id}:activate` - Activate goal
7. `POST /goals/{id}:pause` - Pause goal
8. `POST /goals/{id}:close` - Close goal

### Strategies (4 endpoints)
9. `POST /goals/{goalId}/strategies` - Create strategy
10. `PUT /goals/{goalId}/strategies/{id}` - Update strategy
11. `DELETE /goals/{goalId}/strategies/{id}` - Delete strategy
12. `PUT /goals/{goalId}/strategies:reorder` - Reorder strategies

### KPI Management (7 endpoints)
13. `POST /kpis` - Create KPI instance
14. `GET /kpis/{id}` - Get KPI details
15. `PUT /kpis/{id}` - Update KPI instance
16. `DELETE /kpis/{id}` - Delete KPI instance
17. `GET /kpis` - List KPIs
18. `GET /goals/{goalId}/kpis` - List KPIs for goal
19. `PUT /goals/{goalId}/kpis/{kpiId}:setPrimary` - Set KPI as primary

### KPI Linking (5 endpoints)
20. `POST /goals/{goalId}/kpis:link` - Link KPI to goal
21. `POST /goals/{goalId}/kpis:unlink` - Unlink KPI from goal
22. `POST /goals/{goalId}/kpis/{kpiId}:setThreshold` - Set KPI threshold
23. `GET /goals/{goalId}/kpis/{kpiId}:link` - Get KPI linkage details
24. `GET /goals/{goalId}/available-kpis` - Get available KPIs for goal

### KPI Planning (10 endpoints)
25. `GET /kpi-planning/kpis/{id}/milestones` - Get KPI milestones
26. `PUT /kpi-planning/kpis/{id}/milestones` - Set KPI milestones
27. `GET /kpi-planning/kpis/{id}/plan` - Get KPI planning data
28. `GET /kpi-planning/goals/{goalId}/kpi-planning` - Get goal KPI planning overview
29. `GET /kpi-planning/kpis/{id}/actuals` - Get KPI actuals (historical measurements)
30. `POST /kpi-planning/kpis/{id}/actuals` - Record KPI actual value
31. `POST /kpi-planning/kpis/{id}/adjust` - Adjust KPI plan
32. `GET /kpi-planning/kpis/{kpiId}/cross-goal-impact` - Get cross-goal impact
33. `GET /kpi-planning/kpis/{id}/replan-rule` - Get replan rule
34. `PUT /kpi-planning/kpis/{id}/replan-rule` - Update replan rule

### Actions (7 endpoints)
35. `GET /operations/actions` - List actions
36. `POST /operations/actions` - Create action
37. `PUT /operations/actions/{id}` - Update action
38. `DELETE /operations/actions/{id}` - Delete action
39. `PUT /operations/actions/{id}/goals` - Link action to goals
40. `PUT /operations/actions/{id}/strategies` - Link action to strategies
41. `DELETE /operations/actions/{id}/relationships` - Remove action relationships

### Issues (4 endpoints)
42. `GET /issues` - List issues
43. `POST /issues` - Create issue
44. `PUT /issues/{id}` - Update issue
45. `DELETE /issues/{id}` - Delete issue

### Issue Types (5 endpoints)
46. `GET /operations/issue-types` - List issue types
47. `POST /operations/issue-types` - Create issue type
48. `PUT /operations/issue-types/{id}` - Update issue type
49. `DELETE /operations/issue-types/{id}` - Delete issue type
50. `POST /operations/issue-types/{id}:activate` - Activate issue type

### Issue Statuses (6 endpoints)
51. `GET /operations/issue-statuses` - List issue statuses
52. `POST /operations/issue-statuses` - Create issue status
53. `PUT /operations/issue-statuses/{id}` - Update issue status
54. `DELETE /operations/issue-statuses/{id}` - Delete issue status
55. `POST /operations/issue-statuses/{id}:activate` - Activate issue status
56. `PUT /operations/issue-statuses:reorder` - Reorder issue statuses

### Issue Lifecycle (4 endpoints - uses fetch, not traction client)
57. `POST /issues/{id}/root-cause` - Root cause analysis
58. `POST /issues/{id}/convert-to-actions` - Convert issue to actions
59. `GET /issues/{id}/closure-eligibility` - Check closure eligibility
60. `POST /issues/{id}/close` - Close issue

### Operations Integration (4 endpoints)
61. `POST /operations/kpi-updates` - Sync KPI update
62. `POST /operations/actions/goals` - Get goals for actions
63. `POST /operations/actions/strategies` - Get strategies for actions
64. `POST /operations/goals/kpis` - Get KPIs for goals

### Activity (2 endpoints)
65. `GET /goals/{goalId}/activity` - Get goal activity
66. `POST /goals/{goalId}/activity` - Add activity entry

### Alignment (1 endpoint)
67. `POST /alignment/check` - Calculate alignment

### Reports (1 endpoint)
68. `GET /reports/company` - Generate company report

**Total: 68 API endpoints**

---

## Type Definitions

### Core Enums

```typescript
// Goal lifecycle
type GoalStatus = 'draft' | 'active' | 'completed' | 'paused' | 'cancelled' | 'archived';

// Strategy validation
type StrategyStatus = 'draft' | 'validated' | 'adopted';

// Action tracking
type ActionStatus = 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
type ActionPriority = 'low' | 'medium' | 'high' | 'critical';

// Issue management
type IssueImpact = 'low' | 'medium' | 'high' | 'critical';
type IssuePriority = 'low' | 'medium' | 'high' | 'critical';
type IssueStatusCategory = 'open' | 'active' | 'inactive' | 'closed';

// KPI direction
type KPIDirection = 'up' | 'down'; // up = higher is better, down = lower is better

// KPI types
type KPIType = 'quantitative' | 'qualitative' | 'binary';

// KPI aggregation types
type AggregationType = 'sum' | 'average' | 'min' | 'max' | 'latest' | 'count' | 'pointInTime';

// KPI aggregation periods
type AggregationPeriod = 'none' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';

// KPI data nature
type DataNature = 'snapshot' | 'aggregate' | 'other';

// KPI interpolation methods
type InterpolationMethod = 'linear' | 'exponential' | 'step';

// KPI adjustment strategies
type AdjustmentStrategy = 'maintain_final_goal' | 'proportional_shift' | 'custom';

// KPI data sources
type KPIDataSource = 'manual' | 'action' | 'integration';

// Cross-goal alert decisions
type AlertDecision = 'accepted' | 'rejected' | 'modified';
```

---

## Goals Management

### 1. POST /goals

Create a new goal.

**Request Body:**
```json
{
  "title": "Increase Revenue",
  "intent": "We want to increase revenue by 50% through improved customer retention and new market expansion",
  "description": "Optional additional context about the goal",
  "ownerId": "user_123"
}
```

**Request Constraints:**
- `title`: string, required, max 200 characters
- `intent`: string, required, max 2000 characters
- `description`: string, optional, max 5000 characters
- `ownerId`: string, required, valid user ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "goal_456",
    "title": "Increase Revenue",
    "intent": "We want to increase revenue by 50% through improved customer retention and new market expansion",
    "description": "Optional additional context about the goal",
    "status": "draft",
    "ownerId": "user_123",
    "alignmentScore": 0,
    "alignmentExplanation": "",
    "alignmentSuggestions": [],
    "strategies": [],
    "kpis": [],
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-01-15T10:30:00Z"
  }
}
```

**Response Constraints:**
- `status`: defaults to `"draft"`
- `alignmentScore`: number, 0-100
- `strategies`: array, initially empty
- `kpis`: array, initially empty
- Dates are ISO 8601 strings

---

### 2. GET /goals

List goals with optional filtering.

**Query Parameters:**
- `ownerId` (optional): string - Filter by owner ID

**Response:**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "id": "goal_456",
        "title": "Increase Revenue",
        "intent": "We want to increase revenue by 50%...",
        "description": "Optional additional context",
        "status": "draft",
        "ownerId": "user_123",
        "alignmentScore": 85,
        "alignmentExplanation": "Goal aligns well with vision",
        "alignmentSuggestions": ["Consider adding specific metrics"],
        "strategies": [
          {
            "id": "strategy_789",
            "goalId": "goal_456",
            "description": "Improve customer retention through loyalty programs",
            "order": 1,
            "aiGenerated": false,
            "validationScore": null,
            "validationFeedback": null,
            "status": "draft",
            "createdAt": "2025-01-15T11:00:00Z",
            "updatedAt": "2025-01-15T11:00:00Z"
          }
        ],
        "kpis": [
          {
            "id": "goalkpi_101",
            "goalId": "goal_456",
            "kpiId": "kpi_202",
            "order": 1,
            "createdAt": "2025-01-15T11:30:00Z",
            "updatedAt": "2025-01-15T11:30:00Z"
          }
        ],
        "createdAt": "2025-01-15T10:30:00Z",
        "updatedAt": "2025-01-15T11:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 1,
      "hasMore": false
    }
  }
}
```

**Response Structure:**
- Nested structure: `response.data.data?.data || response.data.data || []`
- Pagination object may be present

---

### 3. GET /goals/{id}

Get detailed goal information.

**Path Parameters:**
- `id`: string, required - Goal ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "goal_456",
    "title": "Increase Revenue",
    "intent": "We want to increase revenue by 50%...",
    "description": "Optional additional context",
    "status": "active",
    "ownerId": "user_123",
    "alignmentScore": 85,
    "alignmentExplanation": "Goal aligns well with vision and purpose",
    "alignmentSuggestions": [
      "Consider adding specific customer retention metrics",
      "Link to customer satisfaction KPIs"
    ],
    "strategies": [
      {
        "id": "strategy_789",
        "goalId": "goal_456",
        "description": "Improve customer retention through loyalty programs",
        "order": 1,
        "aiGenerated": false,
        "validationScore": 75,
        "validationFeedback": "Strategy shows promise with clear approach",
        "status": "validated",
        "createdAt": "2025-01-15T11:00:00Z",
        "updatedAt": "2025-01-16T09:00:00Z"
      }
    ],
    "kpis": [
      {
        "id": "goalkpi_101",
        "goalId": "goal_456",
        "kpiId": "kpi_202",
        "order": 1,
        "createdAt": "2025-01-15T11:30:00Z",
        "updatedAt": "2025-01-15T11:30:00Z"
      }
    ],
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-01-16T09:00:00Z"
  }
}
```

---

### 4. PUT /goals/{id}

Update goal information.

**Path Parameters:**
- `id`: string, required - Goal ID

**Request Body:**
```json
{
  "title": "Increase Revenue by 60%",
  "intent": "Updated intent description",
  "description": "Updated description",
  "status": "active"
}
```

**Request Constraints:**
- All fields are optional (partial update)
- `title`: string, max 200 characters
- `intent`: string, max 2000 characters
- `description`: string, max 5000 characters
- `status`: GoalStatus enum

**Response:**
Same structure as GET /goals/{id}

---

### 5. DELETE /goals/{id}

Delete a goal (soft delete).

**Path Parameters:**
- `id`: string, required - Goal ID

**Response:**
```json
{
  "success": true
}
```

**Status Codes:**
- `200` - Success
- `404` - Goal not found

---

### 6. POST /goals/{id}:activate

Activate a goal (transition from draft or paused to active).

**Path Parameters:**
- `id`: string, required - Goal ID

**Request Body:**
```json
{
  "reason": "Ready to begin Q1 execution"
}
```

**Request Constraints:**
- `reason`: string, optional, max 500 characters

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "goal_456",
    "status": "active",
    // ... other goal fields
  }
}
```

**Status Transitions:**
- `draft` → `active` (starting the goal)
- `paused` → `active` (resuming the goal)

**Status Codes:**
- `200` - Success
- `400` - Cannot activate goal in current state
- `404` - Goal not found

---

### 7. POST /goals/{id}:pause

Pause a goal (transition from active to paused).

**Path Parameters:**
- `id`: string, required - Goal ID

**Request Body:**
```json
{
  "reason": "Temporarily pausing due to resource constraints"
}
```

**Request Constraints:**
- `reason`: string, optional, max 500 characters

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "goal_456",
    "status": "paused",
    // ... other goal fields
  }
}
```

**Status Transitions:**
- `active` → `paused`

**Status Codes:**
- `200` - Success
- `400` - Cannot pause goal in current state
- `404` - Goal not found

---

### 8. POST /goals/{id}:close

Close a goal (transition to completed or cancelled).

**Path Parameters:**
- `id`: string, required - Goal ID

**Request Body:**
```json
{
  "finalStatus": "completed",
  "reason": "Goal achieved ahead of schedule"
}
```

**Request Constraints:**
- `finalStatus`: string, required, must be `"completed"` or `"cancelled"`
- `reason`: string, optional, max 500 characters

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "goal_456",
    "status": "completed",
    // ... other goal fields
  }
}
```

**Status Transitions:**
- `active` → `completed` (only from active)
- Any status except `completed` → `cancelled`

**Status Codes:**
- `200` - Success
- `400` - Cannot close goal in current state
- `404` - Goal not found

---

## Strategies Management

### 9. POST /goals/{goalId}/strategies

Create a new strategy for a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Request Body:**
```json
{
  "title": "Customer Retention Program",
  "goalId": "goal_456",
  "description": "Implement a comprehensive customer loyalty program with tiered rewards",
  "order": 1,
  "aiGenerated": false
}
```

**Request Constraints:**
- `title`: string, required, max 200 characters
- `goalId`: string, required, must match path parameter
- `description`: string, required, max 5000 characters
- `order`: number, optional, defaults to next available order
- `aiGenerated`: boolean, optional, defaults to `false`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "strategy_789",
    "goalId": "goal_456",
    "description": "Implement a comprehensive customer loyalty program with tiered rewards",
    "order": 1,
    "aiGenerated": false,
    "validationScore": null,
    "validationFeedback": null,
    "status": "draft",
    "createdAt": "2025-01-15T11:00:00Z",
    "updatedAt": "2025-01-15T11:00:00Z"
  }
}
```

**Response Constraints:**
- `status`: defaults to `"draft"`
- `validationScore`: number | null, 0-100 when set
- `validationFeedback`: string | null

---

### 10. PUT /goals/{goalId}/strategies/{id}

Update a strategy.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `id`: string, required - Strategy ID

**Request Body:**
```json
{
  "description": "Updated strategy description",
  "order": 2,
  "status": "validated"
}
```

**Request Constraints:**
- All fields are optional (partial update)
- `description`: string, max 5000 characters
- `order`: number, positive integer
- `status`: StrategyStatus enum

**Response:**
Same structure as POST response

---

### 11. DELETE /goals/{goalId}/strategies/{id}

Delete a strategy.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `id`: string, required - Strategy ID

**Response:**
```json
{
  "success": true
}
```

**Status Codes:**
- `200` - Success
- `404` - Strategy not found

---

### 12. PUT /goals/{goalId}/strategies:reorder

Reorder strategies within a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Request Body:**
```json
{
  "goalId": "goal_456",
  "strategyOrders": [
    {
      "strategyId": "strategy_789",
      "newOrder": 2
    },
    {
      "strategyId": "strategy_790",
      "newOrder": 1
    }
  ]
}
```

**Request Constraints:**
- `goalId`: string, required, must match path parameter
- `strategyOrders`: array, required, min 1 item
  - `strategyId`: string, required, valid strategy ID
  - `newOrder`: number, required, positive integer, unique within array

**Response:**
```json
{
  "success": true
}
```

---

## KPI Management

### 13. POST /kpis

Create a new KPI instance (catalog-based or custom).

**Request Body:**
```json
{
  "catalogId": "catalog_kpi_1",
  "name": "Monthly Recurring Revenue",
  "description": "Total predictable revenue per month from subscriptions",
  "unit": "USD",
  "direction": "up",
  "type": "quantitative",
  "category": "Financial",
  "aggregationType": "sum",
  "aggregationPeriod": "monthly",
  "valueType": "aggregate",
  "currentValue": 42000,
  "currentValueDate": "2025-01-15",
  "calculationMethod": "Sum of all subscription revenues",
  "measurementFrequency": "monthly",
  "ownerId": "user_123"
}
```

**Request Constraints:**

**If `catalogId` provided** (catalog-based KPI):
- `name`, `description`, `unit`, `direction`, `type`, `category`: OPTIONAL (inherited from catalog, can be overridden)
- `aggregationType`, `aggregationPeriod`, `valueType`: OPTIONAL (inherited from catalog, can be overridden)

**If `catalogId` is null/omitted** (custom KPI):
- `name`: REQUIRED, max 200 characters
- `description`: REQUIRED, max 2000 characters
- `unit`: REQUIRED, max 50 characters
- `direction`: REQUIRED, KPIDirection enum
  - Valid values: `"up"` | `"down"`
  - `"up"` = higher values are better (e.g., revenue, customer satisfaction)
  - `"down"` = lower values are better (e.g., costs, churn rate)
- `type`: REQUIRED, KPIType enum
  - Valid values: `"quantitative"` | `"qualitative"` | `"binary"`
  - `"quantitative"` = numeric measurements (e.g., revenue, units sold)
  - `"qualitative"` = descriptive/categorical (e.g., customer sentiment: excellent/good/poor)
  - `"binary"` = yes/no, true/false, pass/fail
- `aggregationType`: REQUIRED, AggregationType enum
  - Valid values: `"sum"` | `"average"` | `"min"` | `"max"` | `"latest"` | `"count"` | `"pointInTime"`
  - `"sum"` = add all values in period (e.g., total sales)
  - `"average"` = mean of all values in period
  - `"min"` = lowest value in period
  - `"max"` = highest value in period
  - `"latest"` = most recent value in period
  - `"count"` = number of occurrences
  - `"pointInTime"` = snapshot at specific moment (no aggregation)
- `aggregationPeriod`: REQUIRED, AggregationPeriod enum
  - Valid values: `"none"` | `"daily"` | `"weekly"` | `"monthly"` | `"quarterly"` | `"yearly"`
  - `"none"` = no time-based aggregation (use with pointInTime)
  - `"daily"` = aggregate data by day
  - `"weekly"` = aggregate data by week
  - `"monthly"` = aggregate data by month
  - `"quarterly"` = aggregate data by quarter
  - `"yearly"` = aggregate data by year
- `valueType`: REQUIRED, DataNature enum
  - Valid values: `"snapshot"` | `"aggregate"` | `"other"`
  - `"snapshot"` = point-in-time measurement (e.g., account balance, inventory level)
  - `"aggregate"` = accumulated over time (e.g., monthly revenue, total sales)
  - `"other"` = neither snapshot nor aggregate
- `category`: OPTIONAL, max 100 characters

**Optional fields (all KPI types):**
- `currentValue`: number, optional (defaults to null if omitted)
- `currentValueDate`: ISO date string, optional (defaults to null if omitted)
- `calculationMethod`: string, max 1000 characters
- `measurementFrequency`: string (e.g., "daily", "weekly", "monthly")
- `ownerId`: string, valid user ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpi_456",
    "catalogId": "catalog_kpi_1",
    "name": "Monthly Recurring Revenue",
    "description": "Total predictable revenue per month from subscriptions",
    "unit": "USD",
    "direction": "up",
    "type": "quantitative",
    "category": "Financial",
    "aggregationType": "sum",
    "aggregationPeriod": "monthly",
    "valueType": "aggregate",
    "currentValue": 42000,
    "currentValueDate": "2025-01-15",
    "calculationMethod": "Sum of all subscription revenues",
    "measurementFrequency": "monthly",
    "dataSourceType": "manual",
    "ownerId": "user_123",
    "tenantId": "tenant_789",
    "isShared": false,
    "linkedGoalCount": 0,
    "createdAt": "2025-01-15T10:00:00Z",
    "updatedAt": "2025-01-15T10:00:00Z"
  }
}
```

**Response Fields:**
- `isShared`: boolean, always `false` for newly created KPIs (no goal linkages yet)
- `linkedGoalCount`: number, always `0` for newly created KPIs

**Status Codes:**
- `201` - KPI created successfully
- `400` - Validation error (missing required fields, invalid enum values)
- `404` - Catalog KPI not found (if catalogId provided)

---

### 14. GET /kpis/{id}

Get complete details for a single KPI instance.

**Path Parameters:**
- `id`: string, required - KPI ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpi_456",
    "catalogId": "catalog_kpi_1",
    "name": "Monthly Recurring Revenue",
    "description": "Total predictable revenue per month from subscriptions",
    "unit": "USD",
    "direction": "up",
    "type": "quantitative",
    "category": "Financial",
    "aggregationType": "sum",
    "aggregationPeriod": "monthly",
    "valueType": "aggregate",
    "currentValue": 42000,
    "currentValueDate": "2025-01-15",
    "calculationMethod": "Sum of all subscription revenues",
    "measurementFrequency": "monthly",
    "dataSourceType": "manual",
    "ownerId": "user_123",
    "tenantId": "tenant_789",
    "isShared": true,
    "linkedGoalCount": 3,
    "linkedGoals": [
      {
        "goalId": "goal_123",
        "goalName": "Increase Revenue",
        "isPrimary": true,
        "linkedAt": "2025-01-10T00:00:00Z"
      },
      {
        "goalId": "goal_124",
        "goalName": "Improve Profitability",
        "isPrimary": false,
        "linkedAt": "2025-01-12T00:00:00Z"
      }
    ],
    "createdAt": "2025-01-15T10:00:00Z",
    "updatedAt": "2025-01-15T10:00:00Z"
  }
}
```

**Response Constraints:**
- `isShared`: boolean, true if linked to multiple goals
- `linkedGoalCount`: number, count of goals this KPI is linked to
- `linkedGoals`: array of goal link details with `isPrimary` indicator

**Status Codes:**
- `200` - Success
- `404` - KPI not found

---

### 15. PUT /kpis/{id}

Update properties of an existing KPI instance. Changes affect all goals linked to this KPI.

**Path Parameters:**
- `id`: string, required - KPI ID

**Request Body (all fields optional for partial update):**
```json
{
  "name": "Updated KPI Name",
  "description": "Updated description",
  "unit": "USD",
  "direction": "up",
  "category": "Updated Category",
  "calculationMethod": "Updated calculation method",
  "measurementFrequency": "weekly",
  "ownerId": "user_456"
}
```

**Request Constraints:**
- All fields optional (partial update)
- **CANNOT update**: `catalogId`, `currentValue`, `currentValueDate`, `aggregationType`, `aggregationPeriod`, `valueType`
- If KPI is linked to catalog (`catalogId` not null):
  - Updating `name`, `description`, `unit`, `direction` creates instance-specific override
  - Original catalog values remain unchanged
- Field constraints same as POST /kpis

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpi_456",
    "name": "Updated KPI Name",
    "description": "Updated description",
    "unit": "USD",
    "direction": "up",
    "category": "Updated Category",
    "calculationMethod": "Updated calculation method",
    "measurementFrequency": "weekly",
    "ownerId": "user_456",
    "updatedAt": "2025-01-20T10:00:00Z"
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Validation error
- `404` - KPI not found

---

### 16. DELETE /kpis/{id}

Soft-delete a KPI instance. Only allowed if KPI is not linked to any goals.

**Path Parameters:**
- `id`: string, required - KPI ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpi_456",
    "deletedAt": "2025-01-20T10:00:00Z",
    "message": "KPI soft-deleted successfully"
  }
}
```

**Business Rules:**
- Returns `400` if KPI is linked to any goals
- Must unlink from all goals before deletion
- **Soft-delete behavior**:
  - KPI marked as `isDeleted: true`, `deletedAt` timestamp set
  - KPI record preserved in database (not physically deleted)
  - All associated data retained:
    - ✅ Milestones preserved (linked via KpiId)
    - ✅ Actuals preserved (linked via KpiId)
    - ✅ Plan adjustments preserved (linked via KpiId)
    - ✅ Replan rules preserved (linked via KpiId)
  - Soft-deleted KPIs excluded from list/search queries by default
  - Can be permanently deleted or restored by admin operations (future feature)
  - Historical data remains queryable for reporting/audit purposes

**Data Retention Rationale:**
- Milestones and actuals represent historical business data that should not be lost
- Enables audit trails and historical reporting
- Allows potential KPI restoration without data loss
- Maintains referential integrity for cross-goal KPI analysis

**Status Codes:**
- `200` - Success
- `400` - KPI is linked to goals (cannot delete)
- `404` - KPI not found

---

### 17. GET /kpis

List all KPIs for the tenant.

**Query Parameters:**
- `catalogOnly`: boolean, optional - Only show catalog-based KPIs
- `customOnly`: boolean, optional - Only show custom KPIs
- `includeShared`: boolean, optional, default true - Include KPIs shared across goals
- `category`: string, optional - Filter by category
- `page`: number, optional, default 1
- `pageSize`: number, optional, default 20, max 100

**Response:**
```json
{
  "success": true,
  "data": {
    "kpis": [
      {
        "id": "kpi_456",
        "name": "Monthly Recurring Revenue",
        "unit": "USD",
        "direction": "up",
        "type": "quantitative",
        "category": "Financial",
        "catalogId": "catalog_kpi_1",
        "isShared": true,
        "linkedGoalCount": 3,
        "currentValue": 42000,
        "currentValueDate": "2025-01-15",
        "ownerId": "user_123",
        "createdAt": "2025-01-15T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalCount": 45,
      "totalPages": 3
    }
  }
}
```

**Status Codes:**
- `200` - Success

---

### 18. GET /goals/{goalId}/kpis

List all KPIs linked to a specific goal with primary indicator.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Response:**
```json
{
  "success": true,
  "data": {
    "goalId": "goal_456",
    "goalName": "Increase Revenue",
    "kpis": [
      {
        "linkId": "goalkpi_101",
        "kpiId": "kpi_456",
        "name": "Monthly Recurring Revenue",
        "unit": "USD",
        "direction": "up",
        "type": "quantitative",
        "isPrimary": true,
        "thresholdPct": 80,
        "currentValue": 42000,
        "currentValueDate": "2025-01-15",
        "isShared": true,
        "sharedGoalCount": 3,
        "order": 1,
        "linkedAt": "2025-01-15T11:30:00Z"
      },
      {
        "linkId": "goalkpi_102",
        "kpiId": "kpi_457",
        "name": "Customer Retention Rate",
        "unit": "%",
        "direction": "up",
        "type": "quantitative",
        "isPrimary": false,
        "thresholdPct": 90,
        "currentValue": 85,
        "currentValueDate": "2025-01-14",
        "isShared": false,
        "sharedGoalCount": 1,
        "order": 2,
        "linkedAt": "2025-01-16T10:00:00Z"
      }
    ],
    "totalKpis": 2,
    "hasPrimary": true,
    "primaryKpi": {
      "kpiId": "kpi_456",
      "name": "Monthly Recurring Revenue"
    }
  }
}
```

**Response Constraints:**
- `isPrimary`: boolean, indicates if this KPI is the primary KPI for this goal
- `isShared`: boolean, true if KPI is linked to multiple goals
- `sharedGoalCount`: number, total count of goals this KPI is linked to
- `primaryKpi`: object with details of the primary KPI (null if no KPIs linked)

**Status Codes:**
- `200` - Success
- `404` - Goal not found

---

### 19. PUT /goals/{goalId}/kpis/{kpiId}:setPrimary

Set a specific KPI as the primary KPI for this goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `kpiId`: string, required - KPI ID to set as primary

**Request Body:**
```json
{}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "goalId": "goal_456",
    "previousPrimaryKpiId": "kpi_old_123",
    "newPrimaryKpiId": "kpi_789",
    "updatedAt": "2025-01-15T12:00:00Z"
  }
}
```

**Business Rules:**
- KPI must already be linked to the goal
- Previous primary KPI (if any) automatically demoted to `isPrimary: false`
- Only one KPI can be primary per goal

**Status Codes:**
- `200` - Success
- `400` - KPI is not linked to this goal
- `404` - Goal or KPI not found

---

## KPI Linking

### 20. POST /goals/{goalId}/kpis:link

Link a KPI to a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Request Body:**
```json
{
  "kpiId": "kpi_456",
  "thresholdPct": 80,
  "isPrimary": true
}
```

**Request Constraints:**
- `kpiId`: string, required, valid KPI ID (existing KPI instance)
- `thresholdPct`: number, optional, 0-100, percentage threshold for goal achievement
- `isPrimary`: boolean, optional
  - If `true`: This KPI becomes primary (any existing primary is demoted)
  - If `false` or omitted and goal has no KPIs: Auto-set to `true` (first KPI is primary by default)
  - If `false` or omitted and goal has existing KPIs: Defaults to `false`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "goalkpi_101",
    "goalId": "goal_456",
    "kpiId": "kpi_456",
    "isPrimary": true,
    "thresholdPct": 80,
    "order": 1,
    "linkedAt": "2025-01-15T11:30:00Z"
  }
}
```

**Business Rules:**
- First KPI linked to a goal automatically becomes primary
- If `isPrimary: true` is set, previous primary (if any) is automatically demoted
- KPI can be linked to multiple goals simultaneously

**Status Codes:**
- `201` - KPI linked successfully
- `400` - KPI already linked to this goal
- `404` - Goal or KPI not found

---

### 21. POST /goals/{goalId}/kpis:unlink

Unlink a KPI from a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Request Body:**
```json
{
  "kpiId": "kpi_456",
  "newPrimaryKpiId": "kpi_789"
}
```

**Request Constraints:**
- `kpiId`: string, required, KPI ID to unlink
- `newPrimaryKpiId`: string, optional
  - **REQUIRED** if `kpiId` is the current primary KPI AND goal has other KPIs linked
  - **FORBIDDEN** if `kpiId` is not the current primary KPI
  - **FORBIDDEN** if `kpiId` is the only KPI linked to goal

**Response:**
```json
{
  "success": true,
  "data": {
    "goalId": "goal_456",
    "unlinkedKpiId": "kpi_456",
    "newPrimaryKpiId": "kpi_789",
    "remainingKpiCount": 2
  }
}
```

**Business Rules:**
- Cannot unlink primary KPI without selecting new primary (if other KPIs exist)
- If removing last KPI from goal: Allowed, goal will have no primary KPI
- Unlinking KPI does not delete the KPI instance (still exists for other goals)

**Status Codes:**
- `200` - Success
- `400` - Attempting to unlink primary KPI without providing `newPrimaryKpiId` when other KPIs exist
- `400` - Provided `newPrimaryKpiId` is not linked to this goal
- `404` - KPI not linked to this goal

---

### 22. POST /goals/{goalId}/kpis/{kpiId}:setThreshold

Set threshold percentage for a KPI linked to a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `kpiId`: string, required - KPI ID

**Request Body:**
```json
{
  "thresholdPct": 85
}
```

**Request Constraints:**
- `thresholdPct`: number, required, 0-100

**Response:**
```json
{
  "success": true
}
```

---

### 23. GET /goals/{goalId}/kpis/{kpiId}:link

Get KPI linkage information including threshold.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `kpiId`: string, required - KPI ID

**Response:**
```json
{
  "success": true,
  "data": {
    "thresholdPct": 80
  }
}
```

**Response Constraints:**
- `thresholdPct`: number | null

---

### 24. GET /goals/{goalId}/available-kpis

Get available KPIs for a goal (catalog KPIs and tenant custom KPIs).

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Response:**
```json
{
  "success": true,
  "data": {
    "catalogKpis": [
      {
        "id": "catalog_kpi_1",
        "name": "Monthly Recurring Revenue",
        "description": "Total predictable revenue per month from subscriptions",
        "unit": "USD",
        "direction": "up",
        "category": "Financial",
        "source": "Catalog",
        "isShared": false,
        "usageInfo": {
          "goalCount": 0,
          "isUsedByThisGoal": false
        }
      }
    ],
    "tenantCustomKpis": [
      {
        "id": "custom_kpi_1",
        "name": "Customer Satisfaction Score",
        "description": "Average satisfaction rating from customer surveys",
        "unit": "Score (1-10)",
        "direction": "up",
        "source": "Created by Marketing Goal",
        "isShared": true,
        "usageInfo": {
          "goalCount": 2,
          "isUsedByThisGoal": false
        }
      }
    ]
  }
}
```

**Response Constraints:**
- `catalogKpis`: array of KPICatalogItem
- `tenantCustomKpis`: array of KPI
- `usageInfo.goalCount`: number, count of goals using this KPI
- `usageInfo.isUsedByThisGoal`: boolean, whether this KPI is already linked to the goal

---

## KPI Planning

### 25. GET /kpi-planning/kpis/{id}/milestones

Get all milestones for a KPI.

**Path Parameters:**
- `id`: string, required - KPI ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "milestone_123",
      "kpiId": "kpi_456",
      "milestoneDate": "2025-03-31",
      "targetValue": 50000,
      "label": "Q1 Target",
      "confidenceLevel": 4,
      "rationale": "Based on historical growth trends",
      "createdBy": "user_123",
      "createdAt": "2025-01-01T00:00:00Z",
      "updatedAt": "2025-01-15T10:00:00Z"
    }
  ]
}
```

**Response Constraints:**
- Returns array of KPIMilestone
- `milestoneDate`: ISO date string (YYYY-MM-DD)
- `targetValue`: number, required
- `confidenceLevel`: number, optional, 1-5

---

### 26. PUT /kpi-planning/kpis/{id}/milestones

Set milestones for a KPI (replace or merge).

**Path Parameters:**
- `id`: string, required - KPI ID

**Request Body:**
```json
{
  "milestones": [
    {
      "milestoneDate": "2025-03-31",
      "targetValue": 50000,
      "label": "Q1 Target",
      "confidenceLevel": 0.85,
      "rationale": "Based on historical growth trends"
    },
    {
      "milestoneDate": "2025-06-30",
      "targetValue": 75000,
      "label": "Q2 Target",
      "confidenceLevel": 0.80,
      "rationale": "Accelerated growth expected"
    }
  ],
  "replaceAll": false
}
```

**Request Constraints:**
- `milestones`: array, required, min 1 item
  - `milestoneDate`: string, required, ISO date (YYYY-MM-DD)
  - `targetValue`: number, required
  - `label`: string, optional, max 200 characters
  - `confidenceLevel`: number, optional, 1-5
  - `rationale`: string, optional, max 1000 characters
- `replaceAll`: boolean, optional, defaults to `false`
  - `true`: Replace all existing milestones
  - `false`: Merge with existing milestones (update matching dates, add new ones)

**Response:**
```json
{
  "success": true,
  "data": {
    "milestones": [
      {
        "id": "milestone_123",
        "kpiId": "kpi_456",
        "milestoneDate": "2025-03-31",
        "targetValue": 50000,
        "label": "Q1 Target",
        "confidenceLevel": 4,
        "rationale": "Based on historical growth trends",
        "createdBy": "user_123",
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-15T10:00:00Z"
      }
    ],
    "interpolatedPeriods": {
      "monthly": [
        {
          "periodType": "monthly",
          "periodStart": "2025-01-01",
          "periodEnd": "2025-01-31",
          "startValue": 45000,
          "endValue": 46667,
          "delta": 1667,
          "growthRate": 3.7,
          "interpolatedFromMilestones": ["milestone_123"]
        }
      ],
      "quarterly": [],
      "yearly": []
    },
    "impactAnalysis": {
      "changedMilestones": 1,
      "affectedPeriods": 3,
      "crossGoalAlert": null
    }
  }
}
```

---

### 27. GET /kpi-planning/kpis/{id}/plan

Get complete KPI planning data with trajectory.

**Path Parameters:**
- `id`: string, required - KPI ID

**Query Parameters:**
- `granularity`: string, optional, one of: `"daily"`, `"weekly"`, `"monthly"`, `"quarterly"`, `"yearly"` (default: `"monthly"`)

**Response:**
```json
{
  "success": true,
  "data": {
    "kpi": {
      "id": "kpi_123",
      "name": "Monthly Recurring Revenue",
      "unit": "USD",
      "direction": "up",
      "currentValue": 42000,
      "currentDate": "2025-01-15",
      "interpolationMethod": "linear"
    },
    "milestones": [
      {
        "id": "milestone_456",
        "milestoneDate": "2025-03-31",
        "targetValue": 50000,
        "label": "Q1 Target"
      }
    ],
    "periods": [
      {
        "periodType": "monthly",
        "periodStart": "2025-01-01",
        "periodEnd": "2025-01-31",
        "startValue": 45000,
        "endValue": 46667,
        "delta": 1667,
        "growthRate": 3.7,
        "interpolatedFromMilestones": ["milestone_456"]
      }
    ],
    "trajectory": {
      "method": "linear",
      "totalChange": 5000,
      "averageMonthlyGrowth": 3.7
    }
  }
}
```

---

### 28. GET /kpi-planning/goals/{goalId}/kpi-planning

Get complete KPI planning summary for a goal (all KPIs associated with the goal).

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Response:**
```json
{
  "success": true,
  "data": {
    "goal": {
      "id": "goal_123",
      "name": "Increase Revenue",
      "intent": "We want to increase revenue by 50%..."
    },
    "kpis": [
      {
        "kpiId": "kpi_456",
        "name": "Monthly Recurring Revenue",
        "unit": "USD",
        "isPrimary": true,
        "currentValue": 42000,
        "currentDate": "2025-01-15",
        "milestoneCount": 4,
        "nextMilestone": {
          "id": "milestone_123",
          "milestoneDate": "2025-03-31",
          "targetValue": 50000,
          "label": "Q1 Target"
        },
        "latestActual": {
          "id": "actual_789",
          "measurementDate": "2025-01-15",
          "actualValue": 42000,
          "expectedValue": 41500,
          "variance": 500,
          "variancePercentage": 1.2
        },
        "isShared": true,
        "sharedGoals": [
          {
            "id": "goal_123",
            "name": "Increase Revenue"
          },
          {
            "id": "goal_124",
            "name": "Improve Customer Retention"
          }
        ]
      }
    ]
  }
}
```

---

### 30. POST /kpi-planning/kpis/{id}/actuals

Record a new actual measurement for a KPI.

**Path Parameters:**
- `id`: string, required - KPI ID

**Request Body:**
```json
{
  "measurementDate": "2025-01-31",
  "actualValue": 45000,
  "source": "manual",
  "sourceId": null,
  "adjustmentStrategy": "auto"
}
```

**Request Constraints:**
- `measurementDate`: string, required, ISO date (YYYY-MM-DD)
- `actualValue`: number, required
- `source`: KPIDataSource enum, required
- `sourceId`: string, optional, ID of source (action ID, integration ID, etc.)
- `adjustmentStrategy`: string, optional, one of: `"auto"`, `"manual"`, `"none"` (default: `"none"`)

**Response:**
```json
{
  "success": true,
  "data": {
    "actual": {
      "id": "actual_123",
      "kpiId": "kpi_456",
      "measurementDate": "2025-01-31",
      "actualValue": 45000,
      "expectedValue": 44000,
      "variance": 1000,
      "variancePercentage": 2.27,
      "dataSource": "manual",
      "sourceReferenceId": null,
      "isManualOverride": false,
      "overrideComment": null,
      "triggersReplan": false,
      "replanThresholdExceeded": false,
      "recordedBy": "user_123",
      "recordedAt": "2025-02-01T10:00:00Z"
    },
    "adjustment": null,
    "suggestions": []
  }
}
```

**Response Constraints:**
- `expectedValue`: calculated from milestones via interpolation
- `variance`: `actualValue - expectedValue`
- `variancePercentage`: `(variance / expectedValue) * 100`
- `triggersReplan`: boolean, true if variance exceeds replan threshold
- `adjustment`: KPIPlanAdjustment | null, present if auto-adjustment was applied
- `suggestions`: array of KPIAdjustmentSuggestion, present if replan is recommended

---

### 29. GET /kpi-planning/kpis/{id}/actuals

Get historical actual measurements for a KPI.

**Path Parameters:**
- `id`: string, required - KPI ID

**Query Parameters:**
- `startDate`: string, optional, ISO date (YYYY-MM-DD) - Filter actuals from this date onwards
- `endDate`: string, optional, ISO date (YYYY-MM-DD) - Filter actuals up to this date

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "actual_123",
      "kpiId": "kpi_456",
      "tenantId": "tenant_789",
      "measurementDate": "2025-01-31",
      "actualValue": 45000,
      "expectedValue": 44000,
      "variance": 1000,
      "variancePercentage": 2.27,
      "dataSource": "manual",
      "sourceReferenceId": null,
      "isManualOverride": false,
      "overrideComment": null,
      "triggersReplan": false,
      "replanThresholdExceeded": false,
      "autoAdjustmentApplied": false,
      "recordedBy": "user_123",
      "recordedAt": "2025-02-01T10:00:00Z",
      "createdAt": "2025-02-01T10:00:00Z",
      "updatedAt": "2025-02-01T10:00:00Z"
    }
  ]
}
```

**Response Constraints:**
- Returns array of KPIActual measurements
- `measurementDate`: ISO date string (YYYY-MM-DD)
- `actualValue`: number, the measured value
- `expectedValue`: number, calculated from milestones via interpolation
- `variance`: number, `actualValue - expectedValue`
- `variancePercentage`: number, `(variance / expectedValue) * 100`
- `dataSource`: string, source of the measurement (e.g., "manual", "integration")
- `triggersReplan`: boolean, whether variance exceeds replan threshold
- Ordered by `measurementDate` descending (newest first)

---

### 31. POST /kpi-planning/kpis/{id}/adjust

Apply a KPI plan adjustment (replanning based on actuals).

**Path Parameters:**
- `id`: string, required - KPI ID

**Request Body:**
```json
{
  "strategy": "maintain_final_goal",
  "basedOnActualId": "actual_123",
  "customMilestones": [],
  "rationale": "Adjusting plan to reflect slower-than-expected Q1 performance"
}
```

**Request Constraints:**
- `strategy`: AdjustmentStrategy enum, required
- `basedOnActualId`: string, optional, ID of actual that this adjustment is based on
- `customMilestones`: array, optional, required if `strategy` is `"custom"`
- `rationale`: string, required, max 1000 characters

**Response:**
```json
{
  "success": true,
  "data": {
    "adjustment": {
      "id": "adjustment_789",
      "kpiId": "kpi_456",
      "adjustmentDate": "2025-02-01T15:00:00Z",
      "effectiveDate": "2025-02-01",
      "adjustmentType": "milestone_updated",
      "triggerReason": "actual_variance",
      "basedOnActualId": "actual_123",
      "triggerVariancePercentage": 5.2,
      "previousMilestones": [],
      "newMilestones": [],
      "affectedMilestoneIds": ["milestone_123"],
      "affectedGoalIds": ["goal_123", "goal_456"],
      "recalculatedPeriodCount": 12,
      "adjustmentStrategy": "maintain_final_goal",
      "adjustmentNotes": null,
      "createdBy": "user_123"
    },
    "updatedMilestones": [
      {
        "id": "milestone_123",
        "milestoneDate": "2025-03-31",
        "targetValue": 48000
      }
    ],
    "recalculatedPeriods": []
  }
}
```

---

### 32. GET /kpi-planning/kpis/{kpiId}/cross-goal-impact

Shows which goals use this KPI and their impact level.

**Path Parameters:**
- `kpiId`: string, required - KPI ID

**Response:**
```json
{
  "success": true,
  "data": {
    "kpiId": "kpi_123",
    "kpiName": "Monthly Recurring Revenue",
    "affectedGoals": [
      {
        "goalId": "goal_456",
        "goalTitle": "Increase Revenue by 50%",
        "impactLevel": "high",
        "threshold": 80,
        "currentAlignment": 85
      }
    ],
    "totalGoalsAffected": 1
  }
}
```

**Response Constraints:**
- `impactLevel`: string, one of: `"high"`, `"medium"`, `"low"`
- `threshold`: number, 0-100, threshold percentage for goal
- `currentAlignment`: number, 0-100, current progress percentage

---

### 26. GET /kpi-planning/kpis/{id}/replan-rule

Get auto-replan configuration for a KPI.

**Path Parameters:**
- `id`: string, required - KPI ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "rule_123",
    "kpiId": "kpi_456",
    "varianceThresholdPercentage": 10.0,
    "consecutiveMissesRequired": 2,
    "autoAdjustEnabled": true,
    "adjustmentStrategy": "maintain_final_goal",
    "requireUserApproval": true,
    "notifyOnTrigger": true,
    "notificationRecipients": ["user_123", "user_456"]
  }
}
```

**Response Constraints:**
- Returns `404` if no replan rule exists for the KPI
- `varianceThresholdPercentage`: number, 0-100
- `consecutiveMissesRequired`: number, min 1
- `adjustmentStrategy`: AdjustmentStrategy enum

---

### 27. PUT /kpi-planning/kpis/{id}/replan-rule

Create or update auto-replan configuration.

**Path Parameters:**
- `id`: string, required - KPI ID

**Request Body:**
```json
{
  "varianceThresholdPercentage": 10.0,
  "consecutiveMissesRequired": 2,
  "autoAdjustEnabled": true,
  "adjustmentStrategy": "maintain_final_goal",
  "requireUserApproval": true,
  "notifyOnTrigger": true,
  "notificationRecipients": ["user_123", "user_456"]
}
```

**Request Constraints:**
- All fields are optional (partial update)
- `varianceThresholdPercentage`: number, 0-100
- `consecutiveMissesRequired`: number, min 1
- `adjustmentStrategy`: AdjustmentStrategy enum
- `notificationRecipients`: array of user IDs

**Response:**
Same structure as GET response

---

## Actions Management

### 28. GET /operations/actions

List actions with filtering.

**Query Parameters:**
- `startDate`: string, optional, ISO date string
- `endDate`: string, optional, ISO date string
- `assignedPersonId`: string, optional, user ID
- `goalIds`: string, optional, comma-separated list of goal IDs
- `strategyIds`: string, optional, comma-separated list of strategy IDs
- `issueIds`: string, optional, comma-separated list of issue IDs
- `status`: string, optional, can be repeated, one of: `"not_started"`, `"in_progress"`, `"completed"`, `"blocked"`, `"cancelled"`
- `priority`: string, optional, can be repeated, one of: `"low"`, `"medium"`, `"high"`, `"critical"`

**Response:**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "id": "action_123",
        "title": "Implement customer loyalty program",
        "description": "Set up tiered rewards system",
        "dateEntered": "2025-01-15T10:00:00Z",
        "startDate": "2025-01-20T00:00:00Z",
        "dueDate": "2025-02-15T23:59:59Z",
        "priority": "high",
        "assignedPersonId": "user_456",
        "progress": 45,
        "status": "in_progress",
        "connections": {
          "goalIds": ["goal_123"],
          "strategyIds": ["strategy_789"],
          "issueIds": []
        },
        "createdAt": "2025-01-15T10:00:00Z",
        "updatedAt": "2025-01-20T14:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 1,
      "hasMore": false
    }
  }
}
```

**Response Structure:**
- Nested structure: `response.data.data?.data || response.data.data || []`
- `progress`: number, 0-100
- `connections`: object with arrays of related entity IDs

---

### 29. POST /operations/actions

Create a new action.

**Request Body:**
```json
{
  "title": "Implement customer loyalty program",
  "description": "Set up tiered rewards system with points and tiers",
  "startDate": "2025-01-20T00:00:00Z",
  "dueDate": "2025-02-15T23:59:59Z",
  "priority": "high",
  "assignedPersonId": "user_456",
  "connections": {
    "goalIds": ["goal_123"],
    "strategyIds": ["strategy_789"],
    "issueIds": []
  }
}
```

**Request Constraints:**
- `title`: string, required, max 200 characters
- `description`: string, optional, max 5000 characters
- `startDate`: string, required, ISO 8601 date-time
- `dueDate`: string, required, ISO 8601 date-time, must be after startDate
- `priority`: ActionPriority enum, required
- `assignedPersonId`: string, optional, valid user ID
- `connections`: object, optional
  - `goalIds`: array of strings, optional
  - `strategyIds`: array of strings, optional
  - `issueIds`: array of strings, optional

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "action_123",
    "title": "Implement customer loyalty program",
    "description": "Set up tiered rewards system with points and tiers",
    "dateEntered": "2025-01-15T10:00:00Z",
    "startDate": "2025-01-20T00:00:00Z",
    "dueDate": "2025-02-15T23:59:59Z",
    "priority": "high",
    "assignedPersonId": "user_456",
    "progress": 0,
    "status": "not_started",
    "connections": {
      "goalIds": ["goal_123"],
      "strategyIds": ["strategy_789"],
      "issueIds": []
    },
    "createdAt": "2025-01-15T10:00:00Z",
    "updatedAt": "2025-01-15T10:00:00Z"
  }
}
```

**Response Constraints:**
- `dateEntered`: automatically set to current timestamp
- `progress`: defaults to 0
- `status`: defaults to `"not_started"`

---

### 30. PUT /operations/actions/{id}

Update an action.

**Path Parameters:**
- `id`: string, required - Action ID

**Request Body:**
```json
{
  "title": "Updated action title",
  "description": "Updated description",
  "priority": "critical",
  "assignedPersonId": "user_789",
  "progress": 75,
  "status": "in_progress",
  "startDate": "2025-01-25T00:00:00Z",
  "dueDate": "2025-02-20T23:59:59Z"
}
```

**Request Constraints:**
- All fields are optional (partial update)
- `status`: ActionStatus enum, required if updating other fields (backend requirement)
- `priority`: ActionPriority enum, required if updating other fields (backend requirement)
- `progress`: number, 0-100
- `connections`: handled via separate endpoints (PUT /operations/actions/{id}/goals, PUT /operations/actions/{id}/strategies)

**Response:**
Same structure as POST response

---

### 31. DELETE /operations/actions/{id}

Delete an action.

**Path Parameters:**
- `id`: string, required - Action ID

**Response:**
```json
{
  "success": true
}
```

**Note:** Also removes all relationships automatically

---

### 31. PUT /operations/actions/{id}/goals

Link action to goals (replaces existing goal links).

**Path Parameters:**
- `id`: string, required - Action ID

**Request Body:**
```json
{
  "goalIds": ["goal_1", "goal_2"]
}
```

**Request Constraints:**
- `goalIds`: array of strings, required, valid goal IDs

**Response:**
```json
{
  "success": true
}
```

---

### 32. PUT /operations/actions/{id}/strategies

Link action to strategies (replaces existing strategy links).

**Path Parameters:**
- `id`: string, required - Action ID

**Request Body:**
```json
{
  "strategyIds": ["strategy_1", "strategy_2"]
}
```

**Request Constraints:**
- `strategyIds`: array of strings, required, valid strategy IDs

**Response:**
```json
{
  "success": true
}
```

---

### 33. DELETE /operations/actions/{id}/relationships

Remove all relationships for an action.

**Path Parameters:**
- `id`: string, required - Action ID

**Response:**
```json
{
  "success": true
}
```

---

## Issues Management

### 34. GET /issues

List issues with filtering.

**Query Parameters:**
- `startDate`: string, optional, ISO date string
- `endDate`: string, optional, ISO date string
- `reportedBy`: string, optional, user ID
- `businessImpact`: string, optional, comma-separated, one of: `"low"`, `"medium"`, `"high"`, `"critical"`
- `priority`: string, optional, comma-separated, one of: `"low"`, `"medium"`, `"high"`, `"critical"`
- `status`: string, optional, comma-separated, status config IDs
- `limit`: number, optional, pagination limit (default: 20, max: 200)
- `offset`: number, optional, pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "data": {
    "data": [
      {
        "id": "issue_123",
        "title": "Server downtime affecting customers",
        "description": "Production server experienced 2-hour outage",
        "typeConfigId": "type_bug",
        "statusConfigId": "status_open",
        "reporterId": "user_456",
        "reporterName": "John Doe",
        "impact": "high",
        "priority": "critical",
        "displayOrder": 1,
        "connections": {
          "goalIds": [],
          "strategyIds": [],
          "actionIds": []
        },
        "dateReported": "2025-01-15T10:00:00Z",
        "resolvedAt": null,
        "createdAt": "2025-01-15T10:00:00Z",
        "updatedAt": "2025-01-15T10:00:00Z",
        "createdBy": "user_456",
        "updatedBy": "user_456"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 1,
      "hasMore": false
    }
  }
}
```

**Response Structure:**
- Nested structure: `response.data.data?.data || response.data.data || []`
- `typeConfigId`: string, references issue type configuration
- `statusConfigId`: string, references issue status configuration

---

### 35. POST /issues

Create a new issue.

**Request Body:**
```json
{
  "title": "Server downtime affecting customers",
  "description": "Production server experienced 2-hour outage",
  "typeConfigId": "type_bug",
  "reportedBy": "user_456",
  "businessImpact": "high",
  "priority": "critical",
  "statusId": "status_open",
  "assignedPersonId": "user_789"
}
```

**Request Constraints:**
- `title`: string, required, max 200 characters
- `description`: string, optional, max 5000 characters
- `typeConfigId`: string, required, valid issue type ID
- `reportedBy`: string, required, valid user ID (frontend sends as `reportedBy`, backend expects `ReportedBy` with capital B)
- `businessImpact`: IssueImpact enum, required
- `priority`: IssuePriority enum, required
- `statusId`: string, optional, valid issue status ID (defaults to first status in "open" category)
- `assignedPersonId`: string, optional, valid user ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "issue_123",
    "title": "Server downtime affecting customers",
    "description": "Production server experienced 2-hour outage",
    "typeConfigId": "type_bug",
    "statusConfigId": "status_open",
    "reporterId": "user_456",
    "reporterName": "John Doe",
    "impact": "high",
    "priority": "critical",
    "displayOrder": 1,
    "connections": {
      "goalIds": [],
      "strategyIds": [],
      "actionIds": []
    },
    "dateReported": "2025-01-15T10:00:00Z",
    "resolvedAt": null,
    "createdAt": "2025-01-15T10:00:00Z",
    "updatedAt": "2025-01-15T10:00:00Z",
    "createdBy": "user_456",
    "updatedBy": "user_456"
  }
}
```

**Data Transformation:**
- Frontend sends: `reportedBy` (camelCase)
- Backend expects: `ReportedBy` (PascalCase)
- Transformation handled in `operations-traction-service.ts`

---

### 36. PUT /issues/{id}

Update an issue.

**Path Parameters:**
- `id`: string, required - Issue ID

**Request Body:**
```json
{
  "title": "Updated issue title",
  "description": "Updated description",
  "businessImpact": "critical",
  "priority": "high",
  "statusId": "status_in_progress",
  "assignedPersonId": "user_999"
}
```

**Request Constraints:**
- All fields are optional (partial update)
- `statusId`: string, valid issue status ID
- Note: `reportedBy` transformation applies (frontend: `reportedBy`, backend: `ReportedBy`)

**Response:**
Same structure as POST response

---

### 37. DELETE /issues/{id}

Delete an issue.

**Path Parameters:**
- `id`: string, required - Issue ID

**Response:**
```json
{
  "success": true
}
```

---

## Issue Types Management

### 38. GET /operations/issue-types

List issue types.

**Query Parameters:**
- `includeInactive`: boolean, optional, include inactive types (default: `false`)
- `includeSystem`: boolean, optional, include system types (default: `true`)

**Response:**
```json
{
  "success": true,
  "data": {
    "types": [
      {
        "id": "type_123",
        "name": "Bug",
        "description": "Software defects or errors",
        "color": "#ef4444",
        "icon": "🐛",
        "order": 1,
        "isActive": true,
        "isSystemType": true,
        "isDefault": true,
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": "2025-01-01T00:00:00Z"
      },
      {
        "id": "type_456",
        "name": "Feature Request",
        "description": "New feature or enhancement",
        "color": "#3b82f6",
        "icon": "✨",
        "order": 2,
        "isActive": true,
        "isSystemType": false,
        "isDefault": false,
        "createdAt": "2025-01-15T10:00:00Z",
        "updatedAt": null
      }
    ],
    "total": 2
  }
}
```

**Response Structure:**
- Nested structure: `response.data.data?.types || response.data.data?.data || []`
- `color`: string, hex color code
- `icon`: string, emoji or icon identifier
- `isSystemType`: boolean, true for system-defined types
- `isDefault`: boolean, true for default type

---

### 39. POST /operations/issue-types

Create a new issue type.

**Request Body:**
```json
{
  "name": "Feature Request",
  "description": "New feature or enhancement",
  "color": "#3b82f6",
  "icon": "✨",
  "order": 2,
  "isDefault": false
}
```

**Request Constraints:**
- `name`: string, required, max 100 characters, unique
- `description`: string, optional, max 500 characters
- `color`: string, required, valid hex color code (e.g., `"#3b82f6"`)
- `icon`: string, optional, emoji or icon identifier
- `order`: number, optional, positive integer
- `isDefault`: boolean, optional, defaults to `false`

**Response:**
Same structure as GET response item

---

### 40. PUT /operations/issue-types/{id}

Update an issue type.

**Path Parameters:**
- `id`: string, required - Issue type ID

**Request Body:**
```json
{
  "name": "Updated Type Name",
  "description": "Updated description",
  "color": "#ff0000",
  "icon": "🔴",
  "order": 3
}
```

**Request Constraints:**
- All fields are optional (partial update)
- System types may have restricted fields

**Response:**
Same structure as GET response item

---

### 41. DELETE /operations/issue-types/{id}

Delete an issue type.

**Path Parameters:**
- `id`: string, required - Issue type ID

**Response:**
```json
{
  "success": true
}
```

**Note:** System types cannot be deleted, only deactivated

---

### 42. POST /operations/issue-types/{id}:activate

Reactivate an inactive issue type.

**Path Parameters:**
- `id`: string, required - Issue type ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "type_456",
    "isActive": true,
    // ... other type fields
  }
}
```

---

## Issue Statuses Management

### 43. GET /operations/issue-statuses

List issue statuses.

**Query Parameters:**
- `category`: string, optional, one of: `"open"`, `"active"`, `"inactive"`, `"closed"`
- `includeInactive`: boolean, optional, include inactive statuses (default: `false`)
- `includeSystem`: boolean, optional, include system statuses (default: `true`)

**Response:**
```json
{
  "success": true,
  "data": {
    "statuses": [
      {
        "id": "status_123",
        "name": "Open",
        "description": "Issue is reported and awaiting triage",
        "category": "open",
        "color": "#3b82f6",
        "icon": "📋",
        "order": 1,
        "isActive": true,
        "isSystemStatus": true,
        "createdAt": "2025-01-01T00:00:00Z",
        "updatedAt": null
      },
      {
        "id": "status_456",
        "name": "In Progress",
        "description": "Issue is being actively worked on",
        "category": "active",
        "color": "#f59e0b",
        "icon": "⚙️",
        "order": 2,
        "isActive": true,
        "isSystemStatus": false,
        "createdAt": "2025-01-15T10:00:00Z",
        "updatedAt": null
      }
    ],
    "total": 2
  }
}
```

**Response Structure:**
- Nested structure: `response.data.data?.statuses || response.data.data?.data || []`
- `category`: IssueStatusCategory enum
- `isSystemStatus`: boolean, true for system-defined statuses

---

### 44. POST /operations/issue-statuses

Create a new issue status.

**Request Body:**
```json
{
  "name": "Pending Approval",
  "description": "Awaiting management approval",
  "category": "active",
  "color": "#F39C12",
  "icon": "⏰",
  "order": 4
}
```

**Request Constraints:**
- `name`: string, required, max 100 characters, unique within category
- `description`: string, optional, max 500 characters
- `category`: IssueStatusCategory enum, required
- `color`: string, required, valid hex color code
- `icon`: string, optional, emoji or icon identifier
- `order`: number, optional, positive integer

**Response:**
Same structure as GET response item

---

### 45. PUT /operations/issue-statuses/{id}

Update an issue status.

**Path Parameters:**
- `id`: string, required - Issue status ID

**Request Body:**
```json
{
  "name": "Updated Status Name",
  "description": "Updated description",
  "color": "#ff0000",
  "icon": "🔴",
  "order": 5
}
```

**Request Constraints:**
- All fields are optional (partial update)
- `category`: cannot be changed after creation
- System statuses may have restricted fields

**Response:**
Same structure as GET response item

---

### 46. DELETE /operations/issue-statuses/{id}

Delete an issue status.

**Path Parameters:**
- `id`: string, required - Issue status ID

**Response:**
```json
{
  "success": true
}
```

**Note:** System statuses cannot be deleted, only deactivated

---

### 47. POST /operations/issue-statuses/{id}:activate

Reactivate an inactive issue status.

**Path Parameters:**
- `id`: string, required - Issue status ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "status_456",
    "isActive": true,
    // ... other status fields
  }
}
```

---

### 48. PUT /operations/issue-statuses:reorder

Reorder issue statuses within a category.

**Request Body:**
```json
{
  "category": "active",
  "statusIds": ["status_1", "status_2", "status_3"]
}
```

**Request Constraints:**
- `category`: IssueStatusCategory enum, required
- `statusIds`: array of strings, required, all status IDs in desired order, must all belong to the specified category

**Response:**
```json
{
  "success": true
}
```

---

## Issue Lifecycle

**Note:** These endpoints use `fetch()` directly with `baseUrl` from environment, not the traction axios instance.

### 49. POST /issues/{id}/root-cause

Create root cause analysis for an issue.

**Path Parameters:**
- `id`: string, required - Issue ID

**Request Body:**
```json
{
  "issueId": "issue_123",
  "method": "swot",
  "analysis": {
    "strengths": ["Strong team"],
    "weaknesses": ["Lack of monitoring"],
    "opportunities": ["Improve infrastructure"],
    "threats": ["Customer churn"]
  }
}
```

**Request Constraints:**
- `issueId`: string, required, must match path parameter
- `method`: string, required, one of: `"swot"`, `"five_whys"`
- `analysis`: object, required, structure depends on method

**Response:**
```json
{
  "success": true
}
```

---

### 50. POST /issues/{id}/convert-to-actions

Convert an issue to actions.

**Path Parameters:**
- `id`: string, required - Issue ID

**Request Body:**
```json
{
  "actions": [
    {
      "title": "Fix server monitoring",
      "description": "Implement comprehensive monitoring system",
      "assignedPersonId": "user_456",
      "priority": "high"
    },
    {
      "title": "Update incident response plan",
      "description": "Document and improve response procedures",
      "assignedPersonId": "user_789",
      "priority": "medium"
    }
  ],
  "newStatusId": "status_in_progress"
}
```

**Request Constraints:**
- `actions`: array, required, min 1 item
  - `title`: string, required, max 200 characters
  - `description`: string, optional, max 5000 characters
  - `assignedPersonId`: string, optional, valid user ID
  - `priority`: ActionPriority enum, required
- `newStatusId`: string, optional, valid issue status ID

**Response:**
```json
{
  "success": true,
  "data": {
    "actionIds": ["action_1", "action_2"]
  }
}
```

**Response Constraints:**
- `actionIds`: array of strings, IDs of created actions
- Actions are automatically linked to the issue
- Issue status is updated to `newStatusId` if provided
- Actions inherit the issue's goal and strategy connections automatically

**Implementation:**
- Used by `IssueToActionConverter.tsx` and `useIssueToActionConversion.ts`
- Ensures backend properly connects actions to the issue atomically

---

### 51. GET /issues/{id}/closure-eligibility

Check if an issue can be closed.

**Path Parameters:**
- `id`: string, required - Issue ID

**Response:**
```json
{
  "success": true,
  "data": {
    "canClose": true,
    "completedActions": 3,
    "totalActions": 3
  }
}
```

**Response Constraints:**
- `canClose`: boolean, true if all related actions are completed
- `completedActions`: number, count of completed actions
- `totalActions`: number, total count of related actions

---

### 52. POST /issues/{id}/close

Close an issue.

**Path Parameters:**
- `id`: string, required - Issue ID

**Request Body:**
None (empty body)

**Response:**
```json
{
  "success": true
}
```

**Note:** Issue must be eligible for closure (all actions completed)

---

## Operations Integration

### 53. POST /operations/kpi-updates

Sync KPI update from an action.

**Request Body:**
```json
{
  "actionId": "action_123",
  "kpiId": "kpi_456",
  "horizonId": "horizon_789",
  "newValue": 1000,
  "updateDate": "2025-02-01",
  "notes": "Updated based on action completion"
}
```

**Request Constraints:**
- `actionId`: string, required, valid action ID
- `kpiId`: string, required, valid KPI ID
- `kpiId`: string, required, valid KPI ID
- `horizonId`: string, required, valid time horizon ID
- `newValue`: number, required
- `updateDate`: string, required, ISO date (YYYY-MM-DD)
- `notes`: string, optional, max 1000 characters

**Response:**
```json
{
  "success": true
}
```

---

### 54. POST /operations/actions/goals

Get goals for specific actions.

**Request Body:**
```json
{
  "actionIds": ["action_1", "action_2"]
}
```

**Request Constraints:**
- `actionIds`: array of strings, required, min 1 item, valid action IDs

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "goal_123",
      "title": "Increase Revenue",
      "intent": "We want to increase revenue...",
      "status": "active",
      // ... other goal fields
    }
  ]
}
```

**Response:** Array of Goal objects

---

### 55. POST /operations/actions/strategies

Get strategies for specific actions.

**Request Body:**
```json
{
  "actionIds": ["action_1", "action_2"]
}
```

**Request Constraints:**
- `actionIds`: array of strings, required, min 1 item, valid action IDs

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "strategy_789",
      "goalId": "goal_123",
      "description": "Improve customer retention...",
      "status": "validated",
      // ... other strategy fields
    }
  ]
}
```

**Response:** Array of Strategy objects

---

### 56. POST /operations/goals/kpis

Get KPIs for specific goals.

**Request Body:**
```json
{
  "goalIds": ["goal_1", "goal_2"]
}
```

**Request Constraints:**
- `goalIds`: array of strings, required, min 1 item, valid goal IDs

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "kpi_456",
      "kpiId": "kpi_catalog_1",
      "name": "Monthly Recurring Revenue",
      "unit": "USD",
      "direction": "up",
      // ... other KPI fields
    }
  ]
}
```

**Response:** Array of KPI objects

---

## Activity

### 57. GET /goals/{goalId}/activity

Get activity feed for a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "activity_123",
      "goalId": "goal_456",
      "type": "note",
      "content": "Made progress on customer retention",
      "createdBy": "user_123",
      "createdAt": "2025-01-15T10:00:00Z"
    }
  ]
}
```

---

### 58. POST /goals/{goalId}/activity

Add an activity entry to a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Request Body:**
```json
{
  "type": "note",
  "content": "Made significant progress on customer retention program"
}
```

**Request Constraints:**
- `type`: string, required, activity type
- `content`: string, required, max 5000 characters

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "activity_123",
    "goalId": "goal_456",
    "type": "note",
    "content": "Made significant progress on customer retention program",
    "createdBy": "user_123",
    "createdAt": "2025-01-15T10:00:00Z"
  }
}
```

---

## Alignment

### 59. POST /alignment/check

Calculate goal alignment with business context.

**Request Body:**
```json
{
  "goalId": "goal_123",
  "goalContext": "Increase revenue by improving customer retention",
  "businessContext": {
    "businessName": "Acme Corp",
    "vision": "To be the leading provider of cloud solutions",
    "purpose": "Empower businesses through technology",
    "coreValues": ["Innovation", "Customer Focus", "Integrity"]
  }
}
```

**Request Constraints:**
- `goalId`: string, required, valid goal ID
- `goalContext`: string, required, max 2000 characters
- `businessContext`: object, required
  - `businessName`: string, required, max 200 characters
  - `vision`: string, required, max 2000 characters
  - `purpose`: string, required, max 2000 characters
  - `coreValues`: array of strings, required, min 1 item, max 20 items, each max 100 characters

**Response:**
```json
{
  "success": true,
  "data": {
    "alignmentScore": 85,
    "explanation": "Goal aligns well with customer focus core value and revenue growth vision",
    "suggestions": [
      "Consider adding specific customer retention metrics",
      "Link to customer satisfaction KPIs"
    ],
    "breakdown": {
      "visionAlignment": 90,
      "purposeAlignment": 85,
      "valuesAlignment": 80
    }
  }
}
```

**Response Constraints:**
- `alignmentScore`: number, 0-100
- `breakdown`: object with alignment scores for each dimension (0-100)

---

## Reports

### 60. GET /reports/company

Generate company report (PDF/Excel).

**Query Parameters:**
- `startDate`: string, required, ISO date (YYYY-MM-DD)
- `endDate`: string, required, ISO date (YYYY-MM-DD)
- `format`: string, optional, one of: `"PDF"`, `"DOCX"` (default: `"PDF"`)
- `sections`: string, optional, comma-separated list, e.g., `"Goals,KPIs,Strategies,Issues"`
- `includeAnalytics`: boolean, optional, include analytics (default: `true`)
- `includeCharts`: boolean, optional, include charts (default: `true`)

**Response:**
- Content-Type: `application/pdf` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="company-report-2025-01-15.pdf"`
- Body: Binary file content (Blob)

**Response Constraints:**
- Returns binary file (Blob)
- Filename in Content-Disposition header
- DOCX format may not be fully supported (returns 400 if not available)

---

## Data Transformation Notes

### Frontend → Backend

**Issue Creation/Update:**
- Frontend: `reportedBy` (camelCase)
- Backend: `ReportedBy` (PascalCase)
- Transformation in `operations-traction-service.ts`

**Actions:**
- Frontend sends Date objects
- Backend expects ISO 8601 strings
- Auto-transformed by axios

**Dates:**
- All dates converted to ISO 8601 strings before sending
- Format: `"2025-01-15T10:30:00Z"`

### Backend → Frontend

**Nested Responses:**
Frontend handles multiple possible structures:
```typescript
const data = response.data.data?.data || response.data.data || response.data || [];
```

**Date Conversion:**
All date strings converted to Date objects:
```typescript
createdAt: new Date(apiData.createdAt)
```

**Pagination:**
Pagination object structure:
```typescript
{
  page: number,
  size: number,
  total: number,
  hasMore: boolean
}
```

---

## Error Handling

### Standard Error Response Structure

All error responses follow this consistent format:

```json
{
  "success": false,
  "error": "Human-readable error message describing what went wrong",
  "code": "ERROR_CODE",
  "details": {}  // Optional: Additional context for the error
}
```

### Error Response Examples

#### 400 Bad Request - Validation Error
```json
{
  "success": false,
  "error": "Validation failed",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "email",
    "message": "Invalid email format"
  }
}
```

#### 400 Bad Request - Business Rule Violation
```json
{
  "success": false,
  "error": "Cannot unlink primary KPI without designating a new primary",
  "code": "PRIMARY_KPI_REQUIRED"
}
```

#### 401 Unauthorized
```json
{
  "success": false,
  "error": "Authentication token is invalid or expired",
  "code": "UNAUTHORIZED"
}
```

#### 403 Forbidden
```json
{
  "success": false,
  "error": "You do not have permission to perform this action",
  "code": "FORBIDDEN"
}
```

#### 404 Not Found
```json
{
  "success": false,
  "error": "Goal not found",
  "code": "RESOURCE_NOT_FOUND",
  "details": {
    "resourceType": "Goal",
    "resourceId": "goal_123"
  }
}
```

#### 409 Conflict
```json
{
  "success": false,
  "error": "A goal with this name already exists",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "name",
    "value": "Increase Revenue"
  }
}
```

#### 422 Unprocessable Entity - Multiple Validation Errors
```json
{
  "success": false,
  "error": "Validation failed for multiple fields",
  "code": "VALIDATION_ERROR",
  "details": {
    "errors": [
      {
        "field": "name",
        "message": "Name is required"
      },
      {
        "field": "targetValue",
        "message": "Target value must be greater than 0"
      }
    ]
  }
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error": "An unexpected error occurred",
  "code": "INTERNAL_SERVER_ERROR"
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created (for POST requests)
- `400` - Bad request / validation error / business rule violation
- `401` - Unauthorized (token expired or invalid)
- `403` - Forbidden (insufficient permissions)
- `404` - Resource not found
- `409` - Conflict (e.g., duplicate name)
- `422` - Unprocessable entity (multiple validation errors)
- `500` - Server error

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400, 422 | Input validation failed |
| `UNAUTHORIZED` | 401 | Authentication required or token invalid |
| `FORBIDDEN` | 403 | User lacks required permissions |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource does not exist |
| `DUPLICATE_RESOURCE` | 409 | Resource with same identifier already exists |
| `BUSINESS_RULE_VIOLATION` | 400 | Operation violates business rules |
| `PRIMARY_KPI_REQUIRED` | 400 | Cannot remove primary KPI without replacement |
| `KPI_LINKED_TO_GOALS` | 400 | Cannot delete KPI that is linked to goals |
| `INVALID_STATE_TRANSITION` | 400 | Invalid goal state change requested |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

### Frontend Error Handling

- Token refresh on 401 (automatic via interceptor)
- Offline queue for failed requests
- Cache fallback when offline
- User-friendly error messages via toast notifications

---

## Authentication & Headers

### Required Headers

All requests require:
```
Authorization: Bearer {access_token}
X-Tenant-Id: {tenant_id}
Content-Type: application/json
```

### Token Refresh

- Automatic token refresh on 401 responses
- Retry mechanism for failed requests after refresh
- Session expiration handling

---

## Cache Invalidation Strategy

### Goals
- Invalidate on: create, update, delete, status change
- Cache key: Full list or by ID
- Cache invalidation callbacks supported

### Actions
- Invalidate on: create, update, delete
- Filter-based caching

### Issues
- Invalidate on: create, update, delete
- Filter-based caching

### KPIs
- Invalidate on: milestone updates, actual recordings, plan adjustments
- Goal-specific KPI cache invalidation

---

## Testing Notes

### Mock vs Real API
- All services use real traction API
- No mock mode in production code
- Tests use mocked axios instance

### Environment Variables
```
REACT_APP_TRACTION_API_URL=http://localhost:8002
```

---

## Implementation Files Reference

- `src/services/traction.ts` - Axios instance with interceptors
- `src/services/goal-service.ts` - Goals, Strategies, KPI linking
- `src/services/kpi-planning-service.ts` - KPI Planning
- `src/services/operations-traction-service.ts` - Core Operations API
- `src/services/issue-service.ts` - Issue lifecycle (uses fetch)
- `src/services/activity.ts` - Goal activity
- `src/services/reports.ts` - Company reports

---

## Version History

**v5.0 (2025-01-XX)**
- Complete rewrite from scratch
- All 60 endpoints documented with full request/response payloads
- Expanded nested objects in all examples
- Complete data constraints and validation rules
- Clear separation of concerns
- Removed mixed specifications and changes
- Removed cross-goal-alerts endpoints (25-27) - visual indication via `isShared` and `sharedGoals` in KPI responses is sufficient
- Updated KPI planning routes: `/shared-kpis/` → `/kpi-planning/kpis/` with `/kpi-planning/` prefix

**v4.0 (2025-11-20)**
- KPI route consolidation from `/shared-kpis/...` to `/kpis/...`

**v3.0 (2025-11-10)**
- Complete audit of all frontend API calls
- 61 documented endpoints

---

**End of Specification**

For questions or clarifications, refer to the implementation files or contact the development team.

