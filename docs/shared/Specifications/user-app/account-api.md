# Account API Specification

**Version:** 1.0  
**Status:** Verified Against Implementation  
**Last Updated:** December 30, 2025  
**Base URL:** Account Service (typically `/auth` and `/user` paths)

---

## Overview

The Account API handles all user authentication, profile management, subscription features, and billing operations. This includes:

1. **Authentication** - Login, registration, password reset, email verification, Google OAuth
2. **User Profile** - Get and update user details, preferences
3. **Subscription** - Features, limits, subscription updates
4. **Billing** - Billing portal access

---

## Authentication & Headers

Most endpoints require authentication headers:

```
Authorization: Bearer {accessToken}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

**Exceptions:** Auth endpoints (`/auth/login`, `/auth/register`, `/auth/google`, `/auth/forgot-password`, `/auth/forgot-username`, `/auth/reset-password`) do not require authentication.

---

## Authentication Endpoints

### 1. POST /auth/login

**Description:** Authenticate user with username and password.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json
- X-Frontend-Base-Url: {origin} (optional, for email links)

**Request Body:**

```json
{
  "username": "string (required, email or username)",
  "password": "string (required, min 8 characters)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "accessToken": "string (JWT token)",
    "refreshToken": "string (refresh token)",
    "user": {
      "id": "string (UUID)",
      "email": "string",
      "fullName": "string",
      "phone": "string|null",
      "profileImage": "string (URL)|null",
      "createdAt": "string (ISO 8601 datetime)",
      "updatedAt": "string (ISO 8601 datetime)",
      "isActive": "boolean",
      "emailVerified": "boolean",
      "phoneVerified": "boolean",
      "preferences": {
        "notifications": {
          "email": "boolean",
          "push": "boolean",
          "sms": "boolean",
          "marketing": "boolean"
        },
        "timezone": "string (e.g., UTC, America/New_York)",
        "language": "string (e.g., en, es)",
        "theme": "light|dark|auto"
      },
      "subscription": {
        "id": "string (UUID)",
        "userId": "string (UUID)",
        "plan": "monthly|yearly",
        "status": "active|inactive|cancelled|past_due|trialing",
        "currentPeriodStart": "string (ISO 8601 datetime)",
        "currentPeriodEnd": "string (ISO 8601 datetime)",
        "cancelAtPeriodEnd": "boolean",
        "price": "number (cents)",
        "currency": "string (e.g., USD)"
      }
    },
    "tenant": {
      "id": "string (UUID)"
    }
  }
}
```

**Validation:**
- `username` - Required, must be valid email or username
- `password` - Required, min 8 characters

**Error Responses:**

```json
{
  "success": false,
  "error": "string (error message)",
  "code": "string|null (error code, e.g., EMAIL_NOT_VERIFIED)"
}
```

- 400 Bad Request - Missing or invalid credentials
- 401 Unauthorized - Invalid username/password
- 403 Forbidden - Account not verified or disabled

**Field Mapping Notes:**
- Backend may return `access_token` or `accessToken` (both supported)
- Backend may return `refresh_token` or `refreshToken` (both supported)
- Backend user object uses `first_name`/`last_name` or `firstName`/`lastName` (both supported)
- Frontend combines firstName/lastName into `fullName`
- Backend `avatar_url` maps to frontend `profileImage`

---

### 2. POST /auth/register

**Description:** Register a new user account.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json
- X-Frontend-Base-Url: {origin} (required for email verification links)

**Request Body:**

```json
{
  "email": "string (required, valid email)",
  "username": "string (required, min 3, max 50 chars)",
  "password": "string (required, min 8 chars)",
  "firstName": "string (required, max 50 chars)",
  "lastName": "string (required, max 50 chars)",
  "phone": "string|null (optional, phone number)"
}
```

**Response:** 201 Created

**Case 1: Email verification required**

```json
{
  "success": true,
  "data": {
    "requiresEmailVerification": true,
    "tenantId": "string (UUID)"
  }
}
```

**Case 2: Auto-login (email verification not required)**

```json
{
  "success": true,
  "data": {
    "accessToken": "string (JWT token)",
    "refreshToken": "string (refresh token)",
    "user": {...},
    "tenant": {...}
  }
}
```

**Validation:**
- `email` - Required, valid email format, unique
- `username` - Required, min 3 chars, max 50 chars, unique, alphanumeric + underscores
- `password` - Required, min 8 chars, must include uppercase, lowercase, number
- `firstName` - Required, max 50 chars
- `lastName` - Required, max 50 chars
- `phone` - Optional, digits only (automatically stripped of formatting)

**Error Responses:**

```json
{
  "success": false,
  "error": "Email already registered" | "Username already taken" | "Password too weak"
}
```

- 400 Bad Request - Validation failed
- 409 Conflict - Email or username already exists
- 422 Unprocessable Entity

**Notes:**
- Frontend strips non-digit characters from phone before sending
- Backend creates tenant automatically for new user
- Email verification link sent to provided email address

---

### 3. POST /auth/google

**Description:** Authenticate user with Google OAuth token.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json

**Request Body:**

```json
{
  "token": "string (required, Google OAuth token)"
}
```

**Response:** 200 OK (same structure as `/auth/login` response)

**Error Responses:**
- 400 Bad Request - Invalid token
- 401 Unauthorized - Token expired or invalid

**Notes:**
- Creates user account automatically if not exists
- Uses Google profile information for firstName/lastName
- Tenant created automatically for new users

---

### 4. POST /auth/forgot-password

**Description:** Request password reset email.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json

**Request Body:**

```json
{
  "email": "string (required, valid email)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "message": "If an account exists with that email, a reset link has been sent."
}
```

**Notes:**
- Always returns success to prevent email enumeration
- Reset link sent to email if account exists
- Link expires after configurable time (typically 1-24 hours)

**Error Responses:**
- 400 Bad Request - Invalid email format
- 500 Internal Server Error

---

### 5. POST /auth/forgot-username

**Description:** Request username reminder email.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json

**Request Body:**

```json
{
  "email": "string (required, valid email)"
}
```

**Response:** 200 OK

```json
{
  "success": true
}
```

**Notes:**
- Always returns success to prevent email enumeration
- Username sent to email if account exists
- Frontend implementation explicitly handles this security requirement

**Error Responses:**
- 400 Bad Request - Invalid email format
- 500 Internal Server Error

---

### 6. POST /auth/reset-password

**Description:** Reset password using token from email.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json

**Request Body:**

```json
{
  "token": "string (required, reset token from email)",
  "new_password": "string (required, min 8 chars)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

**Validation:**
- `token` - Required, must be valid and not expired
- `new_password` - Required, min 8 chars, must meet password strength requirements

**Error Responses:**
- 400 Bad Request - Invalid or expired token
- 422 Unprocessable Entity - Password too weak

**Field Naming Note:**
- Backend expects `new_password` (snake_case), not `newPassword`
- This is an exception to the general camelCase convention

---

### 7. POST /auth/refresh

**Description:** Refresh access token using refresh token.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json

**Request Body:**

```json
{
  "refresh_token": "string (required)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "accessToken": "string (new JWT token)",
    "refreshToken": "string (new refresh token)"
  }
}
```

**Error Responses:**
- 400 Bad Request - Invalid refresh token
- 401 Unauthorized - Refresh token expired
- 403 Forbidden - Refresh token revoked

**Field Naming Note:**
- Backend expects `refresh_token` (snake_case)
- Backend may return `access_token` or `accessToken` (both handled)

**Client Behavior:**
- Frontend automatically calls this when receiving 401 on authenticated requests
- New tokens stored in localStorage
- Failed refresh triggers logout and redirect to login

---

### 8. POST /auth/resend-confirmation

**Description:** Resend email verification link.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json
- X-Frontend-Base-Url: {origin} (required for verification link)

**Query Parameters:**
- `email` - User email address (required)

**Request Body:** None (email sent as query parameter)

**Response:** 200 OK

```json
{
  "success": true,
  "message": "Verification email sent"
}
```

**Error Responses:**
- 400 Bad Request - Invalid email or already verified
- 404 Not Found - Email not found
- 429 Too Many Requests - Rate limit exceeded

---

### 9. POST /auth/confirm-email

**Description:** Confirm email address using token from verification email.

**HTTP Method:** POST

**Headers:**
- Content-Type: application/json

**Request Body:**

```json
{
  "token": "string (required, verification token from email)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "message": "Email confirmed successfully"
}
```

**Error Responses:**
- 400 Bad Request - Invalid or expired token
- 410 Gone - Token already used

---

### 10. GET /auth/confirm-email/validate

**Description:** Validate email verification token without consuming it.

**HTTP Method:** GET

**Query Parameters:**
- `token` - Verification token (required)

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "status": "valid|used|expired|not_found"
  }
}
```

**Status Values:**
- `valid` - Token is valid and can be used
- `used` - Token was already used
- `expired` - Token has expired
- `not_found` - Token does not exist

**Error Responses:**
- 400 Bad Request - Missing token parameter

---

### 11. POST /auth/logout

**Description:** Logout user and invalidate refresh token.

**HTTP Method:** POST

**Headers:**
- Authorization: Bearer {token} (optional)

**Query Parameters:**
- `refresh_token` - Refresh token to revoke (optional)

**Request Body:** None

**Response:** 200 OK

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Client Behavior:**
- Clears accessToken, refreshToken, and tenantId from localStorage
- Always succeeds even if backend call fails
- Redirects to login page

**Error Responses:** None (frontend always clears tokens)

---

## User Profile Endpoints

### 12. GET /user/profile

**Description:** Get current user profile.

**HTTP Method:** GET

**Headers:**
- Authorization: Bearer {token} (required)
- X-Tenant-Id: {tenantId} (required)

**Request Parameters:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "email": "string",
    "fullName": "string",
    "phone": "string|null",
    "profileImage": "string (URL)|null",
    "createdAt": "string (ISO 8601 datetime)",
    "updatedAt": "string (ISO 8601 datetime)",
    "isActive": "boolean",
    "emailVerified": "boolean",
    "phoneVerified": "boolean",
    "preferences": {
      "notifications": {
        "email": "boolean",
        "push": "boolean",
        "sms": "boolean",
        "marketing": "boolean"
      },
      "timezone": "string",
      "language": "string",
      "theme": "light|dark|auto"
    },
    "subscription": {
      "id": "string (UUID)",
      "userId": "string (UUID)",
      "plan": "monthly|yearly",
      "status": "active|inactive|cancelled|past_due|trialing",
      "currentPeriodStart": "string (ISO 8601 datetime)",
      "currentPeriodEnd": "string (ISO 8601 datetime)",
      "cancelAtPeriodEnd": "boolean",
      "price": "number (cents)",
      "currency": "string"
    }
  }
}
```

