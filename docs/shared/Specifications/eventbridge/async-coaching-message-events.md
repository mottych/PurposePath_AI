# Async Coaching Message Events - Frontend Integration Specification

**Version**: 1.3.0  
**Date**: February 10, 2026  
**Related Issue**: #222  
**Target Audience**: Frontend Developers, .NET Backend Team

## Overview

This specification defines the complete async pattern for coaching conversation messages, including HTTP APIs, WebSocket events, error handling, and polling fallback. Messages are processed asynchronously (5s - 5min) to avoid API Gateway 30s timeout.

**Single Source of Truth**: This document contains all contracts needed for frontend implementation.

## Field Naming Conventions

### HTTP Responses (FastAPI - snake_case)

All HTTP request/response bodies use **`snake_case`**:

- `job_id`, `session_id`, `is_final`, `max_turns`, `message_count`, `error_code`, `processing_time_ms`, `estimated_duration_ms`

**Example**:
```json
{
  "job_id": "uuid",
  "is_final": false,
  "max_turns": 10
}
```

### WebSocket Payloads (EventBridge - camelCase)

All WebSocket event payloads use **`camelCase`**:

- `jobId`, `sessionId`, `isFinal`, `maxTurns`, `messageCount`, `errorCode`, `eventType`

**Example**:
```json
{
  "jobId": "uuid",
  "isFinal": false,
  "maxTurns": 10
}
```

### Summary

| Transport | Casing | Fields |
|-----------|--------|--------|
| **HTTP (POST/GET)** | `snake_case` | `job_id`, `is_final`, `error_code` |
| **WebSocket Events** | `camelCase` | `jobId`, `isFinal`, `errorCode` |

### Why Async Pattern?

**Problem**: Coaching AI responses can take 20-90 seconds due to:
- Complex conversation context processing
- Prompt cache writes (20-30s first response)
- Final message extraction with structured output

**Solution**: Return 202 Accepted immediately, process async, deliver via WebSocket

### Message Flow

```
┌──────────┐                                    ┌──────────┐
│ Frontend │                                    │  Backend │
└────┬─────┘                                    └────┬─────┘
     │                                               │
     │ POST /ai/coaching/message                     │
     │ { session_id, message }                       │
     ├──────────────────────────────────────────────>│
     │                                               │
     │ 202 Accepted                                  │
     │ { job_id, session_id, status: "pending" }     │
     │<──────────────────────────────────────────────┤
     │                                               │
     │ [Show "AI is thinking..." UI]                 │
     │                                               │
     │                                               │ [Processing 5s-5min]
     │                                               │ [LLM generates response]
     │                                               │
     │                        ┌──────────────┐       │
     │ WebSocket Event        │   EventBridge │       │
     │ ai.message.completed   │      ↓        │       │
     │<───────────────────────┤  WebSocket    │<──────┤
     │                        │   Service     │       │
     │ { message, isFinal }   └──────────────┘       │
     │                                               │
     │ [Display complete response]                   │
     │ [If isFinal: show results]                    │
     │                                               │
```

## API Contracts

### POST /ai/coaching/message

