# Implement Topic-Driven Endpoint Architecture with Unified AI Engine

## Overview

Refactor the coaching service to use a unified topic-driven architecture where all AI endpoints are configured through topic metadata rather than hardcoded service classes. This enables admins to modify prompts, model configurations, and parameters without code deployments.

---

## Problem Statement

**Current State**:
- 44 frontend endpoints exist with hardcoded logic
- Each endpoint has dedicated service class (AlignmentService, StrategyService, etc.)
- Prompts are hardcoded in code
- Model configuration is hardcoded
- Adding new endpoint requires code changes and deployment
- Admins cannot modify AI behavior without developer intervention

**Desired State**:
- Single Unified AI Engine handles all endpoints
- Endpoint → Topic mapping via hardcoded registry
- Topics stored in DynamoDB with S3-backed prompts
- Admins can modify prompts and configurations via admin UI
- New endpoints = new topic configuration (no code changes)
- Automatic topic seeding and cleanup

---

## Architecture Vision

### Single-Shot Flow
```
Frontend → Endpoint → Registry Lookup → Topic Config → Unified AI Engine → LLM Provider → Response Serializer → Frontend
```

### Conversation Flow
```
Frontend → Endpoint → Registry Lookup → Topic Config → Unified AI Engine → Conversation Manager → LLM Provider → Memory Management → Response Serializer → Frontend
```

### Admin Flow
```
Admin UI → List Topics → Select Topic → Edit Prompts/Config → Save to S3/DynamoDB → Preview/Test → Deploy
```

---

## Tasks

### Phase 1: Foundation - Endpoint Registry & Topic Definitions

#### Task 1.1: Create Endpoint Registry
**File**: `coaching/src/core/endpoint_registry.py`

**Requirements**:
- [ ] Create `EndpointDefinition` dataclass with fields:
  - `endpoint_path: str` - API path (e.g., "/coaching/alignment-check")
  - `http_method: str` - HTTP method ("GET", "POST", "PUT", "DELETE")
  - `topic_id: str` - Topic identifier (e.g., "alignment_check")
  - `response_model: str` - Response model class name
  - `requires_conversation: bool` - Single-shot vs conversation
  - `category: str` - Grouping ("strategic_planning", "operations_ai", etc.)
  - `description: str` - Human-readable description
  - `is_active: bool` - Whether endpoint is currently active

- [ ] Create `ENDPOINT_REGISTRY: dict[str, EndpointDefinition]` with all 44 endpoints:
  - **Key format**: `"{HTTP_METHOD}:{path}"` (e.g., `"POST:/coaching/alignment-check"`)
  - **Categories**:
    - `onboarding` (4 endpoints)
    - `conversation` (3 endpoints)
    - `insights` (1 endpoint)
    - `strategic_planning` (5 endpoints)
    - `operations_ai` (9 endpoints)
    - `operations_strategic_integration` (22 endpoints)

- [ ] Add helper functions:
  ```python
  def get_endpoint_definition(method: str, path: str) -> EndpointDefinition | None
  def list_endpoints_by_category(category: str) -> list[EndpointDefinition]
  def list_all_endpoints(active_only: bool = True) -> list[EndpointDefinition]
  def get_topic_for_endpoint(method: str, path: str) -> str | None
  ```

- [ ] Add validation:
  - Ensure no duplicate topic_ids
  - Ensure all topic_ids are valid identifiers
  - Ensure all response models exist

**Reference**: See gap analysis document for complete endpoint list

---

#### Task 1.2: Create Topic Seed Data
**File**: `coaching/src/core/topic_seed_data.py`

