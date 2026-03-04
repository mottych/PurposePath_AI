# Integration Service API Specification (User App)

**Service:** Traction Service (User App Integration APIs)  
**Route Prefixes:** `/connections`, `/measure-integrations`  
**Version:** 1.2  
**Last Updated:** March 3, 2026

## Overview

This specification documents the **implemented user-facing integration APIs** used by the frontend in Settings and Measure flows.

This file intentionally reflects current runtime behavior in `PurposePath.Traction.Lambda` and excludes admin metadata-definition APIs.

### Contract Source of Truth

- Backend async Integration AI+CData event contracts are specified in [../integration/async-integration-ai-cdata-contracts.md](../../integration/async-integration-ai-cdata-contracts.md).
- This frontend spec owns UX-facing request/response behavior and client handling expectations.
- Backend event schema changes must be reflected in both docs in the same change set.

### Key Capabilities

- Connected systems list with status/diagnostics and measure counts
- Add-system bootstrap (provider subaccount + connection persistence)
- Measure integration eligibility/list/get/create/update
- Parameter lookup values from connected systems (`valueKey` + `valueName`)
- Snapshot/aggregate scheduling controls and frequency rules
- Save-gating behavior based on current tested-state rules

### Scope Notes

- `POST /measure-integrations/{integrationId}/test` is **not** currently exposed by the Traction user controller.
- Integration runtime test/config endpoints exist in `PurposePath.Integration.Lambda` and are not part of this FE user contract.
- Admin metadata-definition APIs are out-of-scope here (see `api-admin` specs).

---

## Authentication & Headers

```http
Authorization: Bearer {accessToken}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

All endpoints are tenant-scoped and require authenticated user context.

---

## Endpoint Summary

| Method | Endpoint | Description |
|---|---|---|
| GET | `/connections` | List connected systems with aggregate integration data |
| GET | `/connections/eligible-systems` | Systems user can add now based on eligible measures |
| POST | `/connections/bootstrap` | Ensure tenant-provider/subaccount bootstrap exists |
| POST | `/connections` | Persist system connection returned by provider flow |
| PATCH | `/connections/{connectionId}` | Edit connection display/settings details |
| POST | `/connections/{connectionId}/test` | Test connection and refresh health status |
| GET | `/connections/{connectionId}/measures` | List integrations under a connection |
| GET | `/measure-integrations/eligible-measures` | List measures eligible for integration for selected system |
| GET | `/measure-integrations/eligible` | Alias of eligible-measures endpoint |
| GET | `/measure-integrations/{integrationId}` | Get integration details for edit/view |
| POST | `/measure-integrations/parameter-lookup-values` | Fetch lookup options for a parameter |
| POST | `/measure-integrations` | Create integration definition |
| PUT | `/measure-integrations/{integrationId}` | Update integration definition |

---

## Common Data Models

### ConnectionSummaryResponse

```typescript
interface ConnectionSummaryResponse {
  connectionId: string;                        // UUID
  systemId: string;                            // UUID
  systemName: string;
  systemCategory?: string;
  systemIconUrl?: string;
  connectedMeasureCount: number;               // >= 0
  connectionStatus: 'Healthy' | 'Degraded' | 'Invalid' | 'Expired';
  lastHealthCheckAtUtc?: string;               // ISO-8601 UTC
  lastConnectionErrorCode?: string;
  lastConnectionErrorAtUtc?: string;           // ISO-8601 UTC
}
```

### MeasureIntegrationDefinitionResponse

```typescript
interface MeasureIntegrationDefinitionResponse {
  integrationId: string;
  measureId: string;
  connectionConfigurationId: string;
  isActive: boolean;
  testStatus: 'NotTested' | 'Tested' | 'Invalidated';
  testedAtUtc?: string;
  lastTestExecutionId?: string;
  testFingerprint?: string;
  testInvalidationReasonCode?: string;
  lastReadingAtUtc?: string;
  lastReadingStatus?: 'Success' | 'Failed';
  lastReadingReason?: string;
  dataCalculationMethod: 'PreviousPeriod' | 'MovingAverage';
  frequencyValue: number;
  frequencyUnit: 'Days' | 'Months';
  lagDaysAfterPeriodEnd: number;
  measureTimeZone: string;
  parameterValues: Record<string, IntegrationParameterValueResponse>;
}