**Endpoint**:
```
POST /ai/coaching/message
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request**:
```json
{
  "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "I value integrity and transparency"
}
```

**Success Response - 202 Accepted** (ALWAYS):
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

**Important**: This endpoint **ALWAYS returns 202 Accepted**. It never returns 200 with the assistant message.

**Error Responses**:

| HTTP Status | Error Code | Scenario | Retryable |
|-------------|-----------|----------|-----------|
| 422 | `JOB_VALIDATION_ERROR` | Empty message | No |
| 422 | `SESSION_NOT_FOUND` | Session doesn't exist | No |
| 400 | `SESSION_NOT_ACTIVE` | Session paused/completed/cancelled | No |
| 403 | `SESSION_ACCESS_DENIED` | User doesn't own session | No |
| 422 | `MAX_TURNS_REACHED` | Hit conversation limit | No |
| 410 | `SESSION_IDLE_TIMEOUT` | Session expired from inactivity | No |
| 500 | `INTERNAL_ERROR` | Server error | Yes (after 30s) |

**Example Error**:
```json
{
  "detail": {
    "code": "SESSION_NOT_ACTIVE",
    "message": "Session is not active (status: completed)"
  }
}
```

#### One Message In-Flight Policy

⚠️ **CRITICAL**: Backend does NOT enforce "one message per session in-flight".

**Frontend MUST implement client-side**:
1. Track pending `job_id` per session (localStorage)
2. Disable send button while job pending
3. Only enable after `ai.message.completed` or `ai.message.failed`
4. On page reload: check localStorage for pending job → start polling

**Future**: Backend may add `SESSION_BUSY` (409 Conflict) validation.

### GET /ai/coaching/message/{job_id}

**Endpoint** (polling fallback):
```
GET /ai/coaching/message/{job_id}
Authorization: Bearer <jwt_token>
```

**Use Case**: Fallback when WebSocket unavailable or for debugging.

#### State: pending

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

#### State: processing

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

#### State: completed (non-final turn)

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "completed",
    "message": "That's wonderful! Integrity shows up in how you communicate transparently with your team...",
    "is_final": false,
    "result": null,
    "error": null,
    "processing_time_ms": 12450
  },
  "message": "Job status: completed"
}
```

⚠️ **Note**: `turn`, `max_turns`, and `message_count` are **NOT included** in polling response (WebSocket only).

#### State: completed (final turn with extraction)

```json
{
  "success": true,
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "status": "completed",
    "message": "Thank you for this wonderful conversation! Here are your three core values...",
    "is_final": true,
    "result": {
      "identified_values": [
        "Integrity: Transparent communication",
        "Growth: Continuous learning",
        "Innovation: Creative problem-solving"
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

#### State: failed

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
    "processing_time_ms": 2100
  },
  "message": "Job status: failed"
}
```

#### Job Not Found (after 24hr TTL)

**Status**: `404 Not Found`

```json
{
  "detail": {
    "code": "JOB_NOT_FOUND",
    "message": "Message job not found: {job_id}"
  }
}
```

---

## Completion & Extraction Semantics

### When is_final = true with result = null?

**Possible**: `is_final` can be `true` with `result` being `null` or containing error fields.

#### Scenario 1: Extraction Parsing Failed

Event still sends as `ai.message.completed` (NOT `ai.message.failed`):

```json
{
  "eventType": "ai.message.completed",
  "jobId": "uuid",
  "data": {
    "message": "Thank you for sharing your values...",
    "isFinal": true,
    "result": {
      "parse_error": "Expecting value: line 1 column 1 (char 0)",
      "raw_response": "Here are the values:\n- Integrity\n- Growth\n- Innovation"
    }
  }
}
```

**Frontend Action**:
- Check if `result.parse_error` or `result.validation_error` exists
- Show completion UI with warning: "We had trouble extracting your responses. Please review manually."

#### Scenario 2: Extraction Model Not Configured

```json
{
  "isFinal": true,
  "result": {}  // Empty object
}
```

**Frontend Action**: Show completion message without extraction results.

### When does ai.message.failed occur?

Only for **execution failures before message generation**:

- `SESSION_NOT_FOUND`
- `SESSION_ACCESS_DENIED`
- `SESSION_NOT_ACTIVE`
- `SESSION_IDLE_TIMEOUT`
- `MAX_TURNS_REACHED`
- `LLM_TIMEOUT`
- `LLM_ERROR`
- `INTERNAL_ERROR`

**NOT for extraction failures** - those still return `ai.message.completed` with error fields in `result`.

## WebSocket Events

### Event: `ai.message.completed`

### Event: `ai.message.completed`

**When Received**: After AI successfully generates a response (5s - 5min after POST)

