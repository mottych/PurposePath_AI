# Business Foundation API Specification

**Version:** 1.0  
**Status:** Verified Against Implementation  
**Last Updated:** December 30, 2025  
**Base URL:** `/business/foundation` and `/business/onboarding`

---

## Overview

The Business Foundation API provides complete management of the six strategic pillars:

1. **Business Profile** - Company facts, industry, stage, size
2. **Core Identity** - Vision, purpose, core values
3. **Target Market** - Niche statement, market size, ideal customer avatars (ICAs)
4. **Products & Services** - Product/service catalog with full details
5. **Value Proposition** - USP, key differentiators, competitive positioning
6. **Business Model** - Revenue streams, pricing, partnerships, distribution

The API implements 404 fallback pattern: When backend endpoints are not yet available, the frontend returns mock responses to allow UI development to proceed independently.

---

## Authentication & Headers

All endpoints require:

```
Authorization: Bearer {accessToken}
X-Tenant-Id: {tenantId}
Content-Type: application/json
```

Both headers must be present in request. Bearer token is obtained from `/auth/login` endpoint.

---

## Data Types & Constants

### Enums (Allowed Values)

**CompanyStage** (required in Business Profile)
- `startup` - Finding product-market fit (0-2 years)
- `growth` - Scaling what works (2-5 years)
- `scale` - Expanding markets/products (5-10 years)
- `mature` - Optimization and innovation (10+ years)

**CompanySize** (required in Business Profile)
- `solo` - 1 person
- `micro` - 2-10 employees
- `small` - 11-50 employees
- `medium` - 51-200 employees
- `large` - 201-1000 employees
- `enterprise` - 1000+ employees

**RevenueRange** (optional in Business Profile)
- `pre_revenue`
- `under_100k`
- `100k_500k`
- `500k_1m`
- `1m_5m`
- `5m_10m`
- `10m_50m`
- `over_50m`
- `not_disclosed`

**GeographicFocus** (array, required in Business Profile)
- `local`
- `regional`
- `national`
- `global`

**ProductType** (required when creating product)
- `product`
- `service`
- `subscription`
- `hybrid`

**ProductStatus** (required when creating product)
- `active`
- `in_development`
- `planned`
- `retired`

**PricingTier** (optional for product)
- `premium`
- `mid_market`
- `entry_level`
- `free`

**PricingModel** (optional for product)
- `one_time`
- `subscription`
- `usage_based`
- `freemium`
- `custom`

**GrowthTrend** (optional for target market)
- `declining`
- `stable`
- `growing`
- `rapidly_growing`

**BusinessModelType** (array in Business Model)
- `b2b` - Business to Business
- `b2c` - Business to Consumer
- `b2b2c`
- `marketplace`
- `saas` - Software as a Service
- `consulting`
- `ecommerce`
- `other`

**SectionStatus** (read-only)
- `empty` - No data provided
- `incomplete` - Partial data provided
- `complete` - Fully populated section

### Industry Options (for Business Profile)
Technology, Healthcare, Finance, Education, Retail, Manufacturing, Real Estate, Professional Services, Media & Entertainment, Food & Beverage, Transportation, Construction, Agriculture, Energy, Hospitality, Nonprofit, Government, Other

---

## Core Endpoints

### 1. GET /business/foundation

**Description:** Retrieve complete business foundation data for current tenant.

**HTTP Method:** GET

**Headers:**
- Authorization: Bearer {token}
- X-Tenant-Id: {tenantId}

