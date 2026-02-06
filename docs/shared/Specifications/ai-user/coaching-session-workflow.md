# Coaching Session Workflow

**Version:** 2.6  
**Last Updated:** February 5, 2026  
**Status:** Active

[← Back to Backend Integration](./backend-integration-unified-ai.md)

---

## Overview

This document describes the complete workflow for coaching conversation sessions, including state management, frontend decision logic, and backend behavior.

---

## Session States

### State Definitions

| State | Description | User Can Message? | Auto-Transitions? |
|-------|-------------|-------------------|-------------------|
| **ACTIVE** | Session is open and accepting messages | ✅ Yes | No (manual pause/complete/cancel only) |
| **PAUSED** | Session explicitly paused by user OR idle > 30 min | ❌ No | No |
| **COMPLETED** | Session finished with extracted results | ❌ No | No |
| **CANCELLED** | Session cancelled by user | ❌ No | No |
| **ABANDONED** | Session closed due to conflict or start-new | ❌ No | No |

### Idle vs Paused

- **Idle**: Computed property (`last_activity_at` > 30 minutes ago)
  - Session status remains **ACTIVE**
  - Does NOT block messages if chat window is open
  - Frontend treats as "paused" when reopening window
  
- **Paused**: Explicit status (`status = PAUSED`)
  - User clicked "Pause" button
  - Session idle when user closed window
  - BLOCKS messages until resumed

**Key Insight:** Idle is a UX concept, not a blocker. A user with an open chat window can message even after 2 hours idle.

---

## TTL (Time To Live)

All sessions have automatic cleanup via DynamoDB TTL:

- **Active/Paused sessions:** 14 days from last activity
- **Completed/Cancelled/Abandoned:** 14 days from terminal state

After TTL expires, DynamoDB auto-deletes the session. Next `/start` creates a fresh session.

---

## Frontend Workflow

### Scenario 1: Opening Coaching UI (Chat Window Closed)

```typescript
// User navigates to coaching page
async function initializeCoaching(topicId: string) {
  // 1. Check for existing session
  const check = await api.checkCoachingSession({ topicId });
  
  // 2. Handle conflicts first
  if (check.conflict) {
    showError(`${check.conflict_user_id} is currently using this topic`);
    disableCoachingUI();
    return;
  }
  
  // 3. Handle existing session
  if (check.has_session) {
    // status = "paused" if explicitly paused OR idle
    if (check.status === "paused") {
      const choice = await showDialog({
        title: "Existing Session Found",
        message: "You have an in-progress conversation. What would you like to do?",
        options: ["Resume Session", "Start New Session"]
      });
      
      if (choice === "Resume Session") {
        const response = await api.resumeCoachingSession({
          sessionId: check.session_id
        });
        openChatWindow(response.data);
      } else {
        // Start new - cancels old automatically
        const response = await api.startCoachingSession({ topicId });
        openChatWindow(response.data);
      }
    } else {
      // status = "active" and NOT idle - shouldn't happen, but resume anyway
      const response = await api.resumeCoachingSession({
        sessionId: check.session_id
      });
      openChatWindow(response.data);
    }
  } else {
    // No existing session - start fresh
    const response = await api.startCoachingSession({ topicId });
    openChatWindow(response.data);
  }
}
```

### Scenario 2: Active Conversation (Chat Window Open)

```typescript
// User types message and hits send
async function sendMessage(sessionId: string, message: string) {
  try {
    const response = await api.sendCoachingMessage({
      sessionId,
      message
    });
    
    // Check if conversation completed
    if (response.data.is_final) {
      showCompletionSummary(response.data.result);
      closeChatWindow();
    } else {
      displayMessage(response.data.message);
    }
    
  } catch (error) {
    if (error.code === "SESSION_NOT_ACTIVE") {
      // Session was paused (shouldn't happen in open window, but handle it)
      const choice = await showDialog({
        title: "Session Paused",
        message: "Your session was paused. Resume or start new?",
        options: ["Resume", "Start New"]
      });
      
      if (choice === "Resume") {
        await api.resumeCoachingSession({ sessionId });
      } else {
        await api.startCoachingSession({ topicId });
      }
    } else {
      showError(error.message);
    }
  }
}

// User clicks pause button
async function pauseSession(sessionId: string) {
  await api.pauseCoachingSession({ sessionId });
  closeChatWindow();
}

// User clicks complete button
async function completeSession(sessionId: string) {
  const response = await api.completeCoachingSession({ sessionId });
  showCompletionSummary(response.data.result);
  closeChatWindow();
}
```

---

## Backend Workflow

### Endpoint: GET /session/check

**Purpose:** Detect existing sessions and compute frontend-friendly status.

