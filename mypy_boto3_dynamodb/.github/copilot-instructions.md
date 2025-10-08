# AI Code Assistant Instructions - PurposePath API

## 🎯 Core Development Philosophy

**Quality First**: Always prioritize code quality over speed. Ask "What is the right way to do this?" and "What would an expert do?"

**No Shortcuts**: Never create workarounds, temporary fixes, mask errors, or leave TODO comments. Complete the work properly the first time.

**Expert Standards**: Research best practices, official documentation, and community recommendations before implementing solutions.

---

## 🔄 Development Workflow (CRITICAL)

### Git Branching Strategy (MANDATORY)

**NEVER develop on main/master branches**. Always use feature branches:

```bash
# Start new feature
git checkout develop
git pull origin develop
git checkout -b feature/descriptive-name

# Work on feature
git add .
git commit -m "feat: descriptive commit message"
git push origin feature/descriptive-name

# When ready, create PR to develop branch
```

**Branch Hierarchy:**
```
master (production) ← staging ← develop ← feature/branches
```

### Virtual Environment (MANDATORY)

**ALWAYS use virtual environments** for Python development:

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
# or
uv sync  # if using uv
```

**Never work without an active virtual environment.**

### GitHub Issues Workflow (MANDATORY)

**Every change must be linked to a GitHub issue:**

1. **Create Issue**: Before starting any work
   - Use descriptive titles
   - Add proper labels (`enhancement`, `bug`, `refactor`)
   - Define acceptance criteria
   - Assign to yourself

2. **Update Progress**: Throughout development
   - Comment on issue with progress updates
   - Reference commits: "Working on X in commit abc123"
   - Document blockers or discoveries

3. **Link Commits**: Always reference issue in commits
   ```bash
   git commit -m "feat: implement user authentication #42"
   git commit -m "fix: resolve login validation bug - closes #42"
   ```

4. **Close Issue**: Only when ALL criteria met:
   - ✅ Code implemented and reviewed
   - ✅ Tests written and passing
   - ✅ Documentation updated
   - ✅ No lint/type errors

### Type Safety Requirements (MANDATORY)

**Use Pydantic models everywhere** - avoid `dict[str, Any]` except when absolutely necessary:

✅ **Correct:**
```python
class UserCreateRequest(BaseModel):
    name: str = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="Valid email address")

# Repository operations
def create_user(self, user_data: UserCreateRequest) -> UserResponse:
    # Use user_data.model_dump() for DynamoDB only when required
    return self.dynamodb.put_item(Item=user_data.model_dump())
```

❌ **Incorrect:**
```python
def create_user(self, user_data: dict[str, Any]) -> dict[str, Any]:
    return self.dynamodb.put_item(Item=user_data)
```

**Exception**: DynamoDB responses come as `dict` - transform immediately:
```python
response = dynamodb.get_item(Key={"id": user_id})
if "Item" in response:
    return UserResponse.model_validate(response["Item"])
