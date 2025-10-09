# PurposePath AI Coaching Service - Architecture Design Document

**Document Version:** 1.0.0  
**Last Updated:** October 8, 2025  
**Status:** Design - Ready for Implementation  
**Branch:** feature/phase3-service-architecture

---

## Part 1: Architecture Overview, Technology Stack & Patterns

---

## 📋 Executive Summary

This document defines the comprehensive architecture for the PurposePath AI Coaching Service, supporting two primary interaction modes:

1. **One-Shot Analysis**: Instant AI-powered insights for specific business questions (alignment scoring, strategy recommendations, KPI suggestions, operations analysis)
2. **Conversational Coaching**: Multi-turn guided conversations for deep exploration (core values, purpose, vision, goal setting)

The architecture adheres to **Clean Architecture principles** with strong emphasis on:
- **Domain-Driven Design (DDD)** for clear business domain modeling
- **Hexagonal Architecture (Ports & Adapters)** for technology independence
- **CQRS-lite** for separation of read/write concerns
- **Type Safety** with Pydantic models throughout (eliminating `dict[str, Any]`)
- **Dynamic Prompt Management** for runtime-configurable AI interactions
- **Business Context Enrichment** via AWS Step Functions orchestration

---

## 🎯 Business Context & Requirements Summary

### Interaction Modes

#### One-Shot Analysis
**Purpose:** Quick, instant AI-powered analysis without conversation context

**Characteristics:**
- Single request-response cycle
- Pre-defined prompts with dynamic data injection
- Business context enrichment from .NET database
- Structured, predictable outputs
- Stateless (except for auditing)

**Use Cases:**
- Alignment scoring (goal ↔ business foundation)
- Strategy recommendations
- KPI recommendations
- SWOT analysis
- Root cause analysis suggestions
- Action plan generation
- Prioritization suggestions
- Issue categorization

#### Conversational Coaching
**Purpose:** Multi-turn guided conversations with persistent state

**Characteristics:**
- Multi-step workflow with state management
- Adaptive prompts based on conversation history
- Progress tracking and phase management
- Pause/resume capability
- Business context enrichment at session start
- Personalized guidance based on user responses

**Use Cases:**
- Core values discovery (5-7 values through structured exploration)
- Purpose identification (articulating organizational purpose)
- Vision creation (crafting compelling future vision)
- Goal setting (SMART goal formulation with coaching)

### Business Context Enrichment Pattern

For both interaction modes, **enriched business data** from the .NET database is injected into prompts:

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Frontend   │────→│  Coaching API    │────→│ Step Func.  │
│  (React)    │     │  (Python/FastAPI)│     │ Orchestrator│
└─────────────┘     └──────────────────┘     └──────┬──────┘
                                                     │
                                                     ↓
                           ┌────────────────────────────────────┐
                           │    .NET Business Database API      │
                           │  (Goals, Strategies, KPIs, etc.)   │
                           └────────────────────────────────────┘
                                                     │
                                                     ↓
                           ┌────────────────────────────────────┐
                           │  Enriched Context → Prompt Builder │
                           │  (Dynamic Template + Business Data)│
                           └────────────────────────────────────┘
                                                     │
                                                     ↓
                           ┌────────────────────────────────────┐
                           │      LLM Provider (Bedrock)        │
                           │   (Claude 3.5 Sonnet / Llama)      │
                           └────────────────────────────────────┘
