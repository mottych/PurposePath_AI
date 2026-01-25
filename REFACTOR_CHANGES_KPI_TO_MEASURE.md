# KPI → Measure Refactoring - Complete Changes Summary

**Issue #196: Changing KPI to Measure - AI**
**Branch:** `feature/issue-196-kpi-to-measure`
**Date:** 2026-01-25

## Executive Summary

Systematically renamed all "KPI" references to "Measure" throughout the AI service codebase following DDD principles and ubiquitous language. No backward compatibility - all code, API contracts, and documentation updated.

---

## 🔴 BREAKING CHANGES - API Endpoints

### ❌ DELETED ENDPOINTS
The following endpoints were **completely removed** (replaced by execute-async pattern):

1. **DELETE** `/coaching/kpi-recommendations` 
   - Previously: `POST` endpoint that generated KPI recommendations
   - Status: **REMOVED** (not renamed)
   - Replacement: Use execute-async with `measure_recommendations` topic

### ✅ RENAMED ENDPOINTS (Dead Code - Not Used by Frontend)

2. `/analysis/kpi` → `/analysis/measure`
   - **Note:** This entire `analysis.py` routes file is marked as DEPRECATED dead code
   - Method: `POST`
   - Request Model: `KPIAnalysisRequest` → `MeasureAnalysisRequest`
   - Response Model: `KPIAnalysisResponse` → `MeasureAnalysisResponse`

---

## 📦 PAYLOAD CHANGES

### Request Models (shared/models/requests.py)

**Before:**
```python
class CreateKPIRequest(BaseRequestModel):
    name: str
    current_value: float
    target_value: float | None
    # ... KPI fields

class UpdateKPIRequest(BaseRequestModel):
    # ... KPI update fields

class LinkKPIRequest(BaseRequestModel):
    kpi_id: str
    threshold_pct: float | None
```

**After:**
```python
class CreateMeasureRequest(BaseRequestModel):
    name: str
    current_value: float
    target_value: float | None
    # ... Measure fields

class UpdateMeasureRequest(BaseRequestModel):
    # ... Measure update fields

class LinkMeasureRequest(BaseRequestModel):
    measure_id: str  # ⚠️ Field renamed
    threshold_pct: float | None
```

### Response Models (shared/models/responses.py)

**Before:**
```python
class KPIResponse(BaseResponseModel):
    id: str
    name: str
    current_value: float
    # ...

class KPIListResponse(BaseResponseModel):
    kpis: list[KPIResponse]
    total: int

class KPIReadingResponse(BaseResponseModel):
    # ...

class KPILinkResponse(BaseResponseModel):
    goal_id: str
    kpi_id: str
    # ...

class AlignmentDriversResponse(BaseResponseModel):
    kpi_performance: float  # alias="kpiPerformance"
```

**After:**
```python
class MeasureResponse(BaseResponseModel):
    id: str
    name: str
    current_value: float
    # ...

class MeasureListResponse(BaseResponseModel):
    measures: list[MeasureResponse]  # ⚠️ Field renamed
    total: int

class MeasureReadingResponse(BaseResponseModel):
    # ...

class MeasureLinkResponse(BaseResponseModel):
    goal_id: str
    measure_id: str  # ⚠️ Field renamed
    # ...

class AlignmentDriversResponse(BaseResponseModel):
    measure_performance: float  # ⚠️ alias="measurePerformance"
```

### Analysis API Models (coaching/src/api/models/analysis.py)

**Before:**
```python
class KPIAnalysisRequest(BaseModel):
    current_kpis: list[str]
    context: dict[str, Any]

class KPIRecommendation(BaseModel):
    kpi_name: str
    description: str
    rationale: str
    # ...

class KPIAnalysisResponse(BaseModel):
    kpi_effectiveness_score: float
    current_kpi_analysis: list[dict[str, Any]]
    missing_kpis: list[str]
    recommended_kpis: list[KPIRecommendation]
```

