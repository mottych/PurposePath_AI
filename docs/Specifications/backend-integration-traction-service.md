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

### POST /goals/{id}:close
Close/complete goal. **Implementation:** `goal-service.ts` → `closeGoal()`

**Request:** `{reason?, finalStatus: "completed|cancelled"}`

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

**Query Params:** status, priority, businessImpact, reportedBy, assignedTo, search

### POST /api/operations/issues
Create issue. **Implementation:** `issue-service.ts` → `createIssue()`

**Request:** `{title, description, reportedBy, businessImpact: "low|medium|high|critical", priority, statusId?}`

### PUT /api/operations/issues/{issueId}
Update issue. **Implementation:** `issue-service.ts` → `updateIssue()`

### DELETE /api/operations/issues/{issueId}
Delete issue. **Implementation:** `issue-service.ts` → `deleteIssue()`

### GET /api/operations/issue-statuses
Get issue statuses. **Implementation:** `issue-service.ts` → `getIssueStatuses()`

**Response:** Array of IssueStatus `{id, name, category: "open|active|inactive|closed", color, order}`

### POST /api/operations/issue-statuses
Create custom status.

### PUT /api/operations/issue-statuses/{statusId}
Update status.

### DELETE /api/operations/issue-statuses/{statusId}
Delete status.

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
