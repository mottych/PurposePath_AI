# WebSocket Implementation - Update Protocol

**Purpose:** Ensure documents and progress tracking stay synchronized during implementation

---

## Mandatory Update Workflow

### 🔄 Before Starting Any Task

1. **Read current progress**
   ```
   Read: docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md
   Find: Current phase and next incomplete task
   ```

2. **Create session todo list**
   ```
   Use: manage_todo_list tool
   Add: Tasks planned for this session
   Status: Mark first task as "in-progress"
   ```

3. **Mark task in-progress in progress tracker**
   ```
   Update: docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md
   Change: - [ ] Task X.Y → - [ ] Task X.Y ⏳ IN PROGRESS
   Add note: "Started: [Date] [Time]"
   ```

### ✅ After Completing Any Task

1. **Update session todo list**
   ```
   Use: manage_todo_list tool
   Mark: Current task as "completed"
   Mark: Next task as "in-progress" (if continuing)
   ```

2. **Update progress tracker immediately**
   ```
   Update: docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md
   Change: - [ ] Task X.Y ⏳ → - [x] Task X.Y ✅
   Add note: "Completed: [Date] [Time]"
   Document: Any decisions, blockers, or deviations
   ```

3. **Update phase progress**
   ```
   Calculate: % complete for phase (completed tasks / total tasks)
   Update: Phase status and progress percentage
   Update: "Last Updated" date at top of document
   ```

4. **Add change log entry**
   ```
   Add entry to "Change Log" section:
   "### [Date]
   - **Task X.Y Complete**: [Brief description]
   - **Files Created/Updated**: [List files]
   - **Notes**: [Any important notes]"
   ```

### 🎯 After Completing a Phase

1. **Update progress tracker**
   ```
   Change phase status: ⏳ Not Started → 🔄 In Progress → ✅ Complete
   Add completion date
   Update overall progress percentage
   Calculate total time spent
   ```

2. **Update session recovery document**
   ```
   Update: docs/WEBSOCKET_SESSION_RECOVERY.md
   Change: "Current Phase" and "Next Phase"
   Update: "Overall Progress" percentage
   Update: "Last Updated" date
   ```

3. **Create phase completion summary**
   ```
   Add to change log:
   "### Phase X Complete - [Date]
   - **Duration**: [X days/hours]
   - **Deliverables**: [List files created]
   - **Tests Added**: [List test files]
   - **Issues Encountered**: [List any issues]
   - **Next Phase**: Phase X+1 - [Name]"
   ```

### 📝 Continuous Documentation Updates

**When creating new files:**
```
1. Update progress tracker task checkbox
2. Add file path to "Files Created" in change log
3. Add brief description of file purpose
4. Update relevant section in analysis document if architecture changes
```

**When making architectural decisions:**
```
1. Add note to current task in progress tracker
2. Add entry to "Architectural Decisions" section (if exists)
3. Update session recovery doc if it affects quick reference
4. Document reasoning and alternatives considered
```

**When encountering blockers:**
```
1. Add to "Known Issues & Blockers" section
2. Mark task with blocker emoji: - [ ] Task X.Y ⚠️ BLOCKED
3. Document blocker details and mitigation plan
4. Update status in session todo list
```

---

## Automated Reminder Checklist

Use this checklist at key points during implementation:

### Start of Work Session
```
□ Read WEBSOCKET_IMPLEMENTATION_PROGRESS.md
□ Read WEBSOCKET_SESSION_RECOVERY.md (if new session)
□ Create session todo list with manage_todo_list
□ Mark first task as in-progress in progress tracker
□ Verify Last Updated date is current
```

### After Each Task Completion
```
□ Update session todo list (mark complete)
□ Update progress tracker checkbox (- [x])
□ Add completion note with date/time
□ Document any decisions or issues encountered
□ Update phase progress percentage
□ Add change log entry
□ Commit changes to git (if applicable)
```

### End of Work Session
```
□ Update all todo lists (session and progress tracker)
□ Mark in-progress tasks appropriately
□ Add session summary to change log
□ Update "Last Updated" date
□ Save all documents
□ Commit changes to git
```

