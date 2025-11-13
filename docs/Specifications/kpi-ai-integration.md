# KPI-AI Integration: Template Management Enhancement

**Document Version:** 1.0  
**Last Updated:** November 11, 2025  
**Status:** Proposed Architecture  

---

## Executive Summary

This document outlines the architectural enhancement to support MCP (Model Context Protocol) agent integration with the PurposePath AI template management system. The enhancement enables external systems (specifically the .NET backend) to manage and retrieve prompt templates for KPI-System combinations.

### Key Objectives

- Enable template management for KPI-System combinations
- Support service-to-service authentication for MCP integration
- Maintain backward compatibility with existing coaching templates
- Provide flexible parameter schema management
- Enable external system integration without code deployments

---

## Current State

### What We Have

- ✅ Topic-based coaching templates (enum: `core_values`, `purpose`, `vision`, `goals`)
- ✅ S3-based storage with version management
- ✅ Admin UI for template design
- ✅ JWT-based admin authentication
- ✅ Template CRUD operations

### Limitations

- ❌ Templates tied to predefined enum topics
- ❌ No service-to-service authentication
- ❌ No parameter schema validation
- ❌ Cannot retrieve templates by arbitrary ID
- ❌ No integration with external systems

---

## Proposed Solution

### Architecture Decision: Unified Template System

Implement a single template management system handling both coaching and KPI-System templates with:
- Type-based routing and storage
- Service-to-service API authentication
- Dynamic parameter schema definitions
- Integration endpoints for MCP retrieval
- Backward-compatible API

---

## Data Model

### Single DynamoDB Table (Simplified)

#### `purposepath-llm-prompts-{env}`

**Purpose:** Single source of truth for ALL LLM prompts with embedded configuration and prompt references

**Schema:**
```python
{
    # Primary Key
    "topic_id": "core_values",              # PK - unique topic identifier
    
    # Basic Info
    "topic_name": "Core Values",            # Display name
    "topic_type": "conversation_coaching",  # conversation_coaching | single_shot | kpi_system
    "category": "coaching",                 # coaching | analysis | strategy | kpi
    "description": "Discover core values",  # Help text
    "display_order": 1,                     # Sort order in UI
    "is_active": true,                      # Enable/disable topic
    
    # Parameter Schema (for validation)
    "allowed_parameters": [
        {
            "name": "user_name",
            "type": "string",
            "required": true,
            "description": "User's display name"
        },
        {
            "name": "conversation_history",
            "type": "array",
            "required": false,
            "description": "Previous messages in conversation"
        }
    ],
    
    # Prompts Array (flexible, no versioning)
    "prompts": [
        {
            "prompt_type": "system",        # system | user | assistant | function
            "s3_bucket": "purposepath-templates-dev",
            "s3_key": "prompts/core_values/system.md",
            "updated_at": "2025-01-20T14:00:00Z",
            "updated_by": "admin@purposepath.ai"
        },
        {
            "prompt_type": "user",
            "s3_bucket": "purposepath-templates-dev",
            "s3_key": "prompts/core_values/user.md",
            "updated_at": "2025-01-15T10:00:00Z",
            "updated_by": "admin@purposepath.ai"
        }
    ],
    
    # Configuration
    "config": {
        "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "supports_streaming": true,
        "max_turns": 20                     # For conversation types
    },
    
    # Audit
    "created_at": "2025-01-15T10:00:00Z",
    "created_by": "admin@purposepath.ai",
    "updated_at": "2025-01-20T14:00:00Z"
}
```

**Indexes:**
1. Primary Key: `topic_id`
2. `type-index` - GSI on `topic_type` for filtering (enables `/admin/prompts?topic_type=conversation_coaching`)
3. `category-index` - GSI on `category` for grouping

**Key Design Decisions:**
- ✅ **No separate reference table** - 1:1 relationship, just adds complexity
- ✅ **No separate metadata table** - S3 keys stored directly in prompts array
- ✅ **No versioning** - Admin always updates current, S3 versioning can be enabled if history needed
- ✅ **Flexible prompt types** - Array supports system, user, assistant, function, or future types
- ✅ **Parameters embedded** - Validation schema stored with topic
- ✅ **Independent prompt updates** - Each prompt type can be updated separately

**Example Records:**

