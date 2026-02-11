# Async Coaching Message Events - Frontend Integration Specification

**Version**: 1.2.0  
**Date**: February 10, 2026  
**Related Issue**: #222  
**Target Audience**: Frontend Developers, .NET Backend Team

## Overview

This specification defines the async pattern for coaching conversation messages. Messages are processed asynchronously (5s - 5min) to avoid API Gateway 30s timeout, with complete responses delivered via WebSocket.

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

## API Changes

### POST /ai/coaching/message

**Request** (unchanged):
```json
{
  "session_id": "uuid",
  "message": "User's message content"
}
```

**Response** (NEW - now returns 202 Accepted):
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "session_id": "uuid",
    "status": "pending",
    "estimated_duration_ms": 45000
  },
  "message": "Message job created, processing asynchronously"
}
```

**Status Code**: `202 Accepted` (was `200 OK`)

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `job_id` | string (UUID) | Unique job identifier for tracking this message |
| `session_id` | string (UUID) | Coaching session ID (echo from request) |
| `status` | string | Always "pending" on creation |
| `estimated_duration_ms` | number | Rough estimate: 45000ms (45s average) |

### GET /ai/coaching/message/{job_id}

**NEW** polling endpoint for systems without WebSocket support.

**Response** (while processing):
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "session_id": "uuid",
    "status": "processing",
    "message": null,
    "isFinal": null,
    "result": null
  }
}
```

**Response** (completed):
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "session_id": "uuid",
    "status": "completed",
    "message": "Complete AI coach response here...",
    "isFinal": false,
    "result": null,
    "processing_time_ms": 12500
  }
}
```

**Status Values**: `pending`, `processing`, `completed`, `failed`

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

Frontend should handle these error codes for user-friendly messaging:

| Error Code | User Message | Action |
|-----------|--------------|--------|
| `SESSION_NOT_FOUND` | "Session not found. Please start a new conversation." | Clear session, show start button |
| `SESSION_ACCESS_DENIED` | "You don't have access to this session." | Redirect to home |
| `SESSION_NOT_ACTIVE` | "This session is no longer active." | Show resume or restart options |
| `SESSION_IDLE_TIMEOUT` | "Session expired due to inactivity." | Show restart button |
| `MAX_TURNS_REACHED` | "Conversation limit reached." | Show completion message |
| `LLM_TIMEOUT` | "AI response took too long. Please try again." | Show retry button |
| `LLM_ERROR` | "AI service error. Please try again." | Show retry button |
| `EXTRACTION_FAILED` | "Unable to process final results." | Show manual completion option |
| `INTERNAL_ERROR` | "Something went wrong. Please try again." | Show retry button |

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

## Changelog

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
