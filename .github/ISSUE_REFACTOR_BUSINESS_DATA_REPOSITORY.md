# Refactor Business Data Repository - Remove Duplicate Logic

## 🎯 Overview

The current `business_data_repository.py` contains placeholder methods that duplicate .NET application responsibilities. Business data (vision, purpose, values, niche, ICA, goals, metrics) is stored and managed by the .NET application. The pp_ai service should only READ this data via HTTP APIs, not store or manage it.

## ❌ Problem

**File:** `coaching/src/repositories/business_data_repository.py`

**Current Implementation:**
```python
async def get_business_metrics(self, tenant_id: str) -> MetricsResponse:
    # Placeholder implementation - return structured metrics
    return MetricsResponse(
        metric_type="business_overview",
        time_period="current",
        data_points=[],
        summary={"total_goals": "0", "active_projects": "0", "completion_rate": "0.0"},
        generated_at=datetime.now(UTC),
    )

async def get_business_data(self, tenant_id: str) -> BusinessData | None:
    # Placeholder implementation - would query DynamoDB
    return None

async def update_business_data(self, business_data: BusinessData) -> BusinessData:
    # Placeholder implementation - would update DynamoDB
    return business_data
```

**Issues:**
1. ❌ Suggests pp_ai stores business data (violates architecture)
2. ❌ Returns mock/empty data
3. ❌ Duplicates .NET responsibility
4. ❌ Could confuse future developers about data ownership

## ✅ Solution

### Option 1: Delete the File (Recommended)

**Rationale:**
- Business data is accessed via `BusinessApiClient` (already exists)
- No need for repository abstraction over HTTP client
- Simpler architecture

**Actions:**
1. Delete `coaching/src/repositories/business_data_repository.py`
2. Update imports in services to use `BusinessApiClient` directly
3. Remove from dependency injection

**Services to Update:**
```python
# Before
class InsightsService:
    def __init__(
        self, 
        conversation_repo: ConversationRepository,
        business_data_repo: BusinessDataRepository  # REMOVE
    ):
        self.business_data_repo = business_data_repo

# After
class InsightsService:
    def __init__(
        self, 
        conversation_repo: ConversationRepository,
        business_api_client: BusinessApiClient  # USE THIS
    ):
        self.business_api_client = business_api_client
```

### Option 2: Refactor to Aggregator (If Complex Logic Needed)

**If future needs require aggregating data from multiple .NET endpoints:**

Rename and refactor:
```python
# coaching/src/services/business_data_aggregator.py

class BusinessDataAggregator:
    """
    Aggregates business data from multiple .NET API endpoints.
    
    Note: This service does NOT store data. It only reads from .NET APIs
    and aggregates/transforms for coaching service consumption.
    """
    
    def __init__(self, business_api_client: BusinessApiClient):
        self.api_client = business_api_client
    
    async def get_complete_business_context(self, tenant_id: str) -> Dict[str, Any]:
        """Fetch and aggregate business context from multiple endpoints."""
        
        # Parallel API calls
        foundation, goals, stats, performance = await asyncio.gather(
            self.api_client.get_organizational_context(tenant_id),
            self._fetch_goals(tenant_id),
            self._fetch_goal_stats(tenant_id),
            self._fetch_performance_score(tenant_id)
        )
        
        # Aggregate and return
        return {
            "foundation": foundation,
            "goals": goals,
            "stats": stats,
            "performance": performance
        }
    
    async def _fetch_goals(self, tenant_id: str) -> List[Dict]:
        """Fetch goals from Traction Service."""
        # Call .NET API: GET /goals
        ...
    
    async def _fetch_goal_stats(self, tenant_id: str) -> Dict:
        """Fetch goal statistics from Traction Service."""
        # Call .NET API: GET /goals/stats
        ...
```

## 📁 Files to Modify/Delete

### Delete (Option 1 - Recommended)
1. `coaching/src/repositories/business_data_repository.py`

### Modify
2. `coaching/src/services/insights_service.py`
   - Remove `BusinessDataRepository` dependency
   - Add `BusinessApiClient` dependency
   
3. `coaching/src/api/dependencies.py`
   - Remove `get_business_data_repository()` if exists
   
4. Any other services using `BusinessDataRepository`
   - Search codebase for imports

### Create (Option 2 - Only if needed)
5. `coaching/src/services/business_data_aggregator.py`
   - New aggregator service

## 🔧 Implementation Steps

### Step 1: Find All Usages

```bash
# Search for imports
grep -r "BusinessDataRepository" coaching/src/

# Search for instantiation
grep -r "business_data_repo" coaching/src/
```

### Step 2: Update Service Dependencies

```python
# Example: Update insights_service.py

# OLD
from coaching.src.repositories.business_data_repository import BusinessDataRepository

class InsightsService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        business_data_repo: BusinessDataRepository
    ):
        self.conversation_repo = conversation_repo
        self.business_data_repo = business_data_repo

# NEW
from coaching.src.infrastructure.external.business_api_client import BusinessApiClient

class InsightsService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        business_api_client: BusinessApiClient
    ):
        self.conversation_repo = conversation_repo
        self.business_api_client = business_api_client
```

