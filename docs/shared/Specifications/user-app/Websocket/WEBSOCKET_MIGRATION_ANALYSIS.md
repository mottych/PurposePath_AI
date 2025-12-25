# WebSocket Migration Analysis & Implementation Plan

**Date:** October 5, 2025  
**Project:** PurposePath_Web  
**Purpose:** Migrate from SSE to WebSocket-based real-time updates

---

## Executive Summary

The PurposePath frontend currently has **partial SSE (Server-Sent Events) infrastructure** in place (`src/services/realtime.ts`) that only supports **goal activity updates**. The backend is now implementing **WebSocket-based real-time updates** using AWS API Gateway WebSocket API. This document analyzes the existing implementation and provides a comprehensive migration and expansion plan.

### Key Findings

✅ **Existing Infrastructure:**
- SSE-based goal activity subscription (`subscribeToGoalActivity`)
- Feature flag support (`REACT_APP_FEATURE_REALTIME`)
- SSE base URL override (`REACT_APP_SSE_BASE_URL`)
- Event normalization logic for activities, decisions, attachments
- Mock SSE server for local testing

❌ **What's Missing:**
- **No WebSocket implementation** (only SSE with EventSource)
- **No global real-time connection manager**
- **No support for action, KPI, or issue events**
- **No reconnection logic** (EventSource auto-reconnects but limited control)
- **No connection state management**
- **No event handlers for most backend event types**
- **No integration with state management contexts**
- **No UI indicators for real-time connection status**

🎯 **Migration Strategy:**
- **Replace** `EventSource` with `WebSocket`
- **Expand** from goal-only to all entity types
- **Integrate** with existing Context API state management
- **Add** comprehensive reconnection and error handling
- **Preserve** existing feature flag and configuration patterns

---

## 1. Analysis: Existing Real-time Infrastructure

### 1.1 Current Implementation (`src/services/realtime.ts`)

**Features:**
- ✅ Feature flag check (`isRealtimeEnabled()`)
- ✅ SSE-based connection (`EventSource`)
- ✅ Goal activity subscription (`subscribeToGoalActivity`)
- ✅ Event normalization (activities, decisions, attachments)
- ✅ Token and tenant ID passing via query params
- ✅ Exponential backoff reconnection (via EventSource `onerror`)
- ✅ Status callbacks (`connecting`, `open`, `closed`, `error`, `reconnecting`)

**Limitations:**
- ❌ Only supports **goal activity** events (not actions, KPIs, issues)
- ❌ Uses **EventSource** (SSE) instead of WebSocket
- ❌ No support for tenant-wide subscriptions
- ❌ No ping/pong heartbeat handling
- ❌ No connection lifecycle management (singleton/shared connection)
- ❌ No integration with global state (Context API)
- ❌ Limited event type coverage

**Current Event Types Supported:**
```typescript
// Current (Goal Activity Only)
- activity.created
- decision.created
- attachment.created
- kpi.reading.created (mentioned but not in backend spec)
```

**Backend WebSocket Event Types (from spec):**
```typescript
// Goal Events
- goal.created
- goal.activated
- goal.completed
- goal.cancelled
- goal.activity.created

// Action Events
- action.created
- action.status_changed
- action.completed
- action.priority_changed
- action.reassigned
- action.progress_updated

// KPI Events
- kpi.reading.created

// Issue Events
- issue.created
- issue.status_changed

// Decision Events
- decision.created

// Attachment Events
- attachment.created

// System Events
- ping (respond with pong)
- error
```

### 1.2 State Management Architecture

**Pattern:** Context API (React Context)

**Existing Contexts:**
- `AuthContext` - User, tenant, tokens
- `FeaturesContext` - Feature flags (includes `realtime: boolean`)
- `LimitsContext` - Usage limits
- `SubscriptionContext` - Subscription tier and billing
- `PlanningContext` - Planning periods and time horizons