**Request Parameters:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "tenantId": "string (UUID)",
    "profile": {
      "businessName": "string",
      "businessDescription": "string",
      "address": {
        "street": "string|null",
        "city": "string|null",
        "state": "string|null",
        "zip": "string|null",
        "country": "string (required)"
      },
      "industry": "string (must be from INDUSTRY_OPTIONS list)",
      "subIndustry": "string|null",
      "companyStage": "startup|growth|scale|mature",
      "companySize": "solo|micro|small|medium|large|enterprise",
      "revenueRange": "pre_revenue|under_100k|100k_500k|500k_1m|1m_5m|5m_10m|10m_50m|over_50m|not_disclosed|null",
      "yearFounded": "number|null",
      "geographicFocus": ["local|regional|national|global"],
      "headquartersLocation": "string|null",
      "website": "string|null"
    },
    "identity": {
      "vision": "string",
      "visionTimeframe": "string|null",
      "purpose": "string",
      "whoWeServe": "string|null",
      "values": [
        {
          "id": "string (UUID)",
          "name": "string",
          "meaning": "string",
          "implementation": "string",
          "behaviors": ["string"] | null,
          "displayOrder": "number",
          "createdAt": "string (ISO 8601 datetime)",
          "updatedAt": "string (ISO 8601 datetime)"
        }
      ]
    },
    "market": {
      "nicheStatement": "string",
      "marketSize": "string|null",
      "growthTrend": "declining|stable|growing|rapidly_growing|null",
      "icas": [
        {
          "id": "string (UUID)",
          "name": "string",
          "demographics": "string",
          "goals": "string",
          "painPoints": "string",
          "motivations": "string|null",
          "objections": "string|null",
          "whereToFind": "string|null",
          "buyingProcess": "string|null",
          "displayOrder": "number",
          "createdAt": "string (ISO 8601 datetime)",
          "updatedAt": "string (ISO 8601 datetime)"
        }
      ]
    },
    "products": [
      {
        "id": "string (UUID)",
        "name": "string",
        "tagline": "string|null",
        "type": "product|service|subscription|hybrid",
        "description": "string",
        "problemSolved": "string",
        "keyFeatures": ["string"] | null,
        "targetAudienceIcaId": "string (UUID) | null",
        "pricingTier": "premium|mid_market|entry_level|free|null",
        "pricingModel": "one_time|subscription|usage_based|freemium|custom|null",
        "differentiators": "string|null",
        "status": "active|in_development|planned|retired",
        "revenueContribution": "primary|secondary|emerging|null",
        "displayOrder": "number",
        "createdAt": "string (ISO 8601 datetime)",
        "updatedAt": "string (ISO 8601 datetime)"
      }
    ],
    "proposition": {
      "uniqueSellingProposition": "string",
      "keyDifferentiators": "string",
      "proofPoints": "string|null",
      "customerOutcomes": "string|null",
      "brandPromise": "string|null",
      "primaryCompetitors": ["string"] | null,
      "competitiveAdvantage": "string|null",
      "marketPosition": "leader|challenger|niche|emerging|null"
    },
    "model": {
      "types": ["b2b|b2c|b2b2c|marketplace|saas|consulting|ecommerce|other"],
      "primaryRevenueStream": "string",
      "secondaryRevenueStreams": ["string"] | null,
      "pricingStrategy": "string|null",
      "keyPartners": ["string"] | null,
      "distributionChannels": ["string"] | null,
      "customerAcquisition": "string|null"
    },
    "healthScore": "number (0-100)",
    "sectionStatuses": {
      "profile": "empty|incomplete|complete",
      "identity": "empty|incomplete|complete",
      "market": "empty|incomplete|complete",
      "products": "empty|incomplete|complete",
      "proposition": "empty|incomplete|complete",
      "model": "empty|incomplete|complete"
    },
    "createdAt": "string (ISO 8601 datetime)",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Error Responses:**

- 401 Unauthorized - Missing or invalid token
- 403 Forbidden - Invalid tenant ID
- 500 Internal Server Error

**Notes:**
- Returns complete foundation object even if some sections are empty
- `sectionStatuses` indicates which sections have data
- `healthScore` is calculated based on completeness of all sections

---

### 2. PUT /business/foundation

**Description:** Update complete business foundation (full replacement of entire object).

**HTTP Method:** PUT

**Headers:**
- Authorization: Bearer {token}
- X-Tenant-Id: {tenantId}
- Content-Type: application/json