```

**Key Design Principle:** Business context enrichment should be:
1. **Encapsulated** - Changes to enrichment data don't affect core logic
2. **Flexible** - Easy to add/remove data elements
3. **Prompt-Aware** - Template placeholders dynamically accommodate new data
4. **Version-Controlled** - Prompt templates track which data they expect

---

## 🏗️ Architectural Patterns & Principles

### 1. Hexagonal Architecture (Ports & Adapters)

**Core Domain** (Business Logic):
- Pure domain models and business rules
- Independent of frameworks and infrastructure
- Testable without external dependencies

**Ports** (Interfaces):
- Input ports: API handlers, workflow triggers
- Output ports: Repository interfaces, LLM provider interfaces, external service interfaces

**Adapters**:
- Inbound: FastAPI routes, AWS Lambda handlers
- Outbound: DynamoDB repositories, S3 prompt storage, Bedrock LLM clients, Step Functions orchestration

**Benefits:**
- Technology independence (swap DynamoDB for PostgreSQL without touching domain)
- Testability (mock adapters in tests)
- Clear separation of concerns

### 2. Domain-Driven Design (DDD)

**Strategic Design:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Coaching Bounded Context                 │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Conversation    │  │   Analysis       │               │
│  │  Subdomain       │  │   Subdomain      │               │
│  │                  │  │                  │               │
│  │ - Core Values    │  │ - Alignment      │               │
│  │ - Purpose        │  │ - Strategy       │               │
│  │ - Vision         │  │ - KPI Selection  │               │
│  │ - Goal Setting   │  │ - Operations AI  │               │
│  └──────────────────┘  └──────────────────┘               │
│                                                             │
│  ┌─────────────────────────────────────────────────┐       │
│  │         Prompt Management Subdomain             │       │
│  │  - Template versioning                          │       │
│  │  - Dynamic placeholder resolution               │       │
│  │  - Context enrichment strategies                │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

**Tactical Design:**

**Entities:**
- `Conversation` (aggregate root for conversational coaching)
- `AnalysisRequest` (value object for one-shot analysis)
- `PromptTemplate` (aggregate root for prompt management)

**Value Objects:**
- `Message` (role + content + timestamp)
- `ConversationContext` (phase, insights, progress)
- `AlignmentScore` (score + breakdown + suggestions)
- `StrategyRecommendation` (description + rationale + feasibility)

**Aggregates:**
- Conversation aggregate (maintains consistency of messages, context, phase transitions)
- Prompt template aggregate (ensures template versioning integrity)

**Domain Services:**
- `AlignmentCalculationService` (complex scoring algorithm)
- `PromptEnrichmentService` (business context injection)
- `ConversationFlowService` (phase transitions and completion logic)

**Domain Events:**
- `ConversationInitiated`
- `MessageAdded`
- `ConversationCompleted`
- `AnalysisRequested`
- `AnalysisCompleted`

### 3. CQRS-lite (Command Query Responsibility Segregation)

**Separation of Concerns:**

**Commands** (Write Operations):
- `InitiateConversationCommand`
- `SendMessageCommand`
- `CompleteConversationCommand`
- `RequestAnalysisCommand`

**Queries** (Read Operations):
- `GetConversationQuery`
- `ListUserConversationsQuery`
- `GetInsightsQuery`
- `GetAlignmentScoreQuery`

**Implementation:**
- Commands handled by service layer (business logic)
- Queries handled by repository layer (optimized reads)
- No shared models between commands and queries (separate request/response DTOs)

### 4. Strategy Pattern (Interchangeable Components)

**LLM Provider Strategy:**
```python
class LLMProviderStrategy(Protocol):
    async def generate_response(self, prompt: EnrichedPrompt) -> LLMResponse: ...
    async def stream_response(self, prompt: EnrichedPrompt) -> AsyncIterator[str]: ...

# Implementations:
- BedrockClaudeStrategy
- BedrockLlamaStrategy
- AnthropicStrategy
- OpenAIStrategy
```

**Prompt Strategy:**
```python
class PromptStrategy(Protocol):
    async def build_prompt(self, template: PromptTemplate, context: BusinessContext) -> EnrichedPrompt: ...
    
# Implementations:
- AlignmentScoringPromptStrategy
- StrategySuggestionPromptStrategy
- CoreValuesCoachingPromptStrategy
- SWOTAnalysisPromptStrategy
```

**Context Enrichment Strategy:**
```python
class EnrichmentStrategy(Protocol):
    async def enrich(self, base_data: dict[str, Any]) -> EnrichedContext: ...

# Implementations:
- GoalAlignmentEnrichmentStrategy (fetches goals, strategies, KPIs)
- OperationsEnrichmentStrategy (fetches issues, actions, history)
- CoachingEnrichmentStrategy (fetches business foundation, user profile)
```

### 5. Template Method Pattern (Unified Workflows)

**Base Analysis Workflow:**
```python
class BaseAnalysisWorkflow(ABC):
    async def execute(self, request: AnalysisRequest) -> AnalysisResponse:
        # Template method defining steps
        validated_request = await self.validate_request(request)
        enriched_context = await self.enrich_context(validated_request)
        prompt = await self.build_prompt(enriched_context)
        llm_response = await self.invoke_llm(prompt)
        parsed_response = await self.parse_response(llm_response)
        return await self.format_response(parsed_response)
    
    @abstractmethod
    async def validate_request(self, request: AnalysisRequest) -> ValidatedRequest: ...
    
    @abstractmethod
    async def enrich_context(self, request: ValidatedRequest) -> EnrichedContext: ...
    
    # ... other abstract methods
```

**Implementations:**
- `AlignmentAnalysisWorkflow`
- `StrategyRecommendationWorkflow`
- `SWOTAnalysisWorkflow`
- `ActionPlanGenerationWorkflow`

### 6. Repository Pattern (Data Access Abstraction)

**Interfaces (Ports):**
```python
class ConversationRepositoryPort(Protocol):
    async def create(self, conversation: Conversation) -> Conversation: ...
    async def get(self, conversation_id: str) -> Optional[Conversation]: ...
    async def update(self, conversation: Conversation) -> None: ...
    async def list_by_user(self, user_id: str, filters: ConversationFilters) -> List[Conversation]: ...

class PromptRepositoryPort(Protocol):
    async def get_template(self, topic: str, version: str = "latest") -> PromptTemplate: ...
    async def list_templates(self, topic: Optional[str] = None) -> List[PromptTemplateMetadata]: ...
    async def save_template(self, template: PromptTemplate) -> None: ...