```

---

## 🔍 Problem-Solving

### Root Cause Analysis (Critical for Widespread Issues)

When encountering multiple similar errors:

1. **Pattern Recognition**: Analyze if errors share a common root cause
2. **Isolated Testing**:
   - Fix ONE representative instance first
   - Verify the solution works without side effects
   - Document findings
3. **Root Cause Investigation**: Determine if solution addresses cause vs. symptoms
4. **Strategic Decision**: Choose between "fix once at source" vs "patch each instance"
5. **Systematic Application**: Apply chosen approach consistently

**Triggers**: Multiple similar errors, widespread typing/import issues, repeated patterns

### Test Strategyplatform.openai.com

**When fixing test code**: Assess if rewriting the test is easier than fixing it. Prioritize robust, maintainable tests over complex mocking.

---

## 💻 Code Quality Standards

### Architecture & Design

- **SOLID Principles**: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- **Design Patterns**: Repository, Factory, Dependency Injection where appropriate
- **Domain-Driven Design**: Clear separation of concerns between presentation, business logic, and data access
- **Modularity**: Break complex functions into smaller, reusable components

### Code Standards

- **Readability**: Meaningful names, clear abstractions, well-structured code
- **Documentation**: Clear comments for complex sections, self-documenting code
- **Framework Best Practices**: Follow idiomatic patterns for the technology stack
- **Consistency**: Adhere to existing project conventions unless compelling reasons exist to deviate

## 📁 Project Structure & Conventions

### File Organization Patterns

```
{module}/
├── src/
│   ├── api/routes/          # FastAPI endpoint handlers
│   ├── services/            # Business logic layer
│   ├── repositories/        # Data access layer (typed operations)
│   ├── models/
│   │   ├── requests.py      # API request models
│   │   ├── responses.py     # API response models
│   │   ├── schemas.py       # Domain/shared models
│   │   └── repository_models.py  # Data layer models
│   └── core/               # Configuration, exceptions
├── tests/                  # Test files mirroring src structure
└── pyproject.toml         # Dependencies and configuration
```

### Naming Conventions

- **Files**: snake_case (user_repository.py, auth_service.py)
- **Classes**: PascalCase (UserRepository, AuthService, SubscriptionData)
- **Methods/Functions**: snake_case (create_user, get_subscription, validate_token)
- **Constants**: UPPER_CASE (DEFAULT_TIMEOUT, MAX_RETRIES)
- **Pydantic Models**: Descriptive with purpose suffix (UserCreateRequest, SubscriptionUpdateData)

### Pydantic Model Patterns

- **Request Models**: Validate incoming API data with Field descriptions
- **Response Models**: Structure outgoing API responses with proper typing
- **Data Models**: Repository/service layer operations with model_dump() usage
- **Type Safety**: Always use proper Pydantic models instead of dict[str, Any]
- **Validation**: Include Field descriptions and constraints for all models

### Import Organization

```python
# Standard library
import uuid
from datetime import datetime
from typing import Any, Optional

# Third-party packages
from pydantic import BaseModel, Field
from fastapi import APIRouter

# Internal modules (absolute imports)
from shared.models.schemas import UserProfile
from account.src.models.responses import UserResponse
from account.src.services.auth_service import AuthService
```

### Repository Layer Standards

- Use proper Pydantic models for all create/update operations
- Transform dict[str, Any] to typed models wherever possible
- Maintain DynamoDB compatibility while adding type safety
- Follow established patterns from account/coaching modules

### Dependencies & Security

- **Latest Libraries**: Always use the latest possible libraries supported by the current Python version. Use tools to determine and update dependencies. Never use deprecated libraries
- **Virtual Environment**: Always use and activate a virtual environment for Python projects
- **Compatibility**: Ensure all dependencies work together
- **Security**: Handle edge cases gracefully, validate inputs, secure by default

---

## 🚨 Error Handling & Performance

### Error Management

- **Graceful Handling**: Meaningful error messages, appropriate HTTP status codes
- **Logging**: Sufficient context for debugging
- **Fast Failure**: Fail clearly and early when issues occur

### Performance

- **Algorithmic Efficiency**: Prefer O(1) or O(log n) over O(n) operations
- **Measured Optimization**: Profile before optimizing, but write efficient code from start
- **Caching**: Implement appropriate caching for expensive operations

---

## 🧪 Testing & Validation (MANDATORY)

### Test-First Development

**Every feature must include tests BEFORE issue closure:**

1. **Write Tests First**: Create test cases based on acceptance criteria
2. **Implement Feature**: Write code to make tests pass  
3. **Validate Coverage**: Ensure comprehensive test coverage
4. **Run Full Suite**: All tests must pass before PR

```bash
# Run tests frequently during development
pytest tests/ -v
pytest tests/test_specific_module.py -v