interface IntegrationParameterValueResponse {
  isEnabled: boolean;
  value?: string;
  lookupKey?: string;
  lookupDisplayName?: string;
}
```

### EligibleMeasureForIntegrationResponse

```typescript
interface EligibleMeasureForIntegrationResponse {
  measureId: string;
  name: string;
  unit: string;
  dataType?: string;
  aggregationType?: string;
  aggregationPeriod?: string;
  aiQueryIntent?: string;
}
```

### ParameterLookupValues

```typescript
interface GetParameterLookupValuesRequest {
  connectionId: string;
  parameterId: string;
  systemMeasureConfigId?: string; // mutually exclusive with measureId+systemId
  measureId?: string;
  systemId?: string;
  search?: string;
  page?: number;                  // default 1, min 1
  pageSize?: number;              // default 50, min 1, max 200
}

interface ParameterLookupValuesResponse {
  parameterId: string;
  values: Array<{ valueKey: string; valueName: string }>;
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
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

### 1) List Connected Systems

**GET** `/connections`

Returns connected systems and top-level status for Settings list view.

#### Query Parameters

```typescript
interface GetConnectionsParams {
  includeMeasureCounts?: boolean;              // default: true
  includeDiagnostics?: boolean;                // default: true
}
```

#### Response (200)

```json
{
  "success": true,
  "data": [
    {
      "connectionId": "3d1c3f8d-b00d-4d1f-b634-40f814f9a70f",
      "systemId": "f93c4bb0-e4b3-4a26-a770-8142e31d0c12",
      "systemName": "Salesforce",
      "systemCategory": "CRM",
      "systemIconUrl": "https://cdn.purposepath.app/icons/salesforce.svg",
      "connectedMeasureCount": 4,
      "connectionStatus": "Healthy",
      "lastHealthCheckAtUtc": "2026-02-19T08:02:11Z"
    }
  ]
}
```

#### Constraints

- Returns only current tenant records.
- `connectedMeasureCount` includes active and disabled integrations.

---

### 2) List Eligible Systems for Add-System

**GET** `/connections/eligible-systems`

Returns systems that can currently be added, based on at least one eligible measure.

#### Response (200)

```json
{
  "success": true,
  "data": {
    "canAddSystem": true,
    "reasonIfDisabled": null,
    "systems": [
      {
        "systemId": "f93c4bb0-e4b3-4a26-a770-8142e31d0c12",
        "systemName": "Salesforce",
        "systemIconUrl": "https://cdn.purposepath.app/icons/salesforce.svg",
        "eligibleMeasureCount": 3
      }
    ]
  }
}
```

#### Constraints

- `canAddSystem=false` when no active quantitative measures linked to active goals are eligible.

---

### 3) Bootstrap Tenant Provider/Subaccount

**POST** `/connections/bootstrap`

Ensures tenant-provider bootstrap exists before starting provider connection flow.

#### Request Body

```typescript
interface BootstrapRequest {
  providerCode: 'cdata';
}
```

#### Response (200)

```json
{
  "success": true,
  "data": {
    "providerCode": "cdata",
    "tenantProviderAccountId": "5520a223-8981-40ec-abf3-df00d8765f4a",
    "subaccountCreated": true
  }
}
```

#### Constraints

- Idempotent: repeated calls return existing bootstrap without duplicates.

---

### 4) Create Connection

**POST** `/connections`

Persists a provider connection after user completes provider-hosted connect UX.

#### Request Body

```typescript
interface CreateConnectionRequest {
  systemId: string;                             // required UUID
  providerCode: 'cdata';
  externalConnectionId: string;                 // required
  workspaceContext?: string;
  displayName?: string;                         // max 120 chars
}
```

#### Response (201)

Returns `ConnectionSummaryResponse`.

#### Validation Rules

- `systemId` must reference active supported system.
- `externalConnectionId` required and non-empty.

---

### 4a) Update Connection

**PATCH** `/connections/{connectionId}`

Updates editable user metadata for a connection.

#### Request Body

```typescript
interface UpdateConnectionRequest {
  workspaceContext?: string;
  displayName?: string;
}
```

#### Response (200)

Returns `ConnectionSummaryResponse`.

#### Notes

- If `workspaceContext` is provided but external provider/reference is missing, update fails with code `EXTERNAL_CONNECTION_REFERENCE_MISSING`.
- Not found returns 404 with `INTEGRATION_CONNECTION_NOT_FOUND`.

---

### 5) Test Connection

**POST** `/connections/{connectionId}/test`

Runs connection health test and updates diagnostics.

#### Response (200)

```json
{
  "success": true,
  "data": {
    "connectionId": "3d1c3f8d-b00d-4d1f-b634-40f814f9a70f",
    "connectionStatus": "Healthy",
    "lastHealthCheckAtUtc": "2026-02-19T08:22:05Z",
    "errorCode": null
  }
}
```

---

### 6) List Measures under Connection

**GET** `/connections/{connectionId}/measures`

Used by expandable row in Connected Systems screen.

#### Response (200)

```typescript
interface ConnectionMeasureResponse {
  integrationId: string;
  measureId: string;
  measureName: string;
  isEnabled: boolean;
  lastReadingAtUtc?: string;
  lastReadingStatus?: string;
  lastReadingReason?: string;
}
```

---

### 7) List Eligible Measures for System

**GET** `/measure-integrations/eligible-measures?systemId={systemId}`

Alias supported: `GET /measure-integrations/eligible?systemId={systemId}`

Returns measures eligible for new integration under selected system.

#### Constraints

Eligible measure must be:
- active
- linked to at least one active goal
- catalog-based and supported by selected system
- not already connected to another system
- quantitative

#### Response (200)

Returns `EligibleMeasureForIntegrationResponse[]`.

---

### 8) Create Measure Integration

**POST** `/measure-integrations`

#### Request Body

```typescript
interface CreateMeasureIntegrationRequest {
  measureId: string;                              // required UUID
  connectionConfigurationId: string;              // required UUID
  dataCalculationMethod: 'previousPeriod' | 'movingAverage';
  frequencyValue: number;                         // integer > 0
  frequencyUnit: 'days' | 'months';
  lagDaysAfterPeriodEnd: number;                  // integer >= 0
  measureTimeZone: string;                        // IANA timezone
  isActive: boolean;
  testFingerprint?: string;
  parameterValues: Record<string, {
    isEnabled: boolean;
    value?: string;
    lookupKey?: string;
    lookupDisplayName?: string;
  }>;
}
```

#### Validation Rules

- Create currently requires successful test fingerprint in handler; missing fingerprint fails with `TEST_REQUIRED_BEFORE_CREATE`.
- `connectionConfigurationId` and `measureId` must be valid GUIDs.
- `dataCalculationMethod` and `frequencyUnit` must parse to known enum values.

#### Response (200)

Returns `MeasureIntegrationDefinitionResponse`.

---

### 9) Update Measure Integration

**PUT** `/measure-integrations/{integrationId}`

#### Request Body

```typescript
interface UpdateMeasureIntegrationRequest {
  connectionConfigurationId: string;
  dataCalculationMethod: 'previousPeriod' | 'movingAverage';
  frequencyValue: number;
  frequencyUnit: 'days' | 'months';
  lagDaysAfterPeriodEnd: number;
  measureTimeZone: string;
  isActive: boolean;
  testFingerprint?: string;
  parameterValues: Record<string, {
    isEnabled: boolean;
    value?: string;
    lookupKey?: string;
    lookupDisplayName?: string;
  }>;
}
```

#### Save-Gating Rules (Current Implementation)

- Template-affecting changes require `testFingerprint`, else fails with `RETEST_REQUIRED_FOR_TEMPLATE_CHANGES`.
- Template-affecting checks currently include:
  - connection change
  - parameter dictionary/value/lookup changes
  - calculation method changes
  - lag changes
  - timezone changes
- Frequency-only changes do not trigger retest.

#### Response (200)

Returns `MeasureIntegrationDefinitionResponse`.

---

### 10) Get Parameter Lookup Values

**POST** `/measure-integrations/parameter-lookup-values`

Returns selectable lookup key/name options for a parameter from connected system data.

#### Request Body

`GetParameterLookupValuesRequest` (see common data models).

#### Scope Rules

- Provide either:
  - `systemMeasureConfigId`, or
  - `measureId` + `systemId`
- Do not provide both scope modes together.

#### Response (200)

Returns `ParameterLookupValuesResponse`.

---

### 11) Get Integration Definition

**GET** `/measure-integrations/{integrationId}`

Returns full definition for edit/read views.

#### Response (200)

Returns `MeasureIntegrationDefinitionResponse`.

---

### 12) Not in Current User Contract

- `DELETE /measure-integrations/{integrationId}` is not currently exposed in `PurposePath.Traction.Lambda`.
- `POST /measure-integrations/{integrationId}/test` is not currently exposed in `PurposePath.Traction.Lambda`.
- Any FE use of runtime test endpoint must be explicitly routed/documented via separate Integration runtime contract.

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

- `INTEGRATION_CONNECTION_NOT_FOUND`
- `EXTERNAL_CONNECTION_REFERENCE_MISSING`
- `TEST_REQUIRED_BEFORE_CREATE`
- `RETEST_REQUIRED_FOR_TEMPLATE_CHANGES`
- `CONNECTION_INVALID`
- `PARAMETER_NOT_FOUND`
- `INVALID_LOOKUP_SCOPE`
- `INVALID_PAGINATION`
- `LOOKUP_NOT_CONFIGURED`
