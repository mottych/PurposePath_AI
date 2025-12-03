# Coaching Service API Endpoints - AI Agent Reference

**Purpose**: Complete reference document for all coaching service endpoints used in the frontend application.  
**Service Base URL**: `REACT_APP_COACHING_API_URL` (default: `http://localhost:8000`)  
**Authentication**: Bearer token via `Authorization` header + `X-Tenant-Id` header  
**Content-Type**: `application/json` for all requests

---

## Table of Contents

1. [Onboarding & Business Intelligence](#onboarding--business-intelligence)
2. [Conversation API (Advanced Coaching)](#conversation-api-advanced-coaching)
3. [Insights Generation](#insights-generation)
4. [Strategic Planning AI](#strategic-planning-ai)
5. [Operations AI](#operations-ai)
6. [Operations-Strategic Integration](#operations-strategic-integration)

---

## Onboarding & Business Intelligence

### 1. Website Scan

**Endpoint**: `POST /website/scan`  
**Method**: POST  
**Timeout**: 35 seconds (30s max + 5s buffer)  
**Purpose**: Extract business information from a website URL

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  url: string; // Website URL (must include protocol, e.g., "https://example.com")
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    businessName?: string;
    industry?: string;
    description?: string;
    products?: string[] | Array<{ id?: string; name: string; problem?: string }>;
    targetMarket?: string; // May be returned as 'ica' in API response
    suggestedNiche?: string; // May be returned as 'niche' in API response
    valueProposition?: string; // May be returned as 'value_proposition' in API response
    // Alternative field names from backend:
    niche?: string;
    ica?: string;
    value_proposition?: string;
  };
  error?: string;
  message?: string;
}
```

**Constraints**:
- May return partial results (not all fields guaranteed)
- Can fail with anti-scraping measures
- Backend may return products as array of objects or strings
- Timeout: 35 seconds

**Usage Location**: `src/services/api.ts::scanWebsite()`

---

### 2. Onboarding Suggestions

**Endpoint**: `POST /suggestions/onboarding`  
**Method**: POST  
**Timeout**: 15 seconds (10s max + 5s buffer)  
**Purpose**: Get AI-generated suggestions for onboarding fields (niche, ICA, value proposition)

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  kind: 'niche' | 'ica' | 'valueProposition';
  current?: string; // Current value (optional, for refinement)
  context?: {
    businessName?: string;
    industry?: string;
    products?: string[];
  };
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    suggestions: string[]; // Array of 3-5 suggestions
    reasoning: string; // AI reasoning for the suggestions
  };
  error?: string;
  message?: string;
}
```

**Constraints**:
- Returns 3-5 suggestions per request
- API may return `data.suggestion` (singular) but component expects `data.suggestions` (array)
- Frontend handles both formats for backward compatibility
- Timeout: 15 seconds

**Usage Location**: `src/services/api.ts::getOnboardingSuggestions()`

---

### 3. Onboarding Coaching

**Endpoint**: `POST /coaching/onboarding`  
**Method**: POST  
**Timeout**: 10 seconds (5s max + 5s buffer)  
**Purpose**: Get interactive coaching assistance for onboarding topics (core values, purpose, vision)

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  topic: 'coreValues' | 'purpose' | 'vision';
  message: string; // User's message/question
  context?: {
    businessName?: string;
    industry?: string;
    currentDraft?: string;
  };
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    response: string; // AI coach's response to the user
    suggestions?: string[]; // Optional suggestions based on the conversation
  };
  error?: string;
  message?: string;
}
```

**Constraints**:
- Timeout: 10 seconds
- Used for interactive coaching during onboarding
- Can return suggestions when conversation is complete

**Usage Location**: 
- `src/services/api.ts::getOnboardingCoaching()`
- `src/components/onboarding/OnboardingCoachPanel.tsx`

---

### 4. Business Metrics (Multitenant Conversations)

**Endpoint**: `GET /multitenant/conversations/business-data`  
**Method**: GET  
**Purpose**: Fetch business data summary from multitenant conversations

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    business_data?: {
      revenue?: number;
      profitMargin?: number;
      customerCount?: number;
      employeeCount?: number;
      marketShare?: number;
      growthRate?: number;
    };
  };
  error?: string;
}
```

**Constraints**:
- Returns default metrics (zeros) if endpoint doesn't exist (404) or CORS issue
- Frontend maps to `BusinessMetrics` type with fallback to zeros

**Usage Location**: `src/services/api.ts::getBusinessMetrics()`

---

## Conversation API (Advanced Coaching)

### 5. Initiate Conversation

**Endpoint**: `POST /conversations/initiate`  
**Method**: POST  
**Purpose**: Start a new coaching conversation

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  topic: 'core_values' | 'purpose' | 'vision' | 'goals';
  context?: Record<string, any>; // Additional context dictionary
  language?: string; // Language code (default: 'en')
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    conversation_id: string;
    user_id: string;
    tenant_id: string;
    topic: string;
    status: 'active' | 'paused' | 'completed';
    current_phase: string;
    initial_message: string;
    progress: number; // 0-1
    created_at: string;
  };
  error?: string;
  message?: string;
}
```

**Constraints**:
- Returns conversation details with initial AI message
- Frontend normalizes `id` field from various possible response formats

**Usage Location**: 
- `src/services/api.ts::initiateConversation()`
- `src/services/api.ts::createConversation()` (deprecated wrapper)

---

### 6. Send Conversation Message

**Endpoint**: `POST /conversations/{conversationId}/message`  
**Method**: POST  
**Purpose**: Send a message in an existing conversation

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  user_message: string; // 10-2000 chars
  metadata?: Record<string, any>; // Optional metadata
}
```

