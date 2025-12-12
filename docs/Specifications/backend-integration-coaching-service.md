# Coaching Service Backend Integration Specifications

**Version:** 3.2  
**Last Updated:** December 14, 2025  
**Service Base URL:** `{REACT_APP_COACHING_API_URL}`  
**Default (Localhost):** `http://localhost:8000`  
**Dev Environment:** `https://api.dev.purposepath.app/coaching/api/v1`

[← Back to Index](./backend-integration-index.md)

---

## URL Structure

All endpoints in this document are shown as **relative paths** from the base URL.

**Example:**

- **Endpoint:** `/coaching/alignment-check`
- **Full URL:** `https://api.dev.purposepath.app/coaching/api/v1/coaching/alignment-check`
- **Frontend Usage:** `coachingClient.post('/coaching/alignment-check', data)`

The base URL already includes `/coaching/api/v1`, so endpoints should not repeat this prefix.

## Overview

The Coaching Service handles all AI/ML operations, including goal alignment calculations, strategy suggestions, KPI recommendations, business insights, coaching conversations, and operations AI assistance.

### Frontend Implementation

- **Primary Client:** `coachingClient` (axios instance in `src/services/api.ts`)
- **Related Files:**
  - `src/services/api.ts` - Main ApiClient class with coachingClient
  - `src/services/alignment-engine-service.ts` - Alignment calculations
  - `src/services/strategy-suggestion-service.ts` - Strategy AI
  - `src/services/kpi-recommendation-service.ts` - KPI AI
  - `src/services/operations-ai-service.ts` - Operations AI helpers
  - `src/services/business-data.ts` - Business metrics

---

## Strategic Planning AI Endpoints

### POST /coaching/alignment-check

Calculate alignment score for a goal against business foundation.

**Note:** Full URL: `{BASE_URL}/coaching/alignment-check`

**Request:**

```json
{
  "goalIntent": "string",
  "strategies": ["string"],
  "kpis": ["string"],
  "businessFoundation": {
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string?",
    "valueProposition": "string?"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "alignmentScore": 85,
    "score": 85,
    "explanation": "This goal strongly aligns with your business vision...",
    "suggestions": [
      "Consider adding a strategy focused on...",
      "Your KPIs could be more specific about..."
    ],
    "componentScores": {
      "intentAlignment": 90,
      "strategyAlignment": 85,
      "kpiRelevance": 80
    },
    "breakdown": {
      "visionAlignment": 88,
      "purposeAlignment": 85,
      "valuesAlignment": 82
    },
    "lastUpdated": "2025-10-13T14:30:00Z"
  }
}
```

**Notes:**

- Scores are 0-100 percentages
- Called automatically when goal, strategies, or KPIs change
- Results cached to reduce API calls

**Implementation:** `src/services/alignment-engine-service.ts` → `calculateAlignment()`

---

### POST /coaching/alignment-explanation

Get detailed AI explanation for goal alignment (more verbose than alignment-check).

**Note:** Full URL: `{BASE_URL}/coaching/alignment-explanation`

**Request:**

```json
{
  "goal": {
    "intent": "string",
    "strategies": [{"description": "string"}],
    "kpis": [{"sharedKpiId": "string", "name": "string"}]
  },
  "businessFoundation": {
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string?",
    "valueProposition": "string?"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "explanation": "Your goal 'Increase customer retention' demonstrates strong alignment with your business foundation in several ways: 1) It directly supports your vision of... 2) The strategies outlined... 3) However, consider..."
  }
}
```

**Notes:**

- More detailed explanation than `alignment-check`
- Used for detailed alignment panels
- May take longer to process

**Implementation:** `src/services/alignment-engine-service.ts` → `getAlignmentExplanation()`

---

### POST /coaching/alignment-suggestions

Get AI-generated suggestions for improving goal alignment.

**Note:** Full URL: `{BASE_URL}/coaching/alignment-suggestions`

**Request:**

