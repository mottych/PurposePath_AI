# Dashboard API Specification

**Services:** Account Service (configuration) + Traction Service (widget data)  
**Version:** 1.1  
**Last Updated:** January 9, 2026

## Endpoints Summary

| Method | Endpoint | Service | Description |
|--------|----------|---------|-------------|
| GET | `/dashboard/config` | Account | Get user's dashboard configuration |
| PUT | `/dashboard/config` | Account | Save user's dashboard configuration |
| DELETE | `/dashboard/config` | Account | Reset dashboard to default |
| GET | `/dashboard/templates` | Account | Get available dashboard templates |
| GET | `/dashboard/templates/{id}` | Account | Get specific template details |
| POST | `/dashboard/config/apply-template` | Account | Apply template to user's dashboard |
| GET | `/dashboard/widgets` | Account | Get widget catalog (available widget definitions) |
| GET | `/dashboard/widgets/hot-list/data` | Traction | Get hot list widget data |
| GET | `/dashboard/widgets/recent-activity/data` | Traction | Get recent activity widget data |
| GET | `/dashboard/widgets/action-list/data` | Traction | Get action list widget data |
| GET | `/dashboard/widgets/issue-list/data` | Traction | Get issue list widget data |
| GET | `/dashboard/widgets/goal-progress/data` | Traction | Get goal progress widget data |
| GET | `/dashboard/widgets/measure-graph/data` | Traction | Get measure graph widget data |
| GET | `/dashboard/widgets/actions-by-status/data` | Traction | Get actions by status widget data |
| GET | `/dashboard/widgets/ai-insights/data` | Traction | Get AI insights widget data |
| GET | `/dashboard/widgets/performance-score/data` | Traction | Get performance score widget data |
| GET | `/dashboard/widgets/team-alignment/data` | Traction | Get team alignment widget data |

## Revisions

| Date | Version | Summary |
|------|---------|---------|
| January 9, 2026 | 1.1 | Split specification by service: Account (config/templates) and Traction (widget data) |
| January 8, 2026 | 1.0 | Initial specification for customizable dashboard system |

---

## Overview

The Dashboard API provides endpoints for managing user-customizable dashboards with drag-and-drop widgets. The API is split across two services:

- **Account Service**: Manages dashboard configuration and templates (user preferences, layout state)
- **Traction Service**: Provides operational data for widgets (actions, goals, measures, issues, etc.)

### Key Concepts

- **Dashboard Config**: A user's complete dashboard state (widgets, layout, settings)
- **Widget Definition**: A widget type from the catalog (e.g., "action-list", "measure-graph")
- **Widget Instance**: A specific widget placed on a user's dashboard with its settings
- **Layout**: Position and size of widgets in a responsive grid
- **Template**: Pre-configured dashboard layouts users can apply

---

## Service Configuration

### Account Service (Configuration & Templates)

**Base URL:** `/account/api/v1`  
**Base Path:** `/dashboard`

**Required Headers:**
```http
Authorization: Bearer {accessToken}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

### Traction Service (Widget Data)

**Base URL:** `/traction/api/v1`  
**Base Path:** `/dashboard/widgets`

**Required Headers:**
```http
Authorization: Bearer {accessToken}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

---

# Account Service Endpoints

## Get Dashboard Configuration

**GET** `/account/api/v1/dashboard/config`

Retrieve the authenticated user's dashboard configuration. Returns the default configuration if no custom configuration exists.

### Response Structure

```typescript
interface DashboardConfigResponse {
  success: boolean;
  data: {
    id: string;
    userId: string;
    name: string;
    isDefault: boolean;
    widgets: WidgetInstance[];
    layouts: ResponsiveLayouts;
    createdAt: string;           // ISO 8601
    updatedAt: string;           // ISO 8601
  };
}

interface WidgetInstance {
  instanceId: string;            // Unique ID for this instance
  widgetId: string;              // References widget catalog ID
  title?: string;                // Custom title override
  settings: Record<string, unknown>;
}

interface ResponsiveLayouts {
  lg: WidgetLayout[];            // >= 1200px
  md: WidgetLayout[];            // >= 996px
  sm: WidgetLayout[];            // >= 768px
  xs: WidgetLayout[];            // < 768px
}

interface WidgetLayout {
  i: string;                     // Matches WidgetInstance.instanceId
  x: number;                     // X position (0-based grid column)
  y: number;                     // Y position (0-based grid row)
  w: number;                     // Width in grid units
  h: number;                     // Height in grid units
}
```

