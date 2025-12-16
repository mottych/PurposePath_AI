# Coaching Service Endpoints Used by Frontend

**Updated:** December 15, 2025  
**Purpose:** Document all coaching service endpoints actively called by the frontend.

---

## Summary

| Category | Endpoint | Method | Used By |
|----------|----------|--------|---------|
| Unified AI | `/ai/execute` | POST | Website scan, Reviews |
| Unified AI | `/ai/execute-async` | POST | Async onboarding reviews |
| Unified AI | `/ai/jobs/{jobId}` | GET | Job status polling |
| Coaching Sessions | `/ai/coaching/topics` | GET | BusinessOnboarding |
| Coaching Sessions | `/ai/coaching/start` | POST | OnboardingCoachPanel |
| Coaching Sessions | `/ai/coaching/message` | POST | OnboardingCoachPanel |
| Coaching Sessions | `/ai/coaching/pause` | POST | OnboardingCoachPanel |
| Coaching Sessions | `/ai/coaching/complete` | POST | OnboardingCoachPanel |
| Coaching Sessions | `/ai/coaching/cancel` | POST | OnboardingCoachPanel |
| Coaching Sessions | `/ai/coaching/session` | GET | Session retrieval |
| Insights | `/insights/generate` | POST | Dashboard |
| Business Data | `/multitenant/conversations/business-data` | GET | Business metrics |

---

## Detailed Endpoint Usage

### 1. Unified AI Endpoints

#### POST /ai/execute
**Frontend Method:** `executeAI()`, `scanWebsite()`, `executeOnboardingReview()`  
**Files:** `src/services/api.ts`, `src/components/onboarding/WebsiteScanPanel.tsx`

**Topic IDs used:**
- `website_scan` - Website scanning for onboarding
- `niche_review` - Niche review suggestions
- `ica_review` - ICA review suggestions  
- `value_proposition_review` - Value proposition review suggestions

---

#### POST /ai/execute-async
**Frontend Method:** `executeAIAsync()`, `executeOnboardingReviewAsync()`  
**Files:** `src/services/api.ts`, `src/services/ai-job-service.ts`, `src/hooks/useAsyncAI.ts`

**Topic IDs used:**
- `niche_review`
- `ica_review`
- `value_proposition_review`

---

#### GET /ai/jobs/{jobId}
**Frontend Method:** `getAIJobStatus()`  
**Files:** `src/services/api.ts`, `src/services/ai-job-service.ts`

**Purpose:** Poll for async job status and results

---

### 2. Coaching Conversation Session Endpoints

#### GET /ai/coaching/topics
**Frontend Method:** `getCoachingTopics()`  
**Files:** `src/services/api.ts`, `src/components/BusinessOnboarding.tsx`

**Purpose:** Get available coaching topics with user's completion status

---

#### POST /ai/coaching/start
**Frontend Method:** `startCoachingSession()`  
**Files:** `src/services/api.ts`, `src/components/onboarding/OnboardingCoachPanel.tsx`

**Request:**
```json
{
  "topic_id": "core_values" | "purpose" | "vision",
  "context": { "business_name": "string" }
}
```

---

#### POST /ai/coaching/message
**Frontend Method:** `sendCoachingMessage()`  
**Files:** `src/services/api.ts`, `src/components/onboarding/OnboardingCoachPanel.tsx`

**Request:**
```json
{
  "session_id": "string",
  "message": "string"
}
```

---

#### POST /ai/coaching/pause
**Frontend Method:** `pauseCoachingSession()`  
**Files:** `src/services/api.ts`, `src/components/onboarding/OnboardingCoachPanel.tsx`

**Request:**
```json
{
  "session_id": "string"
}
```

---

#### POST /ai/coaching/complete
**Frontend Method:** `completeCoachingSession()`  
**Files:** `src/services/api.ts`, `src/components/onboarding/OnboardingCoachPanel.tsx`

**Request:**
```json
{
  "session_id": "string"
}
```

---

#### POST /ai/coaching/cancel
**Frontend Method:** `cancelCoachingSession()`  
**Files:** `src/services/api.ts`, `src/components/onboarding/OnboardingCoachPanel.tsx`

**Request:**
```json
{
  "session_id": "string"
}
```

---

#### GET /ai/coaching/session
**Frontend Method:** `getCoachingSession()`  
**Files:** `src/services/api.ts`

**Query Parameters:**
- `session_id` - Session ID to retrieve

---

### 3. Insights & Business Data

#### POST /insights/generate
**Frontend Method:** `generateCoachingInsights()`  
**Files:** `src/services/api.ts`, `src/components/Dashboard.tsx`

**Purpose:** Generate coaching insights for dashboard

---

#### GET /multitenant/conversations/business-data
**Frontend Method:** `getBusinessMetrics()`  
**Files:** `src/services/api.ts`

**Purpose:** Fetch business metrics summary

---

## File References

| File | Endpoints Used |
|------|----------------|
| `src/services/api.ts` | All endpoints defined here |
| `src/components/onboarding/OnboardingCoachPanel.tsx` | `/ai/coaching/start`, `/ai/coaching/message`, `/ai/coaching/pause`, `/ai/coaching/complete`, `/ai/coaching/cancel` |
| `src/components/BusinessOnboarding.tsx` | `/ai/coaching/topics` |
| `src/components/onboarding/WebsiteScanPanel.tsx` | `/ai/execute` (website_scan) |
| `src/services/ai-job-service.ts` | `/ai/execute-async`, `/ai/jobs/{jobId}` |
| `src/hooks/useAsyncAI.ts` | Uses `ai-job-service` |
| `src/components/Dashboard.tsx` | `/insights/generate` |
