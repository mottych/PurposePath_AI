# Async Coaching Messages - Frontend API Contract

**Version**: 1.0.0  
**Date**: February 10, 2026  
**For**: Frontend Implementation (Business Foundation Coaching)  
**Topics**: core_values, purpose, vision

## 1. Canonical Field Naming by Transport

### HTTP Responses (FastAPI with Pydantic)

**All HTTP responses use `snake_case`**:

```python
# Field naming reference
job_id          # NOT jobId
session_id      # NOT sessionId
is_final        # NOT isFinal
max_turns       # NOT maxTurns
message_count   # NOT messageCount
error_code      # NOT errorCode
processing_time_ms  # NOT processingTimeMs
estimated_duration_ms  # NOT estimatedDurationMs
```

### WebSocket Payloads (EventBridge → .NET → Frontend)

**All WebSocket payloads use `camelCase`**:

```typescript
// Field naming reference
jobId           // NOT job_id
sessionId       // NOT session_id
isFinal         // NOT is_final
maxTurns        // NOT max_turns
messageCount    // NOT message_count
errorCode       // NOT error_code
eventType       // Always present
```

### Summary Table

| Context | Casing | Example |
|---------|--------|---------|
| **HTTP Request Bodies** | `snake_case` | `session_id`, `message` |
| **HTTP Response Bodies** | `snake_case` | `job_id`, `is_final`, `error_code` |
| **WebSocket Payloads** | `camelCase` | `jobId`, `isFinal`, `errorCode` |

---

## 2. POST /ai/coaching/message Contract

### Endpoint
```
POST /ai/coaching/message
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Request Body
```json
{
  "session_id": "uuid-string",
  "message": "User's message content"
}
```

### Success Response (202 Accepted)

**Status Code**: `202 Accepted`

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "pending",
    "estimated_duration_ms": 45000
  },
  "message": "Message job created, processing asynchronously"
}
```

### Can it return 200 with full message?

**NO** - This endpoint ALWAYS returns `202 Accepted`. It never returns the assistant message directly.

### Immediate Rejection Errors

#### Empty Message
**Status Code**: `422 Unprocessable Entity`
```json
{
  "detail": {
    "code": "JOB_VALIDATION_ERROR",
    "message": "User message cannot be empty"
  }
}
```

#### Session Not Found
**Status Code**: `422 Unprocessable Entity`
```json
{
  "detail": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session {session_id} not found"
  }
}
```

#### Session Not Active (Paused/Completed/Cancelled)
**Status Code**: `400 Bad Request`
```json
{
  "detail": {
    "code": "SESSION_NOT_ACTIVE",
    "message": "Session is not active (status: completed/paused/cancelled)"
  }
}
```

#### Access Denied (Not Session Owner)
**Status Code**: `403 Forbidden`
```json
{
  "detail": {
    "code": "SESSION_ACCESS_DENIED",
    "message": "User does not own this session"
  }
}
```

#### Max Turns Reached
**Status Code**: `422 Unprocessable Entity`
```json
{
  "detail": {
    "code": "MAX_TURNS_REACHED",
    "message": "Maximum turns (10) reached for session"
  }
}
```

#### Session Idle Timeout
**Status Code**: `410 Gone`
```json
{
  "detail": {
    "code": "SESSION_IDLE_TIMEOUT",
    "message": "Session expired due to inactivity"
  }
}
```

### One Message In-Flight Policy

⚠️ **IMPORTANT**: The current backend implementation does NOT enforce "one message in-flight per session".

**Frontend MUST implement this client-side**:

1. Track pending `job_id` for each session
2. Disable send button while `job_id` is pending
3. Only allow new message after receiving `ai.message.completed` or `ai.message.failed`
4. On page reload, check if there's a pending `job_id` in localStorage and poll its status

**Future Enhancement**: Backend may add `SESSION_BUSY` validation (status code 409):
```json
{
  "detail": {
    "code": "SESSION_BUSY",
    "message": "Another message is currently being processed for this session"
  }
}
```

---

## 3. GET /ai/coaching/message/{job_id} Contract (Polling)

### Endpoint
```
GET /ai/coaching/message/{job_id}
Authorization: Bearer <jwt_token>
```

### State: pending

**Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "pending",
    "message": null,
    "is_final": null,
    "result": null,
    "error": null,
    "processing_time_ms": null
  },
  "message": "Job status: pending"
}
```

### State: processing

**Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "processing",
    "message": null,
    "is_final": null,
    "result": null,
    "error": null,
    "processing_time_ms": null
  },
  "message": "Job status: processing"
}
```

### State: completed (non-final)

**Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "completed",
    "message": "That's a wonderful core value! Integrity means staying true to your principles even when it's difficult. How do you see integrity showing up in your daily leadership decisions?",
    "is_final": false,
    "result": null,
    "error": null,
    "processing_time_ms": 12450
  },
  "message": "Job status: completed"
}
```

**Note**: `turn`, `max_turns`, and `message_count` are NOT included in the polling response (they're in the WebSocket event only). Frontend should track these client-side or fetch from `GET /ai/coaching/session` if needed.

### State: completed (final message)

**Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "completed",
    "message": "Thank you for this wonderful conversation! I've identified your three core values. Let's review what we've discovered together...",
    "is_final": true,
    "result": {
      "identified_values": [
        "Integrity: Staying true to principles even when difficult",
        "Growth: Continuous learning and development",
        "Innovation: Finding creative solutions to challenges"
      ],
      "extraction_type": "core_values",
      "confidence_score": 0.95,
      "metadata": {
        "model_used": "claude-3-5-haiku",
        "extraction_success": true
      }
    },
    "error": null,
    "processing_time_ms": 18720
  },
  "message": "Job status: completed"
}
```

### State: failed

**Status Code**: `200 OK`

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "failed",
    "message": null,
    "is_final": null,
    "result": null,
    "error": "Session not found: f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "processing_time_ms": 125
  },
  "message": "Job status: failed"
}
```

**Note**: `error_code` is NOT exposed in the polling endpoint. Use the WebSocket event for detailed error codes.

### Job Not Found

**Status Code**: `404 Not Found`

```json
{
  "detail": {
    "code": "JOB_NOT_FOUND",
    "message": "Message job not found: 550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 4. WebSocket Contract for Async Coaching Events

### Event: ai.message.completed

**When Received**: 5s - 5min after POST /message

**Payload Structure**:
```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "tenant-uuid",
  "userId": "user-uuid",
  "topicId": "conversation_coaching",
  "eventType": "ai.message.completed",
  "stage": "dev",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "sessionId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "topicId": "conversation_coaching",
    "message": "That's a wonderful core value! Integrity means staying true to your principles even when it's difficult. How do you see integrity showing up in your daily leadership decisions?",
    "isFinal": false,
    "turn": 3,
    "maxTurns": 10,
    "messageCount": 6,
    "result": null
  }
}
```

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventType` | string | Yes | Always `"ai.message.completed"` |
| `jobId` | string | Yes | Top-level job identifier (duplicated in data) |
| `sessionId` | string | No | Top-level session ID (available in data.sessionId) |
| `tenantId` | string | Yes | Tenant ID (for routing) |
| `userId` | string | Yes | User ID (for routing) |
| `topicId` | string | Yes | AI topic (duplicated in data) |
| `stage` | string | Yes | Environment: `"dev"`, `"staging"`, or `"production"` |
| `data.jobId` | string | Yes | Job identifier (matches top-level) |
| `data.sessionId` | string | Yes | Session identifier |
| `data.topicId` | string | Yes | AI topic |
| `data.message` | string | Yes | **Complete AI response** (no streaming) |
| `data.isFinal` | boolean | Yes | Whether conversation is ending |
| `data.turn` | number | Yes | Current turn number (1-indexed, coach responses only) |
| `data.maxTurns` | number | Yes | Maximum turns (0 = unlimited) |
| `data.messageCount` | number | Yes | Total messages (user + AI) |
| `data.result` | object\|null | Yes | Extraction result (when `isFinal` is `true`) |

**Final Message Example** (`isFinal: true`):
```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "tenant-uuid",
  "userId": "user-uuid",
  "topicId": "conversation_coaching",
  "eventType": "ai.message.completed",
  "stage": "dev",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "sessionId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "topicId": "conversation_coaching",
    "message": "Thank you for this wonderful conversation! I've identified your three core values...",
    "isFinal": true,
    "turn": 10,
    "maxTurns": 10,
    "messageCount": 20,
    "result": {
      "identified_values": [
        "Integrity: Staying true to principles",
        "Growth: Continuous learning",
        "Innovation: Creative solutions"
      ],
      "extraction_type": "core_values",
      "confidence_score": 0.95,
      "metadata": {
        "model_used": "claude-3-5-haiku",
        "extraction_success": true
      }
    }
  }
}
```

### Event: ai.message.failed

**When Received**: When message processing fails

**Payload Structure**:
```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "tenant-uuid",
  "userId": "user-uuid",
  "topicId": "conversation_coaching",
  "eventType": "ai.message.failed",
  "stage": "dev",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "sessionId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "topicId": "conversation_coaching",
    "error": "Session not found: f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "errorCode": "PARAMETER_VALIDATION"
  }
}
```

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventType` | string | Yes | Always `"ai.message.failed"` |
| `jobId` | string | Yes | Job identifier |
| `sessionId` | string | No | Session identifier (for routing) |
| `tenantId` | string | Yes | Tenant identifier |
| `userId` | string | Yes | User identifier |
| `topicId` | string | Yes | AI topic |
| `stage` | string | Yes | Environment |
| `data.jobId` | string | Yes | Job identifier |
| `data.sessionId` | string | Yes | Session identifier |
| `data.topicId` | string | Yes | AI topic |
| `data.error` | string | Yes | Human-readable error message |
| `data.errorCode` | string | Yes | Machine-readable error code |

