# Dashboard API Specification

## Status

This specification has been reduced to a thin, non-contract layer as part of Epic #959.

## Canonical Contract Sources

All endpoint-level contract details are now exposed from the deployed runtime endpoint:
- `https://{api-host}/account/api/v1/openapi/v1.json`

Contract details include:
- Paths and HTTP methods
- Request/response schemas and examples
- Status codes and response descriptions
- Auth/security scheme declarations
- OpenAPI/AsyncAPI extensions

## Retained Scope

This document should only contain guidance that is not representable in OpenAPI/AsyncAPI, such as:
- Business workflow narratives
- State transition intent and operator procedures
- Cross-service sequencing notes
- Rollout, migration, and operational caveats

## Authoring Rule

Do not duplicate endpoint contract shapes in this document. Add/update contract-level API details in code and validate against the live runtime endpoint.