```

**Implementations (Adapters):**
- `DynamoDBConversationRepository`
- `S3PromptRepository`
- `RedisConversationCache`

### 7. Dependency Injection (FastAPI Depends)

**Service Resolution:**
```python
# Dependency injection container
async def get_conversation_service(
    repo: ConversationRepository = Depends(get_conversation_repository),
    llm_service: LLMService = Depends(get_llm_service),
    cache_service: CacheService = Depends(get_cache_service),
    prompt_service: PromptService = Depends(get_prompt_service),
    enrichment_service: EnrichmentService = Depends(get_enrichment_service),
) -> ConversationService:
    return ConversationService(
        conversation_repo=repo,
        llm_service=llm_service,
        cache_service=cache_service,
        prompt_service=prompt_service,
        enrichment_service=enrichment_service,
    )

# Usage in routes
@router.post("/conversations/initiate")
async def initiate_conversation(
    request: InitiateConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
    context: RequestContext = Depends(get_current_context),
) -> ApiResponse[ConversationResponse]:
    return await service.initiate_conversation(request, context)
```

**Benefits:**
- Testability (inject mocks)
- Flexibility (swap implementations)
- Clear dependencies

### 8. Interface Segregation (Small, Focused Contracts)

**Principle:** Clients shouldn't depend on interfaces they don't use

**Example:**
```python
# ❌ Fat interface
class CoachingService:
    async def initiate_conversation(...) -> Conversation: ...
    async def send_message(...) -> MessageResponse: ...
    async def calculate_alignment(...) -> AlignmentScore: ...
    async def generate_strategies(...) -> List[Strategy]: ...
    async def recommend_kpis(...) -> List[KPI]: ...
    # Too many responsibilities!

# ✅ Segregated interfaces
class ConversationManagementPort(Protocol):
    async def initiate_conversation(...) -> Conversation: ...
    async def send_message(...) -> MessageResponse: ...

class AlignmentAnalysisPort(Protocol):
    async def calculate_alignment(...) -> AlignmentScore: ...

class StrategyRecommendationPort(Protocol):
    async def generate_strategies(...) -> List[Strategy]: ...

class KPIRecommendationPort(Protocol):
    async def recommend_kpis(...) -> List[KPI]: ...
