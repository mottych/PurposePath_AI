# Real-Time WebSocket Implementation Guide

**Status:** Production Ready  
**Version:** 1.0  
**Last Updated:** November 2025

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Event Types](#event-types)
5. [Usage Patterns](#usage-patterns)
6. [Components](#components)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Overview

The PurposePath WebSocket real-time system provides bidirectional communication between the frontend and backend for instant updates on goals, actions, issues, and KPIs.

### Key Features

- **Post-connection authentication** - Secure WebSocket after connection established
- **Automatic reconnection** - Exponential backoff with configurable retry logic
- **Client-side keep-alive** - Prevents AWS API Gateway timeout (8-min ping)
- **Type-safe events** - Full TypeScript support for all event payloads
- **React integration** - Custom hooks for easy component integration
- **Visual feedback** - Connection indicators, live badges, toast notifications
- **Feature flag support** - Easy enable/disable via environment variable

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend App                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌─────────────────────┐          │
│  │  Components  │────────>│  React Hooks        │          │
│  │  - Dashboard │         │  - useRealtimeEvent │          │
│  │  - GoalRoom  │         │  - useGoalActivity  │          │
│  │  - Operations│         │  - useRealtimeGoals │          │
│  └──────────────┘         └──────────┬──────────┘          │
│         │                             │                      │
│         │                             │                      │
│         v                             v                      │
│  ┌──────────────────────────────────────────────┐          │
│  │         RealtimeContext                       │          │
│  │  - Connection management                      │          │
│  │  - Event subscription registry                │          │
│  │  - State tracking (connected, stats)          │          │
│  └────────────────────┬─────────────────────────┘          │
│                       │                                      │
│                       v                                      │
│  ┌──────────────────────────────────────────────┐          │
│  │     RealtimeWebSocket Manager                 │          │
│  │  - WebSocket connection                       │          │
│  │  - Post-connection auth                       │          │
│  │  - Reconnection with backoff                  │          │
│  │  - Keep-alive ping (8 min)                    │          │
│  │  - Event dispatching                          │          │
│  └────────────────────┬─────────────────────────┘          │
│                       │                                      │
└───────────────────────┼──────────────────────────────────────┘
                        │
                        │ WebSocket (WSS)
                        │
                        v
┌─────────────────────────────────────────────────────────────┐
│              AWS API Gateway WebSocket API                   │
│  wss://api.{env}.purposepath.app/realtime                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        v
┌─────────────────────────────────────────────────────────────┐
│                  Backend Services                            │
│  - Authentication                                            │
│  - Event broadcasting                                        │
│  - Connection management                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Enable/disable real-time features
REACT_APP_FEATURE_REALTIME=true

# WebSocket server URL
REACT_APP_REALTIME_WS_URL=wss://api.dev.purposepath.app/realtime
```

### Environment-Specific URLs

| Environment | WebSocket URL |
|------------|---------------|
| Development | `wss://api.dev.purposepath.app/realtime` |
| Staging | `wss://api.staging.purposepath.app/realtime` |
| Production | `wss://api.purposepath.app/realtime` |

### Local Development

For local development, use the mock WebSocket server:

```bash
# Start mock server
npm run mock:ws

# Configure frontend to use mock server
REACT_APP_REALTIME_WS_URL=ws://localhost:5055
```

---

## Event Types

### Event Message Structure

All WebSocket events follow this structure:

```typescript
interface WebSocketMessage<T = any> {
  type: string;              // Event type (e.g., 'goal.created')
  data: T;                   // Event-specific payload
  timestamp: string;         // ISO 8601 timestamp
  eventId: string;           // Unique event identifier
  tenantId: string;          // Tenant identifier
}
```

### Goal Events (7 types)

| Event Type | Description | Payload |
|-----------|-------------|---------|
| `goal.created` | New goal created | `GoalCreatedEventData` |
| `goal.activated` | Goal activated from draft/paused | `GoalActivatedEventData` |
| `goal.completed` | Goal successfully completed | `GoalCompletedEventData` |
| `goal.cancelled` | Goal cancelled | `GoalCancelledEventData` |
| `goal.paused` | Goal paused | `GoalPausedEventData` |
| `goal.resumed` | Goal resumed from paused | `GoalResumedEventData` |
| `goal.activity.created` | Activity added to goal | `GoalActivityCreatedEventData` |

### Action Events (6 types)

| Event Type | Description | Payload |
|-----------|-------------|---------|
| `action.created` | New action created | `ActionCreatedEventData` |
| `action.status_changed` | Action status updated | `ActionStatusChangedEventData` |
| `action.completed` | Action completed | `ActionCompletedEventData` |
| `action.priority_changed` | Priority updated | `ActionPriorityChangedEventData` |
| `action.reassigned` | Assigned to different user | `ActionReassignedEventData` |
| `action.progress_updated` | Progress percentage changed | `ActionProgressUpdatedEventData` |

### Issue Events (2 types)

| Event Type | Description | Payload |
|-----------|-------------|---------|
| `issue.created` | New issue reported | `IssueCreatedEventData` |
| `issue.status_changed` | Issue status updated | `IssueStatusChangedEventData` |

### KPI Events (1 type)

| Event Type | Description | Payload |
|-----------|-------------|---------|
| `kpi.reading_created` | New KPI reading recorded | `KPIReadingCreatedEventData` |

### Authentication Events

| Event Type | Description |
|-----------|-------------|
| `auth.success` | Authentication successful |
| `auth.error` | Authentication failed |

---

## Usage Patterns

### 1. Subscribe to Specific Events

```typescript
import { useRealtimeEvent } from '../hooks/realtime';
import { useQueryClient } from '@tanstack/react-query';

function GoalList() {
  const queryClient = useQueryClient();

  // Subscribe to goal created events
  useRealtimeEvent({
    eventType: 'goal.created',
    onEvent: (message) => {
      console.log('New goal created:', message.data.title);
      
      // Invalidate cache to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      
      // Show toast notification
      toast.success('New goal created');
    }
  });

  return <div>{/* Goal list UI */}</div>;
}
```

### 2. Goal-Specific Activity Feed

```typescript
import { useGoalActivity } from '../hooks/realtime';

function GoalRoom({ goalId }: { goalId: string }) {
  useGoalActivity({
    goalId,
    onCompleted: (data) => {
      toast.success('Goal completed! 🎉');
      refetchGoal();
    },
    onPaused: (data) => {
      toast.info('Goal paused', {
        description: data.reason
      });
    },
    onActivityCreated: (data) => {
      // Update activity feed
      addActivity(data);
    }
  });

  return <div>{/* Goal UI */}</div>;
}
```

### 3. Connection Status

```typescript
import { useRealtimeConnection } from '../hooks/realtime';

function ConnectionIndicator() {
  const { isConnected, connectionState } = useRealtimeConnection();

  return (
    <div>
      {isConnected ? (
        <span className="text-green-600">● Live</span>
      ) : (
        <span className="text-gray-400">○ Offline</span>
      )}
    </div>
  );
}
```

### 4. Live Update Badges

```typescript
import { LiveBadge, useLiveBadge } from '../components/ui/LiveBadge';

function GoalCard({ goal }: { goal: Goal }) {
  const { showBadge, triggerBadge } = useLiveBadge();

  useRealtimeEvent({
    eventType: 'goal.completed',
    onEvent: (message) => {
      if (message.data.goalId === goal.id) {
        triggerBadge(); // Show "Live" badge
        refetch();
      }
    }
  });

  return (
    <div className="goal-card">
      <LiveBadge show={showBadge} />
      {/* Goal content */}
    </div>
  );
}
```

### 5. Toast Notifications

```typescript
import { realtimeToasts } from '../services/realtime-toasts';

// In a component or hook
useRealtimeEvent({
  eventType: 'issue.created',
  onEvent: (message) => {
    realtimeToasts.issueCreated(message.data);
    refetchIssues();
  }
});
```

### 6. Dashboard-Wide Subscriptions

```typescript
import { useRealtimeGoals } from '../hooks/realtime';

function Dashboard() {
  const queryClient = useQueryClient();

  useRealtimeGoals({
    onGoalCreated: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onGoalCompleted: (data) => {
      toast.success(`Goal completed! 🎉`);
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onAnyGoalEvent: (eventType, data) => {
      console.log('Goal event:', eventType);
    }
  });

  return <div>{/* Dashboard UI */}</div>;
}
```

---

## Components

### Core Components

#### RealtimeContext

Provides WebSocket connection and subscription management to the entire app.

**Location:** `src/contexts/RealtimeContext.tsx`

**Features:**
- Auto-connects on authentication
- Manages connection lifecycle
- Provides subscription registry
- Tracks connection stats

#### RealtimeIndicator

Visual connection status indicator in the header.

**Location:** `src/components/ui/RealtimeIndicator.tsx`

**Props:**
```typescript
interface RealtimeIndicatorProps {
  className?: string;
  showDetails?: boolean;
  position?: 'header' | 'footer';
}
```

#### LiveBadge

Badge showing recent real-time updates.

**Location:** `src/components/ui/LiveBadge.tsx`

**Props:**
```typescript
interface LiveBadgeProps {
  show?: boolean;
  autoHideDuration?: number;
  onHide?: () => void;
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}
```

#### GoalActivityFeed

Real-time activity feed for goal events.

**Location:** `src/components/strategic-planning/GoalActivityFeed.tsx`

**Props:**
```typescript
interface GoalActivityFeedProps {
  goalId: string;
  initialActivities?: ActivityItem[];
  maxActivities?: number;
  autoScroll?: boolean;
}
```

### Custom Hooks

#### useRealtimeEvent

Subscribe to specific event types.

```typescript
useRealtimeEvent({
  eventType: 'goal.created',
  onEvent: (message) => { /* handler */ },
  enabled: true,
  dependencies: []
});
```

#### useRealtimeConnection

Get connection status only.

```typescript
const { isConnected, connectionState, stats } = useRealtimeConnection();
```

#### useGoalActivity

Subscribe to all goal-specific events.

```typescript
useGoalActivity({
  goalId,
  onCompleted: (data) => { /* handler */ },
  onPaused: (data) => { /* handler */ }
});
```

#### useRealtimeGoals

Subscribe to all goal events (not filtered by ID).

```typescript
useRealtimeGoals({
  onGoalCreated: (data) => { /* handler */ },
  onGoalCompleted: (data) => { /* handler */ }
});
```

---

## Troubleshooting

### Connection Issues

**Problem:** WebSocket not connecting

**Solutions:**
1. Check feature flag: `REACT_APP_FEATURE_REALTIME=true`
2. Verify WebSocket URL is correct
3. Check browser console for errors
4. Ensure user is authenticated
5. Check network tab for WebSocket connection
6. Verify backend WebSocket endpoint is running

**Problem:** Frequent disconnections

**Solutions:**
1. Check network stability
2. Verify keep-alive ping is working (every 8 minutes)
3. Check for token expiration issues
4. Review reconnection logs in console

### Event Issues

**Problem:** Events not being received

**Solutions:**
1. Check subscription is active (`useRealtimeEvent` mounted)
2. Verify event type string matches exactly
3. Check WebSocket connection is established
4. Use `RealtimeDebugPanel` in development
5. Check browser console for event logs

**Problem:** Duplicate events

**Solutions:**
1. Ensure hook dependencies are stable
2. Check component isn't remounting unnecessarily
3. Verify subscription cleanup on unmount
4. Use React DevTools to check render cycles

### Performance Issues

**Problem:** High memory usage

**Solutions:**
1. Check for memory leaks in event handlers
2. Ensure proper cleanup of subscriptions
3. Limit activity feed size (`maxActivities` prop)
4. Review event handler complexity

**Problem:** UI lag on events

**Solutions:**
1. Debounce cache invalidations
2. Use optimistic updates for immediate feedback
3. Batch React state updates
4. Profile with React DevTools

### Debug Tools

#### RealtimeDebugPanel

Shows connection stats in development:

```typescript
import { RealtimeDebugPanel } from '../contexts/RealtimeContext';

// Add to App.tsx in development
{process.env.NODE_ENV === 'development' && <RealtimeDebugPanel />}
```

#### Console Logging

Enable verbose logging:

```typescript
// In RealtimeContext or components
const debug = true;

if (debug) {
  console.log('[Realtime] Event received:', message);
}
```

---

## Best Practices

### 1. Cache Invalidation

Always invalidate React Query caches when data changes:

```typescript
useRealtimeEvent({
  eventType: 'goal.created',
  onEvent: () => {
    // Specific queries
    queryClient.invalidateQueries({ queryKey: ['goals'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
  }
});
```

### 2. Event Filtering

Filter events in callbacks to avoid unnecessary updates:

```typescript
useRealtimeEvent({
  eventType: 'action.status_changed',
  onEvent: (message) => {
    // Only handle if relevant
    if (message.data.goalId === currentGoalId) {
      refetchActions();
    }
  }
});
```

### 3. Optimistic Updates

Use optimistic updates for instant UI feedback:

```typescript
const mutation = useMutation({
  mutationFn: completeGoal,
  onMutate: async (goalId) => {
    // Cancel outgoing refetches
    await queryClient.cancelQueries({ queryKey: ['goals', goalId] });
    
    // Snapshot previous value
    const previous = queryClient.getQueryData(['goals', goalId]);
    
    // Optimistically update
    queryClient.setQueryData(['goals', goalId], (old) => ({
      ...old,
      status: 'completed'
    }));
    
    return { previous };
  },
  onError: (err, variables, context) => {
    // Rollback on error
    queryClient.setQueryData(['goals', variables], context.previous);
  },
  onSuccess: () => {
    // Server will send WebSocket event confirming
    toast.success('Goal completed! 🎉');
  }
});
```

### 4. Subscription Cleanup

Hooks automatically cleanup, but manual subscriptions need cleanup:

```typescript
useEffect(() => {
  const subscriptionId = realtimeWebSocket.subscribe('goal.created', handler);
  
  return () => {
    realtimeWebSocket.unsubscribe(subscriptionId);
  };
}, []);
```

### 5. Error Handling

Always handle errors gracefully:

```typescript
useRealtimeEvent({
  eventType: 'goal.created',
  onEvent: (message) => {
    try {
      // Process event
      processGoal(message.data);
    } catch (error) {
      console.error('Failed to process goal event:', error);
      toast.error('Failed to update goal');
    }
  }
});
```

### 6. Feature Flag Respect

Always respect the feature flag:

```typescript
const { isEnabled } = useRealtimeConnection();

if (!isEnabled) {
  // Fallback to polling or show offline indicator
  return <OfflineMode />;
}
```

### 7. Memory Management

Keep activity feeds and event lists bounded:

```typescript
<GoalActivityFeed 
  goalId={goalId}
  maxActivities={50}  // Limit size
  autoScroll={true}
/>
```

---

## Performance Considerations

### Connection Management

- Single WebSocket connection shared across app
- Automatic reconnection with exponential backoff
- Keep-alive ping every 8 minutes
- Connection pooling not needed (single connection)

### Event Processing

- Events processed in order received
- Subscription callbacks executed synchronously
- Use React state batching for multiple updates
- Debounce expensive operations

### Memory Usage

- Event handlers cleaned up on component unmount
- Activity feeds automatically limited
- No event history stored beyond UI needs
- Connection stats updated incrementally

---

## References

- [WebSocket Frontend Integration Spec](./WEBSOCKET_FRONTEND_INTEGRATION_SPEC.md) - Complete event reference
- [Real-time Hooks Usage Guide](./REALTIME_HOOKS_USAGE.md) - Hook examples
- [Backend Integration Spec](../Specifications/backend-integration-traction-service-v2.md) - API reference
- [Mock WebSocket Server](../../scripts/mock-ws-server.js) - Local development

---

## Support

For issues or questions:
1. Check this documentation
2. Review browser console logs
3. Use `RealtimeDebugPanel` in development
4. Check GitHub issues
5. Contact the development team

---

**Document Version:** 1.0  
**Last Updated:** November 2025  
**Status:** Production Ready
