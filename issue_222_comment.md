🚀 Starting implementation on branch `feat/222-async-coaching-messages`

## Simplified Design Decision

After discussion, we're implementing **async without token streaming** to avoid DB lookup overhead on the .NET WebSocket service.

### Event Types (3 Total)
- ✅ `ai.message.created` - Triggers worker Lambda
- ✅ `ai.message.completed` - Sends **complete** response (like current flow)
- ✅ `ai.message.failed` - Error handling
- ❌ ~~`ai.message.token`~~ - Removed (no streaming)

### Benefits
- Frontend receives complete responses (no changes needed to response handling)
- One EventBridge event per message (no DB lookup storm)
- Simpler implementation and testing
- All events include `tenantId` + `userId` for .NET routing
- .NET WebSocket service likely needs zero changes (generic `ai.*` forwarding)

### Implementation Plan
1. Add 3 EventBridge publish methods to `shared/services/eventbridge_client.py`
2. Extend `AIJob` model with `CONVERSATION_MESSAGE` type
3. Create `CoachingMessageJobService` for async execution
4. Update `POST /message` → 202 Accepted with `job_id`
5. Add `GET /message/{job_id}` for polling fallback
6. Unit tests for all components
7. Update documentation

**Estimated completion: 4-6 hours** (reduced from 6-9 without streaming complexity)
