# Account API Specification

**Version:** 2.4  
**Last Updated:** January 28, 2026 (Username support in invitation activation + conflict error)  
**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}` (e.g., `https://api.dev.purposepath.app/account/api/v1`)

## Scope

Consolidated account endpoints implemented by the Account Lambda controllers: `Auth`, `Users`, `Tenants`, `SubscriptionTiers`, `UserSubscription`, `Billing`, `Subscriptions`, `BillingWebhook`, `Health`.

## Conventions

- JSON uses camelCase. Legacy snake_case inputs remain backwards compatible only where noted (logout refresh token).
- Response envelope (`ApiResponse<T>`): `{ "success": true|false, "data": {}, "message": "?", "error": "?", "code": "?" }`.
- Paginated responses use `PaginatedResponse<T>`: same envelope plus `pagination: { page, limit, total, totalPages }`.
- Authenticated endpoints require headers: `Authorization: Bearer {accessToken}`, `X-Tenant-Id: {tenantId}`. Public endpoints are marked.
- Optional headers: `X-Frontend-Base-Url` (used for auth emails), `X-E2E-Test: true` (DEV only to bypass email verification on register).

## JWT Claims (Issue #545)

The access token JWT includes the following custom claims:
- `user_id`: User's GUID
- `tenant_id`: Tenant's GUID
- `username`: User's username
- `email_verified`: Boolean (from Person entity)
- `user_status`: User status (e.g., "Active")
- `role`: User role (e.g., "user" or "admin")
- `is_tenant_owner`: Boolean - `true` if the user is the tenant owner, `false` otherwise (Issue #545)

Frontend can decode the JWT to access these claims, but `isTenantOwner` is also available directly in `AuthResponse.user` for convenience.

## Authentication

### POST /auth/login
- Body: `{ "username": "string", "password": "string" }` (username may be email-style; 3-50 chars).
- Response `AuthResponse`:
```json
{
  "success": true,
  "data": {
    "accessToken": "jwt",
    "refreshToken": "jwt",
    "user": {
      "id": "uuid",
      "email": "string",
      "firstName": "string",
      "lastName": "string",
      "personId": "uuid|null",
      "tenantId": "uuid",
      "status": "string",
      "isEmailVerified": true,
      "isTenantOwner": false,
      "createdAt": "2025-12-29T00:00:00Z",
      "updatedAt": "2025-12-29T00:00:00Z"
    },
    "person": { "id": "uuid", "firstName": "string", "lastName": "string", "email": "string|null", "phone": "string|null", "title": "string|null" },
    "tenant": { "id": "uuid", "name": "string", "status": "string" }
  }
}
```
- **Issue #545**: `user.isTenantOwner` is `true` if the authenticated user is the tenant owner (`tenant.ownerUserId == user.id`), `false` otherwise.
- Errors: 401 invalid credentials, 403 `EMAIL_NOT_VERIFIED`.

### POST /auth/google
- Body: `{ "token": "string" }` (Google ID token from OAuth flow).
- Response: same as login (includes `user.isTenantOwner`).
- Notes: Validates token with Google, creates new user/tenant if external identity not found (new user is automatically the tenant owner), or logs in existing user. Auto-updates user avatar from Google profile if user has no avatar.
- **Issue #546**: Allows registration even if Google doesn't provide email (person.email will be null, person.emailVerified will be false). Frontend can detect missing email and direct user to update it via PUT /user/email.

### POST /auth/microsoft
- Body: `{ "token": "string" }` (Microsoft ID token from OAuth/OIDC flow).
- Response: same as login (includes `user.isTenantOwner`).
- Notes: Validates token with Microsoft OIDC metadata endpoint, creates new user/tenant if external identity not found (new user is automatically the tenant owner), or logs in existing user. Auto-updates user avatar from Microsoft profile if user has no avatar.
- **Issue #546**: Allows registration even if Microsoft doesn't provide email (person.email will be null, person.emailVerified will be false). Frontend can detect missing email and direct user to update it via PUT /user/email.

### POST /auth/register
- Body: `{ "username": "string", "email": "string", "password": "string", "firstName": "string", "lastName": "string", "phone": "string|null" }`.
- DEV-only bypass: `X-E2E-Test: true` skips email verification.
- Response: `AuthResponse` (auto-login path) or validation error. Email verification links use `X-Frontend-Base-Url` if provided.

### POST /auth/forgot-password
- Body: `{ "username": "string" }`.
- Response: `{ "success": true, "message": "Password reset email sent" }`.
- Notes: Password reset email is sent to the email address of the Person linked to the username.

### POST /auth/reset-password
- Body: `{ "token": "string", "newPassword": "string" }`.
- Response: `{ "success": true, "message": "Password reset successfully" }`.

### POST /auth/refresh
- Body: `{ "refreshToken": "string" }`.
- Response: `{ "success": true, "data": { "accessToken": "string", "refreshToken": "string" } }`.

### POST /auth/confirm-email
- Body: `{ "token": "string" }`.
- Response: `{ "success": true, "message": "Email confirmed successfully" }`.

### GET /auth/confirm-email/validate
- Query: `token`.
- Response: `{ "success": true, "data": { "status": "valid|used|expired|not_found|error" } }`.

### POST /auth/resend-confirmation
- Query: `email`; optional `X-Frontend-Base-Url` for link generation.
- Response: `{ "success": true, "message": "Confirmation email resent" }`.

### POST /auth/logout
- Query: `refreshToken` (camelCase). Legacy `refresh_token` still accepted.
- Response: `{ "success": true }`.

### GET /auth/check-username (Public)
**No Auth Required** - Check if a username is available for registration or invitation activation.

- Query: `username` (string, required).
- Response (Available):
```json
{
  "success": true,
  "data": {
    "available": true,
    "username": "johndoe"
  }
}
```
- Response (Not Available):
```json
{
  "success": true,
  "data": {
    "available": false,
    "username": "johndoe",
    "message": "Username is already taken",
    "reasonCode": "TAKEN"
  }
}
```
- Response (Invalid Format):
```json
{
  "success": false,
  "error": "Invalid username format",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "username",
    "message": "Username must be 3-50 characters, start with alphanumeric, and contain only alphanumeric, '.', '_', '-', '@'",
    "reasonCode": "INVALID_FORMAT"
  }
}
```
- Reason Codes (data.reasonCode when `available: false`):
  - `TAKEN`: Username is already in use.
  - `RESERVED`: Username is a reserved system name (admin, support, system, etc.).
  - `PREVIOUSLY_USED`: Username is reserved for 90 days after a change.
  - `CHANGE_RATE_LIMITED`: Authenticated user is within the 30‑day username change cooldown.
- **Notes**: 
  - This is a public endpoint (no authentication required) for use during registration and invitation activation.
  - Returns success with `available: false` for taken usernames (not an error state).
  - Returns error only for invalid format or server errors.
  - Reserved usernames (admin, support, system, etc.) are considered unavailable.
  - If an authenticated user context is available, the response may return `CHANGE_RATE_LIMITED`.

## Users (Single User Operations)

### GET /user/{id}
- Path: user ID (GUID). Public auth required.
- Response: `{ "success": true, "data": { "userId": "uuid", "email": "string", "firstName": "string", "lastName": "string", "avatarUrl": "string|null" } }`.

### GET /user/profile
- Response `UserProfileDetailResponse`: user info with preferences and `personId`.

### PUT /user/profile
- Body (all optional): `{ "firstName": "string|null", "lastName": "string|null", "phone": "string|null", "avatarUrl": "string|null", "preferences": { "theme": "string", "language": "string", "timezone": "string", "dateFormat": "string", "timeFormat": "string", "currency": "string", "notifications": { "email": true, "push": true, "sms": true, "marketing": true, "coachingReminders": true, "teamUpdates": true, "systemNotifications": true }, "coaching": { "preferredSessionLength": 60, "reminderFrequency": "weekly", "coachingStyle": "directive" } } }`.
- Response: updated `UserProfileDetailResponse`.

### PUT /user/email
- **Issue #546**: Update user email (for OAuth users who registered without email).
- Requires authentication (including users with unverified email).
- Body: `{ "email": "string" }`.
- Headers: Optional `X-Frontend-Base-Url` for verification email link.
- Response: `{ "success": true, "message": "Email updated successfully. Verification email sent." }`.
- Errors: 400 invalid email format, 409 email already in use (EMAIL_IN_USE), 404 user not found.
- Notes: Updates person.email and sets person.emailVerified to false. Sends verification email using existing /auth/confirm-email flow. Frontend should direct user to email verification screen after successful update.

### PUT /user/preferences
- Body: `UserPreferencesRequest` (same shape as `preferences` above).
- Response: `{ "success": true, "data": UserPreferencesResponse }`.

### GET /user/features
- Response: `{ "success": true, "data": ["goals", "operations", ...] }`.

### GET /user/limits
- Response `UserLimitsResponse`: `{ "goals": 10, "users": null, "projects": null, "apiCallsPerMonth": 10000, "storageMb": 1024 }` (null = unlimited).

## Tenants

### GET /tenants/{id}
- Response: `TenantResponse` `{ id, name, status, subscriptionTier, createdAt, updatedAt, userCount, isActive }`.

### GET /tenants/current
- Response: `TenantResponse`.

### PUT /tenants/current
- Body: `{ "name": "string|null", "status": "string|null" }`.
- Response: updated `TenantResponse`.

### GET /tenants/settings
- Response: `{ "success": true, "data": { "targetLineMode": "single|three" } }`.

### PUT /tenants/settings
- Body: `{ "targetLineMode": "single|three" }`.
- Response: updated settings.

## Subscription Tiers

### GET /subscription/tiers (public)
- Response: list of `TierResponse` items:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Starter",
      "description": "...",
      "features": ["goals", "operations"],
      "limits": {"goals": 10, "measures": 50, "actions": null},
      "pricing": {"monthly": 29.99, "yearly": 299.99},
      "supportedFrequencies": ["monthly", "yearly"],
      "isActive": true
    }
  ]
}
```

## User Subscription (self-serve)

### GET /user/subscription
- Returns current tenant subscription with embedded tier, or `data: null` if none.

### POST /user/subscription
- Body: `{ "tierId": "uuid", "frequency": "monthly|yearly", "promoCode": "string|null", "paymentMethodId": "string|null" }`.
- Response `CreateUserSubscriptionResponse`: `{ "subscription": UserSubscriptionResponse, "requiresPaymentConfirmation": true|false, "clientSecret": "string|null" }`.

### PUT /user/subscription
- Body: `{ "tierId": "uuid", "frequency": "monthly|yearly", "promoCode": "string|null" }`.
- Response `UpdateUserSubscriptionResponse`: `{ "subscription": UserSubscriptionResponse, "effectiveDate": "ISO-8601" }` (changes take effect end of period).

### DELETE /user/subscription
- Body: `{ "reason": "string|null", "cancelAtPeriodEnd": true|false }`.
- Response `CancelUserSubscriptionResponse`: `{ "subscription": UserSubscriptionResponse, "cancelEffectiveDate": "ISO-8601" }`.

### PUT /user/subscription/auto-renewal
- Body: `{ "autoRenewal": true|false }`.
- Response: updated `UserSubscriptionResponse`.

## Billing (tenant-scoped)

### PUT /billing/subscription
- Body: `{ "newTier": "Starter|Professional|Enterprise", "effectiveDate": "ISO-8601|null", "prorateBilling": true|false }`.
- Response: `SubscriptionResponse`.

### POST /billing/payment-intent
- Body: `{ "tierId": "uuid", "frequency": "monthly|yearly", "promoCode": "string|null" }`.
- Response: `{ "success": true, "data": { "clientSecret": "string", "amount": 2999, "currency": "usd" } }`.

### POST /billing/portal
- Body: `{ "returnUrl": "string|null" }` (defaults to frontend base URL when omitted).
- Response: `{ "success": true, "data": { "url": "https://billing.stripe.com/..." } }`.

## Subscriptions (admin/ops)

### GET /subscriptions
- Query: `page`, `pageSize`, `tenantId`, `status`, `tier`, `isTrialing`, `isActive`, `sortBy` (default `CreatedAt`), `sortOrder` (`asc|desc`).
- Response: `PaginatedResponse<SubscriptionSummaryResponse>` with `data` list and `pagination` metadata.

### GET /subscriptions/{id}
- Path: subscription ID (GUID). Response: `ApiResponse<SubscriptionResponse>`.

### GET /subscriptions/tenant/{tenantId}
- Path: tenant ID (GUID). Response: `ApiResponse<SubscriptionResponse>`.

### POST /subscriptions
- Body: `{ "tenantId": "uuid", "ownerId": "uuid", "tier": "Starter|Professional|Enterprise", "currentPeriodStart": "ISO-8601|null", "currentPeriodEnd": "ISO-8601|null", "startTrial": true|false, "trialEndsAt": "ISO-8601|null" }`.
- Response: `ApiResponse<SubscriptionResponse>` (201 Created on success).

### PUT /subscriptions/{id}/tier
- Body: `{ "newTier": "Starter|Professional|Enterprise", "effectiveDate": "ISO-8601|null", "prorateBilling": true|false }`.
- Response: updated `SubscriptionResponse`.

### POST /subscriptions/{id}/cancel
- Response: `ApiResponse<SubscriptionResponse>` (subscription cancelled immediately).

### POST /subscriptions/{id}/trial
- Body: `{ "trialEndsAt": "ISO-8601" }`. Response: updated `SubscriptionResponse`.

### PUT /subscriptions/{id}/billing-provider
- Body: `{ "billingProviderId": "string", "providerSubscriptionId": "string", "providerCustomerId": "string" }`.
- Response: updated `SubscriptionResponse` (links provider IDs).

### POST /subscriptions/promo/validate (public)
- Body: `{ "promoCode": "string", "tierId": "uuid", "frequency": "monthly|yearly" }`.
- Response: `{ "success": true, "data": { "isValid": true|false, "discount": { "type": "percentage|fixed", "value": 20, "duration": "once", "durationInMonths": 6 }, "newPrice": null, "errorMessage": "string|null" } }`.

### POST /subscriptions/create-payment
- Body: `{ "subscriptionId": "uuid", "paymentProvider": "stripe|paypal|square", "paymentMethodId": "string", "tier": "Starter|Professional|Enterprise", "frequency": "monthly|yearly", "promoCode": "string|null", "metadata": { "key": "value" } }`.
- Response `PaymentSubscriptionResponse`: `{ "providerSubscriptionId": "string", "providerCustomerId": "string", "status": "active|incomplete|trialing|past_due", "clientSecret": "string|null", "requiresAction": true|false, "errorMessage": "string|null" }`.

## Billing Webhook

### POST /billing/webhook/{providerId}
- Path: `providerId` (e.g., `stripe`, `paypal`).
- Headers: signature header varies by provider (`Stripe-Signature`, `PayPal-Signature`, or `X-Webhook-Signature`).
- Body: raw webhook payload from provider.
- Response: `{ "success": true, "data": { "received": true } }` (400 on signature/body validation failure).

## User Invitations (Multi-User System)

**Owner-Only Operations:** All invitation management endpoints except activation are restricted to tenant owners only.

### POST /invitations
**Owner-Only** - Invite a person to create a user account.

- Body:
```json
{
  "personId": "uuid",
  "expirationDays": 7
}
```
- Headers: `Authorization`, `X-Tenant-Id`, `X-Frontend-Base-Url` (required for activation link).
- Response:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "personId": "uuid",
    "tenantId": "uuid",
    "invitedByUserId": "uuid",
    "invitationToken": "64-char-token",
    "status": "Sent",
    "expiresAt": "2026-01-19T00:00:00Z",
    "createdAt": "2026-01-12T00:00:00Z",
    "sentAt": "2026-01-12T00:00:00Z"
  }
}
```
- Errors: 403 not owner, 400 person not found/no email/already linked/active invitation exists.