```json
{
  "goal": {
    "intent": "string",
    "strategies": [{"description": "string"}],
    "kpis": [{"sharedKpiId": "string"}]
  },
  "businessFoundation": {
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "suggestions": [
      "Consider reframing your goal to more explicitly connect with your core value of 'Innovation'",
      "Add a strategy that addresses the gap between current state and vision",
      "Include KPIs that measure progress toward your long-term purpose"
    ]
  }
}
```

**Implementation:** `src/services/alignment-engine-service.ts` → `getAlignmentSuggestions()`

---

### POST /coaching/strategy-suggestions

Get AI-generated strategy recommendations for a goal.

**Note:** Full URL: `{BASE_URL}/coaching/strategy-suggestions`

**Request:**

```json
{
  "goalIntent": "string",
  "businessContext": {
    "industry": "string",
    "businessType": "string",
    "targetMarket": "string",
    "currentChallenges": ["string"]
  },
  "existingStrategies": ["string"],
  "constraints": {
    "budget": 50000,
    "timeline": "6 months",
    "resources": ["2 developers", "1 designer"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "suggestions": [{
      "title": "Implement Customer Feedback Loop",
      "description": "Create a systematic process for gathering and acting on customer feedback",
      "rationale": "This strategy will help you identify pain points and opportunities for retention",
      "difficulty": "medium",
      "timeframe": "2-3 months",
      "expectedImpact": "high",
      "prerequisites": [
        "CRM system in place",
        "Customer communication channels"
      ],
      "estimatedCost": 15000,
      "requiredResources": ["1 product manager", "feedback tool subscription"]
    }],
    "confidence": 0.85,
    "reasoning": "Based on your goal of increasing customer retention and your target market of B2B SaaS customers..."
  }
}
```

**Notes:**

- `difficulty`: "low" | "medium" | "high"
- `expectedImpact`: "low" | "medium" | "high"
- `confidence`: 0-1 scale
- Results depend on quality of business context provided

**Implementation:** `src/services/strategy-suggestion-service.ts` → `getStrategySuggestions()`

---

### POST /coaching/kpi-recommendations

Get AI-recommended KPIs for a goal and strategies.

**Note:** Full URL: `{BASE_URL}/coaching/kpi-recommendations`

**Request:**

```json
{
  "goalIntent": "string",
  "strategies": [{
    "description": "string",
    "category": "string?"
  }],
  "businessContext": {
    "industry": "string",
    "businessType": "string",
    "currentKPIs": ["string"]
  },
  "preferences": {
    "quantitative": true,
    "leadingIndicators": true,
    "laggingIndicators": true
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "recommendations": [{
      "name": "Customer Retention Rate",
      "description": "Percentage of customers retained over a period",
      "category": "customer",
      "unit": "percentage",
      "direction": "up",
      "formula": "(Customers at End - New Customers) / Customers at Start * 100",
      "rationale": "Directly measures success of retention strategies",
      "benchmark": {
        "industry": "SaaS",
        "typical": 85,
        "excellent": 95
      },
      "isLeading": false,
      "frequency": "monthly",
      "difficulty": "low",
      "dataSource": "CRM system"
    }],
    "confidence": 0.90,
    "reasoning": "These KPIs align with your goal and provide actionable metrics..."
  }
}
```

**Notes:**

- `direction`: "up" (higher is better) | "down" (lower is better)
- `isLeading`: true for predictive metrics, false for historical
- `difficulty`: how hard to measure/track

**Implementation:** `src/services/kpi-recommendation-service.ts` → `getKPIRecommendations()`

---

## Operations AI Endpoints

### POST /operations/strategic-alignment

Analyze strategic alignment of operations (actions) with business goals.

**Note:** Full URL: `{BASE_URL}/operations/strategic-alignment`

**Request:**