```python
# Conversation Coaching Topic
{
    "topic_id": "core_values",
    "topic_name": "Core Values",
    "topic_type": "conversation_coaching",
    "category": "coaching",
    "allowed_parameters": [
        {"name": "user_name", "type": "string", "required": true},
        {"name": "user_id", "type": "string", "required": true},
        {"name": "tenant_id", "type": "string", "required": true},
        {"name": "conversation_history", "type": "array", "required": false}
    ],
    "prompts": [
        {
            "prompt_type": "system",
            "s3_bucket": "purposepath-templates-dev",
            "s3_key": "prompts/core_values/system.md",
            "updated_at": "2025-01-20T14:00:00Z",
            "updated_by": "admin@purposepath.ai"
        },
        {
            "prompt_type": "user",
            "s3_bucket": "purposepath-templates-dev",
            "s3_key": "prompts/core_values/user.md",
            "updated_at": "2025-01-20T14:00:00Z",
            "updated_by": "admin@purposepath.ai"
        }
    ],
    "config": {
        "default_model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "supports_streaming": true,
        "max_turns": 20
    },
    "display_order": 1,
    "is_active": true
}

# Single-Shot Analysis Topic
{
    "topic_id": "alignment_analysis",
    "topic_name": "Alignment Analysis",
    "topic_type": "single_shot",
    "category": "analysis",
    "allowed_parameters": [
        {"name": "user_values", "type": "array", "required": true},
        {"name": "goal_description", "type": "string", "required": true}
    ],
    "prompts": [
        {
            "prompt_type": "system",
            "s3_bucket": "purposepath-templates-dev",
            "s3_key": "prompts/alignment_analysis/system.md",
            "updated_at": "2025-01-15T10:00:00Z",
            "updated_by": "admin@purposepath.ai"
        }
    ],
    "config": {
        "default_model": "anthropic.claude-3-haiku-20240307-v1:0",
        "supports_streaming": false
    },
    "display_order": 10,
    "is_active": true
}

# KPI System Topic
{
    "topic_id": "revenue_salesforce",
    "topic_name": "Revenue Growth - Salesforce",
    "topic_type": "kpi_system",
    "category": "kpi",
    "allowed_parameters": [
        {"name": "kpi_value", "type": "number", "required": true},
        {"name": "threshold", "type": "number", "required": true},
        {"name": "time_period", "type": "string", "required": true},
        {"name": "historical_data", "type": "array", "required": false}
    ],
    "prompts": [
        {
            "prompt_type": "system",
            "s3_bucket": "purposepath-templates-dev",
            "s3_key": "prompts/revenue_salesforce/system.md",
            "updated_at": "2025-01-18T09:00:00Z",
            "updated_by": "admin@purposepath.ai"
        },
        {
            "prompt_type": "user",
            "s3_bucket": "purposepath-templates-dev",
            "s3_key": "prompts/revenue_salesforce/user.md",
            "updated_at": "2025-01-18T09:00:00Z",
            "updated_by": "admin@purposepath.ai"
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

### S3 Storage

**Bucket:** `purposepath-templates-{env}`

**Directory Structure (Simplified - by topic and prompt type):**

```
purposepath-templates-dev/
└── prompts/
    ├── core_values/
    │   ├── system.md
    │   └── user.md
    │
    ├── purpose/
    │   ├── system.md
    │   └── user.md
    │
    ├── alignment_analysis/
    │   └── system.md
    │
    └── revenue_salesforce/
        ├── system.md
        └── user.md
```

**Key Points:**
- ✅ **No versioning** - Each prompt file is current version only
- ✅ **Markdown format** - Human-readable, easy to edit
- ✅ **Organized by topic_id** - Natural grouping
- ✅ **Separate files per prompt type** - Independent updates
- ✅ **Simple paths** - `prompts/{topic_id}/{prompt_type}.md`
- ✅ **Optional S3 versioning** - Can enable S3 versioning transparently if history needed

**Prompt File Format (Markdown):**

Prompts are stored as plain markdown for readability:

```markdown
# System Prompt: Core Values Discovery

You are an expert life coach specializing in helping individuals discover their core values.

## Your Approach
- Ask thoughtful, open-ended questions
- Listen actively and reflect back key themes
- Help users articulate what truly matters to them

## Guidelines
- Be empathetic and non-judgmental
- Encourage deep reflection
- Validate user insights

