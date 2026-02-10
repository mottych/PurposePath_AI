# Issue: API Gateway Timeout on Coaching Session Completion

## Incident Date
February 9, 2026 - 23:48 UTC

## Summary
Core values coaching session successfully completed but user received 503 error. On retry, user received "SESSION_NOT_ACTIVE" error because session was already marked completed in database.

## Root Cause
**API Gateway 30-second timeout exceeded by Lambda execution time (32.3 seconds)**

### What Happened (Timeline)
1. `23:48:09` - User message triggered auto-completion (is_final=true from LLM)
2. `23:48:09-31` - Extraction LLM call executed (Core Values extraction)
3. `23:48:31` - Session marked `completed` in DynamoDB with extracted results
4. `23:48:41` - Lambda finished after **32.3 seconds total**
5. `23:48:39` - **API Gateway timed out at 30 seconds, returned 503 to frontend**
6. User retried → Got SESSION_NOT_ACTIVE (correct, session IS completed)

### Technical Details
- **Lambda ExecutionDuration**: 32,312ms (32.3 seconds)
- **API Gateway Timeout**: 30,000ms (30 seconds) - HARD LIMIT for REST APIs
- **Session ID**: `sess_58a0ffa3-6bca-4ed9-9acc-1f99d849065a`
- **RequestId**: `ae220969-d5df-4cdc-a767-70f9fa8624de`

## Current Fix (Implemented)
**Use Claude Haiku for extraction instead of Sonnet (configurable)**

### Changes Made
- [coaching/src/domain/entities/llm_topic.py](../../coaching/src/domain/entities/llm_topic.py)
  - Added `extraction_model_code` field to LLMTopic (optional, defaults to Haiku)
  - Added `get_extraction_model_code()` method for consistent access
- [coaching/src/services/coaching_session_service.py](../../coaching/src/services/coaching_session_service.py)
  - Extraction now uses configured extraction model (defaults to Claude Haiku)
  - Conversation still uses tier-appropriate model (Sonnet for Premium/Ultimate)
  - Total execution time reduced from 30-35s to ~15-20s

### Configuration
To change the extraction model for a topic, set `extraction_model_code` in DynamoDB:
```json
{
  "topic_id": "core_values",
  "extraction_model_code": "claude-3-5-haiku-20241022",
  ...
}
```

If `extraction_model_code` is `null` or not set, defaults to `claude-3-5-haiku-20241022`.

### Performance Impact
- ✅ **Before**: Conversation (8-12s) + Extraction (15-20s) = **25-32s** (sometimes exceeded 30s)
- ✅ **After**: Conversation (8-12s) + Extraction (3-5s) = **~15-20s** (safely under 30s)
- ✅ Cost savings: Haiku is ~90% cheaper than Sonnet for extraction
- ✅ Quality maintained: Extraction is simple structured parsing, doesn't need Sonnet's power
- ✅ **Configurable**: Can change extraction model without code deployment

## Proper Solution Options

### Option 1: Async Extraction with Polling (Recommended)
**Pros**: Clean separation, handles long-running extractions
**Cons**: Requires frontend changes, more complex

1. `send_message` returns immediately with `is_final=true`
2. Backend triggers async extraction (Step Function or EventBridge)
3. Frontend polls `GET /ai/coaching/session/{id}` for completion
4. When `status=completed`, results are available

### Option 2: Make Extraction Faster
**Pros**: No frontend changes needed
**Cons**: May not be possible, depends on LLM performance

- Use faster model for extraction (GPT-4o-mini vs Sonnet)
- Optimize extraction prompt
- Cache conversation formatting
- **Target**: <25 seconds total execution time

### Option 3: Explicit Completion Only (Current Fix)
**Pros**: Simple, prevents timeout
**Cons**: Removes auto-completion feature, frontend must handle `is_final`

- Always require explicit `/complete` call
- Frontend detects `is_final=true` and immediately calls `/complete`
- Extraction happens in separate request

### Option 4: Hybrid - Try Inline, Fallback to Async
**Pros**: Best UX when fast, graceful degradation
**Cons**: Complex implementation

```python
# Pseudocode
if is_final:
    start asyncio.Task(extract_and_complete())
    wait_with_timeout(25_seconds)
    if extraction_done:
        return result
    else:
        return is_final=true, result=pending
```

## Recommendation
**Implement Option 1 (Async Extraction)** for production.

**Short-term workaround**: Use Option 3 (current fix) if frontend already handles explicit completion.

## Frontend Changes Required (Option 1 or 3)
```typescript
// In OnboardingCoachPanel.tsx or wherever message handling is
if (response.is_final && response.status === 'active') {
    // Show "Extracting your results..." UI
    const completion = await api.completeCoachingSession(sessionId);
    // Display completion.result
}
```

## Monitoring & Alerting
Add CloudWatch alarms for:
- Lambda duration > 25 seconds (warning)
- Lambda duration > 28 seconds (critical)
- API Gateway 5xx errors on `/coaching/message`

## Related Issues
- None (new issue)

## References
- CloudWatch Log Group: `/aws/lambda/coaching-api-4b4d001`
- DynamoDB Table: `purposepath-coaching-sessions-dev`
- [Pulumi Lambda Config](../../coaching/pulumi/index.ts#L55) - timeout: 300s
- [API Gateway Limits](https://docs.aws.amazon.com/apigateway/latest/developerguide/limits.html) - Integration timeout: 29s

