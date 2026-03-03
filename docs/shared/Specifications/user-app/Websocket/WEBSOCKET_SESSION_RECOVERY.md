# WebSocket Implementation - Quick Start for AI Agents

**Purpose:** Quick reference for AI agents to resume work after chat session restart

---

## Current Status (As of October 5, 2025)

**Phase:** 0 - Analysis & Planning ✅ **COMPLETE**  
**Next Phase:** 1 - WebSocket Connection Manager (Not Started)  
**Overall Progress:** 16% (1/6 phases)

---

## Critical Files to Read First

1. **📊 Progress Tracker** (READ FIRST)
   - `docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md`
   - Contains detailed task breakdown, checkboxes, status

2. **📖 Analysis Document**
   - `docs/WEBSOCKET_MIGRATION_ANALYSIS.md`
   - Contains architecture, technical specs, code examples

3. **🔧 Existing Implementation**
   - `src/services/realtime.ts` - Current SSE implementation (to be replaced)
   - `src/contexts/AuthContext.tsx` - Token management (ready to use)
   - `src/contexts/FeaturesContext.tsx` - Feature flags

4. **📋 Backend Spec**
   - `docs/backend-integration-specs-v2.md` - API contracts
   - Look for "Real-time Endpoints (SSE)" section (will become WebSocket)

---

## Quick Context Summary

### What We're Doing
- **Migrating** from SSE (Server-Sent Events) to WebSocket for real-time updates
- **Backend** is implementing AWS API Gateway WebSocket API
- **Frontend** needs to replace EventSource with WebSocket and expand event coverage

### What Exists
- ✅ Partial SSE infrastructure (goal activity only)
- ✅ Feature flag system (`REACT_APP_FEATURE_REALTIME`)
- ✅ Auth with token storage, refresh, tenant ID
- ✅ Context API state management pattern
- ✅ TypeScript types for all entities
- ✅ Mock SSE server for local testing

### What's Missing
- ❌ WebSocket implementation (only SSE)
- ❌ Support for action, Measure, issue events
- ❌ Global real-time state management
- ❌ Connection status UI
- ❌ Comprehensive event handlers

---

## Architecture Decision

**Chosen Approach:** Global Context with React Hooks

- Single WebSocket connection via `RealtimeContext`
- React hooks for event subscription: `useRealtimeEvent()`
- Follows existing Context API patterns
- Better performance than component-level subscriptions

---

## Next Action (Phase 1)

Create WebSocket connection manager:

1. **Create** `src/services/realtime-websocket.ts`
   - Implement `RealtimeWebSocket` class
   - Connection lifecycle, reconnection, heartbeat
   - See `WEBSOCKET_MIGRATION_ANALYSIS.md` section 3.1 for code

2. **Create** `src/types/realtime.ts`
   - All event payload types
   - Connection status types

3. **Update** `env.example`
   - Add `REACT_APP_REALTIME_WS_URL`

---

## Backend WebSocket Spec (Quick Reference)

**URL:** `wss://api.{env}.purposepath.app/realtime?access_token={token}&tenant={tenantId}`

**Event Types:**
- Goal: `goal.created`, `goal.activated`, `goal.completed`, `goal.cancelled`, `goal.activity.created`
- Action: `action.created`, `action.status_changed`, `action.completed`, `action.priority_changed`, `action.reassigned`, `action.progress_updated`
- Measure: `measure.reading.created`
- Issue: `issue.created`, `issue.status_changed`
- Decision: `decision.created`
- Attachment: `attachment.created`
- System: `ping` (respond with `pong`), `error`

**Message Format:**
```json
{
  "type": "event_type",
  "timestamp": "ISO8601",
  "data": { /* event-specific payload */ }
}
```

**Error Codes:**
- `UNAUTHORIZED` → refresh token, reconnect
- `RATE_LIMIT_EXCEEDED` → backoff
- `INTERNAL_ERROR` → log and continue

---

## Key Technical Decisions

1. **Use native WebSocket API** (no external library needed)
2. **Exponential backoff** for reconnection: 1s, 2s, 4s, 8s, 16s, 30s (max)
3. **Token refresh** on UNAUTHORIZED via existing `apiClient.refreshToken()`
4. **Event normalization** from snake_case to camelCase (keep from existing code)
5. **Feature flag** controls connection: `REACT_APP_FEATURE_REALTIME`

---

## How to Resume Work

1. **Read progress tracker**: `docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md`
2. **Find current phase**: Check status table and task checkboxes
3. **Review analysis**: `docs/WEBSOCKET_MIGRATION_ANALYSIS.md` for technical details
4. **Create todo list**: Use `manage_todo_list` tool to track session tasks
5. **Update progress**: Mark tasks complete in progress tracker as you go
6. **Update this file**: If architecture changes or new decisions are made

---

## Testing Strategy

- **Mock Server**: `scripts/mock-sse-server.js` (convert to WebSocket)
- **Unit Tests**: `src/services/__tests__/realtime-websocket.test.ts`
- **Manual Tests**: Connect/disconnect, token expiry, network interruption
- **Target Coverage**: 80%+

---

## Resources

### Documentation
- Analysis: `docs/WEBSOCKET_MIGRATION_ANALYSIS.md`
- Progress: `docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md`
- Backend API: `docs/backend-integration-specs-v2.md`
- Goals Design: `docs/design-frontend-goals-module.md`

### Key Services
- Auth: `src/services/api.ts` (apiClient)
- Current Realtime: `src/services/realtime.ts`
- Mock Server: `scripts/mock-sse-server.js`

### Contexts
- Auth: `src/contexts/AuthContext.tsx`
- Features: `src/contexts/FeaturesContext.tsx`
- Limits: `src/contexts/LimitsContext.tsx`
- Subscription: `src/contexts/SubscriptionContext.tsx`
- Planning: `src/contexts/PlanningContext.tsx`

---

## Common Commands

```bash
# Start dev server
npm start

# Run tests
npm test

# Start mock SSE server (will be converted to WebSocket)
npm run sse:mock

# Run with realtime enabled
$env:REACT_APP_FEATURE_REALTIME="true"; npm start
```

---

## Update Instructions

**When completing tasks:**
1. Update checkboxes in `docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md`
2. Update phase status and progress percentages
3. Add notes about decisions or issues encountered
4. Update "Last Updated" date
5. Add change log entry

**When session restarts:**
1. Read this file first
2. Read progress tracker
3. Continue from current phase/task

---

**Last Updated:** October 5, 2025  
**Status:** Analysis complete, ready for implementation
