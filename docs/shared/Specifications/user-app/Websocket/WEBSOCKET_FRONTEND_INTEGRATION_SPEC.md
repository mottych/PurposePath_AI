# PurposePath WebSocket Integration Specification for Frontend

**Document Date:** November 3, 2025  
**Version:** 1.0  
**Audience:** Frontend Development Team (React/TypeScript)  
**Status:** Production Ready

---

## 📋 Table of Contents

1. [Message Envelope Format](#1-message-envelope-format)
2. [Field Naming Convention](#2-field-naming-convention)
3. [Event Types & Payloads](#3-event-types--payloads)
4. [System Events](#4-system-events)
5. [Connection & Authentication](#5-connection--authentication)
6. [Event History on Reconnect](#6-event-history-on-reconnect)
7. [Complete Examples](#7-complete-examples)

---

## 1. Message Envelope Format

All WebSocket messages from backend to frontend follow this **exact structure**:

```typescript
interface WebSocketMessage<T = any> {
  type: string;        // Event type identifier (e.g., "goal.created", "action.completed")
  timestamp: string;   // ISO 8601 UTC timestamp (e.g., "2025-11-03T14:30:00Z")
  data: T;            // Event-specific payload (structure varies by event type)
}
```

### Example Message:

```json
{
  "type": "goal.created",
  "timestamp": "2025-11-03T14:30:00.000Z",
  "data": {
    "goalId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "title": "Increase Revenue by 20%",
    "description": "Focus on enterprise customers",
    "status": "draft",
    "createdAt": "2025-11-03T14:30:00.000Z",
    "createdBy": "user-456"
  }
}
```

### Key Points:

- **`type`**: Always a string, always present, uses dot notation (e.g., `goal.created`, `measure.reading_created`)
- **`timestamp`**: Always ISO 8601 UTC format, millisecond precision
- **`data`**: Always an object (never null), structure depends on event type
- **No additional envelope fields**: No `version`, `id`, or `source` fields

---

## 2. Field Naming Convention

### ✅ ALL payloads use **camelCase** (NOT snake_case)

```typescript
// ✅ CORRECT (What you'll actually receive)
{
  "goalId": "123",
  "tenantId": "tenant-456",
  "userId": "user-789",
  "createdAt": "2025-11-03T14:30:00Z",
  "updatedBy": "user-111"
}

// ❌ WRONG (You will NOT see this format)
{
  "goal_id": "123",           // ❌ Never snake_case
  "tenant_id": "tenant-456",  // ❌ Never snake_case
  "user_id": "user-789"       // ❌ Never snake_case
}
```

### Field Name Examples:

| Entity | Field Names (camelCase) |
|--------|-------------------------|
| **IDs** | `goalId`, `kpiId`, `actionId`, `issueId`, `tenantId`, `userId` |
| **Timestamps** | `createdAt`, `updatedAt`, `deletedAt`, `completedAt`, `pausedAt` |
| **Actions** | `createdBy`, `updatedBy`, `deletedBy`, `completedBy`, `assignedTo` |
| **Nested** | `targetDate`, `targetValue`, `currentValue`, `dueDate`, `achievementRate` |

---

## 3. Event Types & Payloads

### 3.1 Goal Events (7 types)

#### `goal.created`

**When**: New goal is created via `POST /api/goals`

**Payload**:
```typescript
{
  goalId: string;              // UUID
  tenantId: string;            // Tenant identifier
  userId: string;              // Creator user ID
  title: string;               // Goal title
  description: string;         // Goal description (optional field, but always present - can be empty string)
  status: 'draft' | 'active' | 'completed' | 'paused' | 'archived';
  createdAt: string;           // ISO 8601
  createdBy: string;           // User ID who created
}
```

**Real Example**:
```json
{
  "type": "goal.created",
  "timestamp": "2025-11-03T14:30:00.000Z",
  "data": {
    "goalId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "title": "Increase Revenue by 20%",
    "description": "Focus on enterprise customers in Q4",
    "status": "draft",
    "createdAt": "2025-11-03T14:30:00.000Z",
    "createdBy": "user-456"
  }
}
```

---

#### `goal.activated`

**When**: Goal status changes from draft to active

**Payload**:
```typescript
{
  goalId: string;
  tenantId: string;
  previousStatus: string;      // e.g., "draft"
  newStatus: 'active';
  activatedAt: string;
  activatedBy: string;
}
```

**Real Example**:
```json
{
  "type": "goal.activated",
  "timestamp": "2025-11-03T16:00:00.000Z",
  "data": {
    "goalId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "previousStatus": "draft",
    "newStatus": "active",
    "activatedAt": "2025-11-03T16:00:00.000Z",
    "activatedBy": "user-456"
  }
}
```

---

#### `goal.completed`

**When**: Goal is marked as completed

**Payload**:
```typescript
{
  goalId: string;
  tenantId: string;
  completedAt: string;
  completedBy: string;
  finalNotes?: string;         // Optional
}
```

**Real Example**:
```json
{
  "type": "goal.completed",
  "timestamp": "2025-12-31T23:59:00.000Z",
  "data": {
    "goalId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "completedAt": "2025-12-31T23:59:00.000Z",
    "completedBy": "user-456",
    "finalNotes": "Exceeded target by 5.5%"
  }
}
```

---

#### `goal.cancelled`

**When**: Goal is cancelled/abandoned

**Payload**:
```typescript
{
  goalId: string;
  tenantId: string;
  cancelledAt: string;
  cancelledBy: string;
  reason?: string;             // Optional
}
```

---

#### `goal.activity.created`

**When**: Activity/note is added to a goal

**Payload**:
```typescript
{
  activityId: string;
  goalId: string;
  tenantId: string;
  type: 'note' | 'comment' | 'attachment' | 'decision' | 'review';
  title: string;
  content: string;
  tags?: string[];
  createdAt: string;
  createdBy: string;
}
```

**Real Example**:
```json
{
  "type": "goal.activity.created",
  "timestamp": "2025-11-03T17:00:00.000Z",
  "data": {
    "activityId": "activity-888",
    "goalId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "type": "note",
    "title": "Weekly Review Notes",
    "content": "Team reviewed progress, identified 3 blockers",
    "tags": ["weekly-review", "blockers"],
    "createdAt": "2025-11-03T17:00:00.000Z",
    "createdBy": "user-456"
  }
}
```

---

### 3.2 Action Events (6 types)

#### `action.created`

**When**: New action item created via `POST /api/operations/actions`

**Payload**:
```typescript
{
  actionId: string;
  tenantId: string;
  goalId: string;              // Parent goal
  title: string;
  description: string;
  assignedTo: string;          // User ID
  dueDate: string;             // ISO 8601 date
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'todo' | 'in_progress' | 'completed' | 'paused' | 'blocked';
  createdAt: string;
  createdBy: string;
}
```

**Real Example**:
```json
{
  "type": "action.created",
  "timestamp": "2025-11-03T11:00:00.000Z",
  "data": {
    "actionId": "action-555",
    "tenantId": "tenant-123",
    "goalId": "goal-222",
    "title": "Review Q4 Sales Pipeline",
    "description": "Analyze opportunities above $50k",
    "assignedTo": "user-789",
    "dueDate": "2025-11-05",
    "priority": "high",
    "status": "todo",
    "createdAt": "2025-11-03T11:00:00.000Z",
    "createdBy": "user-456"
  }
}
```

---

#### `action.status_changed`

**When**: Action status changes (todo → in_progress → completed)

**Payload**:
```typescript
{
  actionId: string;
  tenantId: string;
  previousStatus: string;
  newStatus: 'todo' | 'in_progress' | 'completed' | 'paused' | 'blocked';
  changedAt: string;
  changedBy: string;
}
```

---

#### `action.completed`

**When**: Action marked as complete

**Payload**:
```typescript
{
  actionId: string;
  tenantId: string;
  completedAt: string;
  completedBy: string;
  outcome?: string;            // Optional completion notes
  onTime: boolean;             // Was it completed by due date?
}
```

---

#### `action.priority_changed`

**When**: Action priority is modified

**Payload**:
```typescript
{
  actionId: string;
  tenantId: string;
  previousPriority: 'low' | 'medium' | 'high' | 'critical';
  newPriority: 'low' | 'medium' | 'high' | 'critical';
  changedAt: string;
  changedBy: string;
  reason?: string;
}
```

---

#### `action.reassigned`

**When**: Action assigned to different user

**Payload**:
```typescript
{
  actionId: string;
  tenantId: string;
  previousAssignee: string | null;
  newAssignee: string;
  assignedAt: string;
  assignedBy: string;
  note?: string;
}
```

---

#### `action.progress_updated`

**When**: Action progress percentage updated

**Payload**:
```typescript
{
  actionId: string;
  tenantId: string;
  previousProgress: number;    // 0-100
  newProgress: number;         // 0-100
  updatedAt: string;
  updatedBy: string;
}
```

---

### 3.3 Measure Events (3 types)

#### `measure.reading.created`

**When**: New Measure value recorded via `POST /api/measures/{id}/readings`

**Payload**:
```typescript
{
  readingId: string;
  kpiId: string;
  tenantId: string;
  value: number;               // The actual Measure value
  date: string;                // ISO 8601 date (e.g., "2025-11-03")
  note?: string;               // Optional note
  recordedAt: string;          // When recorded (ISO 8601)
  recordedBy: string;
  progress?: number;           // % toward target (0-100)
}
```

**Real Example**:
```json
{
  "type": "measure.reading.created",
  "timestamp": "2025-11-03T16:30:00.000Z",
  "data": {
    "readingId": "reading-333",
    "kpiId": "measure-111",
    "tenantId": "tenant-123",
    "value": 125000,
    "date": "2025-11-03",
    "note": "Q4 projection on track",
    "recordedAt": "2025-11-03T16:30:00.000Z",
    "recordedBy": "user-456",
    "progress": 25.0
  }
}
```

---

### 3.4 Issue Events (3 types)

#### `issue.created`

**When**: New issue created via `POST /api/operations/issues`

**Payload**:
```typescript
{
  issueId: string;
  tenantId: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: 'bug' | 'feature' | 'improvement' | 'question' | 'other';
  assignedTo?: string;
  createdAt: string;
  createdBy: string;
}
```

**Real Example**:
```json
{
  "type": "issue.created",
  "timestamp": "2025-11-03T13:00:00.000Z",
  "data": {
    "issueId": "issue-666",
    "tenantId": "tenant-123",
    "title": "Sales forecasting tool showing incorrect data",
    "description": "Q4 projections off by ~15%",
    "severity": "high",
    "status": "open",
    "priority": "urgent",
    "category": "bug",
    "assignedTo": "user-111",
    "createdAt": "2025-11-03T13:00:00.000Z",
    "createdBy": "user-456"
  }
}
```

---

#### `issue.status_changed`

**When**: Issue status updated

**Payload**:
```typescript
{
  issueId: string;
  tenantId: string;
  previousStatus: 'open' | 'in_progress' | 'resolved' | 'closed';
  newStatus: 'open' | 'in_progress' | 'resolved' | 'closed';
  changedAt: string;
  changedBy: string;
}
```

---

### 3.5 Other Events

#### `decision.created`

**When**: Strategic decision is documented

**Payload**:
```typescript
{
  decisionId: string;
  tenantId: string;
  goalId: string;
  title: string;
  decision: string;
  rationale: string;
  impact: string;
  decidedAt: string;
  decidedBy: string;
  participants: string[];      // Array of user IDs
}
```

---

#### `attachment.created`

**When**: File/attachment uploaded to entity

**Payload**:
```typescript
{
  attachmentId: string;
  tenantId: string;
  entityType: 'goal' | 'action' | 'issue';
  entityId: string;
  fileName: string;
  fileSize: number;            // Bytes
  fileType: string;            // MIME type
  uploadedAt: string;
  uploadedBy: string;
}
```

---

## 4. System Events

### 4.1 Ping/Pong (Keep-Alive)

**Backend does NOT send ping messages**. AWS API Gateway WebSocket handles connection keep-alive automatically.

**Client responsibility**: None required for keep-alive.

**What happens if client doesn't respond**: N/A - no ping/pong protocol implemented.

**Connection timeout**: Connections automatically close after **10 minutes of inactivity** (AWS API Gateway default).

**Recommendation**: Send a periodic message from client every 8-9 minutes if no user activity to keep connection alive:

```typescript
// Send keep-alive every 8 minutes
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: 'ping' }));
  }
}, 8 * 60 * 1000);
```

---

### 4.2 Error Events

#### Error Format:

```typescript
{
  type: string;                // Event type + ".error" suffix
  timestamp: string;
  data: {
    error: string;             // Human-readable error message
    code: string;              // Machine-readable error code
  }
}
```

#### Error Codes:

| Code | Description | HTTP Status | Client Action |
|------|-------------|-------------|---------------|
| `UNAUTHORIZED` | Invalid or expired token | 401 | Refresh token, reconnect |
| `FORBIDDEN` | User lacks permission | 403 | Show error, don't retry |
| `NOT_FOUND` | Resource doesn't exist | 404 | Remove from UI |
| `VALIDATION_ERROR` | Invalid request data | 422 | Show validation errors |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 | Backoff, retry after delay |
| `INTERNAL_ERROR` | Server-side error | 500 | Show error, retry |

#### Error Example - Unauthorized:

```json
{
  "type": "connection.error",
  "timestamp": "2025-11-03T14:35:00.000Z",
  "data": {
    "error": "Authentication token expired",
    "code": "UNAUTHORIZED"
  }
}
```

**Client action on UNAUTHORIZED**:
1. Close WebSocket connection
2. Refresh authentication token via `POST /auth/refresh`
3. Reconnect with new token

#### Error Example - Rate Limit:

```json
{
  "type": "broadcast.error",
  "timestamp": "2025-11-03T14:40:00.000Z",
  "data": {
    "error": "Too many requests, please slow down",
    "code": "RATE_LIMIT_EXCEEDED"
  }
}
```

**Client action on RATE_LIMIT_EXCEEDED**:
1. Implement exponential backoff
2. Wait 1s, 2s, 4s, 8s between retries
3. Show user-friendly message

---

## 5. Connection & Authentication

### 5.1 WebSocket URL Format

```
wss://api.{env}.purposepath.app/realtime
```

**Environments**:
- **Development**: `wss://api.dev.purposepath.app/realtime`
- **Staging**: `wss://api.staging.purposepath.app/realtime`
- **Production**: `wss://api.purposepath.app/realtime`

**❌ IMPORTANT**: Do NOT include query parameters in URL (no `?access_token=...` or `?tenant=...`)

### 5.2 Connection Flow

```typescript
// 1. Establish WebSocket connection
const ws = new WebSocket('wss://api.dev.purposepath.app/realtime');

// 2. Wait for connection to open
ws.onopen = () => {
  console.log('WebSocket connected');
  
  // 3. Send authentication message
  const token = localStorage.getItem('authToken');
  ws.send(JSON.stringify({
    action: 'auth',
    token: token
  }));
};

// 4. Receive authentication response
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === 'auth.success') {
    console.log('Authenticated successfully');
    // Connection is ready for events
  } else if (message.type === 'auth.error') {
    console.error('Authentication failed:', message.data.error);
    // Handle authentication failure
  }
};
```

### 5.3 Authentication Response

**Success**:
```json
{
  "type": "auth.success",
  "timestamp": "2025-11-03T14:30:00.000Z",
  "data": {
    "tenantId": "tenant-123",
    "userId": "user-456",
    "connectionId": "conn-abc123"
  }
}
```

**Failure**:
```json
{
  "type": "auth.error",
  "timestamp": "2025-11-03T14:30:00.000Z",
  "data": {
    "error": "Invalid authentication token",
    "code": "UNAUTHORIZED"
  }
}
```

### 5.4 Token Expiration

**What happens**:
1. Backend detects expired token
2. Sends `UNAUTHORIZED` error
3. Closes WebSocket connection

**Client should**:
1. Listen for `UNAUTHORIZED` error
2. Refresh auth token via `POST /auth/refresh`
3. Reconnect with new token

**Example**:
```typescript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.data?.code === 'UNAUTHORIZED') {
    // Token expired, refresh and reconnect
    refreshAuthToken().then(newToken => {
      localStorage.setItem('authToken', newToken);
      reconnect();
    });
  }
};
```

---

## 6. Event History on Reconnect

### 6.1 Current Behavior

**Backend does NOT support `lastEventId` for missed events.**

When client reconnects:
- ❌ No replay of missed events
- ❌ No event history buffer
- ✅ Client continues receiving NEW events from reconnection time forward

### 6.2 Client Recommendation

**Option 1: Optimistic UI + REST API Sync**
```typescript
ws.onopen = async () => {
  // After reconnect, fetch latest data via REST API
  await fetchLatestGoals();
  await fetchLatestActions();
  
  // Then continue with real-time updates
  console.log('Synced with latest data');
};
```

**Option 2: Track Last Sync Time**
```typescript
let lastSyncTime = new Date().toISOString();

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  lastSyncTime = message.timestamp;
  handleEvent(message);
};

ws.onopen = async () => {
  // Fetch events since last sync
  await fetchEventsSince(lastSyncTime);
};
```

**Option 3: Full Reload on Reconnect**
```typescript
ws.onopen = async () => {
  // Simple approach: reload entire page
  window.location.reload();
};
```

### 6.3 Future Enhancement (Roadmap)

Backend team is planning to add:
- Event buffer (last 100 events per tenant)
- `lastEventId` support for replay
- Event sequence numbers

**Not available yet** - use REST API sync for now.

---

## 7. Complete Examples

### Example 1: Goal Creation Flow

**User Action**: User clicks "Create Goal" button and submits form

**REST API Call**:
```http
POST /api/goals
Content-Type: application/json
Authorization: Bearer {token}
X-Tenant-Id: tenant-123

{
  "title": "Increase Revenue by 20%",
  "description": "Focus on enterprise customers"
}
```

**REST API Response** (immediate):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "tenant-123",
  "userId": "user-456",
  "title": "Increase Revenue by 20%",
  "description": "Focus on enterprise customers",
  "status": "draft",
  "createdAt": "2025-11-03T14:30:00.000Z",
  "createdBy": "user-456"
}
```

**WebSocket Event** (within 500ms):
```json
{
  "type": "goal.created",
  "timestamp": "2025-11-03T14:30:00.000Z",
  "data": {
    "goalId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "title": "Increase Revenue by 20%",
    "description": "Focus on enterprise customers",
    "status": "draft",
    "createdAt": "2025-11-03T14:30:00.000Z",
    "createdBy": "user-456"
  }
}
```

**Frontend Behavior**:
1. Optimistic UI update on REST response
2. WebSocket event received by **all connected clients** in same tenant
3. Other users see new goal appear in real-time
4. Creator sees confirmation (event validates optimistic update)

---

### Example 2: Action Status Change

**User Action**: User marks action as "In Progress"

**REST API Call**:
```http
PATCH /api/operations/actions/action-555
Content-Type: application/json
Authorization: Bearer {token}
X-Tenant-Id: tenant-123

{
  "status": "in_progress"
}
```

**WebSocket Event**:
```json
{
  "type": "action.status_changed",
  "timestamp": "2025-11-03T15:20:00.000Z",
  "data": {
    "actionId": "action-555",
    "tenantId": "tenant-123",
    "previousStatus": "todo",
    "newStatus": "in_progress",
    "changedAt": "2025-11-03T15:20:00.000Z",
    "changedBy": "user-789"
  }
}
```

**Frontend Behavior**:
1. Update action status badge
2. Move card to "In Progress" column (if Kanban board)
3. Show user avatar on action card
4. Notify assignee (if different from actor)

---

### Example 3: Measure Reading with Chart Update

**User Action**: User records new Measure value

**REST API Call**:
```http
POST /api/measures/measure-111/readings
Content-Type: application/json
Authorization: Bearer {token}
X-Tenant-Id: tenant-123

{
  "value": 125000,
  "date": "2025-11-03",
  "note": "Q4 projection on track"
}
```

**WebSocket Event**:
```json
{
  "type": "measure.reading.created",
  "timestamp": "2025-11-03T16:30:00.000Z",
  "data": {
    "readingId": "reading-333",
    "kpiId": "measure-111",
    "tenantId": "tenant-123",
    "value": 125000,
    "date": "2025-11-03",
    "note": "Q4 projection on track",
    "recordedAt": "2025-11-03T16:30:00.000Z",
    "recordedBy": "user-456",
    "progress": 25.0
  }
}
```

**Frontend Behavior**:
1. Add data point to chart (Chart.js/Recharts)
2. Update progress bar (25%)
3. Animate chart transition
4. Show notification: "Measure updated: 25% complete"

---

## 8. Integration Checklist

### ✅ Phase 1: Basic Connection

- [ ] Install TypeScript types
- [ ] Create WebSocket hook/service
- [ ] Implement connection management
- [ ] Add reconnection logic (exponential backoff)
- [ ] Show connection status indicator

### ✅ Phase 2: Authentication

- [ ] Send auth message on connect
- [ ] Handle auth success/failure
- [ ] Implement token refresh on expiration
- [ ] Test with expired tokens

### ✅ Phase 3: Event Handling

- [ ] Create event router/dispatcher
- [ ] Implement handlers for all event types
- [ ] Add type safety with TypeScript interfaces
- [ ] Test with real events from backend

### ✅ Phase 4: UI Updates

- [ ] Update goals list on `goal.*` events
- [ ] Update actions list on `action.*` events
- [ ] Update Measure charts on `measure.reading.created`
- [ ] Update issues board on `issue.*` events
- [ ] Show notifications for relevant events

### ✅ Phase 5: Error Handling

- [ ] Handle malformed messages
- [ ] Handle missing data fields
- [ ] Handle cross-tenant events (filter out)
- [ ] Show user-friendly error messages
- [ ] Implement retry logic

### ✅ Phase 6: Performance

- [ ] Debounce rapid updates (Measure readings)
- [ ] Batch UI updates
- [ ] Memoize event handlers
- [ ] Optimize re-renders with React.memo
- [ ] Monitor WebSocket message frequency

### ✅ Phase 7: Testing

- [ ] Unit tests for event handlers
- [ ] Integration tests with mock WebSocket
- [ ] E2E tests with real backend
- [ ] Test reconnection scenarios
- [ ] Test token expiration

---

## 9. TypeScript Types (Copy-Paste Ready)

```typescript
// src/types/websocket-events.ts

export interface WebSocketMessage<T = any> {
  type: string;
  timestamp: string;
  data: T;
}

export interface GoalCreatedEventData {
  goalId: string;
  tenantId: string;
  userId: string;
  title: string;
  description: string;
  status: 'draft' | 'active' | 'completed' | 'paused' | 'archived';
  createdAt: string;
  createdBy: string;
}

export interface GoalActivatedEventData {
  goalId: string;
  tenantId: string;
  previousStatus: string;
  newStatus: 'active';
  activatedAt: string;
  activatedBy: string;
}

export interface ActionCreatedEventData {
  actionId: string;
  tenantId: string;
  goalId: string;
  title: string;
  description: string;
  assignedTo: string;
  dueDate: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'todo' | 'in_progress' | 'completed' | 'paused' | 'blocked';
  createdAt: string;
  createdBy: string;
}

export interface MeasureReadingCreatedEventData {
  readingId: string;
  kpiId: string;
  tenantId: string;
  value: number;
  date: string;
  note?: string;
  recordedAt: string;
  recordedBy: string;
  progress?: number;
}

export interface IssueCreatedEventData {
  issueId: string;
  tenantId: string;
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  category: 'bug' | 'feature' | 'improvement' | 'question' | 'other';
  assignedTo?: string;
  createdAt: string;
  createdBy: string;
}

// ... Add remaining event types from section 3
```

---

## 10. Support & Resources

### Documentation

- **Complete Event Types**: `docs/websocket/event-types.md`
- **TypeScript Types**: `docs/websocket/typescript-types.md`
- **React Examples**: `docs/websocket/react-examples.md`
- **Frontend Integration Guide**: `docs/websocket/frontend-integration.md`
- **Troubleshooting**: `docs/websocket/WEBSOCKET_TROUBLESHOOTING.md`

### Testing

- **WebSocket Testing Tools**: `tools/testing/websocket/`
- **Test Framework**: `tools/testing/websocket/TEST_FRAMEWORK.md`
- **Quick Reference**: `tools/testing/websocket/QUICK_REFERENCE.md`

### Backend Team Contacts

- **Lead Engineer**: [Name]
- **DevOps**: [Name]
- **Slack Channel**: #purposepath-websocket

---

**Document Version:** 1.0  
**Last Updated:** November 3, 2025  
**Next Review:** December 3, 2025

