# Account Service Backend Integration Specifications

**Version:** 5.2  
**Last Updated:** December 29, 2025  
**Audit Summary:** Added Core Values Management endpoints (POST, GET, PUT, DELETE, PUT:reorder) at `/business/foundation/values`. Core values now support detailed fields: name, meaning, implementation, and behaviors (max 10). These CRUD endpoints provide full management separate from the legacy PATCH endpoint which only handles core value names as string arrays.

**Previous Changes:**
- **v5.1 (December 28, 2025):** Added `personId` field to authentication and user profile responses
- **v5.0 (December 26, 2025):** Added complete Business Foundation endpoints with section-specific PATCH endpoints

**Service Base URL:** `{REACT_APP_ACCOUNT_API_URL}`  
**Default (Localhost):** `http://localhost:8001`  
**Dev Environment:** `https://api.dev.purposepath.app/account/api/v1`

[← Back to Index](./index.md)

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
    "accessToken": "string",
    "refreshToken": "string",
    "user": {
      "userId": "string",
      "email": "string",
      "firstName": "string",
      "lastName": "string",
      "personId": "string?",
      "avatarUrl": "string?",
      "createdAt": "string",
      "updatedAt": "string",
      "status": "string",
      "isEmailVerified": "boolean",
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

- Stores `accessToken` → `localStorage.accessToken`
- Stores `refreshToken` → `localStorage.refreshToken`
- Stores `tenant.id` → `localStorage.tenantId`

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
  "firstName": "string",
  "lastName": "string",
  "phone": "string?"
}
```

**Response (Immediate Auth):**

```json
{
  "success": true,
  "data": {
    "accessToken": "string",
    "refreshToken": "string",
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
    "requiresEmailVerification": true,
    "tenantId": "string"
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
  "newPassword": "string"
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
  "refreshToken": "string"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "accessToken": "string",
    "refreshToken": "string"
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
    "status": "valid|used|expired|notFound"
  }
}
```

---

### POST /auth/logout

User logout (invalidates refresh token).

**Query Parameters:**

- `refreshToken` - Refresh token to invalidate

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
    "userId": "string",
    "email": "string",
    "firstName": "string",
    "lastName": "string",
    "personId": "string?",
    "avatarUrl": "string?",
    "createdAt": "string",
    "updatedAt": "string",
    "status": "string",
    "isEmailVerified": "boolean",
    "preferences": {}
  }
}
```

**Notes:**
- `personId` links to the Person entity in the organization structure
- May be `null` if Person record not yet created for user
- Frontend should use `personId` (not `userId`) for Traction API calls that require Person identification

**Implementation:** `src/services/api.ts` → `ApiClient.getUserProfile()`

---

### PUT /user/profile

Update user profile.

**Request:**

```json
{
  "firstName": "string?",
  "lastName": "string?",
  "phone": "string?",
  "avatarUrl": "string?",
  "preferences": {}
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "userId": "string",
    "email": "string",
    "firstName": "string",
    "lastName": "string",
    "personId": "string?",
    "avatarUrl": "string?",
    "createdAt": "string",
    "updatedAt": "string",
    "status": "string",
    "isEmailVerified": "boolean",
    "preferences": {}
  }
}
```

**Notes:**
- Returns updated profile with same structure as GET /user/profile
- `personId` included in response

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
- `measures` - Measures module access
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
    "measures": 50,
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
    "userId": "string",
    "email": "string",
    "firstName": "string",
    "lastName": "string",
    "avatarUrl": "string?"
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
      "measures": 50,
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
  "returnUrl": "string?"
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
  "extendedBy": "adminUserId"
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

### GET /business/onboarding

Get current user's onboarding data.

**URL:** `GET /business/onboarding`

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

### PUT /business/onboarding

Update onboarding data (partial or complete).

**URL:** `PUT /business/onboarding`

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
    "id": "string?",
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

**Products Field Behavior (Smart Merge):**
- Products **with `id`**: Updates existing product
- Products **without `id`** (null/omitted): Creates new product with generated ID
- Products **not in array**: Deleted from business
- **Optional**: Can omit `products` field entirely to leave products unchanged

