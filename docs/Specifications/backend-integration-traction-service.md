# Traction Service Backend Integration Specifications

**Version:** 3.0  
**Service Base URL:** `{REACT_APP_TRACTION_API_URL}`  
**Default (Localhost):** `http://localhost:8002`  
**Dev Environment:** `https://api.dev.purposepath.app/traction/api/v1`

[← Back to Index](./backend-integration-index.md)

## Overview

The Traction Service handles operational data: goals, strategies, KPIs, actions, issues, activity feeds, reports, and real-time updates via SSE.

### Frontend Implementation
- **Primary Client:** `traction` (axios instance in `src/services/traction.ts`)
- **Key Files:** `goal-service.ts`, `action-service.ts`, `issue-service.ts`, `kpi-planning-service.ts`, `realtime.ts`

---

## Goals Management

### GET /goals
List goals with filtering. **Implementation:** `goal-service.ts` → `getGoals()`

**Query Params:** page, size, sort, ownerId, status, valueTag, horizon, search

**Response:** Array of Goal objects with pagination

### POST /goals
Create new goal. **Implementation:** `goal-service.ts` → `createGoal()`

**Request:** `{title, intent?, owner_id, horizon, value_tags[], status?}`

### GET /goals/{id}
Get detailed goal. **Implementation:** `goal-service.ts` → `getGoalById()`

**Response:** Goal with strategies[], kpis[], progress, metadata

### PUT /goals/{id}
Update goal. **Implementation:** `goal-service.ts` → `updateGoal()`

### DELETE /goals/{id}
Delete goal (soft delete). **Implementation:** `goal-service.ts` → `deleteGoal()`

### POST /goals/{id}:activate
Activate a goal (transition from draft or paused to active). **Implementation:** `goal-service.ts` → `activateGoal()`

**Request:**
```json
{
  "reason": "Ready to begin Q1 execution"  // Optional
}
```

**Response:** Updated Goal object with `status: "active"`

**Status Transition:**
- `draft` → `active` (starting the goal)
- `paused` → `active` (resuming the goal)

**Business Rules:**
- Can only activate from `draft` or `paused` status
- If `reason` is provided, an activity entry is created with context-aware title ("Goal Started" for draft→active, "Goal Resumed" for paused→active)
- Activity text format: "Goal started: {reason}" or "Goal resumed: {reason}"

**Validation:**
- Returns 400 if goal cannot be activated from current status (e.g., "Cannot activate goal in Completed status")
- Returns 404 if goal not found

### POST /goals/{id}:pause
Pause an active goal (put on hold). **Implementation:** `goal-service.ts` → `pauseGoal()`

**Request:**
```json
{
  "reason": "Waiting for Q2 budget approval"  // Optional
}
```

**Response:** Updated Goal object with `status: "paused"`

**Status Transition:**
- `active` → `paused`

**Business Rules:**
- Can only pause from `active` status
- If `reason` is provided, an activity entry is created with title "Goal Paused"
- Activity text format: "Goal paused: {reason}"

**Validation:**
- Returns 400 if goal is not `active` (e.g., "Cannot put goal on hold from Completed status")
- Returns 404 if goal not found

### POST /goals/{id}:close
Close/complete a goal. **Implementation:** `goal-service.ts` → `closeGoal()`

**Request:**
```json
{
  "finalStatus": "completed",  // Required: "completed" or "cancelled"
  "reason": "All KPIs achieved"  // Optional
}
```

**Response:** Updated Goal object with `status: "completed"` or `"cancelled"`

**Status Transitions:**
- When `finalStatus: "completed"`:
  - `active` → `completed` (ONLY from active status)
  - Sets `completedAt` timestamp
- When `finalStatus: "cancelled"`:
  - ANY status (except `completed`) → `cancelled`
  - Can cancel from `draft`, `active`, `paused`, or `archived`

**Business Rules:**
- `finalStatus` parameter is **required** to distinguish between successful completion vs abandonment
- If `reason` is provided, an activity entry is created
- Activity text format: "Goal completed: {reason}" or "Goal cancelled: {reason}"
- Cannot cancel a goal that is already `completed`

**Validation:**
- Returns 400 if `finalStatus` is not "completed" or "cancelled"
- Returns 400 if `finalStatus: "completed"` and goal is not `active` (e.g., "Cannot complete goal in Draft status")
- Returns 400 if `finalStatus: "cancelled"` and goal is already `completed` (e.g., "Cannot cancel completed goal")
- Returns 404 if goal not found

