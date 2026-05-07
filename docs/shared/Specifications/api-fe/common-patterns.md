# Common Patterns & Data Models

## Status

This document is a shared non-contract guide.

## Canonical Contract Sources

Concrete endpoint inventories, request/response schemas, examples, status codes, and health-check payloads live in the deployed runtime contracts:
- Account: `https://{api-host}/account/api/v1/openapi/v1.json`
- Admin: `https://{api-host}/admin/api/v1/openapi/v1.json`
- Integration: `https://{api-host}/integration/api/v1/openapi/v1.json`
- Traction: `https://{api-host}/traction/api/v1/openapi/v1.json`
- Async contracts: `https://{api-host}/admin/api/v1/contracts/asyncapi?lambda={scope}`

Retain this file for shared client patterns, lifecycle expectations, and data-model conventions that are not better represented in OpenAPI/AsyncAPI.

[← Back to Index](./index.md)

## Authentication and Headers

### Required Headers

All protected endpoints require these headers:

```http
Authorization: Bearer {accessToken}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

### Special Headers

#### X-Frontend-Base-Url
**Used by:** Account Service auth endpoints that trigger emails

**Value:** `window.location.origin`

**Applicable flows:** Registration, confirmation resend, and any login/verification flow where the backend must generate frontend-facing links. Use the runtime OpenAPI contract for the exact endpoint inventory.

**Purpose:** Backend includes this URL in email links for email verification, password reset, etc.

**Implementation:**
```typescript
// Automatically added by accountClient interceptor
if (/\/auth\/(register|resend-confirmation)/.test(url)) {
  config.headers['X-Frontend-Base-Url'] = window.location.origin;
}
```

---

## Token Management

### Storage

Tokens stored in `localStorage`:

| Key | Value | Purpose |
|-----|-------|---------|
| `accessToken` | JWT access token | Authentication for API requests |
| `refreshToken` | JWT refresh token | Obtain new access token |
| `tenantId` | Tenant/organization ID | Multi-tenant data isolation |

### Token Lifecycle

```
1. User logs in
   ↓
2. Receive accessToken (15min TTL), refreshToken (30d TTL)
   ↓
3. Store in localStorage
   ↓
4. Include in all API requests via Authorization header
   ↓
5. On 401 response:
  a. Call the account-service token refresh endpoint with `refreshToken`
   b. Receive new accessToken + refreshToken
   c. Update localStorage
   d. Retry original request
   ↓
6. If refresh fails: clear tokens, redirect to login
```

### Automatic Token Refresh

All service clients implement automatic token refresh on 401 responses:

**Account & Coaching Services** (`api.ts`):
```typescript
this.accountClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await this.refreshToken();
      // Retry original request
    }
    return Promise.reject(error);
  }
);
```

**Traction Service** (`traction.ts`):
```typescript
// Queue-based refresh to handle concurrent 401s
traction.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      if (isRefreshing) {
        // Queue request during refresh
        return new Promise((resolve, reject) => {
          pendingQueue.push({resolve, reject});
        }).then((token) => {
          error.config.headers.Authorization = `Bearer ${token}`;
          return traction.request(error.config);
        });
      }
      
      isRefreshing = true;
      error.config._retry = true;
      
      const ok = await apiClient.refreshToken();
      const token = apiClient.getToken();
      
      processQueue(null, token);
      
      if (ok && token) {
        error.config.headers.Authorization = `Bearer ${token}`;
        return traction.request(error.config);
      }
    }
    return Promise.reject(error);
  }
);
```

---

## Error Handling

### Standard Error Response

All services return consistent error format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {}  // Optional: Additional context for the error
}
```

**Field Descriptions:**
- `success`: Always `false` for error responses
- `error`: Human-readable message describing what went wrong
- `code`: Machine-readable error code (see Common Error Codes table)
- `details`: Optional object with additional error context (field names, validation errors, resource IDs, etc.)

**Examples:**