**Alternative Legacy Format** (deprecated):
```typescript
{
  message: string; // Simple string format
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    conversation_id: string;
    ai_response: string;
    follow_up_question?: string | null;
    current_phase: string;
    progress: number; // 0-1
    is_complete: boolean;
    insights: string[];
    identified_values: string[]; // For core_values topic
    next_steps?: string | null;
  };
  error?: string;
  message?: string;
}
```

**Legacy Response Normalization**:
Frontend normalizes legacy responses to:
```typescript
{
  reply: string; // From ai_response or message.content
  completed: boolean; // From is_complete or status === 'completed'
  value: any; // From value, payload.value, or result.value
}
```

**Constraints**:
- User message must be 10-2000 characters
- Frontend handles both typed and legacy message formats

**Usage Location**: 
- `src/services/api.ts::sendConversationMessageTyped()`
- `src/services/api.ts::sendConversationMessage()` (deprecated wrapper)

---

### 7. Get Conversation Details

**Endpoint**: `GET /conversations/{conversationId}`  
**Method**: GET  
**Purpose**: Get complete conversation with history and metadata

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    conversation_id: string;
    user_id: string;
    tenant_id: string;
    topic: string;
    status: 'active' | 'paused' | 'completed';
    current_phase: string;
    progress: number; // 0-1
    messages: Array<{
      role: 'assistant' | 'user';
      content: string;
      timestamp: string;
      metadata?: Record<string, any>;
    }>;
    insights: string[];
    identified_values: string[];
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    metadata?: Record<string, any>;
  };
  error?: string;
  message?: string;
}
```

**Constraints**:
- Returns full conversation history
- Includes all messages, insights, and metadata

**Usage Location**: `src/services/api.ts::getConversationDetails()`

---

## Insights Generation

### 8. Generate Coaching Insights

**Endpoint**: `POST /insights/generate`  
**Method**: POST  
**Purpose**: Generate new coaching insights using LLM (these should be persisted to traction service)

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**: None (empty body)

**Response Structure**:
```typescript
{
  success: boolean;
  data?: CoachingInsight[]; // Array of generated insights
  pagination?: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
  error?: string;
  message?: string;
}
```

**CoachingInsight Type**:
```typescript
interface CoachingInsight {
  id?: string;
  title: string;
  description: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  actionable: boolean;
  createdAt?: Date;
  updatedAt?: Date;
}
```

**Constraints**:
- Generated insights should be persisted to traction service using `saveInsightsBatch()`
- Returns empty array with pagination if generation fails

**Usage Location**: 
- `src/services/api.ts::generateCoachingInsights()`
- `src/components/Dashboard.tsx::generateAndPersistInsights()`

**Note**: Insights are stored in Traction service, not Coaching service. This endpoint only generates them.

---

## Strategic Planning AI

### 9. Strategy Suggestions

**Endpoint**: `POST /coaching/strategy-suggestions`  
**Method**: POST  
**Purpose**: Get AI-generated strategy suggestions for a goal

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  goalId: string;
  goalTitle: string;
  goalDescription: string;
  businessFoundation?: BusinessFoundation;
  existingStrategies?: Strategy[];
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    suggestions: Array<{
      description: string;
      reasoning: string;
      confidence: number; // 0-100
      alignmentScore?: number;
    }>;
  };
  error?: string;
}
```

