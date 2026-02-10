# Async Coaching Message Events - EventBridge Specification

**Version**: 1.0.0  
**Date**: February 10, 2026  
**Related Issue**: #222

## Overview

This specification defines three new EventBridge events for asynchronous coaching message processing. These events enable the coaching service to avoid API Gateway 30s timeout by processing messages asynchronously and delivering complete responses via WebSocket.

**Event Flow**:
```
1. Frontend: POST /ai/coaching/message → 202 Accepted {job_id}
2. Backend: Publishes ai.message.created event
3. Worker Lambda: Processes message (5s - 5min)
4. Backend: Publishes ai.message.completed or ai.message.failed
5. .NET WebSocket Service: Receives event → Forwards to frontend
```

## Event Source

- **Source**: `purposepath.ai`
- **Event Bus**: `default`
- **Region**: `us-east-1`

## Event Types

### 1. `ai.message.created`

**Purpose**: Triggers async message processing by worker Lambda

**When Published**: Immediately after POST /ai/coaching/message returns 202 Accepted

**Event Structure**:
```json
{
  "version": "0",
  "id": "uuid",
  "detail-type": "ai.message.created",
  "source": "purposepath.ai",
  "time": "2026-02-10T23:00:00Z",
  "region": "us-east-1",
  "resources": [],
  "detail": {
    "jobId": "uuid",
    "tenantId": "uuid",
    "userId": "uuid",
    "topicId": "conversation_coaching",
    "eventType": "ai.message.created",
    "stage": "dev",
    "data": {
      "jobId": "uuid",
      "sessionId": "uuid",
      "topicId": "conversation_coaching",
      "userMessage": "User's message content here"
    }
  }
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detail.jobId` | string (UUID) | Yes | Unique job identifier for tracking |
| `detail.tenantId` | string (UUID) | Yes | Tenant identifier for routing |
| `detail.userId` | string (UUID) | Yes | User identifier for routing |
| `detail.topicId` | string | Yes | Coaching topic ID (e.g., "conversation_coaching") |
| `detail.eventType` | string | Yes | Always "ai.message.created" |
| `detail.stage` | string | Yes | Environment: "dev", "staging", or "production" |
| `detail.data.sessionId` | string (UUID) | Yes | Coaching session identifier |
| `detail.data.userMessage` | string | Yes | The user's message content |

**⚠️ .NET Backend Action**: This event is consumed by Python worker Lambda only. .NET service should **NOT** handle this event.

---

### 2. `ai.message.completed`

**Purpose**: Delivers the complete AI response to frontend via WebSocket

**When Published**: After successful message processing by worker Lambda

**Event Structure**:
```json
{
  "version": "0",
  "id": "uuid",
  "detail-type": "ai.message.completed",
  "source": "purposepath.ai",
  "time": "2026-02-10T23:00:15Z",
  "region": "us-east-1",
  "resources": [],
  "detail": {
    "jobId": "uuid",
    "tenantId": "uuid",
    "userId": "uuid",
    "topicId": "conversation_coaching",
    "eventType": "ai.message.completed",
    "stage": "dev",
    "data": {
      "jobId": "uuid",
      "sessionId": "uuid",
      "topicId": "conversation_coaching",
      "message": "Complete AI coach response here. This is the full response with no streaming.",
      "isFinal": false,
      "result": null
    }
  }
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detail.jobId` | string (UUID) | Yes | Unique job identifier |
| `detail.tenantId` | string (UUID) | Yes | Tenant identifier for routing |
| `detail.userId` | string (UUID) | Yes | User identifier for routing |
| `detail.topicId` | string | Yes | Coaching topic ID |
| `detail.eventType` | string | Yes | Always "ai.message.completed" |
| `detail.stage` | string | Yes | Environment filter |
| `detail.data.sessionId` | string (UUID) | Yes | Coaching session identifier |
| `detail.data.message` | string | Yes | **Complete AI response** (no streaming) |
| `detail.data.isFinal` | boolean | Yes | Whether this is the final message in conversation |
| `detail.data.result` | object \| null | Yes | Extraction result (only when `isFinal` is true) |