**Request Body:** 

```json
{
  "profile": {
    "businessName": "string",
    "businessDescription": "string",
    "address": {
      "street": "string|null",
      "city": "string|null",
      "state": "string|null",
      "zip": "string|null",
      "country": "string"
    },
    "industry": "string",
    "subIndustry": "string|null",
    "companyStage": "startup|growth|scale|mature",
    "companySize": "solo|micro|small|medium|large|enterprise",
    "revenueRange": "...",
    "yearFounded": "number|null",
    "geographicFocus": ["local|regional|national|global"],
    "headquartersLocation": "string|null",
    "website": "string|null"
  },
  "identity": {...},
  "market": {...},
  "products": [...],
  "proposition": {...},
  "model": {...}
}
```

**Response:** 200 OK (same structure as GET response)

**Validation:**
- `businessName` - Required, max 255 characters
- `businessDescription` - Required, max 2000 characters
- `industry` - Required, must be from INDUSTRY_OPTIONS
- `companyStage` - Required, must be one of enum values
- `companySize` - Required, must be one of enum values
- `geographicFocus` - Required array, min 1 item

**Error Responses:**
- 400 Bad Request - Invalid data or validation failure
- 401 Unauthorized
- 403 Forbidden
- 422 Unprocessable Entity - Validation failed
- 500 Internal Server Error

---

## Section Update Endpoints (PATCH)

These endpoints update individual sections without affecting others. They may fall back to legacy endpoints if the specific PATCH endpoint returns 404.

### 3. PATCH /business/foundation/profile

**Description:** Update business profile section only (name, industry, stage, size, location).

**HTTP Method:** PATCH

**Request Body:**