### GET /invitations
**Owner-Only** - List invitations for tenant.

- Query: `status` (optional: `Pending|Sent|Accepted|Expired|Withdrawn`).
- Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "personId": "uuid",
      "person": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com"
      },
      "tenantId": "uuid",
      "invitedByUserId": "uuid",
      "status": "Sent",
      "expiresAt": "2026-01-19T00:00:00Z",
      "createdAt": "2026-01-12T00:00:00Z",
      "sentAt": "2026-01-12T00:00:00Z",
      "acceptedAt": null
    }
  ]
}
```

### POST /invitations/{id}/resend
**Owner-Only** - Regenerate token and resend invitation email.

- Path: invitation ID (GUID).
- Body:
```json
{
  "expirationDays": 7
}
```
- Headers: `X-Frontend-Base-Url` (required for activation link).
- Response: updated invitation object (same as POST /invitations).
- Errors: 403 not owner, 404 not found, 400 already accepted.

### DELETE /invitations/{id}
**Owner-Only** - Withdraw invitation (cancel before acceptance).

- Path: invitation ID (GUID).
- Response: `{ "success": true, "message": "Invitation withdrawn successfully" }`.
- Errors: 403 not owner, 404 not found, 400 already accepted.

### GET /invitations/validate/{token} (Public)
**No Auth Required** - Validate invitation token before activation.

- Path: invitation token (64-char string).
- Response:
```json
{
  "success": true,
  "data": {
    "isValid": true,
    "invitation": {
      "id": "uuid",
      "personId": "uuid",
      "person": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com"
      },
      "tenantId": "uuid",
      "tenant": {
        "id": "uuid",
        "name": "Acme Corp",
        "status": "Active"
      },
      "status": "Sent",
      "expiresAt": "2026-01-19T00:00:00Z"
    }
  }
}
```
- **Note**: `tenant.name` is populated from the business foundation's company name if available, otherwise falls back to the tenant's name field (Issue #577).
```
- Invalid token response:
```json
{
  "success": false,
  "error": "Invalid or expired invitation",
  "data": { "isValid": false }
}
```

