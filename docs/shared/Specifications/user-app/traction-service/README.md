# Traction Service API Specifications (v7)

**Version:** 7.0  
**Last Updated:** December 23, 2025  
**Service Base URL:** `{REACT_APP_TRACTION_API_URL}`  
**Default (Localhost):** `http://localhost:8002`

[← Back to Main Index](../index.md)

---

## Overview

This directory contains detailed API specifications for the Traction Service, organized by controller/feature area for easier maintenance and reference.

**Version 7 Changes:**
- Removed all deprecated GoalMeasureLink, MeasureMilestone, MeasureActual, and MeasureReading endpoints
- Documented only actively implemented endpoints
- Split large specification into maintainable controller-based documents
- Updated to reflect MeasureLink and MeasureData design (Epic #362)

---

## Authentication & Headers

**All endpoints require:**
- `Authorization: Bearer {accessToken}` - JWT token from authentication
- `X-Tenant-Id: {tenantId}` - Multi-tenancy identifier (UUID)

**Optional headers:**
- `X-Frontend-Base-Url` - Base URL for email links (used by some endpoints)

---

## API Structure

### Controller-Based Specifications

| Document | Controller | Endpoints | Description |
|----------|------------|-----------|-------------|
| [Goals API](./goals-api.md) | GoalsController | 11 endpoints | Goal lifecycle management |
| [Strategies API](./strategies-api.md) | StrategiesController | 6 endpoints | Strategy management and alignment |
| [Measures API](./measures-api.md) | MeasuresController | 5 endpoints | Measure instance management |
| [Measure Links API](./measure-links-api.md) | MeasureLinksController | 6 endpoints | Link Measures to goals, people, strategies |
| [Measure Data API](./measure-data-api.md) | MeasureDataController | 8 endpoints | Targets, actuals, projections |
| [Actions API](./actions-api.md) | ActionsController | 7 endpoints | Action items management |
| [Issues API](./issues-api.md) | IssuesController | 5 endpoints | Issue tracking |
| [Dashboard, Reports & Activities](./dashboard-reports-activities-api.md) | Multiple | 5 endpoints | Command center, reports, activity feeds |

> **Note:** People API has been deferred and moved to Account Service for better organizational alignment.

### Reference Data APIs

> **Note:** Reference data endpoints (issue types, statuses, tags) are integrated within their respective API documents above.

---

## Common Patterns

### Response Structure

All endpoints return a consistent wrapper:

```json
{
  "success": true,
  "data": { /* actual response data */ },
  "error": null,
  "timestamp": "2025-12-23T10:30:00Z"
}
```

### Pagination

List endpoints support pagination:

**Query Parameters:**
- `page` (number, default: 1) - Page number (1-indexed)
- `pageSize` (number, default: 20) - Items per page
- `sortBy` (string) - Field to sort by
- `sortOrder` (string) - "asc" or "desc"

**Paginated Response:**
```json
{
  "success": true,
  "data": {
    "items": [ /* array of items */ ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 150,
      "totalPages": 8
    }
  }
}
```

### Error Responses

```json
{
  "success": false,
  "data": null,
  "error": "Descriptive error message",
  "timestamp": "2025-12-23T10:30:00Z"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (business rule violation)
- `500` - Internal Server Error

### Date/Time Format

All dates use ISO 8601 format: `YYYY-MM-DDTHH:mm:ss.fffZ`

Example: `"2025-12-23T15:30:00.000Z"`

### Field Naming

- **Frontend:** camelCase (e.g., `goalName`, `createdAt`)
- **Backend:** May use PascalCase internally but APIs use camelCase
- **Enums:** lowercase with underscores (e.g., `in_progress`, `on_track`)

---

## Quick Reference

### Most Common Endpoints

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List goals | GET | `/goals` |
| Create goal | POST | `/goals` |
| Get goal details | GET | `/goals/{id}` |
| Update goal | PUT | `/goals/{id}` |
| List Measures | GET | `/measures` |
| Create Measure | POST | `/measures` |
| Link Measure to goal | POST | `/measure-links` |
| Record Measure data | POST | `/measure-data` |
| List actions | GET | `/operations/actions` |
| Create action | POST | `/operations/actions` |
| List issues | GET | `/issues` |
| Create issue | POST | `/issues` |

---

## Migration from v6

**Removed Endpoints (Deprecated):**
- All `/goals/{goalId}/measures:link` endpoints → Use `/measure-links` instead
- All `/goals/{goalId}/measures:unlink` endpoints → Use `/measure-links` DELETE
- All `/goals/{goalId}/available-measures` endpoints → New design pending
- All `/measure-planning/*` endpoints → Redesigned as `/measure-data`
- All shared Measure endpoints → Consolidated into `/measure-links`

**New Endpoints (v7):**
- `/measure-links` - Unified Measure linking
- `/measure-data` - All Measure data operations (targets, actuals, projections)
- Simplified Measure management

**Changed Endpoints:**
- Measure operations moved from goals context to dedicated Measure resources
- More RESTful resource design

---

## Development Guidelines

### Adding New Endpoints

1. Update appropriate controller spec file
2. Document request/response structures completely
3. Include validation rules and constraints
4. Add examples
5. Update this index with endpoint count

### Deprecating Endpoints

1. Mark as deprecated in spec with migration path
2. Add comment to controller code
3. Update migration section in this README
4. Plan removal timeline

### Maintaining Specifications

- Specs should match actual implementation
- Update specs when code changes
- Review specs during code review
- Keep examples realistic

---

## Version History

### v7.0 (December 23, 2025)
- Removed deprecated Measure endpoints (GoalMeasureLink, MeasureMilestone, MeasureActual, MeasureReading)
- Split monolithic spec into controller-based documents
- Updated to reflect MeasureLink and MeasureData design
- 121 files changed, 15,902 lines of deprecated code removed

### v6.0 (December 21, 2025)
- Added Measure linking endpoints
- Added Measure planning endpoints
- Documented nested object structures

### v5.0 (Previous)
- Initial comprehensive specification

---

## Contact & Support

For questions about these specifications:
- Create a GitHub issue
- Tag with `documentation` label
- Reference the specific endpoint/controller