```

---

## 🛠️ Technology Stack

### Core Framework & Language
- **Python 3.11+** - Latest stable version with modern type hints
- **FastAPI 0.109+** - Modern async web framework with automatic OpenAPI docs
- **Pydantic 2.5+** - Data validation and settings management with strong typing
- **Mangum 0.17+** - ASGI adapter for AWS Lambda

### AI/LLM Orchestration
- **LangChain 0.3+** - LLM application framework
  - `langchain-core` - Core abstractions
  - `langchain-community` - Community integrations
  - `langchain-aws` - AWS Bedrock integration
  - `langchain-anthropic` - Direct Anthropic API (backup)
  - `langchain-openai` - OpenAI integration (future)
- **LangGraph 0.2+** - Workflow orchestration for multi-step AI interactions
- **LangSmith 0.1+** - Observability and debugging for LLM applications
- **Tiktoken 0.8+** - Token counting and cost estimation

### AWS Services
- **Amazon Bedrock** - Managed LLM service (Claude 3.5 Sonnet, Llama 3)
- **AWS Lambda** - Serverless compute
- **Amazon DynamoDB** - NoSQL database for conversations, sessions, analytics
- **Amazon S3** - Prompt template storage, conversation exports
- **AWS Step Functions** - Orchestration for business context enrichment
- **Amazon ElastiCache (Redis)** - Session management, caching
- **AWS Secrets Manager** - API keys and credentials
- **Amazon CloudWatch** - Logging, metrics, alarms
- **AWS X-Ray** - Distributed tracing

### Data & Caching
- **Redis 5.0+** - In-memory cache for:
  - Active conversation sessions
  - Prompt template caching
  - LLM response caching (for identical requests)
  - Rate limiting state
- **DynamoDB** - Persistent storage for:
  - Conversations (with TTL for automatic cleanup)
  - Prompt templates metadata
  - User insights and recommendations
  - Analytics and usage metrics

### Development & Quality Tools
- **uv** - Fast Python package installer and resolver
- **pytest 7.4+** - Testing framework with async support
- **pytest-asyncio** - Async test support
- **pytest-mock** - Mocking utilities
- **pytest-cov** - Coverage reporting
- **Black 23.7+** - Code formatter
- **Ruff 0.1+** - Fast Python linter
- **mypy 1.4+** - Static type checker
- **structlog 23.2+** - Structured logging
- **httpx 0.25+** - Async HTTP client for testing

### Deployment & Infrastructure
- **AWS SAM (Serverless Application Model)** - IaC for serverless apps
- **Docker** - Local development containers
- **GitHub Actions** - CI/CD pipelines
- **AWS CodePipeline** - Deployment automation (production)

---

## 📐 High-Level System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Frontend (React)                                    │
│                      TypeScript, API Clients                                 │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTPS/REST
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      API Gateway (AWS)                                       │
│              /coaching/api/v1/*  →  Coaching Lambda                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Coaching Service (Lambda)                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     API Layer (FastAPI)                              │  │
│  │  - Routes (coaching, conversations, insights, suggestions)           │  │
│  │  - Request validation (Pydantic models)                              │  │
│  │  - Authentication & authorization                                    │  │
│  │  - Response serialization                                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Service Layer                                     │  │
│  │                                                                      │  │
│  │  ┌────────────────────┐  ┌────────────────────┐                     │  │
│  │  │  Conversation      │  │   Analysis         │                     │  │
│  │  │  Service           │  │   Services         │                     │  │
│  │  │                    │  │                    │                     │  │
│  │  │ - initiate()       │  │ - alignment()      │                     │  │
│  │  │ - send_message()   │  │ - strategies()     │                     │  │
│  │  │ - pause/resume()   │  │ - kpis()           │                     │  │
│  │  │ - complete()       │  │ - swot()           │                     │  │
│  │  └────────────────────┘  │ - root_cause()     │                     │  │
│  │                          │ - action_plan()    │                     │  │
│  │                          └────────────────────┘                     │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────┐        │  │
│  │  │         Enrichment Service                             │        │  │
│  │  │  - Orchestrates Step Functions for context             │        │  │
│  │  │  - Aggregates business data from .NET API              │        │  │
│  │  │  - Caches enriched context                             │        │  │
│  │  └────────────────────────────────────────────────────────┘        │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────┐        │  │
│  │  │         Prompt Service                                 │        │  │
│  │  │  - Retrieves templates from S3/cache                   │        │  │
│  │  │  - Resolves dynamic placeholders                       │        │  │
│  │  │  - Injects enriched context                            │        │  │
│  │  │  - Manages template versions                           │        │  │
│  │  └────────────────────────────────────────────────────────┘        │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────┐        │  │
│  │  │         LLM Service                                    │        │  │
│  │  │  - Provider abstraction (Strategy pattern)             │        │  │
│  │  │  - Request/response handling                           │        │  │
│  │  │  - Streaming support                                   │        │  │
│  │  │  - Token tracking and cost monitoring                  │        │  │
│  │  └────────────────────────────────────────────────────────┘        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    Domain Layer                                      │  │
│  │  - Entities (Conversation, PromptTemplate)                           │  │
│  │  - Value Objects (Message, AlignmentScore, Strategy)                 │  │
│  │  - Domain Services (alignment calculation, phase transitions)        │  │
│  │  - Business Rules (validation, constraints)                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ↓                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                  Infrastructure Layer                                │  │
│  │                                                                      │  │
│  │  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────────┐   │  │
│  │  │  Repositories   │  │  LLM         │  │  External Services   │   │  │
│  │  │                 │  │  Providers   │  │                      │   │  │
│  │  │ - Conversation  │  │              │  │ - Step Functions     │   │  │
│  │  │ - Prompt        │  │ - Bedrock    │  │ - .NET Business API  │   │  │
│  │  │ - Insights      │  │ - Anthropic  │  │                      │   │  │
│  │  │                 │  │ - OpenAI     │  │                      │   │  │
│  │  └─────────────────┘  └──────────────┘  └──────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ↓                ↓                ↓
        ┌──────────────────┐  ┌─────────────┐  ┌──────────────┐
        │   DynamoDB       │  │  S3 Bucket  │  │    Redis     │
        │  (Conversations) │  │  (Prompts)  │  │   (Cache)    │
        └──────────────────┘  └─────────────┘  └──────────────┘
```

### Context Enrichment Flow (via Step Functions)

```
┌─────────────┐
│  Coaching   │
│  Service    │
└──────┬──────┘
       │ 1. Request analysis with user_id, tenant_id, request_type
       ↓
┌─────────────────────────────────────────────────────────┐
│          AWS Step Functions Orchestrator                │
│                                                         │
│  State Machine: EnrichmentOrchestrator                  │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │  Step 1: Determine Required Context           │     │
│  │  - Based on request_type, identify data needs │     │
│  └───────────────┬───────────────────────────────┘     │
│                  ↓                                      │
│  ┌───────────────────────────────────────────────┐     │
│  │  Step 2: Parallel Context Fetch               │     │
│  │  ┌───────────┐  ┌───────────┐  ┌──────────┐  │     │
│  │  │  Lambda:  │  │  Lambda:  │  │ Lambda:  │  │     │
│  │  │  GetGoals │  │  GetKPIs  │  │ GetUser  │  │     │
│  │  │           │  │           │  │ Profile  │  │     │
│  │  └─────┬─────┘  └─────┬─────┘  └────┬─────┘  │     │
│  │        │              │              │        │     │
│  │        └──────────────┼──────────────┘        │     │
│  │                       │                       │     │
│  │           Calls .NET Business API             │     │
│  └───────────────────────┼───────────────────────┘     │
│                          ↓                              │
│  ┌───────────────────────────────────────────────┐     │
│  │  Step 3: Aggregate & Structure Context        │     │
│  │  - Combine all fetched data                   │     │
│  │  - Apply business rules                       │     │
│  │  - Format for prompt injection                │     │
│  └───────────────┬───────────────────────────────┘     │
│                  ↓                                      │
│  ┌───────────────────────────────────────────────┐     │
│  │  Step 4: Return Enriched Context              │     │
│  │  {                                            │     │
│  │    "goals": [...],                            │     │
│  │    "strategies": [...],                       │     │
│  │    "kpis": [...],                             │     │
│  │    "business_foundation": {...},              │     │
│  │    "user_preferences": {...}                  │     │
│  │  }                                            │     │
│  └───────────────┬───────────────────────────────┘     │
└──────────────────┼─────────────────────────────────────┘
                   │
                   ↓ 2. Enriched context returned
┌─────────────────────────────────┐
│  Prompt Service                 │
│  - Loads template               │
│  - Injects enriched context     │
│  - Resolves placeholders        │
└─────────────┬───────────────────┘
              │
              ↓ 3. Final prompt
┌─────────────────────────────────┐
│  LLM Service                    │
│  - Sends to Bedrock             │
│  - Returns AI response          │
└─────────────────────────────────┘
```

