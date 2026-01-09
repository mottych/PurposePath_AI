# Dashboard Configuration API

**Service:** Traction Service  
**Version:** 1.0  
**Last Updated:** January 8, 2026

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/config` | Get user's dashboard configuration |
| PUT | `/dashboard/config` | Save user's dashboard configuration |
| DELETE | `/dashboard/config` | Reset dashboard to default |
| GET | `/dashboard/templates` | Get available dashboard templates |
| GET | `/dashboard/templates/{id}` | Get specific template details |
| GET | `/dashboard/widgets` | Get available widget catalog |
| GET | `/dashboard/widgets/{widgetId}/data` | Get widget-specific data |

## Revisions

| Date | Version | Summary |
|------|---------|---------|
| January 8, 2026 | 1.0 | Initial specification for customizable dashboard system |

---

## Overview

The Dashboard Configuration API provides endpoints for managing user-customizable dashboards with drag-and-drop widgets. Users can personalize their dashboard layout, configure individual widgets, and save their preferences.

### Key Concepts

- **Dashboard Config**: A user's complete dashboard state (widgets, layout, settings)
- **Widget Definition**: A widget type from the catalog (e.g., "action-list", "measure-graph")
- **Widget Instance**: A specific widget placed on a user's dashboard with its settings
- **Layout**: Position and size of widgets in a responsive grid
- **Template**: Pre-configured dashboard layouts users can apply

---

## Base Configuration

**Base Path:** `/dashboard`

**Required Headers:**
```http
Authorization: Bearer {accessToken}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

---

# Dashboard Configuration Endpoints

## Get Dashboard Configuration