### Routing Strategy

**Frontend MUST route by `jobId` ONLY**:

```typescript
const pendingJobs = new Map<string, PendingJob>();

// When sending message
const response = await sendMessage(sessionId, message);
pendingJobs.set(response.data.job_id, {
  sessionId,
  timestamp: Date.now()
});

// When receiving WebSocket event
websocket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  // Route by jobId only
  if (pendingJobs.has(payload.jobId)) {
    const job = pendingJobs.get(payload.jobId);
    
    if (payload.eventType === 'ai.message.completed') {
      handleCompleted(payload, job.sessionId);
      pendingJobs.delete(payload.jobId);
    } else if (payload.eventType === 'ai.message.failed') {
      handleFailed(payload, job.sessionId);
      pendingJobs.delete(payload.jobId);
    }
  }
};
```

**Do NOT route by sessionId** - multiple jobs can exist for the same session (though frontend should prevent this).

### Additional Events

**NO** - Only `ai.message.completed` and `ai.message.failed` exist.

There is NO `ai.message.started` or `ai.message.processing` event. Frontend should show "AI is thinking..." immediately after 202 response.

---

## 5. Realtime Envelope Compatibility

### What Backend Actually Sends

**Backend sends ONLY `eventType` field** (never `type`):

```json
{
  "eventType": "ai.message.completed",  // ✅ Always present
  "jobId": "...",
  "data": { ... }
}
```

### Frontend Normalization

If your existing WebSocket dispatcher expects `type`, normalize at client side:

```typescript
websocket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  // Normalize field name for compatibility
  const normalizedPayload = {
    ...payload,
    type: payload.eventType,  // Add 'type' alias
  };
  
  // Now your existing dispatcher works
  dispatcher.handleEvent(normalizedPayload);
};
```

### All Event Types Use `eventType`

| Event | Field Name |
|-------|-----------|
| **Async Messages** | `eventType` |
| **Single-shot Jobs** | `eventType` |
| **All Events** | `eventType` (consistent) |

---

## 6. Ordering, Dedupe, and Retries

### Duplicate Events

**Possible**: YES - EventBridge has "at least once" delivery semantics.

**Frontend MUST handle idempotently**:

```typescript
const processedJobs = new Set<string>();

const handleMessageCompleted = (event: MessageCompletedEvent) => {
  const key = `${event.jobId}-completed`;
  
  if (processedJobs.has(key)) {
    console.warn('Duplicate event ignored:', key);
    return;
  }
  
  processedJobs.add(key);
  
  // Process event...
};
```

### Event Ordering

**Per job**: YES - Events for the same `jobId` are ordered.

**Per session**: NO - If multiple jobs exist for the same session (should not happen with frontend enforcement), their events may arrive out of order.

### Internal Retries

**Worker retries**: NO - The worker Lambda does NOT retry failed jobs automatically.

**One terminal event per job**: YES - Each job emits exactly ONE terminal event:
- Either `ai.message.completed`
- Or `ai.message.failed`

**Never both**. If you receive both, it's a duplicate delivery (handle idempotently).

---

## 7. Retention / TTL

### Job Retention