### Example Request

```bash
GET /account/api/v1/dashboard/config
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "id": "config_abc123",
    "userId": "user_xyz789",
    "name": "My Dashboard",
    "isDefault": false,
    "widgets": [
      {
        "instanceId": "hot-list-1704700800000",
        "widgetId": "hot-list",
        "title": null,
        "settings": {
          "showPastDueActions": true,
          "showAtRiskMeasures": true,
          "showCriticalIssues": true,
          "maxItems": 5
        }
      }
    ],
    "layouts": {
      "lg": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 }
      ],
      "md": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 }
      ],
      "sm": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 3, "h": 2 }
      ],
      "xs": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 }
      ]
    },
    "createdAt": "2026-01-08T10:00:00Z",
    "updatedAt": "2026-01-08T15:30:00Z"
  }
}
```

### Business Rules

- Returns default configuration if user has no saved config
- Configuration is user-specific (isolated by userId within tenant)
- Widget instances must reference valid widget IDs from the catalog
- Layout positions must be non-negative integers

---

## Save Dashboard Configuration

**PUT** `/account/api/v1/dashboard/config`

Save or update the authenticated user's dashboard configuration.

### Request Body

```typescript
interface SaveDashboardConfigRequest {
  name?: string;                 // Dashboard name (default: "My Dashboard")
  widgets: WidgetInstance[];
  layouts: ResponsiveLayouts;
}
```

### Example Request

```bash
PUT /account/api/v1/dashboard/config
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

```json
{
  "name": "Executive Dashboard",
  "widgets": [
    {
      "instanceId": "hot-list-1704700800000",
      "widgetId": "hot-list",
      "settings": {
        "showPastDueActions": true,
        "showAtRiskMeasures": true,
        "showCriticalIssues": true,
        "maxItems": 10
      }
    }
  ],
  "layouts": {
    "lg": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 }
    ],
    "md": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 }
    ],
    "sm": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 3, "h": 2 }
    ],
    "xs": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 }
    ]
  }
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "config_abc123",
    "userId": "user_xyz789",
    "name": "Executive Dashboard",
    "isDefault": false,
    "widgets": [...],
    "layouts": {...},
    "createdAt": "2026-01-08T10:00:00Z",
    "updatedAt": "2026-01-08T16:45:00Z"
  }
}
```

### Validation Rules

| Field | Rule |
|-------|------|
| `widgets` | Required, non-empty array |
| `widgets[].instanceId` | Required, unique within dashboard |
| `widgets[].widgetId` | Required, must exist in widget catalog |
| `widgets[].settings` | Optional, widget-specific validation |
| `layouts` | Required, must have lg, md, sm, xs |
| `layouts[].i` | Must match a widget instanceId |
| `layouts[].x` | >= 0, < grid columns (5 for lg) |
| `layouts[].y` | >= 0 |
| `layouts[].w` | >= widget minW, <= widget maxW |
| `layouts[].h` | >= widget minH, <= widget maxH |

### Error Responses

**400 Bad Request - Invalid Widget**
```json
{
  "success": false,
  "error": "Invalid widget ID: unknown-widget",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "widgets[0].widgetId",
    "value": "unknown-widget"
  }
}
```

**403 Forbidden - Widget Not Accessible**
```json
{
  "success": false,
  "error": "Widget 'team-alignment' requires Professional tier or higher",
  "code": "FORBIDDEN",
  "details": {
    "widgetId": "team-alignment",
    "requiredTier": "professional",
    "currentTier": "starter"
  }
}
```

---

## Reset Dashboard Configuration

**DELETE** `/account/api/v1/dashboard/config`

Reset the user's dashboard to the system default configuration.

### Example Request

```bash
DELETE /account/api/v1/dashboard/config
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "default",
    "userId": "user_xyz789",
    "name": "Default Dashboard",
    "isDefault": true,
    "widgets": [...],
    "layouts": {...},
    "createdAt": "2026-01-09T00:00:00Z",
    "updatedAt": "2026-01-09T00:00:00Z"
  }
}
```

---

## Get Available Templates

**GET** `/account/api/v1/dashboard/templates`

Retrieve all available dashboard templates the user can access based on their subscription tier.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category: `starter`, `executive`, `operations` |

### Response Structure

```typescript
interface DashboardTemplatesResponse {
  success: boolean;
  data: DashboardTemplate[];
}

interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  category: 'starter' | 'executive' | 'operations' | 'custom';
  tier: 'free' | 'starter' | 'professional' | 'enterprise';
  previewImageUrl?: string;
  widgetCount: number;
  isAccessible: boolean;          // Based on user's subscription
}
```

### Example Request

```bash
GET /account/api/v1/dashboard/templates?category=executive
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Example Response

```json
{
  "success": true,
  "data": [
    {
      "id": "template_starter_basic",
      "name": "Getting Started",
      "description": "A simple dashboard with essential widgets to get you started",
      "category": "starter",
      "tier": "free",
      "previewImageUrl": "/assets/templates/starter-basic.png",
      "widgetCount": 3,
      "isAccessible": true
    },
    {
      "id": "template_exec_overview",
      "name": "Executive Overview",
      "description": "High-level view of goals, measures, and team performance",
      "category": "executive",
      "tier": "professional",
      "previewImageUrl": "/assets/templates/exec-overview.png",
      "widgetCount": 6,
      "isAccessible": true
    }
  ]
}
```

---

## Get Template Details

**GET** `/account/api/v1/dashboard/templates/{id}`

Retrieve detailed configuration for a specific template.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Template identifier |

### Response

```json
{
  "success": true,
  "data": {
    "id": "template_exec_overview",
    "name": "Executive Overview",
    "description": "High-level view of goals, measures, and team performance",
    "category": "executive",
    "tier": "professional",
    "previewImageUrl": "/assets/templates/exec-overview.png",
    "widgets": [
      {
        "widgetId": "hot-list",
        "settings": {
          "showPastDueActions": true,
          "showAtRiskMeasures": true,
          "showCriticalIssues": true,
          "maxItems": 5
        },
        "layout": { "x": 0, "y": 0, "w": 2, "h": 2 }
      }
    ],
    "isAccessible": true
  }
}
```

### Error Responses

**404 Not Found**
```json
{
  "success": false,
  "error": "Template not found",
  "code": "RESOURCE_NOT_FOUND"
}
```

---

## Apply Template

**POST** `/account/api/v1/dashboard/config/apply-template`

Apply a template to the user's dashboard, replacing their current configuration.

### Request Body

```typescript
interface ApplyTemplateRequest {
  templateId: string;
}
```

### Example Request

```bash
POST /account/api/v1/dashboard/config/apply-template
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

```json
{
  "templateId": "template_exec_overview"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": "config_abc123",
    "userId": "user_xyz789",
    "name": "Executive Overview",
    "isDefault": false,
    "widgets": [...],
    "layouts": {...},
    "createdAt": "2026-01-09T10:00:00Z",
    "updatedAt": "2026-01-09T10:00:00Z"
  }
}
```

---

## Get Widget Catalog

**GET** `/account/api/v1/dashboard/widgets`

Retrieve the complete widget catalog with all available widget definitions. This provides metadata about widgets including their categories, descriptions, size constraints, and accessibility. The frontend uses this as the single source of truth for available widgets.

**Note**: Widget accessibility is determined by the backend based on the user's current subscription tier and enabled features. Refresh strategies and intervals are implementation details handled by individual widget components, not part of the catalog definition.

### Example Request

```bash
GET /account/api/v1/dashboard/widgets
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Response

Response contains a standard envelope with `success` boolean and `data` array of widget definitions.

