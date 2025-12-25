# Unified AI Endpoint Backend Integration Specifications

**Version:** 1.2  
**Last Updated:** December 15, 2025  
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

**Response Model:** `WebsiteScanResponse` — [Get JSON Schema](/ai/schemas/WebsiteScanResponse)

```json
{
  "topic_id": "website_scan",
  "success": true,
  "data": {
    "scan_id": "scan_f3c9ab",
    "captured_at": "2025-12-24T03:12:54Z",
    "source_url": "https://example.com",
    "company_profile": {
      "company_name": "Example Corp",
      "legal_name": "Example Corporation, Inc.",
      "tagline": "Data-driven growth for modern teams",
      "overview": "Example Corp provides analytics-driven marketing platforms that help mid-market teams launch, test, and scale campaigns."
    },
    "target_market": {
      "primary_audience": "Marketing and revenue leaders at mid-market SaaS companies",
      "segments": [
        "B2B SaaS (ARR $5M-$50M)",
        "Hybrid go-to-market teams",
        "Demand generation leaders"
      ],
      "pain_points": [
        "Fragmented channel analytics",
        "Slow experimentation cycles",
        "Unclear attribution for pipeline"
      ]
    },
    "offers": {
      "primary_product": "Growth Experimentation Platform",
      "categories": [
        "Marketing analytics",
        "Campaign orchestration"
      ],
      "features": [
        "Channel performance dashboards",
        "Experiment templates",
        "Automated reporting"
      ],
      "differentiators": [
        "Playbooks tuned for B2B SaaS",
        "Fast setup with existing data stack",
        "Revenue-aware experimentation scoring"
      ]
    },
    "credibility": {
      "notable_clients": [
        "Northwind Analytics",
        "Contoso Labs",
        "Fabrikam Cloud"
      ],
      "testimonials": [
        {
          "quote": "We doubled qualified pipeline after standardizing experiments in one place.",
          "attribution": "VP Growth, Northwind"
        }
      ]
    },
    "conversion": {
      "primary_cta_text": "Book a growth audit",
      "primary_cta_url": "https://example.com/demo",
      "supporting_assets": [
        {
          "label": "2025 SaaS Growth Benchmark Report",
          "url": "https://example.com/benchmark"
        }
      ]
    }
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

**Schema:** Use `GET /ai/schemas/WebsiteScanResponse` to get the full JSON schema with field descriptions. The schema is auto-generated from the Pydantic model.

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

## Coaching Conversation Sessions

The Coaching Conversation endpoints provide multi-turn conversational coaching interactions. Unlike single-shot `/ai/execute` endpoints, coaching sessions maintain state across multiple messages.

### Base URL

All coaching conversation endpoints are prefixed with `/ai/coaching`.

**Full URL Pattern:** `{BASE_URL}/ai/coaching/{endpoint}`

### Available Coaching Topics

The following coaching topics are currently available:

| topic_id | Name | Description |
|----------|------|-------------|
| `core_values` | Core Values Discovery | Discover and articulate your organization's authentic core values |
| `purpose` | Purpose Discovery | Define your organization's deeper purpose and reason for existing |
| `vision` | Vision Crafting | Craft a compelling vision for your organization's future |

**Important:** When calling `/ai/coaching/start`, use the `topic_id` value (e.g., `"core_values"`, `"purpose"`, `"vision"`) - NOT the registry key format.

### Result Model Schemas

When a coaching session completes (`is_final: true`), the `result` field contains a topic-specific structured result.

#### CoreValuesResult (topic: `core_values`)

```json
{
  "values": [
    {
      "name": "string (1-100 chars)",
      "description": "string (10-500 chars) - What this value means",
      "importance": "string (10-500 chars) - Why this value matters"
    }
  ],
  "summary": "string (50-1000 chars) - Overall summary of the values"
}
```

#### PurposeResult (topic: `purpose`)

```json
{
  "purpose_statement": "string (20-500 chars) - The organization's purpose statement",
  "why_it_matters": "string (50-1000 chars) - Why this purpose is meaningful",
  "how_it_guides": "string (50-1000 chars) - How purpose guides decisions"
}
```

#### VisionResult (topic: `vision`)

```json
{
  "vision_statement": "string (20-500 chars) - The organization's vision statement",
  "time_horizon": "string (1-50 chars) - Time frame (e.g., '5 years', '10 years')",
  "key_aspirations": ["string"] // 1-10 aspirations that comprise the vision
}
```

---

### GET /ai/coaching/topics

Get all coaching topics with user's completion status.

**Full URL:** `{BASE_URL}/ai/coaching/topics`

**Response:**

```json
{
  "success": true,
  "data": {
    "topics": [
      {
        "topic_id": "core_values",
        "name": "Core Values Discovery",
        "description": "Discover and articulate your organization's authentic core values",
        "status": "not_started",
        "session_id": null,
        "completed_at": null
      },
      {
        "topic_id": "purpose",
        "name": "Purpose Discovery",
        "description": "Define your organization's deeper purpose and reason for existing",
        "status": "in_progress",
        "session_id": "sess_abc123",
        "completed_at": null
      },
      {
        "topic_id": "vision",
        "name": "Vision Crafting",
        "description": "Craft a compelling vision for your organization's future",
        "status": "completed",
        "session_id": "sess_xyz789",
        "completed_at": "2025-12-15T10:00:00Z"
      }
    ]
  },
  "message": "Topics retrieved successfully"
}
```

**Topic Statuses:**

| Status | Description |
|--------|-------------|
| `not_started` | User has never started this topic |
| `in_progress` | User has an active session |
| `paused` | User has a paused session (can be resumed) |
| `completed` | User has completed this topic |

---

### POST /ai/coaching/start

Start a new coaching session or resume an existing one.

**Full URL:** `{BASE_URL}/ai/coaching/start`

**Request:**

```json
{
  "topic_id": "core_values",
  "context": {
    "business_name": "Acme Corp",
    "industry": "Technology"
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic_id` | string | Yes | ID of the coaching topic (e.g., `core_values`, `purpose`, `vision`) |
| `context` | object | No | Optional context data for the session |

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "tenant_id": "tenant-123",
    "topic_id": "core_values",
    "status": "active",
    "message": "Welcome! Let's begin exploring your core values. What values are most important to you in your business?",
    "turn": 1,
    "max_turns": 10,
    "is_final": false,
    "resumed": false,
    "metadata": {
      "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "processing_time_ms": 1250,
      "tokens_used": 150
    }
  },
  "message": "Session started successfully"
}
```

**Response (Resumed Session):**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "tenant_id": "tenant-123",
    "topic_id": "core_values",
    "status": "active",
    "message": "Welcome back! Let's continue where we left off...",
    "turn": 5,
    "max_turns": 10,
    "is_final": false,
    "resumed": true,
    "metadata": {
      "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "processing_time_ms": 980,
      "tokens_used": 120
    }
  },
  "message": "Session started successfully"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | VALIDATION_ERROR | Request validation failed |
| 409 | SESSION_CONFLICT | Another user has an active session for this topic |
| 422 | INVALID_TOPIC | Topic not found or invalid |

---

### POST /ai/coaching/message

Send a message in an active coaching session.

**Full URL:** `{BASE_URL}/ai/coaching/message`

**Request:**

```json
{
  "session_id": "sess_abc123",
  "message": "I think integrity and innovation are most important to me"
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | ID of the coaching session |
| `message` | string | Yes | User's message content (min 1 character) |

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "message": "That's wonderful! Integrity and innovation are powerful values. Can you tell me more about how integrity shows up in your daily business decisions?",
    "status": "active",
    "turn": 3,
    "max_turns": 10,
    "is_final": false,
    "message_count": 6,
    "result": null,
    "metadata": {
      "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "processing_time_ms": 1450,
      "tokens_used": 180
    }
  },
  "message": "Message processed successfully"
}
```

**Response (Session Auto-Completed by LLM):**

When the LLM determines the conversation is naturally complete, it sets `is_final: true` and includes extracted results:

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "message": "Thank you for this wonderful conversation! I've captured your core values and created a summary of what we discussed.",
    "status": "completed",
    "turn": 8,
    "max_turns": 10,
    "is_final": true,
    "message_count": 16,
    "result": {
      "values": [
        {
          "name": "Integrity",
          "description": "Acting with honesty and transparency in all business dealings",
          "importance": "Builds trust with clients and partners, essential for long-term relationships"
        },
        {
          "name": "Innovation",
          "description": "Continuously seeking new and better solutions to challenges",
          "importance": "Keeps the business competitive and responsive to market changes"
        }
      ],
      "summary": "Based on our conversation, your core values center around integrity in all dealings and a commitment to innovation. These values reflect your belief that sustainable business success comes from building trust while continuously improving."
    },
    "metadata": {
      "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "processing_time_ms": 2100,
      "tokens_used": 350
    }
  },
  "message": "Message processed successfully"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | SESSION_NOT_ACTIVE | Session is not in active state |
