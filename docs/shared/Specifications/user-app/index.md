# PurposePath Backend Integration Specifications - Master Index

**Document Date:** December 23, 2025  
**Version:** 7.0  
**Purpose:** Source of truth for frontend-backend integration points

## Document Structure

This specification is split into multiple documents for efficient AI assistant consumption. Each document can be referenced independently or as a complete set.

### Core Service Specifications

1. **[User & Tenant Management Service](./user-tenant-service.md)** ⭐ NEW (v1.0)
   - Authentication (Login, Register, Google OAuth, Password Reset)
   - User Profile Management
   - Email Verification
   - Subscription & Billing Integration
   - User Features & Limits

2. **[Account API (Auth/Billing/Subscriptions)](./account-api.md)** ⭐ Consolidated (v2.0)
   - Auth flows, profile, tenant endpoints
   - Subscription tiers, user subscriptions
   - Billing portal, payment intents, provider webhooks
   - Health endpoints

3. **[Business Foundation Service](./business-foundation-service.md)** ⭐ NEW (v1.0)
   - Business Profile, Identity, Market, Proposition, Model
   - Core Values Management
   - Ideal Customer Avatars (ICAs)
   - Products & Services Inventory
   - Wizard Progress Tracking

4. **[People Service](./people-service.md)**
   - Person CRUD operations
   - Person tags and types
   - User-person relationships

5. **[Org Structure Service](./org-structure-service.md)**
   - Organization roles and permissions
   - Organization chart and relationships
   - User org structure endpoints

6. **[AI/Coaching Service](../ai-user/backend-integration-unified-ai.md)**
   - AI/ML Endpoints (Alignment, Validation, Suggestions)
   - Business Insights & Metrics
   - Coaching Conversations
   - Strategic Planning AI

7. **[Traction Service](./traction-service/README.md)** ⭐ MODULAR STRUCTURE (v7)
   - **Controller-based specifications** for easier maintenance
   - Goals, Measures, Measure Links, Measure Data, Actions, Issues, People, Dashboard
   - [View Traction Service Index →](./traction-service/README.md)

8. **[Dashboard Service](./dashboard-service.md)** ⭐ NEW (v1.0)
   - User Dashboard Configuration CRUD
   - System Templates Management
   - Widget Catalog & Registry
   - Dynamic Widget Data Retrieval
   - Responsive Grid Layouts

9. **[Common Patterns & Data Models](./common-patterns.md)**
   - Authentication Headers
   - Error Handling
   - Data Models & Enumerations
   - Environment Configuration

---

## 🎉 What's New in v1.0 (December 30, 2025)

### Account Service Split & Cleanup
- **Extracted Account Service into two focused documents:**
  - User & Tenant Management - Authentication, user profile, subscriptions, billing
  - Business Foundation - Foundation sections, wizard, core values, ICAs, products
- **Removed deprecated endpoints:** Onboarding endpoints (moved to Business Foundation), Admin discount codes (not user-frontend), People/Org structure endpoints (out of scope)
- **Standardized naming:** All property names now use camelCase (not snake_case) to match frontend implementation
- **Specification now reflects implementation:** Documents describe actual working code, not aspirational features

### Documentation Standards
- ✅ All endpoints with actual implementation reference
- ✅ Field-by-field request/response examples
- ✅ Frontend service file locations documented
- ✅ Error handling patterns explained
- ✅ CamelCase property names throughout

**Total User/Tenant Endpoints:** 16  
**Total Business Foundation Endpoints:** 25  
**Total Documented:** 41 endpoints across 2 new service specs

## Architecture Overview

### Microservices Structure

PurposePath frontend integrates with three backend microservices through RESTful APIs and Server-Sent Events (SSE).

```
┌─────────────────┐
│   Frontend      │
│  (React/TS)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │  axios  │
    └────┬────┘
         │
    ┌────┴────────────────────────────────┐
    │                                     │
┌───▼────────┐  ┌──────────┐  ┌─────────▼────┐
│  Account   │  │ Coaching │  │   Traction   │
│  Service   │  │ Service  │  │   Service    │
└────────────┘  └──────────┘  └──────────────┘
  Auth/Users    AI/ML/Insights  Goals/Ops/Measures
  Billing                       Real-time
```

### Service Base URLs

| Service | Environment Variable | Default (Localhost) |
|---------|---------------------|---------------------|
| Account | `REACT_APP_ACCOUNT_API_URL` | `http://localhost:8001` |
| Coaching | `REACT_APP_COACHING_API_URL` | `http://localhost:8000` |
| Traction | `REACT_APP_TRACTION_API_URL` | `http://localhost:8002` |

### Service Responsibilities

#### Account Service (User & Tenant Management)

- User authentication (email/password, Google OAuth)
- User profile management
- Email verification and password reset
- Subscription tiers and billing
- Payment processing (Stripe integration)
- User feature access and usage limits
- Token refresh and session management

#### Account Service (Business Foundation)

- Business profile (name, website, address, industry)
- Core identity (vision, purpose, core values)
- Target market (niche, key problems, ideal customer avatars)
- Value proposition (offer, audience, differentiator)
- Business model (revenue, pricing, partnerships)
- Products and services inventory
- Multi-step wizard progress tracking

