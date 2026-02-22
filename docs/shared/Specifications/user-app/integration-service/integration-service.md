# Integration Service API Specification (User App)

**Service:** Integration Service  
**Base Path:** `/integration`  
**Version:** 1.1  
**Last Updated:** February 19, 2026

## Overview

The Integration Service API enables end-user integration workflows in Settings and Measure screens.  
This specification covers **user-facing** endpoints only (no admin metadata-definition endpoints).

### Key Capabilities

- Connected systems list with status/diagnostics and measure counts
- Add-system bootstrap (provider subaccount + connection persistence)
- Measure integration create/edit/delete with eligibility checks
- Snapshot/aggregate scheduling controls and frequency rules
- Parameter selection with optional lookup values (`valueKey` + `valueName`)
- Test-first lifecycle and save gating based on tested-state validity

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
| GET | `/measure-integrations/{integrationId}` | Get integration details for edit/view |
| POST | `/measure-integrations` | Create integration (save-gated by tested state) |
| PUT | `/measure-integrations/{integrationId}` | Update integration (save-gated by tested state rules) |
| DELETE | `/measure-integrations/{integrationId}` | Delete integration |
| POST | `/measure-integrations/{integrationId}/test` | Test retrieval only (no measure-data persistence) |

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

### MeasureIntegrationResponse

```typescript
interface MeasureIntegrationResponse {
  integrationId: string;                       // UUID
  measureId: string;                           // UUID
  measureName: string;
  connectionId: string;                        // UUID
  systemId: string;                            // UUID
  systemName: string;

  isEnabled: boolean;
  testStatus: 'NotTested' | 'Tested' | 'Invalidated';
  testedAtUtc?: string;
  testFingerprint?: string;

  measureType: 'quantitative';
  measureDataType: 'snapshot' | 'aggregate';
  aggregationType?: 'sum' | 'average' | 'count' | 'min' | 'max';
  aggregationPeriod?: 'day' | 'week' | 'month' | 'quarter' | 'year';
  measureIntent: string;

  dataCalculationMethod?: 'previousPeriod' | 'movingAverage';
  frequencyValue: number;                      // integer > 0
  frequencyUnit: 'days' | 'months';
  lagDaysAfterPeriodEnd?: number;              // integer >= 0
  measureTimeZone: string;                     // IANA timezone

  parameters: IntegrationParameterSelection[];

  lastReadingAtUtc?: string;
  lastReadingStatus?: 'Success' | 'Failed';
  lastReadingReason?: string;
}

interface IntegrationParameterSelection {
  parameterId: string;
  parameterName: string;
  sourceColumnName: string;
  dataType: 'string' | 'number' | 'boolean' | 'date' | 'datetime';
  enabled: boolean;
  selectedValueKey?: string;
  selectedValueName?: string;
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

Returns `MeasureIntegrationResponse[]` (list view projection).

---

### 7) List Eligible Measures for System

**GET** `/measure-integrations/eligible-measures?systemId={systemId}`

Returns measures eligible for new integration under selected system.

#### Constraints

Eligible measure must be:
- active
- linked to at least one active goal
- catalog-based and supported by selected system
- not already connected to another system
- quantitative

---

### 8) Create Measure Integration

**POST** `/measure-integrations`

#### Request Body

```typescript
interface CreateMeasureIntegrationRequest {
  measureId: string;                              // required UUID
  connectionId: string;                           // required UUID
  isEnabled: boolean;

  dataCalculationMethod?: 'previousPeriod' | 'movingAverage';
  frequencyValue: number;                         // integer > 0
  frequencyUnit: 'days' | 'months';
  lagDaysAfterPeriodEnd?: number;                 // integer >= 0
  measureTimeZone: string;                        // IANA timezone

  parameters: Array<{
    parameterId: string;
    enabled: boolean;
    selectedValueKey?: string;
    selectedValueName?: string;
  }>;

  testFingerprint: string;                        // required for create
}
```

#### Validation Rules

- Enabled parameters must include both `selectedValueKey` and `selectedValueName`.
- `lagDaysAfterPeriodEnd` required when `dataCalculationMethod=previousPeriod` for aggregate measures.
- Create is rejected without valid tested state/fingerprint.

#### Response (201)

Returns `MeasureIntegrationResponse`.

---

### 9) Update Measure Integration

**PUT** `/measure-integrations/{integrationId}`

Same payload model as create.

#### Save-Gating Rules

- Template-affecting changes require valid tested state before save:
  - parameter enable/disable
  - parameter value changes
  - calculation method changes
  - timezone changes
  - period/lag semantics changes
- Frequency-only changes do not invalidate tested state.

---

### 10) Test Measure Integration

**POST** `/measure-integrations/{integrationId}/test`

Runs retrieval path and returns computed value + execution metadata.  
Does **not** persist measure actuals/current measure value.

#### Response (200)

```json
{
  "success": true,
  "data": {
    "integrationId": "f8f8d8b7-81de-42f7-b689-c0d4b709bc3d",
    "executionId": "ea619bc1-f4ac-4d75-934b-73fc912af5f0",
    "success": true,
    "status": "Succeeded",
    "actualValue": 125.52,
    "measuredAtUtc": "2026-02-19T08:30:00Z",
    "windowStartUtc": "2026-01-01T00:00:00Z",
    "windowEndUtc": "2026-01-31T23:59:59Z",
    "dataSource": "CData",
    "errorCode": null,
    "errorMessage": null,
    "queryMetadata": {
      "templateKey": "templates/cdata/revenue/prompt.txt",
      "systemType": "CData",
      "connectionType": "ApiKey",
      "usesExternalReference": false,
      "externalProvider": null
    }
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

- `CONNECTION_NOT_FOUND`
- `SYSTEM_NOT_ELIGIBLE`
- `MEASURE_NOT_ELIGIBLE`
- `INTEGRATION_NOT_FOUND`
- `ENABLED_PARAMETER_VALUE_REQUIRED`
- `INVALID_TIMEZONE`
- `INVALID_CALCULATION_CONFIGURATION`
- `TEST_REQUIRED_BEFORE_SAVE`
- `TEST_FINGERPRINT_MISMATCH`
- `CONNECTION_TEST_FAILED`
- `EXECUTION_FAILED`
