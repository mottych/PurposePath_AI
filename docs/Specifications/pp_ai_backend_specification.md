# PurposePath AI Coaching Service Backend Specification (pp_ai)

## Overview

This document specifies the required endpoints and functionality to be added to the PurposePath AI Coaching Service (pp_ai) to support AI management features in the Admin Portal. These endpoints will extend the existing coaching service with prompt template management, LLM model configuration, and AI system administration capabilities.

## AI Model Management

### List Available LLM Providers and Models

**Endpoint:** `GET /api/v1/admin/ai/models`

**Description:** Get all supported LLM providers and their available models.

**Response:**
```json
{
  "success": true,
  "data": {
    "providers": [
      {
        "name": "bedrock",
        "displayName": "Amazon Bedrock",
        "isActive": true,
        "models": [
          {
            "id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "name": "Claude 3.5 Sonnet",
            "provider": "Anthropic",
            "version": "20241022-v2",
            "capabilities": [
              "text_generation",
              "conversation",
              "analysis"
            ],
            "maxTokens": 200000,
            "costPer1kTokens": {
              "input": 0.003,
              "output": 0.015
            },
            "isActive": true,
            "isDefault": true
          },
          {
            "id": "anthropic.claude-3-haiku-20240307-v1:0",
            "name": "Claude 3 Haiku",
            "provider": "Anthropic",
            "version": "20240307-v1",
            "capabilities": [
              "text_generation",
              "conversation"
            ],
            "maxTokens": 200000,
            "costPer1kTokens": {
              "input": 0.00025,
              "output": 0.00125
            },
            "isActive": true,
            "isDefault": false
          }
        ]
      }
    ],
    "defaultProvider": "bedrock",
    "defaultModel": "anthropic.claude-3-5-sonnet-20241022-v2:0"
  }
}
```

### Update Model Configuration

**Endpoint:** `PUT /api/v1/admin/ai/models/{modelId}`

**Description:** Update model configuration and availability.

**Request:**
```json
{
  "isActive": true,
  "isDefault": false,
  "costPer1kTokens": {
    "input": 0.003,
    "output": 0.015
  },
  "reason": "Updated pricing from provider"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "previousConfig": {
      "isActive": true,
      "isDefault": true,
      "costPer1kTokens": {
        "input": 0.0025,
        "output": 0.012
      }
    },
    "newConfig": {
      "isActive": true,
      "isDefault": false,
      "costPer1kTokens": {
        "input": 0.003,
        "output": 0.015
      }
    },
    "updatedAt": "2024-01-15T00:00:00Z",
    "updatedBy": "admin@purposepath.ai"
  }
}
```

---

## Prompt Template Management

### List Coaching Topics

**Endpoint:** `GET /api/v1/admin/ai/topics`

**Description:** Get all available coaching topics that have prompt templates.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "topic": "core_values",
      "displayName": "Core Values Discovery",
      "description": "Helps users identify and articulate their core business values",
      "category": "onboarding",
      "hasTemplates": true,
      "templateCount": 3,
      "latestVersion": "v2.1",
      "lastUpdated": "2024-01-15T00:00:00Z"
    },
    {
      "topic": "purpose",
      "displayName": "Purpose Definition",
      "description": "Guides users through defining their business purpose",
      "category": "onboarding",
      "hasTemplates": true,
      "templateCount": 2,
      "latestVersion": "v1.5",
      "lastUpdated": "2024-01-10T00:00:00Z"
    }
  ]
}
```

### List Prompt Template Versions

**Endpoint:** `GET /api/v1/admin/ai/prompts/{topic}/versions`

**Description:** Get all versions of prompt templates for a specific topic.

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "core_values",
    "versions": [
      {
        "version": "v2.1",
        "isLatest": true,
        "createdAt": "2024-01-15T00:00:00Z",
        "createdBy": "admin@purposepath.ai",
        "description": "Improved conversation flow and better examples",
        "templateId": "tmpl_core_values_v2_1",
        "status": "active"
      },
      {
        "version": "v2.0",
        "isLatest": false,
        "createdAt": "2024-01-01T00:00:00Z",
        "createdBy": "admin@purposepath.ai",
        "description": "Major update with new coaching methodology",
        "templateId": "tmpl_core_values_v2_0",
        "status": "archived"
      }
    ]
  }
}
```

### Get Prompt Template

**Endpoint:** `GET /api/v1/admin/ai/prompts/{topic}/{version}`

**Description:** Get detailed prompt template content for editing.

