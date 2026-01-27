# Measures API Specification

**Version:** 7.3  
**Last Updated:** January 9, 2026  
**Base Path:** `/measures`  
**Controller:** `MeasuresController.cs`

## Overview

The Measures API manages Key Performance Indicators (Measures) within the PurposePath system. Measures measure progress toward strategies and goals, supporting both catalog-based Measures (from the Measure library) and custom user-defined Measures.

### Key Features
- List Measures with filtering by owner, goal, or strategy
- Create catalog-based or custom Measures
- Update Measure details or current values
- Soft delete Measures (preserves historical data)
- Query Measure-goal relationships
- Retrieve Measures catalog for designing a new goal (no goalId required)
- Retrieve Measure catalog for new (unpersisted) goals

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 0. Get Measure Summary

**NEW** Issue #526

Retrieve comprehensive MEASURE summary with filtering, aggregations, and detailed measure data. This endpoint provides a complete view of all measures with their relationships, progress, and summary statistics.

**Endpoint:** `GET /measures/summary`

**Headers:**
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Query Parameters:**
- `category` (optional): Filter by measure category (e.g., "Finance", "Sales", "Customer Success")
- `ownerId` (optional): Filter by owner (person ID)
- `status` (optional): Filter by measure status ("active" or "inactive")
- `progressStatus` (optional): Filter by progress status ("on_track", "at_risk", "behind", "no_data")
- `period` (optional): Filter by aggregation period ("daily", "weekly", "monthly", "quarterly", "yearly")
- `includeInactive` (optional): Include inactive measures (default: true)
- `maxDataPoints` (optional): Maximum trend data points to return (default: 5, 0 = all)

**Response 200**

```json
{
  "success": true,
  "data": {
    "measures": [
      {
        "measureId": "m-001",
        "measureName": "Monthly Recurring Revenue",
        "description": "Total monthly recurring revenue from all subscriptions",
        "unit": "$",
        "direction": "up",
        "type": "quantitative",
        "category": "Finance",
        
        "currentValue": 125000,
        "currentValueDate": "2025-01-08",
        
        "latestTarget": {
          "targetId": "t-001",
          "targetValue": 150000,
          "targetDate": "2025-01-31",
          "optimalValue": 175000,
          "minimalValue": 140000,
          "label": "Q1 Target"
        },
        
        "latestActual": {
          "actualId": "a-001",
          "actualValue": 125000,
          "measurementDate": "2025-01-08",
          "actualSubtype": "Measured",
          "recordedBy": "user-123",
          "recordedByName": "John Smith"
        },
        
        "progress": {
          "progressPercentage": 83.3,
          "status": "on_track",
          "variance": -25000,
          "variancePercentage": -16.7,
          "daysUntilTarget": 23,
          "isOverdue": false
        },
        
        "owner": {
          "ownerId": "person-456",
          "ownerName": "Jane Doe",
          "ownerEmail": "jane.doe@example.com"
        },
        
        "goalLinks": [
          {
            "linkId": "link-001",
            "goalId": "goal-001",
            "goalTitle": "Increase Revenue",
            "goalIntent": "Grow monthly recurring revenue to support expansion",
            "goalStatus": "active",
            "isPrimary": true,
            "thresholdPct": 80,
            "riskThresholdPct": 50,
            "weight": 1.0,
            "displayOrder": 0,
            "linkedAt": "2025-01-01T00:00:00Z",
            "linkOwner": {
              "personId": "person-456",
              "personName": "Jane Doe"
            },
            "progress": {
              "progressPercentage": 83.3,
              "status": "on_track",
              "variance": -25000,
              "variancePercentage": -16.7,
              "daysUntilTarget": 23,
              "isOverdue": false
            }
          }
        ],
        
        "strategyLinks": [
          {
            "linkId": "link-003",
            "strategyId": "strat-001",
            "strategyTitle": "Enterprise Sales Initiative",
            "strategyDescription": "Focus on closing enterprise deals",
            "strategyStatus": "in_progress",
            "goalId": "goal-001",
            "goalTitle": "Increase Revenue",
            "thresholdPct": 85,
            "riskThresholdPct": 50,
            "weight": 0.7,
            "displayOrder": 0,
            "linkedAt": "2025-01-02T00:00:00Z",
            "linkOwner": {
              "personId": "person-456",
              "personName": "Jane Doe"
            },
            "progress": {
              "progressPercentage": 83.3,
              "status": "on_track",
              "variance": -25000,
              "variancePercentage": -16.7,
              "daysUntilTarget": 23,
              "isOverdue": false
            }
          }
        ],
        
        "measurementConfig": {
          "aggregationType": "sum",
          "aggregationPeriod": "monthly",
          "valueType": "aggregate",
          "interpolationMethod": "linear",
          "measurementFrequency": "daily"
        },
        
        "sharingInfo": {
          "isShared": true,
          "totalGoalLinks": 2,
          "totalStrategyLinks": 1,
          "catalogId": null,
          "isCustom": true
        },
        
        "metadata": {
          "createdAt": "2024-12-15T10:00:00Z",
          "updatedAt": "2025-01-08T14:30:00Z",
          "createdBy": "user-456"
        },
        
        "trendData": [
          {
            "date": "2024-12-01",
            "value": 100000,
            "isTarget": false,
            "isEstimate": false
          },
          {
            "date": "2024-12-15",
            "value": 110000,
            "isTarget": false,
            "isEstimate": false
          },
          {
            "date": "2025-01-01",
            "value": 120000,
            "isTarget": false,
            "isEstimate": false
          },
          {
            "date": "2025-01-08",
            "value": 125000,
            "isTarget": false,
            "isEstimate": false
          },
          {
            "date": "2025-01-31",
            "value": 150000,
            "isTarget": true,
            "isEstimate": false
          }
        ]
      }
    ],
    
    "summary": {
      "totalMeasures": 47,
      "totalActiveMeasures": 42,
      "totalInactiveMeasures": 5,
      
      "statusBreakdown": {
        "onTrack": 28,
        "atRisk": 10,
        "behind": 4,
        "noData": 5
      },
      
      "categoryBreakdown": [
        {
          "category": "Finance",
          "count": 12,
          "onTrack": 8,
          "atRisk": 3,
          "behind": 1
        },
        {
          "category": "Sales",
          "count": 10,
          "onTrack": 7,
          "atRisk": 2,
          "behind": 1
        },
        {
          "category": "Customer Success",
          "count": 8,
          "onTrack": 5,
          "atRisk": 2,
          "behind": 1
        }
      ],
      
      "ownerBreakdown": [
        {
          "ownerId": "person-456",
          "ownerName": "Jane Doe",
          "measureCount": 8,
          "onTrackCount": 6
        },
        {
          "ownerId": "person-789",
          "ownerName": "Bob Johnson",
          "measureCount": 5,
          "onTrackCount": 4
        }
      ],
      
      "overallHealthScore": 73.5
    },
    
    "metadata": {
      "generatedAt": "2025-01-09T10:30:45Z",
      "queryDurationMs": 124,
      "filters": {
        "category": null,
        "ownerId": null,
        "status": null,
        "progressStatus": null,
        "period": null,
        "includeInactive": true,
        "maxDataPoints": 5
      },
      "version": "1.0"
    }
  },
  "error": null,
  "timestamp": "2025-01-09T10:30:45Z"
}
```