**Error Responses:**
- 401 Unauthorized - Missing or invalid token
- 403 Forbidden - Invalid tenant
- 404 Not Found - User not found

**Field Mapping:**
- Backend `first_name`/`last_name` or `firstName`/`lastName` → Frontend `fullName`
- Backend `avatar_url` → Frontend `profileImage`
- Backend `user_id` or `userId` or `id` → Frontend `id`

---

### 13. PUT /user/profile

**Description:** Update user profile (partial updates supported).

**HTTP Method:** PUT

**Headers:**
- Authorization: Bearer {token} (required)
- X-Tenant-Id: {tenantId} (required)
- Content-Type: application/json

**Request Body:** (all fields optional)

```json
{
  "firstName": "string|null (max 50 chars)",
  "lastName": "string|null (max 50 chars)",
  "phone": "string|null (phone number)",
  "avatar_url": "string|null (profile image URL)",
  "preferences": {
    "notifications": {
      "email": "boolean",
      "push": "boolean",
      "sms": "boolean",
      "marketing": "boolean"
    },
    "timezone": "string",
    "language": "string",
    "theme": "light|dark|auto"
  }
}
```

**Response:** 200 OK (same structure as GET /user/profile)

**Validation:**
- `firstName` - Optional, max 50 chars
- `lastName` - Optional, max 50 chars
- `phone` - Optional, valid phone format
- `avatar_url` - Optional, valid URL
- `preferences` - Optional object, partial updates supported