```json
{
  "success": true,
  "data": [
    {
      "id": "hot-list",
      "name": "Hot List",
      "description": "View urgent items: past due actions, at-risk measures, and critical issues",
      "category": "overview",
      "tags": ["urgent", "alerts", "priority", "at-risk"],
      "isAccessible": true,
      "previewImage": "/assets/widgets/hot-list-preview.png",
      "size": {
        "defaultW": 2,
        "defaultH": 3,
        "minW": 2,
        "minH": 2,
        "maxW": 3,
        "maxH": 5
      }
    },
    {
      "id": "action-list",
      "name": "Action List",
      "description": "Filtered and sorted list of actions with customizable views",
      "category": "actions",
      "tags": ["actions", "tasks", "todo", "list"],
      "isAccessible": true,
      "size": {
        "defaultW": 3,
        "defaultH": 4,
        "minW": 2,
        "minH": 3,
        "maxW": 5,
        "maxH": 6
      }
    },
    {
      "id": "team-alignment",
      "name": "Team Alignment",
      "description": "Measure team alignment across values, goals, and collaboration",
      "category": "team",
      "tags": ["team", "alignment", "collaboration", "department"],
      "isAccessible": false,
      "size": {
        "defaultW": 3,
        "defaultH": 3,
        "minW": 2,
        "minH": 2,
        "maxW": 4,
        "maxH": 4
      }
    }
  ]
}
```

### Response Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | array | yes | Array of widget definition objects |
| `data[].id` | string | yes | Unique widget identifier (e.g., "hot-list", "action-list"). Must be unique and stable across system updates |
| `data[].name` | string | yes | Display name for the widget |
| `data[].description` | string | yes | Description shown in widget gallery |
| `data[].category` | string | yes | Widget category. Must be one of: `overview`, `actions`, `goals`, `measures`, `issues`, `insights`, `team` |
| `data[].tags` | array of strings | no | Optional free-form tags for search/filtering. Common examples: "urgent", "alerts", "priority", "actions", "tasks", "team", "alignment" |
| `data[].isAccessible` | boolean | yes | Indicates if current user can access this widget. Determined by backend based on user's subscription tier and enabled features |
| `data[].previewImage` | string | no | Optional preview image URL for widget gallery |
| `data[].size` | object | yes | Size constraints in grid units |
| `data[].size.defaultW` | number | yes | Default width in grid units when adding widget (1-12) |
| `data[].size.defaultH` | number | yes | Default height in grid rows when adding widget |
| `data[].size.minW` | number | yes | Minimum width in grid columns (1-12) |
| `data[].size.minH` | number | yes | Minimum height in grid rows |
| `data[].size.maxW` | number | yes | Maximum width in grid columns (1-12) |
| `data[].size.maxH` | number | yes | Maximum height in grid rows |

### Widget Categories

| Category | Description | Example Widgets |
|----------|-------------|-----------------|
| `overview` | Summary/aggregation widgets | Hot List, Performance Score |
| `actions` | Action management widgets | Action List, Actions By Status |
| `goals` | Goal tracking widgets | Goal Progress |
| `measures` | Metric visualization widgets | Measure Graph |
| `issues` | Issue management widgets | Issue List |
| `insights` | AI/coaching insights widgets | AI Insights |
| `team` | Team analytics widgets | Team Alignment |

### Field Constraints

- **Widget ID**: Must be unique, alphanumeric with hyphens, stable across system updates
- **Category**: Must exactly match one of the valid category values listed above
- **Size constraints**:
  - All size values must be positive integers
  - `minW` and `maxW` must be between 1 and 12 (grid columns)
  - `minW` ≤ `defaultW` ≤ `maxW`
  - `minH` ≤ `defaultH` ≤ `maxH`
- **Tags**: Array of strings, optional. Used for search/filtering only. No validation rules on tag values.
- **Preview Image**: Must be a valid URL if provided

### Business Rules

- Returns all widgets available in the system, regardless of user's subscription tier
- `isAccessible` field is calculated by backend based on:
  - User's current subscription tier
  - Enabled feature flags for the user
  - Backend-evaluated access rules