```json
{
  "businessName": "string|null",
  "businessDescription": "string|null",
  "address": {
    "street": "string|null",
    "city": "string|null",
    "state": "string|null",
    "zip": "string|null",
    "country": "string|null"
  },
  "industry": "string|null",
  "subIndustry": "string|null",
  "companyStage": "startup|growth|scale|mature|null",
  "companySize": "solo|micro|small|medium|large|enterprise|null",
  "revenueRange": "...|null",
  "yearFounded": "number|null",
  "geographicFocus": ["..."]|null,
  "headquartersLocation": "string|null",
  "website": "string|null"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "profile": {...},
    "sectionStatuses": {
      "profile": "empty|incomplete|complete",
      "identity": "...",
      "market": "...",
      "products": "...",
      "proposition": "...",
      "model": "..."
    },
    "healthScore": "number (0-100)",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, falls back to legacy PUT /business/foundation with businessName field
- Returns mock success if legacy endpoint also fails

**Error Responses:**
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found (triggers fallback)
- 422 Unprocessable Entity

---

### 4. PATCH /business/foundation/identity

**Description:** Update core identity section (vision, purpose). Use dedicated value endpoints for values array.

**HTTP Method:** PATCH

**Request Body:**

```json
{
  "vision": "string|null",
  "visionTimeframe": "string|null",
  "purpose": "string|null",
  "whoWeServe": "string|null"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "identity": {
      "vision": "string",
      "visionTimeframe": "string|null",
      "purpose": "string",
      "whoWeServe": "string|null",
      "values": [...]
    },
    "sectionStatuses": {...},
    "healthScore": "number",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Validation:**
- `vision` - Optional, max 1000 characters
- `purpose` - Optional, max 1000 characters
- `visionTimeframe` - Optional, max 255 characters

**Fallback Behavior:**
- If endpoint returns 404, falls back to legacy PUT /business/foundation with vision and purpose fields

---

### 5. PATCH /business/foundation/market

**Description:** Update target market section (niche, market size, growth trend). Use dedicated ICA endpoints for icas array.

**HTTP Method:** PATCH

**Request Body:**

```json
{
  "nicheStatement": "string|null",
  "marketSize": "string|null",
  "growthTrend": "declining|stable|growing|rapidly_growing|null"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "market": {
      "nicheStatement": "string",
      "marketSize": "string|null",
      "growthTrend": "...",
      "icas": [...]
    },
    "sectionStatuses": {...},
    "healthScore": "number",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Validation:**
- `nicheStatement` - Optional, max 1000 characters
- `marketSize` - Optional, max 500 characters

**Fallback Behavior:**
- If endpoint returns 404, falls back to legacy PUT /business/foundation with targetMarket string

---

### 6. PATCH /business/foundation/proposition

**Description:** Update value proposition section (USP, differentiators, positioning).

**HTTP Method:** PATCH

**Request Body:**

```json
{
  "uniqueSellingProposition": "string|null",
  "keyDifferentiators": "string|null",
  "proofPoints": "string|null",
  "customerOutcomes": "string|null",
  "brandPromise": "string|null",
  "primaryCompetitors": ["string"]|null,
  "competitiveAdvantage": "string|null",
  "marketPosition": "leader|challenger|niche|emerging|null"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "proposition": {...},
    "sectionStatuses": {...},
    "healthScore": "number",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Validation:**
- `uniqueSellingProposition` - Optional, max 500 characters
- `keyDifferentiators` - Optional, max 500 characters
- `primaryCompetitors` - Optional array of strings

**Fallback Behavior:**
- If endpoint returns 404, falls back to legacy PUT /business/foundation with valueProposition field

---

### 7. PATCH /business/foundation/model

**Description:** Update business model section (types, revenue streams, pricing, partnerships).

**HTTP Method:** PATCH

**Request Body:**

```json
{
  "types": ["b2b|b2c|b2b2c|marketplace|saas|consulting|ecommerce|other"]|null,
  "primaryRevenueStream": "string|null",
  "secondaryRevenueStreams": ["string"]|null,
  "pricingStrategy": "string|null",
  "keyPartners": ["string"]|null,
  "distributionChannels": ["string"]|null,
  "customerAcquisition": "string|null"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "model": {...},
    "sectionStatuses": {...},
    "healthScore": "number",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock success (legacy endpoint doesn't support business model)

**Error Responses:** Same as other PATCH endpoints

---

## Products Endpoints

**Base Path:** `/business/foundation/products`

### 8. POST /business/foundation/products

**Description:** Create a new product or service.

**HTTP Method:** POST

**Request Body:**

```json
{
  "name": "string (required, max 255)",
  "tagline": "string|null (max 255)",
  "type": "product|service|subscription|hybrid (required)",
  "description": "string (required, max 2000)",
  "problemSolved": "string (required, max 1000)",
  "keyFeatures": ["string"]|null (max 10 items, each max 200 chars),
  "targetAudienceIcaId": "string (UUID)|null",
  "pricingTier": "premium|mid_market|entry_level|free|null",
  "pricingModel": "one_time|subscription|usage_based|freemium|custom|null",
  "differentiators": "string|null (max 500)",
  "status": "active|in_development|planned|retired (required)",
  "revenueContribution": "primary|secondary|emerging|null"
}
```

**Response:** 201 Created

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "name": "string",
    "tagline": "string|null",
    "type": "product|service|subscription|hybrid",
    "description": "string",
    "problemSolved": "string",
    "keyFeatures": ["string"]|null,
    "targetAudienceIcaId": "string|null",
    "pricingTier": "premium|mid_market|entry_level|free|null",
    "pricingModel": "one_time|subscription|usage_based|freemium|custom|null",
    "differentiators": "string|null",
    "status": "active|in_development|planned|retired",
    "revenueContribution": "primary|secondary|emerging|null",
    "displayOrder": "number",
    "createdAt": "string (ISO 8601 datetime)",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock response with generated temporary ID (format: `temp-{timestamp}`)
- Allows UI to function while backend endpoints are being implemented

**Error Responses:**
- 400 Bad Request - Missing required fields or validation failure
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)
- 422 Unprocessable Entity

---

### 9. PUT /business/foundation/products/{id}

**Description:** Update an existing product.

**HTTP Method:** PUT

**Path Parameters:**
- `id` - Product UUID (required)

**Request Body:** Same as POST (all fields optional except id in URL)

```json
{
  "name": "string|null",
  "tagline": "string|null",
  "type": "product|service|subscription|hybrid|null",
  "description": "string|null",
  "problemSolved": "string|null",
  "keyFeatures": ["string"]|null,
  "targetAudienceIcaId": "string|null",
  "pricingTier": "...|null",
  "pricingModel": "...|null",
  "differentiators": "string|null",
  "status": "active|in_development|planned|retired|null",
  "revenueContribution": "...|null"
}
```

**Response:** 200 OK (same structure as POST response)

**Fallback Behavior:**
- If endpoint returns 404, returns mock response

**Error Responses:**
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)
- 422 Unprocessable Entity

---

### 10. DELETE /business/foundation/products/{id}

**Description:** Delete a product.

**HTTP Method:** DELETE

**Path Parameters:**
- `id` - Product UUID (required)

**Request Body:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "deleted": true,
    "id": "string (UUID)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock success response

**Error Responses:**
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)

---

### 11. PUT /business/foundation/products:reorder

**Description:** Reorder products in display sequence.

**HTTP Method:** PUT

**Request Body:**

```json
{
  "orderedIds": ["string (UUID)", "string (UUID)", ...]
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "string (UUID)",
        "displayOrder": "number (0, 1, 2, ...)"
      }
    ]
  }
}
```

**Validation:**
- `orderedIds` - Required array, min 1 item
- All IDs must be valid UUIDs
- All IDs must correspond to existing products

**Fallback Behavior:**
- If endpoint returns 404, returns mock response with reordered items

**Error Responses:**
- 400 Bad Request - Invalid IDs or format
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)

---

## Core Values Endpoints

**Base Path:** `/business/foundation/values`

### 12. POST /business/foundation/values

**Description:** Create a new core value.

**HTTP Method:** POST

**Request Body:**

```json
{
  "name": "string (required, max 100)",
  "meaning": "string|null (optional, max 500)",
  "implementation": "string|null (optional, max 500)",
  "behaviors": ["string"]|null (optional, max 10 items, each max 500 chars),
  "displayOrder": "number|null (optional, auto-assigned if not specified)"
}
```

**Response:** 201 Created

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "tenantId": "string (UUID)",
    "businessFoundationId": "string (UUID)",
    "name": "string",
    "meaning": "string|null",
    "implementation": "string|null",
    "behaviors": ["string"],
    "displayOrder": "number",
    "isActive": "boolean",
    "createdAt": "string (ISO 8601 datetime)",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock response with generated temporary ID

**Error Responses:**
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)
- 422 Unprocessable Entity

---

### 13. PUT /business/foundation/values/{id}

**Description:** Update an existing core value.

**HTTP Method:** PUT

**Path Parameters:**
- `id` - Value UUID (required)

**Request Body:**

```json
{
  "name": "string|null (max 100 chars)",
  "meaning": "string|null (optional, max 500 chars)",
  "implementation": "string|null (optional, max 500 chars)",
  "behaviors": ["string"]|null (optional, max 10 items, each max 500 chars),
  "displayOrder": "number|null (optional)",
  "isActive": "boolean|null (optional)"
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "tenantId": "string (UUID)",
    "businessFoundationId": "string (UUID)",
    "name": "string",
    "meaning": "string|null",
    "implementation": "string|null",
    "behaviors": ["string"],
    "displayOrder": "number",
    "isActive": "boolean",
    "createdAt": "string (ISO 8601 datetime)",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock response

**Error Responses:**
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)
- 422 Unprocessable Entity

