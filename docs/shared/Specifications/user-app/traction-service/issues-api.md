# Issues API Specification

**Service:** Traction Service  
**Base Path:** `/api/issues`  
**Version:** v7.1  
**Last Updated:** January 4, 2026

## Overview

The Issues API manages operational issues, bugs, blockers, and problems within the PurposePath system. Unlike Goals or Actions, Issues represent problems that need resolution rather than outcomes or tasks. Issues support configurable types and statuses, impact/priority tracking, lifecycle management, and can be converted into actionable items.

### Key Features

- **Configurable Status & Types**: Uses `IssueStatusConfigId` and `IssueTypeConfigId` for tenant-customizable workflows
- **Lifecycle Management**: Start, resolve, close, and reopen issues with specific endpoints
- **Impact & Priority Tracking**: Separate dimensions for business impact vs urgency
- **Tag-Based Organization**: Add/remove tags for flexible categorization
- **Relationship Management**: Link to goals, strategies, and actions
- **Issue Conversion**: Convert issues into one or more actions
- **Statistics Dashboard**: Aggregated metrics by status, type, impact, and timeline

### Design Notes

- **Configuration-Based Status/Types**: Unlike other APIs using simple enums, Issues use configurable status and type systems
- **Lifecycle Endpoints**: Dedicated endpoints for state transitions (start, resolve, close, reopen) ensure proper workflow
- **Bug-Specific Fields**: Includes environment, steps to reproduce, expected/actual behavior for bug tracking
- **Comma-Separated OR Filtering**: Priority and impact support OR logic (e.g., "high,critical")

---

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/issues` | List issues with filtering, sorting, pagination |
| POST | `/issues` | Create new issue with optional connections |
| GET | `/issues/{issueId}` | Get single issue by ID |
| PUT | `/issues/{issueId}` | Update issue fields |
| DELETE | `/issues/{issueId}` | Delete issue (soft delete) |
| PUT | `/issues/{issueId}/status` | Update issue status via config ID |
| PUT | `/issues/{issueId}/assign` | Assign issue to user |
| PUT | `/issues/{issueId}/start` | Start work on issue |
| PUT | `/issues/{issueId}/resolve` | Resolve issue with notes |
| PUT | `/issues/{issueId}/close` | Close issue |
| PUT | `/issues/{issueId}/reopen` | Reopen closed/resolved issue |
| PUT | `/issues/{issueId}/tags` | Add tags to issue |
| DELETE | `/issues/{issueId}/tags` | Remove tags from issue |
| GET | `/issues/stats` | Get aggregated issue statistics |
| POST | `/issues/{issueId}/convert-to-actions` | Convert issue to actions |
| PUT | `/issues:reorder` | Reorder issues (drag-and-drop sorting) |

---

## Common Data Models

### IssueResponse

```typescript
interface IssueResponse {
  id: string;                         // "issue_123abc" format
  title: string;                      // Max 200 characters
  description: string;                // Max 2000 characters
  typeConfigId: string;               // UUID of IssueTypeConfig
  statusConfigId: string;             // UUID of IssueStatusConfig
  impact: 'low' | 'medium' | 'high' | 'critical';
  priority: 'low' | 'medium' | 'high' | 'critical';
  reporterId: string;                 // User ID who reported
  reporterName?: string;              // Display name (optional)
  assignedPersonId?: string;          // User ID assigned to
  assignedPersonName?: string;        // Display name (optional)
  dueDate?: string;                   // ISO 8601 date (nullable)
  estimatedHours?: number;            // 0-1000 range
  actualHours?: number;               // 0-1000 range
  tags: string[];                     // Array of tag strings
  
  // Bug-specific fields
  environment?: string;               // Environment where issue occurs
  stepsToReproduce?: string;          // How to reproduce
  expectedBehavior?: string;          // What should happen
  actualBehavior?: string;            // What actually happens
  
  // Resolution fields
  rootCauseAnalysis?: string;         // Analysis of root cause
  resolutionNotes?: string;           // How issue was resolved
  
  displayOrder: number;               // Custom ordering (>= 0)
  
  connections: {
    goalIds: string[];
    strategyIds: string[];
    actionIds: string[];
  };
  
  createdAt: string;                  // ISO 8601 timestamp
  updatedAt: string;                  // ISO 8601 timestamp
  createdBy: string;                  // User ID
  updatedBy: string;                  // User ID
}
```

### Enumerations

```typescript
// IssueImpact - Business impact level
enum IssueImpact {
  Low = 'low',
  Medium = 'medium',
  High = 'high',
  Critical = 'critical'
}

// Priority - Urgency level (same as Actions)
enum Priority {
  Low = 'low',
  Medium = 'medium',
  High = 'high',
  Critical = 'critical'
}
```

**Impact vs Priority**: 
- **Impact**: Business consequence if unresolved (data loss = high, typo = low)
- **Priority**: Time urgency (blocking production = critical, nice-to-have = low)

---

## Endpoint Details

### 1. List Issues

**GET** `/issues`

Retrieve paginated list of issues with comprehensive filtering options.

#### Query Parameters

```typescript
interface GetIssuesParams {
  // Pagination
  page?: number;                    // Default: 1
  limit?: number;                   // Default: 20, max: 100
  
