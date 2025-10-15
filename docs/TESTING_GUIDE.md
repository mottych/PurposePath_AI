# Testing Guide

**Project**: PurposePath AI Coaching API  
**Created**: October 14, 2025  
**Issue**: #37 - Testing Strategy

---

## 🎯 Overview

This guide covers the testing strategy, patterns, and practices for the PurposePath AI Coaching API.

**Test Coverage Target**: 75%+ across all modules

---

## 📦 Test Infrastructure

### Dependencies

All testing dependencies are in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=7.4.0,<9.0.0",
    "pytest-asyncio>=0.21.0,<1.0.0",
    "pytest-mock>=3.11.1,<4.0.0",
    "pytest-cov>=4.1.0,<6.0.0",
    "pytest-xdist>=3.3.1,<4.0.0",
    
    # Code quality
    "black>=23.7.0,<25.0.0",
    "ruff>=0.1.0,<1.0.0",
    "mypy>=1.4.1,<2.0.0",
    "pre-commit>=3.3.3,<4.0.0",
]
```

### Installation

```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

---

## 🧪 Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run specific test file
pytest coaching/tests/unit/test_llm_service.py

# Run tests by marker
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests
pytest -m "not slow"        # Exclude slow tests

# Run in parallel (faster)
pytest -n auto

# Verbose output
pytest -vv

# Stop on first failure
pytest -x

# Show local variables on failure
pytest --showlocals
```

### Coverage Commands

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html
# Open: htmlcov/index.html

# Terminal coverage report
pytest --cov --cov-report=term-missing

# Check if coverage meets threshold (75%)
pytest --cov --cov-fail-under=75
```

---

## 📂 Test Organization

### Directory Structure

```
coaching/
├── src/                    # Source code
└── tests/                  # All tests
    ├── __init__.py
    ├── conftest.py        # Shared fixtures
    ├── unit/              # Unit tests (70%)
    │   ├── test_llm_service.py
    │   ├── test_conversation_service.py
    │   └── ...
    ├── integration/       # Integration tests (20%)
    │   ├── test_dynamodb_integration.py
    │   ├── test_api_integration.py
    │   └── ...
    └── e2e/              # End-to-end tests (10%)
        ├── test_complete_conversation.py
        └── ...
```

### Test Pyramid

- **70% Unit Tests**: Fast, isolated, test single functions/classes
- **20% Integration Tests**: Test component interactions (DB, APIs)
- **10% E2E Tests**: Test complete user flows

---

## 🏷️ Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_calculation():
    assert add(2, 2) == 4

@pytest.mark.integration
async def test_database_query():
    result = await db.query()
    assert result is not None

@pytest.mark.e2e
async def test_complete_flow():
    # Full system test
    pass

@pytest.mark.slow
def test_expensive_operation():
    # Tests taking > 1 second
    pass

@pytest.mark.smoke
def test_critical_path():
    # Smoke test for critical functionality
    pass
```

**Run specific markers**:
```bash
pytest -m unit              # Fast unit tests only
pytest -m "unit and not slow"  # Fast unit tests
pytest -m "integration or e2e" # Higher level tests
```

---

## 🔧 Writing Tests

### Unit Test Example

```python
"""Unit tests for LLM service."""

import pytest
from unittest.mock import AsyncMock, Mock
from coaching.src.services.llm_service import LLMService


@pytest.mark.unit
class TestLLMService:
    """Test LLM service business logic."""
    
    @pytest.fixture
    def mock_provider_manager(self):
        """Create mock provider manager."""
        manager = AsyncMock()
        manager.get_provider.return_value = AsyncMock()
        return manager
    
    @pytest.fixture
    def llm_service(self, mock_provider_manager):
        """Create LLM service with mocked dependencies."""
        return LLMService(
            provider_manager=mock_provider_manager,
            workflow_orchestrator=AsyncMock(),
            prompt_service=AsyncMock(),
            default_provider="bedrock",
        )
    
    async def test_generate_completion_success(self, llm_service):
        """Test successful completion generation."""
        # Arrange
        prompt = "Test prompt"
        expected_response = "Test response"
        llm_service.provider_manager.get_provider.return_value.generate = AsyncMock(
            return_value=expected_response
        )
        
        # Act
        result = await llm_service.generate_completion(prompt)
        
        # Assert
        assert result == expected_response
        llm_service.provider_manager.get_provider.assert_called_once()
