# KPI Linking & Data Model Refactoring - Frontend Requirements

**Version:** 1.0  
**Date:** December 21, 2025  
**Epic:** #362  
**Status:** In Progress (Backend Phase 2 Complete)

---

## Executive Summary

This document outlines the requirements for refactoring the KPI linking and data management system. The changes enable more flexible KPI assignments (to Persons, Goals, and Strategies) and unify target/actual value storage with enhanced subtype tracking.

---

## Table of Contents

1. [Background & Problem Statement](#background--problem-statement)
2. [Key Concept Changes](#key-concept-changes)
3. [Entity Model Changes](#entity-model-changes)
4. [API Endpoint Changes](#api-endpoint-changes)
5. [UI/UX Requirements](#uiux-requirements)
6. [Data Migration Notes](#data-migration-notes)
7. [Terminology Reference](#terminology-reference)

---

## Background & Problem Statement

### Current Limitations

1. **KPI Linking is Goal-only**: The `GoalKpiLink` entity only supports linking KPIs to Goals, not to individual Persons or specific Strategies within a Goal.

2. **Fragmented Data Storage**: Target values (milestones) and actual values are stored in separate tables (`KpiMilestone`, `KpiActual`, `KpiReading`), making unified queries difficult.

3. **Only One Target Line**: No support for multiple target types (expected, stretch/optimal, minimum thresholds) for visualization.

4. **Calculated Fields Are Persisted**: `ExpectedValue`, `Variance`, and `VariancePercentage` are stored, which causes inconsistencies when targets change.

5. **No Support for Aggregate KPI Period Counts**: Cannot specify "2-week periods" or "bi-weekly" aggregation windows.

### Goals of This Refactoring

1. Allow KPIs to be linked to **Persons** (personal scorecards), **Goals**, and **Strategies**
2. Unify target and actual data into a single `KpiData` entity
3. Support **three target lines** (Expected, Optimal, Minimal) for richer planning visualization
4. Distinguish between **Estimated** and **Measured** actual values
5. Calculate variance on-the-fly instead of persisting it
6. Add `AggregationPeriodCount` for flexible time windows (e.g., "every 2 weeks")

---

## Key Concept Changes

### 1. KPI Linking Model (GoalKpiLink → KpiLink)

**Before:**
- KPI linked only to Goals
- One `GoalKpiLink` record per Goal-KPI pair

**After:**
- KPI linked to Person (required) + optional Goal + optional Strategy
- Three link types:
  - **Personal Scorecard**: KPI linked to Person only (no Goal/Strategy)
  - **Goal-level KPI**: KPI linked to Person + Goal (measures the goal)
  - **Strategy-level KPI**: KPI linked to Person + Goal + Strategy (measures specific strategy)

**Business Rules:**
- Every KpiLink has a PersonId (the person responsible for targets/actuals)
- Goal-level links: Only ONE link allowed per KpiId+GoalId combination
- Strategy-level links: Only ONE link allowed per KpiId+StrategyId combination
- Personal scorecards: Multiple people CAN have the same KPI (personal metrics)

### 2. Unified KPI Data (KpiMilestone + KpiActual + KpiReading → KpiData)

**Before:**
- `KpiMilestone`: Target values with dates
- `KpiActual`: Measured values with calculated variance
- `KpiReading`: Additional readings (rarely used)

**After:**
- Single `KpiData` entity with:
  - `DataCategory`: **Target** or **Actual**
  - `TargetSubtype`: **Expected**, **Optimal**, or **Minimal** (for targets only)
  - `ActualSubtype`: **Estimate** or **Measured** (for actuals only)

### 3. Target Subtypes (Three Lines on Charts)

| Subtype | Visual | Description |
|---------|--------|-------------|
| **Expected** | Black line | Primary target - the realistic goal |
| **Optimal** | Green line | Stretch target - best-case scenario |
| **Minimal** | Red line | Floor threshold - below this is trouble |

**Use Cases:**
- When displaying a single target value, use **Expected**
- When displaying full planning view, show all three lines
- Users can define one, two, or all three for any period

### 4. Actual Subtypes (Estimate vs Measured)

| Subtype | Description |
|---------|-------------|
| **Estimate** | User's best guess when measurement not available |
| **Measured** | Actual recorded measurement from data source |

**Business Rule:** If both Estimate and Measured exist for the same period, **Measured takes precedence** in displays and calculations.

### 5. Field Renames

| Old Name | New Name | Notes |
|----------|----------|-------|
| `ActualValue` | `PostValue` | The recorded value (target or actual) |
| `MeasurementDate` | `PostDate` | The date of the data point |
| `MilestoneDate` | `PostDate` | Unified with actual dates |
| (new) | `MeasuredPeriodStartDate` | Start of measurement window for aggregate KPIs |

### 6. Removed Calculated Fields

The following fields are **no longer persisted**. They will be calculated on-the-fly in the frontend or API response layer:

- `ExpectedValue` (in KpiActual)
- `Variance` (in KpiActual)
- `VariancePercentage` (in KpiActual)

**Rationale:** When targets change, persisted variance becomes incorrect. Calculating on-the-fly ensures consistency.

### 7. Aggregation Period Count

**New field on Kpi entity:** `AggregationPeriodCount`

| Aggregation Period | Count | Meaning |
|--------------------|-------|---------|
| Weekly | 1 | Every week |
| Weekly | 2 | Every 2 weeks (bi-weekly) |
| Monthly | 1 | Every month |
| Monthly | 3 | Every quarter (3 months) |

**Example:** "20 new clients in a 2-week period"
- `AggregationPeriod = Weekly`
- `AggregationPeriodCount = 2`

---

## Entity Model Changes

### New: KpiLink Entity

```
KpiLink
├── Id (KpiLinkId)
├── TenantId
├── KpiId (required)
├── PersonId (required) ← NEW: Person responsible for this link
├── GoalId (optional) ← Links to Goal
├── StrategyId (optional) ← Links to Strategy (requires GoalId)
├── LinkedAt
├── ThresholdPct (optional, 0-100)
├── LinkType (optional: "primary", "secondary", "supporting", "monitoring")
├── Weight (optional, 0.0-1.0)
├── DisplayOrder (optional)
├── IsPrimary (boolean)
└── Audit fields (CreatedBy, CreatedAt, UpdatedBy, UpdatedAt)
```

### New: KpiData Entity

```
KpiData
├── Id (KpiDataId)
├── KpiLinkId (required) ← Links to KpiLink, not directly to Kpi
├── TenantId
├── DataCategory (Target | Actual)
├── TargetSubtype (Expected | Optimal | Minimal) ← only for Targets
├── ActualSubtype (Estimate | Measured) ← only for Actuals
├── PostValue (decimal)
├── PostDate (DateTime)
├── MeasuredPeriodStartDate (DateTime, nullable) ← for aggregate KPIs
├── Label (optional)
├── ConfidenceLevel (1-5, optional)
├── Rationale (optional)
├── OriginalValue (for overrides)
├── IsManualOverride (boolean)
├── OverrideComment (optional)
├── DataSource (optional)
├── SourceReferenceId (optional)
├── TriggersReplan (boolean)
├── ReplanThresholdExceeded (boolean)
├── AutoAdjustmentApplied (boolean, nullable)
└── Audit fields
```

### Modified: Kpi Entity

```
Kpi
├── ... existing fields ...
├── AggregationPeriodCount (int, default 1) ← NEW
└── ... existing fields ...
```

---

## API Endpoint Changes

### Affected Endpoints (Review Required)

Based on the archived `backend-integration-traction-service-v5.md` (now superseded by v7 modular specs in `traction-service/`), the following endpoint groups needed updates:

#### KPI Linking Endpoints (Currently Goal-only, Will Support Person/Strategy)

| # | Endpoint | Current | Change Required |
|---|----------|---------|-----------------|
| 18 | `GET /goals/{goalId}/kpis` | Lists goal KPIs | Add `personId` filter, include `PersonId` in response |
| 19 | `PUT /goals/{goalId}/kpis/{kpiId}:setPrimary` | Set primary | No change needed |
| 20 | `POST /goals/{goalId}/kpis:link` | Link to goal | Add `personId` to request, support Strategy linking |
| 21 | `POST /goals/{goalId}/kpis:unlink` | Unlink from goal | No structural change |
| 22 | `POST /goals/{goalId}/kpis/{kpiId}:setThreshold` | Set threshold | No change needed |
| 23 | `GET /goals/{goalId}/kpis/{kpiId}:link` | Get link details | Include `PersonId`, `StrategyId` in response |
| 24 | `GET /goals/{goalId}/available-kpis` | Available KPIs | No change needed |

#### New Endpoints Needed (Person-based KPI Linking)

| Endpoint | Purpose |
|----------|---------|
| `GET /people/{personId}/kpis` | List all KPIs linked to a person (personal scorecard) |
| `POST /people/{personId}/kpis:link` | Link KPI to person (personal scorecard) |
| `POST /people/{personId}/kpis:unlink` | Unlink KPI from person |
| `GET /strategies/{strategyId}/kpis` | List KPIs linked to a strategy |

#### KPI Planning Endpoints (Milestones → KpiData with Subtypes)

| # | Endpoint | Change Required |
|---|----------|-----------------|
| 25 | `GET /kpi-planning/kpis/{id}/milestones` | **DEPRECATED** - Replace with targets query |
| 26 | `PUT /kpi-planning/kpis/{id}/milestones` | **DEPRECATED** - Replace with target creation |
| 27 | `GET /kpi-planning/kpis/{id}/plan` | Update response to include three target series |
| 28 | `GET /kpi-planning/goals/{goalId}/kpi-planning` | Update to use new KpiData model |
| 29 | `GET /kpi-planning/kpis/{id}/actuals` | **MAJOR CHANGE** - Now returns `KpiData` with `ActualSubtype` |
| 30 | `POST /kpi-planning/kpis/{id}/actuals` | **MAJOR CHANGE** - Include `ActualSubtype` in request |

#### New/Modified Planning Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /kpi-planning/kpi-links/{linkId}/targets` | Get all targets for a KPI link |
| `GET /kpi-planning/kpi-links/{linkId}/targets?subtype=Expected` | Get specific target series |
| `POST /kpi-planning/kpi-links/{linkId}/targets` | Create a target (specify subtype) |
| `GET /kpi-planning/kpi-links/{linkId}/actuals` | Get actuals for a KPI link |
| `POST /kpi-planning/kpi-links/{linkId}/actuals` | Record an actual (specify subtype) |
| `GET /kpi-planning/kpi-links/{linkId}/all-series` | Get all three target lines + actuals |

### Response Format Changes

#### New KPI Link Response

```json
{
  "id": "kpilink_123",
  "kpiId": "kpi_456",
  "personId": "person_789",
  "personName": "John Doe",
  "goalId": "goal_101",
  "goalTitle": "Increase Revenue",
  "strategyId": null,
  "linkedAt": "2025-01-15T10:00:00Z",
  "thresholdPct": 80,
  "isPrimary": true,
  "linkType": "personal" | "goal" | "strategy"
}
```

#### New KPI Data Response (for actuals/targets)

```json
{
  "id": "kpidata_123",
  "kpiLinkId": "kpilink_456",
  "dataCategory": "Target" | "Actual",
  "targetSubtype": "Expected" | "Optimal" | "Minimal",
  "actualSubtype": "Estimate" | "Measured",
  "postValue": 50000,
  "postDate": "2025-03-31",
  "measuredPeriodStartDate": "2025-03-01",
  "label": "Q1 Target",
  "confidenceLevel": 4,
  "rationale": "Based on historical trends"
}
```

#### New Planning Overview Response (Three Lines)

```json
{
  "kpiId": "kpi_123",
  "kpiLinkId": "kpilink_456",
  "currentValue": 42000,
  "targets": {
    "expected": [
      { "postDate": "2025-03-31", "postValue": 50000 },
      { "postDate": "2025-06-30", "postValue": 75000 }
    ],
    "optimal": [
      { "postDate": "2025-03-31", "postValue": 60000 },
      { "postDate": "2025-06-30", "postValue": 90000 }
    ],
    "minimal": [
      { "postDate": "2025-03-31", "postValue": 40000 },
      { "postDate": "2025-06-30", "postValue": 55000 }
    ]
  },
  "actuals": [
    { 
      "postDate": "2025-01-31", 
      "postValue": 45000, 
      "actualSubtype": "Measured" 
    }
  ]
}
```

---

## UI/UX Requirements

### 1. Personal Scorecard View

**New Feature:** Users should be able to view and manage KPIs linked only to themselves (no Goal/Strategy).

**Displays:**
- List of personal KPIs
- Targets (three lines) and actuals for each
- Ability to add new personal KPIs

### 2. Goal KPI View (Updated)

**Changes:**
- Show responsible person for each linked KPI
- Display link type (Goal-level vs Strategy-level)
- Option to link KPI to specific strategy within goal

### 3. KPI Planning Chart (Updated)

**Changes:**
- Display **three target lines** (Expected=black, Optimal=green, Minimal=red)
- Legend to toggle visibility of each line
- Distinguish Estimated vs Measured actuals (different markers/colors)

### 4. Target Entry Form (Updated)

**Changes:**
- Allow entering values for each target subtype
- Option to set only Expected, or all three subtypes
- Default to Expected if only one value entered

### 5. Actual Entry Form (Updated)

**Changes:**
- Radio/toggle to select: "Estimate" or "Measured"
- If Estimate exists for period and user enters Measured, show confirmation
- Clear visual distinction between estimate and measured values

### 6. Variance Display (Updated)

**Changes:**
- Variance is calculated on-the-fly: `PostValue - ExpectedTarget(at PostDate)`
- If no Expected target exists for date, show "No target" instead of variance
- Use interpolation between milestone dates for in-between periods

---

## Data Migration Notes

### Migration Strategy

1. **GoalKpiLink → KpiLink**
   - Map existing `GoalKpiLink` records to new `KpiLink` table
   - Set `PersonId` to the Goal's owner (or a system default)
   - Set `GoalId` from existing link
   - Set `StrategyId` to null (existing links are Goal-level)

2. **KpiMilestone → KpiData (Target)**
   - Create KpiLink for each KpiId-GoalId pair if not exists
   - Map to `KpiData` with `DataCategory = Target`
   - Set `TargetSubtype = Expected` (existing milestones are primary targets)
   - Map `MilestoneDate` → `PostDate`
   - Map `TargetValue` → `PostValue`

3. **KpiActual → KpiData (Actual)**
   - Create KpiLink for each KpiId-GoalId pair if not exists
   - Map to `KpiData` with `DataCategory = Actual`
   - Set `ActualSubtype = Measured` (existing actuals are measured)
   - Map `MeasurementDate` → `PostDate`
   - Map `ActualValue` → `PostValue`
   - **DO NOT migrate**: `ExpectedValue`, `Variance`, `VariancePercentage`

### Backward Compatibility

During transition:
- Keep old tables readable (soft deprecation)
- New API endpoints use new tables
- Old endpoints redirect to new ones with mapping

---

## Terminology Reference

| Term | Definition |
|------|------------|
| **KpiLink** | Association between a KPI and a Person (required), optionally with Goal and Strategy |
| **Personal Scorecard** | KPI linked only to a Person (no Goal/Strategy) |
| **Goal-level KPI** | KPI linked to Person + Goal (measures goal progress) |
| **Strategy-level KPI** | KPI linked to Person + Goal + Strategy (measures strategy execution) |
| **KpiData** | A single data point - either a Target or an Actual |
| **Target** | Planned/desired value at a specific date |
| **Actual** | Recorded/observed value at a specific date |
| **Expected Target** | Primary target line (realistic goal) |
| **Optimal Target** | Stretch target line (best-case, green) |
| **Minimal Target** | Floor threshold line (minimum acceptable, red) |
| **Estimate** | User's best guess when measurement not available |
| **Measured** | Actual recorded value from data or observation |
| **PostValue** | The numeric value being recorded (new name for ActualValue/TargetValue) |
| **PostDate** | The date of the data point (new name for MeasurementDate/MilestoneDate) |
| **MeasuredPeriodStartDate** | For aggregate KPIs, the start of the measurement window |
| **AggregationPeriodCount** | How many periods to aggregate (e.g., 2 for bi-weekly) |

---

## Next Steps

### Backend (In Progress)

1. ✅ Phase 1: Domain Layer - Complete
2. ✅ Phase 2: Infrastructure Layer - Complete
3. 🔜 Phase 3: Application Layer (Commands, Queries, Handlers)
4. 🔜 Phase 4: API Layer (Controllers, DTOs)
5. 🔜 Phase 5: Migration Scripts

### Frontend (Ready to Start)

1. Review this requirements document
2. Update TypeScript interfaces for new models
3. Create new components for Personal Scorecard view
4. Update KPI linking forms to include PersonId
5. Update charts to support three target lines
6. Update actual entry forms for subtype selection
7. Implement on-the-fly variance calculation

---

## Questions for Frontend Team

1. Should personal scorecard be a new page/tab or a filter on existing KPI views?
2. Preferred visualization for three target lines (solid/dashed/dotted)?
3. How to handle old data without PersonId during transition?
4. Should Estimate values have a different marker style than Measured?

---

**Document maintained by:** Agent B (KPI Refactoring)  
**Last Updated:** December 21, 2025  
**Related Issues:** #362 (Epic), #363-#374 (Implementation)

