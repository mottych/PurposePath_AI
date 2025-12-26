# Strategies API Specification

**Controller:** `StrategiesController`  
**Base Route:** `/goals/{goalId}/strategies`  
**Version:** 7.0  
**Last Updated:** December 26, 2025

[← Back to API Index](./README.md)

---

## Overview

The Strategies API manages execution strategies for business goals, including creation, updates, status transitions, reordering, and alignment scoring.

**Endpoints:** 6 total
- 3 CRUD operations (List, Create, Update, Delete)
- 1 reorder endpoint
- 1 alignment update endpoint

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. List Strategies for Goal

**GET** `/goals/{goalId}/strategies`

Retrieve all strategies associated with a specific goal.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (GUID) | Yes | Goal identifier |

#### Response (200 OK)

```json
{
  "success": true,
  "data": [
    {
      "id": "strat-001",
      "goalId": "goal-123",
      "title": "Expand Product Line",
      "description": "Launch 3 new products targeting SMB segment",
      "status": "in_progress",
      "priority": "high",
      "order": 1,
      "aiGenerated": false,
      "validationScore": 85,
      "validationFeedback": "Strong strategy with clear metrics",
      "alignmentScore": 92,
      "alignmentExplanation": "Aligns well with company vision and core values",
      "alignmentSuggestions": [
        "Consider adding customer satisfaction metrics",
        "Link to brand awareness KPIs"
      ],
      "ownerId": "user-456",
      "dueDate": "2025-12-31",
      "tags": ["product", "growth"],
      "createdAt": "2025-01-01T10:00:00Z",
      "updatedAt": "2025-01-15T14:30:00Z"
    }
  ]
}
```

---

### 2. Create Strategy

**POST** `/goals/{goalId}/strategies`

Create a new strategy for a goal.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (GUID) | Yes | Goal identifier |

#### Request Body

```json
{
  "title": "Expand Product Line",
  "description": "Launch 3 new products targeting SMB segment",
  "ownerId": "user-456",
  "priority": "high",
  "dueDate": "2025-12-31",
  "order": 1,
  "aiGenerated": false
}
```

#### Response (201 Created)

```json
{
  "success": true,
  "data": {
    "id": "strat-001",
    "goalId": "goal-123",
    "title": "Expand Product Line",
    "description": "Launch 3 new products targeting SMB segment",
    "status": "planning",
    "priority": "high",
    "order": 1,
    "aiGenerated": false,
    "ownerId": "user-456",
    "dueDate": "2025-12-31",
    "tags": [],
    "createdAt": "2025-01-01T10:00:00Z"
  }
}
```

---

### 3. Update Strategy

**PUT** `/goals/{goalId}/strategies/{id}`

Update an existing strategy.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (GUID) | Yes | Goal identifier |
| `id` | string (GUID) | Yes | Strategy identifier |

#### Request Body

All fields optional:

```json
{
  "title": "Expand Product Line (Updated)",
  "description": "Launch 5 new products targeting SMB and enterprise segments",
  "status": "in_progress",
  "ownerId": "user-789",
  "priority": "critical",
  "dueDate": "2025-11-30",
  "order": 2,
  "validationScore": 90,
  "validationFeedback": "Excellent strategy with clear success criteria"
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "strat-001",
    "goalId": "goal-123",
    "title": "Expand Product Line (Updated)",
    "description": "Launch 5 new products targeting SMB and enterprise segments",
    "status": "in_progress",
    "priority": "critical",
    "order": 2,
    "validationScore": 90,
    "validationFeedback": "Excellent strategy with clear success criteria",
    "ownerId": "user-789",
    "dueDate": "2025-11-30",
    "updatedAt": "2025-01-20T16:45:00Z"
  }
}
```

---

### 4. Update Strategy Alignment

**PATCH** `/goals/{goalId}/strategies/{id}/alignment`

Update strategy alignment scores calculated by the Coaching Service AI.

**Purpose:** This endpoint persists alignment data calculated by the Coaching Service, which evaluates how well the strategy aligns with:
- The goal's intent and objectives
- The business foundation (vision, purpose, core values)
- Company strategy and market positioning

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (GUID) | Yes | Goal identifier |
| `id` | string (GUID) | Yes | Strategy identifier |