```

### Integration Test Example

```python
"""Integration tests for DynamoDB repository."""

import pytest
from coaching.src.infrastructure.repositories.conversation_repository import (
    ConversationRepository
)


@pytest.mark.integration
class TestConversationRepository:
    """Test DynamoDB integration."""
    
    @pytest.fixture
    async def repository(self, dynamodb_resource):
        """Create repository with real DynamoDB (LocalStack)."""
        return ConversationRepository(
            dynamodb_resource=dynamodb_resource,
            table_name="test-conversations",
        )
    
    async def test_create_and_retrieve_conversation(self, repository):
        """Test creating and retrieving a conversation."""
        # Arrange
        conversation = Conversation(
            conversation_id="test-123",
            user_id="user-456",
            tenant_id="tenant-789",
            topic="onboarding",
        )
        
        # Act
        await repository.create(conversation)
        retrieved = await repository.get(conversation.conversation_id)
        
        # Assert
        assert retrieved is not None
        assert retrieved.conversation_id == conversation.conversation_id
        assert retrieved.user_id == conversation.user_id
```

### Async Test Example

```python
"""Test async functions."""

import pytest


@pytest.mark.unit
class TestAsyncOperations:
    """Test async operations."""
    
    async def test_async_function(self):
        """Pytest-asyncio handles async automatically."""
        result = await some_async_function()
        assert result == expected_value
    
    @pytest.mark.asyncio
    async def test_with_explicit_marker(self):
        """Explicit async marker (optional with asyncio_mode=auto)."""
        result = await another_async_function()
        assert result is not None
```

---

## 🎭 Mocking Patterns

### Mock External Services

```python
from unittest.mock import AsyncMock, Mock, patch


# Mock AWS services
@patch("boto3.resource")
def test_with_mocked_dynamodb(mock_boto):
    mock_table = Mock()
    mock_boto.return_value.Table.return_value = mock_table
    # Test code here


# Mock HTTP calls
@patch("httpx.AsyncClient.get")
async def test_api_call(mock_get):
    mock_get.return_value = Mock(
        status_code=200,
        json=lambda: {"data": "value"}
    )
    # Test code here


# Mock LLM responses
@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    service.generate_completion.return_value = "Mocked LLM response"
    return service
```

### Pytest-Mock

```python
def test_with_pytest_mock(mocker):
    """Using pytest-mock plugin."""
    # Mock method
    mock_method = mocker.patch("module.Class.method")
    mock_method.return_value = "mocked"
    
    # Spy on method (calls real method but tracks calls)
    spy = mocker.spy(obj, "method")
    
    # Assert called
    spy.assert_called_once_with(arg1, arg2)
```

---

## 🔍 Test Fixtures

Fixtures are defined in `conftest.py`:

```python
"""Shared test fixtures."""

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def user_context():
    """Mock user context for API tests."""
    return UserContext(
        user_id="test-user-123",
        tenant_id="test-tenant-456",
        email="test@example.com",
    )


@pytest.fixture
async def llm_service():
    """Mock LLM service."""
    service = AsyncMock()
    service.generate_completion.return_value = "Test response"
    return service


@pytest.fixture
def sample_conversation():
    """Sample conversation for testing."""
    return Conversation(
        conversation_id="conv-123",
        user_id="user-456",
        tenant_id="tenant-789",
        topic="onboarding",
        status="active",
    )
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default: new for each test
def per_test_fixture():
    return "new instance per test"

@pytest.fixture(scope="class")  # Shared within test class
def per_class_fixture():
    return "shared in class"

@pytest.fixture(scope="module")  # Shared in module
def per_module_fixture():
    return "shared in module"

@pytest.fixture(scope="session")  # Shared across entire session
def per_session_fixture():
    return "shared across all tests"
```

---

## ✅ Pre-commit Hooks

Pre-commit hooks enforce code quality before commits.

### Setup

```bash
# Install hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

### Configured Hooks

