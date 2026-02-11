# GitHub Copilot Prompt Files

This folder contains workflow prompt files that can be invoked directly in GitHub Copilot Chat.

## Usage

In GitHub Copilot Chat, use `@` to invoke prompt files:

```markdown
@resolve-issue #290
@implement-feature add user notifications  
@fix-bug null reference in login
@refactor user-service
```

## Available Prompts

### @resolve-issue
**Purpose:** Fix GitHub issues following complete workflow  
**Usage:** `@resolve-issue #{issue-number}`  
**Example:** `@resolve-issue #290`

**Enforces:**
- Branch check (creates feature branch if needed)
- Waits for user approval before changes
- Follows Clean Architecture & DDD patterns
- Runs all tests (must pass)
- Commits to feature branch only
- Merges to dev and deletes feature branch
- Closes GitHub issue with summary

### @implement-feature
**Purpose:** Add new features following Clean Architecture  
**Usage:** `@implement-feature {description}`  
**Example:** `@implement-feature add email notifications`

**Enforces:**
- Architecture planning (domain → application → infrastructure → API)
- GUID-based strongly-typed identifiers
- No dictionaries or dynamic types
- DTOs only in presentation layer
- Complete test coverage

### @fix-bug
**Purpose:** Fix bugs with root cause analysis  
**Usage:** `@fix-bug {description}`  
**Example:** `@fix-bug null reference in user service`

**Enforces:**
- Root cause analysis before fix
- Regression test creation
- Minimal targeted fix (no over-engineering)
- Maintains API contracts
- All existing tests must still pass

### @refactor
**Purpose:** Refactor code while preserving behavior  
**Usage:** `@refactor {component-name}`  
**Example:** `@refactor user-service`

**Enforces:**
- Tests must pass BEFORE refactoring starts
- Behavior remains identical (no functional changes)
- Tests must pass AFTER refactoring completes
- Incremental changes with continuous validation

### @Prompt Enhancement
**Purpose:** General development workflow  
**Usage:** `@Prompt Enhancement`

**Enforces:**
- Quality over speed
- Feature branch workflow
- Zero warnings/errors policy
- Complete testing requirements

## Common Features

All prompts enforce:
- ✅ **Branch Check**: Must be on feature branch (not dev/main)
- ✅ **Approval Gate**: Waits for user approval before code changes
- ✅ **Workflow Compliance**: Follows `AI_WORKFLOW_CHECKLIST.md`
- ✅ **Testing Requirements**: All tests must pass
- ✅ **Clean Build**: Zero warnings, zero errors
- ✅ **Proper Merge**: Feature branch → dev → delete feature branch

## Backup Protection

Even if AI forgets workflow, the **git pre-commit hook** blocks direct commits to dev/main:

```
❌ ERROR: Direct commits to 'dev' are forbidden!
```

## Related Documentation

- **AI_WORKFLOW_CHECKLIST.md** - Mandatory workflow steps
- **AI_PROMPT_TEMPLATES.md** - Copy-paste templates (fallback)
- **README_AI_ENFORCEMENT.md** - Complete enforcement system docs
- **QUICK_REFERENCE.md** - One-page cheat sheet
- **COPILOT_RULES.md** - API specification compliance rules
- **DEVELOPMENT_GUIDELINES.md** - Clean Architecture & DDD guide

## Technical Details

**Location:** `.github/prompts/`  
**Format:** Markdown files with `.prompt.md` extension  
**YAML Frontmatter:** `agent: agent`  
**File References:** Use `#file:../FILENAME.md` for cross-references  

## Troubleshooting

**Prompt not appearing in chat?**
- Ensure file has `.prompt.md` extension
- Check YAML frontmatter is correct: `agent: agent`
- Restart VS Code to refresh prompt index

**Prompt not enforcing workflow?**
- File references must be correct (relative paths)
- `AI_WORKFLOW_CHECKLIST.md` must exist
- Git hook must be installed (see `GIT_HOOKS_SETUP.md`)

---

**Remember:** When in doubt, these prompts enforce the right workflow automatically. Trust the system!
