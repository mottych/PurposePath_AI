# Implement Async WebSocket/Polling Pattern for Coaching Messages

**Epic**: Coaching Infrastructure  
**Priority**: P0 - Critical (Blocking Production)  
**Estimate**: 6-9 hours (Backend: 3-4h, Frontend: 2-3h, Testing: 1-2h)  
**Labels**: `enhancement`, `coaching`, `infrastructure`, `production-blocker`

---

## Problem Statement

### Current Issue

Users are experiencing **503 timeout errors** when sending messages during coaching sessions. This happens because:

1. **API Gateway HTTP API has a hard 30-second timeout** (non-configurable)
2. **Claude Sonnet 4.5 response times are variable and unpredictable:**
   - First message in session: 20-40s (prompt cache write)
   - Messages after 5-min idle: 20-40s (cache expired, rewrite)
   - Messages with throttling: 30-76s (Bedrock rate limiting)
   - Extended thinking responses: 15-45s (model complexity)
   - Normal messages: 5-15s (cache hit)

3. **Pattern observed:**
   - Initial message: Fast (< 10s) ✅
   - Subsequent messages: Randomly timeout (30-76s) ❌ → 503 error
   - Retry immediately: Fast (8-10s) ✅ (cache written by failed attempt)

### Root Causes

1. **Prompt Cache Writes**: First cache write per 5-min window takes 20-30+ seconds
2. **Bedrock Throttling**: Burst capacity exhaustion causes queuing/delays
3. **Inference Profile Routing**: Cross-region routing to different endpoints has variable latency
4. **Extended Thinking**: Sonnet 4.5's thinking capability adds processing time
5. **Unpredictable Nature**: LLM response times will only get MORE variable with future models

### Why Current Architecture is Fundamentally Broken

**Synchronous HTTP + Fixed Timeout is incompatible with modern LLMs:**
- Claude Sonnet 4.5: 5-90s response times
- Future models (Sonnet 5, 6): Even more complex, longer thinking times
- Multi-agent workflows: Multiple sequential LLM calls
- Deep reasoning tasks: Can take minutes

**This is an architectural problem, not a configuration problem.**

---

## Proposed Solution: Async WebSocket + Polling Pattern

### Architecture Overview

Adopt the **same async pattern as single-shot AI jobs**, but adapted for streaming conversation:

```
┌──────────────┐                   ┌─────────────────┐
│   Frontend   │                   │  API Gateway    │
│              │                   │  (HTTP API)     │
└──────────────┘                   └─────────────────┘
       │                                    │
       │ 1. POST /message                   │
       │ {session_id, message}              │
       ├───────────────────────────────────>│
       │                                    │
       │ 2. 202 Accepted                    │
       │ {job_id, websocket_url}           │
       │<───────────────────────────────────┤
       │                                    │
       ├─────┐                              │
       │     │ 3a. Connect WebSocket        │
       │     │ (preferred)                  │
       │     │                              │
       │     │ OR                           │
       │     │                              │
       │     │ 3b. Poll GET /message/{job_id}
       │<────┘ (fallback)                   │
       │                                    │
       │ 4. Stream response tokens          │
       │ {type: "token", content: "..."}   │
       │<───────────────────────────────────│
       │                                    │
       │ 5. Complete                        │
       │ {type: "complete", is_final: bool}│
       │<───────────────────────────────────│


Background Processing:
┌─────────────────┐       ┌──────────────────┐       ┌─────────────┐
│   API Lambda    │       │  EventBridge     │       │ Worker      │
│                 │       │                  │       │ Lambda      │
└─────────────────┘       └──────────────────┘       └─────────────┘
         │                         │                         │
         │ Publish ai.message.created                       │
         ├────────────────────────>│                         │
         │                         │ Invoke async            │
         │                         ├────────────────────────>│
         │                         │                         │
         │                         │                Execute LLM
         │                         │                Stream tokens
         │                         │                         │
         │                         │<─ Publish tokens ───────┤
         │                         │   via EventBridge       │
         │                         │                         │
         │<─ Forward to WebSocket ─┤                         │
         │   (or store for poll)   │                         │
```

### Key Components

1. **Job-Based Architecture** (like single-shot):
   - Each message creates an `AIJob` record in DynamoDB
   - Job status: `pending` → `running` → `completed` / `failed`
   - Job results stored for polling fallback

2. **WebSocket Delivery** (primary):
   - Real-time token streaming via WebSocket
   - EventBridge events trigger WebSocket pushes
   - Better UX: Shows "thinking..." with streaming response