---

## 🗂️ Module Organization & Layer Structure

### Directory Structure

```
coaching/
├── src/
│   ├── __init__.py
│   ├── py.typed                    # Type checking marker
│   │
│   ├── api/                        # 🔵 API/Presentation Layer
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app initialization
│   │   ├── dependencies.py         # Dependency injection setup
│   │   ├── auth.py                 # Authentication/authorization
│   │   ├── middleware/             # Request/response middleware
│   │   │   ├── logging.py
│   │   │   ├── error_handling.py
│   │   │   └── rate_limiting.py
│   │   └── routes/                 # API endpoint handlers
│   │       ├── coaching.py         # Coaching endpoints (stub routes)
│   │       ├── conversations.py    # Conversation management
│   │       ├── insights.py         # Insights and recommendations
│   │       ├── suggestions.py      # AI-powered suggestions
│   │       ├── alignment.py        # Alignment analysis endpoints
│   │       ├── strategy.py         # Strategy recommendation endpoints
│   │       ├── kpi.py              # KPI recommendation endpoints
│   │       ├── operations.py       # Operations AI endpoints
│   │       └── health.py           # Health checks
│   │
│   ├── services/                   # 🟢 Application/Service Layer
│   │   ├── __init__.py
│   │   │
│   │   ├── conversation/           # Conversational coaching services
│   │   │   ├── conversation_service.py         # Main orchestrator
│   │   │   ├── conversation_flow_service.py    # Phase management
│   │   │   └── conversation_memory_service.py  # Memory & summarization
│   │   │
│   │   ├── analysis/               # One-shot analysis services
│   │   │   ├── alignment_service.py
│   │   │   ├── strategy_service.py
│   │   │   ├── kpi_service.py
│   │   │   ├── swot_service.py
│   │   │   ├── root_cause_service.py
│   │   │   ├── action_plan_service.py
│   │   │   └── base_analysis_service.py  # Abstract base
│   │   │
│   │   ├── llm/                    # LLM interaction services
│   │   │   ├── llm_service.py              # Main LLM orchestrator
│   │   │   ├── llm_service_adapter.py      # Legacy compatibility
│   │   │   └── response_parser_service.py  # Parse structured outputs
│   │   │
│   │   ├── enrichment/             # Context enrichment services
│   │   │   ├── enrichment_service.py           # Main orchestrator
│   │   │   ├── step_function_client.py         # Step Functions interface
│   │   │   ├── business_api_client.py          # .NET API client
│   │   │   └── enrichment_strategies/          # Strategy implementations
│   │   │       ├── alignment_enrichment.py
│   │   │       ├── coaching_enrichment.py
│   │   │       └── operations_enrichment.py
│   │   │
│   │   ├── prompt/                 # Prompt management services
│   │   │   ├── prompt_service.py               # Template retrieval
│   │   │   ├── prompt_builder_service.py       # Prompt construction
│   │   │   ├── template_engine.py              # Placeholder resolution
│   │   │   └── prompt_strategies/              # Strategy implementations
│   │   │       ├── alignment_prompt.py
│   │   │       ├── coaching_prompt.py
│   │   │       └── operations_prompt.py
│   │   │
│   │   ├── cache_service.py        # Redis caching
│   │   └── insights_service.py     # Insights aggregation
│   │
│   ├── domain/                     # 🟡 Domain Layer (Business Logic)
│   │   ├── __init__.py
│   │   │
│   │   ├── entities/               # Domain entities (aggregates)
│   │   │   ├── conversation.py
│   │   │   ├── prompt_template.py
│   │   │   └── analysis_request.py
│   │   │
│   │   ├── value_objects/          # Immutable value objects
│   │   │   ├── message.py
│   │   │   ├── conversation_context.py
│   │   │   ├── alignment_score.py
│   │   │   ├── strategy_recommendation.py
│   │   │   ├── kpi_recommendation.py
│   │   │   └── enriched_context.py
│   │   │
│   │   ├── services/               # Domain services
│   │   │   ├── alignment_calculator.py
│   │   │   ├── phase_transition_service.py
│   │   │   └── completion_validator.py
│   │   │
│   │   ├── events/                 # Domain events
│   │   │   ├── conversation_events.py
│   │   │   └── analysis_events.py
│   │   │
│   │   └── exceptions/             # Domain exceptions
│   │       ├── conversation_exceptions.py
│   │       └── analysis_exceptions.py
│   │
│   ├── infrastructure/             # 🔴 Infrastructure Layer
│   │   ├── __init__.py
│   │   │
│   │   ├── repositories/           # Data access implementations
│   │   │   ├── conversation_repository.py
│   │   │   ├── prompt_repository.py
│   │   │   ├── insights_repository.py
│   │   │   └── analytics_repository.py
│   │   │
│   │   ├── llm/                    # LLM provider implementations
│   │   │   ├── providers/
│   │   │   │   ├── base.py
│   │   │   │   ├── bedrock.py
│   │   │   │   ├── anthropic.py
│   │   │   │   ├── openai.py
│   │   │   │   └── manager.py      # Provider manager
│   │   │   ├── orchestrator.py     # LLM orchestration (deprecated)
│   │   │   └── memory.py           # Conversation memory
│   │   │
│   │   ├── external/               # External service clients
│   │   │   ├── step_functions/
│   │   │   │   ├── client.py
│   │   │   │   └── state_machines.py
│   │   │   └── business_api/
│   │   │       ├── client.py
│   │   │       └── endpoints.py
│   │   │
│   │   ├── cache/                  # Caching implementations
│   │   │   ├── redis_cache.py
│   │   │   └── in_memory_cache.py  # For testing
│   │   │
│   │   └── observability/          # Logging, metrics, tracing
│   │       ├── logger.py
│   │       ├── metrics.py
│   │       └── tracer.py
│   │
│   ├── models/                     # 📦 Data Transfer Objects (DTOs)
│   │   ├── __init__.py
│   │   ├── requests.py             # API request models
│   │   ├── responses.py            # API response models
│   │   ├── schemas.py              # Shared schemas
│   │   ├── conversation.py         # Conversation models (MOVED TO DOMAIN)
│   │   ├── prompt.py               # Prompt models
│   │   └── analysis.py             # Analysis models
│   │
│   ├── workflows/                  # 🔄 LangGraph Workflow Orchestration
│   │   ├── __init__.py
│   │   ├── base.py                 # Base workflow interface
│   │   ├── orchestrator.py         # Workflow orchestrator
│   │   ├── coaching_workflow.py    # Multi-step coaching
│   │   ├── analysis_workflow.py    # One-shot analysis
│   │   └── templates/              # Workflow templates
│   │       ├── core_values_workflow.py
│   │       ├── purpose_workflow.py
│   │       └── vision_workflow.py
│   │
│   └── core/                       # 🔧 Core Utilities & Configuration
│       ├── __init__.py
│       ├── config.py               # Configuration management
│       ├── constants.py            # Constants and enums
│       ├── exceptions.py           # Base exceptions
│       └── types.py                # Type definitions
│
├── tests/                          # 🧪 Test Suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── unit/                       # Unit tests (isolated)
│   │   ├── domain/
│   │   ├── services/
│   │   └── infrastructure/
│   ├── integration/                # Integration tests
│   │   ├── api/
│   │   ├── repositories/
│   │   └── external/
│   └── e2e/                        # End-to-end tests
│       ├── conversation_flows/
│       └── analysis_flows/
│
├── prompts/                        # 📝 Prompt Templates (S3 sync)
│   ├── core_values/
│   │   ├── v1.0.0.yaml
│   │   └── v1.1.0.yaml
│   ├── purpose/
│   ├── vision/
│   ├── alignment/
│   ├── strategy/
│   └── operations/
│
├── scripts/                        # 🛠️ Utility Scripts
│   └── upload_prompts.ps1
│
├── pyproject.toml                  # Project dependencies
├── uv.lock                         # Locked dependencies
├── template.yaml                   # AWS SAM template
├── samconfig.toml                  # SAM configuration
└── README.md                       # Service documentation
```