**Breaking Change Note:** Enhanced from previous implementation that only accepted `reason` field. Now requires `finalStatus` parameter to properly distinguish between completion and cancellation.

---

## Strategy Management

### POST /goals/{goalId}/strategies
Create strategy. **Implementation:** `goal-service.ts` → `createStrategy()`

**Request:** `{description, status: "draft|validated|adopted", order}`

### PUT /goals/{goalId}/strategies/{strategyId}
Update strategy. **Implementation:** `goal-service.ts` → `updateStrategy()`

### DELETE /goals/{goalId}/strategies/{strategyId}
Delete strategy. **Implementation:** `goal-service.ts` → `deleteStrategy()`

### PUT /goals/{goalId}/strategies:reorder
Reorder strategies. **Implementation:** `goal-service.ts` → `reorderStrategies()`

**Request:** `{strategyIds: ["id1", "id2"]}`

---

## KPI Management

### GET /kpis
List shared KPIs (catalog). **Implementation:** `kpi-planning-service.ts` → `getSharedKPIs()`

**Query Params:** page, size, search, category, ownerId

### POST /kpis
Create shared KPI. **Implementation:** `kpi-planning-service.ts` → `createSharedKPI()`

**Request:** `{name, description, category, unit, direction: "up|down", formula?, isShared}`

### GET /kpis/{id}
Get KPI details with readings. **Implementation:** `kpi-progress-service.ts` → `getKPIById()`

**Response:** May return KPI alone or `{kpi, readings[]}`

### GET /kpis/{id}/readings
Get KPI readings. **Implementation:** `kpi-progress-service.ts` → `getKPIReadings()`

**Query Params:** page, size, startDate, endDate

### POST /kpis/{id}/readings
Create KPI reading. **Implementation:** `kpi-progress-service.ts` → `createKPIReading()`

**Request:** `{period: "YYYY-MM", value, adjustedValue?, reason?}`

---

## KPI-Goal Linkage

### POST /goals/{goalId}/kpis:link
Link KPI to goal. **Implementation:** `goal-service.ts` → `attachKPI()`

**Request:** `{kpi_id, threshold_pct}`

### POST /goals/{goalId}/kpis:unlink
Unlink KPI. **Implementation:** `goal-service.ts` → `detachKPI()`

**Request:** `{kpi_id}`

### POST /goals/{goalId}/kpis/{kpiId}:setThreshold
Update threshold. **Implementation:** `goal-service.ts` → `updateKPIThreshold()`

**Request:** `{threshold_pct}`

### GET /goals/{goalId}/kpis/{kpiId}:link
Get linkage details. **Implementation:** `goal-service.ts` → `getKPILinkage()`

---

## Goal Activity

### GET /goals/{id}/activity
Get activity feed. **Implementation:** `activity.ts` → `getGoalActivity()`

**Query Params:** page, size, type

**Response:** Array of activity entries (weekly_review, note, system, decision, attachment)

### POST /goals/{id}/activity
Create activity entry. **Implementation:** `activity.ts` → `createGoalActivity()`

**Request:** `{type, text, title?, url?, metadata?}`

### POST /goals/{id}/notes
Add note (convenience). **Implementation:** `activity.ts` → `addGoalNote()`

**Request:** `{note, attachments[]?}`

---

## Operations: Actions

### GET /api/operations/actions
List actions. **Implementation:** `action-service.ts` → `getActions()`

**Query Params:** startDate, endDate, assignedPersonId, goalIds, strategyIds, issueIds, status, priority

**Response:** Array of Action objects

### POST /api/operations/actions
Create action. **Implementation:** `action-service.ts` → `createAction()`

**Request:** `{title, description, startDate, dueDate, priority, assignedPersonId, connections: {goalIds[], strategyIds[], issueIds[]}}`

### PUT /api/operations/actions/{actionId}
Update action. **Implementation:** `action-service.ts` → `updateAction()`

### DELETE /api/operations/actions/{actionId}
Delete action. **Implementation:** `action-service.ts` → `deleteAction()`

---

## Operations: Issues

### GET /api/operations/issues
List issues. **Implementation:** `issue-service.ts` → `getIssues()`