| 403 | SESSION_ACCESS_DENIED | User does not own this session |
| 410 | SESSION_EXPIRED | Session has expired |
| 410 | SESSION_IDLE_TIMEOUT | Session exceeded idle timeout |
| 422 | SESSION_NOT_FOUND | Session not found |
| 422 | MAX_TURNS_REACHED | Maximum conversation turns reached |

---

### POST /ai/coaching/pause

Pause an active coaching session.

**Full URL:** `{BASE_URL}/ai/coaching/pause`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "paused",
    "topic_id": "core_values",
    "turn_count": 5,
    "max_turns": 10,
    "created_at": "2025-12-15T10:00:00Z",
    "updated_at": "2025-12-15T10:15:00Z"
  },
  "message": "Session paused successfully"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | SESSION_NOT_ACTIVE | Session cannot be paused (not active) |
| 403 | SESSION_ACCESS_DENIED | User does not own this session |
| 422 | SESSION_NOT_FOUND | Session not found |

---

### POST /ai/coaching/complete

Complete a coaching session and extract results.

**Full URL:** `{BASE_URL}/ai/coaching/complete`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "completed",
    "result": {
      "values": [
        {
          "name": "Integrity",
          "description": "Acting with honesty and transparency in all dealings",
          "importance": "Foundation of trust with clients, partners, and team members"
        },
        {
          "name": "Innovation",
          "description": "Continuously seeking new and better solutions",
          "importance": "Drives competitive advantage and adaptability"
        },
        {
          "name": "Excellence",
          "description": "Striving for the highest quality in everything",
          "importance": "Ensures consistent delivery and customer satisfaction"
        }
      ],
      "summary": "Your core values center around building trust through integrity, staying competitive through innovation, and delivering quality through excellence."
    }
  },
  "message": "Session completed successfully"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | SESSION_NOT_ACTIVE | Session cannot be completed (not active/paused) |