**Progress Status Calculation**

The `progress.status` field is calculated using the following algorithm:

```
Given:
- thresholdPct (e.g., 80)
- riskThresholdPct (e.g., 50)
- variancePercentage = ((currentValue - expectedValue) / |totalChange|) * 100

Status determination:
- If variancePercentage >= (thresholdPct - 100) -> on_track
- If variancePercentage < (thresholdPct - 100) AND variancePercentage >= (riskThresholdPct - 100) -> behind
- If variancePercentage < (riskThresholdPct - 100) -> at_risk
- No data -> no_data

Example with thresholdPct = 80, riskThresholdPct = 50:
- variancePercentage >= -20 -> on_track
- -50 <= variancePercentage < -20 -> behind
- variancePercentage < -50 -> at_risk
```

**Response 400 Bad Request**

```json
{
  "success": false,
  "data": null,
  "error": "Invalid filter parameters",
  "timestamp": "2025-01-09T10:30:45Z"
}
```

**Response 401 Unauthorized**

```json
{
  "success": false,
  "data": null,
  "error": "Unauthorized - Invalid or expired token",
  "timestamp": "2025-01-09T10:30:45Z"
}
```

**Response 500 Internal Server Error**

```json
{
  "success": false,
  "data": null,
  "error": "Internal server error",
  "timestamp": "2025-01-09T10:30:45Z"
}
```

**Implementation:**
- Controller: `MeasuresController.GetMeasureSummary()`
- Handler: `GetMeasureSummaryQueryHandler`
- Query: `GetMeasureSummaryQuery`
- Response DTOs: `MeasureSummaryResponse`, `MeasureSummaryItemResponse`, etc.

---

### 0a. Get Available Measures For New Goal (No goalId)

Retrieve the Measures catalog (catalog + tenant custom) when designing a goal that is not yet persisted. This mirrors the goal-scoped available-measures payload but does not require a `goalId`; `usageInfo.isUsedByThisGoal` is always `false`.

**Endpoint:** `GET /goals/available-measures`

