# Shared Module Analysis - ROOT vs COACHING

**Created**: 2025-06-09  
**Purpose**: Document differences between `pp_ai/shared/` and `pp_ai/coaching/shared/` to plan safe migration  
**Issue**: #116 - Empty topics response investigation revealed duplicate shared modules

---

## Executive Summary

**Finding**: No code directly imports from `coaching.shared.*` - ALL imports use `shared.*` syntax.

**Impact**: The `coaching/shared/` directory appears to be **orphaned/outdated code** that exists in the deployed Lambda but may cause import conflicts.

**Risk**: Having BOTH directories in Lambda creates potential for Python to import the wrong version depending on sys.path order.

**Recommendation**: Migrate all code to use ROOT `shared/` and remove `coaching/shared/` from Dockerfile.

---

## Import Analysis

### Imports from `shared.models.multitenant` (33 matches)

**Classes Imported**:
- `CoachingTopic` (enum with 4 values)
- `RequestContext` (user/tenant context)
- `UserRole` (enum: OWNER, ADMIN, MANAGER, MEMBER, VIEWER)
- `Permission` (enum for permissions)
- `SubscriptionTier` (enum for subscription levels)

**Files Using These Imports**:
```
coaching/src/repositories/topic_repository.py:126
coaching/src/domain/entities/llm_topic.py:430
coaching/src/services/multitenant_conversation_service.py:43-44
coaching/src/middleware/auth.py
coaching/src/middleware/admin_auth.py
coaching/src/dependencies/multitenant_dependencies.py
coaching/src/api/routes/admin/*.py (multiple files)
coaching/src/api/routes/topics.py
coaching/src/api/routes/coaching.py
coaching/src/api/routes/insights.py
coaching/src/api/routes/website.py
coaching/tests/* (multiple test files)
```

### Imports from `shared.models.schemas` (16 matches)

**Classes Imported**:
- `ApiResponse` (generic response envelope)
- `PaginatedResponse` (paginated response envelope)
- `PaginationMeta` (pagination metadata)

**Files Using These Imports**:
```
coaching/src/api/routes/admin/*.py (multiple files)
coaching/src/api/routes/topics.py
coaching/src/api/routes/insights.py
coaching/src/api/routes/coaching.py
coaching/src/api/routes/website.py
coaching/src/api/routes/multitenant_conversations.py
coaching/src/services/insights_service.py
```

### Imports from `shared.services.data_access` (1 match)

**Classes Imported**:
- `BusinessDataRepository`
- `CoachingSessionRepository`
- `UserPreferencesRepository`

**Files Using These Imports**:
```
coaching/src/services/multitenant_conversation_service.py:47
```

### Imports from `coaching.shared.*` (0 matches)

**Result**: NO CODE directly imports from `coaching.shared.*`

---

## File-by-File Comparison

### 1. `multitenant.py`

| Aspect | ROOT (`shared/models/`) | COACHING (`coaching/shared/models/`) |
|--------|------------------------|-------------------------------------|
| **Size** | 12,350 bytes | 12,064 bytes (286 bytes smaller) |
| **Line Differences** | - | 13 differences |
| **Lines** | 357 lines | 346 lines |
| **Unique in ROOT** | (nothing significant) | - |
| **Unique in COACHING** | - | `TRIAL = "trial"` in SubscriptionTier enum (line 50)<br>`has_permission()` method in RequestContext<br>`UserContext` class (alias for RequestContext) |
| **Impact** | Simpler/cleaner | Has extra features |

**Detailed Differences**:

1. **SubscriptionTier enum**:
   - ROOT: `STARTER`, `PROFESSIONAL`, `ENTERPRISE` (3 values)
   - COACHING: `TRIAL`, `STARTER`, `PROFESSIONAL`, `ENTERPRISE` (4 values - has TRIAL)

2. **RequestContext.has_permission() method**:
   - ROOT: Does NOT have this method
   - COACHING: Has this helper method (lines ~250-255):
     ```python
     def has_permission(self, perm: Permission) -> bool:
         try:
             return perm.value in (self.permissions or [])
         except Exception:
             return False
     ```

3. **UserContext class**:
   - ROOT: Does NOT have this class
   - COACHING: Has this as backward-compatible alias (lines ~340):
     ```python
     class UserContext(RequestContext):
         """Backward compatible alias for request-scoped user context."""
         pass
     ```

**Critical Finding**: `UserContext` in COACHING shared is just an ALIAS for RequestContext, but coaching codebase has its OWN `UserContext` defined in `coaching/src/api/models/auth.py` which is DIFFERENT and used extensively (20+ imports). The shared version is NOT used.

