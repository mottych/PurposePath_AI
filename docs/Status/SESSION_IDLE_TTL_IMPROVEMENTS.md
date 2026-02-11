# Session Idle & TTL Management Improvements

**Date:** 2026-02-05  
**Branch:** `fix/session-idle-ttl-improvements`  
**Status:** ✅ Completed & Tested

## Overview

Improved session management to align with real-world usage patterns:
- **Idle sessions are resumable** (not abandoned) - Users may step away, have power outages, etc.
- **TTL-based cleanup** for truly abandoned sessions (30 days for active/paused)
- **New endpoint** for frontend to check session existence and conflicts

---

## Problems Fixed

### 1. **Aggressive Idle Handling** ❌ Old Behavior
```python
# OLD: Session closed after 30 minutes idle
if existing.is_idle():  # After 30 minutes
    if existing.is_active():
        existing.complete(result={})  # ❌ Lost!
    elif existing.is_paused():
        existing.mark_abandoned()     # ❌ Lost!
```

**Impact:** Users lost sessions if they:
- Stepped away for coffee (30+ min)
- Had power outages
- Closed laptop overnight
- Had intermittent connectivity

### 2. **No Session Detection for Frontend** ❌ Old Behavior
- Frontend had to call `/start` blindly (no way to know if session exists)
- No conflict detection before attempting to start
- Had to use expensive `/sessions` list to check

### 3. **TTL Only for Terminal States** ❌ Old Behavior
- Active/Paused sessions: **NO TTL** (kept forever!)
- Only COMPLETED/CANCELLED/ABANDONED: 14-day TTL

---

## Solutions Implemented

### 1. **Idle = Resumable** ✅ New Behavior

```python
# NEW: Always resume existing sessions
if existing is not None:
    # Resume regardless of idle status
    # TTL handles cleanup of truly abandoned sessions
    return await self._resume_session(...)
```

**Changes:**
- Removed idle check from `get_or_create_session` (service layer)
- Removed idle check from `_load_and_validate_session` (service layer)
- Removed idle check from `add_message` (domain entity)

**Files Modified:**
- `coaching/src/services/coaching_session_service.py`
- `coaching/src/domain/entities/coaching_session.py`

### 2. **Extended TTL for Active/Paused Sessions** ✅ New Behavior

```python
# NEW: TTL for all session states
COMPLETED_SESSION_TTL_DAYS = 14   # Terminal states (short cleanup)
ACTIVE_SESSION_TTL_DAYS = 30      # Active/Paused (longer for flexibility)

# Applied on both create() and save()
if session.status in (ConversationStatus.ACTIVE, ConversationStatus.PAUSED):
    ttl_timestamp = now + (30 days)
    item["ttl"] = ttl_timestamp
```

**DynamoDB Auto-Cleanup:**
- Active/Paused: **30 days** (user flexibility for power outages, travel, etc.)
- Completed/Cancelled/Abandoned: **14 days** (faster cleanup)

**Files Modified:**
- `coaching/src/infrastructure/repositories/dynamodb_coaching_session_repository.py`

### 3. **New Session Check Endpoint** ✅ New Feature

```http
GET /api/v1/coaching/session/check?topic_id={topic_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "has_session": true,
    "session_id": "sess_xxx",
    "status": "paused",
    "conflict": false,
    "conflict_user_id": null
  }
}
```

**Use Cases:**
- Frontend can check for existing sessions before showing "Start Session" button
- Detect if another user from same tenant has active session (conflict)
- Show appropriate UI: "Resume Session" vs "Start New Session"

**Files Modified:**
- `coaching/src/api/routes/coaching_sessions.py`

---

## Session Lifecycle Now

### Short Idle (< 30 days)
```
User starts session → User steps away (power outage, etc.) → 
User returns after 5 days → Session RESUMES ✅
```

### Extended Idle (> 30 days)
```
User starts session → User forgets about it → 
30 days pass → DynamoDB auto-deletes via TTL → 
User returns → New session created ✅
```

### Tenant Conflict Detection
```
User A starts session for topic X → 
User B (same tenant) tries to start topic X → 
GET /session/check returns conflict=true → 
Frontend shows: "Another user is using this topic" ✅
```

---

## Testing

### Unit Tests Updated
- **59 tests pass** ✅
- Updated `test_send_message_allows_idle_sessions` to verify idle sessions work
- Removed old test that expected idle timeout errors