**Result Object Structure** (when `isFinal` is true):
```json
{
  "result": {
    "extraction_type": "conversation_result",
    "identified_values": ["value1", "value2", "value3"],
    "progress": 1.0,
    "metadata": {
      "model_used": "claude-3-5-haiku",
      "extraction_success": true
    }
  }
}
```

**✅ .NET Backend Action**: 
1. Subscribe to EventBridge for events where `detail-type` = "ai.message.completed"
2. Filter by `detail.stage` matching your environment
3. Forward to WebSocket clients matching `tenantId` and `userId`
4. Send **complete message** (no token streaming needed)

**WebSocket Payload to Frontend**:
```typescript
{
  eventType: "ai.message.completed",
  jobId: string,
  sessionId: string,
  tenantId: string,
  userId: string,
  data: {
    message: string,        // Complete AI response
    isFinal: boolean,       // Whether conversation is ending
    result: object | null   // Extraction result if final
  }
}
```

---

### 3. `ai.message.failed`

**Purpose**: Notifies frontend of message processing failure

**When Published**: When worker Lambda encounters an error

**Event Structure**:
```json
{
  "version": "0",
  "id": "uuid",
  "detail-type": "ai.message.failed",
  "source": "purposepath.ai",
  "time": "2026-02-10T23:00:15Z",
  "region": "us-east-1",
  "resources": [],
  "detail": {
    "jobId": "uuid",
    "tenantId": "uuid",
    "userId": "uuid",
    "topicId": "conversation_coaching",
    "eventType": "ai.message.failed",
    "stage": "dev",
    "data": {
      "jobId": "uuid",
      "sessionId": "uuid",
      "topicId": "conversation_coaching",
      "error": "Session not found",
      "errorCode": "SESSION_NOT_FOUND"
    }
  }
}
```

**Field Descriptions**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `detail.jobId` | string (UUID) | Yes | Unique job identifier |
| `detail.tenantId` | string (UUID) | Yes | Tenant identifier for routing |
| `detail.userId` | string (UUID) | Yes | User identifier for routing |
| `detail.topicId` | string | Yes | Coaching topic ID |
| `detail.eventType` | string | Yes | Always "ai.message.failed" |
| `detail.stage` | string | Yes | Environment filter |
| `detail.data.sessionId` | string (UUID) | Yes | Coaching session identifier |
| `detail.data.error` | string | Yes | Human-readable error message |
| `detail.data.errorCode` | string | Yes | Machine-readable error code |

**Error Codes**:

| Code | Description |
|------|-------------|
| `SESSION_NOT_FOUND` | Session doesn't exist |
| `SESSION_ACCESS_DENIED` | User doesn't own session |
| `SESSION_NOT_ACTIVE` | Session is paused or completed |
| `SESSION_IDLE_TIMEOUT` | Session expired due to inactivity |
| `MAX_TURNS_REACHED` | Conversation exceeded max turns |
| `LLM_TIMEOUT` | LLM request timed out |
| `LLM_ERROR` | LLM returned an error |
| `EXTRACTION_FAILED` | Failed to extract result |
| `INTERNAL_ERROR` | Unexpected system error |

**✅ .NET Backend Action**: 
1. Subscribe to EventBridge for events where `detail-type` = "ai.message.failed"
2. Filter by `detail.stage` matching your environment
3. Forward to WebSocket clients matching `tenantId` and `userId`

**WebSocket Payload to Frontend**:
```typescript
{
  eventType: "ai.message.failed",
  jobId: string,
  sessionId: string,
  tenantId: string,
  userId: string,
  data: {
    error: string,
    errorCode: string
  }
}
```

---

## .NET Implementation Guide

### EventBridge Subscription Setup

```csharp
// AWS SDK for .NET - EventBridge Rule
var rule = new Amazon.EventBridge.Model.PutRuleRequest
{
    Name = "coaching-message-events-websocket",
    EventBusName = "default",
    State = RuleState.ENABLED,
    EventPattern = JsonSerializer.Serialize(new
    {
        source = new[] { "purposepath.ai" },
        detail_type = new[] { "ai.message.completed", "ai.message.failed" },
        detail = new
        {
            stage = new[] { Environment.GetEnvironmentVariable("STAGE") ?? "dev" }
        }
    })
};

// Target: Lambda function that forwards to WebSocket API
var target = new Amazon.EventBridge.Model.Target
{
    Arn = lambdaArn,
    Id = "websocket-forwarder"
};
```

