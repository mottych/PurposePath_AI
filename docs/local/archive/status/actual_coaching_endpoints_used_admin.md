# Actual Coaching Endpoints Used by PurposePath Admin Portal

This document lists **all Coaching service endpoints actually called by the Admin Portal codebase** (as of this scan).

## Coaching API base URL used by the Admin Portal

All “coaching service” calls go through Axios client `aiApiClient` with baseURL `config.aiApiBaseUrl`.

- **Env var**: `VITE_AI_API_BASE_URL`
- **Default (if env var is missing)**: `https://api.dev.purposepath.app/coaching/api/v1`
- **Admin Portal behavior**: if the URL contains `/coaching/` and does not end with `/admin`, the app **auto-appends `/admin`**

So the effective base is typically:

- **`https://api.dev.purposepath.app/coaching/api/v1/admin`**

Source: `purposepath-admin/src/config/env.ts`, `purposepath-admin/src/services/apiClient.ts`

---

## Endpoints currently used (runtime call sites exist in pages/components)

### Topic management (Admin → “AI Management” → Topics)

These are used via React Query hooks in `purposepath-admin/src/hooks/useTopicManagement.ts`, backed by `purposepath-admin/src/services/aiService.ts`.

1. **GET `/topics`**
   - **Purpose**: list topics (filtering + pagination)
   - **Query params used**: `page`, `page_size`, `category`, `topic_type`, `is_active`, `search`
   - **Called from**:
     - `TopicList` → `useTopics(...)`
     - `TopicFilters` (for categories list) → `useTopics(...)`

2. **GET `/topics/:topic_id`**
   - **Purpose**: fetch full topic details (metadata + allowed parameters + template status)
   - **Called from**:
     - `TopicMetadataEditor` → `useTopic(topicId)`
     - `ParameterManager` → `useTopic(topicId)`

3. **GET `/topics/:topic_id?include_schema=true`**
   - **Purpose**: fetch topic details including `response_schema` for the template editor
   - **Called from**:
     - `PromptEditorDialog` → `useTopicWithSchema(topicId)`

4. **PUT `/topics/:topic_id`**
   - **Purpose**: update topic metadata and/or `allowed_parameters`
   - **Called from**:
     - `TopicMetadataEditor` → `useUpdateTopic()`
     - `ParameterManager` → `useUpdateTopic()`

5. **GET `/topics/:topic_id/prompts/:prompt_type`**
   - **Purpose**: load prompt markdown content for editing
   - **Called from**:
     - `PromptEditorDialog` → `usePrompt(topicId, promptType)` (edit mode)

6. **POST `/topics/:topic_id/prompts`**
   - **Purpose**: create/upload a new prompt for a topic
   - **Called from**:
     - `PromptEditorDialog` → `useCreatePrompt()`

7. **PUT `/topics/:topic_id/prompts/:prompt_type`**
   - **Purpose**: update an existing prompt content
   - **Called from**:
     - `PromptEditorDialog` → `useUpdatePrompt()`

8. **DELETE `/topics/:topic_id/prompts/:prompt_type`**
   - **Purpose**: delete a prompt from a topic
   - **Called from**:
     - `PromptEditorDialog` → `useDeletePrompt()`

9. **GET `/models`**
   - **Purpose**: list available LLM model codes for configuration
   - **Called from**:
     - `AIManagementPage` (“AI Models” tab) → `useAIModels()` → `aiService.getModelsLegacy()`
     - `TopicMetadataEditor` model dropdown → `useModels()` → `aiService.getModels()`

---

### LLM registry & ops (Admin → “LLM Dashboard / Interactions / Configurations”)

These are used via `purposepath-admin/src/services/llm/*` and their corresponding hooks/pages.

10. **GET `/topics/stats`**
    - **Purpose**: LLM dashboard metrics summary (note: this is *not* `/topics/:id/stats`)
    - **Query params used**: `DashboardFilters` (passed as query params)
    - **Called from**:
      - `LLMDashboardPage` → `useLLMDashboardMetrics()` → `llmDashboardService.getDashboardMetrics()`

11. **GET `/health`**
    - **Purpose**: LLM dashboard system health
    - **Called from**:
      - `LLMDashboardPage` → `useLLMSystemHealth()` → `llmDashboardService.getSystemHealth()`

12. **GET `/interactions`**
    - **Purpose**: list LLM interactions
    - **Query params used**: `page`, `per_page`, `category`, `search`
    - **Called from**:
      - `InteractionsPage` → `useLLMInteractions(...)` → `llmInteractionService.getInteractions(...)`

13. **GET `/interactions/:code`**
    - **Purpose**: interaction details modal
    - **Called from**:
      - `InteractionDetailsModal` → `useLLMInteraction(code)` → `llmInteractionService.getInteraction(code)`

14. **GET `/configurations`**
    - **Purpose**: list LLM configurations (table in Configurations page)
    - **Query params used**: `page`, `page_size`, `search`, `interaction_code`, `tier`, `is_active`
    - **Called from**:
      - `ConfigurationsPage` → `useLLMConfigurations(params)` → `llmConfigurationService.getConfigurations(params)`

---

## Endpoints present in the admin codebase but NOT currently called by any page/component

These are defined in services/hooks, but there are **no runtime call sites** in the UI (i.e., not referenced by any page/component; only by hooks/services/tests).

### Topic management (defined but unused)

- **DELETE `/topics/:topic_id`** (topic delete API is implemented in `aiService`, but the current UI does not call it)
- **POST `/topics/validate`**
- **POST `/topics/:topic_id/clone`**
- **GET `/topics/:topic_id/stats`** (per-topic stats; different from `/topics/stats`)
- **PATCH `/topics/bulk`**

### LLM interactions (defined but unused)

- **POST `/interactions/:code/check-compatibility`**

### LLM configurations (defined but unused)

- **GET `/configurations/:id`**
- **DELETE `/configurations/:id`** (with `permanent` query param)
- **POST `/configurations`**
- **PUT `/configurations/:id`**
- **POST `/configurations/:id/activate`**
- **POST `/configurations/:id/deactivate`**
- **POST `/configurations/validate`**
- **POST `/configurations/bulk-deactivate`**
- **POST `/configurations/bulk`**
- **GET `/configurations/:id/dependencies`**

### Legacy “prompt template” endpoints (defined but unused in current UI)

The admin code has a legacy prompt-template system in `aiService`/`useAI`, but the current routed UI does not call these:

- **GET `/prompts`**
- **GET `/prompts/:id`**
- **POST `/prompts`**
- **PUT `/prompts/:id`**
- **DELETE `/prompts/:id`**
- **POST `/prompts/:id/test`**
- **PATCH `/prompts/:id/activate`**
- **GET `/prompts/:id/versions`**

---

## How this list was derived (to ensure completeness)

- Enumerated all call sites importing `aiApiClient` (coaching client) and all usages of `API_ENDPOINTS.AI.*` and `API_ENDPOINTS.LLM.*`
- Verified which hooks are referenced by routed pages/components under `purposepath-admin/src/pages/*` and their child components
- Separated “defined but unused” endpoints by confirming there are **no references from pages/components**