**Headers:**
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response 200**

```json
{
  "success": true,
  "data": {
    "catalogMeasures": [
      {
        "id": "catalog-001",
        "name": "Monthly Recurring Revenue",
        "description": "Total predictable revenue from subscriptions",
        "category": "Financial",
        "unit": "USD",
        "direction": "increase",
        "type": "leading",
        "valueType": "currency",
        "aggregationType": "sum",
        "aggregationPeriod": "monthly",
        "calculationMethod": "Sum of all active subscription values",
        "isIntegrationEnabled": true,
        "usageInfo": {
          "goalCount": 3,
          "isUsedByThisGoal": false
        }
      }
    ],
    "tenantCustomMeasures": [
      {
        "id": "custom-measure-001",
        "name": "Customer Satisfaction Score",
        "description": "Average CSAT from post-purchase surveys",
        "category": "Customer Experience",
        "unit": "score",
        "direction": "increase",
        "type": "lagging",
        "valueType": "percentage",
        "aggregationType": "average",
        "aggregationPeriod": "monthly",
        "calculationMethod": "Average of all survey responses",
        "measureCatalogId": null,
        "isIntegrationEnabled": false,
        "createdAt": "2025-01-15T10:00:00.000Z",
        "createdBy": "user-123",
        "usageInfo": {
          "goalCount": 1,
          "isUsedByThisGoal": false
        }
      }
    ]
  },
  "error": null,
  "timestamp": "2025-12-23T11:30:00.000Z"
}
```

**Notes**
- Same schema as goal-scoped available-measures but without validating goal existence.
- `usageInfo.isUsedByThisGoal` is always `false` for this endpoint; `goalCount` still reflects usage across persisted goals.
- Use [Measure Links API](./measure-links-api.md) to link a Measure once the goal is created.

### 1. List Measures

Retrieve Measures with optional filtering.

