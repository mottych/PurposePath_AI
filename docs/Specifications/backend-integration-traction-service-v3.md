# Traction Service Backend Integration Specifications (v3 - Complete Frontend Implementation)

**Version:** 3.0 - Complete Frontend API Coverage  
**Last Updated:** 2025-11-10  
**Service Base URL:** `{REACT_APP_TRACTION_API_URL}`  
**Default (Localhost):** `http://localhost:8002`  

[← Back to Index](./backend-integration-index.md)

---

## Document Overview

This specification documents **ALL** Traction API endpoints currently called by the frontend application. Each endpoint includes complete request/response payloads and data constraints.

**Important Notes:**

- Routes do NOT include `/api` prefix - base URL already contains full path
- All dates are ISO 8601 format strings
- Frontend uses camelCase for field names
- Nested response structures: `response.data.data?.data || response.data.data || response.data`

---

## Complete API Index

### Goals Management (8 endpoints)

1. `POST /goals` - Create goal
2. `GET /goals` - List goals
3. `GET /goals/{id}` - Get goal
4. `PUT /goals/{id}` - Update goal
5. `DELETE /goals/{id}` - Delete goal
6. `POST /goals/{id}:activate` - Activate
7. `POST /goals/{id}:pause` - Pause
8. `POST /goals/{id}:close` - Close

### Strategies (4 endpoints)

9. `POST /goals/{goalId}/strategies` - Create
10. `PUT /goals/{goalId}/strategies/{id}` - Update
11. `DELETE /goals/{goalId}/strategies/{id}` - Delete
12. `PUT /goals/{goalId}/strategies:reorder` - Reorder

### KPI Linking (5 endpoints)

13. `POST /goals/{goalId}/kpis:link` - Link KPI
14. `POST /goals/{goalId}/kpis:unlink` - Unlink
15. `POST /goals/{goalId}/kpis/{kpiId}:setThreshold` - Set threshold
16. `GET /goals/{goalId}/kpis/{kpiId}:link` - Get linkage
17. `GET /goals/{goalId}/available-kpis` - Available KPIs

### KPI Planning (12 endpoints)

18. `GET /shared-kpis/{id}/milestones` - Get milestones
19. `PUT /shared-kpis/{id}/milestones` - Set milestones
20. `GET /shared-kpis/{id}/plan` - Planning data
21. `GET /goals/{goalId}/kpi-planning` - Goal KPI overview
22. `POST /shared-kpis/{id}/actuals` - Record actual
23. `POST /shared-kpis/{id}/adjust` - Adjust plan
24. `GET /kpis/{id}/cross-goal-impact` - Cross-goal impact
25. `GET /goals/{goalId}/cross-goal-alerts` - Alerts (by goal)
26. `GET /cross-goal-alerts` - All alerts
27. `PATCH /cross-goal-alerts/{id}/acknowledge` - Acknowledge
28. `GET /shared-kpis/{id}/replan-rule` - Get replan rule
29. `PUT /shared-kpis/{id}/replan-rule` - Update replan rule

### Actions (7 endpoints)

30. `GET /operations/actions` - List
31. `POST /operations/actions` - Create
32. `PUT /operations/actions/{id}` - Update
33. `DELETE /operations/actions/{id}` - Delete
34. `PUT /operations/actions/{id}/goals` - Link goals
35. `PUT /operations/actions/{id}/strategies` - Link strategies
36. `DELETE /operations/actions/{id}/relationships` - Remove links

### Issues (4 endpoints)

37. `GET /issues` - List
38. `POST /issues` - Create
39. `PUT /issues/{id}` - Update
40. `DELETE /issues/{id}` - Delete

### Issue Types (5 endpoints)

41. `GET /operations/issue-types` - List
42. `POST /operations/issue-types` - Create
43. `PUT /operations/issue-types/{id}` - Update
44. `DELETE /operations/issue-types/{id}` - Delete
45. `POST /operations/issue-types/{id}:activate` - Activate

