# .NET Backend API - Integration Requirements

## Document Purpose
This document specifies the exact REST API endpoints and SQS message queues that the .NET Backend API must implement to integrate with the Integration Service.

**Version**: 1.0.0  
**Date**: November 11, 2025

---

## Integration Service Endpoints (For .NET Backend Consumption)

The Integration Service exposes the following endpoints that the .NET Backend can call.

### Base URL
```
https://integration.dev.purposepath.app/api/v1
```

Environment-specific:
- Dev: `https://integration.dev.purposepath.app/api/v1`
- Staging: `https://integration.staging.purposepath.app/api/v1`
- Production: `https://integration.purposepath.app/api/v1`

### Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer {jwt_token}
```

JWT token validated against secret in AWS Secrets Manager: `purposepath-jwt-secret-{environment}`

---

### Endpoint 1: Manual Measure Execution

**Method**: `POST`  
**Path**: `/measure-integrations/{integration_id}/execute`  
**Purpose**: Manually trigger Measure execution without waiting for scheduled time

#### Request
**Headers**:
- `Authorization: Bearer {jwt_token}` (required)
- `Content-Type: application/json`

**Path Parameters**:
- `integration_id` (string, required): Measure integration identifier

#### Response (202 Accepted)
```json
{
  "execution_id": "string",
  "status": "queued",
  "message": "Execution queued successfully"
}
```

#### Response Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| execution_id | string | Yes | Unique execution identifier for tracking |
| status | string | Yes | Always "queued" for successful requests |
| message | string | Yes | Human-readable confirmation message |

#### Error Responses
- `400 Bad Request`: Invalid integration_id
- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Integration not found
- `500 Internal Server Error`: Execution failed to queue

---

### Endpoint 2: Validate Connection

**Method**: `POST`  
**Path**: `/connections/validate`  
**Purpose**: Validate connection credentials before saving

#### Request
**Headers**:
- `Authorization: Bearer {jwt_token}` (required)
- `Content-Type: application/json`

**Body**:
```json
{
  "system_type": "string",
  "credentials": {
    "key": "value"
  }
}
```

#### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| system_type | string | Yes | "salesforce", "hubspot", "quickbooks", etc. |
| credentials | object | Yes | System-specific credentials to validate |

#### Response (200 OK)
```json
{
  "valid": true,
  "latency_ms": 245,
  "connection_details": {
    "instance_url": "https://company.salesforce.com",
    "user_info": "user@company.com"
  }
}
```

#### Response Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| valid | boolean | Yes | Whether credentials are valid |
| latency_ms | integer | Yes | Connection test latency in milliseconds |
| error_message | string | No | Error message if validation failed |
| connection_details | object | No | Additional connection information if successful |

#### Error Responses
- `400 Bad Request`: Invalid request format or missing fields
- `401 Unauthorized`: Invalid or missing JWT token
- `500 Internal Server Error`: Validation service error

---

### Endpoint 3: Extract Parameter Values

**Method**: `POST`  
**Path**: `/parameters/extract`  
**Purpose**: Extract available parameter values from external system

#### Request
**Headers**:
- `Authorization: Bearer {jwt_token}` (required)
- `Content-Type: application/json`

**Body**:
```json
{
  "connection_id": "string",
  "system_type": "string",
  "parameter_name": "string",
  "context": {
    "key": "value"
  }
}
```

#### Request Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| connection_id | string | Yes | Connection identifier for credentials |
| system_type | string | Yes | External system type |
| parameter_name | string | Yes | Parameter to extract (e.g., "accounts", "projects") |
| context | object | No | Additional context for parameter extraction |

#### Response (200 OK)
```json
{
  "parameter_name": "accounts",
  "values": [
    {
      "id": "001xx000003DGb2AAG",
      "name": "Acme Corporation",
      "description": "Enterprise Account"
    }
  ],
  "total_count": 150
}
```

#### Response Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| parameter_name | string | Yes | Name of extracted parameter |
| values | array | Yes | Array of available parameter values |
| values[].id | string | Yes | Parameter value identifier |
| values[].name | string | Yes | Human-readable parameter name |
| values[].description | string | No | Optional description |
| total_count | integer | Yes | Total number of available values |

#### Error Responses
- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Connection not found
- `500 Internal Server Error`: Parameter extraction failed

---

### Endpoint 4: Get Execution Status

**Method**: `GET`  
**Path**: `/executions/{execution_id}/status`  
**Purpose**: Get current status of a Measure execution

#### Request
**Headers**:
- `Authorization: Bearer {jwt_token}` (required)

**Path Parameters**:
- `execution_id` (string, required): Execution identifier from manual execution

#### Response (200 OK)
```json
{
  "execution_id": "string",
  "integration_id": "string",
  "status": "completed",
  "started_at": "2025-11-11T10:30:00Z",
  "completed_at": "2025-11-11T10:30:45Z",
  "duration_ms": 45000,
  "result_value": 125000.50,
  "metadata": {
    "tokens_used": 1500,
    "cost": 0.045,
    "llm_model": "claude-sonnet-4"
  }
}
```

#### Response Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| execution_id | string | Yes | Execution identifier |
| integration_id | string | Yes | Integration identifier |
| status | string | Yes | "queued", "running", "completed", "failed", "timeout" |
| started_at | string | No | ISO8601 datetime when execution started |
| completed_at | string | No | ISO8601 datetime when execution completed |
| duration_ms | integer | No | Execution duration in milliseconds |
| result_value | number | No | Measure value (if successful) |
| error_message | string | No | Error message (if failed) |
| metadata | object | No | Execution metadata |

#### Error Responses
- `401 Unauthorized`: Invalid or missing JWT token
- `404 Not Found`: Execution not found
- `500 Internal Server Error`: Status retrieval failed

---

### Endpoint 5: List Available LLM Models

**Method**: `GET`  
**Path**: `/llm-models`  
**Purpose**: Get list of available LLM models for Measure execution

#### Request
**Headers**:
- `Authorization: Bearer {jwt_token}` (required)

#### Response (200 OK)
```json
{
  "models": [
    {
      "id": "claude-sonnet-4",
      "name": "Claude Sonnet 4",
      "provider": "anthropic",
      "description": "Balanced performance and cost",
      "cost_per_token": 0.00003,
      "max_tokens": 200000,
      "supports_tools": true
    }
  ]
}
```

#### Response Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| models | array | Yes | Array of available LLM models |
| models[].id | string | Yes | Model identifier for API calls |
| models[].name | string | Yes | Human-readable model name |
| models[].provider | string | Yes | "anthropic", "openai", "google", "amazon" |
| models[].description | string | Yes | Model description and capabilities |
| models[].cost_per_token | number | Yes | Cost per token in USD |
| models[].max_tokens | integer | Yes | Maximum tokens per request |
| models[].supports_tools | boolean | Yes | Whether model supports MCP tools |

#### Error Responses
- `401 Unauthorized`: Invalid or missing JWT token
- `500 Internal Server Error`: Model list retrieval failed

---

### Usage Examples

#### Manual Measure Execution
```bash
curl -X POST \
  https://integration.dev.purposepath.app/api/v1/measure-integrations/int-123/execute \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json"
