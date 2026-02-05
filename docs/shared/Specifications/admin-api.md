# Admin API Specification

**Version:** 1.3  
**Status:** In Progress - Audit Logs Pending Implementation  
**Last Updated:** February 5, 2026  
**Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`

---

## Overview

The Admin API provides administrative capabilities for managing user subscriptions, trial extensions, discount codes, tenant ownership, tenant people, system settings, and audit logs.

**Authentication Required:** Admin role (JWT with "Admin" role claim)

**Covered Endpoints:**
- Email Template Management (9 endpoints)
- Audit Log Access (4 endpoints)
- System Settings Management (6 endpoints)
- Tenant Management (4 endpoints)
- Subscriber Management (2 endpoints)
- Trial Management (2 endpoints)
- Discount Code Management (7 endpoints)

---

## Admin Email Template Management Endpoints

These endpoints manage transactional email templates used by the platform.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `Content-Type: application/json`

---

### GET /admin/api/v1/email-templates

List email templates with pagination and optional filtering.

**Query Parameters:**

- `page` (integer, optional) - Page number (1-based, default: 1)
- `pageSize` (integer, optional) - Items per page (default: 20, max: 100)
- `category` (string, optional) - Filter by category
- `isActive` (boolean, optional) - Filter by active status

**Response (200 OK):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Welcome Email",
      "subject": "Welcome Email",
      "description": "Welcome new users",
      "category": "welcome",
      "language": "en",
      "isActive": true,
      "isDefault": false,
      "usageCount": 12,
      "lastUsed": "2026-01-20T14:45:00Z",
      "createdAt": "2026-01-01T10:00:00Z",
      "updatedAt": "2026-01-10T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalCount": 45,
    "totalPages": 3
  }
}
```

**Status Codes:**

- `200 OK` - Templates retrieved successfully
- `400 Bad Request` - Invalid pagination parameters
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.ListTemplates()`
- Query: `ListEmailTemplatesQuery`
- Handler: `ListEmailTemplatesQueryHandler`

---

### GET /admin/api/v1/email-templates/{id}

Get a single email template by ID.

**Path Parameters:**

- `id` (string, GUID) - Email template ID

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Welcome Email",
  "subject": "Welcome Email",
  "description": "Welcome new users",
  "category": "welcome",
  "language": "en",
  "htmlContent": "<h1>Welcome</h1>",
  "textContent": "Welcome",
  "variables": [
    {
      "name": "UserName",
      "description": "Recipient name",
      "type": "string",
      "required": true,
      "defaultValue": null,
      "example": null,
      "syntaxHint": "@Model.UserName"
    }
  ],
  "isActive": true,
  "isDefault": false,
  "lastUsed": "2026-01-20T14:45:00Z",
  "usageCount": 12,
  "createdAt": "2026-01-01T10:00:00Z",
  "updatedAt": "2026-01-10T10:00:00Z",
  "createdBy": "admin-user-id",
  "metadata": {
    "openRate": 0,
    "clickRate": 0,
    "bounceRate": 0,
    "lastPerformanceUpdate": null,
    "tags": ["onboarding"],
    "notes": null
  }
}
```

**Status Codes:**

- `200 OK` - Template retrieved successfully
- `404 Not Found` - Template not found
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.GetTemplate()`
- Query: `GetEmailTemplateQuery`
- Handler: `GetEmailTemplateQueryHandler`

---

### POST /admin/api/v1/email-templates

Create a new email template.

**Request:**

```json
{
  "name": "Welcome Email",
  "subject": "Welcome Email",
  "description": "Welcome new users",
  "category": "welcome",
  "language": "en",
  "htmlContent": "<h1>Welcome @Model.UserName</h1>",
  "textContent": "Welcome @Model.UserName",
  "variables": [
    {
      "name": "UserName",
      "description": "Recipient name",
      "type": "string",
      "required": true,
      "defaultValue": null,
      "example": null,
      "syntaxHint": "@Model.UserName"
    }
  ],
  "isActive": true,
  "isDefault": false,
  "tags": ["onboarding"],
  "notes": null
}
```

**Response (201 Created):**

Returns the created template in the same shape as GET by ID.

**Notes (current implementation):**

- `subject` is accepted but ignored; response `subject` uses the template name.
- `language`, `isActive`, `isDefault`, and `notes` are accepted but currently ignored.

**Status Codes:**

- `201 Created` - Template created successfully
- `400 Bad Request` - Validation error (invalid category, duplicate name, etc.)
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.CreateTemplate()`
- Command: `CreateEmailTemplateCommand`
- Handler: `CreateEmailTemplateCommandHandler`

---

### PATCH /admin/api/v1/email-templates/{id}

Update an existing email template (partial update supported).

**Path Parameters:**

- `id` (string, GUID) - Email template ID

**Request:**

```json
{
  "name": "Welcome Email (Updated)",
  "description": "Updated description",
  "category": "welcome",
  "htmlContent": "<h1>Updated</h1>",
  "textContent": "Updated",
  "variables": [
    {
      "name": "UserName",
      "description": "Recipient name",
      "type": "string",
      "required": true,
      "defaultValue": null,
      "example": null,
      "syntaxHint": "@Model.UserName"
    }
  ],
  "tags": ["onboarding"]
}
```

**Response (200 OK):**

Returns the updated template in the same shape as GET by ID.

**Notes (current implementation):**

- `subject`, `language`, `isActive`, `isDefault`, and `notes` are accepted but currently ignored.

**Status Codes:**

- `200 OK` - Template updated successfully
- `400 Bad Request` - Validation error
- `404 Not Found` - Template not found
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.UpdateTemplate()`
- Command: `UpdateEmailTemplateCommand`
- Handler: `UpdateEmailTemplateCommandHandler`

---

### POST /admin/api/v1/email-templates/{id}/clone

Clone an existing email template.

**Path Parameters:**

- `id` (string, GUID) - Email template ID

**Request:**

```json
{
  "name": "Welcome Email (Copy)",
  "description": "Optional description",
  "language": "en"
}
```

**Response (201 Created):**

Returns the cloned template in the same shape as GET by ID.

**Notes (current implementation):**

- Only `name` is used. `description` and `language` are accepted but ignored.

**Status Codes:**

- `201 Created` - Template cloned successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.CloneTemplate()`
- Command: `CloneEmailTemplateCommand`
- Handler: `CloneEmailTemplateCommandHandler`

---

### POST /admin/api/v1/email-templates/{id}/preview

Generate a preview of the template with provided variables.

**Path Parameters:**

- `id` (string, GUID) - Email template ID

**Request:**

```json
{
  "variables": { "UserName": "Jane" },
  "format": "both"
}
```

**Response (200 OK):**

```json
{
  "subject": "Preview",
  "htmlContent": "<h1>Welcome Jane</h1>",
  "textContent": "Welcome Jane",
  "variables": { "UserName": "Jane" },
  "previewUrl": null
}
```

