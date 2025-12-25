# Common Patterns & Data Models

**Version:** 3.0  
**Purpose:** Shared patterns, authentication, error handling, and data models across all services

[← Back to Index](./index.md)

---

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

**Endpoints:**
- `POST /auth/register`
- `POST /auth/resend-confirmation`
- `POST /auth/login` (if `REACT_APP_FE_BASE_HEADER_LOGIN=true`)

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
   a. Call POST /auth/refresh with refreshToken
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
  | 'kpis'           // KPIs module access
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
  | 'kpis'           // Maximum number of KPIs
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
type ActionStatus = 'not_started' | 'in_progress' | 'completed' | 'blocked' | 'cancelled';
type ActionPriority = 'low' | 'medium' | 'high' | 'critical';
type IssueImpact = 'low' | 'medium' | 'high' | 'critical';
type IssueStatusCategory = 'open' | 'active' | 'inactive' | 'closed';
```

### Activity Types

```typescript
type ActivityType = 'weekly_review' | 'note' | 'system' | 'decision' | 'attachment';
```

### Coaching and Insights

```typescript
type InsightCategory = 'strategy' | 'operations' | 'finance' | 'marketing' | 'leadership';
type InsightPriority = 'low' | 'medium' | 'high' | 'critical';
type InsightStatus = 'pending' | 'in_progress' | 'completed';
```

### Onboarding

```typescript
type OnboardingSuggestionKind = 'niche' | 'ica' | 'valueProposition';
type OnboardingCoachingTopic = 'coreValues' | 'purpose' | 'vision';
type OnboardingStatus = 'Not started' | 'In progress' | 'Completed';
```

### KPI

```typescript
type KPIDirection = 'up' | 'down'; // up = higher is better, down = lower is better
```

### Subscription

```typescript
type SubscriptionFrequency = 'monthly' | 'yearly';
type SubscriptionStatus = string; // Dynamic, e.g., 'active', 'trialing', 'past_due', 'cancelled'

// Note: Use isActive boolean for access control, not status string
```

### Promo Codes

```typescript
type PromoDiscountType = 'percentage' | 'fixed';
type PromoDiscountDuration = 'once' | 'repeating' | 'forever';

interface PromoDiscount {
  type: PromoDiscountType;
  value: number; // Percentage (0-100) or fixed amount in cents
  duration: PromoDiscountDuration;
  durationInMonths?: number; // For 'repeating' duration
}
```

### Payment

```typescript
type PaymentIntentStatus = 
  | 'requires_payment_method'
  | 'requires_confirmation'
  | 'requires_action'
  | 'processing'
  | 'succeeded'
  | 'canceled';
```

### Email Confirmation

```typescript
type TokenStatus = 'valid' | 'used' | 'expired' | 'not_found';
```

### Reports

```typescript
type ReportFormat = 'pdf' | 'docx';
```

### Real-time Events

```typescript
type RealtimeEventType = 
  | 'activity.created'
  | 'decision.created'
  | 'attachment.created'
  | 'kpi.reading.created';
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
    limit: number;
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

## Frontend-Backend Data Mapping

The frontend uses camelCase while the backend uses snake_case. Mappings are handled in service layers:

### Common Mappings

| Backend (snake_case) | Frontend (camelCase) |
|---------------------|----------------------|
| `access_token` | `accessToken` |
| `refresh_token` | `refreshToken` |
| `user_id` | `userId` |
| `tenant_id` | `tenantId` |
| `first_name` | `firstName` |
| `last_name` | `lastName` |
| `avatar_url` | `avatarUrl` |
| `created_at` | `createdAt` |
| `updated_at` | `updatedAt` |
| `owner_id` | `ownerId` |
| `value_tags` | `valueTags` |
| `shared_kpi_id` | `sharedKpiId` |
| `threshold_pct` | `threshold` or `thresholdPct` |
| `business_impact` | `businessImpact` |
| `assigned_person_id` | `assignedPersonId` |
| `new_password` | `newPassword` |

### Mapping Functions

