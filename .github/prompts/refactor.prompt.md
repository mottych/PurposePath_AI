---
agent: agent
---

# Refactor Code - Mandatory Workflow

## CRITICAL: Follow #file:../AI_WORKFLOW_CHECKLIST.md EXACTLY

### STEP 1: Branch Check (MANDATORY)

1. Show current branch: `git branch --show-current`
2. **IF on `dev` or `main`:**
   - STOP immediately
   - Create feature branch: `git checkout -b feature/refactor-{component-name}`
   - Example: `git checkout -b feature/refactor-user-service`
3. **WAIT FOR USER APPROVAL** before proceeding

### STEP 2: Refactoring Analysis

1. Identify code smells or architectural issues
2. Define clear refactoring goals:
   - Improve maintainability?
   - Follow Clean Architecture better?
   - Reduce complexity?
   - Improve testability?
3. Document current behavior (tests should capture this)
4. Get user confirmation on refactoring approach

### STEP 3: Test Baseline

1. Run all existing tests: `dotnet test --no-build --verbosity quiet`
2. ALL tests must pass BEFORE refactoring
3. If tests fail, fix them first
4. Document test coverage gaps

### STEP 4: Refactor Implementation

**Follow Clean Architecture principles:**
- Domain: Pure business logic, no external dependencies
- Application: Orchestration, implements domain contracts
- Infrastructure: Database, external services
- API: DTOs, mapping, HTTP concerns

**Common refactorings:**
- Extract method/class for single responsibility
- Move logic to appropriate layer
- Replace primitives with value objects
- Replace dictionaries with strongly-typed classes
- Implement repository pattern
- Add domain events
- Use AutoMapper instead of manual mapping

### STEP 5: Continuous Validation

After EACH refactoring step:
1. Build: `dotnet build --no-restore -v minimal`
2. Run tests: `dotnet test --no-build --verbosity quiet`
3. Ensure tests still pass (behavior unchanged)
4. Fix any broken tests or build errors immediately

### STEP 6: Add Tests if Needed

1. Add unit tests for new methods/classes
2. Add integration tests for new infrastructure code
3. Ensure refactored code has equal or better test coverage

### STEP 7: Final Validation

1. Build: `dotnet build --no-restore -v minimal`
2. Run all tests: `dotnet test --no-build --verbosity quiet`
3. Verify ALL tests pass
4. Fix ALL warnings and errors
5. Confirm behavior unchanged (regression testing)

### STEP 8: Commit & Merge

1. Stage: `git add -A`
2. Commit format: `refactor(#{issue}): {description}`
   - Example: `refactor: Extract email validation to value object`
3. Switch to dev: `git checkout dev`
4. Merge: `git merge --no-ff feature/refactor-{component}`
5. Delete branch: `git branch -d feature/refactor-{component}`

---

**Critical Rules:**
- ✅ Tests must pass BEFORE and AFTER refactoring
- ✅ Behavior must remain identical (no functional changes)
- ✅ Refactor in small, testable increments
- ✅ Build and test after each change
- ❌ Never mix refactoring with feature changes
- ❌ Never skip tests during refactoring
- ❌ Never break existing API contracts

**Refactoring != New Features**
Refactoring changes HOW code works, not WHAT it does.