**Payload**:
```json
{
  "eventType": "ai.message.completed",
  "jobId": "uuid",
  "sessionId": "uuid",
  "tenantId": "uuid",
  "userId": "uuid",
  "data": {
    "message": "Complete AI coach response. This is the full response with no token streaming.",
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
| `jobId` | string (UUID) | Yes | Job identifier from 202 response |
| `sessionId` | string (UUID) | Yes | Coaching session identifier |
| `tenantId` | string (UUID) | Yes | Tenant identifier (for routing) |
| `userId` | string (UUID) | Yes | User identifier (for routing) |
| `data.message` | string | Yes | **Complete AI response** (full text, no streaming) |
| `data.isFinal` | boolean | Yes | `true` if conversation is ending |
| `data.turn` | number | Yes | Current turn number (1-indexed, coach responses only) |
| `data.maxTurns` | number | Yes | Maximum turns allowed (0 = unlimited) |
| `data.messageCount` | number | Yes | Total messages in conversation (user + AI) |
| `data.result` | object \| null | Yes | Extraction result when `isFinal` is `true` |

**When `isFinal` is `true`** (conversation complete):

```json
{
  "eventType": "ai.message.completed",
  "jobId": "uuid",
  "sessionId": "uuid",
  "tenantId": "uuid",
  "userId": "uuid",
  "data": {
    "message": "Final coach message summarizing the conversation...",
    "isFinal": true,
    "turn": 10,
    "maxTurns": 10,
    "messageCount": 20,
    "result": {
      "identified_values": ["value1", "value2", "value3"],
      "extraction_type": "conversation_result",
      "progress": 1.0,
      "metadata": {
        "model_used": "claude-3-5-haiku",
        "extraction_success": true
      }
    }
  }
}
```

**Result Object Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `identified_values` | string[] | Key values/insights identified in conversation |
| `extraction_type` | string | Always `"conversation_result"` |
| `progress` | number | Always `1.0` when final |
| `metadata` | object | Extraction metadata (model used, success flag) |

### Event: `ai.message.failed`

**When Received**: When message processing fails

**Payload**:
```json
{
  "eventType": "ai.message.failed",
  "jobId": "uuid",
  "sessionId": "uuid",
  "tenantId": "uuid",
  "userId": "uuid",
  "data": {
    "error": "Session not found",
    "errorCode": "SESSION_NOT_FOUND"
  }
}
```

**Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `eventType` | string | Yes | Always `"ai.message.failed"` |
| `jobId` | string (UUID) | Yes | Job identifier from 202 response |
| `sessionId` | string (UUID) | Yes | Coaching session identifier |
| `tenantId` | string (UUID) | Yes | Tenant identifier (for routing) |
| `userId` | string (UUID) | Yes | User identifier (for routing) |
| `data.error` | string | Yes | Human-readable error message |
| `data.errorCode` | string | Yes | Machine-readable error code |

## Error Codes

Complete error catalog with user messaging and retryability:

| Error Code | User Message | Retryable | Action |
|-----------|--------------|-----------|--------|
| `SESSION_NOT_FOUND` | "Session not found. Please start a new conversation." | No | Clear session, show start button |
| `SESSION_ACCESS_DENIED` | "You don't have access to this session." | No | Redirect to home |
| `SESSION_NOT_ACTIVE` | "This session is no longer active." | No | Show resume or restart options |
| `SESSION_IDLE_TIMEOUT` | "Session expired due to inactivity." | No | Show restart button |
| `MAX_TURNS_REACHED` | "Conversation limit reached." | No | Show completion message |
| `JOB_VALIDATION_ERROR` | "Invalid request. Please try again." | No | Log error, show generic message |
| `PARAMETER_VALIDATION` | "Invalid parameters. Please try again." | No | Log error, show generic message |
| `LLM_TIMEOUT` | "AI response took too long. Please try again." | Yes | Show retry button (immediate) |
| `LLM_ERROR` | "AI service error. Please try again." | Yes | Show retry button (wait 10s) |
| `INTERNAL_ERROR` | "Something went wrong. Please try again." | Yes | Show retry button (wait 30s) |

**Note**: `EXTRACTION_FAILED` does NOT appear in `ai.message.failed` events. Extraction failures return `ai.message.completed` with error fields in `result`.

### Retry Strategy

```typescript
const getRetryDelay = (errorCode: string): number => {
  switch (errorCode) {
    case 'LLM_TIMEOUT':
      return 0;  // Retry immediately
    case 'LLM_ERROR':
      return 10000;  // Wait 10 seconds
    case 'INTERNAL_ERROR':
      return 30000;  // Wait 30 seconds
    default:
      return -1;  // Not retryable
  }
};