```json
{
  "actions": [{
    "id": "string",
    "title": "string",
    "description": "string",
    "priority": "string",
    "status": "string"
  }],
  "goals": [{
    "id": "string",
    "intent": "string",
    "strategies": ["string"]
  }],
  "businessFoundation": {
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "alignmentAnalysis": [{
      "actionId": "string",
      "alignmentScore": 78,
      "strategicConnections": [{
        "goalId": "string",
        "goalTitle": "string",
        "alignmentScore": 85,
        "impact": "high|medium|low|critical"
      }],
      "recommendations": [
        "Link this action to Goal X for better tracking",
        "Consider prioritizing this action higher due to strategic importance"
      ]
    }],
    "overallAlignment": 82,
    "insights": [
      "30% of your actions are not strategically aligned",
      "Your highest priority actions align well with business goals"
    ]
  }
}
```

**Notes:**

- Helps identify misaligned operational work
- Recommends action prioritization based on strategic value

**Implementation:** `src/services/operations-ai-service.ts` → `analyzeStrategicAlignment()`

---

### POST /operations/root-cause-suggestions

Get AI suggestions for root cause analysis methods.

**Note:** Full URL: `{BASE_URL}/operations/root-cause-suggestions`

**Request:**

```json
{
  "issueTitle": "string",
  "issueDescription": "string",
  "businessImpact": "low|medium|high|critical",
  "context": {
    "reportedBy": "string",
    "dateReported": "string",
    "relatedActions": ["string"],
    "affectedAreas": ["string"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": [{
    "method": "five_whys|fishbone|swot|pareto",
    "confidence": 0.85,
    "suggestions": {
      "fiveWhys": {
        "suggestedQuestions": [
          "Why is customer churn increasing?",
          "Why are customers dissatisfied with onboarding?",
          "Why is the onboarding process confusing?"
        ],
        "potentialRootCauses": [
          "Lack of user documentation",
          "Complex product interface",
          "Missing customer success touchpoints"
        ]
      },
      "swot": {
        "strengths": ["Strong product features", "Good customer support"],
        "weaknesses": ["Poor onboarding experience", "Limited documentation"],
        "opportunities": ["Improve self-service resources", "Add guided tours"],
        "threats": ["Competitors with better onboarding", "Customer expectations rising"]
      }
    },
    "reasoning": "Given the customer-facing nature of this issue and its impact on retention, a Five Whys analysis combined with SWOT would be most effective..."
  }]
}
```

**Notes:**

- Multiple analysis methods suggested
- Confidence score indicates AI certainty
- Pre-filled suggestions to speed up analysis

**Implementation:** `src/services/operations-ai-service.ts` → `getRootCauseSuggestions()`

---

### POST /operations/action-suggestions

Get AI-generated action plan suggestions for an issue.

**Note:** Full URL: `{BASE_URL}/operations/action-suggestions`

**Request:**

```json
{
  "issue": {
    "title": "string",
    "description": "string",
    "impact": "low|medium|high|critical",
    "rootCause": "string?"
  },
  "constraints": {
    "timeline": "string?",
    "budget": 10000,
    "availableResources": ["2 developers", "1 designer"]
  },
  "context": {
    "relatedGoals": ["string"],
    "currentActions": ["string"],
    "businessPriorities": ["string"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": [{
    "title": "Create Interactive Onboarding Tutorial",
    "description": "Build step-by-step guided tour highlighting key product features",
    "priority": "high",
    "estimatedDuration": 40,
    "estimatedCost": 8000,
    "assignmentSuggestion": "Senior Frontend Developer + UX Designer",
    "dependencies": [
      "UX research on user pain points",
      "Product feature priority list"
    ],
    "confidence": 0.88,
    "reasoning": "This action directly addresses the root cause of confusing onboarding and fits within your budget and resource constraints",
    "expectedOutcome": "Reduce onboarding drop-off by 30-40%",
    "risks": ["May require product changes", "User adoption of tutorial"]
  }]
}
```

**Notes:**

- `estimatedDuration` in hours
- Actions ranked by effectiveness and feasibility
- Considers constraints provided

