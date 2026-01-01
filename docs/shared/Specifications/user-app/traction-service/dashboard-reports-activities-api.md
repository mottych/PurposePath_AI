# Dashboard, Reports & Activities APIs

**Service:** Traction Service  
**Version:** v7.0  
**Last Updated:** December 23, 2025

## Overview

This document covers three supporting API groups that provide aggregated views, reporting, and activity tracking across the Traction service:

- **Dashboard API**: Command center with real-time alerts and summaries
- **Reports API**: Generate and retrieve PDF/DOCX reports  
- **Activities API**: Activity feed tracking changes across entities

---

## Table of Contents

- [Dashboard API](#dashboard-api)
  - [GET /dashboard/command-center](#get-command-center-dashboard)
- [Reports API](#reports-api)
  - [GET /reports/company](#generate-company-report)
  - [POST /reports](#create-custom-report)
  - [GET /reports/{id}](#get-report)
- [Activities API](#activities-api)
  - [GET /activity/recent](#get-recent-activities)

---

# Dashboard API

**Base Path:** `/dashboard`

Provides aggregated views and real-time metrics for command center dashboards.

## Get Command Center Dashboard

**GET** `/dashboard/command-center`

Retrieve aggregated command center dashboard with alerts, goals, tasks, and summary statistics.

### Query Parameters

```typescript
interface CommandCenterParams {
  userId?: string;              // Optional user ID (defaults to authenticated user)
  daysAhead?: number;           // Task window in days (default: 7)
  varianceThreshold?: number;   // Measure variance % to trigger "at risk" (default: 10)
}
```

### Response Structure

```typescript
interface CommandCenterDashboardResponse {
  alerts: {
    kpisAtRisk: Array<{
      measureLinkId: string;
      measureId: string;
      measureName: string;
      currentValue: number | null;
      targetValue: number | null;
      variance: number | null;
      variancePercentage: number | null;
      goalId?: string;
      goalTitle?: string;
      strategyId?: string;
      strategyTitle?: string;
      ownerId: string;
      ownerName: string;
    }>;
    
    actionsPastDue: Array<{
      actionId: string;
      title: string;
      dueDate: string;          // ISO 8601
      daysPastDue: number;
      priority: string;
      assignedPersonId: string;
      assignedPersonName: string;
      goalId?: string;
      goalTitle?: string;
      strategyId?: string;
      strategyTitle?: string;
    }>;
    
    criticalIssues: Array<{
      issueId: string;
      title: string;
      impact: string;
      priority: string;
      reporterId: string;
      reporterName: string;
      dateReported: string;     // ISO 8601
      statusName: string;
    }>;
  };
  
  goals: Array<{
    id: string;
    title: string;
    intent: string;
    status: string;
    progress: number;           // 0-100
    ownerId: string;
    ownerName: string;
    
    strategies: Array<{
      id: string;
      title: string;
      progress: number;         // 0-100
      atRisk: boolean;
    }>;
    
    primaryKpi?: {
      measureId: string;
      name: string;
      currentValue: number | null;
      targetValue: number | null;
      progress: number;         // 0-100
    };
    
    stats: {
      totalStrategies: number;
      totalKpis: number;
      totalActions: number;
      activeActions: number;
      completedActions: number;
      atRiskCount: number;
    };
  }>;
  
  myTasks: Array<{
    id: string;
    title: string;
    description?: string;
    dueDate: string;            // ISO 8601
    priority: string;
    status: string;
    progress: number;           // 0-100
    goalId?: string;
    goalTitle?: string;
    strategyId?: string;
    strategyTitle?: string;
  }>;
  
  summaryStats: {
    totalActiveGoals: number;
    goalsOnTrack: number;
    goalsAtRisk: number;
    goalsBehind: number;
    totalKpis: number;
    kpisOnTrack: number;
    kpisAtRisk: number;
    kpisBehind: number;
    totalActiveActions: number;
    actionsPastDue: number;
    actionsThisWeek: number;
    openIssues: number;
    criticalIssues: number;
  };
  
  generatedAt: string;          // ISO 8601
}
```

### Example Request

```bash
GET /api/dashboard/command-center?daysAhead=14&varianceThreshold=15
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Example Response

```json
{
  "success": true,
  "data": {
    "alerts": {
      "kpisAtRisk": [
        {
          "measureLinkId": "link_abc123",
          "measureId": "kpi_revenue",
          "measureName": "Monthly Recurring Revenue",
          "currentValue": 85000,
          "targetValue": 100000,
          "variance": -15000,
          "variancePercentage": -15.0,
          "goalId": "goal_growth_2025",
          "goalTitle": "Achieve $1.2M ARR",
          "ownerId": "user_cfo",
          "ownerName": "Jane Smith"
        }
      ],
      "actionsPastDue": [
        {
          "actionId": "action_urgent123",
          "title": "Complete Q4 budget review",
          "dueDate": "2025-12-15T17:00:00Z",
          "daysPastDue": 8,
          "priority": "high",
          "assignedPersonId": "user_pm",
          "assignedPersonName": "John Doe",
          "goalId": "goal_operational",
          "goalTitle": "Operational Excellence"
        }
      ],
      "criticalIssues": [
        {
          "issueId": "issue_prod123",
          "title": "Production database timeout",
          "impact": "critical",
          "priority": "critical",
          "reporterId": "user_eng",
          "reporterName": "Alice Chen",
          "dateReported": "2025-12-22T09:30:00Z",
          "statusName": "In Progress"
        }
      ]
    },
    
    "goals": [
      {
        "id": "goal_growth_2025",
        "title": "Achieve $1.2M ARR",
        "intent": "Drive sustainable revenue growth",
        "status": "active",
        "progress": 75.0,
        "ownerId": "user_ceo",
        "ownerName": "CEO Name",
        
        "strategies": [
          {
            "id": "strat_marketing",
            "title": "Expand marketing reach",
            "progress": 65.0,
            "atRisk": true
          },
          {
            "id": "strat_sales",
            "title": "Increase sales conversion",
            "progress": 85.0,
            "atRisk": false
          }
        ],
        
        "primaryKpi": {
          "measureId": "kpi_revenue",
          "name": "Monthly Recurring Revenue",
          "currentValue": 85000,
          "targetValue": 100000,
          "progress": 85.0
        },
        
        "stats": {
          "totalStrategies": 2,
          "totalKpis": 5,
          "totalActions": 12,
          "activeActions": 8,
          "completedActions": 4,
          "atRiskCount": 1
        }
      }
    ],
    
    "myTasks": [
      {
        "id": "action_mytask1",
        "title": "Review marketing campaign results",
        "description": "Analyze Q4 campaign ROI",
        "dueDate": "2025-12-26T17:00:00Z",
        "priority": "high",
        "status": "in_progress",
        "progress": 60.0,
        "goalId": "goal_growth_2025",
        "goalTitle": "Achieve $1.2M ARR",
        "strategyId": "strat_marketing",
        "strategyTitle": "Expand marketing reach"
      }
    ],
    
    "summaryStats": {
      "totalActiveGoals": 5,
      "goalsOnTrack": 3,
      "goalsAtRisk": 1,
      "goalsBehind": 1,
      "totalKpis": 18,
      "kpisOnTrack": 12,
      "kpisAtRisk": 4,
      "kpisBehind": 2,
      "totalActiveActions": 34,
      "actionsPastDue": 3,
      "actionsThisWeek": 12,
      "openIssues": 8,
      "criticalIssues": 2
    },
    
    "generatedAt": "2025-12-23T10:30:00Z"
  }
}
```

### Business Rules

- **Default User**: If `userId` not provided, uses authenticated user
- **At-Risk KPIs**: KPIs with `variance >= varianceThreshold`
- **Past Due Actions**: Actions with `dueDate < now` and status != completed
- **Critical Issues**: Issues with impact = "critical" or "high"
- **Task Window**: `myTasks` includes actions due within next `daysAhead` days

### Use Cases

- **Command Center UI**: Real-time dashboard for executives
- **Alert Notifications**: Trigger notifications for at-risk items
- **Team Standups**: Quick status overview for daily meetings
- **Mobile Dashboard**: Optimized summary view for mobile apps

---

# Reports API

**Base Path:** `/reports`

Generate and retrieve PDF/DOCX reports for goals, KPIs, and company-wide analytics.

## Generate Company Report

**GET** `/reports/company`

Generate a company-wide PDF or DOCX report with goals, KPIs, actions, and analytics.

### Query Parameters

```typescript
interface GenerateCompanyReportParams {
  startDate?: string;           // ISO 8601 date (default: 30 days ago)
  endDate?: string;             // ISO 8601 date (default: today)
  format?: 'PDF' | 'DOCX';      // Default: 'PDF' (DOCX not yet supported)
  includeAnalytics?: boolean;   // Include analytics charts (default: true)
  includeCharts?: boolean;      // Include visual charts (default: true)
  sections?: string[];          // Sections to include (default: all)
}
```

### Available Sections

- `goals` - Goals summary and progress
- `measures` - Measure performance and trends
- `actions` - Action completion rates
- `issues` - Issue resolution statistics
- `people` - Team performance metrics
- `executive-summary` - High-level overview

### Response

Returns binary file (PDF or DOCX) with appropriate content-type header.

**Success (200 OK)**
- Content-Type: `application/pdf` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
- Content-Disposition: `attachment; filename="company-report-{timestamp}.pdf"`

### Example Request

```bash
GET /api/reports/company?startDate=2025-11-01&endDate=2025-12-23&format=PDF&includeAnalytics=true&sections=goals,measures,executive-summary
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Business Rules

- **PDF Only**: DOCX generation returns 501 Not Implemented
- **Date Range**: Default is last 30 days
- **Section Filtering**: If `sections` provided, only those sections included
- **Charts**: Requires `includeCharts=true` and sufficient data
- **File Naming**: `company-report-{yyyyMMdd-HHmmss}.pdf`

### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Invalid date range: startDate must be before endDate"
}
```

**501 Not Implemented**
```json
{
  "success": false,
  "error": "DOCX format is not yet supported. Please use PDF format."
}
```

---

## Create Custom Report

**POST** `/reports`

Create a custom report configuration (asynchronous generation).

### Request Body

```typescript
interface CreateReportRequest {
  title: string;                // Report title
  description?: string;         // Optional description
  reportType: string;           // "Company" | "Goals" | "KPIs" | "Actions" | "Custom"
  startDate?: string;           // ISO 8601 date
  endDate?: string;             // ISO 8601 date
  filters?: Record<string, any>; // Custom filters
  sections?: string[];          // Sections to include
}
```

### Example Request

```json
{
  "title": "Q4 2025 Measure Performance Report",
  "description": "Detailed analysis of Q4 Measure trends",
  "reportType": "KPIs",
  "startDate": "2025-10-01",
  "endDate": "2025-12-31",
  "sections": ["measures", "analytics", "trends"]
}
```

### Response

**Success (201 Created)**
```json
{
  "success": true,
  "data": {
    "id": "report_abc123",
    "title": "Q4 2025 Measure Performance Report",
    "description": "Detailed analysis of Q4 Measure trends",
    "status": "Pending",
    "reportType": "KPIs",
    "startDate": "2025-10-01T00:00:00Z",
    "endDate": "2025-12-31T23:59:59Z",
    "createdAt": "2025-12-23T10:30:00Z",
    "generatedAt": null,
    "format": "PDF"
  }
}
```

### Business Rules

- **Async Generation**: Report status is "Pending" initially
- **Status Polling**: Use GET /reports/{id} to check status
- **Ready Status**: When status = "Ready", `downloadUrl` is available

---

## Get Report

**GET** `/reports/{id}`

Retrieve report details and download URL.

### Path Parameters

- `id` (string, required): Report identifier (GUID)

### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "report_abc123",
    "title": "Q4 2025 Measure Performance Report",
    "status": "Ready",
    "reportType": "KPIs",
    "startDate": "2025-10-01T00:00:00Z",
    "endDate": "2025-12-31T23:59:59Z",
    "createdAt": "2025-12-23T10:30:00Z",
    "generatedAt": "2025-12-23T10:35:00Z",
    "format": "PDF",
    "downloadUrl": "/api/v1/reports/company?startDate=2025-10-01&endDate=2025-12-31"
  }
}
```

### Report Status Values

- `Pending` - Report generation queued
- `Processing` - Report generation in progress
- `Ready` - Report available for download
- `Failed` - Report generation failed
- `Expired` - Report download link expired (after 7 days)

---

# Activities API

**Base Path:** `/activity`

Track and retrieve activity feed across goals, strategies, actions, and issues.

## Get Recent Activities

**GET** `/activity/recent`

Retrieve paginated recent activities across all goals for the tenant.

### Query Parameters

```typescript
interface RecentActivitiesParams {
  page?: number;                // Page number (default: 1)
  size?: number;                // Items per page (default: 10, max: 100)
  type?: 'decision' | 'note' | 'attachment' | 'reading';  // Optional filter
}
```

### Response Structure

```typescript
interface RecentActivitiesResponse {
  success: boolean;
  data: Array<{
    id: string;
    type: 'decision' | 'note' | 'attachment' | 'reading';
    userId: string;
    userName: string;
    entityId?: string;          // Goal/Strategy/Action/Issue ID
    entityType?: 'goal' | 'strategy' | 'action' | 'issue';
    entityTitle?: string;
    description: string;
    timestamp: string;          // ISO 8601
  }>;
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

### Example Request

```bash
GET /api/activity/recent?page=1&size=20&type=decision
Authorization: Bearer {token}
X-Tenant-Id: {tenantId}
```

### Example Response

```json
{
  "success": true,
  "data": [
    {
      "id": "activity_abc123",
      "type": "decision",
      "userId": "user_ceo",
      "userName": "Jane Smith",
      "entityId": "goal_growth_2025",
      "entityType": "goal",
      "entityTitle": "Achieve $1.2M ARR",
      "description": "Decided to focus on enterprise customers in Q1 2026",
      "timestamp": "2025-12-23T09:15:00Z"
    },
    {
      "id": "activity_def456",
      "type": "note",
      "userId": "user_pm",
      "userName": "John Doe",
      "entityId": "strat_marketing",
      "entityType": "strategy",
      "entityTitle": "Expand marketing reach",
      "description": "Updated campaign budget allocation",
      "timestamp": "2025-12-23T08:45:00Z"
    },
    {
      "id": "activity_ghi789",
      "type": "attachment",
      "userId": "user_analyst",
      "userName": "Alice Chen",
      "entityId": "kpi_revenue",
      "entityType": "measure",
      "entityTitle": "Monthly Recurring Revenue",
      "description": "Uploaded Q4 revenue analysis spreadsheet",
      "timestamp": "2025-12-22T16:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 147,
    "totalPages": 8
  }
}
```

### Activity Types

| Type | Description |
|------|-------------|
| `decision` | Strategic decision made |
| `note` | Comment or note added |
| `attachment` | File or document attached |
| `reading` | Weekly/monthly review reading |

### Business Rules

- **Pagination**: Default 10 items per page, max 100
- **Tenant Scoped**: Only activities for current tenant
- **Chronological**: Sorted by timestamp descending (newest first)
- **Empty Response**: Returns 200 with empty array if no activities

### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Invalid activity type: invalid_type"
}
```

---

## TypeScript Usage Examples

### Dashboard Command Center

```typescript
import axios from 'axios';

async function getCommandCenter(
  daysAhead: number = 7,
  varianceThreshold: number = 10
) {
  const response = await axios.get('/api/dashboard/command-center', {
    params: { daysAhead, varianceThreshold },
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-Id': tenantId
    }
  });
  
  const { alerts, summaryStats, myTasks } = response.data.data;
  
  console.log(`Critical Alerts: ${alerts.criticalIssues.length}`);
  console.log(`KPIs At Risk: ${alerts.kpisAtRisk.length}`);
  console.log(`Past Due Actions: ${alerts.actionsPastDue.length}`);
  console.log(`My Tasks This Week: ${myTasks.length}`);
  
  return response.data.data;
}

// Dashboard refresh every 5 minutes
setInterval(async () => {
  const dashboard = await getCommandCenter(14, 15);
  updateDashboardUI(dashboard);
}, 5 * 60 * 1000);
```

### Generate and Download Report

```typescript
async function generateCompanyReport(
  startDate: string,
  endDate: string,
  sections: string[] = ['goals', 'measures', 'executive-summary']
) {
  const response = await axios.get('/api/reports/company', {
    params: {
      startDate,
      endDate,
      format: 'PDF',
      includeAnalytics: true,
      includeCharts: true,
      sections: sections.join(',')
    },
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-Id': tenantId
    },
    responseType: 'blob'  // Important for binary data
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `company-report-${Date.now()}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

// Generate Q4 report
await generateCompanyReport('2025-10-01', '2025-12-31');
```

### Activity Feed with Infinite Scroll

```typescript
async function loadActivities(
  page: number = 1,
  size: number = 20,
  type?: 'decision' | 'note' | 'attachment' | 'reading'
) {
  const response = await axios.get('/api/activity/recent', {
    params: { page, size, type },
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-Id': tenantId
    }
  });
  
  return response.data;
}

// Infinite scroll implementation
class ActivityFeed {
  private currentPage = 1;
  private activities: any[] = [];
  
  async loadMore() {
    const result = await loadActivities(this.currentPage, 20);
    this.activities.push(...result.data);
    this.currentPage++;
    return result.pagination.page < result.pagination.totalPages;
  }
  
  async filterByType(type: string) {
    this.currentPage = 1;
    this.activities = [];
    const result = await loadActivities(1, 20, type);
    this.activities = result.data;
  }
}

const feed = new ActivityFeed();
await feed.loadMore();  // Load first 20
// ... user scrolls down ...
await feed.loadMore();  // Load next 20
```

### Create Async Report and Poll Status

```typescript
async function createAndDownloadReport(
  title: string,
  reportType: string,
  startDate: string,
  endDate: string
) {
  // Step 1: Create report
  const createResponse = await axios.post('/api/reports', {
    title,
    reportType,
    startDate,
    endDate,
    sections: ['goals', 'measures', 'analytics']
  }, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-Id': tenantId
    }
  });
  
  const reportId = createResponse.data.data.id;
  
  // Step 2: Poll for completion
  let status = 'Pending';
  let downloadUrl = null;
  
  while (status !== 'Ready' && status !== 'Failed') {
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
    
    const statusResponse = await axios.get(`/api/reports/${reportId}`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-Id': tenantId
      }
    });
    
    status = statusResponse.data.data.status;
    downloadUrl = statusResponse.data.data.downloadUrl;
  }
  
  if (status === 'Ready') {
    console.log(`Report ready: ${downloadUrl}`);
    window.open(downloadUrl, '_blank');
  } else {
    console.error('Report generation failed');
  }
}

// Usage
await createAndDownloadReport(
  'Q4 2025 Performance',
  'Company',
  '2025-10-01',
  '2025-12-31'
);
```

---

## Related APIs

- **[Goals API](./goals-api.md)**: Goal data for dashboard and reports
- **[KPIs API](./measures-api.md)**: Measure metrics for dashboard and reports
- **[Actions API](./actions-api.md)**: Action data for task tracking
- **[Issues API](./issues-api.md)**: Issue data for alerts

---

## Changelog

### v7.0 (December 23, 2025)
- **Dashboard**: Command center with real-time alerts, goals, tasks, summary stats
- **Reports**: Company report generation (PDF), async custom reports
- **Activities**: Paginated activity feed with type filtering

---

## Known Limitations

1. **DOCX Reports**: Not yet implemented (returns 501)
2. **Custom Report Storage**: Currently placeholder implementation
3. **Report Expiry**: Download links expire after 7 days (not yet enforced)
4. **Activity Real-time**: Polling-based, not using SSE/WebSockets yet

---

## Support

For questions or issues:
- **GitHub Issues**: [PurposePath Repository](https://github.com/purposepath/backend)
- **Slack**: #traction-service channel
- **Email**: backend-support@purposepath.com
