# Measure Data API Specification

**Version:** 7.0  
**Last Updated:** December 23, 2025  
**Base Path:** `/measure-links/{linkId}`  
**Controller:** `MeasureDataController.cs`

## Overview

The Measure Data API manages target values and actual measurements for Measure links. This is the v7 unified data model that replaced the deprecated MeasureMilestone, MeasureActual, and MeasureReading entities (issue #374).

### Key Features
- **Targets:** Set expected, optimal, and minimal target values
- **Actuals:** Record measured values and estimates
- **Time-series data:** Track Measure progress over time
- **Override support:** Manual corrections with audit trail
- **Replan triggers:** Flag actuals that require goal replanning
- **Combined queries:** Get all targets + actuals in one request

### Design Philosophy
- **Unified model:** Single `MeasureData` entity with subtypes (replaces 3 separate entities)
- **Link-scoped:** All data is associated with a Measure link (not just a Measure)
- **Category + Subtype:** `Target` (Expected/Optimal/Minimal) or `Actual` (Measured/Estimate)
- **Historical tracking:** All values are preserved with timestamps

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Target Endpoints

### 1. Get Targets

Retrieve all target values for a Measure link.

**Endpoint:** `GET /measure-links/{linkId}/targets`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `targetSubtype` | enum | No | Filter by subtype: `Expected`, `Optimal`, `Minimal` |

#### Request Example

```http
GET /measure-links/link-123/targets?targetSubtype=Expected
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "measureLinkId": "link-123",
    "targetSubtypeFilter": "Expected",
    "targets": [
      {
        "id": "target-001",
        "measureLinkId": "link-123",
        "dataCategory": "Target",
        "targetSubtype": "Expected",
        "actualSubtype": null,
        "postValue": 50000.00,
        "postDate": "2025-12-31T00:00:00Z",
        "measuredPeriodStartDate": "2025-12-01T00:00:00Z",
        "label": "Q4 2025 Target",
        "confidenceLevel": 80,
        "rationale": "Based on historical growth trends",
        "originalValue": null,
        "isManualOverride": false,
        "overrideComment": null,
        "dataSource": null,
        "sourceReferenceId": null,
        "triggersReplan": false,
        "replanThresholdExceeded": false,
        "createdAt": "2025-10-01T10:00:00Z",
        "updatedAt": "2025-10-01T10:00:00Z"
      }
    ],
    "totalCount": 1
  },
  "error": null
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (GUID) | Unique Measure data entry identifier |
| `measureLinkId` | string (GUID) | Associated Measure link |
| `dataCategory` | enum | `Target` or `Actual` |
| `targetSubtype` | enum | For targets: `Expected`, `Optimal`, `Minimal` |
| `actualSubtype` | enum | For actuals: `Measured`, `Estimate` |
| `postValue` | decimal | The value (target or actual) |
| `postDate` | datetime | Target date or measurement date |
| `measuredPeriodStartDate` | datetime | Start of the measurement period |
| `label` | string | Human-readable label (e.g., "Q4 2025 Target") |
| `confidenceLevel` | int | Confidence percentage (0-100) |
| `rationale` | string | Explanation/justification for the value |
| `originalValue` | decimal | Original value before override (if overridden) |
| `isManualOverride` | boolean | Was this value manually overridden? |
| `overrideComment` | string | Comment explaining the override |
| `dataSource` | enum | Where data came from (e.g., `Manual`, `Automated`, `Integration`) |
| `sourceReferenceId` | string | External system reference |
| `triggersReplan` | boolean | Does this actual trigger goal replanning? |
| `replanThresholdExceeded` | boolean | Was threshold exceeded? |
| `createdAt` | datetime | When entry was created |
| `updatedAt` | datetime | Last update timestamp |

#### Target Subtypes

- **Expected:** Standard/baseline target (most common)
- **Optimal:** Stretch goal or best-case scenario
- **Minimal:** Minimum acceptable performance threshold

---

### 2. Create Target

Set a new target value for a Measure link.

**Endpoint:** `POST /measure-links/{linkId}/targets`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Request Body

```json
{
  "targetSubtype": "Expected",
  "targetValue": 50000.00,
  "targetDate": "2025-12-31T00:00:00Z",
  "periodStartDate": "2025-12-01T00:00:00Z",
  "label": "Q4 2025 Revenue Target",
  "confidenceLevel": 80,
  "rationale": "Based on current pipeline and historical conversion rates"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `targetSubtype` | enum | **Yes** | `Expected`, `Optimal`, or `Minimal` |
| `targetValue` | decimal | **Yes** | Target value |
| `targetDate` | datetime | **Yes** | When target should be achieved |
| `periodStartDate` | datetime | No | Start of measurement period |
| `label` | string | No | Human-readable label |
| `confidenceLevel` | int | No | Confidence percentage (0-100) |
| `rationale` | string | No | Explanation for this target |

#### Response

**Status:** `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "target-new-001",
    "measureLinkId": "link-123",
    "dataCategory": "Target",
    "targetSubtype": "Expected",
    "postValue": 50000.00,
    "postDate": "2025-12-31T00:00:00Z",
    "measuredPeriodStartDate": "2025-12-01T00:00:00Z",
    "label": "Q4 2025 Revenue Target",
    "confidenceLevel": 80,
    "rationale": "Based on current pipeline and historical conversion rates",
    "createdAt": "2025-12-23T16:30:00Z",
    "updatedAt": "2025-12-23T16:30:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Multiple targets per subtype:** Can have multiple Expected/Optimal/Minimal targets for different time periods
- **Date ranges:** `targetDate` is when the target should be achieved; `periodStartDate` is the measurement period start
- **Confidence level:** Higher values indicate more certainty about achieving the target

---

### 3. Update Target

Update an existing target value or properties.

**Endpoint:** `PUT /measure-links/{linkId}/targets/{targetId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |
| `targetId` | string (GUID) | **Yes** | Target entry identifier |

#### Request Body

```json
{
  "targetValue": 55000.00,
  "label": "Q4 2025 Revenue Target (Revised)",
  "confidenceLevel": 85,
  "rationale": "Updated based on new deal closures"
}
```

#### Request Fields

All fields are optional. Only provided fields will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `targetValue` | decimal | Updated target value |
| `label` | string | Updated label |
| `confidenceLevel` | int | Updated confidence level (0-100) |
| `rationale` | string | Updated rationale |

**Note:** Cannot change `targetSubtype` or `targetDate` via update. Delete and recreate instead.

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "target-001",
    "measureLinkId": "link-123",
    "dataCategory": "Target",
    "targetSubtype": "Expected",
    "postValue": 55000.00,
    "postDate": "2025-12-31T00:00:00Z",
    "label": "Q4 2025 Revenue Target (Revised)",
    "confidenceLevel": 85,
    "rationale": "Updated based on new deal closures",
    "updatedAt": "2025-12-23T17:00:00Z"
  },
  "error": null
}
```

---

### 4. Delete Target

Remove a target entry.

**Endpoint:** `DELETE /measure-links/{linkId}/targets/{targetId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |
| `targetId` | string (GUID) | **Yes** | Target entry identifier |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "message": "Target deleted successfully"
  },
  "error": null
}
```

#### Business Rules

- **Soft delete:** Target is marked as deleted but preserved for historical analysis
- **Cascade:** Does not affect actuals or the Measure link itself

---

## Actual Endpoints

### 5. Get Actuals

Retrieve all actual measurements for a Measure link.

**Endpoint:** `GET /measure-links/{linkId}/actuals`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actualSubtype` | enum | No | Filter by subtype: `Measured`, `Estimate` |