### After Phase Completion
```
□ Update phase status to ✅ Complete
□ Add phase completion date
□ Calculate and update overall progress %
□ Create phase completion summary in change log
□ Update session recovery document
□ Review and update analysis doc if needed
□ Plan next phase kickoff
```

---

## Document Synchronization Matrix

This matrix shows which documents need updating for each type of change:

| Change Type | Progress Tracker | Session Recovery | Analysis Doc | Change Log |
|-------------|-----------------|------------------|--------------|------------|
| Task started | ✅ Mark in-progress | ❌ | ❌ | ❌ |
| Task complete | ✅ Check box | ❌ | ❌ | ✅ Add entry |
| File created | ✅ Note in task | ❌ | ❌ | ✅ List file |
| Phase complete | ✅ Update status | ✅ Update phase | ❌ | ✅ Summary |
| Architecture change | ✅ Add note | ✅ If major | ✅ Update spec | ✅ Document |
| Blocker encountered | ✅ Mark blocked | ❌ | ❌ | ✅ Add to blockers |
| Decision made | ✅ Add note | ✅ If key decision | ✅ If affects design | ✅ Document reasoning |
| Overall progress | ✅ Update % | ✅ Update % | ❌ | ❌ |

---

## AI Agent Self-Check Protocol

As an AI agent, I will follow this self-check protocol:

### Before Each Response Involving Implementation

1. **Check if task is complete in response**
   - If YES → Update progress tracker BEFORE responding to user
   - If NO → Note what will be done, update after completion

2. **Verify documents are in sync**
   - Read current progress tracker status
   - Verify it matches actual work done
   - If out of sync → Update immediately

3. **Plan updates needed**
   - Identify which documents need updates
   - Use multi_replace_string_in_file for efficiency
   - Update all relevant sections in one operation

### After Each Implementation Step

1. **Mandatory progress update**
   ```typescript
   // After creating file or completing task
   await updateProgressTracker({
     taskId: "1.2",
     status: "complete",
     note: "Created realtime-websocket.ts with full implementation"
   });
   ```

2. **Verify update success**
   - Check that checkbox changed
   - Verify note was added
   - Confirm date updated

3. **Document in response**
   - Tell user what was updated
   - Show updated progress
   - Highlight remaining tasks

### Session Start Protocol

1. **Read progress documents**
   - WEBSOCKET_SESSION_RECOVERY.md (quick context)
   - WEBSOCKET_IMPLEMENTATION_PROGRESS.md (detailed status)

2. **Create session plan**
   - Use manage_todo_list tool
   - List tasks planned for session
   - Mark first task in-progress

3. **Inform user of status**
   - Show current phase and progress
   - Highlight next tasks
   - Ask for confirmation to proceed

---

## Example Update Workflow

### Scenario: Completing Task 1.1 (Create realtime-websocket.ts)

**Step 1: Complete the work**
```typescript
// Create the file with implementation
create_file({
  filePath: "src/services/realtime-websocket.ts",
  content: "/* WebSocket implementation */"
});
```

**Step 2: Update progress tracker (REQUIRED)**
```typescript
multi_replace_string_in_file({
  filePath: "docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md",
  replacements: [
    {
      // Update task checkbox
      oldString: "- [ ] **Task 1.1:** Create `src/services/realtime-websocket.ts`",
      newString: "- [x] **Task 1.1:** Create `src/services/realtime-websocket.ts` ✅ Completed: Oct 5, 2025 14:30"
    },
    {
      // Update Last Updated date
      oldString: "**Last Updated:** October 5, 2025",
      newString: "**Last Updated:** October 5, 2025 14:30"
    },
    {
      // Add change log entry
      oldString: "## Change Log\n\n### October 5, 2025",
      newString: "## Change Log\n\n### October 5, 2025\n- **Task 1.1 Complete**: Created WebSocket connection manager\n- **Files Created**: `src/services/realtime-websocket.ts`\n- **Notes**: Implemented full lifecycle management with reconnection"
    }
  ]
});
```

