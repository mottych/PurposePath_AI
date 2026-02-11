# Admin AI Specifications - LLM Topic Management

- Last Updated: January 30, 2026
- Version: 3.0

## Revision History

| Date | Version | Description |
|------|---------|-------------|
| 2026-01-30 | 3.0 | **Issue #158 Completion:** Added tier-based LLM model selection and topic access control. Replaced `model_code` with `basic_model_code` and `premium_model_code`. Added `tier_level` field (FREE, BASIC, PREMIUM, ULTIMATE). |
| 2026-01-25 | 2.0 | **Issue #196 Completion:** Fixed category enum values to match actual TopicCategory implementation, verified all field values match constants.py |
| 2025-12-25 | 1.0 | Initial admin specification |

---

## Overview

This document specifies all admin endpoints for managing the LLM Topic system. Admin users can update topic configurations, manage prompts, and test topics.

**Important:** Topics are defined in the code-based `endpoint_registry` and cannot be created or deleted by admins. Admins can only:
- Update topic configurations (tier level, dual LLM models, temperature, prompts, etc.)
- Manage prompt content (system, user, assistant prompts)
- Test topic configurations before activation

### Tier-Based Access Control (Issue #158)

Each topic has a `tier_level` that controls:
1. **Topic Access**: Which subscription tiers can access the topic
2. **Model Selection**: Which LLM model to use based on user's tier

**Tier Levels:**
- **FREE**: Users can access only FREE topics, uses `basic_model_code`
- **BASIC**: Users can access FREE + BASIC topics, uses `basic_model_code`
- **PREMIUM**: Users can access FREE + BASIC + PREMIUM topics, uses `premium_model_code`
- **ULTIMATE**: Users can access all topics, uses `premium_model_code`

**Dual Model Configuration:**
- `basic_model_code`: LLM model for FREE and BASIC tier users
- `premium_model_code`: LLM model for PREMIUM and ULTIMATE tier users
- Admins can set different models for each tier (e.g., Claude Haiku for basic, Claude Sonnet for premium)

--- 

## Implementation Status

| Endpoint | Status | Notes |
|----------|--------|-------|
| GET /topics | ✅ Implemented | List topics from registry + DB overrides |
| GET /topics/{topic_id} | ✅ Implemented | |
| PUT /topics/{topic_id} | ✅ Implemented | Update topic config |
| GET /topics/{topic_id}/prompts/{prompt_type} | ✅ Implemented | |
| PUT /topics/{topic_id}/prompts/{prompt_type} | ✅ Implemented | |
| POST /topics/{topic_id}/prompts | ✅ Implemented | |
| DELETE /topics/{topic_id}/prompts/{prompt_type} | ✅ Implemented | |
| GET /models | ✅ Implemented | |
| POST /topics/validate | ✅ Implemented | |
| POST /topics/{topic_id}/test | ✅ Implemented | **New** - Test with auto-enrichment |
| GET /topics/{topic_id}/stats | ⏳ Planned | Usage statistics |

---

## Authentication

All admin endpoints require:

- **Authentication**: Bearer token with admin role
- **Authorization**: `admin:topics:*` permission scope
- **Headers**:
  - `Authorization: Bearer {token}`
  - `Content-Type: application/json`

---

## Endpoints

### 1. List Topics

**Purpose:** Get all topics (active and inactive) for admin management

**Endpoint:**

