# Example: Document Update in Action

**Purpose:** Concrete example of how documents get updated during implementation

---

## Scenario: Implementing Task 1.1 - Create WebSocket Connection Manager

### Initial State (Before Task)

**Progress Tracker Status:**
```markdown
## Phase 1: WebSocket Connection Manager ⏳

**Status:** Not Started
**Estimated Duration:** 2-3 days

### Tasks

- [ ] **Task 1.1:** Create `src/services/realtime-websocket.ts`
  - [ ] Implement `RealtimeWebSocket` class
  - [ ] Connection lifecycle
  ...
```

**Session Todo List:**
```
No todo list found.
```

---

## Step 1: Session Start - Create Todo List

### AI Agent Action:
```typescript
manage_todo_list({
  operation: "write",
  todoList: [
    {
      id: 1,
      title: "Create WebSocket connection manager",
      description: "Implement src/services/realtime-websocket.ts with full lifecycle management",
      status: "in-progress"
    },
    {
      id: 2,
      title: "Create TypeScript types",
      description: "Define all event payload types in src/types/realtime.ts",
      status: "not-started"
    },
    {
      id: 3,
      title: "Update environment config",
      description: "Add REACT_APP_REALTIME_WS_URL to env.example",
      status: "not-started"
    }
  ]
});
```

### AI Response to User:
```markdown
Starting Phase 1: WebSocket Connection Manager

📋 **Session Plan:**
1. ⏳ Create WebSocket connection manager (in progress)
2. ⏹️ Create TypeScript types
3. ⏹️ Update environment config

**Current Status:** Phase 1, Task 1.1
**Overall Progress:** 16% (Phase 0 complete)

Let's begin by creating the WebSocket connection manager...
```

---

## Step 2: Implement the Task

### AI Agent Actions:
```typescript
// 1. Create the file
create_file({
  filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\src\\services\\realtime-websocket.ts",
  content: `
export type ConnectionStatus = 
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

export class RealtimeWebSocket {
  // ... full implementation
}
`
});

// 2. Immediately update progress tracker (mandatory!)
multi_replace_string_in_file({
  explanation: "Update progress tracker after completing Task 1.1",
  replacements: [
    {
      explanation: "Mark Task 1.1 complete",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `- [ ] **Task 1.1:** Create \`src/services/realtime-websocket.ts\`
  - [ ] Implement \`RealtimeWebSocket\` class
  - [ ] Connection lifecycle (connect, disconnect, reconnect)
  - [ ] Exponential backoff with jitter
  - [ ] Ping/pong heartbeat handling
  - [ ] Connection state management
  - [ ] Event emitter pattern`,
      newString: `- [x] **Task 1.1:** Create \`src/services/realtime-websocket.ts\` ✅ **Completed:** Oct 5, 2025 15:30
  - [x] Implement \`RealtimeWebSocket\` class
  - [x] Connection lifecycle (connect, disconnect, reconnect)
  - [x] Exponential backoff with jitter
  - [x] Ping/pong heartbeat handling
  - [x] Connection state management
  - [x] Event emitter pattern
  
  **Notes:** Implemented full lifecycle with exponential backoff (1s → 30s max), ping/pong heartbeat every 30s, and UNAUTHORIZED error handling for token refresh.`
    },
    {
      explanation: "Update phase status from Not Started to In Progress",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `## Phase 1: WebSocket Connection Manager ⏳

**Status:** Not Started  
**Estimated Duration:** 2-3 days`,
      newString: `## Phase 1: WebSocket Connection Manager 🔄

**Status:** In Progress (20% complete - 1/5 subtasks)  
**Started:** October 5, 2025 15:00  
**Estimated Duration:** 2-3 days`
    },
    {
      explanation: "Update overall progress in status table",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `| 0. Analysis & Planning | ✅ Complete | 100% | Oct 5, 2025 | Oct 5, 2025 |
| 1. WebSocket Connection Manager | ⏳ Not Started | 0% | - | - |`,
      newString: `| 0. Analysis & Planning | ✅ Complete | 100% | Oct 5, 2025 | Oct 5, 2025 |
| 1. WebSocket Connection Manager | 🔄 In Progress | 20% | Oct 5, 2025 | - |`
    },
    {
      explanation: "Update overall progress percentage",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `**Overall Progress:** 16% (1/6 phases complete)`,
      newString: `**Overall Progress:** 20% (1 phase + 20% of phase 1)`
    },
    {
      explanation: "Update Last Updated timestamp",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `**Last Updated:** October 5, 2025`,
      newString: `**Last Updated:** October 5, 2025 at 15:30`
    },
    {
      explanation: "Add change log entry",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `## Change Log

### October 5, 2025
- **Analysis Phase Complete**: Created comprehensive WebSocket migration analysis`,
      newString: `## Change Log

### October 5, 2025

**15:30** - Task 1.1 Complete
- ✅ Created \`src/services/realtime-websocket.ts\` (450 lines)
- Implemented \`RealtimeWebSocket\` class with full lifecycle management
- Features: Connection management, exponential backoff (1s-30s), ping/pong heartbeat, UNAUTHORIZED handling
- Phase 1 now 20% complete (1/5 subtasks)

**14:00** - Phase 1 Started
- Began WebSocket Connection Manager implementation
- Created session plan with 5 subtasks

**13:00** - Analysis Phase Complete
- Created comprehensive WebSocket migration analysis`
    }
  ]
});

