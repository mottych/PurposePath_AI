# Shared/Local Classification - 2026-03-12

## Summary

This pass applied the shared/local documentation model in `PurposePath_AI`.

## Added Local Canonical Docs

- `docs/local/README.md`
- `docs/local/solution-overview.md`
- `docs/local/guides/architecture-standards.md`
- `docs/local/guides/coding-standards.md`
- `docs/local/guides/development-guidelines.md`
- `docs/local/guides/reference/README.md`
- `docs/local/process/README.md`
- `docs/local/archive/README.md`

## Moved as Active Local References

- Top-level operational references moved to `docs/local/guides/reference/`
- `docs/architecture/*` moved to `docs/local/guides/reference/architecture/`
- `docs/prompts/*` moved to `docs/local/guides/reference/prompts/`
- `docs/operations/*` moved to `docs/local/process/operations/`

## Archived as Historical

- `docs/Guides/*` -> `docs/local/archive/guides-legacy/`
- `docs/Status/*` -> `docs/local/archive/status/`
- `docs/issues/*` -> `docs/local/archive/issues/`
- `docs/DEVELOPMENT_WORKFLOW.md` -> `docs/local/archive/development-workflow-legacy.md`
- `docs/COPILOT_INSTRUCTIONS_UPDATE.md` -> `docs/local/archive/copilot-instructions-update-legacy.md`

## Notes

- Shared docs in `docs/shared/` remain canonical cross-repo artifacts.
- Any unresolved stale references in archive files are acceptable historical context.