---

### 14. DELETE /business/foundation/values/{id}

**Description:** Delete a core value.

**HTTP Method:** DELETE

**Path Parameters:**
- `id` - Value UUID (required)

**Request Body:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "deleted": true
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock success response

**Error Responses:**
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)

---

### 15. PUT /business/foundation/values:reorder

**Description:** Reorder core values in display sequence.

**HTTP Method:** PUT

**Request Body:**

```json
{
  "coreValueIds": ["string (UUID)", "string (UUID)", ...]
}
```

**Response:** 200 OK

```json
{
  "success": true,
  "data": [
    {
      "id": "string (UUID)",
      "tenantId": "string (UUID)",
      "businessFoundationId": "string (UUID)",
      "name": "string",
      "meaning": "string|null",
      "implementation": "string|null",
      "behaviors": ["string"],
      "displayOrder": "number",
      "isActive": "boolean",
      "createdAt": "string (ISO 8601 datetime)",
      "updatedAt": "string (ISO 8601 datetime)"
    }
  ]
}
```

**Validation:**
- `coreValueIds` - Required array, min 1 item

**Fallback Behavior:**
- If endpoint returns 404, returns mock response

**Error Responses:**
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)

---

## Ideal Customer Avatar (ICA) Endpoints

**Base Path:** `/business/foundation/icas`