**Error Responses:**
- 400 Bad Request - Invalid data
- 401 Unauthorized
- 403 Forbidden
- 422 Unprocessable Entity

**Field Mapping Notes:**
- Frontend sends `firstName`/`lastName` (not first_name/last_name)
- Frontend sends `avatar_url` for profile image
- Backend may accept both snake_case and camelCase
- Frontend `fullName` is split into firstName/lastName before sending
- If `fullName` provided without firstName/lastName, it's automatically split

---

## Subscription & Features Endpoints

### 14. GET /user/features

**Description:** Get list of enabled features for current user's subscription.

**HTTP Method:** GET

**Headers:**
- Authorization: Bearer {token} (required)
- X-Tenant-Id: {tenantId} (required)

**Request Parameters:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": ["string (feature name)", ...]
}
```

**Example:**
```json
{
  "success": true,
  "data": [
    "goals_advanced",
    "coaching_unlimited",
    "export_pdf",
    "api_access"
  ]
}
```

**Fallback Behavior:**
- If endpoint returns 400 or 404, returns empty array `[]`
- Allows UI to function with default free tier features

**Error Responses:**
- 401 Unauthorized
- 403 Forbidden

---

### 15. GET /user/limits

**Description:** Get usage limits for current user's subscription.

**HTTP Method:** GET

**Headers:**
- Authorization: Bearer {token} (required)
- X-Tenant-Id: {tenantId} (required)

**Request Parameters:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "goals": "number|null (max goals, null = unlimited)",
    "strategies": "number|null (max strategies per goal)",
    "measures": "number|null (max KPIs per strategy)",
    "actions": "number|null (max actions)",
    "insights": "number|null (max coaching insights)",
    "storage": "number|null (max storage in bytes)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 400 or 404, returns `{ goals: null }` (unlimited)
- Allows UI to function without enforcing limits

**Error Responses:**
- 401 Unauthorized
- 403 Forbidden

---

### 16. PUT /user/subscription

**Description:** Update subscription plan or tier.

**HTTP Method:** PUT

**Headers:**
- Authorization: Bearer {token} (required)
- X-Tenant-Id: {tenantId} (required)
- Content-Type: application/json

**Request Body:**

```json
{
  "plan": "monthly|yearly|null",
  "tier": "string|null (tier name, e.g., pro, enterprise)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "email": "string",
    "fullName": "string",
    ...
  }
}
```

**Validation:**
- `plan` - Optional, must be "monthly" or "yearly"
- `tier` - Optional, string

**Error Responses:**
- 400 Bad Request - Invalid plan or tier
- 401 Unauthorized
- 403 Forbidden
- 402 Payment Required - Payment method required

---

## Billing Endpoints

### 17. POST /billing/portal

**Description:** Get URL to customer billing portal (Stripe).

**HTTP Method:** POST

**Headers:**
- Authorization: Bearer {token} (required)
- X-Tenant-Id: {tenantId} (required)
- Content-Type: application/json

**Request Body:**

```json
{
  "return_url": "string|null (URL to return to after portal session)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "url": "string (billing portal URL)"
  }
}
```

**Usage:**
- Returns Stripe Customer Portal URL
- User can manage payment methods, view invoices, cancel subscription
- Expires after session timeout (typically 1 hour)

**Error Responses:**
- 400 Bad Request - Invalid return URL
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found - No billing account

**Field Naming Note:**
- Backend expects `return_url` (snake_case)

---

## Additional User Endpoints

### 18. GET /users/{userId}

**Description:** Get user by ID (minimal fields).

**HTTP Method:** GET

**Headers:**
- Authorization: Bearer {token} (required)
- X-Tenant-Id: {tenantId} (required)

**Path Parameters:**
- `userId` - User UUID (required)

**Request Parameters:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "email": "string|null",
    "firstName": "string|null (or first_name)",
    "lastName": "string|null (or last_name)"
  }
}
```

