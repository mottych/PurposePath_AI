# Alignment API Specification

**Controller:** `AlignmentController`  
**Base Route:** `/alignment`  
**Version:** 7.1  
**Last Updated:** January 8, 2026

[← Back to API Index](./README.md)

---

## Overview

The Alignment API provides endpoints for saving and retrieving goal alignment data.

**Important:** Alignment is calculated by the Coaching service (`POST /coaching/alignment-check`). This service provides endpoints to:
1. Save alignment data to Goals (`POST /alignment/save`)
2. Retrieve cached alignment data (`POST /alignment/check`)

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. Save Alignment

**POST** `/alignment/save`

Save alignment data calculated by the Coaching service to a goal.

#### Request Body

```json
{
  "goalId": "uuid",
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
| `goalId` | string (UUID) | Yes | Goal ID to update with alignment data |
| `alignmentScore` | integer | Yes | Overall alignment score (0-100) |
| `explanation` | string | No | AI-generated explanation of the alignment |
| `suggestions` | string[] | No | AI-generated suggestions for improvement |
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

### 2. Check Alignment (Cached)

**POST** `/alignment/check`

Retrieve cached alignment data for a goal intent against business foundation.

If cached alignment data is not available yet, this endpoint returns `200 OK` with `success: false` and an error message. (This is an expected business condition, not a missing route/resource.)

#### Request Body

```json
{
  "goalIntent": "string",
  "businessFoundation": {
    "businessName": "string",
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string",
    "valueProposition": "string"
  }
}
```

#### Request Constraints

| Field | Type | Required | Description |
|------|------|----------|-------------|
| `goalIntent` | string | Yes | Goal intent text to match against cached goals |
| `businessFoundation.businessName` | string | Yes | Business name (provided by client; not used for cache lookup) |
| `businessFoundation.vision` | string | Yes | Vision statement |
| `businessFoundation.purpose` | string | Yes | Purpose statement |
| `businessFoundation.coreValues` | string[] | Yes | List of core values |
| `businessFoundation.targetMarket` | string | No | Target market |
| `businessFoundation.valueProposition` | string | No | Value proposition |

#### Response 200 (Cached Alignment Found)

```json
{
  "success": true,
  "data": {
    "alignmentScore": 85,
    "score": 85,
    "explanation": "This goal strongly aligns with your business vision...",
    "suggestions": [
      "Consider adding a strategy focused on...",
      "Your Measures could be more specific about..."
    ],
    "lastUpdated": "2025-10-13T14:30:00Z"
  },
  "message": null,
  "error": null,
  "code": null
}
```

#### Response 200 (No Cached Alignment)

```json
{
  "success": false,
  "data": null,
  "message": null,
  "error": "No cached alignment data found. Please calculate alignment using the Coaching service first.",
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

- The current implementation performs cache lookup by scanning goals and matching by `goalIntent`. Frontend should prefer passing a stable identifier when/if a goalId-based endpoint is introduced.
