# Business Data Integration Architecture

## 🎯 Core Principle
**.NET API owns ALL business data** - Coaching service accesses via orchestration patterns

## 📊 Data Ownership

### Python Coaching Service Owns
```yaml
✅ conversations - AI chat history
✅ coaching-sessions - Session tracking
```

### .NET API Service Owns  
```yaml
✅ business-data - Business foundation data
✅ users, tenants, subscriptions - Account data
✅ goals, actions, kpis, reviews - Business entities
✅ ALL other business domain tables
```

## 🔀 Integration Patterns

### Pattern 1: Frontend Data Payload
**Use Case**: Lightweight coaching with known context

**Flow:**
```
Frontend → (business context) → Coaching API → AI Response
```

**Request Example:**
```json
{
  "message": "Help me prioritize my goals",
  "conversation_id": "conv123",
  "business_context": {
    "user": {
      "id": "user123",
      "name": "John Smith", 
      "role": "CEO"
    },
    "tenant": {
      "id": "tenant123",
      "company": "Acme Corp",
      "industry": "SaaS"
    },
    "goals": [
      {
        "id": "goal1",
        "title": "Increase Revenue",
        "status": "in_progress",
        "target_value": 1000000
      }
    ],
    "recent_actions": [
      {
        "id": "action1", 
        "title": "Launch marketing campaign",
        "status": "completed"
      }
    ]
  }
}
```

### Pattern 2: Step Functions Orchestrator
**Use Case**: Complex analysis requiring full business data

**Flow:**
```
Frontend → Step Functions → .NET API (data) → Coaching API (enriched) → Response
```

**Step Function Definition:**
```json
{
  "Comment": "Coaching with business data enrichment",
  "StartAt": "GetBusinessData",
  "States": {
    "GetBusinessData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:region:account:function:dotnet-business-data-api",
      "Parameters": {
        "user_id.$": "$.user_id",
        "tenant_id.$": "$.tenant_id",
        "data_scope": "coaching_context"
      },
      "ResultPath": "$.business_data",
      "Next": "ProcessCoaching"
    },
    "ProcessCoaching": {
      "Type": "Task", 
      "Resource": "arn:aws:lambda:region:account:function:python-coaching-api",
      "Parameters": {
        "message.$": "$.message",
        "conversation_id.$": "$.conversation_id",
        "business_context.$": "$.business_data"
      },
      "End": true
    }
  }
}
```

## 🏗️ Implementation Architecture

### .NET Business Data API
```csharp
[HttpGet("business-context")]
public async Task<IActionResult> GetBusinessContext(
    [FromQuery] string userId,
    [FromQuery] string tenantId, 
    [FromQuery] string scope = "coaching_context")
{
    var context = new BusinessContext
    {
        User = await _userRepository.GetByIdAsync(userId),
        Goals = await _goalRepository.GetByTenantAsync(tenantId),
        RecentActions = await _actionRepository.GetRecentAsync(tenantId, 30),
        KPIs = await _kpiRepository.GetActiveAsync(tenantId)
    };
    
    return Ok(context);
}
```

### Python Coaching API Contract
```python
class CoachingRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    business_context: Optional[BusinessContext] = None
    
class BusinessContext(BaseModel):
    user: Optional[UserContext] = None
    tenant: Optional[TenantContext] = None
    goals: List[GoalContext] = []
    recent_actions: List[ActionContext] = []
    kpis: List[KpiContext] = []
```

## 🔄 Decision Matrix

| Scenario | Pattern | Rationale |
|----------|---------|-----------|
| Quick goal advice | Frontend Payload | Small data, fast response |
| Strategic analysis | Step Functions | Complex data aggregation |
| Real-time chat | Frontend Payload | Low latency required |
| Business insights | Step Functions | Full context needed |
| Onboarding help | Frontend Payload | Known user context |

## 🚀 Implementation Priority

1. **Phase 1**: Update coaching service to accept business_context payload
2. **Phase 2**: Create .NET business data API endpoint  
3. **Phase 3**: Build Step Functions orchestrator
4. **Phase 4**: Frontend integration for both patterns

## ✅ Benefits

- **Single Source of Truth**: .NET owns all business logic
- **Performance Flexibility**: Choose pattern by use case  
- **Clean Separation**: No schema synchronization needed
- **Scalable**: Easy to add new business data without coaching changes
- **Testable**: Clear contracts and boundaries