# Business Foundation API Requirements

**Version:** 1.0  
**Last Updated:** December 2024  
**Service:** Account Service (existing) or Traction Service (TBD)  
**Status:** Draft for Backend Review

---

## Overview

This document specifies the API endpoints required to support the enhanced Business Foundation feature. It follows the same patterns established in the existing backend integration specifications.

**Conventions:**
- All dates are ISO 8601 format strings
- All endpoints require `Authorization: Bearer {token}` header
- All endpoints require `X-Tenant-Id` header for multi-tenancy
- Request/Response bodies use camelCase field names
- Standard error responses follow existing patterns

---

## Endpoint Summary

| # | Method | Endpoint | Status | Description |
|---|--------|----------|--------|-------------|
| 1 | GET | `/business/foundation` | **EXISTS** - needs revision | Get complete business foundation |
| 2 | PUT | `/business/foundation` | **REVISED** (was PATCH) | Full update of business foundation |
| 3 | PATCH | `/business/foundation/profile` | **NEW** | Update business profile section only |
| 4 | PATCH | `/business/foundation/identity` | **NEW** | Update core identity section only |
| 5 | PATCH | `/business/foundation/market` | **NEW** | Update target market section only |
| 6 | PATCH | `/business/foundation/proposition` | **NEW** | Update value proposition section only |
| 7 | PATCH | `/business/foundation/model` | **NEW** | Update business model section only |
| 8 | POST | `/business/foundation/products` | **NEW** | Create product |
| 9 | PUT | `/business/foundation/products/{id}` | **NEW** | Update product |
| 10 | DELETE | `/business/foundation/products/{id}` | **NEW** | Delete product |
| 11 | PUT | `/business/foundation/products:reorder` | **NEW** | Reorder products |
| 12 | POST | `/business/foundation/values` | **NEW** | Create core value |
| 13 | PUT | `/business/foundation/values/{id}` | **NEW** | Update core value |
| 14 | DELETE | `/business/foundation/values/{id}` | **NEW** | Delete core value |
| 15 | PUT | `/business/foundation/values:reorder` | **NEW** | Reorder values |
| 16 | POST | `/business/foundation/icas` | **NEW** | Create ICA |
| 17 | PUT | `/business/foundation/icas/{id}` | **NEW** | Update ICA |
| 18 | DELETE | `/business/foundation/icas/{id}` | **NEW** | Delete ICA |
| 19 | GET | `/business/foundation/health` | **NEW** | Get foundation health check |
| 20 | GET | `/business/foundation/wizard-progress` | **NEW** | Get wizard progress state |
| 21 | PUT | `/business/foundation/wizard-progress` | **NEW** | Update wizard progress state |

**Total: 21 endpoints (2 existing with revisions, 19 new)**

---

## Type Definitions

### Enums

```typescript
// Company stage
type CompanyStage = 'startup' | 'growth' | 'scale' | 'mature';

// Company size (employee count)
type CompanySize = 'solo' | 'micro' | 'small' | 'medium' | 'large' | 'enterprise';
// solo: 1, micro: 2-10, small: 11-50, medium: 51-200, large: 201-1000, enterprise: 1000+

// Revenue range
type RevenueRange = 
  | 'pre_revenue' 
  | 'under_100k' 
  | '100k_500k' 
  | '500k_1m' 
  | '1m_5m' 
  | '5m_10m' 
  | '10m_50m' 
  | 'over_50m' 
  | 'not_disclosed';

// Geographic focus
type GeographicFocus = 'local' | 'regional' | 'national' | 'global';

// Product/Service type
type ProductType = 'product' | 'service' | 'subscription' | 'hybrid';

// Product status
type ProductStatus = 'active' | 'in_development' | 'planned' | 'retired';

// Pricing tier
type PricingTier = 'premium' | 'mid_market' | 'entry_level' | 'free';

// Pricing model
type PricingModel = 'one_time' | 'subscription' | 'usage_based' | 'freemium' | 'custom';

// Revenue contribution
type RevenueContribution = 'primary' | 'secondary' | 'emerging';

// Business model type
type BusinessModelType = 'b2b' | 'b2c' | 'b2b2c' | 'marketplace' | 'saas' | 'consulting' | 'ecommerce' | 'other';

// Market position
type MarketPosition = 'leader' | 'challenger' | 'niche' | 'emerging';

// Market growth trend
type GrowthTrend = 'declining' | 'stable' | 'growing' | 'rapidly_growing';

// Section completion status
type SectionStatus = 'empty' | 'incomplete' | 'complete';
```

