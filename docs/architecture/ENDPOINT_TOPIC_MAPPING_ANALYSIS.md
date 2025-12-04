# Endpoint-Topic Mapping Architecture Analysis

**Date**: 2025-12-02
**Purpose**: Validate alignment between your vision and current implementation
**Status**: ⚠️ **PARTIAL ALIGNMENT** - Core infrastructure exists but endpoint mapping is incomplete

---

## Your Vision vs. Current Implementation

### ✅ What's Already Implemented

#### 1. **Topic System Infrastructure** ✅
- **LLMTopic Entity**: Complete domain entity with all required fields
  - `topic_id`, `topic_name`, `topic_type`
  - Model configuration (model_code, temperature, max_tokens, etc.)
  - Parameter definitions
  - Prompt references (S3)
  - Active/inactive status

#### 2. **S3 Prompt Storage** ✅
- **S3PromptStorage Service**: Fully implemented
  - Stores prompts as markdown files in S3
  - Path structure: `prompts/{topic_id}/{prompt_type}.md`
  - Supports system, user, assistant, function prompt types

#### 3. **Topic Repository** ✅
- **TopicRepository**: Complete CRUD operations
  - Get topic by ID
  - List all topics (with active/inactive filter)
  - List by topic type
  - Create, update, delete topics
  - DynamoDB-backed with proper error handling

#### 4. **Prompt Service** ✅
- **PromptService**: Backward-compatible service
  - Loads topic metadata from DynamoDB
  - Retrieves prompt content from S3
  - Caching with TTL
  - Builds templates with system/user prompts

#### 5. **LLM Provider Abstraction** ✅
- **Pluggable Provider System**: Already exists
  - `BedrockLLMProvider`, `AnthropicProvider`, `OpenAIProvider`
  - `ProviderManager` handles multiple providers
  - Each provider implements standard interface

#### 6. **Admin Routes** ✅ (Partial)
- **Admin Topic Routes**: Exist at `/admin/topics`
- **Admin Prompt Routes**: Exist at `/admin/prompts`
- Currently have legacy implementation that needs alignment

---

### ⚠️ What's Missing or Needs Alignment

#### 1. **Endpoint → Topic Mapping** ❌
**Your Vision**:
> "Since topics are related to a specific endpoint we should create a collection of all endpoints defined in the system"

**Current State**:
- No systematic mapping between endpoints and topics
- Topics are hardcoded in route handlers
- Only 4 conversation topics defined (core_values, purpose, vision, goals)
- 44 frontend endpoints have no topic assignments

**Gap**: Need to create an **Endpoint Registry** that maps each endpoint to its topic configuration.

---

#### 2. **Topic Types Missing** ⚠️
**Your Vision**: Topics cover both single-shot and conversation flows

**Current State**:
- `LLMTopic.topic_type` supports: `conversation_coaching`, `single_shot`, `kpi_system`
- Only `conversation_coaching` topics exist (4 topics)
- No `single_shot` topics for analysis endpoints
- No `kpi_system` topics

**Gap**: Need to create 40+ topics for single-shot analysis endpoints

---

#### 3. **Response Serialization** ⚠️
**Your Vision**:
> "we serialize the response to the expected structure and return the result to the frontend"

**Current State**:
- Each route handler manually constructs responses
- No centralized serialization based on topic configuration
- Response models are hardcoded in route decorators

**Gap**: Need **Response Serializer** that uses topic metadata to format AI responses

---

#### 4. **Conversation Management** ⚠️
**Your Vision**:
> "We manage conversation memory, pause and resume operations"

**Current State**:
- ✅ Conversation memory exists (DynamoDB-backed)
- ✅ Pause/resume endpoints exist
- ⚠️ Not using topic configuration for conversation flow
- ⚠️ Conversation logic is hardcoded, not driven by topic metadata

**Gap**: Conversation workflows should be driven by topic configuration

---

## Architecture Comparison

### Your Vision: Topic-Driven Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Endpoint Registry                      │
│  Maps: POST /coaching/alignment-check → topic_id            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Topic Configuration                       │
│  • topic_id: "alignment_check"                              │
│  • topic_type: "single_shot"                                │
│  • model_code: "claude-3-5-sonnet-20241022"                 │
│  • temperature: 0.7                                          │
│  • prompts: [system.md, user.md]                            │
│  • expected_response: AlignmentAnalysisResponse             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  LLM Provider Manager                        │
│  Pluggable: Bedrock | Anthropic | OpenAI                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Response Serializer                         │
│  Formats AI output → expected response structure            │
└─────────────────────────────────────────────────────────────┘
```

### Current Implementation: Route-Driven Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Routes                              │
│  Each route has hardcoded:                                   │
│  • Service dependencies                                      │
│  • Model selection                                           │
│  • Prompt construction                                       │
│  • Response formatting                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Service Layer (per-analysis)                    │
│  AlignmentService | StrategyService | KPIService            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Providers                             │
│  Bedrock | Anthropic | OpenAI                               │
└─────────────────────────────────────────────────────────────┘
```

