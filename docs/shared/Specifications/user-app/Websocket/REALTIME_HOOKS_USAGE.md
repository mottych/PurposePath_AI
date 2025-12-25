# Real-Time Hooks Usage Guide

**Phase 3: State Integration Complete**

This guide shows how to use the real-time WebSocket hooks in your React components.

## Available Hooks

### Core Hooks

1. **`useRealtimeEvent`** - Subscribe to specific event types
2. **`useRealtimeConnection`** - Get connection status
3. **`useRealtime`** - Full context access (connection + subscriptions)

### Specialized Hooks

4. **`useGoalActivity`** - Subscribe to goal-specific events
5. **`useRealtimeGoals`** - Subscribe to all goal events

---

## Installation

All hooks are exported from `src/hooks/realtime.ts`:

```typescript
import { 
  useRealtimeEvent,
  useRealtimeConnection,
  useGoalActivity,
  useRealtimeGoals 
} from '../hooks/realtime';
```

---

## Examples

### 1. Subscribe to Specific Events

```typescript
import { useRealtimeEvent } from '../hooks/realtime';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

function GoalList() {
  const queryClient = useQueryClient();

  // Invalidate cache when goals are created
  useRealtimeEvent({
    eventType: 'goal.created',
    onEvent: (message) => {
      console.log('New goal:', message.data.title);
      queryClient.invalidateQueries({ queryKey: ['goals'] });
      toast.success('New goal created');
    }
  });

  // Celebrate goal completions
  useRealtimeEvent({
    eventType: 'goal.completed',
    onEvent: (message) => {
      toast.success('Goal completed! 🎉', {
        description: message.data.finalNotes
      });
      queryClient.invalidateQueries({ queryKey: ['goals'] });
    }
  });

  return <div>{/* Goal list UI */}</div>;
}
```

### 2. Goal-Specific Activity Feed

```typescript
import { useGoalActivity } from '../hooks/realtime';
import { useState } from 'react';

function GoalRoom({ goalId }: { goalId: string }) {
  const [activities, setActivities] = useState<Activity[]>([]);

  useGoalActivity({
    goalId,
    onActivityCreated: (data) => {
      // Add new activity to the feed
      setActivities(prev => [{
        id: data.activityId,
        type: data.activityType,
        description: data.description,
        timestamp: data.createdAt
      }, ...prev]);
    },
    onCompleted: (data) => {
      toast.success('Goal completed! 🎉');
    },
    onPaused: (data) => {
      toast.info('Goal paused', {
        description: data.reason
      });
    }
  });

  return (
    <div>
      <h2>Activity Feed</h2>
      {activities.map(activity => (
        <ActivityCard key={activity.id} activity={activity} />
      ))}
    </div>
  );
}
```

### 3. Dashboard with All Goal Events

```typescript
import { useRealtimeGoals } from '../hooks/realtime';
import { useQueryClient } from '@tanstack/react-query';

function Dashboard() {
  const queryClient = useQueryClient();

  useRealtimeGoals({
    onGoalCreated: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onGoalCompleted: (data) => {
      toast.success(`Goal "${data.goalId}" completed! 🎉`);
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    },
    onAnyGoalEvent: (eventType, data) => {
      console.log('Goal event:', eventType, data);
    }
  });

  return <div>{/* Dashboard UI */}</div>;
}
```

### 4. Connection Status Indicator

```typescript
import { useRealtimeConnection } from '../hooks/realtime';

function ConnectionIndicator() {
  const { isConnected, connectionState } = useRealtimeConnection();

  if (!isConnected) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <div className="w-2 h-2 rounded-full bg-red-500" />
        <span>Offline</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm text-green-600">
      <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
      <span>Live</span>
    </div>
  );
}
```

### 5. Conditional Subscriptions

```typescript
function OperationsPage() {
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  // Only subscribe when authenticated
  useRealtimeEvent({
    eventType: 'action.completed',
    enabled: isAuthenticated, // Conditional subscription
    onEvent: (message) => {
      queryClient.invalidateQueries({ queryKey: ['actions'] });
    }
  });

  return <div>{/* Operations UI */}</div>;
}
```

### 6. Multiple Event Subscriptions