**Endpoint:** `GET /measures`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ownerId` | string (GUID) | No | Filter by Measure owner (person responsible) |
| `goalId` | string (GUID) | No | Filter by linked goal |
| `strategyId` | string (GUID) | No | Filter by linked strategy |

**Default Behavior:** If no filter is provided, returns all Measures for the tenant (useful for dropdowns and lists).

#### Request Example

```http
GET /measures?goalId=550e8400-e29b-41d4-a716-446655440000
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "data": [
      {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "tenantId": "tenant-123",
        "name": "Monthly Recurring Revenue",
        "description": "Total MRR from all active subscriptions",
        "currentValue": 45000.00,
        "targetValue": 50000.00,
        "unit": "USD",
        "direction": "Increase",
        "type": "Leading",
        "category": "Finance",
        "measurementFrequency": "Monthly",
        "dataSource": "Stripe API",
        "catalogId": "measure-catalog-001",
        "ownerId": "owner-123",
        "strategyId": "strategy-456",
        "currentValueDate": "2025-12-15T00:00:00Z",
        "createdAt": "2025-01-15T10:30:00Z",
        "updatedAt": "2025-12-15T14:25:00Z",
        "isDeleted": false
      }
    ],
    "pagination": {
      "totalCount": 1,
      "page": 1,
      "pageSize": 50
    }
  },
  "error": null
}
```

#### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (GUID) | Unique Measure identifier |
| `tenantId` | string | Organization identifier |
| `name` | string | Measure name (max 200 chars) |
| `description` | string | Detailed description (max 1000 chars) |
| `currentValue` | decimal | Latest recorded value |
| `targetValue` | decimal | Goal/target value |
| `unit` | string | Measurement unit (e.g., "USD", "%", "count") |
| `direction` | enum | `Increase` or `Decrease` (desired trend) |
| `type` | enum | `Leading` or `Lagging` indicator |
| `category` | string | Measure category (e.g., "Finance", "Sales", "Operations") |
| `measurementFrequency` | string | How often measured (e.g., "Daily", "Weekly", "Monthly") |
| `dataSource` | string | Where data comes from |
| `catalogId` | string | If from Measure library, the catalog entry ID |
| `ownerId` | string (GUID) | Person responsible for this Measure |
| `strategyId` | string (GUID) | Linked strategy |
| `currentValueDate` | datetime | When current value was recorded |
| `createdAt` | datetime | When Measure was created |
| `updatedAt` | datetime | Last update timestamp |
| `isDeleted` | boolean | Soft delete flag |

#### Business Rules

- **Filtering Priority:** If multiple filters are provided:
  1. `ownerId` takes precedence
  2. Then `goalId`
  3. Then `strategyId`
  4. Default: All tenant Measures
- **Multi-tenancy:** Only returns Measures for the specified tenant
- **Soft Deletes:** Deleted Measures (`isDeleted: true`) are excluded by default

---

### 2. Create Measure

Create a new Measure (catalog-based or custom).

**Endpoint:** `POST /measures`

#### Request Body

```json
{
  "name": "Customer Retention Rate",
  "description": "Percentage of customers retained over a period",
  "currentValue": 85.5,
  "targetValue": 90.0,
  "unit": "%",
  "direction": "Increase",
  "type": "Lagging",
  "category": "Customer Success",
  "measurementFrequency": "Monthly",
  "dataSource": "CRM System",
  "ownerId": "owner-123",
  "strategyId": "strategy-456",
  "catalogId": "measure-catalog-002",
  "aggregationType": "Average",
  "aggregationPeriod": "Month",
  "valueType": "Percentage",
  "calculationMethod": "(Customers at End - New Customers) / Customers at Start * 100",
  "currentValueDate": "2025-12-15T00:00:00Z"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Measure name (max 200 chars) |
| `description` | string | No | Detailed description |
| `currentValue` | decimal | No | Initial value |
| `targetValue` | decimal | No | Goal value |
| `unit` | string | No | Measurement unit |
| `direction` | enum | No | `Increase` or `Decrease` |
| `type` | enum | No | `Leading` or `Lagging` |
| `category` | string | No | Measure category |
| `measurementFrequency` | No | No | Default: "Monthly" |
| `dataSource` | string | No | Data source identifier |
| `ownerId` | string (GUID) | No | Person responsible (defaults to creator) |
| `strategyId` | string (GUID) | No | Linked strategy |
| `catalogId` | string | No | Measure catalog entry (for library Measures) |
| `aggregationType` | string | No | How data is aggregated (e.g., "Sum", "Average") |
| `aggregationPeriod` | string | No | Time period for aggregation |
| `valueType` | string | No | Data type (e.g., "Number", "Percentage", "Currency") |
| `calculationMethod` | string | No | Formula or method for calculation |
| `currentValueDate` | datetime | No | When current value was recorded (defaults to now) |
| `goalId` | string (GUID) | No | **⚠️ Deprecated:** Link Measure to goal via `/measure-links` instead |

#### Response

**Status:** `201 Created`  
**Location:** `/measures/{id}`

```json
{
  "success": true,
  "data": {
    "id": "789e4567-e89b-12d3-a456-426614174000",
    "tenantId": "tenant-123",
    "name": "Customer Retention Rate",
    "description": "Percentage of customers retained over a period",
    "currentValue": 85.5,
    "targetValue": 90.0,
    "unit": "%",
    "direction": "Increase",
    "type": "Lagging",
    "category": "Customer Success",
    "measurementFrequency": "Monthly",
    "dataSource": "CRM System",
    "catalogId": "measure-catalog-002",
    "ownerId": "owner-123",
    "strategyId": "strategy-456",
    "currentValueDate": "2025-12-15T00:00:00Z",
    "createdAt": "2025-12-23T10:30:00Z",
    "updatedAt": "2025-12-23T10:30:00Z",
    "isDeleted": false
  },
  "error": null
}
```

#### Business Rules

- **Catalog vs Custom:** If `catalogId` is provided, Measure is linked to library entry; otherwise, it's custom
- **Owner Assignment:** If `ownerId` is not provided, defaults to the current user (creator)
- **Tenant Isolation:** Measure is automatically associated with the current tenant
- **⚠️ Goal Linking Deprecated:** The `goalId` field in request is deprecated. Use `/measure-links` endpoint to link Measures to goals

#### Validation Rules

- **Name:** Required, max 200 characters
- **Target Value:** Must be > 0 if provided
- **Direction:** Must be "Increase" or "Decrease" if provided
- **Type:** Must be "Leading" or "Lagging" if provided
- **Owner & Strategy IDs:** Must be valid GUIDs and exist in tenant

---

### 3. Get Measure Details

Retrieve detailed information about a specific Measure, including linked goals.

**Endpoint:** `GET /measures/{id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |

#### Request Example

```http
GET /measures/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "tenantId": "tenant-123",
    "name": "Monthly Recurring Revenue",
    "description": "Total MRR from all active subscriptions",
    "currentValue": 45000.00,
    "targetValue": 50000.00,
    "unit": "USD",
    "direction": "Increase",
    "type": "Leading",
    "category": "Finance",
    "measurementFrequency": "Monthly",
    "dataSource": "Stripe API",
    "catalogId": "measure-catalog-001",
    "ownerId": "owner-123",
    "strategyId": "strategy-456",
    "currentValueDate": "2025-12-15T00:00:00Z",
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-12-15T14:25:00Z",
    "isDeleted": false,
    "linkedGoals": [
      {
        "goalId": "goal-001",
        "goalName": "Grow Revenue",
        "linkId": "link-001",
        "isPrimary": true,
        "linkedAt": "2025-01-20T09:00:00Z"
      }
    ],
    "historicalValues": [
      {
        "value": 42000.00,
        "recordedAt": "2025-11-15T00:00:00Z"
      },
      {
        "value": 45000.00,
        "recordedAt": "2025-12-15T00:00:00Z"
      }
    ]
  },
  "error": null
}
```

#### Additional Fields (Detail Response)

| Field | Type | Description |
|-------|------|-------------|
| `linkedGoals` | array | Goals linked to this Measure |
| `linkedGoals[].goalId` | string (GUID) | Goal identifier |
| `linkedGoals[].goalName` | string | Goal name |
| `linkedGoals[].linkId` | string (GUID) | Measure link identifier |
| `linkedGoals[].isPrimary` | boolean | Is this the primary Measure for the goal? |
| `linkedGoals[].linkedAt` | datetime | When link was created |
| `historicalValues` | array | Previous Measure values (last 12) |
| `historicalValues[].value` | decimal | Historical value |
| `historicalValues[].recordedAt` | datetime | When value was recorded |

#### Error Responses

**Status:** `400 Bad Request`
```json
{
  "success": false,
  "data": null,
  "error": "Invalid Measure ID format"
}
```

**Status:** `404 Not Found`
```json
{
  "success": false,
  "data": null,
  "error": "Measure not found"
}
```

---

### 4. Update Measure

Update Measure details (name, description, target, etc.). Does not update current value — use `PUT /measures/{id}/value` for that.

**Endpoint:** `PUT /measures/{id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |

#### Request Body

```json
{
  "name": "Monthly Recurring Revenue (Updated)",
  "description": "Total MRR from all active subscriptions - Updated methodology",
  "targetValue": 55000.00,
  "unit": "USD",
  "direction": "Increase",
  "type": "Leading",
  "category": "Finance",
  "measurementFrequency": "Monthly",
  "dataSource": "Stripe API v2",
  "ownerId": "new-owner-123"
}
```

#### Request Fields

All fields are optional. Only provided fields will be updated.

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Measure name (max 200 chars) |
| `description` | string | Detailed description |
| `targetValue` | decimal | Updated target value |
| `unit` | string | Measurement unit |
| `direction` | enum | `Increase` or `Decrease` |
| `type` | enum | `Leading` or `Lagging` |
| `category` | string | Measure category |
| `measurementFrequency` | string | Measurement frequency |
| `dataSource` | string | Data source identifier |
| `ownerId` | string (GUID) | New owner (person responsible) |

**Note:** `currentValue` cannot be updated via this endpoint. Use `PUT /measures/{id}/value` instead.

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "tenantId": "tenant-123",
    "name": "Monthly Recurring Revenue (Updated)",
    "description": "Total MRR from all active subscriptions - Updated methodology",
    "currentValue": 45000.00,
    "targetValue": 55000.00,
    "unit": "USD",
    "direction": "Increase",
    "type": "Leading",
    "category": "Finance",
    "measurementFrequency": "Monthly",
    "dataSource": "Stripe API v2",
    "ownerId": "new-owner-123",
    "updatedAt": "2025-12-23T15:45:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Partial Updates:** Only provided fields are updated; others remain unchanged
- **Current Value:** Cannot be updated via this endpoint (use value endpoint)
- **Tenant & ID:** Cannot change Measure's tenant or ID
- **Catalog ID:** Cannot change `catalogId` after creation

---

### 5. Update Measure Value

Update only the current value of a Measure (records new measurement).

**Endpoint:** `PUT /measures/{id}/value`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |

#### Request Body

```json
{
  "value": 47500.00,
  "recordedAt": "2025-12-23T12:00:00Z",
  "notes": "End of Q4 2025"
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | decimal | **Yes** | New Measure value |
| `recordedAt` | datetime | No | When value was recorded (defaults to now) |
| `notes` | string | No | Additional context or notes |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "currentValue": 47500.00,
    "currentValueDate": "2025-12-23T12:00:00Z",
    "updatedAt": "2025-12-23T15:50:00Z"
  },
  "error": null
}
```

#### Business Rules

- **Historical Tracking:** Previous value is stored in history before updating
- **Timestamp:** If `recordedAt` is not provided, uses current UTC time
- **Event Publishing:** Triggers `MeasureValueUpdated` domain event
- **Percentage Change:** System calculates change from previous value

#### Validation Rules

- **Value:** Must be a valid decimal number
- **Recorded At:** Cannot be in the future
- **Notes:** Max 500 characters

---

### 6. Delete Measure

Soft delete a Measure (marks as deleted, preserves historical data).

**Endpoint:** `DELETE /measures/{id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |

#### Request Example

```http
DELETE /measures/123e4567-e89b-12d3-a456-426614174000
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

#### Response

**Status:** `204 No Content`

(No response body on success)

#### Error Responses

**Status:** `400 Bad Request`
```json
{
  "success": false,
  "data": null,
  "error": "Invalid Measure ID format"
}
```

**Status:** `404 Not Found`
```json
{
  "success": false,
  "data": null,
  "error": "Measure not found"
}
```

#### Business Rules

- **Soft Delete:** Measure is marked as deleted (`isDeleted: true`) but not physically removed
- **Historical Data:** All historical values and links are preserved
- **List Queries:** Deleted Measures are excluded from list results by default
- **Restoration:** Can be restored by admin/support team
- **Cascade:** Measure links to goals are also soft deleted

---

### 7. Get Available Measures for New Goals

Retrieve the Measure catalog for a tenant when designing a new goal that is not yet persisted. Returns the same payload as `GET /goals/{goalId}/available-measures` but does not require a `goalId`. Usage data reflects existing goal links across the tenant; `usageInfo.isUsedByThisGoal` is always `false` because no goal is supplied.

**Endpoint:** `GET /goals/available-measures`

#### Response 200

```json
{
  "success": true,
  "data": {
    "catalogMeasures": [
      {
        "id": "catalog-001",
        "name": "Monthly Recurring Revenue",
        "description": "Total predictable revenue from subscriptions",
        "category": "Financial",
        "unit": "USD",
        "direction": "increase",
        "type": "leading",
        "valueType": "currency",
        "aggregationType": "sum",
        "aggregationPeriod": "monthly",
        "calculationMethod": "Sum of all active subscription values",
        "isIntegrationEnabled": true,
        "usageInfo": {
          "goalCount": 3,
          "isUsedByThisGoal": false
        }
      }
    ],
    "tenantCustomMeasures": [
      {
        "id": "custom-measure-001",
        "name": "Customer Satisfaction Score",
        "description": "Average CSAT from post-purchase surveys",
        "category": "Customer Experience",
        "unit": "score",
        "direction": "increase",
        "type": "lagging",
        "valueType": "percentage",
        "aggregationType": "average",
        "aggregationPeriod": "monthly",
        "calculationMethod": "Average of all survey responses",
        "measureCatalogId": null,
        "isIntegrationEnabled": false,
        "createdAt": "2025-01-15T10:00:00.000Z",
        "createdBy": "user-123",
        "usageInfo": {
          "goalCount": 1,
          "isUsedByThisGoal": false
        }
      }
    ]
  },
  "error": null,
  "timestamp": "2026-01-02T00:00:00.000Z"
}
```

#### Notes

- Use when the frontend constructs a goal in-memory and needs the catalog before persisting the goal.
- Usage counts still reflect existing goal links in the tenant; `isUsedByThisGoal` remains `false`.
- Response shape matches `GET /goals/{goalId}/available-measures` for compatibility.

---

### 8. Get Measure Linked Goals (Deprecated)

⚠️ **DEPRECATED (Issue #374):** This endpoint is being migrated to the new MeasureLink design.

**Endpoint:** `GET /measures/{id}/linked-goals`

#### Current Behavior

Returns `501 Not Implemented` with migration message.

```json
{
  "success": false,
  "data": null,
  "error": "This endpoint is being migrated to the new MeasureLink design. Please use the new MeasureLink endpoints."
}
```

#### Migration Path

Use the following endpoints instead:
- **List Measure Links:** `GET /measure-links?measureId={id}`
- **Measure Details with Links:** `GET /measures/{id}` (includes `linkedGoals` in response)

See [Measure Links API](./measure-links-api.md) for details.

---

### 9. Get Measure Options (Issue #469)

Retrieve options for a Qualitative measure. Returns measure-owned options if they exist, otherwise returns inherited options from the linked catalog.

**Endpoint:** `GET /measures/{id}/options`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "options": [
      {
        "id": "opt-001",
        "measureId": "measure-123",
        "catalogId": null,
        "numericValue": 1,
        "label": "Not Met",
        "description": "Performance below 50% of target",
        "sortOrder": 1
      },
      {
        "id": "opt-002",
        "measureId": "measure-123",
        "catalogId": null,
        "numericValue": 2,
        "label": "Partially Met",
        "description": "Performance at 50-80% of target",
        "sortOrder": 2
      },
      {
        "id": "opt-003",
        "measureId": "measure-123",
        "catalogId": null,
        "numericValue": 3,
        "label": "Met",
        "description": "Performance at or above target",
        "sortOrder": 3
      }
    ],
    "isInherited": false,
    "sourceCatalogId": null
  },
  "error": null
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `options` | array | List of option objects |
| `options[].id` | string (GUID) | Unique option identifier |
| `options[].measureId` | string (GUID) | Measure ID (null if inherited) |
| `options[].catalogId` | string (GUID) | Catalog ID (null if measure-owned) |
| `options[].numericValue` | integer | Numeric value for aggregation |
| `options[].label` | string | Display label shown to users |
| `options[].description` | string | Optional explanation |
| `options[].sortOrder` | integer | Display order |
| `isInherited` | boolean | True if options come from catalog |
| `sourceCatalogId` | string (GUID) | Catalog ID if inherited |

#### Business Rules

- Returns empty array for Quantitative measures
- Measure-owned options take precedence over catalog options
- Options are sorted by `sortOrder`

---

### 10. Set Measure Options (Issue #469)

Set or replace all options for a Qualitative measure. This creates measure-owned options.

**Endpoint:** `PUT /measures/{id}/options`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |

#### Request Body

```json
{
  "options": [
    {
      "numericValue": 1,
      "label": "Not Met",
      "description": "Performance below 50% of target",
      "sortOrder": 1
    },
    {
      "numericValue": 2,
      "label": "Partially Met",
      "description": "Performance at 50-80% of target",
      "sortOrder": 2
    },
    {
      "numericValue": 3,
      "label": "Met",
      "description": "Performance at or above target",
      "sortOrder": 3
    }
  ]
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `options` | array | **Yes** | Options to set (minimum 2) |
| `options[].numericValue` | integer | **Yes** | Unique numeric value for aggregation |
| `options[].label` | string | **Yes** | Display label (max 100 chars) |
| `options[].description` | string | No | Explanation text |
| `options[].sortOrder` | integer | No | Display order (defaults to numericValue) |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "options": [...],
    "isInherited": false,
    "sourceCatalogId": null
  },
  "error": null
}
```

#### Validation Rules

- Minimum 2 options required
- `numericValue` must be unique within the measure
- `label` is required and max 100 characters
- Replaces all existing measure-owned options

---

### 11. Delete Measure Options (Issue #469)

Delete all measure-owned options. After deletion, the measure will inherit options from its linked catalog (if any).

**Endpoint:** `DELETE /measures/{id}/options`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |

#### Response

**Status:** `204 No Content`

(No response body on success)

#### Business Rules

- Only deletes measure-owned options
- Does not affect catalog options
- After deletion, measure inherits from catalog (if linked)

---

### 12. Copy Options from Catalog (Issue #469)

Copy options from a catalog entry to create measure-owned options. Use this to "detach" a measure from its catalog's options for customization.

**Endpoint:** `POST /measures/{id}/options/copy-from-catalog/{catalogId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | Measure identifier |
| `catalogId` | string (GUID) | **Yes** | Catalog identifier to copy from |

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "data": {
    "options": [
      {
        "id": "new-opt-001",
        "measureId": "measure-123",
        "catalogId": null,
        "numericValue": 1,
        "label": "Not Met",
        "description": "Performance below target",
        "sortOrder": 1
      },
      ...
    ],
    "isInherited": false,
    "sourceCatalogId": null
  },
  "error": null
}
```

#### Business Rules

- Creates new option records owned by the measure
- Copied options are independent of catalog (future catalog changes don't affect them)
- If measure already has options, they are replaced

---

## Data Models

### MeasureDirection Enum

```typescript
enum MeasureDirection {
  Increase = "Increase", // Higher is better (e.g., revenue, customers)
  Decrease = "Decrease"  // Lower is better (e.g., costs, churn)
}
```

### MeasureType Enum

> **Note:** MeasureType describes how values are **represented and input** (Quantitative = direct number, Qualitative = select from options). This is different from indicator classification (leading/lagging) which may be tracked separately.

```typescript
enum MeasureType {
  Quantitative = "Quantitative",  // Direct numeric input (e.g., $50,000 revenue)
  Qualitative = "Qualitative",    // Select from labeled options (e.g., "Excellent" = 5)
  Binary = "Binary"               // DEPRECATED: Use Qualitative with 2 options instead
}
```

**Examples:**
- **Quantitative:** Revenue ($50,000), Temperature (72°F), Customer Count (1,500)
- **Qualitative:** Satisfaction (Excellent/Good/Fair/Poor → 4/3/2/1), Risk Level (High/Medium/Low → 3/2/1)
- **Binary (deprecated):** Complete (Yes/No) - migrate to Qualitative with options Yes=1, No=0


### Common Categories

Standard Measure categories (not enforced, but commonly used):
- `Finance` - Revenue, costs, profitability
- `Sales` - Pipeline, conversions, deals
- `Marketing` - Leads, CAC, ROAS
- `Customer Success` - Retention, satisfaction, NPS
- `Operations` - Efficiency, productivity, quality
- `Product` - Usage, adoption, feature metrics
- `HR` - Headcount, turnover, engagement

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
| 400 | Invalid GUID format | "Invalid Measure ID format" |
| 400 | Missing required field | "Name is required" |
| 400 | Invalid enum value | "Direction must be 'Increase' or 'Decrease'" |
| 401 | Missing/invalid token | "Unauthorized" |
| 403 | Insufficient permissions | "Access denied to this Measure" |
| 404 | Measure not found | "Measure not found" |
| 422 | Validation failure | "Target value must be greater than 0" |
| 500 | Server error | "Internal server error" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
import { traction } from './traction';

// List Measures for a goal
const measures = await traction.get<PaginatedMeasuresResponse>('/measures', {
  params: { goalId: 'goal-123' }
});

// Create catalog-based Measure
const newMeasure = await traction.post<MeasureResponse>('/measures', {
  name: 'Customer Acquisition Cost',
  catalogId: 'measure-catalog-003',
  targetValue: 100.00,
  unit: 'USD',
  ownerId: 'owner-123',
  strategyId: 'strategy-456'
});

// Update Measure value
await traction.put(`/measures/${measureId}/value`, {
  value: 95.50,
  recordedAt: new Date().toISOString(),
  notes: 'Monthly update'
});

// Get Measure details with linked goals
const measureDetails = await traction.get<MeasureDetailResponse>(`/measures/${measureId}`);
console.log(`Linked to ${measureDetails.data.linkedGoals.length} goals`);

// Delete Measure (soft delete)
await traction.delete(`/measures/${measureId}`);
```

---

## Related APIs

- **[Measure Links API](./measure-links-api.md)** - Link Measures to goals
- **[Measure Data API](./measure-data-api.md)** - Record targets, actuals, projections
- **[Goals API](./goals-api.md)** - Manage goals that Measures measure
- **[Strategies API](./strategies-api.md)** - Strategies that Measures support

---

## Changelog

### v7.4 (January 10, 2026) - Issue #527: Link-Level Progress
- ✨ **Added:** `progress` field to `goalLinks` and `strategyLinks` in GET /measures/summary response
- 🔄 **Changed:** Progress moved from measure level to link level for accurate per-goal/strategy tracking
- 📊 Progress calculation includes: progressPercentage, status (on_track/at_risk/behind/no_data), variance, variancePercentage, daysUntilTarget, isOverdue
- 🧮 Implemented via domain service pattern (`MeasureLinkProgressService`) following DDD principles
- 📝 Each link has independent progress based on its own threshold configuration

### v7.3 (January 9, 2026) - Issue #526: Measure Summary Endpoint
- ✨ Added `GET /measures/summary` - Comprehensive measure tracker with filtering and aggregations
- 📊 Includes progress calculations, goal/strategy links, trend data, and summary statistics
- 🔍 Supports filtering by category, owner, status, progress status, and period
- 📈 Configurable trend data points (default: 5, supports 0 for all)
- 📝 Documented progress status calculation algorithm

### v7.2 (January 8, 2026) - Issue #469: Streamline Measure Terminology
- ✨ Added `GET /measures/{id}/options` - Get options for Qualitative measures
- ✨ Added `PUT /measures/{id}/options` - Set/replace measure options
- ✨ Added `DELETE /measures/{id}/options` - Delete measure-owned options
- ✨ Added `POST /measures/{id}/options/copy-from-catalog/{catalogId}` - Copy catalog options
- 📝 **Fixed MeasureType enum documentation** - Changed from Leading/Lagging to Quantitative/Qualitative/Binary
- ⚠️ Deprecated `Binary` MeasureType - Use Qualitative with 2 options instead
- 📝 Clarified Type vs ValueType terminology (Type = input method, ValueType = data nature)

### v7.1 (January 2, 2026)
- ✨ Added `GET /goals/available-measures` for new (unpersisted) goals
- 📝 Renamed spec files to `measures-*` for consistency

### v7.0 (December 23, 2025)
- ✅ Documented all 7 endpoints with complete examples
- ⚠️ Deprecated `GET /measures/{id}/linked-goals` (returns 501)
- ⚠️ Deprecated `goalId` field in `POST /measures` request
- ✨ Added `linkedGoals` to `GET /measures/{id}` response
- ✨ Added `historicalValues` to detail response
- 📝 Documented catalog-based vs custom Measure creation
- 📝 Clarified filtering behavior and priorities
- 📝 Added frontend TypeScript usage examples

### v6.0 (December 21, 2025)
- Initial Measure endpoints

---

**[← Back to Traction Service Index](./README.md)**
