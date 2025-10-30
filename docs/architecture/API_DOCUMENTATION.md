# LLM Configuration System - API Documentation

**Version**: 1.0.0  
**Last Updated**: October 30, 2025  
**Base Path**: `/api/v1/admin/llm`

---

## Overview

REST API for managing LLM configurations and prompt templates. All endpoints require authentication and admin privileges.

### Authentication

All requests must include a valid JWT token:

```http
Authorization: Bearer <jwt_token>
```

### Common Headers

```http
Content-Type: application/json
Accept: application/json
X-Request-ID: <uuid>
```

---

## Configuration Endpoints

### List Configurations

Retrieve configurations with optional filtering.

**Endpoint**: `GET /configurations`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `interaction_code` | string | No | Filter by interaction |
| `tier` | string | No | Filter by tier (starter/professional/enterprise) |
| `is_active` | boolean | No | Filter by active status |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20, max: 100) |

**Request Example**:

```http
GET /api/v1/admin/llm/configurations?interaction_code=ALIGNMENT_ANALYSIS&is_active=true
```

**Response Example** (200 OK):

```json
{
  "items": [
    {
      "config_id": "config_abc123",
      "interaction_code": "ALIGNMENT_ANALYSIS",
      "template_id": "template_xyz789",
      "model_code": "CLAUDE_3_SONNET",
      "tier": "professional",
      "temperature": 0.7,
      "max_tokens": 4096,
      "is_active": true,
      "created_at": "2025-10-01T10:00:00Z",
      "updated_at": "2025-10-15T14:30:00Z",
      "created_by": "admin_user",
      "effective_from": "2025-10-01T00:00:00Z",
      "effective_until": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### Create Configuration

Create a new LLM configuration.

**Endpoint**: `POST /configurations`

**Request Body**:

```json
{
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "template_id": "template_xyz789",
  "model_code": "CLAUDE_3_SONNET",
  "tier": "professional",
  "temperature": 0.7,
  "max_tokens": 4096,
  "effective_from": "2025-10-30T00:00:00Z",
  "effective_until": null
}
```

**Field Descriptions**:

- `interaction_code` (required): Must exist in INTERACTION_REGISTRY
- `template_id` (required): Must reference active template
- `model_code` (required): Must exist in MODEL_REGISTRY
- `tier` (optional): Target subscription tier (null = default)
- `temperature` (required): 0.0 - 1.0
- `max_tokens` (required): Positive integer
- `effective_from` (required): Start date for configuration
- `effective_until` (optional): End date for configuration

**Response Example** (201 Created):

```json
{
  "config_id": "config_abc123",
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "template_id": "template_xyz789",
  "model_code": "CLAUDE_3_SONNET",
  "tier": "professional",
  "temperature": 0.7,
  "max_tokens": 4096,
  "is_active": true,
  "created_at": "2025-10-30T14:00:00Z",
  "updated_at": "2025-10-30T14:00:00Z",
  "created_by": "admin_user_123",
  "effective_from": "2025-10-30T00:00:00Z",
  "effective_until": null
}
```

**Error Responses**:

- `400 Bad Request`: Invalid request data
- `404 Not Found`: Referenced template/interaction/model not found
- `409 Conflict`: Active configuration already exists for interaction+tier

---

### Get Configuration by ID

Retrieve a specific configuration.

**Endpoint**: `GET /configurations/{config_id}`

**Path Parameters**:

- `config_id`: Configuration identifier

**Response Example** (200 OK):

```json
{
  "config_id": "config_abc123",
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "template_id": "template_xyz789",
  "model_code": "CLAUDE_3_SONNET",
  "tier": "professional",
  "temperature": 0.7,
  "max_tokens": 4096,
  "is_active": true,
  "created_at": "2025-10-01T10:00:00Z",
  "updated_at": "2025-10-15T14:30:00Z",
  "created_by": "admin_user",
  "updated_by": "admin_user",
  "effective_from": "2025-10-01T00:00:00Z",
  "effective_until": null
}
```

**Error Responses**:

- `404 Not Found`: Configuration does not exist

---

### Update Configuration

Update an existing configuration.

**Endpoint**: `PATCH /configurations/{config_id}`

**Request Body** (all fields optional):

```json
{
  "template_id": "template_new456",
  "model_code": "CLAUDE_3_HAIKU",
  "temperature": 0.5,
  "max_tokens": 2048,
  "is_active": true,
  "effective_until": "2025-12-31T23:59:59Z"
}
```

**Response Example** (200 OK):

```json
{
  "config_id": "config_abc123",
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "template_id": "template_new456",
  "model_code": "CLAUDE_3_HAIKU",
  "tier": "professional",
  "temperature": 0.5,
  "max_tokens": 2048,
  "is_active": true,
  "created_at": "2025-10-01T10:00:00Z",
  "updated_at": "2025-10-30T14:30:00Z",
  "created_by": "admin_user",
  "updated_by": "admin_user_123",
  "effective_from": "2025-10-01T00:00:00Z",
  "effective_until": "2025-12-31T23:59:59Z"
}
```

**Error Responses**:

- `400 Bad Request`: Invalid update data
- `404 Not Found`: Configuration or referenced resources not found

---

### Deactivate Configuration

Deactivate a configuration (soft delete).

**Endpoint**: `DELETE /configurations/{config_id}`

**Response Example** (204 No Content)

**Error Responses**:

- `404 Not Found`: Configuration does not exist

---

### Validate Configuration

Validate a configuration against registries.

**Endpoint**: `POST /configurations/{config_id}/validate`

**Response Example** (200 OK):

```json
{
  "valid": true,
  "validation_results": {
    "interaction_code": {
      "valid": true,
      "message": "Interaction exists in registry"
    },
    "model_code": {
      "valid": true,
      "message": "Model exists in registry"
    },
    "template_id": {
      "valid": true,
      "message": "Template exists and is active"
    }
  }
}
```

**Error Response** (200 OK with validation failures):

```json
{
  "valid": false,
  "validation_results": {
    "interaction_code": {
      "valid": false,
      "message": "Interaction 'INVALID_CODE' not found in registry"
    },
    "model_code": {
      "valid": true,
      "message": "Model exists in registry"
    },
    "template_id": {
      "valid": false,
      "message": "Template 'template_xyz' not found or inactive"
    }
  }
}
```

---

## Template Endpoints

### List Templates

Retrieve templates with optional filtering.

**Endpoint**: `GET /templates`

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `interaction_code` | string | No | Filter by interaction |
| `template_code` | string | No | Filter by template code |
| `is_active` | boolean | No | Filter by active status |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20, max: 100) |

**Response Example** (200 OK):

```json
{
  "items": [
    {
      "template_id": "template_xyz789",
      "template_code": "ALIGNMENT_ANALYSIS_V2",
      "interaction_code": "ALIGNMENT_ANALYSIS",
      "name": "Alignment Analysis Template v2",
      "description": "Enhanced goal alignment analysis with value scoring",
      "version": "2.0.0",
      "s3_bucket": "purpose-path-templates",
      "s3_key": "alignment/v2.jinja2",
      "is_active": true,
      "required_parameters": ["goal_text", "purpose", "values"],
      "created_at": "2025-09-15T10:00:00Z",
      "updated_at": "2025-10-01T14:00:00Z",
      "created_by": "admin_user"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### Create Template

Create a new prompt template.

**Endpoint**: `POST /templates`

**Request Body**:

```json
{
  "template_code": "ALIGNMENT_ANALYSIS_V3",
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "name": "Alignment Analysis Template v3",
  "description": "Latest alignment analysis with enhanced scoring",
  "version": "3.0.0",
  "content": "Analyze the goal: {{ goal_text }}\nPurpose: {{ purpose }}\n...",
  "required_parameters": ["goal_text", "purpose", "values"]
}
```

**Field Descriptions**:

- `template_code` (required): Unique template identifier
- `interaction_code` (required): Must exist in INTERACTION_REGISTRY
- `name` (required): Human-readable template name
- `description` (required): Template purpose and usage
- `version` (required): Semantic version (e.g., "1.0.0")
- `content` (required): Jinja2 template content
- `required_parameters` (optional): List of required Jinja2 variables

**Response Example** (201 Created):

```json
{
  "template_id": "template_new123",
  "template_code": "ALIGNMENT_ANALYSIS_V3",
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "name": "Alignment Analysis Template v3",
  "description": "Latest alignment analysis with enhanced scoring",
  "version": "3.0.0",
  "s3_bucket": "purpose-path-templates",
  "s3_key": "alignment/v3.jinja2",
  "is_active": true,
  "required_parameters": ["goal_text", "purpose", "values"],
  "created_at": "2025-10-30T14:00:00Z",
  "updated_at": "2025-10-30T14:00:00Z",
  "created_by": "admin_user_123"
}
```

**Error Responses**:

- `400 Bad Request`: Invalid template content or Jinja2 syntax error
- `409 Conflict`: Template code already exists

---

### Get Template by ID

Retrieve a specific template.

**Endpoint**: `GET /templates/{template_id}`

**Response Example** (200 OK):

```json
{
  "template_id": "template_xyz789",
  "template_code": "ALIGNMENT_ANALYSIS_V2",
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "name": "Alignment Analysis Template v2",
  "description": "Enhanced goal alignment analysis",
  "version": "2.0.0",
  "s3_bucket": "purpose-path-templates",
  "s3_key": "alignment/v2.jinja2",
  "is_active": true,
  "required_parameters": ["goal_text", "purpose", "values"],
  "created_at": "2025-09-15T10:00:00Z",
  "updated_at": "2025-10-01T14:00:00Z",
  "created_by": "admin_user",
  "updated_by": "admin_user"
}
```

---

### Get Template Content

Retrieve the template's Jinja2 content.

**Endpoint**: `GET /templates/{template_id}/content`

**Response Example** (200 OK):

```json
{
  "template_id": "template_xyz789",
  "content": "Analyze the goal: {{ goal_text }}\n\nPurpose: {{ purpose }}\nCore Values: {{ values }}\n\nPlease provide:\n1. Overall alignment score (0-100)\n2. Key strengths\n3. Areas for improvement\n4. Specific recommendations\n\n{% if additional_context %}\nAdditional Context: {{ additional_context }}\n{% endif %}"
}
```

---

### Render Template

Render a template with provided parameters.

**Endpoint**: `POST /templates/{template_id}/render`

**Request Body**:

```json
{
  "parameters": {
    "goal_text": "Increase revenue by 20% in Q4",
    "purpose": "Drive business growth and market expansion",
    "values": "Innovation, Customer Focus, Excellence"
  }
}
```

**Response Example** (200 OK):

```json
{
  "template_id": "template_xyz789",
  "rendered_content": "Analyze the goal: Increase revenue by 20% in Q4\n\nPurpose: Drive business growth and market expansion\nCore Values: Innovation, Customer Focus, Excellence\n\nPlease provide:\n1. Overall alignment score (0-100)\n2. Key strengths\n3. Areas for improvement\n4. Specific recommendations"
}
```

**Error Responses**:

- `400 Bad Request`: Missing required parameters or rendering error
- `404 Not Found`: Template does not exist

---

### Update Template

Update an existing template.

**Endpoint**: `PATCH /templates/{template_id}`

**Request Body** (all fields optional):

```json
{
  "name": "Updated Template Name",
  "description": "Updated description",
  "is_active": false
}
```

**Note**: Template content cannot be updated. Create a new version instead.

**Response Example** (200 OK):

```json
{
  "template_id": "template_xyz789",
  "template_code": "ALIGNMENT_ANALYSIS_V2",
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "name": "Updated Template Name",
  "description": "Updated description",
  "version": "2.0.0",
  "s3_bucket": "purpose-path-templates",
  "s3_key": "alignment/v2.jinja2",
  "is_active": false,
  "required_parameters": ["goal_text", "purpose", "values"],
  "created_at": "2025-09-15T10:00:00Z",
  "updated_at": "2025-10-30T14:30:00Z",
  "created_by": "admin_user",
  "updated_by": "admin_user_123"
}
```

---

### Deactivate Template

Deactivate a template (soft delete).

**Endpoint**: `DELETE /templates/{template_id}`

**Response Example** (204 No Content)

**Error Responses**:

- `404 Not Found`: Template does not exist
- `409 Conflict`: Template is referenced by active configurations

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Configuration validation failed",
    "code": "VALIDATION_FAILED",
    "details": {
      "field": "interaction_code",
      "issue": "Interaction 'INVALID' not found in registry"
    },
    "request_id": "req_abc123xyz"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET/PATCH requests |
| 201 | Created | Successful POST requests |
| 204 | No Content | Successful DELETE requests |
| 400 | Bad Request | Invalid request data or validation failures |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Resource conflict (duplicate, constraint violation) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Rate Limiting

API endpoints are rate-limited to ensure system stability:

- **Admin endpoints**: 100 requests/minute per user
- **Burst allowance**: 20 requests
- **Rate limit headers**:

  ```http
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1698765432
  ```

---

## Versioning

The API uses URL-based versioning: `/api/v1/...`

- Breaking changes result in a new version (v2, v3, etc.)
- Non-breaking changes are added to current version
- Older versions are supported for 12 months after deprecation

---

## Related Documentation

- [Architecture Overview](./LLM_CONFIGURATION_SYSTEM.md)
- [Data Flow Diagrams](./DATA_FLOW_DIAGRAMS.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
