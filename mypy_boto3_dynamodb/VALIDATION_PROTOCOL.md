# Comprehensive Validation Protocol

## Critical Gaps Identified (Issues #85, #87, #88)

### Gap #1 (Issue #85): Subdirectory-Only Validation
**Problem**: Validations only checked subdirectories (coaching/, account/) but missed root-level Python files.
**Impact**: 52 errors in root Python scripts went undetected.

### Gap #2 (Issue #87): Missing Entire Modules  
**Problem**: Even "comprehensive" checks missed entire modules (shared/ directory with 478 errors).
**Impact**: 535 total errors across workspace went undetected.

### Gap #3 (Issue #88): Single-Tool Validation
**Problem**: Only running Ruff missed **type checking errors** that Pylance reports in VS Code.
**Impact**: False "All checks passed!" while VS Code showed Python errors.

### Root Causes
1. Commands like `cd coaching && ruff check src/` only validate one subdirectory
2. **Ruff only checks linting** - doesn't catch type safety issues
3. Missing Pylance (VS Code) and Mypy type checking in validation process

## Error Types and Tools

| Error Type | Tool | What It Checks | Priority |
|------------|------|----------------|----------|
| **Linting** | Ruff | Style, imports, syntax, code quality | HIGH |
| **Type Safety** | Pylance (VS Code) | Type annotations, unresolved imports, type mismatches | HIGH |
| **Type Checking** | Mypy | Static type analysis per service | HIGH |
| **Tests** | Pytest | Unit/integration test failures | HIGH |
| **Markdown** | markdownlint | Documentation formatting | LOW |
| **YAML** | VS Code | CloudFormation schema | LOW |

## MANDATORY: Multi-Tool Validation Process

**⚠️ CRITICAL RULE**: ALL tools must pass before closing any issue.

### Step 1: Ruff Linting (REQUIRED)
```powershell
# ✅ ALWAYS run from workspace root
cd c:\Projects\XBS\PurposePath\PurposePath_Api\pp_ai
python -m ruff check . --exclude=".venv,venv,__pycache__,.pytest_cache,htmlcov,mypy_boto3_dynamodb,stubs"

# ✅ Expected: "All checks passed!"
```

**Checks**: Style, imports, syntax, code quality across:
- Root-level Python files
- ALL service directories (coaching/, account/, traction/, stripe/)
- Shared modules
- Configuration files

### Step 2: Pylance Type Checking (REQUIRED)
```python
# Use VS Code get_errors tool
get_errors()  # Check ALL files

# Or check specific critical files
get_errors(filePaths=[
    "c:\\...\\shared\\dependencies\\typed_dependencies.py",
    "c:\\...\\shared\\examples\\type_usage_examples.py",
    "c:\\...\\shared\\models\\responses.py",
    "c:\\...\\shared\\repositories\\enhanced_repositories.py"
])

# ✅ Expected: "No errors found" for all Python files
```

**ALSO**: Manually check VS Code Problems panel (Ctrl+Shift+M)
- Filter by "Errors" only
- Verify ZERO Python errors shown
- **This is what users see - must be clean!**

### Step 3: Mypy Type Checking (REQUIRED)
```powershell
# Check each service individually
cd coaching
python -m mypy src/ --exclude="tests"

cd ..\account
python -m mypy src/ --exclude="tests"

cd ..\shared
python -m mypy . --exclude="tests,examples"

# ✅ Expected: "Success: no issues found" for each
```

### Step 4: Test Suite (REQUIRED)
```powershell
# Run all tests
cd c:\Projects\XBS\PurposePath\PurposePath_Api\pp_ai
uv run pytest tests/ -v

# ✅ Expected: All tests pass
```

### Step 5: Configuration Validation (REQUIRED)
```powershell
# Verify pyproject.toml has no duplicate keys or syntax errors
python -m ruff check --select I  # Check if ruff can parse config
```

## Pre-Issue-Closure Validation Steps

Before closing ANY GitHub issue, complete ALL steps:

### Step 1: Fix Validation
```powershell
# Apply auto-fixes
python -m ruff check . --fix --unsafe-fixes --exclude=".venv,venv,__pycache__"

# Verify fixes applied
python -m ruff check .
```

### Step 2: Type Checking
```powershell
# Check each service
cd coaching && python -m mypy src/
cd ..\account && python -m mypy src/
cd ..\shared && python -m mypy .
```

