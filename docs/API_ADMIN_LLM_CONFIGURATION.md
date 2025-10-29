# Admin API: LLM Configuration & Templates

**Version:** 1.0  
**Date:** October 29, 2024  
**Base URL:** `/api/admin`  
**Auth:** Admin JWT required

---

## Response Format

All endpoints return:
```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error?: string;
}
```

---

## 1. LLM Interactions

### GET /admin/interactions
**Query:** `?category={string}&active_only={bool}`

**Response:**
```json
{
  "interactions": [{
    "code": "ALIGNMENT_ANALYSIS",
    "description": "Analyze alignment...",
    "category": "analysis",
    "required_parameters": ["user_input", "context"],
    "optional_parameters": ["business_data"],
    "handler_class": "AlignmentAnalysisService"
  }],
  "total_count": 12
}
```

### GET /admin/interactions/{code}
**Response:** Interaction details + active configurations

---

## 2. LLM Models

### GET /admin/models
**Query:** `?provider={string}&active_only={bool}&capability={string}`

**Response:**
```json
{
  "models": [{
    "code": "CLAUDE_3_SONNET",
    "provider": "bedrock",
    "model_name": "anthropic.claude-3-sonnet-20240229-v1:0",
    "version": "20240229",
    "capabilities": ["chat", "analysis", "streaming"],
    "max_tokens": 4096,
    "cost_per_1k_tokens": 0.003,
    "is_active": true
  }],
  "providers": ["bedrock", "anthropic", "openai"],
  "total_count": 8
}
```

---

## 3. LLM Configurations

### GET /admin/configurations
**Query:** `?interaction_code={}&template_id={}&model_code={}&tier={}&active_only={bool}&page={int}&per_page={int}`

**Response:**
```json
{
  "configurations": [{
    "config_id": "cfg_abc123",
    "interaction_code": "ALIGNMENT_ANALYSIS",
    "interaction_description": "Analyze alignment...",
    "template_id": "tmpl_456",
    "template_name": "Alignment Template v2",
    "model_code": "CLAUDE_3_SONNET",
    "model_name": "anthropic.claude-3-sonnet...",
    "tier": "premium",
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "is_active": true,
    "effective_from": "2024-10-01T00:00:00Z",
    "effective_until": null,
    "created_at": "2024-10-15T10:30:00Z",
    "updated_at": "2024-10-20T14:22:00Z",
    "created_by": "admin_123"
  }],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total_count": 24,
    "total_pages": 1
  }
}
```

### GET /admin/configurations/{config_id}
**Response:** Full config with nested interaction, template, model objects

### POST /admin/configurations
**Body:**
```json
{
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "template_id": "tmpl_456",
  "model_code": "CLAUDE_3_SONNET",
  "tier": "premium",
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 1.0,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "effective_from": "2024-11-01T00:00:00Z",
  "effective_until": null
}
```

**Constraints:**
- `temperature`: 0.0-2.0
- `max_tokens`: > 0, ≤ model.max_tokens
- `top_p`: 0.0-1.0
- `frequency_penalty`: -2.0-2.0
- `presence_penalty`: -2.0-2.0

**Validations:**
- interaction_code must exist
- model_code must exist
- template_id must exist
- No duplicate active config for interaction+tier

**Response:** 201 with created config

### PUT /admin/configurations/{config_id}
**Body:** Same fields as POST (all optional)

### DELETE /admin/configurations/{config_id}
**Query:** `?permanent={bool}` (default: false = soft delete)

---

## 4. Templates

### GET /admin/prompts/{topic}/versions
**Path:** `topic` = core_values, purpose, vision, goals

**Response:**
```json
{
  "topic": "core_values",
  "versions": [{
    "version": 2,
    "name": "Core Values v2",
    "isLatest": true,
    "isActive": true,
    "createdAt": "2024-10-15T10:00:00Z",
    "updatedAt": "2024-10-20T14:30:00Z"
  }],
  "totalVersions": 2,
  "latestVersion": 2
}
```

### GET /admin/prompts/{topic}/{version}
**Response:**
```json
{
  "topic": "core_values",
  "phase": "exploration",
  "version": 2,
  "systemPrompt": "You are an AI coaching assistant...",
  "userPromptTemplate": "Let's explore {user_name}...",
  "model": "default-model",
  "parameters": {"user_name": "", "context": ""},
  "metadata": {"phase": "exploration", "name": "Core Values v2"},
  "createdAt": "2024-10-15T10:00:00Z"
}
```

### POST /admin/prompts/{topic}/versions
**Body:**
```json
{
  "name": "Template Name",
  "phase": "exploration",
  "system_prompt": "You are...",
  "user_prompt_template": "Template with {variables}",
  "parameters": {"variable_name": ""},
  "metadata": {},
  "set_as_latest": true
}
```

**Response:** 201 with created template

### PUT /admin/prompts/{topic}/{version}
**Body:** Same fields (all optional except at least one required)

### POST /admin/prompts/{topic}/{version}/set-latest
Makes version the active latest

### DELETE /admin/prompts/{topic}/{version}
Soft delete template version

---

## Data Model Summary

**Interaction** (code-based registry)
- code, description, category
- required_parameters[], optional_parameters[]

**Model** (code-based registry)  
- code, provider, model_name
- capabilities[], max_tokens, cost

**Template** (DynamoDB)
- template_id, name, version
- system_prompt (LLM role/behavior)
- user_prompt_template (prompt with {vars})
- variables[]

**Configuration** (DynamoDB)
- Maps: interaction + template + model + tier
- Runtime params: temperature, max_tokens, top_p, penalties
- Lifecycle: effective_from, effective_until, is_active

---

## Frontend Integration

1. **List Interactions** → Show available interaction types
2. **List Models** → Show available LLM models
3. **List Templates** → Show available templates per topic
4. **Create Configuration** → Assign template + model to interaction
5. **List Configurations** → View all mappings
6. **Update Configuration** → Change model, template, or parameters

---

## Status

**Existing:** Templates endpoints (✅ Complete)  
**Missing:** Interactions, Configurations endpoints (❌ Not implemented)  
**Needs Fix:** Models endpoint (⚠️ Uses hardcoded data, not MODEL_REGISTRY)

**Issue:** #76 tracks implementation

