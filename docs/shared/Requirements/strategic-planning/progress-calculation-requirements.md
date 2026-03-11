# Progress Calculation Requirements

**Document Version:** 1.0  
**Last Updated:** January 20, 2026  
**Related Issue:** #585

## Overview

This document specifies the unified business rules for calculating progress at three levels in the PurposePath system:
1. **Measure Progress** - Progress of individual measures based on actual vs. target data
2. **Strategy Progress** - Progress of strategies based on their linked measures
3. **Goal Progress** - Progress of goals based on measures and strategies

**Single Source of Truth:** All progress calculations are implemented in `ProgressCalculationService` (Domain layer).

---

## Measure Progress

### Requirements

- **Minimum Data:** Requires at least **2 actual data points** and **1 target data point**
- **If insufficient data:** Return `null` (no progress available)

### Formula

```
progress = ((current - baseline) / (target - baseline)) × 100
```

Where:
- **baseline (b)** = The earliest actual data value
- **current (c)** = The latest actual data value  
- **target (t)** = The value of the latest target defined (ultimate target)

### Example

```
Baseline:  January 1, value = 100
Current:   March 1, value = 160
Target:    December 31, value = 200

Progress = (160 - 100) / (200 - 100) × 100 = 60%
```

### Direction Handling

- **Up (default):** Higher values = more progress (formula as above)
- **Down:** Lower values = more progress (inverted calculation)

---

## Variance

Variance measures the difference between where we are and where we are **expected** to be at the current point in time.

### Formula

```
variance = (actualValue - expectedValue) / (targetValue - baselineValue)
```

Where:
- **actualValue (av)** = Latest actual data value
- **expectedValue (ev)** = Interpolated expected value at the date of the latest actual
- **targetValue (tv)** = Latest target value
- **baselineValue (bv)** = Earliest actual data value

### Expected Value Calculation

Expected value is calculated using **linear interpolation** between targets that bracket the latest actual date.

#### Multiple Targets (Standard Case)

Find the two targets that bracket the latest actual date:

```
ev = tbv + ((tav - tbv) × (ad - tbd) / (tad - tbd))
```

Where:
- **ad** = Latest actual data date
- **tbd** = Date of the target data preceding the latest actual
- **tad** = Date of the target data immediately following the latest actual
- **tbv** = Value of the target data preceding the latest actual
- **tav** = Value of the target data immediately following the latest actual

#### Single Target (Edge Case)

When there is only one target, use the **baseline** as the initial target:

```
ev = bv + ((tv - bv) × (ad - bd) / (td - bd))
```

Where:
- **bv** = Baseline value (earliest actual)
- **bd** = Baseline date (earliest actual date)
- **tv** = Target value (single target)
- **td** = Target date (single target)
- **ad** = Latest actual data date

### Example

```
Baseline:     Jan 1, value = 100
First Target: Jun 30, value = 150
Second Target: Dec 31, value = 200
Latest Actual: Apr 1, value = 125

Expected Value at Apr 1:
- Time from baseline to first target: Jan 1 to Jun 30 = 181 days
- Time from baseline to actual: Jan 1 to Apr 1 = 90 days
- Ratio: 90/181 = 0.497
- ev = 100 + (0.497 × (150 - 100)) = 124.85

Variance = 125 - 124.85 = 0.15
Variance % = (0.15 / (200 - 100)) × 100 = 0.15%
```

---

## Progress Status

Progress status categorizes how the measure is performing relative to expectations.

### Status Definitions

1. **on_track** - Variance ≥ 0 (meeting or exceeding expectations)
2. **behind** - Variance < 0 AND |variance| ≤ threshold (below expectations but within acceptable range)
3. **at_risk** - Variance < 0 AND |variance| > threshold (significantly below expectations)

### Threshold Calculation

```
thresholdDeviation = |targetValue - baselineValue| × ((100 - thresholdPct) / 100)
```

Default threshold: **80%** (allows 20% deviation)

### Example

```
Baseline = 100, Target = 200, Threshold = 80%
Total change = 200 - 100 = 100
Threshold deviation = 100 × (100 - 80) / 100 = 20

If expectedValue = 140:
- actualValue = 140 → variance = 0 → status = "on_track"
- actualValue = 130 → variance = -10 → |variance| ≤ 20 → status = "behind"
- actualValue = 110 → variance = -30 → |variance| > 20 → status = "at_risk"
```

---

## Strategy Progress

### Business Rules

