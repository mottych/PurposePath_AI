# Measures API Specification

**Version:** 7.0  
**Last Updated:** December 23, 2025  
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

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. List Measures

Retrieve Measures with optional filtering.

**Endpoint:** `GET /measures`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ownerId` | string (GUID) | No | Filter by Measure owner (person responsible) |
| `goalId` | string (GUID) | No | Filter by linked goal |
| `strategyId` | string (GUID) | No | Filter by linked strategy |

**Default Behavior:** If no filter is provided, returns Measures owned by the current user.

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
  4. Default: Current user's Measures
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

### 7. Get Measure Linked Goals (Deprecated)

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

## Data Models

### MeasureDirection Enum

```typescript
enum MeasureDirection {
  Increase = "Increase", // Higher is better (e.g., revenue, customers)
  Decrease = "Decrease"  // Lower is better (e.g., costs, churn)
}
```

### MeasureType Enum

```typescript
enum MeasureType {
  Leading = "Leading",   // Predictive indicator (e.g., leads generated)
  Lagging = "Lagging"    // Historical indicator (e.g., revenue achieved)
}
```

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