# Check coverage
pytest --cov=src tests/
```

### Test Requirements

- **Unit Tests**: Every function/method with business logic
- **Integration Tests**: API endpoints and database operations
- **Edge Cases**: Error conditions and boundary values
- **Test Quality**: Robust, maintainable tests over brittle mocks

### Definition of Done (CRITICAL)

An issue is **NEVER considered complete** unless ALL criteria are met:

- ✅ **GitHub Issue**: Created, tracked, and linked to commits
- ✅ **Code Completion**: All required functionality fully implemented
- ✅ **Type Safety**: Pydantic models used throughout (no dict[str, Any])
- ✅ **Test Coverage**: Comprehensive tests written and passing
- ✅ **Virtual Environment**: All work done in proper virtual environment
- ✅ **Zero Errors**: Absolutely no errors including:
  - All tests pass without failures
  - No lint issues or warnings (`ruff check`, `black --check`)
  - No syntax errors
  - No type checking errors (`mypy src/`)
  - No compilation errors
- ✅ **Documentation**: Updated for any public APIs or significant changes
- ✅ **Branch Strategy**: Work done in feature branch, PR to develop

### Validation Protocol

1. **Pre-Commit Checks**:
   ```bash
   # Format code
   black src/ tests/
   
   # Check linting
   ruff check src/ tests/
   
   # Type checking
   mypy src/
   
   # Run tests
   pytest tests/ -v
   ```

2. **Issue Update**: Comment on GitHub issue with validation results
3. **PR Creation**: Link to issue, include test results
4. **Issue Closure**: Only after PR merged and all criteria met

---

## 📁 Project Management & Maintenance (CRITICAL)

### GitHub Issues Integration (MANDATORY)

**All development work must be tracked via GitHub issues:**

1. **Issue Creation**:
   ```bash
   # Use gh CLI for consistent issue creation
   gh issue create --title "feat: implement user authentication" \
     --body "## Acceptance Criteria
     - [ ] Create UserAuth Pydantic models
     - [ ] Implement authentication service
     - [ ] Add comprehensive tests
     - [ ] Update API documentation" \
     --label "enhancement,high-priority" \
     --assignee @me
   ```

2. **Progress Updates**:
   - Comment on issues with development progress
   - Reference commits: `Working on authentication in commit abc123`
   - Document any blockers or architectural decisions

3. **Issue Status Management**:
   ```bash
   # Update issue status
   gh issue edit 42 --add-label "in-progress"
   gh issue comment 42 --body "✅ Pydantic models completed, starting service layer"
   ```

4. **Issue Closure**:
   ```bash
   # Only close when ALL criteria met
   gh issue close 42 --comment "✅ All acceptance criteria met:
   - ✅ Code implemented with Pydantic models
   - ✅ Tests passing (100% coverage)  
   - ✅ Type checking clean
   - ✅ Documentation updated"
   ```

### Commit Message Standards

```bash
# Always reference issue numbers
git commit -m "feat: add user authentication models - refs #42"
git commit -m "test: add authentication service tests - refs #42" 
git commit -m "fix: resolve login validation issue - closes #42"
```

### Code Quality Gates

**Before any commit:**
```bash
# Activate virtual environment
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1

# Format and check code
black src/ tests/
ruff check src/ tests/ --fix
mypy src/

# Run tests
pytest tests/ -v --cov=src
```

### Documentation Standards

- **Update README.md**: For any API changes or new features
- **API Documentation**: Keep OpenAPI/FastAPI docs current
- **Architecture Docs**: Update for any significant changes
- **Issue Documentation**: Link all related issues/PRs in commit messages

---

## 🤝 AI Assistant Behavior

### Collaboration Approach

- **Context Awareness**: Read full project context before making changes
- **Transparent Reasoning**: Explain architectural decisions and trade-offs
- **Alternative Solutions**: Suggest multiple approaches when appropriate
- **Clarification**: Ask questions when requirements are ambiguous

### Tool Usage Efficiency

- **Batch Operations**: Use `multi_replace_string_in_file` for multiple independent edits
- **Precise Context**: Include 3-5 lines before/after when using `replace_string_in_file`
- **Targeted Actions**: Choose the most appropriate tool for each task

---

## 📚 Reference Integration

**Additional Sources**: Automatically incorporate conventions from:

- `.github/copilot-instructions.md`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`
- `.cursorrules`, `.windsurfrules`, `.clinerules`
- `.cursor/rules/**`, `.windsurf/rules/**`, `.clinerules/**`
- `README.md`

---

_These instructions prioritize long-term maintainability, code quality, and systematic problem-solving to ensure sustainable development practices._
