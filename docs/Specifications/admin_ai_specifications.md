# Admin AI Specifications - LLM Topic Management

- Created on 11/13/2025

## Overview

This document specifies all admin endpoints required to manage the LLM Topic system. Admin users can create, update, activate/deactivate topics, and manage prompts.

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
| `category` | string | No | - | Filter by category | `core_values`, `purpose`, `vision`, `goals`, `strategy`, `kpi`, `custom` |
| `topic_type` | string | No | - | Filter by type | `coaching`, `assessment`, `analysis`, `kpi` |
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
      "topic_type": "coaching",
      "model_code": "claude-3-5-sonnet-20241022",
      "temperature": 0.7,
      "max_tokens": 2000,
      "is_active": true,
      "description": "Explore core values through conversation",
      "display_order": 1,
      "from_database": true,
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

**Status Codes:**

- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 2. Get Topic Details

**Purpose:** Get complete details for a specific topic including prompts

**Endpoint:**

```http
GET /api/v1/admin/topics/{topic_id}
```

**Path Parameters:**

| Parameter | Type | Required | Description | Format |
|-----------|------|----------|-------------|--------|
| `topic_id` | string | Yes | Unique topic identifier | snake_case, 3-50 chars |

**Response:**

```json
{
  "topic_id": "core_values_coaching",
  "topic_name": "Core Values - Coaching Session",
  "category": "core_values",
  "topic_type": "coaching",
  "description": "Explore your core values through conversation",
  "model_code": "claude-3-5-sonnet-20241022",
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
  "allowed_parameters": [
    {
      "name": "user_name",
      "type": "string",
      "required": true,
      "description": "User's display name"
    }
  ],
  "created_at": "2024-11-01T10:00:00Z",
  "updated_at": "2024-11-13T15:30:00Z",
  "created_by": "admin_123"
}
```

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
  "topic_type": "coaching",
  "description": "Discover your life's purpose through guided conversation",
  "model_code": "claude-3-5-sonnet-20241022",
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
      "description": "User's display name",
      "validation": {
        "min_length": 1,
        "max_length": 100,
        "pattern": null
      }
    }
  ]
}

**Allowed Parameter Types:**

- `string`: Text value
- `integer`: Whole number
- `float`: Decimal number
- `boolean`: true/false
- `array`: List of values
- `object`: Nested structure

**Parameter Validation Schema:**

```json
{
  "name": "parameter_name",
  "type": "string|integer|float|boolean|array|object",
  "required": true,
  "description": "Human-readable description",
  "validation": {
    "min_length": 1,          // For strings
    "max_length": 100,        // For strings
    "pattern": "^[a-z]+$",    // Regex for strings
    "min_value": 0,           // For numbers
    "max_value": 100,         // For numbers
    "allowed_values": [],     // Enum list
    "default": null           // Default value if not provided
  }
}
```

**Validation Rules:**

| Field | Rules | Allowed Values / Format |
|-------|-------|------------------------|
| `topic_id` | Required, unique, lowercase, snake_case, 3-50 chars | Regex: `^[a-z][a-z0-9_]*$` |
| `topic_name` | Required, 3-100 chars | Any printable characters |
| `category` | Required | Enum: `core_values`, `purpose`, `vision`, `goals`, `strategy`, `kpi`, `custom` |
| `topic_type` | Required | Enum: `coaching`, `assessment`, `analysis`, `kpi` |
| `model_code` | Required, must be valid model code | See "Supported Model Codes" below |
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
- `kpi`: Key performance indicators and metrics
- `custom`: Custom topics not fitting standard categories

**Topic Type Descriptions:**

