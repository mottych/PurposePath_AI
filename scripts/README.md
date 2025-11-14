# Development Scripts

This directory contains helper scripts for local development and quality checks.

## 🚀 Quick Start

**First time setup:**

```powershell
# Install Git hooks to automatically catch errors before commits
.\scripts\install-git-hooks.ps1
```

**Regular workflow:**

```powershell
# Fix common issues automatically
.\scripts\quick-fix.ps1

# Run all quality checks
.\scripts\pre-commit-check.ps1
```

## Git Pre-Commit Hook

**Purpose:** Automatically validate code quality before each commit to prevent CI/CD failures.

**Installation:**

```powershell
.\scripts\install-git-hooks.ps1
```

**What it does:**

- Runs automatically before every `git commit`
- Blocks commits if linting or formatting errors are found
- Runs in "Quick mode" (skips tests for faster commits)
- Tests still run in CI/CD pipeline

**Bypass (not recommended):**

```bash
git commit --no-verify -m "your message"
```

## Pre-Commit Check

**Purpose:** Validate code quality manually before committing.

**Usage:**

```powershell
# Full checks (includes unit tests)
.\scripts\pre-commit-check.ps1

# Quick checks (skip tests)
.\scripts\pre-commit-check.ps1 -Quick
```

**What it checks:**

1. ✅ Ruff linting (blocking)
2. ✅ Code formatting (blocking)
3. ⚠️  Type checking (informational only)
4. ✅ Unit tests (blocking, unless -Quick)

**When to run:**

- **Before every commit** to ensure code passes CI/CD checks
- After making code changes
- Before pushing to remote
- When testing full validation including tests

## Quick Fix

**Purpose:** Automatically fix common linting and formatting issues.

**Usage:**

```powershell
.\scripts\quick-fix.ps1
```

**What it fixes:**

- Auto-fixes Ruff linting issues where possible
- Auto-formats all Python code
- Reports remaining issues that need manual fix

**When to run:**

- When pre-commit checks fail
- Before running validation
- After writing new code

## Format Code

**Purpose:** Auto-format all Python code to meet Ruff standards.

**Usage:**

```powershell
.\scripts\format-code.ps1
```

**What it does:**

- Formats all Python files in `coaching/` and `shared/` directories
- Applies consistent code style
- Fixes formatting issues automatically

**When to run:**

- Before running pre-commit checks
- After writing new code
- When pre-commit check reports formatting errors

## 📋 Complete Workflow

**Recommended development workflow:**

```powershell
# 1. Install Git hooks (first time only)
.\scripts\install-git-hooks.ps1

# 2. Make your code changes
# ... edit files ...

# 3. Quick fix common issues
.\scripts\quick-fix.ps1

# 4. Review changes
git diff

# 5. Commit (pre-commit hook runs automatically)
git add .
git commit -m "your message"

# 6. Push
git push origin dev
```

**If pre-commit hook blocks your commit:**

```powershell
# Fix issues automatically
.\scripts\quick-fix.ps1

# Run full validation with tests
.\scripts\pre-commit-check.ps1

# Try commit again
git commit -m "your message"
```

## 🔍 Available Scripts

| Script | Purpose | Auto-runs |
|--------|---------|-----------|
| `install-git-hooks.ps1` | Install pre-commit Git hook | No |
| `pre-commit-check.ps1` | Run all quality checks | Via Git hook |
| `quick-fix.ps1` | Auto-fix linting/formatting | No |
| `format-code.ps1` | Format Python code | No |
| `test_local.ps1` | Run tests quickly | No |

## CI/CD Pipeline

The GitHub Actions pipeline runs the same checks:

1. ✅ Ruff linting (must pass)
2. ✅ Ruff formatting validation (must pass)
3. ⚠️  MyPy type checking (warnings only)
4. ✅ Pytest unit tests (must pass)
5. ✅ Security scan (informational)

**Running these scripts locally ensures your commits will pass CI/CD checks on the first try.**

## Troubleshooting

**Pre-commit hook not running:**

```powershell
# Reinstall the hook
.\scripts\install-git-hooks.ps1
```

**Commit blocked by hook:**

```powershell
# Auto-fix issues
.\scripts\quick-fix.ps1

# Check what's still failing
.\scripts\pre-commit-check.ps1

# If urgent, bypass (not recommended)
git commit --no-verify
```

**Tests failing locally:**

```powershell
# Run tests with details
python -m pytest coaching/tests/unit -v

# Fix the failing tests
# Then run checks again
.\scripts\pre-commit-check.ps1
```

**Missing test dependencies:**

If you see "ModuleNotFoundError" when running tests locally:

```powershell
# Option 1: Install dependencies globally (not recommended)
pip install -r requirements.txt

# Option 2: Use a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Then run tests
python -m pytest coaching/tests/unit -v
```

**Note:** The pre-commit hook runs in "Quick mode" by default (no tests) because:

- Test dependencies may not be installed locally
- Tests are slower and would delay commits
- Tests run automatically in CI/CD with full environment

For full local validation including tests, run:

```powershell
.\scripts\pre-commit-check.ps1  # Runs full check with tests
