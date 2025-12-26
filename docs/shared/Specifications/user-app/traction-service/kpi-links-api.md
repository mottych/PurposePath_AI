# KPI Links API Specification

**Version:** 8.0  
**Last Updated:** December 26, 2025  
**Base Path:** `/kpi-links`  
**Controller:** `KpiLinksController.cs`

## Overview

The KPI Links API manages relationships between KPIs and entities (persons, goals, strategies). Every KPI link requires a person (owner/responsible party) and can optionally be associated with a goal and/or strategy.

### Key Features
- Link KPIs to persons (required), with optional goal and strategy associations
- Configure thresholds, weights, and display order for each link
- Mark primary KPIs for goals
- Query KPI links with flexible filtering (by person, goal, strategy, or KPI)
- Update or remove links
- Automatic cascade delete when tenant-specific KPIs are deleted

### Design Philosophy
- **Unified resource-based API:** All KPI link operations through `/kpi-links` endpoints
- **Person-centric:** Every KPI link must have a person (owner)
- **Flexible filtering:** Query by any entity type (person, goal, strategy, KPI) with optional `includeAll` parameter
- **Derived linkType:** Link type is calculated based on foreign key presence (not persisted)
- **Multi-entity:** One KPI can be linked to multiple persons/goals/strategies simultaneously

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. Get KPI Link by ID

Retrieve details of a specific KPI link.

**Endpoint:** `GET /kpi-links/{linkId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | KPI link identifier |

#### Request Example

```http
GET /kpi-links/link-123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "link-123e4567-e89b-12d3-a456-426614174000",
    "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
    "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
    "thresholdPct": 80.0,
    "linkType": "strategy",
    "weight": 1.5,
    "displayOrder": 1,
    "isPrimary": true,
    "linkedAt": "2025-12-20T10:00:00Z"
  },
  "error": null
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (GUID) | Unique link identifier |
| `kpiId` | string (GUID) | KPI being linked |
| `personId` | string (GUID) | Person responsible (owner) - **Required** |
| `goalId` | string (GUID) | Goal linked to (nullable) |
| `strategyId` | string (GUID) | Strategy linked to (nullable) |
| `thresholdPct` | decimal | Completion threshold percentage (0-100) |
| `linkType` | string | **Calculated field** - Type of link: `"personal"` (only personId), `"goal"` (personId + goalId), `"strategy"` (personId + goalId + strategyId) |
| `weight` | decimal | Relative importance (for weighted calculations) |
| `displayOrder` | int | Sort order in UI (lower = first) |
| `isPrimary` | boolean | Is this the primary KPI for the goal? |
| `linkedAt` | datetime | When link was created |

#### Error Responses

**Status:** `400 Bad Request`
```json
{
  "success": false,
  "data": null,
  "error": "Invalid link ID format"
}
```

**Status:** `404 Not Found`
```json
{
  "success": false,
  "data": null,
  "error": "KPI link not found"
}
```

---

### 2. Create KPI Link

Create a new link between a KPI and person, optionally associating with a goal and/or strategy.

**Endpoint:** `POST /kpi-links`

#### Request Body

```json
{
  "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
  "personId": "person-789e1234-e89b-12d3-a456-426614174002",
  "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
  "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
  "thresholdPct": 85.0,
  "weight": 1.5,
  "displayOrder": 1,
  "isPrimary": false
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kpiId` | string (GUID) | **Yes** | KPI to link |
| `personId` | string (GUID) | **Yes** | Person responsible/owner |
| `goalId` | string (GUID) | No | Goal to associate (required if strategyId provided) |
| `strategyId` | string (GUID) | No | Strategy to associate (requires goalId) |
| `thresholdPct` | decimal | No | Threshold percentage (0-100, default: 80.0) |
| `weight` | decimal | No | Relative weight (default: 1.0) |
| `displayOrder` | int | No | Sort order (default: auto-assigned) |
| `isPrimary` | boolean | No | Mark as primary KPI (default: false) |

**Note:** `linkType` is NOT accepted in requests - it is automatically calculated based on provided fields.

#### Response