const handleError = (event: MessageFailedEvent, retryAttempt: number) => {
  const delay = getRetryDelay(event.data.errorCode);
  
  if (delay < 0 || retryAttempt >= 3) {
    // Show non-retryable error or max retries reached
    showError(getUserMessage(event.data.errorCode));
    return;
  }
  
  // Show retryable error with countdown
  showRetryableError(getUserMessage(event.data.errorCode), delay / 1000);
  
  setTimeout(() => {
    // Retry sending the message
    retryMessage(sessionId, originalMessage, retryAttempt + 1);
  }, delay);
};
```

## Frontend Implementation

### React/TypeScript Example

```typescript
interface CoachingMessageAPI {
  sendMessage(sessionId: string, message: string): Promise<MessageJobResponse>;
}

interface MessageJobResponse {
  job_id: string;
  session_id: string;
  status: 'pending';
  estimated_duration_ms: number;
}

interface MessageCompletedEvent {
  eventType: 'ai.message.completed';
  jobId: string;
  sessionId: string;
  tenantId: string;
  userId: string;
  data: {
    message: string;
    isFinal: boolean;
    turn: number;
    maxTurns: number;
    messageCount: number;
    result: ConversationResult | null;
  };
}

interface MessageFailedEvent {
  eventType: 'ai.message.failed';
  jobId: string;
  sessionId: string;
  tenantId: string;
  userId: string;
  data: {
    error: string;
    errorCode: string;
  };
}

// Sending a message
const handleSendMessage = async (message: string) => {
  try {
    // POST returns immediately with job_id
    const response = await coachingAPI.sendMessage(sessionId, message);
    
    // Show "AI is thinking..." UI
    setProcessingJobId(response.job_id);
    setIsProcessing(true);
    
    // Wait for WebSocket event (handled in useEffect)
  } catch (error) {
    showError('Failed to send message');
  }
};

// WebSocket event handler
useEffect(() => {
  if (!websocket) return;
  
  const handleMessage = (event: MessageEvent) => {
    const payload = JSON.parse(event.data);
    
    switch (payload.eventType) {
      case 'ai.message.completed':
        handleMessageCompleted(payload as MessageCompletedEvent);
        break;
        
      case 'ai.message.failed':
        handleMessageFailed(payload as MessageFailedEvent);
        break;
    }
  };
  
  websocket.addEventListener('message', handleMessage);
  return () => websocket.removeEventListener('message', handleMessage);
}, [websocket]);

const handleMessageCompleted = (event: MessageCompletedEvent) => {
  // Only process if job ID matches current processing
  if (event.jobId !== processingJobId) return;
  
  setIsProcessing(false);
  
  // Add AI message to chat
  addMessage({
    role: 'assistant',
    content: event.data.message
  });
  
  // Update progress indicators
  if (event.data.maxTurns > 0) {
    setProgress(event.data.turn / event.data.maxTurns);
    setProgressText(`Question ${event.data.turn} of ${event.data.maxTurns}`);
  }
  
  // Handle conversation completion
  if (event.data.isFinal) {
    setConversationStatus('completed');
    setConversationResult(event.data.result);
    showCompletionDialog(event.data.result);
  }
};

const handleMessageFailed = (event: MessageFailedEvent) => {
  if (event.jobId !== processingJobId) return;
  
  setIsProcessing(false);
  
  // Show user-friendly error message
  const userMessage = getErrorMessage(event.data.errorCode);
  showError(userMessage, event.data.errorCode);
  
  // Handle specific error types
  if (event.data.errorCode === 'SESSION_NOT_FOUND') {
    clearSession();
  }
};

const getErrorMessage = (code: string): string => {
  const messages = {
    'SESSION_NOT_FOUND': 'Session not found. Please start a new conversation.',
    'SESSION_ACCESS_DENIED': "You don't have access to this session.",
    'LLM_TIMEOUT': 'AI response took too long. Please try again.',
    // ... other codes
  };
  return messages[code] || 'Something went wrong. Please try again.';
};
```

### UI State Management

```typescript
// Processing state
const [isProcessing, setIsProcessing] = useState(false);
const [processingJobId, setProcessingJobId] = useState<string | null>(null);

