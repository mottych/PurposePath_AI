# Resolve GitHub Issue - Mandatory Workflow

## CRITICAL: Follow #file:../rules/cursorrules.mdc EXACTLY

### STEP 1: Issue Intake & Planning

- [ ] Make sure current branch is `dev`
- [ ] Sync `dev`: `git pull origin dev`
- [ ] Read the entire GitHub issue plus linked docs (requirements, design, API specs)
- [ ] Reference supporting files (e.g., `docs/Plans/`, `docs/Specifications/`, architecture guides)
- [ ] STOP!
    Announce action plan and **wait for user approval** before changes
   
### STEP 2: Branch Check (MANDATORY)

- [ ] Create branch: `git checkout -b feature/issue-{ISSUE}-{slug}`
- [ ] Show current branch: `git branch --show-current`
      - Example: `git checkout -b feature/issue-197-parameter-registry-refactoring`
- [ ] Add the `in-progress` label to the issue
- [ ] Post a comment to the issue summarizing:
      - Current understanding / acceptance criteria
      - Planned approach (modules, services, registries touched)
      - Testing + validation plan

### STEP 3: Execute the Work

- [ ] Implement changes within the Python + FastAPI stack:
      - Domain entities in `coaching/src/domain/entities/`
      - Value objects in `coaching/src/domain/value_objects/`
      - Ports in `coaching/src/domain/ports/`
      - Application services in `coaching/src/application/`
      - Infrastructure adapters in `coaching/src/infrastructure/`
      - API routes in `coaching/src/api/routes/`
      - Core types/constants in `coaching/src/core/`
- [ ] Follow Clean Architecture + DDD guidelines
- [ ] When running terminal commands, use flags to avoid interactive prompts. Prefer MCP tools if available.
- [ ] Use Pydantic models, NOT `dict[str, Any]` in domain layer
- [ ] Enforce tenant isolation on all data access
- [ ] Keep files manageable; extract helper services when logic grows
- [ ] Update docs/env variables when behavior or config requirements change
- [ ] Remove temporary code, debug logs, unused imports

### STEP 4: Testing & Validation

- [ ] Add/extend pytest test suites covering the new behavior
- [ ] Execute tests during development:
      ```powershell
      cd coaching && uv run pytest -k "test_name" -v
      ```
- [ ] Final verification:
      ```powershell
      # Linting
      python -m ruff check coaching/ shared/ --fix
      python -m ruff format coaching/ shared/
      
      # Type checking
      python -m mypy coaching/src shared/ --explicit-package-bases
      
      # All tests
      cd coaching && uv run pytest --cov=src
      ```
- [ ] OR use the pre-commit script:
      ```powershell
      .\scripts\pre-commit-check.ps1
      ```
- [ ] Fix every warning/error output by ruff, mypy, or pytest
- [ ] Perform manual API testing when possible (use uvicorn locally)

### STEP 5: Commit to Feature Branch

- [ ] `git add -A`
- [ ] Commit format: `{type}(#{issue}): {summary}` (feat, fix, refactor, docs, test, chore)
- [ ] Include concise bullet summary in commit body if multiple changes

### STEP 6: Merge & Cleanup

- [ ] Switch to dev: `git checkout dev`
- [ ] Pull latest changes: `git pull origin dev`
- [ ] Merge: `git merge --no-ff feature/issue-{NUMBER}-{description}`
- [ ] Resolve any conflicts if they arise
- [ ] Push to origin: `git push origin dev`

### STEP 7: Deployment

- [ ] Watch deployment on GitHub Actions
- [ ] Verify deployment success
- [ ] If deployment fails, investigate and fix issues on the feature branch and repeat STEP 6 and STEP 7
- [ ] After successful deployment, delete local/remote feature branches:
      ```powershell
      git branch -d feature/issue-{NUMBER}-{description}
      git push origin --delete feature/issue-{NUMBER}-{description}
      ```

### STEP 8: Close Issue

- [ ] Post summary comment to GitHub issue
- [ ] Remove 'in-progress' label
- [ ] Close issue with state_reason: 'completed'

---

**Non-negotiables:**
- ❌ Never commit directly to `dev`/`master`/`staging`
- ❌ Never skip ruff/mypy/pytest commands
- ❌ Never leave mock data, TODOs, or `dict[str, Any]` in domain
- ❌ Never skip tenant isolation checks
- ✅ Always document plan + validation steps in the issue
- ✅ Always keep instructions and docs in sync with the change
- ✅ Always use type hints and Pydantic models
- ✅ Always run pre-commit checks before merging