**Notes (current implementation):**

- `subject` is a placeholder (`"Preview"`).
- If `format` is `html`, `textContent` is `null`. If `format` is `text`, `htmlContent` is `null`.

**Status Codes:**

- `200 OK` - Preview generated successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.PreviewTemplate()`
- Command: `PreviewEmailTemplateCommand`
- Handler: `PreviewEmailTemplateCommandHandler`

---

### POST /admin/api/v1/email-templates/{id}/test

Send a test email using the specified template.

**Path Parameters:**

- `id` (string, GUID) - Email template ID

**Request:**

```json
{
  "toEmail": "test@example.com",
  "variables": { "UserName": "Jane" },
  "fromName": "PurposePath",
  "fromEmail": "noreply@purposepath.app"
}
```

**Response (200 OK):**

```json
{
  "sent": true,
  "messageId": "0000000000000000-000000",
  "to": "test@example.com"
}
```

**Notes (current implementation):**

- `fromName` and `fromEmail` are accepted but currently ignored.

**Status Codes:**

- `200 OK` - Test email sent
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.TestTemplate()`
- Command: `TestEmailTemplateCommand`
- Handler: `TestEmailTemplateCommandHandler`

---

### GET /admin/api/v1/email-templates/{id}/analytics

Get usage analytics for a template.

**Path Parameters:**

- `id` (string, GUID) - Email template ID

**Query Parameters:**

- `period` (string, optional) - "day", "week", "month", "year" (default: "month")
- `startDate` (string, optional) - ISO 8601 timestamp
- `endDate` (string, optional) - ISO 8601 timestamp

**Response (200 OK):**

```json
{
  "templateId": "550e8400-e29b-41d4-a716-446655440000",
  "templateName": "Analytics Coming Soon",
  "period": {
    "start": "2026-01-01T00:00:00Z",
    "end": "2026-01-31T23:59:59Z"
  },
  "metrics": {
    "sent": 0,
    "delivered": 0,
    "opened": 0,
    "clicked": 0,
    "bounced": 0,
    "unsubscribed": 0
  },
  "rates": {
    "deliveryRate": 0,
    "openRate": 0,
    "clickRate": 0,
    "bounceRate": 0,
    "unsubscribeRate": 0
  },
  "timeline": []
}
```

**Notes (current implementation):**

- Analytics are placeholders until tracking is implemented.

**Status Codes:**

- `200 OK` - Analytics retrieved successfully
- `404 Not Found` - Template not found
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.GetAnalytics()`
- Query: `GetEmailTemplateAnalyticsQuery`
- Handler: `GetEmailTemplateAnalyticsQueryHandler`

---

### GET /admin/api/v1/email-templates/categories

Get available email template categories with counts.

**Response (200 OK):**

```json
{
  "categories": [
    {
      "name": "welcome",
      "description": "Welcome and onboarding emails",
      "templateCount": 3,
      "requiredVariables": []
    }
  ]
}
```

**Status Codes:**

- `200 OK` - Categories retrieved successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.GetCategories()`
- Query: `GetEmailTemplateCategoriesQuery`
- Handler: `GetEmailTemplateCategoriesQueryHandler`

---

### DELETE /admin/api/v1/email-templates/{id}

Delete an email template (soft delete).

**Path Parameters:**

- `id` (string, GUID) - Email template ID

**Response:**

- `204 No Content`

**Status Codes:**

- `204 No Content` - Template deleted successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `EmailTemplatesController.DeleteTemplate()`
- Command: `DeleteEmailTemplateCommand`
- Handler: `DeleteEmailTemplateCommandHandler`

---

## Admin Audit Log Endpoints

These endpoints provide access to audit trail data for administrative actions and system operations. Audit logs are immutable records used for compliance, security monitoring, and troubleshooting.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `Content-Type: application/json`

---

### GET /admin/api/v1/audit-logs

List audit logs with pagination and comprehensive filtering options.

**Query Parameters (all optional):**

- `adminEmail` (string, optional) - Filter by admin email who performed the action
- `actionType` (string, optional) - Filter by action type (e.g., "USER_CREATED", "SUBSCRIPTION_CHANGED")
- `tenantId` (string, GUID, optional) - Filter by affected tenant ID
- `startDate` (string, ISO 8601, optional) - Start date for audit log entries
- `endDate` (string, ISO 8601, optional) - End date for audit log entries
- `page` (integer, optional) - Page number (1-based, default: 1)
- `pageSize` (integer, optional) - Items per page (default: 50, max: 100)

