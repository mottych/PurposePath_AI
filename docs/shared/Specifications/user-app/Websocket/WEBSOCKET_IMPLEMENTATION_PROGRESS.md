# WebSocket Real-time Implementation - Progress Tracker

**Started:** October 5, 2025  
**Status:** Planning Complete ✅  
**Current Phase:** Ready to Begin Implementation  
**Last Updated:** October 5, 2025

---

## Quick Status Overview

| Phase | Status | Progress | Start Date | Complete Date |
|-------|--------|----------|------------|---------------|
| 0. Analysis & Planning | ✅ Complete | 100% | Oct 5, 2025 | Oct 5, 2025 |
| 1. WebSocket Connection Manager | ⏳ Not Started | 0% | - | - |
| 2. Event Handling System | ⏳ Not Started | 0% | - | - |
| 3. State Integration | ⏳ Not Started | 0% | - | - |
| 4. UI Integration | ⏳ Not Started | 0% | - | - |
| 5. Testing & Documentation | ⏳ Not Started | 0% | - | - |

**Overall Progress**: 29% (Phase 0 complete, Phase 1 at 80%)

---

## Phase 0: Analysis & Planning ✅

**Status:** Complete  
**Completed:** October 5, 2025

### Deliverables
- ✅ `docs/WEBSOCKET_MIGRATION_ANALYSIS.md` - Comprehensive analysis document
- ✅ Architecture recommendations (Global Context approach)
- ✅ Technical specifications
- ✅ Timeline and effort estimates

### Key Findings
- Existing SSE infrastructure in `src/services/realtime.ts`
- Context API state management pattern established
- Authentication fully ready (token storage, refresh, tenant ID)
- TypeScript types complete for all entities
- Feature flag system in place

### Next Steps
- Review analysis with team
- Confirm backend WebSocket spec alignment
- Begin Phase 1: WebSocket Connection Manager

---

## Phase 1: WebSocket Connection Manager ⏳

**Status:** Not Started  
**Estimated Duration:** 2-3 days  
**Dependencies:** Backend WebSocket API deployed

### Tasks

### Task 1.1: Implement RealtimeWebSocket Class
- [x] Create `src/services/realtime-websocket.ts`
  - [ ] Implement `RealtimeWebSocket` class
  - [ ] Connection lifecycle (connect, disconnect, reconnect)
  - [ ] Exponential backoff with jitter
  - [ ] Ping/pong heartbeat handling
  - [ ] Connection state management
  - [ ] Event emitter pattern
  
- [ ] **Task 1.2:** Create `src/types/realtime.ts`
  - [ ] `ConnectionStatus` type
  - [ ] `WebSocketMessage<T>` interface
  - [ ] All event payload types (goals, actions, KPIs, issues)
  - [ ] Event handler types
  
- [ ] **Task 1.3:** Update environment configuration
  ### Task 1.3: Update Environment Configuration
- [x] Add `REACT_APP_REALTIME_WS_URL` to `env.example`
  - [ ] Document environment-specific URLs
  - [ ] Keep `REACT_APP_FEATURE_REALTIME` flag
  
- [ ] **Task 1.4:** Implement token refresh integration
  - [ ] Detect `UNAUTHORIZED` error from WebSocket
  - [ ] Trigger `apiClient.refreshToken()`
  - [ ] Reconnect with new token
  
- [ ] **Task 1.5:** Manual testing
  - [ ] Connect to mock WebSocket server
  - [ ] Test reconnection logic
  - [ ] Test token expiration handling
  - [ ] Test ping/pong heartbeat

### Acceptance Criteria
- ✅ WebSocket connects to backend
- ✅ Handles token expiration and reconnection
- ✅ Exponential backoff works correctly
- ✅ Ping/pong heartbeat implemented
- ✅ Connection state updates correctly

### Notes
- Use native `WebSocket` API (no external library needed)
- Follow existing `realtime.ts` patterns for consistency
- Implement comprehensive error handling

---

## Phase 2: Event Handling System ⏳

**Status:** Not Started  
**Estimated Duration:** 2 days  
**Dependencies:** Phase 1 complete

### Tasks

- [ ] **Task 2.1:** Expand event type support
  - [ ] Goal events (created, activated, completed, cancelled, activity.created)
  - [ ] Action events (created, status_changed, completed, priority_changed, reassigned, progress_updated)
  - [ ] Measure events (reading.created)
  - [ ] Issue events (created, status_changed)
  - [ ] Decision events (created)
  - [ ] Attachment events (created)
  - [ ] System events (ping, error)
  
- [ ] **Task 2.2:** Event normalization
  - [ ] Handle snake_case to camelCase conversion
  - [ ] Validate event payloads
  - [ ] Parse and type-check events
  
- [ ] **Task 2.3:** Create event handler registry
  - [ ] Allow components to subscribe to specific event types
  - [ ] Emit events to all subscribers
  - [ ] Handle cleanup on unmount
  