**Constraints**:
- Base URL already includes `/coaching/api/v1`, so endpoint is `/coaching/strategy-suggestions`
- Full URL: `{BASE_URL}/coaching/strategy-suggestions`

**Usage Location**: `src/services/strategy-suggestion-service.ts::getStrategySuggestions()`

---

### 10. KPI Recommendations

**Endpoint**: `POST /api/coaching/kpi-recommendations`  
**Method**: POST  
**Purpose**: Get AI-generated KPI recommendations for a goal

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  goalId: string;
  goalTitle: string;
  goalDescription: string;
  strategies?: Strategy[];
  businessContext?: any;
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    recommendations: Array<{
      kpiName: string;
      description: string;
      unit: string;
      direction: 'up' | 'down';
      category: string;
      reasoning: string;
      confidence: number; // 0-100
    }>;
  };
  error?: string;
}
```

**Constraints**:
- Full URL: `{BASE_URL}/api/coaching/kpi-recommendations`

**Usage Location**: `src/services/kpi-recommendation-service.ts::getKPIRecommendations()`

---

### 11. Alignment Check

**Endpoint**: `POST /api/coaching/alignment-check`  
**Method**: POST  
**Purpose**: Calculate alignment score between goal and business foundation

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  goal: Goal;
  businessFoundation: BusinessFoundation;
}
```

**Response Structure**:
```typescript
{
  success: boolean;
  data?: {
    score: number; // 0-100 percentage
    explanation: string;
    suggestions: string[];
    breakdown: {
      visionAlignment: number;
      purposeAlignment: number;
      valuesAlignment: number;
    };
  };
  error?: string;
}
```

**Constraints**:
- Full URL: `{BASE_URL}/api/coaching/alignment-check`

**Usage Location**: `src/services/alignment-engine-service.ts::calculateAlignment()`

---

### 12. Alignment Explanation

**Endpoint**: `POST /api/coaching/alignment-explanation`  
**Method**: POST  
**Purpose**: Get detailed AI explanation of goal alignment

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  goal: Goal;
  businessFoundation: BusinessFoundation;
}
```

**Response Structure**:
```typescript
{
  explanation: string; // AI-generated explanation text
}
```

**Constraints**:
- Returns only explanation string (not wrapped in success/error structure)
- Full URL: `{BASE_URL}/api/coaching/alignment-explanation`

**Usage Location**: `src/services/alignment-engine-service.ts::getAlignmentExplanation()`

---

### 13. Alignment Suggestions

**Endpoint**: `POST /api/coaching/alignment-suggestions`  
**Method**: POST  
**Purpose**: Get AI suggestions to improve goal alignment

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  goal: Goal;
  businessFoundation: BusinessFoundation;
}
```

**Response Structure**:
```typescript
{
  suggestions: string[]; // Array of improvement suggestions
}
```

**Constraints**:
- Returns only suggestions array (not wrapped in success/error structure)
- Full URL: `{BASE_URL}/api/coaching/alignment-suggestions`

**Usage Location**: `src/services/alignment-engine-service.ts::getAlignmentSuggestions()`

---

## Operations AI

### 14. Root Cause Suggestions

**Endpoint**: `POST /api/operations/root-cause-suggestions`  
**Method**: POST  
**Purpose**: Get AI suggestions for root cause analysis methods

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  issueTitle: string;
  issueDescription: string;
  businessImpact: IssueImpact;
  context?: {
    reportedBy: string;
    dateReported: Date;
    relatedActions: string[];
  };
}
```

**Response Structure**:
```typescript
Array<{
  method: RootCauseMethod; // 'swot' | 'five_whys' | 'fishbone' | 'pareto'
  confidence: number; // 0-100
  suggestions: {
    swot?: Partial<SWOTAnalysis>;
    fiveWhys?: {
      suggestedQuestions: string[];
      potentialRootCauses: string[];
    };
  };
  reasoning: string;
}>
```

**Usage Location**: `src/services/operations-ai-service.ts::suggestRootCauseAnalysis()`

---

### 15. SWOT Analysis Generation

**Endpoint**: `POST /api/operations/swot-analysis`  
**Method**: POST  
**Purpose**: Generate SWOT analysis for an issue

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  issueTitle: string;
  issueDescription: string;
  businessImpact: IssueImpact;
  context?: string;
}
```

