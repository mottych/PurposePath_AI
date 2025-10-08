# Coaching Service API Endpoints

**Base URL:** `REACT_APP_COACHING_API_URL` (default: `http://localhost:8000/api/v1`)

This document details all endpoints that call the Coaching Service, including LLM-powered AI features.

---

## 1. Alignment & Strategy Guidance

### 1.1 Calculate Alignment
**Endpoint:** `POST /api/coaching/alignment-check`

**Purpose:** AI-powered alignment scoring between goals and business foundation

**Request:**
```json
{
  "goalIntent": "string",
  "strategies": ["string"],
  "kpiNames": ["string"],
  "businessFoundation": {
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string",
    "valueProposition": "string",
    "businessName": "string"
  }
}
```

**Response:**
```json
{
  "alignmentScore": 85,
  "score": 85,
  "explanation": "string",
  "suggestions": ["string"],
  "componentScores": {
    "intentAlignment": 80,
    "strategyAlignment": 85,
    "kpiRelevance": 90
  },
  "breakdown": {
    "visionAlignment": 80,
    "purposeAlignment": 85,
    "valuesAlignment": 90
  },
  "lastUpdated": "2025-01-08T00:00:00Z"
}
```

**Used by:** `alignment-engine-service.ts`

---

### 1.2 Get Alignment Explanation
**Endpoint:** `POST /api/coaching/alignment-explanation`

**Purpose:** LLM-generated explanation of how a goal aligns with business foundation

**Request:**
```json
{
  "goal": { /* Goal object */ },
  "businessFoundation": { /* BusinessFoundation object */ }
}
```

**Response:**
```json
{
  "explanation": "string"
}
```

**Used by:** `alignment-engine-service.ts`

---

### 1.3 Get Alignment Suggestions
**Endpoint:** `POST /api/coaching/alignment-suggestions`

**Purpose:** AI suggestions to improve goal alignment

**Request:**
```json
{
  "goal": { /* Goal object */ },
  "businessFoundation": { /* BusinessFoundation object */ }
}
```

**Response:**
```json
{
  "suggestions": ["string"]
}
```

**Used by:** `alignment-engine-service.ts`

---

### 1.4 Strategy Suggestions
**Endpoint:** `POST /api/coaching/strategy-suggestions`

**Purpose:** LLM-generated strategy recommendations for a goal

**Request:**
```json
{
  "goalIntent": "string",
  "existingStrategies": ["string"],
  "businessContext": {
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string",
    "valueProposition": "string",
    "businessName": "string"
  }
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "description": "string",
      "rationale": "string",
      "feasibilityScore": 85
    }
  ]
}
```

**Used by:** `strategy-suggestion-service.ts`

---

### 1.5 KPI Recommendations
**Endpoint:** `POST /api/coaching/kpi-recommendations`

**Purpose:** AI-powered KPI suggestions relevant to goal

**Request:**
```json
{
  "goalIntent": "string",
  "strategies": ["string"],
  "businessContext": {
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string",
    "valueProposition": "string",
    "businessName": "string"
  },
  "existingKPIs": ["kpi-id-1", "kpi-id-2"]
}
```

**Response:**
```json
{
  "recommendations": [
    {
      "kpiId": "string",
      "relevanceScore": 85,
      "explanation": "string",
      "suggestedTimeHorizons": ["year", "quarter", "month"]
    }
  ]
}
```

**Used by:** `kpi-recommendation-service.ts`

---

## 2. Conversations (LLM Chat Interface)

### 2.1 Create Conversation
**Endpoint:** `POST /conversations/initiate`

**Purpose:** Initialize an LLM conversation session

**Request:**
```json
{
  "topic": "string"
}
```

**Response:**
```json
{
  "id": "conversation-uuid"
}
```

**Used by:** `api.ts` → `alignment.ts`

---

### 2.2 Send Message to Conversation
**Endpoint:** `POST /conversations/{conversationId}/message`

**Purpose:** Send message to LLM and get response

**Request:**
```json
{
  "message": "string"
}
```

**Response:**
```json
{
  "reply": "string",
  "completed": false,
  "value": null
}
```

**Used by:** `api.ts` → `alignment.ts`

---

## 3. Operations AI Features

### 3.1 Root Cause Analysis Suggestions
**Endpoint:** `POST /api/operations/root-cause-suggestions`

**Purpose:** AI suggestions for root cause analysis methods

