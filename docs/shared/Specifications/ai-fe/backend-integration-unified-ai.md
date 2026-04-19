# Unified AI Endpoint Backend Integration Specifications

**Version:** 2.8  
**Last Updated:** April 19, 2026  
**Service Base URL:** `{REACT_APP_COACHING_API_URL}`  
**Default (Localhost):** `http://localhost:8000`  
**Dev Environment:** `https://api.dev.purposepath.app/coaching/api/v1`

[<- Back to Specifications Index](../README.md)

---

## Revision Log

| Date | Version | Description |
|------|---------|-------------|
| 2026-04-19 | 2.8 | **Endpoint-First Contract Source of Truth:** Removed duplicated payload/topic/schema tables from this guide. Runtime OpenAPI and AsyncAPI endpoints are now canonical. Added explicit reference to `x-purposepath-topic-contracts` with `topicType` for both single-shot and conversation topics. |
| 2026-04-19 | 2.7 | Guided goal creation conversation topic (`goals`) added with structured result model. |
| 2026-02-05 | 2.6 | Session management overhaul (`/start`, `/resume`, `/session/check` behavior updates). |

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Endpoints](#core-endpoints)
4. [Runtime Contract Endpoints](#runtime-contract-endpoints)
5. [Payload Discovery Rules](#payload-discovery-rules)
6. [Non-Endpoint Guidance](#non-endpoint-guidance)
7. [Error Handling](#error-handling)
8. [Changelog](#changelog)

---

## Overview

The Unified AI service is **topic-centric**, not endpoint-centric. Clients send a topic identifier and the backend routes by topic type:

- `single_shot` topics -> `/ai/execute` or `/ai/execute-async`
- `conversation_coaching` topics -> `/ai/coaching/*`

Payload structures, available topics, and schema details are defined by runtime contract endpoints, not by static markdown tables in this file.

---

## Architecture

### Topic-Centric Routing

- Topic metadata is defined in registry/config sources.
- Endpoint handlers select execution path based on `topicType`.
- Runtime config and prompts are resolved at execution time.

### Runtime Data Sources

- Topic registry: topic identity/type/category and parameter references.
- DynamoDB runtime config: model/runtime tuning settings.
- Prompt storage: prompt templates used during execution.
- Enrichment services: context data fetched at runtime from configured providers.

---

## Core Endpoints

These are the primary integration endpoints:

- `POST /ai/execute`
- `POST /ai/execute-async`
- `GET /ai/jobs/{jobId}`
- `GET /ai/topics`
- `GET /ai/schemas/{schema_name}`
- `GET /ai/coaching/topics`
- `GET /ai/coaching/session/check`
- `POST /ai/coaching/start`
- `POST /ai/coaching/resume`
- `POST /ai/coaching/message`
- `GET /ai/coaching/message/{job_id}`
- `POST /ai/coaching/pause`
- `POST /ai/coaching/complete`
- `POST /ai/coaching/cancel`
- `GET /ai/coaching/session`
- `GET /ai/coaching/sessions`

Use runtime OpenAPI for authoritative request/response contracts.

---

## Runtime Contract Endpoints

Runtime contract endpoints are the single source of truth.

### OpenAPI (HTTP)

- Endpoint: `{BASE_URL}/openapi/v1.json`
- Includes: HTTP path operations, request/response bodies, examples, component schemas.

### Topic Payload Contract Index

- Location: top-level `x-purposepath-topic-contracts` in OpenAPI.
- Includes one entry per active topic with `topicType`.
- `topicType` values:
  - `single_shot`
  - `conversation_coaching`

Per-topic schema refs in the index:

- `single_shot`
  - `execute.parametersSchemaRef`
  - `execute.responseDataSchemaRef`
  - `executeAsync.activityDataSchemaRef`
- `conversation_coaching`
  - `conversation.startContextSchemaRef`
  - `conversation.resultDataSchemaRef`

### AsyncAPI (Events)

- Endpoint: `{BASE_URL}/contracts/asyncapi`
- Optional scope: `?lambda=coaching`
- Use this for event contracts in async orchestration and completion/failure flows.

---

## Payload Discovery Rules

Use these steps in clients and tooling:

1. Fetch `{BASE_URL}/openapi/v1.json`.
2. Read `x-purposepath-topic-contracts.topics[]`.
3. Route by `topicType`.
4. Resolve schema refs from `#/components/schemas/*` in that same OpenAPI document.
5. Use endpoint request examples from OpenAPI `paths` for canonical payload examples.

No payload/topic/schema tables in this guide should be treated as authoritative.

---

## Non-Endpoint Guidance

This section intentionally includes only information not fully encoded in endpoint schemas.

### Parameter Enrichment Semantics

Request payloads are enriched at runtime using configured source families:

- `REQUEST`
- `ONBOARDING`
- `GOAL`
- `GOALS`
- `MEASURE`
- `MEASURES`
- `ACTION`
- `ISSUE`
- `WEBSITE`
- `CONVERSATION`
- `COMPUTED`

Source membership and retrieval behavior are implementation-level concerns; endpoint payload shapes still come from OpenAPI schema refs.

### Integration Policy

- Treat OpenAPI and AsyncAPI as authoritative contracts.
- Treat this document as narrative/behavioral guidance only.
- Prefer generated clients or runtime schema resolution where possible.

---

## Error Handling

Canonical status codes and error bodies are defined in OpenAPI operation responses.

Client behavior guidance:

1. Check `success` first.
2. Treat `data` as nullable on failures.
3. Use `request_id` for diagnostics and support.
4. For async flows, combine HTTP polling contracts (OpenAPI) with event contracts (AsyncAPI).

---

## Changelog

### Version 2.8 (April 19, 2026)

- Removed duplicated topic, payload, and schema tables from this guide.
- Declared runtime OpenAPI and AsyncAPI endpoints as the single source of truth.
- Added explicit guidance for `x-purposepath-topic-contracts` and `topicType`-based routing.

### Version 2.7 (April 19, 2026)

- Added guided goal creation conversation topic (`goals`) with structured result model.

---

This document is maintained as integration guidance. Runtime contracts exposed by the service are authoritative.