- [ ] **Task 2.4:** Update mock server
  - [ ] Convert `scripts/mock-sse-server.js` to WebSocket
  - [ ] Support all event types
  - [ ] Implement ping/pong
  - [ ] Create `scripts/mock-ws-server.js`

### Acceptance Criteria
- ✅ All backend event types supported
- ✅ Components can subscribe to events
- ✅ Event normalization works correctly
- ✅ Mock server supports WebSocket protocol

### Notes
- Keep event normalization logic from existing `realtime.ts`
- Add comprehensive event validation

---

## Phase 3: State Integration ⏳

**Status:** Not Started  
**Estimated Duration:** 2-3 days  
**Dependencies:** Phase 2 complete

### Tasks

- [ ] **Task 3.1:** Create `src/contexts/RealtimeContext.tsx`
  - [ ] Manage WebSocket connection lifecycle
  - [ ] Provide connection status to components
  - [ ] Implement connection sharing (singleton pattern)
  - [ ] Handle connect/disconnect on auth changes
  
- [ ] **Task 3.2:** Create React hooks
  - [ ] `useRealtime()` - Get connection and status
  - [ ] `useRealtimeEvent(eventType, handler)` - Subscribe to events
  - [ ] `useRealtimeConnection()` - Connection state only
  - [ ] `useGoalActivity(goalId)` - Goal-specific activity feed
  
- [ ] **Task 3.3:** Integrate with App.tsx
  - [ ] Add `<RealtimeProvider>` to component tree
  - [ ] Place after `AuthProvider` (needs auth context)
  - [ ] Place before main route components
  
- [ ] **Task 3.4:** Update components to use hooks
  - [ ] `GoalRoom.tsx` - Use `useGoalActivity()`
  - [ ] Dashboard components - Subscribe to relevant events
  - [ ] Operations page - Subscribe to action/issue events
  
- [ ] **Task 3.5:** Handle optimistic updates
  - [ ] De-duplicate events (check by entity ID)
  - [ ] Prevent double-adding items user just created
  - [ ] Handle race conditions

### Acceptance Criteria
- ✅ Single WebSocket connection shared across app
- ✅ Components can subscribe via hooks
- ✅ Goal activity updates in real-time
- ✅ No duplicate events or data inconsistencies
- ✅ Handles optimistic updates correctly

### Notes
- Follow existing Context API patterns
- Implement proper cleanup in useEffect hooks
- Consider connection sharing across browser tabs (future enhancement)

---

## Phase 4: UI Integration & Indicators ⏳

**Status:** Not Started  
**Estimated Duration:** 1-2 days  
**Dependencies:** Phase 3 complete

### Tasks

- [ ] **Task 4.1:** Create connection status indicator
  - [ ] Create `src/components/ui/RealtimeIndicator.tsx`
  - [ ] Show: Connected, Disconnected, Reconnecting states
  - [ ] Color-coded status (green, gray, yellow)
  - [ ] Optional: Click to see connection details
  - [ ] Add to `Layout.tsx` (header or footer)
  
- [ ] **Task 4.2:** Create real-time badges
  - [ ] Create `src/components/ui/LiveBadge.tsx`
  - [ ] "Live" badge for updated items
  - [ ] Fade in/out animation
  - [ ] Pulse effect for new items
  
- [ ] **Task 4.3:** Implement toast notifications
  - [ ] Goal created/completed events
  - [ ] High-priority action created
  - [ ] Critical issue created
  - [ ] Measure threshold breached (red zone)
  - [ ] Use existing `sonner` library
  
- [ ] **Task 4.4:** Update activity feeds
  - [ ] Real-time updates in `GoalActivityFeed.tsx`
  - [ ] Auto-scroll to new items (optional)
  - [ ] Show "New activity" indicator
  - [ ] Highlight new items briefly
  
- [ ] **Task 4.5:** Add live indicators to dashboards
  - [ ] Dashboard widgets show "Live" badge
  - [ ] Updated rows/cards highlight briefly
  - [ ] Smooth animations for new data

### Acceptance Criteria
- ✅ Connection status visible to user
- ✅ Updated items show live indicator
- ✅ Toast notifications work for important events
- ✅ Activity feeds update in real-time
- ✅ Smooth, non-jarring UI updates

### Notes
- Keep UI updates subtle and professional
- Respect user's `prefers-reduced-motion` setting
- Make connection indicator small and unobtrusive

---

## Phase 5: Testing & Documentation ⏳

**Status:** Not Started  
**Estimated Duration:** 1-2 days  
**Dependencies:** Phase 4 complete

### Tasks

- [ ] **Task 5.1:** Unit tests
  - [ ] Create `src/services/__tests__/realtime-websocket.test.ts`
  - [ ] Test connection lifecycle
  - [ ] Test reconnection logic (exponential backoff)
  - [ ] Test event normalization
  - [ ] Test ping/pong handling
  - [ ] Test error handling (UNAUTHORIZED, RATE_LIMIT, etc.)
  - [ ] Aim for 80%+ code coverage
  
- [ ] **Task 5.2:** Integration tests
  - [ ] Mock WebSocket for testing
  - [ ] Test event flow through contexts
  - [ ] Test component updates on events
  - [ ] Test toast notifications
  - [ ] Test optimistic update handling
  
