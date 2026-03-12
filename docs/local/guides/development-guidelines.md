# Development Guidelines

## Objective

Define contributor workflow for implementing and shipping changes in `PurposePath_AI`.

## Start-of-Work Checklist

1. Confirm issue scope and acceptance criteria.
2. Start from a feature/hotfix branch per shared workflow governance.
3. Identify impacted modules, workflows, and specifications.
4. Confirm environment and dependency prerequisites.

## Implementation Workflow

1. Plan the approach and expected validation steps.
2. Implement in small, reviewable commits by layer.
3. Keep API, application, domain, and infrastructure responsibilities separated.
4. Update tests and docs together with behavior changes.
5. Run full quality gates before completion.

## Validation Commands

Run required checks before merge:

- `python -m ruff check coaching/ shared/`
- `python -m ruff format --check coaching/ shared/`
- `python -m mypy coaching/src shared/ --explicit-package-bases`
- `python -m pytest coaching/tests/unit -v`

## Deployment and Runtime Expectations

- Deployment changes must follow shared deployment standards.
- Production-impacting changes require explicit validation evidence.
- Health and observability guidance should be reviewed for runtime updates.

## Documentation Rules

- Repository-specific guidance belongs in `docs/local/`.
- Cross-repo governance and specs belong in `docs/shared/`.
- When moving docs, update indexes and references in the same change.

## Cross References

- Shared workflow policy: `docs/shared/guides/workflow-governance.md`
- Shared deployment policy: `docs/shared/guides/deployment-standards.md`
- Local architecture standards: `docs/local/guides/architecture-standards.md`
- Local coding standards: `docs/local/guides/coding-standards.md`