**Entity State Management:**
- ❌ **No global Goal context** (components load goals individually via `listGoals()`)
- ❌ **No global Action context** (loaded per component)
- ❌ **No global Issue context** (loaded per component)
- ❌ **No global KPI context** (loaded per component)
- ✅ Uses service layer for data fetching (`src/services/`)

**Current Pattern:**
```typescript
// Components load their own data
const [goals, setGoals] = useState<Goal[]>([]);

useEffect(() => {
  const loadData = async () => {
    const response = await listGoals();
    setGoals(response.data);
  };
  loadData();
}, []);
```

**Issue:** No centralized state means real-time updates need to be applied at each component level OR we need a global state solution.

### 1.3 Authentication Integration

**Token Storage:**
```typescript
// src/contexts/AuthContext.tsx
- accessToken: localStorage (via apiClient.setToken())
- refreshToken: localStorage (key: 'refreshToken')
- tenantId: localStorage (key: 'tenantId')
```

**Token Refresh:**
```typescript
// src/services/api.ts
- 401 interceptor calls /auth/refresh
- Sends { refresh_token } (snake_case)
- Updates tokens in localStorage
```

**Perfect for WebSocket:**
- ✅ Tokens are globally accessible
- ✅ Refresh mechanism already exists
- ✅ Tenant ID is stored and managed

### 1.4 Environment Configuration

**Existing Variables:**
```bash
# env.example
REACT_APP_FEATURE_REALTIME=false  # Feature flag
REACT_APP_SSE_BASE_URL=           # SSE URL override (for mock server)

# Service URLs
REACT_APP_ACCOUNT_API_URL=https://api.dev.purposepath.app/account/api/v1
REACT_APP_COACHING_API_URL=https://api.dev.purposepath.app/coaching/api/v1
REACT_APP_TRACTION_API_URL=https://api.dev.purposepath.app/traction/api/v1
```

**Needed for WebSocket:**
```bash
REACT_APP_REALTIME_WS_URL=wss://api.dev.purposepath.app/realtime
```

### 1.5 Dependencies Audit

**Current Dependencies:**
```json
// package.json
{
  "axios": "^1.6.2",           // HTTP client
  "sonner": "^1.2.4",          // Toast notifications
  "react-router-dom": "^6.8.1" // Routing
}
```

**WebSocket-related (dev dependencies only):**
- `faye-websocket` (via webpack dev server)
- `websocket-driver` (via webpack dev server)

**❌ Missing:**
- No `reconnecting-websocket` library
- No WebSocket client library for production
- No event emitter library (e.g., `mitt`, `eventemitter3`)

**Recommendation:**
- ✅ Use native `WebSocket` API (browser built-in)
- ✅ Implement custom reconnection logic (already exists in SSE version)
- ✅ Use React hooks for event handling (no extra library needed)

### 1.6 TypeScript Types

**Existing Types (`src/types/strategic-planning.ts`):**
```typescript
✅ Goal, GoalStatus, GoalKPI
✅ Action, ActionStatus, ActionPriority
✅ Issue, IssueStatus, IssueImpact
✅ SharedKPI, TimeHorizon, KPIReading
✅ Strategy, Decision
```

**Missing Types:**
- ❌ WebSocket message envelope types
- ❌ Real-time event payload types
- ❌ Connection state types
- ❌ Event handler types

---

## 2. Implementation Plan

### Phase 1: WebSocket Connection Manager (2-3 days)

**Goal:** Replace SSE with WebSocket and add proper connection management.

**Tasks:**

1. **Create WebSocket Connection Manager** (`src/services/realtime-websocket.ts`)
   - Replace `EventSource` with `WebSocket`
   - Implement connection lifecycle (connect, disconnect, reconnect)
   - Add exponential backoff with jitter
   - Add ping/pong heartbeat handling
   - Add connection state management
   - Add event emitter pattern for subscriptions