- [ ] **Task 5.3:** Manual testing
  - [ ] Test all connection flows
  - [ ] Test token expiration handling
  - [ ] Test network interruption recovery
  - [ ] Test in multiple browsers (Chrome, Firefox, Safari, Edge)
  - [ ] Test in multiple tabs (connection sharing)
  - [ ] Test with backend WebSocket API
  
- [ ] **Task 5.4:** Documentation
  - [ ] Create `docs/REALTIME_WEBSOCKET_IMPLEMENTATION.md`
  - [ ] Update `README.md` with WebSocket info
  - [ ] Document environment variables
  - [ ] Document usage patterns for developers
  - [ ] Create migration guide (SSE → WebSocket)
  - [ ] Update `docs/frontend-integration-guide.md`

### Acceptance Criteria
- ✅ 80%+ test coverage for WebSocket code
- ✅ All manual tests pass
- ✅ Documentation complete and accurate
- ✅ Migration guide available
- ✅ Works in all modern browsers

### Notes
- Use Jest and React Testing Library (already in project)
- Document common pitfalls and solutions
- Include troubleshooting section in docs

---

## Rollout & Deployment Plan ⏳

**Status:** Not Started  
**Dependencies:** Phase 5 complete

### Stages

- [ ] **Stage 1: Internal Testing**
  - [ ] Deploy to dev environment
  - [ ] Test with dev backend WebSocket API
  - [ ] Team testing (1-2 days)
  - [ ] Fix any issues found
  
- [ ] **Stage 2: Beta Rollout**
  - [ ] Enable feature flag for select users
  - [ ] Monitor error rates and performance
  - [ ] Collect user feedback
  - [ ] Duration: 1 week
  
- [ ] **Stage 3: Staged Rollout**
  - [ ] 10% of users
  - [ ] 25% of users
  - [ ] 50% of users
  - [ ] 100% of users
  - [ ] Monitor at each stage
  
- [ ] **Stage 4: Cleanup**
  - [ ] Remove old SSE code (`realtime.ts`)
  - [ ] Remove `REACT_APP_SSE_BASE_URL` env var
  - [ ] Remove mock SSE server
  - [ ] Update all documentation

---

## Known Issues & Blockers

### Current Blockers
- None (ready to begin implementation)

### Risks
1. **Backend WebSocket API not deployed**
   - Mitigation: Use mock server for development
   
2. **Token expiration edge cases**
   - Mitigation: Comprehensive testing with expired tokens
   
3. **High message volume performance**
   - Mitigation: Throttle/debounce UI updates if needed

### Questions for Backend Team
- [ ] Confirm WebSocket URL format
- [ ] Confirm ping/pong frequency
- [ ] Confirm message envelope format
- [ ] Confirm error codes
- [ ] Confirm event payload structure (snake_case vs camelCase)
- [ ] Confirm connection limits per tenant
- [ ] Confirm event history on reconnect (lastEventId support?)

---

## Resources & References

### Documentation
- [WebSocket Migration Analysis](./WEBSOCKET_MIGRATION_ANALYSIS.md) - Comprehensive analysis
- [Backend Integration Specs v2](./backend-integration-specs-v2.md) - API contracts
- [Design: Frontend Goals Module](./design-frontend-goals-module.md) - Goals module design

### Backend Specs
- Backend WebSocket implementation: Issue #56
- Backend API: `wss://api.{env}.purposepath.app/realtime`

### Frontend Files
- Current SSE: `src/services/realtime.ts`
- Auth Context: `src/contexts/AuthContext.tsx`
- Feature Flags: `src/contexts/FeaturesContext.tsx`
- Mock Server: `scripts/mock-sse-server.js`

---

## Change Log

### October 5, 2025
- **Analysis Phase Complete**: Created comprehensive WebSocket migration analysis
- **Architecture Decision**: Chose Global Context approach for state management
- **Progress Tracker Created**: This file created to track implementation progress
- **Status**: Ready to begin Phase 1 (WebSocket Connection Manager)

---

## How to Use This Tracker

### For AI Agents
1. **On session start**: Read this file to understand current progress
2. **Before work**: Check current phase and mark tasks as in-progress
3. **After completing tasks**: Update checkboxes and status
4. **When switching phases**: Update phase status and dates
5. **Add notes**: Document decisions, blockers, or important findings

### For Developers
1. **Track progress**: See what's complete and what's next
2. **Pick up work**: Know exactly where to start
3. **Report status**: Use this for standups and status reports
4. **Reference**: Link to relevant documentation and resources

### Updating This File
- Update checkboxes as tasks complete: `- [ ]` → `- [x]`
- Update phase status: `⏳ Not Started` → `🔄 In Progress` → `✅ Complete`
- Update progress percentages in overview table
- Add notes in relevant sections
- Update "Last Updated" date at top
- Add entries to Change Log

---

**Next Action:** Begin Phase 1 - Create WebSocket Connection Manager