#### People Service

- Person CRUD operations
- Person attributes and tags
- Person type definitions
- User-person relationships

#### Org Structure Service

- Organization roles and permissions
- Org chart management
- Reporting relationships
- Access control structures

#### Coaching Service

- All AI/ML operations
- Goal alignment calculations
- Strategy suggestions
- Measure recommendations
- Business insights generation
- Root cause analysis
- Action prioritization and scheduling
- Coaching conversations

#### Traction Service

- Goals CRUD operations
- Strategies and Measures management
- Operations (Actions and Issues)
- Goal-Strategy-Measure relationships
- Activity feeds
- Company reports
- Real-time updates via SSE

## Implementation Details

### Frontend Service Files

| Service | Primary Client | Implementation Files |
|---------|----------------|---------------------|
| User & Tenant Mgmt | `api.ts` → `accountClient` | `src/services/api.ts` |
| Business Foundation | `business-foundation-service.ts` → `accountClient` | `src/services/business-foundation-service.ts`, `src/types/business-foundation.ts` |
| People | TBD | TBD |
| Org Structure | TBD | TBD |
| Coaching | `api.ts` → `coachingClient` | `src/services/api.ts`, `src/services/alignment-engine-service.ts`, `src/services/strategy-suggestion-service.ts`, `src/services/measure-recommendation-service.ts`, `src/services/operations-ai-service.ts` |
| Traction | `traction.ts` → `traction` | `src/services/traction.ts`, `src/services/goal-service.ts`, `src/services/action-service.ts`, `src/services/issue-service.ts`, `src/services/operations-traction-service.ts`, `src/services/measure-planning-service.ts`, `src/services/realtime.ts` |

### Authentication Flow

1. User logs in → POST /auth/login (Account Service)
2. Receives: accessToken, refreshToken, user, tenant
3. Stores: localStorage.accessToken, localStorage.refreshToken, localStorage.tenantId
4. All subsequent requests include:
   - Authorization: Bearer {accessToken}
   - X-Tenant-Id: {tenantId}
5. On 401 response → POST /auth/refresh (Account Service)
6. Updates tokens and retries original request

### Request Interceptors

All service clients (accountClient, coachingClient, traction) implement:

- **Token injection**: Automatically adds `Authorization: Bearer {token}` header
- **Tenant header**: Automatically adds `X-Tenant-Id` header
- **Token refresh**: On 401 response, attempts token refresh and retries request
- **Special headers**: Adds `X-Frontend-Base-Url` for email-triggering endpoints

## Quick Reference

### Most Common Endpoints

| Operation | Endpoint | Service |
|-----------|----------|---------|
| Login | `POST /auth/login` | Account |
| Get User Profile | `GET /user/profile` | Account |
| Get User Subscription | `GET /user/subscription` | Account |
| List Goals | `GET /goals` | Traction |
| Create Goal | `POST /goals` | Traction |
| Calculate Alignment | `POST /api/coaching/alignment-check` | Coaching |
| Get Strategy Suggestions | `POST /api/coaching/strategy-suggestions` | Coaching |
| List Actions | `GET /api/operations/actions` | Traction |
| Create Action | `POST /api/operations/actions` | Traction |
| Real-time Goal Updates | `GET /realtime/goals/{goalId}/activity` (SSE) | Traction |

### Common HTTP Status Codes

| Code | Meaning | Frontend Action |
|------|---------|----------------|
| 200 | Success | Process response data |
| 401 | Unauthorized | Trigger token refresh, retry |
| 403 | Forbidden | Show access denied message |
| 404 | Not Found | Handle missing resource |
| 422 | Validation Error | Show field-specific errors |
| 500 | Server Error | Show generic error, enable retry |

### Environment Variables

```bash
# Service URLs
REACT_APP_ACCOUNT_API_URL=https://api.dev.purposepath.app/account/api/v1
REACT_APP_COACHING_API_URL=https://api.dev.purposepath.app/coaching/api/v1
REACT_APP_TRACTION_API_URL=https://api.dev.purposepath.app/traction/api/v1

# Feature Flags
REACT_APP_FEATURE_REALTIME=true

# SSE Configuration
REACT_APP_SSE_BASE_URL=https://api.dev.purposepath.app/traction/api/v1

# Optional Features
REACT_APP_FE_BASE_HEADER_LOGIN=false
```

## Version History

### Version 3.0 (October 13, 2025)

- Split into multiple documents for AI assistant efficiency
- Updated to reflect current implementation state
- Added frontend service file mappings
- Clarified service responsibilities
- Added implementation details and architecture diagrams

### Version 2.1 (October 1, 2025)

- Added AI/ML endpoints to Coaching Service
- Clarified alignment engine routing
- Added operations AI endpoints

### Version 2.0 (Previous)

- Multi-service architecture
- Separated Account, Coaching, and Traction concerns

---

**Navigation:**

- [Account Service Specs →](./account-service.md)
- [AI/Coaching Service Specs →](../ai-user/backend-integration-unified-ai.md)
- [Traction Service Specs →](./traction-service/README.md)
- [People & Org Structure →](./people-service.md)
- [Common Patterns & Data Models →](./common-patterns.md)