**Implementation:** `src/services/api.ts` → `ApiClient.updateOnboarding()`

---

### PUT /business/onboarding/products

**[NEW]** Bulk update all products - replaces entire product list.

**URL:** `PUT /business/onboarding/products`

**Request:**

```json
{
  "products": [{
    "id": "string?",
    "name": "string",
    "problem": "string"
  }]
}
```

**Response:**

```json
{
  "success": true,
  "data": [{
    "id": "string",
    "name": "string",
    "problem": "string"
  }]
}
```

**Behavior (Smart Merge):**
- Products **with `id`**: Updates existing product
- Products **without `id`**: Creates new product with generated ID
- Products **not in array**: Deleted from business

**Use Case:** Replace entire products list in one transaction (e.g., onboarding form submission).

**Implementation:** `src/services/api.ts` → `ApiClient.updateAllOnboardingProducts()`

---

### POST /business/onboarding/products

Create a new product during onboarding.

**URL:** `POST /business/onboarding/products`

**Request (current schema):**

Only `name` is required. All other fields are optional.

```json
{
  "name": "string",
  "tagline": "string",
  "description": "string",
  "problemSolved": "string",
  "type": "Product|Service|Subscription|Hybrid",
  "status": "Active|InDevelopment|Planned|Retired",
  "targetAudienceIcaId": "guid",
  "keyFeatures": ["string"],
  "pricingTier": "Premium|MidMarket|EntryLevel|Free",
  "pricingModel": "OneTime|Subscription|UsageBased|Freemium|Custom",
  "revenueContribution": "Primary|Secondary|Emerging",
  "differentiators": "string",
  "displayOrder": 0
}
```