#### Request Body

```json
{
  "alignmentScore": 92,
  "alignmentExplanation": "Strategy aligns strongly with company vision to become market leader in cloud solutions. Direct connection to 'Innovation' and 'Customer Focus' core values. Supports goal of increasing market share by 15%.",
  "alignmentSuggestions": [
    "Consider adding customer satisfaction metrics to track alignment with 'Customer Focus' value",
    "Link to brand awareness KPIs to measure market leadership progress"
  ]
}
```

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alignmentScore` | number | Yes | 0-100: How well strategy aligns with goal and business foundation |
| `alignmentExplanation` | string | No | AI-generated explanation of the alignment score |
| `alignmentSuggestions` | string[] | No | AI-generated suggestions for improving alignment |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "id": "strat-001",
    "goalId": "goal-123",
    "title": "Expand Product Line",
    "alignmentScore": 92,
    "alignmentExplanation": "Strategy aligns strongly with company vision...",
    "alignmentSuggestions": [
      "Consider adding customer satisfaction metrics...",
      "Link to brand awareness KPIs..."
    ],
    "updatedAt": "2025-01-21T10:15:00Z"
  }
}
```

#### Business Rules

- **Alignment Score:** Must be between 0-100
- **Frontend Flow:**
  1. Frontend calls Coaching Service to calculate alignment
  2. Coaching Service returns alignment data
  3. Frontend calls this endpoint to persist alignment in Traction Service
  4. Strategy alignment is displayed in UI and influences recommendations

---

### 5. Delete Strategy

**DELETE** `/goals/{goalId}/strategies/{id}`

Delete a strategy.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (GUID) | Yes | Goal identifier |
| `id` | string (GUID) | Yes | Strategy identifier |

#### Response (200 OK)

```json
{
  "success": true,
  "data": {
    "message": "Strategy deleted successfully"
  }
}
```

---

### 6. Reorder Strategies

**PUT** `/goals/{goalId}/strategies:reorder`

Atomically update the display order of multiple strategies within a goal.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (GUID) | Yes | Goal identifier |

#### Request Body

```json
{
  "strategyOrders": [
    { "strategyId": "strat-002", "newOrder": 1 },
    { "strategyId": "strat-001", "newOrder": 2 },
    { "strategyId": "strat-003", "newOrder": 3 }
  ]
}
```

#### Response (200 OK)

```json
{
  "success": true,
  "data": true
}
```

---

## Data Models

### Strategy Status

| Value | Description |
|-------|-------------|
| `planning` | Strategy is being planned |
| `in_progress` | Strategy execution in progress |
| `completed` | Strategy successfully completed |
| `paused` | Strategy execution paused |
| `cancelled` | Strategy cancelled/abandoned |

### Priority

| Value | Description |
|-------|-------------|
| `low` | Low priority |
| `medium` | Medium priority |
| `high` | High priority |
| `critical` | Critical priority |

---

## Error Responses

### 400 Bad Request

```json
{
  "success": false,
  "error": "Invalid strategy ID format"
}
```

### 404 Not Found

```json
{
  "success": false,
  "error": "Strategy not found"
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "Internal server error"
}
```

---

## Business Rules

- **Strategy Order:** Must be unique within a goal
- **Alignment Score:** Optional until Coaching Service calculates it
- **AI Generated:** Flag indicates if strategy was suggested by AI
- **Validation Score:** Optional AI-generated quality score (0-100)
- **Delete:** Deleting a strategy removes it permanently

---

## Related APIs

- [Goals API](./goals-api.md) - Parent goals management
- [KPI Links API](./kpi-links-api.md) - Link KPIs to strategies

---

## Version History

### 7.0 (December 26, 2025)
- Added **PATCH /goals/{goalId}/strategies/{id}/alignment** endpoint
- Added alignment fields to strategy response: `alignmentScore`, `alignmentExplanation`, `alignmentSuggestions`
- Documented complete strategy lifecycle endpoints

### 1.0 (Initial)
- Basic CRUD operations for strategies