### Core Types

```typescript
// Business Address
interface BusinessAddress {
  street?: string;
  city?: string;
  state?: string;
  zip?: string;
  country: string;
}

// Business Profile
interface BusinessProfile {
  businessName: string;
  businessDescription: string;
  address?: BusinessAddress;
  industry: string;
  subIndustry?: string;
  companyStage: CompanyStage;
  companySize: CompanySize;
  revenueRange?: RevenueRange;
  yearFounded?: number;
  geographicFocus: GeographicFocus[];
  headquartersLocation?: string;
  website?: string;
}

// Core Value (enhanced)
interface CoreValue {
  id: string;
  name: string;
  meaning: string;
  implementation: string;
  behaviors?: string[];
  displayOrder: number;
  createdAt: string;
  updatedAt: string;
}

// Core Identity
interface CoreIdentity {
  vision: string;
  visionTimeframe?: string; // e.g., "5 years"
  purpose: string;
  whoWeServe?: string;
  values: CoreValue[];
}

// Ideal Customer Avatar
interface IdealCustomerAvatar {
  id: string;
  name: string;
  demographics: string;
  goals: string;
  painPoints: string;
  motivations?: string;
  objections?: string;
  whereToFind?: string;
  buyingProcess?: string;
  displayOrder: number;
  createdAt: string;
  updatedAt: string;
}

// Target Market
interface TargetMarket {
  nicheStatement: string;
  marketSize?: string;
  growthTrend?: GrowthTrend;
  icas: IdealCustomerAvatar[];
}

// Product/Service (enhanced)
interface Product {
  id: string;
  name: string;
  tagline?: string;
  type: ProductType;
  description: string;
  problemSolved: string;
  keyFeatures?: string[];
  targetAudienceIcaId?: string; // Links to ICA
  pricingTier?: PricingTier;
  pricingModel?: PricingModel;
  differentiators?: string;
  status: ProductStatus;
  revenueContribution?: RevenueContribution;
  displayOrder: number;
  createdAt: string;
  updatedAt: string;
}

// Value Proposition
interface ValueProposition {
  uniqueSellingProposition: string;
  keyDifferentiators: string;
  proofPoints?: string;
  customerOutcomes?: string;
  brandPromise?: string;
  primaryCompetitors?: string[];
  competitiveAdvantage?: string;
  marketPosition?: MarketPosition;
}

// Business Model
interface BusinessModel {
  types: BusinessModelType[];
  primaryRevenueStream: string;
  secondaryRevenueStreams?: string[];
  pricingStrategy?: string;
  keyPartners?: string[];
  distributionChannels?: string[];
  customerAcquisition?: string;
}

// Complete Business Foundation
interface BusinessFoundation {
  id: string;
  tenantId: string;
  
  // Sections
  profile: BusinessProfile;
  identity: CoreIdentity;
  market: TargetMarket;
  products: Product[];
  proposition: ValueProposition;
  model?: BusinessModel;
  
  // Metadata
  healthScore: number; // 0-100
  sectionStatuses: {
    profile: SectionStatus;
    identity: SectionStatus;
    market: SectionStatus;
    products: SectionStatus;
    proposition: SectionStatus;
    model: SectionStatus;
  };
  
  createdAt: string;
  updatedAt: string;
}

// Wizard Progress State
interface WizardProgress {
  currentStep: number; // 1-6
  completedSteps: number[];
  skippedSteps: number[];
  isComplete: boolean;
  lastUpdatedAt: string;
}
```

---

## Endpoint Details

### 1. Get Business Foundation

**Status:** EXISTS - needs revision to support new data model

**Endpoint:** `GET /business/foundation`

