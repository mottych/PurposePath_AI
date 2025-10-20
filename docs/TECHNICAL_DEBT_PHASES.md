# Technical Debt Cleanup - Phased Implementation Plan

**Total MyPy Errors:** 208 across 39 files  
**Strategy:** Fix in 4 phases, starting with highest priority

---

## Phase 1: Core API Files (HIGH PRIORITY) ⚡

**GitHub Issue:** Create issue titled "fix: resolve type errors in core API files (Phase 1)"

**Scope:** Recently refactored API files - ensure type safety in production code

**Files:**
- `coaching/src/api/main.py` - 1 error (untyped decorator)
- `coaching/src/api/routes/conversations.py` - ~15 errors
  - Wrong method names: `calculate_progress()` vs `calculate_progress_percentage()`
  - Wrong method: `generate_response()` vs `generate_coaching_response()`
  - Missing method: `should_complete()`
  - Wrong attribute: `ConversationContext.phase`
  - Untyped decorators
  - EllipsisType default args
- `coaching/src/api/routes/analysis.py` - ~10 errors
  - Dict type mismatches
  - List type mismatches  
  - Missing enum: `AnalysisType.OPERATIONS`
  - Untyped decorators
- `coaching/src/api/routes/health.py` - 2 errors (untyped decorators)

**Estimated Errors:** ~30  
**Estimated Time:** 2-3 hours

**Acceptance Criteria:**
- All type errors resolved in Phase 1 files
- All tests pass
- Ruff, black, mypy checks pass
- No regression in functionality

---

## Phase 2: Service Layer (MEDIUM PRIORITY) 🔧

**GitHub Issue:** Create issue titled "fix: resolve type errors in service layer (Phase 2)"

**Scope:** Business logic services with type mismatches

**Files:**
- `coaching/src/services/multitenant_conversation_service.py` - ~25 errors
  - Pydantic model vs dict mismatches
  - TypedDict extra keys
  - Wrong model attributes (`.get()` vs properties)
  - Type incompatibilities between models
- `coaching/src/services/llm_service.py` - errors TBD
- `coaching/src/services/onboarding_service.py` - ~2 errors
  - Wrong method: `generate_completion()`
- Other service files with type issues

**Estimated Errors:** ~50  
**Estimated Time:** 3-4 hours

**Acceptance Criteria:**
- Service layer properly typed
- Pydantic models used consistently
- All tests pass

---

## Phase 3: Routes & Dependencies (MEDIUM PRIORITY) 📝

**GitHub Issue:** Create issue titled "fix: resolve type errors in routes and dependencies (Phase 3)"

**Scope:** Remaining API routes and dependency injection

**Files:**
- `coaching/src/api/routes/multitenant_conversations.py` - ~9 errors (untyped decorators)
- `coaching/src/api/routes/onboarding.py` - ~7 errors
  - Type mismatches in response models
  - Untyped decorators
  - Missing dependency function
- `coaching/src/api/multitenant_dependencies.py` - 1 error (unused ignore comment)

**Estimated Errors:** ~20  
**Estimated Time:** 2 hours

---

## Phase 4: Infrastructure & Domain (LOW PRIORITY) 🏗️

**GitHub Issue:** Create issue titled "fix: resolve type errors in infrastructure and domain layers (Phase 4)"

**Scope:** Lower-level infrastructure, domain entities, repositories

**Files:**
- Domain entities and value objects
- Repository implementations
- Infrastructure adapters
- Utilities and helpers
- Remaining scattered errors

**Estimated Errors:** ~108  
**Estimated Time:** 4-5 hours

**Note:** Many of these may be in experimental/backup code that could be deleted

---

## Implementation Order

1. ✅ Phase 1 (Core API) - **START HERE**
2. Phase 2 (Services)
3. Phase 3 (Routes)
4. Phase 4 (Infrastructure)

## Success Criteria (All Phases)

- Zero mypy errors in checked files
- All ruff checks pass
- All black formatting checks pass
- All unit tests pass
- All integration tests pass
- No functional regression
- Code follows clean architecture principles
- Proper use of Pydantic models over dicts

---

**Created:** 2025-10-20  
**Last Updated:** 2025-10-20