  // Filtering
  status?: string;                  // Comma-separated statusConfigIds for OR logic
  statusConfigId?: string;          // Single status config ID
  statusCategory?: string;          // "open" | "active" | "inactive" | "closed"
  typeConfigId?: string;            // Issue type config ID
  businessImpact?: string;          // Comma-separated: "low,medium,high,critical" (OR logic)
  priority?: string;                // Comma-separated: "low,medium,high,critical" (OR logic)
  assignedPersonId?: string;        // Filter by assignee
  reporterId?: string;              // Filter by reporter
  
  // Date range filtering
  createdAfter?: string;            // ISO 8601 date
  createdBefore?: string;           // ISO 8601 date
  dueAfter?: string;                // ISO 8601 date
  dueBefore?: string;               // ISO 8601 date
  
  // Tag filtering
  tags?: string;                    // Comma-separated: "bug,urgent"
  
  // Relationship filtering
  actionIds?: string;               // Comma-separated action IDs
  goalIds?: string;                 // Comma-separated goal IDs
  strategyIds?: string;             // Comma-separated strategy IDs
  
  // Sorting
  sort?: 'title' | 'status' | 'type' | 'impact' | 'priority' | 'dueDate' | 'createdAt' | 'updatedAt';
  order?: 'asc' | 'desc';           // Default: 'desc'
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": [
    {
      "id": "issue_abc123",
      "title": "Database connection timeout in production",
      "description": "Users experiencing 5-second delays on dashboard load",
      "typeConfigId": "550e8400-e29b-41d4-a716-446655440001",
      "statusConfigId": "550e8400-e29b-41d4-a716-446655440010",
      "impact": "high",
      "priority": "critical",
      "reporterId": "user_xyz789",
      "reporterName": "John Smith",
      "assignedPersonId": "user_abc456",
      "assignedPersonName": "Jane Doe",
      "dueDate": "2025-01-15",
      "estimatedHours": 8.0,
      "actualHours": null,
      "tags": ["bug", "performance", "database"],
      "environment": "Production AWS us-east-1",
      "stepsToReproduce": "1. Login as admin\n2. Navigate to dashboard\n3. Observe 5s delay",
      "expectedBehavior": "Dashboard loads within 1 second",
      "actualBehavior": "Dashboard takes 5+ seconds to load",
      "rootCauseAnalysis": null,
      "resolutionNotes": null,
      "displayOrder": 1,
      "connections": {
        "goalIds": ["goal_123"],
        "strategyIds": ["strat_456"],
        "actionIds": []
      },
      "createdAt": "2025-01-10T14:30:00Z",
      "updatedAt": "2025-01-10T15:45:00Z",
      "createdBy": "user_xyz789",
      "updatedBy": "user_abc456"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "totalPages": 3,
    "totalItems": 52,
    "hasNextPage": true,
    "hasPreviousPage": false
  }
}
```

#### Business Rules

- **Comma-Separated OR Logic**: `businessImpact=high,critical` returns issues with high OR critical impact
- **Filter Combination**: Multiple filters use AND logic (e.g., priority AND impact AND assignedPersonId)
- **Default Sorting**: By `createdAt desc` (newest first)
- **Pagination Limits**: Max 100 items per page

#### Validation Rules

- `page`: Must be >= 1
- `limit`: Must be 1-100
- `sort`: Must be one of allowed values
- `order`: Must be "asc" or "desc"
- Date filters: Must be valid ISO 8601 dates

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Invalid sort field. Allowed: title, status, type, impact, priority, dueDate, createdAt, updatedAt"
}
```

**401 Unauthorized**
```json
{
  "success": false,
  "error": "Missing or invalid authentication token"
}
```

---

### 2. Create Issue

**POST** `/issues`

Create a new issue with optional connections to goals, strategies, and actions.

#### Request Body

```typescript
interface CreateIssueRequest {
  title: string;                      // Required, max 200 chars
  description?: string;               // Optional, max 2000 chars
  typeConfigId?: string;              // Optional (defaults to Personnel type)
  businessImpact: 'low' | 'medium' | 'high' | 'critical';  // Required
  priority: 'low' | 'medium' | 'high' | 'critical';        // Required
  reportedBy: string;                 // Required, user ID
  dateReported?: string;              // Optional, ISO 8601 (defaults to now)
  statusId?: string;                  // Optional (defaults to "Identified")
  assignedPersonId?: string;          // Optional
  dueDate?: string;                   // Optional, ISO 8601 date
  estimatedHours?: number;            // Optional, 0-1000 range
  tags?: string[];                    // Optional
  environment?: string;               // Optional, for bugs
  stepsToReproduce?: string;          // Optional, for bugs
  expectedBehavior?: string;          // Optional, for bugs
  actualBehavior?: string;            // Optional, for bugs
  displayOrder?: number;              // Optional, >= 0
  connections?: {
    goalIds?: string[];
    strategyIds?: string[];
    actionIds?: string[];
  };
}
```

#### Example Request

