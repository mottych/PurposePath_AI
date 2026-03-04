# Resolve Production Issue - Mandatory Hotfix Workflow

## CRITICAL: Follow #file:../rules/cursorrules.mdc EXACTLY

### STEP 1: Prepare Hotfix Branch (MANDATORY)

#### Branch Setup
- [ ] Ensure clean working tree (starting from local `dev`)
- [ ] Fetch latest remote references: `git fetch origin`
- [ ] Create hotfix branch from remote master: `git checkout -b hotfix/issue-{ISSUE}-{slug} origin/master`
- [ ] Add `in-progress` label to the issue: `gh issue edit {ISSUE} --add-label in-progress`
- [ ] Keep implementation scoped only to production fix requirements
- [ ] Ensure preprod compatibility for config/deployment updates

---

### STEP 2: Issue Intake & Plan Confirmation

- [ ] Read the full issue, incident details, and any linked docs/runbooks
- [ ] Identify blast radius (service, API routes, infra, data, auth, tenant impact)
- [ ] Define rollback and validation strategy before coding
- [ ] Post issue comment with:
      - root-cause hypothesis
      - planned fix scope
      - preprod + production validation plan
- [ ] STOP! Announce plan and wait for user approval before changes

### STEP 3: Implement Hotfix (Scoped + Safe)

- [ ] Implement only the minimal safe fix for production behavior
- [ ] Follow Python + FastAPI clean architecture conventions:
      - Domain entities in `coaching/src/domain/entities/`
      - Value objects in `coaching/src/domain/value_objects/`
      - Ports in `coaching/src/domain/ports/`
      - Application services in `coaching/src/application/`
      - Infrastructure adapters in `coaching/src/infrastructure/`
      - API routes in `coaching/src/api/routes/`
      - Core types/constants in `coaching/src/core/`
- [ ] Use Pydantic models, not untyped `dict[str, Any]` in domain
- [ ] Preserve tenant isolation checks on all data access
- [ ] Update workflow/deployment checks when reliability is part of the incident
- [ ] Remove temporary code, debug logs, and dead code

### STEP 4: Validate on Hotfix Branch (Preprod First)

- [ ] Run lint/type/tests locally before push:
      ```powershell
      # Lint + format
      python -m ruff check coaching/ shared/ --fix
      python -m ruff format coaching/ shared/

      # Type checking
      python -m mypy coaching/src shared/ --explicit-package-bases

      # Tests
      cd coaching && uv run pytest --cov=src
      ```
- [ ] Push hotfix branch: `git push -u origin hotfix/issue-{ISSUE}-{slug}`
- [ ] Confirm preprod deployment workflow runs successfully
- [ ] Execute manual validation in preprod for the incident scenario
- [ ] If validation fails: fix on same hotfix branch and repeat this step

### STEP 5: Promote Hotfix to Production

- [ ] Open PR `hotfix/issue-{ISSUE}-{slug} -> master`
- [ ] Include incident context, root cause, and validation evidence in PR body
- [ ] Merge PR only after preprod validation is confirmed
- [ ] Watch production deployment workflow end-to-end
- [ ] Verify post-deploy checks:
      - Lambda/runtime state healthy (if applicable)
      - API health endpoint responsive
      - CORS preflight/critical route behavior validated

### STEP 6: Propagate Fix Downstream (MANDATORY)

- [ ] Open PR `master -> staging`, merge after checks pass
- [ ] Open PR `staging -> dev`, merge after checks pass
- [ ] Ensure all three branches now contain the hotfix commit(s)

### STEP 7: Close Incident + Cleanup

- [ ] Post closing summary on the issue with:
      - root cause
      - final fix
      - validation evidence (preprod + production)
      - follow-up actions (if any)
- [ ] Remove `in-progress` label
- [ ] Close issue with state_reason: `completed`
- [ ] Delete hotfix branches (local + remote) only after downstream merges:
      ```powershell
      git branch -d hotfix/issue-{ISSUE}-{slug}
      git push origin --delete hotfix/issue-{ISSUE}-{slug}
      ```

---

**Non-negotiables:**
- ❌ Never commit directly to `dev`/`staging`/`master`
- ❌ Never skip preprod validation before `hotfix -> master` merge
- ❌ Never leave workflow reliability gaps unverified for deployment incidents
- ❌ Never leave mock data, TODOs, or `dict[str, Any]` in domain
- ❌ Never skip tenant isolation checks
- ✅ Always keep scope to production incident requirements
- ✅ Always document root cause and validation evidence
- ✅ Always merge `master -> staging -> dev` after hotfix production release
- ✅ Always keep docs/config/workflows in sync with the fix