**After:**
```python
class MeasureAnalysisRequest(BaseModel):
    current_measures: list[str]  # ⚠️ Field renamed
    context: dict[str, Any]

class MeasureRecommendation(BaseModel):
    measure_name: str  # ⚠️ Field renamed
    description: str
    rationale: str
    # ...

class MeasureAnalysisResponse(BaseModel):
    measure_effectiveness_score: float  # ⚠️ Field renamed
    current_measure_analysis: list[dict[str, Any]]  # ⚠️ Field renamed
    missing_measures: list[str]  # ⚠️ Field renamed
    recommended_measures: list[MeasureRecommendation]  # ⚠️ Field renamed
```

### Strategic Planning Models (coaching/src/api/models/strategic_planning.py)

**Before:**
```python
class StrategySuggestion(StrategicPlanningBaseModel):
    # ...
    suggested_kpis: list[str] = Field(alias="suggestedKpis")

class KPIRecommendation(StrategicPlanningBaseModel):
    name: str
    kpi_type: str = Field(alias="type")
    # ...

class KPIRecommendationsData(StrategicPlanningBaseModel):
    recommendations: list[KPIRecommendation]

class KPIRecommendationsResponseV2(StrategicPlanningBaseModel):
    topic_id: str = "kpi_recommendations"
    data: KPIRecommendationsData
```

**After:**
```python
class StrategySuggestion(StrategicPlanningBaseModel):
    # ...
    suggested_measures: list[str] = Field(alias="suggestedMeasures")  # ⚠️ Renamed

class MeasureRecommendation(StrategicPlanningBaseModel):
    name: str
    measure_type: str = Field(alias="type")  # ⚠️ Internal field renamed
    # ...

class MeasureRecommendationsData(StrategicPlanningBaseModel):
    recommendations: list[MeasureRecommendation]  # ⚠️ Type changed

class MeasureRecommendationsResponseV2(StrategicPlanningBaseModel):
    topic_id: str = "measure_recommendations"  # ⚠️ Default changed
    data: MeasureRecommendationsData  # ⚠️ Type changed
```

### Business Context Models (coaching/src/models/business_context.py)

**Before:**
```python
class KpiContext(BaseModel):
    id: str
    name: str
    current_value: float | None
    target_value: float | None
    unit: str | None

class BusinessContext(BaseModel):
    # ...
    kpis: list[KpiContext]
```

**After:**
```python
class MeasureContext(BaseModel):
    id: str
    name: str
    current_value: float | None
    target_value: float | None
    unit: str | None

class BusinessContext(BaseModel):
    # ...
    measures: list[MeasureContext]  # ⚠️ Field renamed
```

---

## 🗂️ DOMAIN MODEL CHANGES

### Domain Entities (shared/models/domain.py)

**Before:**
```python
class KPI(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Key Performance Indicator entity."""
    name: str
    current_value: float
    target_value: float | None
    owner_id: str | None  # "KPI owner user ID"
    # ...
```

**After:**
```python
class Measure(BaseDomainModel, IdentifiedMixin, TenantScopedMixin):
    """Measure entity."""
    name: str
    current_value: float
    target_value: float | None
    owner_id: str | None  # "Measure owner user ID"
    # ...
```

### Repository Changes (shared/repositories/enhanced_repositories.py)

**Before:**
```python
class KPIRepository(BaseRepository[KPI]):
    """Repository for KPI domain objects."""
    
    def create(self, tenant_id: str, model: KPI) -> KPI:
        item["sk"] = f"KPI#{model.id}"
        # ...
    
    def get(self, tenant_id: str, entity_id: str) -> KPI | None:
        Key={"pk": f"TENANT#{tenant_id}", "sk": f"KPI#{entity_id}"}
        # ...
```

**After:**
```python
class MeasureRepository(BaseRepository[Measure]):
    """Repository for Measure domain objects."""
    
    def create(self, tenant_id: str, model: Measure) -> Measure:
        item["sk"] = f"MEASURE#{model.id}"  # ⚠️ DynamoDB key prefix changed
        # ...
    
    def get(self, tenant_id: str, entity_id: str) -> Measure | None:
        Key={"pk": f"TENANT#{tenant_id}", "sk": f"MEASURE#{entity_id}"}
        # ...
```

**⚠️ CRITICAL:** DynamoDB sort key prefix changed from `KPI#` to `MEASURE#`

---

## 📊 TOPIC CHANGES (coaching/src/core/topic_seed_data.py)

### ❌ DELETED TOPICS