**Query Params:** 
- `status` (string) - Filter by status
- `priority` (string) - Filter by priority  
- `businessImpact` (string) - Filter by impact level
- `reportedBy` (string) - Filter by reporter ID
- `assignedTo` (string) - Filter by assignee ID
- `typeConfigId` (string) - Filter by issue type configuration ID
- `search` (string) - Search in title/description
- `page` (number) - Page number for pagination
- `size` (number) - Items per page

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "issue_123abc",
      "title": "Hire senior developer",
      "description": "Need experienced developer for project X",
      "typeConfigId": "uuid",
      "statusConfigId": "uuid",
      "impact": "high",
      "priority": "critical",
      "reporterId": "user_123",
      "reporterName": "John Doe",
      "assignedPersonId": "user_456",
      "assignedPersonName": "Jane Smith",
      "dueDate": "2025-02-15T00:00:00Z",
      "estimatedHours": 40.0,
      "actualHours": 25.5,
      "tags": ["hiring", "urgent"],
      "displayOrder": 1,
      "connections": {
        "goalIds": ["goal_123"],
        "strategyIds": ["strategy_456"],
        "actionIds": ["action_789"]
      },
      "rootCauseAnalysis": "Expansion requirements",
      "resolutionNotes": null,
      "createdAt": "2025-01-15T10:00:00Z",
      "updatedAt": "2025-01-20T14:30:00Z",
      "createdBy": "user_123",
      "updatedBy": "user_123"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 20,
    "total": 45,
    "totalPages": 3
  }
}
```

### POST /api/operations/issues
Create issue. **Implementation:** `issue-service.ts` → `createIssue()`

**Request:** 
```json
{
  "title": "Hire senior developer",
  "description": "Need experienced developer for project X",
  "typeConfigId": "uuid",
  "reportedBy": "user_123",
  "businessImpact": "high",
  "priority": "critical",
  "statusId": "uuid",
  "assignedPersonId": "user_456",
  "dueDate": "2025-02-15T00:00:00Z",
  "estimatedHours": 40.0,
  "tags": ["hiring", "urgent"],
  "connections": {
    "goalIds": ["goal_123"],
    "strategyIds": ["strategy_456"]
  }
}
```

**Response:** Single issue object (same structure as GET response item)

### GET /api/operations/issues/{issueId}
Get single issue. **Implementation:** `issue-service.ts` → `getIssueById()`

**Response:** Single issue object (same structure as GET list response item)

### PUT /api/operations/issues/{issueId}
Update issue. **Implementation:** `issue-service.ts` → `updateIssue()`

**Request:** Same structure as POST (all fields optional except those being updated)

**Response:** Updated issue object

### DELETE /api/operations/issues/{issueId}
Delete issue. **Implementation:** `issue-service.ts` → `deleteIssue()`

**Response:**
```json
{
  "success": true,
  "deletedIssueId": "issue_123abc",
  "deletedAt": "2025-01-20T15:00:00Z"
}
```

---

## Issue Configuration: Types

Issue types define categories for business issues (e.g., Personnel, Financial, Process). Tenants can use SYSTEM types or create custom types.

### GET /api/operations/issue-types
List active issue types. **Implementation:** `issue-service.ts` → `getIssueTypes()`

**Query Params:** 
- `includeInactive` (boolean, default: false) - Include inactive types
- `includeSystem` (boolean, default: true) - Include SYSTEM types

**Response:** 
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Personnel",
      "description": "People-related issues",
      "color": "#FF6B6B",
      "icon": "users",
      "order": 1,
      "isActive": true,
      "isSystemType": true,
      "isDefault": false,
      "createdAt": "2025-01-15T10:00:00Z",
      "updatedAt": null
    }
  ]
}
```

**SYSTEM Types** (provided by default):
- Personnel (People-related issues)
- Financial (Budget, revenue, cost issues)
- Process (Workflow, operational issues)
- Legal (Compliance, legal issues)
- Customer (Customer-related issues)
- Technical (Technology, infrastructure issues)
- General (Miscellaneous issues)

### POST /api/operations/issue-types
Create custom issue type. **Implementation:** `issue-service.ts` → `createIssueType()`

**Request:**
```json
{
  "name": "Marketing",
  "description": "Marketing and branding issues",
  "color": "#4ECDC4",
  "icon": "bullhorn",
  "order": 8,
  "isDefault": false
}
```

**Response:** Created IssueType object