3. **Polling Fallback** (secondary):
   - GET `/message/{job_id}` returns accumulated response
   - Works if WebSocket connection fails
   - Ensures reliability across all network conditions

4. **Session Consistency**:
   - Jobs linked to `session_id`
   - Session state updated only when job completes
   - Multiple concurrent jobs prevented (one at a time per session)

---

## Detailed Implementation Plan

### Phase 1: Backend - Job Infrastructure (2-3 hours)

#### 1.1 Extend AIJob Domain Model

**File**: `coaching/src/domain/entities/ai_job.py`

Add support for conversation messages:

```python
class AIJobType(str, Enum):
    """Type of AI job."""
    SINGLE_SHOT = "single_shot"
    CONVERSATION_MESSAGE = "conversation_message"  # NEW

@dataclass
class AIJob:
    job_id: str
    tenant_id: str
    user_id: str
    topic_id: str
    job_type: AIJobType  # NEW field
    session_id: str | None = None  # NEW: Link to coaching session
    user_message: str | None = None  # NEW: User's message content
    # ... existing fields ...
```

#### 1.2 Create Message Job Service

**File**: `coaching/src/services/coaching_message_job_service.py` (NEW)

```python
class CoachingMessageJobService:
    """Service for async coaching message execution."""
    
    async def create_message_job(
        self,
        session_id: str,
        user_id: str,
        tenant_id: str,
        user_message: str,
    ) -> AIJob:
        """Create async job for coaching message.
        
        Returns 202 Accepted with job_id immediately.
        Actual LLM processing happens in background.
        """
        # 1. Validate session is active
        session = await self.session_repo.get_by_id(session_id, tenant_id)
        if session.status != "active":
            raise SessionNotActiveError(session_id)
        
        # 2. Check for concurrent jobs (prevent race conditions)
        active_job = await self.job_repo.get_active_job_for_session(session_id)
        if active_job:
            raise ConcurrentMessageError(session_id)
        
        # 3. Create job record
        job = AIJob.create(
            tenant_id=tenant_id,
            user_id=user_id,
            topic_id=session.topic_id,
            job_type=AIJobType.CONVERSATION_MESSAGE,
            session_id=session_id,
            user_message=user_message,
        )
        await self.job_repo.save(job)
        
        # 4. Publish event to trigger async execution
        await self.event_publisher.publish_event(
            event_type="ai.message.created",
            detail={
                "job_id": job.job_id,
                "session_id": session_id,
                "tenant_id": tenant_id,
            }
        )
        
        return job
    
    async def execute_message_job(self, job_id: str) -> None:
        """Execute coaching message job (called by worker Lambda).
        
        This method:
        1. Loads job and session
        2. Calls LLM with streaming
        3. Publishes token events to EventBridge
        4. Updates session when complete
        5. Marks job as completed
        """
        # Load job
        job = await self.job_repo.get_by_id(job_id)
        job.mark_as_running()
        await self.job_repo.update(job)
        
        try:
            # Load session and add user message
            session = await self.session_repo.get_by_id(job.session_id, job.tenant_id)
            session.add_user_message(job.user_message)
            
            # Build LLM request
            system_prompt = await self._render_system_prompt(session)
            history = session.get_messages_for_llm(max_messages=30)
            
            # Stream response
            accumulated_response = ""
            async for token in self.llm_service.generate_streaming_response(
                messages=history,
                system_prompt=system_prompt,
                model=session.get_model_for_tier(job.user_id),
            ):
                accumulated_response += token
                
                # Publish token to WebSocket
                await self.event_publisher.publish_event(
                    event_type="ai.message.token",
                    detail={
                        "job_id": job.job_id,
                        "session_id": session.session_id,
                        "token": token,
                    }
                )
            
            # Check for completion signal
            is_final = self._check_completion_signal(accumulated_response)
            
            if is_final:
                # Extract results
                result = await self._extract_and_complete(session, accumulated_response)
                session.complete(result)
                job.mark_as_completed(result={
                    "message": accumulated_response,
                    "is_final": True,
                    "result": result,
                })
            else:
                # Add assistant message
                session.add_assistant_message(accumulated_response)
                job.mark_as_completed(result={
                    "message": accumulated_response,
                    "is_final": False,
                })
            
            # Save updates
            await self.session_repo.update(session)
            await self.job_repo.update(job)
            
            # Publish completion event
            await self.event_publisher.publish_event(
                event_type="ai.message.completed",
                detail={
                    "job_id": job.job_id,
                    "session_id": session.session_id,
                    "is_final": is_final,
                }
            )
            
        except Exception as e:
            logger.error("Message job execution failed", job_id=job_id, error=str(e))
            job.mark_as_failed(
                error_code=AIJobErrorCode.EXECUTION_ERROR,
                error_message=str(e),
            )
            await self.job_repo.update(job)
            
            # Publish failure event
            await self.event_publisher.publish_event(
                event_type="ai.message.failed",
                detail={
                    "job_id": job.job_id,
                    "session_id": job.session_id,
                    "error": str(e),
                }
            )
```