2. **Update Configuration**
   - Add `REACT_APP_REALTIME_WS_URL` to `env.example`
   - Add environment-specific WebSocket URLs
   - Keep `REACT_APP_FEATURE_REALTIME` flag

3. **Implement Token Refresh Integration**
   - Detect `UNAUTHORIZED` error from WebSocket
   - Trigger token refresh via `apiClient.refreshToken()`
   - Reconnect with new token

4. **Add TypeScript Types** (`src/types/realtime.ts`)
   - WebSocket message envelope
   - All event payload types
   - Connection state types
   - Event handler types

**Files to Create:**
- `src/services/realtime-websocket.ts` (new)
- `src/types/realtime.ts` (new)

**Files to Update:**
- `env.example` (add WebSocket URL)
- `src/services/realtime.ts` (deprecate or migrate)

**Acceptance Criteria:**
- ✅ WebSocket connects to backend
- ✅ Handles token expiration and reconnection
- ✅ Exponential backoff works
- ✅ Ping/pong heartbeat implemented
- ✅ Connection state updates correctly

---

### Phase 2: Event Handling System (2 days)

**Goal:** Implement handlers for all backend event types.

**Tasks:**

1. **Expand Event Types**
   - Add all backend event types (goals, actions, KPIs, issues, decisions, attachments)
   - Normalize event payloads (snake_case → camelCase)
   - Add event validation/parsing

2. **Create Event Handler Registry**
   - Allow components to subscribe to specific event types
   - Emit events to subscribers
   - Handle event cleanup on unmount

3. **Update Mock Server** (`scripts/mock-sse-server.js`)
   - Convert to WebSocket mock server
   - Add all event types
   - Support ping/pong

**Files to Create:**
- `scripts/mock-ws-server.js` (new)

**Files to Update:**
- `src/services/realtime-websocket.ts` (event handlers)
- `src/types/realtime.ts` (event types)

**Acceptance Criteria:**
- ✅ All event types supported
- ✅ Components can subscribe to events
- ✅ Event normalization works
- ✅ Mock server supports WebSocket

---

### Phase 3: State Integration (2-3 days)

**Goal:** Integrate real-time updates with application state.

**Options:**

#### Option A: Component-Level Integration (Lightweight)
- Each component subscribes to relevant events
- Updates local state on events
- No global state changes

**Pros:**
- ✅ Simple, minimal changes
- ✅ Follows existing patterns
- ✅ No breaking changes

**Cons:**
- ❌ Duplicate subscriptions
- ❌ No shared state
- ❌ Must handle optimistic updates per component

#### Option B: Global Context (Recommended)
- Create `RealtimeContext` for connection management
- Provide hooks: `useRealtimeGoals()`, `useRealtimeActions()`, etc.
- Centralize event handling and state updates

**Pros:**
- ✅ Single WebSocket connection
- ✅ Centralized event handling
- ✅ Easier to manage optimistic updates
- ✅ Better performance

**Cons:**
- ❌ More upfront work
- ❌ Requires refactoring components

**Recommendation:** **Option B (Global Context)**

**Tasks:**

1. **Create RealtimeContext** (`src/contexts/RealtimeContext.tsx`)
   - Manage WebSocket connection
   - Provide event subscription hooks
   - Provide connection status

2. **Create React Hooks**
   - `useRealtimeConnection()` - Connection state
   - `useRealtimeEvent(eventType, handler)` - Subscribe to events
   - `useGoalActivity(goalId)` - Goal-specific activity feed
   - `useRealtimeGoals()` - All goal events (optional)

3. **Integrate with Existing Components**
   - Update `GoalRoom` to use `useGoalActivity()`
   - Update dashboards to show real-time indicators
   - Add toast notifications for important events

**Files to Create:**
- `src/contexts/RealtimeContext.tsx` (new)
- `src/hooks/useRealtimeEvent.ts` (new)

