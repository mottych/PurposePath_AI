# Measure Linking & Data Model Refactoring - Frontend Requirements

**Version:** 1.0  
**Date:** December 21, 2025  
**Epic:** #362  
**Status:** In Progress (Backend Phase 2 Complete)

---

## Executive Summary

This document outlines the requirements for refactoring the Measure linking and data management system. The changes enable more flexible Measure assignments (to Persons, Goals, and Strategies) and unify target/actual value storage with enhanced subtype tracking.

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

1. **Measure Linking is Goal-only**: The `GoalMeasureLink` entity only supports linking Measures to Goals, not to individual Persons or specific Strategies within a Goal.

2. **Fragmented Data Storage**: Target values (milestones) and actual values are stored in separate tables (`MeasureMilestone`, `MeasureActual`, `MeasureReading`), making unified queries difficult.

3. **Only One Target Line**: No support for multiple target types (expected, stretch/optimal, minimum thresholds) for visualization.

4. **Calculated Fields Are Persisted**: `ExpectedValue`, `Variance`, and `VariancePercentage` are stored, which causes inconsistencies when targets change.

5. **No Support for Aggregate Measure Period Counts**: Cannot specify "2-week periods" or "bi-weekly" aggregation windows.

### Goals of This Refactoring

1. Allow Measures to be linked to **Persons** (personal scorecards), **Goals**, and **Strategies**
2. Unify target and actual data into a single `MeasureData` entity
3. Support **three target lines** (Expected, Optimal, Minimal) for richer planning visualization
4. Distinguish between **Estimated** and **Measured** actual values
5. Calculate variance on-the-fly instead of persisting it
6. Add `AggregationPeriodCount` for flexible time windows (e.g., "every 2 weeks")

---

## Key Concept Changes

### 1. Measure Linking Model (GoalMeasureLink → MeasureLink)

**Before:**
- Measure linked only to Goals
- One `GoalMeasureLink` record per Goal-Measure pair

**After:**
- Measure linked to Person (required) + optional Goal + optional Strategy
- Three link types:
  - **Personal Scorecard**: Measure linked to Person only (no Goal/Strategy)
  - **Goal-level Measure**: Measure linked to Person + Goal (measures the goal)
  - **Strategy-level Measure**: Measure linked to Person + Goal + Strategy (measures specific strategy)

**Business Rules:**
- Every MeasureLink has a PersonId (the person responsible for targets/actuals)
- Goal-level links: Only ONE link allowed per MeasureId+GoalId combination
- Strategy-level links: Only ONE link allowed per MeasureId+StrategyId combination
- Personal scorecards: Multiple people CAN have the same Measure (personal metrics)

### 2. Unified Measure Data (MeasureMilestone + MeasureActual + MeasureReading → MeasureData)

**Before:**
- `MeasureMilestone`: Target values with dates
- `MeasureActual`: Measured values with calculated variance
- `MeasureReading`: Additional readings (rarely used)

**After:**
- Single `MeasureData` entity with:
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
| (new) | `MeasuredPeriodStartDate` | Start of measurement window for aggregate Measures |

### 6. Removed Calculated Fields

The following fields are **no longer persisted**. They will be calculated on-the-fly in the frontend or API response layer:

- `ExpectedValue` (in MeasureActual)
- `Variance` (in MeasureActual)
- `VariancePercentage` (in MeasureActual)

**Rationale:** When targets change, persisted variance becomes incorrect. Calculating on-the-fly ensures consistency.

### 7. Aggregation Period Count

**New field on Measure entity:** `AggregationPeriodCount`

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

### New: MeasureLink Entity

```
MeasureLink
├── Id (MeasureLinkId)
├── TenantId
├── MeasureId (required)
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

### New: MeasureData Entity

```
MeasureData
├── Id (MeasureDataId)
├── MeasureLinkId (required) ← Links to MeasureLink, not directly to Measure
├── TenantId
├── DataCategory (Target | Actual)
├── TargetSubtype (Expected | Optimal | Minimal) ← only for Targets
├── ActualSubtype (Estimate | Measured) ← only for Actuals
├── PostValue (decimal)
├── PostDate (DateTime)
├── MeasuredPeriodStartDate (DateTime, nullable) ← for aggregate Measures
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

### Modified: Measure Entity

```
Measure
├── ... existing fields ...
├── AggregationPeriodCount (int, default 1) ← NEW
└── ... existing fields ...
```

---

## API Endpoint Changes

### Affected Endpoints (Review Required)

Based on the archived `backend-integration-traction-service-v5.md` (now superseded by v7 modular specs in `traction-service/`), the following endpoint groups needed updates:

#### Measure Linking Endpoints (Currently Goal-only, Will Support Person/Strategy)

| # | Endpoint | Current | Change Required |
|---|----------|---------|-----------------|
| 18 | `GET /goals/{goalId}/measures` | Lists goal Measures | Add `personId` filter, include `PersonId` in response |
| 19 | `PUT /goals/{goalId}/measures/{measureId}:setPrimary` | Set primary | No change needed |
| 20 | `POST /goals/{goalId}/measures:link` | Link to goal | Add `personId` to request, support Strategy linking |
| 21 | `POST /goals/{goalId}/measures:unlink` | Unlink from goal | No structural change |
| 22 | `POST /goals/{goalId}/measures/{measureId}:setThreshold` | Set threshold | No change needed |
| 23 | `GET /goals/{goalId}/measures/{measureId}:link` | Get link details | Include `PersonId`, `StrategyId` in response |
| 24 | `GET /goals/{goalId}/available-measures` | Available Measures | No change needed |

