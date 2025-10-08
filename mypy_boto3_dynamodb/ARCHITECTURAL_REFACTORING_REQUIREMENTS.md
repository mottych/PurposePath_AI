# 🏗️ PurposePath API: Complete Architectural Refactoring Requirements

## 🎯 OVERARCHING GOAL: COMPLETE TYPE SAFETY THROUGH PYDANTIC MODELS

**THIS IS NOT A TYPE ANNOTATION PROJECT - THIS IS A COMPLETE ARCHITECTURAL REFACTORING**

### Core Principle
**Replace ALL `dict[str, Any]` usage with proper Pydantic models across the ENTIRE codebase.**

## ❌ What We're Eliminating

### Bad Patterns (Current State)
```python
# ❌ ELIMINATE: Raw dictionary usage
@router.post("/issues", response_model=ApiResponse[dict[str, Any]])
async def create_issue(body: dict[str, Any]) -> ApiResponse[dict[str, Any]]:
    return {"success": True, "data": {...}}

# ❌ ELIMINATE: Repository methods with dictionaries  
def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
    item = self._convert_to_dynamo(session_data)
    
# ❌ ELIMINATE: Business logic with Any
def process_coaching_data(data: Any) -> Any:
```

## ✅ What We're Creating

### Good Patterns (Target State)
```python
# ✅ CREATE: Proper Pydantic request/response models
@router.post("/issues", response_model=ApiResponse[IssueResponse])
async def create_issue(request: CreateIssueRequest) -> ApiResponse[IssueResponse]:
    issue = Issue.create(request)
    return ApiResponse(data=issue)

# ✅ CREATE: Repository methods with domain models
def create_session(self, session: CoachingSession) -> CoachingSession:
    item = session.model_dump()
    
# ✅ CREATE: Business logic with typed objects
def process_coaching_data(session: CoachingSession) -> CoachingOutcome:
```

---

## 🏗️ Phase-by-Phase Requirements

## Phase 1: Create Complete Pydantic Model Architecture

### 🚨 REMINDER: ARCHITECTURAL REFACTORING GOAL
**Replace ALL dict[str, Any] usage with proper Pydantic models across the ENTIRE codebase.**

### Requirements
1. **Create Request Models**: Every API endpoint MUST have a proper Pydantic request model
2. **Create Response Models**: Every API endpoint MUST have a proper Pydantic response model  
3. **Create Domain Models**: All business entities MUST be Pydantic models (not TypedDicts)
4. **Update Shared Types**: Convert TypedDict definitions to proper Pydantic models where appropriate

### Files to Create/Update
- `shared/models/requests.py` - All API request models
- `shared/models/responses.py` - All API response models  
- `shared/models/domain.py` - Core business domain models
- `coaching/src/models/` - Coaching-specific models
- `traction/src/models/` - Traction-specific models
- `account/src/models/` - Account-specific models

### Acceptance Criteria
- [ ] Every API endpoint has proper Pydantic request model
- [ ] Every API endpoint has proper Pydantic response model
- [ ] All business entities are Pydantic models (CoachingSession, User, Goal, etc.)
- [ ] Zero usage of `dict[str, Any]` in model definitions
- [ ] Models include proper validation, field descriptions, and examples

---

## Phase 2: Refactor ALL Repository Layer to Pydantic Models

### 🚨 REMINDER: ARCHITECTURAL REFACTORING GOAL  
**Replace ALL dict[str, Any] usage with proper Pydantic models across the ENTIRE codebase.**

### Requirements
1. **Convert Repository Methods**: All repository methods MUST use Pydantic models as parameters and return types
2. **Update Base Repository**: `BaseRepository[T]` must work with Pydantic models, not dictionaries
3. **Fix DynamoDB Serialization**: Use `model_dump()` and `model_validate()` for DynamoDB operations
4. **Remove Dictionary Conversions**: Eliminate all manual dictionary manipulation

### Files to Refactor
- `shared/services/data_access.py` - Complete refactor to Pydantic models
- `coaching/src/repositories/` - All coaching repositories
- `traction/src/repositories/` - All traction repositories  
- `account/src/repositories/` - All account repositories

### Acceptance Criteria
- [ ] ALL repository methods use Pydantic models (input and output)
- [ ] Zero `Dict[str, Any]` usage in repository layer
- [ ] DynamoDB operations use `model_dump()` and `model_validate()`
- [ ] Repository tests updated to use Pydantic models
- [ ] Type annotations are 100% accurate

---

## Phase 3: Convert ALL API Routes to Pydantic Models

### 🚨 REMINDER: ARCHITECTURAL REFACTORING GOAL
**Replace ALL dict[str, Any] usage with proper Pydantic models across the ENTIRE codebase.**

### Requirements  
1. **Update Route Signatures**: Every route handler MUST use Pydantic request/response models
2. **Fix FastAPI Decorators**: All `@router.post|get|put|delete` decorators must specify proper response models
3. **Update Route Logic**: Route implementation must work with Pydantic objects, not dictionaries
4. **Remove Manual Serialization**: Let Pydantic handle all serialization/deserialization

### Files to Refactor
- `coaching/src/api/routes/` - ALL coaching routes
- `traction/src/api/routes/` - ALL traction routes  
- `account/src/api/routes/` - ALL account routes
- ALL dependency injection functions

### Acceptance Criteria
- [ ] ALL route handlers use Pydantic request models (no `dict[str, Any]`)
- [ ] ALL route handlers use Pydantic response models  
- [ ] Zero manual dictionary manipulation in routes
- [ ] FastAPI automatic validation works correctly
- [ ] OpenAPI documentation is properly generated

---

## Phase 4: Eliminate ALL Any Usage & Complete Type Safety

### 🚨 REMINDER: ARCHITECTURAL REFACTORING GOAL
**Replace ALL dict[str, Any] usage with proper Pydantic models across the ENTIRE codebase.**

### Requirements
1. **Eliminate Explicit Any**: Replace ALL `Any` usage with proper types
2. **Fix Business Logic**: Update all service layer code to work with Pydantic models
3. **Update External Integrations**: Type all AWS, Stripe, and other external API interactions
4. **Complete Validation**: Achieve 0 Pylance errors across entire codebase

### Acceptance Criteria  
- [ ] Zero explicit `Any` usage anywhere in codebase (except unavoidable external library boundaries)
- [ ] ALL business logic works with Pydantic models
- [ ] ALL external API integrations properly typed
- [ ] 0 Pylance errors across entire codebase
- [ ] All tests pass with strict type checking
- [ ] CI/CD enforces type safety

---

## 🎯 Success Metrics

### Quantitative Measures
- **0 Pylance errors** across entire codebase
- **0 explicit Any usage** (except justified external boundaries)  
- **0 dict[str, Any] usage** in application code
- **100% Pydantic model coverage** for all API endpoints

### Qualitative Measures  
- IDE provides full autocomplete and type checking
- New developers can understand data flow through type signatures
- Refactoring is safe due to compile-time type checking
- Business logic is self-documenting through Pydantic models

---

## 🚨 CRITICAL REMINDERS

### For Every Issue/Task
**THIS IS ARCHITECTURAL REFACTORING, NOT TYPE ANNOTATION FIXES**

### For Every Code Change
1. Ask: "Does this eliminate dict[str, Any] usage?"
2. Ask: "Does this use proper Pydantic models?"  
3. Ask: "Is this fully type-safe?"
4. Ask: "Does this move us toward the architectural goal?"

### Success Definition
**The project is successful when every single piece of data flowing through the system is represented by proper Pydantic models with complete type safety.**