### 16. POST /business/foundation/icas

**Description:** Create a new ideal customer avatar.

**HTTP Method:** POST

**Request Body:**

```json
{
  "name": "string (required, max 100)",
  "demographics": "string (required, max 500)",
  "goals": "string (required, max 500)",
  "painPoints": "string (required, max 500)",
  "motivations": "string|null (max 500)",
  "objections": "string|null (max 500)",
  "whereToFind": "string|null (max 500)",
  "buyingProcess": "string|null (max 500)"
}
```

**Response:** 201 Created

```json
{
  "success": true,
  "data": {
    "id": "string (UUID)",
    "name": "string",
    "demographics": "string",
    "goals": "string",
    "painPoints": "string",
    "motivations": "string|null",
    "objections": "string|null",
    "whereToFind": "string|null",
    "buyingProcess": "string|null",
    "displayOrder": "number",
    "createdAt": "string (ISO 8601 datetime)",
    "updatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock response with generated temporary ID

**Error Responses:**
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)
- 422 Unprocessable Entity

---

### 17. PUT /business/foundation/icas/{id}

**Description:** Update an existing ideal customer avatar.

**HTTP Method:** PUT

**Path Parameters:**
- `id` - ICA UUID (required)

**Request Body:**

```json
{
  "name": "string|null",
  "demographics": "string|null",
  "goals": "string|null",
  "painPoints": "string|null",
  "motivations": "string|null",
  "objections": "string|null",
  "whereToFind": "string|null",
  "buyingProcess": "string|null"
}
```

**Response:** 200 OK (same structure as POST response)

**Fallback Behavior:**
- If endpoint returns 404, returns mock response

**Error Responses:**
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)
- 422 Unprocessable Entity

---

### 18. DELETE /business/foundation/icas/{id}

**Description:** Delete an ideal customer avatar.

**HTTP Method:** DELETE

**Path Parameters:**
- `id` - ICA UUID (required)

**Request Body:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "deleted": true,
    "id": "string (UUID)"
  }
}
```

**Fallback Behavior:**
- If endpoint returns 404, returns mock success response

**Error Responses:**
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found (triggers fallback)

---

## Health & Wizard Endpoints

### 19. GET /business/foundation/health

**Description:** Get foundation health check status.

**HTTP Method:** GET