**Problem**: Adding a new endpoint requires:
1. Creating new route file
2. Creating new service class
3. Hardcoding prompts
4. Hardcoding response models
5. No admin can modify without code deployment

---

## Detailed Gap Analysis

### Gap 1: Endpoint Registry

**Need**: Central registry mapping endpoints to topics

**Proposed Structure**:
```python
# coaching/src/core/endpoint_registry.py

@dataclass
class EndpointDefinition:
    endpoint_path: str              # "/coaching/alignment-check"
    http_method: str                # "POST"
    topic_id: str                   # "alignment_check"
    response_model: str             # "AlignmentAnalysisResponse"
    requires_conversation: bool     # False (single-shot)

ENDPOINT_REGISTRY: dict[str, EndpointDefinition] = {
    "POST:/coaching/alignment-check": EndpointDefinition(
        endpoint_path="/coaching/alignment-check",
        http_method="POST",
        topic_id="alignment_check",
        response_model="AlignmentAnalysisResponse",
        requires_conversation=False,
    ),
    "POST:/coaching/strategy-suggestions": EndpointDefinition(
        endpoint_path="/coaching/strategy-suggestions",
        http_method="POST",
        topic_id="strategy_suggestions",
        response_model="StrategySuggestionsResponse",
        requires_conversation=False,
    ),
    # ... 42 more endpoints
}
```

**Usage**:
```python
# In route handler
@router.post("/coaching/alignment-check")
async def alignment_check(request: AlignmentRequest):
    endpoint_def = ENDPOINT_REGISTRY["POST:/coaching/alignment-check"]
    topic = await topic_repo.get(topic_id=endpoint_def.topic_id)

    # Use topic configuration for everything
    result = await ai_engine.execute(
        topic=topic,
        parameters=request.dict(),
        response_model=endpoint_def.response_model
    )
    return result
```

---

### Gap 2: Topic Creation for All Endpoints

**Need**: Create 44 topic configurations (one per endpoint)

**Categories**:
1. **Conversation Topics** (4) - ✅ Already exist
   - `core_values`, `purpose`, `vision`, `goals`

2. **Strategic Planning Topics** (5) - ❌ Need to create
   - `strategy_suggestions`
   - `kpi_recommendations`
   - `alignment_check`
   - `alignment_explanation`
   - `alignment_suggestions`

3. **Operations AI Topics** (9) - ❌ Need to create
   - `root_cause_suggestions`
   - `swot_analysis`
   - `five_whys_questions`
   - `action_suggestions`
   - `optimize_action_plan`
   - `prioritization_suggestions`
   - `scheduling_suggestions`
   - `categorize_issue`
   - `assess_impact`

4. **Operations-Strategic Integration Topics** (22) - ❌ Need to create
   - `action_strategic_context`
   - `suggest_connections`
   - ... (20 more)

5. **Onboarding Topics** (4) - ⚠️ Partially exist
   - `website_scan`
   - `onboarding_suggestions`
   - `onboarding_coaching`
   - `business_metrics`

6. **Insights Topics** (1) - ❌ Need to create
   - `insights_generation`

**Each topic needs**:
- DynamoDB record with metadata
- S3 prompts: `system.md` and `user.md`
- Parameter definitions
- Model configuration

---

### Gap 3: Unified AI Engine

**Need**: Single service that handles all AI interactions using topic configuration

**Proposed**:
```python
# coaching/src/application/ai_engine/unified_ai_engine.py

class UnifiedAIEngine:
    """Single entry point for all AI interactions.

    Replaces: AlignmentService, StrategyService, KPIService, etc.
    """

    def __init__(
        self,
        topic_repo: TopicRepository,
        s3_storage: S3PromptStorage,
        provider_manager: ProviderManager,
        response_serializer: ResponseSerializer,
    ):
        self.topic_repo = topic_repo
        self.s3_storage = s3_storage
        self.provider_manager = provider_manager
        self.serializer = response_serializer

    async def execute_single_shot(
        self,
        topic_id: str,
        parameters: dict[str, Any],
        response_model: Type[BaseModel],
    ) -> BaseModel:
        """Execute single-shot AI request.

        Flow matches your vision:
        1. Get topic from DB
        2. Load prompts from S3
        3. Call LLM with topic config
        4. Serialize response to expected structure
        """
        # 1. Get topic configuration
        topic = await self.topic_repo.get(topic_id=topic_id)
        if not topic or not topic.is_active:
            raise TopicNotFoundError(topic_id=topic_id)

        # 2. Load prompts from S3
        system_prompt = await self.s3_storage.load_prompt(
            topic_id=topic_id,
            prompt_type="system"
        )
        user_prompt = await self.s3_storage.load_prompt(
            topic_id=topic_id,
            prompt_type="user"
        )

        # 3. Call LLM using topic configuration
        provider = self.provider_manager.get_provider(topic.model_code)
        ai_response = await provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt.format(**parameters),
            temperature=topic.temperature,
            max_tokens=topic.max_tokens,
            top_p=topic.top_p,
        )

        # 4. Serialize to expected structure
        result = self.serializer.serialize(
            ai_response=ai_response,
            response_model=response_model,
        )
        return result

    async def execute_conversation(
        self,
        topic_id: str,
        conversation_id: str,
        user_message: str,
    ) -> ConversationResponse:
        """Execute conversation-based AI interaction.

        Handles: memory, pause/resume, completion detection
        """
        # Implementation for conversation flow
        ...
```