**Response Structure**:
```typescript
SWOTAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}
```

**Usage Location**: `src/services/operations-ai-service.ts::generateSWOTAnalysis()`

---

### 16. Five Whys Questions

**Endpoint**: `POST /api/operations/five-whys-questions`  
**Method**: POST  
**Purpose**: Generate Five Whys questions for root cause analysis

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  issueTitle: string;
  issueDescription: string;
  previousAnswers?: string[]; // For iterative questioning
}
```

**Response Structure**:
```typescript
string[] // Array of suggested questions
```

**Usage Location**: `src/services/operations-ai-service.ts::generateFiveWhysQuestions()`

---

### 17. Action Suggestions from Issue

**Endpoint**: `POST /api/operations/action-suggestions`  
**Method**: POST  
**Purpose**: Get AI-generated action plan suggestions from an issue

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  issueTitle: string;
  issueDescription: string;
  businessImpact: IssueImpact;
  priority: IssuePriority;
  context?: {
    reportedBy: string;
    dateReported: Date;
  };
}
```

**Response Structure**:
```typescript
Array<{
  title: string;
  description: string;
  priority: ActionPriority;
  estimatedDuration: number; // in days
  assignmentSuggestion: string;
  dependencies: string[];
  confidence: number; // 0-100
  reasoning: string;
}>
```

**Usage Location**: `src/services/operations-ai-service.ts::suggestActionsFromIssue()`

---

### 18. Optimize Action Plan

**Endpoint**: `POST /api/operations/optimize-action-plan`  
**Method**: POST  
**Purpose**: Optimize the order and scheduling of actions

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  actions: Array<{
    id: string;
    title: string;
    description: string;
    priority: ActionPriority;
    estimatedDuration: number;
    dependencies: any;
  }>;
  constraints?: {
    maxDuration?: number;
    availableResources?: string[];
    deadlines?: Date[];
  };
}
```

**Response Structure**:
```typescript
{
  optimizedOrder: string[]; // Array of action IDs in optimal order
  reasoning: string;
  estimatedCompletion: Date;
  riskFactors: string[];
}
```

**Usage Location**: `src/services/operations-ai-service.ts::optimizeActionPlan()`

---

### 19. Action Prioritization Suggestions

**Endpoint**: `POST /api/operations/prioritization-suggestions`  
**Method**: POST  
**Purpose**: Get AI suggestions for action prioritization

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  actions: Array<{
    id: string;
    title: string;
    description: string;
    currentPriority: ActionPriority;
    dueDate: Date;
    progress: number;
    connections: any;
  }>;
}
```

**Response Structure**:
```typescript
Array<{
  actionId: string;
  suggestedPriority: ActionPriority;
  currentPriority: ActionPriority;
  reasoning: string;
  confidence: number; // 0-100
  urgencyFactors: string[];
  impactFactors: string[];
}>
```

**Usage Location**: `src/services/operations-ai-service.ts::suggestActionPrioritization()`

---

### 20. Scheduling Suggestions

**Endpoint**: `POST /api/operations/scheduling-suggestions`  
**Method**: POST  
**Purpose**: Get AI suggestions for action scheduling

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  actions: Array<{
    id: string;
    title: string;
    currentStartDate: Date;
    currentDueDate: Date;
    priority: ActionPriority;
    assignedPersonId: string;
    estimatedDuration: number;
    dependencies: any;
  }>;
  constraints?: {
    workingHours?: { start: number; end: number };
    weekends?: boolean;
    holidays?: Date[];
    teamCapacity?: number;
  };
}
```

**Response Structure**:
```typescript
Array<{
  actionId: string;
  suggestedStartDate: Date;
  suggestedDueDate: Date;
  reasoning: string;
  confidence: number; // 0-100
  dependencies: string[];
  resourceConsiderations: string[];
}>
```

**Usage Location**: `src/services/operations-ai-service.ts::suggestScheduling()`

---

### 21. Issue Categorization

**Endpoint**: `POST /api/operations/categorize-issue`  
**Method**: POST  
**Purpose**: Get AI categorization and impact assessment for an issue

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  title: string;
  description: string;
  currentImpact: IssueImpact;
  currentPriority: IssuePriority;
  context?: {
    reportedBy: string;
    dateReported: Date;
  };
}
```