Legacy input `problem` is accepted and mapped to `problemSolved`.

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "tenantId": "guid",
    "businessFoundationId": "guid|null",
    "name": "string",
    "tagline": "string|null",
    "description": "string|null",
    "problemSolved": "string|null",
    "type": "Product|Service|Subscription|Hybrid",
    "status": "Active|InDevelopment|Planned|Retired",
    "targetAudienceIcaId": "guid|null",
    "keyFeatures": ["string"],
    "pricingTier": "Premium|MidMarket|EntryLevel|Free|null",
    "pricingModel": "OneTime|Subscription|UsageBased|Freemium|Custom|null",
    "revenueContribution": "Primary|Secondary|Emerging|null",
    "differentiators": "string|null",
    "displayOrder": 0,
    "isFlagship": false,
    "isActive": true,
    "createdAt": "ISO-8601",
    "updatedAt": "ISO-8601|null"
  }
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.createOnboardingProduct()`

---

### PUT /business/onboarding/products/{id}

Update an existing onboarding product.

**URL:** `PUT /business/onboarding/products/{id}`

**Path Parameters:**

- `id` - Product ID

**Request (current schema):**

Only `name` is required. All other fields are optional.

```json
{
  "name": "string",
  "tagline": "string",
  "description": "string",
  "problemSolved": "string",
  "type": "Product|Service|Subscription|Hybrid",
  "status": "Active|InDevelopment|Planned|Retired",
  "targetAudienceIcaId": "guid",
  "keyFeatures": ["string"],
  "pricingTier": "Premium|MidMarket|EntryLevel|Free",
  "pricingModel": "OneTime|Subscription|UsageBased|Freemium|Custom",
  "revenueContribution": "Primary|Secondary|Emerging",
  "differentiators": "string",
  "displayOrder": 0
}
```

Legacy input `problem` is accepted and mapped to `problemSolved`.

**Response:**

Same as POST response schema.

**Implementation:** `src/services/api.ts` → `ApiClient.updateOnboardingProduct()`

---

### DELETE /business/onboarding/products/{id}

Delete product entry.

**URL:** `DELETE /business/onboarding/products/{id}`

**Path Parameters:**

- `id` - Product ID

**Response:**

```json
{
  "success": true,
  "message": "Product deleted successfully"
}
```

**Implementation:** `src/services/api.ts` → `ApiClient.deleteOnboardingProduct()`

---

## Business Foundation Endpoints

The Business Foundation endpoints manage the strategic foundation of the business including company profile, core identity (vision, purpose, mission), target market, value proposition, and business model. This data is used by the strategic planning module and AI alignment engine.

**Base Path:** `/business/foundation`

### GET /business/foundation

Get complete business foundation with all sections and related entities.

**Query Parameters:**

- `includeCoreValues` (boolean, default: true) - Include related core values
- `includeProducts` (boolean, default: true) - Include related products
- `includeIdealCustomerAvatars` (boolean, default: false) - Include related ICAs

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "tenantId": "string (GUID)",
    "completionPercentage": "number (0-100)",
    "version": "number",
    "profile": {
      "companyName": "string",
      "companyDescription": "string?",
      "industry": "string?",
      "subIndustry": "string?",
      "stage": "CompanyStage?",
      "size": "CompanySize?",
      "revenueRange": "RevenueRange?",
      "yearFounded": "number?",
      "geographicFocus": "GeographicFocus?",
      "website": "string?",
      "address": {
        "street": "string?",
        "city": "string?",
        "state": "string?",
        "postalCode": "string?",
        "country": "string?"
      }
    },
    "coreIdentity": {
      "purpose": "string?",
      "vision": "string?",
      "visionTimeframe": "number?",
      "mission": "string?",
      "whoWeServe": "string?",
      "coreValueIds": ["string (GUID)"]
    },
    "targetMarket": {
      "niche": "string?",
      "primaryAudience": "string?",
      "marketSize": "string?",
      "growthTrend": "GrowthTrend?",
      "painPoints": ["string"],
      "desires": ["string"],
      "idealCustomerAvatarIds": ["string (GUID)"]
    },
    "valueProposition": {
      "statement": "string?",
      "uniqueSellingProposition": "string?",
      "keyBenefits": ["string"],
      "differentiators": ["string"],
      "proofPoints": ["string"],
      "customerOutcomes": ["string"],
      "brandPromise": "string?",
      "primaryCompetitors": ["string"],
      "competitiveAdvantage": "string?",
      "marketPosition": "MarketPosition?"
    },
    "businessModel": {
      "type": "BusinessModelType?",
      "secondaryTypes": ["BusinessModelType"],
      "primaryRevenueStream": "string?",
      "revenueStreams": ["string"],
      "pricingStrategy": "string?",
      "keyPartners": ["string"],
      "distributionChannels": ["string"],
      "customerAcquisitionStrategy": "string?",
      "marketPosition": "MarketPosition?",
      "productIds": ["string (GUID)"]
    },
    "coreValues": [
      {
        "id": "string (GUID)",
        "tenantId": "string (GUID)",
        "businessFoundationId": "string (GUID)",
        "name": "string",
        "description": "string?",
        "behaviors": ["string"],
        "displayOrder": "number",
        "isActive": "boolean",
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)?"
      }
    ],
    "idealCustomerAvatars": [
      {
        "id": "string (GUID)",
        "tenantId": "string (GUID)",
        "businessFoundationId": "string (GUID)",
        "name": "string",
        "description": "string?",
        "isPrimary": "boolean",
        "isActive": "boolean",
        "ageRange": "string?",
        "gender": "string?",
        "location": "string?",
        "education": "string?",
        "incomeRange": "string?",
        "jobTitle": "string?",
        "industry": "string?",
        "companySize": "string?",
        "goals": ["string"],
        "challenges": ["string"],
        "values": ["string"],
        "objections": ["string"],
        "motivations": ["string"],
        "onlineChannels": ["string"],
        "contentPreferences": ["string"],
        "communicationPreference": "string?",
        "buyingProcess": "string?",
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)?"
      }
    ],
    "products": [
      {
        "id": "string (GUID)",
        "tenantId": "string (GUID)",
        "businessFoundationId": "string (GUID)?",
        "name": "string",
        "description": "string?",
        "type": "ProductType",
        "status": "ProductStatus",
        "displayOrder": "number",
        "isFlagship": "boolean",
        "pricingTier": "PricingTier?",
        "pricingModel": "PricingModel?",
        "revenueContribution": "RevenueContribution?",
        "features": ["string"],
        "targetSegments": ["string"],
        "createdAt": "string (ISO 8601)",
        "updatedAt": "string (ISO 8601)?"
      }
    ],
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

**Implementation:** `src/services/business-foundation-service.ts` → `getBusinessFoundation()`

---

### PATCH /business/foundation

Update a single field of business foundation using field/value pattern.

**Request:**

```json
{
  "field": "string (required)",
  "value": "any (required)"
}
```

**Field Options:**

| Field | Value Type | Description |
|-------|-----------|-------------|
| `vision` | string | Long-term vision statement |
| `purpose` | string | Company purpose/mission |
| `coreValues` | string[] | Array of core value names |
| `valueProposition` | string | Unique value proposition |
| `businessName` | string | Company name |
| `targetMarket` | string | Target market description |

**Response:** Complete `BusinessFoundationResponse` (see GET response above)

**Implementation:** `src/services/business-foundation-service.ts` → `patchBusinessFoundation()`

---

### PATCH /business/foundation/profile

Update the business profile section.

**Request:**

```json
{
  "businessName": "string?",
  "businessDescription": "string? (max 2000 chars)",
  "industry": "string?",
  "subIndustry": "string?",
  "website": "string?",
  "address": {
    "street": "string?",
    "city": "string?",
    "state": "string?",
    "zip": "string?",
    "country": "string?"
  },
  "headquartersLocation": "string?",
  "companyStage": "CompanyStage?",
  "companySize": "CompanySize?",
  "revenueRange": "RevenueRange?",
  "yearFounded": "number?",
  "geographicFocus": ["GeographicFocus"]?"
}
```

**Response:** Complete `BusinessFoundationResponse`

---

### PATCH /business/foundation/identity

Update the core identity section (purpose, vision, mission).

**Request:**

```json
{
  "purpose": "string?",
  "vision": "string?",
  "visionTimeframe": "string? (e.g., '5 years' → parsed to 5)",
  "mission": "string?",
  "whoWeServe": "string?"
}
```

**Response:** Complete `BusinessFoundationResponse`

---

### PATCH /business/foundation/market

Update the target market section.

**Request:**

```json
{
  "niche": "string?",
  "primaryAudience": "string?",
  "marketSize": "string?",
  "growthTrend": "GrowthTrend?",
  "painPoints": ["string"]?,
  "desires": ["string"]?"
}
```

**GrowthTrend Enum Values:**

- `Declining` - Market is shrinking
- `Stable` - Market is stable
- `Growing` - Market is growing
- `RapidlyGrowing` - Market is rapidly expanding

**Response:** Complete `BusinessFoundationResponse`

---

### PATCH /business/foundation/proposition

Update the value proposition section.

**Request:**

```json
{
  "statement": "string?",
  "uniqueSellingProposition": "string?",
  "keyBenefits": ["string"]?,
  "differentiators": ["string"]?,
  "proofPoints": ["string"]?,
  "customerOutcomes": ["string"]?,
  "brandPromise": "string?",
  "primaryCompetitors": ["string"]?,
  "competitiveAdvantage": "string?",
  "marketPosition": "MarketPosition?"
}
```

**MarketPosition Enum Values:**

- `Leader` - Market leader
- `Challenger` - Challenging the leader
- `Niche` - Specialized niche player
- `Emerging` - New market entrant

**Response:** Complete `BusinessFoundationResponse`

---

### PATCH /business/foundation/model

Update the business model section.

**Request:**

```json
{
  "type": "BusinessModelType?",
  "secondaryTypes": ["BusinessModelType"]?,
  "primaryRevenueStream": "string?",
  "revenueStreams": ["string"]?,
  "pricingStrategy": "string?",
  "keyPartners": ["string"]?,
  "distributionChannels": ["string"]?,
  "customerAcquisitionStrategy": "string?",
  "marketPosition": "MarketPosition?"
}
```

**BusinessModelType Enum Values:**

- `B2B` - Business to Business
- `B2C` - Business to Consumer
- `B2B2C` - Business to Business to Consumer
- `Marketplace` - Two-sided marketplace
- `SaaS` - Software as a Service
- `Consulting` - Consulting/Advisory services
- `Ecommerce` - E-commerce/online retail
- `Other` - Other business model

**Response:** Complete `BusinessFoundationResponse`

---

## Core Values Management Endpoints

The following endpoints manage the detailed core values for a business foundation. Core values can have name, meaning, implementation, and behaviors. These endpoints provide full CRUD operations for managing core values separately from the foundation PATCH endpoints which only handle core value names.

### POST /business/foundation/values

Create a new core value for the business foundation.

**Request:**

```json
{
  "name": "string (required, max 100 chars)",
  "meaning": "string? (max 500 chars)",
  "implementation": "string? (max 500 chars)",
  "behaviors": ["string"]? (max 10 items, each max 500 chars)",
  "displayOrder": "number?"
}
```

**Field Descriptions:**

- `name` - The name of the core value (e.g., "Integrity", "Innovation", "Excellence")
- `meaning` - What this core value means to the organization
- `implementation` - How this core value is implemented in practice
- `behaviors` - Observable behaviors that demonstrate this core value (max 10)
- `displayOrder` - Sorting position (optional, defaults to next available)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "tenantId": "string",
    "businessFoundationId": "string",
    "name": "string",
    "meaning": "string?",
    "implementation": "string?",
    "behaviors": ["string"],
    "displayOrder": "number",
    "isActive": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string? (ISO 8601)"
  }
}
```