**Files to Update:**
- `src/App.tsx` (add RealtimeProvider)
- `src/components/strategic-planning/GoalRoom.tsx` (use hooks)
- Dashboard components (add real-time indicators)

**Acceptance Criteria:**
- ✅ Single WebSocket connection shared across app
- ✅ Components can subscribe to events via hooks
- ✅ Goal activity updates in real-time
- ✅ Toast notifications show for important events

---

### Phase 4: UI Integration & Indicators (1-2 days)

**Goal:** Add visual feedback for real-time updates.

**Tasks:**

1. **Connection Status Indicator**
   - Add small indicator in app header/footer
   - Show: Connected, Disconnected, Reconnecting
   - Optional: click to see details

2. **Real-time Badges**
   - Add "Live" badge to updated items
   - Fade in/out animation for new items
   - Highlight updated rows/cards

3. **Toast Notifications**
   - Goal created/completed
   - High-priority actions created
   - Critical issues created
   - KPI thresholds breached (red zone)

4. **Activity Feed Live Updates**
   - Goal activity feed updates in real-time
   - Auto-scroll to new items (optional)
   - Show "New activity" indicator

**Files to Create:**
- `src/components/ui/RealtimeIndicator.tsx` (new)
- `src/components/ui/LiveBadge.tsx` (new)

**Files to Update:**
- `src/components/Layout.tsx` (add status indicator)
- `src/components/strategic-planning/GoalActivityFeed.tsx` (live updates)
- Dashboard widgets (live badges)

**Acceptance Criteria:**
- ✅ Connection status visible to user
- ✅ Updated items show live indicator
- ✅ Toast notifications work
- ✅ Activity feeds update in real-time

---

### Phase 5: Testing & Documentation (1-2 days)

**Goal:** Ensure quality and maintainability.

**Tasks:**

1. **Unit Tests**
   - WebSocket connection manager
   - Event normalization
   - Reconnection logic
   - Event handler registry

2. **Integration Tests**
   - Mock WebSocket for testing
   - Test event flow through contexts
   - Test UI updates

3. **Documentation**
   - Update `README.md` with WebSocket info
   - Create `docs/REALTIME_WEBSOCKET_IMPLEMENTATION.md`
   - Document environment variables
   - Document usage patterns

4. **Migration Guide**
   - Document SSE → WebSocket migration
   - Update integration guides

**Files to Create:**
- `src/services/__tests__/realtime-websocket.test.ts` (new)
- `docs/REALTIME_WEBSOCKET_IMPLEMENTATION.md` (new)

**Files to Update:**
- `README.md` (add WebSocket section)
- `docs/frontend-integration-guide.md` (update real-time section)

**Acceptance Criteria:**
- ✅ 80%+ test coverage for WebSocket code
- ✅ Documentation complete
- ✅ Migration guide available

---

## 3. Detailed Technical Specifications

### 3.1 WebSocket Connection Manager