## Context
User: {{user_name}}
Previous conversation: {{conversation_history}}
```

**Answer to Question 2: System & User Prompts**

System and user prompts are stored in **separate files** per prompt type. This approach:
- ✅ **Independent updates** - Update system prompt without touching user prompt
- ✅ **Flexible prompt types** - Support system, user, assistant, function, or future types
- ✅ **Simpler updates** - Admin updates one file at a time
- ✅ **Reduced conflicts** - No need to coordinate changes across prompt types
- ✅ **Optional prompts** - Single-shot may only need system prompt

---

## Admin Workflow

### Coaching Topics Workflow

Coaching topics are **seeded at deployment** from the existing enum:

**Step 1: List All Topics (with Optional Filter)**

```http
GET /api/v1/admin/prompts?topic_type=conversation_coaching
```

Response:
```json
{
  "data": [
    {
      "topic_id": "core_values",
      "topic_name": "Core Values",
      "topic_type": "conversation_coaching",
      "available_prompts": ["system", "user"],
      "allowed_parameters": [
        {"name": "user_name", "type": "string", "required": true},
        {"name": "conversation_history", "type": "array", "required": false}
      ]
    }
  ]
}
```

**Step 2: Get Specific Prompt for Editing**

```http
GET /api/v1/admin/prompts/core_values/system
```

Response:
```json
{
  "data": {
    "topic_id": "core_values",
    "prompt_type": "system",
    "content": "You are an expert coach helping users...",
    "allowed_parameters": [...],
    "updated_at": "2025-01-20T14:00:00Z",
    "updated_by": "admin@purposepath.ai"
  }
}
```

**Step 3: Update Prompt**

```http
PUT /api/v1/admin/prompts/core_values/system
Body: {
  "content": "Updated system prompt..."
}
```

Backend:
1. Loads topic record from DynamoDB
2. Validates content against `allowed_parameters`
3. Saves to S3: `prompts/core_values/system.md` (overwrites)
4. Updates `prompts` array in DynamoDB with new `updated_at` and `updated_by`

### KPI-System Topics Workflow

KPI topics are **created on-demand** by admin:

**Step 1: Create New KPI Topic**

```http
POST /api/v1/admin/prompts
Body: {
  "topic_id": "revenue_salesforce",
  "topic_name": "Revenue Growth - Salesforce",
  "topic_type": "kpi_system",
  "category": "kpi",
  "allowed_parameters": [
    {"name": "kpi_value", "type": "number", "required": true},
    {"name": "threshold", "type": "number", "required": true}
  ]
}
```

Response:
```json
{
  "data": {
    "topic_id": "revenue_salesforce",
    "topic_name": "Revenue Growth - Salesforce",
    "message": "Topic created. Now create prompts for this topic."
  }
}
```

**Step 2: Admin Stores topic_id in .NET System**

Admin copies `topic_id` and stores it in the .NET KPI configuration:

```csharp
// In .NET system
var kpiConfig = new KpiSystemConfig {
    SystemName = "Salesforce",
    KpiName = "Revenue Growth",
    AITopicId = "revenue_salesforce",  // Store this!
    Threshold = 100000
};
```

**Step 3: Create System Prompt**

```http
POST /api/v1/admin/prompts/revenue_salesforce/system
Body: {
  "content": "You are an AI analyzing revenue KPI..."
}
```

**Step 4: Create User Prompt (Optional)**

```http
POST /api/v1/admin/prompts/revenue_salesforce/user
Body: {
  "content": "Analyze revenue showing {{kpi_value}}..."
}
```

### Key Workflow Benefits

- ✅ **No breaking changes** - User-facing endpoints unchanged
- ✅ **Simple CRUD** - Standard REST operations on topics and prompts
- ✅ **Type filtering** - Admin UI can filter by topic_type
- ✅ **Independent updates** - Update system prompt without touching user prompt
- ✅ **No versioning complexity** - Current state only, S3 versioning available if needed

---

## Service Layer (Backward Compatibility)

### No Breaking Changes for User-Facing Endpoints

User-facing conversation endpoints remain unchanged:

```http
POST /api/v1/conversations
GET  /api/v1/conversations/{conversation_id}
POST /api/v1/conversations/{conversation_id}/messages
```

### Service Abstraction

The `PromptService` abstracts the new data model internally:

**Current Interface (Unchanged):**
```python
# Calling code - NO CHANGES NEEDED
template = await prompt_service.get_template(topic="core_values")
```

**New Implementation (Internal Changes Only):**
```python
class PromptService:
    async def get_template(self, topic: str) -> PromptTemplate:
        """Get template - abstracts topic lookup internally."""
        
        # 1. Load topic record from DynamoDB
        topic_record = await self.topic_repo.get(topic)
        
        # 2. Load all prompts from S3
        prompts = {}
        for prompt_info in topic_record.prompts:
            content = await self.s3_client.get_object(
                Bucket=prompt_info.s3_bucket,
                Key=prompt_info.s3_key
            )
            prompts[prompt_info.prompt_type] = content
        
        # 3. Return template object
        return PromptTemplate(
            topic=topic,
            system_prompt=prompts.get("system"),
            user_prompt_template=prompts.get("user"),
            parameters=topic_record.allowed_parameters
        )
    
    async def get_prompt(self, topic: str, prompt_type: str) -> str:
        """Get specific prompt type (new method for admin)."""
        topic_record = await self.topic_repo.get(topic)
        
        for prompt_info in topic_record.prompts:
            if prompt_info.prompt_type == prompt_type:
                return await self.s3_client.get_object(
                    Bucket=prompt_info.s3_bucket,
                    Key=prompt_info.s3_key
                )
        
        raise PromptNotFoundError(topic, prompt_type)