**Status Codes:**

- `201 Created` - Core value created successfully
- `400 Bad Request` - Validation error (invalid data)
- `404 Not Found` - Business foundation not found
- `401 Unauthorized` - Missing or invalid authentication

---

### GET /business/foundation/values/{id}

Get a specific core value by ID.

**Path Parameters:**

- `id` - Core value ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "tenantId": "string",
    "businessFoundationId": "string",
    "name": "string",
    "meaning": "string?",
    "implementation": "string?",
    "behaviors": ["string"],
    "displayOrder": "number",
    "isActive": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string? (ISO 8601)"
  }
}
```

**Status Codes:**

- `200 OK` - Core value retrieved successfully
- `404 Not Found` - Core value not found
- `401 Unauthorized` - Missing or invalid authentication

---

### PUT /business/foundation/values/{id}

Update an existing core value.

**Path Parameters:**

- `id` - Core value ID (GUID)

**Request:**

```json
{
  "name": "string? (max 100 chars)",
  "meaning": "string? (max 500 chars)",
  "implementation": "string? (max 500 chars)",
  "behaviors": ["string"]? (max 10 items)",
  "displayOrder": "number?",
  "isActive": "boolean?"
}
```

**Note:** All fields are optional. Only provided fields will be updated.

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "tenantId": "string",
    "businessFoundationId": "string",
    "name": "string",
    "meaning": "string?",
    "implementation": "string?",
    "behaviors": ["string"],
    "displayOrder": "number",
    "isActive": "boolean",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)"
  }
}
```

