# Issue #XXX-4: Domain - Add AggregationPeriodCount to Measure

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** Medium  
**Labels:** `domain`, `entity`, `measure`  
**Estimated Effort:** 1-2 hours

---

## 📋 Description

Add `AggregationPeriodCount` property to the `Measure` entity to support multi-period aggregation windows (e.g., "2 weeks", "3 months").

---

## 🏗️ Changes Required

### Measure Entity Updates

Location: `PurposePath.Domain/Entities/Measure.cs`

Add the following property:

```csharp
/// <summary>
/// Number of aggregation periods in the measurement window.
/// Used with AggregationPeriod to define windows like "2 weeks" or "3 months".
/// Default is 1.
/// </summary>
public int AggregationPeriodCount { get; private set; } = 1;
```

Add setter method:

```csharp
/// <summary>
/// Set the aggregation period count
/// </summary>
/// <param name="count">Number of periods (must be >= 1)</param>
public void SetAggregationPeriodCount(int count)
{
    if (count < 1)
        throw new ArgumentOutOfRangeException(nameof(count), "Aggregation period count must be at least 1");

    AggregationPeriodCount = count;
}
```

Update the `ConfigureAggregation` method:

```csharp
/// <summary>
/// Configure aggregation for automated data sources (Issue #211)
/// </summary>
public void ConfigureAggregation(
    AggregationType aggregationType,
    AggregationPeriod aggregationPeriod,
    DataNature valueType,
    int periodCount = 1)
{
    if (DataSourceType != Common.DataSourceType.Automated)
        throw new InvalidOperationException("Aggregation can only be configured for automated data sources");

    if (periodCount < 1)
        throw new ArgumentOutOfRangeException(nameof(periodCount), "Period count must be at least 1");

    AggregationType = aggregationType;
    AggregationPeriod = aggregationPeriod;
    ValueType = valueType;
    AggregationPeriodCount = periodCount;
}
```

Update the `Restore` factory method to include `aggregationPeriodCount`:

```csharp
public static Measure Restore(
    // ... existing parameters ...
    int aggregationPeriodCount = 1)  // Add this parameter
{
    return new Measure
    {
        // ... existing assignments ...
        AggregationPeriodCount = aggregationPeriodCount
    };
}
```

---

## 📊 Usage Examples

```csharp
// 2-week measurement window
measure.ConfigureAggregation(
    AggregationType.Sum,
    AggregationPeriod.Weekly,
    DataNature.Aggregate,
    periodCount: 2);

// Monthly measurement (1 month)
measure.ConfigureAggregation(
    AggregationType.Sum,
    AggregationPeriod.Monthly,
    DataNature.Aggregate,
    periodCount: 1);

// Quarterly measurement (3 months using monthly base)
measure.ConfigureAggregation(
    AggregationType.Sum,
    AggregationPeriod.Monthly,
    DataNature.Aggregate,
    periodCount: 3);
```

---

## 📁 Files to Modify

| File | Action |
|------|--------|
| `PurposePath.Domain/Entities/Measure.cs` | Modify - add property and methods |

---

## 🧪 Testing

- [ ] AggregationPeriodCount defaults to 1
- [ ] SetAggregationPeriodCount validates count >= 1
- [ ] ConfigureAggregation accepts periodCount parameter
- [ ] Restore method includes aggregationPeriodCount

---

## 🔗 Dependencies

- None (independent change to existing entity)

---

## ✅ Definition of Done

- [ ] `AggregationPeriodCount` property added to Measure entity
- [ ] `SetAggregationPeriodCount` method added
- [ ] `ConfigureAggregation` updated with periodCount parameter
- [ ] `Restore` method updated
- [ ] Unit tests pass
- [ ] Code compiles without errors

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Added AggregationPeriodCount property
- [ ] Added SetAggregationPeriodCount method
- [ ] Updated ConfigureAggregation method
- [ ] Updated Restore method
- [ ] Added unit tests

**Notes:** [Any relevant notes]
```