// 3. Update session todo list
manage_todo_list({
  operation: "write",
  todoList: [
    {
      id: 1,
      title: "Create WebSocket connection manager",
      description: "Implement src/services/realtime-websocket.ts with full lifecycle management",
      status: "completed"
    },
    {
      id: 2,
      title: "Create TypeScript types",
      description: "Define all event payload types in src/types/realtime.ts",
      status: "in-progress"
    },
    {
      id: 3,
      title: "Update environment config",
      description: "Add REACT_APP_REALTIME_WS_URL to env.example",
      status: "not-started"
    }
  ]
});
```

### AI Response to User:
```markdown
✅ **Task 1.1 Complete** - WebSocket Connection Manager Created

**File Created:**
- `src/services/realtime-websocket.ts` (450 lines)

**Features Implemented:**
- ✅ Connection lifecycle management (connect, disconnect, reconnect)
- ✅ Exponential backoff with jitter (1s → 2s → 4s → 8s → 16s → 30s max)
- ✅ Ping/pong heartbeat (every 30 seconds)
- ✅ UNAUTHORIZED error detection and token refresh integration
- ✅ Event emitter pattern for message handling
- ✅ Connection state management with status callbacks

**Progress Updated:**
- ✅ Progress tracker updated (Task 1.1 checkbox marked)
- ✅ Phase 1 status changed to "In Progress (20%)"
- ✅ Overall progress updated to 20%
- ✅ Change log entry added with timestamp
- ✅ Session todo list updated

**Phase 1 Progress:** 20% complete (1/5 subtasks)
**Overall Progress:** 20%

**Next:** Task 1.2 - Create TypeScript types (marked in-progress)

---

Would you like me to continue with Task 1.2, or would you like to review the WebSocket implementation first?
```

---

## Step 3: Continue to Next Task (Task 1.2)

### User Response:
```
Continue with Task 1.2
```

### AI Agent Actions:
```typescript
// 1. Create the types file
create_file({
  filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\src\\types\\realtime.ts",
  content: `
// WebSocket message envelope
export interface WebSocketMessage<T = any> {
  type: string;
  timestamp: string;
  data: T;
}

// Connection status
export type ConnectionStatus = 
  | 'disconnected'
  | 'connecting'
  | 'connected'
  | 'reconnecting'
  | 'error';

// Goal events
export interface GoalCreatedEvent {
  goalId: string;
  tenantId: string;
  title: string;
  ownerId: string;
  horizon: string;
  status: 'draft' | 'active' | 'completed' | 'paused' | 'cancelled';
  valueTags?: string[];
  createdAt: string;
}

// ... all other event types
`
});

