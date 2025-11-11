# Development Scripts

This directory contains helper scripts for local development and quality checks.

## Pre-Commit Check

**Purpose:** Validate code quality before committing to prevent CI/CD failures.

**Usage:**

```powershell
.\scripts\pre-commit-check.ps1
```

**What it checks:**

1. ✅ Ruff linting (blocking)
2. ✅ Code formatting (blocking)
3. ⚠️  Type checking (informational only)

**When to run:**

- **Before every commit** to ensure code passes CI/CD checks
- After making code changes
- Before pushing to remote

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

## Workflow

**Recommended development workflow:**

```powershell
# 1. Make your code changes

# 2. Format the code
.\scripts\format-code.ps1

# 3. Run pre-commit checks
.\scripts\pre-commit-check.ps1

# 4. If checks pass, commit and push
git add .
git commit -m "your message"
git push origin dev
```

## CI/CD Pipeline

The GitHub Actions pipeline runs the same checks:

- Ruff linting
- Ruff formatting validation
- MyPy type checking
- Pytest unit tests (when applicable)

**Running these scripts locally ensures your commits will pass CI/CD checks on the first try.**
