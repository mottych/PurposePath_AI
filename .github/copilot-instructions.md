# AI Code Assistant Instructions - PurposePath AI

**Version**: 2.0.0  
**Last Updated**: October 9, 2025  
**Status**: Active Implementation Guide

---

## 📚 Documentation Hierarchy

**CRITICAL**: Always consult these documents in order before implementing:

1. **This Document** - Development standards and workflow
2. **Architecture Design** (`docs/Plans/AI_COACHING_ARCHITECTURE_DESIGN.md`) - System architecture
3. **Guides** (`docs/Guides/`) - Specific technical guidance
4. **Specification Documents** (`docs/Specifications/`) - API and integration specs
---

## 🎯 Core Development Philosophy

### Quality & Discipline

* Quality first — no shortcuts or temporary hacks.
* Implement long-term, maintainable solutions.
* Remove all temporary code, tests, and data after use.
* Any infrastructure changes must be done through Pulumi as IaC.
* dev branch is the main integration branch; keep it stable. Only merge fully tested, complete features, with no warning or errors on build or tests for the whole solution, even if not related to the changes.
* Always work in active virtual environment.
* Always work in a feature branch off dev.
* **When in doubt - ask me**

### Workflow & GitHub**

* Always work under a GitHub issue; request one if missing.
* When starting to work on an issue - mark the issue in-progress using a label.
* Do not create status documents, only update issues.
* Always work in a feature branch off the `dev` branch
* Use issue ID in commits (e.g., `feat(#123): add API endpoint`).
* Use GitHub Issues: add `in-progress`, post updates as comments, close after completion.

### Testing & Validation**

* Create unit and integration tests for all new or modified logic.
* The task is not complete until everything passes, regardless if failures are related to the issue being worked.
* Do not merge to `dev` code that does not pass all tests and validations.

### Completion & Merge**

1. Make sure there are no warning or errors on build or tests including MyPy, PyLant, ruff, PyDent, Black, or any other errors or warning or errors. If there are - fix them even if they are pre-existing or not related to the last change..
2. Commit with descriptive message referencing the issue. Make sure all pre-commit checks pass.
3. Merge the feature branch into 'dev' and sync.
4. Clean temporary code and artifacts.
5. After successful deployment and verification using E2E test, continue to close the issue:
   1. Update labels (remove in-progress) and **close** the issue on GitHub.
   2. Delete the feature branch both locally and remotely.

**Collaboration**

* Ask for clarification when needed.
* Report progress and blockers promptly.

### Quality First Principles

**Ask Before Acting**: "What is the right way to do this?" and "What would an expert do?"

**No Shortcuts Ever**:
- No workarounds or temporary fixes
- No masking errors or suppressing warnings
- No TODO comments in production code
- Complete the work properly the first time

**Expert Standards**:
- Research official documentation first
- Follow established patterns in codebase
- Consult best practices and community standards
- Document architectural decisions (ADRs)

---

## 🏗️ Architecture Standards (MANDATORY)

### Clean Architecture Layers

We follow **Clean Architecture with DDD** (See: `docs/Guides/clean-architecture-ddd-guidelines.md`):

```
┌─────────────────────────────────────────────┐
│  API Layer (FastAPI)                         │  ← External interface
│  - Routes, Middleware, Auth                  │
├─────────────────────────────────────────────┤
│  Application Services Layer                  │  ← Use case orchestration
│  - Services, Commands, Queries              │
├─────────────────────────────────────────────┤
│  Domain Layer                                │  ← Business logic (NO dependencies)
│  - Entities, Value Objects, Domain Services │
├─────────────────────────────────────────────┤
│  Infrastructure Layer                        │  ← External concerns
│  - Repositories, LLM Providers, Clients     │
└─────────────────────────────────────────────┘
```

**Dependency Rule**: Dependencies ONLY flow inward (API → Services → Domain)

### Domain-Driven Design Patterns