Validation error:
```json
{
  "success": false,
  "error": "Email is required",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "email"
  }
}
```

Multiple validation errors:
```json
{
  "success": false,
  "error": "Validation failed for multiple fields",
  "code": "VALIDATION_ERROR",
  "details": {
    "errors": [
      {"field": "email", "message": "Email is required"},
      {"field": "password", "message": "Password must be at least 8 characters"}
    ]
  }
}
```

Resource not found:
```json
{
  "success": false,
  "error": "User not found",
  "code": "RESOURCE_NOT_FOUND",
  "details": {
    "resourceType": "User",
    "resourceId": "user_123"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description | Usage |
|------|-------------|-------------|-------|
| `VALIDATION_ERROR` | 400, 422 | Input validation failed | Field validation, format errors |
| `UNAUTHORIZED` | 401 | Authentication required | Missing/invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions | User lacks required access |
| `RESOURCE_NOT_FOUND` | 404 | Resource does not exist | Invalid ID, deleted resource |
| `DUPLICATE_RESOURCE` | 409 | Resource already exists | Unique constraint violation |
| `BUSINESS_RULE_VIOLATION` | 400 | Business logic violation | Invalid operation per domain rules |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected error | Server-side errors |

### HTTP Status Codes

| Code | Meaning | Frontend Action |
|------|---------|----------------|
| 200 | Success | Process response (check `success` field) |
| 401 | Unauthorized | Trigger token refresh, retry request |
| 403 | Forbidden | Show "Access Denied" message |
| 404 | Not Found | Handle missing resource |
| 422 | Validation Error | Show field-specific errors |
| 500 | Server Error | Show error message, enable retry |

### Frontend Error Handling Patterns

#### Generic Error Handler
```typescript
try {
  const response = await apiCall();
  if (!response.success) {
    showError(response.error);
    return;
  }
  // Process response.data
} catch (error: any) {
  if (error.response?.status === 401) {
    // Handled by interceptor
  } else if (error.response?.status === 403) {
    showError("You don't have permission to perform this action");
  } else {
    showError(error.response?.data?.error || "An error occurred");
  }
}
```

#### Validation Error Display
```typescript
if (error.response?.status === 422) {
  const validationErrors = error.response.data.errors;
  // Display field-specific errors
  Object.keys(validationErrors).forEach(field => {
    setFieldError(field, validationErrors[field]);
  });
}
```

#### Retry Logic
```typescript
async function apiCallWithRetry(maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiCall();
    } catch (error: any) {
      if (i === maxRetries - 1) throw error;
      if (error.response?.status === 500) {
        await delay(Math.pow(2, i) * 1000); // Exponential backoff
        continue;
      }
      throw error;
    }
  }
}
```

---

## Data Models and Enumerations

### Subscription Features

**Feature Names** (for `/user/features` and tier `features` arrays):

```typescript
type FeatureName = 
  | 'goals'           // Goals module access
  | 'operations'      // Operations module access
  | 'measures'           // Measures module access
  | 'strategies'      // Strategic planning module access
  | 'reports'         // Report generation capability
  | 'realtime'        // Real-time updates via SSE
  | 'attachments'     // File attachment features
  | 'bulkPlanner'     // Bulk planning operations
  | 'strategyCompare' // Strategy comparison tools
  | 'goalCreate';     // Goal creation permissions
```

### Subscription Limits

**Limit Keys** (for `/user/limits` and tier `limits` objects):

```typescript
type LimitName = 
  | 'goals'           // Maximum number of goals
  | 'measures'           // Maximum number of Measures
  | 'actions'        // Maximum number of actions
  | 'strategies'     // Maximum number of strategies
  | 'attachments'    // Maximum number of attachments per goal
  | 'reports';       // Maximum number of reports per month