#### 1.3 Update API Routes

**File**: `coaching/src/api/routes/coaching_sessions.py`

Replace synchronous POST `/message` with async pattern:

```python
@router.post("/message", response_model=MessageJobResponse, status_code=202)
async def send_message_async(
    request: SendMessageRequest,
    user: UserContext = Depends(get_current_user),
    job_service: CoachingMessageJobService = Depends(get_message_job_service),
) -> MessageJobResponse:
    """Send message to coaching session (async).
    
    Returns 202 Accepted immediately with job_id.
    Frontend should connect to WebSocket or poll for results.
    
    Returns:
        job_id: Job identifier for tracking
        websocket_url: WebSocket URL for real-time streaming
        polling_url: Fallback URL for polling
    """
    job = await job_service.create_message_job(
        session_id=request.session_id,
        user_id=user.user_id,
        tenant_id=user.tenant_id,
        user_message=request.message,
    )
    
    return MessageJobResponse(
        job_id=job.job_id,
        session_id=request.session_id,
        status="pending",
        websocket_url=f"wss://api.dev.purposepath.app/ws/coaching/{job.job_id}",
        polling_url=f"/api/v1/ai/coaching/message/{job.job_id}",
    )


@router.get("/message/{job_id}", response_model=MessageJobStatusResponse)
async def get_message_status(
    job_id: str,
    user: UserContext = Depends(get_current_user),
    job_repo: DynamoDBJobRepository = Depends(get_job_repository),
) -> MessageJobStatusResponse:
    """Poll for message job status (fallback when WebSocket unavailable).
    
    Returns:
        status: "pending" | "running" | "completed" | "failed"
        message: Accumulated response (when completed)
        is_final: Whether conversation is complete
        result: Extracted results (if is_final=true)
    """
    job = await job_repo.get_by_id(job_id)
    
    # Validate ownership
    if job.tenant_id != user.tenant_id or job.user_id != user.user_id:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return MessageJobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        message=job.result.get("message") if job.result else None,
        is_final=job.result.get("is_final", False) if job.result else False,
        result=job.result.get("result") if job.result else None,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )
```

#### 1.4 Add Job Repository Methods

**File**: `coaching/src/infrastructure/repositories/dynamodb_job_repository.py`

```python
async def get_active_job_for_session(self, session_id: str) -> AIJob | None:
    """Get active job for session (prevent concurrent messages)."""
    response = self.table.query(
        IndexName="session-status-index",  # GSI on session_id + status
        KeyConditionExpression="session_id = :sid AND status IN (:pending, :running)",
        ExpressionAttributeValues={
            ":sid": session_id,
            ":pending": "pending",
            ":running": "running",
        },
        Limit=1,
    )
    items = response.get("Items", [])
    return AIJob.from_dynamodb(items[0]) if items else None
```

---

### Phase 2: Frontend - WebSocket + Polling (2-3 hours)

#### 2.1 Copy Single-Shot Pattern

**Reference Files** (to copy pattern from):
- Frontend WebSocket handler (from single-shot)
- Polling fallback logic (from single-shot)
- Token streaming display (from single-shot)

#### 2.2 Update Message Sending Flow