1. **If strategy has a primary measure** → Use that measure's progress
2. **Otherwise** → Average all measures that have data (ignore measures without data)
3. **If no measures have data** → Return `null`

### Example

```
Strategy has 3 measures:
- Measure A (primary): no data → skip to rule 2
- Measure B: 60% progress
- Measure C: 80% progress
- Measure D: no data → ignore

Strategy progress = (60 + 80) / 2 = 70%
```

---

## Goal Progress

### Business Rules

1. **If goal has a primary measure** → Use that measure's progress
2. **Otherwise, if goal has measures attached directly** → Average all goal-level measures with data (ignore measures without data)
3. **Otherwise** → Average all strategies with data (ignore strategies without data)
4. **If no data available** → Return `null`

### Example

```
Goal has:
- 2 direct measures (goal-level): 50%, 70%
- 3 strategies: 60%, 80%, no data

Since goal has direct measures with data:
Goal progress = (50 + 70) / 2 = 60%

(Strategies are not used in this case)
```

### Fallback Example

```
Goal has:
- No direct measures
- Strategy A: 60%
- Strategy B: 80%
- Strategy C: no data

Goal progress = (60 + 80) / 2 = 70%
```

---

## Edge Cases

### 1. Insufficient Data

- **Measure:** < 2 actuals OR < 1 target → Return `null` / `no_data`
- **Strategy:** No measures with data → Return `null`
- **Goal:** No measures and no strategies with data → Return `null`

### 2. Zero Change (Target = Baseline)

If `targetValue == baselineValue`:
- Progress = 0%
- Variance calculation may be undefined → handle gracefully

### 3. Date Outside Target Range

- **Before first target:** Interpolate from baseline to first target
- **After last target:** Use last target value as expected value

### 4. Single Actual Data Point

Not valid for progress calculation (requires minimum 2 actuals).

### 5. Negative Progress

Progress can be negative if current value is worse than baseline. This is valid and indicates regression.

### 6. Progress > 100%

Progress can exceed 100% if current value surpasses the target. This is valid and indicates overachievement.

---

## Implementation Notes

### Domain Service

**Class:** `ProgressCalculationService`  
**Location:** `PurposePath.Domain.Services`  
**Interface:** `IProgressCalculationService`

### Methods

```csharp
// Measure-level progress
ProgressInfo CalculateMeasureProgress(
    MeasureLink link,
    IReadOnlyList<MeasureData> allTargets,
    IReadOnlyList<MeasureData> allActuals,
    Measure measure);

// Strategy-level progress
decimal? CalculateStrategyProgress(
    Strategy strategy,
    IReadOnlyList<MeasureLink> measureLinks,
    Func<MeasureLink, decimal?> getMeasureProgress);

// Goal-level progress
decimal? CalculateGoalProgress(
    Goal goal,
    IReadOnlyList<MeasureLink> goalMeasureLinks,
    IReadOnlyList<Strategy> strategies,
    Func<MeasureLink, decimal?> getMeasureProgress,
    Func<Strategy, decimal?> getStrategyProgress);
```

### Return Types

- **Measure Progress:** `ProgressInfo` (includes progress %, status, variance, days until target, overdue flag)
- **Strategy Progress:** `decimal?` (percentage or null if no data)
- **Goal Progress:** `decimal?` (percentage or null if no data)

---

## Testing Requirements

### Unit Tests Required

1. **Measure Progress:**
   - Insufficient data (< 2 actuals, no targets)
   - Minimum data (exactly 2 actuals, 1 target)
   - Multiple targets with interpolation
   - Single target edge case
   - Direction "up" vs "down"
   - Progress > 100% and < 0%
   - Zero change (target = baseline)

2. **Strategy Progress:**
   - Primary measure takes precedence
   - Average of multiple measures
   - Ignore measures without data
   - All measures have no data → null

3. **Goal Progress:**
   - Primary measure takes precedence
   - Average of goal-level measures
   - Fallback to strategies
   - No data → null

### Integration Tests Required

- Full goal → strategies → measures hierarchy
- Widget data providers
- Dashboard calculations
- Command center calculations

---

## Change History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-20 | 1.0 | Initial documentation for unified progress calculation (Issue #585) |

---

## References

- GitHub Issue: #585
- Domain Service: `PurposePath.Domain.Services.ProgressCalculationService`
- Interface: `PurposePath.Domain.Services.IProgressCalculationService`
- Value Object: `PurposePath.Domain.ValueObjects.ProgressInfo`