```http
GET /api/v1/admin/topics
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description | Allowed Values |
|-----------|------|----------|---------|-------------|----------------|
| `page` | integer | No | 1 | Page number | >= 1 |
| `page_size` | integer | No | 50 | Items per page (max 100) | 1-100 |
| `category` | string | No | - | Filter by category | `onboarding`, `conversation`, `insights`, `strategic_planning`, `operations_ai`, `operations_strategic_integration`, `analysis` |
| `topic_type` | string | No | - | Filter by type | `conversation_coaching`, `single_shot`, `measure_system` |
| `is_active` | boolean | No | - | Filter by active status | `true`, `false` |
| `search` | string | No | - | Search in name/description | Max 100 chars |

**Response:**

```json
{
  "topics": [
    {
      "topic_id": "core_values_coaching",
      "topic_name": "Core Values - Coaching Session",
      "category": "core_values",
      "topic_type": "conversation_coaching",
      "tier_level": "free",
      "basic_model_code": "claude-3-5-sonnet-20241022",
      "premium_model_code": "claude-3-5-sonnet-20241022",
      "temperature": 0.7,
      "max_tokens": 2000,
      "is_active": true,
      "description": "Explore core values through conversation",
      "display_order": 1,
      "from_database": true,
      "templates": [
        {"prompt_type": "system", "is_defined": true},
        {"prompt_type": "user", "is_defined": false}
      ],
      "created_at": "2024-11-01T10:00:00Z",
      "updated_at": "2024-11-13T15:30:00Z",
      "created_by": "admin_123"
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 50,
  "has_more": false
}
```

**Response Field Descriptions:**

| Field | Description |
|-------|-------------|
| `from_database` | `true` = Topic config stored in DB, `false` = Using registry defaults |
| `templates` | Array of allowed templates with `is_defined` indicating if uploaded to S3 |

**Status Codes:**

- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 2. Get Topic Details

**Purpose:** Get complete details for a specific topic including prompts and allowed parameters

**Endpoint:**

```http
GET /api/v1/admin/topics/{topic_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description | Format |
|-----------|------|----------|-------------|--------|
| `topic_id` | string | Yes | Unique topic identifier | snake_case, 3-50 chars |

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `include_schema` | boolean | No | `false` | Include JSON schema of the response model for template design |

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "topic_name": "Core Values - Coaching Session",
  "category": "core_values",
  "topic_type": "conversation_coaching",
  "description": "Explore your core values through conversation",
  "tier_level": "free",
  "basic_model_code": "claude-3-5-sonnet-20241022",
  "premium_model_code": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "is_active": true,
  "display_order": 1,
  "from_database": true,
  "prompts": [
    {
      "prompt_type": "system",
      "s3_bucket": "purposepath-prompts-prod",
      "s3_key": "prompts/core_values_coaching/system.md",
      "updated_at": "2024-11-13T15:30:00Z",
      "updated_by": "admin_123"
    },
    {
      "prompt_type": "user",
      "s3_bucket": "purposepath-prompts-prod",
      "s3_key": "prompts/core_values_coaching/user.md",
      "updated_at": "2024-11-13T15:30:00Z",
      "updated_by": "admin_123"
    }
  ],
  "template_status": [
    {
      "prompt_type": "system",
      "is_defined": true,
      "s3_bucket": "purposepath-prompts-prod",
      "s3_key": "prompts/core_values_coaching/system.md",
      "updated_at": "2024-11-13T15:30:00Z",
      "updated_by": "admin_123"
    },
    {
      "prompt_type": "user",
      "is_defined": false,
      "s3_bucket": null,
      "s3_key": null,
      "updated_at": null,
      "updated_by": null
    }
  ],
  "allowed_parameters": [
    {
      "name": "user_name",
      "type": "string",
      "required": true,
      "description": "User's display name"
    },
    {
      "name": "core_values",
      "type": "string",
      "required": false,
      "description": "User's defined core values (auto-enriched from profile)"
    },
    {
      "name": "purpose",
      "type": "string",
      "required": false,
      "description": "User's purpose statement (auto-enriched from profile)"
    }
  ],
  "conversation_config": {
    "max_messages_to_llm": 30,
    "inactivity_timeout_minutes": 30,
    "session_ttl_days": 14,
    "estimated_messages": 20,
    "extraction_model_code": "CLAUDE_3_5_HAIKU"
  },
  "response_schema": null,
  "created_at": "2024-11-01T10:00:00Z",
  "updated_at": "2024-11-13T15:30:00Z",
  "created_by": "admin_123"
}
```

**Response Schema (when `include_schema=true`):**

When the `include_schema` query parameter is set to `true`, the response includes the JSON schema of the expected response model. This is useful for template authors to understand what output fields their prompts should generate.

Example with `include_schema=true`:

```json
{
  "topic_id": "niche_review",
  "...": "...other fields...",
  "response_schema": {
    "title": "OnboardingReviewResponse",
    "type": "object",
    "properties": {
      "strengths": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of strengths identified"
      },
      "weaknesses": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of weaknesses or areas for improvement"
      },
      "recommendations": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of actionable recommendations"
      },
      "alignment_score": {
        "type": "integer",
        "minimum": 0,
        "maximum": 100,
        "description": "Overall alignment score"
      },
      "summary": {
        "type": "string",
        "description": "Summary of the analysis"
      }
    },
    "required": ["strengths", "weaknesses", "recommendations", "alignment_score", "summary"]
  }
}
```

**Note:** The `response_schema` is `null` when:
- `include_schema=false` (default)
- The topic is not in the endpoint registry (custom topics)
- The response model is not registered in the response model registry

**Conversation Config (conversation_coaching topics only):**

For topics with `topic_type: "conversation_coaching"`, the response includes `conversation_config`:

| Field | Type | Range | Default | Description |
|-------|------|-------|---------|-------------|
| `max_messages_to_llm` | integer | 5-100 | 30 | Maximum messages to include in LLM context (sliding window) |
| `inactivity_timeout_minutes` | integer | 5-1440 | 30 | Minutes of inactivity before session auto-pauses |
| `session_ttl_days` | integer | 1-90 | 14 | Days to keep paused/completed sessions before deletion |
| `estimated_messages` | integer | 5-100 | 20 | Estimated messages for a typical session (for progress calculation) |
| `extraction_model_code` | string | - | CLAUDE_3_5_HAIKU | MODEL_REGISTRY code for extraction (e.g., CLAUDE_3_5_HAIKU, CLAUDE_3_5_SONNET_V2) |

**Template Status:**

The `template_status` array shows each allowed template and its definition status:

| Field | Description |
|-------|-------------|
| `is_defined` | `true` if this prompt has been uploaded to S3 |
| `s3_bucket`, `s3_key` | S3 location (null if not defined) |
| `updated_at`, `updated_by` | Last update info (null if not defined) |

**Status Codes:**

- `200 OK`: Success
- `404 Not Found`: Topic does not exist
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 3. Create Topic

**Purpose:** Create a new topic with configuration

**Endpoint:**

```http
POST /api/v1/admin/topics
```

**Request Body:**

```json
{
  "topic_id": "purpose_discovery",
  "topic_name": "Purpose Discovery Session",
  "category": "purpose",
  "topic_type": "conversation_coaching",
  "description": "Discover your life's purpose through guided conversation",
  "tier_level": "free",
  "basic_model_code": "claude-3-5-sonnet-20241022",
  "premium_model_code": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "is_active": false,
  "display_order": 10,
  "allowed_parameters": [
    {
      "name": "user_name",
      "type": "string",
      "required": true,
      "description": "User's display name"
    },
    {
      "name": "core_values",
      "type": "string",
      "required": false,
      "description": "User's defined core values"
    }
  ]
}
```

**Allowed Parameter Types:**

- `string`: Text value
- `integer`: Whole number
- `float`: Decimal number
- `boolean`: true/false
- `array`: List of values
- `object`: Nested structure

**Parameter Definition Schema:**

```json
{
  "name": "parameter_name",
  "type": "string|integer|float|boolean|array|object",
  "required": true,
  "description": "Human-readable description"
}
```

**Validation Rules:**

| Field | Rules | Allowed Values / Format |
|-------|-------|------------------------|
| `topic_id` | Required, unique, lowercase, snake_case, 3-50 chars | Regex: `^[a-z][a-z0-9_]*$` |
| `topic_name` | Required, 3-100 chars | Any printable characters |
| `category` | Required | Enum: `onboarding`, `conversation`, `insights`, `strategic_planning`, `operations_ai`, `operations_strategic_integration`, `analysis` |
| `topic_type` | Required | Enum: `conversation_coaching`, `single_shot`, `measure_system` |
| `tier_level` | Optional, default `free` | Enum: `free`, `basic`, `premium`, `ultimate` |
| `basic_model_code` | Required, must be valid model code | See "Supported Model Codes" below (used for FREE/BASIC tiers) |
| `premium_model_code` | Required, must be valid model code | See "Supported Model Codes" below (used for PREMIUM/ULTIMATE tiers) |
| `temperature` | Required, float | 0.0-2.0 |
| `max_tokens` | Required, integer | 1-100000 (model dependent) |
| `top_p` | Optional, float, default 1.0 | 0.0-1.0 |
| `frequency_penalty` | Optional, float, default 0.0 | -2.0 to 2.0 |
| `presence_penalty` | Optional, float, default 0.0 | -2.0 to 2.0 |
| `display_order` | Optional, integer, default 100 | 1-1000 |
| `description` | Optional | Max 500 chars |
| `is_active` | Optional, boolean, default false | `true`, `false` |

**Supported Model Codes:**

- `claude-3-5-sonnet-20241022` (recommended)
- `claude-3-5-haiku-20241022`
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-4`
- `gpt-3.5-turbo`

