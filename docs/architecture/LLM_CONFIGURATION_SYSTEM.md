# LLM Configuration System Architecture

**Version**: 1.0.0  
**Last Updated**: October 30, 2025  
**Status**: Production Ready

---

## Overview

The LLM Configuration System provides centralized, tier-based management of AI interactions and prompt templates across the PurposePath AI platform. It enables dynamic configuration of LLM interactions with multi-tenant support, caching, and validation.

### Key Features

- **Tier-Based Configuration**: Different configurations for starter, professional, and enterprise tiers
- **Template Management**: Centralized prompt template storage with S3 integration
- **Registry-Based Validation**: Validates all configuration references against interaction and model registries
- **Intelligent Caching**: Redis-based caching for performance
- **Multi-Tenant Support**: Isolated configurations per tenant
- **Dynamic Resolution**: Runtime resolution with fallback logic

---

## System Components

### 1. Core Domain Entities

#### LLMConfiguration

Aggregate root representing an LLM interaction configuration.

```python
class LLMConfiguration(BaseModel):
    config_id: str
    interaction_code: str      # From INTERACTION_REGISTRY
    template_id: str          # References TemplateMetadata
    model_code: str           # From MODEL_REGISTRY  
    tier: str | None          # "starter", "professional", "enterprise", None (default)
    temperature: float        # 0.0 - 1.0
    max_tokens: int          # Context window limit
    is_active: bool          # Enable/disable
    effective_from: datetime # Start date
    effective_until: datetime | None # Optional end date
```

**Business Rules**:

- `interaction_code` must exist in INTERACTION_REGISTRY
- `model_code` must exist in MODEL_REGISTRY  
- `template_id` must reference active template
- Only one active config per interaction+tier combination
- Temperature range: 0.0 - 1.0
- Max tokens must be positive

#### TemplateMetadata

Aggregate root for prompt template metadata.

```python
class TemplateMetadata(BaseModel):
    template_id: str
    template_code: str        # Unique code (e.g., "ALIGNMENT_V2")
    interaction_code: str     # From INTERACTION_REGISTRY
    name: str
    description: str
    s3_bucket: str           # S3 storage location
    s3_key: str              # S3 object key
    version: str             # Semantic versioning
    is_active: bool
    required_parameters: list[str] | None  # Jinja2 variables
```

**Business Rules**:

- `interaction_code` must exist in INTERACTION_REGISTRY
- Only one active template per `template_code`
- S3 bucket and key must be valid
- Template content validated on creation

---

### 2. Application Services

#### LLMConfigurationService

**Purpose**: Orchestrates configuration resolution, validation, and lifecycle management.

**Key Methods**:

- `resolve_configuration(interaction_code, tier)`: Resolves configuration with tier fallback
- `get_configuration_by_id(config_id)`: Retrieves specific configuration
- `list_configurations_for_interaction(interaction_code)`: Lists all configurations  
- `invalidate_cache(interaction_code, tier)`: Clears cached configurations

**Resolution Logic**:

```
1. Check cache for interaction + tier
2. If miss, query repository for tier-specific config
3. If not found, fallback to default config (tier=None)
4. Validate all references (interaction, model, template)
5. Cache result
6. Return configuration
```

**Caching Strategy**:

- Cache key: `llm_config:{interaction_code}:{tier}`
- TTL: 15 minutes
- Invalidation: On configuration updates

#### LLMTemplateService

**Purpose**: Manages template retrieval, rendering, and validation.

**Key Methods**:

- `get_template_by_id(template_id)`: Fetches metadata + content
- `get_active_template_for_interaction(interaction_code)`: Gets active template
- `render_template(template_id, parameters)`: Renders Jinja2 template
- `validate_template_syntax(template_id)`: Validates Jinja2 syntax
- `invalidate_cache(template_id)`: Clears cached template

**Template Flow**:

```
1. Fetch metadata from repository
2. Check content cache
3. If miss, fetch from S3
4. Cache content (TTL: 30 minutes)
5. Render with Jinja2 if parameters provided
6. Return metadata + content/rendered
```

---

### 3. Infrastructure Layer

#### DynamoDBLLMConfigurationRepository

**Table Schema**:

```
PK: CONFIG#{config_id}
SK: METADATA

GSI1:
- PK: INTERACTION#{interaction_code}
- SK: TIER#{tier}#STATUS#{is_active}

Attributes:
- config_id, interaction_code, template_id, model_code
- tier, temperature, max_tokens, is_active
- created_at, updated_at, created_by, updated_by
- effective_from, effective_until
```

**Query Patterns**:

1. Get by ID: Query PK=CONFIG#{id}, SK=METADATA
2. Get active for interaction+tier: Query GSI1 PK=INTERACTION#{code}, SK begins_with TIER#{tier}#STATUS#true
3. List all for interaction: Query GSI1 PK=INTERACTION#{code}

#### DynamoDBLLMTemplateRepository

**Table Schema**:

```
PK: TEMPLATE#{template_id}
SK: METADATA

GSI1:
- PK: INTERACTION#{interaction_code}
- SK: CODE#{template_code}#STATUS#{is_active}

Attributes:
- template_id, template_code, interaction_code
- name, description, version
- s3_bucket, s3_key
- is_active, required_parameters
- created_at, updated_at, created_by, updated_by
```

**Query Patterns**:

1. Get by ID: Query PK=TEMPLATE#{id}, SK=METADATA
2. Get active by code: Query GSI1 where CODE contains template_code and STATUS=true
3. List for interaction: Query GSI1 PK=INTERACTION#{code}

#### S3TemplateStorage

**Bucket Structure**:

```
purpose-path-templates/
├── alignment/
│   ├── v1.jinja2
│   ├── v2.jinja2
│   └── enterprise_v1.jinja2
├── strategy/
│   ├── basic_v1.jinja2
│   └── advanced_v1.jinja2
└── kpi/
    └── definition_v1.jinja2
```

**Access Pattern**:

- Read-heavy (99% reads, 1% writes)
- Cached aggressively (30 min TTL)
- Versioned objects for rollback

#### RedisCache

**Key Patterns**:

```
llm_config:{interaction_code}:{tier}      → LLMConfiguration (15 min TTL)
llm_template:{template_id}:metadata       → TemplateMetadata (30 min TTL)
llm_template:{template_id}:content        → Template content (30 min TTL)
llm_template:{template_id}:rendered:{hash} → Rendered template (5 min TTL)
```

---

### 4. API Layer

#### Admin Configuration Endpoints

**Base Path**: `/api/v1/admin/llm/configurations`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List configurations with filters |
| POST | `/` | Create new configuration |
| GET | `/{config_id}` | Get configuration by ID |
| PATCH | `/{config_id}` | Update configuration |
| DELETE | `/{config_id}` | Deactivate configuration |
| POST | `/{config_id}/validate` | Validate configuration |

#### Admin Template Endpoints

**Base Path**: `/api/v1/admin/llm/templates`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List templates with filters |
| POST | `/` | Create new template |
| GET | `/{template_id}` | Get template by ID |
| PATCH | `/{template_id}` | Update template |
| DELETE | `/{template_id}` | Deactivate template |
| GET | `/{template_id}/content` | Get template content |
| POST | `/{template_id}/render` | Render template with params |

---

## Configuration Resolution Flow

```
┌─────────────────┐
│ Client Request  │
│ (interaction +  │
│  tier)          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Configuration   │
│ Service         │
└────────┬────────┘
         │
         ▼
  ┌─────────────┐ No
  │ Cache Hit?  ├───────┐
  └─────┬───────┘       │
    Yes │               ▼
        │      ┌─────────────────┐
        │      │ Repository:     │
        │      │ Query tier-     │
        │      │ specific config │
        │      └────────┬────────┘
        │               │
        │        ┌──────▼──────┐ Yes
        │        │ Found?      ├────┐
        │        └──────┬──────┘    │
        │          No   │           │
        │               ▼           │
        │      ┌─────────────────┐  │
        │      │ Fallback:       │  │
        │      │ Query default   │  │
        │      │ config (no tier)│  │
        │      └────────┬────────┘  │
        │               │           │
        │               ▼           │
        │        ┌──────────────┐   │
        │        │ Validate:    │◄──┘
        │        │ - Interaction│
        │        │ - Model      │
        │        │ - Template   │
        │        └──────┬───────┘
        │               │
        │               ▼
        │        ┌──────────────┐
        │        │ Cache Result │
        │        └──────┬───────┘
        │               │
        └───────────────┘
                 │
                 ▼
          ┌─────────────┐
          │ Return      │
          │ Config      │
          └─────────────┘
```

---

## Template Rendering Flow