1. **`kpi_recommendations`** - Completely removed (replaced by `measure_recommendations`)

### ✅ RENAMED TOPICS

| Old Topic ID | New Topic ID | Topic Name |
|--------------|--------------|------------|
| `analyze_kpi_impact` | `analyze_measure_impact` | Analyze Measure Impact |
| `record_kpi_update` | `record_measure_update` | Record Measure Update |
| `get_kpi_updates` | `get_measure_updates` | Get Measure Updates |
| `kpi_update_prompt` | `measure_update_prompt` | Measure Update Prompt |
| `update_kpi_from_action` | `update_measure_from_action` | Update Measure from Action |
| `kpi_sync_to_strategic` | `measure_sync_to_strategic` | Measure Sync to Strategic |
| `kpi_sync_from_strategic` | `measure_sync_from_strategic` | Measure Sync from Strategic |
| `detect_kpi_conflicts` | `detect_measure_conflicts` | Detect Measure Conflicts |
| `resolve_kpi_conflict` | `resolve_measure_conflict` | Resolve Measure Conflict |
| `kpi_analysis` | `measure_analysis` | Measure Analysis |

### Topic Prompt Parameter Changes

All topic prompts updated:
- `{kpi_id}` → `{measure_id}`
- `{kpis}` → `{measures}`
- `{related_kpis}` → `{related_measures}`
- `{kpi_updates}` → `{measure_updates}`
- `{strategic_kpis}` → `{strategic_measures}`
- `{operational_kpis}` → `{operational_measures}`

Example from `measure_recommendations` topic:
- **Before:** `"kpiName": "<measure name>"`
- **After:** `"measureName": "<measure name>"`

---

## 📁 FILE CHANGES

### Renamed Files
- `coaching/src/application/analysis/kpi_service.py` → `measure_service.py`
  - Class: `KPIAnalysisService` → `MeasureAnalysisService`

### Modified Files (19 total)

**Coaching Service:**
1. `coaching/src/api/legacy_dependencies.py` - Service factory functions
2. `coaching/src/api/models/analysis.py` - Analysis API models
3. `coaching/src/api/models/strategic_planning.py` - Strategic planning models
4. `coaching/src/api/routes/admin/prompts.py` - Admin routes
5. `coaching/src/api/routes/analysis.py` - Analysis endpoints (deprecated)
6. `coaching/src/api/routes/coaching.py` - Coaching routes
7. `coaching/src/api/routes/coaching_ai.py` - AI coaching routes (deleted endpoint)
8. `coaching/src/application/analysis/__init__.py` - Module exports
9. `coaching/src/core/topic_seed_data.py` - Topic seed data
10. `coaching/src/domain/entities/llm_topic.py` - Topic entity
11. `coaching/src/domain/events/analysis_events.py` - Domain events
12. `coaching/src/models/business_context.py` - Business context models
13. `coaching/src/models/prompt_requests.py` - Prompt request models

**Shared Module:**
14. `shared/domain_types/api_responses.py` - API response types
15. `shared/models/domain.py` - Domain models
16. `shared/models/requests.py` - Request models
17. `shared/models/responses.py` - Response models
18. `shared/repositories/enhanced_repositories.py` - Repository implementations

---

## 🎯 CONSTANTS CHANGES

### coaching/src/core/constants.py

**Already using MEASURE:**
- ✅ `TopicType.MEASURE_SYSTEM` (already existed, was previously `kpi_system`)
- ✅ `AnalysisType.MEASURE` (already existed)
- ✅ `ParameterSource.MEASURE` (already existed)
- ✅ `ParameterSource.MEASURES` (already existed)

### coaching/src/models/prompt_requests.py

**Before:**
```python
category: str = Field(pattern=r"^(coaching|analysis|strategy|kpi)$")
```

**After:**
```python
category: str = Field(pattern=r"^(coaching|analysis|strategy|measure)$")
```

---

## 🔧 INFRASTRUCTURE CHANGES

### DynamoDB Changes
**⚠️ CRITICAL:** Sort key prefix changed in `MeasureRepository`:
- **Before:** `KPI#<id>`
- **After:** `MEASURE#<id>`

**Impact:** Existing KPI records in DynamoDB will **NOT** be accessible by the new repository code unless migrated.

