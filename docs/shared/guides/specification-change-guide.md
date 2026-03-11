# Specification Change Guide

## Purpose

Define the standard process for adding, modifying, deprecating, and archiving API specifications in `docs/shared/Specifications/`.

This guide is shared across repositories and should remain repository-agnostic.

## Scope

Use this guide for:
- New endpoint specifications.
- Contract changes to existing endpoints.
- Clarifications to request/response fields, validation rules, or error structures.
- Deprecation and archive actions for superseded specifications.

## Source of Truth Rule

- Specifications in `docs/shared/Specifications/` are the API contract source of truth.
- Implementation must match approved specifications.
- If code and spec diverge, default action is to align code to spec.

## Change Types

- Additive change: new endpoint or optional field.
- Contract change: path/method/payload/validation/error contract modification.
- Clarification change: non-behavioral documentation clarifications.
- Deprecation change: endpoint/document replaced or retired.

## Required Workflow

1. Identify scope and owning spec file
- Select the correct document under `api-fe/`, `api-admin/`, `ai-fe/`, `ai-admin/`, or `integration/`.
- If no suitable file exists, create one and link it from the nearest index README.

2. Open or reference governing issue
- Track change in a GitHub issue.
- For contract changes, use a spec-change issue path and include impact summary.

3. Define impact before editing
- Consumer impact (web/admin/ai).
- Backward compatibility and migration path.
- Rollout and validation strategy.

4. Update specification content
- Maintain consistent structure:
  - Header and version/date context.
  - Endpoint list/index.
  - Endpoint details with request/response examples.
  - Validation rules and error responses.
- Enforce JSON naming convention from the shared API naming guide.
- Ensure examples are realistic and internally consistent.

5. Cross-check with guardrails
- Validate against `.github/COPILOT_RULES.md`.
- If requirement/spec is ambiguous, stop and request clarification before implementation.

6. Link and index updates
- Update local section README/index when adding or moving files.
- If a document is superseded, note replacement target and date.

7. Validation and close-out
- Confirm implementation and tests align with updated spec.
- Include spec references in issue/PR notes.

## Minimum Checklist

- [ ] Correct spec file selected or created.
- [ ] Impact and compatibility documented.
- [ ] Endpoint contract documented completely.
- [ ] Validation/error behavior documented.
- [ ] Section index/README updated.
- [ ] Superseded docs archived with pointer.
- [ ] Issue/PR includes spec links and validation evidence.

## Deprecation and Archive Rules

When retiring a spec document:
1. Move deprecated file under `docs/shared/Specifications/archive/`.
2. Add or update `docs/shared/Specifications/archive/README.md` entry.
3. Include superseding document link and retirement date.
4. Keep historical docs for traceability.

## Related References

- `docs/shared/Specifications/README.md`
- `.github/COPILOT_RULES.md`
- `docs/shared/guides/workflow-governance.md`
- `docs/shared/guides/api-naming-conventions.md`