**Response (200 OK):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "adminEmail": "admin@example.com",
      "action": "USER_UPDATED",
      "targetType": "user",
      "targetId": "user-123",
      "tenantId": "tenant-456",
      "tenantName": "Acme Corp",
      "details": {
        "changes": [
          {
            "field": "email",
            "oldValue": "old@example.com",
            "newValue": "new@example.com"
          }
        ],
        "reason": "User requested email change"
      },
      "timestamp": "2026-02-04T10:00:00Z",
      "ipAddress": "192.168.1.1",
      "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 100,
    "totalPages": 2
  }
}
```

**Status Codes:**

- `200 OK` - Audit logs retrieved successfully
- `400 Bad Request` - Invalid query parameters (e.g., invalid date format, page < 1)
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `AuditLogsController.ListAuditLogs()`
- Query: `GetAuditLogsQuery`
- Handler: `GetAuditLogsQueryHandler`

**Notes:**

- Response is returned directly (NOT wrapped in ApiResponse object)
- Date filters use ISO 8601 format (e.g., "2026-02-04T10:00:00Z")
- Results are sorted by timestamp descending (most recent first) by default
- Maximum pageSize is 100 entries

---

### GET /admin/api/v1/audit-logs/{id}

Get a single audit log entry by ID.

**Path Parameters:**

- `id` (string, GUID) - Audit log entry ID

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "adminEmail": "admin@example.com",
  "action": "USER_UPDATED",
  "targetType": "user",
  "targetId": "user-123",
  "tenantId": "tenant-456",
  "tenantName": "Acme Corp",
  "details": {
    "changes": [
      {
        "field": "email",
        "oldValue": "old@example.com",
        "newValue": "new@example.com"
      }
    ],
    "reason": "User requested email change"
  },
  "timestamp": "2026-02-04T10:00:00Z",
  "ipAddress": "192.168.1.1",
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

**Status Codes:**

- `200 OK` - Audit log entry retrieved successfully
- `400 Bad Request` - Invalid ID format (not a valid GUID)
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Audit log entry not found
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `AuditLogsController.GetAuditLogById()`
- Query: `GetAuditLogByIdQuery`
- Handler: `GetAuditLogByIdQueryHandler`

**Notes:**

- Response is returned directly (NOT wrapped in ApiResponse object)
- Audit logs are immutable - cannot be modified or deleted after creation

---

### GET /admin/api/v1/audit-logs/export

Export audit logs to CSV format with optional filtering.

**Query Parameters (all optional):**

- `adminEmail` (string, optional) - Filter by admin email
- `actionType` (string, optional) - Filter by action type
- `tenantId` (string, GUID, optional) - Filter by tenant ID
- `startDate` (string, ISO 8601, optional) - Start date
- `endDate` (string, ISO 8601, optional) - End date

**Response (200 OK):**

Content-Type: `text/csv`  
Content-Disposition: `attachment; filename="audit-logs-{timestamp}.csv"`

CSV file with columns:
```csv
Id,AdminEmail,Action,TargetType,TargetId,TenantId,TenantName,Timestamp,IpAddress,Details
550e8400-e29b-41d4-a716-446655440000,admin@example.com,USER_UPDATED,user,user-123,tenant-456,Acme Corp,2026-02-04T10:00:00Z,192.168.1.1,"Field: email, Old: old@example.com, New: new@example.com"
```

**Status Codes:**

- `200 OK` - CSV file generated successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `AuditLogsController.ExportAuditLogs()`
- Query: `ExportAuditLogsQuery`
- Handler: `ExportAuditLogsQueryHandler`

**Notes:**

- Response is a downloadable CSV file (not JSON)
- Filename includes timestamp for easy identification
- No pagination - returns all matching entries (use with caution on large datasets)
- Consider adding date range to prevent excessive data exports

---

### GET /admin/api/v1/audit-logs/action-types

Get list of all available audit log action types.

**Response (200 OK):**

```json
[
  "USER_CREATED",
  "USER_UPDATED",
  "USER_DELETED",
  "USER_ACTIVATED",
  "USER_DEACTIVATED",
  "SUBSCRIPTION_CREATED",
  "SUBSCRIPTION_CHANGED",
  "SUBSCRIPTION_CANCELLED",
  "TRIAL_EXTENDED",
  "TENANT_CREATED",
  "TENANT_DELETED",
  "DISCOUNT_CODE_CREATED",
  "DISCOUNT_CODE_REDEEMED",
  "SETTINGS_UPDATED",
  "EMAIL_TEMPLATE_UPDATED"
]
```

**Status Codes:**

- `200 OK` - Action types retrieved successfully
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `AuditLogsController.GetActionTypes()`
- Query: `GetAuditActionTypesQuery`
- Handler: `GetAuditActionTypesQueryHandler`

**Notes:**

- Response is returned directly as an array of strings (NOT wrapped in ApiResponse object)
- List is derived from the `AuditActionType` enum in the domain model
- Used by frontend for filtering dropdown options

---

## Admin System Settings Endpoints

These endpoints manage system-wide configuration settings for the PurposePath platform. Settings control operational parameters, security policies, email configuration, payment processing, and feature flags.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `Content-Type: application/json`

---

### GET /admin/api/v1/settings

Get all system settings as a flat array of individual setting objects.

**Query Parameters:**

- `category` (string, optional) - Filter by category ("authentication", "email", "billing", "system")
- `search` (string, optional) - Search settings by key or description

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "key": "general.appName",
      "value": "PurposePath",
      "dataType": "string",
      "category": "system",
      "description": "The name of the application displayed to users",
      "defaultValue": "PurposePath",
      "isActive": true,
      "lastModifiedAt": "2026-02-05T01:08:46Z",
      "lastModifiedBy": "system"
    },
    {
      "key": "security.passwordMinLength",
      "value": "8",
      "dataType": "number",
      "category": "authentication",
      "description": "Minimum required length for user passwords",
      "defaultValue": "8",
      "isActive": true,
      "lastModifiedAt": "2026-02-05T01:08:46Z",
      "lastModifiedBy": "admin@example.com"
    },
    {
      "key": "security.passwordRequireUppercase",
      "value": "true",
      "dataType": "boolean",
      "category": "authentication",
      "description": "Require at least one uppercase letter in passwords",
      "defaultValue": "true",
      "isActive": true,
      "lastModifiedAt": "2026-02-05T01:08:46Z",
      "lastModifiedBy": "system"
    },
    {
      "key": "email.provider",
      "value": "aws-ses",
      "dataType": "string",
      "category": "email",
      "description": "Email service provider (aws-ses, sendgrid, smtp)",
      "defaultValue": "aws-ses",
      "isActive": true,
      "lastModifiedAt": "2026-02-05T01:08:46Z",
      "lastModifiedBy": "system"
    },
    {
      "key": "payment.trialPeriodDays",
      "value": "14",
      "dataType": "number",
      "category": "billing",
      "description": "Number of days for trial subscriptions",
      "defaultValue": "14",
      "isActive": true,
      "lastModifiedAt": "2026-02-05T01:08:46Z",
      "lastModifiedBy": "system"
    }
  ]
}
```

**SystemSetting Object Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `key` | string | Unique setting identifier (e.g., "general.appName") |
| `value` | string | Current value (stored as string, converted based on dataType) |
| `dataType` | string | Data type: "boolean", "string", "number", "json" |
| `category` | string | Setting category: "authentication", "email", "billing", "system" |
| `description` | string | Human-readable description of the setting |
| `defaultValue` | string | Default value if reset |
| `isActive` | boolean | Whether setting is active |
| `lastModifiedAt` | string | ISO 8601 timestamp of last modification |
| `lastModifiedBy` | string | Email of admin who last modified |

**Setting Categories:**

| Category | Description | Example Keys |
|----------|-------------|--------------|
| `authentication` | Security and authentication policies | passwordMinLength, maxLoginAttempts, sessionTimeout |
| `email` | Email delivery configuration | provider, fromAddress, fromName, smtpHost |
| `billing` | Payment processing settings | trialPeriodDays, billingCycleDays, currency, provider |
| `system` | General system configuration | appName, companyName, timezone, maintenanceMode |

**Status Codes:**

- `200 OK` - Settings retrieved successfully
- `400 Bad Request` - Invalid category value
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `SystemSettingsController.ListSettings()`
- Query: `ListSystemSettingsQuery`
- Handler: `ListSystemSettingsQueryHandler`

**Notes:**

- Response follows standard ApiResponse wrapper format with `success` and `data` fields
- Settings are returned as a flat array (not nested objects)
- All values are stored as strings and converted based on `dataType`
- Sensitive values may be masked in responses
- Frontend uses this endpoint with `useSettings()` hook

---

### GET /admin/api/v1/settings/{key}

Get a specific system setting by its key.

**Path Parameters:**