```json
{
  "title": "API timeout on /dashboard endpoint",
  "description": "The dashboard endpoint times out after 30 seconds under high load",
  "typeConfigId": "550e8400-e29b-41d4-a716-446655440001",
  "businessImpact": "high",
  "priority": "critical",
  "reportedBy": "user_reporter123",
  "dateReported": "2025-01-10T10:00:00Z",
  "assignedPersonId": "user_dev456",
  "dueDate": "2025-01-20",
  "estimatedHours": 12.0,
  "tags": ["bug", "api", "performance"],
  "environment": "Production - AWS us-east-1",
  "stepsToReproduce": "1. Send 100 concurrent requests to /dashboard\n2. Observe timeout errors",
  "expectedBehavior": "API responds within 5 seconds",
  "actualBehavior": "API times out after 30 seconds",
  "displayOrder": 1,
  "connections": {
    "goalIds": ["goal_perf2025"],
    "strategyIds": ["strat_api_optimization"]
  }
}
```

#### Response

**Success (201 Created)**
```json
{
  "success": true,
  "data": {
    "id": "issue_new123",
    "title": "API timeout on /dashboard endpoint",
    "description": "The dashboard endpoint times out after 30 seconds under high load",
    "typeConfigId": "550e8400-e29b-41d4-a716-446655440001",
    "statusConfigId": "550e8400-e29b-41d4-a716-446655440010",
    "impact": "high",
    "priority": "critical",
    "reporterId": "user_reporter123",
    "assignedPersonId": "user_dev456",
    "dueDate": "2025-01-20",
    "estimatedHours": 12.0,
    "actualHours": null,
    "tags": ["bug", "api", "performance"],
    "environment": "Production - AWS us-east-1",
    "stepsToReproduce": "1. Send 100 concurrent requests to /dashboard\n2. Observe timeout errors",
    "expectedBehavior": "API responds within 5 seconds",
    "actualBehavior": "API times out after 30 seconds",
    "displayOrder": 1,
    "connections": {
      "goalIds": ["goal_perf2025"],
      "strategyIds": ["strat_api_optimization"],
      "actionIds": []
    },
    "createdAt": "2025-01-10T10:00:00Z",
    "updatedAt": "2025-01-10T10:00:00Z",
    "createdBy": "user_reporter123",
    "updatedBy": "user_reporter123"
  }
}
```

#### Business Rules

- **Default Type**: If `typeConfigId` not provided, uses default Personnel type
- **Default Status**: If `statusId` not provided, uses default "Identified" status
- **Default Date Reported**: If `dateReported` not provided, uses current timestamp
- **Automatic Connections**: Creates links to specified goals, strategies, actions atomically

#### Validation Rules

- `title`: Required, 1-200 characters
- `description`: Max 2000 characters
- `businessImpact`: Required, must be low/medium/high/critical
- `priority`: Required, must be low/medium/high/critical
- `reportedBy`: Required, must be valid user ID
- `estimatedHours`: 0-1000 range
- `displayOrder`: Must be >= 0
- `dueDate`: Must be valid ISO 8601 date

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Business impact must be one of: low, medium, high, critical"
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Type configuration not found"
}
```

---

### 3. Get Issue

**GET** `/issues/{issueId}`

Retrieve a single issue by its ID.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "title": "Database connection timeout in production",
    "description": "Users experiencing 5-second delays on dashboard load",
    "typeConfigId": "550e8400-e29b-41d4-a716-446655440001",
    "statusConfigId": "550e8400-e29b-41d4-a716-446655440010",
    "impact": "high",
    "priority": "critical",
    "reporterId": "user_xyz789",
    "reporterName": "John Smith",
    "assignedPersonId": "user_abc456",
    "assignedPersonName": "Jane Doe",
    "dueDate": "2025-01-15",
    "estimatedHours": 8.0,
    "actualHours": 6.5,
    "tags": ["bug", "performance", "database"],
    "environment": "Production AWS us-east-1",
    "stepsToReproduce": "1. Login as admin\n2. Navigate to dashboard\n3. Observe 5s delay",
    "expectedBehavior": "Dashboard loads within 1 second",
    "actualBehavior": "Dashboard takes 5+ seconds to load",
    "rootCauseAnalysis": "Connection pool exhaustion due to missing connection timeout",
    "resolutionNotes": "Added 10s connection timeout and increased pool size from 10 to 20",
    "displayOrder": 1,
    "connections": {
      "goalIds": ["goal_123"],
      "strategyIds": ["strat_456"],
      "actionIds": ["action_789"]
    },
    "createdAt": "2025-01-10T14:30:00Z",
    "updatedAt": "2025-01-12T16:20:00Z",
    "createdBy": "user_xyz789",
    "updatedBy": "user_abc456"
  }
}
```

#### Error Responses

**404 Not Found**
```json
{
  "success": false,
  "error": "Issue not found"
}
```

---

### 4. Update Issue

**PUT** `/issues/{issueId}`

