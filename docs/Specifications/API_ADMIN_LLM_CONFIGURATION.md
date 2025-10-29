# Admin API: LLM Configuration & Templates

**Version:** 2.0  
**Date:** October 29, 2025  
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
  error_code?: 'VALIDATION_ERROR' | 'CONFLICT_ERROR' | 'NOT_FOUND' | 'INVALID_PARAMETERS';
  validation_errors?: Array<{
    field: string;
    message: string;
    code: string;
  }>;
  conflicts?: Array<{
    type: string;
    message: string;
    existing_config_id?: string;
  }>;
}
```

## Template Variable Syntax

**Basic Variables:**
- Use `{variable_name}` syntax in both system_prompt and user_prompt_template
- Variables are case-sensitive
- Variables must match parameters defined by the interaction (in INTERACTION_REGISTRY)
- No nested objects (e.g., `{user.name}` is not supported)
- Simple substitution only (no conditionals or loops)

**Parameter Model:**
- **Parameters are PREDETERMINED by interactions** (in INTERACTION_REGISTRY)
- Templates can only USE parameters, not define or customize them
- The parameters object in templates contains METADATA only (display_name, description)
- Parameter types and validation rules are determined by the interaction, not the template
- At runtime, parameter values come from the endpoint or backend enrichment

**Example:**
```json
{
  "system_prompt": "You are helping {user_name} with {context} analysis",
  "user_prompt_template": "Analyze {user_input} for {user_name}",
  "parameters": {
    "user_name": {
      "display_name": "User Name",
      "description": "The user's display name"
    },
    "context": {
      "display_name": "Analysis Context",
      "description": "Context for the analysis"
    },
    "user_input": {
      "display_name": "User Input",
      "description": "User's input to analyze"
    }
  }
}
```

**Validation Flow:**
1. Extract all `{variables}` from system_prompt and user_prompt_template
2. Check against interaction's required_parameters and optional_parameters
3. Error if template uses parameters not declared by interaction
4. Warn if template doesn't use all required parameters

**What Admin CANNOT Do:**
- ❌ Define new parameters not in interaction
- ❌ Change parameter types
- ❌ Add custom validation rules
- ❌ Make required parameters optional (or vice versa)

**What Admin CAN Do:**
- ✅ Add display_name for UI purposes
- ✅ Add descriptions for documentation
- ✅ Choose which optional parameters to use
- ✅ Embed parameters in system_prompt and/or user_prompt_template

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

## 3. Template Validation & Testing

### POST /admin/templates/{template_id}/test

**Purpose:** Test template rendering with sample parameters

**Body:**

```json
{
  "parameters": {
    "user_name": "John",
    "context": "career",
    "user_input": "I want to find my purpose"
  }
}
```

**Response:**

```json
{
  "rendered_system_prompt": "You are an AI coaching assistant helping John with career analysis...",
  "rendered_user_prompt": "Let's explore John's career goals based on: I want to find my purpose",
  "estimated_tokens": 150,
  "validation_errors": [],
  "parameter_usage": {
    "used_parameters": ["user_name", "context", "user_input"],
    "unused_parameters": [],
    "undeclared_parameters": []
  }
}
```

### GET /admin/templates/{template_id}/parameters

**Purpose:** Analyze template parameter usage

**Response:**

```json
{
  "declared_parameters": ["user_name", "context", "business_type"],
  "used_in_system_prompt": ["user_name"],
  "used_in_user_prompt": ["user_name", "context"],
  "unused_parameters": ["business_type"],
  "undeclared_but_used": []
}
```

---

## 4. Configuration Validation

### POST /admin/configurations/validate

**Purpose:** Validate configuration before creation/update

**Body:**

```json
{
  "interaction_code": "ALIGNMENT_ANALYSIS",
  "template_id": "tmpl_456",
  "model_code": "CLAUDE_3_SONNET",
  "tier": "premium"
}
```

**Response:**

```json
{
  "is_valid": true,
  "warnings": ["Template has 3 unused parameters"],
  "errors": [],
  "conflicts": [{
    "type": "active_configuration_exists",
    "message": "Active configuration already exists for ALIGNMENT_ANALYSIS + premium",
    "existing_config_id": "cfg_xyz789"
  }],
  "dependencies": {
    "template_exists": true,
    "model_exists": true,
    "interaction_exists": true
  }
}
```

---

## 5. LLM Configurations

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
  "is_active": false,
  "conflict_resolution": "auto_deactivate_existing"
}
```