**Category Descriptions:**

- `core_values`: Topics related to identifying and exploring personal values
- `purpose`: Life purpose and meaning discovery
- `vision`: Future vision and aspiration setting
- `goals`: Goal setting and achievement planning
- `strategy`: Strategic planning and decision making
- `measure`: Key performance indicators and metrics
- `custom`: Custom topics not fitting standard categories

**Topic Type Descriptions:**

- `conversation_coaching`: Interactive conversational coaching sessions (multi-turn)
- `single_shot`: One-shot evaluations, assessments, and analysis
- `measure_system`: Measure calculation and tracking

**Prompt Types by Topic Type:**

| Topic Type | Required Prompts | Description |
|------------|-----------------|-------------|
| `conversation_coaching` | `system`, `initiation`, `resume`, `extraction` | System defines coach behavior; initiation starts new sessions; resume continues paused sessions; extraction captures results |
| `single_shot` | `system`, `user` | System defines behavior; user template with parameters |
| `measure_system` | `system`, `user` | System defines calculation behavior; user template for input |

**Response:**

```json
{
  "topic_id": "purpose_discovery",
  "created_at": "2024-11-13T16:00:00Z",
  "message": "Topic created successfully. Upload prompts to activate."
}
```

**Status Codes:**

- `201 Created`: Success
- `400 Bad Request`: Validation error
- `409 Conflict`: Topic ID already exists
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