**Status:** `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "link-new-123",
    "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
    "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
    "thresholdPct": 85.0,
    "linkType": "strategy",
    "weight": 1.5,
    "displayOrder": 1,
    "isPrimary": false,
    "linkedAt": "2025-12-26T10:00:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Person Required:** PersonId must always be provided
- **Strategy Requires Goal:** If strategyId is provided, goalId must also be provided
- **Entity Validation:** All referenced entities (KPI, person, goal, strategy) must exist in tenant
- **Duplicate Prevention:** Cannot create duplicate links (same KPI + person + goal + strategy combination)
- **Auto linkType:** Calculated automatically: `personal` (no goal/strategy), `goal` (has goalId), `strategy` (has goalId + strategyId)
- **Primary KPI:** Setting isPrimary=true may unset other primary KPIs for the same goal

---

### 3. Update KPI Link

Update link configuration (threshold, weight, priority, etc.).

**Endpoint:** `PUT /kpi-links/{linkId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | KPI link identifier |

#### Request Body

```json
{
  "thresholdPct": 85.0,
  "weight": 2.0,
  "displayOrder": 1,
  "isPrimary": true
}
```

#### Request Fields

All fields are optional. Only provided fields will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `thresholdPct` | decimal | Threshold percentage (0-100) |
| `weight` | decimal | Relative weight/importance |
| `displayOrder` | int | Sort order in UI |
| `isPrimary` | boolean | Mark as primary KPI |

**Note:** 
- You cannot change `kpiId`, `goalId`, `personId`, or `strategyId` via update. Delete and recreate the link instead.
- `linkType` is a calculated field and cannot be provided in requests. It is automatically derived from the presence of `goalId` and `strategyId`.

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "link-123e4567-e89b-12d3-a456-426614174000",
    "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
    "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
    "thresholdPct": 85.0,
    "linkType": "strategy",
    "weight": 2.0,
    "displayOrder": 1,
    "isPrimary": true,
    "linkedAt": "2025-12-20T10:00:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Partial Updates:** Only provided fields are updated
- **Primary KPI:** Setting `isPrimary: true` may unset other primary KPIs for the same goal
- **Threshold Range:** Must be between 0 and 100 if provided
- **Display Order:** Used for UI sorting, can be any positive integer
- **Calculated linkType:** Automatically derived - cannot be set via API

---

### 4. Delete KPI Link

Remove a KPI link.

**Endpoint:** `DELETE /kpi-links/{linkId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | KPI link identifier |

#### Request Example

```http
DELETE /kpi-links/link-123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "message": "KPI link deleted successfully",
    "warning": null
  },
  "error": null
}
```

**Status:** `200 OK` (with warning when last link)

```json
{
  "success": true,
  "data": {
    "message": "KPI link deleted successfully",
    "warning": "This was the last link for KPI 'Customer Satisfaction Score'. The KPI is now orphaned and cannot be managed. Consider deleting the KPI if no longer needed."
  },
  "error": null
}
```

#### Business Rules

- **No Cascade:** Does not delete the KPI, goal, or any related data
- **Orphaned KPI Warning:** If this is the last link for a tenant-specific KPI, a warning is returned suggesting KPI deletion
- **Primary Status:** If deleted link was primary, goal has no primary KPI until another is set
- **Targets/Actuals Preserved:** KPI target and actual data remain intact (not deleted with link)

---

### 5. Query KPI Links

Get KPI links with flexible filtering by KPI, person, goal, or strategy.

**Endpoint:** `GET /kpi-links`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `kpiId` | string (GUID) | No | Filter by KPI |
| `personId` | string (GUID) | No | Filter by person |
| `goalId` | string (GUID) | No | Filter by goal |
| `strategyId` | string (GUID) | No | Filter by strategy |
| `includeAll` | boolean | No | Include nested links (default: false) |

**At least one filter parameter is required.** Multiple parameters can be combined.

#### Query Behaviors

**By KPI:**
```http
GET /kpi-links?kpiId={kpiId}
```
Returns all links for this KPI (all persons/goals/strategies where it's used).

**By Person (personal KPIs only):**
```http
GET /kpi-links?personId={personId}
```
Returns only personal KPIs for this person (no goal or strategy associations).

**By Person (all KPIs):**
```http
GET /kpi-links?personId={personId}&includeAll=true
```
Returns all KPIs assigned to this person (personal + goal + strategy).

**By Goal (goal-level KPIs only):**
```http
GET /kpi-links?goalId={goalId}
```
Returns only goal-level KPIs (no strategy associations).

**By Goal (all KPIs including strategies):**
```http
GET /kpi-links?goalId={goalId}&includeAll=true
```
Returns goal-level KPIs AND strategy KPIs for this goal.

**By Strategy:**
```http
GET /kpi-links?strategyId={strategyId}
```
Returns all KPIs linked to this strategy.

**By Person + Goal (intersection):**
```http
GET /kpi-links?personId={personId}&goalId={goalId}
```
Returns KPIs where this person is assigned to work on this specific goal.

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": "link-001",
      "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
      "personId": "person-123",
      "goalId": "goal-001",
      "strategyId": "strategy-001",
      "thresholdPct": 80.0,
      "linkType": "strategy",
      "weight": 1.5,
      "displayOrder": 1,
      "isPrimary": true,
      "linkedAt": "2025-12-20T10:00:00Z"
    },
    {
      "id": "link-002",
      "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
      "personId": "person-456",
      "goalId": "goal-002",
      "strategyId": null,
      "thresholdPct": 75.0,
      "linkType": "goal",
      "weight": 1.0,
      "displayOrder": 2,
      "isPrimary": false,
      "linkedAt": "2025-12-21T14:30:00Z"
    }
  ],
  "error": null
}
```