#### Request Example

```http
GET /measure-links/link-123/actuals?actualSubtype=Measured
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "measureLinkId": "link-123",
    "actuals": [
      {
        "id": "actual-001",
        "measureLinkId": "link-123",
        "dataCategory": "Actual",
        "targetSubtype": null,
        "actualSubtype": "Measured",
        "postValue": 48500.00,
        "postDate": "2025-12-15T00:00:00Z",
        "measuredPeriodStartDate": "2025-12-01T00:00:00Z",
        "dataSource": "Automated",
        "sourceReferenceId": "stripe-mrr-dec-2025",
        "rationale": "Monthly recurring revenue from Stripe",
        "originalValue": null,
        "isManualOverride": false,
        "triggersReplan": false,
        "replanThresholdExceeded": false,
        "createdAt": "2025-12-15T08:00:00Z",
        "updatedAt": "2025-12-15T08:00:00Z"
      }
    ],
    "totalCount": 1
  },
  "error": null
}
```

#### Actual Subtypes

- **Measured:** Actual recorded value from a measurement or data source
- **Estimate:** Projected or estimated value (not yet measured)

---

### 6. Record Actual

Record a new actual measurement or estimate.

**Endpoint:** `POST /measure-links/{linkId}/actuals`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Request Body

```json
{
  "actualSubtype": "Measured",
  "actualValue": 48500.00,
  "measurementDate": "2025-12-15T00:00:00Z",
  "periodStartDate": "2025-12-01T00:00:00Z",
  "dataSource": "Automated",
  "sourceReferenceId": "stripe-mrr-dec-2025",
  "rationale": "Automated sync from Stripe"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `actualSubtype` | enum | **Yes** | `Measured` or `Estimate` |
| `actualValue` | decimal | **Yes** | Actual measured/estimated value |
| `measurementDate` | datetime | **Yes** | When value was measured |
| `periodStartDate` | datetime | No | Start of measurement period |
| `dataSource` | string | No | Where data came from (e.g., "Manual", "Stripe", "Salesforce") |
| `sourceReferenceId` | string | No | External system reference ID |
| `rationale` | string | No | Explanation or context |

#### Response

**Status:** `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "actual-new-001",
    "measureLinkId": "link-123",
    "dataCategory": "Actual",
    "actualSubtype": "Measured",
    "postValue": 48500.00,
    "postDate": "2025-12-15T00:00:00Z",
    "measuredPeriodStartDate": "2025-12-01T00:00:00Z",
    "dataSource": "Automated",
    "sourceReferenceId": "stripe-mrr-dec-2025",
    "rationale": "Automated sync from Stripe",
    "createdAt": "2025-12-23T16:45:00Z",
    "updatedAt": "2025-12-23T16:45:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Historical series:** All actuals are preserved for time-series analysis