```typescript
async function sendMessage(sessionId: string, message: string) {
  // 1. Send message, get job_id
  const response = await api.sendCoachingMessage({
    sessionId,
    message
  });
  
  // Response: { job_id, websocket_url, polling_url }
  
  // 2. Try WebSocket first
  try {
    await connectWebSocketForStreaming(response.websocket_url, {
      onToken: (token) => {
        appendToCurrentMessage(token);  // Stream like ChatGPT
      },
      onComplete: (data) => {
        if (data.is_final) {
          showCompletionSummary(data.result);
          closeChatWindow();
        }
      },
      onError: (error) => {
        console.error("WebSocket failed, falling back to polling", error);
        startPolling(response.polling_url);
      }
    });
  } catch (wsError) {
    // 3. Fallback to polling if WebSocket fails
    startPolling(response.polling_url);
  }
}

async function startPolling(pollingUrl: string) {
  const pollInterval = setInterval(async () => {
    const status = await api.getMessageStatus(pollingUrl);
    
    if (status.status === "completed") {
      clearInterval(pollInterval);
      displayMessage(status.message);
      
      if (status.is_final) {
        showCompletionSummary(status.result);
        closeChatWindow();
      }
    } else if (status.status === "failed") {
      clearInterval(pollInterval);
      showError("Message processing failed");
    }
    // Keep polling if status is "pending" or "running"
  }, 2000);  // Poll every 2 seconds
}
```

#### 2.3 Update UI for Streaming

```typescript
// Show streaming state while waiting
function displayStreamingMessage() {
  return (
    <div className="message assistant streaming">
      <div className="typing-indicator">
        <span></span><span></span><span></span>
      </div>
      <div className="streamed-content">
        {/* Tokens appear here in real-time */}
      </div>
    </div>
  );
}
```

---

### Phase 3: Infrastructure Updates (1 hour)

#### 3.1 Add DynamoDB GSI

**Table**: `purposepath-ai-jobs-dev`

Add Global Secondary Index for session queries:

```typescript
// coaching/pulumi/index.ts
new aws.dynamodb.Table("ai-jobs-table", {
  // ... existing config ...
  globalSecondaryIndexes: [
    // ... existing indexes ...
    {
      name: "session-status-index",
      hashKey: "session_id",
      rangeKey: "status",
      projectionType: "ALL",
    }
  ]
});
```

#### 3.2 Add EventBridge Rules

**Event Types**:
- `ai.message.created` → Triggers worker Lambda
- `ai.message.token` → Forwards to WebSocket
- `ai.message.completed` → Notifies frontend
- `ai.message.failed` → Notifies frontend of error

#### 3.3 WebSocket API (if not already deployed)

If WebSocket API doesn't exist, deploy using API Gateway WebSocket API:

```typescript
// Deploy WebSocket API for real-time token streaming
const wsApi = new aws.apigatewayv2.Api("coaching-websocket-api", {
  protocolType: "WEBSOCKET",
  routeSelectionExpression: "$request.body.action",
});
```

---

### Phase 4: Documentation Updates (30 min)

#### 4.1 Update Workflow Specification

**File**: `docs/shared/Specifications/ai-user/coaching-session-workflow.md`

Add new sections:

##### Section: "Async Message Processing"

```markdown
## Async Message Processing

### Overview

Coaching messages are processed asynchronously to handle variable LLM response times (5-90+ seconds).

**Why Async?**
- Claude Sonnet 4.5 has unpredictable response times
- Prompt cache writes take 20-30 seconds
- Extended thinking can take 45-60 seconds
- Future models will take even longer
- API Gateway 30s timeout is insufficient

### Architecture

POST /message → 202 Accepted (instant)
                ↓
        WebSocket streaming (real-time)
                OR
        Polling fallback (reliability)
                ↓
        Message complete (5-90s later)

### Message States

| State | Description | User Experience |
|-------|-------------|-----------------|
| pending | Job created, queued | "Sending..." spinner |
| running | LLM processing | "Thinking..." with streaming tokens |
| completed | Response ready | Message displayed, interactive |
| failed | Error occurred | Error message shown |
```

##### Update Section: "POST /message"

```markdown
### Endpoint: POST /message (Async)

**Purpose:** Send user message asynchronously.

**Request:**
```json
{
  "session_id": "sess_xxx",
  "message": "I value integrity..."
}
```

**Response: 202 Accepted**
```json
{
  "job_id": "job_abc123",
  "session_id": "sess_xxx",
  "status": "pending",
  "websocket_url": "wss://api.dev.purposepath.app/ws/coaching/job_abc123",
  "polling_url": "/api/v1/ai/coaching/message/job_abc123"
}
```

**WebSocket Streaming (Primary):**

Frontend connects to `websocket_url` and receives:

```json
// Token events (real-time)
{"type": "token", "job_id": "job_abc123", "content": "I "}
{"type": "token", "job_id": "job_abc123", "content": "hear "}
{"type": "token", "job_id": "job_abc123", "content": "you..."}

