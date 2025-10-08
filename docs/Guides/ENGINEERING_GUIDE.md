# PurposePath API Engineering Guide

This guide provides decision rules, best practices, and contribution guidelines for the PurposePath API development team.

## 🎯 Core Development Philosophy

**Quality First**: Always prioritize code quality over speed. Ask "What is the right way to do this?" and "What would an expert do?"

**No Shortcuts**: Never create workarounds, temporary fixes, mask errors, or leave TODO comments. Complete the work properly the first time.

**Expert Standards**: Research best practices, official documentation, and community recommendations before implementing solutions.

---

## 🏗️ Architecture Decisions

### API Design Principles

1. **Consistency Over Convenience**
   - Use consistent naming conventions across all services
   - Standardize response formats with ApiResponse envelope
   - Prefer snake_case for API fields, camelCase for frontend

2. **Objects Over Dictionaries**
   - Use Pydantic models for data validation and structure
   - Repository methods should return typed objects, not raw dictionaries
   - Leverage type hints for better IDE support and error detection

3. **Fail Fast and Clearly**
   - Validate inputs at API boundaries
   - Use specific error codes and messages
   - Log errors with sufficient context for debugging

### Multi-Tenant Architecture

```python
# ✅ Good: Always use RequestContext for tenant isolation
@router.get("/users")
async def get_users(context: RequestContext = Depends(get_current_context)):
    user_repo = UserRepository(context)
    return user_repo.list()

# ❌ Bad: Direct database access without tenant context
@router.get("/users")  
async def get_users():
    return dynamodb.scan(TableName="users")
```

### Authentication & Authorization

```python
# ✅ Good: Use dependency injection for auth
@router.get("/profile")
async def get_profile(current_user: UserProfile = Depends(get_current_user)):
    return current_user

# ✅ Good: Check permissions explicitly when needed
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    context: RequestContext = Depends(get_current_context)
):
    if not context.has_permission(Permission.MANAGE_USERS):
        raise HTTPException(403, "Insufficient permissions")
```

---

## 🔧 Code Standards

### Repository Pattern

```python
# ✅ Good: Return typed objects
class UserRepository:
    def get(self, user_id: str) -> Optional[UserProfile]:
        raw_data = self._fetch_from_db(user_id)
        return UserProfile(**raw_data) if raw_data else None

# ❌ Bad: Return raw dictionaries
class UserRepository:
    def get(self, user_id: str) -> dict[str, Any] | None:
        return self._fetch_from_db(user_id)
```

### Error Handling

```python
# ✅ Good: Use specific error types and codes
from shared.models.schemas import ErrorCode

def validate_email(email: str):
    if not email or "@" not in email:
        raise HTTPException(
            status_code=422,
            detail="Invalid email format", 
            headers={"X-Error-Code": ErrorCode.VALIDATION_ERROR}
        )

# ❌ Bad: Generic error handling
def validate_email(email: str):
    if not email:
        raise Exception("Bad email")
```

### Type Annotations

```python
# ✅ Good: Complete type annotations
from typing import List, Optional, Dict, Any

def process_users(users: List[UserProfile]) -> Dict[str, Any]:
    return {"count": len(users), "active": sum(1 for u in users if u.status == "active")}

# ❌ Bad: Missing type hints
def process_users(users):
    return {"count": len(users), "active": sum(1 for u in users if u.status == "active")}
```

---

## 🧪 Testing Standards

### Test Structure

```python
# ✅ Good: Descriptive test names and clear structure
def test_user_creation_with_valid_data_creates_user_successfully():
    # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}
    
    # Act  
    result = create_user(user_data)
    
    # Assert
    assert result.success is True
    assert result.data.email == "test@example.com"

# ❌ Bad: Unclear test names and structure  
def test_user():
    data = {"email": "test@example.com"}
    result = create_user(data)
    assert result
```

### Mocking Guidelines

```python
# ✅ Good: Mock at service boundaries
@patch("account.src.repositories.UserRepository.get")
def test_get_user_profile(mock_get):
    mock_get.return_value = UserProfile(user_id="123", email="test@example.com")
    
    result = get_user_profile("123")
    
    assert result.user_id == "123"

# ❌ Bad: Mock internal implementation details
@patch("boto3.resource")
def test_get_user_profile(mock_boto):
    # This creates tight coupling to implementation
```

---

## 📦 Service Integration

### Inter-Service Communication

1. **Use Shared Models**
   - Define common models in `shared/` directory
   - Import shared models rather than duplicating
   - Version shared interfaces properly

2. **Dependency Management**
   - Each service manages its own dependencies
   - Use dependency injection for external services
   - Fail gracefully when dependencies are unavailable

