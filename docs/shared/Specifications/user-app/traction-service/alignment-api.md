# Alignment API Specification

**Controller:** `AlignmentController`  
**Base Route:** `/alignment`  
**Version:** 7.2  
**Last Updated:** January 8, 2026

[← Back to API Index](./README.md)

---

## Overview

The Alignment API provides RESTful endpoints for saving and retrieving goal alignment data.

**Important:** Alignment is calculated by the Coaching service (`POST /coaching/alignment-check`). This service provides endpoints to:
1. Save alignment data to Goals (`POST /alignment/{goalId}`)
2. Retrieve cached alignment data (`GET /alignment/{goalId}`)

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. Get Alignment Data

**GET** `/alignment/{goalId}`

Retrieve cached alignment data for a specific goal.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (UUID) | Yes | Goal ID to retrieve alignment for |

#### Response 200 (Success)

```json
{
  "success": true,
  "data": {
    "goalId": "db1f3932-108d-46e8-bb2f-4ec3e9366a66",
    "alignmentScore": 85,
    "explanation": "This goal strongly aligns with your business vision and purpose...",
    "suggestions": [
      "Consider adding a strategy focused on customer acquisition",
      "Your measures could be more specific about timeline"
    ],
    "componentScores": {
      "intentAlignment": 90,
      "strategyAlignment": 80,
      "measureRelevance": 85
    },
    "breakdown": {
      "visionAlignment": 88,
      "purposeAlignment": 85,
      "valuesAlignment": 82
    },
    "lastUpdated": "2025-10-13T14:30:00Z"
  },
  "message": null,
  "error": null,
  "code": null
}
```

#### Response Fields

| Field | Type | Description |
|------|------|-------------|
| `goalId` | string (UUID) | Goal ID |
| `alignmentScore` | integer | Overall alignment score (0-100) |
| `explanation` | string | AI-generated explanation of the alignment |
| `suggestions` | string[] | AI-generated suggestions for improvement |
| `componentScores` | object? | Detailed component scores (nullable) |
| `componentScores.intentAlignment` | integer | Intent alignment score (0-100) |
| `componentScores.strategyAlignment` | integer | Strategy alignment score (0-100) |
| `componentScores.measureRelevance` | integer | Measure relevance score (0-100) |
| `breakdown` | object? | Breakdown by business foundation elements (nullable) |
| `breakdown.visionAlignment` | integer | Vision alignment score (0-100) |
| `breakdown.purposeAlignment` | integer | Purpose alignment score (0-100) |
| `breakdown.valuesAlignment` | integer | Values alignment score (0-100) |
| `lastUpdated` | datetime | When alignment data was last updated |

#### Response 404 (Goal Not Found)

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "Goal not found",
  "code": null
}
```

#### Response 404 (No Alignment Data)

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "No alignment data found for this goal. Please calculate alignment using the Coaching service first.",
  "code": null
}
```

#### Response 500 (Server Error)

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "Internal server error",
  "code": null
}
```

---

### 2. Save Alignment Data

**POST** `/alignment/{goalId}`

Save alignment data calculated by the Coaching service to a specific goal.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string (UUID) | Yes | Goal ID to update with alignment data |

#### Request Body

```json
{
  "alignmentScore": 85,
  "explanation": "This goal strongly aligns with your business vision and purpose...",
  "suggestions": [
    "Consider adding a strategy focused on customer acquisition",
    "Your measures could be more specific about timeline"
  ],
  "componentScores": {
    "intentAlignment": 90,
    "strategyAlignment": 80,
    "measureRelevance": 85
  },
  "breakdown": {
    "visionAlignment": 88,
    "purposeAlignment": 85,
    "valuesAlignment": 82
  }
}
```

#### Request Constraints

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `alignmentScore` | integer | Yes | Overall alignment score (0-100) |
| `explanation` | string | No | AI-generated explanation of the alignment (max 5000 chars) |
| `suggestions` | string[] | No | AI-generated suggestions for improvement (max 10 items) |
| `componentScores` | object | No | Detailed component scores |
| `componentScores.intentAlignment` | integer | Yes* | Intent alignment score (0-100) |
| `componentScores.strategyAlignment` | integer | Yes* | Strategy alignment score (0-100) |
| `componentScores.measureRelevance` | integer | Yes* | Measure relevance score (0-100) |
| `breakdown` | object | No | Breakdown by business foundation elements |
| `breakdown.visionAlignment` | integer | Yes* | Vision alignment score (0-100) |
| `breakdown.purposeAlignment` | integer | Yes* | Purpose alignment score (0-100) |
| `breakdown.valuesAlignment` | integer | Yes* | Values alignment score (0-100) |

*Required if parent object is provided

#### Response 200 (Success)

```json
{
  "success": true,
  "data": {
    "goalId": "db1f3932-108d-46e8-bb2f-4ec3e9366a66",
    "alignmentScore": 85,
    "message": "Alignment data saved successfully"
  },
  "message": null,
  "error": null,
  "code": null
}
```

#### Response 400 (Validation Error)

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "Alignment score must be between 0 and 100",
  "code": null
}
```

#### Response 404 (Goal Not Found)

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "Goal not found",
  "code": null
}
```

#### Response 500 (Server Error)

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "Internal server error",
  "code": null
}
```

---

## Notes

- **RESTful Design**: Endpoints now follow RESTful conventions with resource IDs in URL paths
- **Frontend Context**: Frontend always has `goalId` from goal creation/selection, eliminating need for intent-based lookups
- **Performance**: Direct ID-based lookups are significantly faster than scanning and matching by intent string
- **Simplicity**: No unnecessary business foundation payload in GET requests
- **Breaking Change**: v7.2 removes deprecated `POST /alignment/check` and `POST /alignment/save` endpoints
