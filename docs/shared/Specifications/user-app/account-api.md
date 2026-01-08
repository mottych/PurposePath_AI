# Account API Specification

**Version:** 2.1  
**Last Updated:** January 7, 2026  
**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}` (e.g., `https://api.dev.purposepath.app/account/api/v1`)

## Scope

Consolidated account endpoints implemented by the Account Lambda controllers: `Auth`, `Users`, `Tenants`, `SubscriptionTiers`, `UserSubscription`, `Billing`, `Subscriptions`, `BillingWebhook`, `Health`.

## Conventions

- JSON uses camelCase. Legacy snake_case inputs remain backwards compatible only where noted (logout refresh token).
- Response envelope (`ApiResponse<T>`): `{ "success": true|false, "data": {}, "message": "?", "error": "?", "code": "?" }`.
- Paginated responses use `PaginatedResponse<T>`: same envelope plus `pagination: { page, limit, total, totalPages }`.
- Authenticated endpoints require headers: `Authorization: Bearer {accessToken}`, `X-Tenant-Id: {tenantId}`. Public endpoints are marked.
- Optional headers: `X-Frontend-Base-Url` (used for auth emails), `X-E2E-Test: true` (DEV only to bypass email verification on register).

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
      "createdAt": "2025-12-29T00:00:00Z",
      "updatedAt": "2025-12-29T00:00:00Z"
    },
    "person": { "id": "uuid", "firstName": "string", "lastName": "string", "email": "string|null", "phone": "string|null", "title": "string|null" },
    "tenant": { "id": "uuid", "name": "string", "status": "string" }
  }
}
```
- Errors: 401 invalid credentials, 403 `EMAIL_NOT_VERIFIED`.

### POST /auth/google
- Body: `{ "token": "string" }` (Google ID token from OAuth flow).
- Response: same as login.
- Notes: Validates token with Google, creates new user/tenant if external identity not found, or logs in existing user. Auto-updates user avatar from Google profile if user has no avatar.

### POST /auth/microsoft
- Body: `{ "token": "string" }` (Microsoft ID token from OAuth/OIDC flow).
- Response: same as login.
- Notes: Validates token with Microsoft OIDC metadata endpoint, creates new user/tenant if external identity not found, or logs in existing user. Auto-updates user avatar from Microsoft profile if user has no avatar.

### POST /auth/register
- Body: `{ "username": "string", "email": "string", "password": "string", "firstName": "string", "lastName": "string", "phone": "string|null" }`.
- DEV-only bypass: `X-E2E-Test: true` skips email verification.
- Response: `AuthResponse` (auto-login path) or validation error. Email verification links use `X-Frontend-Base-Url` if provided.

### POST /auth/forgot-password
- Body: `{ "email": "string" }`.
- Response: `{ "success": true, "message": "Password reset email sent" }`.

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

## Users

### GET /users/{id}
- Path: user ID (GUID). Public auth required.
- Response: `{ "success": true, "data": { "userId": "uuid", "email": "string", "firstName": "string", "lastName": "string", "avatarUrl": "string|null" } }`.

### GET /user/profile
- Response `UserProfileDetailResponse`: user info with preferences and `personId`.

### PUT /user/profile
- Body (all optional): `{ "firstName": "string|null", "lastName": "string|null", "phone": "string|null", "avatarUrl": "string|null", "preferences": { "theme": "string", "language": "string", "timezone": "string", "dateFormat": "string", "timeFormat": "string", "currency": "string", "notifications": { "email": true, "push": true, "sms": true, "marketing": true, "coachingReminders": true, "teamUpdates": true, "systemNotifications": true }, "coaching": { "preferredSessionLength": 60, "reminderFrequency": "weekly", "coachingStyle": "directive" } } }`.
- Response: updated `UserProfileDetailResponse`.

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

## Health

### GET /health
- Response: `{ "success": true, "data": { "status": "Healthy", "service": "PurposePath Account Lambda", "version": "x.y.z", "timestamp": "ISO-8601", "environment": "string" } }`.

### GET /health/detailed
- Response includes `checks` array with component-level statuses; returns 503 when any check fails.

### GET /health/ready
- Response: `{ "success": true, "data": { "status": "Ready", "timestamp": "ISO-8601", "message": "Service is ready to accept requests" } }`.

### GET /health/live
- Response: `{ "success": true, "data": { "status": "Alive", "timestamp": "ISO-8601", "message": "Service is running" } }`.