```

**Benefits:**
- ✅ **Zero breaking changes** - Existing calling code works unchanged
- ✅ **Simple interface** - Callers don't need to know about data model
- ✅ **Flexible backend** - Can change storage without affecting callers
- ✅ **Easy testing** - Mock topic repo and S3 client

### Benefits of Unified Topics Table

**Why this approach is superior:**

**1. Unified Template Management**
- ✅ Single table for ALL LLM prompts (conversation + single-shot + KPI)
- ✅ Consistent management UI across all prompt types
- ✅ Same workflow for editing any template
- ✅ Reduced code duplication

**2. Flexibility**
- ✅ Add new topic types without schema changes (just add new `topic_type` value)
- ✅ Dynamic topic management - no code changes to add topics
- ✅ Easy to categorize and filter (coaching, analysis, strategy, KPI)

**3. Developer Experience**
- ✅ Service layer abstracts complexity: `get_template(topic, version)` works for all types
- ✅ No need to know if topic is conversation vs single-shot
- ✅ Consistent API across all prompt types

**4. Future-Proof**
- ✅ Easy to add metadata (model preferences, streaming support, etc.)
- ✅ Can add new categories without breaking changes
- ✅ Supports advanced features (A/B testing, personalization, etc.)

**Example Use Cases:**
```python
# Works for all topic types - same interface
coaching_template = await prompt_service.get_template("core_values", "latest")
analysis_template = await prompt_service.get_template("alignment_analysis", "latest")
kpi_template = await prompt_service.get_template("revenue_salesforce", "latest")
```

---

## Authentication

### Dual Authentication System

#### 1. JWT Authentication (Existing)
For admin users managing templates through UI.

**Header:** `Authorization: Bearer {jwt_token}`

#### 2. API Key Authentication (NEW)
For service-to-service calls (MCP server, .NET backend).

**Header:** `X-Api-Key: {api_key}`

**Implementation:**
```python
# coaching/src/api/middleware/service_auth.py

async def verify_service_token(
    x_api_key: str = Header(..., description="Service API key")
) -> dict:
    """Verify service-to-service API key."""
    settings = get_settings()
    
    # Get key from Secrets Manager
    secret_name = f"purposepath-backend-api-token-{settings.stage}"
    client = get_secretsmanager_client(settings.aws_region)
    response = client.get_secret_value(SecretId=secret_name)
    expected_key = json.loads(response["SecretString"])["api_key"]
    
    # Constant-time comparison
    if not secrets.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {"service_name": "mcp_integration", "role": "system"}
```

**Secret Structure in AWS Secrets Manager:**

Name: `purposepath-backend-api-token-{env}`

Value:
```json
{
  "api_key": "ppath_svc_prod_a1b2c3d4e5f6g7h8...",
  "created_at": "2025-01-15T10:00:00Z",
  "description": "Backend API integration token",
  "version": "v1",
  "rotation_schedule": "90_days"
}
```

**Generate API Key:**
```bash
# Create secret
aws secretsmanager create-secret \
  --name purposepath-backend-api-token-dev \
  --secret-string '{
    "api_key": "ppath_svc_dev_'$(openssl rand -hex 24)'",
    "created_at": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

---

## API Design

### Admin Endpoints (JWT Auth)

**Base:** `/api/v1/admin/`

#### Topic Management

```http
# List all prompts/topics with optional type filter
GET    /admin/prompts?topic_type={type}
       Query: topic_type (optional: conversation_coaching | single_shot | kpi_system)
       Response: List of topics with metadata (NO prompt content)
       
       Response Example:
       {
         "data": [
           {
             "topic_id": "core_values",
             "topic_name": "Core Values",
             "topic_type": "conversation_coaching",
             "category": "coaching",
             "available_prompts": ["system", "user"],
             "allowed_parameters": [
               {"name": "user_name", "type": "string", "required": true}
             ],
             "is_active": true
           }
         ]
       }

# Create new topic (KPI-System only, coaching topics are seeded)
POST   /admin/prompts
       Body: CreateTopicRequest
       Response: Created topic
       
       Request Example:
       {
         "topic_id": "revenue_salesforce",
         "topic_name": "Revenue Growth - Salesforce",
         "topic_type": "kpi_system",
         "category": "kpi",
         "allowed_parameters": [
           {"name": "kpi_value", "type": "number", "required": true}
         ]
       }

# Update topic metadata/parameters
PUT    /admin/prompts/{topic_id}
       Path: topic_id
       Body: UpdateTopicRequest
       Response: Updated topic
```