// Completion event
{
  "type": "complete",
  "job_id": "job_abc123",
  "message": "I hear you...",
  "is_final": false
}
```

**Polling Fallback (Secondary):**

GET `/api/v1/ai/coaching/message/{job_id}` returns:

```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "message": "I hear you...",
  "is_final": false,
  "created_at": "2026-02-10T12:00:00Z",
  "completed_at": "2026-02-10T12:00:15Z"
}
```

**Logic:**
```python
def send_message_async(session_id, user_message):
    # 1. Validate session
    session = get_session(session_id)
    if session.status != "active":
        raise SessionNotActiveError
    
    # 2. Check for concurrent jobs
    active_job = get_active_job_for_session(session_id)
    if active_job:
        raise ConcurrentMessageError
    
    # 3. Create job
    job = create_message_job(session_id, user_message)
    
    # 4. Publish event for async processing
    publish_event("ai.message.created", job_id=job.job_id)
    
    # 5. Return immediately
    return {
        "job_id": job.job_id,
        "status": "pending",
        "websocket_url": f"wss://.../ws/coaching/{job.job_id}",
        "polling_url": f"/message/{job.job_id}"
    }
```
```

#### 4.2 Add API Specification Document

**File**: `docs/shared/Specifications/ai-user/coaching-async-messages.md` (NEW)

Create comprehensive API documentation for async message endpoints:
- POST /message (202 Accepted)
- GET /message/{job_id} (polling)
- WebSocket protocol specification
- Error handling
- Retry logic
- Concurrent message prevention

---

## Testing Requirements

### Unit Tests

1. **Message Job Creation**
   - ✅ Create job for active session
   - ❌ Reject if session not active
   - ❌ Reject if concurrent job exists
   - ✅ Job persisted to DynamoDB

2. **Job Execution**
   - ✅ Session updated with user message
   - ✅ LLM called with correct context
   - ✅ Tokens published to EventBridge
   - ✅ Job marked completed
   - ✅ is_final detected correctly
   - ✅ Results extracted when final

3. **Error Handling**
   - ❌ LLM failure → job marked failed
   - ❌ Session not found → job marked failed
   - ✅ Error event published

### Integration Tests

1. **End-to-End Message Flow**
   ```python
   async def test_async_message_e2e():
       # Start session
       session = await start_session("core_values")
       
       # Send message
       job = await send_message(session.session_id, "Hello")
       assert job.status == "pending"
       
       # Wait for completion
       await wait_for_job_completion(job.job_id, timeout=60)
       
       # Verify result
       job = await get_job(job.job_id)
       assert job.status == "completed"
       assert job.result["message"] is not None
       
       # Verify session updated
       session = await get_session(session.session_id)
       assert len(session.messages) == 2  # user + assistant
   ```

2. **WebSocket Streaming**
   ```python
   async def test_websocket_streaming():
       # Send message
       job = await send_message(session_id, "Tell me about values")
       
       # Connect WebSocket
       tokens = []
       async with connect_websocket(job.websocket_url) as ws:
           async for message in ws:
               if message["type"] == "token":
                   tokens.append(message["content"])
               elif message["type"] == "complete":
                   break
       
       # Verify streaming worked
       assert len(tokens) > 10
       assert "".join(tokens) == message["message"]
   ```

3. **Concurrent Prevention**
   ```python
   async def test_concurrent_message_prevention():
       # Send first message
       job1 = await send_message(session_id, "Message 1")
       
       # Try to send second (should fail)
       with pytest.raises(ConcurrentMessageError):
           await send_message(session_id, "Message 2")
       
       # Wait for first to complete
       await wait_for_job_completion(job1.job_id)
       
       # Now second should work
       job2 = await send_message(session_id, "Message 2")
       assert job2.status == "pending"
   ```

### Load Testing

Test with variable LLM response times:
- 100 concurrent users
- Messages ranging 5-60s response time
- WebSocket connection stability
- Polling fallback activation rate

---

## Acceptance Criteria

### Must Have
- [ ] POST /message returns 202 Accepted instantly (< 500ms)
- [ ] WebSocket delivers tokens in real-time for streaming UX
- [ ] Polling fallback works when WebSocket unavailable
- [ ] No 503 timeout errors regardless of LLM response time
- [ ] Session state consistency maintained
- [ ] Concurrent messages prevented per session
- [ ] is_final detection and result extraction work correctly
- [ ] All existing coaching functionality preserved
- [ ] Unit test coverage > 80% for new code
- [ ] Integration tests pass for all scenarios
- [ ] Documentation updated (workflow, API specs)

