# Coaching API Timeout Analysis - February 10, 2026

## Executive Summary
Users are experiencing **503 timeout errors** when sending messages in coaching sessions. Analysis reveals that **4 requests in the last 4 hours exceeded 30 seconds**, with the worst case at **76.92 seconds** - more than double the API Gateway limit.

## Current Status

### What's Happening
- **Symptom**: Users receive 503 errors when sending coaching messages
- **Root Cause**: Combined conversation + extraction exceeds API Gateway's **30-second hard limit**
- **Lambda Timeout**: 300 seconds (5 minutes) - NOT the issue  
- **Frequency**: 4 timeouts in 4 hours (76s, 42s, 42s, 37s)

### Key Finding: Auto-Completion is the Culprit

The system adds structured output instructions to **every coaching message** that tell the LLM:

```
You MUST respond with JSON in this structure:
{
  "message": "Your response",
  "is_final": true/false,
  "result": {...},
  "confidence": 0.85
}

You should set is_final=true when:
- The user explicitly confirms they are satisfied
- The user says "looks good", "I'm happy with this", "that's perfect"
- The conversation has naturally concluded with clear outcomes
```

**When `is_final=true` is detected:**
1. Conversation LLM call: 8-15s (Claude Sonnet)
2. **Automatic extraction triggered**: 3-8s (Claude Haiku)  
3. DynamoDB updates: 0.5-1s
4. **Total: 11-24s typically, spikes to 30-76s**

**The problem:** The LLM is being asked to decide on EVERY turn whether to complete, and when it does (correctly or incorrectly), extraction happens inline within the same API call.

### Timeout Breakdown
```
User Message → API Gateway (30s limit) → Lambda (300s limit) → Bedrock LLM

Current Flow:
1. Receive user message
2. LLM conversation call: 8-15s (Claude Sonnet)
3. If is_final=true:
   - LLM extraction call: 3-8s (Claude Haiku)
   - Save to DynamoDB: 0.5-1s
4. Return response

Total: 11-24s typical, but can spike to 30-35s under:
   - Network latency to Bedrock
   - Bedrock throttling/queuing
   - Large conversation history
   - Complex extractions
```

### Previous Fix (Feb 9, 2026)
- **Change**: Switched extraction from Sonnet to Haiku  
- **Reduction**: From 25-32s to 15-20s average
- **Status**: INSUFFICIENT - still seeing timeouts due to:
  - Network variability to Bedrock
  - Bedrock throttling during peak usage
  - LLM occasionally triggers completion mid-conversation (though logs show this is rare)

### Log Analysis Findings

**From CloudWatch logs (last 4 hours):**
- ✅ **Most responses correctly show `is_final=False`** 
- ✅ **Most responses are plain text, not JSON** (LLM is NOT always returning structured JSON)
- ❌ **4 requests exceeded 30 seconds:**
  - 18:48:13 → **76.92s** duration
  - 18:45:22 → **37.45s** duration  
  - 18:38:57 → **42.56s** duration
  - 18:08:45 → **42.23s** duration
- ⚠️ **Pattern**: These long requests likely involved auto-completion + extraction

**Good news:** The LLM is mostly ignoring the JSON format instructions and just responding naturally with plain text. This is why most requests complete fine.

**Bad news:** When the LLM DOES decide to return JSON with `is_final=true` (legitimately or prematurely), the extraction happens inline and can push execution time over 30s.

## Infrastructure Details

### Current Configuration
- **API Gateway Type**: HTTP API (not REST API)
- **API Gateway Timeout**: 30 seconds (HARD LIMIT - cannot be changed)
- **Lambda Timeout**: 300 seconds
- **Lambda Memory**: 1024 MB
- **Average conversation LLM call**: 8-15s (Claude Sonnet)
- **Average extraction LLM call**: 3-8s (Claude Haiku)
- **Combined typical**: 11-24s
- **Combined worst-case observed**: 76.92s ❌

### API Gateway Limits
- HTTP APIs: 30-second integration timeout (non-configurable)
- WebSocket APIs: 30-second idle timeout (can extend with keepalive)
- No way to increase HTTP API timeout beyond 30 seconds

### Structured Output Behavior