- `key` (string, required) - Setting key (e.g., "general.appName", "security.passwordMinLength")

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "key": "security.passwordMinLength",
    "value": "8",
    "dataType": "number",
    "category": "authentication",
    "description": "Minimum required length for user passwords",
    "defaultValue": "8",
    "isActive": true,
    "lastModifiedAt": "2026-02-05T01:08:46Z",
    "lastModifiedBy": "admin@example.com"
  }
}
```

**Status Codes:**

- `200 OK` - Setting retrieved successfully
- `400 Bad Request` - Invalid setting key format
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Setting key not found
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `SystemSettingsController.GetSetting()`
- Query: `GetSystemSettingQuery`
- Handler: `GetSystemSettingQueryHandler`

---

### PATCH /admin/api/v1/settings/{key}

Update a specific system setting.

**Path Parameters:**

- `key` (string, required) - Setting key (e.g., "general.appName")

**Request Body:**

```json
{
  "value": "MyCompany Platform",
  "reason": "Rebranding initiative"
}
```

**Request Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `value` | string | Yes | New value for the setting (will be validated based on dataType) |
| `reason` | string | Yes | Reason for the change (for audit trail) |

**Validation Rules by Setting:**

| Key | Data Type | Constraints |
|-----|-----------|-------------|
| `general.appName` | string | 1-100 characters |
| `general.companyName` | string | 1-200 characters |
| `general.supportEmail` | string | Valid email format |
| `general.timezone` | string | Valid IANA timezone |
| `general.maintenanceMode` | boolean | "true" or "false" |
| `security.passwordMinLength` | number | 6-128 |
| `security.maxLoginAttempts` | number | 1-10 |
| `security.lockoutDuration` | number | 1-1440 (minutes) |
| `email.fromAddress` | string | Valid email format |
| `payment.trialPeriodDays` | number | 0-365 |
| `payment.billingCycleDays` | number | 1, 7, 14, 30, 90, 365 |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "key": "general.appName",
    "value": "MyCompany Platform",
    "dataType": "string",
    "category": "system",
    "description": "The name of the application displayed to users",
    "defaultValue": "PurposePath",
    "isActive": true,
    "lastModifiedAt": "2026-02-05T10:30:00Z",
    "lastModifiedBy": "admin@example.com"
  }
}
```

**Status Codes:**

- `200 OK` - Setting updated successfully
- `400 Bad Request` - Validation error (invalid value for data type, out of range, etc.)
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Setting key not found
- `500 Internal Server Error` - Server error

**Error Response Example:**

```json
{
  "success": false,
  "error": "Validation failed: Value must be between 6 and 128",
  "code": "VALIDATION_ERROR"
}
```

**Implementation:**

- Controller: `SystemSettingsController.UpdateSetting()`
- Command: `UpdateSystemSettingCommand`
- Handler: `UpdateSystemSettingCommandHandler`

**Notes:**

- Value is provided as string and validated/converted based on setting's `dataType`
- Changes are logged in audit trail with action type "SETTINGS_UPDATED"
- `reason` field is required for audit compliance
- Some settings may require application restart to take effect

---

### POST /admin/api/v1/settings/{key}/validate

Validate a setting value without saving it.

**Path Parameters:**

- `key` (string, required) - Setting key to validate

**Request Body:**

```json
{
  "value": "5"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "valid": true,
    "errors": []
  }
}
```

**Response (Validation Failed):**

```json
{
  "success": true,
  "data": {
    "valid": false,
    "errors": [
      "Value must be at least 6",
      "Value must be at most 128"
    ]
  }
}
```

**Status Codes:**

- `200 OK` - Validation completed (check `valid` field in response)
- `400 Bad Request` - Invalid setting key
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Setting key not found
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `SystemSettingsController.ValidateSetting()`
- Command: `ValidateSystemSettingCommand`
- Handler: `ValidateSystemSettingCommandHandler`

**Notes:**

- Performs validation without persisting changes
- Useful for real-time validation in UI forms
- Returns validation errors without saving

---

### POST /admin/api/v1/settings/{key}/reset

Reset a specific setting to its default value.

**Path Parameters:**

- `key` (string, required) - Setting key to reset

**Request Body:**

```json
{
  "reason": "Reverting to default configuration"
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "key": "security.passwordMinLength",
    "value": "8",
    "dataType": "number",
    "category": "authentication",
    "description": "Minimum required length for user passwords",
    "defaultValue": "8",
    "isActive": true,
    "lastModifiedAt": "2026-02-05T11:00:00Z",
    "lastModifiedBy": "admin@example.com"
  }
}
```

**Status Codes:**

- `200 OK` - Setting reset successfully
- `400 Bad Request` - Invalid setting key or missing reason
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Setting key not found
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `SystemSettingsController.ResetSetting()`
- Command: `ResetSystemSettingCommand`
- Handler: `ResetSystemSettingCommandHandler`

**Notes:**

- Resets the setting to its `defaultValue`
- `reason` is required for audit trail
- Action is logged with "SETTINGS_UPDATED" action type
- Consider impact before resetting critical settings

---

## Admin Tenant Management Endpoints

### GET /admin/tenants/{tenantId}/people

Get paginated list of people within a specific tenant (admin only).

**Path Parameters:**

- `tenantId` (string, GUID) - The tenant ID

**Query Parameters:**

- `pageNumber` (integer, optional) - Page number (1-based, default: 1)
- `pageSize` (integer, optional) - Items per page (default: 20, max: 100)
- `personTypeId` (string, GUID, optional) - Filter by person type ID
- `status` (string, optional) - Filter by status ('active' or 'inactive')
- `tagId` (string, GUID, optional) - Filter by tag ID
- `search` (string, optional) - Search term (searches firstName, lastName, email)
- `includeRoles` (boolean, optional) - Include role assignments (default: false)

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}` (optional for admin context)
- `Content-Type: application/json`

**Request:**

No request body.

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com",
        "isEmailVerified": true,
        "phone": "+1234567890",
        "title": "Chief Executive Officer",
        "personType": {
          "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
          "name": "Employee",
          "description": "Full-time employee"
        },
        "isActive": true,
        "isAssignable": true,
        "primaryRole": {
          "id": "8d9e6679-7425-40de-944b-e07fc1f90ae8",
          "name": "CEO",
          "description": "Chief Executive Officer"
        },
        "tags": [
          {
            "id": "9e0f6679-7425-40de-944b-e07fc1f90ae9",
            "name": "Leadership",
            "color": "#FF5722"
          }
        ],
        "hasSystemAccess": true,
        "createdAt": "2025-01-15T10:30:00Z",
        "updatedAt": "2025-01-20T14:45:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "pageSize": 20,
      "totalCount": 45,
      "totalPages": 3
    }
  }
}
```

**Status Codes:**

- `200 OK` - People retrieved successfully
- `400 Bad Request` - Invalid request parameters
  - Invalid tenant ID format
  - Invalid person type ID format
  - Invalid tag ID format
  - Invalid status value (must be 'active' or 'inactive')
  - Invalid pagination values
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Tenant not found
- `500 Internal Server Error` - Server error

