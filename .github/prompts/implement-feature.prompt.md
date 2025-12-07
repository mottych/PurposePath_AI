---
agent: agent
---

# Implement New Feature - Mandatory Workflow

## CRITICAL: Follow #file:../AI_WORKFLOW_CHECKLIST.md EXACTLY

### STEP 1: Branch Check (MANDATORY)

1. Show current branch: `git branch --show-current`
2. **IF on `dev` or `main`:**
   - STOP immediately
   - Create feature branch: `git checkout -b feature/{brief-description}`
   - Example: `git checkout -b feature/add-user-notifications`
3. **WAIT FOR USER APPROVAL** before proceeding

### STEP 2: Architecture Planning

1. Review requirements with user
2. Follow Clean Architecture layers:
   - **Domain**: Pure business logic, entities, value objects
   - **Application**: Use cases, commands, queries, handlers
   - **Infrastructure**: Repositories, external services
   - **API**: Controllers, DTOs, mapping, CQRS using MediatR
3. Follow patterns in #file:../DEVELOPMENT_GUIDELINES.md
4. Check API specs in #file:../../docs/Specifications/backend-integration-index.md

### STEP 3: Implementation

1. Create domain models (entities, value objects)
2. Define repository interfaces (domain layer)
3. Implement application handlers (commands/queries)
4. Implement repositories (infrastructure layer)
5. Create API endpoints and DTOs (presentation layer)
6. Use AutoMapper for all conversions

### STEP 4: Testing

1. Create unit tests for domain logic
2. Create integration tests for repositories
3. Create API tests for endpoints
4. Build: `dotnet build --no-restore -v minimal`
5. Run all tests: `dotnet test --no-build --verbosity quiet`
6. Fix ALL warnings and errors

### STEP 5: Commit & Merge

1. Stage: `git add -A`
2. Commit: `feat: {description}`
3. Switch to dev: `git checkout dev`
4. Merge: `git merge --no-ff feature/{description}`
5. Delete branch: `git branch -d feature/{description}`
6. Push to origin: `git push origin dev`
7. Update documentation if needed
8. Delete temporary code, files, and test data


---

**Critical Rules:**
- ✅ Use GUID-based strongly-typed identifiers
- ✅ NO dictionaries or dynamic types
- ✅ DTOs only in presentation layer
- ✅ Domain services return NEW aggregate roots
- ✅ All tests must pass before merging
