# PurposePath API: Implementation Execution Plan

## 🎯 Executive Summary

This document provides the specific execution steps to transform the PurposePath API from its current state (~7,000 Pylance errors) to a fully type-safe, clean architecture foundation.

## 📋 Pre-Execution Checklist

### 1. GitHub Project Setup

```bash
# Run the GitHub project setup script
python setup_github_project.py
```

**Expected Outcomes:**

- [ ] GitHub issues created for each phase
- [ ] Labels and milestones established
- [ ] Existing typing issues closed/consolidated
- [ ] Development toolchain configured

### 2. Development Environment Validation

```bash
# Ensure tools are properly installed
pip install -r requirements-dev.txt
pre-commit install --install-hooks
code --install-extension ms-python.pylance
```

**Validation Commands:**

```bash
# Test Pylance validation script
python pylance_validation.py account
python pylance_validation.py coaching  
python pylance_validation.py traction

# Verify pre-commit hooks
pre-commit run --all-files
```

### 3. Baseline Metrics Collection

```bash
# Capture current state
python pylance_validation.py all > baseline_errors.txt
git add -A && git commit -m "Baseline before typing cleanup"
git push origin dev
```

## 🚀 Phase-by-Phase Execution

### Phase 1: Foundation Setup (Day 1 - 4 hours)

#### 1.1 Shared Type Definitions (90 minutes)

**GitHub Issue:** "🏗️ Create shared type definitions and common patterns"

**Steps:**

```bash
# Create directory structure
mkdir -p shared/types
touch shared/types/__init__.py
```

**Create `shared/types/common.py`:**

```python
from typing import TypeAlias, Literal, TypedDict, NotRequired
from datetime import datetime

# Domain identifiers
UserId: TypeAlias = str
TenantId: TypeAlias = str
ConversationId: TypeAlias = str
MessageId: TypeAlias = str

# API patterns
class ApiSuccessResponse[T](TypedDict):
    data: T
    success: Literal[True]
    message: NotRequired[str]

class ApiErrorResponse(TypedDict):
    error: str
    success: Literal[False]
    details: NotRequired[dict[str, str]]

# Pagination
class PaginationParams(TypedDict):
    page: int
    size: int

class PaginatedResults[T](TypedDict):
    items: list[T]
    total: int
    page: int
    size: int
```

**Create `shared/types/aws.py`:**

```python
from typing import TypedDict, NotRequired, Any
from mypy_boto3_dynamodb.type_defs import (
    QueryOutputTypeDef,
    ScanOutputTypeDef,
    GetItemOutputTypeDef
)

# DynamoDB patterns
class DynamoDBKey(TypedDict):
    PK: str
    SK: str

class DynamoDBItem(TypedDict, total=False):
    PK: str
    SK: str
    type: str
    created_at: str
    updated_at: NotRequired[str]

# Re-export boto3 types for convenience
__all__ = [
    "DynamoDBKey",
    "DynamoDBItem", 
    "QueryOutputTypeDef",
    "ScanOutputTypeDef",
    "GetItemOutputTypeDef"
]
```

**Create `shared/types/external.py`:**

```python
from typing import TypedDict, NotRequired, Literal

# Stripe API responses
class StripeCustomer(TypedDict):
    id: str
    email: str
    name: str | None
    created: int
    metadata: dict[str, str]

class StripeSubscription(TypedDict):
    id: str
    customer: str
    status: Literal["active", "canceled", "incomplete", "past_due"]
    current_period_start: int
    current_period_end: int

# JWT payload structure
class JWTPayload(TypedDict, total=False):
    sub: str  # user_id
    iss: str  # issuer
    tenant_id: str
    role: str
    permissions: list[str]
    subscription_tier: str
    exp: int
    iat: int

# Bedrock/LLM responses
class BedrockResponse(TypedDict):
    output: dict[str, str]
    usage: dict[Literal["input_tokens", "output_tokens"], int]
    stop_reason: Literal["end_turn", "tool_use", "max_tokens"]
```

**Validation:**

```bash
python -c "from shared.types.common import UserId; print('✅ Common types work')"
python pylance_validation.py shared
```

#### 1.2 Shared Infrastructure Fix (150 minutes)

**GitHub Issue:** "🔧 Fix shared infrastructure data access layer"

**Priority Files:**

1. `shared/services/data_access.py` - Most critical
2. `shared/services/aws_helpers.py` - AWS integration
3. `shared/models/multitenant.py` - Core models

**Execution Pattern:**

```python
# Example fix for data_access.py
from shared.types.aws import DynamoDBKey, QueryOutputTypeDef
from typing import cast

async def query_items(
    table_name: str,
    key_condition: str,
    **kwargs: Any
) -> list[dict[str, Any]]:
    """Query DynamoDB items with proper typing."""
    response: QueryOutputTypeDef = dynamodb_table.query(
        KeyConditionExpression=key_condition,
        **kwargs
    )
    return cast(list[dict[str, Any]], response.get("Items", []))
```

**Validation After Each File:**

```bash
python -c "from shared.services.data_access import DataAccessLayer; print('✅ Data access imports')"
python pylance_validation.py shared
```

### Phase 2: Core Services (Day 1-2 - 12 hours)

#### 2.1 Account Service Authentication (3 hours)

**GitHub Issue:** "🔐 Fix Account service authentication typing"

**Critical Files:**

- `account/src/api/auth.py` (line 87 - JWT payload)
- `account/src/services/auth_service.py`

**Implementation:**