**Implementation:** `src/services/operations-ai-service.ts` → `getActionSuggestions()`

---

### POST /operations/prioritization-suggestions

Get AI suggestions for action prioritization.

**Note:** Full URL: `{BASE_URL}/operations/prioritization-suggestions`

**Request:**

```json
{
  "actions": [{
    "id": "string",
    "title": "string",
    "currentPriority": "low|medium|high|critical",
    "dueDate": "string",
    "impact": "string",
    "effort": "string",
    "status": "string",
    "linkedGoals": ["string"]
  }],
  "businessContext": {
    "currentGoals": ["string"],
    "constraints": ["string"],
    "urgentDeadlines": ["string"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": [{
    "actionId": "string",
    "suggestedPriority": "critical",
    "currentPriority": "medium",
    "reasoning": "This action unblocks 3 other high-priority items and aligns with your top business goal",
    "confidence": 0.92,
    "urgencyFactors": [
      "Blocking other work",
      "Customer deadline approaching",
      "Strategic importance"
    ],
    "impactFactors": [
      "Affects revenue",
      "Customer satisfaction",
      "Team productivity"
    ],
    "recommendedAction": "escalate",
    "estimatedBusinessValue": 50000
  }]
}
```

**Notes:**

- Analyzes priority based on dependencies, impact, and business context
- `recommendedAction`: "escalate" | "maintain" | "de-prioritize"

**Implementation:** `src/services/operations-ai-service.ts` → `getPrioritizationSuggestions()`

---

### POST /operations/scheduling-suggestions

Get AI suggestions for action scheduling optimization.

**Note:** Full URL: `{BASE_URL}/operations/scheduling-suggestions`

**Request:**

```json
{
  "actions": [{
    "id": "string",
    "title": "string",
    "estimatedDuration": 40,
    "dependencies": ["string"],
    "assignedTo": "string",
    "currentStartDate": "string?",
    "currentDueDate": "string?",
    "priority": "string"
  }],
  "constraints": {
    "teamCapacity": 160,
    "criticalDeadlines": [{
      "date": "2025-11-01",
      "description": "Product launch"
    }],
    "teamAvailability": [{
      "personId": "string",
      "hoursPerWeek": 40,
      "unavailableDates": ["string"]
    }]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": [{
    "actionId": "string",
    "suggestedStartDate": "2025-10-15",
    "suggestedDueDate": "2025-10-18",
    "reasoning": "This schedule respects dependencies, team capacity, and ensures completion before product launch deadline",
    "confidence": 0.87,
    "dependencies": ["Action B must complete first"],
    "resourceConsiderations": [
      "Assigned developer has 60% capacity this week",
      "Designer needed for final review"
    ],
    "risks": [
      "Tight timeline if dependencies slip",
      "Buffer recommended for testing"
    ],
    "alternativeSchedules": [{
      "startDate": "2025-10-20",
      "dueDate": "2025-10-25",
      "rationale": "More buffer, lower risk"
    }]
  }]
}
```

**Notes:**

- Optimizes for deadline adherence and resource utilization
- Considers dependencies and capacity constraints

**Implementation:** `src/services/operations-ai-service.ts` → `getSchedulingSuggestions()`

---

## Business Insights Endpoints

### GET /multitenant/conversations/business-data

Get business metrics and data summary.

**Note:** Full URL: `{BASE_URL}/multitenant/conversations/business-data`

**Response:**

```json
{
  "success": true,
  "data": {
    "revenue": {
      "current": 125000,
      "previous": 118000,
      "trend": "up",
      "changePercent": 5.9
    },
    "customers": {
      "total": 450,
      "new": 35,
      "churned": 12,
      "retentionRate": 94.7
    },
    "operations": {
      "activeGoals": 12,
      "completedActions": 45,
      "openIssues": 8
    },
    "team": {
      "size": 15,
      "utilization": 78,
      "satisfaction": 8.2
    }
  }
}
```

**Notes:**

