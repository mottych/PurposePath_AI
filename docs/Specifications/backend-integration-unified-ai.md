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
- `website_scan` - Scan website and extract business info
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

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-09 | Initial version with onboarding review topics |

---

_This document will be updated as additional topics are activated in the unified AI endpoint._