```python
# Fix in account/src/api/auth.py
from shared.types.external import JWTPayload
from typing import cast

def _try_decode(secret: str) -> JWTPayload:
    return cast(JWTPayload, jwt.decode(
        token,
        secret,
        algorithms=[settings.jwt_algorithm],
        options={"verify_aud": False, "verify_iss": False},
    ))
```

**Validation:**

```bash
cd account && python -m pytest tests/test_auth.py -v
python pylance_validation.py account | grep "src/api/auth.py"
```

#### 2.2 Account Service Billing (3 hours)

**GitHub Issue:** "💳 Fix Account service Stripe billing integration"

**Critical Lines:**

- `account/src/services/billing_service.py:186` - Customer creation
- `account/src/services/billing_service.py:224` - Subscription listing

**Implementation:**

```python
# Replace explicit Any with proper type handling
from shared.types.external import StripeCustomer

def create_stripe_customer(email: str, name: str) -> str:
    """Create Stripe customer and return ID."""
    customer = stripe.Customer.create(  # type: ignore[misc]
        email=email,
        name=name,
    )
    # Stripe customer ID is always string per API docs
    return cast(str, customer.id)
```

#### 2.3 Coaching Service LLM (3 hours)

**GitHub Issue:** "🤖 Fix Coaching service LLM provider typing"

**Critical Files:**

- `coaching/src/llm/providers/base.py:75,78`
- `coaching/src/llm/orchestrator.py:42,287,288`

#### 2.4 Coaching Service Data (3 hours)

**GitHub Issue:** "💬 Fix Coaching service data access layer"

**Critical File:**

- `coaching/shared/services/data_access.py` (lines 86,160,291,329,334,339,399,417,517,521,524)

### Phase 3: Systematic Patterns (Day 3 Morning - 4 hours)

#### 3.1 Explicit Any Elimination (2 hours)

**GitHub Issue:** "🎯 Eliminate explicit Any annotations systematically"

**Strategy:**

1. Find all explicit `Any` usage: `grep -r "Any" --include="*.py" src/`
2. Categorize and replace systematically
3. Add justified `# type: ignore` for unavoidable cases

#### 3.2 FastAPI Decorator Typing (2 hours)

**GitHub Issue:** "🚀 Fix FastAPI decorator and route handler typing"

**Pattern:**

```python
from typing import Annotated
from fastapi import Depends

@router.post("/endpoint", response_model=ResponseModel)
async def endpoint(
    request: RequestModel,
    service: Annotated[ServiceClass, Depends(get_service)]
) -> ResponseModel:
    return await service.process(request)
```

### Phase 4: Testing & Validation (Day 3 Afternoon - 4 hours)

#### 4.1 Test Code Typing (2 hours)

**GitHub Issue:** "🧪 Fix test code typing and validation"

#### 4.2 Final Validation (2 hours)

**GitHub Issue:** "✅ Final validation and documentation"

**Validation Commands:**

```bash
# Zero error validation
python pylance_validation.py all
echo "Expected: 0 errors found"

# Full test suite
python -m pytest --cov=src --cov-fail-under=80

# CI/CD simulation
pre-commit run --all-files
```

## 📊 Progress Tracking

### Daily Checkpoints

**End of Day 1:**

```bash
python pylance_validation.py all > day1_progress.txt
echo "Target: <2000 errors remaining (>70% reduction)"
```

**End of Day 2:**

```bash
python pylance_validation.py all > day2_progress.txt  
echo "Target: <500 errors remaining (>90% reduction)"
```

**End of Day 3:**

```bash
python pylance_validation.py all > day3_final.txt
echo "Target: 0 errors (100% completion)"
```

### GitHub Issue Updates

After completing each issue:

1. Update GitHub issue with completion comment
2. Close issue with completion summary
3. Reference any learnings or patterns established

## 🎯 Success Criteria

### Quantitative Metrics

- [ ] **Zero Pylance errors** across all services  
- [ ] **100% function signature typing** (no untyped defs)
- [ ] **>90% test coverage** maintained
- [ ] **<5% performance regression** acceptable
- [ ] **All CI/CD checks passing** with strict settings

### Qualitative Validation

- [ ] VS Code shows no red squiggles in any Python file
- [ ] Autocomplete works perfectly for all business logic
- [ ] Refactoring tools work reliably
- [ ] New developer onboarding improved
- [ ] Code serves as self-documentation

## 🚧 Risk Mitigation

### Common Issues & Solutions

**"Too many errors, overwhelming"**

- Work file-by-file, validate frequently
- Use `# type: ignore` temporarily to make progress
- Focus on critical business logic first

**"Third-party libraries breaking"**

- Use strategic `# type: ignore[import]`
- Check for updated stub packages
- Create local stub files if needed

**"Performance regression"**

- Type checking is compile-time only
- If performance issues arise, profile and optimize
- Typing should not affect runtime performance

**"Team resistance to strictness"**

- Emphasize improved developer experience
- Show concrete examples of better IDE support
- Document time savings in debugging

## 🎉 Completion Celebration

When Pylance validation returns "0 errors":

1. **Create completion PR** with before/after metrics
2. **Update documentation** with new development standards  
3. **Team demo** showing improved IDE experience
4. **Establish monitoring** to prevent regression
5. **Plan celebration** - this is a significant engineering achievement!

---

**Document Version:** 1.0  
**Execution Start Date:** [TBD]  
**Target Completion:** 3 business days  
**Success Metric:** Zero Pylance errors across entire codebase
