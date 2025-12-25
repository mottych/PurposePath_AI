# Epic: KPI Linking & Data Model Refactoring

**Epic ID:** #XXX (to be assigned)  
**Created:** December 21, 2025  
**Status:** Planning  
**Priority:** High  
**Labels:** `epic`, `refactoring`, `strategic-planning`, `kpi`

---

## 📋 Executive Summary

This epic covers a comprehensive refactoring of the KPI linking and data tracking system to:

1. **Rename and enhance `GoalKpiLink`** → `KpiLink` with support for linking to Person, Goal, and Strategy
2. **Consolidate data tables** - Merge `KpiActual`, `KpiMilestone`, and `KpiReading` into a unified `KpiData` entity
3. **Add support for multiple target types** - Expected, Optimal, Minimal
4. **Add support for actual value types** - Estimate vs Measured
5. **Add `AggregationPeriodCount`** to support multi-period aggregation windows

---

## 📚 Reference Documents

| Document | Purpose |
|----------|---------|
| `docs/Specifications/people-org-structure-technical-design.md` | Person entity specification |
| `docs/guides/KPI_PLANNING_REQUIREMENTS.md` | Current KPI planning requirements |
| `docs/Specifications/archive/backend-integration-traction-service-v5.md` | Archived v5 API specifications |
| `docs/Specifications/traction-service/` | Current v7 modular API specifications |

---

## 🎯 Business Goals

1. **Flexible KPI Assignment**: Allow KPIs to be linked to Goals, Strategies within Goals, or Persons directly (personal scorecards)
2. **Unified Data Model**: Single source for all KPI target and actual values
3. **Multiple Target Types**: Support Expected (main), Optimal (stretch), and Minimal (floor) targets for visual tracking
4. **Actual Value Types**: Distinguish between Estimated (forecasted) and Measured (actual) values
5. **Simplified Maintenance**: Remove calculated fields that can be derived on-the-fly

---

## 🏗️ Architecture Overview

### Current State

```
Goal (1) ────< GoalKpiLink >──── (1) Kpi
                                     │
                 ┌───────────────────┼───────────────────┐
                 │                   │                   │
            KpiMilestone       KpiActual           KpiReading
            (targets)          (actuals)           (readings)
```

### Target State

```
Person (1) ──┐
             │
Goal (1) ────┼──< KpiLink >──── (1) Kpi
             │        │
Strategy (1)─┘        │
                      │
                  KpiData
                  (unified targets & actuals)
```

---

## 📊 New Data Model

### KpiLink Entity

```csharp
public class KpiLink : FullyAuditableEntity
{
    public KpiLinkId Id { get; private set; }
    public TenantId TenantId { get; private set; }
    public KpiId KpiId { get; private set; }
    
    // Required - person responsible for values on this link
    public PersonId PersonId { get; private set; }
    
    // Optional - Goal association
    public GoalId? GoalId { get; private set; }
    
    // Optional - Strategy association (requires GoalId)
    public StrategyId? StrategyId { get; private set; }
    
    // Existing metadata
    public string? LinkType { get; private set; }
    public decimal? Weight { get; private set; }
    public int? DisplayOrder { get; private set; }
    public bool IsPrimary { get; private set; }
    public decimal? ThresholdPct { get; private set; }
    public DateTime LinkedAt { get; private set; }
}
```

**Uniqueness Constraints:**
- Only ONE link per `(KpiId, GoalId)` where `GoalId IS NOT NULL AND StrategyId IS NULL`
- Only ONE link per `(KpiId, StrategyId)` where `StrategyId IS NOT NULL`
- Multiple links per `(KpiId, PersonId)` allowed when `GoalId IS NULL AND StrategyId IS NULL` (personal scorecards)

### KpiData Entity

```csharp
public class KpiData : FullyAuditableEntity
{
    public KpiDataId Id { get; private set; }
    public KpiLinkId KpiLinkId { get; private set; }
    
    // Data classification
    public KpiDataCategory DataCategory { get; private set; }  // Target | Actual
    public TargetSubtype? TargetSubtype { get; private set; }  // Expected | Optimal | Minimal
    public ActualSubtype? ActualSubtype { get; private set; }  // Estimate | Measured
    
    // Core values (renamed from ActualValue/MeasurementDate)
    public decimal PostValue { get; private set; }
    public string PostDate { get; private set; }  // ISO 8601
    public DateTime? MeasuredPeriodStartDate { get; private set; }  // For aggregate KPIs
    
    // From KpiMilestone
    public string? Label { get; private set; }
    public int? ConfidenceLevel { get; private set; }  // 1-5
    public string? Rationale { get; private set; }
    
    // From KpiActual - Override tracking
    public decimal? OriginalValue { get; private set; }
    public bool IsManualOverride { get; private set; }
    public string? OverrideComment { get; private set; }
    
    // From KpiActual - Source tracking
    public DataSource DataSource { get; private set; }
    public string? SourceReferenceId { get; private set; }
    
    // From KpiActual - Replan triggers
    public bool TriggersReplan { get; private set; }
    public bool ReplanThresholdExceeded { get; private set; }
    public bool? AutoAdjustmentApplied { get; private set; }
    
    // Audit
    public string RecordedBy { get; private set; }
    public DateTimeOffset RecordedAt { get; private set; }
}
```