Update one or more fields of an existing issue. All fields are optional - only provided fields will be updated.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface UpdateIssueRequest {
  title?: string;                     // Max 200 chars
  description?: string;               // Max 2000 chars
  typeConfigId?: string;              // Change issue type
  businessImpact?: 'low' | 'medium' | 'high' | 'critical';
  priority?: 'low' | 'medium' | 'high' | 'critical';
  assignedPersonId?: string;
  dueDate?: string;                   // ISO 8601 date
  estimatedHours?: number;            // 0-1000 range
  actualHours?: number;               // 0-1000 range
  tags?: string[];                    // Replaces existing tags
  environment?: string;
  stepsToReproduce?: string;
  expectedBehavior?: string;
  actualBehavior?: string;
  rootCauseAnalysis?: string;
  resolutionNotes?: string;
  displayOrder?: number;              // >= 0
  statusConfigId?: string;            // Change status (prefer /status endpoint)
}
```

#### Example Request

```json
{
  "priority": "high",
  "assignedPersonId": "user_newdev789",
  "estimatedHours": 10.0,
  "tags": ["bug", "performance", "database", "urgent"]
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "title": "Database connection timeout in production",
    "priority": "high",
    "assignedPersonId": "user_newdev789",
    "assignedPersonName": "Alice Johnson",
    "estimatedHours": 10.0,
    "tags": ["bug", "performance", "database", "urgent"],
    "updatedAt": "2025-01-12T17:00:00Z",
    "updatedBy": "user_currentuser"
    // ... other fields unchanged
  }
}
```

#### Business Rules

- **Partial Updates**: Only provided fields are updated
- **Tag Replacement**: Providing `tags` replaces entire tag array (not merge)
- **Validation**: Only validates fields that are provided
- **Status Changes**: Prefer dedicated `/status` endpoint for status changes

#### Validation Rules

- `title`: 1-200 characters (if provided)
- `description`: Max 2000 characters (if provided)
- `businessImpact`: Must be low/medium/high/critical (if provided)
- `priority`: Must be low/medium/high/critical (if provided)
- `estimatedHours`: 0-1000 range (if provided)
- `actualHours`: 0-1000 range (if provided)
- `displayOrder`: Must be >= 0 (if provided)

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Priority must be one of: low, medium, high, critical"
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Issue not found"
}
```

---

### 5. Delete Issue

**DELETE** `/issues/{issueId}`

Delete an issue (soft delete). The issue is marked as deleted but not physically removed from the database.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "deletedIssueId": "issue_abc123",
    "deletedAt": "2025-01-12T18:00:00Z"
  }
}
```

#### Business Rules

- **Soft Delete**: Issue is marked deleted, not physically removed
- **Cascade Behavior**: Connections to goals/strategies/actions are removed
- **Irreversible**: Cannot be undone via API (database restore only)

#### Error Responses

**404 Not Found**
```json
{
  "success": false,
  "error": "Issue not found"
}
```

---

### 6. Update Issue Status

**PUT** `/issues/{issueId}/status`

Update issue status using a status configuration ID. This is the preferred method for status changes.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface UpdateIssueStatusRequest {
  statusConfigId: string;             // Required, UUID of status config
  reason?: string;                    // Optional, reason for status change
  resolutionNotes?: string;           // Optional, notes about resolution
  actualHours?: number;               // Optional, 0-1000 range
}
```

#### Example Request

```json
{
  "statusConfigId": "550e8400-e29b-41d4-a716-446655440020",
  "reason": "Customer confirmed the fix works in production",
  "resolutionNotes": "Increased connection pool size and added timeout configuration",
  "actualHours": 8.5
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "statusConfigId": "550e8400-e29b-41d4-a716-446655440020",
    "actualHours": 8.5,
    "resolutionNotes": "Increased connection pool size and added timeout configuration",
    "updatedAt": "2025-01-13T09:30:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Domain Event**: Publishes `IssueStatusChanged` event (handled by Issue #222 refactoring)
- **Status Validation**: Status config must exist and belong to tenant
- **Workflow Enforcement**: Some status transitions may be restricted (configured per tenant)

#### Validation Rules

- `statusConfigId`: Required, must be valid UUID
- `actualHours`: 0-1000 range (if provided)

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Status configuration ID is required"
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Status configuration not found"
}
```

---

### 7. Assign Issue

**PUT** `/issues/{issueId}/assign`