**User Note:** You mentioned "no production data, so backward compatibility or data migration is not needed"

### No AWS Infrastructure Code Changes
- **Pulumi:** No changes required (no KPI-specific table names)
- **CloudFormation:** No changes required

---

## 🧪 TEST FILES (TODO #5 - PENDING)

The following test files contain KPI references and need updating:

1. `coaching/tests/unit/infrastructure/external/test_business_api_client.py`
2. `coaching/tests/unit/api/models/test_strategic_planning.py`
3. `coaching/tests/unit/domain/entities/test_llm_topic.py`
4. `coaching/tests/unit/api/routes/admin/test_prompts.py`
5. `coaching/tests/integration/test_llm_prompts_infrastructure.py`
6. `coaching/tests/integration/test_admin_prompts_api.py`
7. `coaching/tests/integration/api/test_analysis.py`

---

## 📚 DOCUMENTATION CHANGES (TODO #6 - PENDING)

Documentation files with KPI references that need updating:
- Architecture docs
- API specifications
- Status/progress docs
- Implementation guides

---

## ✅ VALIDATION STATUS (TODO #7 - PENDING)

**Status:** Cannot run validation tools (ruff, mypy, pytest) due to Python environment configuration.

**Required before merge:**
```powershell
# Linting
python -m ruff check coaching/ shared/ --fix
python -m ruff format coaching/ shared/

# Type checking
python -m mypy coaching/src shared/ --explicit-package-bases

# All tests
cd coaching && uv run pytest --cov=src
```

**OR use the pre-commit script:**
```powershell
.\scripts\pre-commit-check.ps1
```

---

## 🚀 NEXT STEPS FOR FRONTEND/BACKEND/ADMIN TEAMS

### Frontend Changes Required

1. **Remove references to deleted endpoint:**
   - `/coaching/kpi-recommendations` (no longer exists)
   - Migrate to execute-async pattern with `measure_recommendations` topic

2. **Update payload field names:**
   - All request/response models using `kpi`, `kpis`, `kpi_id` → `measure`, `measures`, `measure_id`
   - `AlignmentDriversResponse`: `kpiPerformance` → `measurePerformance`
   - `StrategySuggestion`: `suggestedKpis` → `suggestedMeasures`
   - `BusinessContext`: `kpis` → `measures`

3. **Update topic IDs in execute-async calls:**
   - `kpi_recommendations` → `measure_recommendations` (if used)
   - All operational AI topics (see "Renamed Topics" section)

### Backend Changes Required

1. **Update API calls to AI service:**
   - Change model class references
   - Update field names in payloads
   - Remove calls to deleted `/coaching/kpi-recommendations` endpoint

2. **Database migration (if applicable):**
   - Migrate existing KPI records to use `MEASURE#` prefix
   - Update business data sync logic

### Admin Changes Required

1. **Update topic management UI:**
   - Display new topic IDs and names
   - Update topic creation validation (kpi_system → measure_system)

2. **Update any admin dashboards:**
   - Change KPI references to Measure
   - Update metrics and reporting

---

## 📋 CHECKLIST FOR DEPLOYMENT

- [ ] Complete test file updates (TODO #5)
- [ ] Complete documentation updates (TODO #6)
- [ ] Run full validation suite (TODO #7)
  - [ ] ruff check and format
  - [ ] mypy type checking
  - [ ] pytest with coverage
- [ ] Notify Frontend team of breaking changes
- [ ] Notify Backend team of breaking changes
- [ ] Notify Admin team of breaking changes
- [ ] Update API documentation/OpenAPI specs
- [ ] Coordinate deployment across all services
- [ ] Monitor for issues post-deployment

---

## 🎉 SUMMARY

- **19 files modified**, **1 file renamed**, **1 endpoint deleted**
- **10 topics renamed**, **1 topic deleted**
- **All code references** to KPI updated to Measure
- **All API contracts** updated (breaking changes)
- **DynamoDB sort key prefix** changed: `KPI#` → `MEASURE#`
- **No backward compatibility** maintained
- **Clean, consistent ubiquitous language** throughout codebase

**Branch:** `feature/issue-196-kpi-to-measure`
**Ready for:** Test updates, validation, and coordinated deployment