// When sending message
<button 
  onClick={() => handleSendMessage(userInput)}
  disabled={isProcessing}
>
  {isProcessing ? 'AI is thinking...' : 'Send'}
</button>

// Show processing indicator
{isProcessing && (
  <div className="processing-indicator">
    <Spinner />
    <span>AI is thinking...</span>
    <span className="text-muted">This may take up to 90 seconds</span>
  </div>
)}
```

### Polling Fallback (No WebSocket)

```typescript
// For systems without WebSocket support
const pollMessageStatus = async (jobId: string) => {
  const maxAttempts = 60; // 5 minutes with 5s intervals
  let attempts = 0;
  
  while (attempts < maxAttempts) {
    try {
      const response = await fetch(`/ai/coaching/message/${jobId}`);
      const data = await response.json();
      
      if (data.data.status === 'completed') {
        handleMessageCompleted({
          eventType: 'ai.message.completed',
          jobId: jobId,
          sessionId: data.data.session_id,
          data: {
            message: data.data.message,
            isFinal: data.data.isFinal,
            result: data.data.result
          }
        });
        return;
      }
      
      if (data.data.status === 'failed') {
        throw new Error(data.data.error);
      }
      
      // Still processing, wait 5s
      await new Promise(resolve => setTimeout(resolve, 5000));
      attempts++;
      
    } catch (error) {
      showError('Failed to check message status');
      return;
    }
  }
  
  // Timeout after 5 minutes
  showError('Message processing timed out');
};
```

## Event Type Field

**All WebSocket events use the `eventType` field** to identify the event type.

**Event types**:

| Pattern | Event Type | Description |
|---------|-----------|-------------|
| **Async Messages** (Conversations) | `ai.message.completed` | Coach response ready |
| **Async Messages** (Conversations) | `ai.message.failed` | Message processing failed |
| **Single-shot Jobs** (Analysis) | `ai.job.completed` | Analysis job completed |
| **Single-shot Jobs** (Analysis) | `ai.job.failed` | Analysis job failed |

**WebSocket handler example**:

```typescript
const handleWebSocketMessage = (payload: any) => {
  switch (payload.eventType) {
    case 'ai.message.completed':
    case 'ai.message.failed':
      handleCoachingMessage(payload);
      break;
      
    case 'ai.job.completed':
    case 'ai.job.failed':
      handleJobCompletion(payload);
      break;
      
    default:
      console.warn('Unknown event type:', payload.eventType);
  }
};
```

## Testing

### Manual Testing (Frontend Dev)

1. **Send Message**:
   ```bash
   curl -X POST https://api.dev.purposepath.ai/ai/coaching/message \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"session_id":"your-session-id","message":"Tell me about values"}'
   ```

2. **Check Response**:
   - Verify `202 Accepted` status
   - Save `job_id` from response

3. **Monitor WebSocket**:
   - Open browser DevTools → Network → WS
   - Wait for `ai.message.completed` event
   - Verify `jobId` matches saved value

4. **Test Error Handling**:
   ```bash
   # Invalid session ID
   curl -X POST ... -d '{"session_id":"invalid","message":"test"}'
   ```
   - Verify `ai.message.failed` event received
   - Check `errorCode` is `"SESSION_NOT_FOUND"`

### Integration Checklist

- [ ] POST /message returns 202 with `job_id`
- [ ] "Processing" UI shows after POST
- [ ] WebSocket receives `ai.message.completed` event
- [ ] Complete message displays correctly
- [ ] `isFinal` flag triggers completion flow
- [ ] Error events show user-friendly messages
- [ ] Session cleared on `SESSION_NOT_FOUND`
- [ ] Polling fallback works without WebSocket

## .NET Backend Notes

The .NET WebSocket service must forward EventBridge events to frontend clients:

**Subscribe to EventBridge events**:
- `ai.message.completed` (detail-type)
- `ai.message.failed` (detail-type)
- Filter by `detail.stage` matching environment

**Forward to WebSocket clients**:
- Route by `detail.tenantId` + `detail.userId`
- Send complete EventBridge `detail` object as WebSocket message
- Frontend expects this exact structure

**Do NOT forward**:
- `ai.message.created` events (internal worker trigger only)

## Migration from Synchronous Pattern

### Before (Synchronous)

```typescript
// POST returned complete response after 20-90s
const response = await fetch('/ai/coaching/message', {
  method: 'POST',
  body: JSON.stringify({ session_id, message })
});