The system adds these instructions to the LLM **on every turn**:

````python
# In coaching_session_service.py, send_message()
if endpoint_def.result_model:
    structured_instructions = get_structured_output_instructions(...)
    rendered_system = f"{rendered_system}\n\n{structured_instructions}"
````

**LLM Response Patterns:**
1. **Normal response** (1Most common): Model responds with plain text, ignored JSON instructions
   - Result: `is_final=False`, no extraction, ~8-15s total ✅
2. **Structured response** (Occasional): Model returns JSON with `is_final=true`
   - Result: Extraction triggered, 11-76s total ⚠️
3. **Why this happens**: LLMs don't always follow JSON format instructions perfectly
   - Claude prefers natural conversation over rigid JSON
   - This is actually helping us most of the time!

### When Timeouts Occur

**Timing breakdown when `is_final=true`:**
```
User message received
├─ Validate session: 0.2s
├─ Load prompts from S3: 0.5s
├─ Conversation LLM call: 8-15s
│   └─ (Sometimes much longer due to Bedrock queuing)
├─ Parse response → is_final=true detected
├─ EXTRACTION TRIGGERED (inline, blocking):
│   ├─ Format conversation: 0.1s
│   ├─ Generate extraction prompt: 0.1s
│   ├─ Extraction LLM call: 3-8s
│   │   └─ (Sometimes much longer due to Bedrock queuing)
│   ├─ Parse JSON result: 0.05s
│   └─ Update DynamoDB: 0.5s
└─ Return response

Total: 12-25s typical, 30-77s worst case
API Gateway timeout: 30s HARD LIMIT
Result: 503 error if total > 30s
```

**Observed timeout patterns:**
- Network latency to Bedrock during peak hours
- Bedrock throttling when many requests queued
- Large conversation history (30+ messages)
- Complex extraction with detailed result models

## Solution Options

### ✅ **RECOMMENDED: Option 1 - Make It Fully Async**

Split the final message + extraction into two operations:

**Flow:**
```
1. POST /ai/coaching/message
   - Add user message
   - Call LLM for coach response
   - Return response with is_final flag
   - Total: 8-15s (safely under 30s)

2. If is_final=true, Frontend calls:
   POST /ai/coaching/complete
   - Run extraction
   - Mark complete
   - Return results
   - Total: 3-8s (safely under 30s)
```

**Implementation:**
```python
# In coaching_session_service.py -> send_message()

# REMOVE this block:
if is_final:
    completion_response = await self._extract_and_complete(...)
    return MessageResponse(..., result=completion_response.result)

# REPLACE with:
if is_final:
    # Just flag it as final, don't extract
    return MessageResponse(
        ...,
        is_final=True,
        message=coach_message,
        result=None  # Frontend must call /complete
    )
```

**Frontend Changes Required:**
```typescript
// In OnboardingCoachPanel.tsx or message handler
const response = await sendMessage(sessionId, message);

if (response.is_final) {
    // Show "Processing your results..." UI
    try {
        const completion = await completeSession(sessionId);
        // Display completion.result
        onComplete(completion);
    } catch (error) {
        // Handle completion errors
    }
}
```

**Pros:**
- ✅ Eliminates timeout risk entirely
- ✅ Simple implementation (remove code, not add)
- ✅ Clear separation of concerns
- ✅ Uses EXISTING `/complete` endpoint (already implemented!)
- ✅ No new infrastructure needed
- ✅ Better UX (can show progress between steps)

**Cons:**
- ⚠️ Requires frontend changes
- ⚠️ Extra network round-trip

**Effort:** LOW (backend: 2 hours, frontend: 3 hours, testing: 2 hours)

---

### Option 2 - Use WebSocket for Long Operations

**NOT RECOMMENDED** - Over-engineered for this use case

Replace HTTP API with WebSocket API for coaching endpoints:

**Pros:**
- ✅ Real-time bidirectional communication
- ✅ Can send progress updates
- ✅ No hard timeout on responses

**Cons:**
- ❌ Major infrastructure changes (new API Gateway, connection management)
- ❌ Requires refactoring entire coaching API
- ❌ Frontend must handle WebSocket connections
- ❌ More complex error handling and reconnection logic
- ❌ 3-4 weeks of development time

