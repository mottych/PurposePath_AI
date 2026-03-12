# Coding Standards

## Objective

Define implementation quality and coding conventions for AI services in this repository.

## Core Rules

- Favor readability, explicit typing, and maintainability.
- Prefer typed models over unstructured dictionaries at service boundaries.
- Keep business logic out of route handlers.
- Add/update tests for behavior changes.
- Resolve lint, type, and test failures before completion.

## Python and FastAPI Rules

- Use type hints on public functions and service interfaces.
- Use validated models for request/response payloads.
- Keep route handlers thin; delegate to application services.
- Use structured logging with contextual metadata.
- Avoid implicit side effects in domain/application services.

## AI and Prompt Handling Rules

- Validate prompt inputs and outputs before persisting or returning.
- Keep provider-specific logic behind adapter/service abstractions.
- Treat retry/fallback logic as explicit policy, not hidden behavior.

## Testing Rules

- Run unit tests for touched modules and required integration checks.
- Keep coverage at or above repository baseline targets.
- Include regression tests for defects and contract-impacting behavior.

## Code Hygiene

- Remove temporary debug code and dead paths.
- Keep imports organized and formatting consistent.
- Keep scripts and docs aligned with runtime behavior.

## Cross References

- Architecture constraints: `docs/local/guides/architecture-standards.md`
- Workflow and quality gates: `docs/local/guides/development-guidelines.md`
- Shared governance: `docs/shared/guides/workflow-governance.md`
