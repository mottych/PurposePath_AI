# Unified AI Endpoint Backend Integration Specifications

**Version:** 2.0  
**Last Updated:** January 11, 2026  
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
- **Automatic parameter enrichment** from backend data sources

### Frontend Implementation

- **Primary Client:** `coachingClient` (axios instance in `src/services/api.ts`)
- **Key Pattern:** Call `/ai/execute` with `topic_id` and `parameters`

---

## Architecture

### Parameter Enrichment System

The AI backend automatically enriches prompts with data from multiple sources. When you call `/ai/execute`, the system:

1. **Identifies required parameters** from the topic registry
2. **Groups parameters by source** (one API call per source)
3. **Fetches data** from Business API, Account Service, etc.
4. **Extracts individual values** using defined extraction paths
5. **Renders prompts** with all gathered parameters

This means frontend only needs to provide **request-level parameters** (e.g., `goal_id`, `measure_id`). Context like business foundation, strategies, and measures is automatically fetched.

### Data Sources

| Source | Description | Example Parameters |
|--------|-------------|-------------------|
| `REQUEST` | Provided in API request body | `goal_id`, `measure_id`, `current_value` |
| `ONBOARDING` | Business foundation from Account Service | `vision`, `purpose`, `icas`, `core_values` |
| `GOAL` | Single goal from Traction Service | `goal`, `goal_name`, `goal_description` |
| `GOALS` | All goals from Traction Service | `goals`, `goals_count` |
| `MEASURE` | Single measure from Traction Service | `measure`, `measure_name`, `measure_unit` |
| `MEASURES` | All measures/summary from Traction Service | `measures`, `measures_count` |
| `ACTION` | Single action from Traction Service | `action`, `action_title`, `action_status` |
| `ISSUE` | Single issue from Traction Service | `issue`, `issue_title`, `issue_priority` |
| `WEBSITE` | Scraped website content | `website_content`, `website_title` |
| `CONVERSATION` | Current conversation context | `conversation_history` |
| `COMPUTED` | Derived from other parameters | `alignment_score` |

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
    // Topic-specific parameters (request-level only)
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
    "qualityReview": "Your niche is clear but could be more specific...",
    "suggestions": [
      {
        "text": "We help B2B SaaS startups under $5M ARR build predictable revenue pipelines",
        "reasoning": "More specific target market (B2B SaaS, revenue stage) and clear outcome"
      },
      {
        "text": "We help local service businesses attract high-value clients through digital marketing",
        "reasoning": "Specifies business type and value proposition"
      },
      {
        "text": "We help e-commerce brands scale past $1M revenue with data-driven marketing strategies",
        "reasoning": "Clear niche, growth stage, and methodology"
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
    "captured_at": "2026-01-11T03:12:54Z",
    "source_url": "https://example.com",
    "company_profile": {
      "company_name": "Example Corp",
      "legal_name": "Example Corporation, Inc.",
      "tagline": "Data-driven growth for modern teams",
      "overview": "Example Corp provides analytics-driven marketing platforms..."
    },
    "target_market": {
      "primary_audience": "Marketing and revenue leaders at mid-market SaaS companies",
      "segments": ["B2B SaaS (ARR $5M-$50M)", "Hybrid go-to-market teams"],
      "pain_points": ["Fragmented channel analytics", "Slow experimentation cycles"]
    },
    "offers": {
      "primary_product": "Growth Experimentation Platform",
      "categories": ["Marketing analytics", "Campaign orchestration"],
      "features": ["Channel performance dashboards", "Experiment templates"],
      "differentiators": ["Playbooks tuned for B2B SaaS", "Fast setup"]
    },
    "credibility": {
      "notable_clients": ["Northwind Analytics", "Contoso Labs"],
      "testimonials": [{"quote": "We doubled qualified pipeline...", "attribution": "VP Growth, Northwind"}]
    },
    "conversion": {
      "primary_cta_text": "Book a growth audit",
      "primary_cta_url": "https://example.com/demo"
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

---

### Strategic Planning Topics

#### Topic: `alignment_check`

Calculate alignment score between a goal and business foundation.

**Request:**

```json
{
  "topic_id": "alignment_check",
  "parameters": {
    "goal_id": "goal-123"
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of goal to check alignment for |

**Auto-enriched Parameters:** `goal`, `business_foundation` (vision, purpose, core_values)

**Response Model:** `AlignmentAnalysisResponse`

```json
{
  "topic_id": "alignment_check",
  "success": true,
  "data": {
    "alignment_score": 85,
    "alignment_level": "high",
    "factors": [
      {"factor": "Purpose Alignment", "score": 90, "reasoning": "Goal directly supports core purpose"},
      {"factor": "Values Alignment", "score": 80, "reasoning": "Reflects innovation and integrity values"}
    ]
  },
  "schema_ref": "AlignmentAnalysisResponse"
}
```

---

#### Topic: `alignment_explanation`

Get detailed explanation of an alignment score.

**Request:**

```json
{
  "topic_id": "alignment_explanation",
  "parameters": {
    "goal_id": "goal-123",
    "alignment_score": 85
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of goal |
| `alignment_score` | integer | Yes | Previously calculated alignment score |

**Response Model:** `AlignmentExplanationResponse`

---

#### Topic: `alignment_suggestions`

Get suggestions to improve goal alignment with business foundation.

**Request:**

```json
{
  "topic_id": "alignment_suggestions",
  "parameters": {
    "goal_id": "goal-123",
    "alignment_score": 65
  }
}
```

**Response Model:** `AlignmentSuggestionsResponse`

```json
{
  "topic_id": "alignment_suggestions",
  "success": true,
  "data": {
    "current_score": 65,
    "suggestions": [
      {
        "suggestion": "Reframe the goal to emphasize customer impact",
        "expected_improvement": 15,
        "reasoning": "Better connects to your purpose statement"
      },
      {
        "suggestion": "Add specific metrics tied to core values",
        "expected_improvement": 10,
        "reasoning": "Makes integrity and excellence measurable"
      }
    ],
    "potential_score": 90
  },
  "schema_ref": "AlignmentSuggestionsResponse"
}
```

---

#### Topic: `strategy_suggestions`

Get AI suggestions for strategies based on goals and business foundation.

**Request:**

```json
{
  "topic_id": "strategy_suggestions",
  "parameters": {}
}
```

**Auto-enriched Parameters:** `goals`, `business_foundation`, `existing_strategies`

**Response Model:** `StrategySuggestionsResponse`

---

#### Topic: `measure_recommendations`

Get AI recommendations for measures to track goal progress.

**Request:**

```json
{
  "topic_id": "measure_recommendations",
  "parameters": {}
}
```

**Auto-enriched Parameters:** `goals`, `business_context`, `existing_measures`

**Response Model:** `MeasureRecommendationsResponse`

```json
{
  "topic_id": "measure_recommendations",
  "success": true,
  "data": {
    "recommendations": [
      {
        "name": "Customer Acquisition Cost (CAC)",
        "description": "Average cost to acquire a new customer",
        "unit": "USD",
        "direction": "down",
        "frequency": "monthly",
        "reasoning": "Critical for measuring marketing efficiency"
      },
      {
        "name": "Net Promoter Score (NPS)",
        "description": "Customer satisfaction and loyalty indicator",
        "unit": "score",
        "direction": "up",
        "frequency": "quarterly",
        "reasoning": "Aligns with your value of customer excellence"
      }
    ],
    "total_recommendations": 5
  },
  "schema_ref": "MeasureRecommendationsResponse"
}
```

---

### Operations AI Topics

#### Topic: `root_cause_suggestions`

Get AI suggestions for root causes of an issue.

**Request:**

```json
{
  "topic_id": "root_cause_suggestions",
  "parameters": {
    "issue_id": "issue-456"
  }
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_id` | string | Yes | ID of issue to analyze |

**Auto-enriched Parameters:** `issue`, `business_context`

**Response Model:** `RootCauseSuggestionsResponse`

```json
{
  "topic_id": "root_cause_suggestions",
  "success": true,
  "data": {
    "issue_summary": "Declining customer retention rate",
    "potential_causes": [
      {
        "cause": "Inadequate onboarding process",
        "likelihood": "high",
        "evidence": "Customer feedback mentions confusion in first 30 days",
        "investigation_steps": ["Review onboarding completion rates", "Survey churned customers"]
      },
      {
        "cause": "Feature gaps vs. competitors",
        "likelihood": "medium",
        "evidence": "Exit surveys mention missing integrations",
        "investigation_steps": ["Competitive feature analysis", "Review feature requests"]
      }
    ]
  },
  "schema_ref": "RootCauseSuggestionsResponse"
}
```

---

#### Topic: `swot_analysis`

Generate a SWOT analysis based on business context.

**Request:**

```json
{
  "topic_id": "swot_analysis",
  "parameters": {}
}
```

**Auto-enriched Parameters:** `business_foundation`, `goals`, `strategies`, `measures_summary`

**Response Model:** `SWOTAnalysisResponse`

---

#### Topic: `action_suggestions`

Get AI-suggested actions for an issue.

**Request:**

```json
{
  "topic_id": "action_suggestions",
  "parameters": {
    "issue_id": "issue-456"
  }
}
```

**Response Model:** `ActionSuggestionsResponse`

---

#### Topic: `optimize_action_plan`

Optimize an existing action plan for better outcomes.

**Request:**

```json
{
  "topic_id": "optimize_action_plan",
  "parameters": {
    "goal_id": "goal-123"
  }
}
```

**Auto-enriched Parameters:** `goal`, `actions`, `business_context`

**Response Model:** `OptimizedActionPlanResponse`

---

### Analysis Topics

#### Topic: `measure_analysis`

Analyze measure performance and trends.

**Request:**

```json
{
  "topic_id": "measure_analysis",
  "parameters": {
    "performance_data": {
      "period": "Q4 2025",
      "metrics": [...]
    }
  }
}
```

**Auto-enriched Parameters:** `measures`

**Response Model:** `MeasurePerformanceResponse`

---

## Available Parameter Reference

### Business Foundation Parameters

These parameters are automatically fetched from the Account Service:

| Parameter | Type | Description |
|-----------|------|-------------|
| `vision` | string | Organization's vision statement |
| `purpose` | string | Organization's purpose statement |
| `icas` | array | Ideal Client Avatars with demographics, pain points, goals |
| `core_values` | array | List of core value objects with name, description |
| `pillars` | array | Business foundation pillars |
| `industry` | string | Industry classification |
| `business_type` | string | Type of business |
| `business_stage` | string | Current business stage |

### Strategy Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `strategy` | object | Single strategy details |
| `strategy_name` | string | Strategy name |
| `strategy_description` | string | Strategy description |
| `strategy_alignment_score` | integer | Alignment with business foundation |
| `strategies` | array | All strategies for tenant |

### Goal Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `goal` | object | Complete goal data |
| `goal_name` | string | Goal name/title |
| `goal_description` | string | Goal description |
| `goal_status` | string | Current status |
| `goal_progress` | integer | Progress percentage (0-100) |
| `goal_due_date` | string | Target completion date |
| `goals` | array | All goals for user |
| `goals_count` | integer | Total number of goals |

### Measure Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `measure` | object | Complete measure data |
| `measure_name` | string | Measure name |
| `measure_description` | string | Measure description |
| `measure_unit` | string | Unit of measurement |
| `measure_direction` | string | Target direction (up/down/maintain) |
| `measure_type` | string | Measure type |
| `measure_current_value` | number | Current value |
| `measures` | array | All measures for tenant |
| `measures_count` | integer | Total number of measures |
| `measures_summary` | object | Aggregated measures summary |

### Action Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | object | Complete action data |
| `action_title` | string | Action title |
| `action_description` | string | Action description |
| `action_status` | string | Current status |
| `action_priority` | string | Priority level |
| `action_due_date` | string | Due date |
| `actions` | array | All actions |

### Issue Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `issue` | object | Complete issue data |
| `issue_title` | string | Issue title |
| `issue_description` | string | Issue description |
| `issue_status` | string | Current status |
| `issue_priority` | string | Priority level |
| `issues` | array | All issues |

### People & Organization Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `people` | array | All people in organization |
| `person` | object | Single person details |
| `departments` | array | Organization departments |
| `positions` | array | Organization positions |

---

## Response Model Schemas

### OnboardingReviewResponse

Used by: `niche_review`, `ica_review`, `value_proposition_review`

```typescript
interface OnboardingReviewResponse {
  qualityReview: string;  // AI review with feedback
  suggestions: SuggestionVariation[];  // Exactly 3 suggestions
}

interface SuggestionVariation {
  text: string;      // Suggested text variation
  reasoning: string; // Why this variation is recommended
}
```

### AlignmentAnalysisResponse

Used by: `alignment_check`

```typescript
interface AlignmentAnalysisResponse {
  alignment_score: number;  // 0-100
  alignment_level: "low" | "medium" | "high";
  factors: AlignmentFactor[];
}

interface AlignmentFactor {
  factor: string;
  score: number;
  reasoning: string;
}
```

### MeasureRecommendationsResponse

Used by: `measure_recommendations`

```typescript
interface MeasureRecommendationsResponse {
  recommendations: MeasureRecommendation[];
  total_recommendations: number;
}

interface MeasureRecommendation {
  name: string;
  description: string;
  unit: string;
  direction: "up" | "down" | "maintain";
  frequency: string;
  reasoning: string;
}
```

**JSON Schemas:** Available via `GET /ai/schemas/{schema_name}`

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
| 500 | `Parameter enrichment failed` | Backend data source unavailable |

---

## Usage Examples

### JavaScript/TypeScript

```typescript
// Basic execution with request parameters only
const alignmentResult = await coachingClient.post('/ai/execute', {
  topic_id: 'alignment_check',
  parameters: {
    goal_id: 'goal-123'  // Only need to provide IDs
  }
});

// The backend automatically fetches goal details and business foundation
const { alignment_score, factors } = alignmentResult.data.data;

// Onboarding review (requires full content)
const nicheReview = await coachingClient.post('/ai/execute', {
  topic_id: 'niche_review',
  parameters: {
    current_value: 'We help small businesses grow'
  }
});

const { qualityReview, suggestions } = nicheReview.data.data;
```

### Python

```python
import httpx

async def check_alignment(goal_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/ai/execute",
            json={
                "topic_id": "alignment_check",
                "parameters": {"goal_id": goal_id}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()["data"]
```

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

**Response (Completed):**

```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "topicId": "niche_review",
    "createdAt": "2026-01-11T20:00:00Z",
    "completedAt": "2026-01-11T20:00:35Z",
    "result": {
      "qualityReview": "...",
      "suggestions": [...]
    },
    "processingTimeMs": 35000
  }
}
```

---

### WebSocket Events

Results are delivered via the existing WebSocket connection at `wss://{WEBSOCKET_URL}`.

#### ai.job.completed

```json
{
  "type": "ai.job.completed",
  "timestamp": "2026-01-11T20:00:35Z",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "topicId": "niche_review",
    "result": { ... },
    "processingTimeMs": 35000
  }
}
```

#### ai.job.failed

```json
{
  "type": "ai.job.failed",
  "timestamp": "2026-01-11T20:00:45Z",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "topicId": "niche_review",
    "error": "LLM provider timeout after 60 seconds",
    "errorCode": "LLM_TIMEOUT"
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

**Recommended:** Use async for onboarding review topics (`niche_review`, `ica_review`, `value_proposition_review`) as they may take 30-60 seconds depending on LLM load.

---

## Coaching Conversation Sessions

The Coaching Conversation endpoints provide multi-turn conversational coaching interactions. Unlike single-shot `/ai/execute` endpoints, coaching sessions maintain state across multiple messages.

### Base URL

All coaching conversation endpoints are prefixed with `/ai/coaching`.

**Full URL Pattern:** `{BASE_URL}/ai/coaching/{endpoint}`

### Available Coaching Topics

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
      "description": "string (10-500 chars)",
      "importance": "string (10-500 chars)"
    }
  ],
  "summary": "string (50-1000 chars)"
}
```

#### PurposeResult (topic: `purpose`)

```json
{
  "purpose_statement": "string (20-500 chars)",
  "why_it_matters": "string (50-1000 chars)",
  "how_it_guides": "string (50-1000 chars)"
}
```

#### VisionResult (topic: `vision`)

```json
{
  "vision_statement": "string (20-500 chars)",
  "time_horizon": "string (1-50 chars)",
  "key_aspirations": ["string"]
}
```

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
| `topic_id` | string | Yes | ID of the coaching topic |
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
    "message": "Welcome! Let's begin exploring your core values...",
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

**Response (In Progress):**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "message": "That's wonderful! Can you tell me more about how integrity shows up in your daily business decisions?",
    "status": "active",
    "turn": 3,
    "max_turns": 10,
    "is_final": false,
    "message_count": 6,
    "result": null
  }
}
```

**Response (Auto-Completed):**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "message": "Thank you for this wonderful conversation! I've captured your core values...",
    "status": "completed",
    "turn": 8,
    "is_final": true,
    "result": {
      "values": [...],
      "summary": "..."
    }
  }
}
```

---

### POST /ai/coaching/pause

Pause an active coaching session.

### POST /ai/coaching/complete

Complete a coaching session and extract results.

### POST /ai/coaching/cancel

Cancel a coaching session.

### GET /ai/coaching/session

Get detailed information about a coaching session.

### GET /ai/coaching/sessions

List all coaching sessions for the current user.

### GET /ai/coaching/topics

Get all coaching topics with user's completion status.

---

### Error Response Format

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
| 400 | SESSION_NOT_ACTIVE | Session is not in an active state |
| 400 | VALIDATION_ERROR | Request validation failed |
| 403 | SESSION_ACCESS_DENIED | User does not have access to this session |
| 409 | SESSION_CONFLICT | Another user has an active session |
| 410 | SESSION_EXPIRED | Session has expired |
| 410 | SESSION_IDLE_TIMEOUT | Session exceeded idle timeout |
| 422 | SESSION_NOT_FOUND | Session not found |
| 422 | MAX_TURNS_REACHED | Maximum conversation turns reached |
| 422 | INVALID_TOPIC | Topic not found or invalid |
| 500 | EXTRACTION_FAILED | Failed to extract results |

---

## Changelog

### Version 2.0 (January 2026)

- **Terminology Update:** Replaced all "KPI" references with "Measure"
- **New Data Sources:** Added strategy, measure, people, and organization parameters
- **Parameter Enrichment:** Documented automatic parameter enrichment system
- **New Topics:** Added strategic planning topics (alignment_check, alignment_explanation, alignment_suggestions, strategy_suggestions, measure_recommendations)
- **New Topics:** Added operations AI topics (root_cause_suggestions, swot_analysis, action_suggestions, optimize_action_plan)
- **New Topics:** Added analysis topics (measure_analysis)
- **Parameter Reference:** Complete reference of all available parameters by source
- **Response Models:** Added schemas for new response models

### Version 1.2 (December 2025)

- Added async execution endpoints
- Added coaching conversation sessions
- Added website_scan topic

---

_This document will be updated as additional topics are activated in the unified AI endpoint._
