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

## Endpoint-Topic Mapping Baseline

- Maintain an explicit endpoint-to-topic mapping for AI execution endpoints.
- Avoid hardcoded topic routing in handlers; centralize mapping in configuration/registry.
- Ensure topic metadata covers prompt source, parameter schema, and response contract.
- Keep response serialization aligned to topic metadata instead of per-handler custom shaping.
- Conversation flows (start/resume/check) should remain topic-driven and validation-backed.

## Multi-Tenant and Security Rules

- All data access paths must enforce tenant isolation.
- Request context and user context validation must occur at API boundaries.
- Secrets and environment configuration are externalized, never hardcoded.

## Cross References

- Coding implementation detail: `docs/local/guides/coding-standards.md`
- Execution workflow and quality gates: `docs/local/guides/development-guidelines.md`
- Shared workflow policy: `docs/shared/guides/workflow-governance.md`
- Shared deployment policy: `docs/shared/guides/deployment-standards.md`
- Historical endpoint mapping analysis: `docs/local/archive/analysis/endpoint-topic-mapping-analysis-2025-12-02.md`
