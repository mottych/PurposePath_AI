# Action Plan: Fix 503 Timeouts on Coaching Messages

**Date**: February 10, 2026  
**Severity**: HIGH - Users experiencing 503 errors during coaching sessions

## Problem Statement

Users are getting 503 timeouts on **both final AND non-final** coaching messages:
- **4 recent 503s in last 10 minutes** (per user report)
- **4 documented timeouts in last 4 hours**: 76s, 42s, 42s, 37s
- **API Gateway hard limit**: 30 seconds (cannot be changed)
- **Observed "normal" LLM call times**: 20-21s (dangerously close to limit)

## Root Causes Identified

### 1. **Auto-Completion Inline Extraction** (Known Issue)
When `is_final=true` detected:
- Conversation: 8-15s + Extraction: 3-8s = 11-24s typical, 30-76s worst case
- **Fix**: Split into two API calls (already planned)

### 2. **Bedrock Latency/Throttling** (NEW Critical Issue)
Even **non-final** conversation-only messages are timing out:
- Single LLM call taking 20-30+ seconds
- Suggests Bedrock throttling, queuing, or service degradation
- **No extraction involved** in these timeouts

## Immediate Actions (Next 2 Hours)

### Action 1: Check Bedrock Service Status & Quotas

```bash
# Check Bedrock throttling metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name ModelInvocationThrottles \
  --dimensions Name=ModelId,Value=anthropic.claude-3-5-sonnet-20240620-v1:0 \
  --start-time 2026-02-10T17:00:00Z \
  --end-time 2026-02-10T20:00:00Z \
  --period 300 \
  --statistics Sum

# Check invocation latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name ModelInvocationLatency \
  --dimensions Name=ModelId,Value=anthropic.claude-3-5-sonnet-20240620-v1:0 \
  --start-time 2026-02-10T17:00:00Z \
  --end-time 2026-02-10T20:00:00Z \
  --period 300 \
  --statistics Average,Maximum

# Check current quotas
aws service-quotas get-service-quota \
  --service-code bedrock \
  --quota-code L-D3C4C6E8  # On-Demand tokens per minute
```

**Expected findings:**
- Throttle events > 0 → We're hitting rate limits
- Latency > 10s → Bedrock service issues
- Quota near limit → Need to request increase

### Action 2: Immediate Mitigation - Reduce Message History

**File**: `coaching/src/domain/entities/conversation_config.py`

```python
# Current
max_messages_to_llm: int = 30  # PROBLEM: Too large

# Change to
max_messages_to_llm: int = 15  # Reduce by 50%
```

**Rationale**: Fewer messages = smaller payload = faster LLM processing

**Expected impact**: Reduce LLM call time by 20-30%

### Action 3: Add Request Timeout Guard

**File**: `coaching/src/services/coaching_session_service.py`

Add timeout protection around LLM calls:

```python
async def _execute_llm_call(
    self,
    *,
    messages: list[dict[str, str]],
    llm_topic: LLMTopic,
    temperature_override: float | None = None,
    user_tier: TierLevel | None = None,
) -> tuple[str, ResponseMetadata]:
    """Execute LLM call with timeout protection."""
    import asyncio
    
    # ... existing code ...
    
    try:
        # Add 25-second timeout for LLM call
        # Allows 5s buffer for other operations before API Gateway timeout
        async with asyncio.timeout(25.0):
            response = await provider.generate(
                messages=llm_messages,
                model=model_name,
                temperature=temperature,
                max_tokens=llm_topic.max_tokens,
                system_prompt=system_prompt,
            )
    except asyncio.TimeoutError:
        logger.error(
            "coaching_service.llm_timeout",
            model_code=model_code,
            timeout_seconds=25,
            message_count=len(messages),
        )
        # Return fallback message
        return "I apologize, but I'm experiencing delays. Please try sending your message again.", ResponseMetadata(
            model=model_name,
            processing_time_ms=25000,
            tokens_used=0,
        )
    
    # ... rest of existing code ...
```

**Expected impact**: Prevents API Gateway timeout, returns graceful error to user

### Action 4: Switch to Faster Model for High-Load Periods

**File**: `coaching/src/domain/entities/llm_topic.py`

Consider temporarily using Haiku for ALL tiers during investigation:

```python
def get_model_code_for_tier(self, tier: TierLevel) -> str:
    """TEMPORARILY use Haiku for all tiers to reduce timeout risk."""
    # TODO: Revert after Bedrock throttling investigation
    return self.basic_model_code  # Usually CLAUDE_3_5_HAIKU
    
    # Original code (restore later):
    # if tier in (TierLevel.PREMIUM, TierLevel.ULTIMATE):
    #     return self.premium_model_code
    # return self.basic_model_code
```

