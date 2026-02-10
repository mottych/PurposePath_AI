# Traction Service Backend Integration Specifications (v6)

**Version:** 6.0 - Measure Linking & Data Model Refactoring  
**Last Updated:** 2025-12-21  
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

### Measure Management (7 endpoints)
13. `POST /measures` - Create Measure instance
14. `GET /measures/{id}` - Get Measure details
15. `PUT /measures/{id}` - Update Measure instance
16. `DELETE /measures/{id}` - Delete Measure instance
17. `GET /measures` - List Measures
18. `GET /goals/{goalId}/measures` - List Measures for goal
19. `PUT /goals/{goalId}/measures/{kpiId}:setPrimary` - Set Measure as primary

### Measure Linking (9 endpoints)
20. `POST /goals/{goalId}/measures:link` - Link Measure to goal (with person and optional strategy)
21. `POST /goals/{goalId}/measures:unlink` - Unlink Measure from goal
22. `POST /goals/{goalId}/measures/{kpiId}:setThreshold` - Set Measure threshold
23. `GET /goals/{goalId}/measures/{kpiId}:link` - Get Measure linkage details
24. `GET /goals/{goalId}/available-measures` - Get available Measures for goal
25. `GET /people/{personId}/measures` - List personal scorecard Measures
26. `POST /people/{personId}/measures:link` - Link Measure to person (personal scorecard)
27. `POST /people/{personId}/measures:unlink` - Unlink Measure from person
28. `GET /strategies/{strategyId}/measures` - List Measures for strategy

### Measure Data & Planning (12 endpoints)
29. `GET /measure-links/{linkId}/targets` - Get targets for a Measure link (all subtypes)
30. `POST /measure-links/{linkId}/targets` - Create target (with subtype)
31. `PUT /measure-links/{linkId}/targets/{targetId}` - Update target
32. `DELETE /measure-links/{linkId}/targets/{targetId}` - Delete target
33. `GET /measure-links/{linkId}/actuals` - Get actuals for a Measure link
34. `POST /measure-links/{linkId}/actuals` - Record actual (with subtype)
35. `GET /measure-links/{linkId}/all-series` - Get all target lines + actuals
36. `GET /measure-planning/goals/{goalId}/measure-planning` - Get goal Measure planning overview
37. `POST /measure-planning/measures/{id}/adjust` - Adjust Measure plan
38. `GET /measure-planning/measures/{kpiId}/cross-goal-impact` - Get cross-goal impact
39. `GET /measure-planning/measures/{id}/replan-rule` - Get replan rule
40. `PUT /measure-planning/measures/{id}/replan-rule` - Update replan rule

### Actions (7 endpoints)
41. `GET /operations/actions` - List actions
42. `POST /operations/actions` - Create action
43. `PUT /operations/actions/{id}` - Update action
44. `DELETE /operations/actions/{id}` - Delete action
45. `PUT /operations/actions/{id}/goals` - Link action to goals
46. `PUT /operations/actions/{id}/strategies` - Link action to strategies
47. `DELETE /operations/actions/{id}/relationships` - Remove action relationships

### Issues (4 endpoints)
48. `GET /issues` - List issues
49. `POST /issues` - Create issue
50. `PUT /issues/{id}` - Update issue
51. `DELETE /issues/{id}` - Delete issue

### Issue Types (5 endpoints)
52. `GET /operations/issue-types` - List issue types
53. `POST /operations/issue-types` - Create issue type
54. `PUT /operations/issue-types/{id}` - Update issue type
55. `DELETE /operations/issue-types/{id}` - Delete issue type
56. `POST /operations/issue-types/{id}:activate` - Activate issue type

### Issue Statuses (6 endpoints)
57. `GET /operations/issue-statuses` - List issue statuses
58. `POST /operations/issue-statuses` - Create issue status
59. `PUT /operations/issue-statuses/{id}` - Update issue status
60. `DELETE /operations/issue-statuses/{id}` - Delete issue status
61. `POST /operations/issue-statuses/{id}:activate` - Activate issue status
62. `PUT /operations/issue-statuses:reorder` - Reorder issue statuses

### Issue Lifecycle (4 endpoints - uses fetch, not traction client)
63. `POST /issues/{id}/root-cause` - Root cause analysis
64. `POST /issues/{id}/convert-to-actions` - Convert issue to actions
65. `GET /issues/{id}/closure-eligibility` - Check closure eligibility
66. `POST /issues/{id}/close` - Close issue

### Operations Integration (4 endpoints)
67. `POST /operations/measure-updates` - Sync Measure update
68. `POST /operations/actions/goals` - Get goals for actions
69. `POST /operations/actions/strategies` - Get strategies for actions
70. `POST /operations/goals/measures` - Get Measures for goals

### Activity (2 endpoints)
71. `GET /goals/{goalId}/activity` - Get goal activity
72. `POST /goals/{goalId}/activity` - Add activity entry

### Alignment (1 endpoint)
73. `POST /alignment/check` - Calculate alignment

