---
agent: agent
---

# General Development (Reference Entrypoint)

Use canonical guidance from:

1. `#file:../copilot-instructions.md`
2. `docs/shared/guides/workflow-governance.md`
3. `docs/shared/guides/deployment-standards.md`
4. `docs/local/guides/development-guidelines.md`
5. `docs/local/guides/architecture-standards.md`
6. `docs/local/guides/coding-standards.md`
7. `docs/local/guides/reference/README.md`

Manual fallback only when primary orchestration is unavailable:

1. Confirm scope and required specifications first.
2. Keep layer responsibilities and tenant isolation intact.
3. Update docs when behavior or operational workflow changes.
4. Run repository quality gates before completion.
5. Record validation evidence in issue updates.
- ❌ NO skipping tests
- ✅ GUID-based strongly-typed identifiers
- ✅ AutoMapper for all conversions
- ✅ FluentValidation for input validation
- ✅ MediatR for CQRS pattern

---

**When in doubt - ASK the user!**

**The git pre-commit hook will enforce feature branch workflow automatically.**
