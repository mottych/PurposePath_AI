# PurposePath AI Coaching API Documentation

**Version:** 2.0.0  
**Last Updated:** October 10, 2025  
**Base URL:** `/api/v1`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Conversation Endpoints](#conversation-endpoints)
5. [Analysis Endpoints](#analysis-endpoints)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Overview

The PurposePath AI Coaching API provides intelligent coaching and business analysis capabilities through conversational AI and strategic analysis tools.

### Key Features

- **Conversational Coaching** - Interactive sessions on core values, purpose, vision, and goals
- **Alignment Analysis** - Analyze how goals align with purpose and values
- **Strategy Analysis** - Evaluate strategy effectiveness and get recommendations
- **KPI Analysis** - Assess KPI effectiveness and metric recommendations
- **Operational Analysis** - SWOT, root cause, and action plan analysis

### Architecture

- **Authentication**: JWT Bearer token-based
- **User Context**: Extracted from token (no user_id in request bodies)
- **Multi-Tenancy**: Tenant-scoped data isolation
- **Rate Limiting**: Per-user token bucket (100 burst, 10/sec default)

---

## Authentication

All API endpoints require authentication using JWT Bearer tokens.

### Request Headers

```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

### Token Structure

The JWT token must include the following claims:

```json
{
  "sub": "user_123",           // User ID
  "tenant_id": "tenant_456",   // Tenant ID
  "email": "user@example.com", // User email (optional)
  "roles": ["user"],           // User roles (optional)
  "scopes": ["read:conversations", "write:conversations"], // OAuth2 scopes (optional)
  "exp": 1699564800,           // Expiration timestamp
  "iat": 1699478400            // Issued at timestamp
}
```

### User Context

The API automatically extracts user context from the JWT:

```python
class UserContext:
    user_id: str        # From 'sub' claim
    tenant_id: str      # From 'tenant_id' claim
    email: str | None   # From 'email' claim
    roles: list[str]    # From 'roles' claim
    scopes: list[str]   # From 'scopes' claim
```

**Security Note**: `user_id` and `tenant_id` are NEVER in request bodies - they're extracted from the authenticated token.

---

## Common Patterns

### Request/Response Format

All endpoints use JSON for requests and responses.

**Success Response:**
```json
{
  "conversation_id": "conv_abc123",
  "status": "active",
  "data": { ... }
}
```

**Error Response:**
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": { ... }
}
```

### Pagination

List endpoints support pagination:

```http
GET /api/v1/conversations/?page=1&page_size=20
```

Response includes:
```json
{
  "conversations": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "has_more": true
}
```

### Filtering

Endpoints support filtering where applicable:

```http
GET /api/v1/conversations/?active_only=true
```

---

## Conversation Endpoints

### 1. Initiate Conversation

Start a new coaching conversation.

**Endpoint:** `POST /api/v1/conversations/initiate`

**Request Body:**
```json
{
  "topic": "core_values",
  "context": {
    "prior_sessions": 3,
    "last_topic": "purpose"
  },
  "language": "en"
}
```

**Parameters:**
- `topic` (required): Coaching topic
  - Values: `core_values`, `purpose`, `vision`, `goals`
- `context` (optional): Additional context dictionary
- `language` (optional): Language code (default: "en")

**Response:** `201 Created`
```json
{
  "conversation_id": "conv_abc123",
  "user_id": "user_123",
  "tenant_id": "tenant_456",
  "topic": "core_values",
  "status": "active",
  "current_phase": "introduction",
  "initial_message": "Welcome! Let's explore your core values. What matters most to you in your work and life?",
  "progress": 0.1,
  "created_at": "2025-10-10T21:00:00Z"
}
```

### 2. Send Message

Send a user message and receive AI coaching response.

**Endpoint:** `POST /api/v1/conversations/{conversation_id}/message`

**Request Body:**
```json
{
  "user_message": "I value honesty and transparency in all my work.",
  "metadata": {}
}
```

**Parameters:**
- `user_message` (required): User's message (10-2000 chars)
- `metadata` (optional): Additional metadata

**Response:** `200 OK`
```json
{
  "conversation_id": "conv_abc123",
  "ai_response": "That's wonderful! Honesty is a powerful core value. Can you share a specific example of when you demonstrated this value?",
  "follow_up_question": null,
  "current_phase": "exploration",
  "progress": 0.3,
  "is_complete": false,
  "insights": [
    "User mentioned: I value honesty and transparency..."
  ],
  "identified_values": [],
  "next_steps": null
}
```

### 3. Get Conversation

Retrieve full conversation details.

**Endpoint:** `GET /api/v1/conversations/{conversation_id}`

**Response:** `200 OK`
```json
{
  "conversation_id": "conv_abc123",
  "user_id": "user_123",
  "tenant_id": "tenant_456",
  "topic": "core_values",
  "status": "active",
  "current_phase": "exploration",
  "progress": 0.3,
  "messages": [
    {
      "role": "assistant",
      "content": "Welcome! Let's explore your core values.",
      "timestamp": "2025-10-10T21:00:00Z",
      "metadata": {}
    },
    {
      "role": "user",
      "content": "I value honesty and transparency.",
      "timestamp": "2025-10-10T21:01:00Z",
      "metadata": {}
    }
  ],
  "insights": ["Value: honesty", "Value: transparency"],
  "identified_values": [],
  "created_at": "2025-10-10T21:00:00Z",
  "updated_at": "2025-10-10T21:01:00Z",
  "completed_at": null,
  "metadata": {}
}
```

### 4. List Conversations

List user's conversations with pagination.

**Endpoint:** `GET /api/v1/conversations/`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (1-100, default: 20)
- `active_only` (optional): Filter to active conversations only

**Response:** `200 OK`
```json
{
  "conversations": [
    {
      "conversation_id": "conv_abc123",
      "user_id": "user_123",
      "tenant_id": "tenant_456",
      "topic": "core_values",
      "status": "active",
      "current_phase": "exploration",
      "progress": 0.3,
      "message_count": 5,
      "created_at": "2025-10-10T21:00:00Z",
      "updated_at": "2025-10-10T21:05:00Z",
      "completed_at": null
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

### 5. Pause Conversation

Pause an active conversation.

**Endpoint:** `POST /api/v1/conversations/{conversation_id}/pause`

**Request Body:**
```json
{
  "reason": "Taking a break to reflect"
}
```

**Response:** `204 No Content`

### 6. Complete Conversation

Mark a conversation as complete.

**Endpoint:** `POST /api/v1/conversations/{conversation_id}/complete`

**Request Body:**
```json
{
  "feedback": "Great session! Very insightful.",
  "rating": 5
}
```

**Parameters:**
- `feedback` (optional): User feedback text
- `rating` (optional): Rating 1-5

**Response:** `204 No Content`

---

## Analysis Endpoints

### 1. Alignment Analysis

Analyze how goals/actions align with purpose and values.

**Endpoint:** `POST /api/v1/analysis/alignment`

**Request Body:**
```json
{
  "text_to_analyze": "Our Q1 goals focus on increasing revenue by 20% while maintaining our commitment to customer service excellence and ethical business practices.",
  "context": {
    "purpose": "To provide exceptional customer experiences that drive sustainable growth",
    "core_values": ["Customer-first", "Integrity", "Excellence"]
  }
}
```

**Parameters:**
- `text_to_analyze` (required): Text to analyze (10-10,000 chars)
- `context` (optional): Additional context (purpose, values, etc.)

**Response:** `201 Created`
```json
{
  "analysis_id": "anls_1699478400.123",
  "analysis_type": "alignment",
  "scores": {
    "overall_score": 85.0,
    "purpose_alignment": 90.0,
    "values_alignment": 82.0,
    "goal_clarity": 88.0
  },
  "overall_assessment": "Strong alignment detected between stated goals and core values. Revenue growth is balanced with service excellence.",
  "strengths": [
    "Clear value alignment with customer service excellence",
    "Well-defined purpose integration",
    "Ethical considerations prominent"
  ],
  "misalignments": [
    "Revenue target could be more explicitly tied to customer value"
  ],
  "recommendations": [
    {
      "action": "Add specific customer satisfaction metrics alongside revenue targets",
      "priority": "medium",
      "rationale": "Ensures customer-first value remains central to growth strategy"
    }
  ],
  "created_at": "2025-10-10T21:00:00Z",
  "metadata": {
    "user_id": "user_123",
    "tenant_id": "tenant_456",
    "analysis_version": "1.0"
  }
}
```

### 2. Strategy Analysis

Evaluate business strategy effectiveness.

**Endpoint:** `POST /api/v1/analysis/strategy`

**Request Body:**
```json
{
  "current_strategy": "We plan to grow through content marketing and strategic partnerships with complementary service providers.",
  "context": {
    "industry": "SaaS",
    "market_size": "Mid-market",
    "target_audience": "K-12 educators"
  }
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "anls_1699478400.456",
  "analysis_type": "strategy",
  "effectiveness_score": 75.0,
  "overall_assessment": "Strategy shows promise with clear market positioning, but could benefit from more specific execution plans.",
  "strengths": [
    "Clear market positioning in K-12 education",
    "Strong value proposition for educators",
    "Partnership approach leverages complementary strengths"
  ],
  "weaknesses": [
    "Limited differentiation in crowded SaaS market",
    "Execution plan lacks specific milestones",
    "Partnership criteria not well-defined"
  ],
  "opportunities": [
    "Growing market segment (K-12 digital transformation)",
    "Potential for data-driven personalization",
    "Strategic partnerships could accelerate market entry"
  ],
  "recommendations": [
    {
      "category": "Market Expansion",
      "recommendation": "Develop partnerships with 3-5 key education technology platforms",
      "priority": "high",
      "rationale": "Leverages existing distribution channels and credibility",
      "estimated_impact": "20-30% increase in market reach within 6 months"
    },
    {
      "category": "Differentiation",
      "recommendation": "Focus content marketing on unique pedagogical approach",
      "priority": "high",
      "rationale": "Creates defensible competitive moat",
      "estimated_impact": "15-20% improvement in conversion rates"
    }
  ],
  "created_at": "2025-10-10T21:00:00Z",
  "metadata": {
    "user_id": "user_123",
    "tenant_id": "tenant_456",
    "analysis_version": "1.0"
  }
}
```

### 3. KPI Analysis

Analyze KPI effectiveness and recommend improvements.

**Endpoint:** `POST /api/v1/analysis/kpi`

**Request Body:**
```json
{
  "current_kpis": [
    "Monthly Recurring Revenue",
    "Active Users",
    "Customer Acquisition Cost"
  ],
  "context": {
    "business_goals": ["Grow revenue", "Improve retention", "Reduce churn"],
    "stage": "growth",
    "industry": "SaaS"
  }
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "anls_1699478400.789",
  "analysis_type": "kpi",
  "kpi_effectiveness_score": 70.0,
  "overall_assessment": "Current KPIs cover key financial and usage metrics but miss important retention indicators.",
  "current_kpi_analysis": [
    {
      "kpi": "Monthly Recurring Revenue",
      "assessment": "Good financial metric for growth tracking",
      "relevance": "high",
      "recommendation": "Add MRR growth rate and cohort analysis"
    },
    {
      "kpi": "Active Users",
      "assessment": "Useful engagement metric but needs definition refinement",
      "relevance": "medium",
      "recommendation": "Define 'active' more precisely (e.g., DAU, WAU, MAU)"
    }
  ],
  "missing_kpis": [
    "Customer Churn Rate",
    "Net Promoter Score (NPS)",
    "Customer Lifetime Value (CLV)",
    "Net Revenue Retention"
  ],
  "recommended_kpis": [
    {
      "kpi_name": "Customer Churn Rate",
      "description": "Percentage of customers who cancel subscriptions monthly",
      "rationale": "Critical for SaaS business health and directly ties to retention goal",
      "target_range": "< 5% monthly",
      "measurement_frequency": "monthly"
    },
    {
      "kpi_name": "Net Revenue Retention",
      "description": "Revenue retained from existing customers including expansions and downgrades",
      "rationale": "Indicates product-market fit and expansion potential",
      "target_range": "> 100%",
      "measurement_frequency": "monthly"
    }
  ],
  "created_at": "2025-10-10T21:00:00Z",
  "metadata": {
    "user_id": "user_123",
    "tenant_id": "tenant_456",
    "analysis_version": "1.0"
  }
}
```

### 4. Operations Analysis

Perform operational analysis (SWOT, root cause, action plans).

**Endpoint:** `POST /api/v1/analysis/operations`

**Request Body (SWOT):**
```json
{
  "analysis_type": "swot",
  "description": "Analyze our company's position in the EdTech market for K-12",
  "context": {
    "company_size": "50 employees",
    "market_segment": "K-12 education technology"
  }
}
```

**Request Body (Root Cause):**
```json
{
  "analysis_type": "root_cause",
  "description": "Customer satisfaction scores have been declining for 3 months despite product improvements",
  "context": {
    "recent_changes": ["New UI rollout", "Pricing adjustment", "Support team restructure"]
  }
}
```

**Request Body (Action Plan):**
```json
{
  "analysis_type": "action_plan",
  "description": "Launch new product feature for teacher collaboration within 3 months",
  "context": {
    "team_size": "5 developers",
    "budget": "$50,000",
    "constraints": ["Must integrate with existing platform", "Need teacher beta testers"]
  }
}
```

**Response:** `201 Created`
```json
{
  "analysis_id": "anls_1699478400.101",
  "analysis_type": "operations",
  "specific_analysis_type": "swot",
  "findings": {
    "strengths": [
      "Strong product-market fit in K-12 segment",
      "Experienced education-focused team",
      "High customer retention among power users"
    ],
    "weaknesses": [
      "Limited marketing budget compared to competitors",
      "Slower feature development cycle",
      "Support team capacity constraints"
    ],
    "opportunities": [
      "Growing K-12 digital transformation market",
      "Partnership potential with school districts",
      "International expansion (English-speaking markets)"
    ],
    "threats": [
      "Well-funded competitors entering market",
      "Budget cuts in education sector",
      "Regulatory changes in data privacy (student data)"
    ]
  },
  "recommendations": [
    {
      "action": "Prioritize feature development on high-impact teacher tools",
      "priority": "high",
      "timeline": "Next 3 months",
      "rationale": "Addresses weakness while leveraging strength"
    },
    {
      "action": "Explore strategic partnerships with 2-3 large school districts",
      "priority": "high",
      "timeline": "Next 6 months",
      "rationale": "Capitalizes on opportunity while building competitive moat"
    }
  ],
  "priority_actions": [
    "Address support capacity constraints immediately",
    "Build strategic partnerships to counter competitive threats",
    "Focus on product differentiation through pedagogical innovation"
  ],
  "created_at": "2025-10-10T21:00:00Z",
  "metadata": {
    "user_id": "user_123",
    "tenant_id": "tenant_456",
    "analysis_version": "1.0"
  }
}
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": { ... }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request succeeded, no content to return |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource state conflict (e.g., conversation not active) |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Common Error Codes

**Authentication Errors:**
- `invalid_token` - JWT token is invalid or expired
- `missing_token` - Authorization header not provided

**Validation Errors:**
- `validation_error` - Request validation failed
- `domain_validation_error` - Business rule validation failed

**Resource Errors:**
- `conversation_not_found` - Conversation doesn't exist
- `conversation_not_active` - Conversation is paused or completed

**Rate Limiting:**
- `rate_limit_exceeded` - Too many requests, retry after cooldown

---

## Rate Limiting

The API implements per-user rate limiting using a token bucket algorithm.

### Default Limits

- **Burst Capacity**: 100 requests
- **Refill Rate**: 10 requests/second

### Endpoint-Specific Limits

| Endpoint Prefix | Burst | Rate |
|-----------------|-------|------|
| `/api/v1/analysis/*` | 20 | 1/sec |
| `/api/v1/conversations/initiate` | 10 | 0.5/sec |
| All others | 100 | 10/sec |

### Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
```

### Rate Limit Exceeded

When rate limit is exceeded, you'll receive:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later."
}
```

---

## Examples

### Complete Conversation Flow

```javascript
// 1. Initiate conversation
const initiateResponse = await fetch('/api/v1/conversations/initiate', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    topic: 'core_values',
    language: 'en'
  })
});

const conversation = await initiateResponse.json();
console.log(conversation.initial_message);

// 2. Send user message
const messageResponse = await fetch(
  `/api/v1/conversations/${conversation.conversation_id}/message`,
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_JWT_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      user_message: 'I value integrity and innovation in my work.'
    })
  }
);

const aiResponse = await messageResponse.json();
console.log(aiResponse.ai_response);

// 3. Get conversation history
const historyResponse = await fetch(
  `/api/v1/conversations/${conversation.conversation_id}`,
  {
    headers: {
      'Authorization': 'Bearer YOUR_JWT_TOKEN'
    }
  }
);

const history = await historyResponse.json();
console.log(`Messages: ${history.messages.length}, Progress: ${history.progress}`);

// 4. Complete conversation
await fetch(
  `/api/v1/conversations/${conversation.conversation_id}/complete`,
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_JWT_TOKEN',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      feedback: 'Very helpful session!',
      rating: 5
    })
  }
);
```

### Strategy Analysis

```python
import requests

# Analyze business strategy
response = requests.post(
    'https://api.purposepath.ai/api/v1/analysis/strategy',
    headers={
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    },
    json={
        'current_strategy': '''
            Our growth strategy focuses on:
            1. Content marketing to establish thought leadership
            2. Strategic partnerships with complementary platforms
            3. Product-led growth with freemium model
        ''',
        'context': {
            'industry': 'EdTech',
            'stage': 'Series A',
            'target_market': 'K-12 schools'
        }
    }
)

analysis = response.json()
print(f"Effectiveness: {analysis['effectiveness_score']}/100")
print(f"Strengths: {analysis['strengths']}")
print(f"Recommendations: {len(analysis['recommendations'])}")
```

### Error Handling

```typescript
async function analyzeAlignment(text: string): Promise<AlignmentAnalysisResponse> {
  try {
    const response = await fetch('/api/v1/analysis/alignment', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text_to_analyze: text,
        context: {
          purpose: 'Our company purpose...',
          core_values: ['Integrity', 'Innovation', 'Customer-first']
        }
      })
    });

    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          throw new AuthenticationError('Please log in again');
        case 429:
          throw new RateLimitError('Too many requests, please wait');
        case 422:
          throw new ValidationError(error.details);
        default:
          throw new Error(error.message);
      }
    }

    return await response.json();
    
  } catch (error) {
    console.error('Analysis failed:', error);
    throw error;
  }
}
```

---

## Support

For API support and questions:
- **Documentation**: https://docs.purposepath.ai
- **Email**: api-support@purposepath.ai
- **GitHub Issues**: https://github.com/purposepath/api/issues

---

**Last Updated**: October 10, 2025  
**API Version**: 2.0.0