// Limit values: number (max count) | null (unlimited)
```

### Goal and Strategy Status

```typescript
type GoalStatus = 'draft' | 'active' | 'completed' | 'paused' | 'cancelled';
type StrategyStatus = 'draft' | 'validated' | 'adopted';
type TimeHorizon = 'year' | 'quarter' | 'month';
```

### Operations Status and Priority

```typescript
type ActionStatus = 'notStarted' | 'inProgress' | 'completed' | 'blocked' | 'cancelled';
type ActionPriority = 'low' | 'medium' | 'high' | 'critical';
type IssueImpact = 'low' | 'medium' | 'high' | 'critical';
type IssueStatusCategory = 'open' | 'active' | 'inactive' | 'closed';
```

### Activity Types

```typescript
type ActivityType = 'weeklyReview' | 'note' | 'system' | 'decision' | 'attachment';
```

### Coaching and Insights

```typescript
type InsightCategory = 'strategy' | 'operations' | 'finance' | 'marketing' | 'leadership';
type InsightPriority = 'low' | 'medium' | 'high' | 'critical';
type InsightStatus = 'pending' | 'inProgress' | 'completed';
```

### Onboarding

```typescript
type OnboardingSuggestionKind = 'niche' | 'ica' | 'valueProposition';
type OnboardingCoachingTopic = 'coreValues' | 'purpose' | 'vision';
type OnboardingStatus = 'notStarted' | 'inProgress' | 'completed';
```

### Measure

```typescript
type MeasureDirection = 'up' | 'down'; // up = higher is better, down = lower is better
```

### Subscription

```typescript
type SubscriptionFrequency = 'monthly' | 'yearly';
type SubscriptionStatus = string; // Dynamic, e.g., 'active', 'trialing', 'pastDue', 'cancelled'