**Verification Results**:
- ✅ `UserContext` - 20+ matches, but ALL import from `coaching.src.api.models.auth`, NONE from shared
- ✅ `has_permission()` - ZERO matches in coaching codebase - method not used

**Migration Risk**: 🟢 LOW → Changed from MEDIUM
- `has_permission()` is not used anywhere
- `UserContext` in shared is not used (coaching has its own in src/api/models/auth.py)
- Only difference that matters: COACHING has `TRIAL` subscription tier, ROOT doesn't
- Need to add `TRIAL = "trial"` to ROOT's SubscriptionTier enum before migration

---

### 2. `schemas.py`

| Aspect | ROOT (`shared/models/`) | COACHING (`coaching/shared/models/`) |
|--------|------------------------|-------------------------------------|
| **Size** | 15,120 bytes | 5,161 bytes (9,959 bytes smaller, 3x difference!) |
| **Lines** | 515 lines | 192 lines |
| **Line Differences** | - | 367 differences (massive!) |
| **Public API** | ApiResponse, PaginatedResponse, PaginationMeta, ErrorCode, 50+ classes | ApiResponse, PaginatedResponse, PaginationMeta, 15+ classes |
| **Exports Match?** | ✅ YES - Both export same basic classes | ✅ YES - Compatible API surface |

**ROOT Version Includes** (515 lines):
```python
# Enums
- ErrorCode (50+ standardized error codes)

# Base classes
- BaseModelWithDatetime
- ApiResponse[T]
- PaginationMeta
- PaginatedResponse[T]

# User/Auth models
- UserProfile
- TenantInfo
- AuthResponse
- RegistrationVerificationPending
- UpdateUserProfileRequest
- UpdateSubscriptionRequest
- LoginRequest
- RegisterRequest
- RefreshTokenRequest
- ForgotPasswordRequest
- ResetPasswordRequest
- ConfirmEmailRequest
- GoogleAuthRequest

# Business models
- Address
- OnboardingStep3
- OnboardingStep4
- CreateProductRequest
- UpdateProductRequest
- UpdateOnboardingRequest
- BillingPortalResponse
- UserLimitsResponse

# Plus many more...
```

**COACHING Version Includes** (192 lines):
```python
# Base classes
- BaseModelWithDatetime
- ApiResponse[T]
- PaginationMeta
- PaginatedResponse[T]

# User/Auth models
- UserProfile
- TenantInfo
- AuthResponse
- RegistrationVerificationPending
- UpdateUserProfileRequest
- UpdateSubscriptionRequest
- LoginRequest
- RegisterRequest
- RefreshTokenRequest
- ForgotPasswordRequest
- ResetPasswordRequest
- ConfirmEmailRequest
- GoogleAuthRequest

# That's it - much simpler!
```

**Critical Finding**: ROOT version has 3x more content, including:
- `ErrorCode` enum (not in COACHING)
- Many business-specific models (Address, Onboarding, Products, Billing, etc.)
- These extra models are likely needed for full system functionality

**Migration Risk**: 🟢 LOW - COACHING version is a subset of ROOT. Code importing basic classes (ApiResponse, PaginatedResponse, PaginationMeta) will work with ROOT version since it's a superset.

---

### 3. `data_access.py`

| Aspect | ROOT (`shared/services/`) | COACHING (`coaching/shared/services/`) |
|--------|------------------------|-------------------------------------|
| **Size** | Unknown | 38,904 bytes |
| **Line Differences** | - | 929 differences (MASSIVE!) |
| **Imports** | Unknown | Line 14: `from shared.models.multitenant import ...` |
| **Exports** | Unknown | BusinessDataRepository, CoachingSessionRepository, UserPreferencesRepository |

**Critical Finding**: COACHING version imports from `shared.models.multitenant` (line 14), creating potential circular dependency.

**Usage**: Only ONE file imports from this:
- `coaching/src/services/multitenant_conversation_service.py:47`

**Migration Risk**: 🔴 HIGH - 929 line differences suggest significantly different implementations. Need detailed comparison of:
- `BusinessDataRepository`
- `CoachingSessionRepository`
- `UserPreferencesRepository`

**Next Step**: Compare these three classes implementation-by-implementation.

---

## Python Path Configuration

### Local Development (Tests)

**File**: `coaching/conftest.py` lines 14-23

```python
REPO_ROOT = Path(__file__).parent.parent.resolve()
SHARED_DIR = REPO_ROOT / "shared"  # Points to ROOT shared/
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SHARED_DIR))
```

**Result**: Tests use ROOT `shared/` module.

### Deployed Lambda

**File**: `coaching/Dockerfile` lines 10-11

```dockerfile
COPY coaching ${LAMBDA_TASK_ROOT}/coaching      # Includes coaching/shared/
COPY shared ${LAMBDA_TASK_ROOT}/shared          # ROOT shared/
```

