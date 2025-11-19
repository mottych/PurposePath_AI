# Traction Service Backend Integration Specifications (v2 - Frontend Implementation)

**Version:** 2.1 - Corrected Field Naming Convention  
**Service Base URL:** `{REACT_APP_TRACTION_API_URL}`  
**Default (Localhost):** `http://localhost:8002`  
**Dev Environment:** `https://api.dev.purposepath.app/traction/api/v1`

[← Back to Index](./backend-integration-index.md)

## Overview

This document reflects the **ACTUAL** backend API implementation and field naming conventions.

**Important Notes:**

- Routes do NOT include `/api` prefix - the base URL already contains the full path
- Base URL format: `{BASE_URL}/traction/api/v1`
- All routes are relative (e.g., `/goals`, not `/api/goals`)
- **Field Naming Convention:** API uses **snake_case** for all JSON fields (e.g., `owner_id`, `created_at`, `alignment_score`)
- Backend uses `JsonSnakeCaseNamingPolicy` to convert C# PascalCase properties to snake_case JSON

### Frontend Implementation

- **Primary Client:** `traction` (axios instance in `src/services/traction.ts`)
- **Key Files:** `goal-service.ts`, `operations-traction-service.ts`, `issue-service.ts`, `action-service.ts`, `kpi-planning-service.ts`

---

## Type Definitions

### Enums and Constants

**GoalStatus:**

```typescript
type GoalStatus = 'draft' | 'active' | 'completed' | 'paused' | 'cancelled' | 'archived';
```

**StrategyStatus:**

```typescript
type StrategyStatus = 'draft' | 'validated' | 'adopted';
```

**ActionStatus:**

```typescript
type ActionStatus = 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
```

**ActionPriority:**

```typescript
type ActionPriority = 'low' | 'medium' | 'high' | 'critical';
```

**IssueImpact:**

```typescript
type IssueImpact = 'low' | 'medium' | 'high' | 'critical';
```

**IssuePriority:**

```typescript
type IssuePriority = 'low' | 'medium' | 'high' | 'critical';
```

**IssueStatusCategory:**

```typescript
type IssueStatusCategory = 'open' | 'active' | 'inactive' | 'closed';
```

---

## Goals Management

### POST /goals

Create new goal. **Implementation:** `goal-service.ts:125`

**Request:**

```json
{
  "title": "Increase Revenue",
  "intent": "We want to increase monthly recurring revenue to support expansion",
  "description": "Additional context about the goal",
  "owner_id": "user_abc123"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "goal_abc123",
    "title": "Increase Revenue",
    "intent": "We want to increase monthly recurring revenue to support expansion",
    "description": "Additional context about the goal",
    "status": "draft",
    "owner_id": "user_abc123",
    "alignment_score": 0,
    "alignment_explanation": "",
    "alignment_suggestions": [],
    "strategies": [],
    "kpis": [],
    "created_at": "2025-11-02T23:00:00Z",
    "updated_at": "2025-11-02T23:00:00Z"
  }
}
```

---

### GET /goals

List all goals. **Implementation:** `goal-service.ts:215`

**Query Params:** `ownerId` (optional)

**Response:**

```json
{
  "success": true,
  "data": [/* array of Goal objects */]
}
```

---

### GET /goals/{id}

Get goal details. **Implementation:** `goal-service.ts:150`

**Response:** Same as POST /goals response

---

### PUT /goals/{id}

Update goal. **Implementation:** `goal-service.ts:187`

**Request:** (all fields optional)

```json
{
  "title": "Updated title",
  "intent": "Updated intent",
  "description": "Updated description",
  "status": "active"
}
```

**Response:** Updated Goal object

---

### DELETE /goals/{id}

Delete goal. **Implementation:** `goal-service.ts:255`

**Response:**

```json
{
  "success": true
}
```

---

### POST /goals/{id}:activate

Activate goal (draft/paused → active). **Implementation:** `goal-service.ts:525`

**Request:**

```json
{
  "reason": "Ready to begin Q1 execution"
}
```

**Response:** Updated Goal with status="active"

---

### POST /goals/{id}:pause

Pause goal (active → paused). **Implementation:** `goal-service.ts:566`

**Request:**

```json
{
  "reason": "Waiting for Q2 budget approval"
}
```

**Response:** Updated Goal with status="paused"

---

### POST /goals/{id}:close

Close goal. **Implementation:** `goal-service.ts:609`

**Request:**

```json
{
  "finalStatus": "completed",
  "reason": "All KPIs achieved"
}
```

**Valid finalStatus:** "completed" | "cancelled"

**Response:** Updated Goal with final status