- May be wrapped in `data` envelope or returned directly
- Used for dashboard and business context in AI requests

**Implementation:** `src/services/business-data.ts` → `getBusinessData()`

---

### POST /insights/generate

Generate fresh AI-powered coaching insights using LLM.

**Note:** Full URL: `{BASE_URL}/insights/generate`

**Query Parameters:**

- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)
- `category` - Filter by category (optional)
- `priority` - Filter by priority (optional)
- `status` - Filter by status (optional)

**Response:**

```json
{
  "success": true,
  "data": [{
    "id": "string",
    "title": "Customer Retention Opportunity",
    "description": "Your churn rate increased 15% last month. Consider implementing a customer success program.",
    "category": "operations",
    "priority": "high",
    "status": "active",
    "created_at": "2025-10-13T12:00:00Z",
    "updated_at": "2025-10-13T12:00:00Z",
    "metadata": {
      "conversation_count": 0,
      "business_impact": "medium",
      "effort_required": "medium"
    }
  }],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 8,
    "total_pages": 1
  }
}
```

**Notes:**

- **IMPORTANT:** This endpoint generates NEW insights using LLM (costs money!)
- Each call fetches fresh business data and runs AI analysis
- Frontend should persist results to .NET backend after generation
- For viewing existing insights, call .NET API directly (not this endpoint)
- `category`: "strategy" | "operations" | "finance" | "marketing" | "leadership" | "technology"
- `priority`: "low" | "medium" | "high" | "critical"
- `status`: "active" | "dismissed" | "acknowledged"

**Architecture Flow:**

1. User clicks "Generate Insights" → Frontend calls this endpoint
2. Python AI service fetches data from .NET APIs
3. Python AI service generates insights with Claude Sonnet
4. Returns insights to frontend
5. Frontend sends to .NET backend to persist
6. Subsequent views fetch from .NET (no Python call)

**Implementation:** `src/services/api.ts` → `ApiClient.generateCoachingInsights()`

---

## Onboarding AI Endpoints

### POST /suggestions/onboarding

Get AI suggestions for onboarding fields.

**Note:** Full URL: `{BASE_URL}/suggestions/onboarding`

**Request:**

```json
{
  "kind": "niche|ica|valueProposition",
  "current": "string?",
  "context": {
    "businessName": "string?",
    "industry": "string?",
    "products": ["string"]
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "suggestions": [
      "Small to medium-sized B2B SaaS companies seeking to improve operational efficiency",
      "Growth-stage startups in the productivity software space",
      "Service-based businesses looking to scale operations"
    ],
    "reasoning": "Based on your products and business type..."
  }
}
```

**Notes:**

- `kind`: "niche" | "ica" | "valueProposition"
- Helps users define business positioning during onboarding

**Implementation:** `src/services/api.ts` → `ApiClient.getOnboardingSuggestions()`

---

### POST /website/scan

Scan website URL to extract business information.

**Note:** Full URL: `{BASE_URL}/website/scan`

**Request:**

```json
{
  "url": "https://example.com"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "businessName": "Acme Corp",
    "industry": "Software",
    "description": "Enterprise productivity platform...",
    "products": ["Project Management", "Time Tracking"],
    "targetMarket": "Enterprise teams",
    "suggestedNiche": "Enterprise project management for distributed teams"
  }
}
```

**Notes:**

- Uses web scraping and AI to extract business info
- Results used to pre-fill onboarding form
- May fail if website has anti-scraping measures

**Implementation:** `src/services/api.ts` → `ApiClient.scanWebsite()`

---

### POST /coaching/onboarding

Get coaching assistance for onboarding sections.

**Note:** Full URL: `{BASE_URL}/coaching/onboarding`

**Request:**

```json
{
  "topic": "coreValues|purpose|vision",
  "message": "string",
  "context": {
    "businessName": "string",
    "industry": "string",
    "currentDraft": "string?"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "response": "To develop strong core values, think about what principles guide your business decisions. For example, if customer satisfaction is paramount, 'Customer First' could be a core value. Consider what makes your business unique and what you want your team culture to embody.",
    "suggestions": [
      "Innovation",
      "Integrity",
      "Customer Success",
      "Continuous Improvement"
    ]
  }
}
```