- `coaching`: Interactive conversational coaching sessions
- `assessment`: One-shot evaluations and assessments
- `analysis`: Deep analytical processing of user data
- `kpi`: KPI calculation and tracking

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
  "model_code": "claude-3-5-haiku-20241022",
  "temperature": 0.5,
  "max_tokens": 1500,
  "is_active": true,
  "display_order": 5
}
```

**Notes:**

- Only include fields you want to update
- Cannot update `topic_id`
- Cannot update `category` or `topic_type` (create new topic instead)
- Cannot update `created_at` or `created_by`

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
  "category": "test",
  "topic_type": "coaching",
  "model_code": "claude-3-5-sonnet-20241022",
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

### 12. Clone Topic

**Purpose:** Create a copy of an existing topic for modification

**Endpoint:**

```http
POST /api/v1/admin/topics/{topic_id}/clone
```

**Request Body:**

```json
{
  "new_topic_id": "core_values_coaching_v2",
  "new_topic_name": "Core Values Coaching v2",
  "copy_prompts": true,
  "is_active": false
}
```

**Validation:**

- `new_topic_id`: Required, must follow topic_id format (snake_case, 3-50 chars)
- `new_topic_name`: Required, 3-100 chars
- `copy_prompts`: Optional, boolean, default true
- `is_active`: Optional, boolean, default false

**Response:**

```json
{
  "topic_id": "core_values_coaching_v2",
  "cloned_from": "core_values_coaching",
  "created_at": "2024-11-13T17:00:00Z",
  "message": "Topic cloned successfully"
}
```

**Status Codes:**

- `201 Created`: Success
- `404 Not Found`: Source topic not found
- `409 Conflict`: New topic ID already exists
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 13. Get Topic Usage Statistics

**Purpose:** View usage metrics for a topic

**Endpoint:**

```http
GET /api/v1/admin/topics/{topic_id}/stats
```

**Query Parameters:**

| Parameter | Type | Required | Default | Description | Format |
|-----------|------|----------|---------|-------------|--------|
| `start_date` | string | No | 30 days ago | ISO 8601 date | `YYYY-MM-DDTHH:mm:ssZ` |
| `end_date` | string | No | now | ISO 8601 date | `YYYY-MM-DDTHH:mm:ssZ` |

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
    "active_conversations": 89,
    "completed_conversations": 1158,
    "average_messages_per_conversation": 12.4,
    "total_tokens_used": 1850000,
    "estimated_cost": 27.75
  },
  "performance": {
    "average_conversation_duration_minutes": 18.5,
    "completion_rate": 0.93,
    "user_satisfaction_rating": 4.7
  }
}
```

**Status Codes:**

- `200 OK`: Success
- `404 Not Found`: Topic not found
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

### 14. Bulk Update Topics

**Purpose:** Update multiple topics at once (e.g., activate/deactivate, change model)

**Endpoint:**

```http
PATCH /api/v1/admin/topics/bulk
```

**Request Body:**

```json
{
  "topic_ids": ["core_values_coaching", "purpose_discovery"],
  "updates": {
    "model_code": "claude-3-5-haiku-20241022",
    "is_active": false
  }
}
```

**Validation:**

- `topic_ids`: Required, array of topic IDs, max 50 topics per request
- `updates`: Required, object containing fields to update
- Updatable fields: `model_code`, `temperature`, `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`, `is_active`, `display_order`, `description`, `topic_name`
- Cannot bulk update: `topic_id`, `category`, `topic_type`, `created_at`, `created_by`

**Response:**

```json
{
  "updated": 2,
  "results": [
    {
      "topic_id": "core_values_coaching",
      "success": true
    },
    {
      "topic_id": "purpose_discovery",
      "success": true
    }
  ]
}
```

**Status Codes:**

- `200 OK`: Success (check individual results)
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Missing or invalid auth token
- `403 Forbidden`: Insufficient permissions

---

## Admin UI Workflows

### Creating a New Topic

1. **GET** `/api/v1/admin/models` - Get available models
2. **POST** `/api/v1/admin/topics` - Create topic (inactive)
3. **POST** `/api/v1/admin/topics/{topic_id}/prompts` - Upload system prompt
4. **POST** `/api/v1/admin/topics/{topic_id}/prompts` - Upload user prompt
5. **POST** `/api/v1/admin/topics/validate` - Validate configuration
6. **PUT** `/api/v1/admin/topics/{topic_id}` - Activate topic

### Editing Prompts

1. **GET** `/api/v1/admin/topics/{topic_id}` - Get topic details
2. **GET** `/api/v1/admin/topics/{topic_id}/prompts/system` - Get current content
3. Edit in UI
4. **PUT** `/api/v1/admin/topics/{topic_id}/prompts/system` - Save changes
5. Cache cleared automatically

### A/B Testing

1. **POST** `/api/v1/admin/topics/{original_id}/clone` - Clone topic
2. **PUT** `/api/v1/admin/topics/{clone_id}/prompts/system` - Modify prompts
3. **PUT** `/api/v1/admin/topics/{clone_id}` - Activate clone
4. **GET** `/api/v1/admin/topics/{original_id}/stats` - Compare metrics
5. **GET** `/api/v1/admin/topics/{clone_id}/stats` - Compare metrics
6. Deactivate losing variant

### Updating Model for All Topics

1. **GET** `/api/v1/admin/topics?category=core_values` - Get topics
2. **PATCH** `/api/v1/admin/topics/bulk` - Update all to new model
3. Monitor performance

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

## Audit Logging

All admin actions are logged:

- User ID and timestamp
- Action performed
- Topic/prompt affected
- Changes made (before/after)
- IP address

Logs accessible via:

```http
GET /api/v1/admin/audit-logs?topic_id={topic_id}
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
| View stats | `admin:topics:stats` |
| Bulk operations | `admin:topics:bulk` |

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