**Constraints:**

- `temperature`: 0.0-2.0
- `max_tokens`: > 0, ≤ model.max_tokens
- `top_p`: 0.0-1.0
- `frequency_penalty`: -2.0-2.0
- `presence_penalty`: -2.0-2.0
- `conflict_resolution`: "auto_deactivate_existing" | "fail_on_conflict"

**Validations:**

- interaction_code must exist
- model_code must exist
- template_id must exist
- No duplicate active config for interaction+tier (unless auto_deactivate_existing)

**Response:** 201 with created config

### PUT /admin/configurations/{config_id}

**Body:** Same fields as POST (all optional)

### POST /admin/configurations/{config_id}/activate

**Purpose:** Activate a configuration (deactivates any existing active config for same interaction+tier)

**Response:** Updated configuration

### POST /admin/configurations/{config_id}/deactivate

**Purpose:** Deactivate a configuration

**Response:** Updated configuration

### DELETE /admin/configurations/{config_id}

**Query:** `?permanent={bool}` (default: false = soft delete)

---

## 6. Templates

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
  "systemPrompt": "You are an AI coaching assistant helping {user_name}...",
  "userPromptTemplate": "Let's explore {user_name}'s core values in {context}...",
  "model": "default-model",
  "parameters": {
    "user_name": {
      "display_name": "User Name",
      "description": "The user's display name"
    },
    "context": {
      "display_name": "Analysis Context",
      "description": "Context for the analysis"
    }
  },
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
  "system_prompt": "You are helping {user_name}...",
  "user_prompt_template": "Template with {variables}",
  "parameters": {
    "user_name": {
      "display_name": "User Name",
      "description": "User's name"
    },
    "variables": {
      "display_name": "Variables",
      "description": "Sample variable"
    }
  },
  "metadata": {},
  "set_as_latest": true
}
```

**Parameter Schema (Metadata Only):**

```typescript
interface TemplateParameter {
  display_name: string;        // Display name for admin UI
  description?: string;        // Description for documentation
}
```

**Note:** Types, validation, required/optional status, and default values are determined by the interaction definition in INTERACTION_REGISTRY, not by the template.

**Runtime Behavior:**
- Parameter values are provided by the endpoint or backend enrichment
- Values are substituted into the template at runtime
- Type validation happens at the interaction level, not template level

**Validation:** Template is validated on save to ensure:

- All `{variables}` in prompts are declared in parameters object
- All parameters in parameters object match interaction's allowed parameters
- Template uses parameters defined by the associated interaction (validated during configuration creation)
- No malformed variable syntax

**Response:** 201 with created template

### PUT /admin/prompts/{topic}/{version}

**Body:** Same fields (all optional except at least one required)

**Validation:** Same validation rules apply on update

### POST /admin/prompts/{topic}/{version}/set-latest

Makes version the active latest

### DELETE /admin/prompts/{topic}/{version}

Soft delete template version

---

## Parameter Compatibility Validation

**Critical Rule:** Template parameters must be compatible with interaction parameters.

**Validation Logic:**
```
template_parameters ⊆ (interaction.required_parameters ∪ interaction.optional_parameters)
```

**Process:**
1. Extract all `{variable}` syntax from template's system_prompt and user_prompt_template
2. Get interaction's required_parameters and optional_parameters from INTERACTION_REGISTRY
3. Verify each template parameter exists in interaction's parameter lists
4. Check that all required parameters are available (warn if not used)

**Example:**

**Interaction Definition:**
```python
INTERACTION_REGISTRY["ALIGNMENT_ANALYSIS"] = LLMInteraction(
    code="ALIGNMENT_ANALYSIS",
    required_parameters=["user_input", "context"],
    optional_parameters=["business_data"],
    ...
)
```

**Valid Template:**
```json
{
  "system_prompt": "You are analyzing {context}",
  "user_prompt_template": "Analyze {user_input} in {context}",
  "parameters": {
    "user_input": {"display_name": "User Input"},
    "context": {"display_name": "Context"}
  }
}
```
✅ Valid: All parameters (user_input, context) are in interaction's parameter lists

**Invalid Template:**
```json
{
  "system_prompt": "You are analyzing {context}",
  "user_prompt_template": "Analyze {user_input} with {custom_field}",
  "parameters": {
    "user_input": {"display_name": "User Input"},
    "context": {"display_name": "Context"},
    "custom_field": {"display_name": "Custom Field"}
  }
}
```
❌ Invalid: "custom_field" is not in interaction's parameter lists

**Validation Errors:**
- `PARAMETER_NOT_IN_INTERACTION`: Template uses parameter not defined by interaction
- `MISSING_REQUIRED_PARAMETER`: Template doesn't use a required parameter (warning)
- `UNDECLARED_PARAMETER`: Template uses `{variable}` not declared in parameters object

---

## Configuration Conflict Resolution

**Rules:**

- Only one active configuration per interaction+tier combination
- Creating new configuration with existing interaction+tier can auto-deactivate the previous one
- Manual activation/deactivation through dedicated endpoints
- Soft delete preserves configuration for audit purposes

**Conflict Detection:**

- Check during POST /admin/configurations
- Validate during PUT /admin/configurations/{config_id}
- Return conflict details in validation endpoint

**Conflict Resolution Options:**

- `auto_deactivate_existing`: Automatically deactivate conflicting configuration
- `fail_on_conflict`: Fail creation/update if conflict exists

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
- parameters[] with typing and validation

**Configuration** (DynamoDB)

- Maps: interaction + template + model + tier
- Runtime params: temperature, max_tokens, top_p, penalties
- Lifecycle: is_active (manual activation)

---

## Frontend Integration

1. **List Interactions** → Show available interaction types
2. **List Models** → Show available LLM models
3. **List Templates** → Show available templates per topic
4. **Test Templates** → Preview rendered templates with sample data
5. **Validate Configuration** → Check for conflicts before creation
6. **Create Configuration** → Assign template + model to interaction
7. **List Configurations** → View all mappings
8. **Update Configuration** → Change model, template, or parameters
9. **Activate/Deactivate** → Manual configuration state management

---

## Additional Endpoints

### Template Import/Export

#### POST /admin/templates/import

**Body:**

```json
{
  "templates": [/* template objects */],
  "merge_strategy": "replace" | "skip_existing" | "create_new_version"
}
```

#### GET /admin/templates/export

**Query:** `?topic={}&version={}&format=json`

**Response:** `{ "templates": [...] }`

### Bulk Configuration Operations

#### POST /admin/configurations/bulk-deactivate

**Body:**

```json
{
  "filter": {
    "interaction_code": "ALIGNMENT_ANALYSIS",
    "tier": "premium"
  },
  "reason": "Updating all premium alignment configurations"
}
```

#### GET /admin/configurations/{config_id}/dependencies

**Response:**

```json
{
  "template_exists": true,
  "model_exists": true,
  "interaction_exists": true,
  "issues": []
}
```

---

## Status

**Existing:** Templates endpoints (✅ Complete)

**Missing:** Interactions, Configurations endpoints (❌ Not implemented)

**Needs Fix:** Models endpoint (⚠️ Uses hardcoded data, not MODEL_REGISTRY)

**New Additions:** Validation, testing, conflict resolution endpoints (🆕 Enhanced)

**Issue:** #76 tracks implementation

