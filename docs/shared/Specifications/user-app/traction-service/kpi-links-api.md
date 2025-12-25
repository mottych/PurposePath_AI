# KPI Links API Specification

**Version:** 7.0  
**Last Updated:** December 23, 2025  
**Base Paths:** `/kpi-links`, `/people/{personId}/kpis`, `/strategies/{strategyId}/kpis`  
**Controllers:** `KpiLinksController.cs`, `PersonalKpisController.cs`, `StrategyKpisController.cs`

## Overview

The KPI Links API manages relationships between KPIs and other entities (goals, persons, strategies). This is the v7 design that replaced the deprecated GoalKpiLink model (issue #374).

### Key Features
- Link KPIs to goals, persons (personal scorecard), or strategies
- Configure thresholds, weights, and display order for each link
- Mark primary KPIs for goals
- Query KPI links by KPI, person, or strategy
- Update or remove links while preserving history

### Design Philosophy
- **Resource-based:** KPI links are first-class resources with their own IDs
- **Flexible linking:** Supports goal-KPI, person-KPI, strategy-KPI relationships
- **Configuration:** Each link can have threshold, weight, priority settings
- **Multi-entity:** One KPI can be linked to multiple goals, persons, strategies simultaneously

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Core KPI Links Endpoints

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
    "linkType": "goal",
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
| `personId` | string (GUID) | Person responsible (owner) |
| `goalId` | string (GUID) | Goal linked to (nullable) |
| `strategyId` | string (GUID) | Strategy linked to (nullable) |
| `thresholdPct` | decimal | Completion threshold percentage (0-100) |
| `linkType` | string | Type of link: `"goal"`, `"personal"`, `"strategy"` |
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

### 2. Update KPI Link

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
  "linkType": "goal",
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
| `linkType` | string | `"goal"`, `"personal"`, or `"strategy"` |
| `weight` | decimal | Relative weight/importance |
| `displayOrder` | int | Sort order in UI |
| `isPrimary` | boolean | Mark as primary KPI |

**Note:** You cannot change `kpiId`, `goalId`, `personId`, or `strategyId` via update. Delete and recreate the link instead.

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
    "linkType": "goal",
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

---

### 3. Delete KPI Link

Remove a KPI link (soft delete).

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
    "message": "KPI link deleted successfully"
  },
  "error": null
}
```

#### Business Rules

- **Soft Delete:** Link is marked as deleted but preserved for history
- **Cascade:** Does not delete the KPI or goal itself
- **Primary Status:** If deleted link was primary, goal has no primary KPI until another is set

---

### 4. Get Links by KPI

Get all links for a specific KPI (all goals/persons/strategies it's linked to).

**Endpoint:** `GET /kpi-links/by-kpi/{kpiId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `kpiId` | string (GUID) | **Yes** | KPI identifier |

#### Request Example

```http
GET /kpi-links/by-kpi/kpi-456e7890-e89b-12d3-a456-426614174001
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

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
      "linkType": "goal",
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

- **Show where KPI is used:** Display all goals/strategies using this KPI
- **Multi-goal metrics:** One KPI can track multiple goals simultaneously
- **Cross-functional KPIs:** Shared metrics across teams/strategies

---

## Personal Scorecard Endpoints

### 5. Get Personal KPIs

Get all KPIs linked to a person (their personal scorecard).

**Endpoint:** `GET /people/{personId}/kpis`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `personId` | string (GUID) | **Yes** | Person identifier |

#### Request Example

```http
GET /people/person-789e1234-e89b-12d3-a456-426614174002/kpis
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "personName": "John Doe",
    "kpis": [
      {
        "id": "link-001",
        "kpiId": "kpi-001",
        "personId": "person-789e1234-e89b-12d3-a456-426614174002",
        "goalId": "goal-001",
        "strategyId": "strategy-001",
        "thresholdPct": 80.0,
        "linkType": "personal",
        "weight": 1.5,
        "displayOrder": 1,
        "isPrimary": false,
        "linkedAt": "2025-12-20T10:00:00Z"
      }
    ],
    "totalKpis": 1
  },
  "error": null
}
```

#### Use Cases

- **Personal scorecards:** All KPIs assigned to a person
- **Individual accountability:** Track person-specific metrics
- **Performance reviews:** KPIs for individual evaluation

---

### 6. Link KPI to Person

Add a KPI to a person's personal scorecard.

**Endpoint:** `POST /people/{personId}/kpis:link`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `personId` | string (GUID) | **Yes** | Person identifier |

#### Request Body

```json
{
  "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
  "thresholdPct": 85.0,
  "linkType": "personal",
  "weight": 1.0,
  "displayOrder": 1,
  "isPrimary": false
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kpiId` | string (GUID) | **Yes** | KPI to link |
| `thresholdPct` | decimal | No | Threshold percentage (0-100) |
| `linkType` | string | No | Default: `"personal"` |
| `weight` | decimal | No | Relative weight (default: 1.0) |
| `displayOrder` | int | No | Sort order (default: auto-assigned) |
| `isPrimary` | boolean | No | Mark as primary (default: false) |

#### Response

**Status:** `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "link-new-123",
    "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001",
    "personId": "person-789e1234-e89b-12d3-a456-426614174002",
    "goalId": null,
    "strategyId": null,
    "thresholdPct": 85.0,
    "linkType": "personal",
    "weight": 1.0,
    "displayOrder": 1,
    "isPrimary": false,
    "linkedAt": "2025-12-23T16:00:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Person must exist:** PersonId must be valid in tenant
- **KPI must exist:** KpiId must be valid in tenant
- **Duplicate prevention:** Same KPI can be linked to same person only once (unless different contexts)

---

### 7. Unlink KPI from Person

Remove a KPI from a person's personal scorecard.

**Endpoint:** `POST /people/{personId}/kpis:unlink`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `personId` | string (GUID) | **Yes** | Person identifier |

#### Request Body

```json
{
  "kpiId": "kpi-456e7890-e89b-12d3-a456-426614174001"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kpiId` | string (GUID) | **Yes** | KPI to unlink |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "message": "KPI unlinked successfully"
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
  "error": "KPI not linked to this person"
}
```

---

## Strategy KPIs Endpoints

### 8. Get Strategy KPIs

Get all KPIs linked to a specific strategy.

**Endpoint:** `GET /strategies/{strategyId}/kpis`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `strategyId` | string (GUID) | **Yes** | Strategy identifier |

#### Request Example

```http
GET /strategies/strategy-345e6789-e89b-12d3-a456-426614174004/kpis
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
    "goalId": "goal-001",
    "kpis": [
      {
        "id": "link-001",
        "kpiId": "kpi-001",
        "personId": "person-123",
        "goalId": "goal-001",
        "strategyId": "strategy-345e6789-e89b-12d3-a456-426614174004",
        "thresholdPct": 80.0,
        "linkType": "strategy",
        "weight": 1.5,
        "displayOrder": 1,
        "isPrimary": false,
        "linkedAt": "2025-12-20T10:00:00Z"
      }
    ],
    "totalKpis": 1
  },
  "error": null
}
```

#### Use Cases

- **Strategy tracking:** All KPIs measuring progress toward a strategy
- **Multi-KPI strategies:** Strategies tracked by multiple metrics
- **Cascading metrics:** Strategy KPIs roll up to goal KPIs

---

## Data Models

### Link Types

```typescript
type LinkType = "goal" | "personal" | "strategy";
```

- **goal:** KPI tracks a specific goal
- **personal:** KPI is on a person's personal scorecard
- **strategy:** KPI measures a strategy

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
2. **Duplicate Prevention:** Cannot create duplicate links (same KPI + same target entity)
3. **Person Requirement:** `personId` is always required (owner/responsible party)
4. **Context Flexibility:** Can link KPI to goal only, person only, strategy only, or combinations

### Primary KPI

- **Goal Context:** Each goal can have ONE primary KPI
- **Setting Primary:** Setting a new KPI as primary automatically unsets previous primary for that goal
- **Personal/Strategy:** Primary flag is less common for personal/strategy links

### Soft Delete

- **Preservation:** Deleted links are marked `isDeleted: true` but not removed
- **History:** Supports historical analysis and audit trails
- **Restoration:** Can be restored by admin/support if needed

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
| 400 | Invalid GUID format | "Invalid link ID format" |
| 400 | Missing required field | "KpiId is required" |
| 400 | Invalid threshold | "Threshold must be between 0 and 100" |
| 401 | Missing/invalid token | "Unauthorized" |
| 403 | Insufficient permissions | "Access denied to this KPI link" |
| 404 | Link not found | "KPI link not found" |
| 404 | KPI not linked | "KPI not linked to this person" |
| 409 | Duplicate link | "KPI already linked to this goal" |
| 500 | Server error | "Internal server error" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
import { traction } from './traction';

// Get all links for a KPI
const links = await traction.get<KpiLinkResponse[]>(
  `/kpi-links/by-kpi/${kpiId}`
);

// Link KPI to person (personal scorecard)
const personalLink = await traction.post<KpiLinkResponse>(
  `/people/${personId}/kpis:link`,
  {
    kpiId: kpiId,
    thresholdPct: 85.0,
    linkType: 'personal',
    weight: 1.0
  }
);

// Get person's personal scorecard
const scorecard = await traction.get<PersonalScorecardResponse>(
  `/people/${personId}/kpis`
);

// Update link configuration
await traction.put(`/kpi-links/${linkId}`, {
  thresholdPct: 90.0,
  isPrimary: true,
  weight: 2.0
});

// Delete link
await traction.delete(`/kpi-links/${linkId}`);

// Get strategy KPIs
const strategyKpis = await traction.get<StrategyKpisResponse>(
  `/strategies/${strategyId}/kpis`
);
```

