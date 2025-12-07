---
agent: agent
---

# General Development - Mandatory Workflow

## CRITICAL: Follow #file:../AI_WORKFLOW_CHECKLIST.md EXACTLY

### Core Principles

- ✅ **Quality over Speed** - No shortcuts or temporary solutions
- ✅ **Clean Architecture** - Follow DDD, CQRS, Clean Architecture principles
- ✅ **Feature Branches** - ALWAYS work in feature branches (never dev/main directly)
- ✅ **Zero Warnings** - Fix ALL warnings and errors before completing
- ✅ **All Tests Pass** - No exceptions, even for unrelated tests
- ✅ **Clean Up** - Remove all temporary code, files, and test data

### STEP 1: Branch Check (MANDATORY)

1. **Show current branch:** `git branch --show-current`
2. **IF on `dev` or `main`:**
   - STOP immediately
   - Create feature branch: `git checkout -b feature/{type}-{description}`
   - Examples:
     - `feature/issue-123-fix-login`
     - `feature/add-notifications`
     - `feature/refactor-auth-service`
3. **WAIT FOR USER APPROVAL** before any code changes

### Documentation & Standards

**Always reference:**
- API Specifications: #file:../../docs/Specifications/backend-integration-index.md
- Coding Standards: #file:../COPILOT_RULES.md
- Architecture Guide: #file:../DEVELOPMENT_GUIDELINES.md
- Workflow Checklist: #file:../AI_WORKFLOW_CHECKLIST.md
- General Instructions: #file:../copilot-instructions.md

### GitHub Issue Workflow

1. **Starting:**
   - Read issue completely
   - Add 'in-progress' label
   - Post comment with plan

2. **During Work:**
   - Update issue with progress comments
   - Keep 'in-progress' label active

3. **Completing:**
   - Post summary of changes
   - Update documentation if needed
   - Remove 'in-progress' label
   - Close with state_reason: 'completed'

### Testing Requirements

1. **Unit Tests:**
   - Domain logic (pure business rules)
   - No external dependencies

2. **Integration Tests:**
   - Repository implementations
   - External service interactions

3. **Validation:**
   - Build: `dotnet build --no-restore -v minimal`
   - Tests: `dotnet test --no-build --verbosity quiet`
   - ALL tests must pass (not just new ones)
   - Zero warnings, zero errors

### Commit & Merge Process

1. **Commit to Feature Branch:**
   - Format: `{type}(#{issue}): {description}`
   - Types: feat, fix, refactor, docs, test, chore
   - Include detailed bullet points

2. **Merge to Dev:**
   ```bash
   git checkout dev
   git merge --no-ff feature/{branch-name}
   git branch -d feature/{branch-name}
   git push origin dev
   ```

3. **Clean Up:**
   - Remove temporary files
   - Remove debug code
   - Remove test data

### Architecture Rules

**Domain Layer:**
- Pure business logic only
- No external dependencies
- Defines service contracts
- Works with domain models only

**Application Layer:**
- Implements domain contracts
- Orchestrates use cases
- NO DTO knowledge

**Infrastructure Layer:**
- Repository implementations
- External service calls
- AWS service abstractions

**API/Presentation Layer:**
- Owns all DTOs
- Handles DTO ↔ Domain conversion
- Calls application with domain models

### Critical Rules

- ❌ NO dictionaries or dynamic types
- ❌ NO primitive obsession (use value objects)
- ❌ NO DTOs in application/domain layers
- ❌ NO direct commits to dev/main (git hook blocks this)
- ❌ NO skipping tests
- ✅ GUID-based strongly-typed identifiers
- ✅ AutoMapper for all conversions
- ✅ FluentValidation for input validation
- ✅ MediatR for CQRS pattern

---

**When in doubt - ASK the user!**

**The git pre-commit hook will enforce feature branch workflow automatically.**