**Error Response Example:**

```json
{
  "error": "Invalid tenant ID format"
}
```

**Notes:**

- Endpoint accepts same filtering and pagination options as the user-facing people endpoint
- Admin can view people from any tenant (cross-tenant access)
- Results include system access status (whether person is linked to a user account)
- Role information is included when `includeRoles=true`
- Operation is logged for audit trail
- Pagination is enforced (max 100 items per page)

**Implementation:**

- Controller: `AdminController.GetTenantPeople()`
- Query: `GetPeopleQuery` (via MediatR)
- Handler: `GetPeopleQueryHandler`
- Models: `PersonListResponse`, `PersonListItemModel`
- Mapper: `PeopleMappingProfile`

---

### PUT /admin/tenants/{tenantId}/owner

Change the owner of a tenant (admin only).

**Path Parameters:**

- `tenantId` (string, GUID) - The tenant ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "newOwnerPersonId": "string (GUID)"
}
```

**Request Validation:**

- `newOwnerPersonId`: Required, must be a valid GUID
- Person must exist and belong to the tenant
- Person must be linked to an active user account
- New owner must be different from current owner (if any)

**Response:**

```json
{
  "success": true,
  "data": {
    "tenantId": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Example Tenant",
    "ownerUserId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "updatedAt": "2026-01-21T15:30:00Z"
  }
}
```

**Status Codes:**

- `200 OK` - Tenant owner changed successfully
- `400 Bad Request` - Invalid request or validation error
  - Invalid tenant ID format
  - Invalid person ID format
  - Person not linked to user account
  - User not active
  - Person doesn't belong to tenant
  - New owner same as current owner
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Tenant or person not found

**Error Response Example:**

```json
{
  "success": false,
  "error": "Person must be linked to an active user account"
}
```

**Notes:**

- The endpoint accepts a `personId` (not `userId`) because the admin portal works with people records
- Backend validates that the person is linked to an active user and resolves the user ID automatically
- Person must belong to the same tenant whose owner is being changed
- User linked to the person must be in Active status
- Operation is logged for audit purposes
- Can change owner even if owner was already set (unlike initial owner setup)

**Implementation:**

- Controller: `TenantManagementController.ChangeTenantOwner()`
- Command: `ChangeTenantOwnerCommand`
- Handler: `ChangeTenantOwnerCommandHandler`
- Domain: `Tenant.ChangeOwner(UserId)`

---

### DELETE /admin/tenants/{tenantId}

Delete or anonymize a tenant and all associated data (admin only).

**Path Parameters:**

- `tenantId` (string, GUID) - The tenant ID to delete

**Query Parameters:**

- `deletionMode` (string, default: "Soft") - Deletion mode:
  - `"Soft"`: Anonymize personally identifiable information while preserving business/financial data for compliance (GDPR right to be forgotten)
  - `"Hard"`: Remove all non-financial tenant data (preserves subscriptions, billing, audit logs for 7-year retention)
- `dryRun` (boolean, default: false) - If true, simulates deletion and returns what would be deleted without making changes
- `confirmation` (string, required) - Must be exactly `"DELETE:{tenantId}"` to prevent accidental deletions

**Headers Required:**

```http
Authorization: Bearer {adminJwtToken}
Content-Type: application/json
```

**Request URL Example:**

```
DELETE /admin/tenants/7c9e6679-7425-40de-944b-e07fc1f90ae7?deletionMode=Soft&dryRun=false&confirmation=DELETE:7c9e6679-7425-40de-944b-e07fc1f90ae7
```

**Soft Delete Behavior:**
- Anonymizes: User emails, names, PII fields
- Retains: Subscription records, billing history, audit logs, business metrics
- Compliance: GDPR right to be forgotten while maintaining financial records

**Hard Delete Behavior:**
- Removes: All tenant-related data across all tables (Users, Goals, Measures, Actions, Issues, People, etc.)
- Preserves: Subscription records, payment history, audit logs (7-year retention requirement)
- Tables affected: 25+ DynamoDB tables including Users, Tenants, Goals, Strategies, Measures, Actions, Issues, People, OrgStructure, Products, and more

**Success Response (200 OK):**

```json
{
  "success": true,
  "message": "Tenant 7c9e6679-7425-40de-944b-e07fc1f90ae7 deleted successfully using Soft mode",
  "data": {
    "tenantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "deletionMode": "Soft",
    "itemsDeleted": 145,
    "itemsRetained": 8,
    "totalDeleted": 145,
    "totalRetained": 8,
    "deletedAt": "2025-01-03T10:30:00Z",
    "isDryRun": false
  }
}
```

**Success Response (Dry Run):**

```json
{
  "success": true,
  "message": "Dry run completed. Tenant 7c9e6679-7425-40de-944b-e07fc1f90ae7 would be deleted using Hard mode. No actual changes made.",
  "data": {
    "tenantId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "deletionMode": "Hard",
    "itemsDeleted": 0,
    "itemsRetained": 0,
    "totalDeleted": 152,
    "totalRetained": 8,
    "deletedAt": "2025-01-03T10:30:00Z",
    "isDryRun": true
  }
}
```

**Response Fields:**

- `tenantId`: The tenant ID that was deleted
- `deletionMode`: "Soft" or "Hard"
- `itemsDeleted`: Number of items actually deleted (0 for dry run)
- `itemsRetained`: Number of items retained for compliance
- `totalDeleted`: Total items that would be deleted (dry run) or were deleted
- `totalRetained`: Total items retained for compliance
- `deletedAt`: Timestamp of deletion operation
- `isDryRun`: Whether this was a simulation

**Error Responses:**

- `400 Bad Request` - Validation errors:
  ```json
  {
    "success": false,
    "message": "Invalid deletion mode. Must be 'Soft' or 'Hard'."
  }
  ```
  ```json
  {
    "success": false,
    "message": "Confirmation string must be in format 'DELETE:{tenantId}'"
  }
  ```

- `404 Not Found` - Tenant doesn't exist:
  ```json
  {
    "success": false,
    "message": "Tenant 7c9e6679-7425-40de-944b-e07fc1f90ae7 not found"
  }
  ```

- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User doesn't have admin role

**Validation Rules:**

- `confirmation` parameter must exactly match format `DELETE:{tenantId}`
- `deletionMode` must be "Soft" or "Hard" (case-insensitive)
- `dryRun` accepts true/false or 1/0
- Tenant must exist before deletion

**Business Rules:**

- **Compliance**: Both modes preserve subscription/billing data for 7 years (regulatory requirement)
- **GDPR**: Soft delete satisfies "right to be forgotten" by anonymizing PII
- **Safety**: Confirmation string prevents accidental deletions
- **Audit Trail**: All deletions logged in audit tables (preserved indefinitely)
- **Dry Run**: Test deletion impact before committing changes

**Tables Affected (25+):**

Tenant-related tables scanned for deletion:
- Core: Users, Tenants, Subscriptions
- Traction: Goals, Strategies, Measures, MeasureLinks, MeasureData, Actions, Issues
- People & Org: People, OrgStructure, PersonTypes, PersonTags
- Business Foundation: Products, Services, ICAs, CoreValues
- Activity & Audit: Activities, AuditLogs
- System: Notifications, EmailVerifications, PasswordResets

Tables **always preserved**:
- Subscriptions (includes billing history)
- AuditLogs (compliance requirement)
- Payment transactions (7-year retention)

**Implementation:**

- Controller: `TenantManagementController.DeleteTenant()`
- Command: `DeleteTenantCommand`
- Handler: `DeleteTenantCommandHandler`
- Service: `ITenantDeletionService` → `TenantDeletionService`
- Domain: `DeletionMode` enum, `TenantDeletionResult` model

**Testing Notes:**

- Use `dryRun=true` to preview deletion impact
- Test with non-production tenants first
- Verify audit logs capture deletion events
- Confirm financial data preserved in both modes
- Test confirmation string validation thoroughly

---

### POST /admin/maintenance/cleanup-orphaned-users

Clean up users whose tenants no longer exist (admin only maintenance endpoint).

**Query Parameters:**

- `dryRun` (boolean, default: false) - If true, simulates cleanup and returns what would be deleted without making changes

**Headers Required:**

```http
Authorization: Bearer {adminJwtToken}
Content-Type: application/json
```

**Request URL Example:**

```
POST /admin/maintenance/cleanup-orphaned-users?dryRun=false
```

**Description:**

This maintenance endpoint scans all users in the system and identifies orphaned users (users whose tenant no longer exists in the database). These orphaned records can occur due to:
- Manual database operations
- Incomplete deletion processes
- Data migration issues
- System bugs that left orphaned records

The endpoint provides a safe way to clean up these orphaned users independently of tenant deletion operations.

**Success Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "orphanedUsersFound": 5,
    "orphanedUsersDeleted": 5,
    "deletedUsers": [
      {
        "userId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "username": "john.doe@example.com",
        "formerTenantId": "550e8400-e29b-41d4-a716-446655440000"
      },
      {
        "userId": "8d0f7789-8536-51ef-b827-f18gd2g01bf8",
        "username": "jane.smith@example.com",
        "formerTenantId": "660f9511-f30c-52e5-c938-557766551111"
      }
    ],
    "wasDryRun": false,
    "cleanupCompletedAt": "2026-01-25T15:30:00Z"
  }
}
```

