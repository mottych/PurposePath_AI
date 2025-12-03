# Deprecated Services - Topic-Driven Architecture Migration

**Issue**: #113
**Date**: 2025-12-03
**Status**: Services STILL IN USE - No Removal Needed

## Overview

As part of the topic-driven architecture migration (Issue #113), some endpoints were migrated to use the **UnifiedAIEngine**. However, after verification, the old service classes are **still actively used** by non-migrated `/analysis/*` endpoints.

### Decision: NO SERVICE REMOVAL
After thorough verification, we determined that:
- `/analysis/alignment`, `/analysis/strategy`, `/analysis/kpi` endpoints still use old services
- These endpoints were NOT part of the Phase 3 migration scope
- All service files remain in production use
- **NO files will be deleted** in this cleanup phase

## Deprecated Service Classes

### 1. AlignmentAnalysisService
**Location**: `coaching/src/application/analysis/alignment_service.py`

**Replaced By**: UnifiedAIEngine with topics:
- `alignment_explanation`
- `alignment_suggestions`
- `alignment_check` (not yet implemented)

**Used By (Before Migration)**:
- POST `/coaching/alignment-explanation` ✅ Migrated
- POST `/coaching/alignment-suggestions` ✅ Migrated

**Status**: ⚠️ STILL IN USE - DO NOT REMOVE

---

### 2. StrategySuggestionService
**Location**: `coaching/src/application/analysis/strategy_suggestion_service.py`

**Replaced By**: UnifiedAIEngine with topic:
- `strategy_suggestions`

**Used By (Before Migration)**:
- POST `/coaching/strategy-suggestions` ✅ Migrated

**Status**: ⚠️ STILL IN USE - DO NOT REMOVE

---

### 3. OperationsAIService
**Location**: `coaching/src/application/analysis/operations_ai_service.py`

**Replaced By**: UnifiedAIEngine with topics:
- `operations_strategic_alignment`
- `prioritization_suggestions`
- `scheduling_suggestions`
- `root_cause_suggestions`
- `action_suggestions`

**Used By (Before Migration)**:
- POST `/operations/strategic-alignment` ✅ Migrated
- POST `/operations/prioritization-suggestions` ✅ Migrated
- POST `/operations/scheduling-suggestions` ✅ Migrated
- POST `/operations/root-cause-suggestions` ✅ Migrated
- POST `/operations/action-suggestions` ✅ Migrated

**Status**: ⚠️ STILL IN USE - DO NOT REMOVE

---

### 4. OnboardingService
**Location**: `coaching/src/services/onboarding_service.py`

**Replaced By**: UnifiedAIEngine with topics:
- `onboarding_suggestions`
- `website_scan`
- `onboarding_coaching`

**Used By (Before Migration)**:
- POST `/suggestions/onboarding` ✅ Migrated
- POST `/website/scan` ✅ Migrated
- POST `/coaching/onboarding` ✅ Migrated

**Status**: ⚠️ STILL IN USE - DO NOT REMOVE

---

### 5. InsightsService
**Location**: `coaching/src/services/insights_service.py`

**Replaced By**: UnifiedAIEngine with topic:
- `insights_generation`

**Used By (Before Migration)**:
- POST `/insights/generate` ✅ Migrated (AI generation only)

**Note**: InsightsService still used for CRUD operations:
- GET `/insights/categories`
- GET `/insights/priorities`
- POST `/insights/{insight_id}/dismiss`
- POST `/insights/{insight_id}/acknowledge`

**Status**: Partially deprecated - only AI generation methods can be removed

---

## Dependency Chain Analysis

### Direct Dependencies to Check:
1. **Import statements** across codebase
2. **Test files** that import these services
3. **Dependency injection** in route files
4. **Documentation** referencing these services

### Search Commands:
```bash
# Find all imports of deprecated services
grep -r "from.*alignment_service import" coaching/
grep -r "from.*strategy_suggestion_service import" coaching/
grep -r "from.*operations_ai_service import" coaching/
grep -r "from.*onboarding_service import" coaching/
grep -r "from.*insights_service import" coaching/

# Find all references to service classes
grep -r "AlignmentAnalysisService" coaching/
grep -r "StrategySuggestionService" coaching/
grep -r "OperationsAIService" coaching/
grep -r "OnboardingService" coaching/
grep -r "InsightsService" coaching/
```

---

## Removal Plan (Future Phase)

### Step 1: Verify No Dependencies
- [  ] Run grep commands to find all references
- [  ] Check test files for direct service imports
- [  ] Review any documentation referencing services

### Step 2: Remove Service Files
- [  ] Delete `coaching/src/application/analysis/alignment_service.py`
- [  ] Delete `coaching/src/application/analysis/strategy_suggestion_service.py`
- [  ] Delete `coaching/src/application/analysis/operations_ai_service.py`
- [  ] Delete `coaching/src/services/onboarding_service.py`
- [  ] Update `coaching/src/services/insights_service.py` (remove AI generation methods only)

### Step 3: Clean Up Dependency Injection
- [  ] Remove service factory functions from dependencies files
- [  ] Update `__init__.py` exports

### Step 4: Update Tests
- [  ] Remove or update tests that directly test deprecated services
- [  ] Ensure integration tests cover all migrated functionality

### Step 5: Update Documentation
- [  ] Update README if services are mentioned
- [  ] Update architecture diagrams
- [  ] Update API documentation

---

## Benefits of Removal

### Code Reduction:
- Estimated **~2,000 lines** of code removal
- **5 service files** eliminated (4 complete, 1 partial)
- Reduced maintenance burden

### Architecture Benefits:
- Single code path for all AI operations
- Consistent error handling
- Unified logging and monitoring
- Simplified dependency graph

### Maintenance Benefits:
- Fewer files to update when LLM provider changes
- Consistent prompt management across all endpoints
- Easier to add new AI endpoints

---

## Migration Success Criteria

✅ All migrated endpoints use UnifiedAIEngine
✅ No route files import deprecated services
✅ All tests pass without deprecated services
✅ Documentation updated
✅ No breaking changes to API contracts

---

## Notes

- **Do not remove** until Phase 4 cleanup is approved
- **Verify** all references are updated first
- **Run full test suite** before removal
- **Create backup** branch before deletion
- **Update** this document after removal

---

**Last Updated**: 2025-12-03
**Next Review**: After Phase 4 approval