**Request Parameters:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "healthScore": "number (0-100)",
    "sectionStatuses": {
      "profile": "empty|incomplete|complete",
      "identity": "empty|incomplete|complete",
      "market": "empty|incomplete|complete",
      "products": "empty|incomplete|complete",
      "proposition": "empty|incomplete|complete",
      "model": "empty|incomplete|complete"
    },
    "strengths": ["string"],
    "opportunities": [
      {
        "section": "profile|identity|market|products|proposition|model",
        "issue": "string (description of issue)",
        "impact": "string (impact of issue)",
        "estimatedTime": "string (estimated time to fix)"
      }
    ],
    "recommendations": [
      {
        "priority": "number (1=highest)",
        "action": "string (recommended action)",
        "section": "profile|identity|market|products|proposition|model"
      }
    ],
    "lastUpdated": "string (ISO 8601 datetime)"
  }
}
```

**Error Responses:**
- 401 Unauthorized
- 403 Forbidden
- 500 Internal Server Error

---

### 20. GET /business/foundation/wizard-progress

**Description:** Get multi-step wizard completion progress.

**HTTP Method:** GET

**Request Parameters:** None

**Response:** 200 OK

```json
{
  "success": true,
  "data": {
    "currentStep": "number (1-6)",
    "completedSteps": [1, 2, 3],
    "skippedSteps": [],
    "isComplete": "boolean",
    "lastUpdatedAt": "string (ISO 8601 datetime)"
  }
}
```

**Notes:**
- `currentStep` - Where user is currently (1=profile, 2=identity, 3=products, 4=market, 5=proposition, 6=review)
- `completedSteps` - Array of step numbers user has completed
- `skippedSteps` - Array of step numbers user has skipped
- `isComplete` - True if all 6 steps completed

**Error Responses:**
- 401 Unauthorized
- 403 Forbidden
- 500 Internal Server Error

---

### 21. PUT /business/foundation/wizard-progress

**Description:** Update wizard progress (mark steps complete, move to next step).

**HTTP Method:** PUT

**Request Body:**

```json
{
  "currentStep": "number (1-6)",
  "completedSteps": [1, 2, 3],
  "skippedSteps": [],
  "isComplete": "boolean"
}
```

**Response:** 200 OK (same structure as GET response)

**Validation:**
- `currentStep` - Required, must be 1-6
- `completedSteps` - Required array of integers 1-6
- `skippedSteps` - Required array of integers 1-6
- `isComplete` - Required boolean

**Frontend Handling:**
- Call this endpoint after user completes each wizard step
- Update `currentStep` to next step number
- Add current step to `completedSteps` array
- Set `isComplete = true` when all steps completed

**Error Responses:**
- 400 Bad Request - Invalid step numbers
- 401 Unauthorized
- 403 Forbidden
- 422 Unprocessable Entity

---

## Error Handling

All error responses follow this format:

```json
{
  "success": false,
  "error": "string (error message)"
}
```

**Common HTTP Status Codes:**
- 400 - Bad Request (validation failed, malformed JSON)
- 401 - Unauthorized (missing/invalid token)
- 403 - Forbidden (invalid tenant, insufficient permissions)
- 404 - Not Found (endpoint not yet implemented, triggers fallback)
- 422 - Unprocessable Entity (semantic validation failed)
- 500 - Internal Server Error

**Client Handling:**
- Always check `success` field in response
- On 404, frontend uses mock fallback response
- On 401, refresh token or redirect to login
- On 4xx client errors, display user-friendly error message
- On 500, retry with exponential backoff or display error

---

## Implementation Notes

### Fallback Pattern
When backend endpoints return 404, the frontend returns mock responses:
- Generated IDs use format: `temp-{timestamp}`
- Mock responses allow UI to function independently
- Data is not persisted to backend, but is available locally
- Once backend endpoint is available, real responses are used

### Field Naming
- All field names use **camelCase** (not snake_case)
- Dates are ISO 8601 format with timezone
- UUIDs are standard UUID v4 format strings
- Arrays indicated by square brackets `[]`

### Data Validation
- Max length constraints enforced by backend
- Required fields validated before operation
- Enum values must match exactly
- Nested objects fully validated recursively

### Rate Limiting
Not specified in this version. Implement per-service requirements.

### Caching
Clients may cache GET responses but should respect `updatedAt` timestamps and refresh when needed.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | December 30, 2025 | Initial specification verified against complete implementation. All 21 endpoints documented with full request/response payloads, validation rules, and fallback behavior. Includes 4 fallback patterns (PATCH endpoints, products, values, ICAs). |

