# Squad Local Reference

This folder stores a local snapshot of key upstream Squad documentation so this repository can:

- Review upgrade impact offline and in-code review.
- Keep implementation choices aligned with the latest Squad model.
- Preserve a local baseline for diffing across upgrades.

## Upstream Source

- Repository: https://github.com/bradygaster/squad
- Primary docs site: https://bradygaster.github.io/squad/

## Local Snapshot Files

- `upstream/README.md`
- `upstream/CHANGELOG.md`
- `upstream/sdk-first-mode.md`
- `upstream/migration.md`

## Update Procedure (on Squad upgrade)

1. Upgrade Squad CLI/SDK.
2. Run:
   - `pwsh scripts/utilities/Sync-SquadDocs.ps1`
3. Review diffs in `docs/shared/references/squad/upstream/`.
4. Validate local Squad health:
   - `squad build`
   - `squad doctor`
5. If behavior changed, update local governance/state docs accordingly.

## Validation Notes

- This is a reference mirror for governance decisions, not a replacement for upstream release notes.
- Always include upstream links in PR notes when adopting new Squad behavior.
