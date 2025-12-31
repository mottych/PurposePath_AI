# KPIs API Specification

**Version:** 7.0  
**Last Updated:** December 23, 2025  
**Base Path:** `/kpis`  
**Controller:** `KpisController.cs`

## Overview

The KPIs API manages Key Performance Indicators (KPIs) within the PurposePath system. KPIs measure progress toward strategies and goals, supporting both catalog-based KPIs (from the KPI library) and custom user-defined KPIs.

### Key Features
- List KPIs with filtering by owner, goal, or strategy
- Create catalog-based or custom KPIs
- Update KPI details or current values
- Soft delete KPIs (preserves historical data)
- Query KPI-goal relationships

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. List KPIs

Retrieve KPIs with optional filtering.

**Endpoint:** `GET /kpis`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `ownerId` | string (GUID) | No | Filter by KPI owner (person responsible) |
| `goalId` | string (GUID) | No | Filter by linked goal |
| `strategyId` | string (GUID) | No | Filter by linked strategy |

**Default Behavior:** If no filter is provided, returns KPIs owned by the current user.

#### Request Example

```http
GET /kpis?goalId=550e8400-e29b-41d4-a716-446655440000
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
        "catalogId": "kpi-catalog-001",
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
| `id` | string (GUID) | Unique KPI identifier |
| `tenantId` | string | Organization identifier |
| `name` | string | KPI name (max 200 chars) |
| `description` | string | Detailed description (max 1000 chars) |
| `currentValue` | decimal | Latest recorded value |
| `targetValue` | decimal | Goal/target value |
| `unit` | string | Measurement unit (e.g., "USD", "%", "count") |
| `direction` | enum | `Increase` or `Decrease` (desired trend) |
| `type` | enum | `Leading` or `Lagging` indicator |
| `category` | string | KPI category (e.g., "Finance", "Sales", "Operations") |
| `measurementFrequency` | string | How often measured (e.g., "Daily", "Weekly", "Monthly") |
| `dataSource` | string | Where data comes from |
| `catalogId` | string | If from KPI library, the catalog entry ID |
| `ownerId` | string (GUID) | Person responsible for this KPI |
| `strategyId` | string (GUID) | Linked strategy |
| `currentValueDate` | datetime | When current value was recorded |
| `createdAt` | datetime | When KPI was created |
| `updatedAt` | datetime | Last update timestamp |
| `isDeleted` | boolean | Soft delete flag |

#### Business Rules

- **Filtering Priority:** If multiple filters are provided:
  1. `ownerId` takes precedence
  2. Then `goalId`
  3. Then `strategyId`
  4. Default: Current user's KPIs
- **Multi-tenancy:** Only returns KPIs for the specified tenant
- **Soft Deletes:** Deleted KPIs (`isDeleted: true`) are excluded by default

---

### 2. Create KPI

Create a new KPI (catalog-based or custom).

**Endpoint:** `POST /kpis`

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
  "catalogId": "kpi-catalog-002",
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
| `name` | string | **Yes** | KPI name (max 200 chars) |
| `description` | string | No | Detailed description |
| `currentValue` | decimal | No | Initial value |
| `targetValue` | decimal | No | Goal value |
| `unit` | string | No | Measurement unit |
| `direction` | enum | No | `Increase` or `Decrease` |
| `type` | enum | No | `Leading` or `Lagging` |
| `category` | string | No | KPI category |
| `measurementFrequency` | No | No | Default: "Monthly" |
| `dataSource` | string | No | Data source identifier |
| `ownerId` | string (GUID) | No | Person responsible (defaults to creator) |
| `strategyId` | string (GUID) | No | Linked strategy |
| `catalogId` | string | No | KPI catalog entry (for library KPIs) |
| `aggregationType` | string | No | How data is aggregated (e.g., "Sum", "Average") |
| `aggregationPeriod` | string | No | Time period for aggregation |
| `valueType` | string | No | Data type (e.g., "Number", "Percentage", "Currency") |
| `calculationMethod` | string | No | Formula or method for calculation |
| `currentValueDate` | datetime | No | When current value was recorded (defaults to now) |
| `goalId` | string (GUID) | No | **⚠️ Deprecated:** Link KPI to goal via `/kpi-links` instead |

#### Response

**Status:** `201 Created`  
**Location:** `/kpis/{id}`

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
    "catalogId": "kpi-catalog-002",
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

- **Catalog vs Custom:** If `catalogId` is provided, KPI is linked to library entry; otherwise, it's custom
- **Owner Assignment:** If `ownerId` is not provided, defaults to the current user (creator)
- **Tenant Isolation:** KPI is automatically associated with the current tenant
- **⚠️ Goal Linking Deprecated:** The `goalId` field in request is deprecated. Use `/kpi-links` endpoint to link KPIs to goals

#### Validation Rules

- **Name:** Required, max 200 characters
- **Target Value:** Must be > 0 if provided
- **Direction:** Must be "Increase" or "Decrease" if provided
- **Type:** Must be "Leading" or "Lagging" if provided
- **Owner & Strategy IDs:** Must be valid GUIDs and exist in tenant

---

### 3. Get KPI Details

Retrieve detailed information about a specific KPI, including linked goals.

**Endpoint:** `GET /kpis/{id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | KPI identifier |

#### Request Example

```http
GET /kpis/123e4567-e89b-12d3-a456-426614174000
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
    "catalogId": "kpi-catalog-001",
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
| `linkedGoals` | array | Goals linked to this KPI |
| `linkedGoals[].goalId` | string (GUID) | Goal identifier |
| `linkedGoals[].goalName` | string | Goal name |
| `linkedGoals[].linkId` | string (GUID) | KPI link identifier |
| `linkedGoals[].isPrimary` | boolean | Is this the primary KPI for the goal? |
| `linkedGoals[].linkedAt` | datetime | When link was created |
| `historicalValues` | array | Previous KPI values (last 12) |
| `historicalValues[].value` | decimal | Historical value |
| `historicalValues[].recordedAt` | datetime | When value was recorded |

#### Error Responses

**Status:** `400 Bad Request`
```json
{
  "success": false,
  "data": null,
  "error": "Invalid KPI ID format"
}
```

**Status:** `404 Not Found`
```json
{
  "success": false,
  "data": null,
  "error": "KPI not found"
}
```

---

### 4. Update KPI

Update KPI details (name, description, target, etc.). Does not update current value — use `PUT /kpis/{id}/value` for that.

**Endpoint:** `PUT /kpis/{id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | KPI identifier |

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
| `name` | string | KPI name (max 200 chars) |
| `description` | string | Detailed description |
| `targetValue` | decimal | Updated target value |
| `unit` | string | Measurement unit |
| `direction` | enum | `Increase` or `Decrease` |
| `type` | enum | `Leading` or `Lagging` |
| `category` | string | KPI category |
| `measurementFrequency` | string | Measurement frequency |
| `dataSource` | string | Data source identifier |
| `ownerId` | string (GUID) | New owner (person responsible) |

**Note:** `currentValue` cannot be updated via this endpoint. Use `PUT /kpis/{id}/value` instead.

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
- **Tenant & ID:** Cannot change KPI's tenant or ID
- **Catalog ID:** Cannot change `catalogId` after creation

---

### 5. Update KPI Value

Update only the current value of a KPI (records new measurement).

**Endpoint:** `PUT /kpis/{id}/value`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | KPI identifier |

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
| `value` | decimal | **Yes** | New KPI value |
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
- **Event Publishing:** Triggers `KpiValueUpdated` domain event
- **Percentage Change:** System calculates change from previous value

#### Validation Rules

- **Value:** Must be a valid decimal number
- **Recorded At:** Cannot be in the future
- **Notes:** Max 500 characters

---

### 6. Delete KPI

Soft delete a KPI (marks as deleted, preserves historical data).

**Endpoint:** `DELETE /kpis/{id}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | string (GUID) | **Yes** | KPI identifier |

#### Request Example

```http
DELETE /kpis/123e4567-e89b-12d3-a456-426614174000
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
  "error": "Invalid KPI ID format"
}
```

**Status:** `404 Not Found`
```json
{
  "success": false,
  "data": null,
  "error": "KPI not found"
}
```

#### Business Rules

- **Soft Delete:** KPI is marked as deleted (`isDeleted: true`) but not physically removed
- **Historical Data:** All historical values and links are preserved
- **List Queries:** Deleted KPIs are excluded from list results by default
- **Restoration:** Can be restored by admin/support team
- **Cascade:** KPI links to goals are also soft deleted

---

### 7. Get KPI Linked Goals (Deprecated)

⚠️ **DEPRECATED (Issue #374):** This endpoint is being migrated to the new KpiLink design.

**Endpoint:** `GET /kpis/{id}/linked-goals`

#### Current Behavior

Returns `501 Not Implemented` with migration message.

```json
{
  "success": false,
  "data": null,
  "error": "This endpoint is being migrated to the new KpiLink design. Please use the new KpiLink endpoints."
}
```

#### Migration Path

Use the following endpoints instead:
- **List KPI Links:** `GET /kpi-links?kpiId={id}`
- **KPI Details with Links:** `GET /kpis/{id}` (includes `linkedGoals` in response)

See [KPI Links API](./kpi-links-api.md) for details.

---

## Data Models

### KpiDirection Enum

```typescript
enum KpiDirection {
  Increase = "Increase", // Higher is better (e.g., revenue, customers)
  Decrease = "Decrease"  // Lower is better (e.g., costs, churn)
}
```

### KpiType Enum

```typescript
enum KpiType {
  Leading = "Leading",   // Predictive indicator (e.g., leads generated)
  Lagging = "Lagging"    // Historical indicator (e.g., revenue achieved)
}
```

### Common Categories

Standard KPI categories (not enforced, but commonly used):
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
| 400 | Invalid GUID format | "Invalid KPI ID format" |
| 400 | Missing required field | "Name is required" |
| 400 | Invalid enum value | "Direction must be 'Increase' or 'Decrease'" |
| 401 | Missing/invalid token | "Unauthorized" |
| 403 | Insufficient permissions | "Access denied to this KPI" |
| 404 | KPI not found | "KPI not found" |
| 422 | Validation failure | "Target value must be greater than 0" |
| 500 | Server error | "Internal server error" |

---

## Frontend Usage Examples

### TypeScript Service

```typescript
import { traction } from './traction';

// List KPIs for a goal
const kpis = await traction.get<PaginatedKpisResponse>('/kpis', {
  params: { goalId: 'goal-123' }
});

// Create catalog-based KPI
const newKpi = await traction.post<KpiResponse>('/kpis', {
  name: 'Customer Acquisition Cost',
  catalogId: 'kpi-catalog-003',
  targetValue: 100.00,
  unit: 'USD',
  ownerId: 'owner-123',
  strategyId: 'strategy-456'
});

// Update KPI value
await traction.put(`/kpis/${kpiId}/value`, {
  value: 95.50,
  recordedAt: new Date().toISOString(),
  notes: 'Monthly update'
});

// Get KPI details with linked goals
const kpiDetails = await traction.get<KpiDetailResponse>(`/kpis/${kpiId}`);
console.log(`Linked to ${kpiDetails.data.linkedGoals.length} goals`);

// Delete KPI (soft delete)
await traction.delete(`/kpis/${kpiId}`);
```

---

## Related APIs

- **[KPI Links API](./kpi-links-api.md)** - Link KPIs to goals
- **[KPI Data API](./kpi-data-api.md)** - Record targets, actuals, projections
- **[Goals API](./goals-api.md)** - Manage goals that KPIs measure
- **[Strategies API](./strategies-api.md)** - Strategies that KPIs support

---

## Changelog

### v7.0 (December 23, 2025)
- ✅ Documented all 7 endpoints with complete examples
- ⚠️ Deprecated `GET /kpis/{id}/linked-goals` (returns 501)
- ⚠️ Deprecated `goalId` field in `POST /kpis` request
- ✨ Added `linkedGoals` to `GET /kpis/{id}` response
- ✨ Added `historicalValues` to detail response
- 📝 Documented catalog-based vs custom KPI creation
- 📝 Clarified filtering behavior and priorities
- 📝 Added frontend TypeScript usage examples

### v6.0 (December 21, 2025)
- Initial KPI endpoints

---

**[← Back to Traction Service Index](./README.md)**
