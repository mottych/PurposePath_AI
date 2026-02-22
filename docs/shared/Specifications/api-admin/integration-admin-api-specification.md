# Integration Admin API Specification

**Service:** Admin Service  
**Base Path:** `/admin/api/v1/integrations`  
**Version:** 1.1  
**Last Updated:** February 19, 2026

## Overview

This specification defines admin-only integration endpoints for metadata synchronization and integration-definition management.

### Key Capabilities

- Synchronize available systems from CData
- Define catalog measure intent for SQL-template generation
- Define supported systems per catalog measure (`SystemMeasureConfig`)
- Define parameter metadata (including lookup metadata)
- Generate/persist generic MCP lookup SQL templates

### Out of Scope

- User-facing connection/integration/test endpoints
- Runtime execution endpoints

---

## Authentication

All endpoints require Admin authorization.

```http
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

---

## Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| POST | `/systems/sync` | Trigger systems metadata synchronization from CData |
| GET | `/systems` | List normalized systems catalog |
| GET | `/systems/sync-status` | Get sync job status/diagnostics |
| POST | `/catalog-measures/{catalogMeasureId}/intent` | Create/update measure intent prompt metadata |
| PUT | `/system-measure-configs` | Upsert supported-system definition for catalog measure |
| GET | `/system-measure-configs/{id}` | Get full system-measure config |
| POST | `/system-measure-configs/{id}/parameters` | Create/update parameter definitions |
| POST | `/system-measure-configs/{id}/parameters/{paramId}/lookup-sql/generate` | Generate/persist generic lookup SQL via MCP |

---

## Common Data Models

### IntegrationSystemCatalogItem

```typescript
interface IntegrationSystemCatalogItem {
  systemId: string;                              // UUID (internal)
  sourceSystemId: string;                        // provider-native ID
  code: string;                                  // stable key, e.g. 'salesforce'
  name: string;
  category: string;
  iconUrl?: string;
  isActive: boolean;
  syncedAtUtc: string;                           // ISO-8601 UTC
  createdAtUtc: string;
  updatedAtUtc: string;
}
```

### SystemMeasureConfigResponse

```typescript
interface SystemMeasureConfigResponse {
  id: string;                                    // UUID
  catalogMeasureId: string;                      // UUID
  systemId: string;                              // UUID
  isSupported: boolean;
  intentTemplateVersion: number;                 // >= 1
  updatedAtUtc: string;
  updatedBy: string;
  parameters: IntegrationParameterDefinition[];
}
```

### IntegrationParameterDefinition

```typescript
interface IntegrationParameterDefinition {
  parameterId: string;                           // UUID
  friendlyName: string;                          // max 80 chars
  sourceColumnName: string;                      // max 120 chars
  dataType: 'string' | 'number' | 'boolean' | 'date' | 'datetime';

  hasLookup: boolean;
  lookupValueKeyColumn?: string;
  lookupValueNameColumn?: string;
  lookupSqlTemplate?: string;