### POST /invitations/activate (Public)
**No Auth Required** - Activate invitation and create user account.

- Body (Password-based):
```json
{
  "token": "64-char-token",
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```
- Body (OAuth-based):
```json
{
  "token": "64-char-token",
  "username": "johndoe",
  "googleUserId": "google-oauth-id",
  "googleEmail": "john.doe@example.com",
  "googleProfilePictureUrl": "https://...",
  "username": "johndoe"
}
```
- **Field Constraints:**
  - `username` (optional): 3-50 characters, must start with alphanumeric, can contain alphanumeric + `.` `_` `-` `@`. Regex: `/^[a-zA-Z0-9][a-zA-Z0-9._@-]{2,49}$/`. When omitted, username is auto-generated from email (backward compatibility).
  - `password` (password-based only): Required for password activation.
  - `googleUserId`, `googleEmail`, `googleProfilePictureUrl` (OAuth-based only): Required for OAuth activation.
- Username rules:
  - 3-50 characters
  - Must start with a letter or number
  - Allowed characters: letters, numbers, `.`, `_`, `-`, `@`
  - Reserved usernames are not allowed (e.g., admin, support, system)
- Response:
```json
{
  "success": true,
  "data": {
    "accessToken": "jwt",
    "refreshToken": "jwt",
    "user": {
      "id": "uuid",
      "username": "johndoe",
      "personId": "uuid",
      "tenantId": "uuid",
      "status": "Active",
      "createdAt": "2026-01-12T00:00:00Z"
    },
    "person": {
      "id": "uuid",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@example.com",
      "linkedUserId": "uuid"
    },
    "tenant": {
      "id": "uuid",
      "name": "Acme Corp",
      "status": "Active"
    }
  }
}
```
- **Note**: `tenant.name` is populated from the business foundation's company name if available, otherwise falls back to the tenant's name field.
- **Email Verification** (Issue #619): When a user activates their account via invitation, their email is automatically marked as verified (`person.isEmailVerified = true`). The invitation acceptance itself serves as email validation, eliminating the need for a separate email verification step. The user's status is set to `Active` immediately upon successful activation.
- Errors:
  - 400 `VALIDATION_ERROR`: Invalid token/expired/already used/person already linked/email mismatch (OAuth)/invalid username format.
  - 409 `USERNAME_NOT_AVAILABLE`: The specified username is already taken by another user (global uniqueness check).
- **Backward Compatibility**: When `username` is omitted, the system auto-generates a username from the person's email address (existing behavior).

**Error Responses:**

```json
{
  "success": false,
  "error": "Username is already taken",
  "code": "DUPLICATE_RESOURCE",
  "details": {
    "field": "username"
  }
}
```

```json
{
  "success": false,
  "error": "Username is invalid",
  "code": "VALIDATION_ERROR",
  "details": {
    "field": "username"
  }
}
```

## Users (Multi-User Operations - Owner Only)

### GET /users
**Owner-Only** - List all users in tenant.

- Query: `status` (optional: `Active|Inactive` - omit to return all users).
- Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "username": "johndoe",
      "personId": "uuid",
      "person": {
        "firstName": "John",
        "lastName": "Doe",
        "email": "john.doe@example.com"
      },
      "status": "Active",
      "createdAt": "2026-01-01T00:00:00Z",
      "lastLoginAt": "2026-01-12T08:00:00Z"
    }
  ]
}
```
- Errors: 403 not owner.

### GET /users/count
**Owner-Only** - Get count of users in tenant (for billing and management).

- Query: `status` (optional: `Active|Inactive` - omit to return count of all users).
- Response:
```json
{
  "success": true,
  "data": {
    "userCount": 5
  }
}
```
- Errors: 403 not owner.

### POST /users/{id}/deactivate
**Owner-Only** - Deactivate another user (cannot deactivate self).

- Path: user ID (GUID).
- Response: `{ "success": true, "message": "User deactivated successfully" }`.
- Errors: 403 not owner, 400 cannot deactivate self, 404 user not found.

## Health

### GET /health
- Response: `{ "success": true, "data": { "status": "Healthy", "service": "PurposePath Account Lambda", "version": "x.y.z", "timestamp": "ISO-8601", "environment": "string" } }`.

### GET /health/detailed
- Response includes `checks` array with component-level statuses; returns 503 when any check fails.

### GET /health/ready
- Response: `{ "success": true, "data": { "status": "Ready", "timestamp": "ISO-8601", "message": "Service is ready to accept requests" } }`.

### GET /health/live
- Response: `{ "success": true, "data": { "status": "Alive", "timestamp": "ISO-8601", "message": "Service is running" } }`.
