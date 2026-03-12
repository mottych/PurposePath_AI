---
agent: agent
---

# Resolve Issue (Reference Entrypoint)

Use canonical guidance from:

1. `#file:../copilot-instructions.md`
2. `docs/shared/guides/workflow-governance.md`
3. `docs/shared/guides/deployment-standards.md`
4. `docs/local/guides/development-guidelines.md`
5. `docs/local/guides/architecture-standards.md`
6. `docs/local/guides/coding-standards.md`
7. `docs/shared/Specifications/`

Manual fallback only when primary orchestration is unavailable:

1. Work from a feature/hotfix branch, never protected branches directly.
2. Confirm issue scope and relevant shared specifications.
3. Keep API/application/domain/infrastructure boundaries clean.
4. Run repository quality gates (ruff, mypy, pytest) before completion.
5. Update issue status with validation evidence.
