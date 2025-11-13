# Admin Template Management API Specification

**Version:** 1.0  
**Base URL:** `https://api.dev.purposepath.app/coaching/api/v1/admin`  
**Authentication:** JWT (Bearer token)

---

## Table of Contents

1. [Enums & Constants](#enums--constants)
2. [Topic Management Endpoints](#topic-management-endpoints)
3. [Prompt Content Endpoints](#prompt-content-endpoints)
4. [Data Models](#data-models)
5. [Validation Rules](#validation-rules)

---

## Enums & Constants

### TopicType

```typescript
enum TopicType {
  CONVERSATION_COACHING = "conversation_coaching",
  SINGLE_SHOT = "single_shot",
  KPI_SYSTEM = "kpi_system"
}
```

### Category

```typescript
enum Category {
  COACHING = "coaching",
  ANALYSIS = "analysis",
  STRATEGY = "strategy",
  KPI = "kpi"
}
```

### PromptType

```typescript
enum PromptType {
  SYSTEM = "system",
  USER = "user",
  ASSISTANT = "assistant",
  FUNCTION = "function"
}
```

### ParameterType

```typescript
enum ParameterType {
  STRING = "string",
  NUMBER = "number",
  BOOLEAN = "boolean",
  ARRAY = "array",
  OBJECT = "object"
}
```

---

## Topic Management Endpoints

### 1. List All Topics

**Endpoint:** `GET /prompts`

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic_type | string (TopicType) | No | Filter by topic type |

**Request Example:**
```http
GET /admin/prompts?topic_type=conversation_coaching
Authorization: Bearer {jwt_token}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": [
    {
      "topic_id": "core_values",
      "topic_name": "Core Values",
      "topic_type": "conversation_coaching",
      "category": "coaching",
      "description": "Discover your core values through guided conversation",
      "display_order": 1,
      "is_active": true,
      "available_prompts": ["system", "user"],
      "allowed_parameters": [
        {
          "name": "user_name",
          "type": "string",
          "required": true,
          "description": "User's display name"
        },
        {
          "name": "user_id",
          "type": "string",
          "required": true
        },
        {
          "name": "conversation_history",
          "type": "array",
          "required": false
        }
      ],
      "config": {
        "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "supports_streaming": true,
        "max_turns": 20
      },
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-20T14:00:00Z"
    }
  ]
}
```

### 2. Create New Topic

**Endpoint:** `POST /prompts`

**Note:** Only KPI-System topics can be created. Coaching topics are seeded at deployment.

**Request Body:**
```json
{
  "topic_id": "revenue_salesforce",
  "topic_name": "Revenue Growth - Salesforce",
  "topic_type": "kpi_system",
  "category": "kpi",
  "description": "Analyze revenue KPI from Salesforce",
  "allowed_parameters": [
    {
      "name": "kpi_value",
      "type": "number",
      "required": true,
      "description": "Current KPI value"
    },
    {
      "name": "threshold",
      "type": "number",
      "required": true,
      "description": "Target threshold"
    },
    {
      "name": "time_period",
      "type": "string",
      "required": true,
      "description": "Time period for analysis"
    }
  ],
  "config": {
    "default_model": "anthropic.claude-3-haiku-20240307-v1:0",
    "supports_streaming": false
  },
  "display_order": 100,
  "is_active": true
}
```

**Constraints:**
- `topic_id`: Lowercase alphanumeric + underscores, max 64 chars, must be unique
- `topic_name`: Max 128 chars
- `topic_type`: Must be `kpi_system` for creation
- `category`: Must be valid Category enum value
- `allowed_parameters`: At least 1 parameter required

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "topic_id": "revenue_salesforce",
    "topic_name": "Revenue Growth - Salesforce",
    "message": "Topic created successfully. Create prompts next.",
    "created_at": "2025-01-20T15:30:00Z"
  }
}
```

**Error Response:** `400 Bad Request`
```json
{
  "success": false,
  "error": {
    "code": "INVALID_TOPIC_TYPE",
    "message": "Only kpi_system topics can be created via API"
  }
}
```

### 3. Update Topic Metadata

**Endpoint:** `PUT /prompts/{topic_id}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic_id | string | Yes | Topic identifier |

**Request Body:**
```json
{
  "topic_name": "Revenue Growth - Salesforce (Updated)",
  "description": "Updated description",
  "allowed_parameters": [
    {
      "name": "kpi_value",
      "type": "number",
      "required": true,
      "description": "Current KPI value"
    },
    {
      "name": "threshold",
      "type": "number",
      "required": true
    }
  ],
  "config": {
    "default_model": "anthropic.claude-3-haiku-20240307-v1:0",
    "supports_streaming": false
  },
  "display_order": 105,
  "is_active": true
}
```

**Note:** Cannot update `topic_id` or `topic_type`. All fields are optional.

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "topic_id": "revenue_salesforce",
    "topic_name": "Revenue Growth - Salesforce (Updated)",
    "updated_at": "2025-01-20T16:00:00Z"
  }
}
```

---

## Prompt Content Endpoints

### 4. Get Prompt Content

**Endpoint:** `GET /prompts/{topic_id}/{prompt_type}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic_id | string | Yes | Topic identifier |
| prompt_type | string (PromptType) | Yes | Type of prompt (system, user, etc.) |

**Request Example:**
```http
GET /admin/prompts/core_values/system
Authorization: Bearer {jwt_token}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "topic_id": "core_values",
    "prompt_type": "system",
    "content": "You are an expert life coach specializing in helping individuals discover their core values.\n\n## Your Approach\n- Ask thoughtful, open-ended questions\n- Listen actively and reflect back key themes\n\n## Context\nUser: {{user_name}}\nUser ID: {{user_id}}",
    "allowed_parameters": [
      {
        "name": "user_name",
        "type": "string",
        "required": true
      },
      {
        "name": "user_id",
        "type": "string",
        "required": true
      }
    ],
    "s3_location": {
      "bucket": "purposepath-templates-dev",
      "key": "prompts/core_values/system.md"
    },
    "updated_at": "2025-01-20T14:00:00Z",
    "updated_by": "admin@purposepath.ai"
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "success": false,
  "error": {
    "code": "PROMPT_NOT_FOUND",
    "message": "Prompt type 'system' not found for topic 'core_values'"
  }
}
```

### 5. Create Prompt

**Endpoint:** `POST /prompts/{topic_id}/{prompt_type}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic_id | string | Yes | Topic identifier (must exist) |
| prompt_type | string (PromptType) | Yes | Type of prompt to create |

**Request Body:**
```json
{
  "content": "You are an AI analyzing revenue KPI data from Salesforce.\n\n## Analysis Guidelines\n- Compare against threshold: {{threshold}}\n- Analyze trends over {{time_period}}\n- Provide actionable recommendations\n\n## Current Data\nKPI Value: {{kpi_value}}"
}
```

**Constraints:**
- `content`: Required, min 10 chars, max 50,000 chars
- Must use valid parameter placeholders matching topic's `allowed_parameters`
- Parameter format: `{{parameter_name}}`

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "topic_id": "revenue_salesforce",
    "prompt_type": "system",
    "s3_location": {
      "bucket": "purposepath-templates-dev",
      "key": "prompts/revenue_salesforce/system.md"
    },
    "created_at": "2025-01-20T15:45:00Z",
    "created_by": "admin@purposepath.ai"
  }
}
```

**Error Response:** `400 Bad Request` (Invalid parameter)
```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "Parameter 'invalid_param' used in content is not in allowed_parameters list",
    "details": {
      "invalid_parameters": ["invalid_param"],
      "allowed_parameters": ["kpi_value", "threshold", "time_period"]
    }
  }
}
```

### 6. Update Prompt

**Endpoint:** `PUT /prompts/{topic_id}/{prompt_type}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic_id | string | Yes | Topic identifier |
| prompt_type | string (PromptType) | Yes | Type of prompt to update |

**Request Body:**
```json
{
  "content": "Updated prompt content...\n\nUser: {{user_name}}\nContext: {{conversation_history}}"
}
```

**Note:** This overwrites the existing prompt. No versioning is maintained in the data model (S3 versioning can be enabled separately).

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "topic_id": "core_values",
    "prompt_type": "system",
    "updated_at": "2025-01-20T16:15:00Z",
    "updated_by": "admin@purposepath.ai"
  }
}
```

### 7. Delete Prompt

**Endpoint:** `DELETE /prompts/{topic_id}/{prompt_type}`

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic_id | string | Yes | Topic identifier |
| prompt_type | string (PromptType) | Yes | Type of prompt to delete |

**Request Example:**
```http
DELETE /admin/prompts/revenue_salesforce/user
Authorization: Bearer {jwt_token}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "topic_id": "revenue_salesforce",
    "prompt_type": "user",
    "message": "Prompt deleted successfully",
    "deleted_at": "2025-01-20T16:30:00Z"
  }
}
```

**Note:** Deletes the prompt from S3 and removes it from the topic's `prompts` array.

---

## Data Models

### AllowedParameter

```typescript
interface AllowedParameter {
  name: string;              // Parameter name (snake_case)
  type: ParameterType;       // string | number | boolean | array | object
  required: boolean;         // Whether parameter is required
  description?: string;      // Optional description
  default?: any;             // Optional default value
}
```

### TopicConfig

```typescript
interface TopicConfig {
  default_model: string;          // e.g., "anthropic.claude-3-sonnet-20240229-v1:0"
  supports_streaming: boolean;    // Whether topic supports streaming responses
  max_turns?: number;             // Max conversation turns (for conversation_coaching)
  temperature?: number;           // LLM temperature (0.0 - 1.0)
  max_tokens?: number;            // Max response tokens
}
```

### Topic (Full Object)

```typescript
interface Topic {
  topic_id: string;
  topic_name: string;
  topic_type: TopicType;
  category: Category;
  description?: string;
  display_order: number;
  is_active: boolean;
  allowed_parameters: AllowedParameter[];
  available_prompts: PromptType[];  // List of prompt types that exist
  config: TopicConfig;
  created_at: string;               // ISO 8601 datetime
  created_by?: string;
  updated_at: string;               // ISO 8601 datetime
}
```

### PromptDetail

```typescript
interface PromptDetail {
  topic_id: string;
  prompt_type: PromptType;
  content: string;                  // Markdown content with {{parameter}} placeholders
  allowed_parameters: AllowedParameter[];
  s3_location: {
    bucket: string;
    key: string;
  };
  updated_at: string;               // ISO 8601 datetime
  updated_by: string;               // Email of admin who last updated
}
```

---

## Validation Rules

### Topic ID
- **Pattern:** `^[a-z0-9_]+$` (lowercase alphanumeric + underscores)
- **Min Length:** 3
- **Max Length:** 64
- **Must be unique**

### Topic Name
- **Min Length:** 3
- **Max Length:** 128

### Prompt Content
- **Min Length:** 10
- **Max Length:** 50,000
- **Parameter Syntax:** `{{parameter_name}}`
- **Validation:** All parameters used must exist in `allowed_parameters`

### Parameter Names
- **Pattern:** `^[a-z_][a-z0-9_]*$` (snake_case)
- **Min Length:** 2
- **Max Length:** 64
- **Reserved:** Cannot start with underscore followed by underscore (`__`)

### Display Order
- **Type:** Integer
- **Min:** 0
- **Max:** 9999
- **Default:** 100

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TOPIC_NOT_FOUND` | 404 | Topic with given ID does not exist |
| `PROMPT_NOT_FOUND` | 404 | Prompt type does not exist for topic |
| `INVALID_TOPIC_TYPE` | 400 | Invalid or disallowed topic type |
| `INVALID_PARAMETER` | 400 | Prompt uses parameter not in allowed list |
| `DUPLICATE_TOPIC_ID` | 409 | Topic ID already exists |
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT token |
| `FORBIDDEN` | 403 | User lacks admin permissions |

---

## Usage Examples

### Creating a Complete KPI Topic

**Step 1: Create Topic**
```http
POST /admin/prompts
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "topic_id": "churn_hubspot",
  "topic_name": "Customer Churn - HubSpot",
  "topic_type": "kpi_system",
  "category": "kpi",
  "description": "Analyze customer churn metrics from HubSpot",
  "allowed_parameters": [
    {"name": "churn_rate", "type": "number", "required": true},
    {"name": "threshold", "type": "number", "required": true},
    {"name": "period", "type": "string", "required": true}
  ],
  "config": {
    "default_model": "anthropic.claude-3-haiku-20240307-v1:0",
    "supports_streaming": false
  },
  "is_active": true
}
```

**Step 2: Create System Prompt**
```http
POST /admin/prompts/churn_hubspot/system
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "content": "You are an AI analyzing customer churn data.\n\nChurn Rate: {{churn_rate}}%\nThreshold: {{threshold}}%\nPeriod: {{period}}"
}
```

**Step 3: Create User Prompt**
```http
POST /admin/prompts/churn_hubspot/user
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "content": "Analyze the churn rate and provide recommendations."
}
```

### Updating Existing Coaching Prompt

```http
PUT /admin/prompts/core_values/system
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "content": "You are an expert life coach.\n\nUser: {{user_name}}\nID: {{user_id}}\n\nGuide them through core values discovery."
}
```

---

## Notes

1. **Authentication:** All endpoints require valid JWT token with admin role
2. **Content-Type:** All POST/PUT requests must use `application/json`
3. **Idempotency:** PUT operations are idempotent (safe to retry)
4. **Rate Limiting:** 100 requests per minute per user
5. **Coaching Topics:** Cannot create new coaching topics via API (seeded at deployment)
6. **Parameter Validation:** Prompt content is validated against allowed_parameters on create/update
7. **S3 Versioning:** Not exposed via API, but can be enabled at infrastructure level if needed

---

**End of Specification**
