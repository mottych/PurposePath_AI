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
│   ├── account-service.md       # Auth, users, billing
│   ├── people-service.md        # People CRUD operations
│   ├── org-structure-service.md # Roles, org chart (user endpoints)
│   ├── common-patterns.md       # Shared patterns & data models
│   └── traction-service/        # Traction feature APIs
│       ├── README.md            # Traction service index
│       ├── goals-api.md
│       ├── measures-api.md
│       ├── measure-links-api.md
│       ├── measure-data-api.md
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
    ├── measure-refactor-issues/     # Measure refactoring issue specs
    └── *.md                     # Various archived specs
```

---

## Quick Links

### User Application APIs

| Document | Description | Endpoints |
|----------|-------------|-----------|
| [Account Service](./user-app/account-service.md) | Authentication, users, billing | ~20 |
| [AI/Coaching Service](./ai-user/backend-integration-unified-ai.md) | AI/ML coaching features | ~15 |
| [People Service](./user-app/people-service.md) | Person management, tags, types | ~25 |
| [Org Structure Service](./user-app/org-structure-service.md) | Roles, relationships, org chart | ~20 |
| [Traction Service](./user-app/traction-service/README.md) | Goals, Measures, Actions, Issues | 66 |

**Total User App Endpoints:** ~146

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

### Change History

| Date | Version | Changes |
|------|---------|---------|
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
