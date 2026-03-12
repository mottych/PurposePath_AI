---
agent: agent
---

# Fix Bug (Reference Entrypoint)

Use canonical guidance from:

1. `#file:../copilot-instructions.md`
2. `docs/shared/guides/workflow-governance.md`
3. `docs/local/guides/development-guidelines.md`
4. `docs/local/guides/architecture-standards.md`
5. `docs/local/guides/coding-standards.md`

Manual fallback only when primary orchestration is unavailable:

1. Document root cause before applying code changes.
2. Apply minimal fix in the correct layer.
3. Add regression coverage for the bug path.
4. Run quality gates and verify no regressions.
5. Update issue status with fix and validation evidence.