| 403 | SESSION_ACCESS_DENIED | User does not own this session |
| 422 | SESSION_NOT_FOUND | Session not found |
| 500 | EXTRACTION_FAILED | Failed to extract results from session |

---

### POST /ai/coaching/cancel

Cancel a coaching session.

**Full URL:** `{BASE_URL}/ai/coaching/cancel`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "status": "cancelled",
    "topic_id": "core_values",
    "turn_count": 3,
    "max_turns": 10,
    "created_at": "2025-12-15T10:00:00Z",
    "updated_at": "2025-12-15T10:05:00Z"
  },
  "message": "Session cancelled successfully"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | SESSION_NOT_ACTIVE | Session cannot be cancelled (already completed) |
| 403 | SESSION_ACCESS_DENIED | User does not own this session |
| 422 | SESSION_NOT_FOUND | Session not found |

---

### GET /ai/coaching/session

Get detailed information about a coaching session.

**Full URL:** `{BASE_URL}/ai/coaching/session?session_id={session_id}`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | ID of the session to retrieve |

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "tenant_id": "tenant-123",
    "topic_id": "core_values",
    "user_id": "user-456",
    "status": "active",
    "messages": [
      {
        "role": "assistant",
        "content": "Welcome! Let's explore your core values...",
        "timestamp": "2025-12-15T10:00:00Z"
      },
      {
        "role": "user",
        "content": "I think integrity is important...",
        "timestamp": "2025-12-15T10:01:00Z"
      }
    ],
    "context": {},
    "max_turns": 10,
    "created_at": "2025-12-15T10:00:00Z",
    "updated_at": "2025-12-15T10:01:00Z",
    "completed_at": null,
    "extracted_result": null
  },
  "message": "Session retrieved successfully"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 403 | SESSION_ACCESS_DENIED | User does not own this session |