// Note: Use isActive boolean for access control, not status string
```

### Billing Discounts

Use canonical billing endpoints under `/billing/*` for discount preview/application contract details.

```typescript
type BillingPriceAdjustmentType = 'percent' | 'amount' | 'override';

interface BillingDiscountLine {
  adjustmentType: BillingPriceAdjustmentType;
  percentOff?: number; // Required when adjustmentType = 'percent' (0-100)
  amountOff?: { amount: number; currency: string }; // Required when adjustmentType = 'amount'
  overridePrice?: { amount: number; currency: string }; // Required when adjustmentType = 'override'
}
```

### Payment

```typescript
type PaymentIntentStatus = 
  | 'requiresPaymentMethod'
  | 'requiresConfirmation'
  | 'requiresAction'
  | 'processing'
  | 'succeeded'
  | 'canceled';
```

### Email Confirmation

```typescript
type TokenStatus = 'valid' | 'used' | 'expired' | 'notFound';
```

### Reports

```typescript
type ReportFormat = 'pdf' | 'docx';
```

### Real-time Events

```typescript
type RealtimeEventType = 
  | 'activityCreated'
  | 'decisionCreated'
  | 'attachmentCreated'
  | 'measureReadingCreated';
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Service Base URLs
REACT_APP_ACCOUNT_API_URL=https://api.dev.purposepath.app/account/api/v1
REACT_APP_COACHING_API_URL=https://api.dev.purposepath.app/coaching/api/v1
REACT_APP_TRACTION_API_URL=https://api.dev.purposepath.app/traction/api/v1

# Feature Flags
REACT_APP_MOCK_MODE=false               # Global mock mode toggle
REACT_APP_MOCK_ACCOUNT=false            # Mock Account Service only
REACT_APP_MOCK_COACHING=false           # Mock Coaching Service only
REACT_APP_MOCK_TRACTION=false           # Mock Traction Service only
REACT_APP_FEATURE_REALTIME=true         # Enable real-time SSE features

# SSE Configuration
REACT_APP_SSE_BASE_URL=https://api.dev.purposepath.app/traction/api/v1

# Optional Features
REACT_APP_FE_BASE_HEADER_LOGIN=false    # Add X-Frontend-Base-Url to login requests
```

### Environment-Specific URLs

| Environment | Base URL |
|-------------|----------|
| Development | `https://api.dev.purposepath.app` |
| Staging | `https://api.staging.purposepath.app` |
| Production | `https://api.purposepath.app` |

### Mock Mode Behavior

When service-specific mock flags are enabled:
- API calls return realistic mock data
- No network requests made to backend
- Suitable for development and offline testing
- Each service can be mocked independently

**Example:**
```bash
REACT_APP_MOCK_ACCOUNT=false  # Real Account API
REACT_APP_MOCK_COACHING=true  # Mock Coaching API
REACT_APP_MOCK_TRACTION=false # Real Traction API
```

---

## API Response Patterns

### Success Response

```typescript
interface ApiResponse<T> {
  success: true;
  data: T;
}
```

### Paginated Response

```typescript
interface PaginatedResponse<T> {
  success: true;
  data: T[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
}
```

### Error Response

```typescript
interface ErrorResponse {
  success: false;
  error: string;
  code?: string;
  errors?: Record<string, string>; // Field-specific validation errors
}
```

---

## Data Models

### Standard Field Naming

All API responses use **camelCase** for JSON property names:

**Common Fields:**
- `accessToken`, `refreshToken` - Authentication tokens
- `userId`, `tenantId` - Entity identifiers
- `firstName`, `lastName` - User name fields
- `avatarUrl` - User profile picture URL
- `createdAt`, `updatedAt` - Timestamps
- `ownerId` - Resource owner identifier
- `valueTags` - Array of value identifiers
- `sharedMeasureId` - Shared Measure identifier
- `thresholdPct` - Percentage threshold value
- `businessImpact` - Business impact description
- `assignedPersonId` - Person assignment identifier
- `newPassword` - New password for updates

### TypeScript Model Example

**User Profile** (`api.ts`):
```typescript
interface UserProfile {
  userId: string;
  email: string;
  firstName: string;
  lastName: string;
  avatarUrl?: string;
  createdAt: string;
  updatedAt: string;
  status: string;
  emailVerified: boolean;
  preferences: Record<string, any>;
}
```

---

## Caching Strategy

### Client-Side Caching

**Goals Cache** (`goal-service.ts`):
```typescript
class GoalCache {
  private goalListCache: Goal[] | null = null;
  private goalCache: Map<string, Goal> = new Map();
  
  invalidateAll(): void {
    this.goalListCache = null;
    this.goalCache.clear();
    this.notifyInvalidation();
  }
}
```

**Alignment Cache** (`alignment-cache-service.ts`):
```typescript
// Caches alignment calculations to reduce API calls
// Cache key: hash of goal intent + strategies + Measures
// TTL: 5 minutes
```

**When to Invalidate:**
- After create/update/delete operations
- On user-triggered refresh
- After certain time periods (TTL)

---

## Optimistic Updates

Frontend implements optimistic updates for better UX:

**Pattern** (`optimistic-updates.ts`):
```typescript
async function updateWithOptimism(
  optimisticUpdate: () => void,
  apiCall: () => Promise<any>,
  rollback: () => void
) {
  optimisticUpdate(); // Update UI immediately
  
  try {
    await apiCall(); // Make API call
  } catch (error) {
    rollback(); // Revert on failure
    showError(error);
  }
}
```

**Example:**
```typescript
// Update goal status immediately
setGoalStatus(goalId, 'completed');

try {
  await goalService.closeGoal(goalId, {finalStatus: 'completed'});
} catch (error) {
  // Revert to previous status
  setGoalStatus(goalId, previousStatus);
  showError('Failed to close goal');
}
```

---

## Real-Time Connection Management

**SSE Connection** (`realtime.ts`):
```typescript
class RealtimeService {
  private connections: Map<string, EventSource> = new Map();
  
  subscribe(goalId: string, callback: (event) => void) {
    const url = `${SSE_BASE_URL}/realtime/goals/${goalId}/activity?` +
      `accessToken=${token}&tenantId=${tenantId}`;
    
    const eventSource = new EventSource(url);
    
    eventSource.addEventListener('activityCreated', callback);
    eventSource.addEventListener('error', () => {
      // Auto-reconnect with exponential backoff
      this.reconnect(goalId, callback);
    });
    
    this.connections.set(goalId, eventSource);
  }
  
  unsubscribe(goalId: string) {
    const connection = this.connections.get(goalId);
    if (connection) {
      connection.close();
      this.connections.delete(goalId);
    }
  }
}
```

**Connection Features:**
- Auto-reconnect on disconnect
- Exponential backoff for reconnection attempts
- Event deduplication using `lastEventId`
- Graceful fallback to polling if SSE unavailable

---

## Performance Considerations

### Request Batching

Batch-related entity queries:
```typescript
// Instead of N requests
for (const actionId of actionIds) {
  await getActionGoals(actionId);
}

// Make 1 request
const goalsMap = await getActionGoalRelationships({actionIds});
```

### Debouncing

Debounce expensive operations:
```typescript
const debouncedAlignment = debounce(async () => {
  await calculateAlignment(goal);
}, 1000); // Wait 1s after last change
```

### Lazy Loading

Load data on-demand:
```typescript
// Load goals list immediately
const goals = await getGoals();

// Load full goal details only when opened
const goalDetails = await getGoalById(selectedGoalId);
```

---

## Health Check Patterns

Health checks remain part of the runtime API surface, but the concrete routes, payloads, and status codes belong in the deployed OpenAPI contracts rather than this shared guide.

### Retained Semantic Guidance

- Basic health checks support lightweight availability monitoring.
- Detailed health checks are for diagnostics and dependency visibility.
- Readiness determines whether traffic should be routed to a pod.
- Liveness determines whether orchestration should restart a pod.

### Readiness vs Liveness

```text
Readiness: "Can I send traffic to this pod?"
Liveness:  "Should I restart this pod?"
```

Typical lifecycle:

1. A pod starts and fails readiness until initialization completes.
2. Traffic begins only after readiness succeeds.
3. A transient dependency failure should normally remove the pod from traffic without forcing restart.
4. A deadlock or unrecoverable runtime hang should eventually fail liveness and trigger restart.

### Operational Guidance

- Keep readiness probes stricter than liveness probes.
- Use detailed health checks for observability dashboards and incident triage.
- Treat readiness failures as traffic-routing events first, not automatic restart signals.
- Treat liveness failures as recovery signals for deadlock or unrecoverable process states.
- Validate concrete health payloads and paths against the runtime OpenAPI endpoints for the affected service before rollout or monitoring changes.

2. **Liveness Probe:**

   - Keep checks simple and fast
   - Only fail for unrecoverable errors (deadlocks, memory exhaustion)
   - Use longer timeouts and less frequent checks
   - Avoid checking external dependencies (use readiness for that)

3. **Detailed Health:**

   - Include all dependency statuses
   - Add latency metrics
   - Include version information
   - Log failures for debugging

4. **Basic Health:**

   - Keep extremely lightweight
   - Return quickly
   - Minimal dependencies
   - Suitable for high-frequency polling

---

## Security Best Practices

1. **Never log sensitive data:**

   ```typescript
   // Bad
   console.log('Token:', accessToken);
   
   // Good
   console.log('Token:', accessToken.slice(0, 10) + '...');
   ```

2. **Validate on both client and server:**

   - Client validation for UX
   - Server validation for security

3. **Handle token expiration gracefully:**

   - Auto-refresh on 401
   - Clear tokens and redirect on refresh failure

4. **Use HTTPS in production:**

   - All API endpoints must use HTTPS
   - No mixed content

5. **Sanitize user input:**

   - Especially in rich text editors
   - Prevent XSS attacks

---

**Navigation:**

- [← Back to Index](./index.md)
- [← Account Service](./account-service.md)
- [← AI/Coaching Service](../ai-user/backend-integration-unified-ai.md)
- [← Traction Service](./index.md)