```python
# ✅ Good: Graceful degradation
class UserService:
    def __init__(self, coaching_service: Optional[CoachingService] = None):
        self.coaching_service = coaching_service
    
    def get_user_with_stats(self, user_id: str) -> UserProfile:
        user = self.get_user(user_id)
        
        # Gracefully handle missing coaching service
        if self.coaching_service:
            try:
                user.stats = self.coaching_service.get_stats(user_id)
            except Exception as e:
                logger.warning(f"Failed to get coaching stats: {e}")
                user.stats = {}
        
        return user
```

---

## 🚀 Deployment & Operations

### Configuration Management

```python
# ✅ Good: Use Pydantic settings with validation
class Settings(BaseSettings):
    database_url: str = Field(..., description="Database connection URL")
    jwt_secret: str = Field(..., description="JWT signing secret")
    log_level: str = Field("INFO", description="Logging level")
    
    class Config:
        env_prefix = "PURPOSEPATH_"

# ❌ Bad: Direct environment variable access
import os
DATABASE_URL = os.environ["DATABASE_URL"]  # Might not exist
```

### Logging Standards

```python
# ✅ Good: Structured logging with context
logger.info(
    "User login successful",
    user_id=user.user_id,
    tenant_id=user.tenant_id,
    email=user.email,
    ip_address=request.client.host
)

# ❌ Bad: Unstructured logging
logger.info(f"User {user.email} logged in")
```

---

## 🔒 Security Guidelines

### Input Validation

```python
# ✅ Good: Validate at API boundaries
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)

@router.post("/users")
async def create_user(request: CreateUserRequest):
    # Pydantic automatically validates the input
    return user_service.create(request)
```

### Authentication Patterns

```python
# ✅ Good: Use FastAPI dependency system
async def get_current_user(
    token: str = Depends(oauth2_scheme)
) -> UserProfile:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(401, "Invalid token")
        
        user = user_service.get(user_id)
        if not user:
            raise HTTPException(401, "User not found")
            
        return user
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

---

## 📋 Contribution Checklist

Before submitting a PR, ensure:

### Code Quality
- [ ] All functions have type hints
- [ ] No `TODO` comments in production code
- [ ] Error handling follows established patterns
- [ ] Logging includes appropriate context
- [ ] No hardcoded values (use configuration)

### Testing
- [ ] Unit tests cover new functionality
- [ ] Integration tests pass
- [ ] Edge cases are tested
- [ ] Mocking is done at appropriate boundaries

### Security
- [ ] Input validation is implemented
- [ ] Authentication/authorization is enforced
- [ ] No sensitive data in logs
- [ ] SQL injection protection (use parameterized queries)

### Documentation
- [ ] API endpoints have comprehensive docstrings
- [ ] Complex business logic is documented
- [ ] Configuration changes are documented
- [ ] Breaking changes are noted

### Performance
- [ ] Database queries are optimized
- [ ] N+1 query problems are avoided
- [ ] Appropriate caching is implemented
- [ ] Rate limiting is configured

---

## 🛠️ Tools and Standards

### Development Tools
- **Code Formatting**: Black (line length 100)
- **Linting**: Ruff with aggressive settings
- **Type Checking**: mypy in strict mode
- **Testing**: pytest with coverage reporting
- **Security**: bandit for security analysis

### Code Review Standards

1. **Functionality**: Does it work correctly?
2. **Security**: Are there security vulnerabilities?
3. **Performance**: Is it efficient enough?
4. **Maintainability**: Is it easy to understand and modify?
5. **Testing**: Is it properly tested?

### Git Workflow

```bash
# Feature branch naming
feature/user-authentication
bugfix/login-validation-error
hotfix/security-vulnerability

# Commit message format
feat(auth): add JWT token refresh functionality
fix(user): resolve email validation edge case
docs(api): update authentication endpoint documentation
```

---

## ❓ Decision Framework

When facing technical decisions, use this framework:

1. **Requirements**: Does it meet the functional requirements?
2. **Security**: Is it secure by default?
3. **Performance**: Will it scale appropriately?
4. **Maintainability**: Can the team maintain it long-term?
5. **Standards**: Does it follow established patterns?
6. **Testing**: Can it be thoroughly tested?

### Common Decision Points

**Should I use a dictionary or a Pydantic model?**
- Use Pydantic models for structured data with validation
- Use dictionaries only for truly dynamic key-value data

**Should I create a new service or extend existing?**
- Create new if it's a distinct business domain
- Extend existing if it's closely related functionality

**How should I handle errors?**
- Use specific exception types
- Include enough context for debugging
- Follow the established error response format

---

## 📞 Getting Help

**Architecture Questions**: Discussion in team meetings
**Code Review**: Pull request reviews
**Security Concerns**: Security team consultation
**Performance Issues**: Performance review with senior engineers

---

This guide evolves with the project. When you encounter new patterns or make architectural decisions, document them here for the team's benefit.