```typescript
function IssuesBoard() {
  const queryClient = useQueryClient();

  // Subscribe to issue created
  useRealtimeEvent({
    eventType: 'issue.created',
    onEvent: (message) => {
      const { severity } = message.data;
      
      if (severity === 'critical') {
        toast.error('Critical issue created!', {
          description: message.data.title
        });
      }
      
      queryClient.invalidateQueries({ queryKey: ['issues'] });
    }
  });

  // Subscribe to issue status changes
  useRealtimeEvent({
    eventType: 'issue.status_changed',
    onEvent: (message) => {
      if (message.data.newStatus === 'resolved') {
        toast.success('Issue resolved');
      }
      queryClient.invalidateQueries({ queryKey: ['issues'] });
    }
  });

  return <div>{/* Issues board UI */}</div>;
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
    // Invalidate specific query
    queryClient.invalidateQueries({ queryKey: ['goals'] });
    
    // Or invalidate multiple related queries
    queryClient.invalidateQueries({ queryKey: ['goals'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
  }
});
```

### 2. Event Filtering

Filter events in the callback to avoid unnecessary updates:

```typescript
useRealtimeEvent({
  eventType: 'action.status_changed',
  onEvent: (message) => {
    // Only handle if it's for our specific goal
    if (message.data.goalId === currentGoalId) {
      refetchActions();
    }
  }
});
```

### 3. Toast Notifications

Use appropriate toast types for different events:

```typescript
// Success for positive events
toast.success('Goal completed! 🎉');

// Error for critical issues
toast.error('Critical issue reported');

// Info for status changes
toast.info('Goal paused');

// Warning for important notifications
toast.warning('KPI threshold breached');
```

### 4. Cleanup

Hooks automatically clean up subscriptions when components unmount. No manual cleanup needed!

### 5. Feature Flag

Always respect the feature flag - hooks automatically disable when `REACT_APP_FEATURE_REALTIME=false`.

---

## Optimistic Updates

When making mutations, use optimistic updates for instant UI feedback:

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';

function useCompleteGoal() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (goalId: string) => goalService.complete(goalId),
    
    // Optimistic update
    onMutate: async (goalId) => {
      await queryClient.cancelQueries({ queryKey: ['goals', goalId] });
      
      const previousGoal = queryClient.getQueryData(['goals', goalId]);
      
      // Update UI immediately
      queryClient.setQueryData(['goals', goalId], (old: any) => ({
        ...old,
        status: 'completed'
      }));
      
      return { previousGoal };
    },
    
    // Rollback on error
    onError: (err, goalId, context) => {
      queryClient.setQueryData(['goals', goalId], context.previousGoal);
      toast.error('Failed to complete goal');
    },
    
    // Refetch on success (server will send WebSocket event too)
    onSuccess: () => {
      toast.success('Goal completed! 🎉');
    }
  });
}
```

---

## Troubleshooting

### Events Not Received

1. Check feature flag: `REACT_APP_FEATURE_REALTIME=true`
2. Check connection: Use `<RealtimeDebugPanel />` in development
3. Check WebSocket URL: `REACT_APP_REALTIME_WS_URL` is set
4. Check authentication: Must be logged in
5. Check browser console for errors

### Duplicate Events

Ensure you're not subscribing multiple times:

```typescript
// ❌ Bad - subscribes on every render
function BadComponent() {
  const [data, setData] = useState([]);
  
  // This creates new subscription on every render!
  useRealtimeEvent({
    eventType: 'goal.created',
    onEvent: () => setData([...data, newItem])
  });
}

// ✅ Good - stable callback reference
function GoodComponent() {
  const queryClient = useQueryClient();
  
  useRealtimeEvent({
    eventType: 'goal.created',
    onEvent: () => {
      queryClient.invalidateQueries({ queryKey: ['goals'] });
    }
  });
}
```

### Connection Status

Monitor connection in development:

```typescript
import { RealtimeDebugPanel } from '../contexts/RealtimeContext';

function App() {
  return (
    <>
      {process.env.NODE_ENV === 'development' && <RealtimeDebugPanel />}
      {/* Rest of app */}
    </>
  );
}
```

---

## Next Steps

- **Phase 4:** Visual feedback (live badges, toast notifications, activity feeds)
- **Phase 5:** Testing and documentation

For more details, see:
- `docs/Websocket/WEBSOCKET_FRONTEND_INTEGRATION_SPEC.md` - Event types reference
- `src/contexts/RealtimeContext.tsx` - Context implementation
- `src/hooks/` - Hook implementations
