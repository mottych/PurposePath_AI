# Measure Links API Specification

**Version:** 8.4  
**Last Updated:** January 15, 2026  
**Base Path:** `/measure-links`  
**Controller:** `MeasureLinksController.cs`

## Overview

The Measure Links API manages relationships between Measures and entities (persons, goals, strategies). Every Measure link requires a person (owner/responsible party) and can optionally be associated with a goal and/or strategy.

### Key Features
- Link Measures to persons (required), with optional goal and strategy associations
- Configure thresholds, weights, and display order for each link
- Mark primary Measures for goals
- Query Measure links with flexible filtering (by person, goal, strategy, or Measure)
- Update or remove links
- Automatic cascade delete when tenant-specific Measures are deleted

### Design Philosophy
- **Unified resource-based API:** All Measure link operations through `/measure-links` endpoints
- **Person-centric:** Every Measure link must have a person (owner)
- **Flexible filtering:** Query by any entity type (person, goal, strategy, Measure) with optional `includeAll` parameter
- **Derived linkType:** Link type is calculated based on foreign key presence (not persisted)
- **Multi-entity:** One Measure can be linked to multiple persons/goals/strategies simultaneously

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. Get Measure Link by ID

Retrieve details of a specific Measure link.

**Endpoint:** `GET /measure-links/{linkId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Request Example

```http
GET /measure-links/link-123e4567-e89b-12d3-a456-426614174000
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
    "measureId": "measure-456e7890-e89b-12d3-a456-426614174001",
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
    "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
    "thresholdPct": 80.0,
    "riskThresholdPct": 50.0,
    "linkType": "strategy",
    "weight": 1.5,
    "displayOrder": 1,
    "isPrimary": true,
    "linkedAt": "2025-12-20T10:00:00Z",
    "progress": {
      "progressPercentage": 85.5,
      "status": "on_track",
      "variance": 10.5,
      "variancePercentage": 14.0,
      "daysUntilTarget": 15,
      "isOverdue": false
    }
  },
  "error": null
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (GUID) | Unique link identifier |
| `measureId` | string (GUID) | Measure being linked |
| `personId` | string (GUID) | Person responsible (owner) - **Required** |
| `goalId` | string (GUID) | Goal linked to (nullable) |
| `strategyId` | string (GUID) | Strategy linked to (nullable) |
| `thresholdPct` | decimal | Completion threshold percentage (0-100) |
| `riskThresholdPct` | decimal | Risk threshold percentage (0-100) |
| `linkType` | string | **Calculated field** - Type of link: `"personal"` (only personId), `"goal"` (personId + goalId), `"strategy"` (personId + goalId + strategyId) |
| `weight` | decimal | Relative importance (for weighted calculations, 0.0-1.0) |
| `displayOrder` | int | Sort order in UI (lower = first) |
| `isPrimary` | boolean | Is this the primary Measure for the goal? |
| `linkedAt` | datetime | When link was created |
| `progress` | object | **Issue #527** - Progress calculation based on latest target and actual values. Includes `progressPercentage` (0-100+), `status` (on_track/at_risk/behind/no_data), `variance`, `variancePercentage`, `daysUntilTarget`, and `isOverdue`. Returns `null` if no target or actual data exists. |

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
  "error": "Measure link not found"
}
```

---

### 2. Create Measure Link

Create a new link between a Measure and person, optionally associating with a goal and/or strategy.

**Endpoint:** `POST /measure-links`

#### Request Body

```json
{
  "measureId": "measure-456e7890-e89b-12d3-a456-426614174001",
  "personId": "person-789e1234-e89b-12d3-a456-426614174002",
  "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
  "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
  "thresholdPct": 85.0,
  "riskThresholdPct": 50.0,
  "weight": 1.5,
  "displayOrder": 1,
  "isPrimary": false
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `measureId` | string (GUID) | **Yes** | Measure to link |
| `personId` | string (GUID) | **Yes** | Person responsible/owner |
| `goalId` | string (GUID) | No | Goal to associate (required if strategyId provided) |
| `strategyId` | string (GUID) | No | Strategy to associate (requires goalId) |
| `thresholdPct` | decimal | No | Threshold percentage (0-100, default: 80.0) |
| `riskThresholdPct` | decimal | No | Risk threshold percentage (0-100, default: 50.0) |
| `weight` | decimal | No | Relative weight (default: 1.0) |
| `displayOrder` | int | No | Sort order (default: auto-assigned) |
| `isPrimary` | boolean | No | Mark as primary Measure (default: false) |

**Note:** `linkType` is NOT accepted in requests - it is automatically calculated based on provided fields.

#### Response

**Status:** `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "link-new-123",
    "measureId": "measure-456e7890-e89b-12d3-a456-426614174001",
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
    "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
    "thresholdPct": 85.0,
    "riskThresholdPct": 50.0,
    "linkType": "strategy",
    "weight": 0.5,
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
- **Entity Validation:** All referenced entities (Measure, person, goal, strategy) must exist in tenant
- **Duplicate Prevention:** Cannot create duplicate links (same Measure + person + goal + strategy combination)
- **Auto linkType:** Calculated automatically: `personal` (no goal/strategy), `goal` (has goalId), `strategy` (has goalId + strategyId)
- **Primary Measure:** Setting isPrimary=true may unset other primary Measures for the same goal

---

### 3. Update Measure Link

Update link configuration (person, goal, strategy, threshold, weight, priority, etc.).

**Endpoint:** `PUT /measure-links/{linkId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Request Body

```json
{
  "personId": "person-789e1234-e89b-12d3-a456-426614174002",
  "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
  "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
  "thresholdPct": 85.0,
  "riskThresholdPct": 50.0,
  "weight": 2.0,
  "displayOrder": 1,
  "isPrimary": true
}
```

#### Request Fields

All fields are optional. Only provided fields will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `personId` | string (GUID) | Person responsible for this link. **When changed, propagates to the Measure and all other links for that Measure.** |
| `goalId` | string (GUID) | Goal association. Set to associate with a goal or change association. Note: Removing goal (by setting to null) will also remove strategy. |
| `strategyId` | string (GUID) | Strategy association. Requires a goal to be set. Must belong to the specified goal. |
| `thresholdPct` | decimal | Threshold percentage (0-100) |
| `riskThresholdPct` | decimal | Risk threshold percentage (0-100) |
| `weight` | decimal | Relative weight/importance |
| `displayOrder` | int | Sort order in UI |
| `isPrimary` | boolean | Mark as primary Measure |

**Notes:** 
- You cannot change `measureId` via update. Delete and recreate the link instead.
- `linkType` is a calculated field and cannot be provided in requests. It is automatically derived from the presence of `goalId` and `strategyId`.
- **PersonId Propagation:** When `personId` is updated, the change propagates to:
  - The Measure's `ownerId` field
  - All other MeasureLinks associated with the same Measure
- **Strategy Validation:** When `strategyId` is provided, the system validates that:
  - A `goalId` is set (either in the request or already on the link)
  - The strategy exists and belongs to the specified goal

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "link-123e4567-e89b-12d3-a456-426614174000",
    "measureId": "measure-456e7890-e89b-12d3-a456-426614174001",
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "goalId": "goal-012e3456-e89b-12d3-a456-426614174003",
    "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
    "thresholdPct": 85.0,
    "riskThresholdPct": 50.0,
    "linkType": "strategy",
    "weight": 0.8,
    "displayOrder": 1,
    "isPrimary": true,
    "linkedAt": "2025-12-20T10:00:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Partial Updates:** Only provided fields are updated
- **PersonId Propagation:** Updating `personId` cascades to Measure and all related links atomically
- **Goal Association:** Can be set or changed; removing goal also removes strategy
- **Strategy Validation:** 
  - Strategy requires a goal to be present
  - Strategy must belong to the specified goal
  - System validates strategy-goal relationship before update
- **Primary Measure:** Setting `isPrimary: true` may unset other primary Measures for the same goal
- **Threshold Range:** Must be between 0 and 100 if provided
- **Risk Threshold Range:** Must be between 0 and 100 if provided and must be <= thresholdPct
- **Display Order:** Used for UI sorting, can be any positive integer
- **Calculated linkType:** Automatically derived from `goalId` and `strategyId` presence - cannot be set via API

#### Error Responses

**404 Not Found** - Link, Goal, or Strategy not found:
```json
{
  "success": false,
  "error": "MEASURE link not found",
  "code": "MEASURE_LINK_NOT_FOUND"
}
```

**400 Bad Request** - Validation errors:
```json
{
  "success": false,
  "error": "Strategy requires a Goal to be set",
  "code": "STRATEGY_REQUIRES_GOAL"
}
```

```json
{
  "success": false,
  "error": "Strategy 345e6789... does not belong to Goal 012e3456...",
  "code": "STRATEGY_GOAL_MISMATCH"
}
```

---

### 4. Delete Measure Link

Remove a Measure link.

**Endpoint:** `DELETE /measure-links/{linkId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Request Example

```http
DELETE /measure-links/link-123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "message": "Measure link deleted successfully",
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
    "message": "Measure link deleted successfully",
    "warning": "This was the last link for Measure 'Customer Satisfaction Score'. The Measure is now orphaned and cannot be managed. Consider deleting the Measure if no longer needed."
  },
  "error": null
}
```

#### Business Rules

- **No Cascade:** Does not delete the Measure, goal, or any related data
- **Orphaned Measure Warning:** If this is the last link for a tenant-specific Measure, a warning is returned suggesting Measure deletion
- **Primary Status:** If deleted link was primary, goal has no primary Measure until another is set
- **Targets/Actuals Preserved:** Measure target and actual data remain intact (not deleted with link)

---

### 5. Query Measure Links

Get Measure links with flexible filtering by Measure, person, goal, or strategy.

**Endpoint:** `GET /measure-links`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `measureId` | string (GUID) | No | Filter by Measure |
| `personId` | string (GUID) | No | Filter by person |
| `goalId` | string (GUID) | No | Filter by goal |
| `strategyId` | string (GUID) | No | Filter by strategy |
| `includeAll` | boolean | No | Include nested links (default: false) |
| `measureInfo` | boolean | No | Include enriched measure details (default: false) - **Issue #562** |

**At least one filter parameter is required.** Multiple parameters can be combined.

#### Query Behaviors

**By Measure:**
```http
GET /measure-links?measureId={measureId}
```
Returns all links for this Measure (all persons/goals/strategies where it's used).

**By Person (personal Measures only):**
```http
GET /measure-links?personId={personId}
```
Returns only personal Measures for this person (no goal or strategy associations).

**By Person (all Measures):**
```http
GET /measure-links?personId={personId}&includeAll=true
```
Returns all Measures assigned to this person (personal + goal + strategy).

**By Goal (goal-level Measures only):**
```http
GET /measure-links?goalId={goalId}
```
Returns only goal-level Measures (no strategy associations).

**By Goal (all Measures including strategies):**
```http
GET /measure-links?goalId={goalId}&includeAll=true
```
Returns goal-level Measures AND strategy Measures for this goal.

**By Strategy:**
```http
GET /measure-links?strategyId={strategyId}
```
Returns all Measures linked to this strategy.

**By Person + Goal (intersection):**
```http
GET /measure-links?personId={personId}&goalId={goalId}
```
Returns Measures where this person is assigned to work on this specific goal.

**With Enriched Measure Info (Issue #562):**
```http
GET /measure-links?goalId={goalId}&measureInfo=true
```
Returns measure links with additional measure details including aggregation config, owner info, trend data, and metadata.

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": "link-001",
      "measureId": "measure-456e7890-e89b-12d3-a456-426614174001",
      "measureName": "Customer Satisfaction Score",
      "unit": "percentage",
      "personId": "person-123",
      "personName": "John Doe",
      "goalId": "goal-001",
      "goalTitle": "Increase Customer Satisfaction",
      "strategyId": "strategy-001",
      "strategyTitle": "Improve Support Response Time",
      "thresholdPct": 80.0,
      "linkType": "strategy",
      "weight": 0.75,
      "displayOrder": 1,
      "isPrimary": true,
      "linkedAt": "2025-12-20T10:00:00Z",
      "currentValue": 87.5,
      "currentValueDate": "2025-12-25T09:30:00Z",
      "progress": {
        "progressPercentage": 85.5,
        "status": "on_track",
        "variance": 10.5,
        "variancePercentage": 14.0,
        "daysUntilTarget": 15,
        "isOverdue": false
      },
      "measure": {
        "measurementConfig": {
          "aggregationPeriod": "monthly"
        },
        "ownerId": "person-789",
        "ownerName": "Sarah Johnson",
        "ownerEmail": "sarah.johnson@example.com",
        "trendData": [
          {
            "date": "2025-12-01",
            "value": 85.0,
            "isTarget": true
          },
          {
            "date": "2025-12-01",
            "value": 82.3,
            "isTarget": false
          },
          {
            "date": "2025-11-01",
            "value": 80.0,
            "isTarget": true
          },
          {
            "date": "2025-11-01",
            "value": 78.5,
            "isTarget": false
          }
        ],
        "metadata": {
          "createdAt": "2025-10-15T08:30:00Z",
          "updatedAt": "2025-12-20T14:22:00Z"
        }
      }
    },
    {
      "id": "link-002",
      "measureId": "measure-456e7890-e89b-12d3-a456-426614174001",
      "measureName": "Customer Satisfaction Score",
      "unit": "percentage",
      "personId": "person-456",
      "personName": "Jane Smith",
      "goalId": "goal-002",
      "strategyId": null,
      "thresholdPct": 75.0,
      "linkType": "goal",
      "weight": 0.5,
      "displayOrder": 2,
      "isPrimary": false,
      "linkedAt": "2025-12-21T14:30:00Z",
      "currentValue": null,
      "currentValueDate": null
    }
  ],
  "error": null
}
```

