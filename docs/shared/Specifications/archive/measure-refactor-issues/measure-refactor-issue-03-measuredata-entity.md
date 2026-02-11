# Issue #XXX-3: Domain - Create MeasureData Entity

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `domain`, `entity`, `measure-data`  
**Estimated Effort:** 6-8 hours

---

## 📋 Description

Create the unified `MeasureData` entity that consolidates `MeasureActual`, `MeasureMilestone`, and `MeasureReading` into a single table supporting both target and actual values with subtypes.

---

## 🏗️ Entity Design

### MeasureData Entity

Location: `PurposePath.Domain/Entities/MeasureData.cs`

```csharp
using PurposePath.Domain.Common;
using PurposePath.Domain.Events;
using PurposePath.Domain.ValueObjects;

namespace PurposePath.Domain.Entities;

/// <summary>
/// Unified entity for Measure target and actual values.
/// Replaces MeasureActual, MeasureMilestone, and MeasureReading.
/// </summary>
public class MeasureData : FullyAuditableEntity
{
    public MeasureDataId Id { get; private set; }
    public MeasureLinkId MeasureLinkId { get; private set; }
    
    // Data classification
    public MeasureDataCategory DataCategory { get; private set; }
    public TargetSubtype? TargetSubtype { get; private set; }
    public ActualSubtype? ActualSubtype { get; private set; }
    
    // Core values
    public decimal PostValue { get; private set; }
    public string PostDate { get; private set; }  // ISO 8601 date string
    public DateTime? MeasuredPeriodStartDate { get; private set; }  // For aggregate Measures
    
    // Target metadata (from MeasureMilestone)
    public string? Label { get; private set; }
    public int? ConfidenceLevel { get; private set; }  // 1-5
    public string? Rationale { get; private set; }
    
    // Override tracking (from MeasureActual)
    public decimal? OriginalValue { get; private set; }
    public bool IsManualOverride { get; private set; }
    public string? OverrideComment { get; private set; }
    
    // Source tracking (from MeasureActual)
    public DataSource DataSource { get; private set; }
    public string? SourceReferenceId { get; private set; }
    
    // Replan triggers (from MeasureActual)
    public bool TriggersReplan { get; private set; }
    public bool ReplanThresholdExceeded { get; private set; }
    public bool? AutoAdjustmentApplied { get; private set; }
    
    // Audit
    public string RecordedBy { get; private set; }
    public DateTimeOffset RecordedAt { get; private set; }

    private MeasureData()
    {
        Id = null!;
        MeasureLinkId = null!;
        PostDate = null!;
        RecordedBy = null!;
    }

    #region Factory Methods for Targets

    /// <summary>
    /// Create an Expected target (primary target)
    /// </summary>
    public static MeasureData CreateExpectedTarget(
        MeasureLinkId kpiLinkId,
        decimal targetValue,
        string targetDate,
        string recordedBy,
        DateTime? periodStartDate = null,
        string? label = null,
        int? confidenceLevel = null,
        string? rationale = null)
    {
        return CreateTarget(kpiLinkId, TargetSubtype.Expected, targetValue, targetDate, 
            recordedBy, periodStartDate, label, confidenceLevel, rationale);
    }

    /// <summary>
    /// Create an Optimal target (stretch goal)
    /// </summary>
    public static MeasureData CreateOptimalTarget(
        MeasureLinkId kpiLinkId,
        decimal targetValue,
        string targetDate,
        string recordedBy,
        DateTime? periodStartDate = null,
        string? label = null,
        int? confidenceLevel = null,
        string? rationale = null)
    {
        return CreateTarget(kpiLinkId, TargetSubtype.Optimal, targetValue, targetDate,
            recordedBy, periodStartDate, label, confidenceLevel, rationale);
    }

    /// <summary>
    /// Create a Minimal target (floor/threshold)
    /// </summary>
    public static MeasureData CreateMinimalTarget(
        MeasureLinkId kpiLinkId,
        decimal targetValue,
        string targetDate,
        string recordedBy,
        DateTime? periodStartDate = null,
        string? label = null,
        int? confidenceLevel = null,
        string? rationale = null)
    {
        return CreateTarget(kpiLinkId, TargetSubtype.Minimal, targetValue, targetDate,
            recordedBy, periodStartDate, label, confidenceLevel, rationale);
    }

    private static MeasureData CreateTarget(
        MeasureLinkId kpiLinkId,
        TargetSubtype targetSubtype,
        decimal targetValue,
        string targetDate,
        string recordedBy,
        DateTime? periodStartDate,
        string? label,
        int? confidenceLevel,
        string? rationale)
    {
        ValidateDate(targetDate);
        ValidateConfidenceLevel(confidenceLevel);
        ValidateRecordedBy(recordedBy);

        var data = new MeasureData
        {
            Id = MeasureDataId.New(),
            MeasureLinkId = kpiLinkId ?? throw new ArgumentNullException(nameof(kpiLinkId)),
            DataCategory = MeasureDataCategory.Target,
            TargetSubtype = targetSubtype,
            ActualSubtype = null,
            PostValue = targetValue,
            PostDate = targetDate.Trim(),
            MeasuredPeriodStartDate = periodStartDate,
            Label = label?.Trim(),
            ConfidenceLevel = confidenceLevel,
            Rationale = rationale?.Trim(),
            DataSource = DataSource.Manual,
            RecordedBy = recordedBy.Trim(),
            RecordedAt = DateTimeOffset.UtcNow
        };

        data.AddDomainEvent(new MeasureTargetCreatedEvent(
            data.Id, data.MeasureLinkId, targetSubtype, targetValue, targetDate));

        return data;
    }

    #endregion

    #region Factory Methods for Actuals

    /// <summary>
    /// Create an Estimated actual (forecast/estimate)
    /// </summary>
    public static MeasureData CreateEstimate(
        MeasureLinkId kpiLinkId,
        decimal estimatedValue,
        string measurementDate,
        string recordedBy,
        DataSource dataSource = DataSource.Manual,
        DateTime? periodStartDate = null,
        string? sourceReferenceId = null)
    {
        return CreateActual(kpiLinkId, ActualSubtype.Estimate, estimatedValue, measurementDate,
            recordedBy, dataSource, periodStartDate, sourceReferenceId);
    }

    /// <summary>
    /// Create a Measured actual (recorded value)
    /// </summary>
    public static MeasureData CreateMeasured(
        MeasureLinkId kpiLinkId,
        decimal measuredValue,
        string measurementDate,
        string recordedBy,
        DataSource dataSource = DataSource.Manual,
        DateTime? periodStartDate = null,
        string? sourceReferenceId = null)
    {
        return CreateActual(kpiLinkId, ActualSubtype.Measured, measuredValue, measurementDate,
            recordedBy, dataSource, periodStartDate, sourceReferenceId);
    }

    private static MeasureData CreateActual(
        MeasureLinkId kpiLinkId,
        ActualSubtype actualSubtype,
        decimal value,
        string measurementDate,
        string recordedBy,
        DataSource dataSource,
        DateTime? periodStartDate,
        string? sourceReferenceId)
    {
        ValidateDate(measurementDate);
        ValidateRecordedBy(recordedBy);

        var data = new MeasureData
        {
            Id = MeasureDataId.New(),
            MeasureLinkId = kpiLinkId ?? throw new ArgumentNullException(nameof(kpiLinkId)),
            DataCategory = MeasureDataCategory.Actual,
            TargetSubtype = null,
            ActualSubtype = actualSubtype,
            PostValue = value,
            PostDate = measurementDate.Trim(),
            MeasuredPeriodStartDate = periodStartDate,
            DataSource = dataSource,
            SourceReferenceId = sourceReferenceId?.Trim(),
            RecordedBy = recordedBy.Trim(),
            RecordedAt = DateTimeOffset.UtcNow,
            IsManualOverride = false,
            TriggersReplan = false,
            ReplanThresholdExceeded = false
        };

        data.AddDomainEvent(new MeasureActualRecordedEvent(
            data.Id, data.MeasureLinkId, actualSubtype, value, measurementDate, dataSource));

        return data;
    }

    #endregion

    #region Update Methods

    /// <summary>
    /// Update target value
    /// </summary>
    public void UpdateTargetValue(decimal newValue, string? rationale = null)
    {
        if (DataCategory != MeasureDataCategory.Target)
            throw new InvalidOperationException("Can only update target value for Target data");

        var previousValue = PostValue;
        PostValue = newValue;
        
        if (!string.IsNullOrWhiteSpace(rationale))
            Rationale = rationale.Trim();
        
        UpdatedAt = DateTime.UtcNow;

        AddDomainEvent(new MeasureTargetUpdatedEvent(Id, MeasureLinkId, previousValue, newValue));
    }

    /// <summary>
    /// Update actual value with optional override tracking
    /// </summary>
    public void UpdateActualValue(decimal newValue, string? overrideComment = null)
    {
        if (DataCategory != MeasureDataCategory.Actual)
            throw new InvalidOperationException("Can only update actual value for Actual data");

        if (!IsManualOverride && overrideComment != null)
        {
            OriginalValue = PostValue;
            IsManualOverride = true;
        }

        PostValue = newValue;
        OverrideComment = overrideComment?.Trim();
        RecordedAt = DateTimeOffset.UtcNow;
        UpdatedAt = DateTime.UtcNow;
    }

    /// <summary>
    /// Set confidence level for targets
    /// </summary>
    public void SetConfidenceLevel(int confidenceLevel)
    {
        ValidateConfidenceLevel(confidenceLevel);
        ConfidenceLevel = confidenceLevel;
        UpdatedAt = DateTime.UtcNow;
    }

    /// <summary>
    /// Mark this actual as triggering a replan
    /// </summary>
    public void MarkAsReplanTrigger(bool thresholdExceeded, bool autoAdjustmentApplied)
    {
        if (DataCategory != MeasureDataCategory.Actual)
            throw new InvalidOperationException("Can only mark Actual data as replan trigger");

        TriggersReplan = true;
        ReplanThresholdExceeded = thresholdExceeded;
        AutoAdjustmentApplied = autoAdjustmentApplied;
        UpdatedAt = DateTime.UtcNow;
    }

    #endregion

    #region Restore Method

    /// <summary>
    /// Factory method to restore MeasureData from persistence
    /// </summary>
    public static MeasureData Restore(
        MeasureDataId id,
        MeasureLinkId kpiLinkId,
        MeasureDataCategory dataCategory,
        TargetSubtype? targetSubtype,
        ActualSubtype? actualSubtype,
        decimal postValue,
        string postDate,
        DateTime? measuredPeriodStartDate,
        string? label,
        int? confidenceLevel,
        string? rationale,
        decimal? originalValue,
        bool isManualOverride,
        string? overrideComment,
        DataSource dataSource,
        string? sourceReferenceId,
        bool triggersReplan,
        bool replanThresholdExceeded,
        bool? autoAdjustmentApplied,
        string recordedBy,
        DateTimeOffset recordedAt,
        UserId createdBy,
        DateTime createdAt,
        UserId? updatedBy,
        DateTime? updatedAt)
    {
        return new MeasureData
        {
            Id = id,
            MeasureLinkId = kpiLinkId,
            DataCategory = dataCategory,
            TargetSubtype = targetSubtype,
            ActualSubtype = actualSubtype,
            PostValue = postValue,
            PostDate = postDate,
            MeasuredPeriodStartDate = measuredPeriodStartDate,
            Label = label,
            ConfidenceLevel = confidenceLevel,
            Rationale = rationale,
            OriginalValue = originalValue,
            IsManualOverride = isManualOverride,
            OverrideComment = overrideComment,
            DataSource = dataSource,
            SourceReferenceId = sourceReferenceId,
            TriggersReplan = triggersReplan,
            ReplanThresholdExceeded = replanThresholdExceeded,
            AutoAdjustmentApplied = autoAdjustmentApplied,
            RecordedBy = recordedBy,
            RecordedAt = recordedAt,
            CreatedBy = createdBy,
            CreatedAt = createdAt,
            UpdatedBy = updatedBy,
            UpdatedAt = updatedAt
        };
    }

    #endregion

    #region Validation

    private static void ValidateDate(string dateString)
    {
        if (string.IsNullOrWhiteSpace(dateString))
            throw new ArgumentException("Date cannot be empty", nameof(dateString));

        if (!DateTime.TryParse(dateString, null, System.Globalization.DateTimeStyles.RoundtripKind, out _))
            throw new ArgumentException("Date must be valid ISO 8601 format", nameof(dateString));
    }

    private static void ValidateConfidenceLevel(int? confidenceLevel)
    {
        if (confidenceLevel.HasValue && (confidenceLevel.Value < 1 || confidenceLevel.Value > 5))
            throw new ArgumentException("Confidence level must be between 1 and 5", nameof(confidenceLevel));
    }

    private static void ValidateRecordedBy(string recordedBy)
    {
        if (string.IsNullOrWhiteSpace(recordedBy))
            throw new ArgumentException("RecordedBy cannot be empty", nameof(recordedBy));
    }

    #endregion
}
```