// HTTP 200 with complete message
const data = await response.json();
displayMessage(data.message);  // Full response immediately
```

**Problems**:
- API Gateway 30s timeout → 503 errors for long responses
- User waited with blocking UI
- No progress indication

### After (Asynchronous)

```typescript
// POST returns immediately
const response = await fetch('/ai/coaching/message', {
  method: 'POST',
  body: JSON.stringify({ session_id, message })
});

// HTTP 202 with job_id
const data = await response.json();
showProcessing(data.job_id);

// Wait for WebSocket event (5s - 5min later)
websocket.on('message', (event) => {
  if (event.eventType === 'ai.message.completed') {
    hideProcessing();
    displayMessage(event.data.message);
  }
});
```

**Benefits**:
- No API Gateway timeout (202 returns instantly)
- Non-blocking UI with progress indicator
- Lambda can process for up to 5 minutes
- Better error handling

## Sequence Diagrams

### Normal Flow

```
User          Frontend        API Gateway     Lambda          EventBridge     WebSocket
 |                |               |              |                 |              |
 |-- Type msg --->|               |              |                 |              |
 |                |-- POST ------>|              |                 |              |
 |                |               |-- Invoke --->|                 |              |
 |                |               |              |-- Publish ----->|              |
 |                |               |              | (ai.message.created)           |
 |                |<-- 202 -------|<-- Return ---|                 |              |
 |<-- "Thinking"--|               |              |                 |              |
 |                |               |              |                 |              |
 |                |               |        [Worker processes       |              |
 |                |               |         5s - 5 minutes]        |              |
 |                |               |              |                 |              |
 |                |               |              |-- Publish ----->|              |
 |                |               |              | (ai.message.completed)         |
 |                |               |              |                 |-- Forward -->|
 |                |<-- WebSocket event (complete message) <--------|              |
 |<-- Display ----|               |              |                 |              |
```

### Error Flow

```
User          Frontend        API Gateway     Lambda          EventBridge     WebSocket
 |                |               |              |                 |              |
 |-- Type msg --->|               |              |                 |              |
 |                |-- POST ------>|              |                 |              |
 |                |               |-- Invoke --->|                 |              |
 |                |               |              |-- Publish ----->|              |
 |                |<-- 202 -------|<-- Return ---|                 |              |
 |<-- "Thinking"--|               |              |                 |              |
 |                |               |              |                 |              |
 |                |               |        [Worker encounters      |              |
 |                |               |         error - LLM timeout]   |              |
 |                |               |              |                 |              |
 |                |               |              |-- Publish ----->|              |
 |                |               |              | (ai.message.failed)            |
 |                |               |              |                 |-- Forward -->|
 |                |<-- WebSocket event (error) <------------------|              |
 |<-- Error UI ---|               |              |                 |              |
```

---

## Implementation Guidelines

### Event Ordering & Deduplication

**Ordering Guarantees**:
- Events for the **same `jobId`** are delivered in order
- Events across different jobs have no ordering guarantee
- Sequence: `ai.message.created` (internal) → `ai.message.completed` OR `ai.message.failed` (never both)

**Deduplication**:
- EventBridge may deliver duplicate events (rare, but possible)
- **Frontend must handle idempotently**: Check if `jobId` already processed before updating UI
- **One terminal event per job**: Either `completed` OR `failed`, never both

**Routing**:
- Route by `jobId` ONLY (not sessionId)
- Multiple pending jobs per session are possible (since backend doesn't enforce one-in-flight)

```typescript
const processedJobs = new Set<string>();