**Logic:**
```python
def check_session(topic_id, user_id, tenant_id):
    # Get user's session
    user_session = repo.get_active_for_user_topic(user_id, topic_id, tenant_id)
    
    # Get any tenant session (conflict detection)
    tenant_session = repo.get_active_by_tenant_topic(tenant_id, topic_id)
    
    if user_session:
        actual_status = user_session.status  # "active" or "paused"
        is_idle = user_session.is_idle()     # last_activity > 30 min
        
        # Compute status for frontend
        if actual_status == "paused" OR is_idle:
            computed_status = "paused"
        else:
            computed_status = "active"
    
    return {
        "has_session": user_session is not None,
        "session_id": user_session.session_id if user_session else None,
        "status": computed_status,          # "active" or "paused"
        "actual_status": actual_status,      # Raw DB value
        "is_idle": is_idle,                  # Boolean
        "conflict": tenant_session and tenant_session.user_id != user_id,
        "conflict_user_id": tenant_session.user_id if conflict else None
    }
```

### Endpoint: POST /start

**Purpose:** ALWAYS create a new session (cancels existing).

**Logic:**
```python
def start_session(topic_id, user_id, tenant_id, context):
    # Check for existing session
    existing = repo.get_active_for_user_topic(user_id, topic_id, tenant_id)
    
    if existing:
        # Cancel existing - user wants fresh start
        if existing.status == "active":
            existing.cancel()
        elif existing.status == "paused":
            existing.mark_abandoned()
        repo.update(existing)
    
    # Create new session
    session = CoachingSession(
        topic_id=topic_id,
        user_id=user_id,
        tenant_id=tenant_id,
        status="active",
        context=context,
        ttl=now() + 14 days
    )
    
    # Load INITIATION template
    initiation_template = load_template(topic_id, "INITIATION")
    system_template = load_template(topic_id, "SYSTEM")
    
    # Generate first message
    llm_response = call_llm([
        {"role": "system", "content": render(system_template, context)},
        {"role": "user", "content": render(initiation_template, context)}
    ])
    
    session.add_assistant_message(llm_response)
    repo.create(session)
    
    return SessionResponse(
        session_id=session.session_id,
        message=llm_response,
        status="active",
        resumed=False  # Fresh start
    )
```

### Endpoint: POST /resume

**Purpose:** Continue existing session with RESUME template.

**Logic:**
```python
def resume_session(session_id, user_id, tenant_id):
    # Load session
    session = repo.get_by_id_for_tenant(session_id, tenant_id)
    
    # Validate ownership
    if session.user_id != user_id:
        raise SessionAccessDeniedError
    
    # Load RESUME template
    resume_template = load_template(session.topic_id, "RESUME")
    system_template = load_template(session.topic_id, "SYSTEM")
    
    # Build context with summary
    context = {
        **session.context,
        "conversation_summary": summarize_conversation(session.messages),
        "current_turn": session.get_turn_count(),
        "max_turns": session.max_turns
    }
    
    # Get conversation history
    history = session.get_messages_for_llm(max_messages=20)
    
    # Generate welcome back message
    llm_response = call_llm([
        {"role": "system", "content": render(system_template, session.context)},
        *history,
        {"role": "user", "content": render(resume_template, context)}
    ])
    
    # Resume if paused
    if session.status == "paused":
        session.resume()  # Changes status to "active"
    
    session.add_assistant_message(llm_response)
    repo.update(session)
    
    return SessionResponse(
        session_id=session.session_id,
        message=llm_response,
        status="active",
        resumed=True  # Continued session
    )
```

### Endpoint: POST /message

**Purpose:** Send user message in active session.

**Logic:**
```python
def send_message(session_id, user_id, tenant_id, user_message):
    # Load session
    session = repo.get_by_id_for_tenant(session_id, tenant_id)
    
    # Validate ownership
    if session.user_id != user_id:
        raise SessionAccessDeniedError
    
    # Check status (NO idle check - allow messages if window open)
    if session.status != "active":
        raise SessionNotActiveError  # Only blocks if explicitly PAUSED
    
    # Add user message
    session.add_user_message(user_message)
    
    # Generate response
    system_template = load_template(session.topic_id, "SYSTEM")
    history = session.get_messages_for_llm(max_messages=30)
    
    llm_response = call_llm([
        {"role": "system", "content": render(system_template, session.context)},
        *history
    ])
    
    # Check if LLM signaled completion
    is_final = check_completion_signal(llm_response)
    
    if is_final:
        # Extract results
        result = extract_results(session, llm_response)
        session.complete(result)
        repo.update(session)
        
        return MessageResponse(
            message=llm_response,
            status="completed",
            is_final=True,
            result=result
        )
    else:
        session.add_assistant_message(llm_response)
        repo.update(session)
        
        return MessageResponse(
            message=llm_response,
            status="active",
            is_final=False
        )
```

### Endpoint: POST /pause

**Purpose:** Explicitly pause session.

**Logic:**
```python
def pause_session(session_id, user_id, tenant_id):
    session = repo.get_by_id_for_tenant(session_id, tenant_id)
    
    if session.user_id != user_id:
        raise SessionAccessDeniedError
    
    session.pause()  # Changes status to "paused"
    repo.update(session)
    
    return SessionStateResponse(
        session_id=session.session_id,
        status="paused"
    )
```