**Validation:**
- `name`: Required, max 100 chars, unique per tenant
- `color`: Optional, hex color format (e.g., #FF6B6B)
- `icon`: Optional, string identifier
- `order`: Optional, positive integer
- `isDefault`: Optional, boolean (default: false). Only one type can be default per tenant.

### PUT /api/operations/issue-types/{typeId}
Update custom issue type. **Implementation:** `issue-service.ts` → `updateIssueType()`

**Request:**
```json
{
  "name": "Marketing & Sales",
  "description": "Updated description",
  "color": "#4ECDC4",
  "icon": "chart-line",
  "order": 5,
  "isDefault": true
}
```

**Notes:**
- Cannot modify SYSTEM types (isSystemType = true)
- All fields optional; only provided fields are updated
- Setting `isDefault: true` will unset any previous default type

### DELETE /api/operations/issue-types/{typeId}
Soft-delete custom issue type (sets isActive = false). **Implementation:** `issue-service.ts` → `deleteIssueType()`

**Notes:**
- Cannot delete SYSTEM types
- Cannot delete if issues exist with this type (must reassign first)
- Soft delete only (preserves data integrity)

### POST /api/operations/issue-types/{typeId}:activate
Reactivate a previously deleted issue type. **Implementation:** `issue-service.ts` → `activateIssueType()`

**Response:** Updated IssueType with `isActive: true`

---

## Issue Configuration: Statuses

Issue statuses define the workflow states (e.g., Open, In Progress, Resolved, Closed). Tenants can use SYSTEM statuses or create custom ones.

### GET /api/operations/issue-statuses
List active issue statuses. **Implementation:** `issue-service.ts` → `getIssueStatuses()`

**Query Params:**
- `category` (string) - Filter by category: "open" | "active" | "inactive" | "closed"
- `includeInactive` (boolean, default: false) - Include inactive statuses
- `includeSystem` (boolean, default: true) - Include SYSTEM statuses

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Open",
      "description": "Issue reported, not yet started",
      "category": "open",
      "color": "#3498db",
      "icon": "inbox",
      "order": 1,
      "isActive": true,
      "isSystemStatus": true,
      "createdAt": "2025-01-15T10:00:00Z",
      "updatedAt": null
    }
  ]
}
```

**SYSTEM Statuses** (provided by default):

**Open Category:**
- Open (Issue reported, awaiting triage)
- Backlog (Acknowledged, queued for future work)

**Active Category:**
- In Progress (Currently being worked on)
- In Review (Work completed, under review)
- Blocked (Work paused due to dependencies)

**Inactive Category:**
- On Hold (Temporarily paused)
- Deferred (Postponed to later date)

**Closed Category:**
- Resolved (Issue fixed/completed)
- Closed (Issue no longer relevant)
- Duplicate (Duplicate of another issue)
- Won't Fix (Decided not to address)

### POST /api/operations/issue-statuses
Create custom issue status. **Implementation:** `issue-service.ts` → `createIssueStatus()`

**Request:**
```json
{
  "name": "Pending Approval",
  "description": "Awaiting management approval",
  "category": "active",
  "color": "#F39C12",
  "icon": "clock",
  "order": 4
}
```

**Response:** Created IssueStatus object

**Validation:**
- `name`: Required, max 100 chars, unique per tenant
- `category`: Required, one of: "open" | "active" | "inactive" | "closed"
- `color`: Optional, hex color format
- `icon`: Optional, string identifier
- `order`: Optional, positive integer (controls display order)

### PUT /api/operations/issue-statuses/{statusId}
Update custom issue status. **Implementation:** `issue-service.ts` → `updateIssueStatus()`

**Request:**
```json
{
  "name": "Pending Review",
  "description": "Updated description",
  "color": "#E67E22",
  "icon": "eye",
  "order": 3
}
```

**Notes:**
- Cannot modify SYSTEM statuses (isSystemStatus = true)
- Cannot change `category` after creation (data integrity)
- All fields optional except for category restriction

### DELETE /api/operations/issue-statuses/{statusId}
Soft-delete custom issue status. **Implementation:** `issue-service.ts` → `deleteIssueStatus()`

**Notes:**
- Cannot delete SYSTEM statuses
- Cannot delete if issues exist with this status (must reassign first)
- Soft delete only (sets isActive = false)

### POST /api/operations/issue-statuses/{statusId}:activate
Reactivate a previously deleted issue status. **Implementation:** `issue-service.ts` → `activateIssueStatus()`

**Response:** Updated IssueStatus with `isActive: true`

### PUT /api/operations/issue-statuses:reorder
Reorder issue statuses within a category. **Implementation:** `issue-service.ts` → `reorderIssueStatuses()`

**Request:**
```json
{
  "category": "active",
  "statusIds": ["uuid1", "uuid2", "uuid3"]
}
```

**Notes:**
- Updates `order` field for each status
- Only affects statuses within the specified category
- Array order determines new display order

---

## Relationship Management

### PUT /api/operations/actions/{actionId}/goals
Link action to goals. **Implementation:** `operations-traction-service.ts` → `linkActionToGoals()`

**Request:** `{goalIds: []}` (replaces existing)

### PUT /api/operations/actions/{actionId}/strategies
Link action to strategies. **Implementation:** `operations-traction-service.ts` → `linkActionToStrategies()`

**Request:** `{strategyIds: []}`

### DELETE /api/operations/actions/{actionId}/relationships
Clear all relationships. **Implementation:** `operations-traction-service.ts` → `clearActionRelationships()`

### POST /api/operations/kpi-updates
Create KPI update from action. **Implementation:** `operations-traction-service.ts` → `syncKPIUpdate()`

**Request:** `{actionId, kpiId, sharedKpiId, horizonId, newValue, updateDate, notes?}`

### POST /api/operations/actions/goals
Get related goals (batch). **Implementation:** `operations-traction-service.ts` → `getActionGoalRelationships()`

**Request:** `{actionIds: []}` → **Response:** Map of actionId to Goal[]

### POST /api/operations/actions/strategies
Get related strategies (batch). **Implementation:** `operations-traction-service.ts` → `getActionStrategyRelationships()`

**Request:** `{actionIds: []}`

### POST /api/operations/goals/kpis
Get related KPIs (batch). **Implementation:** `operations-traction-service.ts` → `getGoalKPIRelationships()`

**Request:** `{goalIds: []}`

---

## Reports

### GET /reports/company
Generate company report. **Implementation:** `reports.ts` → `generateReport()`

**Query Params:** format (pdf|docx), from (date), to (date)

**Response:** Binary blob (PDF/DOCX file)

---

## Real-time Updates (SSE)

### GET /realtime/goals/{goalId}/activity
Real-time goal activity via Server-Sent Events. **Implementation:** `realtime.ts` → `subscribeToGoalActivity()`

**Query Params:** 
- `access_token` - JWT token
- `tenant` - Tenant ID
- `lastEventId` - Last received event ID (reconnection)

**Event Types:**
- `activity.created` - New activity item
- `decision.created` - New decision recorded
- `attachment.created` - New attachment added
- `kpi.reading.created` - New KPI reading

**Event Data Format:**
```json
{
  "type": "activity.created",
  "goalId": "string",
  "activity": {
    "id": "string",
    "text": "string",
    "createdAt": "string",
    "title": "string?",
    "url": "string?"
  }
}
```

**Frontend Connection Management:**
- Auto-reconnect on disconnect
- Event deduplication using lastEventId
- Falls back to polling if SSE unavailable

### GET /realtime/tenants/{tenantId}
Tenant-wide real-time updates. **Status:** Defined but not yet implemented

---

## Analytics Endpoints

Dashboard and performance analytics endpoints for visualizing overall system health and team alignment.

### GET /goals/stats

Get aggregated statistics across all goals.

**Response:**

```json
{
  "success": true,
  "data": {
    "totalGoals": 15,
    "activeGoals": 12,
    "completedGoals": 3,
    "goalsByStatus": {
      "draft": 2,
      "active": 12,
      "completed": 3,
      "paused": 0,
      "cancelled": 0
    },
    "goalsByHorizon": {
      "year": 5,
      "quarter": 7,
      "month": 3
    },
    "averageProgress": 67.5
  }
}
```

**Frontend Usage:** Dashboard goal statistics widget

**Implementation:** `src/components/Dashboard.tsx` → `loadGoalStats()`

---

### GET /activity/recent

Get recent activity feed across all goals and operations.

**Query Parameters:**

- `size` - Number of recent items (default: 10, max: 50)

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "type": "goal_created|goal_updated|strategy_added|kpi_updated|action_completed",
      "userId": "string",
      "userName": "string",
      "entityId": "string",
      "entityType": "goal|strategy|kpi|action|issue",
      "entityTitle": "string",
      "description": "string",
      "timestamp": "2025-10-16T14:30:00Z"
    }
  ]
}
```

