# Architecture Standards

## Objective

Define mandatory architecture boundaries for `PurposePath_AI` services.

## Required Patterns

- Follow Clean Architecture with inward dependency flow.
- Keep domain layer independent from infrastructure frameworks.
- Use explicit contracts between application and infrastructure layers.
- Keep API layer as transport boundary with request/response translation only.

## Layer Rules

- Domain (`coaching/src/domain/`) contains business invariants and value objects.
- Application (`coaching/src/application/`) orchestrates use cases and workflows.
- Infrastructure (`coaching/src/infrastructure/`) implements persistence and external providers.
- API (`coaching/src/api/`) handles HTTP concerns, auth context, and DTO mapping.

## AI Service Boundaries

- Prompt/template retrieval and LLM provider access stay in infrastructure/application layers.
- Domain logic must not depend directly on Bedrock/OpenAI client code.
- Workflow orchestration state should be typed and validated.

## Multi-Tenant and Security Rules

- All data access paths must enforce tenant isolation.
- Request context and user context validation must occur at API boundaries.
- Secrets and environment configuration are externalized, never hardcoded.

## Cross References

- Coding implementation detail: `docs/local/guides/coding-standards.md`
- Execution workflow and quality gates: `docs/local/guides/development-guidelines.md`
- Shared workflow policy: `docs/shared/guides/workflow-governance.md`
- Shared deployment policy: `docs/shared/guides/deployment-standards.md`