**Rationale**: Haiku is 3-5x faster than Sonnet, quality still acceptable for coaching
**Expected impact**: Reduce LLM time from 15s → 5s

## Short-Term Actions (Next 24 Hours)

### Action 5: Split Extraction to Separate Call (Already Planned)

**File**: `coaching/src/services/coaching_session_service.py` line 979

```python
# REMOVE inline extraction
if is_final:
    logger.info(
        "coaching_service.final_message_detected",
        session_id=session_id,
    )
    return MessageResponse(
        session_id=session_id,
        message=coach_message,
        status=session.status,
        is_final=True,
        result=None,  # Frontend must call /complete
        # ... rest
    )
```

**Frontend change**: Call `/complete` endpoint when `is_final=true`

**Expected impact**: Eliminates 30-76s timeouts completely for completion flow

### Action 6: Add CloudWatch Alarms

```bash
# Alert on API Gateway 5xx errors
aws cloudwatch put-metric-alarm \
  --alarm-name coaching-api-5xx-high \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 300 \
  --threshold 3 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1

# Alert on Lambda duration approaching limit
aws cloudwatch put-metric-alarm \
  --alarm-name coaching-lambda-duration-critical \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --dimensions Name=FunctionName,Value=coaching-api-4b4d001 \
  --statistic Maximum \
  --period 60 \
  --threshold 25000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Action 7: Request Bedrock Quota Increase

If throttling detected:
1. Open AWS Support case requesting increased quota
2. Justify based on production usage patterns  
3. Request 2-3x current quota

## Long-Term Actions (Next Week)

### Option 1: Use Provisioned Throughput

Purchase guaranteed Bedrock capacity:
- Eliminates throttling
- Predictable latency
- Higher cost but better UX

### Option 2: Implement Retry with Exponential Backoff

Add intelligent retry logic for Bedrock throttling:

```python
async def _execute_llm_call_with_retry(self, ...):
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            return await self._execute_llm_call(...)
        except ThrottlingException:
            if attempt < max_retries:
                wait_time = (2 ** attempt) * 0.5  # 0.5s, 1s
                await asyncio.sleep(wait_time)
            else:
                raise
```

### Option 3: Add Caching Layer

Cache LLM responses for common coaching patterns:
- "Tell me about yourself" type questions
- Initial greeting responses
- Reduces Bedrock calls by 10-20%

## Monitoring & Validation

### Metrics to Track

1. **API Gateway 5xx rate** (target: <1%)
2. **Lambda duration p95** (target: <20s)
3. **Lambda duration max** (target: <25s)
4. **Bedrock throttle events** (target: 0)
5. **Bedrock invocation latency p95** (target: <10s)

### Success Criteria

- ✅ Zero 503 errors for 24 hours
- ✅ P95 response time < 15 seconds
- ✅ No Bedrock throttling events
- ✅ User complaints stop

## Rollback Plan

If immediate mitigations cause issues:

1. **Revert max_messages_to_llm**: Change back to 30
2. **Revert model selection**: Restore Sonnet for Premium/Ultimate
3. **Remove timeout guard**: If causing incorrect fallback responses

## Decision Log

| Action | Status | Owner | Deadline | Notes |
|--------|--------|-------|----------|-------|
| Check Bedrock metrics | ⏳ Pending | DevOps | 2h | Need AWS access |
| Reduce message history | ⏳ Pending | Backend | 2h | Low risk |
| Add timeout guard | ⏳ Pending | Backend | 4h | Test thoroughly |
| Split extraction call | ⏳ Pending | Backend + Frontend | 24h | Already planned |
| Request quota increase | ⏳ Pending | DevOps | 48h | If throttling confirmed |

## Communication Plan

**To Users** (if issues persist):
> "We're experiencing temporary delays with our AI coaching service due to high demand. We're actively working on improvements and expect resolution within 24 hours. Your progress is saved and you can retry your messages."

**To Team**:
- Immediate: Slack alert about active investigation
- Daily: Status update until resolved
- Post-resolution: Retrospective and permanent fixes

---

## Next Steps

**RIGHT NOW** (Priority 1):
1. Run Bedrock CloudWatch queries (Action 1)
2. If throttling detected → implement Actions 2, 3, 4 immediately
3. If no throttling → focus on Action 5 (split extraction)

**TODAY** (Priority 2):
4. Deploy Action 5 (split extraction to separate call)
5. Set up CloudWatch alarms (Action 6)
6. Monitor for 4 hours after deployment

**THIS WEEK** (Priority 3):
7. Evaluate provisioned throughput vs retry strategies
8. Implement chosen long-term solution
9. Complete retrospective