**Response:**
```json
{
  "success": true,
  "data": {
    "templateId": "tmpl_core_values_v2_1",
    "topic": "core_values",
    "version": "v2.1",
    "isLatest": true,
    "metadata": {
      "title": "Core Values Discovery Coach",
      "description": "Helps users identify and articulate their core business values",
      "category": "onboarding",
      "tags": ["values", "foundation", "onboarding"]
    },
    "systemPrompt": "You are an expert business coach specializing in helping entrepreneurs and business leaders discover their core values...",
    "userPromptTemplate": "I want to discover my core business values. Here's some information about my business:\n\nBusiness Name: {{business_name}}\nIndustry: {{industry}}\nBusiness Description: {{business_description}}\n\nPlease help me identify my core values through a structured conversation.",
    "parameters": [
      {
        "name": "business_name",
        "displayName": "Business Name",
        "type": "string",
        "required": true,
        "description": "The name of the user's business"
      },
      {
        "name": "industry",
        "displayName": "Industry",
        "type": "string",
        "required": false,
        "description": "The industry or sector the business operates in"
      },
      {
        "name": "business_description",
        "displayName": "Business Description",
        "type": "text",
        "required": true,
        "description": "A brief description of what the business does"
      }
    ],
    "conversationFlow": {
      "maxTurns": 10,
      "completionCriteria": [
        "User has identified at least 3 core values",
        "Each value has been explained and validated",
        "User confirms satisfaction with the identified values"
      ]
    },
    "examples": [
      {
        "input": "Business Name: TechStart Inc.\nIndustry: Software Development\nBusiness Description: We create mobile apps for small businesses",
        "expectedOutput": "I'd love to help you discover your core values for TechStart Inc. Let's start by exploring what drives your passion for creating mobile apps for small businesses..."
      }
    ],
    "createdAt": "2024-01-15T00:00:00Z",
    "createdBy": "admin@purposepath.ai",
    "lastModifiedAt": "2024-01-15T00:00:00Z",
    "lastModifiedBy": "admin@purposepath.ai"
  }
}
```

### Create Prompt Template Version

**Endpoint:** `POST /api/v1/admin/ai/prompts/{topic}/versions`

**Description:** Create a new version of a prompt template.

**Request:**
```json
{
  "version": "v2.2",
  "sourceVersion": "v2.1",
  "description": "Enhanced with industry-specific examples",
  "metadata": {
    "title": "Core Values Discovery Coach",
    "description": "Helps users identify and articulate their core business values with industry-specific guidance",
    "category": "onboarding",
    "tags": ["values", "foundation", "onboarding", "industry-specific"]
  },
  "systemPrompt": "You are an expert business coach specializing in helping entrepreneurs and business leaders discover their core values. You have deep knowledge of various industries and can provide industry-specific guidance...",
  "userPromptTemplate": "I want to discover my core business values. Here's some information about my business:\n\nBusiness Name: {{business_name}}\nIndustry: {{industry}}\nBusiness Description: {{business_description}}\n\nPlease help me identify my core values through a structured conversation, taking into account industry best practices.",
  "parameters": [
    {
      "name": "business_name",
      "displayName": "Business Name",
      "type": "string",
      "required": true,
      "description": "The name of the user's business"
    },
    {
      "name": "industry",
      "displayName": "Industry",
      "type": "string",
      "required": true,
      "description": "The industry or sector the business operates in"
    },
    {
      "name": "business_description",
      "displayName": "Business Description",
      "type": "text",
      "required": true,
      "description": "A brief description of what the business does"
    }
  ],
  "conversationFlow": {
    "maxTurns": 12,
    "completionCriteria": [
      "User has identified at least 3 core values",
      "Each value has been explained and validated",
      "Values align with industry best practices",
      "User confirms satisfaction with the identified values"
    ]
  },
  "examples": [
    {
      "input": "Business Name: TechStart Inc.\nIndustry: Software Development\nBusiness Description: We create mobile apps for small businesses",
      "expectedOutput": "I'd love to help you discover your core values for TechStart Inc. In the software development industry, successful companies often emphasize values like innovation, reliability, and customer-centricity. Let's explore what drives your passion for creating mobile apps..."
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "templateId": "tmpl_core_values_v2_2",
    "topic": "core_values",
    "version": "v2.2",
    "createdAt": "2024-01-15T00:00:00Z",
    "createdBy": "admin@purposepath.ai",
    "status": "draft"
  }
}
```

### Update Prompt Template

**Endpoint:** `PUT /api/v1/admin/ai/prompts/{topic}/{version}`

**Description:** Update an existing prompt template version.

**Request:** Same structure as create, with optional fields.

**Response:**
```json
{
  "success": true,
  "data": {
    "templateId": "tmpl_core_values_v2_2",
    "topic": "core_values",
    "version": "v2.2",
    "updatedAt": "2024-01-15T00:00:00Z",
    "updatedBy": "admin@purposepath.ai",
    "changes": [
      "Updated system prompt",
      "Added new parameter: industry",
      "Modified conversation flow criteria"
    ]
  }
}
```

### Set Latest Version

**Endpoint:** `POST /api/v1/admin/ai/prompts/{topic}/{version}/set-latest`