#### Use Cases

- **Personal scorecards:** `?personId={id}` - Show person's personal KPIs
- **Person workload:** `?personId={id}&includeAll=true` - All KPIs assigned to person
- **Goal tracking:** `?goalId={id}` - Goal-level KPIs only
- **Goal cascade:** `?goalId={id}&includeAll=true` - Goal + strategy KPIs
- **Strategy metrics:** `?strategyId={id}` - All KPIs for a strategy
- **Cross-functional KPIs:** `?kpiId={id}` - Where is this KPI used?
- **Person-goal assignment:** `?personId={id}&goalId={id}` - Person's work on specific goal

---

## Cascade Delete Behavior

When a tenant-specific KPI is deleted via `DELETE /kpis/{kpiId}`, the following cascade deletions occur automatically:

1. **KPI Links:** All links to this KPI are deleted
2. **KPI Targets:** All target data for this KPI is deleted
3. **KPI Actuals:** All actual measurement data for this KPI is deleted

**Note:** This cascade only applies to tenant-specific KPIs. Catalog KPIs cannot be deleted by users.

**Warning:** Cascade delete is permanent and cannot be undone. Ensure proper confirmation before deleting KPIs.

---

## Data Models

### Link Type (Calculated Field)

```typescript
type LinkType = "personal" | "goal" | "strategy";
```

**Calculation Logic:**
- **personal:** Only `personId` is set (no `goalId` or `strategyId`)
- **goal:** `personId` + `goalId` are set (no `strategyId`)
- **strategy:** `personId` + `goalId` + `strategyId` are all set

**Important:** `linkType` is NOT persisted in the database. It is calculated on-the-fly based on the presence of foreign keys. Do not include it in POST/PUT request bodies.

### Threshold Percentage

- **Range:** 0 - 100
- **Meaning:** Completion threshold for the KPI (e.g., 80% = "on track" at 80% of target)
- **Usage:** UI can show red/yellow/green status based on `currentValue` vs `targetValue` at threshold

### Weight

- **Range:** Any positive decimal
- **Meaning:** Relative importance for weighted calculations
- **Default:** 1.0
- **Usage:** When calculating weighted averages of multiple KPIs

### Display Order

- **Range:** Any positive integer
- **Meaning:** Sort order in UI (ascending)
- **Usage:** Controls how KPIs are listed on scorecards/dashboards

---

## Business Rules

### Link Creation

1. **Entity Validation:** All referenced entities (KPI, person, goal, strategy) must exist in tenant
2. **Duplicate Prevention:** Cannot create duplicate links (same KPI + same person + same goal + same strategy)
3. **Strategy Requires Goal:** Cannot link to strategy without also linking to goal
4. **Person Required:** Every link must have a person (owner)

### Primary KPI

1. **Goal Scope:** Primary flag only applies when goalId is present
2. **Single Primary:** Only one KPI can be primary per goal
3. **Auto-Unset:** Setting isPrimary=true on one link may automatically set isPrimary=false on other links for the same goal