Assign an issue to a specific user.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface AssignIssueRequest {
  assignedPersonId: string;           // Required, user ID
  reason?: string;                    // Optional, reason for assignment
}
```

#### Example Request

```json
{
  "assignedPersonId": "user_dev789",
  "reason": "Alice has expertise in database performance optimization"
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "assignedPersonId": "user_dev789",
    "assignedPersonName": "Alice Chen",
    "updatedAt": "2025-01-13T10:00:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Domain Event**: Publishes `IssueAssigned` event
- **Unassignment**: Pass empty string or null to unassign
- **User Validation**: Assigned user must exist in tenant

#### Validation Rules

- `assignedPersonId`: Required

#### Error Responses

**404 Not Found**
```json
{
  "success": false,
  "error": "User not found or not in tenant"
}
```

---

### 8. Start Issue

**PUT** `/issues/{issueId}/start`

Mark an issue as started and transition to "In Progress" status.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface StartIssueRequest {
  notes?: string;                     // Optional, notes about starting work
}
```

#### Example Request

```json
{
  "notes": "Beginning investigation by reviewing application logs"
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "statusConfigId": "550e8400-e29b-41d4-a716-446655440015",
    "updatedAt": "2025-01-13T11:00:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Status Lookup**: Uses tenant's default "In Progress" status config
- **TODO Note**: Current implementation has placeholder for status config lookup
- **Domain Event**: Publishes `IssueStarted` event

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "InProgressStatusConfigId is required in request"
}
```

---

### 9. Resolve Issue

**PUT** `/issues/{issueId}/resolve`

Mark an issue as resolved with required resolution notes.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface ResolveIssueRequest {
  resolutionNotes: string;            // Required, how issue was resolved
  rootCauseAnalysis?: string;         // Optional, analysis of root cause
  actualHours?: number;               // Optional, 0-1000 range
}
```

#### Example Request

```json
{
  "resolutionNotes": "Increased database connection pool from 10 to 20 connections and added 10-second timeout",
  "rootCauseAnalysis": "Connection pool was exhausted during peak traffic due to missing timeout configuration, causing new requests to hang indefinitely",
  "actualHours": 12.5
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "statusConfigId": "550e8400-e29b-41d4-a716-446655440025",
    "resolutionNotes": "Increased database connection pool from 10 to 20 connections and added 10-second timeout",
    "rootCauseAnalysis": "Connection pool was exhausted during peak traffic due to missing timeout configuration...",
    "actualHours": 12.5,
    "updatedAt": "2025-01-15T14:30:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Status Lookup**: Uses tenant's default "Resolved" status config
- **Required Notes**: Resolution notes are mandatory
- **Domain Event**: Publishes `IssueResolved` event
- **TODO Note**: Current implementation has placeholder for status config lookup

#### Validation Rules

- `resolutionNotes`: Required
- `actualHours`: 0-1000 range (if provided)

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Resolution notes are required"
}
```

---

### 10. Close Issue

**PUT** `/issues/{issueId}/close`

Close an issue permanently.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface CloseIssueRequest {
  reason?: string;                    // Optional, reason for closing
}
```

#### Example Request

```json
{
  "reason": "Verified fix in production for 48 hours with no recurrence"
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "statusConfigId": "550e8400-e29b-41d4-a716-446655440030",
    "updatedAt": "2025-01-17T10:00:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Status Lookup**: Uses tenant's default "Closed" status config
- **Domain Event**: Publishes `IssueClosed` event
- **TODO Note**: Current implementation has placeholder for status config lookup

---

### 11. Reopen Issue

**PUT** `/issues/{issueId}/reopen`

Reopen a closed or resolved issue.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface ReopenIssueRequest {
  reason: string;                     // Required, reason for reopening
}
```

#### Example Request

```json
{
  "reason": "Issue reoccurred in production - timeout errors returned after 72 hours"
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "statusConfigId": "550e8400-e29b-41d4-a716-446655440012",
    "updatedAt": "2025-01-20T09:00:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Status Lookup**: Uses tenant's default "Reopen" status config
- **Required Reason**: Must provide reason for reopening
- **Domain Event**: Publishes `IssueReopened` event
- **TODO Note**: Current implementation has placeholder for status config lookup

#### Validation Rules

- `reason`: Required

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Reason is required for reopening an issue"
}
```

---

### 12. Add Tags to Issue

**PUT** `/issues/{issueId}/tags`

Add one or more tags to an issue. Uses batch command for optimized single database operation.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface AddIssueTagsRequest {
  tags: string[];                     // Required, array of tag strings
}
```

#### Example Request

```json
{
  "tags": ["production", "hotfix", "customer-reported"]
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "tags": ["bug", "performance", "database", "production", "hotfix", "customer-reported"],
    "updatedAt": "2025-01-13T12:00:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Additive**: New tags are added to existing tags (not replaced)
- **Deduplication**: Duplicate tags are ignored
- **Batch Operation**: Single database write for all tags
- **Case-Sensitive**: Tags are case-sensitive

#### Validation Rules

- `tags`: Required, must be non-empty array

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "Tags array cannot be empty"
}
```

---

### 13. Remove Tags from Issue

**DELETE** `/issues/{issueId}/tags`

Remove one or more tags from an issue. Uses batch command for optimized single database operation.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface RemoveIssueTagsRequest {
  tags: string[];                     // Required, array of tag strings to remove
}
```

#### Example Request

```json
{
  "tags": ["hotfix", "urgent"]
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "id": "issue_abc123",
    "tags": ["bug", "performance", "database", "production"],
    "updatedAt": "2025-01-14T09:00:00Z"
    // ... other fields
  }
}
```

#### Business Rules

- **Subtractive**: Specified tags are removed from existing tags
- **Non-Existent Tags**: Attempting to remove non-existent tags is ignored (no error)
- **Batch Operation**: Single database write for all tag removals
- **Case-Sensitive**: Tag matching is case-sensitive

#### Validation Rules

- `tags`: Required, must be non-empty array

---

### 14. Get Issue Statistics

**GET** `/issues/stats`

Retrieve aggregated statistics about issues for the tenant.

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "totalIssues": 127,
    "openIssues": 42,
    "inProgressIssues": 18,
    "resolvedIssues": 35,
    "closedIssues": 30,
    "overdueIssues": 7,
    "criticalIssues": 5,
    "resolutionRate": 0.73,
    
    "typeStats": {
      "bugs": 45,
      "features": 12,
      "tasks": 38,
      "improvements": 22,
      "documentation": 10
    },
    
    "impactStats": {
      "low": 32,
      "medium": 58,
      "high": 28,
      "critical": 9
    },
    
    "timelineStats": {
      "averageResolutionTimeHours": 16.5,
      "issuesCreatedThisWeek": 8,
      "issuesResolvedThisWeek": 12,
      "issuesCreatedThisMonth": 34,
      "issuesResolvedThisMonth": 38
    }
  }
}
```

#### Data Model

```typescript
interface IssueStatsData {
  totalIssues: number;
  openIssues: number;
  inProgressIssues: number;
  resolvedIssues: number;
  closedIssues: number;
  overdueIssues: number;
  criticalIssues: number;
  resolutionRate: number;             // 0.0-1.0 (73% = 0.73)
  
  typeStats: {
    bugs: number;
    features: number;
    tasks: number;
    improvements: number;
    documentation: number;
  };
  
  impactStats: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  
  timelineStats: {
    averageResolutionTimeHours: number;
    issuesCreatedThisWeek: number;
    issuesResolvedThisWeek: number;
    issuesCreatedThisMonth: number;
    issuesResolvedThisMonth: number;
  };
}
```

#### Business Rules

- **Tenant Scoped**: Statistics only include issues for current tenant
- **Resolution Rate**: (Resolved + Closed) / Total Issues
- **Overdue**: Issues with dueDate < now and status != closed/resolved

---

### 15. Convert Issue to Actions

**POST** `/issues/{issueId}/convert-to-actions`

Convert an issue into one or more actions. Actions inherit the issue's goal/strategy connections and are automatically linked back to the issue.

#### Path Parameters

- `issueId` (string, required): Issue identifier

#### Request Body

```typescript
interface ConvertIssueToActionsRequest {
  actions: Array<{
    title: string;                    // Required, max 200 chars
    description?: string;             // Optional, max 5000 chars
    assignedPersonId?: string;        // Optional
    priority: 'low' | 'medium' | 'high' | 'critical';  // Required
  }>;                                 // Required, min 1 action
  newStatusId?: string;               // Optional, new status for issue after conversion
}
```

#### Example Request

```json
{
  "actions": [
    {
      "title": "Increase database connection pool size",
      "description": "Increase connection pool from 10 to 20 in production configuration",
      "assignedPersonId": "user_dev789",
      "priority": "critical"
    },
    {
      "title": "Add connection timeout configuration",
      "description": "Add 10-second timeout to prevent hanging connections",
      "assignedPersonId": "user_dev789",
      "priority": "critical"
    },
    {
      "title": "Monitor connection pool metrics",
      "description": "Set up CloudWatch dashboards to monitor connection pool usage",
      "assignedPersonId": "user_ops456",
      "priority": "high"
    }
  ],
  "newStatusId": "550e8400-e29b-41d4-a716-446655440015"
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "actionIds": [
      "action_new001",
      "action_new002",
      "action_new003"
    ]
  }
}
```

#### Business Rules

- **Inheritance**: Actions inherit issue's goal/strategy connections automatically
- **Bidirectional Link**: Actions are linked to the originating issue
- **Atomic Creation**: All actions created in single transaction (all or nothing)
- **Optional Status Change**: Can optionally update issue status after conversion
- **Action Properties**: Actions use issue's dueDate if no specific date provided

#### Validation Rules

- `actions`: Required, must have at least 1 action
- `actions[].title`: Required, max 200 characters
- `actions[].description`: Max 5000 characters
- `actions[].priority`: Required, must be low/medium/high/critical

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "At least one action is required"
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Issue not found"
}
```

---

### 16. Reorder Issues

**PUT** `/issues:reorder`

Reorder issues (drag-and-drop sorting). Updates the `displayOrder` field for each issue based on its position in the provided array. Similar to `/operations/issue-statuses:reorder` pattern.

#### Request Body

```typescript
interface ReorderIssuesRequest {
  issueIds: string[];                 // Ordered array of issue IDs (min 1 item)
}
```

#### Example Request

```json
{
  "issueIds": [
    "issue_123abc",
    "issue_456def",
    "issue_789ghi",
    "issue_012jkl"
  ]
}
```

#### Response

**Success (200 OK)**
```json
{
  "success": true,
  "data": {
    "issues": [
      {
        "id": "issue_123abc",
        "title": "Critical production bug",
        "displayOrder": 0,
        // ... other issue fields
      },
      {
        "id": "issue_456def",
        "title": "Database connection timeout",
        "displayOrder": 1,
        // ... other issue fields
      },
      {
        "id": "issue_789ghi",
        "title": "UI rendering issue",
        "displayOrder": 2,
        // ... other issue fields
      },
      {
        "id": "issue_012jkl",
        "title": "Performance degradation",
        "displayOrder": 3,
        // ... other issue fields
      }
    ],
    "total": 4,
    "page": 1,
    "limit": 4,
    "totalPages": 1
  }
}
```

#### Business Rules

- **Position-Based Ordering**: Array index determines new displayOrder (0-indexed)
- **Tenant Scoped**: All issues must belong to current tenant
- **Atomic Update**: All display orders updated in single transaction
- **No Gaps**: Display order is sequential based on array position
- **Validation**: Returns 400 if any issue ID is invalid or not found

#### Validation Rules

- `issueIds`: Required, must have at least 1 item
- All issue IDs must exist and belong to current tenant
- Issue IDs must be valid identifiers

#### Error Responses

**400 Bad Request**
```json
{
  "success": false,
  "error": "At least one issue ID is required"
}
```

**400 Bad Request - Invalid Issue ID**
```json
{
  "success": false,
  "error": "Issue with ID 'issue_invalid' not found"
}
```

**404 Not Found**
```json
{
  "success": false,
  "error": "Issue with ID 'issue_123abc' not found"
}
```

---

## TypeScript Usage Examples

### List Issues with Filtering

```typescript
import axios from 'axios';