**Requirements**:
- [ ] Create `TopicSeedData` dataclass with fields:
  - `topic_id: str`
  - `topic_name: str`
  - `topic_type: str` - "conversation_coaching" | "single_shot" | "kpi_system"
  - `category: str`
  - `description: str`
  - `model_code: str` - Default: "anthropic.claude-3-5-sonnet-20241022-v1:0"
  - `temperature: float` - Default: 0.7
  - `max_tokens: int` - Default: 4096
  - `top_p: float` - Default: 1.0
  - `frequency_penalty: float` - Default: 0.0
  - `presence_penalty: float` - Default: 0.0
  - `allowed_parameters: list[dict]` - Parameter schema definitions
  - `default_system_prompt: str` - Default system prompt content
  - `default_user_prompt: str` - Default user prompt content
  - `display_order: int`

- [ ] Create `TOPIC_SEED_DATA: dict[str, TopicSeedData]` with all 44 topics
  - Use existing prompts from hardcoded services as defaults
  - Define parameter schemas for each topic
  - Set appropriate model configurations

- [ ] Add helper function:
  ```python
  def get_seed_data_for_topic(topic_id: str) -> TopicSeedData | None
  def list_all_seed_data() -> list[TopicSeedData]
  ```

**Example**:
```python
TOPIC_SEED_DATA = {
    "alignment_check": TopicSeedData(
        topic_id="alignment_check",
        topic_name="Goal Alignment Check",
        topic_type="single_shot",
        category="strategic_planning",
        description="Calculate alignment score between goal and business foundation",
        model_code="anthropic.claude-3-5-sonnet-20241022-v1:0",
        temperature=0.7,
        max_tokens=2048,
        allowed_parameters=[
            {"name": "goal", "type": "object", "required": True},
            {"name": "businessFoundation", "type": "object", "required": True}
        ],
        default_system_prompt="You are an AI alignment analyst...",
        default_user_prompt="Analyze alignment for:\nGoal: {goal}\nFoundation: {businessFoundation}",
        display_order=10
    ),
    # ... 43 more topics
}
```

---

#### Task 1.3: Topic Seeding Service
**File**: `coaching/src/services/topic_seeding_service.py`

**Requirements**:
- [ ] Create `TopicSeedingService` class with methods:

  ```python
  class TopicSeedingService:
      def __init__(
          self,
          topic_repo: TopicRepository,
          s3_storage: S3PromptStorage,
      ):
          ...

      async def seed_all_topics(
          self,
          force_update: bool = False,
          dry_run: bool = False,
      ) -> SeedingResult:
          """Seed all topics from ENDPOINT_REGISTRY and TOPIC_SEED_DATA.

          Args:
              force_update: Update existing topics even if they exist
              dry_run: Don't make changes, just report what would happen

          Returns:
              SeedingResult with created/updated/deactivated counts
          """
          ...

      async def seed_topic(
          self,
          topic_id: str,
          force_update: bool = False,
      ) -> bool:
          """Seed a single topic."""
          ...

      async def deactivate_orphaned_topics(
          self,
          dry_run: bool = False,
      ) -> list[str]:
          """Deactivate topics that no longer have endpoints.

          Returns:
              List of deactivated topic IDs
          """
          ...

      async def validate_topics(self) -> ValidationReport:
          """Validate all topics against endpoint registry.

          Checks:
          - All endpoints have topics
          - All topics have endpoints (or are orphaned)
          - All prompts exist in S3
          - All parameter schemas are valid
          """
          ...
  ```

- [ ] Create `SeedingResult` dataclass:
  ```python
  @dataclass
  class SeedingResult:
      created: list[str]          # New topics created
      updated: list[str]          # Existing topics updated
      skipped: list[str]          # Topics skipped (already exist)
      deactivated: list[str]      # Orphaned topics deactivated
      errors: list[tuple[str, str]]  # (topic_id, error_message)
  ```

- [ ] Create `ValidationReport` dataclass:
  ```python
  @dataclass
  class ValidationReport:
      missing_topics: list[str]       # Endpoints without topics
      orphaned_topics: list[str]      # Topics without endpoints
      missing_prompts: list[str]      # Topics missing S3 prompts
      invalid_parameters: list[str]   # Topics with invalid parameter schemas
      is_valid: bool
  ```