**User Profile Mapping** (`api.ts`):
```typescript
private mapBackendUserProfileToFrontend(backendUser: any): UserProfile {
  return {
    userId: backendUser.user_id,
    email: backendUser.email,
    firstName: backendUser.first_name,
    lastName: backendUser.last_name,
    avatarUrl: backendUser.avatar_url,
    createdAt: backendUser.created_at,
    updatedAt: backendUser.updated_at,
    status: backendUser.status,
    emailVerified: backendUser.email_verified,
    preferences: backendUser.preferences || {}
  };
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
// Cache key: hash of goal intent + strategies + KPIs
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
      `access_token=${token}&tenant=${tenantId}`;
    
    const eventSource = new EventSource(url);
    
    eventSource.addEventListener('activity.created', callback);
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

## Health Check Endpoints (Kubernetes Patterns)

### Overview

All services implement standard Kubernetes health check patterns for infrastructure monitoring, orchestration, and load balancing. These endpoints provide different levels of health information for various use cases.

### Service Availability

| Service | Base Route | Endpoints |
|---------|-----------|-----------|
| Account Service | `/health` | All 4 health check types |
| Traction Service | `/health` | All 4 health check types |

### Endpoints

#### 1. GET /health - Basic Health Check

**Purpose:** Lightweight availability check for load balancers and uptime monitoring

**Authentication:** None (public endpoint)

**Request:** No parameters

**Response:** `ApiResponse<HealthCheckResponse>` (200 OK)

```json
{
  "success": true,
  "data": {
    "status": "Healthy",
    "service": "PurposePath Account Lambda",
    "version": "1.0.0",
    "timestamp": "2025-10-17T12:00:00Z",
    "environment": "production"
  }
}
```

**Use Cases:**

- Load balancer health checks
- Basic uptime monitoring
- Service discovery verification
- Quick availability checks

**Check Frequency:** High (every 5-10 seconds)

---

#### 2. GET /health/detailed - Detailed Health Status

**Purpose:** Comprehensive health check with dependency status and diagnostics

**Authentication:** None (public endpoint)

**Request:** No parameters

**Response:** `ApiResponse<HealthCheckResponse>` (200 OK or 503 Service Unavailable)

**Success Response (200):**

```json
{
  "success": true,
  "data": {
    "status": "Healthy",
    "service": "PurposePath Traction Lambda",
    "version": "1.0.0",
    "timestamp": "2025-10-17T12:00:00Z",
    "environment": "production",
    "checks": [
      {
        "component": "API",
        "status": "Healthy",
        "description": "API is responsive"
      },
      {
        "component": "Application",
        "status": "Healthy",
        "description": "Application is running normally"
      },
      {
        "component": "Configuration",
        "status": "Healthy",
        "description": "Environment: production"
      }
    ]
  }
}
```

**Failure Response (503):**
```json
{
  "success": true,
  "data": {
    "status": "Unhealthy",
    "service": "PurposePath Account Lambda",
    "version": "1.0.0",
    "timestamp": "2025-10-17T12:00:00Z",
    "environment": "production",
    "checks": [
      {
        "component": "Application",
        "status": "Unhealthy",
        "description": "Database connection failed"
      }
    ]
  }
}
```

**Use Cases:**

- Monitoring dashboards (Datadog, New Relic, CloudWatch)
- Detailed service health debugging
- Dependency health tracking
- Root cause analysis during incidents

**Check Frequency:** Medium (every 30-60 seconds)

---

#### 3. GET /health/ready - Readiness Probe

**Purpose:** Kubernetes readiness probe - determines if pod should receive traffic

**Authentication:** None (public endpoint)

**Request:** No parameters

**Response:** 200 OK or 503 Service Unavailable

**Success Response (200):**

```json
{
  "success": true,
  "data": {
    "status": "Ready",
    "timestamp": "2025-10-17T12:00:00Z",
    "message": "Service is ready to accept requests"
  }
}
```

**Failure Response (503):**

```json
{
  "success": false,
  "error": "Service not ready"
}
```

**Kubernetes Behavior:**

- **200 response:** Pod added to service load balancer pool (receives traffic)
- **503 response:** Pod removed from load balancer pool (stops receiving traffic)
- **Does NOT restart pod** (unlike liveness probe)
- Pod stays running but excluded from traffic routing

**Use Cases:**

- Zero-downtime deployments
- Gradual rollouts and canary deployments
- Prevents traffic to initializing pods
- Warm-up period handling
- Database connection establishment
- Cache warming

**Check Frequency:** High (every 10 seconds)

**Example Kubernetes Configuration:**

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

---

#### 4. GET /health/live - Liveness Probe

**Purpose:** Kubernetes liveness probe - determines if pod should be restarted

**Authentication:** None (public endpoint)

**Request:** No parameters

**Response:** 200 OK (always successful unless service is completely unresponsive)

**Response (200):**

```json
{
  "success": true,
  "data": {
    "status": "Alive",
    "timestamp": "2025-10-17T12:00:00Z",
    "message": "Service is running"
  }
}
```

**Kubernetes Behavior:**

- **200 response:** Pod continues running normally
- **No response or timeout:** Kubernetes **restarts the pod**
- **More lenient than readiness** (higher thresholds)
- Used to detect deadlocks, memory leaks, or unrecoverable states

**Use Cases:**

- Automatic recovery from deadlocks
- Memory leak detection and recovery
- Thread hang detection
- Self-healing infrastructure
- Recovery from unrecoverable errors

**Check Frequency:** Low (every 30-60 seconds)

**Example Kubernetes Configuration:**

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 30
  timeoutSeconds: 10
  successThreshold: 1
  failureThreshold: 3
```