**Entities** (Aggregate Roots):
```python
class Conversation(BaseModel):
    """Aggregate root with business rules."""
    conversation_id: ConversationId
    
    def add_message(self, role: MessageRole, content: str) -> None:
        """Business rule: Cannot add to completed conversations."""
        if not self.is_active():
            raise ValueError("Cannot add message to completed conversation")
        # ... business logic
```

**Value Objects** (Immutable):
```python
class AlignmentScore(BaseModel):
    """Immutable value object."""
    overall_score: float = Field(..., ge=0, le=100)
    
    class Config:
        frozen = True  # Immutable
```

**Domain Services** (Stateless):
```python
class AlignmentCalculatorService:
    """Stateless domain service for complex business logic."""
    def calculate_alignment(self, input: AlignmentInput) -> AlignmentScore:
        # Pure business logic, no infrastructure dependencies
        pass
```

**Repository Pattern** (Port/Adapter):
```python
# Domain port (interface)
class ConversationRepositoryPort(Protocol):
    async def create(self, conversation: Conversation) -> Conversation: ...
    async def get(self, id: ConversationId) -> Optional[Conversation]: ...

# Infrastructure adapter (implementation)
class DynamoDBConversationRepository:
    async def create(self, conversation: Conversation) -> Conversation:
        # DynamoDB-specific implementation
        pass
```

---

## 🔄 Development Workflow (CRITICAL)

### Git Branching Strategy

**NEVER commit directly to master, staging, or dev branches!**

**Branch Hierarchy** (See: `docs/Guides/BRANCHING_STRATEGY.md`):
```
master (production) ←── PR ←── staging ←── PR ←── dev ←── feature/branches
```

**Workflow**:
```bash
# 1. Start from dev
git checkout dev
git pull origin dev

# 2. Create feature branch
git checkout -b feature/descriptive-name

# 3. Work and commit (reference issue)
git commit -m "feat: implement feature - refs #42"

# 4. Push and create PR
git push origin feature/descriptive-name
# Create PR from feature → dev via GitHub

# 5. After merge, delete feature branch
git branch -d feature/descriptive-name
git push origin --delete feature/descriptive-name
```

### Commit Message Convention (Conventional Commits)

**Format**: `<type>(<scope>): <subject>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance
- `chore`: Maintenance
- `ci`: CI/CD changes

**Examples**:
```bash
feat(coaching): implement alignment calculation service - refs #5
fix(llm): resolve provider timeout handling - closes #12
test(domain): add unit tests for conversation entity - refs #4
docs(api): update coaching endpoint documentation
```

---

## 📋 GitHub Issues Workflow (MANDATORY)

**EVERY change MUST be linked to a GitHub issue.**

### Issue Lifecycle

1. **Create Issue Before Starting**:
   ```bash
   gh issue create \
     --title "Phase 1.2: Implement AlignmentScore value object" \
     --body "..." \
     --label "enhancement,phase-1"
   ```

2. **Update Progress**:
   - Comment regularly with progress updates
   - Reference commits: "Implemented validation in commit abc123"
   - Document blockers immediately

3. **Link All Commits**:
   ```bash
   git commit -m "feat: add alignment score calculation - refs #5"
   ```

4. **Close Only When Complete**:
   - ✅ Code implemented and reviewed
   - ✅ Tests passing (coverage targets met)
   - ✅ Type checking clean (`mypy --strict`)
   - ✅ Linting clean (`ruff check`, `black`)
   - ✅ Documentation updated
   - ✅ PR approved and merged

---

## 🔒 Type Safety Requirements (MANDATORY)

### Pydantic Models Everywhere

**ZERO `dict[str, Any]` in domain layer!**

✅ **Correct**:
```python
from pydantic import BaseModel, Field

class AlignmentScore(BaseModel):
    """Strongly typed value object."""
    overall_score: float = Field(..., ge=0, le=100, description="Overall alignment")
    component_scores: ComponentScores
    explanation: str = Field(..., min_length=10)
    
    class Config:
        frozen = True  # Immutable