**Seeding Logic**:
1. Load all endpoint definitions from `ENDPOINT_REGISTRY`
2. For each endpoint:
   - Check if topic exists in DynamoDB
   - If not exists: Create from `TOPIC_SEED_DATA`
   - If exists and `force_update=True`: Update from seed data
   - Create S3 prompts if they don't exist
3. Find orphaned topics (topics in DB but not in registry)
4. Deactivate orphaned topics (set `is_active=False`)
5. Return `SeedingResult` with summary

---

#### Task 1.4: CLI Command for Seeding
**File**: `coaching/src/scripts/seed_topics.py`

**Requirements**:
- [ ] Create CLI script with arguments:
  ```bash
  python -m coaching.src.scripts.seed_topics \
      --force-update \
      --dry-run \
      --topic-id alignment_check \
      --validate-only
  ```

- [ ] Arguments:
  - `--force-update`: Update existing topics
  - `--dry-run`: Report changes without applying
  - `--topic-id`: Seed specific topic (optional)
  - `--validate-only`: Just run validation report
  - `--deactivate-orphans`: Deactivate topics without endpoints

- [ ] Output:
  - Colored console output
  - Summary table
  - Error details
  - Validation warnings

**Example Output**:
```
Topic Seeding Report
====================

Created Topics (23):
  ✅ alignment_check
  ✅ strategy_suggestions
  ✅ kpi_recommendations
  ...

Updated Topics (4):
  🔄 core_values (updated model config)
  🔄 purpose (updated prompts)
  ...

Skipped Topics (15):
  ⏭️  vision (already exists, no force-update)
  ...

Deactivated Topics (2):
  ⚠️  old_topic_1 (no endpoint)
  ⚠️  old_topic_2 (no endpoint)

Errors (0):

Summary:
  Total Topics: 44
  Created: 23
  Updated: 4
  Skipped: 15
  Deactivated: 2
  Errors: 0

✅ Seeding completed successfully
```

---

### Phase 2: Unified AI Engine

#### Task 2.1: Response Serializer
**File**: `coaching/src/application/ai_engine/response_serializer.py`

**Requirements**:
- [ ] Create `ResponseSerializer` class:
  ```python
  class ResponseSerializer:
      async def serialize(
          self,
          ai_response: str,
          response_model: Type[BaseModel],
          topic_id: str,
      ) -> BaseModel:
          """Serialize AI text response to structured model."""
          ...

      async def serialize_conversation(
          self,
          ai_response: str,
          topic: LLMTopic,
      ) -> ConversationResponse:
          """Serialize conversation response with special handling."""
          ...
  ```

- [ ] Serialization strategies:
  1. Try JSON parsing first (for structured output)
  2. Use regex extraction for known patterns
  3. Fall back to LLM-assisted parsing if needed

- [ ] Add validation after serialization
- [ ] Log serialization failures for debugging

---

#### Task 2.2: Unified AI Engine - Single Shot
**File**: `coaching/src/application/ai_engine/unified_ai_engine.py`

**Requirements**:
- [ ] Create `UnifiedAIEngine` class:
  ```python
  class UnifiedAIEngine:
      def __init__(
          self,
          topic_repo: TopicRepository,
          s3_storage: S3PromptStorage,
          provider_manager: ProviderManager,
          response_serializer: ResponseSerializer,
          cache_service: CacheService,
      ):
          ...

      async def execute_single_shot(
          self,
          topic_id: str,
          parameters: dict[str, Any],
          response_model: Type[BaseModel],
          user_context: RequestContext,
      ) -> BaseModel:
          """Execute single-shot AI request using topic configuration.

          Flow:
          1. Get topic configuration from DynamoDB
          2. Validate parameters against topic schema
          3. Load prompts from S3
          4. Render prompts with parameters
          5. Call LLM using topic model config
          6. Serialize response to expected model
          7. Cache result
          """
          ...
  ```

- [ ] Implement caching strategy:
  - Cache key: `hash(topic_id + parameters)`
  - TTL: Configurable per topic
  - Invalidation: On topic update