#### Prompt Content Management

```http
# Get specific prompt content for editing
GET    /admin/prompts/{topic_id}/{prompt_type}
       Path: topic_id (e.g., "core_values")
       Path: prompt_type (e.g., "system" | "user" | "assistant")
       Response: Prompt content + metadata
       
       Response Example:
       {
         "data": {
           "topic_id": "core_values",
           "prompt_type": "system",
           "content": "You are an expert coach...",
           "allowed_parameters": [...],
           "updated_at": "2025-01-20T14:00:00Z",
           "updated_by": "admin@purposepath.ai"
         }
       }

# Create new prompt type for existing topic
POST   /admin/prompts/{topic_id}/{prompt_type}
       Path: topic_id
       Path: prompt_type
       Body: { "content": "..." }
       Response: Created prompt
       
       Request Example:
       {
         "content": "You are an AI analyzing revenue KPI..."
       }

# Update prompt content (overwrites)
PUT    /admin/prompts/{topic_id}/{prompt_type}
       Path: topic_id
       Path: prompt_type
       Body: { "content": "..." }
       Response: Updated prompt
       
       Request Example:
       {
         "content": "Updated system prompt..."
       }

# Delete prompt type
DELETE /admin/prompts/{topic_id}/{prompt_type}
       Path: topic_id
       Path: prompt_type
       Response: Success confirmation
```

### System-to-System Endpoints (API Key Auth)

**Base:** `/api/v1/prompts/`

```http
# Get all prompt content for a topic (for LLM consumption)
GET    /prompts/{topic_id}
       Header: X-Api-Key
       Path: topic_id
       Response: All prompts for the topic (NO parameters)
       
       Response Example:
       {
         "data": {
           "topic_id": "core_values",
           "prompts": {
             "system": "You are an expert coach...",
             "user": "Help {{user_name}} discover..."
           }
         }
       }

# Batch get multiple topics
POST   /prompts/batch
       Header: X-Api-Key
       Body: { "topic_ids": [...] }
       Response: Map of topic_id to prompts
       
       Request Example:
       {
         "topic_ids": ["core_values", "purpose", "revenue_salesforce"]
       }
       
       Response Example:
       {
         "data": {
           "core_values": {
             "prompts": { "system": "...", "user": "..." }
           },
           "purpose": {
             "prompts": { "system": "...", "user": "..." }
           },
           "revenue_salesforce": {
             "prompts": { "system": "...", "user": "..." }
           }
         }
       }
```

**Example Usage:**
```bash
# Get single topic prompts
curl -X GET \
  "https://api.dev.purposepath.app/coaching/api/v1/prompts/revenue_salesforce" \
  -H "X-Api-Key: ppath_svc_dev_abc123..."

# Batch retrieval
curl -X POST \
  "https://api.dev.purposepath.app/coaching/api/v1/prompts/batch" \
  -H "X-Api-Key: ppath_svc_dev_abc123..." \
  -H "Content-Type: application/json" \
  -d '{
    "topic_ids": ["revenue_salesforce", "churn_hubspot"]
  }'
```

---

## Integration with .NET System

### Simplified Integration Pattern

**.NET System:**
- Stores `ai_topic_id` in KPI configuration records
- Calls AI system with `ai_topic_id` when analysis needed
- **Does NOT expose** KPI lists to AI system

**AI System:**
- Admin creates topics independently
- Admin stores `topic_id` in .NET system manually
- Provides analysis when .NET calls with `topic_id`

### Workflow

**Step 1: Admin Creates Topic in AI System**

Admin creates new KPI topic:

```http
POST /api/v1/admin/prompts
Body: {
  "topic_id": "revenue_salesforce",
  "topic_name": "Revenue Growth - Salesforce",
  "topic_type": "kpi_system",
  "category": "kpi",
  "allowed_parameters": [
    {"name": "kpi_value", "type": "number", "required": true},
    {"name": "threshold", "type": "number", "required": true}
  ]
}
```

Response includes `topic_id` to store in .NET.

**Step 2: Admin Creates Prompts**

```http
POST /api/v1/admin/prompts/revenue_salesforce/system
Body: { "content": "You are an AI analyzing revenue..." }

POST /api/v1/admin/prompts/revenue_salesforce/user
Body: { "content": "Analyze revenue {{kpi_value}}..." }
```

**Step 3: Admin Stores topic_id in .NET**

Admin navigates to .NET admin UI and configures KPI:

```csharp
// In .NET system
var kpiConfig = new KpiSystemConfig {
    SystemName = "Salesforce",
    KpiName = "Revenue Growth",
    AITopicId = "revenue_salesforce",  // Stored here
    Threshold = 100000
};
```