interface GetIssuesParams {
  page?: number;
  limit?: number;
  priority?: string;
  businessImpact?: string;
  assignedPersonId?: string;
  statusCategory?: string;
  tags?: string;
  sort?: string;
  order?: string;
}

async function listIssues(params: GetIssuesParams) {
  const response = await axios.get('/api/issues', {
    params,
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-Id': tenantId
    }
  });
  
  return response.data;
}

// Get critical and high priority issues assigned to specific user
const criticalIssues = await listIssues({
  priority: 'critical,high',           // OR logic
  assignedPersonId: 'user_dev123',
  statusCategory: 'open',
  sort: 'dueDate',
  order: 'asc'
});

// Get issues with specific tags
const taggedIssues = await listIssues({
  tags: 'bug,performance',
  businessImpact: 'high,critical',    // OR logic
  sort: 'priority',
  order: 'desc'
});
```

### Create Issue with Connections

```typescript
interface CreateIssuePayload {
  title: string;
  description?: string;
  businessImpact: 'low' | 'medium' | 'high' | 'critical';
  priority: 'low' | 'medium' | 'high' | 'critical';
  reportedBy: string;
  assignedPersonId?: string;
  dueDate?: string;
  estimatedHours?: number;
  tags?: string[];
  environment?: string;
  stepsToReproduce?: string;
  expectedBehavior?: string;
  actualBehavior?: string;
  connections?: {
    goalIds?: string[];
    strategyIds?: string[];
  };
}