**Request:**
```json
{
  "issueTitle": "string",
  "issueDescription": "string",
  "businessImpact": "low|medium|high|critical",
  "context": {
    "reportedBy": "string",
    "dateReported": "ISO-8601",
    "relatedActions": ["action-id"]
  }
}
```

**Response:**
```json
[
  {
    "method": "swot|five_whys|fishbone",
    "confidence": 0.85,
    "suggestions": {
      "swot": {
        "strengths": ["string"],
        "weaknesses": ["string"],
        "opportunities": ["string"],
        "threats": ["string"]
      },
      "fiveWhys": {
        "suggestedQuestions": ["string"],
        "potentialRootCauses": ["string"]
      }
    },
    "reasoning": "string"
  }
]
```

**Used by:** `operations-ai-service.ts`

---

### 3.2 Generate SWOT Analysis
**Endpoint:** `POST /api/operations/swot-analysis`

**Purpose:** LLM-generated SWOT analysis for an issue

**Request:**
```json
{
  "issueTitle": "string",
  "issueDescription": "string",
  "businessImpact": "low|medium|high|critical",
  "context": "string"
}
```

**Response:**
```json
{
  "strengths": ["string"],
  "weaknesses": ["string"],
  "opportunities": ["string"],
  "threats": ["string"]
}
```

**Used by:** `operations-ai-service.ts`

---

### 3.3 Generate Five Whys Questions
**Endpoint:** `POST /api/operations/five-whys-questions`

**Purpose:** AI-generated follow-up questions for Five Whys analysis

**Request:**
```json
{
  "issueTitle": "string",
  "issueDescription": "string",
  "previousAnswers": ["string"]
}
```

**Response:**
```json
["string"]
```

**Used by:** `operations-ai-service.ts`

---

### 3.4 Action Plan Suggestions
**Endpoint:** `POST /api/operations/action-suggestions`

**Purpose:** AI-generated action plan suggestions from issue

**Request:**
```json
{
  "issueTitle": "string",
  "issueDescription": "string",
  "businessImpact": "low|medium|high|critical",
  "priority": "low|medium|high|critical",
  "context": {
    "reportedBy": "string",
    "dateReported": "ISO-8601"
  }
}
```

**Response:**
```json
[
  {
    "title": "string",
    "description": "string",
    "priority": "low|medium|high|critical",
    "estimatedDuration": 5,
    "assignmentSuggestion": "string",
    "dependencies": ["string"],
    "confidence": 0.85,
    "reasoning": "string"
  }
]
```

**Used by:** `operations-ai-service.ts`

---

### 3.5 Optimize Action Plan
**Endpoint:** `POST /api/operations/optimize-action-plan`

**Purpose:** AI-optimized action sequencing and scheduling

**Request:**
```json
{
  "actions": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "priority": "low|medium|high|critical",
      "estimatedDuration": 5,
      "dependencies": ["action-id"]
    }
  ],
  "constraints": {
    "maxDuration": 30,
    "availableResources": ["string"],
    "deadlines": ["ISO-8601"]
  }
}
```

**Response:**
```json
{
  "optimizedOrder": ["action-id"],
  "reasoning": "string",
  "estimatedCompletion": "ISO-8601",
  "riskFactors": ["string"]
}
```

**Used by:** `operations-ai-service.ts`

---

### 3.6 Prioritization Suggestions
**Endpoint:** `POST /api/operations/prioritization-suggestions`

**Purpose:** AI recommendations for action prioritization

**Request:**
```json
{
  "actions": [
    {
      "id": "string",
      "title": "string",
      "description": "string",
      "currentPriority": "low|medium|high|critical",
      "dueDate": "ISO-8601",
      "progress": 50,
      "connections": {
        "goalIds": ["string"],
        "strategyIds": ["string"]
      }
    }
  ]
}
```

**Response:**
```json
[
  {
    "actionId": "string",
    "suggestedPriority": "high",
    "currentPriority": "medium",
    "reasoning": "string",
    "confidence": 0.8,
    "urgencyFactors": ["string"],
    "impactFactors": ["string"]
  }
]
```

**Used by:** `operations-ai-service.ts`

---

### 3.7 Scheduling Suggestions
**Endpoint:** `POST /api/operations/scheduling-suggestions`

**Purpose:** AI-optimized scheduling recommendations