**Error Response (Validation):**

```json
{
  "error": "Validation failed",
  "validation_errors": [
    {
      "field": "topic_id",
      "message": "Topic ID must be snake_case",
      "code": "INVALID_FORMAT"
    }
  ]
}
```

---

### 4. Update Topic

**Purpose:** Update topic configuration (excluding prompts)

**Endpoint:**

```http
PUT /api/v1/admin/topics/{topic_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description | Format |
|-----------|------|----------|-------------|--------|
| `topic_id` | string | Yes | Unique topic identifier | snake_case, 3-50 chars |

**Request Body:**

```json
{
  "topic_name": "Core Values - Updated Name",
  "description": "Updated description",
  "tier_level": "basic",
  "basic_model_code": "claude-3-5-haiku-20241022",
  "premium_model_code": "claude-3-5-sonnet-20241022",
  "temperature": 0.5,
  "max_tokens": 1500,
  "is_active": true,
  "display_order": 5,
  "conversation_config": {
    "max_messages_to_llm": 30,
    "inactivity_timeout_minutes": 45,
    "session_ttl_days": 14,
    "estimated_messages": 25,
    "extraction_model_code": "CLAUDE_3_5_SONNET_V2"
  },
  "allowed_parameters": [
    {
      "name": "user_name",
      "type": "string",
      "required": true,
      "description": "User's display name"
    }
  ]
}
```

**Notes:**

- Only include fields you want to update
- Cannot update `topic_id`
- Cannot update `category` or `topic_type` (create new topic instead)
- Cannot update `created_at` or `created_by`
- `allowed_parameters` replaces entire list when provided
- `conversation_config` is only applicable for `conversation_coaching` topic types

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "updated_at": "2024-11-13T16:15:00Z",
  "message": "Topic updated successfully"
}
```

**Status Codes:**

- `200 OK`: Success
- `400 Bad Request`: Validation error
- `404 Not Found`: Topic does not exist
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 5. Delete Topic

**Purpose:** Soft delete a topic (mark as inactive)

**Endpoint:**

```http
DELETE /api/v1/admin/topics/{topic_id}
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description | Allowed Values |
|-----------|------|----------|---------|-------------|----------------|
| `hard_delete` | boolean | No | false | If true, permanently delete (use with caution) | `true`, `false` |

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "deleted_at": "2024-11-13T16:20:00Z",
  "message": "Topic deactivated successfully"
}
```