### Reports (1 endpoint)
74. `GET /reports/company` - Generate company report

**Total: 74 API endpoints**

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

// Measure direction
type MeasureDirection = 'up' | 'down'; // up = higher is better, down = lower is better

// Measure types
type MeasureType = 'quantitative' | 'qualitative' | 'binary';

// Measure aggregation types
type AggregationType = 'sum' | 'average' | 'min' | 'max' | 'latest' | 'count' | 'pointInTime';

// Measure aggregation periods
type AggregationPeriod = 'none' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';

// Measure data nature
type DataNature = 'snapshot' | 'aggregate' | 'other';

// Measure data category (v6: unified target/actual storage)
type MeasureDataCategory = 'Target' | 'Actual';

// Measure target subtypes (v6: three target lines for planning)
type TargetSubtype = 'Expected' | 'Optimal' | 'Minimal';
// Expected = Primary target line (black) - realistic goal
// Optimal = Stretch target line (green) - best-case scenario
// Minimal = Floor threshold line (red) - minimum acceptable

// Measure actual subtypes (v6: distinguish estimate vs measured)
type ActualSubtype = 'Estimate' | 'Measured';
// Estimate = User's best guess when measurement not available
// Measured = Actual recorded measurement from data source

// Measure link types (v6: flexible linking to Person, Goal, Strategy)
type MeasureLinkType = 'personal' | 'goal' | 'strategy';
// personal = Measure linked only to Person (personal scorecard)
// goal = Measure linked to Person + Goal
// strategy = Measure linked to Person + Goal + Strategy

// Measure interpolation methods
type InterpolationMethod = 'linear' | 'exponential' | 'step';

// Measure adjustment strategies
type AdjustmentStrategy = 'maintain_final_goal' | 'proportional_shift' | 'custom';

