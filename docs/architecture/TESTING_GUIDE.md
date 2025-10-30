# LLM Configuration System - Testing Guide

**Version**: 1.0.0  
**Last Updated**: October 30, 2025  
**Test Coverage**: 144 tests (126 unit + 18 performance)

---

## Overview

Comprehensive testing guide for the LLM Configuration System covering unit tests, integration tests, performance tests, and E2E testing strategies.

---

## Test Architecture

### Test Pyramid

```
┌──────────────┐
│  E2E Tests   │  5% - Critical user flows
├──────────────┤
│ Integration  │  15% - Service integration
├──────────────┤
│  Unit Tests  │  80% - Business logic
└──────────────┘
```

### Test Coverage Targets

| Layer | Target | Current |
|-------|--------|---------|
| Domain Entities | 90%+ | 95% |
| Registries | 85%+ | 92% |
| API Routes | 80%+ | 88% |
| Services | 75%+ | Partial |
| Overall | 80%+ | 87% |

---

## Test Categories

### 1. Unit Tests (126 tests)

**Location**: `coaching/tests/unit/`

#### Code Registry Tests (25 tests)

**File**: `test_constants.py`, `test_llm_interactions.py`, `test_llm_models.py`, `test_types.py`

**Coverage**:

- Interaction registry validation
- Model registry validation  
- Capability checks
- Type conversions and validation
- Registry lookup and verification

**Example**:

```python
def test_interaction_code_exists_in_registry():
    """Test that all interaction codes are valid."""
    assert "ALIGNMENT_ANALYSIS" in INTERACTION_REGISTRY
    assert "STRATEGY_ANALYSIS" in INTERACTION_REGISTRY
    
def test_model_code_capabilities():
    """Test model capability lookups."""
    model = MODEL_REGISTRY["CLAUDE_3_SONNET"]
    assert model.supports_streaming is True
    assert model.max_tokens == 200000
```

#### Domain Entity Tests (34 tests)

**Files**: `test_llm_configuration.py`, `test_template_metadata.py`

**Coverage**:

- Entity creation and validation
- Field constraints (temperature, max_tokens)
- Business rule validation
- Immutability checks
- Serialization/deserialization

**Example**:

```python
def test_configuration_temperature_range():
    """Test temperature must be between 0 and 1."""
    with pytest.raises(ValidationError):
        LLMConfiguration(
            config_id="test_config",
            interaction_code="ALIGNMENT_ANALYSIS",
            template_id="template_123",
            model_code="CLAUDE_3_SONNET",
            temperature=1.5,  # Invalid: > 1.0
            max_tokens=4096
        )
        
def test_template_required_parameters():
    """Test template tracks required parameters."""
    template = TemplateMetadata(
        template_id="template_123",
        template_code="ALIGNMENT_V1",
        interaction_code="ALIGNMENT_ANALYSIS",
        name="Test Template",
        description="Test",
        s3_bucket="test-bucket",
        s3_key="test-key",
        version="1.0.0",
        required_parameters=["goal_text", "purpose"]
    )
    
    assert "goal_text" in template.required_parameters
    assert "purpose" in template.required_parameters
```

#### API Tests (67 tests)

**Files**: `test_configurations_api.py`, `test_templates_api.py`, `test_interactions_api.py`, `test_models_api.py`

**Coverage**:

- Endpoint responses (200, 201, 400, 404)
- Request validation
- Authentication/authorization
- Pagination
- Filtering and sorting

**Example**:

```python
@pytest.mark.asyncio
async def test_create_configuration_success(
    client: TestClient,
    mock_service: AsyncMock
):
    """Test successful configuration creation."""
    request_data = {
        "interaction_code": "ALIGNMENT_ANALYSIS",
        "template_id": "template_123",
        "model_code": "CLAUDE_3_SONNET",
        "tier": "professional",
        "temperature": 0.7,
        "max_tokens": 4096
    }
    
    response = client.post(
        "/api/v1/admin/llm/configurations",
        json=request_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["interaction_code"] == "ALIGNMENT_ANALYSIS"
    assert data["tier"] == "professional"
```

---

### 2. Integration Tests (3 files)

**Location**: `coaching/tests/integration/`

#### Configuration Service Integration

**File**: `test_llm_configuration_integration.py`

**Coverage**:

- Repository integration
- Cache integration  
- Tier-based resolution logic
- Fallback mechanisms
- Validation against registries

**Example**:

