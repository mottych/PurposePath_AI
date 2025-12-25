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
- Removed all deprecated GoalKpiLink, KpiMilestone, KpiActual, and KpiReading endpoints
- Documented only actively implemented endpoints
- Split large specification into maintainable controller-based documents
- Updated to reflect KpiLink and KpiData design (Epic #362)

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
| [Goals API](./goals-api.md) | GoalsController | 11 endpoints | Goal lifecycle management, strategies |
| [KPIs API](./kpis-api.md) | KpisController | 5 endpoints | KPI instance management |
| [KPI Links API](./kpi-links-api.md) | KpiLinksController | 6 endpoints | Link KPIs to goals, people, strategies |
| [KPI Data API](./kpi-data-api.md) | KpiDataController | 8 endpoints | Targets, actuals, projections |
| [Actions API](./actions-api.md) | ActionsController | 7 endpoints | Action items management |
| [Issues API](./issues-api.md) | IssuesController | 5 endpoints | Issue tracking |
| [People API](./people-api.md) | PeopleController | 4 endpoints | People/team management |
| [Dashboard API](./dashboard-api.md) | DashboardController | 3 endpoints | Command center data |
| [Reports API](./reports-api.md) | ReportsController | 2 endpoints | Reporting and analytics |
| [Activities API](./activities-api.md) | ActivitiesController | 2 endpoints | Activity feeds |

### Reference Data APIs

| Document | Description |
|----------|-------------|
| [Reference Data API](./reference-data-api.md) | Issue types, statuses, person types, tags, roles |

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
| List KPIs | GET | `/kpis` |
| Create KPI | POST | `/kpis` |
| Link KPI to goal | POST | `/kpi-links` |
| Record KPI data | POST | `/kpi-data` |
| List actions | GET | `/operations/actions` |
| Create action | POST | `/operations/actions` |
| List issues | GET | `/issues` |
| Create issue | POST | `/issues` |

---

## Migration from v6

**Removed Endpoints (Deprecated):**
- All `/goals/{goalId}/kpis:link` endpoints → Use `/kpi-links` instead
- All `/goals/{goalId}/kpis:unlink` endpoints → Use `/kpi-links` DELETE
- All `/goals/{goalId}/available-kpis` endpoints → New design pending
- All `/kpi-planning/*` endpoints → Redesigned as `/kpi-data`
- All shared KPI endpoints → Consolidated into `/kpi-links`

**New Endpoints (v7):**
- `/kpi-links` - Unified KPI linking
- `/kpi-data` - All KPI data operations (targets, actuals, projections)
- Simplified KPI management

**Changed Endpoints:**
- KPI operations moved from goals context to dedicated KPI resources
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
- Removed deprecated KPI endpoints (GoalKpiLink, KpiMilestone, KpiActual, KpiReading)
- Split monolithic spec into controller-based documents
- Updated to reflect KpiLink and KpiData design
- 121 files changed, 15,902 lines of deprecated code removed

### v6.0 (December 21, 2025)
- Added KPI linking endpoints
- Added KPI planning endpoints
- Documented nested object structures

### v5.0 (Previous)
- Initial comprehensive specification

---

## Contact & Support

For questions about these specifications:
- Create a GitHub issue
- Tag with `documentation` label
- Reference the specific endpoint/controller