**Test Files:**
- `coaching/tests/unit/services/test_coaching_session_service.py`
- `coaching/tests/unit/domain/entities/test_coaching_session.py`

### Test Coverage
```bash
pytest tests/unit/services/test_coaching_session_service.py \
       tests/unit/domain/entities/test_coaching_session.py -v
# ===== 59 passed in 0.33s =====
```

---

## API Changes

### New Endpoint

#### `GET /api/v1/coaching/session/check`

**Query Parameters:**
- `topic_id` (required): Coaching topic ID to check

**Response Fields:**
- `has_session`: boolean - Current user has active/paused session for this topic
- `session_id`: string | null - Session ID if exists
- `status`: string | null - Session status (active, paused)
- `conflict`: boolean - Another user from same tenant has active session
- `conflict_user_id`: string | null - Other user's ID if conflict

**Example Usage (Frontend):**
```typescript
// Before showing "Start Session" button
const check = await api.checkSession({ topicId: 'core_values' });

if (check.conflict) {
  showError(`${check.conflict_user_id} is currently using this topic`);
} else if (check.has_session) {
  showButton('Resume Session', check.session_id);
} else {
  showButton('Start New Session');
}
```

---

## Configuration

### TTL Settings (Repository Level)
```python
# coaching/src/infrastructure/repositories/dynamodb_coaching_session_repository.py
COMPLETED_SESSION_TTL_DAYS = 14  # Terminal states
ACTIVE_SESSION_TTL_DAYS = 30      # Active/Paused states
```

### Idle Timeout (Still Tracked, Not Enforced)
```python
# coaching/src/models/admin_topics.py - LLMTopicSessionSettings
inactivity_timeout_minutes: int = 30  # Default: 30 minutes

# Note: This is now tracked for metrics/analytics only
# It does NOT block session resumption
```

---

## Migration Notes

### Database Changes
- **NO schema changes required** ✅
- TTL field already exists in DynamoDB table
- New TTL values applied automatically on next session update

### Behavior Changes
1. **Sessions no longer auto-close after 30 minutes idle**
   - Old: Idle → Abandoned/Completed
   - New: Idle → Resumable (cleaned up after 30 days via TTL)

2. **Frontend can check for sessions before starting**
   - Old: Blind `/start` call (might resume or create)
   - New: `/session/check` first, then decide UI flow

3. **All sessions now have TTL**
   - Old: Active/Paused kept forever
   - New: Active/Paused auto-deleted after 30 days

---

## Files Changed

### Core Logic
- ✅ `coaching/src/services/coaching_session_service.py` - Removed idle checks
- ✅ `coaching/src/domain/entities/coaching_session.py` - Removed idle enforcement
- ✅ `coaching/src/infrastructure/repositories/dynamodb_coaching_session_repository.py` - Added TTL

### API Layer
- ✅ `coaching/src/api/routes/coaching_sessions.py` - Added `/session/check` endpoint

### Tests
- ✅ `coaching/tests/unit/services/test_coaching_session_service.py` - Updated idle test

---

## Next Steps

### Deployment
1. Merge to `dev` branch
2. Deploy to dev environment
3. Verify DynamoDB TTL working correctly
4. Deploy to staging
5. Frontend integration with `/session/check` endpoint
6. Deploy to production

### Frontend Integration Required
```typescript
// Add this function to api.ts
export async function checkCoachingSession(params: {
  topicId: string;
}): Promise<ApiResponse<SessionCheckResponse>> {
  return apiClient.get('/coaching/session/check', { params });
}

// Use before starting session
const check = await checkCoachingSession({ topicId: 'core_values' });
```

### Optional Future Enhancements
1. **Configurable TTL** - Allow admin to configure TTL per topic
2. **Idle notifications** - Notify users when sessions have been idle for X days
3. **Session transfer** - Allow admin to transfer session between users in same tenant
4. **Auto-pause UI** - Frontend could show "This session has been idle for 5 days" warning

---

## Summary

✅ **Idle sessions are now resumable** (aligned with real-world usage)  
✅ **TTL-based cleanup** (30 days for active/paused, 14 days for terminal)  
✅ **New endpoint** for session detection and conflict checking  
✅ **All tests pass** (59/59)  
✅ **No breaking changes** to existing API contracts  
✅ **No database migration required**

**User Experience Impact:**
- Users can step away without losing sessions
- Power outages don't destroy sessions
- Frontend can provide better UX with session detection
- Truly abandoned sessions still get cleaned up automatically
