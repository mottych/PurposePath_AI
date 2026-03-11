# Shared Docs Boundary

## Purpose

`docs/shared/` contains cross-repository documentation that is synchronized by `.github/workflows/sync-shared-docs.yml`.

## What Belongs Here

- Cross-repo process guides and governance that should be identical in all repositories.
- Shared requirements and specifications consumed by multiple repositories.
- Canonical workflow and deployment policies that are repository-agnostic.

## Current Shared Canonical Guides

- `docs/shared/guides/workflow-governance.md`
- `docs/shared/guides/deployment-standards.md`
- `docs/shared/guides/agent-operation-standard.md`
- `docs/shared/guides/specification-change-guide.md`
- `docs/shared/guides/api-naming-conventions.md`

## Exclusions

Do not put repository-specific architecture, language/framework implementation rules, or service-local runbooks in `docs/shared/`.
Those belong in `docs/local/`.