### Event Handler Example

```csharp
public class CoachingMessageEventHandler
{
    private readonly IWebSocketService _webSocketService;
    private readonly ILogger<CoachingMessageEventHandler> _logger;

    public async Task<APIGatewayProxyResponse> HandleEventBridgeEvent(
        EventBridgeEvent<CoachingMessageEventDetail> eventBridgeEvent)
    {
        var detail = eventBridgeEvent.Detail;
        
        // Validate event
        if (string.IsNullOrEmpty(detail.TenantId) || string.IsNullOrEmpty(detail.UserId))
        {
            _logger.LogWarning("Invalid event: missing tenantId or userId");
            return new APIGatewayProxyResponse { StatusCode = 400 };
        }

        // Route based on event type
        switch (eventBridgeEvent.DetailType)
        {
            case "ai.message.completed":
                await HandleMessageCompleted(detail);
                break;
                
            case "ai.message.failed":
                await HandleMessageFailed(detail);
                break;
                
            default:
                _logger.LogWarning($"Unknown event type: {eventBridgeEvent.DetailType}");
                return new APIGatewayProxyResponse { StatusCode = 400 };
        }

        return new APIGatewayProxyResponse { StatusCode = 200 };
    }

    private async Task HandleMessageCompleted(CoachingMessageEventDetail detail)
    {
        var payload = new
        {
            eventType = "ai.message.completed",
            jobId = detail.JobId,
            sessionId = detail.Data.SessionId,
            tenantId = detail.TenantId,
            userId = detail.UserId,
            data = new
            {
                message = detail.Data.Message,
                isFinal = detail.Data.IsFinal,
                result = detail.Data.Result
            }
        };

        // Forward to WebSocket clients
        await _webSocketService.SendToUser(
            tenantId: detail.TenantId,
            userId: detail.UserId,
            message: JsonSerializer.Serialize(payload)
        );

        _logger.LogInformation(
            "Forwarded ai.message.completed to user {UserId} in tenant {TenantId}",
            detail.UserId, detail.TenantId);
    }

    private async Task HandleMessageFailed(CoachingMessageEventDetail detail)
    {
        var payload = new
        {
            eventType = "ai.message.failed",
            jobId = detail.JobId,
            sessionId = detail.Data.SessionId,
            tenantId = detail.TenantId,
            userId = detail.UserId,
            data = new
            {
                error = detail.Data.Error,
                errorCode = detail.Data.ErrorCode
            }
        };

        await _webSocketService.SendToUser(
            tenantId: detail.TenantId,
            userId: detail.UserId,
            message: JsonSerializer.Serialize(payload)
        );

        _logger.LogWarning(
            "Forwarded ai.message.failed to user {UserId}: {ErrorCode}",
            detail.UserId, detail.Data.ErrorCode);
    }
}

// Model Classes
public class CoachingMessageEventDetail
{
    public string JobId { get; set; }
    public string TenantId { get; set; }
    public string UserId { get; set; }
    public string TopicId { get; set; }
    public string EventType { get; set; }
    public string Stage { get; set; }
    public CoachingMessageData Data { get; set; }
}

public class CoachingMessageData
{
    public string JobId { get; set; }
    public string SessionId { get; set; }
    public string TopicId { get; set; }
    
    // For ai.message.completed
    public string Message { get; set; }
    public bool IsFinal { get; set; }
    public object Result { get; set; }
    
    // For ai.message.failed
    public string Error { get; set; }
    public string ErrorCode { get; set; }
}
```

### User Routing Logic