```

❌ **Incorrect**:
```python
def calculate_score(data: dict[str, Any]) -> dict[str, Any]:
    return {"score": data.get("value", 0)}
```

### Domain ID Types (Strong Typing)

Use `NewType` for compile-time safety (See: `docs/Guides/shared-types-guide.md`):

```python
from typing import NewType
from uuid import uuid4

ConversationId = NewType('ConversationId', str)
UserId = NewType('UserId', str)

def create_conversation_id() -> ConversationId:
    return ConversationId(str(uuid4()))

# Type-safe function signatures
def get_conversation(id: ConversationId) -> Optional[Conversation]:
    pass
```

### DynamoDB Response Handling

Transform raw responses immediately:

```python
# ✅ Good: Transform immediately
response = dynamodb.get_item(Key={"PK": "USER#123"})
if "Item" in response:
    return UserEntity.model_validate(response["Item"])

# ❌ Bad: Return raw dict
return response.get("Item", {})
```

---

## 🧪 Testing Strategy (INTEGRATED THROUGHOUT)

### Test Pyramid (Per Phase)

```
┌──────────────┐
│  E2E Tests   │  10% - Critical flows
├──────────────┤
│ Integration  │  20% - API, DB, External
├──────────────┤
│  Unit Tests  │  70% - Domain logic
└──────────────┘
```

### Coverage Targets (MANDATORY)

- **Domain Layer**: 85%+ unit test coverage
- **Service Layer**: 75%+ unit test coverage  
- **Infrastructure**: 70%+ integration test coverage
- **Overall Project**: 75%+ combined coverage

### Test Structure

```python
# tests/unit/domain/entities/test_conversation.py
import pytest
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.core.constants import MessageRole

class TestConversationEntity:
    """Test suite for Conversation aggregate root."""
    
    @pytest.fixture
    def conversation(self) -> Conversation:
        """Create test conversation."""
        return Conversation(
            conversation_id=create_conversation_id(),
            user_id=create_user_id("user_123"),
            tenant_id=create_tenant_id("tenant_456"),
            topic="core_values"
        )
    
    def test_add_message_to_active_conversation_succeeds(
        self, 
        conversation: Conversation
    ) -> None:
        """Test: Active conversation can receive messages."""
        # Arrange
        initial_count = len(conversation.messages)
        
        # Act
        conversation.add_message(
            role=MessageRole.USER,
            content="Test message",
            metadata={}
        )
        
        # Assert
        assert len(conversation.messages) == initial_count + 1
        assert conversation.context.response_count == 1
    
    def test_add_message_to_completed_conversation_raises_error(
        self, 
        conversation: Conversation
    ) -> None:
        """Test: Cannot add messages to completed conversations."""
        # Arrange
        conversation.mark_completed()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot add message"):
            conversation.add_message(
                role=MessageRole.USER,
                content="Test",
                metadata={}
            )
```

### Test-First Development

**Process**:
1. Write test based on acceptance criteria
2. Watch test fail (Red)
3. Implement minimal code to pass (Green)
4. Refactor for quality (Refactor)
5. Repeat

---

## 🛠️ Code Quality Standards

### Pre-Commit Validation

**Run BEFORE every commit**:

```bash
# 1. Format code
black src/ tests/

# 2. Check linting
ruff check src/ tests/ --fix

# 3. Type checking
mypy src/ --strict

