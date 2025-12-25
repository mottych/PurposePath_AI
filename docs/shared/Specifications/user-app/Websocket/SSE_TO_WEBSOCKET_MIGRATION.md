# SSE to WebSocket Migration Guide

**Status:** Migration Complete  
**Date:** November 2025

## Overview

This guide documents the migration from Server-Sent Events (SSE) to WebSocket for real-time updates in PurposePath.

---

## Migration Summary

| Aspect | SSE (Old) | WebSocket (New) |
|--------|-----------|-----------------|
| **Connection** | Unidirectional (server → client) | Bidirectional |
| **Protocol** | HTTP | WS/WSS |
| **Authentication** | Header-based | Post-connection message |
| **Reconnection** | Automatic by browser | Custom with exponential backoff |
| **Keep-alive** | Server-sent comments | Client ping every 8 min |
| **Event Format** | Text-based SSE | JSON WebSocket messages |
| **Connection Sharing** | One per tab | Shared across app |

---

## What Changed

### 1. Connection Management

**Old (SSE):**
```typescript
// Multiple EventSource connections
const eventSource = new EventSource('/api/events');
event Source.addEventListener('message', handler);
```

**New (WebSocket):**
```typescript
// Single WebSocket connection managed by RealtimeContext
import { useRealtimeEvent } from '../hooks/realtime';

useRealtimeEvent({
  eventType: 'goal.created',
  onEvent: (message) => { /* handler */ }
});
```

### 2. Authentication

**Old (SSE):**
- Token passed in URL query parameter
- Authentication on connection

**New (WebSocket):**
- Token sent in post-connection auth message
- Server validates and responds with `auth.success` or `auth.error`

### 3. Event Structure

**Old (SSE):**
```
event: goal-created
data: {"id": "123", "title": "New Goal"}
```

**New (WebSocket):**
```json
{
  "type": "goal.created",
  "data": {
    "goalId": "123",
    "title": "New Goal",
    "tenantId": "tenant-1",
    "createdAt": "2025-11-03T12:00:00Z"
  },
  "timestamp": "2025-11-03T12:00:00Z",
  "eventId": "evt_abc123",
  "tenantId": "tenant-1"
}
```

### 4. Event Naming

| SSE Event | WebSocket Event |
|-----------|-----------------|
| `goal-created` | `goal.created` |
| `goal-updated` | Multiple specific events (`goal.activated`, `goal.completed`, etc.) |
| `action-created` | `action.created` |
| `issue-created` | `issue.created` |

### 5. React Integration

**Old (SSE):**
```typescript
// Manual subscription management
useEffect(() => {
  const es = new EventSource('/api/events');
  es.addEventListener('goal-created', handler);
  return () => es.close();
}, []);
```

**New (WebSocket):**
```typescript
// Automatic subscription cleanup
useRealtimeEvent({
  eventType: 'goal.created',
  onEvent: handler
});
```

---

## Breaking Changes

### 1. Event Type Names

**Impact:** Code that references event types

**Action Required:**
- Replace hyphenated event names with dot notation
- Update event type strings in code
- Use `EventTypes` constants from `types/realtime.ts`

**Example:**
```typescript
// ❌ Old
eventSource.addEventListener('goal-created', handler);

// ✅ New
useRealtimeEvent({
  eventType: 'goal.created',  // or EventTypes.GOAL_CREATED
  onEvent: handler
});
```

### 2. Event Data Structure

**Impact:** Code that accesses event data properties

**Action Required:**
- Update property access to use new structure
- All fields are camelCase
- Wrapped in `message.data`

**Example:**
```typescript
// ❌ Old
function handler(event) {
  const goalId = event.data.goal_id;
}

// ✅ New
function handler(message) {
  const goalId = message.data.goalId;  // camelCase
}
```

### 3. Connection Management

**Impact:** Custom connection handling code

**Action Required:**
- Remove manual EventSource creation
- Use RealtimeContext instead
- Let framework handle reconnection

**Example:**
```typescript
// ❌ Old - Manual management
const [eventSource, setEventSource] = useState(null);

useEffect(() => {
  const es = new EventSource('/api/events');
  setEventSource(es);
  return () => es.close();
}, []);

// ✅ New - Managed by context
// Just use hooks, context handles connection
useRealtimeEvent({ eventType: 'goal.created', onEvent: handler });
```

---

## Migration Steps

### Step 1: Update Environment Variables

Add WebSocket configuration:

```bash
# .env.development
REACT_APP_FEATURE_REALTIME=true
REACT_APP_REALTIME_WS_URL=wss://api.dev.purposepath.app/realtime

# .env.production
REACT_APP_FEATURE_REALTIME=true
REACT_APP_REALTIME_WS_URL=wss://api.purposepath.app/realtime
```

### Step 2: Remove Old SSE Code

**Files to remove/deprecate:**
- `src/services/realtime.ts` (old SSE implementation)
- `scripts/mock-sse-server.js` (old mock server)
- Any custom EventSource wrappers

### Step 3: Update Component Subscriptions

Replace SSE subscriptions with WebSocket hooks:

```typescript
// Before
useEffect(() => {
  const es = new EventSource('/api/realtime/events');
  
  es.addEventListener('goal-created', (event) => {
    const data = JSON.parse(event.data);
    handleGoalCreated(data);
  });
  
  return () => es.close();
}, []);

// After
useRealtimeEvent({
  eventType: 'goal.created',
  onEvent: (message) => {
    handleGoalCreated(message.data);
  }
});
```