**Frontend Usage:** Dashboard recent activity feed

**Implementation:** `src/components/Dashboard.tsx` → `loadRecentActivity()`

---

### GET /performance/score

Get overall performance score across goals, strategies, KPIs, and actions.

**Response:**

```json
{
  "success": true,
  "data": {
    "overallScore": 78.5,
    "components": {
      "goals": {
        "score": 75.0,
        "weight": 0.4,
        "metrics": {
          "completionRate": 80.0,
          "onTimeRate": 70.0
        }
      },
      "strategies": {
        "score": 82.0,
        "weight": 0.2,
        "metrics": {
          "validatedRate": 85.0,
          "adoptionRate": 79.0
        }
      },
      "kpis": {
        "score": 76.0,
        "weight": 0.3,
        "metrics": {
          "targetAchievementRate": 72.0,
          "onTrackRate": 80.0
        }
      },
      "actions": {
        "score": 81.0,
        "weight": 0.1,
        "metrics": {
          "completionRate": 85.0,
          "onTimeRate": 77.0
        }
      }
    },
    "trend": "improving|stable|declining",
    "lastCalculated": "2025-10-16T14:30:00Z"
  }
}
```

**Frontend Usage:** Dashboard performance score widget

**Notes:**
- Overall score calculated from weighted component scores
- Score range: 0-100
- Recalculated periodically by backend