// 2. Update progress tracker
multi_replace_string_in_file({
  explanation: "Update progress tracker after completing Task 1.2",
  replacements: [
    {
      explanation: "Mark Task 1.2 complete",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `- [ ] **Task 1.2:** Create \`src/types/realtime.ts\`
  - [ ] \`ConnectionStatus\` type
  - [ ] \`WebSocketMessage<T>\` interface
  - [ ] All event payload types (goals, actions, KPIs, issues)
  - [ ] Event handler types`,
      newString: `- [x] **Task 1.2:** Create \`src/types/realtime.ts\` ✅ **Completed:** Oct 5, 2025 16:00
  - [x] \`ConnectionStatus\` type
  - [x] \`WebSocketMessage<T>\` interface
  - [x] All event payload types (goals, actions, KPIs, issues)
  - [x] Event handler types
  
  **Notes:** Defined 15+ event types covering all backend events. Used TypeScript discriminated unions for type safety.`
    },
    {
      explanation: "Update phase progress",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `**Status:** In Progress (20% complete - 1/5 subtasks)`,
      newString: `**Status:** In Progress (40% complete - 2/5 subtasks)`
    },
    {
      explanation: "Update overall progress table",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `| 1. WebSocket Connection Manager | 🔄 In Progress | 20% | Oct 5, 2025 | - |`,
      newString: `| 1. WebSocket Connection Manager | 🔄 In Progress | 40% | Oct 5, 2025 | - |`
    },
    {
      explanation: "Update overall progress",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `**Overall Progress:** 20% (1 phase + 20% of phase 1)`,
      newString: `**Overall Progress:** 23% (1 phase + 40% of phase 1)`
    },
    {
      explanation: "Add change log entry",
      filePath: "c:\\Projects\\XBS\\PurposePath\\PurposePath_Web\\docs\\WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
      oldString: `### October 5, 2025

**15:30** - Task 1.1 Complete`,
      newString: `### October 5, 2025

**16:00** - Task 1.2 Complete
- ✅ Created \`src/types/realtime.ts\` (250 lines)
- Defined 15+ event payload types using TypeScript discriminated unions
- Covers: Goal, Action, KPI, Issue, Decision, Attachment, System events
- Full type safety for WebSocket message handling
- Phase 1 now 40% complete (2/5 subtasks)

**15:30** - Task 1.1 Complete`
    }
  ]
});

// 3. Update session todo list
manage_todo_list({
  operation: "write",
  todoList: [
    {
      id: 1,
      title: "Create WebSocket connection manager",
      description: "Implement src/services/realtime-websocket.ts with full lifecycle management",
      status: "completed"
    },
    {
      id: 2,
      title: "Create TypeScript types",
      description: "Define all event payload types in src/types/realtime.ts",
      status: "completed"
    },
    {
      id: 3,
      title: "Update environment config",
      description: "Add REACT_APP_REALTIME_WS_URL to env.example",
      status: "in-progress"
    }
  ]
});
```

---

## Pattern: The Update Loop

**Every time a task completes, this exact sequence happens:**

```
1. Complete the implementation (create/edit files)
2. IMMEDIATELY update progress tracker:
   - Mark checkbox complete
   - Update phase progress %
   - Update overall progress %
   - Add change log entry
   - Update timestamp
3. Update session todo list
4. Inform user with updated progress
5. Move to next task
```

**This ensures:**
- ✅ Documents always in sync
- ✅ Progress always accurate
- ✅ Session recovery always possible
- ✅ User always informed
- ✅ History captured in change log

---

## Verification: End of Session

### AI Agent Final Actions:

```typescript
// Check all documents are updated
const progressDoc = await read_file("docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md");
const sessionRecovery = await read_file("docs/WEBSOCKET_SESSION_RECOVERY.md");

// Verify phase progress
// Expected: Phase 1 at 40% (2/5 tasks complete)
// Expected: Overall at 23%

// Update session recovery doc with current state
replace_string_in_file({
  filePath: "docs/WEBSOCKET_SESSION_RECOVERY.md",
  oldString: `**Phase:** 0 - Analysis & Planning ✅ **COMPLETE**  
**Next Phase:** 1 - WebSocket Connection Manager (Not Started)  
**Overall Progress:** 16% (1/6 phases)`,
  newString: `**Phase:** 1 - WebSocket Connection Manager 🔄 **IN PROGRESS** (40%)  
**Next Task:** 1.3 - Update environment configuration  
**Overall Progress:** 23%`
});
```

### AI Response to User:

```markdown
## Session Summary

**Work Completed:**
1. ✅ Task 1.1 - WebSocket Connection Manager (450 lines)
2. ✅ Task 1.2 - TypeScript Types (250 lines)

**Files Created:**
- `src/services/realtime-websocket.ts`
- `src/types/realtime.ts`

**Progress:**
- Phase 1: 40% complete (2/5 tasks)
- Overall: 23% complete

**Documents Updated:**
- ✅ Progress tracker (2 tasks checked, phase %, change log)
- ✅ Session recovery (current state updated)
- ✅ Session todo list (all current)

**Next Session:**
- Continue with Task 1.3: Update environment configuration
- Then Task 1.4: Token refresh integration
- Then Task 1.5: Manual testing

**Resume Command:**
Read `docs/WEBSOCKET_SESSION_RECOVERY.md` to pick up exactly where we left off.

All progress tracked and saved! 🎯
```

---

## Key Takeaway

**Every single task completion triggers a mandatory document update sequence.**

This ensures that if the chat session ends at ANY point, the next session can:
1. Read the progress docs
2. See exactly what's done (checkboxes)
3. See exactly what's next
4. Continue seamlessly

**No progress is ever lost!** 🔒
