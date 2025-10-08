# PurposePath API: Development Standards & Best Practices

## 🎯 Mission Statement

**Objective:** Establish and maintain a codebase that is strongly typed, follows clean architecture principles, and prevents technical debt accumulation through enforced development standards.

## 🛠️ Recommended Development Environment

### IDE Configuration: VS Code (Recommended Primary)

#### Essential Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.mypy-type-checker", 
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-toolsai.jupyter",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "github.vscode-pull-request-github",
    "github.copilot",
    "github.copilot-chat"
  ]
}
```

#### Workspace Settings (.vscode/settings.json)

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.completeFunctionParens": true,
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.inlayHints.variableTypes": true,
  "python.linting.mypyEnabled": true,
  "python.linting.enabled": true,
  "python.linting.lintOnSave": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=100"],
  "python.sortImports.args": ["--profile", "black"],
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  "editor.formatOnSave": true,
  "editor.formatOnPaste": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true,
    "source.fixAll": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/node_modules": true
  },
  "search.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true, 
    "**/.mypy_cache": true
  }
}
```

### Alternative IDE Support

#### JetBrains PyCharm Professional

- **Pros:** Superior debugging, database integration, excellent refactoring
- **Cons:** Resource intensive, licensing cost
- **Setup:** Import project, enable type checking, configure AWS toolkit

#### Cursor (AI-Enhanced VS Code)

- **Pros:** AI pair programming, VS Code compatibility
- **Cons:** Early stage, potential privacy concerns
- **Setup:** Same as VS Code + AI features configuration

## 📦 Development Toolchain

### Core Tools Installation

```bash
# Development dependencies
pip install -r requirements-dev.txt

# Key tools include:
# - mypy: Static type checking
# - black: Code formatting  
# - isort: Import sorting
# - flake8: Linting
# - pytest: Testing framework
# - pre-commit: Git hooks
# - coverage: Test coverage
```

### Pre-commit Hook Configuration (.pre-commit-config.yaml)

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        args: [--line-length=100]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=100, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--strict, --show-error-codes]
```

### GitHub Actions CI/CD (.github/workflows/type-check.yml)

```yaml
name: Type Safety & Code Quality

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  type-check:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11, 3.12]
        service: [account, coaching, traction]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r ${{ matrix.service }}/requirements-dev.txt
        
    - name: Type check with mypy
      run: |
        cd ${{ matrix.service }}
        mypy src/ --strict --show-error-codes
        
    - name: Lint with flake8
      run: |
        cd ${{ matrix.service }}
        flake8 src/ --max-line-length=100
        
    - name: Format check with black
      run: |
        cd ${{ matrix.service }}
        black --check --line-length=100 src/
        
    - name: Import order check
      run: |
        cd ${{ matrix.service }}
        isort --check-only --profile=black src/
        
    - name: Run tests with coverage
      run: |
        cd ${{ matrix.service }}
        pytest --cov=src --cov-report=xml --cov-fail-under=80
        
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
```

## 🏗️ Architectural Standards

### Clean Architecture Layers

#### 1. Presentation Layer (FastAPI Routes)

```python
# Standard route structure
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from ..models.requests import CreateUserRequest
from ..models.responses import UserResponse
from ..services.user_service import UserService
from ..dependencies import get_user_service, get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserProfile, Depends(get_current_user)]
) -> UserResponse:
    """Create a new user with proper type safety."""
    try:
        user = await service.create_user(request)
        return UserResponse.from_domain(user)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already exists: {e.email}"
        )
```

#### 2. Application Layer (Services)

```python
# Service layer with dependency injection
from typing import Protocol

class UserRepositoryProtocol(Protocol):
    async def create_user(self, user: UserEntity) -> UserEntity: ...
    async def get_user_by_email(self, email: str) -> UserEntity | None: ...

class UserService:
    def __init__(self, repository: UserRepositoryProtocol) -> None:
        self._repository = repository
    
    async def create_user(self, request: CreateUserRequest) -> UserEntity:
        # Check for existing user
        existing = await self._repository.get_user_by_email(request.email)
        if existing:
            raise UserAlreadyExistsError(request.email)
        
        # Create domain entity
        user = UserEntity(
            user_id=generate_user_id(),
            email=request.email,
            name=request.name,
            created_at=datetime.now(UTC)
        )
        
        return await self._repository.create_user(user)
```

#### 3. Domain Layer (Models & Entities)

```python
# Domain entities with Pydantic
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Literal

class UserEntity(BaseModel):
    """Core user domain entity."""
    user_id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address") 
    name: str = Field(..., min_length=1, max_length=100)
    subscription_tier: Literal["starter", "professional", "enterprise"] = "starter"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime | None = None
    
    class Config:
        frozen = True  # Immutable domain entity

# Request/Response models  
class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    
class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    subscription_tier: str
    is_active: bool
    created_at: datetime
    
    @classmethod
    def from_domain(cls, user: UserEntity) -> "UserResponse":
        return cls(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            subscription_tier=user.subscription_tier,
            is_active=user.is_active,
            created_at=user.created_at
        )