---

### Gap 4: Response Serializer

**Need**: Service to convert AI text to structured responses

**Proposed**:
```python
# coaching/src/application/ai_engine/response_serializer.py

class ResponseSerializer:
    """Serializes AI responses to expected structures."""

    async def serialize(
        self,
        ai_response: str,
        response_model: Type[BaseModel],
    ) -> BaseModel:
        """Convert AI text response to structured model.

        Options:
        1. Use structured output (Claude/GPT with JSON mode)
        2. Parse markdown/text into model fields
        3. Use function calling to enforce structure
        """
        # Try to parse as JSON first
        try:
            data = json.loads(ai_response)
            return response_model(**data)
        except json.JSONDecodeError:
            # Fall back to LLM-assisted parsing
            parsed = await self._llm_parse(ai_response, response_model)
            return parsed
```

---

### Gap 5: Admin UI Integration

**Your Vision**:
> Admin frontend get a list of topics
> Admin select a topic to view/edit (admin can not change topics)
> Admin configure topic and associated templates

**Current State**:
- Admin routes exist (`/admin/topics`, `/admin/prompts`)
- Need to update to:
  1. List all 44 endpoint-topics
  2. Allow editing topic configuration (model, temperature, etc.)
  3. Allow editing prompts in S3
  4. Preview/test changes before saving
  5. Version control for prompts

**Gap**: Admin UI needs to be aligned with endpoint registry

---

## Migration Path

### Phase 1: Foundation (Week 1)
1. ✅ Create `EndpointRegistry` with all 44 endpoints
2. ✅ Create 44 topic records in DynamoDB (with defaults)
3. ✅ Create initial S3 prompts for each topic (migrate from hardcoded)

### Phase 2: Unified Engine (Week 2)
4. ✅ Build `UnifiedAIEngine` service
5. ✅ Build `ResponseSerializer` service
6. ✅ Migrate 1-2 endpoints to use new engine (proof of concept)

### Phase 3: Migration (Week 3-4)
7. ✅ Migrate all single-shot endpoints to `UnifiedAIEngine`
8. ✅ Migrate conversation endpoints to `UnifiedAIEngine`
9. ✅ Remove old service classes (AlignmentService, StrategyService, etc.)

### Phase 4: Admin Tools (Week 5)
10. ✅ Update admin routes to use endpoint registry
11. ✅ Build prompt editor UI
12. ✅ Add preview/test functionality
13. ✅ Add version control for prompts

---

## Benefits of Your Vision

### ✅ Admin Configurability
- Admins can modify prompts without code changes
- A/B test different prompt strategies
- Quickly adjust model parameters (temperature, max_tokens)
- No deployment needed for prompt changes

### ✅ Consistency
- All endpoints use same flow
- Centralized error handling
- Consistent logging and monitoring
- Easier to maintain

### ✅ Scalability
- Adding new endpoint = adding topic configuration
- No new service classes needed
- Reuse existing infrastructure

### ✅ Testing
- Mock topics for testing
- Test prompts in isolation
- Version control for prompts

---

## Recommendation

**YES, your vision is well-aligned with good architecture patterns**, and the foundation is already in place. The missing pieces are:

1. **Endpoint Registry** (1-2 days)
2. **44 Topic Configurations** (2-3 days)
3. **Unified AI Engine** (3-5 days)
4. **Response Serializer** (2-3 days)
5. **Migrate Endpoints** (5-7 days)
6. **Admin UI Updates** (3-5 days)

**Total Effort**: 3-4 weeks for complete migration

**Immediate Next Step**: Create the Endpoint Registry document and start mapping endpoints to topics. This will serve as the blueprint for all other work.

Would you like me to:
1. Generate the complete Endpoint Registry mapping?
2. Create a template for topic configurations?
3. Draft the Unified AI Engine implementation?

---

**Document Status**: Draft for Review
**Next Actions**: Get stakeholder approval before proceeding with migration
