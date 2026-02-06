# Unified AI Endpoint Backend Integration Specifications

**Version:** 2.6  
**Last Updated:** February 5, 2026  
**Service Base URL:** `{REACT_APP_COACHING_API_URL}`  
**Default (Localhost):** `http://localhost:8000`  
**Dev Environment:** `https://api.dev.purposepath.app/coaching/api/v1`

[← Back to Index](./backend-integration-index.md)

---

## Revision Log

| Date | Version | Description |
|------|---------|-------------|
| 2026-02-05 | 2.6 | **Session Management Overhaul:** Changed `/start` to ALWAYS create new session (cancels existing). Added `/resume` endpoint with RESUME template for continuing sessions. Added `/session/check` endpoint for detecting existing sessions and conflicts. Idle sessions (>30min) are now resumable (not auto-abandoned). TTL set to 14 days for all sessions. |
| 2026-02-02 | 2.5 | **Insights Enhancement:** Enhanced insights_generation topic with KISS framework (Keep, Improve, Start, Stop), purpose-driven alignment analysis, measure-based state assessment, and leadership-focused framing. Now includes strategies and detailed measures data for comprehensive business analysis |
| 2026-01-29 | 2.4 | **Issue #201 Completion:** Redesigned website_scan response structure to align with BusinessFoundation data model - now extracts industry, founding year, vision/purpose hints, core values, and structures data for direct population of business foundation fields |
| 2026-01-29 | 2.3 | **Issue #200 Completion:** Enriched alignment_check topic with strategies parameter - alignment analysis now considers implementation strategies alongside goal and business foundation |
| 2026-01-25 | 2.2 | **Issue #196 Completion:** Fixed measure_recommendations field name (kpiName → name), verified all field names match Pydantic models, ensured prompt templates align with validation schemas |
| 2026-01-15 | 2.1 | Major restructure: Added revision log, index, reorganized topics by category, moved async and coaching endpoints to Core Endpoints section, verified all topics from registry |
| 2026-01-11 | 2.0 | Terminology update: Replaced all "KPI" references with "Measure", added new topics and parameter enrichment documentation |
| 2025-12-15 | 1.2 | Added async execution endpoints and coaching conversation sessions |
| 2025-11-01 | 1.1 | Added onboarding review topics |
| 2025-10-15 | 1.0 | Initial version with unified AI endpoint |