**Status Codes:**

- `200 OK`: Success (soft delete)
- `204 No Content`: Success (hard delete)
- `404 Not Found`: Topic does not exist
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 6. Get Prompt Content

**Purpose:** Retrieve actual prompt content (markdown text) for editing

**Endpoint:**

```http
GET /api/v1/admin/topics/{topic_id}/prompts/{prompt_type}
```

**Path Parameters:**

| Parameter | Type | Required | Description | Allowed Values |
|-----------|------|----------|-------------|----------------|
| `topic_id` | string | Yes | Unique topic identifier | snake_case, 3-50 chars |
| `prompt_type` | string | Yes | Type of prompt | Enum: `system`, `user`, `assistant` |

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "prompt_type": "system",
  "content": "You are an expert life coach specializing in helping people discover their core values...\n\n## Your Role\n...",
  "s3_key": "prompts/core_values_coaching/system.md",
  "updated_at": "2024-11-13T15:30:00Z",
  "updated_by": "admin_123"
}
```

**Status Codes:**

- `200 OK`: Success
- `404 Not Found`: Topic or prompt not found
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 7. Update Prompt Content

**Purpose:** Update prompt markdown content

**Endpoint:**

```http
PUT /api/v1/admin/topics/{topic_id}/prompts/{prompt_type}
```

**Path Parameters:**

| Parameter | Type | Required | Description | Allowed Values |
|-----------|------|----------|-------------|----------------|
| `topic_id` | string | Yes | Unique topic identifier | snake_case, 3-50 chars |
| `prompt_type` | string | Yes | Type of prompt | Enum: `system`, `user`, `assistant` |

**Request Body:**

```json
{
  "content": "# Updated System Prompt\n\nYou are an expert life coach...",
  "commit_message": "Improved clarity and added examples"
}
```

**Validation:**

- `content`: Required, markdown text, 1-50,000 chars, UTF-8 encoded
- `commit_message`: Optional, for audit trail, max 200 chars

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "prompt_type": "system",
  "s3_key": "prompts/core_values_coaching/system.md",
  "updated_at": "2024-11-13T16:30:00Z",
  "version": "1.2.0",
  "message": "Prompt updated successfully"
}
```

**Status Codes:**

- `200 OK`: Success
- `400 Bad Request`: Validation error
- `404 Not Found`: Topic not found
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 8. Create/Upload New Prompt

**Purpose:** Add a new prompt type to a topic

**Endpoint:**

```http
POST /api/v1/admin/topics/{topic_id}/prompts
```

**Request Body:**

```json
{
  "prompt_type": "assistant",
  "content": "# Assistant Prompt\n\nProvide helpful guidance..."
}
```

**Validation:**