async function createIssue(payload: CreateIssuePayload) {
  const response = await axios.post('/api/issues', payload, {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-Id': tenantId
    }
  });
  
  return response.data;
}

// Create bug with connections
const newIssue = await createIssue({
  title: 'Login page crashes on Safari',
  description: 'Users on Safari 17+ experience crash when clicking login button',
  businessImpact: 'high',
  priority: 'critical',
  reportedBy: 'user_support123',
  assignedPersonId: 'user_frontend456',
  dueDate: '2025-01-25',
  estimatedHours: 8,
  tags: ['bug', 'frontend', 'safari', 'login'],
  environment: 'Production - Safari 17.2 on macOS Sonoma',
  stepsToReproduce: '1. Open login page in Safari\n2. Enter credentials\n3. Click login button',
  expectedBehavior: 'User is logged in and redirected to dashboard',
  actualBehavior: 'Browser tab crashes immediately',
  connections: {
    goalIds: ['goal_stability_2025'],
    strategyIds: ['strat_browser_compatibility']
  }
});
```

### Issue Lifecycle Management

```typescript
// Start working on issue
async function startIssue(issueId: string, notes?: string) {
  const response = await axios.put(
    `/api/issues/${issueId}/start`,
    { notes },
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-Id': tenantId
      }
    }
  );
  
  return response.data;
}

// Resolve issue
async function resolveIssue(
  issueId: string,
  resolutionNotes: string,
  rootCauseAnalysis?: string,
  actualHours?: number
) {
  const response = await axios.put(
    `/api/issues/${issueId}/resolve`,
    {
      resolutionNotes,
      rootCauseAnalysis,
      actualHours
    },
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-Id': tenantId
      }
    }
  );
  
  return response.data;
}

// Workflow example
const issue = await createIssue({ /* ... */ });
await startIssue(issue.data.id, 'Beginning investigation');
// ... work on issue ...
await resolveIssue(
  issue.data.id,
  'Fixed by updating Safari-specific CSS transform',
  'Safari 17+ changed transform-origin behavior causing layout crash',
  6.5
);
```

### Convert Issue to Actions

```typescript
interface ActionToCreate {
  title: string;
  description?: string;
  assignedPersonId?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
}

async function convertIssueToActions(
  issueId: string,
  actions: ActionToCreate[],
  newStatusId?: string
) {
  const response = await axios.post(
    `/api/issues/${issueId}/convert-to-actions`,
    {
      actions,
      newStatusId
    },
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-Id': tenantId
      }
    }
  );
  
  return response.data;
}

// Convert complex issue into multiple actions
const conversionResult = await convertIssueToActions(
  'issue_complex123',
  [
    {
      title: 'Update Safari CSS transforms',
      description: 'Fix transform-origin issue in Safari 17+',
      assignedPersonId: 'user_css_expert',
      priority: 'critical'
    },
    {
      title: 'Add Safari 17+ compatibility tests',
      description: 'Prevent regression in future Safari versions',
      assignedPersonId: 'user_qa_lead',
      priority: 'high'
    },
    {
      title: 'Update browser compatibility documentation',
      description: 'Document Safari 17+ quirks',
      assignedPersonId: 'user_tech_writer',
      priority: 'medium'
    }
  ],
  'status_in_progress'  // Update issue to "In Progress" after conversion
);

console.log(`Created ${conversionResult.data.actionIds.length} actions from issue`);
```

### Tag Management

```typescript
// Add tags
async function addTags(issueId: string, tags: string[]) {
  const response = await axios.put(
    `/api/issues/${issueId}/tags`,
    { tags },
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-Id': tenantId
      }
    }
  );
  
  return response.data;
}