### Issue Statuses (6 endpoints)

46. `GET /operations/issue-statuses` - List
47. `POST /operations/issue-statuses` - Create
48. `PUT /operations/issue-statuses/{id}` - Update
49. `DELETE /operations/issue-statuses/{id}` - Delete
50. `POST /operations/issue-statuses/{id}:activate` - Activate
51. `PUT /operations/issue-statuses:reorder` - Reorder

### Issue Lifecycle (4 endpoints - uses fetch, not traction client)

52. `POST /issues/{id}/root-cause` - Root cause analysis
53. `POST /issues/{id}/convert-to-actions` - Convert
54. `GET /issues/{id}/closure-eligibility` - Check eligibility
55. `POST /issues/{id}/close` - Close

### Operations Integration (4 endpoints)

56. `POST /operations/kpi-updates` - Sync KPI update
57. `POST /operations/actions/goals` - Get goals for actions
58. `POST /operations/actions/strategies` - Get strategies for actions
59. `POST /operations/goals/kpis` - Get KPIs for goals

### Other Services (2 endpoints)

60. `POST /alignment/check` - Calculate alignment
61. `GET /reports/company` - Company report

**Total: 61 API endpoints**

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
```

---

## Goals Management

See full specification at: [backend-integration-traction-service-v3-goals.md](./backend-integration-traction-service-v3-goals.md)

**Summary of endpoints:**

- `POST /goals` - Create with title, intent, description, ownerId
- `GET /goals?ownerId={id}` - List with optional owner filter
- `GET /goals/{id}` - Get details including strategies and KPIs
- `PUT /goals/{id}` - Update any field
- `DELETE /goals/{id}` - Delete goal
- `POST /goals/{id}:activate` - Draft/Paused → Active
- `POST /goals/{id}:pause` - Active → Paused
- `POST /goals/{id}:close` - Active → Completed (or any → Cancelled)

---

## Strategies Management

**POST /goals/{goalId}/strategies**

- Create strategy with description, order, aiGenerated flag
- Returns strategy with id, status: 'draft'

**PUT /goals/{goalId}/strategies/{id}**

- Update description, order, or status
- Status: 'draft' | 'validated' | 'adopted'

**DELETE /goals/{goalId}/strategies/{id}**

- Remove strategy

**PUT /goals/{goalId}/strategies:reorder**

- Batch reorder: `{ strategyOrders: [{ strategyId, newOrder }] }`

---

## KPI Management

**POST /goals/{goalId}/kpis:link**

```json
{
  "kpiId": "kpi_catalog_123",
  "thresholdPct": 80
}
```

**POST /goals/{goalId}/kpis:unlink**

```json
{
  "kpiId": "sharedKpi_456"
}
```

**GET /goals/{goalId}/available-kpis**

Returns:

```json
{
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
```

---

## Actions Management

**GET /operations/actions**
Query params: `startDate`, `endDate`, `assignedPersonId`, `goalIds`, `strategyIds`, `issueIds`, `status`, `priority`

Returns nested: `response.data.data?.data || response.data.data || []`

**POST /operations/actions**

```json
{
  "title": "string",
  "description": "string",
  "startDate": "ISO date",
  "dueDate": "ISO date",
  "priority": "low|medium|high|critical",
  "assignedPersonId": "user_id",
  "connections": {
    "goalIds": [],
    "strategyIds": [],
    "issueIds": []
  }
}
```

**PUT /operations/actions/{id}**

- All fields optional
- Can update connections

**DELETE /operations/actions/{id}**

- Also removes relationships

**PUT /operations/actions/{id}/goals**

```json
{
  "goalIds": ["goal_1", "goal_2"]
}
```

**PUT /operations/actions/{id}/strategies**

```json
{
  "strategyIds": ["strat_1", "strat_2"]
}
```

---

## Issues Management

**GET /issues**
Query params: `startDate`, `endDate`, `reportedBy`, `businessImpact`, `priority`, `status`

**POST /issues**

```json
{
  "title": "string",
  "description": "string",
  "typeConfigId": "issue_type_id",
  "reportedBy": "user_id",
  "businessImpact": "low|medium|high|critical",
  "priority": "low|medium|high|critical",
  "statusId": "optional",
  "assignedPersonId": "optional"
}
```

**PUT /issues/{id}**

- Partial update
- Backend expects `ReportedBy` (capital B) per transformation

**DELETE /issues/{id}**

---

## Issue Configuration

### Issue Types

**GET /operations/issue-types**

Query params: `includeInactive`, `includeSystem`

Returns:

```json
{
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

**Extract:** `response.data.data?.types || response.data.data?.data || []`

**POST /operations/issue-types**

```json
{
  "name": "string",
  "description": "string",
  "color": "#hexcode",
  "icon": "emoji",
  "order": 1,
  "isDefault": false
}
```

**PUT /operations/issue-types/{id}**

- Partial update

**DELETE /operations/issue-types/{id}**

**POST /operations/issue-types/{id}:activate**

- Reactivate inactive type

### Issue Statuses

**GET /operations/issue-statuses**

Query params: `category`, `includeInactive`, `includeSystem`

Returns:

```json
{
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

**Extract:** `response.data.data?.statuses || response.data.data?.data || []`

**POST /operations/issue-statuses**

```json
{
  "name": "string",
  "description": "string",
  "category": "open|active|inactive|closed",
  "color": "#hexcode",
  "icon": "emoji",
  "order": 1
}
```

**PUT /operations/issue-statuses/{id}**

- Partial update

**DELETE /operations/issue-statuses/{id}**

**POST /operations/issue-statuses/{id}:activate**

- Reactivate

**PUT /operations/issue-statuses:reorder**

```json
{
  "category": "open|active|inactive|closed",
  "statusIds": ["id1", "id2", "id3"]
}
```

---

## Issue Lifecycle (Non-Traction Client)

**Note:** These use `fetch()` directly with `baseUrl` from env, not the traction axios instance.

**POST /issues/{id}/root-cause**

```json
{
  "issueId": "issue_123",
  "method": "swot|five_whys",
  "analysis": { /* SWOT or FiveWhys structure */ }
}
```

**POST /issues/{id}/convert-to-actions**

```json
{
  "actions": [{
    "title": "string",
    "description": "string",
    "assignedPersonId": "user_id",
    "priority": "low|medium|high|critical"
  }],
  "newStatusId": "status_config_id"
}
```

Returns: `{ actionIds: ["action_1", "action_2"] }`

**GET /issues/{id}/closure-eligibility**
Returns:

```json
{
  "canClose": true,
  "completedActions": 3,
  "totalActions": 3
}
```

**POST /issues/{id}/close**

- No payload
- Marks issue as closed

---

## KPI Planning (Milestone-Based)

**GET /shared-kpis/{id}/milestones**

- Returns array of milestones

**PUT /shared-kpis/{id}/milestones**

```json
{
  "milestones": [{
    "milestoneDate": "2025-03-31",
    "targetValue": 50000,
    "description": "Q1 Target"
  }],
  "replaceAll": false
}
```

Returns: milestones, interpolated periods, impact analysis

**GET /shared-kpis/{id}/plan?granularity=monthly**

- Returns KPI info, milestones, interpolated periods, trajectory

**GET /goals/{goalId}/kpi-planning**

- Overview of all KPIs for a goal

**POST /shared-kpis/{id}/actuals**

```json
{
  "measurementDate": "2025-01-31",
  "actualValue": 45000,
  "source": "manual|action|integration",
  "sourceId": "optional",
  "adjustmentStrategy": "auto|manual|none"
}
```

**POST /shared-kpis/{id}/adjust**

```json
{
  "adjustmentType": "maintain_final_goal|proportional_shift|custom",
  "basedOnActualId": "optional",
  "customMilestones": [],
  "rationale": "string"
}
```

**GET /kpis/{id}/cross-goal-impact**

- Shows which goals use this KPI

**GET /cross-goal-alerts?status=pending**

- Get pending alerts

**PATCH /cross-goal-alerts/{id}/acknowledge**

```json
{
  "decision": "accepted|rejected|modified",
  "notes": "optional"
}
```

**GET /shared-kpis/{id}/replan-rule**

- Get auto-replan configuration

**PUT /shared-kpis/{id}/replan-rule**

- Update replan configuration

---

## Operations Integration

**POST /operations/kpi-updates**

```json
{
  "actionId": "string",
  "kpiId": "string",
  "sharedKpiId": "string",
  "horizonId": "string",
  "newValue": 1000,
  "updateDate": "ISO date",
  "notes": "optional"
}
```

**POST /operations/actions/goals**

```json
{
  "actionIds": ["action_1", "action_2"]
}
```

Returns: Array of Goal objects

**POST /operations/actions/strategies**

```json
{
  "actionIds": ["action_1", "action_2"]
}
```

Returns: Array of Strategy objects

**POST /operations/goals/kpis**

```json
{
  "goalIds": ["goal_1", "goal_2"]
}
```

Returns: Array of SharedKPI objects

---

## Alignment & Reports

**POST /alignment/check**

```json
{
  "goalId": "goal_123",
  "goalContext": "string",
  "businessContext": {
    "businessName": "string",
    "vision": "string",
    "purpose": "string",
    "coreValues": []
  }
}
```

Returns:

```json
{
  "alignmentScore": 85,
  "explanation": "string",
  "suggestions": []
}
```

**GET /reports/company**
Query params: Company report parameters
Response: Blob (PDF/Excel)

---

## Data Transformation Notes

### Frontend → Backend

**Issue Creation:**

- Frontend: `reportedBy` (camelCase)
- Backend: `ReportedBy` (PascalCase)
- Transformation in `operations-traction-service.ts`

**Actions:**

- Frontend sends full date objects
- Backend expects ISO strings
- Auto-transformed by axios

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

---

## Error Handling

**Standard Error Response:**

```json
{
  "success": false,
  "error": "Error message"
}
```

**Common HTTP Status Codes:**

- `200` - Success
- `400` - Bad request / validation error
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Resource not found
- `500` - Server error

**Frontend Error Handling:**

- Token refresh on 401 (automatic via interceptor)
- Offline queue for failed requests
- Cache fallback when offline
- User-friendly error messages via toast

---

## Cache Invalidation Strategy

**Goals:**

- Invalidate on: create, update, delete, status change
- Cache key: Full list or by ID

**Actions:**

- Invalidate on: create, update, delete
- Filter-based caching

**Issues:**

- Invalidate on: create, update, delete
- Filter-based caching

---

## Testing Notes

**Mock vs Real API:**

- All services use real traction API
- No mock mode in production code
- Tests use mocked axios instance

**Environment Variables:**

```
REACT_APP_TRACTION_API_URL=http://localhost:8002
```

---

## Implementation Files Reference

- `src/services/goal-service.ts` - Goals, Strategies, KPI linking
- `src/services/action-service.ts` - Actions wrapper
- `src/services/issue-service.ts` - Issues wrapper
- `src/services/operations-traction-service.ts` - Core Operations API
- `src/services/kpi-planning-service.ts` - KPI Planning
- `src/services/traction.ts` - Axios instance with interceptors

---

## Version History

**v3.0 (2025-11-10)**

- Complete audit of all frontend API calls
- Added 61 documented endpoints
- Comprehensive request/response examples
- Data transformation notes
- Cache invalidation strategy

**v2.0 (Previous)**

- Initial comprehensive documentation
- 45+ endpoints documented

---

**End of Specification**

For questions or clarifications, refer to the implementation files or contact the development team.
