---
agent: agent
---

# Resolve GitHub Issue - Mandatory Workflow (Python/FastAPI)

## CRITICAL: Follow #file:../copilot-instructions.md Standards

### STEP 0: Pre-Flight Checks (MANDATORY)

1. **Verify virtual environment active**: Check for `(.venv)` in prompt
   - If not active: `. .venv/Scripts/Activate.ps1` (Windows) or `source .venv/bin/activate` (Unix)
2. **Show current branch**: `git branch --show-current`
3. **IF on `dev`, `staging`, or `master`:**
   - ⛔ **STOP IMMEDIATELY** - Never commit directly to protected branches
   - Create feature branch: `git checkout -b fix/{ISSUE_NUMBER}-{brief-description}`
   - Branch naming:
     - `fix/123-description` for bug fixes
     - `feat/123-description` for features
     - `refactor/123-description` for refactoring
   - Example: `git checkout -b fix/117-suggestions-authentication`
4. **WAIT FOR USER CONFIRMATION** before proceeding

### STEP 1: GitHub Issue Setup

1. **Read the issue completely** - understand acceptance criteria
2. **Mark issue in-progress**:
   ```bash
   gh issue edit {ISSUE_NUMBER} --add-label "in-progress"
   gh issue comment {ISSUE_NUMBER} --body "🚀 Starting work on this issue..."
   ```
3. **Post investigation plan** as issue comment if complex

### STEP 2: Implementation (Quality First)

1. **Follow Clean Architecture + DDD patterns** per #file:../copilot-instructions.md:
   - Domain layer: NO external dependencies
   - Use Pydantic models (NO `dict[str, Any]`)
   - Strong typing with `NewType` for domain IDs
   - Repository pattern (Port/Adapter)
2. **Follow API specifications**:
   - #file:../../docs/Specifications/backend-integration-index.md
   - #file:../../docs/API_DOCUMENTATION.md
3. **Implement tests alongside code** (TDD when possible)
4. **Use structured logging** (structlog) with context

### STEP 3: Code Quality Validation (MANDATORY - ALL MUST PASS)

Run in this exact order:

```bash
# 1. Format code
black coaching/src/ coaching/tests/

# 2. Lint and auto-fix
ruff check coaching/src/ coaching/tests/ --fix

# 3. Type checking (strict mode)
mypy coaching/src/ --strict

# 4. Run ALL unit tests (not just new ones)
python -m pytest coaching/tests/unit/ -x --tb=short -q

# 5. Optional: Run integration tests if infrastructure changed
python -m pytest coaching/tests/integration/ -x --tb=short -q
```

**CRITICAL**: Fix ALL errors and warnings (even unrelated ones). The task is NOT complete until everything passes.

### STEP 4: Commit to Feature Branch

1. **Clean up temporary files**:
   ```bash
   rm -f issue_body.md
   rm -rf __pycache__/
   ```

2. **Stage changes**:
   ```bash
   git add -A
   ```

3. **Commit with conventional format**:
   ```bash
   git commit -m "{type}(#{issue}): {description}"
   ```
   
   **Commit types**:
   - `feat`: New feature
   - `fix`: Bug fix
   - `refactor`: Code refactoring
   - `test`: Tests only
   - `docs`: Documentation
   - `chore`: Maintenance
   
   **Examples**:
   - `fix(#117): use get_current_context for suggestions authentication`
   - `feat(#42): implement alignment score calculation service`
   - `test(#89): add unit tests for conversation entity`

4. **Verify pre-commit hooks pass** (ruff, black, mypy)

### STEP 5: Merge & Sync to Dev

```bash
# 1. Switch to dev
git checkout dev

# 2. Merge with no-fast-forward (preserves history)
git merge --no-ff fix/{ISSUE_NUMBER}-{description} -m "Merge fix/{ISSUE_NUMBER}-{description}"

# 3. Delete local feature branch
git branch -d fix/{ISSUE_NUMBER}-{description}

# 4. Push to origin
git push origin dev
```

**WAIT for deployment** - CI/CD pipeline will trigger automatically

### STEP 6: Post-Deployment Verification (E2E Testing)

1. **Monitor deployment**:
   ```bash
   gh run list --workflow=deploy-dev.yml --limit 1
   gh run watch {RUN_ID} --exit-status
   ```

2. **Run E2E tests** against deployed API:
   - Test with real JWT tokens
   - Verify CloudWatch logs
   - Check all affected endpoints

3. **If tests fail**:
   - ⛔ Do NOT close issue
   - Create new feature branch from dev
   - Fix and repeat from STEP 2

### STEP 7: Close Issue & Cleanup

**ONLY after successful deployment and E2E verification:**

1. **Update issue with results**:
   ```bash
   gh issue comment {ISSUE_NUMBER} --body "✅ **Resolved and verified in production**
   
   **Changes:**
   - {summary of changes}
   
   **Testing:**
   - ✅ 887 unit tests passing
   - ✅ E2E verification completed
   - ✅ CloudWatch logs confirmed
   
   **Deployment:**
   - Commit: {commit_sha}
   - Deployed to: dev environment"
   ```

2. **Remove in-progress label and close**:
   ```bash
   gh issue edit {ISSUE_NUMBER} --remove-label "in-progress"
   gh issue close {ISSUE_NUMBER} --reason "completed"
   ```

3. **Delete remote feature branch** (if exists):
   ```bash
   git push origin --delete fix/{ISSUE_NUMBER}-{description}
   ```

4. **Clean up all temporary artifacts**:
   - Remove debug code
   - Delete test data files
   - Remove unused imports

---

## ⚠️ Critical Reminders (copilot-instructions.md)

### NEVER:
- ❌ Commit directly to `dev`, `staging`, or `master` branches
- ❌ Skip any validation step (black, ruff, mypy, pytest)
- ❌ Leave warnings or errors (even unrelated ones)
- ❌ Use `dict[str, Any]` in domain layer
- ❌ Hardcode secrets or configuration values
- ❌ Create TODO comments in production code
- ❌ Close issue before deployment verification
- ❌ Work without active virtual environment

### ALWAYS:
- ✅ Work in feature branch off `dev`
- ✅ Activate virtual environment first
- ✅ Link all commits to issue number
- ✅ Run ALL tests (not just new ones)
- ✅ Use Pydantic models and strong typing
- ✅ Follow Clean Architecture + DDD patterns
- ✅ Write tests alongside implementation
- ✅ Update GitHub issue with progress
- ✅ Verify E2E after deployment
- ✅ Clean up temporary code and branches

### When in Doubt:
- 🤔 **ASK THE USER** - Quality over speed
- 📖 Consult #file:../copilot-instructions.md
- 🏗️ Review architecture docs in `docs/Plans/`
- 📋 Check specifications in `docs/Specifications/`

---

**Quality First Principles**: No shortcuts. Expert standards. Complete it right the first time.