- [ ] Add telemetry:
  - Log topic_id, model, tokens used
  - Track execution time
  - Track cache hit/miss

- [ ] Error handling:
  - Topic not found
  - Prompt not found
  - Parameter validation failure
  - LLM provider errors
  - Serialization errors

---

#### Task 2.3: Unified AI Engine - Conversation
**File**: `coaching/src/application/ai_engine/unified_ai_engine.py`

**Requirements**:
- [ ] Add conversation methods to `UnifiedAIEngine`:
  ```python
  async def initiate_conversation(
      self,
      topic_id: str,
      user_context: RequestContext,
      initial_parameters: dict[str, Any] | None = None,
  ) -> ConversationResponse:
      """Start new conversation using topic configuration."""
      ...

  async def send_message(
      self,
      conversation_id: str,
      user_message: str,
      user_context: RequestContext,
  ) -> MessageResponse:
      """Send message in existing conversation."""
      ...

  async def pause_conversation(
      self,
      conversation_id: str,
  ) -> None:
      """Pause conversation (save state)."""
      ...

  async def resume_conversation(
      self,
      conversation_id: str,
  ) -> ConversationResponse:
      """Resume paused conversation."""
      ...

  async def complete_conversation(
      self,
      conversation_id: str,
  ) -> BaseModel:
      """Mark conversation complete and extract final result."""
      ...
  ```

- [ ] Conversation memory management:
  - Load conversation history from DynamoDB
  - Maintain context window (last N messages)
  - Summarize older messages if needed

- [ ] Phase detection:
  - Use topic configuration to determine phases
  - Track progress through conversation
  - Detect completion criteria

---

### Phase 3: Endpoint Migration

#### Task 3.1: Create Generic Route Handler
**File**: `coaching/src/api/routes/generic_ai_handler.py`

**Requirements**:
- [ ] Create generic handler function:
  ```python
  async def handle_ai_request(
      request: BaseModel,
      http_method: str,
      endpoint_path: str,
      user_context: RequestContext,
      ai_engine: UnifiedAIEngine,
  ) -> BaseModel:
      """Generic handler for all AI endpoints.

      Steps:
      1. Lookup endpoint in registry
      2. Get topic_id
      3. Validate request against topic parameters
      4. Execute via UnifiedAIEngine
      5. Return response
      """
      ...
  ```

- [ ] Support both single-shot and conversation endpoints
- [ ] Automatic request/response validation
- [ ] Consistent error handling

---

#### Task 3.2: Migrate Strategic Planning Endpoints (5)
**Files**:
- `coaching/src/api/routes/coaching_ai.py`
- `coaching/src/api/routes/analysis.py`

**Requirements**:
- [ ] Migrate endpoints to use `UnifiedAIEngine`:
  - `POST /coaching/strategy-suggestions`
  - `POST /coaching/alignment-check` (fix path from `/analysis/alignment`)
  - `POST /coaching/kpi-recommendations` (fix path from `/analysis/kpi`)
  - `POST /coaching/alignment-explanation`
  - `POST /coaching/alignment-suggestions`

- [ ] Update route handlers to use generic handler
- [ ] Remove old service classes (AlignmentService, StrategyService, KPIService)
- [ ] Add integration tests for each endpoint

---

#### Task 3.3: Migrate Operations AI Endpoints (9)
**File**: `coaching/src/api/routes/operations_ai.py`

**Requirements**:
- [ ] Migrate endpoints:
  - `POST /operations/root-cause-suggestions`
  - `POST /operations/swot-analysis` (implement missing)
  - `POST /operations/five-whys-questions` (implement missing)
  - `POST /operations/action-suggestions`
  - `POST /operations/optimize-action-plan`
  - `POST /operations/prioritization-suggestions`
  - `POST /operations/scheduling-suggestions`
  - `POST /operations/categorize-issue` (implement missing)
  - `POST /operations/assess-impact` (implement missing)