**Step 4: .NET System Calls AI for Analysis**

When KPI analysis is needed:

```http
POST /api/v1/prompts/revenue_salesforce/analyze
Headers:
  X-Api-Key: {api_key}
Body: {
  "kpi_value": 95000,
  "threshold": 100000,
  "time_period": "Q4 2025"
}

Response: {
  "data": {
    "analysis": "Revenue is $95,000, which is 5% below...",
    "recommendations": ["..."],
    "severity": "warning"
  }
}
```

---

## Code Structure

### New/Modified Files

```
coaching/
├── src/
│   ├── api/
│   │   ├── middleware/
│   │   │   └── service_auth.py                    # NEW: API key auth for system-to-system
│   │   └── routes/
│   │       ├── admin/
│   │       │   └── prompts.py                     # NEW: Admin prompt management endpoints
│   │       └── prompts.py                         # NEW: System-to-system prompt retrieval
│   ├── domain/
│   │   └── entities/
│   │       └── llm_topic.py                       # NEW: Unified topic entity
│   ├── models/
│   │   ├── prompt_requests.py                     # NEW: Request models
│   │   └── prompt_responses.py                    # NEW: Response models
│   ├── repositories/
│   │   └── topic_repository.py                    # NEW: Topic CRUD operations
│   ├── services/
│   │   └── prompt_service.py                      # UPDATED: Load from topics table + S3
│   └── scripts/
│       └── seed_topics.py                         # NEW: Seed coaching topics at deployment
└── docs/
    └── specifications/
        └── kpi-ai-integration.md                  # This document
```

### Domain Model

```python
# coaching/src/domain/entities/llm_topic.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

@dataclass
class PromptInfo:
    """Individual prompt information."""
    prompt_type: str  # system | user | assistant | function
    s3_bucket: str
    s3_key: str
    updated_at: datetime
    updated_by: str

@dataclass
class ParameterDefinition:
    """Parameter schema."""
    name: str
    type: str  # string | number | boolean | array | object
    required: bool
    description: Optional[str] = None
    default: Optional[Any] = None

@dataclass
class LLMTopic:
    """Unified topic entity for all LLM prompts."""
    topic_id: str  # PK
    topic_name: str
    topic_type: str  # conversation_coaching | single_shot | kpi_system
    category: str  # coaching | analysis | strategy | kpi
    description: Optional[str]
    display_order: int
    is_active: bool
    
    # Parameter schema
    allowed_parameters: List[ParameterDefinition]
    
    # Prompts (flexible array)
    prompts: List[PromptInfo]
    
    # Configuration
    config: Dict[str, Any]  # model, streaming, max_turns, etc.
    
    # Audit
    created_at: datetime
    created_by: str
    updated_at: datetime
```

### Repository Pattern

```python
# coaching/src/repositories/topic_repository.py

class TopicRepository:
    """Repository for LLM topics."""
    
    async def get(self, topic_id: str) -> Optional[LLMTopic]:
        """Get template by ID."""
        
    async def list_by_type(
        self,
        template_type: TemplateType,
        filters: Dict = None,
        page: int = 1,
        page_size: int = 50
    ) -> List[Template]:
        """List templates with filters."""
        
    async def create(self, template: Template) -> Template:
        """Create new template."""
        
    async def update(
        self,
        template_id: str,
        updates: Dict
    ) -> Template:
        """Update existing template."""
        
    async def delete(self, template_id: str) -> bool:
        """Soft delete template."""
```

---

## Security

### API Key Management

**Rotation Strategy:**
- Automatic rotation every 90 days
- Support for multiple active keys during rotation
- Version tracking in secret metadata

**Rate Limiting:**
```python
from slowapi import Limiter

# Per API key limits
@limiter.limit("1000/minute")  # Template retrieval
@limiter.limit("100/minute")   # Batch retrieval
```

**Audit Logging:**
- Log all API key authentications
- Track template retrievals
- Monitor for suspicious patterns
- Alert on invalid key attempts

### Input Validation

- Template ID format: `^[a-z0-9_]+$`
- Parameter name format: `^[a-z0-9_]+$`
- Template size limit: 50KB
- Parameter count limit: 50 per template
- Sanitize all user inputs

---

## Migration Path

### Phase 1: Foundation (Week 1-2)
- ✅ Create DynamoDB tables
- ✅ Implement service authentication middleware
- ✅ Create unified `TemplateRepository`
- ✅ Define domain models

### Phase 2: API Development (Week 2-3)
- ✅ Implement KPI-System admin endpoints
- ✅ Implement integration endpoints
- ✅ Add parameter management
- ✅ Add validation logic