- Widget IDs must remain stable across updates (used in saved dashboard configurations)
- Size constraints use grid units (default grid is 5 columns for large screens, see Grid Configuration section)
- Descriptions and metadata can be updated dynamically without frontend code changes
- Refresh strategies and intervals are widget implementation details handled in widget code, not included in catalog

### Error Responses

**401 Unauthorized**
```json
{
  "success": false,
  "error": "Unauthorized",
  "code": "UNAUTHORIZED"
}
```

**500 Internal Server Error**
```json
{
  "success": false,
  "error": "Internal server error",
  "code": "INTERNAL_SERVER_ERROR"
}
```

---

# Traction Service Endpoints

## Hot List Widget

**GET** `/traction/api/v1/dashboard/widgets/hot-list/data`

Get urgent items: past due actions, at-risk measures, and critical issues.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `showPastDueActions` | boolean | true | Include past due actions |
| `showAtRiskMeasures` | boolean | true | Include at-risk measures |
| `showCriticalIssues` | boolean | true | Include critical issues |
| `maxItemsPerSection` | number | 5 | Max items per section |

### Response

```json
{
  "success": true,
  "data": {
    "pastDueActions": [
      {
        "id": "action_001",
        "title": "Complete Q4 budget review",
        "daysOverdue": 3,
        "priority": "high",
        "assigneeName": "John Doe"
      }
    ],
    "atRiskMeasures": [
      {
        "id": "m1",
        "name": "Monthly Revenue",
        "variance": -15,
        "goalTitle": "Achieve $1.2M ARR"
      }
    ],
    "criticalIssues": [
      {
        "id": "issue_001",
        "title": "Production outage",
        "impact": "critical",
        "daysOpen": 1,
        "reporterName": "Alice Chen"
      }
    ]
  }
}
```

---

## Recent Activity Widget

**GET** `/traction/api/v1/dashboard/widgets/recent-activity/data`

Get recent activities across the system.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `maxItems` | number | 5 | Maximum activities |
| `activityTypes` | string | - | Comma-separated types |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "activity_001",
      "type": "decision",
      "title": "Decision made",
      "description": "Decided to focus on enterprise customers",
      "entityType": "goal",
      "entityId": "goal_001",
      "entityName": "Achieve $1.2M ARR",
      "createdAt": "2026-01-08T09:15:00Z",
      "userName": "Jane Smith"
    }
  ]
}
```

---

## Action List Widget

**GET** `/traction/api/v1/dashboard/widgets/action-list/data`

Get a filtered and sorted list of actions.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dateRangePreset` | string | week | Date range filter |
| `startDate` | string | - | Custom start date (ISO 8601) |
| `endDate` | string | - | Custom end date (ISO 8601) |
| `statusFilter` | string | - | Comma-separated statuses |
| `assigneeFilter` | string | - | Comma-separated user IDs |
| `sortBy` | string | dueDate | Sort field |
| `sortOrder` | string | asc | Sort direction |
| `maxItems` | number | 10 | Maximum items to return |
| `showCompleted` | boolean | false | Include completed actions |

### Response

```json
{
  "success": true,
  "data": {
    "actions": [
      {
        "id": "action_001",
        "title": "Review marketing campaign",
        "dueDate": "2026-01-10T17:00:00Z",
        "priority": "high",
        "status": "in_progress",
        "progress": 60,
        "assigneeName": "John Doe",
        "goalTitle": "Achieve $1.2M ARR"
      }
    ],
    "total": 25
  }
}
```

---

## Issue List Widget

**GET** `/traction/api/v1/dashboard/widgets/issue-list/data`

Get a filtered list of issues.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `impactFilter` | string | - | Comma-separated impacts |
| `priorityFilter` | string | - | Comma-separated priorities |
| `statusFilter` | string | - | Comma-separated status categories |
| `sortBy` | string | priority | Sort field |
| `sortOrder` | string | desc | Sort direction |
| `maxItems` | number | 10 | Maximum items |

### Response

```json
{
  "success": true,
  "data": {
    "issues": [
      {
        "id": "issue_001",
        "title": "Customer churn increasing",
        "impact": "high",
        "priority": "high",
        "status": "investigating",
        "reporterName": "Customer Success",
        "affectedGoalsCount": 2,
        "createdAt": "2026-01-05T10:00:00Z"
      }
    ],
    "total": 15
  }
}
```

