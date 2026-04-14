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

- Deployed OpenAPI/AsyncAPI endpoints are the API/interface contract source of truth.
- `docs/shared/Specifications/` documents are thin non-contract references for workflow, state, and operational semantics.
- If code and runtime contract endpoints diverge, default action is to align code and validate against the runtime endpoints.

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

1.1 Identify owning runtime contract endpoint
- HTTP contracts: `https://{api-host}/{service}/api/v1/openapi/v1.json`
- Async/event contracts: `https://{api-host}/admin/api/v1/contracts/asyncapi?lambda={scope}`
- AI coaching Lambda (PurposePath_AI, **dev only**): HTTP `https://{api-host}/coaching/api/v1/openapi/v1.json`, Swagger `https://{api-host}/coaching/api/v1/swagger`, AsyncAPI `https://{api-host}/coaching/api/v1/contracts/asyncapi` (optional `?lambda=coaching`)

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
  - Runtime contract endpoint reference(s).
  - Non-contract semantic guidance only.
- Enforce JSON naming convention from the shared API naming guide.
- Ensure examples are realistic and internally consistent.

4.1 Validate contracts from runtime endpoints
- Validate OpenAPI/AsyncAPI behavior against the live runtime endpoints for the affected environment after contract-affecting code changes.
- Do not duplicate endpoint request/response shape definitions in thin spec docs.

5. Cross-check with guardrails
- Validate against `.github/COPILOT_RULES.md`.
- If requirement/spec is ambiguous, stop and request clarification before implementation.

6. Link and index updates
- Update local section README/index when adding or moving files.
- If a document is superseded, note replacement target and date.

7. Validation and close-out
- Confirm implementation and tests align with the runtime contract endpoints.
- Include runtime endpoint references in issue/PR notes.
- Ensure repository contract guard workflows pass for runtime contract validation.

## Repository Enforcement (PurposePath_Api)

- Workflow(s): `.github/workflows/api-contract-spec-guard.yml` and related runtime contract validation pipelines.
- Enforcement behavior:
  - Fails when affected services do not expose valid runtime contract endpoints.
  - Validates required contract expectations for register idempotency and confirm-email status outcomes against the live Account OpenAPI endpoint.

## Minimum Checklist

- [ ] Correct spec file selected or created.
- [ ] Impact and compatibility documented.
- [ ] Runtime contract endpoints validated for affected services.
- [ ] Validation/error behavior represented in runtime contracts and verified.
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