**Effort:** VERY HIGH (not justified for this problem)

---

### Option 3 - Try Inline with Timeout Guard

Attempt extraction inline but with a safety timeout:

```python
async def send_message(...):
    # ... existing code ...
    
    if is_final:
        try:
            # Try to complete within 25 seconds
            async with asyncio.timeout(25.0):
                completion = await self._extract_and_complete(...)
                return MessageResponse(..., result=completion.result)
        except asyncio.TimeoutError:
            # Fallback: just return is_final=true
            logger.warning("extraction_timeout_fallback")
            return MessageResponse(..., is_final=True, result=None)
```

**Pros:**
- ✅ Best of both worlds when it works
- ✅ Graceful degradation

**Cons:**
- ⚠️ Still requires frontend to handle missing results
- ⚠️ Wasted Bedrock LLM calls if timeout occurs
- ⚠️ Complex to get timeout value right (race conditions)
- ⚠️ Doesn't fully solve the problem

**Effort:** MEDIUM (3-5 hours + extensive testing)

---

### Option 4 - EventBridge + Polling (Over-engineered)

**NOT RECOMMENDED** - Too complex

Use EventBridge to trigger async extraction:

**Flow:**
1. `/message` returns with `is_final=true`
2. Publish EventBridge event
3. Separate Lambda processes extraction
4. Frontend polls `/session/{id}` until complete

**Pros:**
- ✅ Truly async
- ✅ Can handle very long operations

**Cons:**
- ❌ Requires EventBridge setup
- ❌ New Lambda function for extraction
- ❌ Polling adds latency
- ❌ More moving parts = more failure modes
- ❌ Overkill for 3-8 second extraction

**Effort:** HIGH (2-3 days)

---

## Recommendation: Implement Option 1

**Why Option 1 is Best:**

1. **Simplest**: Remove problematic code, use existing endpoint
2. **Safest**: Eliminates timeout risk completely
3. **Fastest to implement**: 1 day end-to-end
4. **Better UX**: Users see "Processing results..." instead of mysterious timeout
5. **Lowest risk**: No new infrastructure, minimal code changes
6. **Future-proof**: If extraction gets slower, still no timeout

**Implementation Plan:**

### Phase 1: Backend Changes (2 hours)

```python
# File: coaching/src/services/coaching_session_service.py
# Line: ~980 (in send_message method)

# BEFORE:
if is_final:
    logger.info("coaching_service.auto_completion_triggered", ...)
    completion_response = await self._extract_and_complete(...)
    return MessageResponse(..., result=completion_response.result)

# AFTER:
if is_final:
    logger.info(
        "coaching_service.final_message_detected",
        session_id=session_id,
        message="Client must call /complete endpoint for extraction"
    )
    # Return immediately - client must explicitly call /complete
    return MessageResponse(
        session_id=session_id,
        message=coach_message,
        status=session.status,
        turn=session.get_turn_count(),
        max_turns=session.max_turns,
        is_final=True,
        message_count=session.get_message_count(),
        result=None,  # Client must call /complete to get result
        metadata=response_metadata,
    )
```

### Phase 2: Frontend Changes (3 hours)

Update coaching message handler to detect `is_final` and call complete:

```typescript
// Pseudo-code - adapt to actual frontend structure
async function handleSendMessage(sessionId: string, message: string) {
    try {
        const response = await api.sendCoachingMessage(sessionId, message);
        
        // Add message to UI
        addMessageToChat(response.message);
        
        // Check if conversation is complete
        if (response.is_final) {
            // Show "Extracting your results..." indicator
            setProcessingResults(true);
            
            try {
                const completion = await api.completeCoachingSession(sessionId);
                
                // Show results
                handleSessionComplete(completion.result);
            } catch (error) {
                // Handle extraction errors
                showError("Failed to process results. Please try again.");
            } finally {
                setProcessingResults(false);
            }
        }
    } catch (error) {
        handleMessageError(error);
    }
}
```

### Phase 3: Testing (2 hours)