**Step 3: Update session todo list**
```typescript
manage_todo_list({
  operation: "write",
  todoList: [
    { id: 1, title: "Create WebSocket manager", status: "completed" },
    { id: 2, title: "Create TypeScript types", status: "in-progress" },
    { id: 3, title: "Update env config", status: "not-started" }
  ]
});
```

**Step 4: Inform user**
```markdown
✅ **Task 1.1 Complete**: Created `src/services/realtime-websocket.ts`

**Progress Updated:**
- Progress tracker checkbox marked complete
- Change log entry added
- Session todo list updated

**Phase 1 Progress:** 20% (1/5 subtasks complete)
**Overall Progress:** 18% (phase 0 + 20% of phase 1)

**Next:** Task 1.2 - Create TypeScript types (in progress)
```

---

## Validation Checks

Before marking a phase complete, verify:

```
□ All task checkboxes marked complete
□ Phase status updated to ✅ Complete
□ Completion date added
□ Phase progress = 100%
□ Overall progress % updated
□ Change log has phase completion entry
□ Session recovery doc updated
□ All files mentioned in tasks exist
□ All tests mentioned pass
□ Documentation updated
```

---

## Recovery from Missed Updates

If documents fall out of sync:

1. **Detect the issue**
   - Compare actual files created vs. progress tracker
   - Check for tasks marked complete but files don't exist
   - Look for completed work not reflected in tracker

2. **Reconcile immediately**
   - Create reconciliation change log entry
   - Update all missed checkboxes at once
   - Add note explaining the gap
   - Verify current state is accurate

3. **Prevent recurrence**
   - Follow mandatory update workflow strictly
   - Use multi_replace for batch updates
   - Always update before responding to user

---

## Tools for Updates

### Use These Tools Consistently

1. **manage_todo_list** - Session-level tracking
   ```typescript
   // Start of session
   manage_todo_list({ operation: "write", todoList: [...] });
   
   // After each task
   manage_todo_list({ operation: "write", todoList: [...] }); // Updated status
   ```

2. **multi_replace_string_in_file** - Batch document updates
   ```typescript
   // Update multiple sections at once
   multi_replace_string_in_file({
     explanation: "Update progress tracker after completing task 1.1",
     replacements: [
       { filePath, oldString, newString, explanation },
       { filePath, oldString, newString, explanation },
       // ... more updates
     ]
   });
   ```

3. **replace_string_in_file** - Single section updates
   ```typescript
   // For simple updates
   replace_string_in_file({ filePath, oldString, newString });
   ```

---

## Success Metrics

Progress tracking is successful when:

- ✅ Documents always reflect current state
- ✅ No tasks marked complete without evidence (files, commits)
- ✅ Change log has entry for every significant change
- ✅ Session recovery doc always accurate for quick restart
- ✅ Phase progress percentages accurate
- ✅ User can see progress at a glance
- ✅ Another AI agent can resume work seamlessly

---

## Quick Reference Commands

```bash
# Check current progress
cat docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md | grep "Overall Progress"

# Check current phase
cat docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md | grep "Status:" | head -6

# Check incomplete tasks
cat docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md | grep "\- \[ \]"

# Check last updated
cat docs/WEBSOCKET_IMPLEMENTATION_PROGRESS.md | grep "Last Updated"
```

---

## Commit Message Templates

When committing progress updates:

```bash
# After task completion
git commit -m "feat: Complete task X.Y - [brief description]

- Created/Updated: [files]
- Progress: Phase X now Y% complete
- Updated: Progress tracker and change log"

# After phase completion
git commit -m "feat: Complete Phase X - [phase name]

- All tasks complete
- Deliverables: [list files]
- Progress: Overall XX% complete
- Next: Phase X+1"

# Progress tracking update only
git commit -m "docs: Update progress tracker

- Mark task X.Y complete
- Update phase progress to Y%
- Add change log entry"
```

---

**Remember:** Progress tracking is not optional—it's mandatory for successful implementation and seamless session recovery!