---

## Goal Progress Widget

**GET** `/traction/api/v1/dashboard/widgets/goal-progress/data`

Get goal progress with strategies and measures.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `goalIds` | string | - | Comma-separated goal IDs (optional, all if empty) |
| `status` | string | active | Goal status filter |
| `showStrategies` | boolean | true | Include strategy data |
| `showMeasures` | boolean | true | Include measure data |
| `maxGoals` | number | 5 | Maximum goals to return |

### Response

```json
{
  "success": true,
  "data": {
    "goals": [
      {
        "id": "goal_001",
        "title": "Achieve $1.2M ARR",
        "progress": 75,
        "expectedProgress": 70,
        "status": "on_track",
        "ownerName": "Jane Smith",
        "strategies": [
          {
            "id": "strat_001",
            "title": "Expand marketing",
            "progress": 65
          }
        ],
        "measures": [
          {
            "id": "measure_revenue",
            "name": "Monthly Revenue",
            "currentValue": 95000,
            "targetValue": 100000,
            "unit": "USD",
            "isPrimary": true
          }
        ]
      }
    ],
    "summary": {
      "total": 5,
      "onTrack": 3,
      "atRisk": 1,
      "behind": 1,
      "completed": 0
    }
  }
}
```

---

## Measure Graph Widget

**GET** `/traction/api/v1/dashboard/widgets/measure-graph/data`

Get measure data with historical values and trend.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `measureId` | string | Yes | Measure ID to display |
| `dateRange` | string | No | Time range: week, month, quarter, year, all |
| `startDate` | string | No | Custom start date (ISO 8601) |
| `endDate` | string | No | Custom end date (ISO 8601) |

### Response

```json
{
  "success": true,
  "data": {
    "measureId": "measure_revenue",
    "measureName": "Monthly Recurring Revenue",
    "unit": "USD",
    "direction": "up",
    "currentValue": 95000,
    "targetValue": 100000,
    "variance": -5.0,
    "dataPoints": [
      { "date": "2025-10-01", "value": 75000, "target": 80000 },
      { "date": "2025-11-01", "value": 82000, "target": 90000 },
      { "date": "2025-12-01", "value": 90000, "target": 95000 },
      { "date": "2026-01-01", "value": 95000, "target": 100000 }
    ],
    "trend": {
      "direction": "up",
      "changePercent": 26.7,
      "projection": 102000
    }
  }
}
```

---

## Actions By Status Widget

**GET** `/traction/api/v1/dashboard/widgets/actions-by-status/data`

Get action counts grouped by status, assignee, or priority.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `groupBy` | string | status | Group by: status, assignee, priority |
| `dateRange` | string | month | Date range filter |
| `chartType` | string | bar | Chart type: bar, pie, donut |

### Response

```json
{
  "success": true,
  "data": {
    "groups": [
      { "name": "Not Started", "key": "not_started", "count": 12, "percentage": 24 },
      { "name": "In Progress", "key": "in_progress", "count": 25, "percentage": 50 },
      { "name": "Blocked", "key": "blocked", "count": 3, "percentage": 6 },
      { "name": "Completed", "key": "completed", "count": 10, "percentage": 20 }
    ],
    "total": 50
  }
}
```

---

## AI Insights Widget

**GET** `/traction/api/v1/dashboard/widgets/ai-insights/data`

Get AI-generated insights and recommendations.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `maxItems` | number | 3 | Maximum insights |
| `priority` | string | all | Priority filter: all, high, critical |
| `insightTypes` | string | - | Comma-separated types |

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": "insight_001",
      "type": "recommendation",
      "title": "Focus on Enterprise Segment",
      "description": "Analysis shows 40% higher conversion rates in enterprise segment",
      "priority": "high",
      "category": "strategy",
      "createdAt": "2026-01-07T14:00:00Z",
      "actionable": true,
      "actionLabel": "View Analysis"
    }
  ]
}
```

---

## Performance Score Widget

**GET** `/traction/api/v1/dashboard/widgets/performance-score/data`

Get overall performance score with component breakdown.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dateRange` | string | month | Time range for calculation |
| `showHistory` | boolean | true | Include historical trend |