---

## 🎨 Design Patterns Summary

| Pattern | Purpose | Implementation Location |
|---------|---------|------------------------|
| **Hexagonal Architecture** | Isolate business logic from infrastructure | Overall structure: domain ↔ services ↔ infrastructure |
| **Domain-Driven Design** | Model business domain accurately | `domain/` entities, value objects, services |
| **CQRS-lite** | Separate read/write operations | Services layer: command services vs query repositories |
| **Strategy Pattern** | Interchangeable algorithms | LLM providers, prompt builders, enrichment strategies |
| **Template Method** | Define algorithm skeleton | `BaseAnalysisWorkflow`, `BaseCoachingWorkflow` |
| **Repository Pattern** | Abstract data access | `repositories/` with port interfaces |
| **Dependency Injection** | Invert dependencies | FastAPI `Depends()` in `api/dependencies.py` |
| **Factory Pattern** | Create complex objects | `PromptFactory`, `EnrichmentStrategyFactory` |
| **Adapter Pattern** | Convert interfaces | `LLMServiceAdapter`, Step Functions client |
| **Observer Pattern** | Publish domain events | Domain event publishers for analytics |
| **Circuit Breaker** | Fault tolerance | External service calls (Step Functions, .NET API) |
| **Retry Pattern** | Resilience | LLM invocations, external API calls |
| **Cache-Aside** | Performance optimization | Prompt templates, enriched contexts |

