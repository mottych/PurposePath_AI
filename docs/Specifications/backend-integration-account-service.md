# Account Service Backend Integration Specifications

**Version:** 3.0  
**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`  
**Dev Environment:** `https://api.dev.purposepath.app/account/api/v1`

[← Back to Index](./backend-integration-index.md)

## Overview

The Account Service handles all user authentication, profile management, subscription/billing operations, and onboarding workflows.

### Frontend Implementation

- **Primary Client:** `accountClient` (axios instance in `src/services/api.ts`)
- **Related Files:**
  - `src/services/api.ts` - Main ApiClient class
  - `src/services/account.ts` - Account-specific operations
  - `src/services/subscriptions.ts` - Subscription management
  - `src/services/users.ts` - User profile operations

---

## Authentication Endpoints

### POST /auth/login

User authentication with email/password.

**Request:**

```json
{
  "email": "string",
  "password": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "user": {
      "user_id": "string",
      "email": "string",
      "first_name": "string",
      "last_name": "string",
      "avatar_url": "string?",
      "created_at": "string",
      "updated_at": "string",
      "status": "string",
      "email_verified": "boolean",
      "preferences": {}
    },
    "tenant": {
      "id": "string",
      "name": "string"
    }
  }
}
```

**Special Headers:**

- `X-Frontend-Base-Url: {window.location.origin}` (if `REACT_APP_FE_BASE_HEADER_LOGIN=true`)

**Frontend Handling:**

- Stores `access_token` → `localStorage.accessToken`
- Stores `refresh_token` → `localStorage.refreshToken`
- Stores `tenant.id` → `localStorage.tenantId`
- Maps backend snake_case to frontend camelCase

**Implementation:** `src/services/api.ts` → `ApiClient.login()`

---

### POST /auth/google

Google OAuth authentication.

**Request:**

```json
{
  "token": "string"
}
```

**Response:** Same as `/auth/login`

**Frontend Handling:**

- Same token storage as email/password login
- Google token obtained from Google OAuth flow

**Implementation:** `src/services/api.ts` → `ApiClient.loginWithGoogle()`

---

### POST /auth/register

New user registration.

**Request:**

```json
{
  "email": "string",
  "password": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string?"
}
```

**Response (Immediate Auth):**

```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "user": "UserProfile",
    "tenant": "TenantInfo"
  }
}
```

**Response (Email Verification Required):**

```json
{
  "success": true,
  "data": {
    "requires_email_verification": true,
    "tenant_id": "string"
  }
}
```

**Special Headers:** `X-Frontend-Base-Url: {window.location.origin}`

**Frontend Handling:**

- If tokens returned: same as login flow
- If verification required: show verification pending UI
- Strips non-digits from phone number before sending

**Implementation:** `src/services/api.ts` → `ApiClient.register()`

---

### POST /auth/forgot-password

Initiate password reset flow.

**Request:**

```json
{
  "email": "string"
}
```

**Response:**

```json
{
  "success": true
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.forgotPassword()`

---

### POST /auth/reset-password

Complete password reset with token.

**Request:**

```json
{
  "token": "string",
  "new_password": "string"
}
```

**Response:**

```json
{
  "success": true
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.resetPassword()`

---

### POST /auth/refresh

Refresh access token using refresh token.

**Request:**

```json
{
  "refresh_token": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string"
  }
}
```

**Frontend Handling:**

- Automatically called on 401 responses
- Updates stored tokens
- Retries original failed request

**Implementation:** `src/services/api.ts` → `ApiClient.refreshToken()` (private)

---

### POST /auth/resend-confirmation

Resend email confirmation link.

**Query Parameters:**

- `email` - Email address to resend confirmation to

**Special Headers:** `X-Frontend-Base-Url: {window.location.origin}`

**Response:**

```json
{
  "success": true
}
```

---

### POST /auth/confirm-email

Confirm email address with token.

**Request:**

```json
{
  "token": "string"
}
```

**Response:**

```json
{
  "success": true
}
```

---

### GET /auth/confirm-email/validate

Validate email confirmation token without consuming it.

**Query Parameters:**

- `token` - Email confirmation token

**Response:**

```json
{
  "success": true,
  "data": {
    "status": "valid|used|expired|not_found"
  }
}
```

---

### POST /auth/logout

User logout (invalidates refresh token).

**Query Parameters:**

- `refresh_token` - Refresh token to invalidate

**Response:**

```json
{
  "success": true
}
```

**Frontend Handling:**

