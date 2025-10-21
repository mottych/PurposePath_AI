# Implement Token Usage Tracking by Tenant

## 🎯 Overview

Implement comprehensive token usage tracking and cost analytics for all LLM calls. AWS Bedrock returns accurate token counts in every response, but we're not currently storing this data. This feature will enable usage monitoring, cost tracking, tenant billing, and admin analytics.

## 💡 Key Insight

**You were correct!** Token counting is already available from Bedrock - we just need to store and expose it.

```json
{
  "usage": {
    "inputTokens": 245,
    "outputTokens": 156,
    "totalTokens": 401
  }
}
```

## 📋 Requirements

### Business Requirements
- Track token usage per tenant
- Calculate costs per LLM call
- Store usage metrics for analytics
- Support admin dashboard queries
- Enable billing/chargeback if needed

### Technical Requirements
- Store token data with each conversation message
- Aggregate usage by tenant, date, model, topic
- Support time-range queries
- Track: input tokens, output tokens, total tokens, cost, model, timestamp
- No performance impact on conversation flow

## 🏗️ Architecture

```
LLM Call
    ↓
Bedrock Response (includes token counts)
    ↓
Extract: inputTokens, outputTokens
    ↓
Calculate: cost = (input * input_rate) + (output * output_rate)
    ↓
Store in Message with tokens metadata
    ↓
Save to DynamoDB (conversations table)
    ↓
[Optional] Aggregate to usage analytics table
    ↓
Admin API queries for analytics
```

## 📁 Files to Modify/Create

### Modify

1. **`coaching/src/domain/value_objects/message.py`**
   - Add token tracking fields
   - Add cost calculation

2. **`coaching/src/infrastructure/llm/bedrock_provider.py`**
   - Extract token counts from responses
   - Return token metadata

3. **`coaching/src/infrastructure/repositories/dynamodb_conversation_repository.py`**
   - Store token data in message items
   - Add usage query methods

4. **`coaching/src/services/conversation_service.py`**
   - Pass token data when creating messages

### Create

5. **`coaching/src/services/usage_analytics_service.py`**
   - Aggregate usage queries
   - Calculate costs
   - Generate reports

6. **`coaching/src/models/usage_models.py`**
   - UsageRecord
   - UsageAnalytics
   - CostBreakdown

7. **`coaching/src/api/routes/admin/usage.py`** (Part of Admin API - Phase 1)
   - Admin endpoints for usage analytics

## 🔧 Implementation Details

### Step 1: Update Message Model

```python
# coaching/src/domain/value_objects/message.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict

@dataclass
class Message:
    """Represents a conversation message with LLM metadata."""
    
    content: str
    role: str  # "user" | "assistant" | "system"
    timestamp: datetime
    
    # NEW: Token tracking
    tokens: Optional[Dict[str, int]] = None
    # {
    #   "input": 245,
    #   "output": 156,
    #   "total": 401
    # }
    
    cost: Optional[float] = None  # Cost in USD
    model_id: Optional[str] = None  # e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0"
    
    def calculate_cost(self, input_rate: float, output_rate: float) -> float:
        """Calculate cost based on token counts and pricing."""
        if not self.tokens:
            return 0.0
        
        input_cost = (self.tokens["input"] / 1000) * input_rate
        output_cost = (self.tokens["output"] / 1000) * output_rate
        return input_cost + output_cost
```

### Step 2: Extract Token Data from Bedrock

```python
# coaching/src/infrastructure/llm/bedrock_provider.py

async def generate(
    self,
    messages: List[Dict[str, str]],
    model: str = "anthropic.claude-3-5-sonnet-20241022-v2:0",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    system_prompt: Optional[str] = None,
) -> Tuple[str, Dict[str, int]]:  # CHANGED: Return tokens too
    """
    Generate response from Bedrock.
    
    Returns:
        Tuple of (response_text, token_usage_dict)
    """
    
    # ... existing request logic ...
    
    response = self.bedrock_client.invoke_model(
        modelId=model,
        body=json.dumps(request_body)
    )
    
    response_body = json.loads(response['body'].read())
    
    # Extract content
    content_blocks = response_body.get('content', [])
    response_text = next(
        (block['text'] for block in content_blocks if block['type'] == 'text'),
        ''
    )
    
    # NEW: Extract token usage
    usage = response_body.get('usage', {})
    token_usage = {
        "input": usage.get('inputTokens', 0),
        "output": usage.get('outputTokens', 0),
        "total": usage.get('inputTokens', 0) + usage.get('outputTokens', 0)
    }
    
    logger.info(
        "LLM response generated",
        model=model,
        tokens_input=token_usage["input"],
        tokens_output=token_usage["output"],
        tokens_total=token_usage["total"]
    )
    
    return response_text, token_usage
```

### Step 3: Model Pricing Configuration