const handleWebSocketEvent = (event: MessageCompletedEvent | MessageFailedEvent) => {
  // Deduplication check
  if (processedJobs.has(event.jobId)) {
    console.warn('Duplicate event for job:', event.jobId);
    return;
  }
  
  processedJobs.add(event.jobId);
  
  // Process event...
};
```

### Retention & TTL

**Job Retention**: 24 hours from creation

After 24 hours:
- `GET /message/{job_id}` returns `404 JOB_NOT_FOUND`
- Jobs automatically deleted from DynamoDB
- Frontend should not store `job_id` beyond 24 hours

**Session Retention**: No automatic expiration

- Paused sessions never expire automatically
- Idle timeout only marks session inactive (doesn't delete)
- Sessions persist until explicitly completed or cancelled

**Recommendation**: Clear `job_id` from localStorage after receiving terminal event.

### Polling Strategy

**When to use**:
- Primary: WebSocket event delivery
- Fallback: Polling when WebSocket disconnected or safety timeout exceeded

**Recommended polling**:

```typescript
const pollMessageStatus = async (jobId: string) => {
  const POLL_INTERVAL = 5000;  // 5 seconds
  const MAX_DURATION = 300000;  // 5 minutes
  const startTime = Date.now();
  
  while (Date.now() - startTime < MAX_DURATION) {
    try {
      const response = await fetch(`/ai/coaching/message/${jobId}`);
      const data = await response.json();
      
      if (data.data.status === 'completed') {
        handleCompleted(data.data);
        return;
      }
      
      if (data.data.status === 'failed') {
        handleFailed(data.data);
        return;
      }
      
      // Still processing, wait before next poll
      await sleep(POLL_INTERVAL);
      
    } catch (error) {
      console.error('Polling error:', error);
      await sleep(POLL_INTERVAL);
    }
  }
  
  // Timeout after 5 minutes
  showError('Request timed out. Please try again.');
};
```

**Safety timeout for WebSocket**:

```typescript
// Start polling if no WebSocket event received after 90s
const safetyTimeout = setTimeout(() => {
  if (jobStillPending) {
    console.warn('No WebSocket event after 90s, starting polling...');
    startPolling(jobId);
  }
}, 90000);

// Cancel timeout when WebSocket event arrives
websocket.addEventListener('message', (event) => {
  clearTimeout(safetyTimeout);
  // process event...
});
```

**Key Points**:
- Interval: 5 seconds (balance between latency and server load)
- Max duration: 5 minutes (matches Lambda timeout)
- Always prefer WebSocket over polling
- Use polling as fallback only

---

## Frequently Asked Questions

### Q: What if WebSocket connection is lost?

Use polling fallback with `GET /message/{job_id}`:

```typescript
// Detect WebSocket disconnect
websocket.onclose = () => {
  if (processingJobId) {
    startPolling(processingJobId);
  }
};

const startPolling = async (jobId: string) => {
  const interval = setInterval(async () => {
    const response = await fetch(`/ai/coaching/message/${jobId}`);
    const data = await response.json();
    
    if (data.data.status === 'completed' || data.data.status === 'failed') {
      clearInterval(interval);
      handleCompletion(data);
    }
  }, 5000);  // Poll every 5 seconds
};
```

### Q: What if user closes browser during processing?

- Job continues in Lambda (no automatic cancellation)
- Result saved in DynamoDB
- Next time user opens app, check for pending jobs:
  ```typescript
  useEffect(() => {
    // On mount, check for pending jobs
    const pendingJob = localStorage.getItem('pendingJobId');
    if (pendingJob) {
      startPolling(pendingJob);
    }
  }, []);
  ```

### Q: How long should "Processing" UI show?

- **Minimum**: 1 second (avoid flash)
- **Average**: 20-30 seconds
- **Maximum**: Display "This is taking longer than usual" after 60s
- **Timeout**: Show error after 5 minutes

```typescript
useEffect(() => {
  if (!isProcessing) return;
  
  const warningTimer = setTimeout(() => {
    showWarning('This is taking longer than usual...');
  }, 60000);  // 1 minute
  
  const timeoutTimer = setTimeout(() => {
    showError('Request timed out. Please try again.');
    setIsProcessing(false);
  }, 300000);  // 5 minutes
  
  return () => {
    clearTimeout(warningTimer);
    clearTimeout(timeoutTimer);
  };
}, [isProcessing]);
```

### Q: Can user send another message while processing?

Recommended: **No** - Disable send button while `isProcessing === true`

```typescript
<button 
  onClick={handleSend}
  disabled={isProcessing || !userInput.trim()}