**Implementation:** `src/components/Dashboard.tsx` → `loadPerformanceScore()`

---

### GET /team/alignment

Get team alignment score and metrics.

**Response:**

```json
{
  "success": true,
  "data": {
    "alignmentScore": 85.0,
    "teamSize": 12,
    "goalsWithMultipleOwners": 8,
    "sharedKPIs": 15,
    "collaborationMetrics": {
      "crossGoalCollaboration": 72.0,
      "strategyAlignment": 88.0,
      "kpiSharing": 65.0
    },
    "trend": "improving|stable|declining",
    "lastCalculated": "2025-10-16T14:30:00Z"
  }
}
```

**Frontend Usage:** Dashboard team alignment widget

**Notes:**
- Alignment score based on goal/strategy/KPI relationships
- Higher score indicates better team coordination
- Score range: 0-100

**Implementation:** `src/components/Dashboard.tsx` → `loadTeamAlignment()`

---

## Data Models

### Goal
```typescript
{
  id: string;
  title: string;
  intent: string;
  ownerId: string;
  ownerName: string;
  horizon: "year"|"quarter"|"month";
  status: "draft"|"active"|"completed"|"paused"|"cancelled";
  valueTags: string[];
  strategies: Strategy[];
  kpis: GoalKPI[];
  progress: number;
  metadata: object;
  createdAt: string;
  updatedAt: string;
}
```

### Strategy
```typescript
{
  id: string;
  goalId: string;
  description: string;
  status: "draft"|"validated"|"adopted";
  order: number;
  createdAt: string;
}
```

### GoalKPI
```typescript
{
  id: string;
  goalId: string;
  sharedKpiId: string;
  name: string;
  description: string;
  category: string;
  unit: string;
  direction: "up"|"down";
  threshold: number;
  currentValue: number;
  targetValue: number;
  progress: number;
}
```

### Action
```typescript
{
  id: string;
  title: string;
  description: string;
  startDate: string;
  dueDate: string;
  priority: "low"|"medium"|"high"|"critical";
  status: "not_started"|"in_progress"|"completed"|"blocked"|"cancelled";
  assignedPersonId: string;
  assignedPersonName: string;
  progress: number;
  connections: {
    goalIds: string[];
    strategyIds: string[];
    issueIds: string[];
  };
  createdAt: string;
  updatedAt: string;
}
```

### Issue
```typescript
{
  id: string;
  title: string;
  description: string;
  reportedBy: string;
  reportedByName: string;
  businessImpact: "low"|"medium"|"high"|"critical";
  priority: number;
  status: IssueStatus;
  rootCauseAnalysis?: {
    method: "five_whys"|"fishbone"|"swot"|"pareto";
    findings: object;
  };
  createdAt: string;
  updatedAt: string;
}
```

---

## Error Responses

Standard error format:
```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes
- `GOAL_NOT_FOUND` - Goal does not exist
- `INSUFFICIENT_PERMISSIONS` - User lacks access
- `GOAL_LIMIT_REACHED` - Subscription limit exceeded
- `INVALID_STATUS_TRANSITION` - Invalid status change
- `DEPENDENCY_EXISTS` - Cannot delete (dependencies exist)

---

**Navigation:**
- [← Back to Index](./backend-integration-index.md)
- [← Coaching Service](./backend-integration-coaching-service.md)
- [Common Patterns →](./backend-integration-common-patterns.md)