**TTL**: `24 hours` from job creation

After 24 hours, the job record is automatically deleted from DynamoDB.

### GET /message/{job_id} After Expiry

**Status Code**: `404 Not Found`

```json
{
  "detail": {
    "code": "JOB_NOT_FOUND",
    "message": "Message job not found: 550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Frontend handling**:
- If user closes browser and comes back >24 hours later, the pending job ID will not be found
- Clear from localStorage and allow new message

### Session TTL

**Active session TTL**: `30 minutes` of inactivity (idle timeout)

**Paused session TTL**: No automatic expiry - paused sessions remain until user resumes or cancels

**Can paused session always be resumed?**

YES, until:
1. User explicitly cancels the session
2. User starts a new session for the same topic (cancels previous)
3. Session is completed

**No automatic expiry for paused sessions**.

---

## 8. Completion Semantics

### Is `result` guaranteed non-null when `isFinal=true`?

**NO** - `result` can be `null` even when `isFinal=true`.

### What happens if extraction fails?

**Extraction failures do NOT emit `ai.message.failed`**.

Instead, you receive `ai.message.completed` with `isFinal=true` and a result containing error fields:

```json
{
  "eventType": "ai.message.completed",
  "data": {
    "message": "Thank you! Let me summarize what we discussed...",
    "isFinal": true,
    "result": {
      "raw_response": "The LLM response that couldn't be parsed",
      "parse_error": "Expecting value: line 1 column 1 (char 0)"
    }
  }
}
```

**or**

```json
{
  "eventType": "ai.message.completed",
  "data": {
    "message": "Thank you! Let me summarize what we discussed...",
    "isFinal": true,
    "result": {
      "raw_response": "{\"invalid\": \"data\"}",
      "validation_error": "Field 'identified_values' required"
    }
  }
}
```

### Frontend Completion Flow

```typescript
const handleMessageCompleted = (event: MessageCompletedEvent) => {
  if (event.data.isFinal) {
    const result = event.data.result;
    
    if (!result) {
      // No extraction attempted (topic has no result model)
      showCompletionWithoutExtraction(event.data.message);
      return;
    }
    
    if (result.parse_error || result.validation_error) {
      // Extraction failed - show error UI
      showExtractionError({
        message: event.data.message,
        error: result.parse_error || result.validation_error,
        rawResponse: result.raw_response
      });
      return;
    }
    
    // Successful extraction
    showCompletionWithResult(event.data.message, result);
  } else {
    // Normal message
    addMessageToChat(event.data.message);
  }
};
```

---

## 9. Error Catalog (Authoritative)

### Error Codes with Retryability

| Error Code | Description | Retryable | User Action | HTTP Status |
|-----------|-------------|-----------|-------------|--------------|
| `SESSION_NOT_FOUND` | Session doesn't exist | NO | Start new session | 422 |
| `SESSION_ACCESS_DENIED` | User doesn't own session | NO | Contact support | 403 |
| `SESSION_NOT_ACTIVE` | Session paused/completed/cancelled | NO | Check session status, resume if paused | 400 |
| `SESSION_IDLE_TIMEOUT` | Session expired (30min inactivity) | NO | Start new session | 410 |
| `MAX_TURNS_REACHED` | Conversation limit exceeded | NO | Session auto-completed | 422 |
| `LLM_TIMEOUT` | LLM request timed out (5min) | YES | Retry message | N/A (WebSocket) |
| `LLM_ERROR` | LLM service error | YES | Retry after 10s | N/A (WebSocket) |
| `PARAMETER_VALIDATION` | Invalid parameters | NO | Fix input | 422 |
| `INTERNAL_ERROR` | Unexpected system error | YES | Retry after 30s | 500 |
| `JOB_VALIDATION_ERROR` | Empty message or invalid job params | NO | Fix message | 422 |
| `JOB_NOT_FOUND` | Job expired or never existed | NO | Send new message | 404 |

### Additional Validation Errors (HTTP Only)

These occur during POST /message:

| Error Code | Description | HTTP Status |
|-----------|-------------|--------------|
| `SESSION_CONFLICT` | Another user has active session for topic | 409 |
| `INVALID_TOPIC` | Topic not found | 422 |
| `TEMPLATE_NOT_FOUND` | Prompt template missing | 500 |
| `TOPIC_NOT_ACTIVE` | Topic disabled | 422 |

### Error Handling Strategy

```typescript
const ERROR_ACTIONS = {
  // No retry - user action required
  SESSION_NOT_FOUND: 'start_new',
  SESSION_ACCESS_DENIED: 'contact_support',
  SESSION_NOT_ACTIVE: 'check_status',
  SESSION_IDLE_TIMEOUT: 'start_new',
  MAX_TURNS_REACHED: 'show_completion',
  PARAMETER_VALIDATION: 'fix_input',
  JOB_VALIDATION_ERROR: 'fix_input',
  JOB_NOT_FOUND: 'clear_pending',
  
  // Auto-retry with backoff
  LLM_TIMEOUT: { retry: true, delay: 0 },
  LLM_ERROR: { retry: true, delay: 10000 },
  INTERNAL_ERROR: { retry: true, delay: 30000 },
};
```

---

## 10. Recommended FE Polling Strategy

### When to Poll

**Poll ONLY when**:
1. WebSocket is disconnected
2. WebSocket event not received within safety timeout (90 seconds)
3. Browser was closed and reopened with pending job in localStorage

**Do NOT poll** if WebSocket is connected and working.

### Polling Configuration

```typescript
const POLLING_CONFIG = {
  // Poll interval
  intervalMs: 5000,  // 5 seconds
  
  // Max polling duration
  maxWaitMs: 300000,  // 5 minutes (matches Lambda timeout)
  
  // Safety timeout for WebSocket
  websocketSafetyTimeoutMs: 90000,  // 90 seconds
  
  // Warning threshold
  showWarningAfterMs: 60000,  // 1 minute
};
```

### Implementation Example

```typescript
class MessageJobPoller {
  private intervalId: NodeJS.Timeout | null = null;
  private startTime: number = 0;
  private warningShown: boolean = false;
  