- `prompt_type`: Required, enum: `system`, `user`, `assistant`
- `content`: Required, markdown text, 1-50,000 chars, UTF-8 encoded

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "prompt_type": "assistant",
  "s3_key": "prompts/core_values_coaching/assistant.md",
  "created_at": "2024-11-13T16:35:00Z",
  "message": "Prompt created successfully"
}
```

**Status Codes:**

- `201 Created`: Success
- `400 Bad Request`: Validation error
- `409 Conflict`: Prompt type already exists
- `404 Not Found`: Topic not found
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 9. Delete Prompt

**Purpose:** Remove a prompt from a topic

**Endpoint:**

```http
DELETE /api/v1/admin/topics/{topic_id}/prompts/{prompt_type}
```

**Response:**

```json
{
  "message": "Prompt deleted successfully"
}
```

**Status Codes:**

- `200 OK`: Success
- `404 Not Found`: Prompt not found
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 10. List Available Models

**Purpose:** Get list of supported LLM models for topic configuration

**Endpoint:**

```http
GET /api/v1/admin/models
```

**Response:**

```json
{
  "models": [
    {
      "model_code": "claude-3-5-sonnet-20241022",
      "model_name": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "capabilities": ["chat", "function_calling"],
      "context_window": 200000,
      "max_output_tokens": 4096,
      "cost_per_input_million": 3.00,
      "cost_per_output_million": 15.00,
      "is_active": true
    },
    {
      "model_code": "claude-3-5-haiku-20241022",
      "model_name": "Claude 3.5 Haiku",
      "provider": "anthropic",
      "capabilities": ["chat"],
      "context_window": 200000,
      "max_output_tokens": 4096,
      "cost_per_input_million": 0.80,
      "cost_per_output_million": 4.00,
      "is_active": true
    }
  ]
}
```

**Status Codes:**

- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid auth token

---

### 11. Validate Topic Configuration

**Purpose:** Test a topic configuration before saving

**Endpoint:**

```http
POST /api/v1/admin/topics/validate
```

**Request Body:**

```json
{
  "topic_id": "test_topic",
  "topic_name": "Test Topic",
  "category": "custom",
  "topic_type": "single_shot",
  "tier_level": "free",
  "basic_model_code": "claude-3-5-sonnet-20241022",
  "premium_model_code": "claude-3-5-sonnet-20241022",
  "temperature": 0.7,
  "max_tokens": 2000,
  "prompts": [
    {
      "prompt_type": "system",
      "content": "Test system prompt with {user_name}"
    }
  ],
  "allowed_parameters": [
    {
      "name": "user_name",
      "type": "string",
      "required": true
    }
  ]
}
```

**Response (Valid):**

```json
{
  "valid": true,
  "warnings": [],
  "suggestions": [
    "Consider lowering temperature to 0.5 for more consistent responses"
  ]
}
```

**Response (Invalid):**

```json
{
  "valid": false,
  "errors": [
    {
      "field": "prompts[0].content",
      "message": "Prompt references parameter 'user_age' which is not defined",
      "code": "UNDEFINED_PARAMETER"
    }
  ],
  "warnings": [
    {
      "field": "temperature",
      "message": "High temperature may produce inconsistent results",
      "code": "HIGH_TEMPERATURE"
    }
  ]
}
```

**Status Codes:**

- `200 OK`: Validation complete (check `valid` field)
- `400 Bad Request`: Malformed request
- `401 Unauthorized`: Missing or invalid auth token

---

### 12. Test Topic

**Purpose:** Test a topic configuration by executing it with sample parameters. Allows admins to verify prompts work correctly before activating a topic.

**Endpoint:**

```http
POST /api/v1/admin/topics/{topic_id}/test
```

**Path Parameters:**

| Parameter | Type | Required | Description | Format |
|-----------|------|----------|-------------|--------|
| `topic_id` | string | Yes | Unique topic identifier | snake_case, 3-50 chars |

**Request Body:**

```json
{
  "parameters": {
    "website_url": "https://example.com",
    "scan_depth": 2
  },
  "allow_inactive": false
}
```

**Notes:**

- **Only supports `single_shot` topics** - conversation_coaching and other topic types cannot be tested via this endpoint
- Parameters not provided will be auto-enriched if a JWT token is supplied (template processor enabled)
- `allow_inactive`: When true, permits testing inactive topics for draft validation

**Response (Success):**

```json
{
  "success": true,
  "topic_id": "website_scan",
  "rendered_system_prompt": "...system prompt after substitutions...",
  "rendered_user_prompt": "...user prompt after substitutions...",
  "enriched_parameters": {
    "website_url": "https://example.com",
    "scan_depth": 2,
    "website_content": "..."
  },
  "response": {
    "scan_id": "a1d3b5d8-42cd-4d76-80db-92cf3b4a1a91",
    "captured_at": "2025-12-24T05:10:11Z",
    "source_url": "https://example.com",
    "company_profile": {"company_name": "Acme", "legal_name": "Acme, Inc.", "tagline": "...", "overview": "..."},
    "target_market": {"primary_audience": "...", "segments": ["..."], "pain_points": ["..."]},
    "offers": {"primary_product": "...", "categories": ["..."], "features": ["..."], "differentiators": ["..."]},
    "credibility": {"notable_clients": ["..."], "testimonials": [{"quote": "...", "attribution": "..."}]},
    "conversion": {"primary_cta_text": "...", "primary_cta_url": "https://example.com/demo", "supporting_assets": [{"label": "ROI calculator", "url": "https://example.com/roi"}]}
  },
  "response_model": "WebsiteScanResponse",
  "response_schema": {"title": "WebsiteScanResponse", "type": "object", "properties": {"scan_id": {"type": "string"}, "captured_at": {"type": "string"}}},
  "llm_metadata": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "usage": {"prompt_tokens": 1200, "completion_tokens": 600, "total_tokens": 1800},
    "finish_reason": "stop"
  },
  "execution_time_ms": 1245.5
}
```

**Response (Error):**

```json
{
  "success": false,
  "topic_id": "website_scan",
  "error": "Missing required parameters: website_url",
  "execution_time_ms": 150.2
}
```

**Status Codes:**

- `200 OK`: Test completed (check `success` field)
- `400 Bad Request`: Unsupported topic type (only single_shot topics supported)
- `404 Not Found`: Topic not found
- `422 Unprocessable Entity`: Missing required parameters
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions
- `500 Internal Server Error`: AI processing or serialization failure

---

### 14. Get Topic Usage Statistics (Planned)

**Status:** ⏳ Not yet implemented

**Purpose:** View usage metrics for a topic

**Endpoint:**

```http
GET /api/v1/admin/topics/{topic_id}/stats
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `start_date` | string | No | 30 days ago | ISO 8601 date |
| `end_date` | string | No | now | ISO 8601 date |

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "period": {
    "start": "2024-10-14T00:00:00Z",
    "end": "2024-11-13T23:59:59Z"
  },
  "usage": {
    "total_conversations": 1247,
    "total_tokens_used": 1850000,
    "estimated_cost": 27.75
  }
}
```

---

## Admin UI Workflows

### Configuring a Topic

Topics are defined in the `endpoint_registry` code. Admins configure them by:

1. **GET** `/api/v1/admin/topics` - View all topics with `templates` (showing allowed and defined prompts)
2. **GET** `/api/v1/admin/topics/{topic_id}` - Get topic details with `template_status` and `allowed_parameters`
3. **POST** `/api/v1/admin/topics/{topic_id}/prompts` - Upload required prompts (system, user, etc.)
4. **PUT** `/api/v1/admin/topics/{topic_id}` - Update model config (temperature, max_tokens, etc.)
5. **POST** `/api/v1/admin/topics/{topic_id}/test` - Test with sample parameters
6. **PUT** `/api/v1/admin/topics/{topic_id}` - Activate topic (`is_active: true`)

### Editing Prompts

1. **GET** `/api/v1/admin/topics/{topic_id}` - Get topic details with `template_status` and `allowed_parameters`
2. **GET** `/api/v1/admin/topics/{topic_id}/prompts/{prompt_type}` - Get current content
3. Edit in UI using `allowed_parameters` as available placeholders
4. **PUT** `/api/v1/admin/topics/{topic_id}/prompts/{prompt_type}` - Save changes
5. **POST** `/api/v1/admin/topics/{topic_id}/test` - Test the changes
6. Cache cleared automatically

---

## Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `TOPIC_NOT_FOUND` | 404 | Topic ID does not exist |
| `TOPIC_EXISTS` | 409 | Topic ID already taken |
| `INVALID_TOPIC_ID` | 400 | Topic ID format invalid |
| `INVALID_MODEL` | 400 | Model code not recognized |
| `PROMPT_NOT_FOUND` | 404 | Prompt type not found |
| `PROMPT_EXISTS` | 409 | Prompt type already exists |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid auth |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `S3_ERROR` | 500 | Cloud storage error |
| `CACHE_ERROR` | 500 | Cache operation failed |

---

## Rate Limiting

Admin endpoints have separate rate limits:

- **Read operations**: 100 requests/minute
- **Write operations**: 20 requests/minute
- **Bulk operations**: 5 requests/minute

Headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699987200
```

---

## Permissions

Required permission scopes:

| Action | Permission |
|--------|-----------|
| List topics | `admin:topics:read` |
| View topic | `admin:topics:read` |
| Create topic | `admin:topics:write` |
| Update topic | `admin:topics:write` |
| Delete topic | `admin:topics:delete` |
| View prompts | `admin:topics:read` |
| Update prompts | `admin:prompts:write` |
| Test topic | `admin:topics:write` |
| View stats | `admin:topics:stats` |

---

## Versioning

API Version: `v1`

Version in URL: `/api/v1/admin/...`

Breaking changes will increment major version.

---

## Support

For API issues or questions:

- Documentation: `llm_topic_architecture.md`
- Frontend changes: `fe_ai_specifications.md`
- Support: backend-team@purposepath.com