### Should Have
- [ ] WebSocket reconnection logic with exponential backoff
- [ ] Token rate limiting (prevent flooding)
- [ ] Job TTL cleanup (delete completed jobs after 24h)
- [ ] CloudWatch metrics for job duration, failure rates
- [ ] Admin API to view job status for debugging

### Nice to Have
- [ ] Job cancellation (user can cancel message in-flight)
- [ ] Optimistic UI updates (show user message immediately)
- [ ] Read receipts (show when coach is "typing")
- [ ] Job retry mechanism for transient failures

---

## Migration Strategy

### Phase 1: Deploy Infrastructure
1. Deploy DynamoDB GSI for session queries
2. Deploy EventBridge rules
3. Deploy WebSocket API (if needed)
4. Test infrastructure in dev

### Phase 2: Deploy Backend (Backward Compatible)
1. Deploy new async endpoints alongside old sync endpoint
2. Keep old POST /message working (don't break existing frontend)
3. Test async endpoints in dev
4. Roll out to staging

### Phase 3: Update Frontend
1. Update frontend to use async endpoints
2. Test WebSocket streaming
3. Test polling fallback
4. Deploy to production

### Phase 4: Remove Old Endpoint (After Frontend Migration)
1. Monitor usage of old sync endpoint (should be zero)
2. Deprecate old endpoint
3. Remove old code after 2 weeks

### Rollback Plan
If issues found in production:
1. Frontend can revert to old sync endpoint
2. Old endpoint remains functional during transition
3. No data loss (sessions unchanged)

---

## Alternatives Considered

### 1. Application Load Balancer (ALB)
- **Pro**: Solves timeout issue, no code changes
- **Con**: $30-40/month per environment
- **Con**: Still has max timeout (120s), doesn't solve root cause
- **Con**: Doesn't enable streaming UX
- **Con**: Going against industry standard (all AI apps use async)
- **Decision**: Rejected - band-aid, not a solution

### 2. Disable Prompt Caching
- **Pro**: Consistent response times
- **Con**: 2-3s overhead per message
- **Con**: Increased costs (~$0.003 per message)
- **Con**: Doesn't solve throttling or extended thinking delays
- **Decision**: Rejected - performance regression

### 3. API Gateway WebSocket only (no polling)
- **Pro**: Simpler architecture
- **Con**: Doesn't work on all networks (corporate firewalls)
- **Con**: No fallback if WebSocket fails
- **Decision**: Rejected - reliability concern

---

## Success Metrics

### Performance
- **Zero 503 timeout errors** (current: 4+ per 10 minutes)
- **Mean response time**: 5-15s (acceptable, not blocking)
- **P95 response time**: < 45s
- **P99 response time**: < 90s
- **WebSocket connection success rate**: > 95%
- **Polling fallback activation rate**: < 5%

### Reliability
- **Job completion rate**: > 99.5%
- **Job failure rate**: < 0.5%
- **Concurrent message prevention**: 100%
- **Session state consistency**: 100%

### User Experience
- **Time to first token**: < 2s (via WebSocket)
- **Streaming smoothness**: No token batching delays
- **Error recovery**: Automatic retry on transient failures

---

## Related Issues

- Issue #XXX: 503 Timeout Investigation
- Issue #75: Multi-model support (GPT-5, Gemini 2.5)
- Issue #136: LLM Provider Factory
- Issue #208: Extraction model configuration

---

## References

- **Single-shot async pattern**: `coaching/src/services/async_execution_service.py`
- **Bedrock provider**: `coaching/src/infrastructure/llm/bedrock_provider.py`
- **Current workflow**: `docs/shared/Specifications/ai-user/coaching-session-workflow.md`
- **API Gateway limits**: https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Backend implementation | 3-4 hours | Async endpoints, job service, worker Lambda |
| Frontend implementation | 2-3 hours | WebSocket client, polling fallback, UI updates |
| Testing | 1-2 hours | Unit tests, integration tests, E2E validation |
| Documentation | 30 min | Workflow spec, API docs |
| **Total** | **6-9 hours** | **Production-ready async messaging** |

---

## Next Steps

1. Create this GitHub issue
2. Set priority to P0 (production blocker)
3. Assign to developer
4. Schedule for immediate sprint
5. Deploy to dev → staging → production within 1-2 days
6. Monitor metrics and user feedback
7. Consider ALB only as fallback if async has issues (unlikely)