- **Measured vs Estimate:** Use `Measured` for confirmed values, `Estimate` for projections
- **Data source tracking:** `dataSource` and `sourceReferenceId` provide audit trail

---

### 7. Override Actual

Manually override an actual value with a correction.

**Endpoint:** `PUT /measure-links/{linkId}/actuals/{actualId}/override`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |
| `actualId` | string (GUID) | **Yes** | Actual entry identifier |

#### Request Body

```json
{
  "newValue": 49000.00,
  "overrideComment": "Corrected for refunds not reflected in automated sync"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `newValue` | decimal | **Yes** | Corrected value |
| `overrideComment` | string | **Yes** | Explanation for the override |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "actual-001",
    "measureLinkId": "link-123",
    "dataCategory": "Actual",
    "actualSubtype": "Measured",
    "postValue": 49000.00,
    "originalValue": 48500.00,
    "isManualOverride": true,
    "overrideComment": "Corrected for refunds not reflected in automated sync",
    "updatedAt": "2025-12-23T17:15:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Audit trail:** Original value is preserved in `originalValue` field
- **Flag set:** `isManualOverride` is set to `true`
- **Required comment:** Override comment is mandatory for accountability

---

### 8. Mark Replan Trigger

Flag an actual as triggering goal replanning.

**Endpoint:** `POST /measure-links/{linkId}/actuals/{actualId}/replan-trigger`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |
| `actualId` | string (GUID) | **Yes** | Actual entry identifier |

#### Request Body

```json
{
  "thresholdExceeded": true,
  "autoAdjustmentApplied": false
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thresholdExceeded` | boolean | **Yes** | Was performance threshold exceeded? |
| `autoAdjustmentApplied` | boolean | No | Was an automatic adjustment made? |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "actual-001",
    "measureLinkId": "link-123",
    "triggersReplan": true,
    "replanThresholdExceeded": true,
    "updatedAt": "2025-12-23T17:30:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Replan workflow:** Flags actual as requiring attention for goal replanning
- **Threshold tracking:** Records whether performance threshold was exceeded
- **Dashboard visibility:** Replan-triggering actuals can be surfaced on dashboards

---

## Combined Data Endpoint

### 9. Get All Series

Retrieve all targets and actuals for a Measure link in one request.

**Endpoint:** `GET /measure-links/{linkId}/all-series`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `linkId` | string (GUID) | **Yes** | Measure link identifier |

#### Request Example

```http
GET /measure-links/link-123/all-series
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "measureLinkId": "link-123",
    "targets": {
      "measureLinkId": "link-123",
      "expected": [
        {
          "id": "target-001",
          "postValue": 50000.00,
          "postDate": "2025-12-31T00:00:00Z",
          "label": "Q4 2025 Target"
        }
      ],
      "optimal": [
        {
          "id": "target-002",
          "postValue": 60000.00,
          "postDate": "2025-12-31T00:00:00Z",
          "label": "Q4 2025 Stretch Goal"
        }
      ],
      "minimal": [
        {
          "id": "target-003",
          "postValue": 45000.00,
          "postDate": "2025-12-31T00:00:00Z",
          "label": "Q4 2025 Minimum"
        }
      ],
      "totalTargets": 3
    },
    "actuals": [
      {
        "id": "actual-001",
        "actualSubtype": "Measured",
        "postValue": 48500.00,
        "postDate": "2025-12-15T00:00:00Z"
      }
    ],
    "latestActual": {
      "id": "actual-001",
      "actualSubtype": "Measured",
      "postValue": 48500.00,
      "postDate": "2025-12-15T00:00:00Z"
    },
    "totalActuals": 1
  },
  "error": null
}
```

#### Use Cases

- **Dashboard charts:** Single request for complete time-series visualization
- **Performance comparison:** Compare actuals against all three target levels
- **Progress tracking:** Show current performance vs. targets

---

## Data Models

### Data Category Enum

```typescript
enum DataCategory {
  Target = "Target",  // Target values
  Actual = "Actual"   // Actual measurements
}
```

### Target Subtype Enum

```typescript
enum TargetSubtype {
  Expected = "Expected",  // Standard/baseline target
  Optimal = "Optimal",    // Stretch goal
  Minimal = "Minimal"     // Minimum acceptable
}
```

### Actual Subtype Enum

```typescript
enum ActualSubtype {
  Measured = "Measured",  // Actual measured value
  Estimate = "Estimate"   // Projected/estimated value
}
```

### Data Source Enum

```typescript
enum DataSource {
  Manual = "Manual",           // Manually entered
  Automated = "Automated",     // Automated sync/import
  Integration = "Integration"  // External system integration
}
```

---

## Business Rules

### Targets

1. **Multiple targets per period:** Can set Expected, Optimal, and Minimal targets for the same time period
2. **Time-series:** Can have multiple target entries for different future dates
3. **Confidence level:** Optional 0-100 value indicating certainty about achieving the target
4. **Rationale:** Recommended to document why a target was set at a specific value

### Actuals

1. **Historical preservation:** All actuals are kept for historical analysis
2. **Measured vs Estimate:**
   - Use `Measured` for confirmed values from data sources
   - Use `Estimate` for projections or manual estimates
3. **Override capability:** Can correct values with audit trail (original value + comment)
4. **Data source tracking:** Records where data came from and reference ID

### Replan Triggers

- **Threshold-based:** System can flag actuals that exceed variance thresholds
- **Manual flagging:** Users can mark actuals as triggering replanning
- **Dashboard surfacing:** Replan-triggered actuals can be highlighted on dashboards

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
| 400 | Missing required field | "TargetValue is required" |
| 400 | Invalid subtype | "Invalid target subtype. Must be 'Expected', 'Optimal', or 'Minimal'" |
| 401 | Missing/invalid token | "Unauthorized" |
| 403 | Insufficient permissions | "Access denied to this Measure link" |
| 404 | Entry not found | "Target not found" |
| 422 | Validation failure | "MeasurementDate cannot be in the future" |
| 500 | Server error | "Internal server error" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
import { traction } from './traction';

// Get all targets for a Measure link
const targets = await traction.get<MeasureTargetsListResponse>(
  `/measure-links/${linkId}/targets`
);

// Create an expected target
const newTarget = await traction.post<MeasureDataResponse>(
  `/measure-links/${linkId}/targets`,
  {
    targetSubtype: 'Expected',
    targetValue: 50000.00,
    targetDate: '2025-12-31T00:00:00Z',
    label: 'Q4 2025 Target',
    confidenceLevel: 80,
    rationale: 'Based on pipeline analysis'
  }
);

// Record a measured actual
const actual = await traction.post<MeasureDataResponse>(
  `/measure-links/${linkId}/actuals`,
  {
    actualSubtype: 'Measured',
    actualValue: 48500.00,
    measurementDate: '2025-12-15T00:00:00Z',
    dataSource: 'Automated',
    sourceReferenceId: 'stripe-mrr-dec-2025'
  }
);

// Override an actual with correction
await traction.put(`/measure-links/${linkId}/actuals/${actualId}/override`, {
  newValue: 49000.00,
  overrideComment: 'Corrected for data sync issue'
});

// Get all data (targets + actuals) for charts
const allData = await traction.get<AllKpiDataResponse>(
  `/measure-links/${linkId}/all-series`
);

// Chart the data
renderChart({
  expected: allData.data.targets.expected,
  optimal: allData.data.targets.optimal,
  minimal: allData.data.targets.minimal,
  actuals: allData.data.actuals,
  latest: allData.data.latestActual
});
```

