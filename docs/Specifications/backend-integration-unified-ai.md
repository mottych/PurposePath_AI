# Unified AI Endpoint Backend Integration Specifications

**Version:** 1.0  
**Last Updated:** December 9, 2025  
**Service Base URL:** `{REACT_APP_COACHING_API_URL}`  
**Default (Localhost):** `http://localhost:8000`  
**Dev Environment:** `https://api.dev.purposepath.app/coaching/api/v1`

[← Back to Index](./backend-integration-index.md)

---

## Overview

The Unified AI endpoints provide a single entry point (`/ai/execute`) for all single-shot AI operations. Instead of separate endpoints for each topic, callers specify a `topic_id` and the appropriate parameters.

### Benefits

- **Single endpoint** for all single-shot AI operations
- **Dynamic response models** based on topic
- **Schema discovery** via `/ai/schemas/{schema_name}`
- **Topic listing** via `/ai/topics`
- **Consistent error handling** across all topics

### Frontend Implementation

- **Primary Client:** `coachingClient` (axios instance in `src/services/api.ts`)
- **Key Pattern:** Call `/ai/execute` with `topic_id` and `parameters`

---

## Core Endpoints

### POST /ai/execute

Execute any registered single-shot AI topic.

**Full URL:** `{BASE_URL}/ai/execute`

**Request:**

```json
{
  "topic_id": "string",
  "parameters": {
    // Topic-specific parameters
  }
}
```

**Response:**