**Current Response:**
```json
{
  "success": true,
  "data": {
    "businessName": "Acme Corp",
    "vision": "To be the leading...",
    "purpose": "We empower businesses...",
    "coreValues": ["Innovation", "Integrity"],
    "targetMarket": "Mid-market B2B",
    "valueProposition": "We offer..."
  }
}
```

**New Response:**
```json
{
  "success": true,
  "data": {
    "id": "bf_123",
    "tenantId": "tenant_456",
    
    "profile": {
      "businessName": "Acme Corp",
      "businessDescription": "We build enterprise software that simplifies complex business processes.",
      "address": {
        "street": "123 Main Street",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94105",
        "country": "United States"
      },
      "industry": "Technology",
      "subIndustry": "SaaS",
      "companyStage": "growth",
      "companySize": "small",
      "revenueRange": "1m_5m",
      "yearFounded": 2018,
      "geographicFocus": ["national"],
      "headquartersLocation": "San Francisco, CA",
      "website": "https://acmecorp.com"
    },
    
    "identity": {
      "vision": "To be the leading platform for strategic business planning.",
      "visionTimeframe": "5 years",
      "purpose": "We empower businesses to achieve their full potential through clarity and focus.",
      "whoWeServe": "Growing businesses seeking strategic clarity",
      "values": [
        {
          "id": "val_001",
          "name": "Innovation",
          "meaning": "We challenge conventional thinking and embrace creative solutions.",
          "implementation": "We dedicate 20% of team time to experimentation.",
          "behaviors": ["Question assumptions", "Prototype before perfecting"],
          "displayOrder": 1,
          "createdAt": "2024-01-15T10:00:00Z",
          "updatedAt": "2024-06-20T14:30:00Z"
        },
        {
          "id": "val_002",
          "name": "Integrity",
          "meaning": "We do the right thing, even when no one is watching.",
          "implementation": "Transparent decision-making and open communication.",
          "behaviors": ["Speak truth to power", "Admit mistakes quickly"],
          "displayOrder": 2,
          "createdAt": "2024-01-15T10:00:00Z",
          "updatedAt": "2024-01-15T10:00:00Z"
        }
      ]
    },
    
    "market": {
      "nicheStatement": "Mid-market B2B SaaS companies seeking strategic planning tools.",
      "marketSize": "$2.5B TAM",
      "growthTrend": "growing",
      "icas": [
        {
          "id": "ica_001",
          "name": "Marketing Mary",
          "demographics": "35-50 years old, Marketing Director or VP at mid-market tech companies.",
          "goals": "Scale marketing operations while proving ROI to leadership.",
          "painPoints": "Too many tools, lack of integration, difficulty measuring effectiveness.",
          "motivations": "Career advancement, team recognition, strategic impact.",
          "objections": "Budget constraints, change management concerns.",
          "whereToFind": "LinkedIn, marketing conferences, industry webinars.",
          "buyingProcess": "Research online, request demo, get CFO approval.",
          "displayOrder": 1,
          "createdAt": "2024-02-01T09:00:00Z",
          "updatedAt": "2024-05-15T11:00:00Z"
        }
      ]
    },
    
    "products": [
      {
        "id": "prod_001",
        "name": "PurposePath Pro",
        "tagline": "Strategic planning for growing businesses",
        "type": "subscription",
        "description": "AI-powered strategic planning platform with goal setting, Measure tracking, and team alignment tools.",
        "problemSolved": "Businesses struggle to translate vision into actionable plans.",
        "keyFeatures": ["Goal wizard", "Measure tracking", "AI recommendations", "Team alignment"],
        "targetAudienceIcaId": "ica_001",
        "pricingTier": "premium",
        "pricingModel": "subscription",
        "differentiators": "AI-powered insights combined with proven frameworks.",
        "status": "active",
        "revenueContribution": "primary",
        "displayOrder": 1,
        "createdAt": "2024-01-20T10:00:00Z",
        "updatedAt": "2024-07-01T09:00:00Z"
      }
    ],
    
    "proposition": {
      "uniqueSellingProposition": "The only strategic planning platform that combines AI insights with proven frameworks.",
      "keyDifferentiators": "AI-powered recommendations, integrated coaching, built for growing businesses.",
      "proofPoints": "500+ businesses, 78% goal completion rate.",
      "customerOutcomes": "3x faster goal completion, 92% report better clarity.",
      "brandPromise": "Clarity on your path forward.",
      "primaryCompetitors": ["Monday.com", "Notion", "Spreadsheets"],
      "competitiveAdvantage": "Purpose-built for strategic planning with AI guidance.",
      "marketPosition": "challenger"
    },
    
    "model": {
      "types": ["b2b", "saas"],
      "primaryRevenueStream": "Monthly and annual subscriptions",
      "secondaryRevenueStreams": ["Implementation services", "Training"],
      "pricingStrategy": "Value-based with three tiers",
      "keyPartners": ["Strategic coaching networks", "Business accelerators"],
      "distributionChannels": ["Direct website", "Partner referrals"],
      "customerAcquisition": "Content marketing, referrals, partnerships"
    },
    
    "healthScore": 85,
    "sectionStatuses": {
      "profile": "complete",
      "identity": "incomplete",
      "market": "complete",
      "products": "incomplete",
      "proposition": "complete",
      "model": "complete"
    },
    
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Migration Notes:**
- Existing `coreValues: string[]` migrates to `identity.values[]` with name only, empty meaning/implementation
- Existing `targetMarket: string` migrates to `market.nicheStatement`
- Existing `valueProposition: string` migrates to `proposition.uniqueSellingProposition`
- Existing products (name, problem) migrate with empty description, flagged as incomplete

---

### 2. Update Business Foundation (Full)

**Status:** REVISED (was PATCH, now PUT for full replacement)

**Endpoint:** `PUT /business/foundation`

**Request:**
```json
{
  "profile": {
    "businessName": "Acme Corp",
    "businessDescription": "Enterprise software company...",
    "address": {
      "street": "123 Main Street",
      "city": "San Francisco",
      "state": "CA",
      "zip": "94105",
      "country": "United States"
    },
    "industry": "Technology",
    "subIndustry": "SaaS",
    "companyStage": "growth",
    "companySize": "small",
    "revenueRange": "1m_5m",
    "yearFounded": 2018,
    "geographicFocus": ["national"],
    "headquartersLocation": "San Francisco, CA",
    "website": "https://acmecorp.com"
  },
  "identity": {
    "vision": "To be the leading platform...",
    "visionTimeframe": "5 years",
    "purpose": "We empower businesses...",
    "whoWeServe": "Growing businesses"
  },
  "market": {
    "nicheStatement": "Mid-market B2B SaaS...",
    "marketSize": "$2.5B TAM",
    "growthTrend": "growing"
  },
  "proposition": {
    "uniqueSellingProposition": "The only platform...",
    "keyDifferentiators": "AI-powered...",
    "proofPoints": "500+ businesses...",
    "customerOutcomes": "3x faster...",
    "brandPromise": "Clarity on your path forward.",
    "primaryCompetitors": ["Monday.com", "Notion"],
    "competitiveAdvantage": "Purpose-built...",
    "marketPosition": "challenger"
  },
  "model": {
    "types": ["b2b", "saas"],
    "primaryRevenueStream": "Subscriptions",
    "secondaryRevenueStreams": ["Services"],
    "pricingStrategy": "Value-based",
    "keyPartners": ["Coaching networks"],
    "distributionChannels": ["Direct", "Partners"],
    "customerAcquisition": "Content marketing"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    // Full BusinessFoundation object (same as GET response)
  }
}
```

**Notes:**
- Does NOT update nested arrays (products, values, icas) - use dedicated endpoints
- Recalculates `healthScore` and `sectionStatuses` after update

---

### 3. Update Business Profile Section

**Status:** NEW

**Endpoint:** `PATCH /business/foundation/profile`

**Request:**
```json
{
  "businessName": "Acme Corp",
  "businessDescription": "Enterprise software company...",
  "address": {
    "street": "123 Main Street",
    "city": "San Francisco",
    "state": "CA",
    "zip": "94105",
    "country": "United States"
  },
  "industry": "Technology",
  "subIndustry": "SaaS",
  "companyStage": "growth",
  "companySize": "small",
  "revenueRange": "1m_5m",
  "yearFounded": 2018,
  "geographicFocus": ["national", "regional"],
  "headquartersLocation": "San Francisco, CA",
  "website": "https://acmecorp.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "profile": {
      // Updated BusinessProfile object
    },
    "sectionStatuses": {
      "profile": "complete",
      // ... other statuses
    },
    "healthScore": 87,
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `businessName`: required, max 200 characters
- `businessDescription`: required, max 2000 characters
- `address`: optional, nested object
  - `address.country`: required if address provided