**GET** `/dashboard/config`

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
GET /api/v1/dashboard/config
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
      },
      {
        "instanceId": "action-list-1704700800001",
        "widgetId": "action-list",
        "title": "My Actions",
        "settings": {
          "dateRangePreset": "week",
          "statusFilter": ["notStarted", "inProgress"],
          "assigneeFilter": [],
          "sortBy": "dueDate",
          "sortOrder": "asc",
          "maxItems": 10,
          "showCompleted": false
        }
      },
      {
        "instanceId": "measure-graph-1704700800002",
        "widgetId": "measure-graph",
        "title": "Revenue Tracking",
        "settings": {
          "measureId": "measure_revenue_001",
          "timeRange": "quarter",
          "chartType": "line",
          "showTarget": true,
          "showTrend": true
        }
      }
    ],
    "layouts": {
      "lg": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 },
        { "i": "action-list-1704700800001", "x": 2, "y": 0, "w": 3, "h": 2 },
        { "i": "measure-graph-1704700800002", "x": 0, "y": 2, "w": 3, "h": 2 }
      ],
      "md": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 },
        { "i": "action-list-1704700800001", "x": 2, "y": 0, "w": 2, "h": 2 },
        { "i": "measure-graph-1704700800002", "x": 0, "y": 2, "w": 4, "h": 2 }
      ],
      "sm": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 3, "h": 2 },
        { "i": "action-list-1704700800001", "x": 0, "y": 2, "w": 3, "h": 2 },
        { "i": "measure-graph-1704700800002", "x": 0, "y": 4, "w": 3, "h": 2 }
      ],
      "xs": [
        { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 },
        { "i": "action-list-1704700800001", "x": 0, "y": 2, "w": 2, "h": 2 },
        { "i": "measure-graph-1704700800002", "x": 0, "y": 4, "w": 2, "h": 2 }
      ]
    },
    "createdAt": "2026-01-08T10:00:00Z",
    "updatedAt": "2026-01-08T15:30:00Z"
  }
}
```

### Default Dashboard Response

When a user has no saved configuration, return the system default:

```json
{
  "success": true,
  "data": {
    "id": "default",
    "userId": "user_xyz789",
    "name": "Default Dashboard",
    "isDefault": true,
    "widgets": [
      {
        "instanceId": "hot-list-default",
        "widgetId": "hot-list",
        "settings": {
          "showPastDueActions": true,
          "showAtRiskMeasures": true,
          "showCriticalIssues": true,
          "maxItems": 5
        }
      },
      {
        "instanceId": "recent-activity-default",
        "widgetId": "recent-activity",
        "settings": {
          "maxItems": 5,
          "activityTypes": []
        }
      }
    ],
    "layouts": {
      "lg": [
        { "i": "hot-list-default", "x": 0, "y": 0, "w": 2, "h": 2 },
        { "i": "recent-activity-default", "x": 2, "y": 0, "w": 3, "h": 2 }
      ],
      "md": [
        { "i": "hot-list-default", "x": 0, "y": 0, "w": 2, "h": 2 },
        { "i": "recent-activity-default", "x": 2, "y": 0, "w": 2, "h": 2 }
      ],
      "sm": [
        { "i": "hot-list-default", "x": 0, "y": 0, "w": 3, "h": 2 },
        { "i": "recent-activity-default", "x": 0, "y": 2, "w": 3, "h": 2 }
      ],
      "xs": [
        { "i": "hot-list-default", "x": 0, "y": 0, "w": 2, "h": 2 },
        { "i": "recent-activity-default", "x": 0, "y": 2, "w": 2, "h": 2 }
      ]
    },
    "createdAt": "2026-01-08T00:00:00Z",
    "updatedAt": "2026-01-08T00:00:00Z"
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

**PUT** `/dashboard/config`

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
PUT /api/v1/dashboard/config
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
    },
    {
      "instanceId": "goal-progress-1704700800003",
      "widgetId": "goal-progress",
      "title": "Q1 Goals",
      "settings": {
        "goalIds": ["goal_001", "goal_002"],
        "showStrategies": true,
        "showMeasures": true
      }
    }
  ],
  "layouts": {
    "lg": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 },
      { "i": "goal-progress-1704700800003", "x": 2, "y": 0, "w": 3, "h": 3 }
    ],
    "md": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 },
      { "i": "goal-progress-1704700800003", "x": 2, "y": 0, "w": 2, "h": 3 }
    ],
    "sm": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 3, "h": 2 },
      { "i": "goal-progress-1704700800003", "x": 0, "y": 2, "w": 3, "h": 3 }
    ],
    "xs": [
      { "i": "hot-list-1704700800000", "x": 0, "y": 0, "w": 2, "h": 2 },
      { "i": "goal-progress-1704700800003", "x": 0, "y": 2, "w": 2, "h": 3 }
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

**400 Bad Request - Layout Mismatch**
```json
{
  "success": false,
  "error": "Layout references non-existent widget instance",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "layouts.lg[0].i",
    "value": "non-existent-instance",
    "validInstances": ["hot-list-1704700800000", "goal-progress-1704700800003"]
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

**DELETE** `/dashboard/config`

Reset the user's dashboard to the system default configuration.

### Example Request

```bash
DELETE /api/v1/dashboard/config
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "Dashboard reset to default",
    "config": {
      "id": "default",
      "userId": "user_xyz789",
      "name": "Default Dashboard",
      "isDefault": true,
      "widgets": [...],
      "layouts": {...}
    }
  }
}
```

---

# Dashboard Templates Endpoints

## Get Available Templates

**GET** `/dashboard/templates`

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
GET /api/v1/dashboard/templates?category=executive
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
    },
    {
      "id": "template_ops_daily",
      "name": "Daily Operations",
      "description": "Action-focused dashboard for daily standups and task management",
      "category": "operations",
      "tier": "starter",
      "previewImageUrl": "/assets/templates/ops-daily.png",
      "widgetCount": 4,
      "isAccessible": true
    },
    {
      "id": "template_enterprise_full",
      "name": "Enterprise Command Center",
      "description": "Comprehensive dashboard with all widgets and advanced analytics",
      "category": "executive",
      "tier": "enterprise",
      "previewImageUrl": "/assets/templates/enterprise-full.png",
      "widgetCount": 10,
      "isAccessible": false
    }
  ]
}
```