// Remove tags
async function removeTags(issueId: string, tags: string[]) {
  const response = await axios.delete(
    `/api/issues/${issueId}/tags`,
    {
      data: { tags },
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'X-Tenant-Id': tenantId
      }
    }
  );
  
  return response.data;
}

// Tag management workflow
await addTags('issue_abc123', ['urgent', 'customer-impact', 'production']);
await removeTags('issue_abc123', ['urgent']);  // Issue addressed
```

### Get Issue Statistics

```typescript
async function getIssueStats() {
  const response = await axios.get('/api/issues/stats', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'X-Tenant-Id': tenantId
    }
  });
  
  return response.data;
}

// Dashboard metrics
const stats = await getIssueStats();
console.log(`Total Issues: ${stats.data.totalIssues}`);
console.log(`Critical Issues: ${stats.data.criticalIssues}`);
console.log(`Resolution Rate: ${(stats.data.resolutionRate * 100).toFixed(1)}%`);
console.log(`Average Resolution Time: ${stats.data.timelineStats.averageResolutionTimeHours} hours`);
```

---

## Migration Notes from v6

### Configuration-Based Status & Types

**v6 (Simple Enums)**
```typescript
// Old approach used hardcoded status/type enums
status: 'open' | 'in_progress' | 'resolved' | 'closed'
type: 'bug' | 'feature' | 'task'
```

**v7 (Configuration-Based)**
```typescript
// New approach uses configurable status and type systems
statusConfigId: string;   // UUID referencing IssueStatusConfig
typeConfigId: string;     // UUID referencing IssueTypeConfig

// Each tenant can define custom statuses and types
// Status configs include: id, name, category, displayOrder, isDefault
// Type configs include: id, name, description, icon, color
```

**Migration Impact**: Frontend must fetch status/type configurations separately and use IDs in requests instead of hardcoded enum values.

### Lifecycle Endpoints

**v6**: Single `/status` endpoint for all status changes

**v7**: Dedicated endpoints for specific transitions
- `PUT /issues/{id}/start` - Start work
- `PUT /issues/{id}/resolve` - Mark resolved
- `PUT /issues/{id}/close` - Close issue
- `PUT /issues/{id}/reopen` - Reopen issue
- `PUT /issues/{id}/status` - Generic status change

**Migration Strategy**: Use specific lifecycle endpoints for better semantics and validation. Generic `/status` endpoint still available for custom workflows.

### Tag Management Optimization

**v6**: Single-tag add/remove operations

**v7**: Batch tag operations
- `PUT /issues/{id}/tags` with array - Add multiple tags atomically
- `DELETE /issues/{id}/tags` with array - Remove multiple tags atomically

**Migration Strategy**: Update frontend to send tag arrays instead of individual tags for better performance.

### Issue Conversion Feature

**New in v7**: `POST /issues/{issueId}/convert-to-actions`

Enables breaking down complex issues into actionable work items with automatic connection inheritance. Not available in v6.

---

## Related APIs

- **[Actions API](./actions-api.md)**: Created from issue conversion
- **[Goals API](./goals-api.md)**: Issue connections to goals
- **People API** (coming): Reporter and assignee details
- **Configuration API** (coming): IssueStatusConfig and IssueTypeConfig management

---

## Changelog

### v7.1 (January 4, 2026)
- **NEW**: Reorder issues endpoint (`PUT /issues:reorder`) for drag-and-drop sorting support
  - Updates `displayOrder` field based on array position
  - Supports atomic batch updates in single transaction
  - Similar pattern to issue-statuses:reorder endpoint

### v7.0 (December 23, 2025)
- **NEW**: Configuration-based status and types replacing hardcoded enums
- **NEW**: Dedicated lifecycle endpoints (start, resolve, close, reopen)
- **NEW**: Batch tag management (add/remove multiple tags atomically)
- **NEW**: Issue conversion to actions with inheritance
- **NEW**: Comprehensive filtering with comma-separated OR logic for priority/impact
- **NEW**: Issue statistics endpoint with type, impact, and timeline breakdowns
- **IMPROVED**: Bug-specific fields (environment, steps to reproduce, expected/actual behavior)
- **IMPROVED**: Root cause analysis and resolution notes tracking
- **CHANGED**: Status and type now use config IDs instead of enum strings

---

## TODO / Known Limitations

1. **Status Config Lookup**: Current implementation has placeholder for tenant default status config lookups (start, resolve, close, reopen endpoints)
2. **Relationship Endpoints**: Not yet implemented (coming soon):
   - `PUT /api/issues/{issueId}/goals`
   - `PUT /api/issues/{issueId}/strategies`
   - `PUT /api/issues/{issueId}/actions`
   - `DELETE /api/issues/{issueId}/relationships`
3. **Status Configuration Management**: Separate API needed for managing IssueStatusConfig and IssueTypeConfig entities
4. **Workflow Validation**: Status transition rules not yet enforced (e.g., can't resolve without being in-progress)

---

## Support

For questions or issues:
- **GitHub Issues**: [PurposePath Repository](https://github.com/purposepath/backend)
- **Slack**: #traction-service channel
- **Email**: backend-support@purposepath.com
