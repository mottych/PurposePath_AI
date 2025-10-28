# Development Workflow - PurposePath AI

## Root Cause: 60+ Failed Deployments

### Why It Happened:
1. **Dependency Conflicts** (35+ failures)
   - No dependency lock file
   - Manual version pinning without compatibility checks
   - langchain ecosystem required specific boto3/httpx/pydantic versions

2. **Python Version Incompatibility** (15+ failures)
   - Code used Python 3.12 features without `from __future__ import annotations`
   - CI runs Python 3.11 where `StateGraph[dict]` fails

3. **No Local Validation** (Process Failure)
   - Changes pushed without running tests locally
   - Every error discovered in CI (3-5 min delay × 60 = 5 hours wasted)

4. **Missing Dev Dependencies**
   - Type stubs added reactively, not proactively

---

## ✅ MANDATORY: Local Testing Before Push

### Quick Check (30 seconds):
```powershell
# From pp_ai directory
.\scripts\test_local.ps1
```

### Manual Steps:
```powershell
# 1. Lint
python -m ruff check coaching/ shared/

# 2. Format
python -m ruff format --check coaching/ shared/

# 3. Type Check
python -m mypy coaching/src shared/ --explicit-package-bases

# 4. Tests
python -m pytest coaching/tests/unit -v
```

**RULE: If any check fails locally, FIX IT before pushing.**

---

## Development Process

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name dev
```

### 2. Make Changes
- Write code
- Add/update tests
- Update type hints

### 3. Run Local Tests
```powershell
.\scripts\test_local.ps1
```

### 4. Fix All Errors
- **Zero tolerance**: All errors must be fixed
- No `# noqa`, no `# type: ignore` (except documented cases)
- No shortcuts

### 5. Commit & Push
```bash
git add .
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### 6. Merge to Dev
```bash
git checkout dev
git merge feature/your-feature-name
git push origin dev
```

### 7. Monitor CI
- Check GitHub Actions: https://github.com/mottych/PurposePath_AI/actions
- If CI fails, diagnose and fix immediately
- DO NOT push again without local verification

---

## Dependency Management

### Adding New Dependencies

**ALWAYS check compatibility first:**

```powershell
# 1. Check current versions
pip list | Select-String "package-name"

# 2. Check what depends on it
pip show package-name

# 3. Add to requirements-dev.txt with compatible version
# Example:
new-package==1.2.3  # Compatible with langchain==0.3.13
```

### Current Version Matrix (as of 2025-01-28):
```
Python: 3.11+ 
boto3: 1.35.74
langchain: 0.3.13
langchain-core: (let pip resolve, ~=0.3.26)
langchain-aws: 0.2.9
pydantic: 2.10.4
httpx: 0.27.2
```

**DO NOT upgrade these without testing locally first!**

---

## Common Issues & Solutions

### Issue: StateGraph not subscriptable
```python
# ❌ Wrong
async def build_graph(self) -> StateGraph[dict[str, Any]]:

# ✅ Correct
from __future__ import annotations  # Add at top of file

async def build_graph(self) -> StateGraph[dict[str, Any]]:
```

### Issue: Missing type stubs
```
# Error: ModuleNotFoundError: No module named 'mypy_boto3_...'

# Fix: Add to requirements-dev.txt
boto3-stubs[service-name]==1.35.74
```

### Issue: Import order
```powershell
# Fix automatically
python -m ruff format coaching/ shared/
```

---

## CI/CD Pipeline

### What Gets Checked:
1. **Ruff Linting** - Code quality rules
2. **Ruff Formatting** - Code style consistency
3. **MyPy** - Type checking (warnings only)
4. **Pytest** - Unit tests with coverage
5. **Bandit** - Security scanning (informational)
6. **Safety** - Dependency vulnerabilities (informational)

### Success Criteria:
- ✅ All linting passes
- ✅ All formatting passes
- ✅ All tests pass
- ✅ No type errors (except documented)

---

## Quality Standards

**From global rules: ZERO ERRORS, ZERO WARNINGS, ZERO COMPROMISES**

1. Fix errors properly, don't mask them
2. Take as long as needed to do it right
3. Never add `# noqa` or `# type: ignore` without documentation
4. All tests must pass
5. Code must be production-ready

---

## Emergency Procedures

### If CI Fails:

1. **DO NOT push again immediately**
2. Pull the failed run logs:
   ```powershell
   gh run view <run-id> --log-failed
   ```
3. Reproduce locally:
   ```powershell
   .\scripts\test_local.ps1
   ```
4. Fix the root cause
5. Verify fix locally
6. Then push

### If Tests Fail Locally But Not in IDE:

1. Check Python version: `python --version`
2. Reinstall dependencies:
   ```powershell
   pip install -r coaching/requirements-dev.txt
   ```
3. Clear pytest cache:
   ```powershell
   pytest --cache-clear
   ```

---

## Tools & Commands

### Useful Commands:
```powershell
# Format code
python -m ruff format coaching/ shared/

# Auto-fix linting issues
python -m ruff check coaching/ shared/ --fix

# Run specific test
python -m pytest coaching/tests/unit/test_file.py::TestClass::test_method -v

# Check coverage
python -m pytest coaching/tests/unit --cov=coaching/src --cov-report=html

# View coverage report
start htmlcov/index.html
```

### GitHub CLI Commands:
```powershell
# List recent runs
gh run list --branch dev --limit 5

# Watch current run
gh run watch

# View failed run logs
gh run view <run-id> --log-failed
```

---

## Success Metrics

### Goal: 100% Successful Deployments

**Before this workflow:**
- 60+ failed deployments over 2 days
- 0% success rate
- ~5 hours wasted in CI

**After this workflow:**
- Expected: 95%+ success rate
- Most errors caught locally (< 30 seconds)
- CI only catches edge cases

---

## Next Steps

1. ✅ **Always run `.\scripts\test_local.ps1` before pushing**
2. ✅ **Fix all test failures (currently 68 remaining)**
3. ✅ **Set up pre-commit hooks** (optional but recommended)
4. ✅ **Document any new patterns** in this file

---

**Remember: Quality > Speed. Fix it right the first time.**