---

## Get Template Details

**GET** `/dashboard/templates/{id}`

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
      },
      {
        "widgetId": "goal-progress",
        "settings": {
          "showStrategies": true,
          "showMeasures": true
        },
        "layout": { "x": 2, "y": 0, "w": 3, "h": 2 }
      },
      {
        "widgetId": "performance-score",
        "settings": {
          "showTrend": true,
          "showBreakdown": true
        },
        "layout": { "x": 0, "y": 2, "w": 2, "h": 2 }
      },
      {
        "widgetId": "team-alignment",
        "settings": {
          "showFactors": true
        },
        "layout": { "x": 2, "y": 2, "w": 2, "h": 2 }
      },
      {
        "widgetId": "ai-insights",
        "settings": {
          "maxItems": 3,
          "priorityFilter": ["high", "critical"]
        },
        "layout": { "x": 4, "y": 2, "w": 1, "h": 2 }
      },
      {
        "widgetId": "recent-activity",
        "settings": {
          "maxItems": 5
        },
        "layout": { "x": 0, "y": 4, "w": 5, "h": 1 }
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

**403 Forbidden - Template Not Accessible**
```json
{
  "success": false,
  "error": "Template 'Enterprise Command Center' requires Enterprise tier",
  "code": "FORBIDDEN",
  "details": {
    "templateId": "template_enterprise_full",
    "requiredTier": "enterprise",
    "currentTier": "professional"
  }
}
```

---

# Widget Catalog Endpoints

## Get Widget Catalog

**GET** `/dashboard/widgets`

Retrieve all available widgets with their definitions, settings schemas, and access requirements.

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category: `overview`, `actions`, `goals`, `measures`, `issues`, `insights`, `team` |
| `tier` | string | Filter by maximum tier: `free`, `starter`, `professional`, `enterprise` |

### Response Structure

```typescript
interface WidgetCatalogResponse {
  success: boolean;
  data: WidgetDefinition[];
}

interface WidgetDefinition {
  id: string;
  name: string;
  description: string;
  category: WidgetCategory;
  tier: WidgetTier;
  requiredFeature?: string;
  icon: string;                   // Lucide icon name
  size: {
    minW: number;
    minH: number;
    maxW: number;
    maxH: number;
    defaultW: number;
    defaultH: number;
  };
  settingsSchema: SettingsSchema;
  defaultSettings: Record<string, unknown>;
  isAccessible: boolean;          // Based on user's subscription
  accessReason?: string;          // Why widget is not accessible
}

interface SettingsSchema {
  fields: SettingField[];
}

interface SettingField {
  key: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'multiselect' | 'checkbox' | 'daterange' | 'entity-picker';
  description?: string;
  required?: boolean;
  defaultValue: unknown;
  options?: Array<{ value: string; label: string }>;
  entityType?: 'goal' | 'measure' | 'action' | 'issue' | 'user';
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
  };
}

type WidgetCategory = 'overview' | 'actions' | 'goals' | 'measures' | 'issues' | 'insights' | 'team';
type WidgetTier = 'free' | 'starter' | 'professional' | 'enterprise';
```

### Example Request

```bash
GET /api/v1/dashboard/widgets?category=actions
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Example Response

```json
{
  "success": true,
  "data": [
    {
      "id": "hot-list",
      "name": "Hot List",
      "description": "Shows urgent items: past due actions, at-risk measures, and critical issues",
      "category": "overview",
      "tier": "free",
      "icon": "Flame",
      "size": {
        "minW": 2,
        "minH": 2,
        "maxW": 3,
        "maxH": 4,
        "defaultW": 2,
        "defaultH": 2
      },
      "settingsSchema": {
        "fields": [
          {
            "key": "showPastDueActions",
            "label": "Show Past Due Actions",
            "type": "checkbox",
            "defaultValue": true
          },
          {
            "key": "showAtRiskMeasures",
            "label": "Show At-Risk Measures",
            "type": "checkbox",
            "defaultValue": true
          },
          {
            "key": "showCriticalIssues",
            "label": "Show Critical Issues",
            "type": "checkbox",
            "defaultValue": true
          },
          {
            "key": "maxItems",
            "label": "Maximum Items Per Section",
            "type": "number",
            "defaultValue": 5,
            "validation": { "min": 1, "max": 20 }
          }
        ]
      },
      "defaultSettings": {
        "showPastDueActions": true,
        "showAtRiskMeasures": true,
        "showCriticalIssues": true,
        "maxItems": 5
      },
      "isAccessible": true
    },
    {
      "id": "action-list",
      "name": "Action List",
      "description": "Display a filtered and sorted list of actions",
      "category": "actions",
      "tier": "starter",
      "icon": "CheckSquare",
      "size": {
        "minW": 2,
        "minH": 2,
        "maxW": 5,
        "maxH": 4,
        "defaultW": 3,
        "defaultH": 2
      },
      "settingsSchema": {
        "fields": [
          {
            "key": "dateRangePreset",
            "label": "Date Range",
            "type": "select",
            "defaultValue": "week",
            "options": [
              { "value": "today", "label": "Today" },
              { "value": "week", "label": "This Week" },
              { "value": "month", "label": "This Month" },
              { "value": "quarter", "label": "This Quarter" },
              { "value": "all", "label": "All Time" }
            ]
          },
          {
            "key": "statusFilter",
            "label": "Status Filter",
            "type": "multiselect",
            "defaultValue": [],
            "options": [
              { "value": "notStarted", "label": "Not Started" },
              { "value": "inProgress", "label": "In Progress" },
              { "value": "blocked", "label": "Blocked" },
              { "value": "completed", "label": "Completed" }
            ]
          },
          {
            "key": "assigneeFilter",
            "label": "Assignee Filter",
            "type": "entity-picker",
            "entityType": "user",
            "defaultValue": []
          },
          {
            "key": "sortBy",
            "label": "Sort By",
            "type": "select",
            "defaultValue": "dueDate",
            "options": [
              { "value": "dueDate", "label": "Due Date" },
              { "value": "priority", "label": "Priority" },
              { "value": "status", "label": "Status" },
              { "value": "createdAt", "label": "Created Date" }
            ]
          },
          {
            "key": "sortOrder",
            "label": "Sort Order",
            "type": "select",
            "defaultValue": "asc",
            "options": [
              { "value": "asc", "label": "Ascending" },
              { "value": "desc", "label": "Descending" }
            ]
          },
          {
            "key": "maxItems",
            "label": "Maximum Items",
            "type": "number",
            "defaultValue": 10,
            "validation": { "min": 1, "max": 50 }
          },
          {
            "key": "showCompleted",
            "label": "Show Completed Actions",
            "type": "checkbox",
            "defaultValue": false
          }
        ]
      },
      "defaultSettings": {
        "dateRangePreset": "week",
        "statusFilter": [],
        "assigneeFilter": [],
        "sortBy": "dueDate",
        "sortOrder": "asc",
        "maxItems": 10,
        "showCompleted": false
      },
      "isAccessible": true
    },
    {
      "id": "measure-graph",
      "name": "Measure Graph",
      "description": "Visualize a specific measure's progress over time",
      "category": "measures",
      "tier": "professional",
      "icon": "LineChart",
      "size": {
        "minW": 2,
        "minH": 2,
        "maxW": 5,
        "maxH": 4,
        "defaultW": 3,
        "defaultH": 2
      },
      "settingsSchema": {
        "fields": [
          {
            "key": "measureId",
            "label": "Measure",
            "type": "entity-picker",
            "entityType": "measure",
            "required": true,
            "defaultValue": null
          },
          {
            "key": "timeRange",
            "label": "Time Range",
            "type": "select",
            "defaultValue": "quarter",
            "options": [
              { "value": "month", "label": "This Month" },
              { "value": "quarter", "label": "This Quarter" },
              { "value": "year", "label": "This Year" },
              { "value": "all", "label": "All Time" }
            ]
          },
          {
            "key": "chartType",
            "label": "Chart Type",
            "type": "select",
            "defaultValue": "line",
            "options": [
              { "value": "line", "label": "Line Chart" },
              { "value": "bar", "label": "Bar Chart" },
              { "value": "area", "label": "Area Chart" }
            ]
          },
          {
            "key": "showTarget",
            "label": "Show Target Line",
            "type": "checkbox",
            "defaultValue": true
          },
          {
            "key": "showTrend",
            "label": "Show Trend Line",
            "type": "checkbox",
            "defaultValue": true
          }
        ]
      },
      "defaultSettings": {
        "measureId": null,
        "timeRange": "quarter",
        "chartType": "line",
        "showTarget": true,
        "showTrend": true
      },
      "isAccessible": true
    },
    {
      "id": "team-alignment",
      "name": "Team Alignment",
      "description": "Display team alignment score with factor breakdown",
      "category": "team",
      "tier": "enterprise",
      "requiredFeature": "teamAnalytics",
      "icon": "Users",
      "size": {
        "minW": 2,
        "minH": 2,
        "maxW": 3,
        "maxH": 3,
        "defaultW": 2,
        "defaultH": 2
      },
      "settingsSchema": {
        "fields": [
          {
            "key": "showFactors",
            "label": "Show Factor Breakdown",
            "type": "checkbox",
            "defaultValue": true
          },
          {
            "key": "showTrend",
            "label": "Show Historical Trend",
            "type": "checkbox",
            "defaultValue": true
          }
        ]
      },
      "defaultSettings": {
        "showFactors": true,
        "showTrend": true
      },
      "isAccessible": false,
      "accessReason": "Requires Enterprise tier"
    }
  ]
}
```

---

## Get Widget Data

**GET** `/dashboard/widgets/{widgetId}/data`

Retrieve data for a specific widget instance based on its settings.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `widgetId` | string | Widget definition ID from catalog |

### Query Parameters

Widget settings passed as query parameters. Each widget has different parameters based on its `settingsSchema`.

### Widget-Specific Endpoints

#### Hot List Widget

**GET** `/dashboard/widgets/hot-list/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `showPastDueActions` | boolean | true | Include past due actions |
| `showAtRiskMeasures` | boolean | true | Include at-risk measures |
| `showCriticalIssues` | boolean | true | Include critical issues |
| `maxItems` | number | 5 | Max items per section |

**Response:**
```json
{
  "success": true,
  "data": {
    "pastDueActions": [
      {
        "id": "action_001",
        "title": "Complete Q4 budget review",
        "dueDate": "2026-01-05T17:00:00Z",
        "daysPastDue": 3,
        "priority": "high",
        "assignedPersonId": "user_pm",
        "assignedPersonName": "John Doe"
      }
    ],
    "atRiskMeasures": [
      {
        "measureLinkId": "link_001",
        "measureId": "measure_revenue",
        "measureName": "Monthly Revenue",
        "currentValue": 85000,
        "targetValue": 100000,
        "variancePercentage": -15.0,
        "goalTitle": "Achieve $1.2M ARR"
      }
    ],
    "criticalIssues": [
      {
        "id": "issue_001",
        "title": "Production outage",
        "impact": "critical",
        "priority": "critical",
        "reporterName": "Alice Chen",
        "daysSinceReported": 1
      }
    ],
    "counts": {
      "pastDueActions": 3,
      "atRiskMeasures": 2,
      "criticalIssues": 1
    }
  }
}
```

#### Action List Widget

**GET** `/dashboard/widgets/action-list/data`

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

**Response:**
```json
{
  "success": true,
  "data": {
    "actions": [
      {
        "id": "action_001",
        "title": "Review marketing campaign",
        "description": "Analyze Q4 campaign ROI",
        "dueDate": "2026-01-10T17:00:00Z",
        "priority": "high",
        "status": "inProgress",
        "progress": 60,
        "assignedPersonId": "user_pm",
        "assignedPersonName": "John Doe",
        "goalId": "goal_001",
        "goalTitle": "Achieve $1.2M ARR"
      }
    ],
    "pagination": {
      "total": 25,
      "returned": 10,
      "hasMore": true
    }
  }
}
```

#### Measure Graph Widget

**GET** `/dashboard/widgets/measure-graph/data`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `measureId` | string | Yes | Measure ID to display |
| `timeRange` | string | No | Time range: month, quarter, year, all |
| `startDate` | string | No | Custom start date (ISO 8601) |
| `endDate` | string | No | Custom end date (ISO 8601) |

**Response:**
```json
{
  "success": true,
  "data": {
    "measure": {
      "id": "measure_revenue",
      "name": "Monthly Recurring Revenue",
      "unit": "USD",
      "direction": "up",
      "currentValue": 95000,
      "targetValue": 100000
    },
    "dataPoints": [
      { "date": "2025-10-01", "value": 75000, "target": 80000 },
      { "date": "2025-11-01", "value": 82000, "target": 90000 },
      { "date": "2025-12-01", "value": 90000, "target": 95000 },
      { "date": "2026-01-01", "value": 95000, "target": 100000 }
    ],
    "trend": {
      "direction": "up",
      "changePercentage": 26.7,
      "projectedValue": 102000,
      "projectedDate": "2026-02-01"
    }
  }
}
```

#### Goal Progress Widget

**GET** `/dashboard/widgets/goal-progress/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `goalIds` | string | - | Comma-separated goal IDs (optional, all if empty) |
| `status` | string | active | Goal status filter |
| `showStrategies` | boolean | true | Include strategy data |
| `showMeasures` | boolean | true | Include measure data |
| `maxGoals` | number | 5 | Maximum goals to return |

**Response:**
```json
{
  "success": true,
  "data": {
    "goals": [
      {
        "id": "goal_001",
        "title": "Achieve $1.2M ARR",
        "status": "active",
        "progress": 75,
        "ownerId": "user_ceo",
        "ownerName": "Jane Smith",
        "strategies": [
          {
            "id": "strat_001",
            "title": "Expand marketing",
            "progress": 65,
            "atRisk": true
          }
        ],
        "primaryMeasure": {
          "id": "measure_revenue",
          "name": "Monthly Revenue",
          "currentValue": 95000,
          "targetValue": 100000,
          "progress": 95
        }
      }
    ],
    "summary": {
      "totalGoals": 5,
      "onTrack": 3,
      "atRisk": 1,
      "behind": 1
    }
  }
}
```

#### Issue List Widget

**GET** `/dashboard/widgets/issue-list/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `impactFilter` | string | - | Comma-separated impacts |
| `priorityFilter` | string | - | Comma-separated priorities |
| `statusFilter` | string | - | Comma-separated status categories |
| `assigneeFilter` | string | - | Comma-separated user IDs |
| `sortBy` | string | priority | Sort field |
| `sortOrder` | string | desc | Sort direction |
| `maxItems` | number | 10 | Maximum items |

**Response:**
```json
{
  "success": true,
  "data": {
    "issues": [
      {
        "id": "issue_001",
        "title": "Customer churn increasing",
        "description": "Monthly churn rate increased to 5%",
        "impact": "high",
        "priority": "high",
        "statusName": "In Progress",
        "statusCategory": "active",
        "reporterId": "user_cs",
        "reporterName": "Customer Success",
        "assignedPersonId": "user_pm",
        "assignedPersonName": "John Doe",
        "createdAt": "2026-01-05T10:00:00Z",
        "daysSinceCreated": 3
      }
    ],
    "pagination": {
      "total": 15,
      "returned": 10,
      "hasMore": true
    }
  }
}
```

#### AI Insights Widget

**GET** `/dashboard/widgets/ai-insights/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `maxItems` | number | 3 | Maximum insights |
| `priorityFilter` | string | - | Comma-separated priorities |
| `categoryFilter` | string | - | Comma-separated categories |

**Response:**
```json
{
  "success": true,
  "data": {
    "insights": [
      {
        "id": "insight_001",
        "title": "Focus on Enterprise Segment",
        "description": "Analysis shows 40% higher conversion rates in enterprise segment",
        "category": "strategy",
        "priority": "high",
        "createdAt": "2026-01-07T14:00:00Z"
      }
    ]
  }
}
```

#### Actions By Status Widget

**GET** `/dashboard/widgets/actions-by-status/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `groupBy` | string | status | Group by: status, assignee, priority |
| `dateRangePreset` | string | month | Date range filter |
| `chartType` | string | bar | Chart type: bar, pie, donut |

**Response:**
```json
{
  "success": true,
  "data": {
    "groups": [
      { "name": "Not Started", "key": "notStarted", "count": 12, "percentage": 24 },
      { "name": "In Progress", "key": "inProgress", "count": 25, "percentage": 50 },
      { "name": "Blocked", "key": "blocked", "count": 3, "percentage": 6 },
      { "name": "Completed", "key": "completed", "count": 10, "percentage": 20 }
    ],
    "total": 50
  }
}
```

#### Recent Activity Widget

**GET** `/dashboard/widgets/recent-activity/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `maxItems` | number | 5 | Maximum activities |
| `activityTypes` | string | - | Comma-separated types |

**Response:**
```json
{
  "success": true,
  "data": {
    "activities": [
      {
        "id": "activity_001",
        "type": "decision",
        "description": "Decided to focus on enterprise customers",
        "userId": "user_ceo",
        "userName": "Jane Smith",
        "entityId": "goal_001",
        "entityType": "goal",
        "entityTitle": "Achieve $1.2M ARR",
        "timestamp": "2026-01-08T09:15:00Z"
      }
    ]
  }
}
```

#### Performance Score Widget

**GET** `/dashboard/widgets/performance-score/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `showTrend` | boolean | true | Include historical trend |
| `showBreakdown` | boolean | true | Include component breakdown |

**Response:**
```json
{
  "success": true,
  "data": {
    "overallScore": 78,
    "previousScore": 72,
    "change": 6,
    "trend": "improving",
    "components": {
      "goalCompletion": 85,
      "measurePerformance": 72,
      "timelineAdherence": 68,
      "businessGrowth": 87
    },
    "history": [
      { "date": "2025-10-01", "score": 65 },
      { "date": "2025-11-01", "score": 68 },
      { "date": "2025-12-01", "score": 72 },
      { "date": "2026-01-01", "score": 78 }
    ],
    "lastCalculated": "2026-01-08T00:00:00Z"
  }
}
```

#### Team Alignment Widget

**GET** `/dashboard/widgets/team-alignment/data`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `showFactors` | boolean | true | Include factor breakdown |
| `showTrend` | boolean | true | Include historical trend |

**Response:**
```json
{
  "success": true,
  "data": {
    "alignmentScore": 82,
    "previousScore": 78,
    "change": 4,
    "trend": "improving",
    "factors": {
      "valuesAlignment": 88,
      "goalDistribution": 75,
      "collaboration": 85,
      "communication": 80
    },
    "history": [
      { "date": "2025-10-01", "score": 72 },
      { "date": "2025-11-01", "score": 75 },
      { "date": "2025-12-01", "score": 78 },
      { "date": "2026-01-01", "score": 82 }
    ],
    "lastAssessment": "2026-01-05T00:00:00Z"
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

## Widget Tiers

| Tier | Description | Access |
|------|-------------|--------|
| `free` | Basic widgets | All users |
| `starter` | Standard widgets | Starter+ subscription |
| `professional` | Advanced widgets | Professional+ subscription |
| `enterprise` | Premium widgets | Enterprise subscription only |

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