**Error Responses:**
- 400 Bad Request - Missing user ID
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found - User not found

**Notes:**
- Used for fetching details of other users (e.g., assignees, collaborators)
- Limited fields returned for privacy
- Backend may return snake_case or camelCase field names

---

## Error Handling

All error responses follow this format:

```json
{
  "success": false,
  "error": "string (error message)",
  "code": "string|null (error code)"
}
```

**Common HTTP Status Codes:**
- 400 - Bad Request (validation failed, malformed JSON)
- 401 - Unauthorized (missing/invalid token)
- 403 - Forbidden (invalid tenant, insufficient permissions)
- 404 - Not Found (resource not found, endpoint not implemented)
- 409 - Conflict (duplicate email/username)
- 422 - Unprocessable Entity (semantic validation failed)
- 429 - Too Many Requests (rate limit exceeded)
- 500 - Internal Server Error

**Error Codes (code field):**
- `EMAIL_NOT_VERIFIED` - Email verification required
- `INVALID_CREDENTIALS` - Username/password incorrect
- `TOKEN_EXPIRED` - Token has expired
- `RATE_LIMIT_EXCEEDED` - Too many requests

**Client Handling:**
- Always check `success` field first
- On 401, attempt token refresh via `/auth/refresh`
- On refresh failure, clear tokens and redirect to login
- On 4xx client errors, display user-friendly error message
- On 500, retry with exponential backoff or display error