**Description:** Mark a specific version as the latest/active version.

**Request:**
```json
{
  "reason": "Testing completed successfully, ready for production"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "core_values",
    "previousLatestVersion": "v2.1",
    "newLatestVersion": "v2.2",
    "updatedAt": "2024-01-15T00:00:00Z",
    "updatedBy": "admin@purposepath.ai"
  }
}
```

### Test Prompt Template

**Endpoint:** `POST /api/v1/admin/ai/prompts/{topic}/{version}/test`

**Description:** Test a prompt template with sample data before deployment.

**Request:**
```json
{
  "testParameters": {
    "business_name": "Test Company Inc.",
    "industry": "Technology",
    "business_description": "We develop AI-powered solutions for healthcare"
  },
  "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "testId": "test_12345",
    "renderedPrompt": {
      "system": "You are an expert business coach specializing in helping entrepreneurs...",
      "user": "I want to discover my core business values. Here's some information about my business:\n\nBusiness Name: Test Company Inc.\nIndustry: Technology\nBusiness Description: We develop AI-powered solutions for healthcare\n\nPlease help me identify my core values through a structured conversation, taking into account industry best practices."
    },
    "aiResponse": "I'd love to help you discover your core values for Test Company Inc. In the healthcare technology industry, successful companies often emphasize values like patient safety, innovation, data privacy, and accessibility...",
    "tokenUsage": {
      "inputTokens": 245,
      "outputTokens": 156,
      "totalTokens": 401
    },
    "cost": {
      "inputCost": 0.000735,
      "outputCost": 0.00234,
      "totalCost": 0.003075
    },
    "responseTime": 1.23,
    "testedAt": "2024-01-15T00:00:00Z"
  }
}
```

### Delete Prompt Template Version

**Endpoint:** `DELETE /api/v1/admin/ai/prompts/{topic}/{version}`

**Description:** Delete a specific version of a prompt template.

**Request:**
```json
{
  "reason": "Version contains errors and should not be used",
  "confirmDeletion": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "topic": "core_values",
    "version": "v2.0",
    "deletedAt": "2024-01-15T00:00:00Z",
    "deletedBy": "admin@purposepath.ai"
  }
}
```

---

## Prompt Parameter Management

### List Available Parameters

**Endpoint:** `GET /api/v1/admin/ai/parameters`

**Description:** Get all available parameters that can be used in prompt templates.

**Response:**
```json
{
  "success": true,
  "data": {
    "categories": [
      {
        "name": "business_info",
        "displayName": "Business Information",
        "parameters": [
          {
            "name": "business_name",
            "displayName": "Business Name",
            "type": "string",
            "description": "The name of the user's business",
            "example": "Acme Corporation"
          },
          {
            "name": "industry",
            "displayName": "Industry",
            "type": "string",
            "description": "The industry or sector the business operates in",
            "example": "Technology"
          }
        ]
      },
      {
        "name": "user_info",
        "displayName": "User Information",
        "parameters": [
          {
            "name": "first_name",
            "displayName": "First Name",
            "type": "string",
            "description": "The user's first name",
            "example": "John"
          }
        ]
      }
    ]
  }
}
```

---

## AI Usage Analytics

### Get AI Usage Statistics

**Endpoint:** `GET /api/v1/admin/ai/usage`

**Description:** Get AI usage statistics and costs.

**Query Parameters:**
- `dateFrom` (string, optional) - ISO date, default: 30 days ago
- `dateTo` (string, optional) - ISO date, default: now
- `groupBy` (string, optional) - Group by: day, week, month, model, topic

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalRequests": 15420,
      "totalTokens": 2450000,
      "totalCost": 156.75,
      "averageResponseTime": 1.45,
      "period": {
        "from": "2024-01-01T00:00:00Z",
        "to": "2024-01-31T23:59:59Z"
      }
    },
    "byModel": [
      {
        "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "modelName": "Claude 3.5 Sonnet",
        "requests": 12500,
        "inputTokens": 1800000,
        "outputTokens": 450000,
        "totalCost": 132.50,
        "averageResponseTime": 1.52
      }
    ],
    "byTopic": [
      {
        "topic": "core_values",
        "displayName": "Core Values Discovery",
        "requests": 3200,
        "totalCost": 42.30,
        "averageResponseTime": 1.38
      }
    ],
    "dailyUsage": [
      {
        "date": "2024-01-15",
        "requests": 520,
        "tokens": 85000,
        "cost": 5.25
      }
    ]
  }
}
```

### Get Model Performance Metrics

**Endpoint:** `GET /api/v1/admin/ai/models/{modelId}/metrics`

**Description:** Get detailed performance metrics for a specific model.

**Query Parameters:**
- `dateFrom` (string, optional)
- `dateTo` (string, optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "modelName": "Claude 3.5 Sonnet",
    "period": {
      "from": "2024-01-01T00:00:00Z",
      "to": "2024-01-31T23:59:59Z"
    },
    "metrics": {
      "totalRequests": 12500,
      "successfulRequests": 12485,
      "failedRequests": 15,
      "successRate": 99.88,
      "averageResponseTime": 1.52,
      "medianResponseTime": 1.35,
      "p95ResponseTime": 2.45,
      "averageInputTokens": 144,
      "averageOutputTokens": 36,
      "totalCost": 132.50,
      "costPerRequest": 0.0106
    },
    "errorBreakdown": [
      {
        "errorType": "rate_limit_exceeded",
        "count": 8,
        "percentage": 53.33
      },
      {
        "errorType": "timeout",
        "count": 4,
        "percentage": 26.67
      }
    ]
  }
}
```