### Response

```json
{
  "success": true,
  "data": {
    "overallScore": 78,
    "previousScore": 72,
    "change": 6,
    "trend": "improving",
    "components": [
      { "name": "Goal Completion", "key": "goalCompletion", "score": 85, "weight": 0.3 },
      { "name": "Measure Performance", "key": "measurePerformance", "score": 72, "weight": 0.25 },
      { "name": "Timeline Adherence", "key": "timelineAdherence", "score": 68, "weight": 0.25 },
      { "name": "Business Growth", "key": "businessGrowth", "score": 87, "weight": 0.2 }
    ],
    "history": [
      { "date": "2025-10-01", "score": 65 },
      { "date": "2025-11-01", "score": 68 },
      { "date": "2025-12-01", "score": 72 },
      { "date": "2026-01-01", "score": 78 }
    ]
  }
}
```

---

## Team Alignment Widget

**GET** `/traction/api/v1/dashboard/widgets/team-alignment/data`

Get team alignment score with factor breakdown.

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `displayMode` | string | score | Display mode: score, factors, trend |
| `showHistory` | boolean | true | Include historical trend |

### Response

```json
{
  "success": true,
  "data": {
    "alignmentScore": 82,
    "previousScore": 78,
    "change": 4,
    "trend": "improving",
    "factors": [
      { "name": "Values Alignment", "key": "valuesAlignment", "score": 88, "icon": "heart" },
      { "name": "Goal Distribution", "key": "goalDistribution", "score": 75, "icon": "target" },
      { "name": "Collaboration", "key": "collaboration", "score": 85, "icon": "users" },
      { "name": "Communication", "key": "communication", "score": 80, "icon": "message" }
    ],
    "history": [
      { "date": "2025-10-01", "score": 72 },
      { "date": "2025-11-01", "score": 75 },
      { "date": "2025-12-01", "score": 78 },
      { "date": "2026-01-01", "score": 82 }
    ]
  }
}
```

---

# Data Types Summary

## Widget Categories

| Category | Description | Example Widgets |
|----------|-------------|-----------------|
| `overview` | Summary/aggregation | Hot List, Performance Score |
| `actions` | Action management | Action List, Actions By Status |
| `goals` | Goal tracking | Goal Progress |
| `measures` | Metric visualization | Measure Graph |
| `issues` | Issue management | Issue List |
| `insights` | AI/coaching | AI Insights |
| `team` | Team analytics | Team Alignment |

## Widget Access Control

Widget accessibility is determined by the backend based on:
- User's current subscription tier (free, starter, professional, enterprise)
- Enabled feature flags for the user
- Dynamic business rules managed by the backend

The widget catalog API returns `isAccessible: boolean` for each widget, eliminating the need for the frontend to evaluate tier requirements or feature flags. This allows the backend to manage tier definitions and access rules dynamically without requiring frontend code changes.

**Note**: Tier and feature requirements are internal backend concerns and are not exposed in the API response.

## Grid Configuration

```typescript
const GRID_CONFIG = {
  cols: { lg: 5, md: 4, sm: 3, xs: 2 },
  rowHeight: 120,                    // pixels
  breakpoints: { lg: 1200, md: 996, sm: 768, xs: 0 },
  containerPadding: [16, 16],
  margin: [16, 16],
};
```

---

# Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Widget/template not accessible for tier |
| `RESOURCE_NOT_FOUND` | 404 | Widget, template, or config not found |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

---

# Related APIs

- **[Dashboard, Reports & Activities API](./traction-service/dashboard-reports-activities-api.md)**: Command center data
- **[Actions API](./traction-service/actions-api.md)**: Action data source
- **[Goals API](./traction-service/goals-api.md)**: Goal data source
- **[Measures API](./traction-service/measures-api.md)**: Measure data source
- **[Issues API](./traction-service/issues-api.md)**: Issue data source
- **[Coaching Service](./coaching-service.md)**: AI insights data source