**Success Response (Dry Run):**

```json
{
  "success": true,
  "data": {
    "orphanedUsersFound": 5,
    "orphanedUsersDeleted": 0,
    "deletedUsers": [
      {
        "userId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "username": "john.doe@example.com",
        "formerTenantId": "550e8400-e29b-41d4-a716-446655440000"
      }
    ],
    "wasDryRun": true,
    "cleanupCompletedAt": "2026-01-25T15:30:00Z"
  }
}
```

**Response Fields:**

- `orphanedUsersFound`: Number of orphaned users identified in the system
- `orphanedUsersDeleted`: Number of orphaned users actually deleted (0 for dry run)
- `deletedUsers`: Array of deleted user details (limited to first 100 for performance)
  - `userId`: The orphaned user's ID
  - `username`: The orphaned user's username/email
  - `formerTenantId`: The tenant ID that no longer exists
- `wasDryRun`: Whether this was a simulation
- `cleanupCompletedAt`: Timestamp of cleanup operation

**Error Responses:**

- `401 Unauthorized` - Missing or invalid admin token:
  ```json
  {
    "success": false,
    "error": "Unauthorized"
  }
  ```

- `403 Forbidden` - User doesn't have admin role:
  ```json
  {
    "success": false,
    "error": "Forbidden: Admin role required"
  }
  ```

- `500 Internal Server Error` - Unexpected error during cleanup:
  ```json
  {
    "success": false,
    "error": "An error occurred during orphaned user cleanup"
  }
  ```

**Business Rules:**

- **Safety**: Use `dryRun=true` first to preview impact before actual deletion
- **Performance**: Scans all users in the database (can be slow for large datasets)
- **Audit Trail**: All deletions logged in audit tables
- **Verification**: Checks tenant existence before marking user as orphaned
- **Independence**: Can be run without deleting a specific tenant
- **Idempotent**: Safe to run multiple times (subsequent runs find 0 orphaned users)

**When to Use:**

- After manual database operations
- Periodic maintenance to ensure database integrity
- After data migration or restoration
- When audit logs indicate orphaned user issues
- Before database performance optimization

**Implementation:**

- Controller: `MaintenanceController.CleanupOrphanedUsers()`
- Command: `CleanupOrphanedUsersCommand`
- Handler: `CleanupOrphanedUsersCommandHandler`
- Service: `ITenantDeletionService.CleanupOrphanedUsersAsync()`

**Testing Notes:**

- Always use `dryRun=true` first to preview results
- Monitor performance on production (can be slow for millions of users)
- Verify audit logs capture all deletions
- Test with known orphaned users in staging environment
- Confirm orphaned user count decreases after actual cleanup

---

## Admin Subscriber Management Endpoints

### GET /admin/subscribers

Get paginated list of subscribers (tenants with subscriptions) with filtering and sorting.

**Query Parameters:**