---

### Health Check Comparison Table

| Endpoint | Purpose | K8s Feature | Failure Behavior | Check Frequency | Authentication |
|----------|---------|-------------|------------------|-----------------|----------------|
| `/health` | Basic availability | Load Balancer | None (monitoring only) | High (5-10s) | None |
| `/health/detailed` | Diagnostics | Observability | None (monitoring only) | Medium (30-60s) | None |
| `/health/ready` | Traffic routing | Readiness Probe | Remove from LB pool | High (10s) | None |
| `/health/live` | Pod health | Liveness Probe | **Restart pod** | Low (30-60s) | None |

### Readiness vs Liveness

**Key Difference:**

```text
Readiness: "Can I send traffic to this pod?"
Liveness:  "Should I restart this pod?"
```

**Example Scenario:**

1. Pod starts → Readiness fails (503) → No traffic sent
2. Pod initializes → Readiness passes (200) → Traffic starts flowing
3. Pod runs fine → Both probes pass (200)
4. Database connection lost → Readiness fails (503) → Traffic stops, **pod stays running**
5. Database reconnects → Readiness passes (200) → Traffic resumes
6. Pod deadlocks → Liveness fails (no response) → **Kubernetes restarts pod**

### Monitoring Integration

#### Datadog Integration

```yaml
# datadog-agent.yaml
checks:
  - name: purposepath_health
    url: https://api.purposepath.app/health/detailed
    method: GET
    interval: 60
    alert_on_failure: true
```

#### New Relic Synthetic Monitor

```javascript
// New Relic Synthetic Script
const assert = require('assert');

$http.get('https://api.purposepath.app/health/detailed', function(err, response, body) {
  assert.equal(response.statusCode, 200, 'Expected 200 OK');
  const data = JSON.parse(body);
  assert.equal(data.data.status, 'Healthy', 'Service should be healthy');
  
  data.data.checks.forEach(check => {
    assert.equal(check.status, 'Healthy', `${check.component} should be healthy`);
  });
});
```

#### CloudWatch Alarms

```bash
# Create CloudWatch alarm for health check failures
aws cloudwatch put-metric-alarm \
  --alarm-name purposepath-account-unhealthy \
  --alarm-description "Alert when Account service is unhealthy" \
  --metric-name HealthCheckStatus \
  --namespace PurposePath/Services \
  --statistic Average \
  --period 60 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 3
```

### Frontend Integration Example

Frontend can use health checks for status pages or admin dashboards:

```typescript
// Status page component
async function checkServiceHealth() {
  try {
    const accountHealth = await fetch('/api/v1/health');
    const tractionHealth = await fetch('/api/v1/health');
    
    return {
      account: accountHealth.ok ? 'operational' : 'degraded',
      traction: tractionHealth.ok ? 'operational' : 'degraded'
    };
  } catch (error) {
    return {
      account: 'down',
      traction: 'down'
    };
  }
}

// Admin dashboard with detailed status
async function getDetailedServiceStatus() {
  const response = await fetch('/api/v1/health/detailed');
  const data = await response.json();
  
  return {
    status: data.data.status,
    version: data.data.version,
    checks: data.data.checks,
    timestamp: data.data.timestamp
  };
}
```

### Complete Kubernetes Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: purposepath-account
spec:
  replicas: 3
  selector:
    matchLabels:
      app: purposepath-account
  template:
    metadata:
      labels:
        app: purposepath-account
    spec:
      containers:
      - name: account-service
        image: purposepath/account:latest
        ports:
        - containerPort: 8080
        
        # Readiness probe - controls traffic routing
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        
        # Liveness probe - controls pod restart
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          successThreshold: 1
          failureThreshold: 3
        
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: purposepath-account
spec:
  selector:
    app: purposepath-account
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

### Best Practices

1. **Readiness Probe:**

   - Check all critical dependencies (database, cache, external APIs)
   - Return 503 if any critical dependency is unavailable
   - Use shorter timeouts and more frequent checks
   - Should recover automatically when dependencies recover

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
- [← Coaching Service](./coaching-service.md)
- [← Traction Service](./traction-service/README.md)