  async start(jobId: string, sessionId: string): Promise<void> {
    this.startTime = Date.now();
    this.warningShown = false;
    
    this.intervalId = setInterval(async () => {
      const elapsed = Date.now() - this.startTime;
      
      // Show warning after 1 minute
      if (elapsed > POLLING_CONFIG.showWarningAfterMs && !this.warningShown) {
        this.warningShown = true;
        showNotification('This is taking longer than usual...');
      }
      
      // Timeout after 5 minutes
      if (elapsed > POLLING_CONFIG.maxWaitMs) {
        this.stop();
        handleTimeout(jobId, sessionId);
        return;
      }
      
      // Poll status
      try {
        const response = await fetch(`/ai/coaching/message/${jobId}`);
        const data = await response.json();
        
        if (data.data.status === 'completed') {
          this.stop();
          handleCompleted(data.data, sessionId);
        } else if (data.data.status === 'failed') {
          this.stop();
          handleFailed(data.data, sessionId);
        }
        // Continue polling if pending/processing
        
      } catch (error) {
        console.error('Polling error:', error);
        // Continue polling - don't stop on network errors
      }
    }, POLLING_CONFIG.intervalMs);
  }
  
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}
```

### WebSocket with Polling Fallback

```typescript
// Start polling fallback after safety timeout
const websocketSafetyTimer = setTimeout(() => {
  console.warn('WebSocket event not received, starting polling fallback');
  poller.start(jobId, sessionId);
}, POLLING_CONFIG.websocketSafetyTimeoutMs);

// Cancel polling if WebSocket delivers event
websocket.onmessage = (event) => {
  clearTimeout(websocketSafetyTimer);
  poller.stop();
  handleEvent(event);
};
```

---

## Summary Checklist

- [ ] HTTP responses use `snake_case`
- [ ] WebSocket payloads use `camelCase`
- [ ] POST /message always returns `202` (never `200`)
- [ ] Frontend enforces one message in-flight (backend doesn't validate)
- [ ] Route WebSocket events by `jobId` only
- [ ] Handle duplicate events idempotently
- [ ] Extraction failures return `ai.message.completed` with error fields (not `ai.message.failed`)
- [ ] Poll only as fallback (5s interval, 5min max)
- [ ] Job TTL is 24 hours
- [ ] Paused sessions don't expire automatically

---

## Related Documentation

- [Async Coaching Message Events Specification](./async-coaching-message-events.md)
- [Coaching Session Workflow](../ai-user/coaching-session-workflow.md)
- [Issue #222](https://github.com/mottych/PurposePath_AI/issues/222)
