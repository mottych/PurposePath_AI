---
agent: agent
---

# Fix Bug - Mandatory Workflow

## CRITICAL: Follow #file:../AI_WORKFLOW_CHECKLIST.md EXACTLY

### STEP 1: Branch Check (MANDATORY)

1. Show current branch: `git branch --show-current`
2. **IF on `dev` or `main`:**
   - STOP immediately
   - Create feature branch: `git checkout -b feature/fix-{brief-description}`
   - Example: `git checkout -b feature/fix-null-reference-error`
3. **WAIT FOR USER APPROVAL** before proceeding

### STEP 2: Root Cause Analysis

1. Review error message/stack trace
2. Identify the failing component
3. Locate the exact line/method causing issue
4. Determine why it fails (logic error, null reference, race condition, etc.)
5. Document findings for user

### STEP 3: Fix Implementation

1. Implement minimal fix that addresses root cause
2. Follow Clean Architecture principles
3. Maintain existing API contracts per #file:../COPILOT_RULES.md
4. Do NOT introduce breaking changes
5. Add/update comments explaining the fix

### STEP 4: Regression Testing

1. Create regression test that reproduces the bug
2. Verify test fails before fix (proves it catches the bug)
3. Apply fix
4. Verify test passes after fix
5. Run all existing tests: `dotnet test --no-build --verbosity quiet`
6. Ensure NO test regressions

### STEP 5: Validation

1. Build: `dotnet build --no-restore -v minimal`
2. Fix ALL warnings and errors
3. Verify the specific bug is fixed
4. Verify no new bugs introduced

### STEP 6: Commit & Merge

1. Stage: `git add -A`
2. Commit format: `fix(#{issue}): {description}`
3. Switch to dev: `git checkout dev`
4. Merge: `git merge --no-ff feature/fix-{description}`
5. Delete branch: `git branch -d feature/fix-{description}`

### STEP 7: Close Issue (if applicable)

1. Post root cause analysis and fix summary to issue
2. Remove 'in-progress' label
3. Close issue with state_reason: 'completed'

---

**Remember:**
- 🔍 Always do root cause analysis first
- 🧪 Always add regression test
- 🚫 Never skip existing tests
- ✅ Fix must be minimal and targeted