// Measure data sources
type MeasureDataSource = 'manual' | 'action' | 'integration';

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
    "measures": [],
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-01-15T10:30:00Z"
  }
}
```

**Response Constraints:**
- `status`: defaults to `"draft"`
- `alignmentScore`: number, 0-100
- `strategies`: array, initially empty
- `measures`: array, initially empty
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
        "measures": [
          {
            "id": "goalmeasure_101",
            "goalId": "goal_456",
            "kpiId": "measure_202",
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
      "Link to customer satisfaction Measures"
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
    "measures": [
      {
        "id": "goalmeasure_101",
        "goalId": "goal_456",
        "kpiId": "measure_202",
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

## Measure Management

### 13. POST /measures

Create a new Measure instance (catalog-based or custom).

**Request Body:**
```json
{
  "catalogId": "catalog_measure_1",
  "name": "Monthly Recurring Revenue",
  "description": "Total predictable revenue per month from subscriptions",
  "unit": "USD",
  "direction": "up",
  "type": "quantitative",
  "category": "Financial",
  "aggregationType": "sum",
  "aggregationPeriod": "monthly",
  "aggregationPeriodCount": 1,
  "valueType": "aggregate",
  "currentValue": 42000,
  "currentValueDate": "2025-01-15",
  "calculationMethod": "Sum of all subscription revenues",
  "measurementFrequency": "monthly",
  "ownerId": "user_123"
}
```

**Request Constraints:**

**If `catalogId` provided** (catalog-based Measure):
- `name`, `description`, `unit`, `direction`, `type`, `category`: OPTIONAL (inherited from catalog, can be overridden)
- `aggregationType`, `aggregationPeriod`, `valueType`: OPTIONAL (inherited from catalog, can be overridden)

**If `catalogId` is null/omitted** (custom Measure):
- `name`: REQUIRED, max 200 characters
- `description`: REQUIRED, max 2000 characters
- `unit`: REQUIRED, max 50 characters
- `direction`: REQUIRED, MeasureDirection enum
  - Valid values: `"up"` | `"down"`
  - `"up"` = higher values are better (e.g., revenue, customer satisfaction)
  - `"down"` = lower values are better (e.g., costs, churn rate)
- `type`: REQUIRED, MeasureType enum
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
- `aggregationPeriodCount`: OPTIONAL, number, default 1
  - Specifies how many periods to aggregate (e.g., 2 for bi-weekly when period is weekly)
  - Example: weekly + count=2 = every 2 weeks
  - Example: monthly + count=3 = quarterly
- `valueType`: REQUIRED, DataNature enum
  - Valid values: `"snapshot"` | `"aggregate"` | `"other"`
  - `"snapshot"` = point-in-time measurement (e.g., account balance, inventory level)
  - `"aggregate"` = accumulated over time (e.g., monthly revenue, total sales)
  - `"other"` = neither snapshot nor aggregate
- `category`: OPTIONAL, max 100 characters

**Optional fields (all Measure types):**
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
    "id": "measure_456",
    "catalogId": "catalog_measure_1",
    "name": "Monthly Recurring Revenue",
    "description": "Total predictable revenue per month from subscriptions",
    "unit": "USD",
    "direction": "up",
    "type": "quantitative",
    "category": "Financial",
    "aggregationType": "sum",
    "aggregationPeriod": "monthly",
    "aggregationPeriodCount": 1,
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
- `aggregationPeriodCount`: number, how many periods to aggregate (e.g., 2 for bi-weekly)
- `isShared`: boolean, always `false` for newly created Measures (no goal linkages yet)
- `linkedGoalCount`: number, always `0` for newly created Measures

**Status Codes:**
- `201` - Measure created successfully
- `400` - Validation error (missing required fields, invalid enum values)
- `404` - Catalog Measure not found (if catalogId provided)

---

### 14. GET /measures/{id}

Get complete details for a single Measure instance.

**Path Parameters:**
- `id`: string, required - Measure ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "measure_456",
    "catalogId": "catalog_measure_1",
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
- `linkedGoalCount`: number, count of goals this Measure is linked to
- `linkedGoals`: array of goal link details with `isPrimary` indicator

**Status Codes:**
- `200` - Success
- `404` - Measure not found

---

### 15. PUT /measures/{id}

Update properties of an existing Measure instance. Changes affect all goals linked to this Measure.

**Path Parameters:**
- `id`: string, required - Measure ID

**Request Body (all fields optional for partial update):**
```json
{
  "name": "Updated Measure Name",
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
- If Measure is linked to catalog (`catalogId` not null):
  - Updating `name`, `description`, `unit`, `direction` creates instance-specific override
  - Original catalog values remain unchanged
- Field constraints same as POST /measures

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "measure_456",
    "name": "Updated Measure Name",
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
- `404` - Measure not found

---

### 16. DELETE /measures/{id}

Soft-delete a Measure instance. Only allowed if Measure is not linked to any goals.

**Path Parameters:**
- `id`: string, required - Measure ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "measure_456",
    "deletedAt": "2025-01-20T10:00:00Z",
    "message": "Measure soft-deleted successfully"
  }
}
```

**Business Rules:**
- Returns `400` if Measure is linked to any goals
- Must unlink from all goals before deletion
- **Soft-delete behavior**:
  - Measure marked as `isDeleted: true`, `deletedAt` timestamp set
  - Measure record preserved in database (not physically deleted)
  - All associated data retained:
    - ✅ Milestones preserved (linked via MeasureId)
    - ✅ Actuals preserved (linked via MeasureId)
    - ✅ Plan adjustments preserved (linked via MeasureId)
    - ✅ Replan rules preserved (linked via MeasureId)
  - Soft-deleted Measures excluded from list/search queries by default
  - Can be permanently deleted or restored by admin operations (future feature)
  - Historical data remains queryable for reporting/audit purposes

**Data Retention Rationale:**
- Milestones and actuals represent historical business data that should not be lost
- Enables audit trails and historical reporting
- Allows potential Measure restoration without data loss
- Maintains referential integrity for cross-goal Measure analysis

**Status Codes:**
- `200` - Success
- `400` - Measure is linked to goals (cannot delete)
- `404` - Measure not found

---

### 17. GET /measures

List all Measures for the tenant.

**Query Parameters:**
- `catalogOnly`: boolean, optional - Only show catalog-based Measures
- `customOnly`: boolean, optional - Only show custom Measures
- `includeShared`: boolean, optional, default true - Include Measures shared across goals
- `category`: string, optional - Filter by category
- `page`: number, optional, default 1
- `pageSize`: number, optional, default 20, max 100

**Response:**
```json
{
  "success": true,
  "data": {
    "measures": [
      {
        "id": "measure_456",
        "name": "Monthly Recurring Revenue",
        "unit": "USD",
        "direction": "up",
        "type": "quantitative",
        "category": "Financial",
        "catalogId": "catalog_measure_1",
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

### 18. GET /goals/{goalId}/measures

List all Measures linked to a specific goal with primary indicator.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Response:**
```json
{
  "success": true,
  "data": {
    "goalId": "goal_456",
    "goalName": "Increase Revenue",
    "measures": [
      {
        "linkId": "goalmeasure_101",
        "kpiId": "measure_456",
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
        "linkId": "goalmeasure_102",
        "kpiId": "measure_457",
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
    "totalMeasures": 2,
    "hasPrimary": true,
    "primaryMeasure": {
      "kpiId": "measure_456",
      "name": "Monthly Recurring Revenue"
    }
  }
}
```

**Response Constraints:**
- `isPrimary`: boolean, indicates if this Measure is the primary Measure for this goal
- `isShared`: boolean, true if Measure is linked to multiple goals
- `sharedGoalCount`: number, total count of goals this Measure is linked to
- `primaryMeasure`: object with details of the primary Measure (null if no Measures linked)

**Status Codes:**
- `200` - Success
- `404` - Goal not found

---

### 19. PUT /goals/{goalId}/measures/{kpiId}:setPrimary

Set a specific Measure as the primary Measure for this goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `kpiId`: string, required - Measure ID to set as primary

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
    "previousPrimaryMeasureId": "measure_old_123",
    "newPrimaryMeasureId": "measure_789",
    "updatedAt": "2025-01-15T12:00:00Z"
  }
}
```

**Business Rules:**
- Measure must already be linked to the goal
- Previous primary Measure (if any) automatically demoted to `isPrimary: false`
- Only one Measure can be primary per goal

**Status Codes:**
- `200` - Success
- `400` - Measure is not linked to this goal
- `404` - Goal or Measure not found

---

## Measure Linking

### 20. POST /goals/{goalId}/measures:link

Link a Measure to a goal with a responsible person.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Request Body:**
```json
{
  "kpiId": "measure_456",
  "personId": "person_789",
  "strategyId": null,
  "thresholdPct": 80,
  "isPrimary": true,
  "linkType": "primary",
  "weight": 0.5,
  "displayOrder": 1
}
```

**Request Constraints:**
- `kpiId`: string, required, valid Measure ID (existing Measure instance)
- `personId`: string, required, valid Person ID (person responsible for targets/actuals)
- `strategyId`: string, optional, valid Strategy ID (only if linking to a specific strategy within the goal)
- `thresholdPct`: number, optional, 0-100, percentage threshold for goal achievement
- `isPrimary`: boolean, optional
  - If `true`: This Measure becomes primary (any existing primary is demoted)
  - If `false` or omitted and goal has no Measures: Auto-set to `true` (first Measure is primary by default)
  - If `false` or omitted and goal has existing Measures: Defaults to `false`
- `linkType`: string, optional, one of: `"primary"`, `"secondary"`, `"supporting"`, `"monitoring"`
- `weight`: number, optional, 0.0-1.0, importance weight for composite progress calculation
- `displayOrder`: number, optional, display order in UI

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpilink_101",
    "kpiId": "measure_456",
    "personId": "person_789",
    "personName": "John Doe",
    "goalId": "goal_456",
    "strategyId": null,
    "isPrimary": true,
    "thresholdPct": 80,
    "linkType": "primary",
    "weight": 0.5,
    "displayOrder": 1,
    "linkedAt": "2025-01-15T11:30:00Z"
  }
}
```

**Business Rules:**
- Every Measure link requires a personId (the person responsible for targets/actuals)
- First Measure linked to a goal automatically becomes primary
- If `isPrimary: true` is set, previous primary (if any) is automatically demoted
- Measure can be linked to multiple goals simultaneously
- Goal-level links: Only ONE link allowed per MeasureId+GoalId combination (without strategyId)
- Strategy-level links: Only ONE link allowed per MeasureId+StrategyId combination

**Status Codes:**
- `201` - Measure linked successfully
- `400` - Measure already linked to this goal/strategy
- `404` - Goal, Measure, Person, or Strategy not found

---

### 21. POST /goals/{goalId}/measures:unlink

Unlink a Measure from a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Request Body:**
```json
{
  "kpiId": "measure_456",
  "newPrimaryMeasureId": "measure_789"
}
```

**Request Constraints:**
- `kpiId`: string, required, Measure ID to unlink
- `newPrimaryMeasureId`: string, optional
  - **REQUIRED** if `kpiId` is the current primary Measure AND goal has other Measures linked
  - **FORBIDDEN** if `kpiId` is not the current primary Measure
  - **FORBIDDEN** if `kpiId` is the only Measure linked to goal

**Response:**
```json
{
  "success": true,
  "data": {
    "goalId": "goal_456",
    "unlinkedMeasureId": "measure_456",
    "newPrimaryMeasureId": "measure_789",
    "remainingMeasureCount": 2
  }
}
```

**Business Rules:**
- Cannot unlink primary Measure without selecting new primary (if other Measures exist)
- If removing last Measure from goal: Allowed, goal will have no primary Measure
- Unlinking Measure does not delete the Measure instance (still exists for other goals)

**Status Codes:**
- `200` - Success
- `400` - Attempting to unlink primary Measure without providing `newPrimaryMeasureId` when other Measures exist
- `400` - Provided `newPrimaryMeasureId` is not linked to this goal
- `404` - Measure not linked to this goal

---

### 22. POST /goals/{goalId}/measures/{kpiId}:setThreshold

Set threshold percentage for a Measure linked to a goal.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `kpiId`: string, required - Measure ID

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

### 23. GET /goals/{goalId}/measures/{kpiId}:link

Get Measure linkage information including threshold, person, and strategy.

**Path Parameters:**
- `goalId`: string, required - Goal ID
- `kpiId`: string, required - Measure ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpilink_101",
    "kpiId": "measure_456",
    "personId": "person_789",
    "personName": "John Doe",
    "goalId": "goal_456",
    "strategyId": null,
    "thresholdPct": 80,
    "linkType": "primary",
    "weight": 0.5,
    "displayOrder": 1,
    "isPrimary": true,
    "linkedAt": "2025-01-15T11:30:00Z"
  }
}
```

**Response Constraints:**
- `thresholdPct`: number | null
- `personId`: string, required (person responsible for this link)
- `strategyId`: string | null (null for goal-level links)

---

### 24. GET /goals/{goalId}/available-measures

Get available Measures for a goal (catalog Measures and tenant custom Measures).

**Path Parameters:**
- `goalId`: string, required - Goal ID

**Response:**
```json
{
  "success": true,
  "data": {
    "catalogMeasures": [
      {
        "id": "catalog_measure_1",
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
    "tenantCustomMeasures": [
      {
        "id": "custom_measure_1",
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
- `catalogMeasures`: array of MeasureCatalogItem
- `tenantCustomMeasures`: array of Measure
- `usageInfo.goalCount`: number, count of goals using this Measure
- `usageInfo.isUsedByThisGoal`: boolean, whether this Measure is already linked to the goal

---

## Measure Linking - Person-based Endpoints

### 25. GET /people/{personId}/measures

List all Measures linked to a person (personal scorecard).

**Path Parameters:**
- `personId`: string, required - Person ID

**Response:**
```json
{
  "success": true,
  "data": {
    "personId": "person_789",
    "personName": "John Doe",
    "measures": [
      {
        "linkId": "kpilink_101",
        "kpiId": "measure_456",
        "name": "Billable Hours",
        "unit": "hours",
        "direction": "up",
        "linkType": "personal",
        "goalId": null,
        "strategyId": null,
        "isPrimary": true,
        "thresholdPct": 80,
        "currentValue": 120,
        "linkedAt": "2025-01-15T11:30:00Z"
      }
    ],
    "totalMeasures": 1
  }
}
```

---

### 26. POST /people/{personId}/measures:link

Link a Measure to a person as a personal scorecard metric.

**Path Parameters:**
- `personId`: string, required - Person ID

**Request Body:**
```json
{
  "kpiId": "measure_456",
  "thresholdPct": 80,
  "isPrimary": true,
  "linkType": "primary",
  "weight": 1.0,
  "displayOrder": 1
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpilink_101",
    "kpiId": "measure_456",
    "personId": "person_789",
    "goalId": null,
    "strategyId": null,
    "isPrimary": true,
    "thresholdPct": 80,
    "linkedAt": "2025-01-15T11:30:00Z"
  }
}
```

**Business Rules:**
- Multiple people CAN have the same Measure linked (personal metrics)
- No Goal or Strategy association (personal scorecard only)

---

### 27. POST /people/{personId}/measures:unlink

Unlink a Measure from a person's personal scorecard.

**Path Parameters:**
- `personId`: string, required - Person ID

**Request Body:**
```json
{
  "kpiLinkId": "kpilink_101"
}
```

**Response:**
```json
{
  "success": true
}
```

---

### 28. GET /strategies/{strategyId}/measures

List all Measures linked to a specific strategy.

**Path Parameters:**
- `strategyId`: string, required - Strategy ID

**Response:**
```json
{
  "success": true,
  "data": {
    "strategyId": "strategy_456",
    "goalId": "goal_123",
    "measures": [
      {
        "linkId": "kpilink_102",
        "kpiId": "measure_789",
        "name": "Conversion Rate",
        "unit": "%",
        "personId": "person_123",
        "personName": "Jane Smith",
        "isPrimary": true,
        "linkedAt": "2025-01-15T11:30:00Z"
      }
    ]
  }
}
```

---

## Measure Data & Planning

### 29. GET /measure-links/{linkId}/targets

Get all targets for a Measure link (supports filtering by subtype).

**Path Parameters:**
- `linkId`: string, required - MeasureLink ID

**Query Parameters:**
- `subtype`: string, optional - Filter by target subtype: `"Expected"`, `"Optimal"`, `"Minimal"`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "kpidata_123",
      "kpiLinkId": "kpilink_101",
      "dataCategory": "Target",
      "targetSubtype": "Expected",
      "postValue": 50000,
      "postDate": "2025-03-31",
      "measuredPeriodStartDate": null,
      "label": "Q1 Target",
      "confidenceLevel": 4,
      "rationale": "Based on historical growth trends",
      "createdAt": "2025-01-01T00:00:00Z",
      "updatedAt": "2025-01-15T10:00:00Z"
    },
    {
      "id": "kpidata_124",
      "kpiLinkId": "kpilink_101",
      "dataCategory": "Target",
      "targetSubtype": "Optimal",
      "postValue": 60000,
      "postDate": "2025-03-31",
      "label": "Q1 Stretch Target",
      "confidenceLevel": 3
    },
    {
      "id": "kpidata_125",
      "kpiLinkId": "kpilink_101",
      "dataCategory": "Target",
      "targetSubtype": "Minimal",
      "postValue": 40000,
      "postDate": "2025-03-31",
      "label": "Q1 Floor"
    }
  ]
}
```

**Response Constraints:**
- `dataCategory`: always `"Target"`
- `targetSubtype`: one of `"Expected"`, `"Optimal"`, `"Minimal"`
- `postDate`: ISO date string (YYYY-MM-DD) - target date
- `postValue`: number, the target value
- `measuredPeriodStartDate`: ISO date string, null for snapshot Measures

---

### 30. POST /measure-links/{linkId}/targets

Create a new target for a Measure link.

**Path Parameters:**
- `linkId`: string, required - MeasureLink ID

**Request Body:**
```json
{
  "targetSubtype": "Expected",
  "postValue": 50000,
  "postDate": "2025-03-31",
  "measuredPeriodStartDate": "2025-03-01",
  "label": "Q1 Target",
  "confidenceLevel": 4,
  "rationale": "Based on historical growth trends"
}
```

**Request Constraints:**
- `targetSubtype`: string, required, one of: `"Expected"`, `"Optimal"`, `"Minimal"`
- `postValue`: number, required
- `postDate`: string, required, ISO date (YYYY-MM-DD)
- `measuredPeriodStartDate`: string, optional, ISO date - for aggregate Measures
- `label`: string, optional, max 200 characters
- `confidenceLevel`: number, optional, 1-5
- `rationale`: string, optional, max 1000 characters

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "kpidata_123",
    "kpiLinkId": "kpilink_101",
    "dataCategory": "Target",
    "targetSubtype": "Expected",
    "postValue": 50000,
    "postDate": "2025-03-31",
    "createdAt": "2025-01-15T10:00:00Z"
  }
}
```

---

### 31. PUT /measure-links/{linkId}/targets/{targetId}

Update an existing target.

**Path Parameters:**
- `linkId`: string, required - MeasureLink ID
- `targetId`: string, required - MeasureData ID (target)

**Request Body:**
```json
{
  "postValue": 55000,
  "label": "Updated Q1 Target",
  "confidenceLevel": 5,
  "rationale": "Revised based on strong Q4 performance"
}
```

**Response:**
Same structure as POST response.

---

### 32. DELETE /measure-links/{linkId}/targets/{targetId}

Delete a target.

**Path Parameters:**
- `linkId`: string, required - MeasureLink ID
- `targetId`: string, required - MeasureData ID (target)

**Response:**
```json
{
  "success": true
}
```

---

### 33. GET /measure-links/{linkId}/actuals

Get all actuals for a Measure link.

**Path Parameters:**
- `linkId`: string, required - MeasureLink ID

**Query Parameters:**
- `startDate`: string, optional, ISO date - filter from date
- `endDate`: string, optional, ISO date - filter to date
- `subtype`: string, optional - Filter by actual subtype: `"Estimate"`, `"Measured"`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "kpidata_200",
      "kpiLinkId": "kpilink_101",
      "dataCategory": "Actual",
      "actualSubtype": "Measured",
      "postValue": 45000,
      "postDate": "2025-01-31",
      "measuredPeriodStartDate": "2025-01-01",
      "dataSource": "manual",
      "sourceReferenceId": null,
      "isManualOverride": false,
      "overrideComment": null,
      "originalValue": null,
      "triggersReplan": false,
      "replanThresholdExceeded": false,
      "createdAt": "2025-02-01T10:00:00Z"
    }
  ]
}
```

**Response Constraints:**
- `dataCategory`: always `"Actual"`
- `actualSubtype`: one of `"Estimate"`, `"Measured"`
- Ordered by `postDate` descending (newest first)
- If both Estimate and Measured exist for same period, both are returned (frontend decides which to display)

---

### 34. POST /measure-links/{linkId}/actuals

Record an actual value for a Measure link.

**Path Parameters:**
- `linkId`: string, required - MeasureLink ID

**Request Body:**
```json
{
  "actualSubtype": "Measured",
  "postValue": 45000,
  "postDate": "2025-01-31",
  "measuredPeriodStartDate": "2025-01-01",
  "dataSource": "manual",
  "sourceReferenceId": null
}
```

**Request Constraints:**
- `actualSubtype`: string, required, one of: `"Estimate"`, `"Measured"`
- `postValue`: number, required
- `postDate`: string, required, ISO date (YYYY-MM-DD)
- `measuredPeriodStartDate`: string, optional, ISO date - for aggregate Measures
- `dataSource`: string, optional, one of: `"manual"`, `"action"`, `"integration"`
- `sourceReferenceId`: string, optional, ID of source (action ID, integration ID)

**Response:**
```json
{
  "success": true,
  "data": {
    "actual": {
      "id": "kpidata_200",
      "kpiLinkId": "kpilink_101",
      "dataCategory": "Actual",
      "actualSubtype": "Measured",
      "postValue": 45000,
      "postDate": "2025-01-31",
      "triggersReplan": false,
      "replanThresholdExceeded": false,
      "createdAt": "2025-02-01T10:00:00Z"
    },
    "computedVariance": {
      "expectedValue": 44000,
      "variance": 1000,
      "variancePercentage": 2.27
    }
  }
}
```

**Response Notes:**
- `computedVariance`: calculated on-the-fly from the Expected target at the same date
- `expectedValue`, `variance`, `variancePercentage` are NOT persisted, only returned for convenience

---

### 35. GET /measure-links/{linkId}/all-series

Get all target lines (Expected, Optimal, Minimal) plus actuals for charting.

**Path Parameters:**
- `linkId`: string, required - MeasureLink ID

**Query Parameters:**
- `startDate`: string, optional, ISO date
- `endDate`: string, optional, ISO date

**Response:**
```json
{
  "success": true,
  "data": {
    "kpiLinkId": "kpilink_101",
    "measure": {
      "id": "measure_456",
      "name": "Monthly Recurring Revenue",
      "unit": "USD",
      "direction": "up",
      "aggregationPeriod": "monthly",
      "aggregationPeriodCount": 1
    },
    "targets": {
      "expected": [
        { "postDate": "2025-03-31", "postValue": 50000, "label": "Q1" },
        { "postDate": "2025-06-30", "postValue": 75000, "label": "Q2" }
      ],
      "optimal": [
        { "postDate": "2025-03-31", "postValue": 60000 },
        { "postDate": "2025-06-30", "postValue": 90000 }
      ],
      "minimal": [
        { "postDate": "2025-03-31", "postValue": 40000 },
        { "postDate": "2025-06-30", "postValue": 55000 }
      ]
    },
    "actuals": [
      { 
        "postDate": "2025-01-31", 
        "postValue": 45000, 
        "actualSubtype": "Measured" 
      }
    ],
    "interpolatedExpected": [
      { "date": "2025-01-31", "value": 44000 },
      { "date": "2025-02-28", "value": 47000 },
      { "date": "2025-03-31", "value": 50000 }
    ]
  }
}
```

**Response Notes:**
- `targets.expected`: Primary target line (black on charts)
- `targets.optimal`: Stretch target line (green on charts)
- `targets.minimal`: Floor threshold line (red on charts)
- `interpolatedExpected`: Pre-computed interpolated values for the Expected line
- All three target lines are optional (may be empty arrays if not defined)

---

### 36. GET /measure-planning/goals/{goalId}/measure-planning

Get complete Measure planning summary for a goal (all Measure links associated with the goal).

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
    "kpiLinks": [
      {
        "linkId": "kpilink_101",
        "kpiId": "measure_456",
        "kpiName": "Monthly Recurring Revenue",
        "unit": "USD",
        "personId": "person_789",
        "personName": "John Doe",
        "strategyId": null,
        "isPrimary": true,
        "targetCount": 12,
        "nextTarget": {
          "id": "kpidata_123",
          "targetSubtype": "Expected",
          "postDate": "2025-03-31",
          "postValue": 50000,
          "label": "Q1 Target"
        },
        "latestActual": {
          "id": "kpidata_200",
          "actualSubtype": "Measured",
          "postDate": "2025-01-15",
          "postValue": 42000
        },
        "computedVariance": {
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

**Response Notes:**
- `computedVariance`: Calculated on-the-fly, not stored
- `targetCount`: Count of all targets (all subtypes combined)
- `nextTarget`: The next Expected target by date

---

### 37. POST /measure-planning/measures/{id}/adjust

Apply a Measure plan adjustment (replanning based on actuals).

**Path Parameters:**
- `id`: string, required - Measure ID

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
      "kpiId": "measure_456",
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

### 38. GET /measure-planning/measures/{kpiId}/cross-goal-impact

Shows which goals use this Measure and their impact level.

**Path Parameters:**
- `kpiId`: string, required - Measure ID

**Response:**
```json
{
  "success": true,
  "data": {
    "kpiId": "measure_123",
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

### 39. GET /measure-planning/measures/{id}/replan-rule

Get auto-replan configuration for a Measure.

**Path Parameters:**
- `id`: string, required - Measure ID

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "rule_123",
    "kpiId": "measure_456",
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
- Returns `404` if no replan rule exists for the Measure
- `varianceThresholdPercentage`: number, 0-100
- `consecutiveMissesRequired`: number, min 1
- `adjustmentStrategy`: AdjustmentStrategy enum

---

### 40. PUT /measure-planning/measures/{id}/replan-rule

Create or update auto-replan configuration.

**Path Parameters:**
- `id`: string, required - Measure ID

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

### 41. GET /operations/actions

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

### 42. POST /operations/actions

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

### 43. PUT /operations/actions/{id}

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

### 44. DELETE /operations/actions/{id}

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

### 45. PUT /operations/actions/{id}/goals

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

### 46. PUT /operations/actions/{id}/strategies

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

### 47. DELETE /operations/actions/{id}/relationships

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

### 48. GET /issues

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

### 49. POST /issues

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

### 50. PUT /issues/{id}

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

### 51. DELETE /issues/{id}

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

### 52. GET /operations/issue-types

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

### 53. POST /operations/issue-types

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

### 54. PUT /operations/issue-types/{id}

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

### 55. DELETE /operations/issue-types/{id}

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

### 56. POST /operations/issue-types/{id}:activate

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

### 57. GET /operations/issue-statuses

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

### 58. POST /operations/issue-statuses

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

### 59. PUT /operations/issue-statuses/{id}

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

### 60. DELETE /operations/issue-statuses/{id}

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

### 61. POST /operations/issue-statuses/{id}:activate

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

### 62. PUT /operations/issue-statuses:reorder

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

### 63. POST /issues/{id}/root-cause

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

### 64. POST /issues/{id}/convert-to-actions

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

### 65. GET /issues/{id}/closure-eligibility

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

### 66. POST /issues/{id}/close

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

### 67. POST /operations/measure-updates

Sync Measure update from an action.

**Request Body:**
```json
{
  "actionId": "action_123",
  "kpiId": "measure_456",
  "horizonId": "horizon_789",
  "newValue": 1000,
  "updateDate": "2025-02-01",
  "notes": "Updated based on action completion"
}
```

**Request Constraints:**
- `actionId`: string, required, valid action ID
- `kpiId`: string, required, valid Measure ID
- `kpiId`: string, required, valid Measure ID
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

### 68. POST /operations/actions/goals

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

### 69. POST /operations/actions/strategies

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

### 70. POST /operations/goals/measures

Get Measures for specific goals.

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
      "id": "measure_456",
      "kpiId": "measure_catalog_1",
      "name": "Monthly Recurring Revenue",
      "unit": "USD",
      "direction": "up",
      // ... other Measure fields
    }
  ]
}
```

**Response:** Array of Measure objects

---

## Activity

### 71. GET /goals/{goalId}/activity

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

### 72. POST /goals/{goalId}/activity

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

### 73. POST /alignment/check

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
      "Link to customer satisfaction Measures"
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

### 74. GET /reports/company

Generate company report (PDF/Excel).

**Query Parameters:**
- `startDate`: string, required, ISO date (YYYY-MM-DD)
- `endDate`: string, required, ISO date (YYYY-MM-DD)
- `format`: string, optional, one of: `"PDF"`, `"DOCX"` (default: `"PDF"`)
- `sections`: string, optional, comma-separated list, e.g., `"Goals,Measures,Strategies,Issues"`
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
  "error": "Cannot unlink primary Measure without designating a new primary",
  "code": "PRIMARY_Measure_REQUIRED"
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
| `PRIMARY_Measure_REQUIRED` | 400 | Cannot remove primary Measure without replacement |
| `Measure_LINKED_TO_GOALS` | 400 | Cannot delete Measure that is linked to goals |
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

### Measures
- Invalidate on: milestone updates, actual recordings, plan adjustments
- Goal-specific Measure cache invalidation

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
- `src/services/goal-service.ts` - Goals, Strategies, Measure linking
- `src/services/measure-planning-service.ts` - Measure Planning
- `src/services/operations-traction-service.ts` - Core Operations API
- `src/services/issue-service.ts` - Issue lifecycle (uses fetch)
- `src/services/activity.ts` - Goal activity
- `src/services/reports.ts` - Company reports

---

## Version History

**v6.0 (2025-12-21) - Measure Linking & Data Model Refactoring**
- **BREAKING**: Renamed `GoalMeasureLink` to `MeasureLink` with extended linking support
- **BREAKING**: Merged `MeasureMilestone` and `MeasureActual` into unified `MeasureData` entity
- **BREAKING**: Field renames: `actualValue`→`postValue`, `measurementDate`→`postDate`
- **NEW**: Measure linking now requires `personId` (person responsible for targets/actuals)
- **NEW**: Measure linking supports optional `strategyId` (strategy-level links within goals)
- **NEW**: Personal scorecard endpoints (`/people/{personId}/measures`)
- **NEW**: Strategy-level Measure endpoints (`/strategies/{strategyId}/measures`)
- **NEW**: Three target subtypes: Expected (primary), Optimal (stretch), Minimal (floor)
- **NEW**: Two actual subtypes: Estimate (user guess), Measured (real data)
- **NEW**: `aggregationPeriodCount` field on Measure for multi-period aggregation
- **NEW**: All-series endpoint for charting (all 3 target lines + actuals)
- **REMOVED**: Persisted `expectedValue`, `variance`, `variancePercentage` (now calculated on-the-fly)
- **REMOVED**: Old `/measure-planning/measures/{id}/milestones` endpoints (replaced by targets)
- **REMOVED**: Old `/measure-planning/measures/{id}/actuals` endpoints (replaced by measure-links endpoints)
- Total: 74 API endpoints (6 new, some deprecated)

**v5.0 (2025-01-XX)**
- Complete rewrite from scratch
- All 68 endpoints documented with full request/response payloads
- Expanded nested objects in all examples
- Complete data constraints and validation rules
- Clear separation of concerns
- Removed mixed specifications and changes
- Removed cross-goal-alerts endpoints (25-27) - visual indication via `isShared` and `sharedGoals` in Measure responses is sufficient
- Updated Measure planning routes: `/shared-measures/` → `/measure-planning/measures/` with `/measure-planning/` prefix

**v4.0 (2025-11-20)**
- Measure route consolidation from `/shared-measures/...` to `/measures/...`

**v3.0 (2025-11-10)**
- Complete audit of all frontend API calls
- 61 documented endpoints

---

**End of Specification**

For questions or clarifications, refer to the implementation files or contact the development team.