- [ ] Use `UnifiedAIEngine`
- [ ] Remove old service classes
- [ ] Add tests

---

#### Task 3.4: Migrate Onboarding & Conversation Endpoints (8)
**Files**:
- `coaching/src/api/routes/website.py`
- `coaching/src/api/routes/suggestions.py`
- `coaching/src/api/routes/coaching.py`
- `coaching/src/api/routes/conversations.py`

**Requirements**:
- [ ] Migrate single-shot endpoints:
  - `POST /website/scan`
  - `POST /suggestions/onboarding`
  - `POST /coaching/onboarding`
  - `GET /multitenant/conversations/business-data`
  - `POST /insights/generate`

- [ ] Migrate conversation endpoints:
  - `POST /conversations/initiate`
  - `POST /conversations/{id}/message`
  - `GET /conversations/{id}`

- [ ] Use `UnifiedAIEngine` for both types
- [ ] Maintain backward compatibility

---

#### Task 3.5: Implement Missing Operations-Strategic Integration (22)
**File**: `coaching/src/api/routes/operations_strategic_integration.py` (new)

**Requirements**:
- [ ] Create new router for integration endpoints
- [ ] Implement all 22 missing endpoints using `UnifiedAIEngine`
- [ ] Create topics for each endpoint
- [ ] Write comprehensive tests

**Note**: This is a large task and should be broken into sub-tasks

---

### Phase 4: Admin UI & Testing

#### Task 4.1: Update Admin Topic Routes
**File**: `coaching/src/api/routes/admin/topics.py`

**Requirements**:
- [ ] Update endpoints to use `ENDPOINT_REGISTRY`:
  - `GET /admin/topics` - List all topics from registry
  - `GET /admin/topics/{topic_id}` - Get topic details
  - `PUT /admin/topics/{topic_id}` - Update topic configuration
  - `PUT /admin/topics/{topic_id}/prompts` - Update prompts
  - `POST /admin/topics/{topic_id}/test` - Test topic with sample input

- [ ] Add validation:
  - Only allow editing active topics
  - Validate model configurations
  - Validate parameter schemas

- [ ] Add versioning:
  - Track prompt versions in S3
  - Allow rollback to previous version

---

#### Task 4.2: Admin Prompt Editor
**File**: `coaching/src/api/routes/admin/prompts.py`

**Requirements**:
- [ ] Create endpoints:
  - `GET /admin/topics/{topic_id}/prompts/{type}` - Get prompt content
  - `PUT /admin/topics/{topic_id}/prompts/{type}` - Update prompt
  - `GET /admin/topics/{topic_id}/prompts/{type}/versions` - List versions
  - `POST /admin/topics/{topic_id}/prompts/{type}/rollback` - Rollback

- [ ] Support markdown editing
- [ ] Support variable validation
- [ ] Preview prompt rendering

---

#### Task 4.3: Topic Testing & Preview
**File**: `coaching/src/api/routes/admin/topic_testing.py`

**Requirements**:
- [ ] Create testing endpoint:
  ```python
  POST /admin/topics/{topic_id}/test
  {
    "parameters": { ... },  # Test parameters
    "use_draft": true        # Use draft prompts (not saved)
  }
  ```

- [ ] Return:
  - AI response
  - Serialized result
  - Tokens used
  - Execution time
  - Any errors

- [ ] Support draft mode (test without saving)

---

#### Task 4.4: Integration Tests
**File**: `coaching/tests/integration/test_unified_ai_engine.py`

**Requirements**:
- [ ] Test seeding service:
  - Seed all topics
  - Validate topics
  - Deactivate orphans
  - Force update
  - Dry run mode

- [ ] Test unified engine:
  - Single-shot execution
  - Conversation flow
  - Parameter validation
  - Response serialization
  - Caching
  - Error handling

- [ ] Test endpoint migration:
  - All 44 endpoints work
  - Backward compatibility
  - Performance benchmarks

---

## Success Criteria