```python
@pytest.mark.asyncio
async def test_resolve_with_tier_fallback(
    service: LLMConfigurationService,
    mock_repository: AsyncMock
):
    """Test fallback to default when tier config not found."""
    # Setup: No tier-specific config
    mock_repository.get_active_configuration_for_interaction.side_effect = [
        None,  # First call (tier-specific)
        default_config  # Second call (default)
    ]
    
    config = await service.resolve_configuration(
        interaction_code="ALIGNMENT_ANALYSIS",
        tier="enterprise"
    )
    
    assert config is not None
    assert config.tier is None  # Default config
```

#### Template Service Integration

**File**: `test_llm_template_integration.py`

**Coverage**:

- S3 fetch integration
- Cache integration
- Jinja2 rendering
- Syntax validation
- Parameter validation

**Example**:

```python
@pytest.mark.asyncio
async def test_render_template_with_parameters(
    service: LLMTemplateService,
    mock_s3_client: MagicMock
):
    """Test template rendering with Jinja2."""
    parameters = {
        "goal_text": "Test goal",
        "purpose": "Test purpose"
    }
    
    rendered = await service.render_template(
        template_id="template_123",
        parameters=parameters
    )
    
    assert "Test goal" in rendered
    assert "Test purpose" in rendered
```

#### End-to-End Workflows

**File**: `test_llm_config_e2e.py`

**Coverage**:

- Complete API-to-database flows
- Multi-tier configuration scenarios
- Template lifecycle (create → use → update)
- Configuration validation workflows

---

### 3. Performance Tests (18 tests)

**Location**: `coaching/tests/performance/`

#### Configuration Performance

**File**: `test_llm_config_performance.py`

**Tests**:

- Single resolution latency (< 100ms cold, < 5ms warm)
- Sequential throughput (> 500 req/s)
- Concurrent throughput (> 1000 req/s)
- Cache hit rate (> 95%)
- Cache speedup (> 10x)
- Tier fallback latency (< 150ms)

**Example**:

```python
@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_resolution_throughput(
    service: LLMConfigurationService,
    test_tier: str
):
    """Test concurrent resolution throughput."""
    num_requests = 100
    
    # Warm up cache
    await service.resolve_configuration(
        interaction_code="ALIGNMENT_ANALYSIS",
        tier=test_tier
    )
    
    # Measure concurrent throughput
    start = time.perf_counter()
    
    tasks = [
        service.resolve_configuration(
            interaction_code="ALIGNMENT_ANALYSIS",
            tier=test_tier
        )
        for _ in range(num_requests)
    ]
    await asyncio.gather(*tasks)
    
    elapsed = time.perf_counter() - start
    throughput = num_requests / elapsed
    
    assert throughput > 1000
```

#### Template Performance

**File**: `test_llm_template_performance.py`

**Tests**:

- Template fetch latency (< 150ms cold, < 5ms warm)
- Rendering latency (< 10ms simple, < 20ms complex)
- Rendering throughput (> 1000/s sequential, > 2000/s concurrent)
- S3 cache effectiveness (< 5% S3 calls after warm-up)
- Cache speedup vs S3 (> 10x)

---

## Running Tests

### Run All Tests

```bash
# All unit tests
pytest coaching/tests/unit/ -v

# All integration tests
pytest coaching/tests/integration/ -v

# All performance tests
pytest coaching/tests/performance/ -v -m performance

# All tests
pytest coaching/tests/ -v
```

### Run Specific Test Files

```bash
# Single file
pytest coaching/tests/unit/domain/entities/llm_config/test_llm_configuration.py -v

# Specific test class
pytest coaching/tests/unit/api/routes/admin/test_configurations_api.py::TestCreateConfiguration -v

# Specific test
pytest coaching/tests/unit/api/routes/admin/test_configurations_api.py::TestCreateConfiguration::test_create_configuration_success -v
```

### Coverage Reports

```bash
# Run with coverage
pytest coaching/tests/unit/ --cov=coaching/src --cov-report=html

# View coverage report
open htmlcov/index.html

# Coverage threshold check
pytest coaching/tests/unit/ --cov=coaching/src --cov-fail-under=80
```

### Performance Testing

```bash
# Run performance tests with output
pytest coaching/tests/performance/ -v -m performance -s

# Run specific performance test
pytest coaching/tests/performance/test_llm_config_performance.py::TestConfigurationResolutionPerformance -v -s
```

---

## Test Fixtures

### Common Fixtures

**Request Context**:

```python
@pytest.fixture
def admin_context() -> RequestContext:
    """Admin request context for testing."""
    return RequestContext(
        user_id="admin_user_123",
        tenant_id="tenant_123",
        role=UserRole.ADMIN,
        subscription_tier=SubscriptionTier.PROFESSIONAL
    )
```

**Test Configuration**:

```python
@pytest.fixture
def test_config() -> LLMConfiguration:
    """Sample LLM configuration for testing."""
    return LLMConfiguration(
        config_id="test_config_123",
        interaction_code="ALIGNMENT_ANALYSIS",
        template_id="template_123",
        model_code="CLAUDE_3_SONNET",
        tier="professional",
        temperature=0.7,
        max_tokens=4096,
        is_active=True,
        created_by="test_user",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        effective_from=datetime.utcnow()
    )
```

**Mock Services**:

```python
@pytest.fixture
def mock_config_service() -> AsyncMock:
    """Mock configuration service."""
    service = AsyncMock(spec=LLMConfigurationService)
    service.resolve_configuration.return_value = test_config()
    return service

@pytest.fixture
def mock_cache() -> MagicMock:
    """Mock cache with in-memory store."""
    cache = MagicMock()
    cache_store = {}
    
    cache.get.side_effect = lambda key: cache_store.get(key)
    cache.set.side_effect = lambda k, v, ttl=None: cache_store.__setitem__(k, v)
    
    return cache
```

---

## Testing Best Practices

### 1. Test Naming Convention

Use descriptive test names that explain the scenario:

```python
# Good
def test_resolve_configuration_falls_back_to_default_when_tier_not_found():
    pass

# Bad  
def test_resolve():
    pass
```

### 2. Arrange-Act-Assert Pattern

Structure tests clearly:

```python
def test_create_configuration():
    # Arrange
    request_data = {...}
    mock_service.create.return_value = expected_config
    
    # Act
    response = client.post("/configurations", json=request_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["config_id"] == expected_config.config_id
```

### 3. Test Isolation

Each test should be independent:

```python
@pytest.fixture(autouse=True)
def reset_mocks(mock_repository, mock_cache):
    """Reset mocks before each test."""
    mock_repository.reset_mock()
    mock_cache.reset_mock()
    yield
```

### 4. Async Testing

Use pytest-asyncio for async tests:

```python
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

### 5. Mock External Dependencies

Always mock external services:

```python
@pytest.fixture
def mock_s3_client():
    """Mock S3 client."""
    with patch('boto3.client') as mock:
        mock.return_value.get_object.return_value = {
            'Body': Mock(read=lambda: b'template content')
        }
        yield mock
```

---

## Continuous Integration

### GitHub Actions Workflow

Tests run automatically on:

- Push to `dev` or `main` branches
- Pull requests to `dev` or `main`

**Workflow Steps**:

1. Lint check (Ruff)
2. Type check (MyPy)
3. Unit tests
4. Integration tests
5. Coverage report

### Pre-Commit Hooks

Run tests before committing:

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

**`.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest coaching/tests/unit/
        language: system
        pass_filenames: false
```

---

## Test Maintenance

### When to Update Tests

Update tests when:

- Adding new features
- Modifying business logic
- Changing API contracts
- Refactoring code
- Fixing bugs

### Test Refactoring

Refactor tests to:

- Remove duplication
- Improve readability
- Enhance maintainability
- Add missing coverage

### Flaky Test Management

If a test is flaky:

1. Identify the cause (timing, external dependency)
2. Add retries for external calls
3. Use deterministic test data
4. Fix race conditions

---

## Debugging Failed Tests

### Common Failure Patterns

**Issue**: Import errors

```bash
# Solution: Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

**Issue**: Async test failures

```bash
# Solution: Ensure pytest-asyncio is installed
pip install pytest-asyncio
```

**Issue**: Mock not called

```python
# Add debugging
print(f"Mock called: {mock.called}")
print(f"Call count: {mock.call_count}")
print(f"Call args: {mock.call_args}")
```

### Verbose Output

```bash
# Show print statements
pytest -v -s

# Show full traceback
pytest -v --tb=long

# Stop on first failure
pytest -v -x
```

---

## Related Documentation

- [Architecture Overview](./LLM_CONFIGURATION_SYSTEM.md)
- [API Documentation](./API_DOCUMENTATION.md)
- [Development Guide](../Guides/DEVELOPMENT_GUIDE.md)
- [Performance Tests README](../../coaching/tests/performance/README.md)