```python
# coaching/src/infrastructure/llm/model_pricing.py

from typing import Dict

# Pricing per 1K tokens (as of Oct 2025)
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "input": 0.003,   # $3.00 per 1M tokens
        "output": 0.015   # $15.00 per 1M tokens
    },
    "anthropic.claude-3-haiku-20240307-v1:0": {
        "input": 0.00025,  # $0.25 per 1M tokens
        "output": 0.00125  # $1.25 per 1M tokens
    },
    "anthropic.claude-3-opus-20240229-v1:0": {
        "input": 0.015,   # $15.00 per 1M tokens
        "output": 0.075   # $75.00 per 1M tokens
    }
}

def get_model_pricing(model_id: str) -> Dict[str, float]:
    """Get pricing for a model."""
    return MODEL_PRICING.get(model_id, {"input": 0.0, "output": 0.0})

def calculate_cost(input_tokens: int, output_tokens: int, model_id: str) -> float:
    """Calculate cost for token usage."""
    pricing = get_model_pricing(model_id)
    
    input_cost = (input_tokens / 1000) * pricing["input"]
    output_cost = (output_tokens / 1000) * pricing["output"]
    
    return round(input_cost + output_cost, 6)  # Round to 6 decimals
```

### Step 4: Store Token Data

```python
# coaching/src/services/conversation_service.py

async def send_message(
    self, 
    conversation_id: str, 
    user_message: str
) -> Message:
    """Send user message and get AI response."""
    
    # ... existing logic ...
    
    # Call LLM
    response_text, token_usage = await self.llm_service.generate(
        messages=message_history,
        model=model_id
    )
    
    # Calculate cost
    from coaching.src.infrastructure.llm.model_pricing import calculate_cost
    cost = calculate_cost(
        token_usage["input"],
        token_usage["output"],
        model_id
    )
    
    # Create assistant message with token data
    assistant_message = Message(
        content=response_text,
        role="assistant",
        timestamp=datetime.now(UTC),
        tokens=token_usage,
        cost=cost,
        model_id=model_id
    )
    
    # Save to conversation
    conversation.add_message(assistant_message)
    await self.conversation_repo.update(conversation)
    
    logger.info(
        "Message sent with token tracking",
        conversation_id=conversation_id,
        tokens=token_usage["total"],
        cost=cost,
        model=model_id
    )
    
    return assistant_message
```

### Step 5: DynamoDB Storage

```python
# coaching/src/infrastructure/repositories/dynamodb_conversation_repository.py

def _message_to_dict(self, message: Message) -> Dict[str, Any]:
    """Convert Message to DynamoDB dict."""
    item = {
        "content": message.content,
        "role": message.role,
        "timestamp": message.timestamp.isoformat(),
    }
    
    # NEW: Include token data
    if message.tokens:
        item["tokens"] = message.tokens
    if message.cost is not None:
        item["cost"] = Decimal(str(message.cost))  # DynamoDB requires Decimal
    if message.model_id:
        item["model_id"] = message.model_id
    
    return item

def _dict_to_message(self, item: Dict[str, Any]) -> Message:
    """Convert DynamoDB dict to Message."""
    return Message(
        content=item["content"],
        role=item["role"],
        timestamp=datetime.fromisoformat(item["timestamp"]),
        tokens=item.get("tokens"),
        cost=float(item["cost"]) if "cost" in item else None,
        model_id=item.get("model_id")
    )
```

### Step 6: Usage Analytics Service

```python
# coaching/src/services/usage_analytics_service.py

from datetime import datetime, timedelta
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()

class UsageAnalyticsService:
    """Service for querying token usage and cost analytics."""
    
    def __init__(self, conversation_repo):
        self.conversation_repo = conversation_repo
    
    async def get_tenant_usage(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get usage analytics for a tenant in date range."""
        
        # Query conversations in date range
        conversations = await self.conversation_repo.find_by_tenant(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Aggregate token usage
        total_tokens = 0
        total_cost = 0.0
        total_requests = 0
        by_model = {}
        by_topic = {}
        
        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "assistant" and msg.tokens:
                    total_tokens += msg.tokens["total"]
                    total_cost += msg.cost or 0.0
                    total_requests += 1
                    
                    # Group by model
                    model_id = msg.model_id or "unknown"
                    if model_id not in by_model:
                        by_model[model_id] = {
                            "requests": 0,
                            "tokens": 0,
                            "cost": 0.0
                        }
                    by_model[model_id]["requests"] += 1
                    by_model[model_id]["tokens"] += msg.tokens["total"]
                    by_model[model_id]["cost"] += msg.cost or 0.0
                    
                    # Group by topic
                    topic = conv.topic
                    if topic not in by_topic:
                        by_topic[topic] = {
                            "requests": 0,
                            "tokens": 0,
                            "cost": 0.0
                        }
                    by_topic[topic]["requests"] += 1
                    by_topic[topic]["tokens"] += msg.tokens["total"]
                    by_topic[topic]["cost"] += msg.cost or 0.0
        
        return {
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost": round(total_cost, 2),
                "average_tokens_per_request": total_tokens // total_requests if total_requests > 0 else 0,
                "average_cost_per_request": round(total_cost / total_requests, 4) if total_requests > 0 else 0.0
            },
            "by_model": by_model,
            "by_topic": by_topic
        }
    
    async def get_all_tenants_usage(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get usage for all tenants (admin view)."""
        
        # This would require a GSI on tenant_id + timestamp
        # Or scan all conversations (expensive)
        # Better approach: Store daily aggregates
        ...
```