---

## Strategy Management

### POST /goals/{goalId}/strategies

Create strategy. **Implementation:** `goal-service.ts:284`

**Request:**

```json
{
  "description": "Launch targeted marketing campaign in Q1",
  "order": 1,
  "aiGenerated": false
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "strategy_abc123",
    "goalId": "goal_abc123",
    "description": "Launch targeted marketing campaign in Q1",
    "order": 1,
    "aiGenerated": false,
    "status": "draft",
    "validationScore": null,
    "validationFeedback": null,
    "createdAt": "2025-11-02T23:00:00Z",
    "updatedAt": "2025-11-02T23:00:00Z"
  }
}
```

---

### PUT /goals/{goalId}/strategies/{strategyId}

Update strategy. **Implementation:** `goal-service.ts:311`

**Request:** (all fields optional)

```json
{
  "description": "Updated strategy description",
  "order": 2,
  "status": "validated"
}
```

---

### DELETE /goals/{goalId}/strategies/{strategyId}

Delete strategy. **Implementation:** `goal-service.ts:342`

---

### PUT /goals/{goalId}/strategies:reorder

Reorder strategies. **Implementation:** `goal-service.ts:372`

**Request:**

```json
{
  "goalId": "goal_abc123",
  "strategyOrders": [
    {"strategyId": "strategy_1", "newOrder": 1},
    {"strategyId": "strategy_2", "newOrder": 2}
  ]
}
```

---

## KPI Management

### POST /goals/{goalId}/kpis:link

Link KPI to goal. **Implementation:** `goal-service.ts:401`

**Request:**

```json
{
  "kpiId": "kpi_abc123",
  "thresholdPct": 80
}
```

---

### POST /goals/{goalId}/kpis:unlink

Unlink KPI. **Implementation:** `goal-service.ts:427`

**Request:**

```json
{
  "kpiId": "kpi_abc123"
}
```

---

### POST /goals/{goalId}/kpis/{kpiId}:setThreshold

Update threshold. **Implementation:** `goal-service.ts:460`

**Request:**

```json
{
  "thresholdPct": 85
}
```

---

### GET /goals/{goalId}/kpis/{kpiId}:link

Get linkage info. **Implementation:** `goal-service.ts:491`

**Response:**

```json
{
  "success": true,
  "data": {
    "thresholdPct": 80
  }
}
```

---

## Operations: Actions

### GET /operations/actions

List actions. **Implementation:** `operations-traction-service.ts:64`

**Query Params:** startDate, endDate, assignedPersonId, goalIds, strategyIds, issueIds, status, priority

**Response:** Array of Action objects

---

### POST /operations/actions

Create action. **Implementation:** `operations-traction-service.ts:110`

**Request:**

```json
{
  "title": "Launch marketing campaign",
  "description": "Execute social media strategy",
  "dateEntered": "2025-11-01T10:00:00Z",
  "startDate": "2025-11-05T00:00:00Z",
  "dueDate": "2025-11-30T00:00:00Z",
  "priority": "high",
  "assignedPersonId": "user_123",
  "connections": {
    "goalIds": ["goal_123"],
    "strategyIds": ["strategy_456"],
    "issueIds": []
  }
}
```

**Response:** Created Action object

---

### PUT /operations/actions/{actionId}

Update action. **Implementation:** `operations-traction-service.ts:132`

**Request:** (all fields optional)

---

### DELETE /operations/actions/{actionId}

Delete action. **Implementation:** `operations-traction-service.ts:163`

---

## Operations: Issues

### GET /issues

List issues. **Implementation:** `operations-traction-service.ts:185`

**Query Params:** startDate, endDate, reportedBy, businessImpact, priority, status

**Response:** Array of Issue objects

---

### POST /issues

Create issue. **Implementation:** `operations-traction-service.ts:223`

**Request:**

```json
{
  "title": "Hire senior developer",
  "description": "Need experienced developer for project X",
  "typeConfigId": "type_uuid",
  "reportedBy": "user_123",
  "businessImpact": "high",
  "priority": "critical",
  "statusId": "status_uuid",
  "assignedPersonId": "user_456",
  "dueDate": "2025-12-15T00:00:00Z",
  "estimatedHours": 40.0,
  "tags": ["hiring", "urgent"],
  "dateReported": "2025-11-01T10:00:00Z",
  "connections": {
    "goalIds": ["goal_123"],
    "strategyIds": ["strategy_456"]
  }
}
```

**Response:** Created Issue object

---

### PUT /issues/{issueId}

Update issue. **Implementation:** `operations-traction-service.ts:239`

**Request:** (all fields optional)