**Note:** Calculated fields removed (will be computed on-the-fly):
- ~~ExpectedValue~~ (calculated from Target data)
- ~~Variance~~ (calculated: PostValue - ExpectedValue)
- ~~VariancePercentage~~ (calculated: Variance / ExpectedValue * 100)

### New Enums

```csharp
public enum KpiDataCategory
{
    Target,   // Planned/target value
    Actual    // Actual/recorded value
}

public enum TargetSubtype
{
    Expected,  // Primary target - realistic, committed goal (black line)
    Optimal,   // Stretch target - best-case aspirational goal (green line)
    Minimal    // Minimum target - floor, below which indicates trouble (red line)
}

public enum ActualSubtype
{
    Estimate,  // User's best guess when no measurement available
    Measured   // Actual recorded value (wins over Estimate for same period)
}
```

### Kpi Entity Changes

Add `AggregationPeriodCount` to support multi-period windows:

```csharp
// In Kpi entity
public int? AggregationPeriodCount { get; private set; }  // NEW: e.g., 2 for "2 weeks"
```

---

## 📋 Linked Issues (Implementation Order)

### Phase 1: Domain Layer Foundation

| Issue | Title | Dependencies |
|-------|-------|--------------|
| #XXX-1 | **Domain: Add new enums and value objects** | None |
| #XXX-2 | **Domain: Create KpiLink entity (rename GoalKpiLink)** | #XXX-1 |
| #XXX-3 | **Domain: Create KpiData entity** | #XXX-1, #XXX-2 |
| #XXX-4 | **Domain: Add AggregationPeriodCount to Kpi** | None |

### Phase 2: Infrastructure Layer

| Issue | Title | Dependencies |
|-------|-------|--------------|
| #XXX-5 | **Infrastructure: KpiLink data model, mapper, repository** | #XXX-2 |
| #XXX-6 | **Infrastructure: KpiData data model, mapper, repository** | #XXX-3 |

### Phase 3: Application Layer

| Issue | Title | Dependencies |
|-------|-------|--------------|
| #XXX-7 | **Application: KpiLink commands and queries** | #XXX-5 |
| #XXX-8 | **Application: KpiData commands and queries** | #XXX-6 |

### Phase 4: API Layer

| Issue | Title | Dependencies |
|-------|-------|--------------|
| #XXX-9 | **API: Update KPI linking endpoints** | #XXX-7 |
| #XXX-10 | **API: Update KPI planning endpoints** | #XXX-8 |

### Phase 5: Migration & Cleanup

| Issue | Title | Dependencies |
|-------|-------|--------------|
| #XXX-11 | **Migration: Data migration scripts** | #XXX-5, #XXX-6 |
| #XXX-12 | **Cleanup: Remove deprecated entities and tables** | #XXX-11 |

---

## 📈 Progress Tracking

### Epic Progress Template

Update this section as work progresses:

```markdown
## Progress Update - [DATE]

### Completed
- [ ] Issue #XXX-1: Domain enums and value objects
- [ ] Issue #XXX-2: KpiLink entity
- [ ] Issue #XXX-3: KpiData entity
- [ ] Issue #XXX-4: AggregationPeriodCount
- [ ] Issue #XXX-5: KpiLink infrastructure
- [ ] Issue #XXX-6: KpiData infrastructure
- [ ] Issue #XXX-7: KpiLink application layer
- [ ] Issue #XXX-8: KpiData application layer
- [ ] Issue #XXX-9: KPI linking API
- [ ] Issue #XXX-10: KPI planning API
- [ ] Issue #XXX-11: Data migration
- [ ] Issue #XXX-12: Cleanup

### Current Phase: [Phase Name]
### Blockers: [None / List blockers]
### Notes: [Any relevant notes]
```

---

## ⚠️ Breaking Changes

1. **GoalKpiLink renamed to KpiLink** - All references must be updated
2. **KpiActual, KpiMilestone, KpiReading tables deprecated** - Data migrated to KpiData
3. **Calculated fields removed** - Frontend must calculate variance on-the-fly
4. **New required field PersonId on KpiLink** - Migration will use current Kpi.OwnerId or user who created the link

---

## 🔄 Migration Strategy

1. **Create new tables** (`kpi-links`, `kpi-data`) alongside existing tables
2. **Run migration scripts** to copy data from old to new tables
3. **Update application code** to use new entities
4. **Verify data integrity** with validation scripts
5. **Deprecate old code paths** (keep for rollback)
6. **Remove old tables** after validation period

---

## ✅ Acceptance Criteria

- [ ] KPIs can be linked to Goals, Strategies, or Persons
- [ ] Personal scorecards work (KPI linked only to Person)
- [ ] Goal-level KPI links enforce uniqueness per Goal
- [ ] Strategy-level KPI links enforce uniqueness per Strategy
- [ ] KpiData supports Target and Actual categories
- [ ] Target subtypes (Expected, Optimal, Minimal) work correctly
- [ ] Actual subtypes (Estimate, Measured) work correctly with Measured winning for same period
- [ ] Variance is calculated on-the-fly (not stored)
- [ ] AggregationPeriodCount works with AggregationPeriod
- [ ] All existing functionality preserved (replanning, thresholds, etc.)
- [ ] Data migration successful with no data loss
- [ ] Old tables removed after successful migration

---

## 📝 Notes

- Wait for Person entity implementation (see `docs/Specifications/people-org-structure-technical-design.md`)
- Person.Id will be available in domain layer soon
- Consider feature flags for gradual rollout

---

**End of Epic Document**