```

#### Connection Validation
```bash
curl -X POST \
  https://integration.dev.purposepath.app/api/v1/connections/validate \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "system_type": "salesforce",
    "credentials": {
      "instance_url": "https://company.salesforce.com",
      "access_token": "00D..."
    }
  }'
```

#### Parameter Extraction
```bash
curl -X POST \
  https://integration.dev.purposepath.app/api/v1/parameters/extract \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "conn-123",
    "system_type": "salesforce",
    "parameter_name": "accounts"
  }'
```

---

## REST API Endpoints to Implement

### Base URL
```
https://api.dev.purposepath.app/integration/api/v1
```

Environment-specific:
- Dev: `https://api.dev.purposepath.app/integration/api/v1`
- Staging: `https://api.staging.purposepath.app/integration/api/v1`
- Production: `https://api.purposepath.app/integration/api/v1`

**Note**: This is the .NET Backend API base URL, not the Integration Service URL.

### Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer {service_token}
```

Service token stored in AWS Secrets Manager: `purposepath-backend-api-token-{environment}`

---

## Endpoint 1: Get Measure Integration Configuration

**Method**: `GET`  
**Path**: `/measure-integrations/{integration_id}/config`  
**Purpose**: Retrieve complete configuration for executing a Measure integration

### Request
**Headers**:
- `Authorization: Bearer {token}` (required)
- `Content-Type: application/json`

**Path Parameters**:
- `integration_id` (string, required): Unique Measure integration identifier

### Response (200 OK)
```json
{
  "integration_id": "string",
  "measure_id": "string",
  "connection_id": "string",
  "template_key": "string",
  "parameter_values": {
    "key": "value"
  },
  "frequency": "string",
  "is_point_in_time": boolean,
  "system_type": "string",
  "llm_model": "string"
}
```

### Response Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| integration_id | string | Yes | Measure integration identifier |
| measure_id | string | Yes | Measure identifier |
| connection_id | string | Yes | Connection identifier for retrieving credentials |
| template_key | string | Yes | Template topic identifier (e.g., "salesforce_revenue") |
| parameter_values | object | Yes | Key-value pairs for template rendering |
| frequency | string | Yes | "daily", "weekly", "monthly", "quarterly", "yearly" |
| is_point_in_time | boolean | Yes | true = single date, false = date range |
| system_type | string | Yes | "salesforce", "hubspot", "quickbooks", etc. |
| llm_model | string | No | LLM model ID (optional, defaults to Claude Sonnet) |

### Error Responses
- `404 Not Found`: Integration does not exist
- `401 Unauthorized`: Invalid or missing authentication
- `500 Internal Server Error`: Server error

---

## Endpoint 2: Get Connection Credentials

**Method**: `GET`  
**Path**: `/connections/{connection_id}/credentials`  
**Purpose**: Retrieve decrypted credentials for connecting to external systems

### Request
**Headers**:
- `Authorization: Bearer {token}` (required)
- `Content-Type: application/json`

**Path Parameters**:
- `connection_id` (string, required): Unique connection identifier

### Response (200 OK)
Returns a dynamic JSON object with system-specific credentials.

**Salesforce Example**:
```json
{
  "instance_url": "https://company.salesforce.com",
  "access_token": "00D...",
  "refresh_token": "5Aep...",
  "client_id": "3MVG...",
  "client_secret": "ABC..."
}
```

**HubSpot Example**:
```json
{
  "api_key": "pat-na1-...",
  "portal_id": "12345678"
}
```

**QuickBooks Example**:
```json
{
  "access_token": "eyJlbmMiOi...",
  "refresh_token": "L011...",
  "realm_id": "9130353234567890",
  "client_id": "AB...",
  "client_secret": "CD..."
}
```

### Security Requirements
- Credentials MUST be encrypted at rest
- Credentials MUST be decrypted only when requested
- HTTPS/TLS 1.2+ required
- Access MUST be logged for audit

### Error Responses
- `404 Not Found`: Connection does not exist
- `401 Unauthorized`: Invalid or missing authentication
- `500 Internal Server Error`: Server error

---

## Endpoint 3: Get Active Integrations

**Method**: `GET`  
**Path**: `/measure-integrations/active`  
**Purpose**: Retrieve all active Measure integrations for scheduled execution

### Request
**Headers**:
- `Authorization: Bearer {token}` (required)
- `Content-Type: application/json`

**Query Parameters** (all optional):
- `frequency` (string): Filter by frequency
- `tenant_id` (string): Filter by tenant
- `limit` (integer): Max results (default: 100)
- `offset` (integer): Pagination offset (default: 0)

### Response (200 OK)
```json
{
  "integrations": [
    {
      "integration_id": "string",
      "measure_id": "string",
      "tenant_id": "string",
      "frequency": "string",
      "schedule_time": "HH:MM:SS",
      "timezone": "string",
      "is_active": boolean,
      "last_execution": "ISO8601 datetime",
      "next_execution": "ISO8601 datetime"
    }
  ],
  "total_count": integer,
  "has_more": boolean
}
```

### Response Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| integrations | array | Yes | Array of active integration objects |
| integration_id | string | Yes | Integration identifier |
| measure_id | string | Yes | Measure identifier |
| tenant_id | string | Yes | Tenant identifier |
| frequency | string | Yes | Execution frequency |
| schedule_time | string | Yes | Time of day to execute (HH:MM:SS) |
| timezone | string | Yes | Timezone for schedule_time |
| is_active | boolean | Yes | Whether integration is active |
| last_execution | string | No | ISO8601 datetime of last execution |
| next_execution | string | No | ISO8601 datetime of next scheduled execution |
| total_count | integer | Yes | Total number of active integrations |
| has_more | boolean | Yes | Whether more results exist |

### Error Responses
- `401 Unauthorized`: Invalid or missing authentication
- `500 Internal Server Error`: Server error

---

## SQS Message Queues to Consume

### Queue Naming Convention
```
purposepath-{queue-type}-{environment}
```

### AWS Region
All queues are in `us-east-1` (configurable per environment)

### Required IAM Permissions
```json
{
  "Effect": "Allow",
  "Action": [
    "sqs:ReceiveMessage",
    "sqs:DeleteMessage",
    "sqs:GetQueueUrl",
    "sqs:GetQueueAttributes"
  ],
  "Resource": "arn:aws:sqs:us-east-1:*:purposepath-*"
}
```

---

## Queue 1: Measure Results

**Queue Name**: `purposepath-measure-results-{environment}`  
**Purpose**: Receive successful Measure execution results

### Message Format
```json
{
  "measure_id": "string",
  "tenant_id": "string",
  "value": number,
  "execution_id": "string",
  "metadata": {
    "tokens_used": integer,
    "cost": number,
    "execution_time_ms": integer,
    "llm_model": "string",
    "tools_called": ["string"]
  }
}
```

### Message Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| measure_id | string | Yes | Measure identifier |
| tenant_id | string | Yes | Tenant identifier |
| value | number | Yes | Calculated Measure value (decimal/float) |
| execution_id | string | Yes | Unique execution identifier |
| metadata | object | Yes | Execution metadata |
| metadata.tokens_used | integer | Yes | LLM tokens consumed |
| metadata.cost | number | Yes | Execution cost in USD |
| metadata.execution_time_ms | integer | No | Duration in milliseconds |
| metadata.llm_model | string | No | LLM model used |
| metadata.tools_called | array | No | List of MCP tools invoked |

### Processing Requirements
- Store Measure value with timestamp
- Associate with tenant and Measure
- Track execution metadata for cost analysis
- Update Measure dashboard/charts
- Trigger any downstream workflows

---

## Queue 2: Notifications

**Queue Name**: `purposepath-notifications-{environment}`  
**Purpose**: Receive error and alert notifications

### Message Format
```json
{
  "tenant_id": "string",
  "measure_id": "string",
  "integration_id": "string",
  "notification_type": "string",
  "error_message": "string",
  "severity": "string",
  "suggested_action": "string"
}
```

### Message Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| tenant_id | string | Yes | Tenant identifier |
| measure_id | string | Yes | Measure identifier |
| integration_id | string | Yes | Integration identifier |
| notification_type | string | Yes | Type of notification (see types below) |
| error_message | string | Yes | Human-readable error message |
| severity | string | Yes | "low", "medium", "high", "critical" |
| suggested_action | string | No | Recommended action for user |

### Notification Types
- `connection_failed`: Connection to external system failed
- `authentication_failed`: Authentication/credentials invalid
- `token_expired`: OAuth token expired, needs refresh
- `rate_limit_exceeded`: API rate limit hit
- `data_extraction_failed`: Failed to extract Measure value
- `timeout`: Execution exceeded timeout
- `consecutive_failures`: Multiple consecutive failures
- `system_error`: Internal system error

### Processing Requirements
- Create notification record in database
- Send notification to user (email, in-app, etc.)
- Update integration status if needed
- Track failure patterns for alerting

---

## Queue 3: Execution Status

**Queue Name**: `purposepath-execution-status-{environment}`  
**Purpose**: Receive execution status updates

### Message Format
```json
{
  "execution_id": "string",
  "integration_id": "string",
  "status": "string",
  "duration_ms": integer,
  "result_value": number,
  "error_message": "string"
}
```

### Message Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| execution_id | string | Yes | Unique execution identifier |
| integration_id | string | Yes | Integration identifier |
| status | string | Yes | "success", "failed", "timeout" |
| duration_ms | integer | No | Execution duration in milliseconds |
| result_value | number | No | Measure value (if successful) |
| error_message | string | No | Error message (if failed) |

### Processing Requirements
- Update execution log/history
- Track execution metrics (duration, success rate)
- Update integration last_execution timestamp
- Calculate next_execution timestamp
- Monitor for performance degradation

---

## Message Processing Best Practices

### Long Polling
Use long polling (WaitTimeSeconds=20) to reduce empty receives and costs.

### Batch Processing
Process messages in batches (MaxNumberOfMessages=10) for efficiency.

### Visibility Timeout
Set appropriate visibility timeout (300 seconds recommended) to prevent duplicate processing.

### Dead Letter Queues
Each queue has a corresponding DLQ:
- `purposepath-measure-results-{env}-dlq`
- `purposepath-notifications-{env}-dlq`
- `purposepath-execution-status-{env}-dlq`

Messages are sent to DLQ after 3 failed processing attempts.

### Error Handling
- Catch and log all processing errors
- Delete message only after successful processing
- Let failed messages retry or go to DLQ
- Monitor DLQ depth and alert on messages

---

## Error Response Format

All API endpoints should return errors in this format:

```json
{
  "error": "Human-readable error message",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional context"
  }
}
```

### Standard HTTP Status Codes
- `200 OK`: Success
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Environment Configuration

### Environment Variables Required
- `BACKEND_API_URL`: Base URL for Backend API
- `AWS_REGION`: AWS region for SQS queues (default: us-east-1)
- `ENVIRONMENT`: Environment name (dev, staging, prod)

### Secrets in AWS Secrets Manager
- `purposepath-backend-api-token-{env}`: Service authentication token

---

## Testing Checklist

### Integration Service Endpoints (Consumption)
- [ ] POST /measure-integrations/{id}/execute triggers manual execution
- [ ] POST /connections/validate validates Salesforce credentials
- [ ] POST /connections/validate validates HubSpot credentials
- [ ] POST /connections/validate validates QuickBooks credentials
- [ ] POST /parameters/extract retrieves account list from Salesforce
- [ ] POST /parameters/extract retrieves projects from other systems
- [ ] GET /executions/{id}/status returns execution status
- [ ] GET /llm-models returns list of available models
- [ ] All Integration Service endpoints require valid JWT authentication
- [ ] All Integration Service endpoints return 401 for invalid/missing JWT

### REST API Endpoints (Implementation)
- [ ] GET /measure-integrations/{id}/config returns valid configuration
- [ ] GET /measure-integrations/{id}/config returns 404 for non-existent integration
- [ ] GET /connections/{id}/credentials returns decrypted credentials
- [ ] GET /connections/{id}/credentials returns 404 for non-existent connection
- [ ] GET /measure-integrations/active returns list of active integrations
- [ ] All endpoints require valid authentication
- [ ] All endpoints return 401 for invalid/missing auth

### SQS Message Consumers
- [ ] Measure results queue consumer processes messages correctly
- [ ] Notifications queue consumer creates notifications
- [ ] Execution status queue consumer updates execution logs
- [ ] Failed messages are retried appropriately
- [ ] Messages are deleted after successful processing
- [ ] DLQ monitoring is configured

---

**Document Version**: 1.0.0  
**Last Updated**: November 11, 2025