---

## Conversation Management

### List Active Conversations

**Endpoint:** `GET /api/v1/admin/ai/conversations`

**Description:** Get list of active AI coaching conversations for monitoring.

**Query Parameters:**
- `page` (int, default: 1)
- `pageSize` (int, default: 50)
- `topic` (string, optional) - Filter by coaching topic
- `status` (string, optional) - Filter by status: active, completed, abandoned
- `tenantId` (string, optional) - Filter by tenant

**Response:**
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "conversationId": "conv_12345",
        "tenantId": "tenant_abc",
        "tenantName": "Acme Corp",
        "userId": "user_xyz",
        "topic": "core_values",
        "topicDisplayName": "Core Values Discovery",
        "status": "active",
        "startedAt": "2024-01-15T10:00:00Z",
        "lastMessageAt": "2024-01-15T10:15:00Z",
        "messageCount": 6,
        "tokenUsage": 1250,
        "estimatedCost": 0.045,
        "templateVersion": "v2.1"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 50,
      "totalCount": 150,
      "totalPages": 3
    }
  }
}
```

### Get Conversation Details

**Endpoint:** `GET /api/v1/admin/ai/conversations/{conversationId}`

**Description:** Get detailed conversation history and metadata.

**Response:**
```json
{
  "success": true,
  "data": {
    "conversationId": "conv_12345",
    "tenantId": "tenant_abc",
    "tenantName": "Acme Corp",
    "userId": "user_xyz",
    "userEmail": "john@acme.com",
    "topic": "core_values",
    "topicDisplayName": "Core Values Discovery",
    "status": "active",
    "startedAt": "2024-01-15T10:00:00Z",
    "lastMessageAt": "2024-01-15T10:15:00Z",
    "templateVersion": "v2.1",
    "parameters": {
      "business_name": "Acme Corp",
      "industry": "Manufacturing",
      "business_description": "We manufacture eco-friendly packaging solutions"
    },
    "messages": [
      {
        "messageId": "msg_1",
        "role": "user",
        "content": "I want to discover my core business values...",
        "timestamp": "2024-01-15T10:00:00Z",
        "tokenCount": 45
      },
      {
        "messageId": "msg_2",
        "role": "assistant",
        "content": "I'd love to help you discover your core values for Acme Corp...",
        "timestamp": "2024-01-15T10:00:15Z",
        "tokenCount": 156,
        "modelUsed": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "responseTime": 1.23,
        "cost": 0.0045
      }
    ],
    "totalTokens": 1250,
    "totalCost": 0.045,
    "completionStatus": {
      "isCompleted": false,
      "completionPercentage": 60,
      "criteriaProgress": [
        {
          "criteria": "User has identified at least 3 core values",
          "status": "in_progress",
          "progress": "2 of 3 values identified"
        }
      ]
    }
  }
}
```

---

## Error Handling

All endpoints should return consistent error responses:

```json
{
  "success": false,
  "error": "Detailed error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "validation error details"
  }
}
```

Common HTTP status codes:
- 200: Success
- 400: Bad Request (validation errors)
- 401: Unauthorized (invalid admin token)
- 403: Forbidden (not authorized for AI management)
- 404: Not Found (template/model not found)
- 409: Conflict (version already exists)
- 500: Internal Server Error

## Implementation Notes

1. **S3 Integration**: Prompt templates should continue to be stored in S3 but accessed through the service layer, not directly by the frontend.

2. **Versioning**: All prompt template operations should maintain proper versioning and prevent accidental overwrites of active templates.

3. **Testing**: The test endpoint should use a separate model instance or sandbox environment to avoid affecting production usage statistics.

4. **Caching**: Frequently accessed templates should be cached to improve performance.

5. **Audit Logging**: All administrative changes to prompts and models should be logged for audit purposes.

6. **Validation**: Prompt templates should be validated for proper parameter syntax and required fields before saving.

7. **Rollback**: Consider implementing rollback functionality to quickly revert to previous template versions if issues are discovered.