### Phase 3: Integration (Week 3-4)
- ✅ Create service API key secrets
- ✅ Implement sync mechanism (if webhook)
- ✅ Test with .NET system
- ✅ Test with MCP server

### Phase 4: Migration (Week 4)
- ✅ Migrate coaching templates to unified system
- ✅ Update coaching endpoints to use new repository
- ✅ Maintain backward compatibility
- ✅ Update documentation

### Phase 5: Frontend (Week 5-6)
- ✅ Update admin UI for KPI-System templates
- ✅ Add parameter management UI
- ✅ Add template type selector
- ✅ Testing and QA

---

## Testing Strategy

### Unit Tests
- Repository layer (CRUD operations)
- Service authentication
- Parameter validation
- Template version management

### Integration Tests
- End-to-end template lifecycle
- API key authentication flow
- Batch retrieval performance
- .NET system integration

### Performance Tests
- Template retrieval latency < 100ms
- Batch retrieval for 100 templates
- DynamoDB query performance
- S3 read performance

---

## Monitoring & Observability

### Metrics
- Template retrieval count (by template_id)
- API key authentication success/failure rate
- Template creation/update frequency
- Integration endpoint latency
- Error rates by endpoint

### Alarms
- Invalid API key attempts > 10/minute
- Template retrieval errors > 5%
- Integration endpoint latency > 500ms
- DynamoDB throttling

### Logging
- All API key authentications (with key prefix only)
- All template CRUD operations
- All integration endpoint calls
- Parameter validation failures

---

## Appendices

### Appendix A: Request/Response Examples

**Create KPI-System Template:**
```json
POST /api/v1/admin/kpi-system/templates
{
  "kpiId": "revenue_growth",
  "systemId": "salesforce",
  "externalConfigId": "kpi_sys_123",
  "displayName": "Revenue Growth Analysis for Salesforce",
  "description": "Analyzes revenue trends and anomalies",
  "systemPrompt": "You are an expert business analyst...",
  "userPromptTemplate": "Analyze {{kpi_name}} for {{date_range}}...",
  "modelConfig": {
    "provider": "anthropic",
    "model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7
  },
  "parameters": [
    {
      "name": "date_range",
      "dataType": "string",
      "required": true,
      "validation": {
        "type": "enum",
        "enum_values": ["last_7_days", "last_30_days", "last_90_days"]
      }
    }
  ]
}

Response: 201 Created
{
  "success": true,
  "data": {
    "templateId": "kpi_revenue_salesforce_v1",
    "templateType": "kpi_system",
    "version": "1.0.0",
    ...
  }
}
```

**Retrieve Template (MCP):**
```bash
GET /api/v1/integration/templates/kpi_revenue_salesforce_v1?include_parameters=true
Header: X-Api-Key: ppath_svc_dev_abc123...

Response: 200 OK
{
  "success": true,
  "data": {
    "templateId": "kpi_revenue_salesforce_v1",
    "systemPrompt": "...",
    "userPromptTemplate": "...",
    "parameters": [
      {
        "name": "date_range",
        "dataType": "string",
        "required": true,
        "defaultValue": "last_30_days",
        "validation": {...}
      }
    ]
  }
}
```

### Appendix B: IAM Policy for Lambda