```

#### 4. Infrastructure Layer (Repositories)

```python
# Repository implementation with proper typing
from mypy_boto3_dynamodb import DynamoDBServiceResource
from mypy_boto3_dynamodb.service_resource import Table

class DynamoDBUserRepository:
    def __init__(self, table: Table) -> None:
        self._table = table
    
    async def create_user(self, user: UserEntity) -> UserEntity:
        item = {
            "PK": f"USER#{user.user_id}",
            "SK": f"PROFILE#{user.user_id}",
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "subscription_tier": user.subscription_tier,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat(),
            "type": "user_profile"
        }
        
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(PK)"
            )
            return user
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise UserAlreadyExistsError(user.email)
            raise
```

### Type Definition Standards

#### Common Type Aliases

```python
# shared/types/common.py
from typing import TypeAlias, NewType, Literal
from datetime import datetime

# Strong typing for domain IDs
UserId: TypeAlias = str
TenantId: TypeAlias = str  
ConversationId: TypeAlias = str
MessageId: TypeAlias = str

# AWS Resource identifiers
DynamoDBKey: TypeAlias = dict[str, str]
S3Key: TypeAlias = str

# API Response patterns
SuccessResponse: TypeAlias = dict[Literal["success"], Literal[True]]
ErrorResponse: TypeAlias = dict[Literal["error"], str]

# Common data structures
TimestampedRecord: TypeAlias = dict[str, str | datetime]
PaginationParams: TypeAlias = dict[Literal["page", "size"], int]
```

#### TypedDict for External APIs

```python
# shared/types/external.py
from typing import TypedDict, NotRequired, Literal

class StripeCustomer(TypedDict):
    id: str
    email: str
    name: str | None
    created: int
    metadata: dict[str, str]

class DynamoDBItem(TypedDict, total=False):
    PK: str
    SK: str
    type: str
    created_at: str
    updated_at: NotRequired[str]

class BedrockResponse(TypedDict):
    output: dict[str, str]
    usage: dict[Literal["input_tokens", "output_tokens"], int]
    stop_reason: Literal["end_turn", "tool_use", "max_tokens"]
```

## 🧪 Testing Standards

### Test Structure & Typing

```python
# tests/test_user_service.py
import pytest
from unittest.mock import AsyncMock
from datetime import datetime, UTC

from src.services.user_service import UserService
from src.models.entities import UserEntity
from src.models.requests import CreateUserRequest
from src.exceptions import UserAlreadyExistsError

class TestUserService:
    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Typed mock repository."""
        repository = AsyncMock()
        repository.create_user.return_value = UserEntity(
            user_id="test-user-123",
            email="test@example.com",
            name="Test User", 
            created_at=datetime.now(UTC)
        )
        return repository
    
    @pytest.fixture
    def service(self, mock_repository: AsyncMock) -> UserService:
        """User service with mocked dependencies."""
        return UserService(repository=mock_repository)
    
    async def test_create_user_success(
        self, 
        service: UserService, 
        mock_repository: AsyncMock
    ) -> None:
        """Test successful user creation."""
        # Arrange
        request = CreateUserRequest(
            email="test@example.com",
            name="Test User"
        )
        mock_repository.get_user_by_email.return_value = None
        
        # Act
        result = await service.create_user(request)
        
        # Assert
        assert result.email == "test@example.com"
        assert result.name == "Test User"
        mock_repository.create_user.assert_called_once()
    
    async def test_create_user_duplicate_email(
        self,
        service: UserService,
        mock_repository: AsyncMock
    ) -> None:
        """Test user creation with duplicate email."""
        # Arrange
        request = CreateUserRequest(
            email="existing@example.com", 
            name="Test User"
        )
        existing_user = UserEntity(
            user_id="existing-123",
            email="existing@example.com",
            name="Existing User",
            created_at=datetime.now(UTC)
        )
        mock_repository.get_user_by_email.return_value = existing_user
        
        # Act & Assert
        with pytest.raises(UserAlreadyExistsError):
            await service.create_user(request)
```

### Integration Test Patterns

```python
# tests/integration/test_user_api.py
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient

from src.main import app

@pytest.fixture
async def async_client() -> AsyncClient:
    """Async HTTP client for integration tests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