---

## Token Management

### Access Token
- JWT format
- Expires after configurable time (typically 15 minutes to 1 hour)
- Stored in localStorage as `accessToken`
- Included in Authorization header: `Bearer {token}`

### Refresh Token
- Opaque token format
- Expires after longer period (typically 7-30 days)
- Stored in localStorage as `refreshToken`
- Used to obtain new access token via `/auth/refresh`
- Invalidated on logout

### Tenant ID
- UUID format
- Stored in localStorage as `tenantId`
- Included in X-Tenant-Id header
- Obtained from login/register response
- Cleared on logout

### Auto-Refresh Behavior
- Frontend intercepts 401 responses on authenticated requests
- Automatically calls `/auth/refresh` with refresh token
- If refresh succeeds, retries original request with new token
- If refresh fails, triggers logout and redirect
- Implements deduplication to prevent multiple concurrent refresh attempts
- Queues requests during refresh to retry after completion

---

## Field Naming Conventions

### Backend to Frontend Mapping

**User Fields:**
- `first_name` or `firstName` → `fullName` (combined)
- `last_name` or `lastName` → `fullName` (combined)
- `avatar_url` → `profileImage`
- `user_id` or `userId` or `id` → `id`
- `created_at` → `createdAt`
- `updated_at` → `updatedAt`
- `email_verified` → `emailVerified`

**Token Fields:**
- `access_token` or `accessToken` → `accessToken`
- `refresh_token` or `refreshToken` → `refreshToken`

**General Rule:**
- Backend accepts both snake_case and camelCase in most endpoints
- Frontend sends camelCase in request bodies
- Frontend accepts both from backend and normalizes to camelCase
- Exception: `/auth/reset-password` requires `new_password` (snake_case)
- Exception: `/auth/refresh` requires `refresh_token` (snake_case)
- Exception: `/billing/portal` requires `return_url` (snake_case)

---

## Implementation Notes

### Phone Number Handling
- Frontend strips all non-digit characters before sending to backend
- Backend stores digits only
- Frontend re-formats for display (e.g., (555) 123-4567)

### Email Enumeration Prevention
- `/auth/forgot-password` always returns success
- `/auth/forgot-username` always returns success
- Prevents attackers from determining valid email addresses

### Password Requirements
- Minimum 8 characters
- Must include uppercase letter
- Must include lowercase letter
- Must include number
- Special characters recommended but not required

### Security Headers
- `X-Frontend-Base-Url` header used for email link generation
- Helps backend construct correct verification/reset links
- Should match the origin where frontend is hosted

### Rate Limiting
- Not explicitly documented in this version
- Backend may implement rate limiting on sensitive endpoints
- Frontend should handle 429 Too Many Requests appropriately

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 30, 2025 | Initial specification verified against complete implementation. All 18+ endpoints documented with full request/response payloads, validation rules, field mapping, and special handling notes. Technology-agnostic format. |