```json
{
  "topic_id": "string",
  "success": true,
  "data": {
    // Response varies by topic - see schema_ref
  },
  "schema_ref": "string",
  "metadata": {
    "model": "string",
    "tokens_used": 0,
    "processing_time_ms": 0,
    "finish_reason": "stop"
  }
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 404 | Topic not found in registry |
| 400 | Topic is not active |
| 400 | Topic is conversation type (use conversation endpoints) |
| 422 | Missing required parameters |
| 500 | Response model not configured |

---

### GET /ai/topics

List all available single-shot topics with their parameters.

**Full URL:** `{BASE_URL}/ai/topics`

**Response:**

```json
[
  {
    "topic_id": "niche_review",
    "description": "Review and suggest variations for business niche",
    "response_model": "OnboardingReviewResponse",
    "parameters": [
      {
        "name": "current_value",
        "type": "string",
        "required": true,
        "description": "Current niche value to review"
      }
    ]
  }
]
```

---

### GET /ai/schemas/{schema_name}

Get JSON schema for a response model.

**Full URL:** `{BASE_URL}/ai/schemas/{schema_name}`

**Example:** `GET /ai/schemas/OnboardingReviewResponse`

**Response:** JSON Schema definition for the response model.

---

## Supported Topics

### Onboarding Review Topics

These topics review user-provided content and suggest improvements.

---

#### Topic: `niche_review`

Review and suggest variations for business niche.

**Request:**

```json
{
  "topic_id": "niche_review",
  "parameters": {
    "current_value": "We help small business owners with marketing"
  }
}
```

**Response Model:** `OnboardingReviewResponse`

```json
{
  "topic_id": "niche_review",
  "success": true,
  "data": {
    "qualityReview": "Your niche is clear but could be more specific. Consider narrowing your target market and specifying the outcomes you deliver...",
    "suggestions": [
      {
        "text": "We help B2B SaaS startups under $5M ARR build predictable revenue pipelines",
        "reasoning": "More specific target market (B2B SaaS, revenue stage) and clear outcome (predictable pipelines)"
      },
      {
        "text": "We help local service businesses attract high-value clients through digital marketing",
        "reasoning": "Specifies business type (local service) and value proposition (high-value clients)"
      },
      {
        "text": "We help e-commerce brands scale past $1M revenue with data-driven marketing strategies",
        "reasoning": "Clear niche (e-commerce), growth stage ($1M), and methodology (data-driven)"
      }
    ]
  },
  "schema_ref": "OnboardingReviewResponse",
  "metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 450,
    "processing_time_ms": 2340,
    "finish_reason": "stop"
  }
}
```

---

#### Topic: `ica_review`

Review and suggest variations for Ideal Client Avatar (ICA).

**Request:**

```json
{
  "topic_id": "ica_review",
  "parameters": {
    "current_value": "Business owners who want to grow"
  }
}
```

**Response Model:** `OnboardingReviewResponse`

```json
{
  "topic_id": "ica_review",
  "success": true,
  "data": {
    "qualityReview": "Your ICA is too broad. A strong ICA should include demographics, psychographics, pain points, and goals...",
    "suggestions": [
      {
        "text": "Growth-minded CEOs of B2B companies with 10-50 employees, frustrated by inconsistent lead flow and seeking scalable marketing systems",
        "reasoning": "Includes role, company size, pain point (inconsistent leads), and goal (scalable systems)"
      },
      {
        "text": "Ambitious founders of 2-5 year old businesses generating $500K-$2M revenue, ready to invest in professional marketing to reach the next level",
        "reasoning": "Specifies business maturity, revenue stage, and readiness to invest"
      },
      {
        "text": "Time-strapped small business owners wearing too many hats, looking for done-for-you marketing solutions",
        "reasoning": "Identifies key pain point (time-strapped) and preferred solution type (done-for-you)"
      }
    ]
  },
  "schema_ref": "OnboardingReviewResponse",
  "metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 520,
    "processing_time_ms": 2890,
    "finish_reason": "stop"
  }
}
```

---

#### Topic: `value_proposition_review`

Review and suggest variations for value proposition.

**Request:**

```json
{
  "topic_id": "value_proposition_review",
  "parameters": {
    "current_value": "We provide great marketing services"
  }
}
```

**Response Model:** `OnboardingReviewResponse`

```json
{
  "topic_id": "value_proposition_review",
  "success": true,
  "data": {
    "qualityReview": "Your value proposition lacks specificity and differentiation. Strong value propositions explain what you do, for whom, and what makes you different...",
    "suggestions": [
      {
        "text": "We transform struggling marketing departments into revenue-generating machines through our proven 90-day Marketing Acceleration Program",
        "reasoning": "Clear transformation (struggling to revenue-generating), specific methodology (90-day program)"
      },
      {
        "text": "We help growth-stage companies double their qualified leads in 6 months using AI-powered marketing automation",
        "reasoning": "Specific outcome (double leads), timeline (6 months), and differentiator (AI-powered)"
      },
      {
        "text": "We deliver enterprise-quality marketing strategies at startup-friendly prices, with guaranteed ROI tracking",
        "reasoning": "Value contrast (enterprise quality, startup prices), risk reduction (guaranteed ROI tracking)"
      }
    ]
  },
  "schema_ref": "OnboardingReviewResponse",
  "metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 480,
    "processing_time_ms": 2650,
    "finish_reason": "stop"
  }
}
```

---

## Response Model Schemas

### OnboardingReviewResponse

Used by: `niche_review`, `ica_review`, `value_proposition_review`

```typescript
interface OnboardingReviewResponse {
  qualityReview: string;  // AI review of current content with feedback
  suggestions: SuggestionVariation[];  // Exactly 3 suggestions
}