```typescript
// src/services/realtime-websocket.ts

export type ConnectionStatus = 
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

export class RealtimeWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectDelay = 30000;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingTimer: NodeJS.Timeout | null = null;
  private eventHandlers = new Map<string, Set<Function>>();
  private status: ConnectionStatus = 'disconnected';
  private statusCallbacks = new Set<(status: ConnectionStatus) => void>();

  constructor(
    private getToken: () => string | null,
    private getTenantId: () => string | null,
    private onUnauthorized: () => Promise<void>
  ) {}

  connect() {
    const token = this.getToken();
    const tenantId = this.getTenantId();
    
    if (!token || !tenantId) {
      console.error('[Realtime] Missing token or tenantId');
      return;
    }

    const baseUrl = this.getWebSocketUrl();
    const url = `${baseUrl}?access_token=${token}&tenant=${tenantId}`;
    
    this.updateStatus('connecting');
    this.ws = new WebSocket(url);
    
    this.ws.onopen = () => this.handleOpen();
    this.ws.onmessage = (event) => this.handleMessage(event);
    this.ws.onerror = (error) => this.handleError(error);
    this.ws.onclose = () => this.handleClose();
  }

  private handleOpen() {
    console.log('[Realtime] Connected');
    this.reconnectAttempts = 0;
    this.updateStatus('connected');
    this.startPingTimer();
  }

  private handleMessage(event: MessageEvent) {
    try {
      const message = JSON.parse(event.data);
      
      // Handle ping
      if (message.type === 'ping') {
        this.sendPong();
        return;
      }
      
      // Handle error
      if (message.type === 'error') {
        this.handleServerError(message.data);
        return;
      }
      
      // Emit to subscribers
      this.emit(message.type, message.data);
    } catch (error) {
      console.error('[Realtime] Failed to parse message:', error);
    }
  }

  private handleError(error: Event) {
    console.error('[Realtime] WebSocket error:', error);
    this.updateStatus('error');
  }

  private handleClose() {
    console.log('[Realtime] Disconnected');
    this.stopPingTimer();
    this.updateStatus('disconnected');
    this.scheduleReconnect();
  }

  private async handleServerError(errorData: any) {
    if (errorData.code === 'UNAUTHORIZED') {
      console.log('[Realtime] Token expired, refreshing...');
      await this.onUnauthorized();
      this.reconnect();
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    
    const delay = Math.min(
      1000 * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );
    
    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++;
      this.reconnectTimer = null;
      this.updateStatus('reconnecting');
      this.connect();
    }, delay);
  }

  private sendPong() {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'pong',
        timestamp: new Date().toISOString()
      }));
    }
  }

  private startPingTimer() {
    this.pingTimer = setInterval(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) {
        this.stopPingTimer();
      }
    }, 30000);
  }

  private stopPingTimer() {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  on(eventType: string, handler: Function) {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)!.add(handler);
  }

  off(eventType: string, handler: Function) {
    this.eventHandlers.get(eventType)?.delete(handler);
  }

  private emit(eventType: string, data: any) {
    this.eventHandlers.get(eventType)?.forEach(handler => handler(data));
  }

  onStatusChange(callback: (status: ConnectionStatus) => void) {
    this.statusCallbacks.add(callback);
    return () => this.statusCallbacks.delete(callback);
  }

  private updateStatus(status: ConnectionStatus) {
    this.status = status;
    this.statusCallbacks.forEach(cb => cb(status));
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.stopPingTimer();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  reconnect() {
    this.disconnect();
    this.connect();
  }

  private getWebSocketUrl(): string {
    const override = process.env.REACT_APP_REALTIME_WS_URL?.trim();
    if (override) return override;
    
    const stage = process.env.REACT_APP_STAGE || 'dev';
    const envMap: Record<string, string> = {
      dev: 'wss://api.dev.purposepath.app/realtime',
      staging: 'wss://api.staging.purposepath.app/realtime',
      prod: 'wss://api.purposepath.app/realtime'
    };
    
    return envMap[stage] || envMap.dev;
  }
}
```

### 3.2 React Context Integration

```typescript
// src/contexts/RealtimeContext.tsx

import React, { createContext, useContext, useEffect, useState } from 'react';
import { RealtimeWebSocket } from '../services/realtime-websocket';
import { apiClient } from '../services/api';

interface RealtimeContextValue {
  connection: RealtimeWebSocket | null;
  status: ConnectionStatus;
  isEnabled: boolean;
}

const RealtimeContext = createContext<RealtimeContextValue | null>(null);

export const RealtimeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connection, setConnection] = useState<RealtimeWebSocket | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const isEnabled = useFeatures().realtime;

  useEffect(() => {
    if (!isEnabled) return;

    const ws = new RealtimeWebSocket(
      () => apiClient.getToken(),
      () => localStorage.getItem('tenantId'),
      async () => {
        await apiClient.refreshToken();
      }
    );

    ws.onStatusChange(setStatus);
    ws.connect();
    setConnection(ws);

    return () => {
      ws.disconnect();
    };
  }, [isEnabled]);

  return (
    <RealtimeContext.Provider value={{ connection, status, isEnabled }}>
      {children}
    </RealtimeContext.Provider>
  );
};

export const useRealtime = () => {
  const context = useContext(RealtimeContext);
  if (!context) throw new Error('useRealtime must be within RealtimeProvider');
  return context;
};

export function useRealtimeEvent<T = any>(
  eventType: string,
  handler: (data: T) => void,
  enabled = true
) {
  const { connection } = useRealtime();

  useEffect(() => {
    if (!connection || !enabled) return;
    
    connection.on(eventType, handler);
    return () => connection.off(eventType, handler);
  }, [connection, eventType, handler, enabled]);
}
```