- [ ] All 44 topics exist in DynamoDB
- [ ] All 44 prompts exist in S3
- [ ] All 44 endpoints use `UnifiedAIEngine`
- [ ] Seeding service runs successfully
- [ ] Admin can edit topics without deployment
- [ ] All tests pass
- [ ] Performance is equivalent or better than before
- [ ] Documentation is complete

---

## Technical Specifications

### Database Schema

**DynamoDB Table: `coaching_topics_{env}`**
```
Primary Key: topic_id (String)
GSI: topic_type-display_order-index

Attributes:
- topic_id: String (PK)
- topic_name: String
- topic_type: String (GSI)
- category: String
- is_active: Boolean
- model_code: String
- temperature: Number
- max_tokens: Number
- top_p: Number
- frequency_penalty: Number
- presence_penalty: Number
- allowed_parameters: List<Map>
- prompts: List<Map>
- created_at: String (ISO 8601)
- updated_at: String (ISO 8601)
- description: String
- display_order: Number (GSI sort key)
- created_by: String
- additional_config: Map
```

### S3 Bucket Structure

**Bucket: `purposepath-prompts-{env}`**
```
prompts/
├── alignment_check/
│   ├── system.md
│   ├── user.md
│   └── versions/
│       ├── v1_20250101_120000.md
│       └── v2_20250115_143000.md
├── strategy_suggestions/
│   ├── system.md
│   └── user.md
...
```

### API Response Format

**Standard Response**:
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "topic_id": "alignment_check",
    "model_used": "claude-3-5-sonnet",
    "tokens_used": 1234,
    "execution_time_ms": 450
  }
}
```

---

## Dependencies

- Existing `LLMTopic` entity
- Existing `TopicRepository`
- Existing `S3PromptStorage`
- Existing `ProviderManager`
- DynamoDB table (already exists)
- S3 bucket (already exists)

---

## Migration Strategy

### Backward Compatibility

During migration, support both old and new approaches:
1. Keep old service classes temporarily
2. Add feature flag: `USE_UNIFIED_ENGINE`
3. Gradually migrate endpoints
4. Remove old services after all endpoints migrated

### Rollback Plan

If issues arise:
1. Disable `USE_UNIFIED_ENGINE` flag
2. Revert to old service classes
3. Keep topic data (no data loss)

---

## Testing Checklist

- [ ] Unit tests for seeding service
- [ ] Unit tests for unified engine
- [ ] Unit tests for response serializer
- [ ] Integration tests for each endpoint
- [ ] E2E tests for full workflows
- [ ] Performance benchmarks
- [ ] Load tests with 1000+ requests
- [ ] Admin UI manual testing

---

## Documentation Checklist

- [ ] Architecture diagram
- [ ] Endpoint registry documentation
- [ ] Topic configuration guide
- [ ] Prompt writing guide
- [ ] Admin user guide
- [ ] API documentation updates
- [ ] Migration guide

---

## Timeline Estimate

| Phase | Tasks | Duration | Dependencies |
|-------|-------|----------|--------------|
| Phase 1 | Foundation | 1 week | None |
| Phase 2 | Unified Engine | 1 week | Phase 1 |
| Phase 3 | Endpoint Migration | 2 weeks | Phase 2 |
| Phase 4 | Admin & Testing | 1 week | Phase 3 |
| **Total** | | **5 weeks** | |

---

## Related Issues

- Endpoint Gap Analysis: See `COACHING_SERVICE_ENDPOINT_GAP_ANALYSIS.md`
- Architecture Analysis: See `ENDPOINT_TOPIC_MAPPING_ANALYSIS.md`

---

## Notes

- All prompts should be markdown format
- Prompt variables use `{variable_name}` syntax
- Topics are immutable by admins (only prompts/config editable)
- Orphaned topics are deactivated, not deleted (data preservation)
- Seeding should be idempotent (safe to run multiple times)

---

**Labels**: `enhancement`, `architecture`, `ai-engine`, `priority-high`
**Milestone**: Q1 2025
**Assignee**: Backend Team
