# Measure Links API Specification

**Version:** 7.0  
**Last Updated:** December 23, 2025  
**Base Paths:** `/measure-links`, `/people/{personId}/measures`, `/strategies/{strategyId}/measures`  
**Controllers:** `MeasureLinksController.cs`, `PersonalMeasuresController.cs`, `StrategyMeasuresController.cs`

## Overview

The Measure Links API manages relationships between Measures and other entities (goals, persons, strategies). This is the v7 design that replaced the deprecated GoalMeasureLink model (issue #374).

### Key Features
- Link Measures to goals, persons (personal scorecard), or strategies
- Configure thresholds, weights, and display order for each link
- Mark primary Measures for goals
- Query Measure links by Measure, person, or strategy
- Update or remove links while preserving history

### Design Philosophy
- **Resource-based:** Measure links are first-class resources with their own IDs
- **Flexible linking:** Supports goal-Measure, person-Measure, strategy-Measure relationships
- **Configuration:** Each link can have threshold, weight, priority settings
- **Multi-entity:** One Measure can be linked to multiple goals, persons, strategies simultaneously

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Core Measure Links Endpoints

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
    "kpiId": "measure-456e7890-e89b-12d3-a456-426614174001",
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
| `kpiId` | string (GUID) | Measure being linked |
| `personId` | string (GUID) | Person responsible (owner) |
| `goalId` | string (GUID) | Goal linked to (nullable) |
| `strategyId` | string (GUID) | Strategy linked to (nullable) |
| `thresholdPct` | decimal | Completion threshold percentage (0-100) |
| `linkType` | string | Type of link: `"goal"`, `"personal"`, `"strategy"` |
| `weight` | decimal | Relative importance (for weighted calculations) |
| `displayOrder` | int | Sort order in UI (lower = first) |
| `isPrimary` | boolean | Is this the primary Measure for the goal? |
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
  "error": "Measure link not found"
}
```

---

### 2. Update Measure Link

Update link configuration (threshold, weight, priority, etc.).

**Endpoint:** `PUT /measure-links/{linkId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

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
| `isPrimary` | boolean | Mark as primary Measure |

**Note:** You cannot change `kpiId`, `goalId`, `personId`, or `strategyId` via update. Delete and recreate the link instead.

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "link-123e4567-e89b-12d3-a456-426614174000",
    "kpiId": "measure-456e7890-e89b-12d3-a456-426614174001",
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
- **Primary Measure:** Setting `isPrimary: true` may unset other primary Measures for the same goal
- **Threshold Range:** Must be between 0 and 100 if provided
- **Display Order:** Used for UI sorting, can be any positive integer

---

### 3. Delete Measure Link

Remove a Measure link (soft delete).

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
    "message": "Measure link deleted successfully"
  },
  "error": null
}
```

#### Business Rules

- **Soft Delete:** Link is marked as deleted but preserved for history
- **Cascade:** Does not delete the Measure or goal itself
- **Primary Status:** If deleted link was primary, goal has no primary Measure until another is set

---

### 4. Get Links by Measure

Get all links for a specific Measure (all goals/persons/strategies it's linked to).

**Endpoint:** `GET /measure-links/by-measure/{kpiId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `kpiId` | string (GUID) | **Yes** | Measure identifier |

#### Request Example

```http
GET /measure-links/by-measure/measure-456e7890-e89b-12d3-a456-426614174001
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
      "kpiId": "measure-456e7890-e89b-12d3-a456-426614174001",
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
      "kpiId": "measure-456e7890-e89b-12d3-a456-426614174001",
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

- **Show where Measure is used:** Display all goals/strategies using this Measure
- **Multi-goal metrics:** One Measure can track multiple goals simultaneously
- **Cross-functional Measures:** Shared metrics across teams/strategies

---

## Personal Scorecard Endpoints

### 5. Get Personal Measures

Get all Measures linked to a person (their personal scorecard).

**Endpoint:** `GET /people/{personId}/measures`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `personId` | string (GUID) | **Yes** | Person identifier |

#### Request Example

```http
GET /people/person-789e1234-e89b-12d3-a456-426614174002/measures
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
    "measures": [
      {
        "id": "link-001",
        "kpiId": "measure-001",
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
    "totalMeasures": 1
  },
  "error": null
}
```

#### Use Cases

- **Personal scorecards:** All Measures assigned to a person
- **Individual accountability:** Track person-specific metrics
- **Performance reviews:** Measures for individual evaluation

---

### 6. Link Measure to Person

Add a Measure to a person's personal scorecard.

**Endpoint:** `POST /people/{personId}/measures:link`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `personId` | string (GUID) | **Yes** | Person identifier |

#### Request Body

```json
{
  "kpiId": "measure-456e7890-e89b-12d3-a456-426614174001",
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
| `kpiId` | string (GUID) | **Yes** | Measure to link |
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
    "kpiId": "measure-456e7890-e89b-12d3-a456-426614174001",
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
- **Measure must exist:** MeasureId must be valid in tenant
- **Duplicate prevention:** Same Measure can be linked to same person only once (unless different contexts)

---

### 7. Unlink Measure from Person

Remove a Measure from a person's personal scorecard.

**Endpoint:** `POST /people/{personId}/measures:unlink`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `personId` | string (GUID) | **Yes** | Person identifier |

#### Request Body

```json
{
  "kpiId": "measure-456e7890-e89b-12d3-a456-426614174001"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `kpiId` | string (GUID) | **Yes** | Measure to unlink |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "message": "Measure unlinked successfully"
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
  "error": "Measure not linked to this person"
}
```

---

## Strategy Measures Endpoints

### 8. Get Strategy Measures

Get all Measures linked to a specific strategy.

**Endpoint:** `GET /strategies/{strategyId}/measures`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `strategyId` | string (GUID) | **Yes** | Strategy identifier |

#### Request Example

```http
GET /strategies/strategy-345e6789-e89b-12d3-a456-426614174004/measures
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
    "measures": [
      {
        "id": "link-001",
        "kpiId": "measure-001",
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
    "totalMeasures": 1
  },
  "error": null
}
```

#### Use Cases

- **Strategy tracking:** All Measures measuring progress toward a strategy
- **Multi-Measure strategies:** Strategies tracked by multiple metrics
- **Cascading metrics:** Strategy Measures roll up to goal Measures

---

## Data Models

### Link Types

```typescript
type LinkType = "goal" | "personal" | "strategy";
```

- **goal:** Measure tracks a specific goal
- **personal:** Measure is on a person's personal scorecard
- **strategy:** Measure measures a strategy

### Threshold Percentage

- **Range:** 0 - 100
- **Meaning:** Completion threshold for the Measure (e.g., 80% = "on track" at 80% of target)
- **Usage:** UI can show red/yellow/green status based on `currentValue` vs `targetValue` at threshold

### Weight

- **Range:** Any positive decimal
- **Meaning:** Relative importance for weighted calculations
- **Default:** 1.0
- **Usage:** When calculating weighted averages of multiple Measures

### Display Order

- **Range:** Any positive integer
- **Meaning:** Sort order in UI (ascending)
- **Usage:** Controls how Measures are listed on scorecards/dashboards

---

## Business Rules

### Link Creation

1. **Entity Validation:** All referenced entities (Measure, person, goal, strategy) must exist in tenant
2. **Duplicate Prevention:** Cannot create duplicate links (same Measure + same target entity)
3. **Person Requirement:** `personId` is always required (owner/responsible party)
4. **Context Flexibility:** Can link Measure to goal only, person only, strategy only, or combinations

### Primary Measure

- **Goal Context:** Each goal can have ONE primary Measure
- **Setting Primary:** Setting a new Measure as primary automatically unsets previous primary for that goal
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
| 400 | Missing required field | "MeasureId is required" |
| 400 | Invalid threshold | "Threshold must be between 0 and 100" |
| 401 | Missing/invalid token | "Unauthorized" |
| 403 | Insufficient permissions | "Access denied to this Measure link" |
| 404 | Link not found | "Measure link not found" |
| 404 | Measure not linked | "Measure not linked to this person" |
| 409 | Duplicate link | "Measure already linked to this goal" |
| 500 | Server error | "Internal server error" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
import { traction } from './traction';

// Get all links for a Measure
const links = await traction.get<MeasureLinkResponse[]>(
  `/measure-links/by-measure/${kpiId}`
);

// Link Measure to person (personal scorecard)
const personalLink = await traction.post<MeasureLinkResponse>(
  `/people/${personId}/measures:link`,
  {
    kpiId: kpiId,
    thresholdPct: 85.0,
    linkType: 'personal',
    weight: 1.0
  }
);

// Get person's personal scorecard
const scorecard = await traction.get<PersonalScorecardResponse>(
  `/people/${personId}/measures`
);

// Update link configuration
await traction.put(`/measure-links/${linkId}`, {
  thresholdPct: 90.0,
  isPrimary: true,
  weight: 2.0
});

// Delete link
await traction.delete(`/measure-links/${linkId}`);

// Get strategy Measures
const strategyMeasures = await traction.get<StrategyMeasuresResponse>(
  `/strategies/${strategyId}/measures`
);
```

---

## Migration from v6

### Deprecated Endpoints (Removed in v7)

| Old Endpoint (v6) | New Endpoint (v7) | Notes |
|-------------------|-------------------|-------|
| `POST /goals/{goalId}/measures:link` | `POST /measure-links` + specify `goalId` | Resource-based design |
| `POST /goals/{goalId}/measures:unlink` | `DELETE /measure-links/{linkId}` | Use link ID |
| `GET /goals/{goalId}/measures` | `GET /measure-links?goalId={goalId}` | Query parameter |
| `GET /measures/{kpiId}/linked-goals` | `GET /measure-links/by-measure/{kpiId}` | Renamed for clarity |

### Key Differences

**v6 (GoalMeasureLink):**
- Nested under goals: `/goals/{goalId}/measures`
- Goal-centric design
- Limited to goal-Measure relationships

**v7 (MeasureLink):**
- Top-level resource: `/measure-links`
- Measure-centric design
- Supports goal, person, strategy relationships
- First-class link entities with IDs

---

## Related APIs

- **[Measures API](./measures-api.md)** - Manage Measures
- **[Measure Data API](./measure-data-api.md)** - Record Measure values, targets, actuals
- **[Goals API](./goals-api.md)** - Manage goals
- **[Strategies API](./strategies-api.md)** - Manage strategies
- **[People API](./people-api.md)** - Manage people/team members

---

## Changelog

### v7.0 (December 23, 2025)
- ✨ New MeasureLink design replacing GoalMeasureLink (Issue #374)
- ✅ Documented 8 endpoints across 3 controllers
- ✨ Added personal scorecard endpoints (`/people/{personId}/measures`)
- ✨ Added strategy Measure endpoints (`/strategies/{strategyId}/measures`)
- ✨ Resource-based link management (`/measure-links`)
- 📝 Complete request/response examples for all endpoints
- 📝 Business rules, validation, error handling documented
- 📝 Migration guide from v6 GoalMeasureLink pattern

### v6.0 (December 21, 2025)
- ⚠️ Deprecated GoalMeasureLink design

---

**[← Back to Traction Service Index](./README.md)**