```
┌──────────────────┐
│ Render Request   │
│ (template_id +   │
│  parameters)     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Template Service │
└────────┬─────────┘
         │
         ▼
  ┌─────────────┐
  │ Get Template│
  │ Metadata    │
  └─────┬───────┘
        │
        ▼
  ┌──────────────┐ No
  │ Content      ├──────┐
  │ Cached?      │      │
  └──────┬───────┘      │
     Yes │              ▼
         │     ┌─────────────────┐
         │     │ Fetch from S3   │
         │     └────────┬────────┘
         │              │
         │              ▼
         │     ┌─────────────────┐
         │     │ Cache Content   │
         │     └────────┬────────┘
         │              │
         └──────────────┘
                 │
                 ▼
          ┌─────────────┐
          │ Validate    │
          │ Parameters  │
          └─────┬───────┘
                │
                ▼
          ┌─────────────┐
          │ Render with │
          │ Jinja2      │
          └─────┬───────┘
                │
                ▼
          ┌─────────────┐
          │ Return      │
          │ Rendered    │
          └─────────────┘
```

---

## Security & Multi-Tenancy

### Tenant Isolation

All configuration and template access is scoped by tenant:

```python
# Request context carries tenant_id
context = RequestContext(
    user_id="user_123",
    tenant_id="tenant_456",  # ← Enforced at API layer
    role=UserRole.ADMIN,
    subscription_tier=SubscriptionTier.PROFESSIONAL
)

# Service methods inherit tenant context
config = await service.resolve_configuration(
    interaction_code="ALIGNMENT_ANALYSIS",
    tier="professional"
)
```

### Access Control

- **Admin APIs**: Require `ADMIN` or `OWNER` role
- **Configuration Management**: Admin-only operations
- **Template Management**: Admin-only operations
- **Resolution**: Available to all authenticated users

### Data Protection

- **At Rest**: DynamoDB encryption, S3 server-side encryption
- **In Transit**: HTTPS/TLS 1.3
- **Cache**: Redis with encryption
- **Secrets**: AWS Secrets Manager for S3 credentials

---

## Performance Characteristics

### Latency Targets

| Operation | Cold Cache | Warm Cache |
|-----------|------------|------------|
| Configuration resolution | < 100ms | < 5ms |
| Template fetch | < 150ms | < 5ms |
| Template rendering | < 20ms | < 10ms |

### Throughput Targets

| Operation | Sequential | Concurrent (10x) |
|-----------|------------|------------------|
| Configuration resolution | > 500/s | > 1,000/s |
| Template rendering | > 1,000/s | > 2,000/s |

### Cache Effectiveness

- **Hit Rate Target**: > 95%
- **Speedup**: > 10x vs cold cache
- **S3 Call Reduction**: < 5% after warm-up

---

## Error Handling

### Domain Exceptions

```python
class ConfigurationNotFoundError(DomainError):
    """No configuration found for interaction and tier."""
    
class InvalidConfigurationError(DomainError):
    """Configuration references invalid interaction/model/template."""
    
class TemplateNotFoundError(DomainError):
    """Template does not exist."""
    
class TemplateRenderingError(DomainError):
    """Template rendering failed (syntax/missing params)."""
```

### Error Responses

```json
{
  "error": {
    "type": "ConfigurationNotFoundError",
    "message": "No configuration found for ALIGNMENT_ANALYSIS (tier: professional)",
    "code": "CONFIG_NOT_FOUND",
    "details": {
      "interaction_code": "ALIGNMENT_ANALYSIS",
      "tier": "professional",
      "attempted_fallback": true
    }
  }
}
```

---

## Monitoring & Observability

### Metrics

**Configuration Service**:

- `llm_config.resolution.latency` (histogram)
- `llm_config.resolution.cache_hit_rate` (gauge)
- `llm_config.resolution.errors` (counter)
- `llm_config.validation.failures` (counter)

**Template Service**:

- `llm_template.fetch.latency` (histogram)
- `llm_template.render.latency` (histogram)
- `llm_template.s3.fetch_count` (counter)
- `llm_template.cache_hit_rate` (gauge)

### Logging

Structured logging with context:

```python
logger.info(
    "llm_config.resolution.started",
    interaction_code=interaction_code,
    tier=tier,
    tenant_id=context.tenant_id
)

logger.info(
    "llm_config.resolution.completed",
    interaction_code=interaction_code,
    tier=tier,
    config_id=config.config_id,
    cache_hit=cache_hit,
    elapsed_ms=elapsed_ms
)
```

---

## Future Enhancements

1. **A/B Testing**: Support for multiple active configurations per tier
2. **Cost Tracking**: Track LLM usage costs per tenant/interaction
3. **Template Versioning**: Blue-green deployment of template updates
4. **Configuration Presets**: Common configuration templates
5. **Analytics**: Usage patterns and optimization recommendations

---

## Related Documentation

- [API Documentation](./API_DOCUMENTATION.md)
- [Data Flow Diagrams](./DATA_FLOW_DIAGRAMS.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Clean Architecture Guidelines](../Guides/clean-architecture-ddd-guidelines.md)
