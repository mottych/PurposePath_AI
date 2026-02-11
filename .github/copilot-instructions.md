# AI Code Assistant Instructions - PurposePath AI

**Version**: 3.0.0  
**Last Updated**: December 12, 2025

## Architecture Overview

PurposePath is a serverless AI coaching platform using **Clean Architecture with DDD**. The coaching service (`coaching/src/`) orchestrates multi-turn conversations with Amazon Bedrock (Claude).

```
coaching/src/
├── domain/          # Business logic, NO external dependencies
│   ├── entities/    # Aggregate roots (Conversation)
│   ├── value_objects/  # Immutable (Message, AlignmentScore)
│   ├── ports/       # Repository interfaces (Protocol classes)
│   └── exceptions/  # Domain-specific exceptions
├── application/     # Use case orchestration
│   ├── conversation/  # ConversationApplicationService
│   └── ai_engine/   # LLM orchestration
├── infrastructure/  # External concerns
│   ├── repositories/  # DynamoDB implementations
│   └── llm/providers/ # Bedrock, Anthropic, OpenAI adapters
├── api/             # FastAPI routes, middleware, auth
│   ├── routes/      # Endpoint definitions
│   └── dependencies/ # Dependency injection
└── core/            # Types, constants, config
```

**Dependency Rule**: API → Application → Domain ← Infrastructure (domain has NO outward dependencies)

## Critical Development Rules

### Workflow (MANDATORY)
- **Always work in feature branch off `dev`** - NEVER commit to master/staging/dev directly
- **Every change needs a GitHub issue** - Mark `in-progress`, reference in commits
- **Commit format**: `feat(coaching): description - refs #42`
- **Before merge**: All tests pass, zero mypy/ruff errors (even pre-existing ones)

### Type Safety (MANDATORY)
- **ZERO `dict[str, Any]` in domain layer** - use Pydantic models
- **Use NewType IDs** from `coaching/src/core/types.py`:
  ```python
  from coaching.src.core.types import ConversationId, UserId, TenantId
  ```
- **Transform DynamoDB responses immediately** to domain entities

### Multi-Tenancy (MANDATORY)
All queries MUST enforce tenant isolation. Two patterns exist:

```python
# Pattern 1: Composite key (shared tables) - see shared/repositories/
Key={"pk": f"TENANT#{tenant_id}", "sk": f"ENTITY#{entity_id}"}

# Pattern 2: Simple key + filter (coaching conversations)
response = table.get_item(Key={"conversation_id": conversation_id})
if item.get("tenant_id") != tenant_id:
    return None  # Enforce isolation
```

### Test Coverage (MANDATORY)
- **Domain layer**: 85%+ unit test coverage
- **Service layer**: 75%+ coverage
- **Overall project**: 75%+ combined coverage

## Key Commands

```powershell
# Quality checks (run before every commit)
.\scripts\pre-commit-check.ps1        # Full check with tests
.\scripts\pre-commit-check.ps1 -Quick # Skip tests

# Auto-fix formatting issues
.\scripts\quick-fix.ps1

# Manual validation
python -m ruff check coaching/ shared/ --fix
python -m ruff format coaching/ shared/
python -m mypy coaching/src shared/ --explicit-package-bases

# Tests
cd coaching && uv run pytest                    # All tests
cd coaching && uv run pytest -k "test_name"     # Specific test
cd coaching && uv run pytest --cov=src          # With coverage

# Local development server
cd coaching && uv run uvicorn src.api.main:app --reload

# Deploy (Pulumi)
cd infrastructure/pulumi && pulumi up   # Infrastructure
cd coaching/pulumi && pulumi up         # Lambda + API Gateway
```

## Code Patterns

### Domain Entity (Aggregate Root)
```python
# coaching/src/domain/entities/conversation.py
class Conversation(BaseModel):
    conversation_id: ConversationId
    user_id: UserId
    tenant_id: TenantId
    status: ConversationStatus = ConversationStatus.ACTIVE
    
    def add_message(self, role: MessageRole, content: str) -> None:
        if not self.is_active():
            raise ConversationNotActive(self.conversation_id)
```

### Application Service
```python
# coaching/src/application/conversation/conversation_service.py
class ConversationApplicationService:
    def __init__(self, conversation_repository: ConversationRepositoryPort):
        self.repository = conversation_repository  # Inject port, not implementation
```

### Repository (Port/Adapter)
```python
# Port (domain layer)
class ConversationRepositoryPort(Protocol):
    async def get_by_id(self, id: ConversationId) -> Conversation | None: ...

# Adapter (infrastructure layer)
class DynamoDBConversationRepository:
    async def get_by_id(self, id: ConversationId) -> Conversation | None:
        response = self.table.get_item(Key={"conversation_id": id})
        return Conversation.model_validate(response["Item"]) if "Item" in response else None
```

### API Route with Dependency Injection
```python
# coaching/src/api/routes/conversations.py
@router.post("/initiate", response_model=ConversationResponse)
async def initiate_conversation(
    request: InitiateConversationRequest,
    user: UserContext = Depends(get_current_user),
    handler: GenericAIHandler = Depends(get_generic_handler),
) -> ConversationResponse:
```

### AI Workflows (LangGraph)
For complex AI orchestration, use LangGraph workflows in `coaching/src/workflows/`:
- Keep workflow logic separate from business logic
- Use typed state objects for workflow data
- Implement as composable, testable graph nodes

## Tech Stack Quick Reference

| Component | Technology |
|-----------|------------|
| API Framework | FastAPI + Mangum (Lambda adapter) |
| LLM | Amazon Bedrock (Claude), LangChain, LangGraph |
| Database | DynamoDB (single-table design) |
| IaC | Pulumi (TypeScript for Lambda, Python for infra) |
| Auth | JWT with tenant/user context |
| Observability | structlog for structured logging |

## Documentation References

- Architecture: `docs/Plans/AI_COACHING_ARCHITECTURE_DESIGN.md`
- Clean Architecture Guide: `docs/Guides/clean-architecture-ddd-guidelines.md`
- API Specs: `docs/Specifications/`

**When in doubt - ask me**