# 4. Run tests
pytest tests/ -v --cov=src --cov-fail-under=75
```

### Function Signature Requirements

**ALWAYS include complete type hints**:

```python
# ✅ Good: Complete annotations
async def process_conversation(
    conversation_id: ConversationId,
    user_context: UserContext,
    message: str,
    *,  # Force keyword-only parameters
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> ConversationResponse:
    """
    Process user message and generate AI response.
    
    Args:
        conversation_id: Unique conversation identifier
        user_context: User and tenant context
        message: User's input message
        max_tokens: Maximum tokens for LLM response
        temperature: LLM temperature parameter
        
    Returns:
        ConversationResponse with AI-generated content
        
    Raises:
        ConversationNotFound: If conversation doesn't exist
        LLMProviderError: If LLM generation fails
    """
    pass

# ❌ Bad: Missing types
async def process_conversation(conversation_id, user_context, message, max_tokens=1000):
    pass
```

### Error Handling Patterns

**Domain-specific exceptions**:

```python
# Base exception
class CoachingDomainException(Exception):
    """Base exception for coaching domain."""
    pass

# Specific exceptions
class ConversationNotFound(CoachingDomainException):
    """Conversation not found."""
    def __init__(self, conversation_id: ConversationId) -> None:
        self.conversation_id = conversation_id
        super().__init__(f"Conversation not found: {conversation_id}")

class InvalidPhaseTransition(CoachingDomainException):
    """Invalid conversation phase transition."""
    def __init__(self, from_phase: str, to_phase: str, reason: str) -> None:
        super().__init__(
            f"Cannot transition from {from_phase} to {to_phase}: {reason}"
        )
```

### Logging Standards (Structured)

```python
import structlog

logger = structlog.get_logger(__name__)

async def create_conversation(request: InitiateRequest) -> Conversation:
    """Create new conversation with structured logging."""
    logger.info(
        "conversation.create.started",
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        topic=request.topic
    )
    
    try:
        conversation = Conversation(...)
        await repository.create(conversation)
        
        logger.info(
            "conversation.create.completed",
            conversation_id=conversation.conversation_id,
            user_id=request.user_id
        )
        
        return conversation
        
    except Exception as e:
        logger.error(
            "conversation.create.failed",
            error=str(e),
            error_type=type(e).__name__,
            user_id=request.user_id,
            exc_info=True
        )
        raise
```

---

## 📁 Project Structure & Organization

### Module Organization (Clean Architecture)

```
coaching/
├── src/
│   ├── domain/                    # 🟡 Domain Layer (NO external dependencies)
│   │   ├── entities/              # Aggregate roots (Conversation, PromptTemplate)
│   │   ├── value_objects/         # Immutable objects (Message, AlignmentScore)
│   │   ├── services/              # Domain services (AlignmentCalculator)
│   │   ├── events/                # Domain events (ConversationInitiated)
│   │   ├── exceptions/            # Domain exceptions
│   │   └── ports/                 # Repository interfaces (protocols)
│   │
│   ├── services/                  # 🟢 Application Services Layer
│   │   ├── conversation/          # Conversation orchestration
│   │   ├── analysis/              # One-shot analysis services
│   │   ├── enrichment/            # Context enrichment
│   │   ├── prompt/                # Prompt management
│   │   └── llm/                   # LLM orchestration
│   │
│   ├── infrastructure/            # 🔴 Infrastructure Layer
│   │   ├── repositories/          # Repository implementations
│   │   ├── llm/providers/         # LLM provider adapters
│   │   ├── external/              # External API clients
│   │   ├── cache/                 # Caching implementations
│   │   └── observability/         # Logging, metrics, tracing
│   │
│   ├── api/                       # 🔵 API/Presentation Layer
│   │   ├── routes/                # FastAPI endpoints
│   │   ├── middleware/            # Middleware (logging, errors)
│   │   ├── dependencies.py        # Dependency injection
│   │   └── main.py                # FastAPI app
│   │
│   ├── workflows/                 # 🔄 LangGraph Workflows
│   │   ├── base.py
│   │   ├── coaching_workflow.py
│   │   └── analysis_workflow.py
│   │
│   ├── models/                    # 📦 DTOs (To be deprecated)
│   │   ├── requests.py            # API request models
│   │   └── responses.py           # API response models
│   │
│   └── core/                      # 🔧 Core Utilities
│       ├── types.py               # Domain ID types
│       ├── constants.py           # Enums and constants
│       ├── config.py              # Configuration
│       └── exceptions.py          # Base exceptions
│
├── tests/
│   ├── unit/                      # Unit tests (70%)
│   ├── integration/               # Integration tests (20%)
│   └── e2e/                       # E2E tests (10%)
│
├── prompts/                       # Prompt templates
└── pyproject.toml                 # Dependencies
```

### Naming Conventions

- **Files**: `snake_case.py` (e.g., `alignment_calculator.py`)
- **Classes**: `PascalCase` (e.g., `AlignmentCalculatorService`)
- **Functions/Methods**: `snake_case` (e.g., `calculate_alignment`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `PHASE_PROGRESS_WEIGHTS`)
- **Private**: `_leading_underscore` (e.g., `_internal_method`)

### Import Organization

```python
"""Module docstring."""

# 1. Standard library
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

# 2. Third-party packages
from pydantic import BaseModel, Field, EmailStr
from fastapi import APIRouter, Depends, HTTPException

# 3. Internal modules - absolute imports
from coaching.src.domain.entities.conversation import Conversation
from coaching.src.domain.value_objects.message import Message
from coaching.src.core.types import ConversationId, UserId
from coaching.src.core.constants import ConversationPhase

# 4. Module-level constants
LOGGER = structlog.get_logger(__name__)
```

---

## 🚀 Implementation Roadmap Integration

**CRITICAL**: Always check current phase before implementing!

### Current Phase Status

Check `docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md` for:
- Current phase requirements
- Acceptance criteria
- Test coverage targets
- Deliverables checklist

### Phase-Specific Guidelines

**Phase 1 (Foundation & Domain Core)**:
- Focus: Domain entities, value objects, domain services
- No infrastructure dependencies in domain layer
- 70%+ unit test coverage
- Observability foundation (structlog)

**Phase 2 (Domain Events & Exceptions)**:
- Focus: Event-driven architecture
- Domain event emission
- Exception hierarchy

**Phase 3 (Infrastructure Layer)**:
- Focus: Repository implementations
- LLM provider adapters
- External service clients
- Integration tests

**Phase 4+ (Application Services, Analysis, Workflows, API)**:
- Follow roadmap sequentially
- Each phase builds on previous
- Quality gates enforced

---

## 📊 Definition of Done (CRITICAL)

**An issue is NEVER complete unless ALL criteria are met:**

### Code Quality Checklist
- [ ] All functions have complete type hints
- [ ] No `dict[str, Any]` in domain layer
- [ ] Pydantic models used throughout
- [ ] No TODO comments
- [ ] No hardcoded values (use configuration)
- [ ] Error handling follows patterns
- [ ] Structured logging with context

### Testing Checklist
- [ ] Unit tests written (70%+ coverage)
- [ ] Integration tests for infrastructure
- [ ] E2E tests for critical flows
- [ ] All tests passing
- [ ] Edge cases covered
- [ ] Mocking at appropriate boundaries

### Validation Checklist
- [ ] `black src/ tests/` (formatting)
- [ ] `ruff check src/ tests/` (linting)
- [ ] `mypy src/ --strict` (type checking)
- [ ] `pytest --cov=src --cov-fail-under=75` (tests)
- [ ] No warnings or errors

### Documentation Checklist
- [ ] Docstrings for public API
- [ ] Complex logic documented
- [ ] Architecture docs updated
- [ ] README updated if needed

### Process Checklist
- [ ] Feature branch from dev
- [ ] Commits reference issue numbers
- [ ] PR created with description
- [ ] Code review approved
- [ ] PR merged to dev
- [ ] Issue closed with summary

---

## 🔐 Security & Best Practices

### Input Validation

**Validate at API boundaries**:

```python
from pydantic import BaseModel, Field, validator

class CreateConversationRequest(BaseModel):
    """Validated request model."""
    user_id: str = Field(..., min_length=1, max_length=100)
    topic: str = Field(..., regex="^(core_values|purpose|vision|goals)$")
    
    @validator('topic')
    def validate_topic(cls, v: str) -> str:
        """Ensure topic is supported."""
        if v not in SUPPORTED_TOPICS:
            raise ValueError(f"Unsupported topic: {v}")
        return v
```

### Multi-Tenancy (MANDATORY)

**Always scope queries by tenant**:

```python
# ✅ Good: Tenant-scoped
class ConversationRepository:
    def __init__(self, tenant_id: TenantId) -> None:
        self.tenant_id = tenant_id
    
    async def list_by_user(self, user_id: UserId) -> list[Conversation]:
        # Query includes tenant_id filter
        return await self._query(
            PK=f"TENANT#{self.tenant_id}#USER#{user_id}"
        )

# ❌ Bad: No tenant isolation
async def list_conversations(user_id: str) -> list[dict]:
    return dynamodb.query(KeyConditionExpression="user_id = :uid")
```

### Secrets Management

**NEVER hardcode secrets**:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Environment-based configuration."""
    jwt_secret: str = Field(..., description="JWT signing secret")
    bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## 🤝 AI Assistant Behavior

### Before Making Changes

1. **Read Context**: Review relevant files and documentation
2. **Check Phase**: Verify current implementation phase
3. **Understand Requirements**: Read issue acceptance criteria
4. **Plan Approach**: Think through solution architecture
5. **Ask if Unclear**: Clarify ambiguous requirements

### When Implementing

1. **Follow Patterns**: Use established patterns in codebase
2. **Write Tests First**: TDD approach when possible
3. **Document Decisions**: Add comments for complex logic
4. **Use Types**: Strong typing throughout
5. **Validate Early**: Run checks frequently

### After Implementation

1. **Run All Checks**: Format, lint, type check, test
2. **Update Documentation**: Keep docs current
3. **Update Issue**: Comment progress
4. **Review Changes**: Self-review before PR
5. **Clean Up**: Remove debug code, unused imports

### Communication Style

- **Transparent**: Explain reasoning and trade-offs
- **Specific**: Reference files, functions, line numbers
- **Alternative Solutions**: Suggest multiple approaches
- **Admit Uncertainty**: Ask rather than guess
- **Concise**: Be brief but complete

---

## 📚 Quick Reference Links

### Essential Documentation

- **Implementation Roadmap**: `docs/Plans/REVISED_IMPLEMENTATION_ROADMAP.md`
- **Architecture Design**: `docs/Plans/AI_COACHING_ARCHITECTURE_DESIGN.md`
- **Plan Summary**: `docs/Plans/PLAN_UPDATE_SUMMARY.md`

### Technical Guides

- **Branching Strategy**: `docs/Guides/BRANCHING_STRATEGY.md`
- **Development Guide**: `docs/Guides/DEVELOPMENT_GUIDE.md`
- **Development Standards**: `docs/Guides/DEVELOPMENT_STANDARDS.md`
- **Engineering Guide**: `docs/Guides/ENGINEERING_GUIDE.md`
- **Clean Architecture**: `docs/Guides/clean-architecture-ddd-guidelines.md`
- **Shared Types**: `docs/Guides/shared-types-guide.md`

### Project Files

- **Main README**: `README.md`
- **Coaching README**: `coaching/README.md`
- **Project Config**: `pyproject.toml`

---

## 🎯 Summary Checklist

Before starting ANY work:

- [ ] Read current phase in REVISED_IMPLEMENTATION_ROADMAP.md
- [ ] Check GitHub issue requirements
- [ ] Verify in feature branch (not dev/staging/master)
- [ ] Virtual environment activated
- [ ] Understand acceptance criteria

While working:

- [ ] Follow Clean Architecture layers
- [ ] Use strong typing (Pydantic, NewType)
- [ ] Write tests alongside implementation
- [ ] Run pre-commit checks frequently
- [ ] Commit with issue reference

Before closing issue:

- [ ] All Definition of Done criteria met
- [ ] All tests passing (coverage targets)
- [ ] Zero type/lint errors
- [ ] Documentation updated
- [ ] PR approved and merged

---

**Remember**: Quality over speed. No shortcuts. Expert standards always.

---

_This document integrates guidance from all project documentation and enforces consistent development practices across the PurposePath AI Coaching Service._

**Version 2.0.0 - October 9, 2025**
