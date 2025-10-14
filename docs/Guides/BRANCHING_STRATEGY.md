# PurposePath AI Branching Strategy

**Last Updated**: October 8, 2025  
**Repository**: PurposePath_AI  
**Owner**: mottych

---

## Overview

This repository follows a **three-tier branching strategy** aligned with our deployment environments:

- **`master`** → Production environment
- **`staging`** → Staging environment
- **`dev`** → Development environment

---

## Branch Hierarchy

```
master (production)
  ↑
  PR & Deploy
  ↑
staging (staging environment)
  ↑
  PR & Deploy
  ↑
dev (development environment)
  ↑
  Merge when feature complete
  ↑
feature/* (feature branches)
```

---

## Branching Workflow

### 1. **Feature Development**

When starting new work:

```bash
# Ensure you're on the latest dev branch
git checkout dev
git pull origin dev

# Create a feature branch
git checkout -b feature/your-feature-name

# Work on your feature, commit regularly
git add .
git commit -m "feat: descriptive commit message"

# Push to remote for backup/collaboration
git push -u origin feature/your-feature-name
```

### 2. **Merging to Dev**

When feature is complete and tested:

```bash
# Ensure your feature branch is up to date with dev
git checkout dev
git pull origin dev
git checkout feature/your-feature-name
git merge dev

# Run tests to ensure everything works
pytest

# Merge to dev
git checkout dev
git merge feature/your-feature-name --no-ff

# Push to remote
git push origin dev

# Delete feature branch (optional)
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

### 3. **Promoting to Staging**

When dev has clean code and features aligned with frontend:

```bash
# Create a Pull Request from dev to staging on GitHub
# After PR review and approval:

git checkout staging
git pull origin staging
git merge dev --no-ff -m "chore: promote dev to staging"
git push origin staging

# Deploy to staging environment
# Run integration tests on staging
```

### 4. **Promoting to Production**

When staging is validated and ready:

```bash
# Create a Pull Request from staging to master on GitHub
# After PR review and approval:

git checkout master
git pull origin master
git merge staging --no-ff -m "chore: promote staging to production"
git push origin master

# Tag the release
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Deploy to production environment
```

---

## Branch Protection Rules (Recommended)

Configure these on GitHub:

### **master** (Production)
- ✅ Require pull request reviews before merging (2 approvals)
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Include administrators
- ✅ Require signed commits
- ✅ Do not allow force pushes
- ✅ Do not allow deletions

### **staging**
- ✅ Require pull request reviews before merging (1 approval)
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ✅ Do not allow force pushes

### **dev**
- ✅ Require status checks to pass before merging
- ⚠️ Allow force pushes (for rebasing during development)

---

## Commit Message Convention

Follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

**Examples:**
```bash
feat(coaching): implement AI coaching conversation workflow
fix(llm): resolve provider timeout handling
docs(api): update coaching endpoint documentation
test(workflows): add integration tests for analysis workflow
chore(deps): upgrade boto3 to latest version
```

---

## Emergency Hotfix Process

For critical production issues:

```bash
# Create hotfix branch from master
git checkout master
git pull origin master
git checkout -b hotfix/critical-bug-description

# Fix the issue
# Test thoroughly
# Commit with clear message

# Merge to master
git checkout master
git merge hotfix/critical-bug-description --no-ff
git push origin master

# Backport to staging
git checkout staging
git merge master
git push origin staging

# Backport to dev
git checkout dev
git merge staging
git push origin dev

# Delete hotfix branch
git branch -d hotfix/critical-bug-description
git push origin --delete hotfix/critical-bug-description
```

---

## Environment Alignment

| Branch    | Environment | URL                                      | Purpose                          |
|-----------|-------------|------------------------------------------|----------------------------------|
| `master`  | Production  | `https://ai.api.purposepath.com`        | Live production AI services      |
| `staging` | Staging     | `https://staging.ai.api.purposepath.com`| Pre-production validation        |
| `dev`     | Development | `https://dev.ai.api.purposepath.com`    | Active development testing       |

---

## Current Repository Status

**Branches:**
- ✅ `master` - Production (stable)
- ✅ `staging` - Staging (stable)
- ✅ `dev` - Development (active)

**Repository created**: October 8, 2025  
**Branching strategy implemented**: October 8, 2025  
**Status**: Clean slate - Python-based AI coaching microservices

---

## Quick Reference Commands

```bash
# Check current branch
git branch

# Switch branches
git checkout master|staging|dev

# Update current branch with remote
git pull origin $(git branch --show-current)

# Create feature branch from dev
git checkout dev && git pull && git checkout -b feature/my-feature

# Push current branch to remote
git push origin $(git branch --show-current)

# View all branches
git branch -a

# Delete local branch
git branch -d branch-name

# Delete remote branch
git push origin --delete branch-name
```

---

## Notes

- **Always branch from `dev`** for new features
- **Never commit directly to `master` or `staging`**
- **Always use Pull Requests** for staging and master merges
- **Run full test suite** before merging to any environment branch
- **Tag releases** on master for version tracking
- **Keep branches synchronized** by regularly merging up the chain

---

## Support

For questions about the branching strategy, contact the development team or refer to:
- [Git Workflow Documentation](./GIT_WORKFLOW.md)
- [Contributing Guidelines](../.github/DEVELOPMENT_GUIDELINES.md)