**Notes:**

- Interactive coaching for business foundation elements
- Provides context-aware guidance and examples

**Implementation:** `src/services/api.ts` → `ApiClient.getOnboardingCoaching()`

---

## Conversation Management Endpoints

### POST /conversations/initiate

Start new coaching conversation.

**Note:** Full URL: `{BASE_URL}/conversations/initiate`

**Request:**

```json
{
  "topic": "string",
  "initialMessage": "string?",
  "context": {
    "goalId": "string?",
    "issueId": "string?"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "topic": "string",
    "createdAt": "2025-10-13T14:30:00Z"
  }
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.initiateConversation()`

---

### POST /conversations/{id}/message

Send message to coaching conversation.

**Note:** Full URL: `{BASE_URL}/conversations/{id}/message`

**Path Parameters:**

- `id` - Conversation ID

**Request:**

```json
{
  "message": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "response": "Based on your situation, I recommend focusing on...",
    "suggestions": ["string"],
    "relatedInsights": ["string"]
  }
}
```

**Notes:**

- Response format may vary
- Frontend normalizes response for consistent handling

**Implementation:** `src/services/api.ts` → `ApiClient.sendConversationMessage()`

---

## Conversation Coaching Endpoints (Topic-Based)

These endpoints provide a generic, topic-based coaching conversation engine for multi-turn AI coaching sessions. Topics include core values discovery, purpose exploration, vision setting, and goals coaching.

### GET /ai/coaching/topics

Get available coaching topics with user's status for each.

**Note:** Full URL: `{BASE_URL}/ai/coaching/topics`

**Response:**

