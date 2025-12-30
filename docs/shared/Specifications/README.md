# PurposePath API Specifications

**Last Updated:** December 23, 2025

This folder contains all API specification documents for PurposePath, organized by consuming application.

---

## Directory Structure

```
Specifications/
├── README.md                    ← You are here
│
├── user-app/                    # User Application (React Frontend)
│   ├── index.md                 # Master index for user-facing APIs
│   ├── user-tenant-service.md   # Auth, users, subscriptions, billing
│   ├── business-foundation-service.md # Business foundation, wizard, values, ICAs, products
│   ├── people-service.md        # People CRUD operations
│   ├── org-structure-service.md # Roles, relationships, org chart
│   ├── coaching-service.md      # AI/ML coaching endpoints
│   ├── common-patterns.md       # Shared patterns & data models
│   └── traction-service/        # Traction feature APIs
│       ├── README.md            # Traction service index
│       ├── goals-api.md
│       ├── kpis-api.md
│       ├── kpi-links-api.md
│       ├── kpi-data-api.md
│       ├── actions-api.md
│       ├── issues-api.md
│       └── dashboard-reports-activities-api.md
│
├── admin-portal/                # Admin Portal (Internal)
│   └── admin-api-specification.md  # Complete admin API spec
│
└── archive/                     # Obsolete/Reference Documents
    ├── README.md                # Archive index
    ├── admin-integration/       # Old admin docs (19 files)
    ├── kpi-refactor-issues/     # KPI refactoring issue specs
    └── *.md                     # Various archived specs
```

---

## Quick Links

### User Application APIs

| Document | Description | Endpoints |
|----------|-------------|-----------|
| [User & Tenant Management](./user-app/user-tenant-service.md) | Authentication, user profile, subscriptions, billing | 16 |
| [Business Foundation](./user-app/business-foundation-service.md) | Business profile, identity, market, model, wizard, values, ICAs, products | 25 |
| [People Service](./user-app/people-service.md) | Person management, tags, types | ~25 |
| [Org Structure Service](./user-app/org-structure-service.md) | Roles, relationships, org chart | ~20 |
| [Coaching Service](./user-app/coaching-service.md) | AI/ML coaching features | ~15 |
| [Traction Service](./user-app/traction-service/README.md) | Goals, KPIs, Actions, Issues | 66 |

**Total User App Endpoints:** ~167

### Admin Portal APIs

| Document | Description | Endpoints |
|----------|-------------|-----------|
| [Admin API](./admin-portal/admin-api-specification.md) | Complete admin portal spec | ~80 |

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

### Document Header ###
1. Docuemnt Nae
2. Document version
3. Last Update Date
4. List of endpoints in the docuemnt `GET /auth/login`
5. Revisions audit table, including date, version, short summary of the cahnge 

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

Specification shoud **not** include version history or audit and revision comment, **only reflect current state**.

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| File names | kebab-case | `user-tenant-service.md`, `people-service.md` |
| Endpoint paths | kebab-case | `/api/business-foundation/core-values`, `/api/people/{id}/tags` |
| Request/Response fields | **camelCase** | `businessName`, `firstName`, `createdAt` |
| TypeScript types | PascalCase | `UserProfile`, `BusinessFoundation`, `PersonResponse` |

**IMPORTANT:** All REST API field names use **camelCase** (not snake_case) to match frontend TypeScript types.

---

## Versioning

- **Current Version:** 7.0 (December 2025)
- **Traction Service:** v7 modular (controller-based docs)
- **People/Org Service:** v1.1 (migrated to Account Lambda)

### Change History

| Date | Version | Changes |
|------|---------|---------|
| Dec 30, 2025 | 1.0 | Account Service split into User & Tenant Management and Business Foundation. Removed deprecated onboarding/admin/people endpoints. Standardized to camelCase throughout. Specifications now reflect actual implementation. |
| Dec 23, 2025 | 7.0 | Documentation reorganization, v7 traction specs |
| Dec 22, 2025 | 1.1 | People/Org endpoints migrated to Account service |
| Dec 21, 2025 | 7.0 | KPI Link/Data refactoring, modular traction specs |

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
