# Coaching Service Backend Integration Specifications

**Version:** 3.2  
**Last Updated:** October 28, 2025  
**Service Base URL:** `{REACT_APP_COACHING_API_URL}`  
**Default (Localhost):** `http://localhost:8000`  
**Dev Environment:** `https://api.dev.purposepath.app/coaching/api/v1`

[← Back to Index](./backend-integration-index.md)

---

## URL Structure

All endpoints in this document are shown as **relative paths** from the base URL.

**Example:**

- **Endpoint:** `/analysis/alignment`
- **Full URL:** `https://api.dev.purposepath.app/coaching/api/v1/analysis/alignment`
- **Frontend Usage:** `coachingClient.post('/analysis/alignment', data)`

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

### POST /analysis/alignment

Calculate alignment score for a goal against business foundation.

**Note:** Full URL: `{BASE_URL}/analysis/alignment`

**Request:**

```json
{
  "text_to_analyze": "string",
  "context": {
    "purpose": "string",
    "vision": "string",
    "coreValues": ["string"],
    "targetMarket": "string?",
    "valueProposition": "string?"
  }
}
```

**Response:**

```json
{
  "analysis_id": "anls_1234567890.123",
  "analysis_type": "alignment",
  "scores": {
    "overall_score": 85.0,
    "purpose_alignment": 88.0,
    "values_alignment": 82.0,
    "goal_clarity": 90.0
  },
  "overall_assessment": "This goal strongly aligns with your business vision...",
  "strengths": [
    "Clear connection to core values",
    "Well-defined success metrics"
  ],
  "misalignments": [
    "Limited focus on long-term vision"
  ],
  "recommendations": [
    "Consider adding a strategy focused on...",
    "Your KPIs could be more specific about..."
  ],
  "created_at": "2025-10-13T14:30:00Z",
  "metadata": {
    "user_id": "string",
    "tenant_id": "string",
    "analysis_version": "1.0"
  }
}
```

**Notes:**

- Scores are 0-100 floating point values
- Returns detailed analysis with strengths, misalignments, and recommendations
- Created via `/analysis/alignment` endpoint

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

### POST /analysis/strategy

Get AI-generated strategy analysis and recommendations.

**Note:** Full URL: `{BASE_URL}/analysis/strategy`

**Request:**

```json
{
  "current_strategy": "string",
  "context": {
    "industry": "string",
    "businessType": "string",
    "targetMarket": "string",
    "goals": ["string"],
    "currentChallenges": ["string"]
  }
}
```

**Response:**

```json
{
  "analysis_id": "anls_1234567890.123",
  "analysis_type": "strategy",
  "effectiveness_score": 75.0,
  "overall_assessment": "Your current strategy shows good alignment with market needs but could benefit from clearer execution plans...",
  "strengths": [
    "Clear focus on customer retention",
    "Leverages existing capabilities"
  ],
  "weaknesses": [
    "Limited differentiation from competitors",
    "Resource allocation unclear"
  ],
  "opportunities": [
    "Expand into adjacent markets",
    "Develop strategic partnerships"
  ],
  "recommendations": [{
    "category": "Execution",
    "recommendation": "Implement Customer Feedback Loop",
    "priority": "high",
    "rationale": "This will help identify pain points and opportunities for retention",
    "estimated_impact": "Potential 20-30% improvement in retention metrics"
  }],
  "created_at": "2025-10-13T14:30:00Z",
  "metadata": {
    "user_id": "string",
    "tenant_id": "string",
    "analysis_version": "1.0"
  }
}
```

**Notes:**

- `effectiveness_score`: 0-100 floating point value
- `priority`: "low" | "medium" | "high"
- Returns comprehensive SWOT-style analysis with actionable recommendations

**Implementation:** `src/services/strategy-suggestion-service.ts` → `getStrategySuggestions()`

---

### POST /analysis/kpi

Get AI-recommended KPIs analysis for goals and strategies.

**Note:** Full URL: `{BASE_URL}/analysis/kpi`

**Request:**

```json
{
  "current_kpis": ["string"],
  "context": {
    "industry": "string",
    "businessType": "string",
    "goals": ["string"],
    "strategies": ["string"]
  }
}
```

**Response:**

```json
{
  "analysis_id": "anls_1234567890.123",
  "analysis_type": "kpi",
  "kpi_effectiveness_score": 80.0,
  "overall_assessment": "Your current KPIs provide good coverage but could be more specific...",
  "current_kpi_analysis": [
    "Customer Retention Rate is well-defined and measurable",
    "Revenue growth metric lacks time-based targets"
  ],
  "missing_kpis": [
    "Customer Lifetime Value (CLV)",
    "Net Promoter Score (NPS)"
  ],
  "recommended_kpis": [{
    "kpi_name": "Customer Retention Rate",
    "description": "Percentage of customers retained over a period",
    "rationale": "Directly measures success of retention strategies",
    "target_range": "85-95%",
    "measurement_frequency": "monthly"
  }],
  "created_at": "2025-10-13T14:30:00Z",
  "metadata": {
    "user_id": "string",
    "tenant_id": "string",
    "analysis_version": "1.0"
  }
}
```

**Notes:**

- `kpi_effectiveness_score`: 0-100 floating point value
- Returns analysis of current KPIs plus recommendations for improvements and additions
- `measurement_frequency`: "daily" | "weekly" | "monthly" | "quarterly"

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
