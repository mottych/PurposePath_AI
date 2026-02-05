# Admin API Specification

**Version:** 2.1  
**Status:** Complete  
**Last Updated:** February 5, 2026  
**Base URL:** `{REACT_APP_ADMIN_API_URL}/admin/api/v1`  
**Default (Localhost):** `http://localhost:8003/admin/api/v1`  
**Production:** `https://api.purposepath.app/admin/api/v1`

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| Feb 5, 2026 | 2.1 | Added System Settings Management (5 endpoints) and Role Template Management (8 endpoints) | System |
| Feb 4, 2026 | 2.0 | Complete specification with all endpoints documented | System |
| Jan 22, 2026 | 1.1 | Added tenant management and discount codes | System |
| Dec 15, 2025 | 1.0 | Initial specification | System |

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [Endpoints by Category](#endpoints-by-category)
   - [Health & System](#health--system)
   - [Authentication](#authentication-endpoints)
   - [System Seeding](#system-seeding)
   - [Issue Type Configuration](#issue-type-configuration)
   - [Issue Status Configuration](#issue-status-configuration)
   - [Email Template Management](#email-template-management)
   - [Subscriber Management](#subscriber-management)
   - [Plan Management](#plan-management)
   - [Feature Management](#feature-management)
   - [Subscription Operations](#subscription-operations)
   - [System Settings Management](#system-settings-management)
   - [Role Template Management](#role-template-management)
   - [People Management](#people-management)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)

---

## Overview

The Admin API provides comprehensive administrative capabilities for managing the PurposePath platform. It includes functionality for:

- **System Configuration**: Seeding reference data (tiers, settings, templates)
- **System Settings**: Managing operational parameters, security policies, email/payment configuration
- **Role Templates**: Managing organizational structure templates for tenants
- **Subscription Management**: Managing plans, pricing, subscribers, features
- **Email Templates**: Creating and managing email templates
- **Issue Configuration**: Configuring issue types and statuses
- **User Support**: Trial extensions, discounts, feature grants
- **Audit Logging**: Tracking all administrative actions

**Security**: All endpoints require Admin role authorization via JWT token with "Admin" policy claim.

**Audit Trail**: All write operations are automatically logged with admin user ID, action details, and timestamps.

---

## Authentication

### Required Headers

All Admin API endpoints (except auth endpoints) require:

```http
Authorization: Bearer {admin_access_token}
Content-Type: application/json
```

### Admin Role Requirement

Admins must be members of the **Portal Admins** Google Workspace group. The validation process:

1. Admin authenticates via Google OAuth 2.0
2. System validates Google Workspace group membership
3. JWT token is issued with "Admin" role claim
4. All subsequent requests validated against this role

### Token Expiration

- **Access Token**: 1 hour
- **Refresh Token**: 30 days
- Use `POST /auth/refresh` to obtain new tokens

---

## Common Patterns

### Pagination

Paginated endpoints use consistent query parameters:

```
?page=1&pageSize=20
```

**Response Structure:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "pagination": {
      "currentPage": 1,
      "pageSize": 20,
      "totalCount": 150,
      "totalPages": 8
    }
  }
}
```

**Constraints:**
- `page`: Minimum 1 (1-based indexing)
- `pageSize`: 1-100 (default: 20-50 depending on endpoint)

### Response Envelope

**Success Response:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

### Seeding Results

System seeding endpoints return:

```json
{
  "itemsCreated": 10,
  "itemsSkipped": 5,
  "errors": ["Optional error message"]
}
```

**Pattern**: INSERT-IF-NOT-FOUND (idempotent operations)

### Audit Logging

All write operations automatically log:
- Admin user ID
- Action type (create, update, delete, etc.)
- Resource type and ID
- Descriptive message
- Timestamp
- IP address (from request context)

---

## Endpoints by Category

---

## Health & System

### GET /health

Health check endpoint (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "service": "PurposePath Admin Lambda",
  "version": "1.2.0",
  "timestamp": "2026-02-04T10:30:00Z",
  "environment": "Production"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

## Authentication Endpoints

### POST /auth/validate

Validate admin user via Google OAuth and issue JWT tokens (public endpoint).

**Request:**
```json
{
  "googleAccessToken": "string",
  "email": "admin@example.com"
}
```

**Validations:**
- `googleAccessToken`: Required, valid Google OAuth access token
- `email`: Required, valid email format

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@example.com",
    "name": "Admin User",
    "picture": null,
    "role": "admin",
    "createdAt": "2025-01-15T10:30:00Z",
    "lastLoginAt": "2026-02-04T10:30:00Z",
    "accessToken": "eyJ...",
    "refreshToken": "eyJ..."
  }
}
```

**Status Codes:**
- `200 OK` - Validation successful
- `400 Bad Request` - Invalid request format or missing fields
- `401 Unauthorized` - Invalid Google token
- `403 Forbidden` - User not in Portal Admins group
- `500 Internal Server Error` - Server error

**Notes:**
- Validates Google Workspace group membership
- Generates JWT tokens with 1-hour expiration
- No existing JWT required (public endpoint)

---

### POST /auth/refresh

Refresh admin access token using refresh token (public endpoint).

**Request:**
```json
{
  "refreshToken": "eyJ..."
}
```

**Response:**
```json
{
  "success": true,
  "accessToken": "eyJ...",
  "refreshToken": "eyJ...",
  "expiresIn": 3600
}
```

**Status Codes:**
- `200 OK` - Token refreshed successfully
- `400 Bad Request` - Missing refresh token
- `401 Unauthorized` - Invalid or expired refresh token
- `500 Internal Server Error` - Server error

**Notes:**
- Validates existing refresh token
- Issues new access and refresh tokens
- Refresh tokens valid for 30 days

---

## System Seeding

### POST /seed

Seed all system data (subscription tiers, issue configs, settings, templates, dashboards).

**No Request Body**

**Response:**
```json
{
  "subscription_tiers": {
    "itemsCreated": 3,
    "itemsSkipped": 0,
    "errors": []
  },
  "issue_status_configs": {
    "itemsCreated": 8,
    "itemsSkipped": 0,
    "errors": []
  },
  "settings": {
    "itemsCreated": 15,
    "itemsSkipped": 0,
    "errors": []
  },
  "email_templates": {
    "itemsCreated": 10,
    "itemsSkipped": 0,
    "errors": []
  },
  "issue_type_configs": {
    "itemsCreated": 5,
    "itemsSkipped": 0,
    "errors": []
  },
  "dashboard_templates": {
    "itemsCreated": 3,
    "itemsSkipped": 0,
    "errors": []
  }
}
```

**Status Codes:**
- `200 OK` - Seeding completed

**Notes:**
- Idempotent operation (INSERT-IF-NOT-FOUND pattern)
- Safe to run multiple times
- Skips existing items
- Creates only new items
- Use individual endpoints for targeted seeding

---

### POST /seed/subscription-tiers

Seed subscription tier reference data (Basic, Professional, Enterprise).

**No Request Body**

**Response:**
```json
{
  "itemsCreated": 3,
  "itemsSkipped": 0,
  "errors": []
}
```

**Seeds:**
1. **Basic** - $9.99/month, $99.99/year (5 goals, 25 actions, basic features)
2. **Professional** - $29.99/month, $299.99/year (25 goals, 150 actions, advanced features)
3. **Enterprise** - $99.99/month, $999.99/year (unlimited resources, all features)

**Status Codes:**
- `200 OK` - Seeding completed

---

### POST /seed/issue-status-configs

Seed issue status configurations (Open, In Progress, Resolved, Closed, etc.).

**No Request Body**

**Response:**
```json
{
  "itemsCreated": 8,
  "itemsSkipped": 0,
  "errors": []
}
```

**Seeds:**
- Open (category: Open)
- In Progress (category: InProgress)
- Resolved (category: Resolved)
- Closed (category: Closed)
- Blocked (category: InProgress)
- On Hold (category: InProgress)
- Cannot Reproduce (category: Closed)
- Duplicate (category: Closed)

**Status Codes:**
- `200 OK` - Seeding completed

---

### POST /seed/settings

Seed system settings (auth, email, billing, maintenance configurations).

**No Request Body**

**Response:**
```json
{
  "itemsCreated": 15,
  "itemsSkipped": 0,
  "errors": []
}
```

**Seeds:**
- Auth settings (email verification, session timeout, password requirements, OAuth)
- Email settings (from address, verification expiry)
- Billing settings (trial period, default currency)
- System settings (maintenance mode, frontend base URL)

**Status Codes:**
- `200 OK` - Seeding completed

---

### POST /seed/email-templates

Seed email templates (verification, password reset, welcome, trial notifications, payment alerts).

**No Request Body**

**Response:**
```json
{
  "itemsCreated": 10,
  "itemsSkipped": 0,
  "errors": []
}
```

**Seeds 10 Templates:**
1. `email_verification` - Email verification (authentication)
2. `password_reset` - Password reset (authentication)
3. `welcome_email` - Welcome email (onboarding)
4. `username_changed` - Username change notification (authentication)
5. `trial_ending_soon` - Trial ending in 3 days (trial)
6. `trial_ending_tomorrow` - Trial ending tomorrow (trial)
7. `trial_expired` - Trial expired (trial)
8. `payment_failed` - Payment failure (payment)
9. `payment_retry` - Payment retry attempt (payment)
10. `subscription_suspended` - Subscription suspended (payment)

**Template Features:**
- RazorLight syntax (replaces Mustache `{{variable}}` with `@Model.Variable`)
- Structured variable definitions with types and requirements
- HTML and plain text versions
- Category-based organization
- Active by default

**Status Codes:**
- `200 OK` - Seeding completed

**Notes:**
- Templates use RazorLight engine
- Variables validated against schema
- Safe for repeated calls (won't overwrite existing)
- Use for initial setup or adding new templates

---

### POST /seed/issue-type-configs

Seed issue type configurations (Bug, Feature Request, Task, etc.).

**No Request Body**

**Response:**
```json
{
  "itemsCreated": 5,
  "itemsSkipped": 0,
  "errors": []
}
```

**Seeds:**
- Bug (system type, red color, bug icon)
- Feature Request (system type, blue color, feature icon)
- Task (system type, green color, task icon)
- Improvement (system type, yellow color, lightbulb icon)
- Question (system type, purple color, question icon)

**Status Codes:**
- `200 OK` - Seeding completed

---

### POST /seed/dashboard-templates

Seed dashboard templates (Default, Executive, Daily Operations).

**No Request Body**

**Response:**
```json
{
  "itemsCreated": 3,
  "itemsSkipped": 0,
  "errors": []
}
```

**Seeds:**
1. **Default Dashboard** - Goals + Actions (general users)
2. **Executive Overview** - Strategic goals, alignment, performance, AI insights
3. **Daily Operations** - Actions by status, hot list, issue list, recent activity

**Status Codes:**
- `200 OK` - Seeding completed

---

## Issue Type Configuration

System-level issue types managed by admins (tenant-level types not included).

### GET /issue-types

List all system issue type configurations.

**Query Parameters:**
- `includeInactive` (boolean, optional): Include inactive types (default: false)

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "tenantId": "SYSTEM",
    "name": "Bug",
    "description": "Software defect or error",
    "color": "#FF5252",
    "icon": "bug",
    "order": 1,
    "isActive": true,
    "isSystemType": true,
    "isDefault": true,
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-01-20T14:45:00Z"
  }
]
```

**Status Codes:**
- `200 OK` - Types retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token

---

### GET /issue-types/{id}

Get a single issue type configuration by ID.

**Path Parameters:**
- `id` (string, GUID) - Issue type ID

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "SYSTEM",
  "name": "Bug",
  "description": "Software defect or error",
  "color": "#FF5252",
  "icon": "bug",
  "order": 1,
  "isActive": true,
  "isSystemType": true,
  "isDefault": true,
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2025-01-20T14:45:00Z"
}
```

**Status Codes:**
- `200 OK` - Type retrieved successfully
- `400 Bad Request` - Invalid ID format
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue type not found or not a system type

---

### POST /issue-types

Create a new system issue type configuration.

**Request:**
```json
{
  "name": "Security Issue",
  "description": "Security vulnerability or concern",
  "color": "#FF0000",
  "icon": "shield",
  "order": 10,
  "isDefault": false
}
```

**Validations:**
- `name`: Required, 1-50 characters, unique within system types
- `description`: Optional, max 200 characters
- `color`: Required, valid hex color format (#RRGGBB)
- `icon`: Required, 1-30 characters
- `order`: Required, positive integer
- `isDefault`: Optional, boolean (only one default allowed)

**Response:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "tenantId": "SYSTEM",
  "name": "Security Issue",
  "description": "Security vulnerability or concern",
  "color": "#FF0000",
  "icon": "shield",
  "order": 10,
  "isActive": true,
  "isSystemType": true,
  "isDefault": false,
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T10:30:00Z"
}
```

**Status Codes:**
- `201 Created` - Issue type created successfully
- `400 Bad Request` - Invalid request data or duplicate name
- `401 Unauthorized` - Missing or invalid admin token

**Notes:**
- Automatically set as system type
- Tenant ID set to "SYSTEM"
- Initially active

---

### PUT /issue-types/{id}

Update an existing system issue type configuration.

**Path Parameters:**
- `id` (string, GUID) - Issue type ID

**Request:**
```json
{
  "name": "Critical Bug",
  "description": "High-priority software defect",
  "color": "#FF0000",
  "icon": "alert",
  "order": 1,
  "isDefault": true
}
```

**Validations:**
- All fields optional (partial updates supported)
- Same validation rules as POST

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "SYSTEM",
  "name": "Critical Bug",
  "description": "High-priority software defect",
  "color": "#FF0000",
  "icon": "alert",
  "order": 1,
  "isActive": true,
  "isSystemType": true,
  "isDefault": true,
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2026-02-04T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Issue type updated successfully
- `400 Bad Request` - Invalid request data or not a system type
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue type not found

---

### DELETE /issue-types/{id}

Soft delete an issue type configuration (sets isActive=false).

**Path Parameters:**
- `id` (string, GUID) - Issue type ID

**No Request Body**

**Response:**
```
204 No Content
```

**Status Codes:**
- `204 No Content` - Issue type deactivated successfully
- `400 Bad Request` - Invalid ID or not a system type
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue type not found

**Notes:**
- Soft delete only (sets isActive=false)
- Existing issues retain their type reference
- Use POST /issue-types/{id}/activate to restore

---

### POST /issue-types/{id}/activate

Activate (restore) a soft-deleted issue type.

**Path Parameters:**
- `id` (string, GUID) - Issue type ID

**No Request Body**

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "SYSTEM",
  "name": "Bug",
  "description": "Software defect or error",
  "color": "#FF5252",
  "icon": "bug",
  "order": 1,
  "isActive": true,
  "isSystemType": true,
  "isDefault": true,
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2026-02-04T11:15:00Z"
}
```

**Status Codes:**
- `200 OK` - Issue type activated successfully
- `400 Bad Request` - Invalid ID, not a system type, or already active
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue type not found

---

### POST /issue-types/{id}/set-default

Set an issue type as the default system type.

**Path Parameters:**
- `id` (string, GUID) - Issue type ID

**No Request Body**

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "tenantId": "SYSTEM",
  "name": "Task",
  "description": "General task or work item",
  "color": "#4CAF50",
  "icon": "task",
  "order": 3,
  "isActive": true,
  "isSystemType": true,
  "isDefault": true,
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2026-02-04T11:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Default set successfully
- `400 Bad Request` - Invalid ID or not a system type
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue type not found

**Notes:**
- Unsets previous default automatically
- Only one default allowed per tenant
- Must be active to set as default

---

## Issue Status Configuration

System-level issue statuses managed by admins.

### GET /issue-statuses

List all system issue status configurations.

**Query Parameters:**
- `includeInactive` (boolean, optional): Include inactive statuses (default: false)

**Response:**
```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "tenantId": null,
    "name": "Open",
    "category": "Open",
    "order": 1,
    "isSystemStatus": true,
    "isActive": true,
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-01-20T14:45:00Z"
  }
]
```

**Status Codes:**
- `200 OK` - Statuses retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token

---

### GET /issue-statuses/{id}

Get a single issue status configuration by ID.

**Path Parameters:**
- `id` (string, GUID) - Issue status ID

**Response:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440000",
  "tenantId": null,
  "name": "Open",
  "category": "Open",
  "order": 1,
  "isSystemStatus": true,
  "isActive": true,
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2025-01-20T14:45:00Z"
}
```

**Status Codes:**
- `200 OK` - Status retrieved successfully
- `400 Bad Request` - Invalid ID format
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue status not found or not a system status

---

### POST /issue-statuses

Create a new system issue status configuration.

**Request:**
```json
{
  "name": "Needs Review",
  "category": "InProgress",
  "order": 5,
  "description": "Waiting for review",
  "color": "#FFA726",
  "icon": "review"
}
```

**Validations:**
- `name`: Required, 1-50 characters, unique within system statuses
- `category`: Required, valid StatusCategory enum (Open, InProgress, Resolved, Closed)
- `order`: Required, positive integer
- `description`: Optional, max 200 characters
- `color`: Optional, valid hex color format
- `icon`: Optional, 1-30 characters

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "tenantId": null,
  "name": "Needs Review",
  "category": "InProgress",
  "order": 5,
  "isSystemStatus": true,
  "isActive": true,
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T10:30:00Z"
}
```

**Status Codes:**
- `201 Created` - Issue status created successfully
- `400 Bad Request` - Invalid request data or duplicate name
- `401 Unauthorized` - Missing or invalid admin token

---

### PUT /issue-statuses/{id}

Update an existing system issue status configuration.

**Path Parameters:**
- `id` (string, GUID) - Issue status ID

**Request:**
```json
{
  "name": "Under Review",
  "category": "InProgress",
  "order": 4,
  "description": "Currently under review",
  "color": "#FF9800",
  "icon": "magnify"
}
```

**Validations:**
- All fields optional (partial updates supported)
- Same validation rules as POST

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "tenantId": null,
  "name": "Under Review",
  "category": "InProgress",
  "order": 4,
  "isSystemStatus": true,
  "isActive": true,
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Issue status updated successfully
- `400 Bad Request` - Invalid request data or not a system status
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue status not found

---

### POST /issue-statuses/{id}/deactivate

Deactivate an issue status configuration (sets isActive=false).

**Path Parameters:**
- `id` (string, GUID) - Issue status ID

**No Request Body**

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "tenantId": null,
  "name": "Under Review",
  "category": "InProgress",
  "order": 4,
  "isSystemStatus": true,
  "isActive": false,
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T11:15:00Z"
}
```

**Status Codes:**
- `200 OK` - Issue status deactivated successfully
- `400 Bad Request` - Invalid ID, not a system status, or already inactive
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue status not found

---

### POST /issue-statuses/{id}/activate

Activate (restore) a deactivated issue status.

**Path Parameters:**
- `id` (string, GUID) - Issue status ID

**No Request Body**

**Response:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440000",
  "tenantId": null,
  "name": "Under Review",
  "category": "InProgress",
  "order": 4,
  "isSystemStatus": true,
  "isActive": true,
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T11:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Issue status activated successfully
- `400 Bad Request` - Invalid ID, not a system status, or already active
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Issue status not found

---

## Email Template Management

Comprehensive email template management system with RazorLight rendering engine.

### GET /email-templates

List all email templates with pagination and filtering.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `pageSize` (integer, optional): Items per page (default: 20, max: 100)
- `category` (string, optional): Filter by category
- `isActive` (boolean, optional): Filter by active status

**Response:**
```json
{
  "templates": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440000",
      "name": "email_verification",
      "subject": "Verify Your Email Address - PurposePath",
      "description": "Default email verification template",
      "category": "authentication",
      "language": "en",
      "isActive": true,
      "isDefault": false,
      "createdBy": "system",
      "createdAt": "2025-01-15T10:30:00Z",
      "updatedAt": "2025-01-20T14:45:00Z",
      "version": 1
    }
  ],
  "totalCount": 10,
  "currentPage": 1,
  "pageSize": 20
}
```

**Status Codes:**
- `200 OK` - Templates retrieved successfully
- `400 Bad Request` - Invalid pagination or filter parameters
- `401 Unauthorized` - Missing or invalid admin token

---

### GET /email-templates/{id}

Get a specific email template by ID.

**Path Parameters:**
- `id` (string, GUID) - Template ID

**Response:**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440000",
  "name": "email_verification",
  "subject": "Verify Your Email Address - PurposePath",
  "description": "Default email verification template",
  "category": "authentication",
  "htmlContent": "<!DOCTYPE html>...",
  "textContent": "Welcome to PurposePath!...",
  "variables": [
    {
      "name": "FirstName",
      "type": "String",
      "description": "Recipient first name",
      "required": true
    },
    {
      "name": "VerificationLink",
      "type": "Url",
      "description": "Email verification link",
      "required": true
    }
  ],
  "tags": ["verification", "onboarding"],
  "language": "en",
  "isActive": true,
  "isDefault": false,
  "isSystem": false,
  "version": 1,
  "createdBy": "system",
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2025-01-20T14:45:00Z"
}
```

**Status Codes:**
- `200 OK` - Template retrieved successfully
- `400 Bad Request` - Invalid ID format
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Template not found

---

### POST /email-templates

Create a new email template.

**Request:**
```json
{
  "name": "custom_welcome",
  "subject": "Welcome to Our Platform!",
  "description": "Custom welcome email for new users",
  "category": "onboarding",
  "htmlContent": "<!DOCTYPE html><html>...",
  "textContent": "Welcome {{firstName}}!...",
  "variables": [
    {
      "name": "FirstName",
      "type": "String",
      "description": "User's first name",
      "required": true
    }
  ],
  "tags": ["welcome", "custom"],
  "language": "en",
  "isActive": true
}
```

**Validations:**
- `name`: Required, unique, 1-100 characters, lowercase with underscores
- `subject`: Required, 1-200 characters
- `description`: Optional, max 500 characters
- `category`: Required, valid category (authentication, onboarding, trial, payment, subscription)
- `htmlContent`: Required, valid HTML
- `textContent`: Optional, plain text version
- `variables`: Required array, each with name, type, description, required flag
- `language`: Optional, ISO 639-1 code (default: "en")

**Response:**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "name": "custom_welcome",
  "subject": "Welcome to Our Platform!",
  "description": "Custom welcome email for new users",
  "category": "onboarding",
  "htmlContent": "<!DOCTYPE html><html>...",
  "textContent": "Welcome {{firstName}}!...",
  "variables": [...],
  "tags": ["welcome", "custom"],
  "language": "en",
  "isActive": true,
  "isDefault": false,
  "version": 1,
  "createdBy": "admin-user-id",
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T10:30:00Z"
}
```

**Status Codes:**
- `201 Created` - Template created successfully
- `400 Bad Request` - Invalid request data or duplicate name
- `401 Unauthorized` - Missing or invalid admin token

---

### PATCH /email-templates/{id}

Update an existing email template (partial update).

**Path Parameters:**
- `id` (string, GUID) - Template ID

**Request:**
```json
{
  "subject": "Updated Subject Line",
  "description": "Updated description",
  "htmlContent": "<!DOCTYPE html>...",
  "isActive": true
}
```

**Validations:**
- All fields optional (partial update)
- Same validation rules as POST for provided fields

**Response:**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440000",
  "name": "custom_welcome",
  "subject": "Updated Subject Line",
  "description": "Updated description",
  "category": "onboarding",
  "htmlContent": "<!DOCTYPE html>...",
  "textContent": "Welcome {{firstName}}!...",
  "variables": [...],
  "tags": ["welcome", "custom"],
  "language": "en",
  "isActive": true,
  "isDefault": false,
  "version": 2,
  "createdBy": "admin-user-id",
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Template updated successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Template not found

---

### POST /email-templates/{id}/clone

Clone an existing email template.

**Path Parameters:**
- `id` (string, GUID) - Source template ID

**Request:**
```json
{
  "newName": "custom_welcome_v2",
  "newDescription": "Cloned welcome email template",
  "newLanguage": "en"
}
```

**Response:**
```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440000",
  "name": "custom_welcome_v2",
  "subject": "Welcome to Our Platform!",
  "description": "Cloned welcome email template",
  "category": "onboarding",
  "htmlContent": "<!DOCTYPE html>...",
  "textContent": "Welcome {{firstName}}!...",
  "variables": [...],
  "tags": ["welcome", "custom"],
  "language": "en",
  "isActive": false,
  "isDefault": false,
  "version": 1,
  "createdBy": "admin-user-id",
  "createdAt": "2026-02-04T11:00:00Z",
  "updatedAt": "2026-02-04T11:00:00Z"
}
```

**Status Codes:**
- `201 Created` - Template cloned successfully
- `400 Bad Request` - Invalid source ID or duplicate new name
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Source template not found

**Notes:**
- Cloned templates start as inactive (isActive=false)
- All content and variables copied from source
- New template gets new ID and creation timestamp

---

### POST /email-templates/{id}/preview

Preview rendered email template with sample data.

**Path Parameters:**
- `id` (string, GUID) - Template ID

**Request:**
```json
{
  "previewData": {
    "FirstName": "John",
    "VerificationLink": "https://app.purposepath.com/verify?token=abc123"
  },
  "renderFormat": "html"
}
```

**Response:**
```json
{
  "renderedHtml": "<!DOCTYPE html><html>...<p>Hi John,</p>...",
  "renderedText": "Hi John,\n\nThank you for registering...",
  "subject": "Verify Your Email Address - PurposePath",
  "variables": [
    {
      "name": "FirstName",
      "value": "John",
      "provided": true
    },
    {
      "name": "VerificationLink",
      "value": "https://app.purposepath.com/verify?token=abc123",
      "provided": true
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Preview rendered successfully
- `400 Bad Request` - Invalid template ID or missing required variables
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Template not found

---

### POST /email-templates/{id}/test

Send test email using template.

**Path Parameters:**
- `id` (string, GUID) - Template ID

**Request:**
```json
{
  "testEmail": "admin@example.com",
  "testData": {
    "FirstName": "Test User",
    "VerificationLink": "https://app.purposepath.com/verify?token=test123"
  }
}
```

**Response:**
```json
{
  "success": true,
  "messageId": "550e8400-e29b-41d4-a716-446655440000",
  "sentTo": "admin@example.com",
  "sentAt": "2026-02-04T11:30:00Z"
}
```

**Status Codes:**
- `200 OK` - Test email sent successfully
- `400 Bad Request` - Invalid request data or missing variables
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Template not found
- `500 Internal Server Error` - Email delivery failure

---

### GET /email-templates/{id}/analytics

Get template usage analytics.

**Path Parameters:**
- `id` (string, GUID) - Template ID

**Response:**
```json
{
  "templateId": "990e8400-e29b-41d4-a716-446655440000",
  "templateName": "email_verification",
  "totalSent": 15420,
  "sentLast30Days": 1250,
  "sentLast7Days": 310,
  "sentToday": 45,
  "averageOpenRate": 72.5,
  "averageClickRate": 34.2,
  "lastSent": "2026-02-04T10:00:00Z",
  "mostRecentErrors": [
    {
      "errorMessage": "Invalid recipient email",
      "occurredAt": "2026-02-03T15:30:00Z",
      "count": 2
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Analytics retrieved successfully
- `400 Bad Request` - Invalid template ID
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Template not found

---

### DELETE /email-templates/{id}

Delete an email template (soft delete).

**Path Parameters:**
- `id` (string, GUID) - Template ID

**No Request Body**

**Response:**
```
204 No Content
```

**Status Codes:**
- `204 No Content` - Template deleted successfully
- `400 Bad Request` - Invalid ID or system template (cannot delete)
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Template not found

**Notes:**
- Soft delete only (sets isActive=false, retains data)
- System templates cannot be deleted
- Templates with active email sends retained for audit

---

### GET /email-templates/categories

Get list of available template categories.

**No Query Parameters**

**Response:**
```json
{
  "categories": [
    {
      "category": "authentication",
      "description": "Email verification and confirmation",
      "templateCount": 3
    },
    {
      "category": "onboarding",
      "description": "Welcome and onboarding emails",
      "templateCount": 1
    },
    {
      "category": "trial",
      "description": "Trial period notifications",
      "templateCount": 3
    },
    {
      "category": "payment",
      "description": "Payment and billing notifications",
      "templateCount": 3
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Categories retrieved successfully
- `401 Unauthorized` - Missing or invalid admin token

---

## Subscriber Management

Comprehensive tenant/subscriber management for viewing and managing customer subscriptions.

### GET /subscribers

Get paginated list of subscribers with filtering and sorting.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `pageSize` (integer, optional): Items per page (default: 50, max: 100)
- `search` (string, optional): Search by tenant name or email
- `status` (string, optional): Filter by subscription status (Active, Trial, Cancelled, Suspended)
- `tier` (string, GUID, optional): Filter by subscription tier ID
- `renewalFrequency` (string, optional): Filter by billing frequency (Monthly, Yearly)
- `sortBy` (string, optional): Sort field (Name, CreatedAt, Status, TierId, Frequency)
- `sortOrder` (string, optional): Sort direction (Ascending, Descending)

**Response:**
```json
{
  "items": [
    {
      "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
      "businessName": "Acme Corporation",
      "ownerEmail": "owner@acme.com",
      "ownerName": "John Doe",
      "subscription": {
        "id": "dd0e8400-e29b-41d4-a716-446655440000",
        "status": "Active",
        "tier": {
          "id": "550e8400-e29b-41d4-a716-446655440001",
          "name": "Professional",
          "displayName": "Professional"
        },
        "frequency": "Monthly",
        "startDate": "2025-01-15T00:00:00Z",
        "currentPeriodEnd": "2026-03-15T00:00:00Z",
        "autoRenew": true,
        "monthlyPrice": 29.99,
        "yearlyPrice": 299.99
      },
      "userCount": 5,
      "createdAt": "2025-01-15T10:30:00Z",
      "lastActivityAt": "2026-02-04T09:15:00Z"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "pageSize": 50,
    "totalCount": 342,
    "totalPages": 7
  }
}
```

**Status Codes:**
- `200 OK` - Subscribers retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token

**Notes:**
- Search performs case-insensitive match on business name and owner email
- All filters can be combined
- Results sorted by specified field and order
- Audit log entry created for admin action

---

### GET /subscribers/{tenantId}

Get detailed information about a specific subscriber.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Response:**
```json
{
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "businessName": "Acme Corporation",
  "website": "https://acme.com",
  "industry": "Technology",
  "address": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "postalCode": "94105",
    "country": "USA"
  },
  "owner": {
    "userId": "ee0e8400-e29b-41d4-a716-446655440000",
    "email": "owner@acme.com",
    "firstName": "John",
    "lastName": "Doe",
    "createdAt": "2025-01-15T10:30:00Z"
  },
  "subscription": {
    "id": "dd0e8400-e29b-41d4-a716-446655440000",
    "status": "Active",
    "tier": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Professional",
      "displayName": "Professional",
      "features": ["Goals", "Operations", "Measures", "Strategies", "Realtime"],
      "limits": {
        "goals": 25,
        "actions": 150,
        "strategies": 15
      }
    },
    "frequency": "Monthly",
    "startDate": "2025-01-15T00:00:00Z",
    "currentPeriodStart": "2026-02-15T00:00:00Z",
    "currentPeriodEnd": "2026-03-15T00:00:00Z",
    "trialEnd": null,
    "autoRenew": true,
    "cancelAt": null,
    "cancelledAt": null,
    "monthlyPrice": 29.99,
    "yearlyPrice": 299.99,
    "currency": "USD"
  },
  "usage": {
    "userCount": 5,
    "goalCount": 12,
    "actionCount": 87,
    "measureCount": 24
  },
  "featureGrants": [
    {
      "featureCode": "BulkPlanner",
      "grantedAt": "2025-06-01T00:00:00Z",
      "expiresAt": "2026-06-01T00:00:00Z",
      "reason": "Beta tester access"
    }
  ],
  "paymentMethod": {
    "type": "card",
    "last4": "4242",
    "brand": "Visa",
    "expiryMonth": 12,
    "expiryYear": 2027
  },
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2026-02-04T09:15:00Z",
  "lastActivityAt": "2026-02-04T09:15:00Z"
}
```

**Status Codes:**
- `200 OK` - Subscriber details retrieved successfully
- `400 Bad Request` - Invalid tenant ID format
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant not found

**Notes:**
- Provides comprehensive view of tenant, subscription, usage, and payment details
- Includes granted features beyond tier
- Shows current billing period and renewal status
- Audit log entry created

---

## Plan Management

Subscription tier/plan management including creation, updates, and deactivation.

### GET /plans

Get paginated list of subscription plans.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `pageSize` (integer, optional): Items per page (default: 20, max: 100)
- `isActive` (boolean, optional): Filter by active status
- `includeUsage` (boolean, optional): Include subscriber counts (default: false)

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Professional",
      "displayName": "Professional",
      "description": "Designed for growing teams...",
      "monthlyPrice": 29.99,
      "yearlyPrice": 299.99,
      "currency": "USD",
      "isActive": true,
      "sortOrder": 2,
      "subscriberCount": 142,
      "createdAt": "2025-01-01T00:00:00Z",
      "updatedAt": "2025-12-15T10:00:00Z"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "pageSize": 20,
    "totalCount": 3,
    "totalPages": 1
  }
}
```

**Status Codes:**
- `200 OK` - Plans retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token

---

### GET /plans/{id}

Get detailed information about a specific plan.

**Path Parameters:**
- `id` (string, GUID) - Plan ID

**Query Parameters:**
- `includeUsage` (boolean, optional): Include detailed usage statistics (default: false)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Professional",
  "displayName": "Professional",
  "description": "Designed for growing teams that need advanced features...",
  "pricing": {
    "monthlyPrice": 29.99,
    "yearlyPrice": 299.99,
    "currency": "USD"
  },
  "features": [
    "Goals",
    "Operations",
    "Measures",
    "Strategies",
    "Realtime",
    "Reports",
    "Attachments",
    "BulkPlanner",
    "StrategyCompare"
  ],
  "limits": {
    "goals": 25,
    "actions": 150,
    "strategies": 15,
    "measures": 50,
    "attachments": 250,
    "reports": 25
  },
  "supportedFrequencies": ["Monthly", "Yearly"],
  "isActive": true,
  "sortOrder": 2,
  "usage": {
    "totalSubscribers": 142,
    "activeSubscribers": 138,
    "trialSubscribers": 4,
    "monthlyRevenue": 4137.62,
    "yearlyRevenue": 0,
    "totalRevenue": 4137.62
  },
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2025-12-15T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Plan details retrieved successfully
- `400 Bad Request` - Invalid plan ID format
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Plan not found

---

### POST /plans

Create a new subscription plan.

**Request:**
```json
{
  "name": "Enterprise",
  "displayName": "Enterprise",
  "description": "Unlimited power for large organizations...",
  "pricing": {
    "monthlyPrice": 99.99,
    "yearlyPrice": 999.99,
    "currency": "USD"
  },
  "features": [
    "Goals",
    "Operations",
    "Measures",
    "Strategies",
    "Realtime",
    "Reports",
    "Attachments",
    "BulkPlanner",
    "StrategyCompare",
    "GoalCreate"
  ],
  "limits": {
    "goals": null,
    "actions": null,
    "strategies": null,
    "measures": null,
    "attachments": null,
    "reports": null
  },
  "supportedFrequencies": ["Monthly", "Yearly"],
  "isActive": true,
  "sortOrder": 3
}
```

**Validations:**
- `name`: Required, unique, 1-50 characters, PascalCase
- `displayName`: Required, 1-100 characters
- `description`: Required, 1-500 characters
- `pricing.monthlyPrice`: Required, positive decimal
- `pricing.yearlyPrice`: Required, positive decimal
- `pricing.currency`: Required, 3-letter ISO currency code
- `features`: Required array of valid FeatureName enums
- `limits`: Object with integer values or null (unlimited)
- `supportedFrequencies`: Required array, at least one frequency
- `sortOrder`: Required, positive integer

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "name": "Enterprise",
  "displayName": "Enterprise",
  "description": "Unlimited power for large organizations...",
  "pricing": {
    "monthlyPrice": 99.99,
    "yearlyPrice": 999.99,
    "currency": "USD"
  },
  "features": [...],
  "limits": {...},
  "supportedFrequencies": ["Monthly", "Yearly"],
  "isActive": true,
  "sortOrder": 3,
  "createdAt": "2026-02-04T10:30:00Z",
  "updatedAt": "2026-02-04T10:30:00Z"
}
```

**Status Codes:**
- `201 Created` - Plan created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `409 Conflict` - Plan name already exists

**Notes:**
- Creates new plan immediately available for subscriptions
- Audit log entry created
- Admin user ID tracked in metadata

---

### PUT /plans/{id}

Update an existing subscription plan.

**Path Parameters:**
- `id` (string, GUID) - Plan ID

**Request:**
```json
{
  "displayName": "Professional Plus",
  "description": "Enhanced professional tier...",
  "pricing": {
    "monthlyPrice": 34.99,
    "yearlyPrice": 349.99,
    "currency": "USD"
  },
  "features": [...],
  "limits": {...},
  "supportedFrequencies": ["Monthly", "Yearly"],
  "isActive": true,
  "sortOrder": 2
}
```

**Validations:**
- All fields optional (partial update)
- Same validation rules as POST for provided fields
- `name` cannot be changed (immutable)

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "name": "Professional",
  "displayName": "Professional Plus",
  "description": "Enhanced professional tier...",
  "pricing": {
    "monthlyPrice": 34.99,
    "yearlyPrice": 349.99,
    "currency": "USD"
  },
  "features": [...],
  "limits": {...},
  "supportedFrequencies": ["Monthly", "Yearly"],
  "isActive": true,
  "sortOrder": 2,
  "createdAt": "2025-01-01T00:00:00Z",
  "updatedAt": "2026-02-04T11:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Plan updated successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Plan not found

**Notes:**
- Existing subscriptions retain current pricing
- New subscriptions use updated pricing
- Feature/limit changes require validation
- Breaking changes flagged in audit log

---

### POST /plans/{id}/deactivate

Deactivate a subscription plan with grandfathering or migration options.

**Path Parameters:**
- `id` (string, GUID) - Plan ID

**Request:**
```json
{
  "grandfatherExisting": true,
  "migrationPlanId": "550e8400-e29b-41d4-a716-446655440002",
  "effectiveDate": "2026-03-01T00:00:00Z",
  "reason": "Plan consolidation - migrating to Enterprise tier"
}
```

**Validations:**
- `grandfatherExisting`: Required, boolean
- `migrationPlanId`: Optional GUID (required if grandfatherExisting=false)
- `effectiveDate`: Optional ISO 8601 date (default: immediate)
- `reason`: Required, 1-500 characters

**Response:**
```json
{
  "planId": "550e8400-e29b-41d4-a716-446655440001",
  "planName": "Professional",
  "deactivated": true,
  "effectiveDate": "2026-03-01T00:00:00Z",
  "grandfatheredSubscribers": 142,
  "migrationPlanId": "550e8400-e29b-41d4-a716-446655440002",
  "migratedSubscribers": 0,
  "reason": "Plan consolidation - migrating to Enterprise tier",
  "deactivatedAt": "2026-02-04T11:00:00Z",
  "deactivatedBy": "admin-user-id"
}
```

**Status Codes:**
- `200 OK` - Plan deactivated successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Plan not found

**Notes:**
- If `grandfatherExisting=true`: Existing subscribers keep plan
- If `grandfatherExisting=false`: Requires migration plan for active subscribers
- Deactivated plans hidden from new subscriptions
- Audit log entry tracks reason and affected subscribers

---

### DELETE /plans/{id}

Delete a subscription plan (with safety checks).

**Path Parameters:**
- `id` (string, GUID) - Plan ID

**No Request Body**

**Response:**
```
204 No Content
```

**Status Codes:**
- `204 No Content` - Plan deleted successfully
- `400 Bad Request` - Invalid plan ID
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Plan not found
- `409 Conflict` - Plan has active subscriptions (cannot delete)

**Restrictions:**
- Can ONLY delete plans with zero active subscriptions
- Plans with subscription history must be deactivated instead
- System default plans cannot be deleted

**Notes:**
- Hard delete (permanent removal)
- Use POST /plans/{id}/deactivate for plans with subscribers
- Audit log entry created before deletion

---

### POST /plans/{id}/validate

Validate plan updates before applying to check for breaking changes.

**Path Parameters:**
- `id` (string, GUID) - Plan ID

**Request:**
```json
{
  "displayName": "Professional Plus",
  "pricing": {
    "monthlyPrice": 34.99,
    "yearlyPrice": 349.99,
    "currency": "USD"
  },
  "features": [...],
  "limits": {...}
}
```

**Response:**
```json
{
  "isValid": true,
  "warnings": [],
  "breakingChanges": [
    {
      "type": "FeatureRemoval",
      "description": "Removing feature 'Realtime' will affect 45 subscribers",
      "affectedCount": 45,
      "severity": "High"
    },
    {
      "type": "LimitReduction",
      "description": "Reducing goal limit from 25 to 15 will affect 12 subscribers exceeding new limit",
      "affectedCount": 12,
      "severity": "Medium"
    }
  ],
  "nonBreakingChanges": [
    {
      "type": "PriceIncrease",
      "description": "Monthly price increasing from $29.99 to $34.99",
      "affectedCount": 142,
      "severity": "Low"
    }
  ],
  "recommendations": [
    "Consider grandfathering existing subscribers on current pricing",
    "Notify affected subscribers 30 days before feature removal",
    "Provide migration path for subscribers exceeding new limits"
  ]
}
```

**Status Codes:**
- `200 OK` - Validation completed
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Plan not found

**Notes:**
- Non-destructive validation only
- Checks for breaking changes and affected subscribers
- Provides recommendations for safe rollout
- Use before applying changes to production plans

---

### GET /plans/{id}/affected-subscribers

Get count of subscribers affected by a plan.

**Path Parameters:**
- `id` (string, GUID) - Plan ID

**Response:**
```json
{
  "planId": "550e8400-e29b-41d4-a716-446655440001",
  "planName": "Professional",
  "totalSubscribers": 142,
  "activeSubscribers": 138,
  "trialSubscribers": 4,
  "cancelledSubscribers": 0,
  "suspendedSubscribers": 0,
  "subscribersByFrequency": {
    "Monthly": 120,
    "Yearly": 22
  },
  "revenueImpact": {
    "monthlyRevenue": 4137.62,
    "yearlyRevenue": 0,
    "projectedAnnualRevenue": 49651.44
  }
}
```

**Status Codes:**
- `200 OK` - Affected subscribers retrieved successfully
- `400 Bad Request` - Invalid plan ID
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Plan not found

---

## Feature Management

Manage system features and tenant-specific feature grants.

### GET /features

Get list of all available system features.

**No Query Parameters**

**Response:**
```json
{
  "features": [
    {
      "code": "Goals",
      "name": "Goal Management",
      "description": "Create and track strategic goals",
      "category": "Core"
    },
    {
      "code": "Operations",
      "name": "Operations Management",
      "description": "Manage actions and issues",
      "category": "Core"
    },
    {
      "code": "Measures",
      "name": "MEASURE Management",
      "description": "Track and analyze MEASUREs",
      "category": "Core"
    },
    {
      "code": "Realtime",
      "name": "Real-time Collaboration",
      "description": "Real-time updates via SSE",
      "category": "Advanced"
    },
    {
      "code": "BulkPlanner",
      "name": "Bulk Planning",
      "description": "Bulk create actions and strategies",
      "category": "Premium"
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Features retrieved successfully
- `401 Unauthorized` - Missing or invalid admin token

---

### GET /features/tiers

Get feature matrix for all subscription tiers.

**No Query Parameters**

**Response:**
```json
{
  "tiers": [
    {
      "tierId": "550e8400-e29b-41d4-a716-446655440000",
      "tierName": "Basic",
      "features": ["Goals", "Operations", "Measures"]
    },
    {
      "tierId": "550e8400-e29b-41d4-a716-446655440001",
      "tierName": "Professional",
      "features": [
        "Goals",
        "Operations",
        "Measures",
        "Strategies",
        "Realtime",
        "Reports",
        "Attachments",
        "BulkPlanner",
        "StrategyCompare"
      ]
    },
    {
      "tierId": "550e8400-e29b-41d4-a716-446655440002",
      "tierName": "Enterprise",
      "features": [
        "Goals",
        "Operations",
        "Measures",
        "Strategies",
        "Realtime",
        "Reports",
        "Attachments",
        "BulkPlanner",
        "StrategyCompare",
        "GoalCreate"
      ]
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Tier features retrieved successfully
- `401 Unauthorized` - Missing or invalid admin token

---

### PUT /features/tiers/{tierId}

Update features for a subscription tier.

**Path Parameters:**
- `tierId` (string, GUID) - Tier ID

**Request:**
```json
{
  "features": [
    "Goals",
    "Operations",
    "Measures",
    "Strategies",
    "Realtime",
    "Reports"
  ],
  "reason": "Removing premium features for tier consolidation"
}
```

**Validations:**
- `features`: Required array of valid FeatureName enums
- `reason`: Required, 1-500 characters (audit trail)

**Response:**
```json
{
  "tierId": "550e8400-e29b-41d4-a716-446655440001",
  "tierName": "Professional",
  "features": [
    "Goals",
    "Operations",
    "Measures",
    "Strategies",
    "Realtime",
    "Reports"
  ],
  "affectedSubscribers": 142,
  "removedFeatures": ["BulkPlanner", "StrategyCompare"],
  "addedFeatures": [],
  "updatedAt": "2026-02-04T11:00:00Z",
  "updatedBy": "admin-user-id",
  "reason": "Removing premium features for tier consolidation"
}
```

**Status Codes:**
- `200 OK` - Tier features updated successfully
- `400 Bad Request` - Invalid request data or invalid feature codes
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tier not found

**Notes:**
- Changes apply to all subscribers immediately
- Removed features disabled for all tenants on tier
- Added features enabled for all tenants on tier
- Audit log entry tracks changes and reason
- Breaking changes require admin confirmation

---

### POST /features/tiers/{tierId}/validate

Validate tier feature changes before applying.

**Path Parameters:**
- `tierId` (string, GUID) - Tier ID

**Request:**
```json
{
  "features": [
    "Goals",
    "Operations",
    "Measures",
    "Strategies",
    "Realtime",
    "Reports"
  ]
}
```

**Response:**
```json
{
  "isValid": true,
  "warnings": [],
  "breakingChanges": [
    {
      "type": "FeatureRemoval",
      "feature": "BulkPlanner",
      "affectedSubscribers": 45,
      "description": "45 subscribers currently using Bulk Planning feature"
    },
    {
      "type": "FeatureRemoval",
      "feature": "StrategyCompare",
      "affectedSubscribers": 28,
      "description": "28 subscribers currently using Strategy Comparison feature"
    }
  ],
  "addedFeatures": [],
  "removedFeatures": ["BulkPlanner", "StrategyCompare"],
  "affectedSubscribers": 142,
  "recommendations": [
    "Notify affected subscribers 30 days before feature removal",
    "Consider offering feature grants to power users",
    "Provide alternative workflows for removed features"
  ]
}
```

**Status Codes:**
- `200 OK` - Validation completed
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tier not found

---

### GET /features/tenants/{tenantId}/grants

Get tenant-specific feature grants.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Response:**
```json
{
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "businessName": "Acme Corporation",
  "tierFeatures": ["Goals", "Operations", "Measures"],
  "grants": [
    {
      "grantId": "ff0e8400-e29b-41d4-a716-446655440000",
      "featureCode": "BulkPlanner",
      "featureName": "Bulk Planning",
      "grantedAt": "2025-06-01T00:00:00Z",
      "expiresAt": "2026-06-01T00:00:00Z",
      "grantedBy": "admin-user-id",
      "reason": "Beta tester access",
      "isActive": true,
      "isExpired": false
    }
  ],
  "totalGrants": 1,
  "activeGrants": 1,
  "expiredGrants": 0
}
```

**Status Codes:**
- `200 OK` - Feature grants retrieved successfully
- `400 Bad Request` - Invalid tenant ID
- `401 Unauthorized` - Missing or invalid admin token

---

### POST /features/tenants/{tenantId}/grants

Add a tenant-specific feature grant.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Request:**
```json
{
  "feature": "BulkPlanner",
  "expiresWithPlan": false,
  "customExpirationDate": "2026-12-31T23:59:59Z",
  "reason": "Promotional access for annual contract"
}
```

**Validations:**
- `feature`: Required, valid FeatureName enum
- `expiresWithPlan`: Required, boolean (if true, grant expires with subscription)
- `customExpirationDate`: Optional ISO 8601 date (required if expiresWithPlan=false)
- `reason`: Required, 1-500 characters

**Response:**
```json
{
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "businessName": "Acme Corporation",
  "tierFeatures": ["Goals", "Operations", "Measures"],
  "grants": [
    {
      "grantId": "ff0e8400-e29b-41d4-a716-446655440001",
      "featureCode": "BulkPlanner",
      "featureName": "Bulk Planning",
      "grantedAt": "2026-02-04T11:00:00Z",
      "expiresAt": "2026-12-31T23:59:59Z",
      "grantedBy": "admin-user-id",
      "reason": "Promotional access for annual contract",
      "isActive": true,
      "isExpired": false
    }
  ],
  "totalGrants": 1,
  "activeGrants": 1,
  "expiredGrants": 0
}
```

**Status Codes:**
- `201 Created` - Feature grant added successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `409 Conflict` - Feature already granted or included in tier

**Notes:**
- Grants override tier restrictions
- Expiration handled automatically
- Audit log entry created
- Feature enabled immediately for tenant

---

### DELETE /features/tenants/{tenantId}/grants/{feature}

Remove a tenant-specific feature grant.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID
- `feature` (string) - Feature code

**Request:**
```json
{
  "reason": "End of promotional period"
}
```

**Validations:**
- `reason`: Required, 1-500 characters

**Response:**
```
204 No Content
```

**Status Codes:**
- `204 No Content` - Feature grant removed successfully
- `400 Bad Request` - Invalid tenant ID or feature code
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - No active grant found for feature

**Notes:**
- Immediately revokes feature access
- Audit log entry created
- Cannot remove tier-included features

---

### GET /features/tenants/{tenantId}/effective

Get effective features for a tenant (tier + grants).

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Response:**
```json
{
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "businessName": "Acme Corporation",
  "tier": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Basic",
    "features": ["Goals", "Operations", "Measures"]
  },
  "grants": [
    {
      "featureCode": "BulkPlanner",
      "source": "Grant",
      "expiresAt": "2026-06-01T00:00:00Z"
    }
  ],
  "effectiveFeatures": [
    {
      "code": "Goals",
      "source": "Tier"
    },
    {
      "code": "Operations",
      "source": "Tier"
    },
    {
      "code": "Measures",
      "source": "Tier"
    },
    {
      "code": "BulkPlanner",
      "source": "Grant",
      "expiresAt": "2026-06-01T00:00:00Z"
    }
  ],
  "totalFeatures": 4
}
```

**Status Codes:**
- `200 OK` - Effective features retrieved successfully
- `400 Bad Request` - Invalid tenant ID
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant not found

---

## Subscription Operations

Administrative subscription management operations (trials, discounts, billing extensions).

### POST /subscriptions/{tenantId}/extend-trial

Extend subscription trial period.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Request:**
```json
{
  "newExpirationDate": "2026-03-15T23:59:59Z",
  "reason": "Customer requested additional time for evaluation"
}
```

**Validations:**
- `newExpirationDate`: Required, ISO 8601 date, future date, after current trial end
- `reason`: Required, 1-500 characters

**Response:**
```json
{
  "subscriptionId": "dd0e8400-e29b-41d4-a716-446655440000",
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "previousTrialEnd": "2026-02-15T23:59:59Z",
  "newTrialEnd": "2026-03-15T23:59:59Z",
  "daysExtended": 28,
  "reason": "Customer requested additional time for evaluation",
  "extendedAt": "2026-02-04T11:00:00Z",
  "extendedBy": "admin-user-id"
}
```

**Status Codes:**
- `200 OK` - Trial extended successfully
- `400 Bad Request` - Invalid request data or subscription not in trial
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant or subscription not found

**Notes:**
- Only applies to subscriptions in trial status
- Extends trial period without changing billing
- Audit log entry created
- Email notification sent to tenant owner

---

### POST /subscriptions/{tenantId}/apply-discount

Apply ad-hoc discount to subscription.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Request:**
```json
{
  "discountType": "Percentage",
  "value": 25,
  "cyclesToApply": 3,
  "reason": "Customer service recovery - service outage compensation"
}
```

**Validations:**
- `discountType`: Required, enum (Percentage, FixedAmount)
- `value`: Required, positive decimal
  - Percentage: 1-100
  - FixedAmount: positive amount in subscription currency
- `cyclesToApply`: Required, positive integer (number of billing cycles)
- `reason`: Required, 1-500 characters

**Response:**
```json
{
  "subscriptionId": "dd0e8400-e29b-41d4-a716-446655440000",
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "discountType": "Percentage",
  "value": 25,
  "cyclesToApply": 3,
  "currentPrice": 29.99,
  "discountedPrice": 22.49,
  "totalSavings": 22.50,
  "startsAt": "2026-02-15T00:00:00Z",
  "endsAt": "2026-05-15T00:00:00Z",
  "reason": "Customer service recovery - service outage compensation",
  "appliedAt": "2026-02-04T11:00:00Z",
  "appliedBy": "admin-user-id"
}
```

**Status Codes:**
- `200 OK` - Discount applied successfully
- `400 Bad Request` - Invalid request data or subscription not active
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant or subscription not found

**Notes:**
- Applies to next N billing cycles
- Automatically removes after specified cycles
- Audit log entry created
- Email confirmation sent to tenant

---

### POST /subscriptions/{tenantId}/extend-billing

Extend billing period (skip payment cycles as credit).

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Request:**
```json
{
  "monthsToExtend": 3,
  "reason": "Compensation for platform issues during Q1"
}
```

**Validations:**
- `monthsToExtend`: Required, positive integer (1-12)
- `reason`: Required, 1-500 characters

**Response:**
```json
{
  "subscriptionId": "dd0e8400-e29b-41d4-a716-446655440000",
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "monthsExtended": 3,
  "previousPeriodEnd": "2026-03-15T00:00:00Z",
  "newPeriodEnd": "2026-06-15T00:00:00Z",
  "creditValue": 89.97,
  "reason": "Compensation for platform issues during Q1",
  "extendedAt": "2026-02-04T11:00:00Z",
  "extendedBy": "admin-user-id"
}
```

**Status Codes:**
- `200 OK` - Billing extended successfully
- `400 Bad Request` - Invalid request data or subscription not active
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant or subscription not found

**Notes:**
- Extends subscription without payment
- Credit applied as billing period extension
- Maintains same subscription tier and features
- Audit log entry created
- Email notification sent to tenant

---

### POST /subscriptions/{tenantId}/grant-feature

Grant feature to subscription (uses TenantFeatureGrant).

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Request:**
```json
{
  "feature": "BulkPlanner",
  "expiresAt": "2026-06-01T00:00:00Z",
  "reason": "Beta testing program participant"
}
```

**Validations:**
- `feature`: Required, valid FeatureName enum
- `expiresAt`: Optional ISO 8601 date (null for permanent)
- `reason`: Required, 1-500 characters

**Response:**
```json
{
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "featureCode": "BulkPlanner",
  "featureName": "Bulk Planning",
  "grantedAt": "2026-02-04T11:00:00Z",
  "expiresAt": "2026-06-01T00:00:00Z",
  "reason": "Beta testing program participant",
  "grantedBy": "admin-user-id"
}
```

**Status Codes:**
- `200 OK` - Feature granted successfully
- `400 Bad Request` - Invalid request data or feature already granted
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant not found

**Notes:**
- Same as POST /features/tenants/{tenantId}/grants
- Provided for convenience in subscription context
- See Feature Management section for details

---

### POST /subscriptions/{tenantId}/designate-test

Designate subscription as test account.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Request:**
```json
{
  "isTest": true,
  "reason": "Internal testing environment"
}
```

**Validations:**
- `isTest`: Required, boolean
- `reason`: Required, 1-500 characters

**Response:**
```json
{
  "subscriptionId": "dd0e8400-e29b-41d4-a716-446655440000",
  "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
  "isTest": true,
  "previousStatus": false,
  "reason": "Internal testing environment",
  "updatedAt": "2026-02-04T11:00:00Z",
  "updatedBy": "admin-user-id"
}
```

**Status Codes:**
- `200 OK` - Test status updated successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant or subscription not found

**Notes:**
- Test accounts excluded from billing and analytics
- Flagged in reports and dashboards
- Can be toggled on/off
- Audit log entry created

---

### GET /subscriptions/{tenantId}/audit-log

Get subscription audit log.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `pageSize` (integer, optional): Items per page (default: 50, max: 100)
- `actionType` (string, optional): Filter by action type
- `from` (datetime, optional): Start date filter (ISO 8601)
- `to` (datetime, optional): End date filter (ISO 8601)

**Response:**
```json
{
  "entries": [
    {
      "id": "audit-550e8400-e29b-41d4-a716-446655440000",
      "tenantId": "cc0e8400-e29b-41d4-a716-446655440000",
      "actionType": "ExtendTrial",
      "description": "Extended trial period from 2026-02-15 to 2026-03-15",
      "performedBy": "admin-user-id",
      "performedByName": "Admin User",
      "reason": "Customer requested additional time for evaluation",
      "metadata": {
        "previousTrialEnd": "2026-02-15T23:59:59Z",
        "newTrialEnd": "2026-03-15T23:59:59Z",
        "daysExtended": 28
      },
      "performedAt": "2026-02-04T11:00:00Z"
    }
  ],
  "pagination": {
    "currentPage": 1,
    "pageSize": 50,
    "totalCount": 127,
    "totalPages": 3
  }
}
```

**Status Codes:**
- `200 OK` - Audit log retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant not found

**Notes:**
- Complete audit trail of all admin actions
- Filterable by action type and date range
- Includes admin user details and reasons
- Metadata contains action-specific details

---

## System Settings Management

These endpoints manage system-wide configuration settings for the PurposePath platform. Settings control operational parameters, security policies, email configuration, payment processing, and feature flags.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `Content-Type: application/json`

---

### GET /settings

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

### GET /settings/{key}

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

### PATCH /settings/{key}

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

### POST /settings/{key}/validate

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

### POST /settings/{key}/reset

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

## Role Template Management

These endpoints manage organizational role templates that tenants can use to quickly set up their organizational structure. Templates contain predefined roles with reporting hierarchies.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `Content-Type: application/json`

---

### GET /role-templates

Get list of all role templates with optional filtering.

**Query Parameters:**

- `search` (string, optional) - Search by template name
- `category` (string, optional) - Filter by category ("STARTUP", "SMB", "ENTERPRISE", "EOS", "SCALING")
- `is_active` (boolean, optional) - Filter by active status

**Response (200 OK):**

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Technology Startup",
      "description": "Basic organizational structure for tech startups",
      "category": "STARTUP",
      "roles_count": 8,
      "is_active": true,
      "preview": {
        "total_roles": 8,
        "sample_roles": ["CEO", "CTO", "CFO"]
      },
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-02-01T14:30:00Z"
    }
  ]
}
```

**Status Codes:**

- `200 OK` - Templates retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `RoleTemplatesController.ListTemplates()`
- Query: `ListRoleTemplatesQuery`
- Handler: `ListRoleTemplatesQueryHandler`

---

### GET /role-templates/{id}

Get a specific role template with all its roles.

**Path Parameters:**

- `id` (string, GUID) - Template ID

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Technology Startup",
    "description": "Complete organizational structure for tech startups",
    "category": "STARTUP",
    "is_active": true,
    "roles": [
      {
        "id": "role-uuid",
        "code": "CEO",
        "name": "Chief Executive Officer",
        "description": "Leads the company",
        "responsibilities": "Set vision, manage executives...",
        "reports_to_code": null,
        "created_at": "2026-01-15T10:00:00Z"
      },
      {
        "id": "role-uuid-2",
        "code": "CTO",
        "name": "Chief Technology Officer",
        "description": "Oversees technology",
        "responsibilities": "Manage tech stack, lead dev team...",
        "reports_to_code": "CEO",
        "created_at": "2026-01-15T10:05:00Z"
      }
    ],
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-02-01T14:30:00Z"
  }
}
```

**Status Codes:**

- `200 OK` - Template retrieved successfully
- `400 Bad Request` - Invalid template ID format
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Template not found
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `RoleTemplatesController.GetTemplate()`
- Query: `GetRoleTemplateQuery`
- Handler: `GetRoleTemplateQueryHandler`

---

### POST /role-templates

Create a new role template.

**Request Body:**

```json
{
  "name": "Technology Startup",
  "description": "Basic tech startup org structure",
  "category": "STARTUP",
  "is_active": true
}
```

**Validation Rules:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | Yes | 1-100 characters, unique |
| `description` | string | No | Max 500 characters |
| `category` | string | Yes | Enum: "STARTUP", "SMB", "ENTERPRISE", "EOS", "SCALING" |
| `is_active` | boolean | No | Default: true |

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "new-uuid",
    "name": "Technology Startup",
    "description": "Basic tech startup org structure",
    "category": "STARTUP",
    "is_active": true,
    "roles": [],
    "created_at": "2026-02-05T15:00:00Z",
    "updated_at": "2026-02-05T15:00:00Z"
  }
}
```

**Status Codes:**

- `201 Created` - Template created successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `409 Conflict` - Template name already exists
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `RoleTemplatesController.CreateTemplate()`
- Command: `CreateRoleTemplateCommand`
- Handler: `CreateRoleTemplateCommandHandler`

---

### PUT /role-templates/{id}

Update an existing role template.

**Path Parameters:**

- `id` (string, GUID) - Template ID

**Request Body:**

```json
{
  "name": "Updated Template Name",
  "description": "Updated description",
  "category": "ENTERPRISE",
  "is_active": false
}
```

**Notes:**

- All fields are optional (partial update supported)
- Cannot change template ID

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Updated Template Name",
    "description": "Updated description",
    "category": "ENTERPRISE",
    "is_active": false,
    "roles": [...],
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-02-05T15:30:00Z"
  }
}
```

**Status Codes:**

- `200 OK` - Template updated successfully
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Template not found
- `409 Conflict` - Duplicate name
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `RoleTemplatesController.UpdateTemplate()`
- Command: `UpdateRoleTemplateCommand`
- Handler: `UpdateRoleTemplateCommandHandler`

---

### DELETE /role-templates/{id}

Delete a role template.

**Path Parameters:**

- `id` (string, GUID) - Template ID

**Response:**

```
204 No Content
```

**Status Codes:**

- `204 No Content` - Template deleted successfully
- `400 Bad Request` - Invalid template ID
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Template not found
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `RoleTemplatesController.DeleteTemplate()`
- Command: `DeleteRoleTemplateCommand`
- Handler: `DeleteRoleTemplateCommandHandler`

---

### POST /role-templates/{id}/roles

Add a role to a template.

**Path Parameters:**

- `id` (string, GUID) - Template ID

**Request Body:**

```json
{
  "code": "VP_SALES",
  "name": "Vice President of Sales",
  "description": "Leads sales team",
  "responsibilities": "* Drive revenue\n* Manage team\n* Set targets",
  "reports_to_code": "CEO"
}
```

**Validation Rules:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `code` | string | Yes | 2-50 chars, uppercase, alphanumeric + underscore, unique within template |
| `name` | string | Yes | 1-100 characters |
| `description` | string | No | Max 500 characters |
| `responsibilities` | string | No | Max 2000 characters, markdown supported |
| `reports_to_code` | string | No | Must be a valid role code within same template |

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "id": "role-uuid",
    "code": "VP_SALES",
    "name": "Vice President of Sales",
    "description": "Leads sales team",
    "responsibilities": "* Drive revenue\n* Manage team\n* Set targets",
    "reports_to_code": "CEO",
    "created_at": "2026-02-05T15:30:00Z"
  }
}
```

**Status Codes:**

- `201 Created` - Role added successfully
- `400 Bad Request` - Validation error (invalid code format, circular reference)
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Template not found
- `409 Conflict` - Role code already exists in template
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `RoleTemplatesController.AddRole()`
- Command: `AddTemplateRoleCommand`
- Handler: `AddTemplateRoleCommandHandler`

**Notes:**

- Role codes must be uppercase (e.g., "CEO", "VP_SALES")
- `reports_to_code` creates hierarchical structure
- System validates against circular references

---

### PUT /role-templates/{id}/roles/{roleId}

Update a role within a template.

**Path Parameters:**

- `id` (string, GUID) - Template ID
- `roleId` (string, GUID) - Role ID

**Request Body:**

```json
{
  "name": "Vice President of Sales & Marketing",
  "description": "Oversees sales and marketing",
  "responsibilities": "Updated responsibilities...",
  "reports_to_code": "COO"
}
```

**Notes:**

- All fields are optional (partial update supported)
- Cannot change `code` after creation
- Can set `reports_to_code` to null to remove reporting relationship

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "id": "role-uuid",
    "code": "VP_SALES",
    "name": "Vice President of Sales & Marketing",
    "description": "Oversees sales and marketing",
    "responsibilities": "Updated responsibilities...",
    "reports_to_code": "COO",
    "created_at": "2026-01-15T10:05:00Z"
  }
}
```

**Status Codes:**

- `200 OK` - Role updated successfully
- `400 Bad Request` - Validation error (circular reference, invalid reports_to_code)
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Template or role not found
- `500 Internal Server Error` - Server error

**Implementation:**

- Controller: `RoleTemplatesController.UpdateRole()`
- Command: `UpdateTemplateRoleCommand`
- Handler: `UpdateTemplateRoleCommandHandler`

---

### DELETE /role-templates/{id}/roles/{roleId}

Remove a role from a template.

**Path Parameters:**

- `id` (string, GUID) - Template ID
- `roleId` (string, GUID) - Role ID

**Response:**

```
204 No Content
```

**Status Codes:**

- `204 No Content` - Role deleted successfully
- `400 Bad Request` - Cannot delete role (other roles report to it)
- `401 Unauthorized` - Missing or invalid admin token
- `403 Forbidden` - User lacks admin role
- `404 Not Found` - Template or role not found
- `500 Internal Server Error` - Server error

**Error Response (Role Has Subordinates):**

```json
{
  "success": false,
  "error": "Cannot delete role 'CEO' because roles ['CTO', 'CFO'] report to it",
  "code": "ROLE_HAS_SUBORDINATES"
}
```

**Implementation:**

- Controller: `RoleTemplatesController.DeleteRole()`
- Command: `DeleteTemplateRoleCommand`
- Handler: `DeleteTemplateRoleCommandHandler`

**Notes:**

- Cannot delete a role if other roles have `reports_to_code` pointing to it
- Must reassign or delete subordinate roles first

---

## People Management

Manage people within specific tenants (admin cross-tenant access).

### GET /tenants/{tenantId}/people

Get paginated list of people within a specific tenant.

**Path Parameters:**
- `tenantId` (string, GUID) - Tenant ID

**Query Parameters:**
- `pageNumber` (integer, optional): Page number (default: 1)
- `pageSize` (integer, optional): Items per page (default: 20, max: 100)
- `personTypeId` (string, GUID, optional): Filter by person type ID
- `status` (string, optional): Filter by status ('active' or 'inactive')
- `tagId` (string, GUID, optional): Filter by tag ID
- `search` (string, optional): Search term (firstName, lastName, email)
- `includeRoles` (boolean, optional): Include role assignments (default: false)

**Response:**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@acme.com",
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
```

**Status Codes:**
- `200 OK` - People retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid admin token
- `404 Not Found` - Tenant not found

**Notes:**
- Admin can view people from any tenant (cross-tenant access)
- Same filtering options as user-facing endpoint
- Results include system access status (user account linkage)
- Role information included when `includeRoles=true`
- Audit log entry created

---

## Data Models

### SeedingResult

```typescript
interface SeedingResult {
  itemsCreated: number;
  itemsSkipped: number;
  errors: string[];
}
```

### PaginationInfo

```typescript
interface PaginationInfo {
  currentPage: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
}
```

### SubscriptionTier

```typescript
interface SubscriptionTier {
  id: string; // GUID
  name: string;
  displayName: string;
  description: string;
  pricing: {
    monthlyPrice: number;
    yearlyPrice: number;
    currency: string; // ISO currency code
  };
  features: FeatureName[];
  limits: {
    goals: number | null; // null = unlimited
    actions: number | null;
    strategies: number | null;
    measures: number | null;
    attachments: number | null;
    reports: number | null;
  };
  supportedFrequencies: SubscriptionFrequency[];
  isActive: boolean;
  sortOrder: number;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}
```

### FeatureName (Enum)

```typescript
enum FeatureName {
  Goals = "Goals",
  Operations = "Operations",
  Measures = "Measures",
  Strategies = "Strategies",
  Realtime = "Realtime",
  Reports = "Reports",
  Attachments = "Attachments",
  BulkPlanner = "BulkPlanner",
  StrategyCompare = "StrategyCompare",
  GoalCreate = "GoalCreate"
}
```

### SubscriptionStatus (Enum)

```typescript
enum SubscriptionStatus {
  Active = "Active",
  Trial = "Trial",
  Cancelled = "Cancelled",
  Suspended = "Suspended",
  PastDue = "PastDue"
}
```

### SubscriptionFrequency (Enum)

```typescript
enum SubscriptionFrequency {
  Monthly = "Monthly",
  Yearly = "Yearly"
}
```

### StatusCategory (Enum)

```typescript
enum StatusCategory {
  Open = "Open",
  InProgress = "InProgress",
  Resolved = "Resolved",
  Closed = "Closed"
}
```

### VariableType (Enum)

```typescript
enum VariableType {
  String = "String",
  Number = "Number",
  Boolean = "Boolean",
  Date = "Date",
  Url = "Url",
  Email = "Email"
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

### Common HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET, PUT, POST (non-creation) |
| 201 | Created | Successful POST (resource creation) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request data, validation errors |
| 401 | Unauthorized | Missing or invalid authentication token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource, constraint violation |
| 500 | Internal Server Error | Unexpected server error |

### Validation Errors

Validation errors return 400 Bad Request with detailed field-level errors:

```json
{
  "success": false,
  "error": "Validation failed",
  "details": [
    {
      "field": "email",
      "message": "Invalid email format"
    },
    {
      "field": "monthlyPrice",
      "message": "Must be a positive number"
    }
  ]
}
```

### Business Rule Violations

Business rule violations return 400 Bad Request with context:

```json
{
  "success": false,
  "error": "Cannot delete plan with active subscriptions",
  "details": {
    "planId": "550e8400-e29b-41d4-a716-446655440001",
    "activeSubscribers": 142,
    "action": "Use POST /plans/{id}/deactivate instead"
  }
}
```

---

## Summary

**Total Endpoints:** 101

**Breakdown by Category:**
- Health & System: 1
- Authentication: 2
- System Seeding: 7
- Issue Type Configuration: 7
- Issue Status Configuration: 6
- Email Template Management: 9
- Subscriber Management: 2
- Plan Management: 8
- Feature Management: 12
- Subscription Operations: 6
- System Settings Management: 5
- Role Template Management: 8
- People Management: 1

**All endpoints require Admin role authorization except:**
- GET /health
- POST /auth/validate
- POST /auth/refresh

**Audit Logging:** All write operations automatically logged with admin user ID, action details, and timestamps.

**Pattern Consistency:** All endpoints follow standard patterns for pagination, filtering, error handling, and response envelopes.

---

## Related Documentation

- **[Backend Development Guidelines](../../.github/DEVELOPMENT_GUIDELINES.md)** - Architecture & coding standards
- **[Copilot Rules](../../.github/COPILOT_RULES.md)** - Specification enforcement rules
- **[User App Specifications](../user-app/index.md)** - User-facing API specifications

---

**End of Specification**
