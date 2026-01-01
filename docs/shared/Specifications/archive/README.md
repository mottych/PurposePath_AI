# Archived Specifications

This folder contains obsolete API specification documents that have been superseded by newer versions.

## Archived Files

### Traction Service Specifications

| File | Version | Date Archived | Superseded By | Notes |
|------|---------|---------------|---------------|-------|
| `backend-integration-traction-service-v5.md` | v5.0 | December 23, 2025 | v7 modular specs | Monolithic spec with deprecated Measure entities |
| `backend-integration-traction-service-v6.md` | v6.0 | December 23, 2025 | v7 modular specs | 3,547 lines monolithic spec |

## Current Specifications

**Traction Service v7** - See [`../traction-service/README.md`](../traction-service/README.md)

The v7 specifications have been reorganized into **controller-based modular documents** for easier maintenance and AI assistant consumption:

- [`goals-api.md`](../traction-service/goals-api.md) - 13 endpoints
- [`measures-api.md`](../traction-service/measures-api.md) - 7 endpoints
- [`measure-links-api.md`](../traction-service/measure-links-api.md) - 8 endpoints
- [`measure-data-api.md`](../traction-service/measure-data-api.md) - 9 endpoints
- [`actions-api.md`](../traction-service/actions-api.md) - 9 endpoints
- [`issues-api.md`](../traction-service/issues-api.md) - 15 endpoints
- [`dashboard-reports-activities-api.md`](../traction-service/dashboard-reports-activities-api.md) - 5 endpoints

## Key Changes from v6 to v7

### Deprecated Entities Removed (15,902 lines)
- ❌ `GoalKpiLink` → ✅ `MeasureLink` (unified linking model)
- ❌ `MeasureMilestone` → ✅ `MeasureData` (unified target/actual model)
- ❌ `MeasureActual` → ✅ `MeasureData`
- ❌ `MeasureReading` → ✅ `MeasureData`

### New Features in v7
- ✅ Configuration-based issue status/types
- ✅ Batch tag operations
- ✅ Issue lifecycle endpoints
- ✅ Issue to actions conversion
- ✅ Unified Measure data model

### Documentation Structure
- **v5/v6**: Single monolithic file (3,547 lines)
- **v7**: Controller-based modular files (easier to maintain, better for AI assistants)

## Why These Files Are Archived

1. **Code Cleanup**: Issue #374 removed 15,902 lines of deprecated code
2. **Modular Structure**: v7 splits into controller-based documents
3. **Maintenance**: Smaller files easier to maintain and update
4. **AI Assistant Efficiency**: Modular structure optimizes token usage

## Do Not Delete

These archived files are kept for:
- Historical reference
- Migration documentation
- Troubleshooting legacy issues
- Understanding API evolution

---

**Last Updated:** December 23, 2025  
**Archived By:** PurposePath Development Team