**Result**: Lambda has BOTH:
- `/var/task/shared/` (ROOT)
- `/var/task/coaching/shared/` (COACHING)

**Import Resolution**: Python will use whichever comes first in `sys.path`. Since COACHING contains `shared/`, imports might resolve to the wrong version!

---

## Current Status

### What We Know

✅ **No direct `coaching.shared` imports** - All code uses `shared.*` syntax  
✅ **Local tests use ROOT** - Via conftest.py configuration  
✅ **Lambda has BOTH** - Potential for import conflicts  
✅ **schemas.py compatible** - ROOT is superset of COACHING  
✅ **50+ files import from shared** - Widespread usage  

### What We Don't Know

❓ **multitenant.py**: Is `UserContext` or `has_permission()` used?  
❓ **data_access.py**: How different are the repository implementations?  
❓ **Import conflicts**: Which version does Lambda actually import?  
❓ **Root cause**: Is shared module confusion causing empty topics?  

---

## Migration Plan (Draft)

### Phase 1: Analysis (CURRENT)

- [x] Catalog all imports from shared modules
- [x] Compare file sizes and line counts
- [x] Verify no direct `coaching.shared` imports
- [ ] **TODO**: Check if `UserContext` or `has_permission()` are used
- [ ] **TODO**: Compare `data_access.py` repository implementations
- [ ] **TODO**: Test import resolution in Lambda environment

### Phase 2: Verification

- [ ] Run all tests with ROOT shared/ only
- [ ] Deploy test version without coaching/shared/
- [ ] Verify CloudWatch logs show correct behavior
- [ ] Confirm topics endpoint returns data

### Phase 3: Migration

- [ ] Update Dockerfile to exclude coaching/shared/
  ```dockerfile
  # OLD (line 10)
  COPY coaching ${LAMBDA_TASK_ROOT}/coaching
  
  # NEW (line 10)
  COPY coaching/src ${LAMBDA_TASK_ROOT}/coaching/src
  COPY coaching/prompts ${LAMBDA_TASK_ROOT}/coaching/prompts
  # ... explicitly copy only needed directories, exclude coaching/shared
  ```
- [ ] Delete `coaching/shared/` directory
- [ ] Update any import paths if needed
- [ ] Full test suite run
- [ ] Deploy to dev
- [ ] Verify topics endpoint

### Phase 4: Validation

- [ ] Monitor CloudWatch for errors
- [ ] Run integration tests
- [ ] Verify all 883 tests still pass
- [ ] Close issue #116

---

## Risk Assessment

### LOW RISK ✅

**`shared.models.schemas` migration**:
- ROOT version is superset of COACHING
- Code only imports basic classes (ApiResponse, PaginatedResponse, PaginationMeta)
- These exist in both versions with compatible APIs
- Migration should be seamless

### MEDIUM RISK 🟡

**`shared.models.multitenant` migration**:
- COACHING has unique `UserContext` class not in ROOT
- COACHING has unique `has_permission()` method
- Need to verify these aren't used anywhere
- If used, must port to ROOT or refactor code

### HIGH RISK 🔴

**`shared.services.data_access` migration**:
- 929 line differences suggest major implementation divergence
- Only used by one file (multitenant_conversation_service.py)
- Repository implementations may have different behavior
- Requires detailed comparison and testing

---

## Next Actions

1. **Check for UserContext usage** (MEDIUM priority):
   ```bash
   git grep -n "UserContext" coaching/
   ```

2. **Check for has_permission usage** (MEDIUM priority):
   ```bash
   git grep -n "has_permission" coaching/
   ```

3. **Compare data_access.py repositories** (HIGH priority):
   - Compare `BusinessDataRepository` implementations
   - Compare `CoachingSessionRepository` implementations
   - Compare `UserPreferencesRepository` implementations

4. **Test import resolution** (HIGH priority):
   ```python
   # In Lambda environment, which version imports?
   import shared.models.schemas as schemas
   print(schemas.__file__)
   ```

5. **Create test deployment** (HIGH priority):
   - Update Dockerfile to exclude coaching/shared
   - Deploy to test environment
   - Verify functionality

---

## Questions for User

1. **UserContext class**: Do you know if this class is used anywhere? It's in COACHING multitenant.py but not in ROOT.

2. **data_access.py**: Should we use ROOT version or COACHING version? They're vastly different (929 line diff).

3. **Migration timing**: Should we fix this shared module issue as part of #116 or create separate issue?

4. **Testing approach**: Do you want test deployment first, or should we analyze code more before changing Dockerfile?

---

**Document Status**: Draft - Awaiting user input on next steps