interface SuggestionVariation {
  text: string;      // The suggested text variation
  reasoning: string; // Explanation of why this variation is recommended
}
```

**JSON Schema:** Available via `GET /ai/schemas/OnboardingReviewResponse`

---

### Website & Onboarding Topics

#### Topic: `website_scan`

Scan a website URL and extract business information for onboarding.

**Request:**

```json
{
  "topic_id": "website_scan",
  "parameters": {
    "website_url": "https://example.com"
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `website_url` | string | Yes | URL of website to scan |

**Response Model:** `WebsiteScanResponse`

```json
{
  "topic_id": "website_scan",
  "success": true,
  "data": {
    "products": [
      {
        "id": "coaching-program",
        "name": "Business Coaching Program",
        "problem": "Helps entrepreneurs overcome growth plateaus"
      },
      {
        "id": "strategy-workshop",
        "name": "Strategy Workshop",
        "problem": "Provides clarity on business direction and priorities"
      }
    ],
    "niche": "Business coaching for growth-stage entrepreneurs seeking to scale their companies while maintaining work-life balance.",
    "ica": "Mid-career entrepreneurs (35-50) running businesses with $500K-$5M revenue, feeling stuck at a growth plateau, seeking strategic guidance and accountability.",
    "value_proposition": "Transform your business growth while reclaiming your personal time through our proven coaching methodology."
  },
  "schema_ref": "WebsiteScanResponse",
  "metadata": {
    "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "tokens_used": 1850,
    "processing_time_ms": 8500,
    "finish_reason": "stop"
  }
}
```

**Notes:**

- This topic uses a **retrieval method** (`get_website_content`) to fetch and parse the website
- The `website_url` parameter is passed from the frontend payload
- The retrieval method scrapes the website and provides `website_content`, `website_title`, and `meta_description` to the prompt template
- Results used to pre-fill onboarding form
- May return partial results if website has anti-scraping measures

**WebsiteScanResponse Schema:**

```typescript
interface WebsiteScanResponse {
  products: ProductInfo[];
  niche: string;
  ica: string;
  value_proposition: string;
}

interface ProductInfo {
  id: string;      // Unique identifier (lowercase, hyphenated)
  name: string;    // Product/service name
  problem: string; // Problem it solves
}
```

---

## Additional Topics (Coming Soon)

The following topics are registered in the system and will be documented as they become active:

### Strategic Planning
- `alignment_check` - Calculate goal alignment score
- `alignment_explanation` - Get detailed alignment explanation
- `alignment_suggestions` - Get suggestions to improve alignment
- `strategy_suggestions` - AI suggestions for strategies
- `kpi_recommendations` - AI recommendations for KPIs

### Operations AI
- `root_cause_suggestions` - Root cause analysis suggestions
- `swot_analysis` - Generate SWOT analysis
- `five_whys_questions` - Generate Five Whys questions
- `action_suggestions` - Suggest actions for issues
- `optimize_action_plan` - Optimize action plans

### Website & Onboarding
- ~~`website_scan` - Scan website and extract business info~~ **→ ACTIVE** (see above)
- `onboarding_suggestions` - Generate onboarding suggestions
- `onboarding_coaching` - AI coaching for onboarding
- `business_metrics` - Retrieve business metrics

---

## Error Handling

All errors follow the standard API error format:

```json
{
  "detail": "Error message here"
}
```

### Common Error Codes

| Status | Error | Resolution |
|--------|-------|------------|
| 404 | `Topic not found: {topic_id}` | Check `topic_id` against `/ai/topics` |
| 400 | `Topic is not active: {topic_id}` | Topic is disabled, contact admin |
| 400 | `Topic {topic_id} is type {type}` | Use conversation endpoints for coaching |
| 422 | `Missing required parameters: [...]` | Include all required parameters |
| 500 | `Response model not configured` | Backend configuration issue |

---

## Usage Examples

### JavaScript/TypeScript

```typescript
// Using coachingClient from api.ts
const response = await coachingClient.post('/ai/execute', {
  topic_id: 'niche_review',
  parameters: {
    current_value: 'We help small businesses grow'
  }
});

const { qualityReview, suggestions } = response.data.data;
```

### Python

```python
import httpx

async def review_niche(current_value: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/ai/execute",
            json={
                "topic_id": "niche_review",
                "parameters": {"current_value": current_value}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()["data"]
```

---

---

## Async Execution (Long-Running Operations)

For AI operations that may exceed API Gateway's 30-second timeout (e.g., complex analysis, multi-step reasoning), use the async execution endpoint.

### POST /ai/execute-async

Execute an AI topic asynchronously. Returns immediately with a job ID; results delivered via WebSocket.

**Full URL:** `{BASE_URL}/ai/execute-async`

**Request:** Same as `/ai/execute`

```json
{
  "topic_id": "niche_review",
  "parameters": {
    "current_value": "We help small business owners with marketing"
  }
}
```

**Response (Immediate):**

```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "topicId": "niche_review",
    "estimatedDurationMs": 30000
  }
}
```

**Job Statuses:**

- `pending` - Job accepted, queued for processing
- `processing` - Job is actively being processed
- `completed` - Job finished successfully (result in WebSocket event)
- `failed` - Job failed (error in WebSocket event)

---

### GET /ai/jobs/{jobId}

Check status of an async job. Use for polling fallback if WebSocket disconnects.

**Full URL:** `{BASE_URL}/ai/jobs/{jobId}`

**Response (Pending):**

```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "processing",
    "topicId": "niche_review",
    "createdAt": "2025-12-10T20:00:00Z"
  }
}
```

**Response (Completed):**

```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "topicId": "niche_review",
    "createdAt": "2025-12-10T20:00:00Z",
    "completedAt": "2025-12-10T20:00:35Z",
    "result": {
      "qualityReview": "...",
      "suggestions": [...]
    },
    "processingTimeMs": 35000
  }
}
```

**Response (Failed):**

```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "failed",
    "topicId": "niche_review",
    "createdAt": "2025-12-10T20:00:00Z",
    "completedAt": "2025-12-10T20:00:45Z",
    "error": "LLM provider timeout",
    "errorCode": "LLM_TIMEOUT"
  }
}
```

---

### EventBridge Events

The AI service publishes events to AWS EventBridge for async processing and real-time notifications. The .NET WebSocket broadcaster subscribes to these events and forwards them to connected clients.

**Event Bus**: `default`  
**Source**: `purposepath.ai`

#### EventBridge Event Structure

All events follow this envelope structure:

```json
{
  "version": "0",
  "id": "event-id-from-eventbridge",
  "detail-type": "ai.job.completed",
  "source": "purposepath.ai",
  "account": "123456789012",
  "time": "2025-12-10T20:00:35Z",
  "region": "us-east-1",
  "detail": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "topicId": "niche_review",
    "eventType": "ai.job.completed",
    "data": {
      "jobId": "550e8400-e29b-41d4-a716-446655440000",
      "topicId": "niche_review",
      "result": { ... },
      "processingTimeMs": 35000
    }
  }
}
```

#### ai.job.created (EventBridge)

Published when an async job is created. Triggers the job executor Lambda.

```json
{
  "detail-type": "ai.job.created",
  "source": "purposepath.ai",
  "detail": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "topicId": "niche_review",
    "eventType": "ai.job.created",
    "data": {
      "jobId": "550e8400-e29b-41d4-a716-446655440000",
      "topicId": "niche_review",
      "parameters": {
        "current_value": "We help small businesses grow"
      },
      "estimatedDurationMs": 30000
    }
  }
}
```

#### ai.job.started (EventBridge)

Published when job processing begins.

```json
{
  "detail-type": "ai.job.started",
  "source": "purposepath.ai",
  "detail": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "topicId": "niche_review",
    "eventType": "ai.job.started",
    "data": {
      "jobId": "550e8400-e29b-41d4-a716-446655440000",
      "topicId": "niche_review",
      "estimatedDurationMs": 30000
    }
  }
}
```

#### ai.job.completed (EventBridge)

Published when job finishes successfully. **The `data` object contains the full result.**

```json
{
  "detail-type": "ai.job.completed",
  "source": "purposepath.ai",
  "detail": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "topicId": "niche_review",
    "eventType": "ai.job.completed",
    "data": {
      "jobId": "550e8400-e29b-41d4-a716-446655440000",
      "topicId": "niche_review",
      "result": {
        "qualityReview": "Your niche is clear but could be more specific...",
        "suggestions": [
          {
            "text": "We help B2B SaaS startups...",
            "reasoning": "More specific target market..."
          }
        ]
      },
      "processingTimeMs": 35000
    }
  }
}
```

#### ai.job.failed (EventBridge)

Published when job fails.

```json
{
  "detail-type": "ai.job.failed",
  "source": "purposepath.ai",
  "detail": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "tenant-123",
    "userId": "user-456",
    "topicId": "niche_review",
    "eventType": "ai.job.failed",
    "data": {
      "jobId": "550e8400-e29b-41d4-a716-446655440000",
      "topicId": "niche_review",
      "error": "LLM provider timeout after 60 seconds",
      "errorCode": "LLM_TIMEOUT"
    }
  }
}
```

#### .NET Broadcaster Implementation Notes

The WebSocket broadcaster should:

1. **Subscribe** to EventBridge events with source `purposepath.ai`
2. **Route** messages to the correct WebSocket connection using `detail.tenantId` and `detail.userId`
3. **Forward the full `detail.data` object** as the WebSocket message `data` field
4. **Use `detail.eventType`** as the WebSocket message `type` field

**Example transformation:**

```csharp
// EventBridge detail -> WebSocket message
var websocketMessage = new {
    type = eventBridgeDetail.eventType,      // "ai.job.completed"
    timestamp = DateTime.UtcNow.ToString("o"),
    data = eventBridgeDetail.data            // Forward ENTIRE data object including result
};
```

---

### WebSocket Events

Results are delivered via the existing WebSocket connection at `wss://{WEBSOCKET_URL}`.

#### ai.job.started

Sent when job processing begins.

```json
{
  "type": "ai.job.started",
  "timestamp": "2025-12-10T20:00:00Z",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "topicId": "niche_review",
    "estimatedDurationMs": 30000
  }
}
```

#### ai.job.completed

Sent when job finishes successfully.

```json
{
  "type": "ai.job.completed",
  "timestamp": "2025-12-10T20:00:35Z",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "topicId": "niche_review",
    "result": {
      "qualityReview": "Your niche is clear but could be more specific...",
      "suggestions": [
        {
          "text": "We help B2B SaaS startups...",
          "reasoning": "More specific target market..."
        }
      ]
    },
    "processingTimeMs": 35000
  }
}
```

#### ai.job.failed

Sent when job fails.

```json
{
  "type": "ai.job.failed",
  "timestamp": "2025-12-10T20:00:45Z",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "topicId": "niche_review",
    "error": "LLM provider timeout after 60 seconds",
    "errorCode": "LLM_TIMEOUT"
  }
}
```

---

### Frontend Integration Pattern

```typescript
// 1. Start async job
const { jobId, status } = await coachingClient.post('/ai/execute-async', {
  topic_id: 'niche_review',
  parameters: { current_value: 'We help small businesses grow' }
});

// 2. Store pending job (for recovery)
const pendingJobs = JSON.parse(localStorage.getItem('pendingAiJobs') || '[]');
pendingJobs.push({ jobId, topicId: 'niche_review', startedAt: Date.now() });
localStorage.setItem('pendingAiJobs', JSON.stringify(pendingJobs));

// 3. Listen for WebSocket events
websocket.on('message', (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'ai.job.completed' && data.data.jobId === jobId) {
    handleResult(data.data.result);
    removePendingJob(jobId);
  }
  if (data.type === 'ai.job.failed' && data.data.jobId === jobId) {
    handleError(data.data.error);
    removePendingJob(jobId);
  }
});

// 4. Polling fallback (on reconnect or page load)
async function checkPendingJobs() {
  const pendingJobs = JSON.parse(localStorage.getItem('pendingAiJobs') || '[]');
  for (const job of pendingJobs) {
    if (Date.now() - job.startedAt > 300000) { // 5 min TTL
      removePendingJob(job.jobId);
      continue;
    }
    const status = await coachingClient.get(`/ai/jobs/${job.jobId}`);
    if (status.data.status === 'completed') {
      handleResult(status.data.result);
      removePendingJob(job.jobId);
    } else if (status.data.status === 'failed') {
      handleError(status.data.error);
      removePendingJob(job.jobId);
    }
  }
}
```

---

### When to Use Async vs Sync

| Use Case | Endpoint | Reason |
|----------|----------|--------|
| Quick operations (<10s) | `POST /ai/execute` | Simpler, immediate response |
| Complex analysis (>20s) | `POST /ai/execute-async` | Avoids API Gateway timeout |
| Batch operations | `POST /ai/execute-async` | Process in background |
| User waiting on screen | `POST /ai/execute-async` | Better UX with progress |

**Recommended:** Use async for all onboarding review topics (`niche_review`, `ica_review`, `value_proposition_review`) as they may take 30-60 seconds depending on LLM load.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1 | 2025-12-10 | Added async execution endpoints and WebSocket events |
| 1.0 | 2025-12-09 | Initial version with onboarding review topics |

---

_This document will be updated as additional topics are activated in the unified AI endpoint._