## ✅ Acceptance Criteria

### Data Storage
- [ ] All LLM responses store token counts (input, output, total)
- [ ] All LLM responses store calculated cost
- [ ] All LLM responses store model ID
- [ ] Token data persists in DynamoDB with messages

### Cost Calculation
- [ ] Model pricing configuration exists for all supported models
- [ ] Costs calculated accurately (per 1K tokens)
- [ ] Costs rounded to 6 decimal places
- [ ] Costs stored as Decimal in DynamoDB

### Analytics
- [ ] Query usage by tenant + date range
- [ ] Aggregate by model
- [ ] Aggregate by topic
- [ ] Calculate: total requests, total tokens, total cost, averages

### Performance
- [ ] No performance impact on conversation flow
- [ ] Token storage adds < 10ms per message
- [ ] Analytics queries return in < 2 seconds

### Logging
- [ ] Log token usage with each LLM call
- [ ] Log cost with each LLM call
- [ ] Structured logs for monitoring

## 🧪 Testing Requirements

### Unit Tests

```python
# tests/unit/test_message_model.py

def test_message_with_tokens():
    """Test Message with token metadata."""
    msg = Message(
        content="Test",
        role="assistant",
        timestamp=datetime.now(),
        tokens={"input": 100, "output": 50, "total": 150},
        cost=0.0015,
        model_id="anthropic.claude-3-haiku-20240307-v1:0"
    )
    assert msg.tokens["total"] == 150
    assert msg.cost == 0.0015

def test_calculate_cost():
    """Test cost calculation."""
    msg = Message(
        content="Test",
        role="assistant",
        timestamp=datetime.now(),
        tokens={"input": 1000, "output": 500, "total": 1500}
    )
    # Claude Haiku: $0.00025 input, $0.00125 output per 1K tokens
    cost = msg.calculate_cost(0.00025, 0.00125)
    assert cost == 0.000875  # (1000/1000 * 0.00025) + (500/1000 * 0.00125)
```

### Integration Tests

```python
# tests/integration/test_token_tracking.py

async def test_conversation_stores_tokens():
    """Test that tokens are stored with conversation messages."""
    # Send message
    response = await conversation_service.send_message(conv_id, "Hello")
    
    # Verify message has token data
    assert response.tokens is not None
    assert response.tokens["total"] > 0
    assert response.cost > 0
    assert response.model_id is not None
    
    # Retrieve from DB
    conv = await conversation_repo.get_by_id(conv_id)
    last_message = conv.messages[-1]
    assert last_message.tokens == response.tokens
    assert last_message.cost == response.cost
```

## 📊 Monitoring & Observability

### CloudWatch Metrics
- `TokenUsage.Total` (per tenant)
- `TokenUsage.Cost` (per tenant)
- `TokenUsage.RequestCount` (per tenant)
- `TokenUsage.AveragePerRequest`

### CloudWatch Alarms
- Alert if daily cost > $100 for any tenant
- Alert if tokens/request > 10,000 (potential infinite loop)
- Alert if cost calculation fails

### Logs
```python
logger.info(
    "LLM call completed",
    tenant_id=tenant_id,
    conversation_id=conversation_id,
    model=model_id,
    tokens_input=tokens["input"],
    tokens_output=tokens["output"],
    tokens_total=tokens["total"],
    cost_usd=cost
)
```

## 🔗 Dependencies

- ✅ Bedrock Provider (returns token counts)
- ✅ Message Model (can add fields)
- ✅ DynamoDB Repository (can store additional fields)
- ✅ Conversation Service (orchestrates flow)
- ⚠️ Model pricing config (new)
- ⚠️ Usage analytics service (new)

## 📈 Estimated Effort

- **Update Message model:** 1 hour
- **Update Bedrock provider:** 2 hours
- **Model pricing config:** 1 hour
- **Update conversation service:** 2 hours
- **Update DynamoDB repository:** 2 hours
- **Usage analytics service:** 3-4 hours
- **Testing:** 2-3 hours
- **Total:** 13-15 hours

## 🚀 Deployment Notes

1. Update DynamoDB table (no schema changes needed - flexible schema)
2. Deploy new code
3. Backfill: Existing messages won't have token data (acceptable)
4. Monitor CloudWatch for cost tracking
5. Set up billing alerts

## 📚 References

- Bedrock pricing: https://aws.amazon.com/bedrock/pricing/
- Bedrock API docs: https://docs.aws.amazon.com/bedrock/
- Admin spec: `docs/Specifications/pp_ai_backend_specification.md` (Lines 518-627)

## 👥 Assignee

- Backend Developer familiar with AWS Bedrock

## 🏷️ Labels

`feature`, `analytics`, `monitoring`, `high-priority`, `backend`

---

**Created:** 2025-10-21  
**Status:** Ready for Implementation  
**Priority:** HIGH