**Request:**
```json
{
  "actions": [
    {
      "id": "string",
      "title": "string",
      "currentStartDate": "ISO-8601",
      "currentDueDate": "ISO-8601",
      "priority": "low|medium|high|critical",
      "assignedPersonId": "string",
      "estimatedDuration": 5,
      "dependencies": ["action-id"]
    }
  ],
  "constraints": {
    "workingHours": { "start": 9, "end": 17 },
    "weekends": false,
    "holidays": ["ISO-8601"],
    "teamCapacity": 5
  }
}
```

**Response:**
```json
[
  {
    "actionId": "string",
    "suggestedStartDate": "ISO-8601",
    "suggestedDueDate": "ISO-8601",
    "reasoning": "string",
    "confidence": 0.75,
    "dependencies": ["action-id"],
    "resourceConsiderations": ["string"]
  }
]
```

**Used by:** `operations-ai-service.ts`

---

### 3.8 Categorize Issue
**Endpoint:** `POST /api/operations/categorize-issue`

**Purpose:** AI-powered issue categorization and tagging

**Request:**
```json
{
  "title": "string",
  "description": "string",
  "currentImpact": "low|medium|high|critical",
  "currentPriority": "low|medium|high|critical",
  "context": {
    "reportedBy": "string",
    "dateReported": "ISO-8601"
  }
}
```

**Response:**
```json
{
  "suggestedImpact": "high",
  "currentImpact": "medium",
  "suggestedPriority": "high",
  "currentPriority": "medium",
  "category": "string",
  "tags": ["string"],
  "reasoning": "string",
  "confidence": 0.82
}
```

**Used by:** `operations-ai-service.ts`

---

### 3.9 Assess Issue Impact
**Endpoint:** `POST /api/operations/assess-impact`

**Purpose:** AI assessment of issue business impact

**Request:**
```json
{
  "issue": {
    "title": "string",
    "description": "string",
    "currentImpact": "low|medium|high|critical"
  },
  "businessContext": {}
}
```

**Response:**
```json
{
  "suggestedImpact": "high",
  "reasoning": "string",
  "confidence": 0.85,
  "impactFactors": ["string"],
  "mitigationSuggestions": ["string"]
}
```

**Used by:** `operations-ai-service.ts`

---

## 4. Operations-Strategic Integration

### 4.1 Get Action Strategic Context
**Endpoint:** `GET /api/operations/actions/{actionId}/strategic-context`

**Headers:** `Authorization: Bearer {token}`

**Response:**
```json
{
  "action": {},
  "strategicConnections": [
    {
      "goalId": "string",
      "goalTitle": "string",
      "strategyId": "string",
      "strategyDescription": "string",
      "alignmentScore": 85,
      "impact": "low|medium|high|critical"
    }
  ],
  "kpiImpacts": [
    {
      "kpiId": "string",
      "kpiName": "string",
      "currentValue": 100,
      "targetValue": 150,
      "potentialImpact": 15,
      "confidence": 80,
      "timeToImpact": 14
    }
  ],
  "recommendedKPIUpdates": [],
  "alignmentRecommendations": ["string"]
}
```

**Used by:** `operations-strategic-integration-service.ts`

---

### 4.2 Suggest Strategic Connections
**Endpoint:** `POST /api/operations/actions/suggest-connections`

**Headers:** `Authorization: Bearer {token}`

**Request:**
```json
{
  "action": {},
  "goals": []
}
```

**Response:**
```json
[
  {
    "goalId": "string",
    "goalTitle": "string",
    "strategyId": "string",
    "strategyDescription": "string",
    "alignmentScore": 85,
    "impact": "high"
  }
]
```

**Used by:** `operations-strategic-integration-service.ts`

---

## Summary

### Service Files Using Coaching API:
1. **`alignment-engine-service.ts`** - Alignment scoring, explanations, suggestions
2. **`alignment.ts`** - Conversation-based alignment explainer
3. **`kpi-recommendation-service.ts`** - KPI recommendations
4. **`strategy-suggestion-service.ts`** - Strategy suggestions
5. **`operations-ai-service.ts`** - Operations AI (root cause, SWOT, actions, prioritization)
6. **`operations-strategic-integration-service.ts`** - Strategic integration and context

### LLM-Powered Endpoints:
- Alignment explanations and suggestions
- Strategy suggestions
- KPI recommendations
- Conversation chat interface
- Root cause analysis
- SWOT analysis
- Five Whys questions
- Action planning and optimization
- Prioritization and scheduling
- Issue categorization and impact assessment

### Authentication:
Most endpoints require `Authorization: Bearer {token}` header and `X-Tenant-Id` header for multi-tenancy support.