**Response Structure**:
```typescript
{
  suggestedImpact: IssueImpact;
  currentImpact: IssueImpact;
  suggestedPriority: IssuePriority;
  currentPriority: IssuePriority;
  category: string;
  tags: string[];
  reasoning: string;
  confidence: number; // 0-100
}
```

**Usage Location**: `src/services/operations-ai-service.ts::categorizeIssue()`

---

### 22. Assess Issue Impact

**Endpoint**: `POST /api/operations/assess-impact`  
**Method**: POST  
**Purpose**: Get detailed impact assessment for an issue

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  issue: {
    title: string;
    description: string;
    currentImpact: IssueImpact;
  };
  businessContext?: any;
}
```

**Response Structure**:
```typescript
{
  suggestedImpact: IssueImpact;
  reasoning: string;
  confidence: number; // 0-100
  impactFactors: string[];
  mitigationSuggestions: string[];
}
```

**Usage Location**: `src/services/operations-ai-service.ts::assessIssueImpact()`

---

## Operations-Strategic Integration

### 23. Action Strategic Context

**Endpoint**: `GET /api/operations/actions/{actionId}/strategic-context`  
**Method**: GET  
**Purpose**: Get strategic context for an action (connections to goals, KPIs)

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
{
  action: Action;
  strategicConnections: Array<{
    goalId: string;
    goalTitle: string;
    strategyId?: string;
    strategyDescription?: string;
    alignmentScore: number;
    impact: 'low' | 'medium' | 'high' | 'critical';
  }>;
  kpiImpacts: Array<{
    kpiId: string;
    kpiName: string;
    currentValue: number;
    targetValue: number;
    potentialImpact: number;
    confidence: number; // 0-100
    timeToImpact: number; // Days
  }>;
  recommendedKPIUpdates: ActionKPIUpdate[];
  alignmentRecommendations: string[];
}
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::getActionStrategicContext()`

---

### 24. Suggest Strategic Connections

**Endpoint**: `POST /api/operations/actions/suggest-connections`  
**Method**: POST  
**Purpose**: Get AI suggestions for connecting an action to goals/strategies

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  action: Action;
  goals: Goal[];
}
```

**Response Structure**:
```typescript
Array<{
  goalId: string;
  goalTitle: string;
  strategyId?: string;
  strategyDescription?: string;
  alignmentScore: number;
  impact: 'low' | 'medium' | 'high' | 'critical';
}>
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::suggestStrategicConnections()`

---

### 25. Update Action Strategic Connections

**Endpoint**: `PUT /api/operations/actions/{actionId}/connections`  
**Method**: PUT  
**Purpose**: Update strategic connections for an action

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  goalIds: string[];
  strategyIds: string[];
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::updateActionStrategicConnections()`

---

### 26. Analyze KPI Impact

**Endpoint**: `POST /api/operations/actions/analyze-kpi-impact`  
**Method**: POST  
**Purpose**: Analyze how an action will impact KPIs

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  action: Action;
  sharedKPIs: SharedKPI[];
}
```

**Response Structure**:
```typescript
Array<{
  kpiId: string;
  kpiName: string;
  currentValue: number;
  targetValue: number;
  potentialImpact: number;
  confidence: number; // 0-100
  timeToImpact: number; // Days
}>
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::analyzeKPIImpact()`

---

### 27. Record KPI Update

**Endpoint**: `POST /api/operations/kpi-updates`  
**Method**: POST  
**Purpose**: Record a KPI update from an action

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  actionId: string;
  kpiId: string;
  horizonId: string;
  newValue: number;
  notes?: string;
  recordedBy: string;
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::recordKPIUpdate()`

---

### 28. Get KPI Update History

**Endpoint**: `GET /api/operations/kpi-updates?kpiId={kpiId}&horizonId={horizonId}`  
**Method**: GET  
**Purpose**: Get history of KPI updates

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Query Parameters**:
- `kpiId`: string (required)
- `horizonId`: string (required)

**Response Structure**:
```typescript
Array<ActionKPIUpdate> // Returns empty array on error
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::getKPIUpdateHistory()`

---