#### New Endpoints Needed (Person-based Measure Linking)

| Endpoint | Purpose |
|----------|---------|
| `GET /people/{personId}/measures` | List all Measures linked to a person (personal scorecard) |
| `POST /people/{personId}/measures:link` | Link Measure to person (personal scorecard) |
| `POST /people/{personId}/measures:unlink` | Unlink Measure from person |
| `GET /strategies/{strategyId}/measures` | List Measures linked to a strategy |

#### Measure Planning Endpoints (Milestones → MeasureData with Subtypes)

| # | Endpoint | Change Required |
|---|----------|-----------------|
| 25 | `GET /measure-planning/measures/{id}/milestones` | **DEPRECATED** - Replace with targets query |
| 26 | `PUT /measure-planning/measures/{id}/milestones` | **DEPRECATED** - Replace with target creation |
| 27 | `GET /measure-planning/measures/{id}/plan` | Update response to include three target series |
| 28 | `GET /measure-planning/goals/{goalId}/measure-planning` | Update to use new MeasureData model |
| 29 | `GET /measure-planning/measures/{id}/actuals` | **MAJOR CHANGE** - Now returns `MeasureData` with `ActualSubtype` |
| 30 | `POST /measure-planning/measures/{id}/actuals` | **MAJOR CHANGE** - Include `ActualSubtype` in request |

#### New/Modified Planning Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /measure-planning/measure-links/{linkId}/targets` | Get all targets for a Measure link |
| `GET /measure-planning/measure-links/{linkId}/targets?subtype=Expected` | Get specific target series |
| `POST /measure-planning/measure-links/{linkId}/targets` | Create a target (specify subtype) |
| `GET /measure-planning/measure-links/{linkId}/actuals` | Get actuals for a Measure link |
| `POST /measure-planning/measure-links/{linkId}/actuals` | Record an actual (specify subtype) |
| `GET /measure-planning/measure-links/{linkId}/all-series` | Get all three target lines + actuals |

### Response Format Changes

#### New Measure Link Response

```json
{
  "id": "measurelink_123",
  "measureId": "measure_456",
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

#### New Measure Data Response (for actuals/targets)

```json
{
  "id": "measuredata_123",
  "measureLinkId": "measurelink_456",
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
  "measureId": "measure_123",
  "measureLinkId": "measurelink_456",
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

**New Feature:** Users should be able to view and manage Measures linked only to themselves (no Goal/Strategy).

**Displays:**
- List of personal Measures
- Targets (three lines) and actuals for each
- Ability to add new personal Measures

### 2. Goal Measure View (Updated)

**Changes:**
- Show responsible person for each linked Measure
- Display link type (Goal-level vs Strategy-level)
- Option to link Measure to specific strategy within goal

### 3. Measure Planning Chart (Updated)

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

1. **GoalMeasureLink → MeasureLink**
   - Map existing `GoalMeasureLink` records to new `MeasureLink` table
   - Set `PersonId` to the Goal's owner (or a system default)
   - Set `GoalId` from existing link
   - Set `StrategyId` to null (existing links are Goal-level)

2. **MeasureMilestone → MeasureData (Target)**
   - Create MeasureLink for each MeasureId-GoalId pair if not exists
   - Map to `MeasureData` with `DataCategory = Target`
   - Set `TargetSubtype = Expected` (existing milestones are primary targets)
   - Map `MilestoneDate` → `PostDate`
   - Map `TargetValue` → `PostValue`

3. **MeasureActual → MeasureData (Actual)**
   - Create MeasureLink for each MeasureId-GoalId pair if not exists
   - Map to `MeasureData` with `DataCategory = Actual`
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
| **MeasureLink** | Association between a Measure and a Person (required), optionally with Goal and Strategy |
| **Personal Scorecard** | Measure linked only to a Person (no Goal/Strategy) |
| **Goal-level Measure** | Measure linked to Person + Goal (measures goal progress) |
| **Strategy-level Measure** | Measure linked to Person + Goal + Strategy (measures strategy execution) |
| **MeasureData** | A single data point - either a Target or an Actual |
| **Target** | Planned/desired value at a specific date |
| **Actual** | Recorded/observed value at a specific date |
| **Expected Target** | Primary target line (realistic goal) |
| **Optimal Target** | Stretch target line (best-case, green) |
| **Minimal Target** | Floor threshold line (minimum acceptable, red) |
| **Estimate** | User's best guess when measurement not available |
| **Measured** | Actual recorded value from data or observation |
| **PostValue** | The numeric value being recorded (new name for ActualValue/TargetValue) |
| **PostDate** | The date of the data point (new name for MeasurementDate/MilestoneDate) |
| **MeasuredPeriodStartDate** | For aggregate Measures, the start of the measurement window |
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
4. Update Measure linking forms to include PersonId
5. Update charts to support three target lines
6. Update actual entry forms for subtype selection
7. Implement on-the-fly variance calculation

---

## Questions for Frontend Team

1. Should personal scorecard be a new page/tab or a filter on existing Measure views?
2. Preferred visualization for three target lines (solid/dashed/dotted)?
3. How to handle old data without PersonId during transition?
4. Should Estimate values have a different marker style than Measured?

---

**Document maintained by:** Agent B (Measure Refactoring)  
**Last Updated:** December 21, 2025  
**Related Issues:** #362 (Epic), #363-#374 (Implementation)