---

### DELETE /issues/{issueId}

Delete issue. **Implementation:** `operations-traction-service.ts:254`

---

## Issue Configuration

### GET /operations/issue-types

List issue types. **Implementation:** `operations-traction-service.ts:366`

**Query Params:** includeInactive, includeSystem

---

### POST /operations/issue-types

Create issue type. **Implementation:** `operations-traction-service.ts:379`

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

---

### PUT /operations/issue-types/{typeId}

Update issue type. **Implementation:** `operations-traction-service.ts:389`

---

### DELETE /operations/issue-types/{typeId}

Delete issue type. **Implementation:** `operations-traction-service.ts:403`

---

### POST /operations/issue-types/{typeId}:activate

Activate issue type. **Implementation:** `operations-traction-service.ts:412`

---

### GET /operations/issue-statuses

List statuses. **Implementation:** `operations-traction-service.ts:426`

**Query Params:** category, includeInactive, includeSystem

---

### POST /operations/issue-statuses

Create status. **Implementation:** `operations-traction-service.ts:436`

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

---

### PUT /operations/issue-statuses/{statusId}

Update status. **Implementation:** `operations-traction-service.ts:446`

---

### DELETE /operations/issue-statuses/{statusId}

Delete status. **Implementation:** `operations-traction-service.ts:456`

---

### POST /operations/issue-statuses/{statusId}:activate

Activate status. **Implementation:** `operations-traction-service.ts:465`

---

### PUT /operations/issue-statuses:reorder

Reorder statuses. **Implementation:** `operations-traction-service.ts:475`

**Request:**

```json
{
  "category": "active",
  "statusIds": ["uuid1", "uuid2", "uuid3"]
}
```

---

## Issue Lifecycle

### POST /issues/{issueId}/root-cause

Create root cause analysis. **Implementation:** `issue-service.ts:185`

---

### POST /issues/{issueId}/convert-to-actions

Convert issue to actions. **Implementation:** `issue-service.ts:204`

**Request:**

```json
{
  "actions": [/* CreateActionRequest array */],
  "newStatusId": "status_uuid"
}
```

**Response:** Array of created action IDs

---

### GET /issues/{issueId}/closure-eligibility

Check closure eligibility. **Implementation:** `issue-service.ts:229`

**Response:**

```json
{
  "canClose": true,
  "completedActions": 5,
  "totalActions": 6
}
```

---

### POST /issues/{issueId}/close

Close issue. **Implementation:** `issue-service.ts:244`

---

## KPI Planning Endpoints

### GET /shared-kpis/{sharedKpiId}/milestones

Get KPI milestones. **Implementation:** `kpi-planning-service.ts:22`

---

### PUT /shared-kpis/{sharedKpiId}/milestones

Update milestones. **Implementation:** `kpi-planning-service.ts:55`

**Request:**

```json
{
  "milestones": [/* array of milestones */],
  "replaceAll": true
}
```

---

### GET /shared-kpis/{sharedKpiId}/plan

Get KPI plan. **Implementation:** `kpi-planning-service.ts:99`

**Query Params:** granularity

---

### GET /goals/{goalId}/kpi-planning

Get goal KPI planning. **Implementation:** `kpi-planning-service.ts:140`

---

### POST /shared-kpis/{sharedKpiId}/actuals

Record actual value. **Implementation:** `kpi-planning-service.ts:174`

---

### POST /shared-kpis/{sharedKpiId}/adjust

Adjust KPI plan. **Implementation:** `kpi-planning-service.ts:208`

---

### GET /kpis/{kpiId}/cross-goal-impact

Get cross-goal impact. **Implementation:** `kpi-planning-service.ts:241`

---

### GET /cross-goal-alerts

Get cross-goal alerts. **Implementation:** `kpi-planning-service.ts:263`

---

### GET /shared-kpis/{sharedKpiId}/replan-rule

Get replan rule. **Implementation:** `kpi-planning-service.ts:311`

---

### PUT /shared-kpis/{sharedKpiId}/replan-rule

Update replan rule. **Implementation:** `kpi-planning-service.ts:331`

---

### GET /goals/{goalId}/available-kpis

Get available KPIs for goal. **Implementation:** `kpi-planning-service.ts:355`

---

## Additional Endpoints

### POST /alignment/check

Calculate alignment. **Implementation:** `goal-service.ts:655`

---

### POST /api/actions/{actionId}/kpi-updates

Update action KPIs. **Implementation:** `action-service.ts:163`

---

**Navigation:**

- [← Back to Index](./backend-integration-index.md)
- [Original Spec (v1)](./backend-integration-traction-service.md)