---

## 🔒 Security & Compliance

### Authentication & Authorization
- **JWT tokens** for user authentication (validated at API Gateway)
- **Request context** includes `user_id`, `tenant_id`, `permissions`
- **Multi-tenancy** enforced at data access layer (all queries scoped by `tenant_id`)

### Data Protection
- **Encryption at rest** (DynamoDB, S3, Redis)
- **Encryption in transit** (TLS 1.2+)
- **Secrets management** (AWS Secrets Manager for API keys)
- **PII handling** (business context data encrypted, audit logs)

### AI Safety
- **Prompt injection prevention** (input sanitization, template validation)
- **Content filtering** (AWS Bedrock guardrails)
- **Rate limiting** (per user, per tenant)
- **Cost controls** (token limits, budget alerts)

---

## 📊 Observability & Monitoring

### Logging Strategy
- **Structured logging** with `structlog`
- **Log levels**: DEBUG (dev), INFO (staging), WARN/ERROR (prod)
- **Context propagation**: `conversation_id`, `user_id`, `tenant_id`, `request_id`
- **PII redaction** in logs

### Metrics Collection
- **Business metrics**:
  - Conversations initiated/completed per hour
  - Analysis requests per type
  - Average conversation duration
  - Completion rates
- **Technical metrics**:
  - API response times (P50, P95, P99)
  - LLM latency and token usage
  - Cache hit rates
  - Error rates by type
- **Cost metrics**:
  - Bedrock token costs per request
  - Step Functions execution costs
  - Data transfer costs

### Tracing
- **AWS X-Ray** for distributed tracing
- **Trace context** propagated across Lambda, Step Functions, external APIs
- **Span annotations** for LLM calls, enrichment steps, database queries

### Alerting
- **Critical alerts**:
  - Error rate > 5%
  - P99 latency > 5 seconds
  - LLM provider failures
  - Step Functions failures
- **Warning alerts**:
  - Cache miss rate > 30%
  - Token usage spike > 20% increase
  - Conversation abandonment > 40%

---

## 🚀 Deployment & Scalability

### Deployment Strategy
- **Environment progression**: `dev` → `staging` → `production`
- **Blue/green deployment** for zero-downtime releases
- **Canary releases** (10% → 50% → 100% traffic shift)
- **Automated rollback** on error rate threshold

### Scalability Design
- **Stateless Lambda functions** (horizontal auto-scaling)
- **DynamoDB on-demand** (automatic capacity scaling)
- **Redis cluster mode** (multi-AZ, read replicas)
- **S3 high availability** (99.99% uptime SLA)
- **Step Functions** (concurrent execution limits)

### Performance Targets
- **API response time**: P95 < 2 seconds (excluding LLM latency)
- **LLM response time**: P95 < 5 seconds for one-shot, < 3 seconds for conversational
- **Conversation initiation**: < 1 second
- **Message processing**: < 3 seconds total (enrichment + LLM + persistence)
- **Cache hit rate**: > 70% for prompt templates
- **Concurrent users**: 10,000+ per service

---

## 🧪 Testing Strategy

### Test Pyramid

```
              ┌─────────────────┐
              │   E2E Tests     │  ← 10% (Critical user flows)
              │   (Slow)        │
              └─────────────────┘
           ┌─────────────────────────┐
           │  Integration Tests      │  ← 20% (Service boundaries)
           │  (Medium)               │
           └─────────────────────────┘
      ┌───────────────────────────────────┐
      │      Unit Tests                   │  ← 70% (Domain logic, services)
      │      (Fast)                       │
      └───────────────────────────────────┘
```

### Unit Tests (70%)
- **Domain logic** (entities, value objects, domain services)
- **Service layer** (business workflows, orchestration)
- **Utilities** (prompt builders, parsers, validators)
- **Mocked dependencies** (repositories, LLM providers, external services)
- **Coverage target**: > 85%

### Integration Tests (20%)
- **Repository layer** (DynamoDB, Redis, S3)
- **LLM provider integration** (using test models)
- **Step Functions client** (with mock state machines)
- **API endpoints** (FastAPI TestClient)
- **Coverage target**: > 70%

### End-to-End Tests (10%)
- **Complete conversation flows** (initiate → messages → complete)
- **One-shot analysis flows** (request → enrichment → LLM → response)
- **Error scenarios** (failures, timeouts, retries)
- **Performance tests** (load testing with Locust)

### Test Data Management
- **Factories** (using `factory_boy` for test data)
- **Fixtures** (pytest fixtures for common setups)
- **Mocking** (using `pytest-mock` and `httpx.mock`)
- **Cleanup** (automatic teardown of test resources)

---

## 📚 Documentation Standards

### Code Documentation
- **Docstrings** (Google style) for all public classes, methods
- **Type hints** on all function signatures
- **Inline comments** for complex business logic
- **README** in each major module

### API Documentation
- **OpenAPI/Swagger** (auto-generated by FastAPI)
- **Request/response examples** in docstrings
- **Error codes** and meanings documented
- **Rate limits** and quotas specified

