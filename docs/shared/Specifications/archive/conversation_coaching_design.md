# Conversation Coaching Engine - Technical Design Document

**Version:** 1.0.0  
**Created:** December 15, 2025  
**Status:** Approved for Implementation  
**Related Issue:** TBD (GitHub Issue to be created)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Data Models](#3-data-models)
4. [Component Reference](#4-component-reference)
5. [Flow Specifications](#5-flow-specifications)
6. [Template System](#6-template-system)
7. [Extraction System](#7-extraction-system)
8. [API Endpoints](#8-api-endpoints)
9. [Error Handling](#9-error-handling)
10. [Testing Strategy](#10-testing-strategy)
11. [Migration & Cleanup](#11-migration--cleanup)
12. [Implementation Checklist](#12-implementation-checklist)

---

## 1. Overview

### 1.1 Purpose

The Conversation Coaching Engine orchestrates multi-turn AI coaching conversations. It manages session lifecycle, prompt construction, LLM execution, and structured data extraction.

### 1.2 Design Principles

- **Single Source of Truth**: Topic Registry for topic definitions, LLMTopic DB for runtime configuration
- **Separation of Concerns**: Internal conversation format separate from extraction result model
- **Reusable Components**: Leverage existing TemplateParameterProcessor, ProviderManager, TopicRepository
- **Clean Architecture**: Domain layer has no external dependencies

### 1.3 Key Terminology

| Term | Definition |
|------|------------|
| **Topic** | A registered AI operation (e.g., `COACHING:core_values`) |
| **Session** | A multi-turn conversation instance for a specific topic |
| **Turn** | One user message + one AI response |
| **Extraction** | Separate LLM call to convert conversation into structured data |
| **Result Model** | Pydantic model defining extracted output schema |

---

## 2. Architecture

### 2.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Layer                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ POST /initiate  │  │ POST /message   │  │ POST /complete  │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                        │
│           └────────────────────┼────────────────────┘                        │
│                                ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                    CoachingSessionService                                ││
│  │  - Session lifecycle management                                          ││
│  │  - Conversation orchestration                                            ││
│  │  - Extraction coordination                                               ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Configuration  │      │    Execution    │      │   Persistence   │
│     Layer       │      │     Layer       │      │     Layer       │
├─────────────────┤      ├─────────────────┤      ├─────────────────┤
│ TopicRepository │      │ TemplateParam   │      │ SessionRepo     │
│ (LLMTopic DB)   │      │ Processor       │      │ (DynamoDB)      │
├─────────────────┤      ├─────────────────┤      └─────────────────┘
│ TOPIC_REGISTRY  │      │ ProviderManager │
│ (Python code)   │      │ (LLM providers) │
├─────────────────┤      ├─────────────────┤
│ S3PromptStorage │      │ ExtractionUtil  │
│ (Templates)     │      │ (structured_    │
└─────────────────┘      │  output.py)     │
                         └─────────────────┘
```

### 2.2 Component Dependencies

```
API Routes
    └── CoachingSessionService
            ├── TopicRepository (get LLM config from DB)
            ├── TOPIC_REGISTRY (get topic definition)
            ├── TemplateParameterProcessor (resolve params, render templates)
            ├── S3PromptStorage (load templates)
            ├── ProviderManager (execute LLM calls)
            ├── ExtractionUtils (generate extraction prompts)
            └── CoachingSessionRepository (persist sessions)
```

### 2.3 Dependency Rule

```
API → Application → Domain ← Infrastructure

Domain layer has NO outward dependencies.
Infrastructure implements domain ports (Protocol classes).
```

---

## 3. Data Models

### 3.1 Topic Registry Entry (Python Code)

**Location:** `coaching/src/core/endpoint_registry.py` → rename to `topic_registry.py`

```python
@dataclass
class TopicDefinition:
    """Static topic definition in code."""
    topic_id: str                           # e.g., "COACHING:core_values"
    name: str                               # Human-readable name
    description: str                        # Description of the topic
    topic_type: TopicType                   # SINGLE_SHOT or CONVERSATION
    parameters: list[ParameterDefinition]  # Required/optional parameters
    result_model: type[BaseModel] | None   # Pydantic model for output
    templates: dict[TemplateType, str]     # Template S3 keys by type
    
    # Optional - only for single-shot endpoints
    endpoint_path: str | None = None       # e.g., "/ai/execute"
    http_method: str | None = None         # e.g., "POST"

class TemplateType(Enum):
    """Template types for coaching conversations."""
    SYSTEM = "system"           # System prompt (AI persona, rules)
    INITIATION = "initiation"   # First turn prompt
    RESUME = "resume"           # Resume conversation prompt
    EXTRACTION = "extraction"   # Auto-generated from result_model
```

**Example Registration:**

```python
TOPIC_REGISTRY["COACHING:core_values"] = TopicDefinition(
    topic_id="COACHING:core_values",
    name="Core Values Coaching",
    description="AI-guided session to identify core values",
    topic_type=TopicType.CONVERSATION,
    parameters=[
        ParameterDefinition(
            name="business_context",
            param_type=ParameterType.STRING,
            required=True,
            description="Business context for coaching"
        ),
    ],
    result_model=CoreValuesResult,
    templates={
        TemplateType.SYSTEM: "coaching/core_values/system.md",
        TemplateType.INITIATION: "coaching/core_values/initiation.md",
        TemplateType.RESUME: "coaching/core_values/resume.md",
    },
)
```

### 3.2 LLMTopic Database Entry (DynamoDB)

**Table:** `LLMTopic`  
**Purpose:** Admin-configurable runtime settings

```python
class LLMTopic(BaseModel):
    """Runtime configuration from DynamoDB."""
    topic_id: str                    # PK - matches TOPIC_REGISTRY key
    tenant_id: str                   # For multi-tenancy
    
    # LLM Configuration
    model_code: str                  # e.g., "bedrock-claude-sonnet"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Conversation Settings
    max_turns: int = 10              # Maximum conversation turns
    session_ttl_hours: int = 24      # Session expiration
    idle_timeout_minutes: int = 30   # Inactive session timeout
    
    # Feature Flags
    is_active: bool = True
    enable_streaming: bool = False
    
    # Metadata
    created_at: datetime
    updated_at: datetime
```

### 3.3 MODEL_REGISTRY (Python Code)

**Location:** `coaching/src/core/model_registry.py`

```python
MODEL_REGISTRY: dict[str, ModelConfig] = {
    "bedrock-claude-sonnet": ModelConfig(
        provider="bedrock",
        model_name="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        supports_streaming=True,
    ),
    "bedrock-claude-haiku": ModelConfig(
        provider="bedrock",
        model_name="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        supports_streaming=True,
    ),
    "openai-gpt4o": ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        supports_streaming=True,
    ),
}
```

### 3.4 CoachingSession Entity (Domain)

**Location:** `coaching/src/domain/entities/coaching_session.py`

```python
class CoachingSession(BaseModel):
    """Aggregate root for coaching session."""
    session_id: SessionId
    topic_id: str
    user_id: UserId
    tenant_id: TenantId
    
    # State
    status: SessionStatus           # ACTIVE, COMPLETED, EXPIRED, ABANDONED
    current_turn: int = 0
    max_turns: int                  # From LLMTopic config
    
    # Conversation (internal format)
    messages: list[ConversationMessage] = []
    
    # Timing
    created_at: datetime
    updated_at: datetime
    expires_at: datetime            # Calculated from session_ttl_hours
    last_activity_at: datetime
    idle_timeout_minutes: int       # From LLMTopic config
    
    # Extraction (populated on completion)
    extracted_result: dict | None = None
    extraction_model: str | None = None

class ConversationMessage(BaseModel):
    """Internal conversation message format."""
    role: MessageRole               # USER, ASSISTANT, SYSTEM
    content: str
    timestamp: datetime
    turn_number: int | None = None  # For user/assistant pairs

class SessionStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"
```

### 3.5 Result Models (Domain)

**Location:** `coaching/src/domain/models/coaching_results.py`

```python
class CoreValuesResult(BaseModel):
    """Extraction result for core values coaching."""
    values: list[CoreValue]
    alignment_score: float
    summary: str

class CoreValue(BaseModel):
    name: str
    description: str
    importance_rank: int

class StrategySuggestionsResult(BaseModel):
    """Extraction result for strategy coaching."""
    strategies: list[Strategy]
    priority_order: list[str]
    implementation_notes: str
```

---

## 4. Component Reference

### 4.1 TopicRepository

**Location:** `coaching/src/infrastructure/repositories/topic_repository.py`  
**Purpose:** Retrieve LLMTopic configuration from DynamoDB

**Interface (Port):**

```python
class TopicRepositoryPort(Protocol):
    async def get_topic_config(
        self, topic_id: str, tenant_id: TenantId
    ) -> LLMTopic | None:
        """Get LLM configuration for a topic."""
        ...
    
    async def get_active_topics(
        self, tenant_id: TenantId
    ) -> list[LLMTopic]:
        """Get all active topics for tenant."""
        ...
```

**DynamoDB Key Structure:**

```python
Key = {
    "pk": f"TENANT#{tenant_id}",
    "sk": f"TOPIC#{topic_id}"
}
```

### 4.2 TemplateParameterProcessor

**Location:** `coaching/src/services/template_parameter_processor.py`  
**Purpose:** Resolve parameters and render templates

**Key Methods:**

```python
class TemplateParameterProcessor:
    async def process_template(
        self,
        template_content: str,
        topic_id: str,
        provided_params: dict[str, Any],
        user_context: UserContext,
    ) -> str:
        """
        1. Get parameter definitions from TOPIC_REGISTRY
        2. Validate required parameters are present
        3. Execute retrieval methods for dynamic parameters
        4. Render template with resolved values
        """
        ...
    
    def validate_parameters(
        self,
        topic_id: str,
        provided_params: dict[str, Any],
    ) -> list[str]:
        """Return list of missing required parameters."""
        ...
```

**Parameter Resolution Order:**

1. Check if parameter provided in request
2. Check if parameter has retrieval method → execute it
3. Check if parameter has default value → use it
4. If required and missing → raise error

### 4.3 S3PromptStorage

**Location:** `coaching/src/infrastructure/storage/s3_prompt_storage.py`  
**Purpose:** Load templates from S3

**Interface:**

```python
class S3PromptStorage:
    async def get_template(
        self, template_key: str
    ) -> str:
        """Load template content from S3."""
        ...
    
    async def get_templates_batch(
        self, template_keys: list[str]
    ) -> dict[str, str]:
        """Load multiple templates efficiently."""
        ...
```

**S3 Structure:**

```
s3://purposepath-prompts-{env}/
├── coaching/
│   ├── core_values/
│   │   ├── system.md
│   │   ├── initiation.md
│   │   └── resume.md
│   ├── strategy_suggestions/
│   │   ├── system.md
│   │   ├── initiation.md
│   │   └── resume.md
│   └── ...
└── single-shot/
    ├── niche_review/
    │   └── system.md
    └── ...
```

### 4.4 ProviderManager

**Location:** `coaching/src/infrastructure/llm/provider_manager.py`  
**Purpose:** Execute LLM calls with provider abstraction

**Interface:**

```python
class ProviderManager:
    async def execute(
        self,
        messages: list[dict],
        model_config: ModelConfig,
        temperature: float,
        max_tokens: int,
    ) -> LLMResponse:
        """Execute LLM call with specified configuration."""
        ...
    
    async def execute_with_fallback(
        self,
        messages: list[dict],
        primary_config: ModelConfig,
        fallback_config: ModelConfig | None,
        **kwargs,
    ) -> LLMResponse:
        """Execute with automatic fallback on failure."""
        ...
```

**LLMResponse:**

```python
class LLMResponse(BaseModel):
    content: str
    model: str
    tokens_used: int
    finish_reason: str
    processing_time_ms: int
```

### 4.5 ExtractionUtils

**Location:** `coaching/src/core/structured_output.py`  
**Purpose:** Generate extraction prompts from result models

**Key Functions:**

```python
def get_extraction_prompt(
    result_model: type[BaseModel],
    conversation_history: str,
) -> str:
    """
    Generate extraction prompt with:
    1. Structured output instructions
    2. JSON schema from result_model
    3. Conversation history
    4. Extraction directive
    """
    ...

def get_structured_output_instructions() -> str:
    """Return standard structured output instructions."""
    ...

def build_system_prompt_with_structured_output(
    base_system_prompt: str,
    result_model: type[BaseModel],
) -> str:
    """Append structured output instructions to system prompt."""
    ...
```

### 4.6 CoachingSessionRepository

**Location:** `coaching/src/infrastructure/repositories/coaching_session_repository.py`  
**Purpose:** Persist and retrieve coaching sessions

**Interface (Port):**

```python
class CoachingSessionRepositoryPort(Protocol):
    async def create(self, session: CoachingSession) -> CoachingSession:
        """Create new session."""
        ...
    
    async def get_by_id(
        self, session_id: SessionId, tenant_id: TenantId
    ) -> CoachingSession | None:
        """Get session by ID with tenant isolation."""
        ...
    
    async def get_active_for_user_topic(
        self, user_id: UserId, topic_id: str, tenant_id: TenantId
    ) -> CoachingSession | None:
        """Get active session for user+topic combination."""
        ...
    
    async def update(self, session: CoachingSession) -> CoachingSession:
        """Update existing session."""
        ...
    
    async def mark_expired(self, session_id: SessionId) -> None:
        """Mark session as expired."""
        ...
```

**DynamoDB Key Structure:**

```python
# Primary key
Key = {"session_id": session_id}

# GSI for user+topic lookup
GSI_UserTopic = {
    "pk": f"USER#{user_id}#TOPIC#{topic_id}",
    "sk": f"TENANT#{tenant_id}"
}
```

---

## 5. Flow Specifications

### 5.1 Session Initiation Flow

**Endpoint:** `POST /coaching/sessions/initiate`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Request Validation                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1.1 Receive request: {topic_id, parameters}                                  │
│ 1.2 Authenticate user → extract user_id, tenant_id                          │
│ 1.3 Validate topic_id exists in TOPIC_REGISTRY                              │
│ 1.4 Validate topic_type == CONVERSATION                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Session Resolution                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2.1 Query: get_active_for_user_topic(user_id, topic_id, tenant_id)          │
│ 2.2 If active session exists:                                               │
│     a. If session.user_id == current_user → RESUME (Phase 3-Resume)         │
│     b. If session.user_id != current_user → BLOCK (Issue #157)              │
│        Return 409 Conflict: "Session in progress by another user"           │
│ 2.3 If no active session → CREATE NEW (Phase 3-Create)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐
│ Phase 3-Create: New Session     │ │ Phase 3-Resume: Existing Session        │
├─────────────────────────────────┤ ├─────────────────────────────────────────┤
│ 3.1 Load LLMTopic config from   │ │ 3.1 Load resume template from S3        │
│     TopicRepository             │ │ 3.2 Load LLMTopic config (for model)    │
│ 3.2 Load system + initiation    │ │ 3.3 Render resume template with:        │
│     templates from S3 (batch)   │ │     - conversation_summary              │
│ 3.3 Validate parameters via     │ │     - current_turn / max_turns          │
│     TemplateParameterProcessor  │ │ 3.4 Build messages array:               │
│ 3.4 Render templates with       │ │     [system, ...history, resume]        │
│     resolved parameters         │ │                                         │
│ 3.5 Create session entity with  │ │                                         │
│     TTL from LLMTopic config:   │ │                                         │
│     - max_turns                 │ │                                         │
│     - session_ttl_hours         │ │                                         │
│     - idle_timeout_minutes      │ │                                         │
│ 3.6 Build messages array:       │ │                                         │
│     [system, initiation]        │ │                                         │
└─────────────────────────────────┘ └─────────────────────────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 4: LLM Execution                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4.1 Resolve model from MODEL_REGISTRY[llm_topic.model_code]                 │
│ 4.2 Call ProviderManager.execute() with:                                    │
│     - messages array                                                         │
│     - model_config (provider, model_name)                                   │
│     - temperature, max_tokens from LLMTopic                                 │
│ 4.3 Receive LLMResponse                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 5: Response Processing                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5.1 Append assistant message to session.messages                            │
│ 5.2 Update session metadata:                                                │
│     - current_turn += 1                                                     │
│     - last_activity_at = now()                                              │
│     - updated_at = now()                                                    │
│ 5.3 Persist session to DynamoDB                                             │
│ 5.4 Return response:                                                        │
│     {session_id, message, turn, max_turns, is_final: false}                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Continue Conversation Flow

**Endpoint:** `POST /coaching/sessions/{session_id}/message`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Request Validation                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1.1 Receive request: {message: string}                                       │
│ 1.2 Authenticate user → extract user_id, tenant_id                          │
│ 1.3 Load session by session_id with tenant isolation                        │
│ 1.4 Validate session.status == ACTIVE                                       │
│ 1.5 Validate session.user_id == current_user_id                             │
│ 1.6 Check idle timeout (last_activity_at + idle_timeout_minutes)            │
│ 1.7 Check max turns (current_turn < max_turns)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Message Processing                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2.1 Append user message to session.messages                                 │
│ 2.2 Load system template (for context, may cache)                           │
│ 2.3 Build messages array: [system, ...all history]                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 3: LLM Execution                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3.1 Load LLMTopic config for model settings                                 │
│ 3.2 Resolve model from MODEL_REGISTRY                                       │
│ 3.3 Call ProviderManager.execute()                                          │
│ 3.4 Receive LLMResponse                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 4: Response Processing                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4.1 Parse AI response for completion signals:                               │
│     - Check for is_final flag in response                                   │
│     - Check for natural completion phrases                                  │
│ 4.2 Append assistant message to session.messages                            │
│ 4.3 Update session: turn++, last_activity_at, updated_at                    │
│ 4.4 Determine is_final:                                                     │
│     - AI indicated completion, OR                                           │
│     - current_turn >= max_turns                                             │
│ 4.5 Persist session                                                         │
│ 4.6 Return response:                                                        │
│     {session_id, message, turn, max_turns, is_final}                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 5: Completion Check                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5.1 If is_final == true:                                                    │
│     → Automatically trigger extraction (Phase 6)                            │
│ 5.2 If is_final == false:                                                   │
│     → Return response, await next user message                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Complete Session Flow (User-Initiated or Auto)

**Endpoint:** `POST /coaching/sessions/{session_id}/complete`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 1: Validation                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1.1 Load session with tenant isolation                                       │
│ 1.2 Validate session.status == ACTIVE                                       │
│ 1.3 Validate session.user_id == current_user_id                             │
│ 1.4 (User-initiated completion is always allowed)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 2: Extraction Prompt Generation                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2.1 Get result_model from TOPIC_REGISTRY[topic_id]                          │
│ 2.2 Build conversation history string from session.messages                 │
│ 2.3 Generate extraction prompt using structured_output.py:                  │
│     - STRUCTURED_OUTPUT_INSTRUCTIONS                                        │
│     - JSON schema from result_model.model_json_schema()                     │
│     - Conversation history                                                   │
│     - Extraction directive                                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 3: Extraction LLM Call                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3.1 Load LLMTopic config (may use different model for extraction)           │
│ 3.2 Build extraction messages: [system_with_structured_output, extraction]  │
│ 3.3 Call ProviderManager.execute()                                          │
│ 3.4 Parse JSON response                                                     │
│ 3.5 Validate against result_model schema                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Phase 4: Finalization                                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4.1 Store extracted_result in session                                       │
│ 4.2 Update session.status = COMPLETED                                       │
│ 4.3 Update session metadata (completed_at)                                  │
│ 4.4 Persist final session state                                             │
│ 4.5 Return response:                                                        │
│     {session_id, status: "completed", result: extracted_result}             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Template System

### 6.1 Template Types

| Type | Purpose | When Used |
|------|---------|-----------|
| `SYSTEM` | AI persona, rules, context | Every LLM call |
| `INITIATION` | First turn prompt | New session only |
| `RESUME` | Continue existing session | Resume session |
| `EXTRACTION` | Auto-generated | Session completion |

### 6.2 Template Structure

**System Template (`system.md`):**

```markdown
You are an AI coach specializing in {{topic_name}}.

## Context
Business: {{business_name}}
Industry: {{industry}}

## Your Role
- Guide the user through discovering their {{topic_focus}}
- Ask probing questions
- Provide supportive feedback

## Rules
- Maximum {{max_turns}} conversation turns
- Current turn: {{current_turn}}
- Always acknowledge the user's input before asking new questions
```

**Initiation Template (`initiation.md`):**

```markdown
Let's begin exploring your {{topic_focus}}.

Based on your business context:
{{business_context}}

I'd like to start by understanding...
```

**Resume Template (`resume.md`):**

```markdown
Welcome back! Let's continue our conversation about {{topic_focus}}.

## Where We Left Off
{{conversation_summary}}

We're on turn {{current_turn}} of {{max_turns}}.

Let's pick up where we left off...
```

### 6.3 Parameter Resolution

**TemplateParameterProcessor** resolves parameters in this order:

1. **Request Parameters**: Provided in API call
2. **Retrieval Methods**: Execute async functions to fetch data
3. **Default Values**: Fallback if not required
4. **Validation**: Raise error if required parameter missing

**Parameter Definition Example:**

```python
ParameterDefinition(
    name="business_context",
    param_type=ParameterType.STRING,
    required=True,
    description="Business context for coaching",
    retrieval_method="get_business_context",  # Optional async function
    default_value=None,
)
```

---

## 7. Extraction System

### 7.1 Extraction Overview

Extraction is a **separate LLM call** that converts the conversation into structured data. It only uses the `result_model` - the conversation itself uses an internal format.

### 7.2 Extraction Prompt Generation

**Location:** `coaching/src/core/structured_output.py`

```python
STRUCTURED_OUTPUT_INSTRUCTIONS = """
## Response Format Requirements

You MUST respond with valid JSON that matches the provided schema.

### Rules:
1. Output ONLY the JSON object, no markdown code blocks
2. Include ALL required fields
3. Use the exact field names from the schema
4. Follow the specified data types exactly
"""

EXTRACTION_PROMPT_TEMPLATE = """
{structured_output_instructions}

## JSON Schema
```json
{json_schema}
```

## Conversation to Extract From
{conversation_history}

## Task
Extract the key information from this conversation into the JSON format above.
Analyze all messages and synthesize the insights shared during the conversation.
"""
```

### 7.3 Result Model Schema Generation

```python
def get_extraction_prompt(
    result_model: type[BaseModel],
    conversation_history: str,
) -> str:
    schema = result_model.model_json_schema()
    return EXTRACTION_PROMPT_TEMPLATE.format(
        structured_output_instructions=STRUCTURED_OUTPUT_INSTRUCTIONS,
        json_schema=json.dumps(schema, indent=2),
        conversation_history=conversation_history,
    )
```

### 7.4 Extraction Triggers

Extraction is triggered when:
1. **AI indicates completion**: Response contains completion signal
2. **Max turns reached**: `current_turn >= max_turns`
3. **User requests completion**: Calls `/complete` endpoint

---

## 8. API Endpoints

### 8.1 Endpoint Specifications

Based on [backend-integration-unified-ai.md](./backend-integration-unified-ai.md):

#### POST /coaching/sessions/initiate

**Request:**

```json
{
  "topic_id": "COACHING:core_values",
  "parameters": {
    "business_context": "We help small businesses with marketing"
  }
}
```

**Response (New Session):**

```json
{
  "session_id": "sess_abc123",
  "topic_id": "COACHING:core_values",
  "status": "active",
  "turn": 1,
  "max_turns": 10,
  "message": "Let's begin exploring your core values...",
  "is_final": false,
  "metadata": {
    "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    "processing_time_ms": 2340
  }
}
```

**Response (Resumed Session):**

```json
{
  "session_id": "sess_abc123",
  "topic_id": "COACHING:core_values",
  "status": "active",
  "turn": 4,
  "max_turns": 10,
  "message": "Welcome back! Let's continue...",
  "is_final": false,
  "resumed": true,
  "metadata": {...}
}
```

#### POST /coaching/sessions/{session_id}/message

**Request:**

```json
{
  "message": "I think integrity is important to me"
}
```

**Response:**

```json
{
  "session_id": "sess_abc123",
  "turn": 5,
  "max_turns": 10,
  "message": "That's wonderful that integrity resonates with you...",
  "is_final": false,
  "metadata": {...}
}
```

#### POST /coaching/sessions/{session_id}/complete

**Request:** (empty body or optional feedback)

```json
{}
```

**Response:**

```json
{
  "session_id": "sess_abc123",
  "status": "completed",
  "result": {
    "values": [
      {"name": "Integrity", "description": "...", "importance_rank": 1},
      {"name": "Innovation", "description": "...", "importance_rank": 2}
    ],
    "alignment_score": 0.85,
    "summary": "Based on our conversation..."
  },
  "metadata": {...}
}
```

#### GET /coaching/sessions/{session_id}

**Response:**

```json
{
  "session_id": "sess_abc123",
  "topic_id": "COACHING:core_values",
  "status": "active",
  "turn": 5,
  "max_turns": 10,
  "created_at": "2025-12-15T10:00:00Z",
  "last_activity_at": "2025-12-15T10:15:00Z",
  "expires_at": "2025-12-16T10:00:00Z"
}
```

### 8.2 Error Responses

| Status | Code | Message |
|--------|------|---------|
| 400 | INVALID_TOPIC | Topic not found or not a conversation type |
| 400 | MISSING_PARAMETERS | Required parameters missing: [...] |
| 401 | UNAUTHORIZED | Invalid or missing authentication |
| 403 | FORBIDDEN | User does not own this session |
| 404 | SESSION_NOT_FOUND | Session not found |
| 409 | SESSION_CONFLICT | Session in progress by another user |
| 410 | SESSION_EXPIRED | Session has expired |
| 422 | MAX_TURNS_REACHED | Maximum conversation turns reached |

---

## 9. Error Handling

### 9.1 Error Categories

```python
# Domain Exceptions
class SessionNotFoundError(DomainException): ...
class SessionExpiredError(DomainException): ...
class SessionNotActiveError(DomainException): ...
class SessionAccessDeniedError(DomainException): ...
class MaxTurnsReachedError(DomainException): ...
class SessionConflictError(DomainException): ...

# Application Exceptions
class TopicNotFoundError(ApplicationException): ...
class TopicNotConversationTypeError(ApplicationException): ...
class MissingParametersError(ApplicationException): ...
class ExtractionFailedError(ApplicationException): ...

# Infrastructure Exceptions
class LLMProviderError(InfrastructureException): ...
class TemplateNotFoundError(InfrastructureException): ...
class RepositoryError(InfrastructureException): ...
```

### 9.2 Error Mapping

```python
ERROR_STATUS_MAP = {
    SessionNotFoundError: (404, "SESSION_NOT_FOUND"),
    SessionExpiredError: (410, "SESSION_EXPIRED"),
    SessionAccessDeniedError: (403, "FORBIDDEN"),
    SessionConflictError: (409, "SESSION_CONFLICT"),
    MaxTurnsReachedError: (422, "MAX_TURNS_REACHED"),
    TopicNotFoundError: (400, "INVALID_TOPIC"),
    MissingParametersError: (400, "MISSING_PARAMETERS"),
    LLMProviderError: (503, "LLM_UNAVAILABLE"),
}
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Domain Layer (85%+ coverage):**

```python
# tests/unit/domain/test_coaching_session.py
class TestCoachingSession:
    def test_add_message_increments_turn(self): ...
    def test_add_message_when_inactive_raises(self): ...
    def test_is_expired_checks_expires_at(self): ...
    def test_is_idle_checks_timeout(self): ...
    def test_can_add_turn_checks_max_turns(self): ...

# tests/unit/domain/test_session_status.py
class TestSessionStatus:
    def test_active_allows_messages(self): ...
    def test_completed_blocks_messages(self): ...
```

**Application Layer (75%+ coverage):**

```python
# tests/unit/application/test_coaching_session_service.py
class TestCoachingSessionService:
    async def test_initiate_creates_new_session(self): ...
    async def test_initiate_resumes_existing_session(self): ...
    async def test_initiate_blocks_different_user(self): ...
    async def test_add_message_validates_ownership(self): ...
    async def test_add_message_checks_idle_timeout(self): ...
    async def test_complete_triggers_extraction(self): ...
```

### 10.2 Integration Tests

```python
# tests/integration/test_coaching_flow.py
class TestCoachingFlowIntegration:
    async def test_full_conversation_flow(self): ...
    async def test_resume_session_flow(self): ...
    async def test_extraction_produces_valid_result(self): ...
    async def test_expired_session_handling(self): ...

# tests/integration/test_repository_integration.py
class TestCoachingSessionRepository:
    async def test_create_and_retrieve_session(self): ...
    async def test_tenant_isolation(self): ...
    async def test_get_active_for_user_topic(self): ...
```

### 10.3 End-to-End Tests

```python
# tests/e2e/test_coaching_api.py
class TestCoachingAPIE2E:
    async def test_initiate_endpoint(self): ...
    async def test_message_endpoint(self): ...
    async def test_complete_endpoint(self): ...
    async def test_full_coaching_journey(self): ...
    async def test_concurrent_session_blocking(self): ...
```

---

## 11. Migration & Cleanup

### 11.1 Files to Delete

```
coaching/src/core/coaching_topic_registry.py          # Duplicate registry
coaching/src/core/constants.py → DEFAULT_LLM_MODELS   # Deprecated constant
coaching/src/domain/entities/llm_configuration.py     # Deprecated entity (if exists)
```

### 11.2 Files to Rename

```
coaching/src/core/endpoint_registry.py → topic_registry.py
```

### 11.3 Files to Update

All files importing from `endpoint_registry`:
- `coaching/src/services/coaching_session_service.py`
- `coaching/src/services/topic_seeding_service.py`
- `coaching/src/services/parameter_gathering_service.py`
- `coaching/src/services/async_execution_service.py`
- `coaching/src/infrastructure/repositories/topic_repository.py`
- `coaching/src/api/routes/admin/topics.py`
- `coaching/src/api/routes/admin/prompts.py`
- `coaching/src/api/routes/ai_execute.py`
- `coaching/src/api/dependencies/generic_ai_handler.py`
- `coaching/src/services/unified_ai_engine.py`

### 11.4 Database Updates

No DynamoDB table changes required - using existing:
- `LLMTopic` - for configuration
- `CoachingSession` - for session storage

---

## 12. Implementation Checklist

### Phase 1: Foundation

- [ ] Rename `endpoint_registry.py` → `topic_registry.py`
- [ ] Update all imports (11 files)
- [ ] Add `TemplateType` enum to registry
- [ ] Make `endpoint_path`/`http_method` optional
- [ ] Delete `coaching_topic_registry.py`
- [ ] Delete `DEFAULT_LLM_MODELS` from constants.py
- [ ] Verify `structured_output.py` is complete

### Phase 2: Domain Layer

- [ ] Create/update `CoachingSession` entity
- [ ] Create `ConversationMessage` value object
- [ ] Create `SessionStatus` enum
- [ ] Define domain exceptions
- [ ] Create `CoachingSessionRepositoryPort` protocol
- [ ] Add result models for coaching topics

### Phase 3: Infrastructure Layer

- [ ] Implement `DynamoDBCoachingSessionRepository`
- [ ] Add GSI for user+topic lookup
- [ ] Ensure tenant isolation in all queries
- [ ] Update `S3PromptStorage` for batch loading

### Phase 4: Application Layer

- [ ] Implement `CoachingSessionService`
  - [ ] `initiate_session()` method
  - [ ] `add_message()` method
  - [ ] `complete_session()` method
  - [ ] `get_session()` method
- [ ] Integrate with `TemplateParameterProcessor`
- [ ] Integrate with `ProviderManager`
- [ ] Implement extraction logic

### Phase 5: API Layer

- [ ] Create/update `POST /coaching/sessions/initiate`
- [ ] Create/update `POST /coaching/sessions/{id}/message`
- [ ] Create/update `POST /coaching/sessions/{id}/complete`
- [ ] Create/update `GET /coaching/sessions/{id}`
- [ ] Add proper error handling middleware
- [ ] Add request/response validation

### Phase 6: Testing

- [ ] Unit tests for domain entities (85%+)
- [ ] Unit tests for application service (75%+)
- [ ] Integration tests for repository
- [ ] Integration tests for full flow
- [ ] E2E tests for API endpoints

### Phase 7: Documentation

- [ ] Update API documentation
- [ ] Update architecture diagrams
- [ ] Add runbook for common issues

---

## Appendix A: Sequence Diagrams

### A.1 Initiate Session Sequence

```
Client          API           Service        TopicRepo      SessionRepo    TemplateProc    S3Storage    ProviderMgr
  │              │              │              │              │              │              │              │
  │──POST /init──▶              │              │              │              │              │              │
  │              │──initiate()──▶              │              │              │              │              │
  │              │              │──get_config──▶              │              │              │              │
  │              │              │◀──LLMTopic───┤              │              │              │              │
  │              │              │──get_active──────────────────▶              │              │              │
  │              │              │◀──None/Session───────────────┤              │              │              │
  │              │              │──get_templates────────────────────────────────────────────▶              │
  │              │              │◀──templates───────────────────────────────────────────────┤              │
  │              │              │──process()────────────────────────────────▶              │              │
  │              │              │◀──rendered────────────────────────────────┤              │              │
  │              │              │──execute()──────────────────────────────────────────────────────────────▶
  │              │              │◀──response──────────────────────────────────────────────────────────────┤
  │              │              │──create()─────────────────────▶              │              │              │
  │              │◀──response───┤              │              │              │              │              │
  │◀──200 OK─────┤              │              │              │              │              │              │
```

---

## Appendix B: State Machine

### B.1 Session State Transitions

```
                    ┌─────────────────┐
                    │                 │
        ┌───────────▶    ACTIVE      │◀─────────────┐
        │           │                 │              │
        │           └────────┬────────┘              │
        │                    │                       │
        │         ┌──────────┼──────────┐            │
        │         │          │          │            │
        │         ▼          ▼          ▼            │
   ┌────┴────┐ ┌─────────┐ ┌─────────┐ ┌────────┐   │
   │ CREATED │ │COMPLETED│ │ EXPIRED │ │ABANDONED│  │
   └─────────┘ └─────────┘ └─────────┘ └────────┘   │
        │                                            │
        │                                            │
        └───────────── (resume) ─────────────────────┘

Transitions:
- CREATED → ACTIVE: First LLM response received
- ACTIVE → COMPLETED: Extraction successful
- ACTIVE → EXPIRED: TTL exceeded
- ACTIVE → ABANDONED: Idle timeout exceeded
- ACTIVE → ACTIVE: Message added (turn incremented)
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-15 | AI Assistant | Initial design document |