### 29. Issue Strategic Context

**Endpoint**: `GET /api/operations/issues/{issueId}/strategic-context`  
**Method**: GET  
**Purpose**: Get strategic context for an issue (threatened goals, affected KPIs)

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
{
  issue: Issue;
  threatenedGoals: Array<{
    goalId: string;
    goalTitle: string;
    strategyId?: string;
    strategyDescription?: string;
    alignmentScore: number;
    impact: 'low' | 'medium' | 'high' | 'critical';
  }>;
  affectedKPIs: Array<{
    kpiId: string;
    kpiName: string;
    currentValue: number;
    targetValue: number;
    potentialImpact: number;
    confidence: number; // 0-100
    timeToImpact: number; // Days
  }>;
  strategicRisk: 'low' | 'medium' | 'high' | 'critical';
  recommendedActions: Array<{
    title: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    estimatedImpact: string;
    targetGoalIds: string[];
    targetStrategyIds: string[];
  }>;
}
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::getIssueStrategicContext()`

---

### 30. Generate Actions from Issue

**Endpoint**: `POST /api/operations/issues/{issueId}/generate-actions`  
**Method**: POST  
**Purpose**: Generate action templates from an issue

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  issue: Issue;
  goals: Goal[];
  targetGoalIds?: string[];
}
```

**Response Structure**:
```typescript
Array<Partial<Action>> // Array of action templates
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::generateActionsFromIssue()`

---

### 31. Calculate Operations Alignment

**Endpoint**: `POST /api/operations/strategic-alignment`  
**Method**: POST  
**Purpose**: Calculate overall alignment score between operations and strategic planning

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  goals: Goal[];
  actions: Action[];
  issues: Issue[];
}
```

**Response Structure**:
```typescript
{
  overallScore: number; // 0-100
  goalAlignmentScores: Array<{
    goalId: string;
    score: number;
    actionCount: number;
  }>;
  unalignedActions: Action[];
  strategicRisks: Array<{
    issueId: string;
    riskLevel: string;
    affectedGoals: string[];
  }>;
}
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::calculateOperationsAlignment()`

---

### 32. Complete Action

**Endpoint**: `POST /api/operations/actions/{actionId}/complete`  
**Method**: POST  
**Purpose**: Mark an action as complete

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::completeAction()`

---

### 33. Get KPI Update Prompt

**Endpoint**: `GET /api/operations/actions/{actionId}/kpi-update-prompt`  
**Method**: GET  
**Purpose**: Check if action completion should prompt for KPI update

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
boolean // Whether to show KPI update prompt
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::getKPIUpdatePrompt()`

---

### 34. Update KPI from Action

**Endpoint**: `POST /api/operations/actions/{actionId}/update-kpi`  
**Method**: POST  
**Purpose**: Update a KPI value from action completion

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  kpiId: string;
  newValue: number;
  notes: string;
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::updateKPIFromAction()`

---

### 35. Convert Issue to Actions

**Endpoint**: `POST /api/operations/issues/{issueId}/convert-to-actions`  
**Method**: POST  
**Purpose**: Convert issue to actual action items

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  actionTemplates: Array<{
    title: string;
    description: string;
    priority: string;
  }>;
}
```

**Response Structure**:
```typescript
Array<{
  id: string;
  title: string;
}>
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::convertIssueToActions()`

---

### 36. Check Issue Closure Eligibility

**Endpoint**: `GET /api/operations/issues/{issueId}/closure-eligibility`  
**Method**: GET  
**Purpose**: Check if an issue can be closed (all actions completed, etc.)

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
boolean // Whether issue can be closed
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::checkIssueClosureEligibility()`

---

### 37. Close Issue

**Endpoint**: `POST /api/operations/issues/{issueId}/close`  
**Method**: POST  
**Purpose**: Close an issue with a reason

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  reason: string;
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::closeIssue()`

---

### 38. Get Strategic Context

**Endpoint**: `GET /api/strategic/context`  
**Method**: GET  
**Purpose**: Get strategic planning context (goals, strategies)

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
{
  goals: any[];
  strategies: any[];
}
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::getStrategicContext()`

---

### 39. Create Action with Strategic Context