  isActive: boolean;
  sortOrder: number;                             // >= 0
}
```

### ApiResponse Envelope

```typescript
interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  message?: string | null;
  error?: string | null;
  code?: string | null;
  details?: unknown;
}
```

---

## Endpoint Details

### 1) Synchronize Systems Metadata

**POST** `/systems/sync`

Triggers provider metadata synchronization.

#### Request Body

```typescript
interface SyncSystemsRequest {
  providerCode: 'cdata';
  fullResync?: boolean;                          // default false
}
```

#### Response (202)

```json
{
  "success": true,
  "data": {
    "syncRunId": "6d4468d1-89ce-4996-a5ec-d0fcd1e6fa17",
    "providerCode": "cdata",
    "startedAtUtc": "2026-02-19T09:02:18Z",
    "status": "Running"
  }
}
```

#### Constraints

- Endpoint is idempotent for repeated trigger attempts within active run window.
- Upsert behavior must avoid duplicate systems.

---

### 2) List Systems Catalog

**GET** `/systems`

#### Query Parameters

```typescript
interface GetSystemsParams {
  providerCode?: 'cdata';
  category?: string;
  isActive?: boolean;
  page?: number;                                 // default 1
  limit?: number;                                // default 50, max 200
}
```

#### Response (200)

Returns `IntegrationSystemCatalogItem[]` with optional pagination metadata.

---

### 3) Get Sync Status

**GET** `/systems/sync-status`

#### Response (200)

```json
{
  "success": true,
  "data": {
    "lastRunId": "6d4468d1-89ce-4996-a5ec-d0fcd1e6fa17",
    "status": "Completed",
    "startedAtUtc": "2026-02-19T09:02:18Z",
    "completedAtUtc": "2026-02-19T09:02:43Z",
    "systemsUpserted": 62,
    "errorCode": null,
    "errorMessage": null
  }
}
```

---

### 4) Upsert Catalog Measure Intent

**POST** `/catalog-measures/{catalogMeasureId}/intent`

Creates/updates intent prompt metadata used to generate SQL templates.

#### Request Body

```typescript
interface UpsertCatalogMeasureIntentRequest {
  intentTemplate: string;                        // required, max 4000 chars
  promptNotes?: string;                          // max 4000 chars
  dataTypeScope: 'snapshot' | 'aggregate' | 'both';
  aggregationAware: boolean;
  versionComment?: string;                       // max 500 chars
}
```

#### Response (200)

```json
{
  "success": true,
  "data": {
    "catalogMeasureId": "af5d1450-b89a-4a9f-a4ad-f06144bf1a13",
    "intentTemplateVersion": 4,
    "updatedAtUtc": "2026-02-19T09:10:12Z"
  }
}
```

---

### 5) Upsert System Measure Config

**PUT** `/system-measure-configs`

#### Request Body

```typescript
interface UpsertSystemMeasureConfigRequest {
  id?: string;                                   // optional for create
  catalogMeasureId: string;                      // required UUID
  systemId: string;                              // required UUID
  isSupported: boolean;
}
```

#### Constraints

- Unique by (`catalogMeasureId`, `systemId`).
- `isSupported=false` marks config inactive for eligibility checks.

#### Response (200)

Returns `SystemMeasureConfigResponse`.

---

### 6) Get System Measure Config

**GET** `/system-measure-configs/{id}`

Returns configuration + parameters + lookup SQL metadata.

---

### 7) Upsert Parameter Definitions

**POST** `/system-measure-configs/{id}/parameters`

#### Request Body

```typescript
interface UpsertParameterDefinitionsRequest {
  parameters: Array<{
    parameterId?: string;
    friendlyName: string;                        // required, max 80
    sourceColumnName: string;                    // required, max 120
    dataType: 'string' | 'number' | 'boolean' | 'date' | 'datetime';
    hasLookup: boolean;
    lookupValueKeyColumn?: string;
    lookupValueNameColumn?: string;
    isActive?: boolean;
    sortOrder?: number;
  }>;
}
```

#### Validation Rules

- `friendlyName` and `sourceColumnName` are required.
- if `hasLookup=true`, both `lookupValueKeyColumn` and `lookupValueNameColumn` are required.
- parameter names must be unique per config.

---

### 8) Generate Lookup SQL via MCP

**POST** `/system-measure-configs/{id}/parameters/{paramId}/lookup-sql/generate`

Generates reusable lookup SQL template using MCP and persists it.

#### Request Body

```typescript
interface GenerateLookupSqlRequest {
  providerCode: 'cdata';
  dataDescription: string;                        // required, max 2000 chars
  tenantProviderContextId: string;                // required UUID
  overwriteExisting?: boolean;                    // default false
}
```

#### MCP Constraints (Critical)

Lookup SQL must be generic/reusable and generated with inputs including:
- data source
- tenant/subaccount context
- description of required data

#### Response (200)

```json
{
  "success": true,
  "data": {
    "parameterId": "10f5be08-c8c2-476c-ab18-ae7d2d2ecf1e",
    "lookupSqlTemplate": "SELECT Id AS value_key, Name AS value_name FROM Accounts ORDER BY Name",
    "generatedAtUtc": "2026-02-19T09:16:50Z",
    "generationSource": "MCP"
  }
}
```

---

## Error Responses

### Standard Error Envelope

```json
{
  "success": false,
  "data": null,
  "error": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "details": null
}
```

### Common Error Codes

- `SYNC_FAILED`
- `SYNC_ALREADY_RUNNING`
- `SYSTEM_NOT_FOUND`
- `CATALOG_MEASURE_NOT_FOUND`
- `SYSTEM_MEASURE_CONFIG_NOT_FOUND`
- `UNSUPPORTED_SYSTEM_MEASURE_COMBINATION`
- `INVALID_PARAMETER_DEFINITION`
- `LOOKUP_METADATA_REQUIRED`
- `MCP_LOOKUP_SQL_GENERATION_FAILED`