| 422 | SESSION_NOT_FOUND | Session not found |

---

### GET /ai/coaching/sessions

List all coaching sessions for the current user.

**Full URL:** `{BASE_URL}/ai/coaching/sessions?include_completed={bool}&limit={int}`

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_completed` | boolean | No | false | Include completed/cancelled sessions |
| `limit` | integer | No | 20 | Maximum sessions to return (1-100) |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "session_id": "sess_abc123",
      "topic_id": "core_values",
      "status": "active",
      "turn_count": 5,
      "created_at": "2025-12-15T10:00:00Z",
      "updated_at": "2025-12-15T10:15:00Z"
    },
    {
      "session_id": "sess_def456",
      "topic_id": "purpose",
      "status": "paused",
      "turn_count": 3,
      "created_at": "2025-12-14T09:00:00Z",
      "updated_at": "2025-12-14T09:10:00Z"
    }
  ],
  "message": "Found 2 sessions"
}
```

---

### Error Response Format

All coaching conversation errors follow this format:

```json
{
  "detail": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session not found: sess_abc123"
  }
}
```

### Complete Error Code Reference

| Status | Code | Description |
|--------|------|-------------|
| 400 | SESSION_NOT_ACTIVE | Session is not in an active state for the requested operation |
| 400 | VALIDATION_ERROR | Request validation failed |
| 403 | SESSION_ACCESS_DENIED | User does not have access to this session |
| 409 | SESSION_CONFLICT | Another user has an active session for this topic |
| 410 | SESSION_EXPIRED | Session has expired |
| 410 | SESSION_IDLE_TIMEOUT | Session exceeded idle timeout |
| 422 | SESSION_NOT_FOUND | Session not found |
| 422 | MAX_TURNS_REACHED | Maximum conversation turns reached |
| 422 | INVALID_TOPIC | Topic not found or invalid |
| 500 | EXTRACTION_FAILED | Failed to extract results from session |

---

### Frontend Integration Example

```typescript
// Start or resume a coaching session
async function startCoachingSession(topicId: string, context?: Record<string, any>) {
  try {
    const response = await coachingClient.post('/ai/coaching/start', {
      topic_id: topicId,
      context
    });
    return response.data.data;
  } catch (error) {
    if (error.response?.status === 409) {
      // Another user has an active session
      throw new Error('Session in progress by another user');
    }
    throw error;
  }
}

// Send a message and get coach response
async function sendMessage(sessionId: string, message: string) {
  try {
    const response = await coachingClient.post('/ai/coaching/message', {
      session_id: sessionId,
      message
    });
    const { message: coachMessage, status, result, is_final } = response.data.data;
    
    if (is_final || status === 'completed') {
      // Session was auto-completed by the LLM
      handleCompletion(result);
    }
    
    return response.data.data;
  } catch (error) {
    if (error.response?.status === 422) {
      const code = error.response.data.detail?.code;
      if (code === 'MAX_TURNS_REACHED') {
        // Prompt user to complete the session
        return completeSession(sessionId);
      }
    }
    throw error;
  }
}

// Complete session manually
async function completeSession(sessionId: string) {
  const response = await coachingClient.post('/ai/coaching/complete', {
    session_id: sessionId
  });
  return response.data.data;
}
```

---

_This document will be updated as additional topics are activated in the unified AI endpoint._