```csharp
public interface IWebSocketService
{
    Task SendToUser(string tenantId, string userId, string message);
}

public class WebSocketService : IWebSocketService
{
    private readonly IAmazonApiGatewayManagementApi _apiGatewayClient;
    private readonly IConnectionStore _connectionStore;

    public async Task SendToUser(string tenantId, string userId, string message)
    {
        // Get all active connections for this user in this tenant
        var connections = await _connectionStore.GetConnectionsForUser(tenantId, userId);
        
        foreach (var connectionId in connections)
        {
            try
            {
                await _apiGatewayClient.PostToConnectionAsync(new PostToConnectionRequest
                {
                    ConnectionId = connectionId,
                    Data = new MemoryStream(Encoding.UTF8.GetBytes(message))
                });
            }
            catch (GoneException)
            {
                // Connection closed, remove from store
                await _connectionStore.RemoveConnection(connectionId);
            }
        }
    }
}
```

---

## Frontend Integration Notes

**No Frontend Changes Required** if WebSocket already handles events by `eventType`.

The frontend will receive these events through the existing WebSocket connection:

```typescript
// Existing WebSocket handler should work
websocket.onmessage = (event) => {
  const payload = JSON.parse(event.data);
  
  switch (payload.eventType) {
    case 'ai.message.completed':
      // Handle complete message
      updateChat(payload.data.message);
      if (payload.data.isFinal) {
        handleConversationComplete(payload.data.result);
      }
      break;
      
    case 'ai.message.failed':
      // Handle error
      showError(payload.data.error, payload.data.errorCode);
      break;
  }
};
```

---

## Testing

### Manual Testing with AWS CLI

```bash
# Publish test completed event
aws events put-events --entries '[
  {
    "Source": "purposepath.ai",
    "DetailType": "ai.message.completed",
    "Detail": "{\"jobId\":\"test-job-123\",\"tenantId\":\"test-tenant\",\"userId\":\"test-user\",\"topicId\":\"conversation_coaching\",\"eventType\":\"ai.message.completed\",\"stage\":\"dev\",\"data\":{\"jobId\":\"test-job-123\",\"sessionId\":\"test-session\",\"topicId\":\"conversation_coaching\",\"message\":\"Test response from coach\",\"isFinal\":false,\"result\":null}}"
  }
]'

# Publish test failed event
aws events put-events --entries '[
  {
    "Source": "purposepath.ai",
    "DetailType": "ai.message.failed",
    "Detail": "{\"jobId\":\"test-job-456\",\"tenantId\":\"test-tenant\",\"userId\":\"test-user\",\"topicId\":\"conversation_coaching\",\"eventType\":\"ai.message.failed\",\"stage\":\"dev\",\"data\":{\"jobId\":\"test-job-456\",\"sessionId\":\"test-session\",\"topicId\":\"conversation_coaching\",\"error\":\"Test error message\",\"errorCode\":\"INTERNAL_ERROR\"}}"
  }
]'
```

### Verification Checklist

- [ ] EventBridge rule created with correct pattern
- [ ] Lambda function subscribed to rule
- [ ] Events filtered by `stage` environment variable
- [ ] WebSocket forwards to correct `tenantId` + `userId`
- [ ] Complete message (no streaming) sent in single payload
- [ ] Error events display user-friendly messages
- [ ] Stale connections removed on GoneException
- [ ] CloudWatch logs show successful event routing

---

## Migration Notes

### Backward Compatibility

- Existing `ai.job.completed` events remain unchanged
- This is a **new pattern** for conversation coaching only
- Single-shot AI operations (e.g., business analysis) still use `ai.job.completed`

### Rollout Plan

1. **Phase 1**: Deploy .NET EventBridge handlers (this spec) ✅
2. **Phase 2**: Deploy Python worker Lambda (already deployed) ✅
3. **Phase 3**: Monitor CloudWatch for successful event routing
4. **Phase 4**: Verify WebSocket delivery in dev environment
5. **Phase 5**: Deploy to staging, then production

---

## Support

**Questions?** Contact the coaching service team or refer to:
- [Coaching Session Workflow](../ai-user/coaching-session-workflow.md)
- [Issue #222](https://github.com/mottych/PurposePath_AI/issues/222)
- [EventBridge Client Source](../../../../shared/services/eventbridge_client.py)
