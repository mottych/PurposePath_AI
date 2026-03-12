# PurposePath AI Solution Overview

## Purpose

`PurposePath_AI` is the AI services repository for PurposePath. It provides coaching-oriented APIs, domain workflows, and AI orchestration services deployed in AWS.

## Scope

This repository owns:

- AI coaching service implementation (Python + FastAPI).
- Domain/application/infrastructure layering for AI workflows.
- LLM orchestration and prompt processing.
- AI service deployment and runtime operations.

This repository does not own:

- Frontend UX implementation (`PurposePath_Web`).
- Cross-repo orchestration governance (`purposepath-orchestrator`).

## Core Components

- `coaching/src/domain/`: domain entities, value objects, and contracts.
- `coaching/src/application/`: use-case orchestration and handlers.
- `coaching/src/infrastructure/`: adapters, repositories, and providers.
- `coaching/src/api/`: FastAPI routes and API boundary concerns.
- `shared/`: shared utilities and schema assets.
- `coaching/pulumi/` and workflow files: service deployment automation.

## Canonical Standards

- Shared standards:
  - `docs/shared/guides/workflow-governance.md`
  - `docs/shared/guides/deployment-standards.md`
  - `docs/shared/guides/agent-operation-standard.md`
- Local standards:
  - `docs/local/guides/architecture-standards.md`
  - `docs/local/guides/coding-standards.md`
  - `docs/local/guides/development-guidelines.md`

## Decision Rule

When guidance conflicts:

1. Shared and local canonical guides win.
2. Local reference docs are secondary.
3. Archive docs are historical context only.