### Step 3: Test Suite
```powershell
# Run all tests
uv run pytest tests/ -v
```

### Step 4: Manual VS Code Inspection
- Open VS Code Problems panel (Ctrl+Shift+M)
- Filter by "Errors" only
- Check each file mentioned in the issue
- Verify ZERO errors in Problems panel

### Step 5: Documentation
```powershell
# Create validation report
echo "## Validation Results" > VALIDATION_REPORT.md
echo "- Ruff: $(python -m ruff check . | tail -1)" >> VALIDATION_REPORT.md
echo "- Tests: $(uv run pytest tests/ --co -q | wc -l) tests" >> VALIDATION_REPORT.md
```

## Issue Closure Checklist

- [ ] All root-level Python files checked
- [ ] All service directories validated
- [ ] Configuration files (pyproject.toml) verified
- [ ] `python -m ruff check .` returns "All checks passed!"
- [ ] VS Code Problems panel shows ZERO Python errors
- [ ] All tests pass
- [ ] GitHub issue updated with validation results
- [ ] No temporary files or debug code left behind

## Common Validation Mistakes to Avoid

### ❌ Mistake 1: Only checking subdirectories
```powershell
# WRONG - misses root files
cd coaching && python -m ruff check src/
```

### ✅ Correct: Check entire workspace
```powershell
# RIGHT - checks everything
cd c:\Projects\XBS\PurposePath\PurposePath_Api\pp_ai
python -m ruff check .
```

### ❌ Mistake 2: Ignoring pyproject.toml errors
```powershell
# Config errors silently break tools
# Always verify config is valid FIRST
```

### ✅ Correct: Validate config before running tools
```powershell
# Test if config parses correctly
python -c "import tomli; tomli.load(open('pyproject.toml', 'rb'))"
```

### ❌ Mistake 3: Relying only on automated tools
```powershell
# Tools can miss context-specific issues
```

### ✅ Correct: Combine automated + manual checks
```powershell
# 1. Run automated tools
# 2. Check VS Code Problems panel manually
# 3. Review file context in get_errors output
```

## Validation Tools Reference

### Ruff (Linting)
```powershell
# Basic check
python -m ruff check .

# Auto-fix safe issues
python -m ruff check . --fix

# Auto-fix all issues (including unsafe)
python -m ruff check . --fix --unsafe-fixes

# Check specific files
python -m ruff check file1.py file2.py
```

### Mypy (Type Checking)
```powershell
# Check with project config
python -m mypy src/

# Strict checking
python -m mypy src/ --strict

# Check specific file
python -m mypy path/to/file.py
```

### Get Errors (VS Code)
```python
# Check specific files
get_errors(filePaths=["path/to/file.py"])

# Check all errors in workspace
get_errors()
```

## Automated Validation Script

Create a validation script to run all checks:

```powershell
# validate_all.ps1
cd c:\Projects\XBS\PurposePath\PurposePath_Api\pp_ai

Write-Host "🔍 Validating Root Files..." -ForegroundColor Cyan
python -m ruff check *.py

Write-Host "`n🔍 Validating Coaching Service..." -ForegroundColor Cyan
cd coaching
python -m ruff check src/
python -m mypy src/

Write-Host "`n🔍 Validating Account Service..." -ForegroundColor Cyan
cd ..\account
python -m ruff check src/
python -m mypy src/

Write-Host "`n🔍 Running Tests..." -ForegroundColor Cyan
cd ..
uv run pytest tests/ -v --tb=short

Write-Host "`n✅ Validation Complete!" -ForegroundColor Green
```

## Integration with GitHub Workflow

### Before Creating Issue
1. Identify ALL affected files (including root level)
2. Document current error count
3. Create issue with complete file list

### During Issue Work
1. Run validation after each significant change
2. Update issue with progress
3. Document any new errors discovered

### Before Closing Issue
1. Complete full validation checklist
2. Post validation results to issue
3. Verify "Definition of Done" met
4. Only then close issue

## Contact & Questions

When encountering validation gaps or unclear errors:
1. Ask user for clarification
2. Document the gap in this protocol
3. Update validation procedures
4. Prevent future occurrences

**Remember**: Quality over speed. Zero errors means ZERO errors, not "close enough."