---

## Complete User Journey Examples

### Example 1: Normal Flow (No Interruptions)

```
1. User opens coaching UI
   → GET /session/check → has_session=false
   → Frontend shows "Start Session"
   
2. User clicks "Start Session"
   → POST /start → Creates session with INITIATION template
   → Frontend opens chat window
   
3. User chats with AI for 20 minutes
   → POST /message (multiple times)
   → Status remains "active"
   
4. LLM signals conversation complete
   → POST /message → is_final=true, result extracted
   → Frontend shows summary, closes chat
   
5. Session TTL: 14 days until auto-delete
```

### Example 2: User Steps Away (Idle)

```
1. User starts session, chats for 10 minutes
   → POST /start
   → POST /message (several times)
   
2. User steps away (leaves chat window open)
   → 45 minutes pass (> 30 min idle threshold)
   → Status still "active" in DB
   → No auto-pause
   
3. User returns, types message (window still open)
   → POST /message → SUCCESS (no idle check)
   → Conversation continues normally
```

### Example 3: User Closes Window, Returns Later

```
1. User starts session, chats for 10 minutes
   → POST /start
   → POST /message (several times)
   
2. User closes browser (or navigates away)
   → 2 hours pass
   → Status still "active" in DB
   
3. User returns, reopens coaching UI
   → GET /session/check
   → has_session=true, status="paused" (because is_idle=true)
   
4. Frontend shows "Resume or Start New?"
   
5. User clicks "Resume"
   → POST /resume → Uses RESUME template
   → Welcome back message with summary
   → Status changed to "active"
   
6. User continues conversation
   → POST /message
```

### Example 4: User Explicitly Pauses

```
1. User starts session, chats for 10 minutes
   → POST /start
   → POST /message (several times)
   
2. User clicks "Pause" button
   → POST /pause
   → Status = "paused" (explicit)
   → Frontend closes chat window
   
3. User tries to send message (shouldn't happen, but...)
   → POST /message
   → ERROR: SESSION_NOT_ACTIVE (400)
   
4. User returns 3 days later
   → GET /session/check
   → has_session=true, status="paused"
   
5. User clicks "Resume"
   → POST /resume
   → Conversation continues
```

### Example 5: User Wants Fresh Start

```
1. User has existing session (paused, 5 days old)
   → GET /session/check
   → has_session=true, status="paused"
   
2. Frontend shows "Resume or Start New?"
   
3. User clicks "Start New"
   → POST /start
   → Backend cancels old session
   → Creates new session with INITIATION template
   → Fresh conversation begins
```

### Example 6: Multi-User Conflict

```
1. User A starts session for "core_values" topic
   → POST /start
   → Session created for tenant + topic
   
2. User B (same tenant) opens coaching UI
   → GET /session/check?topic_id=core_values
   → has_session=false (User B has no session)
   → conflict=true, conflict_user_id="user_a"
   
3. Frontend shows:
   "Another user (User A) is currently using this topic. Please wait."
   → Coaching UI disabled for User B
   
4. User A completes session
   → POST /complete
   → Session status = "completed"
   
5. User B refreshes
   → GET /session/check
   → conflict=false (User A's session no longer active)
   → User B can now start
```

---

## State Transition Diagram

```
                    POST /start
                    (new session)
                         ↓
                    ┌─────────┐
          ┌────────→│ ACTIVE  │←────────┐
          │         └─────────┘         │
          │              │               │
          │              │ POST /pause   │
          │              ↓               │
POST /resume        ┌─────────┐    (auto on resume)
(welcome back)      │ PAUSED  │         │
          │         └─────────┘         │
          └──────────────┘               │
                                         │
From ACTIVE:                             │
  - POST /complete → COMPLETED          │
  - POST /cancel → CANCELLED            │
  - POST /start (new) → ABANDONED       │
  - TTL expires (14 days) → DELETED     │
```

---

## Summary

**Key Principles:**
1. **Start = Always New** - Cancels existing, uses INITIATION template
2. **Resume = Continue** - Uses RESUME template with summary
3. **Idle ≠ Error** - Open chat windows can message even after hours idle
4. **Frontend Decides** - `/session/check` provides info, frontend controls UX
5. **TTL Cleanup** - All sessions auto-delete after 14 days
6. **Explicit Pauses** - Only explicit PAUSED status blocks messages

**Workflow Checklist:**
- [ ] Frontend calls `/session/check` before showing UI
- [ ] Frontend shows "Resume or Start New?" for paused sessions
- [ ] Frontend blocks UI if conflict detected
- [ ] `/start` always creates fresh session (cancels existing)
- [ ] `/resume` continues with welcome-back message
- [ ] `/message` works in active sessions (no idle check)
- [ ] Explicit `/pause` blocks future messages until resumed
- [ ] TTL handles long-term cleanup automatically