### 3.3 Usage Example

```typescript
// src/components/strategic-planning/GoalRoom.tsx

export const GoalRoom: React.FC<{ goalId: string }> = ({ goalId }) => {
  const [activities, setActivities] = useState<Activity[]>([]);

  // Subscribe to goal activity events
  useRealtimeEvent('goal.activity.created', (data) => {
    if (data.goalId === goalId) {
      setActivities(prev => [data.activity, ...prev]);
      toast.success('New activity added');
    }
  });

  // Subscribe to goal completion
  useRealtimeEvent('goal.completed', (data) => {
    if (data.goalId === goalId) {
      toast.success('Goal completed! 🎉');
    }
  });

  // ... rest of component
};
```

---

## 4. Migration Path: SSE → WebSocket

### Step-by-Step Migration

1. **Keep SSE as Fallback (Optional)**
   - If needed, keep `realtime.ts` for backward compatibility
   - Add WebSocket as primary, fallback to SSE if unavailable

2. **Gradual Rollout**
   - Phase 1: Deploy WebSocket backend
   - Phase 2: Deploy WebSocket frontend (with feature flag)
   - Phase 3: Enable for beta users
   - Phase 4: Enable for all users
   - Phase 5: Remove SSE code

3. **Deprecation Timeline**
   - Week 1-2: WebSocket implementation
   - Week 3: Testing with beta users
   - Week 4: Full rollout
   - Week 5+: Monitor and remove SSE

### Breaking Changes

❌ **None** - WebSocket is a drop-in replacement for SSE at the API level.

### Configuration Changes

```bash
# Old (SSE)
REACT_APP_SSE_BASE_URL=http://localhost:5055

# New (WebSocket)
REACT_APP_REALTIME_WS_URL=ws://localhost:5055
```

---

## 5. Risk Assessment & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| WebSocket connection fails | High | Low | Exponential backoff, graceful degradation |
| Token expiration mid-connection | Medium | Medium | Detect UNAUTHORIZED, refresh, reconnect |
| Duplicate events (race condition) | Low | Medium | Implement idempotency checks, de-dupe by ID |
| High message volume (performance) | Medium | Low | Throttle/debounce UI updates, batch processing |
| Browser compatibility | Low | Low | Use native WebSocket (supported in all modern browsers) |
| Mock server doesn't match backend | Medium | High | Keep mock server in sync with backend spec |

---

## 6. Testing Strategy

### Unit Tests

- ✅ WebSocket connection lifecycle
- ✅ Reconnection logic
- ✅ Event normalization
- ✅ Ping/pong handling
- ✅ Error handling

### Integration Tests

- ✅ Mock WebSocket server
- ✅ Context integration
- ✅ Component updates on events
- ✅ Toast notifications

### Manual Testing

- ✅ Connect/disconnect/reconnect flows
- ✅ Token expiration handling
- ✅ Multiple tabs (connection sharing)
- ✅ Network interruption recovery
- ✅ Cross-browser testing

---