### Step 3: Update Method Calls

```python
# OLD
metrics = await self.business_data_repo.get_business_metrics(tenant_id)

# NEW
# Option A: Call specific endpoint
foundation = await self.business_api_client.get_organizational_context(tenant_id)

# Option B: Call Traction Service directly
stats = await self.business_api_client.call_endpoint(
    method="GET",
    endpoint="/goals/stats",
    tenant_id=tenant_id
)
```

### Step 4: Update Dependency Injection

```python
# coaching/src/api/dependencies.py

# REMOVE (if exists)
def get_business_data_repository() -> BusinessDataRepository:
    dynamodb = get_dynamodb_resource()
    return BusinessDataRepository(dynamodb, "business-data-table")

# KEEP (already exists)
def get_business_api_client() -> BusinessApiClient:
    base_url = os.getenv("BUSINESS_API_BASE_URL")
    jwt_token = get_service_token()
    return BusinessApiClient(base_url=base_url, jwt_token=jwt_token)
```

### Step 5: Delete Repository File

```bash
rm coaching/src/repositories/business_data_repository.py
```

### Step 6: Update Tests

```python
# tests/unit/test_insights_service.py

# OLD
def test_insights_with_business_data(mocker):
    mock_repo = mocker.Mock(spec=BusinessDataRepository)
    mock_repo.get_business_metrics.return_value = {...}

# NEW
def test_insights_with_business_data(mocker):
    mock_client = mocker.Mock(spec=BusinessApiClient)
    mock_client.get_organizational_context.return_value = {...}
```

## ✅ Acceptance Criteria

### Code Changes
- [ ] `business_data_repository.py` deleted OR refactored to aggregator
- [ ] All services updated to use `BusinessApiClient`
- [ ] Dependency injection updated
- [ ] No references to `BusinessDataRepository` in codebase
- [ ] All tests updated and passing

### Documentation
- [ ] Architecture doc clarifies: .NET owns business data, pp_ai reads only
- [ ] Comments added explaining data flow
- [ ] README updated if architecture diagrams present

### Testing
- [ ] All existing tests pass
- [ ] Services correctly call .NET APIs
- [ ] No mock data returned from pp_ai

## 🧪 Testing Requirements

### Unit Tests
```python
# tests/unit/test_insights_service.py

async def test_insights_calls_business_api_client(mocker):
    """Verify InsightsService uses BusinessApiClient, not repository."""
    mock_client = mocker.Mock(spec=BusinessApiClient)
    mock_client.get_organizational_context.return_value = {
        "vision": "Test Vision",
        "purpose": "Test Purpose"
    }
    
    service = InsightsService(
        conversation_repo=mocker.Mock(),
        business_api_client=mock_client
    )
    
    await service._fetch_business_context("tenant-123")
    
    mock_client.get_organizational_context.assert_called_once_with("tenant-123")
```

### Integration Tests
```python
# tests/integration/test_business_data_integration.py

async def test_no_business_data_stored_in_pp_ai():
    """Verify pp_ai doesn't store business data in DynamoDB."""
    # Verify no business data tables exist
    # Verify BusinessApiClient is used for all business data access
```

## 📊 Affected Services

Grep results will identify all affected services. Likely candidates:

1. `InsightsService` - Uses business metrics
2. `OnboardingService` - May reference business data
3. `ConversationService` - May use business context
4. `WorkflowOrchestrator` - May inject business data into prompts

## 🔗 Dependencies

- ✅ `BusinessApiClient` (already exists)
- ✅ .NET API endpoints (already available)
- ⚠️ Update service constructors
- ⚠️ Update dependency injection

## 📈 Estimated Effort

- **Find all usages:** 0.5 hours
- **Update services:** 1-2 hours
- **Update dependency injection:** 0.5 hours
- **Update tests:** 1 hour
- **Testing & verification:** 0.5-1 hour
- **Total:** 3-5 hours

## 🚨 Breaking Changes

**None expected** - This is internal refactoring. External APIs unchanged.

## 📚 References

- Architecture decision: .NET owns business data
- `BusinessApiClient`: `coaching/src/infrastructure/external/business_api_client.py`
- .NET API specs: `docs/Specifications/backend-integration-*.md`

## 💡 Notes

**Why this matters:**
- Clear separation of concerns
- Prevents data duplication
- Avoids sync issues between pp_ai and .NET
- Simplifies architecture
- Makes data ownership explicit

**Future consideration:**
If complex aggregation logic is needed, create `BusinessDataAggregator` service that reads from multiple .NET endpoints but doesn't store data.

## 👥 Assignee

- Backend Developer

## 🏷️ Labels

`refactor`, `architecture`, `tech-debt`, `high-priority`, `backend`

---

**Created:** 2025-10-21  
**Status:** Ready for Implementation  
**Priority:** HIGH  
**Type:** Refactoring / Technical Debt