--- 

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Endpoints](#core-endpoints)
   - [POST /ai/execute](#post-aiexecute)
   - [GET /ai/topics](#get-aitopics)
   - [GET /ai/schemas/{schema_name}](#get-aischemasschema_name)
   - [POST /ai/execute-async](#post-aiexecute-async)
   - [GET /ai/jobs/{jobId}](#get-aijobsjobid)
   - [Coaching Conversation Endpoints](#coaching-conversation-endpoints)
4. [Available Parameters](#available-parameters)
5. [Supported Topics](#supported-topics)
   - [Topic Summary by Category](#topic-summary-by-category)
6. [Single-Shot Topics by Category](#single-shot-topics-by-category)
   - [Onboarding](#onboarding-topics)
   - [Insights](#insights-topics)
   - [Strategic Planning](#strategic-planning-topics)
   - [Operations AI](#operations-ai-topics)
   - [Operations-Strategic Integration](#operations-strategic-integration-topics)
   - [Analysis](#analysis-topics)
7. [Conversation Topics](#conversation-topics)
8. [Response Model Schemas](#response-model-schemas)
9. [Error Handling](#error-handling)
10. [Usage Examples](#usage-examples)
11. [Changelog](#changelog)

---

## Overview

The Unified AI system is **topic-centric**, not endpoint-centric. All AI capabilities are organized as **topics** identified by a `topic_id`. Topics are routed to the appropriate endpoint based on their type:

- **Single-Shot Topics** → `/ai/execute` or `/ai/execute-async`
- **Conversation Topics** → `/ai/coaching/*` endpoints

Instead of separate endpoints for each capability, callers specify a `topic_id` and the appropriate parameters. The system handles routing, validation, and execution automatically.

### Benefits

- **Topic-driven architecture** - All capabilities defined as topics, not hardcoded endpoints
- **Single endpoint** for all single-shot AI operations (`/ai/execute`)
- **Dynamic response models** based on topic
- **Schema discovery** via `/ai/schemas/{schema_name}`
- **Topic listing** via `/ai/topics`
- **Consistent error handling** across all topics
- **Automatic parameter enrichment** from backend data sources
- **Flexible routing** - Endpoints determine routing based on `TopicType`

### Frontend Implementation

- **Primary Client:** `coachingClient` (axios instance in `src/services/api.ts`)
- **Key Pattern:** Call `/ai/execute` with `topic_id` and `parameters`
- **Topic Discovery:** Use `GET /ai/topics` to discover available topics and their parameters

---

## Architecture

### Topic-Centric Design

The AI system is built around **topics**, not endpoints. Each topic represents a specific AI capability (e.g., `niche_review`, `alignment_check`, `core_values`). Topics are identified by a `topic_id` and are routed to the appropriate endpoint based on their `TopicType`:

- **Single-Shot Topics** (`TopicType.SINGLE_SHOT`) → Use `/ai/execute` or `/ai/execute-async`
- **Conversation Topics** (`TopicType.CONVERSATION_COACHING`) → Use `/ai/coaching/*` endpoints

**Key Principle:** Endpoints determine routing based on `TopicType`. Topic definitions do not include endpoint paths or HTTP methods—these are determined by the endpoint handlers.

### Topic Data Sources

Topic information comes from multiple sources, each serving a specific purpose:

| Source | Purpose | Contains |
|--------|---------|----------|
| **Topic Registry** (Static Code) | Topic metadata and validation | `topic_id`, `topic_type`, `category`, `description`, `response_model`, `parameter_refs`, `is_active` |
| **DynamoDB** (via `TopicRepository`) | Runtime topic configuration | `model_code`, `temperature`, `max_tokens`, execution parameters, runtime settings |
| **S3** (via `S3PromptStorage`) | Template content | System prompts, user prompts, template files referenced by topic |
| **Topic Seed Data** | Initialization | Default configurations used to seed/initialize topics in DynamoDB |

**Execution Flow:**
1. Request arrives with `topic_id` → Topic Registry validates topic exists and is active
2. DynamoDB provides runtime configuration (model, temperature, etc.)
3. S3 provides prompt templates
4. Parameter enrichment fetches data from various sources
5. LLM executes with configured model and prompts
6. Response is serialized to the topic's response model

### Parameter Enrichment System

The AI backend automatically enriches prompts with data from multiple sources. When you call `/ai/execute`, the system:

1. **Identifies required parameters** from the topic registry
2. **Groups parameters by source** (one API call per source)
3. **Fetches data** from Business API, Account Service, etc.
4. **Extracts individual values** using defined extraction paths
5. **Renders prompts** with all gathered parameters

This means frontend only needs to provide **request-level parameters** (e.g., `goal_id`, `measure_id`). Context like business foundation, strategies, and measures is automatically fetched.

### Parameter Sources

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

**Note:** All endpoints use topic-based routing. Topics are identified by `topic_id` and routed based on their `TopicType`:
- `TopicType.SINGLE_SHOT` → `/ai/execute` or `/ai/execute-async`
- `TopicType.CONVERSATION_COACHING` → `/ai/coaching/*` endpoints

Topic definitions do not include endpoint paths or HTTP methods—these are determined by the endpoint handlers based on the topic's type.

### POST /ai/execute

Execute any registered single-shot AI topic.

**Routing:** This endpoint handles all topics with `TopicType.SINGLE_SHOT`.

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
| 404 | Topic not found in topic registry |
| 400 | Topic is not active (inactive in registry or DynamoDB) |
| 400 | Topic is conversation type (use `/ai/coaching/*` endpoints) |
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
        "required": false,
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

### POST /ai/execute-async

Execute an AI topic asynchronously. Returns immediately with a job ID; results delivered via WebSocket.

**Routing:** This endpoint handles all topics with `TopicType.SINGLE_SHOT` (same as `/ai/execute`, but for long-running operations).

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

**Response (Failed):**

```json
{
  "success": true,
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "failed",
    "topicId": "niche_review",
    "createdAt": "2026-01-11T20:00:00Z",
    "completedAt": "2026-01-11T20:00:45Z",
    "error": "LLM provider timeout",
    "errorCode": "LLM_TIMEOUT"
  }
}
```

### WebSocket Events

Results are delivered via the existing WebSocket connection at `wss://{WEBSOCKET_URL}`.

#### ai.job.completed

```json
{
  "jobId": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "tenant-123",
  "userId": "user-456",
  "topicId": "niche_review",
  "eventType": "ai.job.completed",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "topicId": "niche_review",
    "result": {
      "topic_id": "niche_review",
      "success": true,
      "data": {
        "qualityReview": "...",
        "suggestions": [...]
      },
      "schema_ref": "OnboardingReviewResponse"
    },
    "processingTimeMs": 35000
  },
  "stage": "dev"
}
```

**Key Fields:**
- `jobId`, `tenantId`, `userId`, `topicId`, `eventType` - Top-level metadata
- `data.result` - The actual AI response (structure varies by topic)
- `data.processingTimeMs` - How long the AI took to process
- `stage` - Environment (dev/staging/prod)

#### ai.job.failed

```json
{
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
  },
  "stage": "dev"
}
```

### When to Use Async vs Sync

| Use Case | Endpoint | Reason |
|----------|----------|--------|
| Quick operations (<10s) | `POST /ai/execute` | Simpler, immediate response |
| Complex analysis (>20s) | `POST /ai/execute-async` | Avoids API Gateway timeout |
| Batch operations | `POST /ai/execute-async` | Process in background |
| User waiting on screen | `POST /ai/execute-async` | Better UX with progress |

**Recommended:** Use async for onboarding review topics (`niche_review`, `ica_review`, `value_proposition_review`) as they may take 30-60 seconds depending on LLM load.

---

### Coaching Conversation Endpoints

The Coaching Conversation endpoints provide multi-turn conversational coaching interactions. Unlike single-shot `/ai/execute` endpoints, coaching sessions maintain state across multiple messages.

**Routing:** These endpoints handle all topics with `TopicType.CONVERSATION_COACHING`.

**Base URL:** All coaching conversation endpoints are prefixed with `/ai/coaching`.

**Full URL Pattern:** `{BASE_URL}/ai/coaching/{endpoint}`

#### Available Coaching Topics

| topic_id | Name | Description |
|----------|------|-------------|
| `core_values` | Core Values Discovery | Discover and articulate your organization's authentic core values |
| `purpose` | Purpose Discovery | Define your organization's deeper purpose and reason for existing |
| `vision` | Vision Crafting | Craft a compelling vision for your organization's future |

**Important:** When calling `/ai/coaching/start`, use the `topic_id` value (e.g., `"core_values"`, `"purpose"`, `"vision"`) - NOT the registry key format.

#### GET /ai/coaching/topics

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
      }
    ]
  },
  "message": "Topics retrieved successfully"
}
```

#### GET /ai/coaching/session/check

**NEW in v2.6** - Check if a resumable session exists for a topic.

**Full URL:** `{BASE_URL}/ai/coaching/session/check?topic_id={topic_id}`

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic_id` | string | Yes | ID of the coaching topic to check |

**Response:**

```json
{
  "success": true,
  "data": {
    "has_session": true,
    "session_id": "sess_abc123",
    "status": "paused",
    "actual_status": "active",
    "is_idle": true,
    "conflict": false,
    "conflict_user_id": null
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `has_session` | boolean | Whether current user has an active/paused session for this topic |
| `session_id` | string \| null | Session ID if exists |
| `status` | string \| null | Computed status: "active" or "paused" (see below) |
| `actual_status` | string \| null | Raw database status |
| `is_idle` | boolean | Whether session has been idle > 30 minutes |
| `conflict` | boolean | Whether another user from same tenant has active session |
| `conflict_user_id` | string \| null | Other user's ID if conflict |

**Status Logic:**
- Returns `"paused"` if session is explicitly PAUSED **OR** ACTIVE but idle > 30 minutes
- Returns `"active"` if session is ACTIVE and NOT idle

**Use Case:** Frontend calls this before starting/resuming to show appropriate UI:
- If `status === "paused"` → Show "Resume or Start New?" dialog
- If `conflict === true` → Show "Another user is using this topic"
- If `has_session === false` → Show "Start Session"

---

#### POST /ai/coaching/start

**CHANGED in v2.6** - Now ALWAYS creates a new session (cancels any existing session).

Start a brand new coaching session. If user has an existing session for this topic,
it will be cancelled/abandoned first. Use `/resume` endpoint to continue existing sessions.

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
    "session_id": "sess_new456",
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

**Note:** Uses INITIATION template for fresh start conversation.

---

#### POST /ai/coaching/resume

**NEW in v2.6** - Resume an existing coaching session with welcome-back message.

Continue an existing session using the RESUME template, which welcomes the user back
and summarizes the conversation so far. Works for both PAUSED and ACTIVE sessions.

**Full URL:** `{BASE_URL}/ai/coaching/resume`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | ID of the session to resume |

**Response:**

```json
{
  "success": true,
  "data": {
    "session_id": "sess_abc123",
    "tenant_id": "tenant-123",
    "topic_id": "core_values",
    "status": "active",
    "message": "Welcome back! Last time we discussed your core values: integrity and innovation. Let's continue...",
    "turn": 3,
    "max_turns": 10,
    "is_final": false,
    "resumed": true,
    "metadata": {
      "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
      "processing_time_ms": 1350,
      "tokens_used": 180
    }
  },
  "message": "Session resumed successfully"
}
```

**Note:** Uses RESUME template with conversation summary. If session was PAUSED, status changes to ACTIVE.

#### POST /ai/coaching/message

Send a message in an active coaching session.

**CHANGED in v2.6:** No longer checks idle timeout. Messages continue active conversations
even if idle > 30 minutes (user may have chat window open with breaks). Only rejects
messages to explicitly PAUSED sessions.

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

**Error Response (Session Paused):**

If session is explicitly PAUSED (not just idle), returns HTTP 400:

```json
{
  "code": "SESSION_NOT_ACTIVE",
  "message": "Session is not active (status: paused)",
  "current_status": "paused"
}
```

Frontend should catch this and prompt user to resume or start new session.

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

#### POST /ai/coaching/pause

Pause an active coaching session.

**Full URL:** `{BASE_URL}/ai/coaching/pause`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

#### POST /ai/coaching/complete

Complete a coaching session and extract results.

**Full URL:** `{BASE_URL}/ai/coaching/complete`

**Request:**

```json
{
  "session_id": "sess_abc123"
}
```

#### POST /ai/coaching/cancel

Cancel a coaching session.

**Full URL:** `{BASE_URL}/ai/coaching/cancel`

#### GET /ai/coaching/session

Get detailed information about a coaching session.

**Full URL:** `{BASE_URL}/ai/coaching/session?session_id={session_id}`

#### GET /ai/coaching/sessions

List all coaching sessions for the current user.

**Full URL:** `{BASE_URL}/ai/coaching/sessions?include_completed={bool}&limit={int}`

---

## Available Parameters

Parameters can be provided in the request body or automatically enriched from various sources. The following parameter sources are available:

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

## Supported Topics

### Topic Summary by Category

#### Onboarding

- [website_scan](#topic-website_scan) - Scan a website and extract business information
- [onboarding_suggestions](#topic-onboarding_suggestions) - Generate onboarding suggestions based on scanned website
- [onboarding_coaching](#topic-onboarding_coaching) - AI coaching for onboarding process
- [business_metrics](#topic-business_metrics) - Retrieve business metrics and data for coaching context
- [niche_review](#topic-niche_review) - Review and suggest variations for business niche
- [ica_review](#topic-ica_review) - Review and suggest detailed ICA personas with demographics, goals, pain points, and buying behavior
- [value_proposition_review](#topic-value_proposition_review) - Review and suggest variations for value proposition
- [core_values](#topic-core_values) - Discover and articulate your organization's authentic core values through guided coaching
- [purpose](#topic-purpose) - Define your organization's deeper purpose and reason for existing through guided coaching
- [vision](#topic-vision) - Craft a compelling vision for your organization's future through guided coaching

#### Insights

- [insights_generation](#topic-insights_generation) - Generate leadership insights using KISS framework with purpose-driven alignment analysis

#### Strategic Planning

- [goal_intent_review](#topic-goal_intent_review) - Review and suggest goal intent statements (WHAT + WHY)
- [strategy_suggestions](#topic-strategy_suggestions) - Generate strategic planning suggestions
- [measure_recommendations](#topic-measure_recommendations) - Recommend measures based on business goals
- [alignment_check](#topic-alignment_check) - Calculate alignment score between goal and business foundation
- [alignment_explanation](#topic-alignment_explanation) - Explain alignment score calculation
- [alignment_suggestions](#topic-alignment_suggestions) - Suggest improvements to increase alignment

#### Operations AI

- [root_cause_suggestions](#topic-root_cause_suggestions) - Suggest root causes for operational issues
- [swot_analysis](#topic-swot_analysis) - Generate SWOT analysis for operations
- [five_whys_questions](#topic-five_whys_questions) - Generate Five Whys analysis questions
- [action_suggestions](#topic-action_suggestions) - Suggest actions to resolve operational issues
- [optimize_action_plan](#topic-optimize_action_plan) - Optimize action plan for better execution
- [prioritization_suggestions](#topic-prioritization_suggestions) - Suggest prioritization of operational tasks
- [scheduling_suggestions](#topic-scheduling_suggestions) - Suggest optimal scheduling for tasks
- [categorize_issue](#topic-categorize_issue) - Categorize operational issue by type and severity
- [assess_impact](#topic-assess_impact) - Assess business impact of operational issue

#### Operations-Strategic Integration

- [action_strategic_context](#topic-action_strategic_context) - Get strategic context for a specific action
- [suggest_connections](#topic-suggest_connections) - Suggest strategic connections for actions
- [update_connections](#topic-update_connections) - Update strategic connections for an action
- [create_issue_from_action](#topic-create_issue_from_action) - Create an issue from an incomplete action
- [create_action_from_issue](#topic-create_action_from_issue) - Create action items from an issue
- [complete_action](#topic-complete_action) - Complete an action and update related items
- [close_issue](#topic-close_issue) - Close an issue and update related items
- [issue_status](#topic-issue_status) - Get comprehensive status of an issue
- [issue_related_actions](#topic-issue_related_actions) - Get actions related to an issue
- [update_measure](#topic-update_measure) - Update a measure value with audit trail
- [calculate_measure](#topic-calculate_measure) - Calculate measure value from linked data
- [measure_history](#topic-measure_history) - Get historical values for a measure
- [measure_impact](#topic-measure_impact) - Analyze measure impact on strategic goals
- [action_measure_impact](#topic-action_measure_impact) - Calculate impact of action completion on measures
- [sync_measures_to_strategy](#topic-sync_measures_to_strategy) - Sync operational measures to strategic planning
- [detect_measure_conflicts](#topic-detect_measure_conflicts) - Detect conflicts between operational and strategic measures
- [resolve_measure_conflict](#topic-resolve_measure_conflict) - Resolve a detected measure conflict
- [operations_strategic_alignment](#topic-operations_strategic_alignment) - Get alignment status between operations and strategy
- [cascade_action_update](#topic-cascade_action_update) - Cascade action updates to related items
- [cascade_issue_update](#topic-cascade_issue_update) - Cascade issue updates to related items
- [cascade_measure_update](#topic-cascade_measure_update) - Cascade measure updates to related strategic items

#### Analysis

- [topic_strategic_context](#topic-topic_strategic_context) - Get strategic context for admin topic management
- [alignment_analysis](#topic-alignment_analysis) - Analyze goal alignment with business foundation
- [measure_analysis](#topic-measure_analysis) - Analyze measure performance trends
- [operations_analysis](#topic-operations_analysis) - Perform operational analysis (SWOT, root cause, etc.)

---

## Single-Shot Topics by Category

### Onboarding Topics

#### Topic: `website_scan`

Scan a website URL and extract business foundation information for onboarding. The response structure aligns with the BusinessFoundation data model to facilitate direct population of business foundation fields.

**Request Payload Structure:**

```json
{
  "topic_id": "website_scan",
  "parameters": {
    "website_url": "https://example.com"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `website_url` | string | Yes | URL of website to scan (must start with http:// or https://) |

**Response Model:** `WebsiteScanResponse` — [Get JSON Schema](/ai/schemas/WebsiteScanResponse)

```json
{
  "topic_id": "website_scan",
  "success": true,
  "data": {
    "scan_id": "scan_f3c9ab",
    "captured_at": "2026-01-29T18:45:00Z",
    "source_url": "https://example.com",
    "business_profile": {
      "business_name": "Example Corp",
      "business_description": "Example Corp provides AI-powered strategic planning tools that help growing businesses achieve clarity and focus.",
      "industry": "Technology",
      "year_founded": 2018,
      "headquarters_location": "San Francisco, CA",
      "website": "https://example.com"
    },
    "core_identity": {
      "vision_hint": "To be the leading platform for strategic business planning",
      "purpose_hint": "We empower businesses to achieve their full potential through clarity and focus",
      "inferred_values": ["Innovation", "Integrity", "Customer Success", "Continuous Improvement"]
    },
    "target_market": {
      "niche_statement": "Mid-market B2B SaaS companies seeking strategic planning and execution tools",
      "segments": ["B2B SaaS (ARR $5M-$50M)", "Growth-stage technology companies", "Professional services firms"],
      "pain_points": ["Fragmented strategic planning tools", "Lack of goal-execution alignment", "Difficulty measuring progress"]
    },
    "products": [
      {
        "name": "PurposePath Pro",
        "description": "AI-powered strategic planning platform with goal setting, measure tracking, and team alignment",
        "problem_solved": "Businesses struggle to translate vision into actionable plans and measure progress effectively",
        "key_features": ["Goal wizard", "Measure tracking", "AI recommendations", "Team collaboration"]
      },
      {
        "name": "Executive Coaching",
        "description": "One-on-one strategic coaching for business leaders",
        "problem_solved": "Leaders need guidance to develop effective strategies and overcome execution challenges",
        "key_features": ["Personalized coaching", "Strategic frameworks", "Accountability system"]
      }
    ],
    "value_proposition": {
      "unique_selling_proposition": "The only strategic planning platform that combines AI insights with proven business frameworks",
      "key_differentiators": ["AI-powered recommendations", "Integrated coaching", "Built specifically for strategic planning"],
      "proof_points": ["500+ businesses served", "78% goal completion rate", "92% report better strategic clarity"]
    }
  },
  "schema_ref": "WebsiteScanResponse",
  "metadata": {
    "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "tokens_used": 2100,
    "processing_time_ms": 9200,
    "finish_reason": "stop"
  }
}
```

**Response Structure Details:**

| Section | Fields | Description |
|---------|--------|-------------|
| `business_profile` | business_name, business_description, industry, year_founded, headquarters_location, website | Core business information aligned with BusinessFoundation.profile |
| `core_identity` | vision_hint, purpose_hint, inferred_values | Vision, purpose, and values inferred from website content, aligned with BusinessFoundation.identity |
| `target_market` | niche_statement, segments, pain_points | Target market information aligned with BusinessFoundation.market |
| `products` | name, description, problem_solved, key_features | Product/service array aligned with BusinessFoundation.products |
| `value_proposition` | unique_selling_proposition, key_differentiators, proof_points | Value proposition aligned with BusinessFoundation.proposition |

**Notes:**

- This topic uses a **retrieval method** (`get_website_content`) to fetch and parse the website
- The `website_url` parameter is passed from the frontend payload
- The retrieval method scrapes the website and provides `website_content`, `website_title`, and `meta_description` to the prompt template
- **Response structure aligns with BusinessFoundation data model** - extracted data can be directly mapped to business foundation fields
- Optional fields (industry, year_founded, vision_hint, purpose_hint, etc.) return null if not found on website
- May return partial results if website has anti-scraping measures
- Use extracted data to pre-populate business foundation onboarding wizard

---

#### Topic: `onboarding_suggestions`

Generate onboarding suggestions based on scanned website.

**Request Payload Structure:**

```json
{
  "topic_id": "onboarding_suggestions",
  "parameters": {
    "kind": "niche",
    "current": "We help small businesses grow",
    "context": {
      "industry": "Software",
      "targetMarket": "SMBs"
    }
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `kind` | string | Yes | Type of suggestion: "niche", "ica", or "valueProposition" |
| `current` | string | No | Current draft text (optional) |
| `context` | object | No | Business context dictionary (key-value pairs) |

**Response Model:** `OnboardingSuggestionsResponse`

**Response Payload Structure:**

```json
{
  "suggestions": ["string"],
  "reasoning": "string"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | array of string | AI-generated suggestions |
| `reasoning` | string | Explanation of why these suggestions fit |

---

#### Topic: `onboarding_coaching`

AI coaching for onboarding process.

**Request Payload Structure:**

```json
{
  "topic_id": "onboarding_coaching",
  "parameters": {
    "topic": "coreValues",
    "message": "I'm struggling to identify our core values",
    "context": {
      "stage": "early",
      "priorAttempts": 2
    }
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic` | string | Yes | Onboarding topic: "coreValues", "purpose", or "vision" |
| `message` | string | Yes | User's question or request for help (min 1 char) |
| `context` | object | No | Business context dictionary (key-value pairs) |

**Response Model:** `OnboardingCoachingResponse`

**Response Payload Structure:**

```json
{
  "response": "string",
  "suggestions": ["string"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `response` | string | AI coach's response |
| `suggestions` | array of string (optional) | Suggested values/statements |

---

#### Topic: `business_metrics`

Retrieve business metrics and data for coaching context.

**Response Model:** `BusinessMetricsResponse`

**Response Payload Structure:**

```json
{
  "tenant_id": "string",
  "business_data": {}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `tenant_id` | string | The tenant identifier |
| `business_data` | object | Dictionary containing various business metrics and data |

---

#### Topic: `niche_review`

Review and suggest variations for business niche.

**Request Payload Structure:**

```json
{
  "topic_id": "niche_review",
  "parameters": {
    "current_value": "We help small business owners with marketing"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_value` | string | Yes | Current niche text to review and improve |

**Response Model:** `OnboardingReviewResponse`

**Response Payload Structure:**

The `data` field contains:

```json
{
  "qualityReview": "string",
  "suggestions": [
    {
      "text": "string",
      "reasoning": "string"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `qualityReview` | string | AI review of the current content quality with feedback. Use newlines (\n) to separate sections like Overall Assessment, Strengths, Weaknesses, and Suggestions for readability |
| `suggestions` | array of SuggestionVariation | Exactly 3 suggested variations |

**SuggestionVariation Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The suggested text variation |
| `reasoning` | string | Explanation of why this variation is recommended. Use newlines (\n) to separate paragraphs for readability |

**Example Response:**

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

Review and suggest detailed ICA (Ideal Client Avatar) personas with demographics, goals, pain points, and buying behavior.

**Request:**

```json
{
  "topic_id": "ica_review",
  "parameters": {
    "current_value": "Business owners who want to grow"  // Optional - can generate suggestions without a draft
  }
}
```

**Response Model:** `IcaReviewResponse`

**Response Payload Structure:**

```typescript
{
  "qualityReview": "string | null",  // Review of current ICA if provided, null otherwise
  "suggestions": [
    {
      "title": "string",  // Descriptive persona name
      "demographics": "string",  // Age, gender, location, income, education, occupation, family
      "goalsAspirations": "string",  // What they want to achieve
      "painPoints": "string",  // Problems and frustrations they face
      "motivations": "string",  // What drives their decisions
      "commonObjectives": "string",  // Milestones they're working toward
      "whereToFind": "string",  // Channels, communities, platforms
      "buyingProcess": "string"  // How they research and make decisions
    }
    // Exactly 3 suggestions
  ]
}
```

**Key Features:**
- **Optional current_value**: Can generate suggestions without existing ICA
- **Comprehensive personas**: Each suggestion includes 8 detailed fields
- **Business alignment**: Suggestions consider niche, value proposition, and products
- **Actionable insights**: Includes where to find prospects and their buying behavior

---

#### Topic: `value_proposition_review`

Review and suggest detailed value proposition variations with comprehensive positioning strategy.

**Request:**

```json
{
  "topic_id": "value_proposition_review",
  "parameters": {
    "current_value": "We provide great marketing services"  // Optional - can generate suggestions without a draft
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_value` | string | No | Current value proposition to review and improve. If not provided, AI will generate suggestions from business context |

**Response Model:** `ValuePropositionReviewResponse`

**Response Payload Structure:**

The `data` field contains:

```json
{
  "qualityReview": "string or null",
  "insufficientInformation": false,
  "suggestions": [
    {
      "uspStatement": "string",
      "keyDifferentiators": ["string"],
      "customerOutcomes": ["string"],
      "proofPoints": ["string"],
      "brandPromise": "string",
      "primaryCompetitor": "string or null",
      "competitiveAdvantage": "string",
      "marketPosition": "Market Leader|Challenger|Niche Player|Emerging"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `qualityReview` | string or null | AI review of the current value proposition quality with feedback. Null if no current_value was provided or if there's insufficient information. Use newlines (\n) to separate sections for readability |
| `insufficientInformation` | boolean | True if there's not enough business context to generate quality suggestions. Default: false |
| `suggestions` | array of ValuePropositionSuggestion | Exactly 3 detailed value proposition suggestions with positioning strategy |

**ValuePropositionSuggestion Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `uspStatement` | string | Unique Selling Proposition statement - the core value promise (10-500 chars) |
| `keyDifferentiators` | array of strings | 2-5 key differentiators that set the business apart from competitors |
| `customerOutcomes` | array of strings | 2-5 specific outcomes or benefits customers can expect |
| `proofPoints` | array of strings | 2-7 short credibility markers (testimonials, metrics, achievements, certifications, years in business, notable clients) |
| `brandPromise` | string | The brand promise - what the business commits to delivering consistently (10-300 chars) |
| `primaryCompetitor` | string or null | Primary competitor or competitive segment (if known/applicable), or null |
| `competitiveAdvantage` | string | Key competitive advantage that drives market differentiation (10-400 chars) |
| `marketPosition` | string | Market position: "Market Leader", "Challenger", "Niche Player", or "Emerging" |

**Example Response:**

```json
{
  "topic_id": "value_proposition_review",
  "success": true,
  "data": {
    "qualityReview": "Your current value proposition is too generic and doesn't communicate specific value...\n\nStrengths:\n- Clear service category\n\nWeaknesses:\n- Lacks differentiation\n- No specific outcomes mentioned\n- Doesn't target a specific audience\n\nSuggestions:\n- Specify your target market\n- Highlight unique methodology or approach\n- Include measurable outcomes",
    "insufficientInformation": false,
    "suggestions": [
      {
        "uspStatement": "We help B2B SaaS companies scale from $1M to $10M ARR through data-driven growth marketing that delivers predictable pipeline",
        "keyDifferentiators": [
          "Specialized focus on B2B SaaS growth stage",
          "Data-driven methodology with daily performance dashboards",
          "Proven playbook for scaling ARR 10x",
          "Full-stack marketing team included"
        ],
        "customerOutcomes": [
          "Predictable monthly pipeline generation",
          "40%+ reduction in customer acquisition cost",
          "3x increase in qualified lead volume within 90 days",
          "Clear ROI tracking on every marketing dollar"
        ],
        "proofPoints": [
          "Helped 15+ SaaS companies achieve 10x ARR growth",
          "Average 180% ROI in first 6 months",
          "Featured in SaaStr and SaaS Weekly",
          "Certified HubSpot and Google Premier Partner",
          "12 years B2B SaaS marketing experience"
        ],
        "brandPromise": "We guarantee measurable pipeline growth within 90 days or work for free until you do",
        "primaryCompetitor": "Full-service digital agencies without SaaS specialization",
        "competitiveAdvantage": "Specialized SaaS growth expertise with proven scaling playbook and performance guarantees",
        "marketPosition": "Niche Player"
      },
      {
        "uspStatement": "Transform your marketing chaos into a revenue engine with our AI-powered marketing platform and expert support",
        "keyDifferentiators": [
          "AI-powered automation and optimization",
          "White-glove onboarding and strategy support",
          "All-in-one platform eliminating tool sprawl",
          "Real-time performance insights"
        ],
        "customerOutcomes": [
          "Save 20+ hours per week on marketing tasks",
          "Increase conversion rates by 35%+",
          "Unified view of entire marketing funnel",
          "Professional marketing without hiring full team"
        ],
        "proofPoints": [
          "500+ businesses trust our platform",
          "4.8/5 star rating with 200+ reviews",
          "Named G2 Leader in Marketing Automation",
          "$50M+ in tracked customer revenue",
          "99.9% platform uptime guarantee"
        ],
        "brandPromise": "We deliver marketing technology that actually works, backed by humans who care about your success",
        "primaryCompetitor": "HubSpot",
        "competitiveAdvantage": "Combines enterprise-grade AI automation with personalized human support at SMB-friendly pricing",
        "marketPosition": "Challenger"
      },
      {
        "uspStatement": "Get world-class marketing strategy and execution without the enterprise price tag - perfect for growing businesses ready to scale",
        "keyDifferentiators": [
          "Fractional CMO + execution team model",
          "Enterprise expertise at mid-market pricing",
          "Flexible month-to-month engagements",
          "Industry-specific strategy frameworks"
        ],
        "customerOutcomes": [
          "Strategic marketing direction from day one",
          "Professional brand positioning and messaging",
          "Consistent content and campaign execution",
          "Marketing that scales with your growth"
        ],
        "proofPoints": [
          "Former Fortune 500 marketing executives",
          "Managed $100M+ in marketing budgets",
          "50+ client success stories across 12 industries",
          "Average 2.5 year client relationship",
          "Published authors and conference speakers"
        ],
        "brandPromise": "We bring Fortune 500 marketing expertise to growing businesses who deserve better than generic agencies",
        "primaryCompetitor": "Traditional marketing agencies",
        "competitiveAdvantage": "Senior-level strategic expertise combined with execution capabilities at accessible pricing for mid-market",
        "marketPosition": "Niche Player"
      }
    ]
  },
  "schema_ref": "ValuePropositionReviewResponse",
  "metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 1250,
    "processing_time_ms": 4500,
    "finish_reason": "stop"
  }
}
```

**Insufficient Information Example:**

```json
{
  "topic_id": "value_proposition_review",
  "success": true,
  "data": {
    "qualityReview": "Not enough information provided to generate quality value proposition suggestions. Please provide:\n- Target market or niche description\n- Products/services offered\n- Ideal customer profile\n- Any unique aspects of your business approach",
    "insufficientInformation": true,
    "suggestions": [
      {
        "uspStatement": "Unable to generate specific USP without business context",
        "keyDifferentiators": ["More information needed", "Business context required"],
        "customerOutcomes": ["Specific outcomes depend on your business model", "Customer benefits require market understanding"],
        "proofPoints": ["Proof points require business history", "Credentials need business context"],
        "brandPromise": "Brand promise requires understanding of your business values and approach",
        "primaryCompetitor": null,
        "competitiveAdvantage": "Competitive advantage analysis requires market and offering details",
        "marketPosition": "Emerging"
      },
      {
        "uspStatement": "Comprehensive value proposition requires detailed business information",
        "keyDifferentiators": ["Business differentiation needs context", "Unique value requires market understanding"],
        "customerOutcomes": ["Customer results depend on service offering", "Outcomes require target market knowledge"],
        "proofPoints": ["Track record information needed", "Credibility markers require business details"],
        "brandPromise": "Promise development needs business mission and values",
        "primaryCompetitor": null,
        "competitiveAdvantage": "Advantage statement requires competitive landscape understanding",
        "marketPosition": "Emerging"
      },
      {
        "uspStatement": "Strategic positioning requires foundational business information",
        "keyDifferentiators": ["Differentiators need business context", "Competitive factors require market data"],
        "customerOutcomes": ["Value delivery depends on business model", "Benefits require offering details"],
        "proofPoints": ["Success indicators need business history", "Evidence requires operational context"],
        "brandPromise": "Promise crafting needs core business values",
        "primaryCompetitor": null,
        "competitiveAdvantage": "Strategic advantage analysis requires comprehensive business understanding",
        "marketPosition": "Emerging"
      }
    ]
  },
  "schema_ref": "ValuePropositionReviewResponse",
  "metadata": {
    "model": "gpt-4o-mini",
    "tokens_used": 450,
    "processing_time_ms": 1800,
    "finish_reason": "stop"
  }
}
```

---

### Insights Topics

#### Topic: `insights_generation`

Generate leadership insights using KISS framework (Keep, Improve, Start, Stop) based on current business state, measures, and purpose alignment.

**Request Payload Structure:**

```json
{
  "topic_id": "insights_generation",
  "parameters": {
    "page": 1,
    "page_size": 20,
    "category": "strategy",  // Optional filter
    "priority": "high",      // Optional filter
    "status": "active"       // Optional filter
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | number | No | Page number for pagination (default: 1) |
| `page_size` | number | No | Items per page (default: 20, max: 100) |
| `category` | string | No | Filter by category: strategy, operations, finance, marketing, leadership, technology |
| `priority` | string | No | Filter by priority: critical, high, medium, low |
| `status` | string | No | Filter by status: active, dismissed, acknowledged, in_progress, completed |

**Auto-enriched Parameters:** `foundation` (vision, purpose, core values, target market), `goals` (with progress), `strategies` (linked to goals), `measures` (with current/target values), `recent_actions`, `open_issues`

**Core Premise:**

Purpose-driven businesses aligned with their values result in:
- Engaged employees who are motivated and productive
- Loyal customers who trust and advocate for the brand
- Improved bottom line through sustainable growth

**KISS Framework:**

Each insight is categorized using KISS:
- **KEEP**: What's working well and aligned with purpose/values (continue doing)
- **IMPROVE**: What's partially working but needs optimization
- **START**: What's missing that should be initiated
- **STOP**: What's misaligned or counterproductive (cease doing)

**Response Model:** `InsightsGenerationResponse`

**Response Payload Structure:**

The LLM generates a list of insights (typically 5-10) in a single response. This is ephemeral data - the .NET backend handles persistence and adds system fields (id, status, timestamps).

```typescript
{
  "insights": [
    {
      "title": "string",
      "description": "string",
      "category": "strategy" | "operations" | "finance" | "marketing" | "leadership" | "technology",
      "priority": "critical" | "high" | "medium" | "low",
      "kiss_category": "keep" | "improve" | "start" | "stop",
      "alignment_impact": "string",
      "business_impact": "low" | "medium" | "high",
      "effort_required": "low" | "medium" | "high"
    }
    // ... 4-9 more insights
  ]
}
```

**Note:** System fields like `id`, `status`, `created_at`, `updated_at` are added by the .NET backend when persisting, not generated by the LLM.

**Frontend Integration:**
1. Call `/ai/execute-async` with `topic_id: "insights_generation"`
2. Poll job status until complete
3. Receive insights array from Python AI service (ephemeral, no persistence)
4. **Persist to .NET Traction Service:** POST `/traction/api/v1/insights/batch` with insights array
5. .NET backend adds: `id`, `tenantId`, `status` (default "active"), `createdAt`, `updatedAt`
6. Subsequent page loads fetch from .NET backend via GET `/traction/api/v1/insights` (not Python AI)
7. **Widget displays insights:** GET `/traction/api/v1/dashboard/widgets/ai-insights/data` with camelCase properties

**Related Specifications:**
- **Persistence & CRUD:** See [Coaching Insights API](../../user-app/traction-service/insights-api.md) for POST /batch, GET, PUT, DELETE endpoints
- **Widget Display:** See [Dashboard Service - AI Insights Widget](../../user-app/dashboard-service.md#ai-insights-widget) for widget data endpoint

---

### Strategic Planning Topics

#### Topic: `strategy_suggestions`

Generate strategic planning suggestions.

**Request:**

```json
{
  "topic_id": "strategy_suggestions",
  "parameters": {
    "goal_id": "abc-123"
  }
}
```

**Response Model:** `StrategySuggestionsResponse`

**Response Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | StrategySuggestion[] | Array of strategy suggestions |
| `description` | string | What's happening, why it matters, with specific data references (20-2000 chars) |
| `category` | string | Business domain: "strategy", "operations", "finance", "marketing", "leadership", "technology" |
| `priority` | string | Urgency level: "critical", "high", "medium", "low" |
| `kiss_category` | string | KISS framework: "keep", "improve", "start", "stop" |
| `alignment_impact` | string | How this affects purpose/values alignment and business outcomes (max 500 chars) |
| `status` | string | Current status: "active", "dismissed", "acknowledged", "in_progress", "completed" |
| `created_at` | ISO8601 datetime | When insight was generated |
| `updated_at` | ISO8601 datetime | Last update timestamp |
| `metadata` | InsightMetadata | Additional insight metadata |

**InsightMetadata Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `conversation_count` | number | Number of conversations contributing to this insight |
| `business_impact` | string | Business impact level: "low", "medium", "high" |
| `effort_required` | string | Implementation effort: "low", "medium", "high" |

**PaginationMeta Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `page` | number | Current page number |
| `limit` | number | Items per page |
| `total` | number | Total number of insights (all pages) |
| `total_pages` | number | Total number of pages |

**Analysis Focus:**

Insights prioritize:
- Alignment gaps between vision/purpose/values and current execution
- Goals with low progress or behind schedule
- Strategies missing for critical goals
- Measures showing concerning trends (current far from target)
- Actions not aligned with priority goals
- Issues blocking strategic progress
- Patterns suggesting systemic misalignment

**Example Response:**

```json
{
  "topic_id": "insights_generation",
  "success": true,
  "data": {
    "success": true,
    "data": [
      {
        "id": "insight-abc123",
        "title": "Customer retention goal 30% behind target - missing engagement strategy",
        "description": "Based on measure 'Customer Retention Rate' (current: 70%, target: 90%), your customer retention goal is significantly behind schedule. Analysis shows no strategies defined for customer engagement or retention, despite this being aligned with your core value 'Customer First'. This gap is impacting both customer loyalty and bottom line growth.",
        "category": "strategy",
        "priority": "high",
        "kiss_category": "start",
        "alignment_impact": "Starting a customer engagement strategy aligns with your core value 'Customer First' and directly supports your purpose of 'empowering businesses to grow sustainably'. Improved retention drives loyal customers and recurring revenue.",
        "status": "active",
        "created_at": "2026-02-02T10:00:00Z",
        "updated_at": "2026-02-02T10:00:00Z",
        "metadata": {
          "conversation_count": 0,
          "business_impact": "high",
          "effort_required": "medium"
        }
      },
      {
        "id": "insight-def456",
        "title": "Operational efficiency improving - maintain focus on process optimization",
        "description": "Based on measure 'Task Completion Rate' (current: 88%, target: 90%), your operations team is performing well and making steady progress. The current approach to process documentation and automation aligns with your value of 'Excellence'. Continue investing in these areas to sustain momentum.",
        "category": "operations",
        "priority": "medium",
        "kiss_category": "keep",
        "alignment_impact": "Maintaining this operational excellence supports your purpose and demonstrates commitment to doing things right. This builds team confidence and customer trust.",
        "status": "active",
        "created_at": "2026-02-02T10:00:00Z",
        "updated_at": "2026-02-02T10:00:00Z",
        "metadata": {
          "conversation_count": 0,
          "business_impact": "medium",
          "effort_required": "low"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 8,
      "total_pages": 1
    }
  },
  "schema_ref": "PaginatedInsightResponse",
  "metadata": {
    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "tokens_used": 3245,
    "processing_time_ms": 4567,
    "finish_reason": "stop"
  }
}
```

**Frontend Implementation Notes:**

```typescript
// Example TypeScript usage
const response = await coachingClient.post('/ai/execute', {
  topic_id: 'insights_generation',
  parameters: {
    page: 1,
    page_size: 20,
    category: 'strategy',  // Optional filter
    priority: 'high'       // Optional filter
  }
});

// Access the insights array
const insights = response.data.data.data;  // response.data.data.data[] for nested structure
const pagination = response.data.data.pagination;

// Or access directly if using the legacy /insights/generate endpoint
const directResponse = await coachingClient.post('/insights/generate', {
  page: 1,
  page_size: 20,
  category: 'strategy'
});
const directInsights = directResponse.data.data;  // Direct access
const directPagination = directResponse.data.pagination;

// Process insights
insights.forEach(insight => {
  console.log(`[${insight.kiss_category.toUpperCase()}] ${insight.title}`);
  console.log(`Priority: ${insight.priority}, Impact: ${insight.metadata.business_impact}`);
  console.log(`Alignment: ${insight.alignment_impact}`);
});
```

**Notes:**

- The AI analyzes current business state using measure data (current vs target values) to assess performance
- Suggests KISS actions (Keep, Improve, Start, Stop) that maintain purpose-driven alignment
- Each insight includes specific data references (goals, measures, strategies) in the description
- `alignment_impact` explains how the insight affects values alignment, employee engagement, and bottom line
- **IMPORTANT:** This endpoint generates NEW insights using LLM (costs money!) - cache results on frontend/backend

---

### Strategic Planning Topics

#### Topic: `goal_intent_review`

Review and suggest goal intent statements that define WHAT to achieve and WHY, ensuring clarity and business alignment.

**Purpose:**
Help users craft effective goal intents that focus on desired outcomes (WHAT) and business rationale (WHY), not actions or strategies (HOW). Validates that intents are not too action-focused and align with business foundation.

**Request Payload Structure:**

```json
{
  "topic_id": "goal_intent_review",
  "parameters": {
    "current_intent": "Implement a customer success program",
    "goalId": "goal-123"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current_intent` | string | No | Draft goal intent to review (optional) |
| `goalId` | string | No | ID of the goal (optional, for context) |

**Auto-enriched Parameters:**
- `vision` - Business vision statement
- `purpose` - Business purpose statement
- `core_values` - List of core values
- `target_market` - Target market description
- `value_proposition` - Value proposition
- `goal_title` - Goal title (if goalId provided)
- `goal_description` - Goal description (if goalId provided)
- `current_strategies` - Existing strategies (if goalId provided)
- `current_measures` - Existing measures (if goalId provided)
- `other_goals` - All other goals for context

**Key Concepts:**
- **INTENT**: Defines WHAT we want to achieve and WHY (business outcome). Example: "Increase customer retention to build long-term relationships and sustainable revenue growth"
- **STRATEGY**: Defines HOW we will achieve the intent. Example: "Implement customer success program"
- **MEASURE**: Defines WHEN and HOW MUCH. Example: "Customer Retention Rate reaches 90% by Q4"

**Functionality:**
1. **Quality Review** (if current intent provided):
   - Validates the intent is not a strategy or action
   - Scores quality from 0-100
   - Identifies if it lacks WHY component or is too action-focused
2. **Intent Suggestions**: Generates exactly 3 intent variations that:
   - Focus on desired outcomes (WHAT + WHY)
   - Align with business vision, purpose, and core values
   - Are specific enough to guide strategy but not prescriptive
   - Are realistic yet ambitious

**Response Model:** `GoalIntentReviewResponse`

**Response Payload Structure:**

```json
{
  "qualityReview": "string or null",
  "qualityScore": 75,
  "suggestions": [
    {
      "title": "Customer Retention Focus",
      "intentStatement": "Increase customer retention to build long-term relationships and create predictable recurring revenue",
      "explanation": "This intent clearly defines the desired outcome (increased retention) and the business rationale (long-term relationships and revenue stability)",
      "strengthens": ["clarity", "alignment", "outcome-focus", "measurability"],
      "alignmentHighlights": {
        "vision": "Aligns with vision of becoming the trusted partner for growing businesses",
        "purpose": "Supports purpose of empowering sustainable business growth",
        "values": [
          "Customer First: Prioritizes long-term customer relationships",
          "Sustainability: Focuses on predictable, recurring revenue"
        ]
      }
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `qualityReview` | string \| null | Assessment of current intent (if provided), otherwise null |
| `qualityScore` | number \| null | Quality score 0-100 (if current intent provided), otherwise null |
| `suggestions` | array of IntentSuggestion | List of 3 intent statement variations |

**IntentSuggestion Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Descriptive label for this intent variation (5-100 chars) |
| `intentStatement` | string | The suggested goal intent statement (20-300 chars) |
| `explanation` | string | Why this intent is effective and aligned (50-500 chars) |
| `strengthens` | array of string | List of 2-4 aspects this intent strengthens (clarity, alignment, motivation, etc.) |
| `alignmentHighlights` | object | How this intent connects to business foundation |

**AlignmentHighlights Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `vision` | string | How intent connects to business vision |
| `purpose` | string | How intent serves business purpose |
| `values` | array of string | How intent aligns with specific core values |

**Quality Score Interpretation:**
- **90-100**: Excellent intent - clear, aligned, outcome-focused
- **70-89**: Good intent - minor improvements needed
- **50-69**: Moderate intent - significant refinement required
- **30-49**: Weak intent - may be too action-focused or misaligned
- **0-29**: Poor intent - needs complete rework, likely a strategy or action

**Usage Notes:**
- Intent should describe desired END STATE, not actions to take
- Avoid prescriptive language like "implement", "create", "launch" - these are strategies
- Focus on business outcomes and value creation
- The WHY component explains business rationale and expected impact

---

#### Topic: `strategy_suggestions`

Generate strategy suggestions for a specific goal, including review of existing strategies for alignment and efficiency.

**Request Payload Structure:**

```json
{
  "topic_id": "strategy_suggestions",
  "parameters": {
    "goalId": "goal-123",
    "goalIntent": "Increase customer retention by 20%",
    "businessContext": {
      "targetMarket": "Small to medium businesses",
      "valueProposition": "Comprehensive solutions with personal service",
      "businessName": "Sample Business",
      "industry": "Software",
      "businessType": "B2B SaaS",
      "currentChallenges": ["High churn", "Competition"]
    },
    "constraints": {
      "budget": 50000,
      "timeline": "6 months",
      "resources": ["2 developers", "1 designer"]
    }
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goalId` | string | Yes | The unique identifier of the goal requiring strategies |
| `goalIntent` | string | No | Optional goal intent/description (5-500 chars). If not provided, will be extracted from goal data |
| `businessContext` | BusinessContext | No | Optional additional business context. Business foundation (vision, purpose, core values) is auto-enriched |
| `constraints` | Constraints | No | Resource constraints for strategy implementation |

**BusinessContext Structure (optional):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `targetMarket` | string | No | Target market description |
| `valueProposition` | string | No | Value proposition statement |
| `businessName` | string | No | Business name |
| `industry` | string | No | Industry sector |
| `businessType` | string | No | Type of business (e.g., "B2B SaaS", "E-commerce") |
| `currentChallenges` | array of string | No | List of current business challenges |

**Constraints Structure (optional):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `budget` | number | No | Budget constraint in dollars |
| `timeline` | string | No | Timeline constraint (e.g., "6 months", "Q2 2025") |
| `resources` | array of string | No | Available resources (e.g., ["2 developers", "1 designer"]) |

**Auto-enriched Parameters:**
- `goal` - Complete goal data (from `goal_id`)
- `goal_title` - Goal title
- `goal_description` - Goal description
- `business_foundation` - Vision, purpose, core values
- `strategies` - All strategies (filtered by `goal_id` in template to get strategies for this goal)

**Functionality:**
1. **Strategy Review**: If the goal has existing strategies, the AI will review each one for:
   - Alignment with the goal and business foundation
   - Efficiency and effectiveness
   - Areas for improvement or optimization
2. **New Strategy Suggestions**: Generates 3-5 new strategy suggestions that:
   - Directly support the specific goal
   - Align with business foundation (vision, purpose, core values)
   - Consider existing strategies to avoid duplication
   - Provide diverse strategic options

**Response Model:** `StrategySuggestionsResponse`

**Response Payload Structure:**

```json
{
  "suggestions": [
    {
      "title": "string",
      "description": "string",
      "rationale": "string",
      "difficulty": "low" | "medium" | "high",
      "timeframe": "string",
      "expectedImpact": "low" | "medium" | "high",
      "prerequisites": ["string"],
      "estimatedCost": number | null,
      "requiredResources": ["string"]
    }
  ],
  "confidence": number,
  "reasoning": "string"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | array of StrategySuggestion | List of strategy suggestions |
| `confidence` | number (0-1) | Confidence score for suggestions |
| `reasoning` | string | Overall reasoning for suggestions |

**StrategySuggestion Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Strategy title |
| `description` | string | Detailed strategy description |
| `rationale` | string | Why this strategy makes sense |
| `difficulty` | string | Implementation difficulty: "low", "medium", or "high" |
| `timeframe` | string | Expected timeframe (e.g., "2-3 months") |
| `expectedImpact` | string | Expected impact level: "low", "medium", or "high" |
| `prerequisites` | array of string | Prerequisites for implementation |
| `estimatedCost` | number \| null | Estimated cost in dollars (optional) |
| `requiredResources` | array of string | Required resources |

---

#### Topic: `measure_recommendations`

Recommend catalog measures for a goal or strategy, with suggested owner assignment based on positions/roles.

**Request Payload Structure:**

```json
{
  "topic_id": "measure_recommendations",
  "parameters": {
    "goal_id": "goal-123",
    "strategy_id": "strategy-456"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of the goal to recommend measures for |
| `strategy_id` | string | No | Optional: ID of specific strategy to recommend measures for. If provided, measures will be associated with the strategy rather than the goal directly |

**Auto-enriched Parameters:**
- `goal` - Goal data from goal_id
- `strategies` - All strategies (filtered by goal_id in template)
- `business_context` - Business foundation (vision, purpose, core values)
- `existing_measures` - Existing measures for the tenant
- `measure_catalog` - Complete measure catalog data
- `catalog_measures` - List of available catalog measures from measure library
- `tenant_custom_measures` - List of tenant custom measures
- `roles` - List of all roles in the organization
- `positions` - List of all positions in the organization
- `people` - List of all people in the organization

**Response Model:** `MeasureRecommendationsResponse` (aliases to `KPIRecommendationsResponseV2`)

**Response Payload Structure:**

The `data` field contains:

```json
{
  "recommendations": [
    {
      "name": "string",
      "description": "string",
      "unit": "string",
      "direction": "up" | "down",
      "type": "quantitative" | "qualitative" | "binary",
      "reasoning": "string",
      "suggestedTarget": {
        "value": "string",
        "timeframe": "string",
        "rationale": "string"
      } | null,
      "measurementApproach": "string",
      "measurementFrequency": "daily" | "weekly" | "monthly" | "quarterly",
      "isPrimaryCandidate": boolean,
      "catalogMeasureId": "string | null",
      "suggestedOwnerId": "string | null",
      "suggestedOwnerName": "string | null",
      "suggestedPositionId": "string | null",
      "associationType": "goal" | "strategy" | null,
      "associatedEntityId": "string | null"
    }
  ],
  "analysisNotes": "string"
}
```

**Key Features:**
- **Catalog Measures**: AI recommends measures from the measure catalog when available, falling back to custom measures only if no suitable catalog measure exists
- **Owner Assignment**: AI suggests appropriate person/position to assign as measure owner based on role accountability, position responsibilities, and measure category
- **Strategy Support**: Measures can be associated with either a goal (default) or a specific strategy (if strategy_id provided)

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `recommendations` | array of MeasureRecommendation | List of measure recommendations (1-5 items) |
| `analysisNotes` | string | Overall analysis and reasoning (50-300 chars) |

**MeasureRecommendation Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (5-50 chars) | Measure name |
| `description` | string (20-300 chars) | What it measures and why it matters |
| `unit` | string (1-20 chars) | Unit of measurement (e.g., '%', 'USD', 'count') |
| `direction` | string | Desired direction: "up" or "down" |
| `type` | string | Measure type: "quantitative", "qualitative", or "binary" |
| `reasoning` | string (50-300 chars) | Why this measure is recommended |
| `suggestedTarget` | SuggestedTarget \| null | Optional suggested target |
| `measurementApproach` | string (20-200 chars) | How to measure this measure |
| `measurementFrequency` | string | Measurement frequency: "daily", "weekly", "monthly", or "quarterly" |
| `isPrimaryCandidate` | boolean | Whether this should be the primary measure |
| `catalogMeasureId` | string \| null | ID of recommended catalog measure (if from catalog) |
| `suggestedOwnerId` | string \| null | Suggested person ID to assign as measure owner |
| `suggestedOwnerName` | string \| null | Suggested person name to assign as measure owner |
| `suggestedPositionId` | string \| null | Suggested position ID (optional, if position-based assignment) |
| `associationType` | string \| null | Whether measure is for "goal" or "strategy" |
| `associatedEntityId` | string \| null | Goal ID or Strategy ID this measure is associated with |

**SuggestedTarget Structure (optional):**

| Field | Type | Description |
|-------|------|-------------|
| `value` | number | Target value |
| `timeframe` | string | Timeframe for achieving target (e.g., 'Q4 2025') |
| `rationale` | string | Rationale for this target |

**Example Response:**

```json
{
  "topic_id": "measure_recommendations",
  "success": true,
  "data": {
    "recommendations": [
      {
        "name": "Monthly Recurring Revenue",
        "description": "Total predictable revenue from subscriptions, critical for tracking revenue growth",
        "unit": "USD",
        "direction": "up",
        "type": "quantitative",
        "reasoning": "Directly measures revenue growth goal and aligns with business model",
        "suggestedTarget": {
          "value": "150000",
          "timeframe": "Q1 2025",
          "rationale": "Based on current growth trajectory and market conditions"
        },
        "measurementApproach": "Sum of all active subscription values at month end",
        "measurementFrequency": "monthly",
        "isPrimaryCandidate": true,
        "catalogMeasureId": "catalog-001",
        "suggestedOwnerId": "person-456",
        "suggestedOwnerName": "Jane Doe",
        "suggestedPositionId": "position-789",
        "associationType": "goal",
        "associatedEntityId": "goal-123"
      }
    ],
    "analysisNotes": "Recommended catalog measures that align with your goal and business foundation. Suggested owners are based on role accountability and measure category."
  },
  "schema_ref": "MeasureRecommendationsResponse"
}
```

---

#### Topic: `alignment_check`

Calculate alignment score between a goal and business foundation, considering both the goal itself and the strategies chosen to implement it.

**Request Payload Structure:**

```json
{
  "topic_id": "alignment_check",
  "parameters": {
    "goal_id": "goal-123"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of goal to check alignment for |

**Auto-enriched Parameters:** `goal`, `business_foundation` (vision, purpose, core_values), `strategies` (implementation strategies for the goal)

**Response Model:** `AlignmentCheckResponse`

**Response Payload Structure:**

The `data` field contains:

```json
{
  "alignmentScore": number,
  "explanation": "string",
  "suggestions": ["string"],
  "breakdown": {
    "visionAlignment": number,
    "purposeAlignment": number,
    "valuesAlignment": number
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `alignmentScore` | number (0-100) | Overall alignment score |
| `explanation` | string (50-500 chars) | Human-readable explanation of the alignment |
| `suggestions` | array of string (0-3 items) | Actionable improvement suggestions |
| `breakdown` | AlignmentBreakdown | Breakdown of alignment scores by component |

**AlignmentBreakdown Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `visionAlignment` | number (0-100) | Alignment with company vision |
| `purposeAlignment` | number (0-100) | Alignment with company purpose |
| `valuesAlignment` | number (0-100) | Alignment with core values |

**Example Response:**

```json
{
  "topic_id": "alignment_check",
  "success": true,
  "data": {
    "alignmentScore": 85,
    "explanation": "Your goal shows strong alignment with your stated purpose and values. The goal directly supports your vision of 'Lead with clarity. Grow with purpose.' However, it could be strengthened by adding specific metrics tied to your core value of Integrity.",
    "suggestions": [
      "Add specific metrics to measure success against your core values",
      "Define how this goal will demonstrate 'Do it Right' in execution",
      "Include milestones that reflect your commitment to Joy and Freedom"
    ],
    "breakdown": {
      "visionAlignment": 90,
      "purposeAlignment": 88,
      "valuesAlignment": 78
    }
  },
  "schema_ref": "AlignmentCheckResponse",
  "metadata": {
    "model": "gpt-5.2-2025-12-11",
    "tokens_used": 3124,
    "processing_time_ms": 6290,
    "finish_reason": "stop"
  }
}
```

---

#### Topic: `alignment_explanation`

Get detailed explanation of an alignment score.

**Request Payload Structure:**

```json
{
  "topic_id": "alignment_explanation",
  "parameters": {
    "goal_id": "goal-123",
    "alignment_score": 85
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of goal |
| `alignment_score` | integer | Yes | Previously calculated alignment score (0-100) |

**Response Model:** `AlignmentExplanationResponse`

**Response Payload Structure:**

```json
{
  "explanation": "string",
  "key_factors": ["string"],
  "improvement_areas": ["string"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `explanation` | string | Detailed explanation of alignment |
| `key_factors` | array of string | Key factors influencing the score |
| `improvement_areas` | array of string | Areas for improvement |

---

#### Topic: `alignment_suggestions`

Get suggestions to improve goal alignment with business foundation.

**Request Payload Structure:**

```json
{
  "topic_id": "alignment_suggestions",
  "parameters": {
    "goal_id": "goal-123",
    "alignment_score": 65
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of goal |
| `alignment_score` | integer | Yes | Previously calculated alignment score (0-100) |

**Response Model:** `AlignmentSuggestionsResponse`

**Response Payload Structure:**

```json
{
  "suggestions": ["string"],
  "impact_analysis": "string"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | array of string | List of suggestions to improve alignment |
| `impact_analysis` | string | Analysis of potential impact |

**Example Response:**

```json
{
  "topic_id": "alignment_suggestions",
  "success": true,
  "data": {
    "suggestions": [
      "Reframe the goal to emphasize customer impact",
      "Add specific metrics that align with core values",
      "Connect the goal more explicitly to your vision statement"
    ],
    "impact_analysis": "These changes could improve alignment by 15-20 points..."
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

**Response Model:** `SwotAnalysisResponse`

**Status:** Inactive

---

#### Topic: `five_whys_questions`

Generate Five Whys analysis questions.

**Response Model:** `FiveWhysQuestionsResponse`

**Status:** Inactive

---

#### Topic: `action_suggestions`

Get AI-suggested actions for a goal or specific strategy.

**Request Payload Structure:**

```json
{
  "topic_id": "action_suggestions",
  "parameters": {
    "goal_id": "goal-123",
    "strategy_id": "strategy-456"  // Optional
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of the goal to generate action suggestions for |
| `strategy_id` | string | No | Optional: ID of specific strategy to generate actions for. If omitted, generates actions for all strategies under the goal |

**Auto-enriched Parameters:** `goal`, `strategies`, `business_foundation`

**Behavior:**
- **Without `strategy_id`**: Generates actions for all strategies under the goal (covers entire goal execution)
- **With `strategy_id`**: Generates actions only for that specific strategy (focused recommendations)

**Response Model:** `ActionSuggestionsResponse`

**Response Payload Structure:**

The `data` field contains:

```json
{
  "suggestions": [
    {
      "title": "string",
      "description": "string",
      "reasoning": "string",
      "priority": "low" | "medium" | "high" | "critical",
      "estimatedDuration": "string",
      "suggestedOwnerRole": "string" | null,
      "dependencies": ["string"],
      "sequenceOrder": number
    }
  ],
  "analysisNotes": "string",
  "timelineEstimate": "string" | null
}
```

| Field | Type | Description |
|-------|------|-------------|
| `suggestions` | array of ActionSuggestion | List of action suggestions (1-10 items) |
| `analysisNotes` | string (50-200 chars) | Meta-commentary on the suggestions |
| `timelineEstimate` | string \| null | Overall timeline estimate (optional) |

**ActionSuggestion Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string (5-100 chars) | Action title |
| `description` | string (50-500 chars) | Detailed action description |
| `reasoning` | string (50-200 chars) | Why this action is important |
| `priority` | string | Priority level: "low", "medium", "high", or "critical" |
| `estimatedDuration` | string | Human-readable duration estimate (e.g., '2 weeks') |
| `suggestedOwnerRole` | string \| null | Suggested role for ownership (optional) |
| `dependencies` | array of string | Titles of prerequisite actions (0-3 items) |
| `sequenceOrder` | number (≥1) | Suggested execution order |
| `associatedStrategyId` | string \| null | Strategy ID this action supports (null for goal-level actions) |
| `associatedStrategyName` | string \| null | Strategy name this action supports |

---

#### Topic: `optimize_action_plan`

Optimize an existing action plan for better outcomes.

**Request Payload Structure:**

```json
{
  "topic_id": "optimize_action_plan",
  "parameters": {
    "goal_id": "goal-123"
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `goal_id` | string | Yes | ID of the goal whose action plan should be optimized |

**Auto-enriched Parameters:** `goal`, `actions`, `business_context`

**Response Model:** `OptimizedActionPlanResponse`

**Response Payload Structure:**

```json
{
  "optimized_plan": [
    {
      "title": "string",
      "description": "string",
      "priority": "low" | "medium" | "high" | "critical",
      "estimatedDuration": number,
      "estimatedCost": number | null,
      "assignmentSuggestion": "string" | null,
      "dependencies": ["string"],
      "confidence": number,
      "reasoning": "string",
      "expectedOutcome": "string,
      "risks": ["string"]
    }
  ],
  "optimization_rationale": "string",
  "efficiency_gain": "string"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `optimized_plan` | array of ActionSuggestion | Optimized list of actions |
| `optimization_rationale` | string | Why this plan is optimized |
| `efficiency_gain` | string | Estimated efficiency gain |

**Note:** The `ActionSuggestion` structure in `optimize_action_plan` includes additional fields like `estimatedCost`, `confidence`, `expectedOutcome`, and `risks` compared to `action_suggestions`.

---

#### Topic: `prioritization_suggestions`

Suggest prioritization of operational tasks.

**Request Payload Structure:**

```json
{
  "topic_id": "prioritization_suggestions",
  "parameters": {
    "actions": [
      {
        "id": "action-123",
        "title": "Implement new feature",
        "currentPriority": "medium",
        "dueDate": "2025-03-15",
        "impact": "High customer satisfaction",
        "effort": "2 weeks",
        "status": "in_progress",
        "linkedGoals": ["goal-123"]
      }
    ],
    "businessContext": {
      "currentGoals": ["Increase revenue", "Improve retention"],
      "constraints": ["Limited budget", "Tight timeline"],
      "urgentDeadlines": ["Q1 launch"]
    }
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actions` | array of PrioritizationActionInput | Yes | Actions to prioritize (1-200 items) |
| `businessContext` | BusinessContext | Yes | Business context for prioritization |

**PrioritizationActionInput Structure:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique action identifier |
| `title` | string | Yes | Action title (min 1 char) |
| `currentPriority` | string | Yes | Current priority: "low", "medium", "high", or "critical" |
| `dueDate` | string | No | Due date in ISO8601 format |
| `impact` | string | No | Expected impact description |
| `effort` | string | No | Required effort description |
| `status` | string | Yes | Current status |
| `linkedGoals` | array of string | No | Linked goal IDs |

**BusinessContext Structure:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `currentGoals` | array of string | No | Current business goals |
| `constraints` | array of string | No | Business constraints |
| `urgentDeadlines` | array of string | No | Urgent deadlines |

**Response Model:** `PrioritizationSuggestionsResponse` (maps to `PrioritizationResponse`)

**Response Payload Structure:**

The `data` field contains:

```json
{
  "success": boolean,
  "data": [
    {
      "actionId": "string",
      "suggestedPriority": "low" | "medium" | "high" | "critical",
      "currentPriority": "low" | "medium" | "high" | "critical",
      "reasoning": "string",
      "confidence": number,
      "urgencyFactors": ["string"],
      "impactFactors": ["string"],
      "recommendedAction": "escalate" | "maintain" | "de-prioritize",
      "estimatedBusinessValue": number | null
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Request success status |
| `data` | array of PrioritizationSuggestion | Prioritization suggestions |

**PrioritizationSuggestion Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `actionId` | string | Action identifier |
| `suggestedPriority` | string | Suggested priority level |
| `currentPriority` | string | Current priority level |
| `reasoning` | string | Reasoning for suggestion |
| `confidence` | number (0-1) | Confidence score |
| `urgencyFactors` | array of string | Factors contributing to urgency |
| `impactFactors` | array of string | Factors contributing to impact |
| `recommendedAction` | string | Recommended action |
| `estimatedBusinessValue` | number \| null | Estimated business value in currency units (optional) |

---

#### Topic: `scheduling_suggestions`

Suggest optimal scheduling for tasks.

**Request Payload Structure:**

```json
{
  "topic_id": "scheduling_suggestions",
  "parameters": {
    "actions": [
      {
        "id": "action-123",
        "title": "Implement new feature",
        "estimatedDuration": 80,
        "dependencies": ["action-456"],
        "assignedTo": "user-789",
        "currentStartDate": "2025-02-01",
        "currentDueDate": "2025-02-15",
        "priority": "high"
      }
    ],
    "constraints": {
      "teamCapacity": 160,
      "criticalDeadlines": [
        {
          "date": "2025-03-01",
          "description": "Q1 launch deadline"
        }
      ],
      "teamAvailability": [
        {
          "personId": "user-789",
          "hoursPerWeek": 40,
          "unavailableDates": ["2025-02-10"]
        }
      ]
    }
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `actions` | array of SchedulingActionInput | Yes | Actions to schedule (1-100 items) |
| `constraints` | SchedulingConstraints | Yes | Scheduling constraints |

**SchedulingActionInput Structure:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique action identifier |
| `title` | string | Yes | Action title (min 1 char) |
| `estimatedDuration` | number | Yes | Estimated duration in hours (must be > 0) |
| `dependencies` | array of string | No | Action IDs this depends on |
| `assignedTo` | string | No | Assigned person/team ID |
| `currentStartDate` | string | No | Current start date in ISO8601 format |
| `currentDueDate` | string | No | Current due date in ISO8601 format |
| `priority` | string | Yes | Priority level: "low", "medium", "high", or "critical" |

**SchedulingConstraints Structure:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `teamCapacity` | number | Yes | Total team capacity in hours (must be > 0) |
| `criticalDeadlines` | array of CriticalDeadline | No | Critical deadline constraints |
| `teamAvailability` | array of TeamAvailability | No | Team member availability |

**CriticalDeadline Structure:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | Yes | Deadline date in ISO8601 format |
| `description` | string | Yes | Deadline description |

**TeamAvailability Structure:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `personId` | string | Yes | Person/team member identifier |
| `hoursPerWeek` | number | Yes | Available hours per week (1-168) |
| `unavailableDates` | array of string | No | Unavailable dates in ISO8601 format |

**Response Model:** `SchedulingSuggestionsResponse` (maps to `SchedulingResponse`)

**Response Payload Structure:**

The `data` field contains:

```json
{
  "success": boolean,
  "data": [
    {
      "actionId": "string",
      "suggestedStartDate": "string (ISO8601)",
      "suggestedDueDate": "string (ISO8601)",
      "reasoning": "string",
      "confidence": number,
      "dependencies": ["string"],
      "resourceConsiderations": ["string"],
      "risks": ["string"],
      "alternativeSchedules": [
        {
          "startDate": "string (ISO8601)",
          "dueDate": "string (ISO8601)",
          "rationale": "string"
        }
      ]
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Request success status |
| `data` | array of SchedulingSuggestion | Scheduling suggestions |

**SchedulingSuggestion Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `actionId` | string | Action identifier |
| `suggestedStartDate` | string | Suggested start date (ISO8601) |
| `suggestedDueDate` | string | Suggested due date (ISO8601) |
| `reasoning` | string | Reasoning for schedule |
| `confidence` | number (0-1) | Confidence score |
| `dependencies` | array of string | Dependencies that influenced schedule |
| `resourceConsiderations` | array of string | Resource considerations |
| `risks` | array of string | Identified risks |
| `alternativeSchedules` | array of AlternativeSchedule | Alternative scheduling options (optional) |

**AlternativeSchedule Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `startDate` | string | Alternative start date (ISO8601) |
| `dueDate` | string | Alternative due date (ISO8601) |
| `rationale` | string | Rationale for this alternative |

---

#### Topic: `categorize_issue`

Categorize operational issue by type and severity.

**Response Model:** `IssueCategoryResponse`

**Status:** Inactive

---

#### Topic: `assess_impact`

Assess business impact of operational issue.

**Response Model:** `ImpactAssessmentResponse`

**Status:** Inactive

---

### Operations-Strategic Integration Topics

*Note: Most topics in this category are currently inactive. Only active topics are listed below.*

#### Topic: `action_strategic_context`

Get strategic context for a specific action.

**Response Model:** `ActionStrategicContextResponse`

**Status:** Inactive

---

#### Topic: `suggest_connections`

Suggest strategic connections for actions.

**Response Model:** `SuggestedConnectionsResponse`

**Status:** Inactive

---

#### Topic: `update_connections`

Update strategic connections for an action.

**Response Model:** `UpdateConnectionsResponse`

**Status:** Inactive

---

#### Topic: `create_issue_from_action`

Create an issue from an incomplete action.

**Response Model:** `CreateIssueResponse`

**Status:** Inactive

---

#### Topic: `create_action_from_issue`

Create action items from an issue.

**Response Model:** `CreateActionResponse`

**Status:** Inactive

---

#### Topic: `complete_action`

Complete an action and update related items.

**Response Model:** `CompleteActionResponse`

**Status:** Inactive

---

#### Topic: `close_issue`

Close an issue and update related items.

**Response Model:** `CloseIssueResponse`

**Status:** Inactive

---

#### Topic: `issue_status`

Get comprehensive status of an issue.

**Response Model:** `IssueStatusResponse`

**Status:** Inactive

---

#### Topic: `issue_related_actions`

Get actions related to an issue.

**Response Model:** `RelatedActionsResponse`

**Status:** Inactive

---

#### Topic: `update_measure`

Update a measure value with audit trail.

**Response Model:** `UpdateMeasureResponse`

**Status:** Inactive

---

#### Topic: `calculate_measure`

Calculate measure value from linked data.

**Response Model:** `CalculateMeasureResponse`

**Status:** Inactive

---

#### Topic: `measure_history`

Get historical values for a measure.

**Response Model:** `MeasureHistoryResponse`

**Status:** Inactive

---

#### Topic: `measure_impact`

Analyze measure impact on strategic goals.

**Response Model:** `MeasureImpactResponse`

**Status:** Inactive

---

#### Topic: `action_measure_impact`

Calculate impact of action completion on measures.

**Response Model:** `ActionMeasureImpactResponse`

**Status:** Inactive

---

#### Topic: `sync_measures_to_strategy`

Sync operational measures to strategic planning.

**Response Model:** `SyncMeasuresResponse`

**Status:** Inactive

---

#### Topic: `detect_measure_conflicts`

Detect conflicts between operational and strategic measures.

**Response Model:** `MeasureConflictsResponse`

**Status:** Inactive

---

#### Topic: `resolve_measure_conflict`

Resolve a detected measure conflict.

**Response Model:** `ResolveConflictResponse`

**Status:** Inactive

---

#### Topic: `operations_strategic_alignment`

Get alignment status between operations and strategy.

**Response Model:** `StrategicAlignmentResponse`

**Status:** Inactive

---

#### Topic: `cascade_action_update`

Cascade action updates to related items.

**Response Model:** `CascadeUpdateResponse`

**Status:** Inactive

---

#### Topic: `cascade_issue_update`

Cascade issue updates to related items.

**Response Model:** `CascadeUpdateResponse`

**Status:** Inactive

---

#### Topic: `cascade_measure_update`

Cascade measure updates to related strategic items.

**Response Model:** `CascadeUpdateResponse`

**Status:** Inactive

---

### Analysis Topics

#### Topic: `alignment_analysis`

Analyze goal alignment with business foundation.

**Response Model:** `GoalAlignmentResponse`

**Note:** Response model structure not yet defined in codebase. Schema will be available via `GET /ai/schemas/GoalAlignmentResponse` once implemented.

---

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

**Note:** Response model structure not yet defined in codebase. Schema will be available via `GET /ai/schemas/MeasurePerformanceResponse` once implemented.

---

#### Topic: `operations_analysis`

Perform operational analysis (SWOT, root cause, action plan).

**Request Payload Structure:**

```json
{
  "topic_id": "operations_analysis",
  "parameters": {
    "analysis_type": "swot",
    "description": "We're experiencing declining customer retention and need to understand the root causes and develop an action plan.",
    "context": {
      "industry": "SaaS",
      "companySize": "50-100 employees",
      "recentChanges": ["New pricing model", "Product update"]
    }
  }
}
```

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `analysis_type` | string | Yes | Type of operational analysis: "swot", "root_cause", or "action_plan" |
| `description` | string | Yes | Description of situation/problem (10-10000 chars) |
| `context` | object | No | Additional operational context (key-value pairs) |

**Response Model:** `OperationsAnalysisResponse`

**Response Payload Structure:**

```json
{
  "analysis_id": "string",
  "analysis_type": "string",
  "specific_analysis_type": "string",
  "findings": {},
  "recommendations": [
    {}
  ],
  "priority_actions": ["string"],
  "created_at": "string (ISO8601)",
  "metadata": {}
}
```

| Field | Type | Description |
|-------|------|-------------|
| `analysis_id` | string | Analysis identifier |
| `analysis_type` | string | Analysis type |
| `specific_analysis_type` | string | Specific operational analysis type (e.g., "swot", "root_cause", "action_plan") |
| `findings` | object | Analysis findings (structure varies by type) |
| `recommendations` | array of object | Actionable recommendations |
| `priority_actions` | array of string | High-priority actions |
| `created_at` | string | Analysis timestamp (ISO8601) |
| `metadata` | object | Additional metadata |

**Note:** The `findings` structure varies based on `specific_analysis_type`. For SWOT analysis, it may contain `strengths`, `weaknesses`, `opportunities`, and `threats` arrays.

---

#### Topic: `topic_strategic_context`

Get strategic context for admin topic management.

**Response Model:** `TopicStrategicContextResponse`

**Status:** Inactive

---

## Conversation Topics

### Topic: `core_values`

Discover and articulate your organization's authentic core values through guided coaching.

**Type:** Conversation Coaching  
**Category:** Onboarding  
**Result Model:** `CoreValuesResult`

**Response Payload Structure (During Conversation):**

During the conversation, responses follow the `ConversationResponse` structure:

```json
{
  "message": "string",
  "is_final": boolean,
  "result": null | CoreValuesResult,
  "confidence": number
}
```

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | AI coach's conversational response |
| `is_final` | boolean | Whether the conversation has concluded |
| `result` | CoreValuesResult \| null | Final result when `is_final` is true |
| `confidence` | number (0-1) | Confidence score for the response |

**Final Result Schema (when `is_final` is true):**

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

| Field | Type | Description |
|-------|------|-------------|
| `values` | array of CoreValue | List of identified core values (1-7 items) |
| `summary` | string (50-1000 chars) | Summary of the core values |

**CoreValue Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (1-100 chars) | Value name (e.g., "Integrity", "Innovation") |
| `description` | string (10-500 chars) | What this value means to the organization |
| `importance` | string (10-500 chars) | Why this value matters and how it guides decisions |

**Endpoints:** Use `/ai/coaching/start`, `/ai/coaching/message`, `/ai/coaching/complete`

---

### Topic: `purpose`

Define your organization's deeper purpose and reason for existing through guided coaching.

**Type:** Conversation Coaching  
**Category:** Onboarding  
**Result Model:** `PurposeResult`

**Response Payload Structure (During Conversation):**

Same as `core_values` - responses follow the `ConversationResponse` structure with `message`, `is_final`, `result`, and `confidence` fields.

**Final Result Schema (when `is_final` is true):**

```json
{
  "purpose_statement": "string (20-500 chars)",
  "why_it_matters": "string (50-1000 chars)",
  "how_it_guides": "string (50-1000 chars)"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `purpose_statement` | string (20-500 chars) | The organization's purpose statement |
| `why_it_matters` | string (50-1000 chars) | Why this purpose is meaningful |
| `how_it_guides` | string (50-1000 chars) | How purpose guides decisions |

**Endpoints:** Use `/ai/coaching/start`, `/ai/coaching/message`, `/ai/coaching/complete`

---

### Topic: `vision`

Craft a compelling vision for your organization's future through guided coaching.

**Type:** Conversation Coaching  
**Category:** Onboarding  
**Result Model:** `VisionResult`

**Response Payload Structure (During Conversation):**

Same as `core_values` - responses follow the `ConversationResponse` structure with `message`, `is_final`, `result`, and `confidence` fields.

**Final Result Schema (when `is_final` is true):**

```json
{
  "vision_statement": "string (20-500 chars)",
  "time_horizon": "string (1-50 chars)",
  "key_aspirations": ["string"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `vision_statement` | string (20-500 chars) | The organization's vision statement |
| `time_horizon` | string (1-50 chars) | Time frame for the vision (e.g., "5 years", "10 years") |
| `key_aspirations` | array of string (1-10 items) | Key aspirations that comprise the vision |

**Endpoints:** Use `/ai/coaching/start`, `/ai/coaching/message`, `/ai/coaching/complete`

---

## Response Model Schemas

### OnboardingReviewResponse

Used by: `niche_review`, `value_proposition_review`

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

### IcaReviewResponse

Used by: `ica_review`

```typescript
interface IcaReviewResponse {
  qualityReview: string | null;  // Review of current ICA if provided, null if no current_value
  suggestions: IcaSuggestion[];   // Exactly 3 detailed persona suggestions
}

interface IcaSuggestion {
  title: string;            // Descriptive persona name (5-100 chars)
  demographics: string;     // Age, gender, location, income, education, occupation, family (20-500 chars)
  goalsAspirations: string; // What they want to achieve, ambitions (20-500 chars)
  painPoints: string;       // Problems, challenges, frustrations (20-500 chars)
  motivations: string;      // What drives them, values, priorities (20-500 chars)
  commonObjectives: string; // Typical goals and milestones (20-500 chars)
  whereToFind: string;      // Channels, communities, platforms (20-500 chars)
  buyingProcess: string;    // Research and decision-making process (20-500 chars)
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
| 404 | `Topic not found: {topic_id}` | Topic not found in topic registry. Check `topic_id` against `/ai/topics` |
| 400 | `Topic is not active: {topic_id}` | Topic is disabled in registry or DynamoDB, contact admin |
| 400 | `Topic {topic_id} is type {type}` | Use appropriate endpoint based on TopicType (single-shot vs conversation) |
| 422 | `Missing required parameters: [...]` | Include all required parameters as defined in topic registry |
| 500 | `Response model not configured` | Response model not found in response model registry |
| 500 | `Parameter enrichment failed` | Backend data source unavailable |

### Coaching Conversation Error Codes

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

### Async Execution

```typescript
// 1. Start async job
const { jobId, status } = await coachingClient.post('/ai/execute-async', {
  topic_id: 'niche_review',
  parameters: { current_value: 'We help small businesses grow' }
});

// 2. Listen for WebSocket events
websocket.on('message', (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'ai.job.completed' && data.data.jobId === jobId) {
    handleResult(data.data.result);
  }
});
```

### Coaching Conversation

```typescript
// Start or resume a coaching session
async function startCoachingSession(topicId: string, context?: Record<string, any>) {
  const response = await coachingClient.post('/ai/coaching/start', {
    topic_id: topicId,
    context
  });
  return response.data.data;
}

// Send a message and get coach response
async function sendMessage(sessionId: string, message: string) {
  const response = await coachingClient.post('/ai/coaching/message', {
    session_id: sessionId,
    message
  });
  return response.data.data;
}
```

---

## Changelog

### Version 2.1 (January 15, 2026)

- **Major Restructure:** Added revision log at top, comprehensive table of contents with hyperlinks
- **Reorganization:** Moved async execution and coaching conversation endpoints to Core Endpoints section
- **Topic Organization:** Created Supported Topics summary with hyperlinks organized by category
- **Parameter Reference:** Moved available parameters section after index
- **Complete Topic List:** Verified and listed all topics from registry by category (single-shot first, then conversation)
- **Response Models:** Verified all response models match the codebase registry
- **Architectural Clarification:** Documented topic-centric architecture, clarified topic data sources (registry, DynamoDB, S3, seed data), and explained endpoint routing based on TopicType

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

_This document is maintained in sync with the topic registry in the codebase. All topics are defined in `coaching/src/core/topic_registry.py`._