```yaml
Policies:
  - Statement:
    # Secrets Manager access
    - Effect: Allow
      Action:
        - secretsmanager:GetSecretValue
      Resource:
        - !Sub arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:purposepath-jwt-secret-${Stage}-*
        - !Sub arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:purposepath-backend-api-token-${Stage}-*
    
    # DynamoDB access
    - Effect: Allow
      Action:
        - dynamodb:GetItem
        - dynamodb:PutItem
        - dynamodb:UpdateItem
        - dynamodb:DeleteItem
        - dynamodb:Query
        - dynamodb:Scan
      Resource:
        - !Sub arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/purposepath-template-metadata-${Stage}
        - !Sub arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/purposepath-template-metadata-${Stage}/index/*
        - !Sub arn:aws:dynamodb:${AWS::Region}:${AWS::AccountId}:table/purposepath-template-parameters-${Stage}
    
    # S3 access
    - Effect: Allow
      Action:
        - s3:GetObject
        - s3:PutObject
        - s3:DeleteObject
      Resource:
        - !Sub arn:aws:s3:::purposepath-templates-${Stage}/*
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-11 | Use unified template system | Single source of truth, reduced duplication |
| 2025-11-11 | API Key authentication for service-to-service | Simpler than OAuth, sufficient for MVP |
| 2025-11-11 | DynamoDB for metadata | Fast lookups, serverless, cost-effective |
| 2025-11-11 | S3 for template content | Existing pattern, version support |
| 2025-11-11 | Manual creation for MVP | Simpler than sync, proves concept |

---

## Open Questions

1. **Webhook URL from .NET:** What will be the webhook endpoint URL if we implement Option B?
2. **Rate Limits:** Are the proposed rate limits (1000/min, 100/min batch) sufficient?
3. **Template Size:** Is 50KB max template size appropriate?
4. **Parameter Count:** Is 50 parameters per template sufficient?
5. **API Key Rotation:** Should rotation be automated or manual for MVP?

---

## Next Steps

1. **Approval:** Review and approve this architecture
2. **Decision:** Choose sync strategy (manual vs webhook)
3. **Setup:** Create DynamoDB tables and secrets
4. **Implementation:** Begin Phase 1 development
5. **Coordination:** Align with .NET team on integration approach

---

## Summary - Final Simplified Architecture

### Core Design Principles

1. **Single Table**: One DynamoDB table for all LLM prompts
2. **No Versioning**: Current state only, simple overwrites
3. **No External Dependencies**: AI system doesn't call .NET
4. **Flexible Prompt Types**: Dynamic array supports system, user, assistant, function, or future types
5. **Type Filtering**: Admin UI can filter by topic_type for focused management

### Data Model (Final)

**Single Table: `purposepath-llm-prompts-{env}`**

All LLM prompts (coaching, single-shot, KPI) stored in one table:

```python
{
    "topic_id": "core_values",  # PK
    "topic_name": "Core Values",
    "topic_type": "conversation_coaching",  # or single_shot or kpi_system
    "category": "coaching",
    "allowed_parameters": [{"name": "user_name", "type": "string", "required": true}],
    "prompts": [
        {"prompt_type": "system", "s3_key": "prompts/core_values/system.md", ...},
        {"prompt_type": "user", "s3_key": "prompts/core_values/user.md", ...}
    ],
    "config": {"default_model": "...", "supports_streaming": true}
}
```

**S3 Storage:**
- Path: `prompts/{topic_id}/{prompt_type}.md`
- Format: Markdown (human-readable)
- No versioning (current state only)

### API Design (Final)

**Admin APIs (JWT Auth):**
- `GET /admin/prompts?topic_type={type}` - List topics
- `POST /admin/prompts` - Create topic (KPI only)
- `GET /admin/prompts/{topic_id}/{prompt_type}` - Get prompt content
- `PUT /admin/prompts/{topic_id}/{prompt_type}` - Update prompt
- `POST /admin/prompts/{topic_id}/{prompt_type}` - Create prompt type

**System APIs (API Key Auth):**
- `GET /prompts/{topic_id}` - Get all prompts for topic
- `POST /prompts/batch` - Batch get multiple topics

### Workflows

**Coaching Topics (Seeded at Deployment):**
1. Migration script seeds 4 coaching topics from enum
2. Admin updates prompts via admin UI
3. User conversations use existing endpoints (no breaking changes)

**KPI-System Topics (Created On-Demand):**
1. Admin creates topic in AI system → receives `topic_id`
2. Admin creates system/user prompts
3. Admin stores `topic_id` in .NET KPI configuration
4. .NET calls AI with `topic_id` when analysis needed

### Key Benefits

- ✅ **Maximum Simplicity**: Single table, zero joins, zero hops
- ✅ **No Versioning Complexity**: Current state only, S3 versioning available if needed
- ✅ **Flexible Prompt Types**: Array supports any type (system, user, assistant, function)
- ✅ **Independent Updates**: Update system prompt without touching user prompt
- ✅ **No Breaking Changes**: User-facing endpoints unchanged
- ✅ **Type Filtering**: Admin UI filters by topic_type
- ✅ **Service Abstraction**: `get_template(topic)` works for all types
- ✅ **Future-Proof**: Easy to add new types, categories, features

### Answers to Design Questions

**Q1: Where are parameters stored?**
→ In `llm-prompts` table as `allowed_parameters` array embedded in topic record

**Q2: How to handle system and user prompts?**
→ Separate files per prompt type (system.md, user.md) for independent updates

**Q3: How to avoid .NET calls from AI system?**
→ Admin manually stores `topic_id` in .NET, .NET calls AI (not vice versa)

**Q4: How to handle version history?**
→ No explicit versioning. Enable S3 versioning transparently if history needed

---

## Markdown Formatting Note

This document contains minor markdown formatting warnings (MD031, MD032, MD036, MD040) related to:
- Blank lines around code fences and lists
- Emphasis used as headings
- Missing language specifiers for code blocks

These are cosmetic issues and do not affect the technical content. They can be addressed in a formatting pass after the architecture is approved.

---

**Document End**