**Note:** The query response includes denormalized fields for convenience:
- `measureName` - Name of the linked Measure
- `unit` - Unit of measurement
- `personName` - Name of the responsible person
- `goalTitle` - Title/name of the linked goal (if any) - **Issue #569**
- `strategyTitle` - Title/name of the linked strategy (if any) - **Issue #569**
- `currentValue` - Latest actual value (if any)
- `currentValueDate` - Date of the latest actual value (if any)
- `progress` - Progress calculation (Issue #527)
- `measure` - Enriched measure details (only when `measureInfo=true`) - **Issue #562**
  - `measurementConfig.aggregationPeriod` - Aggregation period ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')
  - `ownerId` - Person responsible for the measure
  - `ownerName` - Owner's display name (denormalized)
  - `ownerEmail` - Owner's email (denormalized)
  - `trendData` - Array of recent data points (5-10 points) for sparkline visualization
  - `metadata` - Audit information (createdAt, updatedAt)

#### Use Cases

- **Personal scorecards:** `?personId={id}` - Show person's personal Measures
- **Person workload:** `?personId={id}&includeAll=true` - All Measures assigned to person
- **Goal tracking:** `?goalId={id}` - Goal-level Measures only
- **Goal cascade:** `?goalId={id}&includeAll=true` - Goal + strategy Measures
- **Strategy metrics:** `?strategyId={id}` - All Measures for a strategy
- **Cross-functional Measures:** `?measureId={id}` - Where is this Measure used?
- **Person-goal assignment:** `?personId={id}&goalId={id}` - Person's work on specific goal

---

## Cascade Delete Behavior

When a tenant-specific Measure is deleted via `DELETE /measures/{measureId}`, the following cascade deletions occur automatically:

1. **Measure Links:** All links to this Measure are deleted
2. **Measure Targets:** All target data for this Measure is deleted
3. **Measure Actuals:** All actual measurement data for this Measure is deleted

**Note:** This cascade only applies to tenant-specific Measures. Catalog Measures cannot be deleted by users.

**Warning:** Cascade delete is permanent and cannot be undone. Ensure proper confirmation before deleting Measures.

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
- **Meaning:** Completion threshold for the Measure (e.g., 80% = "on track" at 80% of target)
- **Usage:** UI can show red/yellow/green status based on `currentValue` vs `targetValue` at threshold

### Risk Threshold Percentage

- **Range:** 0 - 100 (must be ≤ `thresholdPct`)
- **Meaning:** Risk threshold for "at risk" status (e.g., 50% = "at risk" when variance percentage < -50)
- **Usage:** Determines split between "behind" and "at_risk" statuses

### Weight

- **Range:** 0.0 - 1.0
- **Meaning:** Relative importance for weighted calculations (normalized)
- **Default:** 1.0 (but must be within 0.0-1.0 range)
- **Validation:** Domain enforces 0.0 ≤ weight ≤ 1.0
- **Usage:** When calculating weighted averages of multiple Measures

### Display Order

- **Range:** Any positive integer
- **Meaning:** Sort order in UI (ascending)
- **Usage:** Controls how Measures are listed on scorecards/dashboards

---

## Business Rules

### Link Creation

1. **Entity Validation:** All referenced entities (Measure, person, goal, strategy) must exist in tenant
2. **Duplicate Prevention:** Cannot create duplicate links (same Measure + same person + same goal + same strategy)
3. **Strategy Requires Goal:** Cannot link to strategy without also linking to goal
4. **Person Required:** Every link must have a person (owner)

### Primary Measure

1. **Goal Scope:** Primary flag only applies when goalId is present
2. **Single Primary:** Only one Measure can be primary per goal
3. **Auto-Unset:** Setting isPrimary=true on one link may automatically set isPrimary=false on other links for the same goal

### Delete Behavior

1. **Link Deletion:** Removing a link does NOT delete the Measure or any entities
2. **Orphan Warning:** If last link is deleted for a tenant-specific Measure, system warns about orphaned Measure
3. **Cascade Delete:** Only `DELETE /measures/{id}` triggers cascade (links, targets, actuals)

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
| `400` | Duplicate link | "Measure link already exists" |
| `404` | Link not found | "Measure link not found" |
| `404` | Referenced entity not found | "Measure not found" |
| `422` | Validation failed | "Threshold percentage must be between 0 and 100" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
// Create personal Measure link
const response = await traction.post('/measure-links', {
  measureId: 'measure-123',
  personId: 'person-456',
  thresholdPct: 85.0,
  weight: 0.8,  // Must be between 0.0 and 1.0
  displayOrder: 1
});

// Create goal Measure link
await traction.post('/measure-links', {
  measureId: 'measure-123',
  personId: 'person-456',
  goalId: 'goal-789',
  thresholdPct: 80.0,
  weight: 0.9,  // Must be between 0.0 and 1.0
  isPrimary: true
});

// Create strategy Measure link
await traction.post('/measure-links', {
  measureId: 'measure-123',
  personId: 'person-456',
  goalId: 'goal-789',
  strategyId: 'strategy-101',
  thresholdPct: 75.0,
  weight: 0.7  // Must be between 0.0 and 1.0
});

// Query personal Measures (returns denormalized fields)
const personalMeasures = await traction.get('/measure-links', {
  params: { personId: 'person-456' }
});
// Response includes: measureName, unit, personName, currentValue, currentValueDate

// Query all Measures for person (including goals/strategies)
const allMeasures = await traction.get('/measure-links', {
  params: { personId: 'person-456', includeAll: true }
});

// Query goal Measures
const goalMeasures = await traction.get('/measure-links', {
  params: { goalId: 'goal-789' }
});

// Query goal + strategy Measures
const goalAllMeasures = await traction.get('/measure-links', {
  params: { goalId: 'goal-789', includeAll: true }
});

// Update link configuration
await traction.put(`/measure-links/${linkId}`, {
  thresholdPct: 90.0,
  isPrimary: true,
  weight: 0.95  // Must be between 0.0 and 1.0
});

// Delete link
await traction.delete(`/measure-links/${linkId}`);
```

---

## Related APIs

- **[Measures API](./measures-api.md)** - Manage Measures
- **[Measure Data API](./measure-data-api.md)** - Record Measure values, targets, actuals
- **[Goals API](./goals-api.md)** - Manage goals
- **[Strategies API](./strategies-api.md)** - Manage strategies
- **[People API](./people-api.md)** - Manage people/team members

---

## Changelog

### v8.3 (January 15, 2026) - Issue #569: Goal and Strategy Titles
- ✨ **Added:** `goalTitle` and `strategyTitle` fields to all Measure Link response payloads
- 🚀 **Performance:** Reduces frontend API calls by providing denormalized goal/strategy names directly in responses
- 📝 **Implementation:** Query handler fetches and populates titles with throttled parallelism (max 10 concurrent)
- 🔧 **Nullable fields:** Both fields return `null` when goal/strategy is not linked to the Measure Link

### v8.2 (January 10, 2026) - Issue #527: Progress Calculation
- ✨ **Added:** `progress` field to all measure link responses (GET /measure-links, GET /measure-links/{id})
- 📊 Progress calculation includes: progressPercentage, status (on_track/at_risk/behind/no_data), variance, variancePercentage, daysUntilTarget, isOverdue
- 🧮 Implemented via domain service pattern (`MeasureLinkProgressService`) following DDD principles
- 📝 Progress calculated based on latest target and actual values, accounting for measure direction and threshold
- 🚀 Batch optimization with throttled parallelism (max 10 concurrent) for performance

### v8.1 (January 8, 2026)
- 📝 **Updated:** Weight range clarified to 0.0-1.0 (matches domain validation)
- ✨ **Added:** Query response includes denormalized fields: `measureName`, `unit`, `personName`, `currentValue`, `currentValueDate`
- 📝 **Documentation:** Updated all examples to reflect actual implementation with denormalized fields
- 🔧 **Clarification:** Weight validation enforces 0.0 ≤ weight ≤ 1.0 in domain layer

### v8.0 (December 26, 2025)
- 🔄 **BREAKING:** Unified Measure Links API - removed separate controllers
- ❌ **Removed:** `PersonalMeasuresController` endpoints (`POST /people/{personId}/measures:link`, `POST /people/{personId}/measures:unlink`, `GET /people/{personId}/measures`)
- ❌ **Removed:** `StrategyMeasuresController` endpoints (`GET /strategies/{strategyId}/measures`)
- ✨ **Added:** `POST /measure-links` - unified endpoint for creating all link types
- ✨ **Added:** `GET /measure-links` with query parameters - flexible filtering by measureId, personId, goalId, strategyId
- ✨ **Added:** `includeAll` query parameter for nested link retrieval
- 🔄 **Changed:** `linkType` is now a calculated/derived field (not persisted, not accepted in requests)
- ✨ **Added:** Cascade delete behavior when Measures are deleted
- ✨ **Added:** Orphaned Measure warning when last link is deleted
- 📝 **Documentation:** Complete v8 specification with 5 unified endpoints

### v7.0 (December 23, 2025)
- ✨ New MeasureLink design replacing GoalMeasureLink (Issue #374)
- ✅ Documented 8 endpoints across 3 controllers
- ✨ Added personal scorecard endpoints (`/people/{personId}/measures`)
- ✨ Added strategy Measure endpoints (`/strategies/{strategyId}/measures`)

---

**[← Back to Traction Service Index](./README.md)**