- `page` (number, default: 1) - Page number (1-based)
- `pageSize` (number, default: 50) - Items per page (1-100)
- `search` (string, optional) - Search by tenant name or email (case-insensitive partial match)
- `status` (string, optional) - Filter by subscription status ("Active", "Trialing", "PastDue", "Canceled", "Expired")
- `tier` (string, optional) - Filter by subscription tier ID (GUID)
- `renewalFrequency` (string, optional) - Filter by billing frequency ("Monthly", "Yearly")
- `sortBy` (string, default: "CreatedAt") - Sort field ("Name", "CreatedAt", "Status", "TierId", "Frequency")
- `sortOrder` (string, default: "Descending") - Sort direction ("Ascending", "Descending")

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "items": [
    {
      "tenantId": "550e8400-e29b-41d4-a716-446655440000",
      "businessName": "Acme Corporation",
      "contactName": "John Doe",
      "contactEmail": "john.doe@acme.com",
      "owner": {
        "userId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "personId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
        "name": "Jane Smith",
        "email": "jane.smith@acme.com"
      },
      "subscription": {
        "subscriptionId": "123e4567-e89b-12d3-a456-426614174000",
        "status": "Active",
        "currentTier": {
          "id": "tier-professional",
          "name": "professional",
          "displayName": "Professional"
        },
        "billingInfo": {
          "frequency": "Monthly",
          "monthlyRecurringRevenue": 99.99,
          "currentPeriodStart": "2025-12-01T00:00:00Z",
          "currentPeriodEnd": "2026-01-01T00:00:00Z",
          "nextBillingDate": "2026-01-01T00:00:00Z"
        }
      },
      "usage": {
        "goalsCount": 12,
        "goalsLimit": 50,
        "measuresCount": 35,
        "measuresLimit": 200,
        "actionsCount": 87,
        "actionsLimit": null,
        "usersCount": 5
      },
      "createdAt": "2025-10-01T12:00:00Z",
      "lastActivityAt": "2025-12-30T15:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalCount": 150,
    "totalPages": 3
  }
}
```

**Field Descriptions:**

- `owner`: Optional. The designated owner of the tenant (set via PUT /admin/tenants/{tenantId}/owner)
  - `userId`: User ID of the owner
  - `personId`: Person ID of the owner
  - `name`: Full name of the owner (from Person record)
  - `email`: Email address of the owner (from Person record)
  - Will be `null` if no owner has been explicitly assigned

**Status Codes:**

- `200 OK` - Success
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token

**Notes:**

- Requires admin authentication
- Returns only tenants that have active subscriptions
- Contact info represents the primary/first active user in the tenant
- Owner info represents the explicitly designated owner (may differ from contact)
- Last activity is determined by the most recent user login

**Implementation:**

- Controller: `AdminController.GetSubscribers()`
- Query: `GetSubscribersQuery`
- Handler: `GetSubscribersQueryHandler`

---

### GET /admin/subscribers/{tenantId}

Get comprehensive details about a specific subscriber including payment history, users, and audit logs.

**Path Parameters:**

- `tenantId` (string, GUID) - The tenant ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "tenantId": "550e8400-e29b-41d4-a716-446655440000",
  "businessName": "Acme Corporation",
  "contactName": "John Doe",
  "contactEmail": "john.doe@acme.com",
  "owner": {
    "userId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "personId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "name": "Jane Smith",
    "email": "jane.smith@acme.com"
  },
  "subscription": {
    "subscriptionId": "123e4567-e89b-12d3-a456-426614174000",
    "status": "Active",
    "currentTier": {
      "id": "tier-professional",
      "name": "professional",
      "displayName": "Professional"
    },
    "billingInfo": {
      "frequency": "Monthly",
      "monthlyRecurringRevenue": 99.99,
      "currentPeriodStart": "2025-12-01T00:00:00Z",
      "currentPeriodEnd": "2026-01-01T00:00:00Z",
      "nextBillingDate": "2026-01-01T00:00:00Z"
    },
    "lifetimeValue": 599.94,
    "totalPayments": 6
  },
  "users": [
    {
      "userId": "user-1",
      "email": "john.doe@acme.com",
      "firstName": "John",
      "lastName": "Doe",
      "status": "Active",
      "role": "User",
      "createdAt": "2025-10-01T12:00:00Z",
      "lastLoginAt": "2025-12-30T15:30:00Z"
    }
  ],
  "paymentHistory": [
    {
      "paymentId": "payment-123",
      "amount": 99.99,
      "currency": "USD",
      "status": "Succeeded",
      "paymentMethod": "Card",
      "createdAt": "2025-12-01T00:00:00Z",
      "invoiceUrl": "https://stripe.com/invoices/..."
    }
  ],
  "recentAudit": [
    {
      "action": "owner_changed",
      "resourceType": "Tenant",
      "resourceId": "550e8400-e29b-41d4-a716-446655440000",
      "userId": "admin-123",
      "userName": "Admin User",
      "timestamp": "2025-12-28T10:00:00Z",
      "details": "Changed owner to Jane Smith"
    }
  ],
  "usage": {
    "goalsCount": 12,
    "goalsLimit": 50,
    "measuresCount": 35,
    "measuresLimit": 200,
    "actionsCount": 87,
    "actionsLimit": null,
    "usersCount": 5,
    "storageUsed": 1024.5,
    "storageLimit": 10240,
    "apiCallsThisMonth": 1523,
    "featureUsage": {
      "coaching": 45,
      "traction": 120
    }
  },
  "createdAt": "2025-10-01T12:00:00Z",
  "lastActivityAt": "2025-12-30T15:30:00Z",
  "subscriptionHistory": [],
  "featureGrants": [],
  "supportTickets": []
}
```

**Field Descriptions:**

- `owner`: Optional. The designated owner of the tenant (set via PUT /admin/tenants/{tenantId}/owner)
  - `userId`: User ID of the owner
  - `personId`: Person ID of the owner
  - `name`: Full name of the owner (from Person record)
  - `email`: Email address of the owner (from Person record)
  - Will be `null` if no owner has been explicitly assigned

**Status Codes:**

- `200 OK` - Success
- `400 Bad Request` - Invalid tenant ID format
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant not found

**Notes:**

- Requires admin authentication
- Returns comprehensive subscriber information for admin dashboard
- Includes last 20 payment history entries
- Includes last 50 audit log entries
- Contact info represents the primary/first active user
- Owner info represents the explicitly designated owner

**Implementation:**

- Controller: `AdminController.GetSubscriberDetails()`
- Query: `GetSubscriberDetailsQuery`
- Handler: `GetSubscriberDetailsQueryHandler`

---

## Admin Trial Management Endpoints

### PUT /admin/users/{userId}/subscription/trial/extend

Extend trial subscription for a user (admin only).

**Path Parameters:**

- `userId` - User ID to extend trial for

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Request:**

```json
{
  "newExpirationDate": "2025-12-01T00:00:00Z",
  "reason": "Customer success initiative",
  "extendedBy": "adminUserId"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "string",
      "userId": "string",
      "tier": {
        "id": "string",
        "name": "string",
        "features": ["string"],
        "limits": {},
        "supportedFrequencies": ["monthly", "yearly"]
      },
      "frequency": "monthly|yearly",
      "status": "string",
      "isActive": true,
      "currentPeriodStart": "2025-10-01T00:00:00Z",
      "currentPeriodEnd": "2025-11-01T00:00:00Z",
      "expirationDate": "string?",
      "cancelAtPeriodEnd": false,
      "autoRenewal": true,
      "price": 29.99,
      "currency": "USD",
      "isTrial": true,
      "trialEndDate": "2025-12-01T00:00:00Z",
      "trialExtendedBy": "adminUserId",
      "trialExtensionReason": "Customer success initiative"
    },
    "previousExpirationDate": "2025-11-13T00:00:00Z",
    "newExpirationDate": "2025-12-01T00:00:00Z"
  }
}
```

**Status Codes:**

- `200 OK` - Trial extended successfully
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - User not found

**Notes:**

- Requires admin authentication
- Can extend both active and expired trials
- Logged for audit purposes

---