- `industry`: required, max 100 characters
- `companyStage`: required, must be valid enum
- `companySize`: required, must be valid enum
- `geographicFocus`: required, min 1 item
- `website`: optional, must be valid URL format

---

### 4. Update Core Identity Section

**Status:** NEW

**Endpoint:** `PATCH /business/foundation/identity`

**Request:**
```json
{
  "vision": "To be the leading platform for strategic business planning.",
  "visionTimeframe": "5 years",
  "purpose": "We empower businesses to achieve their full potential.",
  "whoWeServe": "Growing businesses seeking strategic clarity"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "identity": {
      "vision": "To be the leading platform...",
      "visionTimeframe": "5 years",
      "purpose": "We empower businesses...",
      "whoWeServe": "Growing businesses...",
      "values": [
        // Existing values array (not modified by this endpoint)
      ]
    },
    "sectionStatuses": {
      "identity": "complete",
      // ...
    },
    "healthScore": 88,
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `vision`: required, max 2000 characters
- `purpose`: required, max 2000 characters

**Notes:**
- Does NOT modify `values` array - use dedicated value endpoints

---

### 5. Update Target Market Section

**Status:** NEW

**Endpoint:** `PATCH /business/foundation/market`

**Request:**
```json
{
  "nicheStatement": "Mid-market B2B SaaS companies seeking strategic planning tools.",
  "marketSize": "$2.5B TAM",
  "growthTrend": "growing"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "market": {
      "nicheStatement": "Mid-market B2B SaaS...",
      "marketSize": "$2.5B TAM",
      "growthTrend": "growing",
      "icas": [
        // Existing ICAs array (not modified by this endpoint)
      ]
    },
    "sectionStatuses": {
      "market": "complete",
      // ...
    },
    "healthScore": 89,
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `nicheStatement`: required, max 2000 characters

**Notes:**
- Does NOT modify `icas` array - use dedicated ICA endpoints

---

### 6. Update Value Proposition Section

**Status:** NEW

**Endpoint:** `PATCH /business/foundation/proposition`

**Request:**
```json
{
  "uniqueSellingProposition": "The only strategic planning platform...",
  "keyDifferentiators": "AI-powered recommendations, integrated coaching.",
  "proofPoints": "500+ businesses have achieved their goals.",
  "customerOutcomes": "3x faster goal completion.",
  "brandPromise": "Clarity on your path forward.",
  "primaryCompetitors": ["Monday.com", "Notion", "Spreadsheets"],
  "competitiveAdvantage": "Purpose-built for strategic planning.",
  "marketPosition": "challenger"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "proposition": {
      // Updated ValueProposition object
    },
    "sectionStatuses": {
      "proposition": "complete",
      // ...
    },
    "healthScore": 90,
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `uniqueSellingProposition`: required, max 2000 characters
- `keyDifferentiators`: required, max 2000 characters

---

### 7. Update Business Model Section

**Status:** NEW

**Endpoint:** `PATCH /business/foundation/model`

**Request:**
```json
{
  "types": ["b2b", "saas"],
  "primaryRevenueStream": "Monthly and annual subscriptions",
  "secondaryRevenueStreams": ["Implementation services", "Training"],
  "pricingStrategy": "Value-based pricing with three tiers",
  "keyPartners": ["Strategic coaching networks", "Business accelerators"],
  "distributionChannels": ["Direct website", "Partner referrals"],
  "customerAcquisition": "Content marketing, referrals, partnerships"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "model": {
      // Updated BusinessModel object
    },
    "sectionStatuses": {
      "model": "complete",
      // ...
    },
    "healthScore": 92,
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `types`: required, min 1 item, valid enum values
- `primaryRevenueStream`: required, max 500 characters

---

### 8. Create Product

**Status:** NEW

**Endpoint:** `POST /business/foundation/products`

**Request:**
```json
{
  "name": "PurposePath Pro",
  "tagline": "Strategic planning for growing businesses",
  "type": "subscription",
  "description": "AI-powered strategic planning platform with goal setting, Measure tracking.",
  "problemSolved": "Businesses struggle to translate vision into actionable plans.",
  "keyFeatures": ["Goal wizard", "Measure tracking", "AI recommendations"],
  "targetAudienceIcaId": "ica_001",
  "pricingTier": "premium",
  "pricingModel": "subscription",
  "differentiators": "AI-powered insights combined with proven frameworks.",
  "status": "active",
  "revenueContribution": "primary"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "prod_002",
    "name": "PurposePath Pro",
    "tagline": "Strategic planning for growing businesses",
    "type": "subscription",
    "description": "AI-powered strategic planning platform...",
    "problemSolved": "Businesses struggle to translate...",
    "keyFeatures": ["Goal wizard", "Measure tracking", "AI recommendations"],
    "targetAudienceIcaId": "ica_001",
    "pricingTier": "premium",
    "pricingModel": "subscription",
    "differentiators": "AI-powered insights...",
    "status": "active",
    "revenueContribution": "primary",
    "displayOrder": 2,
    "createdAt": "2024-12-20T15:30:00Z",
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `name`: required, max 200 characters, unique within tenant
- `type`: required, valid enum
- `description`: required, max 2000 characters
- `problemSolved`: required, max 2000 characters
- `status`: required, valid enum

---

### 9. Update Product

**Status:** NEW

**Endpoint:** `PUT /business/foundation/products/{id}`

**Path Parameters:**
- `id`: Product ID (e.g., `prod_001`)

**Request:**
```json
{
  "name": "PurposePath Pro",
  "tagline": "Strategic planning platform",
  "type": "subscription",
  "description": "Updated description...",
  "problemSolved": "Updated problem statement...",
  "keyFeatures": ["Feature 1", "Feature 2"],
  "targetAudienceIcaId": "ica_001",
  "pricingTier": "premium",
  "pricingModel": "subscription",
  "differentiators": "Updated differentiators...",
  "status": "active",
  "revenueContribution": "primary"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "prod_001",
    // Full Product object with updates
    "updatedAt": "2024-12-20T16:00:00Z"
  }
}
```

---

### 10. Delete Product

**Status:** NEW

**Endpoint:** `DELETE /business/foundation/products/{id}`

**Path Parameters:**
- `id`: Product ID (e.g., `prod_001`)

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "id": "prod_001"
  }
}
```

**Business Rules:**
- Must have at least 1 product - cannot delete if only 1 remains

---

### 11. Reorder Products

**Status:** NEW

**Endpoint:** `PUT /business/foundation/products:reorder`

**Request:**
```json
{
  "orderedIds": ["prod_003", "prod_001", "prod_002"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "products": [
      { "id": "prod_003", "displayOrder": 1 },
      { "id": "prod_001", "displayOrder": 2 },
      { "id": "prod_002", "displayOrder": 3 }
    ]
  }
}
```

---

### 12. Create Core Value

**Status:** NEW

**Endpoint:** `POST /business/foundation/values`

**Request:**
```json
{
  "name": "Innovation",
  "meaning": "We challenge conventional thinking and embrace creative solutions.",
  "implementation": "We dedicate 20% of team time to experimentation.",
  "behaviors": ["Question assumptions", "Prototype before perfecting", "Celebrate learning"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "val_003",
    "name": "Innovation",
    "meaning": "We challenge conventional thinking...",
    "implementation": "We dedicate 20% of team time...",
    "behaviors": ["Question assumptions", "Prototype before perfecting", "Celebrate learning"],
    "displayOrder": 3,
    "createdAt": "2024-12-20T15:30:00Z",
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `name`: required, max 100 characters, unique within tenant
- `meaning`: required, max 1000 characters
- `implementation`: required, max 1000 characters
- `behaviors`: optional, max 10 items, each max 200 characters
- Maximum 7 values per tenant

---

### 13. Update Core Value

**Status:** NEW

**Endpoint:** `PUT /business/foundation/values/{id}`

**Path Parameters:**
- `id`: Value ID (e.g., `val_001`)

**Request:**
```json
{
  "name": "Innovation",
  "meaning": "Updated meaning...",
  "implementation": "Updated implementation...",
  "behaviors": ["Updated behavior 1", "Updated behavior 2"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "val_001",
    // Full CoreValue object with updates
    "updatedAt": "2024-12-20T16:00:00Z"
  }
}
```

---

### 14. Delete Core Value

**Status:** NEW

**Endpoint:** `DELETE /business/foundation/values/{id}`

**Path Parameters:**
- `id`: Value ID (e.g., `val_001`)

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "id": "val_001"
  }
}
```

**Business Rules:**
- Must have at least 3 values - cannot delete if only 3 remain

---

### 15. Reorder Values

**Status:** NEW

**Endpoint:** `PUT /business/foundation/values:reorder`

**Request:**
```json
{
  "orderedIds": ["val_003", "val_001", "val_002"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "values": [
      { "id": "val_003", "displayOrder": 1 },
      { "id": "val_001", "displayOrder": 2 },
      { "id": "val_002", "displayOrder": 3 }
    ]
  }
}
```

---

### 16. Create ICA

**Status:** NEW

**Endpoint:** `POST /business/foundation/icas`

**Request:**
```json
{
  "name": "Marketing Mary",
  "demographics": "35-50 years old, Marketing Director or VP at mid-market tech companies.",
  "goals": "Scale marketing operations while proving ROI to leadership.",
  "painPoints": "Too many tools, lack of integration, difficulty measuring effectiveness.",
  "motivations": "Career advancement, team recognition, strategic impact.",
  "objections": "Budget constraints, change management concerns.",
  "whereToFind": "LinkedIn, marketing conferences, industry webinars.",
  "buyingProcess": "Research online, request demo, get CFO approval."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "ica_002",
    "name": "Marketing Mary",
    "demographics": "35-50 years old...",
    "goals": "Scale marketing operations...",
    "painPoints": "Too many tools...",
    "motivations": "Career advancement...",
    "objections": "Budget constraints...",
    "whereToFind": "LinkedIn, marketing conferences...",
    "buyingProcess": "Research online...",
    "displayOrder": 2,
    "createdAt": "2024-12-20T15:30:00Z",
    "updatedAt": "2024-12-20T15:30:00Z"
  }
}
```

**Validation:**
- `name`: required, max 100 characters
- `demographics`: required, max 1000 characters
- `goals`: required, max 1000 characters
- `painPoints`: required, max 1000 characters
- Maximum 3 ICAs per tenant

---

### 17. Update ICA

**Status:** NEW

**Endpoint:** `PUT /business/foundation/icas/{id}`

**Path Parameters:**
- `id`: ICA ID (e.g., `ica_001`)

**Request:**
```json
{
  "name": "Marketing Mary",
  "demographics": "Updated demographics...",
  "goals": "Updated goals...",
  "painPoints": "Updated pain points...",
  "motivations": "Updated motivations...",
  "objections": "Updated objections...",
  "whereToFind": "Updated channels...",
  "buyingProcess": "Updated process..."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "ica_001",
    // Full ICA object with updates
    "updatedAt": "2024-12-20T16:00:00Z"
  }
}
```

---

### 18. Delete ICA

**Status:** NEW

**Endpoint:** `DELETE /business/foundation/icas/{id}`

**Path Parameters:**
- `id`: ICA ID (e.g., `ica_001`)

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted": true,
    "id": "ica_001"
  }
}
```

**Business Rules:**
- Products referencing this ICA will have `targetAudienceIcaId` set to null

---

### 19. Get Foundation Health

**Status:** NEW

**Endpoint:** `GET /business/foundation/health`

**Response:**
```json
{
  "success": true,
  "data": {
    "healthScore": 78,
    "sectionStatuses": {
      "profile": "complete",
      "identity": "incomplete",
      "market": "complete",
      "products": "incomplete",
      "proposition": "complete",
      "model": "empty"
    },
    "strengths": [
      "Clear and compelling vision statement",
      "Well-defined target market with detailed ICA",
      "Products have clear problem statements"
    ],
    "opportunities": [
      {
        "section": "products",
        "issue": "2 products missing descriptions",
        "impact": "Reduces AI recommendation accuracy",
        "estimatedTime": "15 minutes"
      },
      {
        "section": "identity",
        "issue": "Values lack implementation details",
        "impact": "Harder to apply values in daily decisions",
        "estimatedTime": "20 minutes"
      },
      {
        "section": "model",
        "issue": "Business model section not started",
        "impact": "Limits AI understanding of strategic priorities",
        "estimatedTime": "10 minutes"
      }
    ],
    "recommendations": [
      {
        "priority": 1,
        "action": "Complete product descriptions",
        "section": "products"
      },
      {
        "priority": 2,
        "action": "Add implementation to each value",
        "section": "identity"
      },
      {
        "priority": 3,
        "action": "Define basic business model",
        "section": "model"
      }
    ],
    "lastUpdated": "2024-12-20T15:30:00Z"
  }
}
```

---

### 20. Get Wizard Progress

**Status:** NEW

**Endpoint:** `GET /business/foundation/wizard-progress`

**Response:**
```json
{
  "success": true,
  "data": {
    "currentStep": 3,
    "completedSteps": [1, 2],
    "skippedSteps": [],
    "isComplete": false,
    "lastUpdatedAt": "2024-12-20T14:00:00Z"
  }
}
```

---

### 21. Update Wizard Progress

**Status:** NEW

**Endpoint:** `PUT /business/foundation/wizard-progress`

**Request:**
```json
{
  "currentStep": 4,
  "completedSteps": [1, 2, 3],
  "skippedSteps": [],
  "isComplete": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "currentStep": 4,
    "completedSteps": [1, 2, 3],
    "skippedSteps": [],
    "isComplete": false,
    "lastUpdatedAt": "2024-12-20T15:30:00Z"
  }
}
```

---

## Error Responses

All endpoints follow the standard error response format:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      {
        "field": "name",
        "message": "Name is required"
      }
    ]
  }
}
```