1. **Unit Tests**: Update message response tests for `result=None` when `is_final=true`
2. **Integration Tests**: Test `/message` → `/complete` flow
3. **Manual Testing**: Test with actual coaching sessions
4. **Load Testing**: Verify no timeouts under load

### Phase 4: Deployment & Monitoring

1. Deploy backend changes
2. Deploy frontend changes
3. Monitor CloudWatch for:
   - API Gateway 5xx errors (should decrease to near-zero)
   - Lambda duration on `/message` (should stay < 20s)
   - Lambda duration on `/complete` (should stay < 10s)

## Monitoring & Alerts

### CloudWatch Metrics to Track

```bash
# API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name coaching-api-5xx-errors \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold

# Lambda duration warning (25s threshold)
aws cloudwatch put-metric-alarm \
  --alarm-name coaching-lambda-duration-warning \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Maximum \
  --period 300 \
  --threshold 25000 \
  --comparison-operator GreaterThanThreshold
```

### Log Queries for Debugging

```
# Find timeout patterns
fields @timestamp, @message
| filter @message like /timeout|503|exceed/
| sort @timestamp desc
| limit 50

# Track LLM call durations
fields @timestamp, processing_time_ms, model_code
| filter @message like /llm_call_completed/
| stats max(processing_time_ms), avg(processing_time_ms), count() by model_code
```

## Alternative: Quick Wins (If Frontend Changes Blocked)

If frontend changes cannot be made immediately, implement **partial mitigations**:

### 1. Reduce Conversation Model Tier for Basic Users
```python
# For Basic/Starter tier users, use Haiku for conversations too
# This reduces conversation time from 8-15s to 3-6s
```

### 2. Implement Message History Truncation
```python
# Limit messages sent to LLM to reduce processing time
max_messages = 20  # Instead of 30
```

### 3. Add Lambda Warming
```python
# Keep Lambda warm to eliminate cold start delays
# Use EventBridge scheduled rule to ping every 5 minutes
```

### 4. Optimize DynamoDB Queries
```python
# Use batch writes for session updates
# Project only needed attributes in queries
```

**Expected Impact**: Reduce average time by 2-3 seconds (not enough to eliminate timeouts)

## Related Files

- [coaching/src/services/coaching_session_service.py](../../coaching/src/services/coaching_session_service.py) - Line 980 (send_message method)
- [coaching/src/api/routes/coaching_sessions.py](../../coaching/src/api/routes/coaching_sessions.py) - API endpoints
- [coaching/pulumi/index.ts](../../coaching/pulumi/index.ts) - Infrastructure config
- [ISSUE_API_GATEWAY_TIMEOUT.md](./ISSUE_API_GATEWAY_TIMEOUT.md) - Previous incident (Feb 9)

## Conclusion

**The good news:** The LLM is NOT incorrectly detecting completion mid-conversation. Log analysis shows `is_final=False` in the vast majority of responses.

**The problem:** When the conversation legitimately completes (or the LLM thinks it does), the automatic inline extraction can push total execution time beyond API Gateway's 30-second limit, especially when:
- Bedrock is experiencing latency or throttling
- Conversation history is large
- Multiple LLM calls queue up

**Recommended Solution: Implement Option 1 (Async Split)** for a clean, simple solution that:
- Eliminates timeouts permanently  
- Works regardless of LLM behavior (JSON vs plain text responses)
- Improves user experience with clear progress indicators
- Requires minimal code changes (remove auto-extraction)
- Uses existing infrastructure (the `/complete` endpoint already works!)

The `/complete` endpoint already exists and handles extraction correctly. We just need to:
1. **Stop auto-completing in `/message`** → Remove the inline extraction code
2. **Update frontend to call `/complete`** when `is_final=true` is detected

**Estimated Timeline:**
- Backend changes: 2 hours (remove auto-extraction)
- Frontend changes: 3 hours (add complete call after is_final)  
- Testing: 2 hours
- **Total: 1 day** (fastest, safest solution)

**Why this is the right approach:**
- ✅ Fix works even if LLM completion detection is imperfect
- ✅ Clear separation of concerns (conversation vs extraction)
- ✅ Better UX (users see "Processing your results...")
- ✅ No timeout risk regardless of Bedrock latency
- ✅ Minimal code changes, low risk