---

## Migration from v6

### Deprecated Endpoints (Removed in v7)

| Old Endpoint (v6) | New Endpoint (v7) | Notes |
|-------------------|-------------------|-------|
| `POST /goals/{goalId}/kpis:link` | `POST /kpi-links` + specify `goalId` | Resource-based design |
| `POST /goals/{goalId}/kpis:unlink` | `DELETE /kpi-links/{linkId}` | Use link ID |
| `GET /goals/{goalId}/kpis` | `GET /kpi-links?goalId={goalId}` | Query parameter |
| `GET /kpis/{kpiId}/linked-goals` | `GET /kpi-links/by-kpi/{kpiId}` | Renamed for clarity |

### Key Differences

**v6 (GoalKpiLink):**
- Nested under goals: `/goals/{goalId}/kpis`
- Goal-centric design
- Limited to goal-KPI relationships

**v7 (KpiLink):**
- Top-level resource: `/kpi-links`
- KPI-centric design
- Supports goal, person, strategy relationships
- First-class link entities with IDs

---

## Related APIs

- **[KPIs API](./kpis-api.md)** - Manage KPIs
- **[KPI Data API](./kpi-data-api.md)** - Record KPI values, targets, actuals
- **[Goals API](./goals-api.md)** - Manage goals
- **[Strategies API](./strategies-api.md)** - Manage strategies
- **[People API](./people-api.md)** - Manage people/team members

---

## Changelog

### v7.0 (December 23, 2025)
- ✨ New KpiLink design replacing GoalKpiLink (Issue #374)
- ✅ Documented 8 endpoints across 3 controllers
- ✨ Added personal scorecard endpoints (`/people/{personId}/kpis`)
- ✨ Added strategy KPI endpoints (`/strategies/{strategyId}/kpis`)
- ✨ Resource-based link management (`/kpi-links`)
- 📝 Complete request/response examples for all endpoints
- 📝 Business rules, validation, error handling documented
- 📝 Migration guide from v6 GoalKpiLink pattern

### v6.0 (December 21, 2025)
- ⚠️ Deprecated GoalKpiLink design

---

**[← Back to Traction Service Index](./README.md)**