### GET /admin/users/{userId}/subscription/trial/history

Get trial extension history for a user (admin only).

**Path Parameters:**

- `userId` - User ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "userId": "string",
      "previousExpirationDate": "string (ISO 8601)",
      "newExpirationDate": "string (ISO 8601)",
      "extendedBy": "string (Admin User ID)",
      "reason": "string",
      "extendedAt": "string (ISO 8601)"
    }
  ]
}
```

**Status Codes:**

- `200 OK` - Success
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - User not found

---

## Discount Code Management Endpoints

**Base Path:** `/admin/discount-codes`

### GET /admin/discount-codes

Get paginated list of discount codes with optional filtering and sorting.

**Query Parameters:**

- `page` (number, default: 1) - Page number (1-based)
- `pageSize` (number, default: 20) - Items per page (1-100)
- `status` (string, optional) - Filter by status ("active", "inactive", "expired", or null for all)
- `search` (string, optional) - Search by discount code (case-insensitive partial match)
- `sortBy` (string, default: "createdAt") - Sort field ("createdAt", "code", "redemptions", "expiresAt")
- `sortOrder` (string, default: "desc") - Sort direction ("asc" or "desc")

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string (GUID)",
        "code": "string",
        "description": "string",
        "discountType": "percentage | fixed",
        "value": "number",
        "durationInCycles": "number",
        "isActive": "boolean",
        "expiresAt": "string (ISO 8601)?",
        "currentRedemptions": "number",
        "maxRedemptions": "number",
        "applicableTiers": ["string"],
        "applicableFrequencies": ["string"],
        "isOneTimeUsePerTenant": "boolean",
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)"
      }
    ],
    "pagination": {
      "page": "number",
      "pageSize": "number",
      "totalCount": "number",
      "totalPages": "number",
      "hasNext": "boolean",
      "hasPrevious": "boolean"
    }
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Invalid query parameters
- `401` - Unauthorized (missing or invalid admin token)

---

### GET /admin/discount-codes/{id}

Get comprehensive details of a specific discount code.

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "description": "string",
    "discountType": "percentage | fixed",
    "value": "number",
    "durationInCycles": "number",
    "isActive": "boolean",
    "expiresAt": "string (ISO 8601)?",
    "currentRedemptions": "number",
    "maxRedemptions": "number",
    "applicableTiers": ["string"],
    "applicableFrequencies": ["string"],
    "isOneTimeUsePerTenant": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Invalid discount code ID format
- `401` - Unauthorized
- `404` - Discount code not found

---

### POST /admin/discount-codes

Create a new discount code.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "code": "string",
  "description": "string",
  "discountType": "percentage | fixed",
  "value": "number",
  "durationInCycles": "number",
  "maxRedemptions": "number?",
  "applicableTiers": ["string"]?,
  "applicableFrequencies": ["string"]?,
  "isOneTimeUsePerTenant": "boolean",
  "expiresAt": "string (ISO 8601)?"
}
```

**Validation Rules:**

- `code`: 4-20 characters, uppercase letters and numbers only
- `discountType`: "percentage" or "fixed"
- `value`: For percentage: 1-100 (inclusive), For fixed: > 0
- `durationInCycles`: Positive integer (number of billing cycles)
- `applicableTiers`: Valid values: ["starter", "professional", "enterprise"] or empty for all
- `applicableFrequencies`: Valid values: ["monthly", "annual"] or empty for all

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "description": "string",
    "discountType": "percentage | fixed",
    "value": "number",
    "durationInCycles": "number",
    "isActive": "boolean",
    "expiresAt": "string (ISO 8601)?",
    "currentRedemptions": "number",
    "maxRedemptions": "number",
    "applicableTiers": ["string"],
    "applicableFrequencies": ["string"],
    "isOneTimeUsePerTenant": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `201` - Created (includes Location header with resource URL)
- `400` - Validation error
- `401` - Unauthorized
- `409` - Conflict (discount code already exists)

---

### PATCH /admin/discount-codes/{id}

Update an existing discount code (partial update).

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`
- `Content-Type: application/json`

**Request:**

```json
{
  "description": "string?",
  "maxRedemptions": "number?",
  "expiresAt": "string (ISO 8601)?",
  "applicableTiers": ["string"]?,
  "applicableFrequencies": ["string"]?,
  "isOneTimeUsePerTenant": "boolean?"
}
```

**Immutable Fields (cannot be updated):**

- `code` - Create new code instead
- `discountType` - Create new code instead
- `value` - Create new code instead
- `durationInCycles` - Create new code instead

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "description": "string",
    "discountType": "percentage | fixed",
    "value": "number",
    "durationInCycles": "number",
    "isActive": "boolean",
    "expiresAt": "string (ISO 8601)?",
    "currentRedemptions": "number",
    "maxRedemptions": "number",
    "applicableTiers": ["string"],
    "applicableFrequencies": ["string"],
    "isOneTimeUsePerTenant": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Validation error or attempting to update immutable fields
- `401` - Unauthorized
- `404` - Discount code not found

---

### POST /admin/discount-codes/{id}/enable

Enable a previously disabled discount code.

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "isActive": true,
    "expiresAt": "string (ISO 8601)?",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200` - Success
- `400` - Code already active or expired
- `401` - Unauthorized
- `404` - Discount code not found

---

### POST /admin/discount-codes/{id}/disable

Disable an active discount code to prevent new redemptions.

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "isActive": false,
    "expiresAt": "string (ISO 8601)?",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Notes:**

- Existing redemptions remain unaffected
- Preserves redemption history and statistics
- Use this instead of DELETE for codes with redemptions

**Status Codes:**

- `200` - Success
- `400` - Code already inactive
- `401` - Unauthorized
- `404` - Discount code not found

---

### DELETE /admin/discount-codes/{id}

Delete a discount code permanently (only if never redeemed).

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```
204 No Content
```

**Restrictions:**

- Can ONLY delete codes with **zero redemptions** (`currentRedemptions = 0`)
- Codes with redemption history CANNOT be deleted (returns 409 Conflict)
- For codes with redemptions, use `POST /admin/discount-codes/{id}/disable` instead

**Status Codes:**

- `204` - No Content (successful deletion)
- `400` - Invalid discount code ID format
- `401` - Unauthorized
- `404` - Discount code not found
- `409` - Conflict (code has redemptions and cannot be deleted)

---

## Error Responses

All Admin API endpoints follow the standard error format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `UNAUTHORIZED` - User lacks admin role
- `INVALID_CODE_FORMAT` - Discount code doesn't meet format requirements
- `CODE_ALREADY_EXISTS` - Code is already in use
- `CODE_HAS_REDEMPTIONS` - Cannot delete code with existing redemptions
- `INVALID_REQUEST` - Malformed request or missing required fields

---

**Navigation:**

- [← Back to Index](./index.md)