### Architecture Documentation
- **Architecture Decision Records (ADRs)** for major decisions
- **Diagrams** (C4 model: context, containers, components)
- **Runbooks** for operational procedures
- **Troubleshooting guides**

---

## 🔄 Migration & Backward Compatibility

### Existing Code Preservation
- **Current implementations** remain functional during refactoring
- **Deprecation warnings** for old interfaces
- **Parallel implementations** (new architecture alongside legacy)
- **Feature flags** to toggle between old/new implementations

### Phased Migration
1. **Phase 1**: New domain layer with adapters to existing services
2. **Phase 2**: Refactor service layer to use new domain
3. **Phase 3**: Replace infrastructure layer (repositories, providers)
4. **Phase 4**: Update API layer to new patterns
5. **Phase 5**: Remove deprecated code

---

## 📈 Success Metrics

### Technical KPIs
- **Code quality**: > 85% test coverage, 0 critical security vulnerabilities
- **Performance**: P95 < 2s API latency, P95 < 5s total request time
- **Reliability**: 99.9% uptime, < 0.1% error rate
- **Scalability**: Support 10,000 concurrent users

### Business KPIs
- **User engagement**: > 70% conversation completion rate
- **AI quality**: > 90% user satisfaction (helpful ratings)
- **Adoption**: > 80% of users try at least one AI feature
- **Efficiency**: 50% reduction in time to create aligned goals

---

## 🗺️ Roadmap & Future Enhancements

### Phase 1: Foundation (Current)
- ✅ Core architecture design
- ✅ Domain models and types
- ✅ LLM provider abstraction
- ✅ Basic conversation management

### Phase 2: One-Shot Analysis (Next)
- 🔲 Alignment analysis service
- 🔲 Strategy recommendation service
- 🔲 KPI recommendation service
- 🔲 Context enrichment via Step Functions
- 🔲 Dynamic prompt templates

### Phase 3: Conversational Coaching
- 🔲 Core values coaching workflow
- 🔲 Purpose coaching workflow
- 🔲 Vision coaching workflow
- 🔲 Advanced conversation memory
- 🔲 Progress tracking and resumption

### Phase 4: Operations AI
- 🔲 SWOT analysis
- 🔲 Root cause analysis
- 🔲 Action plan generation
- 🔲 Prioritization engine
- 🔲 Scheduling optimization

### Phase 5: Advanced Features
- 🔲 Multi-language support
- 🔲 Voice interface
- 🔲 Admin UI for prompt management
- 🔲 A/B testing framework for prompts
- 🔲 Advanced analytics dashboard

---

## 🤝 Team & Responsibilities

### Development Team Structure
- **Tech Lead**: Architecture decisions, code reviews, technical guidance
- **Backend Engineers**: Service implementation, testing, deployment
- **AI/ML Engineer**: Prompt engineering, LLM optimization, quality assurance
- **DevOps Engineer**: Infrastructure, CI/CD, monitoring, alerts
- **QA Engineer**: Test strategy, automation, quality gates

### Code Ownership
- **Domain Layer**: Shared ownership (requires architectural review)
- **Service Layer**: Feature team ownership
- **Infrastructure Layer**: Platform team ownership
- **API Layer**: API team ownership

---

## 📖 Glossary

**Aggregate**: Cluster of domain objects treated as a single unit (e.g., Conversation with Messages)

**Bounded Context**: Explicit boundary within which a domain model is defined and applicable

**Context Enrichment**: Adding business data to prompts for more relevant AI responses

**Domain Event**: Something that happened in the domain that domain experts care about

**Entity**: Domain object with distinct identity that persists over time

**Hexagonal Architecture**: Architecture style isolating core logic from external concerns

**LangGraph**: Framework for building stateful, multi-step AI applications

**One-Shot Analysis**: Single request-response AI interaction without conversation state

**Port**: Interface defining how external world interacts with domain

**Prompt Template**: Reusable template defining how to structure prompts for AI

**Repository**: Abstraction for data access, treating collections as in-memory sets

**Value Object**: Immutable object defined by its attributes, not identity

**Workflow**: Multi-step process orchestrating multiple services to achieve goal

---

**End of Part 1: Architecture Overview**

**Next: Part 2 will contain detailed implementation specifications, component designs, API contracts, data models, workflow definitions, and implementation roadmap.**

---

**Document Status**: ✅ Part 1 Complete - Ready for Review  
**Next Action**: Review Part 1 and provide feedback before proceeding to Part 2

---

## 📌 Implementation Status Update (October 9, 2025)

**IMPORTANT**: The implementation plan for this architecture has been revised and organized into a comprehensive roadmap.

**See**: `REVISED_IMPLEMENTATION_ROADMAP.md` for:
- 8 structured implementation phases (12-15 weeks)
- Integrated testing strategy (not deferred)
- Observability-first approach (from Phase 1)
- Clear migration strategy from current code
- GitHub issues aligned with phases
- Detailed acceptance criteria and quality gates

**Summary**: `PLAN_UPDATE_SUMMARY.md`
