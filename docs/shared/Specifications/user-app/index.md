# PurposePath Backend Integration Specifications - Master Index

**Document Date:** December 23, 2025  
**Version:** 7.0  
**Purpose:** Source of truth for frontend-backend integration points

## Document Structure

This specification is split into multiple documents for efficient AI assistant consumption. Each document can be referenced independently or as a complete set.

### Core Service Specifications

1. **[Account Service](./account-service.md)**
   - Authentication & Authorization
   - User Management
   - Subscription & Billing
   - Onboarding Workflows

2. **[Coaching Service](./coaching-service.md)**
   - AI/ML Endpoints (Alignment, Validation, Suggestions)
   - Business Insights & Metrics
   - Coaching Conversations
   - Strategic Planning AI

3. **[Traction Service](./traction-service/README.md)** ⭐ NEW STRUCTURE (v7)
   - **Controller-based specifications** for easier maintenance
   - Goals, KPIs, KPI Links, KPI Data, Actions, Issues, People, Dashboard
   - [View Traction Service Index →](./traction-service/README.md)

4. **[Common Patterns & Data Models](./common-patterns.md)**
   - Authentication Headers
   - Error Handling
   - Data Models & Enumerations
   - Environment Configuration

---

## 🎉 What's New in v7 (December 23, 2025)

### Traction Service Reorganization
- **Split into controller-based documents** - Each API (Goals, KPIs, Actions, etc.) has its own specification file
- **Removed deprecated endpoints** - Cleaned 15,902 lines of deprecated code
- **New KpiLink & KpiData design** - Replaced old GoalKpiLink, KpiMilestone, KpiActual patterns
- **Complete documentation** - Full request/response examples, validation rules, business rules

### Status
- ✅ **Goals API** - Complete (13 endpoints documented)
- ✅ **KPIs API** - Complete (7 endpoints documented)
- ✅ **KPI Links API** - Complete (8 endpoints documented)
- ✅ **KPI Data API** - Complete (9 endpoints documented)
- ✅ **Actions API** - Complete (9 endpoints documented)
- ✅ **Issues API** - Complete (15 endpoints documented)
- ✅ **Dashboard/Reports/Activities APIs** - Complete (5 endpoints documented)
- ⏭️ **People API** - Deferred (moving to Account service)

**Total Documented:** 66 endpoints across 7 API groups

### Migration Notes
- Old v5/v6 monolithic specs archived in `./archive/`
- New v7 modular controller-based specifications
- Complete with request/response examples, TypeScript types, business rules

See [Traction Service Index](./traction-service/README.md) for complete details.

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
  Auth/Users    AI/ML/Insights  Goals/Ops/KPIs
  Billing                       Real-time
```

### Service Base URLs

| Service | Environment Variable | Default (Localhost) |
|---------|---------------------|---------------------|
| Account | `REACT_APP_ACCOUNT_API_URL` | `http://localhost:8001` |
| Coaching | `REACT_APP_COACHING_API_URL` | `http://localhost:8000` |
| Traction | `REACT_APP_TRACTION_API_URL` | `http://localhost:8002` |

### Service Responsibilities

#### Account Service

- User authentication (email/password, Google OAuth)
- User profile management
- Subscription tiers and billing
- Payment processing (Stripe integration)
- Onboarding data management
- Feature flags and user limits

#### Coaching Service

- All AI/ML operations
- Goal alignment calculations
- Strategy suggestions
- KPI recommendations
- Business insights generation
- Root cause analysis
- Action prioritization and scheduling
- Coaching conversations

#### Traction Service

- Goals CRUD operations
- Strategies and KPIs management
- Operations (Actions and Issues)
- Goal-Strategy-KPI relationships
- Activity feeds
- Company reports
- Real-time updates via SSE

## Implementation Details

### Frontend Service Files

| Service | Primary Client | Implementation Files |
|---------|----------------|---------------------|
| Account | `api.ts` → `accountClient` | `src/services/api.ts`, `src/services/account.ts`, `src/services/subscriptions.ts`, `src/services/users.ts` |
| Coaching | `api.ts` → `coachingClient` | `src/services/api.ts`, `src/services/alignment-engine-service.ts`, `src/services/strategy-suggestion-service.ts`, `src/services/kpi-recommendation-service.ts`, `src/services/operations-ai-service.ts` |
| Traction | `traction.ts` → `traction` | `src/services/traction.ts`, `src/services/goal-service.ts`, `src/services/action-service.ts`, `src/services/issue-service.ts`, `src/services/operations-traction-service.ts`, `src/services/kpi-planning-service.ts`, `src/services/realtime.ts` |

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
- [Coaching Service Specs →](./coaching-service.md)
- [Traction Service Specs →](./traction-service/README.md)
- [People & Org Structure →](./people-service.md)
- [Common Patterns & Data Models →](./common-patterns.md)