**Error Codes:**
- `VALIDATION_ERROR` (400) - Request validation failed
- `NOT_FOUND` (404) - Resource not found
- `CONFLICT` (409) - Duplicate resource or constraint violation
- `BUSINESS_RULE_VIOLATION` (400) - Operation violates business rules

---

## Migration Considerations

### Data Migration for Existing Users

When the new endpoints are deployed, existing user data should be migrated:

1. **Business Profile**: 
   - `businessName` → direct copy
   - `address` → direct copy (preserve street, city, state, zip, country)
   - `website` → direct copy (if exists)
   - Other fields (industry, stage, size, etc.) → default to null/empty
2. **Core Identity**: 
   - `vision`, `purpose` → direct copy
   - `coreValues: string[]` → create CoreValue entries with name only, empty meaning/implementation
3. **Target Market**:
   - `targetMarket` (or `niche`) → `nicheStatement`
   - `ica` → create single ICA with demographics field populated, other fields empty
   - ICAs → empty array if no existing ICA
4. **Products**: 
   - Existing products with name + problem → migrate with empty description, flag incomplete
5. **Value Proposition**:
   - `valueProposition` → `uniqueSellingProposition`
6. **Business Model**: Empty (new feature)

### Backward Compatibility

The existing `GET /business/foundation` endpoint should continue to work during transition, returning the new structure. The `PATCH /business/foundation` endpoint is being replaced with `PUT` for full updates and section-specific `PATCH` endpoints.

---

## AI Service Endpoints (Separate Service)

The following AI endpoints are specified separately in the AI service documentation:

| Endpoint | Description |
|----------|-------------|
| `POST /ai/foundation/health-check` | AI-powered comprehensive health analysis |
| `POST /ai/foundation/suggest-vision` | Generate vision statement suggestions |
| `POST /ai/foundation/suggest-values` | Generate core value suggestions |
| `POST /ai/foundation/enrich-ica` | Enrich ICA with additional details |
| `POST /ai/foundation/suggest-products` | Suggest products based on business context |
| `POST /ai/foundation/refine-usp` | Refine unique selling proposition |

These will be documented in a separate AI service specification update.

---

**End of API Requirements Document**

