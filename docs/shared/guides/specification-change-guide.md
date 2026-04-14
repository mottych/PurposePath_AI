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

- OpenAPI/AsyncAPI artifacts under `docs/contracts/` are the API/interface contract source of truth.
- `docs/shared/Specifications/` documents are thin non-contract references for workflow, state, and operational semantics.
- If code and contract artifacts diverge, default action is to align code and regenerate artifacts.

## Contract Strictness Principles

- Do not add tolerant API variants for out-of-spec caller behavior (for example alias query keys or alternate payload field names) unless explicitly approved through a spec-change path.
- Do not normalize malformed contract values into permissive defaults in API handlers (for example coercing invalid values to null to avoid contract-level failures) unless explicitly approved through a spec-change path.
- When a caller request shape is out of spec, fix the caller/source system to match the published contract instead of expanding backend tolerance.
- Do not introduce legacy or backward-compatibility branches by default for contract drift; use explicit approval and documented migration only when required.

## Change Types

- Additive change: new endpoint or optional field.
- Contract change: path/method/payload/validation/error contract modification.
- Clarification change: non-behavioral documentation clarifications.
- Deprecation change: endpoint/document replaced or retired.

## Required Workflow

1. Identify scope and owning spec file
- Select the correct document under `api-fe/`, `api-admin/`, `ai-fe/`, `ai-admin/`, or `integration/`.
- If no suitable file exists, create one and link it from the nearest index README.

1.1 Identify owning generated contract artifact
- HTTP contracts: `docs/contracts/openapi/*.openapi.json`
- Async/event contracts: `docs/contracts/asyncapi/*.yaml`

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
  - Contract artifact reference(s).
  - Non-contract semantic guidance only.
- Enforce JSON naming convention from the shared API naming guide.
- Ensure examples are realistic and internally consistent.

4.1 Regenerate contracts from code
- Regenerate OpenAPI/AsyncAPI artifacts under `docs/contracts/` after contract-affecting code changes.
- Do not duplicate endpoint request/response shape definitions in thin spec docs.

5. Cross-check with guardrails
- Validate against `.github/COPILOT_RULES.md`.
- If requirement/spec is ambiguous, stop and request clarification before implementation.

6. Link and index updates
- Update local section README/index when adding or moving files.
- If a document is superseded, note replacement target and date.

7. Validation and close-out
- Confirm implementation and tests align with generated contract artifacts.
- Include `docs/contracts` references in issue/PR notes.
- Ensure repository contract guard workflows pass for contract generation and validation.

## Repository Enforcement (PurposePath_Api)

- Workflow(s): `.github/workflows/api-contract-spec-guard.yml` and related contract validation pipelines.
- Enforcement behavior:
  - Fails when contract-affecting changes do not update/regenerate required contract artifacts.
  - Validates required contract expectations for register idempotency and confirm-email status outcomes.

## Minimum Checklist

- [ ] Correct spec file selected or created.
- [ ] Impact and compatibility documented.
- [ ] Generated contract artifacts updated/regenerated.
- [ ] Validation/error behavior represented in generated contracts and verified.
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
- `docs/shared/process/squad/workflow-governance.md`
- `docs/shared/guides/api-naming-conventions.md`
