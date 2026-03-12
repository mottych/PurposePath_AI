# GitHub Copilot Prompt Files

This folder contains lightweight prompt entrypoints that route execution to canonical shared and local guides.
Prompt files intentionally avoid duplicating policy text.

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
**Purpose:** Route issue work to canonical workflow, architecture, coding, and spec guides.

### @implement-feature
**Purpose:** Route feature work to canonical implementation and specification guidance.

### @fix-bug
**Purpose:** Route defect work to canonical bug-fix and validation standards.

### @refactor
**Purpose:** Route refactoring to canonical architecture and quality boundaries.

### @Prompt Enhancement
**Purpose:** General routing prompt for mixed tasks.

## Common Features

All prompts route to canonical docs that enforce:
- ✅ Branch safety and issue workflow hygiene
- ✅ Quality gates and deployment controls
- ✅ Architecture and coding boundaries
- ✅ Shared specification alignment

## Backup Protection

Even if AI forgets workflow, the **git pre-commit hook** blocks direct commits to dev/main:

```
❌ ERROR: Direct commits to 'dev' are forbidden!
```

## Related Documentation

- `../copilot-instructions.md`
- `../../docs/shared/guides/workflow-governance.md`
- `../../docs/shared/guides/deployment-standards.md`
- `../../docs/local/guides/development-guidelines.md`
- `../../docs/local/guides/architecture-standards.md`
- `../../docs/local/guides/coding-standards.md`
- `../../docs/shared/Specifications/`

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
- Canonical docs must exist at referenced locations
- Git hook setup should still block direct protected-branch commits

---

**Remember:** When in doubt, these prompts enforce the right workflow automatically. Trust the system!
