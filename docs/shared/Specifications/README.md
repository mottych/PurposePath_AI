# PurposePath API Specifications

**Last Updated:** February 4, 2026

This folder contains all API specification documents for PurposePath, organized by consuming application.

---

## Directory Structure

```
Specifications/
├── README.md                    ← You are here
├── admin-api.md                 # Legacy admin API (see admin-portal/ for current)
│
├── user-app/                    # User Application (React Frontend)
│   ├── index.md                 # Master index for user-facing APIs
│   ├── account-api.md           # Account, billing, subscriptions (consolidated)
│   ├── account-gap.md           # Account service gap analysis
│   ├── business-foundation-api.md # Business foundation, wizard, values, ICAs
│   ├── people-service.md        # People CRUD operations
│   ├── org-structure-service.md # Roles, org chart (user endpoints)
│   ├── dashboard-service.md     # Dashboard configuration and widgets
│   ├── common-patterns.md       # Shared patterns & data models
│   ├── traction-service/        # Traction feature APIs
│   │   ├── README.md            # Traction service index
│   │   ├── goals-api.md         # Goals management
│   │   ├── strategies-api.md    # Strategies management
│   │   ├── measures-api.md      # MEASUREs management
│   │   ├── measure-links-api.md # MEASURE relationships
│   │   ├── measure-data-api.md  # MEASURE data points
│   │   ├── actions-api.md       # Actions/To-dos
│   │   ├── issues-api.md        # Issues/Roadblocks
│   │   ├── alignment-api.md     # Alignment calculations
│   │   ├── insights-api.md      # AI insights
│   │   └── dashboard-reports-activities-api.md
│   └── Websocket/               # WebSocket specifications
│
├── admin-portal/                # Admin Portal (Internal)
│   └── admin-api-specification.md  # Complete admin API spec (v2.0)
│
├── ai-user/                     # AI/Coaching Services
│   └── backend-integration-unified-ai.md  # Unified AI/Coaching API
│
├── ai-admin-portal/             # AI Admin Portal
│
└── archive/                     # Obsolete/Reference Documents
    ├── README.md                # Archive index
    └── ...                      # Various archived specs
```

---

## Quick Links

### User Application APIs

| Document | Description | Endpoints |
|----------|-------------|-----------|
| [Master Index](./user-app/index.md) | Complete user app API overview | All |
| [User & Tenant Service](./user-app/user-tenant-service.md) | Authentication, profile, subscriptions | ~16 |
| [Business Foundation Service](./user-app/business-foundation-service.md) | Business setup, wizard, values | ~25 |
| [Account API](./user-app/account-api.md) | Auth, billing, subscriptions (consolidated) | ~40 |
| [AI/Coaching Service](./user-app/coaching-service.md) | AI/ML coaching features | ~20 |
| [People Service](./user-app/people-service.md) | Person management, tags, types | ~25 |
| [Org Structure Service](./user-app/org-structure-service.md) | Roles, relationships, org chart | ~20 |
| [Dashboard Service](./user-app/dashboard-service.md) | Dashboard configuration, widgets | ~15 |
| [Traction Service](./user-app/traction-service/README.md) | Goals, Measures, Actions, Issues | ~66 |

**Total User App Endpoints:** ~227

### Admin Portal APIs

| Document | Description | Endpoints |
|----------|-------------|-----------|
| [Admin API v2.0](./admin-portal/admin-api-specification.md) | Complete admin portal spec (updated Feb 4, 2026) | 88 |

**Total Admin Endpoints:** 88

---

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway                               │
│    api.dev.purposepath.app / api.purposepath.app            │
└─────────────────┬───────────────────┬───────────────────────┘
                  │                   │
    ┌─────────────▼─────────┐   ┌─────▼─────────────┐
    │    User App Routes    │   │  Admin Routes     │
    │    /account/api/v1    │   │  /admin/api/v1    │
    │    /traction/api/v1   │   │                   │
    │    /coaching/api/v1   │   │                   │
    └─────────────┬─────────┘   └─────┬─────────────┘
                  │                   │
    ┌─────────────▼─────────┐   ┌─────▼─────────────┐
    │   Account Lambda      │   │   Admin Lambda    │
    │   Traction Lambda     │   │                   │
    │   Coaching Lambda     │   │                   │
    └───────────────────────┘   └───────────────────┘
```

---

## Document Standards

### API Documentation Format

Each API document follows this structure:

1. **Header** - Version, dates, base URL
2. **Overview** - Service purpose, key concepts
3. **Endpoints** - Grouped by resource/feature
   - HTTP method + path
   - Request/response examples
   - Field constraints
   - Error responses
4. **Data Types** - TypeScript interfaces, enums
5. **Error Codes** - Standard error codes

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| File names | kebab-case | `people-service.md` |
| Endpoint paths | kebab-case | `/api/people/{id}/tags` |
| Request/Response fields | snake_case | `first_name`, `created_at` |
| TypeScript types | PascalCase | `PersonResponse` |

---

## Versioning

- **Current Version:** 7.0 (December 2025)
- **Traction Service:** v7 modular (controller-based docs)
- **People/Org Service:** v1.1 (migrated to Account Lambda)
- **Admin API:** v2.0 (comprehensive spec with all endpoints, Feb 4, 2026)

### Change History

| Date | Version | Changes |
|------|---------|---------|
| Feb 4, 2026 | 2.0 | Admin API v2.0: Complete specification with all 88 endpoints documented |
| Dec 30, 2025 | 1.0 | User/Tenant and Business Foundation services split from Account service |
| Dec 23, 2025 | 7.0 | Documentation reorganization, v7 traction specs |
| Dec 22, 2025 | 1.1 | People/Org endpoints migrated to Account service |
| Dec 21, 2025 | 7.0 | Measure Link/Data refactoring, modular traction specs |

---

## For Developers

### Adding New Endpoints

1. Determine which service/document the endpoint belongs to
2. Add to appropriate section following existing format
3. Include request/response examples with realistic data
4. Document all field constraints and validation rules
5. Add error responses for common failure cases
6. Update endpoint counts in this README

### Archiving Documents

When deprecating a specification:
1. Move to `archive/` folder
2. Add entry to `archive/README.md`
3. Note the superseding document
4. Keep for 6 months minimum for reference

---

## Related Documentation

- **[Backend Development Guidelines](../../.github/DEVELOPMENT_GUIDELINES.md)** - Architecture & coding standards
- **[Copilot Rules](../../.github/COPILOT_RULES.md)** - Spec enforcement rules
- **[Deployment Guide](../Deployment/)** - Infrastructure & deployment