### Delete Behavior

1. **Link Deletion:** Removing a link does NOT delete the KPI or any entities
2. **Orphan Warning:** If last link is deleted for a tenant-specific KPI, system warns about orphaned KPI
3. **Cascade Delete:** Only `DELETE /kpis/{id}` triggers cascade (links, targets, actuals)

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "data": null,
  "error": "Error message describing what went wrong"
}
```

### Common Error Codes

| Status Code | Scenario | Error Message |
|-------------|----------|---------------|
| `400` | Invalid GUID format | "Invalid link ID format" |
| `400` | Missing required field | "PersonId is required" |
| `400` | Strategy without goal | "Strategy link requires goalId" |
| `400` | Duplicate link | "KPI link already exists" |
| `404` | Link not found | "KPI link not found" |
| `404` | Referenced entity not found | "KPI not found" |
| `422` | Validation failed | "Threshold percentage must be between 0 and 100" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
// Create personal KPI link
const response = await traction.post('/kpi-links', {
  kpiId: 'kpi-123',
  personId: 'person-456',
  thresholdPct: 85.0,
  weight: 1.0,
  displayOrder: 1
});

// Create goal KPI link
await traction.post('/kpi-links', {
  kpiId: 'kpi-123',
  personId: 'person-456',
  goalId: 'goal-789',
  thresholdPct: 80.0,
  isPrimary: true
});

// Create strategy KPI link
await traction.post('/kpi-links', {
  kpiId: 'kpi-123',
  personId: 'person-456',
  goalId: 'goal-789',
  strategyId: 'strategy-101',
  thresholdPct: 75.0
});

// Query personal KPIs
const personalKpis = await traction.get('/kpi-links', {
  params: { personId: 'person-456' }
});

// Query all KPIs for person (including goals/strategies)
const allKpis = await traction.get('/kpi-links', {
  params: { personId: 'person-456', includeAll: true }
});

// Query goal KPIs
const goalKpis = await traction.get('/kpi-links', {
  params: { goalId: 'goal-789' }
});

// Query goal + strategy KPIs
const goalAllKpis = await traction.get('/kpi-links', {
  params: { goalId: 'goal-789', includeAll: true }
});

// Update link configuration
await traction.put(`/kpi-links/${linkId}`, {
  thresholdPct: 90.0,
  isPrimary: true,
  weight: 2.0
});

// Delete link
await traction.delete(`/kpi-links/${linkId}`);
```

---

## Related APIs

- **[KPIs API](./kpis-api.md)** - Manage KPIs
- **[KPI Data API](./kpi-data-api.md)** - Record KPI values, targets, actuals
- **[Goals API](./goals-api.md)** - Manage goals
- **[Strategies API](./strategies-api.md)** - Manage strategies
- **[People API](./people-api.md)** - Manage people/team members

---

## Changelog

### v8.0 (December 26, 2025)
- 🔄 **BREAKING:** Unified KPI Links API - removed separate controllers
- ❌ **Removed:** `PersonalKpisController` endpoints (`POST /people/{personId}/kpis:link`, `POST /people/{personId}/kpis:unlink`, `GET /people/{personId}/kpis`)
- ❌ **Removed:** `StrategyKpisController` endpoints (`GET /strategies/{strategyId}/kpis`)
- ✨ **Added:** `POST /kpi-links` - unified endpoint for creating all link types
- ✨ **Added:** `GET /kpi-links` with query parameters - flexible filtering by kpiId, personId, goalId, strategyId
- ✨ **Added:** `includeAll` query parameter for nested link retrieval
- 🔄 **Changed:** `linkType` is now a calculated/derived field (not persisted, not accepted in requests)
- ✨ **Added:** Cascade delete behavior when KPIs are deleted
- ✨ **Added:** Orphaned KPI warning when last link is deleted
- 📝 **Documentation:** Complete v8 specification with 5 unified endpoints

### v7.0 (December 23, 2025)
- ✨ New KpiLink design replacing GoalKpiLink (Issue #374)
- ✅ Documented 8 endpoints across 3 controllers
- ✨ Added personal scorecard endpoints (`/people/{personId}/kpis`)
- ✨ Added strategy KPI endpoints (`/strategies/{strategyId}/kpis`)

---

**[← Back to Traction Service Index](./README.md)**
