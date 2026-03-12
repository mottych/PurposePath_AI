---
agent: agent
---

# Refactor Code (Reference Entrypoint)

Use canonical guidance from:

1. `#file:../copilot-instructions.md`
2. `docs/shared/guides/workflow-governance.md`
3. `docs/local/guides/development-guidelines.md`
4. `docs/local/guides/architecture-standards.md`
5. `docs/local/guides/coding-standards.md`

Manual fallback only when primary orchestration is unavailable:

1. Establish baseline tests before refactoring.
2. Keep behavior unchanged unless explicitly requested.
3. Refactor in small steps with continuous validation.
4. Preserve architecture and contract boundaries.
5. Run full quality gates before completion.