**Endpoint**: `POST /api/operations/actions/create-with-context`  
**Method**: POST  
**Purpose**: Create an action with pre-connected strategic context

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  title: string;
  goalIds: string[];
  strategyIds: string[];
  description: string;
}
```

**Response Structure**:
```typescript
{
  id: string;
}
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::createActionWithStrategicContext()`

---

### 40. Get Action Strategic Relationships

**Endpoint**: `GET /api/operations/actions/{actionId}/relationships`  
**Method**: GET  
**Purpose**: Get strategic relationships for an action

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
{
  goals: any[];
  strategies: any[];
}
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::getActionStrategicRelationships()`

---

### 41. Sync KPI to Strategic Planning

**Endpoint**: `POST /api/operations/kpi-sync/to-strategic-planning`  
**Method**: POST  
**Purpose**: Sync KPI update to strategic planning system

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  kpiId: string;
  newValue: number;
  source: string;
  notes: string;
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::syncKPIToStrategicPlanning()`

---

### 42. Sync KPI from Strategic Planning

**Endpoint**: `POST /api/operations/kpi-sync/from-strategic-planning`  
**Method**: POST  
**Purpose**: Sync KPI update from strategic planning system

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  kpiId: string;
  newValue: number;
  source: string;
  notes: string;
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::syncKPIFromStrategicPlanning()`

---

### 43. Detect KPI Conflicts

**Endpoint**: `GET /api/operations/kpi-conflicts`  
**Method**: GET  
**Purpose**: Detect conflicts between KPI updates from different sources

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>"
}
```

**Response Structure**:
```typescript
Array<{
  id: string;
  kpiId: string;
}> // Returns empty array on error
```

**Usage Location**: `src/services/operations-strategic-integration-service.ts::detectKPIConflicts()`

---

### 44. Resolve KPI Conflict

**Endpoint**: `POST /api/operations/kpi-conflicts/{conflictId}/resolve`  
**Method**: POST  
**Purpose**: Resolve a detected KPI conflict

**Request Headers**:
```json
{
  "Authorization": "Bearer <access_token>",
  "X-Tenant-Id": "<tenant_id>",
  "Content-Type": "application/json"
}
```

**Request Payload**:
```typescript
{
  resolution: string;
}
```

**Response**: Empty (204 No Content on success)

**Usage Location**: `src/services/operations-strategic-integration-service.ts::resolveKPIConflict()`

---

## Authentication & Headers

All endpoints require:

1. **Authorization Header**: `Bearer <access_token>`
   - Token obtained from Account service login
   - Stored in `localStorage.getItem('accessToken')`
   - Automatically attached by `coachingClient` interceptor

2. **X-Tenant-Id Header**: `<tenant_id>`
   - Tenant ID from user session
   - Stored in `localStorage.getItem('tenantId')`
   - Automatically attached by `coachingClient` interceptor

3. **Content-Type Header**: `application/json`
   - Required for all POST/PUT requests
   - Automatically set by axios client

## Error Handling

All endpoints follow consistent error response format:

```typescript
{
  success: false;
  error: string; // Error message
  message?: string; // Alternative error message field
  code?: string; // Error code (if available)
}
```

Frontend error handling:
- Checks `error.response?.data?.error` first
- Falls back to `error.response?.data?.message`
- Provides default error message if neither available
- Some services return empty arrays/objects on error for graceful degradation

## Timeout Values

- **Website Scan**: 35 seconds
- **Onboarding Suggestions**: 15 seconds
- **Onboarding Coaching**: 10 seconds
- **Default**: 10 seconds (axios default)

## Base URL Configuration

Base URL is configured via environment variable:
- **Development**: `REACT_APP_COACHING_API_URL` (default: `http://localhost:8000`)
- **Production**: Set in build-time environment variables

**Note**: Some services use different URL patterns:
- Services using `api.ts` coachingClient: Base URL includes `/coaching/api/v1`
- Services using direct fetch: Base URL may need `/api/coaching/` prefix
- Check individual service files for exact URL construction

## Service Files Reference

- **Main API Client**: `src/services/api.ts`
- **Strategy Suggestions**: `src/services/strategy-suggestion-service.ts`
- **KPI Recommendations**: `src/services/kpi-recommendation-service.ts`
- **Alignment Engine**: `src/services/alignment-engine-service.ts`
- **Operations AI**: `src/services/operations-ai-service.ts`
- **Operations-Strategic Integration**: `src/services/operations-strategic-integration-service.ts`

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-02  
**Maintained By**: AI Agent