- Clears all localStorage tokens and tenant ID
- Redirects to login page

---

## User Management Endpoints

### GET /user/profile

Get current authenticated user's profile.

**Headers Required:**

- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}`

**Response:**

```json
{
  "success": true,
  "data": {
    "user_id": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "avatar_url": "string?",
    "created_at": "string",
    "updated_at": "string",
    "status": "string",
    "email_verified": "boolean",
    "preferences": {}
  }
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.getUserProfile()`

---

### PUT /user/profile

Update user profile.

**Request:**

```json
{
  "first_name": "string?",
  "last_name": "string?",
  "phone": "string?",
  "avatar_url": "string?",
  "preferences": {}
}
```

**Response:**

```json
{
  "success": true,
  "data": "UserProfile"
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.updateUserProfile()`

---

### GET /user/features

Get enabled features for current user based on subscription tier.

**Response:**

```json
{
  "success": true,
  "data": ["goals", "operations", "realtime", "reports", "bulkPlanner"]
}
```

**Feature Values:**

- `goals` - Goals module access
- `operations` - Operations module access
- `kpis` - KPIs module access
- `strategies` - Strategic planning module access
- `reports` - Report generation capability
- `realtime` - Real-time updates via SSE
- `attachments` - File attachment features
- `bulkPlanner` - Bulk planning operations
- `strategyCompare` - Strategy comparison tools
- `goalCreate` - Goal creation permissions

**Implementation:** `src/services/api.ts` → `ApiClient.getUserFeatures()`

---

### GET /user/limits

Get user quotas and limits based on subscription tier.

**Response:**

```json
{
  "success": true,
  "data": {
    "goals": 10,
    "kpis": 50,
    "actions": null,
    "strategies": 20
  }
}
```

**Notes:**

- `null` means unlimited
- Keys correspond to module names
- Frontend should enforce these limits in UI

**Implementation:** `src/services/api.ts` → `ApiClient.getUserLimits()`

---

### GET /users/{id}

Get user by ID (for display purposes like assignee names).

**Path Parameters:**

- `id` - User ID

**Response:**

```json
{
  "success": true,
  "data": {
    "user_id": "string",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "avatar_url": "string?"
  }
}
```

**Implementation:** `src/services/users.ts` → `getUserById()`

---

## Subscription and Billing Endpoints

### GET /subscription/tiers

Get all available subscription tiers with pricing (dynamic).

**Response:**

```json
{
  "success": true,
  "data": [{
    "id": "string",
    "name": "string",
    "description": "string",
    "features": ["goals", "operations", "reports"],
    "limits": {
      "goals": 10,
      "kpis": 50,
      "actions": null
    },
    "pricing": {
      "monthly": 29.99,
      "yearly": 299.99
    },
    "supportedFrequencies": ["monthly", "yearly"],
    "isActive": true
  }]
}
```

**Notes:**

- Pricing is dynamic and may change
- `supportedFrequencies` indicates which billing cycles are available
- If tier only supports monthly, `yearly` will be `null`
- Both monthly and yearly subscriptions can be cancelled anytime

**Implementation:** `src/services/subscriptions.ts` → `getSubscriptionTiers()`

---

### GET /user/subscription

Get current user's subscription details with tier information.

**Response:**

```json
{
  "success": true,
  "data": {
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
    "isTrial": false,
    "trialEndDate": "string?",
    "trialExtendedBy": "string?",
    "trialExtensionReason": "string?"
  }
}
```

**Implementation:** `src/services/subscriptions.ts` → `getUserSubscription()`

---

### POST /user/subscription

Create new subscription (for users without active subscription).

**Request:**

```json
{
  "tierId": "string",
  "frequency": "monthly|yearly",
  "promoCode": "string?",
  "paymentMethodId": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": "UserSubscription",
    "requiresPaymentConfirmation": false,
    "clientSecret": "string?"
  }
}
```

**Notes:**

- `paymentMethodId` from Stripe Elements payment collection
- `clientSecret` returned if payment requires additional 3D Secure confirmation
- Backend handles Stripe payment processing

**Implementation:** `src/services/subscriptions.ts` → `createSubscription()`

---

### PUT /user/subscription

Update existing subscription (for users with active subscription).

**Request:**

```json
{
  "tierId": "string",
  "frequency": "monthly|yearly",
  "promoCode": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": "UserSubscription",
    "effectiveDate": "2025-11-01T00:00:00Z"
  }
}
```

**Notes:**

- Changes take effect at end of current billing cycle
- `effectiveDate` indicates when change applies
- Frequency must be in tier's `supportedFrequencies`

**Implementation:** `src/services/api.ts` → `ApiClient.updateSubscription()`

---

### DELETE /user/subscription

Cancel user subscription.

**Request:**

```json
{
  "reason": "string?",
  "cancelAtPeriodEnd": true
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": "UserSubscription",
    "cancelEffectiveDate": "2025-11-01T00:00:00Z"
  }
}
```

**Notes:**

- If `cancelAtPeriodEnd` is `true`, cancellation at end of billing period
- If `false`, immediate cancellation
- User retains access until `cancelEffectiveDate`

**Implementation:** `src/services/subscriptions.ts` → `cancelSubscription()`

---

### POST /subscription/promo/validate

Validate promo code and calculate discounted price.

**Request:**

```json
{
  "promoCode": "string",
  "tierId": "string",
  "frequency": "monthly|yearly"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "isValid": true,
    "discount": {
      "type": "percentage|fixed",
      "value": 20,
      "duration": "once|repeating|forever",
      "durationInMonths": 6
    },
    "newPrice": 23.99
  }
}
```

**Implementation:** `src/services/subscriptions.ts` → `validatePromoCode()`

---

### POST /subscription/trial/start

Start trial subscription without payment method.

**Request:**

```json
{
  "tierId": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": "UserSubscription",
    "trialEndDate": "2025-11-13T00:00:00Z"
  }
}
```

**Notes:**

- Trial duration determined by backend configuration
- User can upgrade to paid during or after trial

**Implementation:** `src/services/subscriptions.ts` → `startTrial()`

---

### POST /billing/portal

Get Stripe billing portal URL for subscription management.

**Request:**

```json
{
  "return_url": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "url": "https://billing.stripe.com/session/..."
  }
}
```

**Frontend Handling:**

- Redirect user to returned URL
- User manages payment methods, invoices, etc. in Stripe portal

**Implementation:** `src/services/api.ts` → `ApiClient.getBillingPortalUrl()`

---

### POST /billing/payment-intent

Create Stripe payment intent for subscription setup.

**Request:**

```json
{
  "tierId": "string",
  "frequency": "monthly|yearly",
  "promoCode": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "clientSecret": "pi_xxx_secret_xxx",
    "amount": 2999,
    "currency": "usd"
  }
}
```

**Notes:**

- Amount in cents (2999 = $29.99)
- `clientSecret` used with Stripe Elements for payment collection
- Amount reflects tier pricing with promo code discount applied

**Implementation:** Used internally by subscription flows

---

### POST /billing/webhook

Handle Stripe webhooks (internal, not called by frontend).

**Notes:**

- Backend-only endpoint
- Handles async payment confirmations, failures, subscription updates
- Updates subscription status based on Stripe events

---

### PUT /user/subscription/auto-renewal

Update auto-renewal setting for subscription.

**Request:**

```json
{
  "autoRenewal": true
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": "UserSubscription"
  }
}
```

**Implementation:** `src/services/subscriptions.ts` → `updateAutoRenewal()`

---

## Admin Trial Management Endpoints

### PUT /admin/users/{userId}/subscription/trial/extend

Extend trial subscription for a user (admin only).

**Path Parameters:**

- `userId` - User ID to extend trial for

**Request:**

```json
{
  "newExpirationDate": "2025-12-01T00:00:00Z",
  "reason": "Customer success initiative",
  "extendedBy": "admin_user_id"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "subscription": "UserSubscription",
    "previousExpirationDate": "2025-11-13T00:00:00Z",
    "newExpirationDate": "2025-12-01T00:00:00Z"
  }
}
```

**Notes:**

- Requires admin authentication
- Can extend both active and expired trials
- Logged for audit purposes

---

### GET /admin/users/{userId}/subscription/trial/history

Get trial extension history for a user (admin only).

**Path Parameters:**

- `userId` - User ID

**Response:**

```json
{
  "success": true,
  "data": [{
    "id": "string",
    "previousExpirationDate": "string",
    "newExpirationDate": "string",
    "extendedBy": "string",
    "reason": "string",
    "extendedAt": "string"
  }]
}
```

---

## Onboarding Endpoints

### GET /onboarding

Get current user's onboarding data.

**Response:**

```json
{
  "success": true,
  "data": {
    "businessName": "string",
    "website": "string?",
    "address": {
      "street": "string",
      "city": "string",
      "state": "string",
      "zip": "string",
      "country": "string"
    },
    "products": [{
      "id": "string",
      "name": "string",
      "problem": "string"
    }],
    "step3": {
      "niche": "string",
      "ica": "string",
      "valueProposition": "string"
    },
    "step4": {
      "coreValues": ["string"],
      "coreValuesStatus": "Not started|In progress|Completed",
      "purpose": "string",
      "purposeStatus": "Not started|In progress|Completed",
      "vision": "string",
      "visionStatus": "Not started|In progress|Completed"
    }
  }
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.getOnboarding()`

---

### PUT /onboarding

Update onboarding data (partial or complete).

**Request:**

```json
{
  "businessName": "string?",
  "website": "string?",
  "address": {
    "street": "string?",
    "city": "string?",
    "state": "string?",
    "zip": "string?",
    "country": "string?"
  },
  "products": [{
    "id": "string",
    "name": "string",
    "problem": "string"
  }],
  "step3": {
    "niche": "string?",
    "ica": "string?",
    "valueProposition": "string?"
  },
  "step4": {
    "coreValues": ["string"],
    "coreValuesStatus": "string",
    "purpose": "string",
    "purposeStatus": "string",
    "vision": "string",
    "visionStatus": "string"
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": "OnboardingData"
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.updateOnboarding()`

---

### POST /onboarding/products

Create new product entry in onboarding.

**Request:**

```json
{
  "name": "string",
  "problem": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "problem": "string"
  }
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.createOnboardingProduct()`

---

### PUT /onboarding/products/{id}

Update product entry.

**Path Parameters:**

- `id` - Product ID

**Request:**

```json
{
  "name": "string",
  "problem": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "name": "string",
    "problem": "string"
  }
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.updateOnboardingProduct()`

---

### DELETE /onboarding/products/{id}

Delete product entry.

**Path Parameters:**

- `id` - Product ID

**Response:**

```json
{
  "success": true
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.deleteOnboardingProduct()`

---

## Business Foundation Endpoints

The Business Foundation endpoints manage the strategic foundation of the business including vision, purpose, core values, and market positioning. This data is used by the strategic planning module and AI alignment engine.

### GET /api/business/foundation

Get business identity and strategic foundation.

**Response:**

```json
{
  "success": true,
  "data": {
    "businessName": "string",
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string?",
    "valueProposition": "string?"
  }
}
```

**Response Fields:**

- `businessName` - Company name
- `vision` - Long-term vision statement
- `purpose` - Company purpose/mission
- `coreValues` - Array of core values (e.g., ["Innovation", "Integrity", "Customer Focus"])
- `targetMarket` - Target market description (optional)
- `valueProposition` - Unique value proposition (optional)

**Frontend Handling:**

- Cached for 5 minutes by `BusinessFoundationService`
- Used by alignment engine for strategic alignment calculations
- Required for strategic planning module
- Used in onboarding completeness checks

**Implementation:** `src/services/business-foundation-service.ts` → `getBusinessFoundation()`

---

### PUT /api/business/foundation

Update business foundation information (partial updates supported).

**Request:**

```json
{
  "businessName": "string?",
  "vision": "string?",
  "purpose": "string?",
  "coreValues": ["string"]?,
  "targetMarket": "string?",
  "valueProposition": "string?"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "businessName": "string",
    "vision": "string",
    "purpose": "string",
    "coreValues": ["string"],
    "targetMarket": "string?",
    "valueProposition": "string?"
  }
}
```

**Notes:**

- All fields are optional (partial update pattern)
- Returns complete updated foundation
- Updates invalidate the cache in `BusinessFoundationService`
- Typically called during onboarding or business settings

**Implementation:** `src/services/business-foundation-service.ts` → `updateBusinessFoundation()`

---

## Error Responses

All Account Service endpoints follow the standard error format:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `INVALID_CREDENTIALS` - Login failed
- `EMAIL_ALREADY_EXISTS` - Registration with existing email
- `INVALID_TOKEN` - Expired or invalid token
- `SUBSCRIPTION_LIMIT_REACHED` - User at subscription limit
- `PAYMENT_FAILED` - Payment processing error
- `PROMO_CODE_INVALID` - Invalid or expired promo code

---

**Navigation:**

- [← Back to Index](./backend-integration-index.md)
- [Coaching Service Specs →](./backend-integration-coaching-service.md)
- [Traction Service Specs →](./backend-integration-traction-service.md)
- [Common Patterns →](./backend-integration-common-patterns.md)