**Status Codes:**

- `200 OK` - Core value updated successfully
- `400 Bad Request` - Validation error
- `404 Not Found` - Core value not found
- `401 Unauthorized` - Missing or invalid authentication

---

### DELETE /business/foundation/values/{id}

Delete (deactivate) a core value.

**Path Parameters:**

- `id` - Core value ID (GUID)

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string",
    "deleted": true
  }
}
```

**Status Codes:**

- `200 OK` - Core value deleted successfully
- `404 Not Found` - Core value not found
- `401 Unauthorized` - Missing or invalid authentication

**Note:** Core values are soft-deleted (marked inactive) rather than permanently removed.

---

### PUT /business/foundation/values:reorder

Reorder core values by specifying the desired sequence of IDs.

**Request:**

```json
{
  "coreValueIds": ["string"] (required, array of core value IDs in desired order)
}
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": "string",
      "tenantId": "string",
      "businessFoundationId": "string",
      "name": "string",
      "meaning": "string?",
      "implementation": "string?",
      "behaviors": ["string"],
      "displayOrder": "number",
      "isActive": "boolean",
      "createdAt": "string (ISO 8601)",
      "updatedAt": "string (ISO 8601)"
    }
  ]
}
```

**Status Codes:**

- `200 OK` - Core values reordered successfully
- `400 Bad Request` - Invalid request (missing or invalid core value IDs)
- `401 Unauthorized` - Missing or invalid authentication

**Notes:**

- All core values must belong to the same business foundation
- Display order is automatically assigned based on array position (1, 2, 3, ...)
- Only active core values in the provided array will be updated

---

### GET /business/foundation/wizard-progress

Get the current wizard progress state for the business foundation wizard.

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "tenantId": "string (GUID)",
    "businessFoundationId": "string (GUID)",
    "currentStep": "number",
    "completedSteps": ["number"],
    "stepData": {
      "step1": { ... },
      "step2": { ... }
    },
    "lastActiveAt": "string (ISO 8601)",
    "createdAt": "string (ISO 8601)",
    "updatedAt": "string (ISO 8601)?"
  }
}
```