class TestUserAPI:
    async def test_create_user_integration(
        self, 
        async_client: AsyncClient
    ) -> None:
        """Full integration test for user creation."""
        # Arrange
        user_data = {
            "email": "integration@example.com",
            "name": "Integration User"
        }
        
        # Act
        response = await async_client.post("/users/", json=user_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["email"] == "integration@example.com"
        assert "user_id" in response_data
```

## 📏 Code Quality Standards

### Function Signature Requirements

```python
# ✅ Good: Complete type annotations
async def process_conversation(
    conversation_id: str,
    user_context: RequestContext,
    message: str,
    *,  # Force keyword-only parameters
    max_tokens: int = 1000,
    temperature: float = 0.7
) -> ConversationResponse:
    """Process user message and generate response."""
    pass

# ❌ Bad: Missing type annotations  
async def process_conversation(conversation_id, user_context, message, max_tokens=1000):
    pass
```

### Error Handling Patterns

```python
# Domain-specific exceptions
class PurposePathError(Exception):
    """Base exception for PurposePath application."""
    pass

class UserError(PurposePathError):
    """User-related errors."""
    pass

class UserNotFoundError(UserError):
    """User not found in system."""
    def __init__(self, user_id: str) -> None:
        self.user_id = user_id
        super().__init__(f"User not found: {user_id}")

class ConversationError(PurposePathError):
    """Conversation-related errors.""" 
    pass

# Error handling in services
async def get_user_conversations(user_id: str) -> list[ConversationSummary]:
    try:
        user = await user_repository.get_user(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        
        conversations = await conversation_repository.get_by_user_id(user_id)
        return [ConversationSummary.from_entity(c) for c in conversations]
        
    except ClientError as e:
        logger.error(f"AWS error retrieving conversations: {e}")
        raise ConversationError(f"Failed to retrieve conversations for user {user_id}")
```

### Logging Standards

```python
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Structured logging with proper typing
async def create_user(request: CreateUserRequest) -> UserEntity:
    logger.info(
        "Creating new user",
        extra={
            "email": request.email,
            "name": request.name,
            "action": "user_creation_started"
        }
    )
    
    try:
        user = await user_repository.create_user(request)
        logger.info(
            "User created successfully",
            extra={
                "user_id": user.user_id,
                "email": user.email,
                "action": "user_creation_completed"
            }
        )
        return user
    except Exception as e:
        logger.error(
            "User creation failed", 
            extra={
                "email": request.email,
                "error": str(e),
                "action": "user_creation_failed"
            },
            exc_info=True
        )
        raise
```

## 🔧 Configuration Management

### Environment-Specific Settings

```python
# src/core/config.py
from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    # Environment
    stage: Literal["dev", "staging", "prod"] = "dev"
    debug: bool = False
    
    # Database
    dynamodb_table_name: str
    dynamodb_endpoint_url: str | None = None
    
    # Authentication
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # External Services
    stripe_api_key: str
    stripe_webhook_secret: str
    
    # LLM Configuration
    bedrock_region: str = "us-east-1"
    default_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    max_tokens: int = 4000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Dependency injection
@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

## 🚫 Anti-Patterns to Avoid

### Type Safety Violations

```python
# ❌ Avoid: Generic Any usage
def process_data(data: Any) -> Any:
    return data.get("result")

# ✅ Better: Specific types
def process_user_data(data: dict[str, str]) -> str | None:
    return data.get("result")

# ❌ Avoid: Untyped external API calls
customer = stripe.Customer.create(email=email)
return customer.id

# ✅ Better: Typed boundaries
customer = stripe.Customer.create(email=email)  # type: ignore[misc]
return cast(str, customer.id)  # Known from Stripe docs
```

### Architecture Violations

```python
# ❌ Avoid: Business logic in routes
@router.post("/users/")
async def create_user(request: CreateUserRequest):
    # Don't put business logic here
    if await user_repository.get_by_email(request.email):
        raise HTTPException(409, "User exists")
    user = await user_repository.create(request)
    return user

# ✅ Better: Delegate to service layer
@router.post("/users/")
async def create_user(
    request: CreateUserRequest,
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.create_user(request)
```

## 📊 Monitoring & Maintenance

### Type Coverage Tracking

```bash
# Weekly type coverage report
mypy --html-report coverage-report src/
mypy --txt-report coverage-report src/

# Coverage metrics to track:
# - Functions with complete annotations: >95%
# - Lines with type information: >90%  
# - Files passing strict mode: 100%
```

### Automated Quality Gates

```yaml
# GitHub branch protection rules
rules:
  - name: "Type Safety"
    checks:
      - "Type check (3.11, account)"
      - "Type check (3.11, coaching)" 
      - "Type check (3.11, traction)"
    required: true
    
  - name: "Code Quality"
    checks:
      - "Lint check"
      - "Format check"
      - "Import order check"
    required: true
    
  - name: "Test Coverage"
    checks:
      - "Coverage >80%"
    required: true
```

## 📚 Team Training & Knowledge Sharing

### Onboarding Checklist

- [ ] Development environment setup complete
- [ ] VS Code extensions installed and configured
- [ ] Pre-commit hooks activated
- [ ] Type safety guidelines reviewed
- [ ] Architecture patterns understood
- [ ] First type-safe feature implemented and reviewed

### Regular Reviews

- **Weekly:** Type coverage reports and error trending
- **Monthly:** Architecture pattern adherence review
- **Quarterly:** Toolchain updates and best practice evolution

---

**Document Version:** 1.0  
**Last Updated:** September 24, 2025  
**Next Review:** December 24, 2025  
**Maintainer:** Engineering Team