---

## 📁 Files to Create/Modify

| File | Action |
|------|--------|
| `PurposePath.Domain/Entities/MeasureData.cs` | Create |
| `PurposePath.Domain/Events/MeasureTargetCreatedEvent.cs` | Create |
| `PurposePath.Domain/Events/MeasureTargetUpdatedEvent.cs` | Create |
| `PurposePath.Domain/Events/MeasureActualRecordedEvent.cs` | Update (add ActualSubtype) |
| `PurposePath.Domain/Repositories/IMeasureDataRepository.cs` | Create |

---

## 🧪 Testing

### Target Tests
- [ ] Create Expected target
- [ ] Create Optimal target
- [ ] Create Minimal target
- [ ] Update target value
- [ ] Set confidence level (validation 1-5)

### Actual Tests
- [ ] Create Estimate actual
- [ ] Create Measured actual
- [ ] Update actual with override
- [ ] Mark as replan trigger

### Validation Tests
- [ ] Invalid date format throws exception
- [ ] Invalid confidence level throws exception
- [ ] Empty recordedBy throws exception
- [ ] Cannot update target value on Actual data
- [ ] Cannot mark Target data as replan trigger

---

## 🔗 Dependencies

- Issue #XXX-1: Domain enums and value objects (`MeasureDataId`, `MeasureDataCategory`, etc.)
- Issue #XXX-2: MeasureLink entity (`MeasureLinkId`)

---

## ✅ Definition of Done

- [ ] `MeasureData` entity created with all properties and methods
- [ ] Factory methods for all target and actual types
- [ ] Repository interface `IMeasureDataRepository` created
- [ ] Domain events created/updated
- [ ] Unit tests pass
- [ ] Code compiles without errors

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created MeasureData entity
- [ ] Created target factory methods
- [ ] Created actual factory methods
- [ ] Created IMeasureDataRepository interface
- [ ] Created/updated domain events
- [ ] Added unit tests

**Notes:** [Any relevant notes]
```