---

### PUT /business/foundation/wizard-progress

Update the wizard progress state.

**Request:**

```json
{
  "currentStep": "number",
  "completedSteps": ["number"]?,
  "stepData": "object?"
}
```

**Response:** Complete wizard progress response (see GET response above)

---

## Tenant Settings Endpoints

### GET /tenants/settings

Get current tenant settings (Measure configuration, etc).

**Authentication:** Required  
**Headers:**
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}` (auto-injected by frontend)

**Request:** None

**Response:**

```json
{
  "success": true,
  "data": {
    "targetLineMode": "single" | "three"
  }
}
```

**Response Fields:**
- `targetLineMode` (string): Measure target line configuration
  - `"single"` - Only expected target line (default)
  - `"three"` - Expected, optimal, and minimal target lines

**Status Codes:**
- `200` - Success
- `401` - Unauthorized (missing/invalid token)
- `404` - Tenant not found
- `500` - Server error

**Frontend Handling:** `src/services/account.ts`

---

### PUT /tenants/settings

Update current tenant settings.

**Authentication:** Required  
**Headers:**
- `Authorization: Bearer {accessToken}`
- `X-Tenant-Id: {tenantId}` (auto-injected by frontend)

**Request:**

```json
{
  "targetLineMode": "single" | "three"
}
```

**Request Fields:**
- `targetLineMode` (string, required): Target line mode configuration
  - Valid values: `"single"` or `"three"`

**Response:**

```json
{
  "success": true,
  "data": {
    "targetLineMode": "single" | "three"
  }
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request (missing field or invalid value)
- `401` - Unauthorized (missing/invalid token)
- `404` - Tenant not found
- `500` - Server error

**Business Rules:**
- Mode change does NOT affect existing Measure data
- Single mode: UI hides optimal/minimal target inputs
- Three mode: UI shows all three target inputs
- Charts always show expected line; optional lines only if data exists

**Frontend Handling:** `src/services/account.ts`

---

## Business Foundation Enumerations Reference

### CompanyStage

| Value | Description |
````
|-------|-------------|
| `Startup` | 0-2 years, finding product-market fit |
| `Growth` | 2-5 years, scaling operations |
| `Scale` | 5-10 years, expanding markets |
| `Mature` | 10+ years, optimizing operations |

### CompanySize

| Value | Description |
|-------|-------------|
| `Solo` | 1 employee (solopreneur) |
| `Micro` | 2-9 employees |
| `Small` | 10-49 employees |
| `Medium` | 50-249 employees |
| `Large` | 250-999 employees |
| `Enterprise` | 1000+ employees |

### RevenueRange

| Value | Description |
|-------|-------------|
| `PreRevenue` | No revenue yet |
| `Under100K` | $1 - $100K annually |
| `From100KTo500K` | $100K - $500K annually |
| `From500KTo1M` | $500K - $1M annually |
| `From1MTo5M` | $1M - $5M annually |
| `From5MTo10M` | $5M - $10M annually |
| `From10MTo50M` | $10M - $50M annually |
| `Over50M` | $50M+ annually |
| `NotDisclosed` | Prefer not to disclose |

### GeographicFocus

| Value | Description |
|-------|-------------|
| `Local` | Single city or local region |
| `Regional` | Multiple regions within a country |
| `National` | Entire country |
| `Global` | Multiple countries/international |

### ProductType

| Value | Description |
|-------|-------------|
| `Product` | Physical or digital product |
| `Service` | Professional service |
| `Subscription` | Recurring subscription offering |
| `Hybrid` | Combination of product and service |

### ProductStatus

| Value | Description |
|-------|-------------|
| `Active` | Currently available and active |
| `InDevelopment` | Currently being developed |
| `Planned` | Planned for future release |
| `Retired` | No longer offered |

### PricingTier

| Value | Description |
|-------|-------------|
| `Premium` | High-end/premium pricing |
| `MidMarket` | Middle-tier pricing |
| `EntryLevel` | Budget-friendly/entry-level pricing |
| `Free` | Free offering |

### PricingModel

| Value | Description |
|-------|-------------|
| `OneTime` | One-time purchase |
| `Subscription` | Recurring subscription |
| `UsageBased` | Pay per use/consumption |
| `Freemium` | Free tier with paid features |
| `Custom` | Custom/negotiated pricing |

### RevenueContribution

| Value | Description |
|-------|-------------|
| `Primary` | Main revenue source |
| `Secondary` | Supporting revenue stream |
| `Emerging` | New/growing revenue stream |

---

## Admin Discount Code Management

**Authentication Required:** Admin role (JWT with "Admin" role claim)  
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

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "isActive": true,
    ...
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

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "string (GUID)",
    "code": "string",
    "isActive": false,
    ...
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

### GET /admin/discount-codes/{id}/usage

Get redemption history and usage statistics for a discount code.

**Path Parameters:**

- `id` (string, GUID) - The discount code ID

**Query Parameters:**

- `page` (number, default: 1) - Page number (1-based)
- `pageSize` (number, default: 20) - Items per page (1-100)

**Response:**

```json
{
  "success": true,
  "data": {
    "discountCode": {
      "id": "string (GUID)",
      "code": "string",
      "currentRedemptions": "number",
      "maxRedemptions": "number"
    },
    "redemptions": [
      {
        "id": "string (GUID)",
        "tenantId": "string (GUID)",
        "tenantName": "string",
        "userId": "string (GUID)",
        "userEmail": "string",
        "subscriptionTier": "string",
        "subscriptionFrequency": "string",
        "appliedDiscountAmount": "number",
        "redeemedAt": "string (ISO 8601)"
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
- `400` - Invalid parameters
- `401` - Unauthorized
- `404` - Discount code not found

---

### POST /admin/discount-codes/validate

**PUBLIC ENDPOINT** - Validate a discount code during signup (NO AUTHENTICATION REQUIRED).

**Request:**

```json
{
  "code": "string",
  "tierId": "string",
  "frequency": "monthly | annual"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "isValid": "boolean",
    "code": "string",
    "discountType": "percentage | fixed",
    "discountValue": "number",
    "durationInCycles": "number",
    "calculatedDiscount": "number?",
    "error": "string?"
  }
}
```

**Validation Checks:**

1. Code exists and is active (`isActive = true`)
2. Code has not expired (`expiresAt` is null or future date)
3. Max redemptions limit not reached (`currentRedemptions < maxRedemptions`)
4. Code applies to specified subscription tier (or all tiers)
5. Code applies to specified billing frequency (or all frequencies)

**Response Fields:**

- `isValid`: `true` if all checks pass, `false` otherwise
- `discountType`: "percentage" or "fixed"
- `discountValue`: Percentage (1-100) or fixed dollar amount
- `durationInCycles`: Number of billing cycles discount applies
- `calculatedDiscount`: Actual dollar amount (for fixed discounts) or null (calculated at subscription time for percentage)
- `error`: Error message if `isValid = false`

**Status Codes:**

- `200` - Success (both valid and invalid codes return 200 with `isValid` flag)
- `400` - Invalid request format

**Security Considerations:**

- Returns generic "invalid code" message for non-existent codes
- Rate limiting recommended to prevent code enumeration attacks
- Validation attempts logged for security monitoring

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

- [← Back to Index](./index.md)
- [Coaching Service Specs →](./coaching-service.md)
- [Traction Service Specs →](./traction-service/README.md)
- [Common Patterns →](./common-patterns.md)
