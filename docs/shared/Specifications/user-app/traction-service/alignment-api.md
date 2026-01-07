# Alignment API Specification

**Controller:** `AlignmentController`  
**Base Route:** `/alignment`  
**Version:** 7.0  
**Last Updated:** January 7, 2026

[← Back to API Index](./README.md)

---

## Overview

The Alignment API provides access to cached goal alignment data.

**Important:** Alignment is calculated by the Coaching service (`POST /coaching/alignment-check`) and persisted as alignment fields on Goals. This endpoint reads from that cached data.

---

## Authentication

All endpoints require:
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

---

## Endpoints

### 1. Check Alignment (Cached)

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