---

## Migration from v6

### Deprecated Entities (Removed in v7)

| Old Entity (v6) | New Entity (v7) | Notes |
|-----------------|-----------------|-------|
| `MeasureMilestone` | `MeasureData` (Target subtype) | Unified into single entity |
| `MeasureActual` | `MeasureData` (Actual subtype) | Unified into single entity |
| `MeasureReading` | `MeasureData` (Actual subtype) | Merged with MeasureActual |

### Key Differences

**v6 (Separate entities):**
- `MeasureMilestone` for target values
- `MeasureActual` for measured values
- `MeasureReading` for estimates
- Different endpoints for each type

**v7 (Unified model):**
- Single `MeasureData` entity with `DataCategory` (Target/Actual)
- Target subtypes: Expected/Optimal/Minimal
- Actual subtypes: Measured/Estimate
- Consistent endpoints: `/measure-links/{linkId}/targets` and `/measure-links/{linkId}/actuals`

### Benefits of v7 Design

- ✅ Single entity reduces complexity
- ✅ Consistent API patterns
- ✅ Easier querying (all data in one table)
- ✅ Better time-series support
- ✅ Unified audit trail

---

## Related APIs

- **[Measure Links API](./measure-links-api.md)** - Link KPIs to goals/persons/strategies
- **[KPIs API](./measures-api.md)** - Manage KPIs
- **[Goals API](./goals-api.md)** - Manage goals

---

## Changelog

### v7.0 (December 23, 2025)
- ✨ New unified MeasureData model replacing MeasureMilestone/MeasureActual/MeasureReading (Issue #374)
- ✅ Documented 9 endpoints with complete examples
- ✨ Target subtypes: Expected, Optimal, Minimal
- ✨ Actual subtypes: Measured, Estimate
- ✨ Override capability with audit trail
- ✨ Replan trigger flagging
- ✨ Combined all-series endpoint for charts
- 📝 Complete request/response examples
- 📝 Business rules and validation documented
- 📝 Migration guide from v6 entities

### v6.0 (December 21, 2025)
- ⚠️ Deprecated MeasureMilestone, MeasureActual, MeasureReading

---

**[← Back to Traction Service Index](./README.md)**