>
  {isProcessing ? 'AI is thinking...' : 'Send'}
</button>
```

### Q: What's `estimated_duration_ms` for?

Optional: Show user estimated wait time from 202 response

```typescript
const { estimated_duration_ms } = response;  // e.g., 25000 (25s)

if (estimated_duration_ms > 30000) {
  showNotice('This may take up to 90 seconds');
}
```

---

## Quick Reference Checklist

✅ HTTP responses use `snake_case` (job_id, is_final, max_turns)  
✅ WebSocket payloads use `camelCase` (jobId, isFinal, maxTurns)  
✅ POST /message **always** returns `202` (never `200`)  
✅ Frontend enforces one message in-flight (backend doesn't validate)  
✅ Route WebSocket events by `jobId` only (not sessionId)  
✅ Handle duplicate events idempotently (check processedJobs Set)  
✅ Extraction failures return `ai.message.completed` with error fields (NOT `ai.message.failed`)  
✅ Poll only as fallback (5s interval, 5min max, prefer WebSocket)  
✅ Job TTL is 24 hours  
✅ Paused sessions don't expire automatically  
✅ Retry failed jobs with delays: LLM_TIMEOUT (0s), LLM_ERROR (10s), INTERNAL_ERROR (30s)  
✅ Use 90s WebSocket safety timeout before starting polling

---

## Changelog

### Version 1.3.0 (2026-02-10)

- **Single Source of Truth Consolidation**
- Consolidated `FRONTEND_API_CONTRACT.md` into this specification
- Added **Field Naming Conventions** section (HTTP=snake_case, WebSocket=camelCase)
- **Complete API Contracts** with error scenarios:
  - POST `/message`: All 7 error types with HTTP status codes
  - GET `/message/{job_id}`: All 4 job states with JSON examples
  - Added ⚠️ one-message-in-flight policy clarification (backend doesn't enforce)
- **Enhanced Completion Semantics** section:
  - Extraction failures documented (return `completed` with error fields, NOT `failed`)
  - Added JSON examples for success vs. extraction failure
- **Error Catalog** with retryability details:
  - Added `Retryable` column to error table
  - Added retry strategy with TypeScript implementation example
  - Specified retry delays: LLM_TIMEOUT (0s), LLM_ERROR (10s), INTERNAL_ERROR (30s)
- **Implementation Guidelines** section:
  - Event ordering & deduplication (idempotent handling)
  - Retention & TTL (24hr jobs, paused sessions never expire)
  - Polling strategy (5s interval, 5min max, WebSocket-first with safety timeout)
- Removed duplicate documentation to maintain clarity

### Version 1.2.0 (2026-02-10)

- **Added progress tracking fields for frontend UX**
- Added `turn`, `maxTurns`, `messageCount` to `ai.message.completed` event
- Frontend can now show "Question 3 of 10" progress indicators
- Frontend can show "You have 7 questions remaining"
- **Fixed event type naming documentation**
- All events use `eventType` field consistently (not `Type` vs `eventType`)
- Removed incorrect documentation about Type/eventType inconsistency
- Updated TypeScript examples with progress handling code

### Version 1.1.0 (2026-02-10)

- **Rewritten for frontend integration focus**
- Removed C# implementation code (moved to backend docs)
- Added comprehensive frontend code examples
- Added error handling reference
- Added sequence diagrams
- Added FAQ section

### Version 1.0.0 (2026-01-15)

- Initial EventBridge specification
- Event schemas for ai.message.* events
- C# implementation examples

---

## Related Documentation

- [Coaching Session Workflow](../ai-user/coaching-session-workflow.md)
- [Issue #222: Async WebSocket Pattern](https://github.com/mottych/PurposePath_AI/issues/222)
- [EventBridge Client Source](../../../../shared/services/eventbridge_client.py)