1. **Ruff** - Linting and formatting
2. **MyPy** - Type checking
3. **YAML/JSON validation**
4. **Trailing whitespace removal**
5. **End-of-file fixer**
6. **Bandit** - Security checks

### Bypass (Use Sparingly!)

```bash
# Skip pre-commit hooks (NOT RECOMMENDED)
git commit --no-verify -m "message"
```

---

## 📊 Coverage Requirements

### Minimum Coverage: 75%

```bash
# Check coverage
pytest --cov --cov-fail-under=75

# If below 75%, build fails
```

### Coverage Configuration

In `pytest.ini`:

```ini
[pytest]
addopts =
    --cov=coaching/src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=75
```

### Excluding Files from Coverage

In `pyproject.toml`:

```toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
    "*/migrations/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```

---

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"
      
      - name: Run tests with coverage
        run: |
          pytest --cov --cov-fail-under=75
      
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
```

---

## 🎯 Best Practices

### 1. Test Naming

```python
# ✅ Good: Descriptive names
def test_user_creation_with_valid_email_succeeds():
    pass

def test_conversation_start_requires_authentication():
    pass

# ❌ Bad: Vague names
def test_user():
    pass

def test_1():
    pass
```

### 2. Arrange-Act-Assert Pattern

```python
def test_calculation():
    # Arrange: Set up test data
    a = 2
    b = 3
    
    # Act: Execute the code under test
    result = add(a, b)
    
    # Assert: Verify the result
    assert result == 5
```

### 3. One Assertion Per Test (Guideline)

```python
# ✅ Preferred: Focused test
def test_user_has_correct_email():
    user = create_user(email="test@example.com")
    assert user.email == "test@example.com"

def test_user_has_correct_name():
    user = create_user(name="John")
    assert user.name == "John"

# ⚠️ Acceptable for related assertions
def test_user_creation():
    user = create_user(email="test@example.com", name="John")
    assert user.email == "test@example.com"
    assert user.name == "John"
    assert user.created_at is not None
```

### 4. Use Fixtures for Setup

```python
# ✅ Good: Use fixtures
@pytest.fixture
def user():
    return create_test_user()

def test_user_deletion(user):
    delete_user(user.id)
    assert get_user(user.id) is None

# ❌ Bad: Duplicate setup
def test_user_deletion():
    user = create_test_user()  # Repeated setup
    delete_user(user.id)
```

### 5. Test Edge Cases

```python
def test_divide():
    # Happy path
    assert divide(10, 2) == 5
    
    # Edge cases
    assert divide(0, 5) == 0
    assert divide(5, 1) == 5
    
    # Error cases
    with pytest.raises(ZeroDivisionError):
        divide(5, 0)
```

---

## 📝 Common Patterns

### Testing Exceptions

```python
def test_invalid_input_raises_error():
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(invalid_data)
```

### Testing Async Context Managers

```python
async def test_async_context_manager():
    async with AsyncResource() as resource:
        assert resource.is_open
    assert resource.is_closed
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert double(input) == expected
```

---

## 🐛 Debugging Tests

### Run Specific Test

```bash
# By test name
pytest -k "test_user_creation"

# By file and test
pytest coaching/tests/unit/test_llm.py::test_generate_completion
```

### Debug Mode

```python
# Add breakpoint
def test_something():
    result = complex_calculation()
    breakpoint()  # Execution stops here
    assert result == expected
```

### Verbose Output

```bash
# Show all output including print statements
pytest -s

# Very verbose
pytest -vv

# Show locals on failure
pytest --showlocals
```

---

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Asyncio](https://pytest-asyncio.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Pre-commit](https://pre-commit.com/)

---

## ✅ Checklist for New Tests

- [ ] Test file named `test_*.py`
- [ ] Test functions named `test_*`
- [ ] Appropriate marker added (`@pytest.mark.unit`, etc.)
- [ ] Fixtures used for setup
- [ ] Arrange-Act-Assert pattern followed
- [ ] Edge cases covered
- [ ] Assertions are clear and specific
- [ ] Docstrings explain what is being tested
- [ ] Tests are independent (no shared state)
- [ ] Tests run successfully: `pytest path/to/test_file.py`
- [ ] Coverage maintained: `pytest --cov`

---

**Happy Testing! 🎉**