### Step 4: Update Event Handlers

Update handlers to use new data structure:

```typescript
// Before
function handleGoalCreated(data) {
  console.log('Goal:', data.goal_id, data.goal_title);
}

// After
function handleGoalCreated(data) {
  console.log('Goal:', data.goalId, data.title);
}
```

### Step 5: Test Migration

1. Enable WebSocket feature flag
2. Verify connection indicator shows "Connected"
3. Test each event type:
   - Create goal → verify toast notification
   - Complete goal → verify UI update
   - Create action → verify dashboard update
4. Test reconnection (disable network, re-enable)
5. Test multiple tabs (connection sharing)

---

## Deprecated Code

### Files Marked for Removal

These files are no longer used and can be removed:

| File | Status | Replacement |
|------|--------|-------------|
| `src/services/realtime.ts` | Deprecated | `src/services/realtime-websocket.ts` |
| `scripts/mock-sse-server.js` | Deprecated | `scripts/mock-ws-server.js` |
| Old event handlers in components | To migrate | Use hooks from `src/hooks/realtime.ts` |

### Removal Timeline

- **Phase 1 (Current):** Both systems operational, WebSocket is default
- **Phase 2 (2 weeks):** Monitor WebSocket stability
- **Phase 3 (4 weeks):** Remove SSE feature flag
- **Phase 4 (6 weeks):** Delete deprecated SSE code

---

## Compatibility

### Browser Support

WebSocket is supported in:
- ✅ Chrome 16+
- ✅ Firefox 11+
- ✅ Safari 7+
- ✅ Edge (all versions)
- ✅ Mobile browsers (iOS Safari 7+, Chrome Mobile)

**Result:** Better compatibility than SSE (which had issues in some browsers)

### Backend Compatibility

WebSocket backend must support:
- AWS API Gateway WebSocket API
- Post-connection authentication
- Event broadcasting to connections
- Connection lifecycle management

---

## Rollback Plan

If critical issues arise:

### 1. Quick Rollback (Feature Flag)

```bash
# Disable WebSocket
REACT_APP_FEATURE_REALTIME=false
```

This disables all WebSocket features. Components gracefully degrade to periodic polling if implemented.

### 2. Full Rollback (Code)

If needed to revert to SSE:

1. Revert to previous Git tag
2. Redeploy frontend
3. Keep SSE backend endpoints active
4. Monitor for 24 hours

**Rollback Command:**
```bash
git revert <websocket-merge-commit>
git push origin main
```

---

## Testing Checklist

### Functional Testing

- [ ] Connection established on login
- [ ] Events received and processed
- [ ] Toast notifications appear
- [ ] Activity feeds update
- [ ] Connection indicator accurate
- [ ] Reconnection after network loss
- [ ] Token refresh handling
- [ ] Multi-tab behavior correct

### Performance Testing

- [ ] Connection time < 500ms
- [ ] Event latency < 100ms
- [ ] No memory leaks (1hr+ test)
- [ ] Handles 100+ events/min
- [ ] Reconnection < 1s average

### Browser Testing

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari
- [ ] Mobile Chrome

---

## Troubleshooting Migration Issues

### Issue: Events not being received

**Possible Causes:**
1. Feature flag not enabled
2. WebSocket URL incorrect
3. Authentication failing
4. Backend not broadcasting events

**Solutions:**
1. Check `REACT_APP_FEATURE_REALTIME=true`
2. Verify `REACT_APP_REALTIME_WS_URL`
3. Check browser console for auth errors
4. Verify backend WebSocket implementation

### Issue: Old event names still in code

**Solution:**
Search codebase for old patterns:

```bash
# Find hyphenated event names
grep -r "goal-created" src/
grep -r "action-updated" src/

# Find snake_case properties
grep -r "goal_id" src/
grep -r "user_id" src/
```

Replace with new conventions.

### Issue: Duplicate events

**Cause:** Both SSE and WebSocket active

**Solution:**
Ensure old SSE code is completely removed or feature flagged off.

---

## Benefits of Migration

### 1. Better Performance

- Single connection vs multiple EventSource connections
- Lower bandwidth (binary WebSocket frames)
- Faster reconnection with custom backoff

### 2. Enhanced Features

- Bidirectional communication (future: client → server)
- Structured event format with TypeScript types
- Better error handling and recovery
- Connection state visibility

### 3. Improved DX (Developer Experience)

- Type-safe event handling
- React hooks for easy integration
- Built-in reconnection logic
- Better debugging tools

### 4. Cost Reduction

- Fewer HTTP connections
- More efficient AWS API Gateway usage
- Better connection pooling

---

## Resources

- [WebSocket Implementation Guide](./REALTIME_WEBSOCKET_IMPLEMENTATION.md)
- [React Hooks Usage Guide](./REALTIME_HOOKS_USAGE.md)
- [WebSocket Frontend Spec](./WEBSOCKET_FRONTEND_INTEGRATION_SPEC.md)
- [Backend Integration Spec](../Specifications/backend-integration-traction-service-v2.md)

---

## Support

For migration questions or issues:

1. Review this guide
2. Check implementation documentation
3. Test with mock WebSocket server locally
4. Review browser console logs
5. Contact development team

---

**Migration Status:** ✅ Complete  
**SSE Deprecation:** Scheduled for 6 weeks  
**WebSocket Status:** Production Ready
