# Project Structure Cleanup Plan

**Date:** October 8, 2025  
**Issue:** Duplicate code directories causing confusion and wasted effort  
**Status:** 🔴 CRITICAL - Must fix immediately

## Problem Identified

### Code Duplication Discovery

We have **DUPLICATE coaching services** in the repository:

```
pp_ai/
├── coaching/                          ❌ DUPLICATE (orphaned, no pyproject.toml)
│   ├── src/                          
│   ├── tests/
│   └── samconfig.toml
│
└── mypy_boto3_dynamodb/
    ├── coaching/                      ✅ REAL PROJECT (has pyproject.toml, installed package)
    │   ├── src/
    │   ├── tests/
    │   ├── pyproject.toml
    │   └── uv.lock
    └── shared/                        ✅ REAL SHARED (has models, services, repositories)
```

### Impact

- **Working on same code 3 times** - Fixing bugs in wrong location
- **Tests run against wrong code** - Validation meaningless
- **Git confusion** - Which files to commit?
- **Wasted development time** - Debugging phantom issues

### Confirmed Facts

1. **Installed package:** `purposepath-coaching` points to `mypy_boto3_dynamodb/coaching/`
2. **Project config:** Only `mypy_boto3_dynamodb/coaching/pyproject.toml` exists
3. **Test execution:** Tests run from `mypy_boto3_dynamodb/coaching/tests/`
4. **Shared code:** `mypy_boto3_dynamodb/shared/` has the real shared modules

## Root Cause Analysis

This duplication likely happened due to:
1. **Historical migration** - Old structure not fully cleaned up
2. **Poor naming** - Why is everything under `mypy_boto3_dynamodb`? That's a package name, not a service folder!
3. **Lack of .gitignore** - Should have prevented duplicate tracking

## Cleanup Plan

### Phase 1: Verify and Document (10 minutes)

1. ✅ **DONE:** Identify which is the real project
2. ✅ **DONE:** Confirm installed package location
3. **TODO:** Check if `coaching/` has any unique files not in `mypy_boto3_dynamodb/coaching/`
4. **TODO:** Document the intended structure

### Phase 2: Safe Removal (15 minutes)

1. **Backup:** Create backup of `coaching/` directory (just in case)
2. **Compare:** Diff the two directories to ensure no unique code
3. **Remove:** Delete `pp_ai/coaching/` directory
4. **Verify:** Run tests to ensure nothing broke
5. **Commit:** Commit the cleanup

### Phase 3: Restructure (30 minutes)

The current structure is confusing. Why is everything under `mypy_boto3_dynamodb`?

**Current (Confusing):**
```
pp_ai/
└── mypy_boto3_dynamodb/        ← WTF? This is a PyPI package name!
    ├── coaching/
    ├── shared/
    └── ...
```

**Proposed (Clear):**
```
pp_ai/
├── services/
│   └── coaching/               ← Clear: this is a service
│       ├── src/
│       ├── tests/
│       └── pyproject.toml
│
├── shared/                     ← Clear: shared code
│   ├── models/
│   ├── services/
│   └── repositories/
│
└── infrastructure/             ← Clear: deployment stuff
    ├── account/
    └── ...
```

### Phase 4: Update References (20 minutes)

After restructuring:
1. Update import statements
2. Update pyproject.toml paths
3. Update test configurations
4. Update CI/CD references
5. Update documentation

## Immediate Action Required

### Step 1: Compare Directories

```powershell
# Check if coaching/ has any unique files
$real = Get-ChildItem -Path "mypy_boto3_dynamodb\coaching\src" -Recurse -File
$dupe = Get-ChildItem -Path "coaching\src" -Recurse -File
# Compare file counts and names
```

### Step 2: Delete Duplicate (After Verification)

```powershell
# Backup first
Copy-Item -Path "coaching" -Destination "coaching_BACKUP_2025-10-08" -Recurse

# Then remove
Remove-Item -Path "coaching" -Recurse -Force
```

### Step 3: Run Tests

```powershell
cd mypy_boto3_dynamodb\coaching
pytest tests/ -v
```

## Why This Happened

Looking at the folder structure, I suspect:
1. Someone started with a package named `mypy_boto3_dynamodb` (probably for type stubs)
2. Then put actual service code inside it (WRONG!)
3. Later someone created `coaching/` at the root thinking it should be there
4. Both coexisted, causing confusion

## Correct Structure Going Forward

### Option A: Keep Current Names (Minimal Change)
```
pp_ai/
├── mypy_boto3_dynamodb/
│   ├── coaching/               ← Keep working here
│   │   ├── src/
│   │   ├── tests/
│   │   └── pyproject.toml
│   └── shared/
└── (delete coaching/)
```

### Option B: Rename to Logical Structure (Recommended)
```
pp_ai/
├── coaching/                   ← Rename from mypy_boto3_dynamodb/coaching
│   ├── src/
│   ├── tests/
│   └── pyproject.toml
├── shared/                     ← Move from mypy_boto3_dynamodb/shared
│   ├── models/
│   └── services/
└── infrastructure/
```

## Decision Required

**QUESTION FOR USER:**

Do you want to:

**Option 1 (Quick Fix):** Just delete `coaching/` duplicate, keep working in `mypy_boto3_dynamodb/coaching/`

**Option 2 (Proper Fix):** Rename `mypy_boto3_dynamodb/` to a logical structure (`services/`, `shared/`, etc.)

My recommendation: **Option 2** - Fix it properly now. The current structure with `mypy_boto3_dynamodb` as a parent folder is misleading and will confuse future developers.

## Next Steps

1. **User Decision:** Choose Option 1 or Option 2
2. **Execute Cleanup:** Remove duplicates
3. **Restructure (if Option 2):** Rename directories logically
4. **Update Configs:** Fix pyproject.toml, imports, tests
5. **Test Everything:** Ensure nothing broke
6. **Commit:** Clean commit with clear message
7. **Document:** Update project structure docs

## Time Estimate

- **Option 1 (Quick):** 15 minutes
- **Option 2 (Proper):** 1 hour

**WORTH IT:** Option 2 saves hours of future confusion.