## 7. Timeline & Effort Estimate

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Connection Manager | 2-3 days | Backend WebSocket API deployed |
| Phase 2: Event Handling | 2 days | Phase 1 |
| Phase 3: State Integration | 2-3 days | Phase 2 |
| Phase 4: UI Integration | 1-2 days | Phase 3 |
| Phase 5: Testing & Docs | 1-2 days | Phase 4 |
| **Total** | **8-12 days** | - |

---

## 8. Success Criteria

✅ **Functional:**
- WebSocket connection establishes on login
- Automatically reconnects on disconnect
- All event types handled correctly
- State updates in real-time
- Token expiration handled gracefully

✅ **Non-Functional:**
- < 1s reconnection time (average)
- < 100ms event-to-UI latency
- 95%+ uptime (excluding backend issues)
- No memory leaks
- Works in all modern browsers

✅ **User Experience:**
- Connection status visible
- Real-time updates feel instant
- Toast notifications for important events
- No duplicate/stale data

---

## 9. Recommended Next Steps

1. **Review this analysis** with backend team to confirm WebSocket spec alignment
2. **Approve migration approach** (Global Context vs. Component-Level)
3. **Create tasks** in project management tool
4. **Implement Phase 1** (Connection Manager)
5. **Deploy backend WebSocket API** (if not already done)
6. **Run parallel testing** with mock server
7. **Beta rollout** to select users
8. **Full deployment** with monitoring

---

## 10. Questions for Backend Team

1. **WebSocket URL format confirmed?**
   - `wss://api.{env}.purposepath.app/realtime?access_token={token}&tenant={tenantId}`

2. **Ping/pong frequency?**
   - How often does backend send `ping`?
   - Is `pong` response required or optional?

3. **Message envelope format confirmed?**
   ```json
   {
     "type": "event_type",
     "timestamp": "ISO8601",
     "data": { ... }
   }
   ```

4. **Error codes confirmed?**
   - `UNAUTHORIZED` → refresh token
   - `RATE_LIMIT_EXCEEDED` → backoff
   - `INTERNAL_ERROR` → log and continue

5. **Event payload structure confirmed?**
   - Are payloads snake_case or camelCase?
   - Do we need to normalize?

6. **Connection limit per tenant?**
   - Should we share one connection across tabs?
   - Or allow multiple connections?

7. **Event history on reconnect?**
   - Does backend support `lastEventId` for missed events?
   - Or do we just continue from current?

---

## Appendix A: File Structure

```
src/
  services/
    realtime-websocket.ts          # NEW: WebSocket connection manager
    realtime.ts                     # DEPRECATED: Old SSE implementation
    __tests__/
      realtime-websocket.test.ts   # NEW: Unit tests
      
  contexts/
    RealtimeContext.tsx             # NEW: Global realtime context
    
  hooks/
    useRealtimeEvent.ts             # NEW: Event subscription hook
    
  types/
    realtime.ts                     # NEW: WebSocket types
    
  components/
    ui/
      RealtimeIndicator.tsx         # NEW: Connection status indicator
      LiveBadge.tsx                 # NEW: Live update badge

scripts/
  mock-ws-server.js                 # NEW: Mock WebSocket server
  mock-sse-server.js                # DEPRECATED: Old SSE mock
  
docs/
  WEBSOCKET_MIGRATION_ANALYSIS.md  # THIS FILE
  REALTIME_WEBSOCKET_IMPLEMENTATION.md  # NEW: Implementation guide
```

---

## Appendix B: Environment Variables

```bash
# env.example

# ============================================================================
# REALTIME CONFIGURATION
# ============================================================================

# Enable Realtime (WebSocket) when backend is available
REACT_APP_FEATURE_REALTIME=false

# WebSocket URL (overrides default environment-based URL)
# Development: ws://localhost:5055 (mock server)
# Production: wss://api.{env}.purposepath.app/realtime
REACT_APP_REALTIME_WS_URL=

# DEPRECATED: Old SSE configuration (remove after migration)
# REACT_APP_SSE_BASE_URL=
```

---

**End of Analysis**