```json
{
  "topics": [
    {
      "topic_id": "core_values_coaching",
      "name": "Core Values Discovery",
      "description": "Explore and discover your core values through guided conversation",
      "status": "not_started",
      "session_id": null,
      "completed_at": null
    },
    {
      "topic_id": "purpose_coaching",
      "name": "Purpose Exploration",
      "description": "Discover your life's purpose through meaningful dialogue",
      "status": "in_progress",
      "session_id": "sess_abc123",
      "completed_at": null
    },
    {
      "topic_id": "vision_coaching",
      "name": "Vision Setting",
      "description": "Define your future vision and aspirations",
      "status": "completed",
      "session_id": "sess_xyz789",
      "completed_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**Status Values:**

- `not_started` - User has never started this topic
- `in_progress` - User has an active or paused session
- `completed` - User has completed this topic

---

### POST /ai/coaching/start

Start a new coaching session or resume an existing one.

**Note:** Full URL: `{BASE_URL}/ai/coaching/start`

**Request:**

```json
{
  "topic_id": "core_values_coaching",
  "context": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic_id` | string | Yes | The coaching topic ID |
| `context` | object | No | Additional context for the session |

**Response:**

```json
{
  "session_id": "sess_abc123",
  "tenant_id": "tenant_xyz",
  "topic_id": "core_values_coaching",
  "status": "active",
  "coach_message": "Hello! I'm excited to help you explore and discover your core values today...",
  "message_count": 1,
  "estimated_completion": 0.05
}
```

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier |
| `tenant_id` | string | Tenant ID |
| `topic_id` | string | The coaching topic ID |
| `status` | string | Session status: `active`, `paused`, `completed`, `cancelled` |
| `coach_message` | string | The coach's response message |
| `message_count` | integer | Total messages in the session |
| `estimated_completion` | float | Progress estimate (0-1) |

**Notes:**

- If user has an existing session (active or paused) for this topic, it resumes that session
- If no session exists, starts a new one with an initial coach message

---

### POST /ai/coaching/message

Send a message to an active coaching session.

**Note:** Full URL: `{BASE_URL}/ai/coaching/message`

**Request:**

```json
{
  "session_id": "sess_abc123",
  "message": "I think my most important value is honesty..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | The session ID |
| `message` | string | Yes | User's message |

**Response:**

```json
{
  "session_id": "sess_abc123",
  "coach_message": "That's wonderful that you identify honesty as important. Can you share a specific time when acting with honesty made a significant impact?",
  "message_count": 3,
  "estimated_completion": 0.15,
  "status": "active"
}
```

---

### POST /ai/coaching/pause

Pause an active coaching session.

**Note:** Full URL: `{BASE_URL}/ai/coaching/pause`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

**Response:**

```json
{
  "session_id": "sess_abc123",
  "status": "paused",
  "message": "Session paused successfully. You can resume anytime."
}
```

**Notes:**

- Paused sessions can be resumed later using the `start` endpoint
- Sessions auto-pause after inactivity (configurable per topic)

---

### POST /ai/coaching/complete

Complete a coaching session and extract results.

**Note:** Full URL: `{BASE_URL}/ai/coaching/complete`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

**Response:**

```json
{
  "session_id": "sess_abc123",
  "status": "completed",
  "result": {
    "core_values": ["Honesty", "Growth", "Compassion", "Integrity", "Family"],
    "insights": "Based on our conversation, your core values center around authentic relationships and personal development...",
    "recommendations": ["Consider journaling about how these values show up daily", "Reflect on decisions through the lens of these values"]
  },
  "message_count": 15
}
```

**Notes:**

- The `result` structure varies by topic type
- For core_values, returns discovered values
- For purpose, returns purpose statement
- For vision, returns vision statement
- Results are persisted and can be retrieved via the session details endpoint

---

### POST /ai/coaching/cancel

Cancel an active or paused coaching session.

**Note:** Full URL: `{BASE_URL}/ai/coaching/cancel`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

**Response:**

```json
{
  "session_id": "sess_abc123",
  "status": "cancelled",
  "message": "Session cancelled. You can start a new session anytime."
}
```

**Notes:**

- Cancelled sessions cannot be resumed
- User can start a fresh session for the same topic

---

### GET /ai/coaching/session

Get detailed information about a coaching session.

**Note:** Full URL: `{BASE_URL}/ai/coaching/session?session_id={session_id}`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The session ID |

**Response:**

```json
{
  "session_id": "sess_abc123",
  "tenant_id": "tenant_xyz",
  "topic_id": "core_values_coaching",
  "user_id": "user_123",
  "status": "active",
  "messages": [
    {
      "role": "assistant",
      "content": "Hello! I'm excited to help you explore...",
      "timestamp": "2025-01-15T10:00:00Z"
    },
    {
      "role": "user",
      "content": "I think my most important value is honesty...",
      "timestamp": "2025-01-15T10:02:00Z"
    }
  ],
  "message_count": 2,
  "estimated_completion": 0.10,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:02:00Z",
  "completed_at": null,
  "result": null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `messages` | array | Full conversation history |
| `messages[].role` | string | `user`, `assistant`, or `system` |
| `messages[].content` | string | Message content |
| `messages[].timestamp` | string | ISO 8601 timestamp |
| `result` | object | Extracted results (only for completed sessions) |

---

## Error Responses

All Coaching Service endpoints follow the standard error format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `INSUFFICIENT_CONTEXT` - Not enough data to generate AI response
- `AI_SERVICE_UNAVAILABLE` - ML service temporarily unavailable
- `RATE_LIMIT_EXCEEDED` - Too many AI requests
- `INVALID_GOAL_DATA` - Malformed goal structure
- `ALIGNMENT_CALCULATION_FAILED` - Error during alignment processing

---

**Navigation:**

- [← Back to Index](./backend-integration-index.md)
- [← Account Service](./backend-integration-account-service.md)
- [Traction Service Specs →](./backend-integration-traction-service.md)
- [Common Patterns →](./backend-integration-common-patterns.md)
