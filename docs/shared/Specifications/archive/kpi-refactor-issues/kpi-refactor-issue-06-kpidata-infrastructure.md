# Issue #XXX-6: Infrastructure - MeasureData Data Model, Mapper, Repository

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `infrastructure`, `data-model`, `repository`, `measure-data`  
**Estimated Effort:** 8-10 hours

---

## 📋 Description

Implement the infrastructure layer components for the new `MeasureData` entity, including DynamoDB data model, mapper, and repository.

---

## 🏗️ Implementation Details

### 1. Data Model

Location: `PurposePath.Infrastructure/DataModels/MeasureDataDataModel.cs`

```csharp
using Amazon.DynamoDBv2.DataModel;

namespace PurposePath.Infrastructure.DataModels;

[DynamoDBTable("purposepath-measure-data")]
public class MeasureDataDataModel : BaseDataModel
{
    [DynamoDBHashKey("id")]
    public string Id { get; set; } = string.Empty;

    [DynamoDBProperty("measure_link_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("measure-link-index")]
    public string MeasureLinkId { get; set; } = string.Empty;

    // Data classification
    [DynamoDBProperty("data_category")]
    public string DataCategory { get; set; } = string.Empty;  // "Target" or "Actual"

    [DynamoDBProperty("target_subtype")]
    public string? TargetSubtype { get; set; }  // "Expected", "Optimal", "Minimal"

    [DynamoDBProperty("actual_subtype")]
    public string? ActualSubtype { get; set; }  // "Estimate", "Measured"

    // Core values
    [DynamoDBProperty("post_value")]
    public decimal PostValue { get; set; }

    [DynamoDBProperty("post_date")]
    [DynamoDBGlobalSecondaryIndexRangeKey("measure-link-index")]
    public string PostDate { get; set; } = string.Empty;

    [DynamoDBProperty("measured_period_start_date")]
    public string? MeasuredPeriodStartDate { get; set; }

    // Target metadata
    [DynamoDBProperty("label")]
    public string? Label { get; set; }

    [DynamoDBProperty("confidence_level")]
    public int? ConfidenceLevel { get; set; }

    [DynamoDBProperty("rationale")]
    public string? Rationale { get; set; }

    // Override tracking
    [DynamoDBProperty("original_value")]
    public decimal? OriginalValue { get; set; }

    [DynamoDBProperty("is_manual_override")]
    public bool IsManualOverride { get; set; }

    [DynamoDBProperty("override_comment")]
    public string? OverrideComment { get; set; }

    // Source tracking
    [DynamoDBProperty("data_source")]
    public string DataSource { get; set; } = string.Empty;

    [DynamoDBProperty("source_reference_id")]
    public string? SourceReferenceId { get; set; }

    // Replan triggers
    [DynamoDBProperty("triggers_replan")]
    public bool TriggersReplan { get; set; }

    [DynamoDBProperty("replan_threshold_exceeded")]
    public bool ReplanThresholdExceeded { get; set; }

    [DynamoDBProperty("auto_adjustment_applied")]
    public bool? AutoAdjustmentApplied { get; set; }

    // Audit
    [DynamoDBProperty("recorded_by")]
    public string RecordedBy { get; set; } = string.Empty;

    [DynamoDBProperty("recorded_at")]
    public string RecordedAt { get; set; } = string.Empty;

    [DynamoDBProperty("created_by")]
    public string CreatedBy { get; set; } = string.Empty;

    [DynamoDBProperty("created_at")]
    public string CreatedAt { get; set; } = string.Empty;

    [DynamoDBProperty("updated_by")]
    public string? UpdatedBy { get; set; }

    [DynamoDBProperty("updated_at")]
    public string? UpdatedAt { get; set; }

    // Composite index for querying by category
    [DynamoDBGlobalSecondaryIndexHashKey("measure-link-category-index")]
    public string MeasureLinkCategoryKey => $"{MeasureLinkId}#{DataCategory}";

    // Composite index for querying targets by subtype
    [DynamoDBGlobalSecondaryIndexHashKey("target-subtype-index")]
    public string? TargetKey => DataCategory == "Target" ? $"{MeasureLinkId}#{TargetSubtype}" : null;
}
```

### 2. GSI Configuration

| GSI Name | Partition Key | Sort Key | Purpose |
|----------|---------------|----------|---------|
| `measure-link-index` | measure_link_id | post_date | Get all data for a link, sorted by date |
| `measure-link-category-index` | measure_link_id#data_category | - | Get targets or actuals for a link |
| `target-subtype-index` | measure_link_id#target_subtype | - | Get specific target type (Expected, Optimal, Minimal) |

### 3. Mapper

Location: `PurposePath.Infrastructure/Mappers/MeasureDataMapper.cs`

```csharp
using PurposePath.Domain.Common;
using PurposePath.Domain.Entities;
using PurposePath.Domain.ValueObjects;
using PurposePath.Infrastructure.DataModels;

namespace PurposePath.Infrastructure.Mappers;

public static class MeasureDataMapper
{
    public static MeasureDataDataModel ToDataModel(MeasureData entity)
    {
        return new MeasureDataDataModel
        {
            Id = entity.Id.ToString(),
            MeasureLinkId = entity.MeasureLinkId.ToString(),
            DataCategory = entity.DataCategory.ToString(),
            TargetSubtype = entity.TargetSubtype?.ToString(),
            ActualSubtype = entity.ActualSubtype?.ToString(),
            PostValue = entity.PostValue,
            PostDate = entity.PostDate,
            MeasuredPeriodStartDate = entity.MeasuredPeriodStartDate?.ToString("O"),
            Label = entity.Label,
            ConfidenceLevel = entity.ConfidenceLevel,
            Rationale = entity.Rationale,
            OriginalValue = entity.OriginalValue,
            IsManualOverride = entity.IsManualOverride,
            OverrideComment = entity.OverrideComment,
            DataSource = entity.DataSource.ToString(),
            SourceReferenceId = entity.SourceReferenceId,
            TriggersReplan = entity.TriggersReplan,
            ReplanThresholdExceeded = entity.ReplanThresholdExceeded,
            AutoAdjustmentApplied = entity.AutoAdjustmentApplied,
            RecordedBy = entity.RecordedBy,
            RecordedAt = entity.RecordedAt.ToString("O"),
            CreatedBy = entity.CreatedBy.ToString(),
            CreatedAt = entity.CreatedAt.ToString("O"),
            UpdatedBy = entity.UpdatedBy?.ToString(),
            UpdatedAt = entity.UpdatedAt?.ToString("O")
        };
    }

    public static MeasureData ToDomain(MeasureDataDataModel dataModel)
    {
        return MeasureData.Restore(
            id: MeasureDataId.From(dataModel.Id),
            measureLinkId: MeasureLinkId.From(dataModel.MeasureLinkId),
            dataCategory: Enum.Parse<MeasureDataCategory>(dataModel.DataCategory),
            targetSubtype: string.IsNullOrEmpty(dataModel.TargetSubtype) 
                ? null 
                : Enum.Parse<TargetSubtype>(dataModel.TargetSubtype),
            actualSubtype: string.IsNullOrEmpty(dataModel.ActualSubtype) 
                ? null 
                : Enum.Parse<ActualSubtype>(dataModel.ActualSubtype),
            postValue: dataModel.PostValue,
            postDate: dataModel.PostDate,
            measuredPeriodStartDate: string.IsNullOrEmpty(dataModel.MeasuredPeriodStartDate) 
                ? null 
                : DateTime.Parse(dataModel.MeasuredPeriodStartDate),
            label: dataModel.Label,
            confidenceLevel: dataModel.ConfidenceLevel,
            rationale: dataModel.Rationale,
            originalValue: dataModel.OriginalValue,
            isManualOverride: dataModel.IsManualOverride,
            overrideComment: dataModel.OverrideComment,
            dataSource: Enum.Parse<DataSource>(dataModel.DataSource),
            sourceReferenceId: dataModel.SourceReferenceId,
            triggersReplan: dataModel.TriggersReplan,
            replanThresholdExceeded: dataModel.ReplanThresholdExceeded,
            autoAdjustmentApplied: dataModel.AutoAdjustmentApplied,
            recordedBy: dataModel.RecordedBy,
            recordedAt: DateTimeOffset.Parse(dataModel.RecordedAt),
            createdBy: UserId.From(dataModel.CreatedBy),
            createdAt: DateTime.Parse(dataModel.CreatedAt),
            updatedBy: string.IsNullOrEmpty(dataModel.UpdatedBy) ? null : UserId.From(dataModel.UpdatedBy),
            updatedAt: string.IsNullOrEmpty(dataModel.UpdatedAt) ? null : DateTime.Parse(dataModel.UpdatedAt));
    }
}
```

### 4. Repository Interface

Location: `PurposePath.Domain/Repositories/IMeasureDataRepository.cs`

```csharp
using PurposePath.Domain.Entities;
using PurposePath.Domain.ValueObjects;

namespace PurposePath.Domain.Repositories;

public interface IMeasureDataRepository
{
    Task<MeasureData?> GetByIdAsync(MeasureDataId id, CancellationToken ct = default);
    
    // Get all data for a link
    Task<IEnumerable<MeasureData>> GetByMeasureLinkIdAsync(MeasureLinkId measureLinkId, CancellationToken ct = default);
    
    // Get targets for a link
    Task<IEnumerable<MeasureData>> GetTargetsAsync(MeasureLinkId measureLinkId, CancellationToken ct = default);
    
    // Get specific target type
    Task<IEnumerable<MeasureData>> GetTargetsBySubtypeAsync(
        MeasureLinkId measureLinkId, 
        TargetSubtype subtype, 
        CancellationToken ct = default);
    
    // Get actuals for a link
    Task<IEnumerable<MeasureData>> GetActualsAsync(MeasureLinkId measureLinkId, CancellationToken ct = default);
    
    // Get actuals by subtype (Estimate or Measured)
    Task<IEnumerable<MeasureData>> GetActualsBySubtypeAsync(
        MeasureLinkId measureLinkId, 
        ActualSubtype subtype, 
        CancellationToken ct = default);
    
    // Get data within date range
    Task<IEnumerable<MeasureData>> GetByDateRangeAsync(
        MeasureLinkId measureLinkId, 
        DateTime startDate, 
        DateTime endDate, 
        CancellationToken ct = default);
    
    // Get latest actual (Measured wins over Estimate for same date)
    Task<MeasureData?> GetLatestActualAsync(MeasureLinkId measureLinkId, CancellationToken ct = default);
    
    // Get target for specific date
    Task<MeasureData?> GetTargetForDateAsync(
        MeasureLinkId measureLinkId, 
        TargetSubtype subtype, 
        string postDate, 
        CancellationToken ct = default);
    
    Task CreateAsync(MeasureData data, CancellationToken ct = default);
    Task UpdateAsync(MeasureData data, CancellationToken ct = default);
    Task DeleteAsync(MeasureDataId id, CancellationToken ct = default);
    Task DeleteByMeasureLinkIdAsync(MeasureLinkId measureLinkId, CancellationToken ct = default);
}
```

### 5. Repository Implementation

Location: `PurposePath.Infrastructure/Repositories/DynamoDbMeasureDataRepository.cs`

Implement all methods from the interface using DynamoDB queries with the defined GSIs.

---

## 📁 Files to Create/Modify

| File | Action |
|------|--------|
| `PurposePath.Infrastructure/DataModels/MeasureDataDataModel.cs` | Create |
| `PurposePath.Infrastructure/Mappers/MeasureDataMapper.cs` | Create |
| `PurposePath.Infrastructure/Repositories/DynamoDbMeasureDataRepository.cs` | Create |
| `PurposePath.Domain/Repositories/IMeasureDataRepository.cs` | Create |
| `PurposePath.Infrastructure/Configuration/DynamoDbSettings.cs` | Modify |
| `PurposePath.Infrastructure/ServiceCollectionExtensions.cs` | Modify |
| `Pulumi/DynamoDbStack.cs` | Modify - add table and GSIs |

---

## 🧪 Testing

### CRUD Tests
- [ ] Create target data point
- [ ] Create actual data point
- [ ] Retrieve by ID
- [ ] Update data point
- [ ] Delete data point

### Query Tests
- [ ] Get all data for MeasureLink
- [ ] Get only targets
- [ ] Get only actuals
- [ ] Get targets by subtype (Expected, Optimal, Minimal)
- [ ] Get actuals by subtype (Estimate, Measured)
- [ ] Get data by date range
- [ ] Get latest actual (with Measured priority)
- [ ] Get target for specific date

### Mapper Tests
- [ ] Correct enum serialization/deserialization
- [ ] Nullable fields handled correctly
- [ ] Date formats preserved

---

## 🔗 Dependencies

- Issue #XXX-3: MeasureData domain entity
- Issue #XXX-5: MeasureLink infrastructure (for MeasureLinkId)

---

## ✅ Definition of Done

- [ ] Data model created with correct DynamoDB attributes
- [ ] All GSIs defined and configured
- [ ] Mapper implemented with correct conversions
- [ ] Repository implemented with all query methods
- [ ] DynamoDB table and GSIs configured in Pulumi
- [ ] Repository registered in DI container
- [ ] Integration tests pass

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created MeasureDataDataModel
- [ ] Created MeasureDataMapper
- [ ] Created IMeasureDataRepository interface
- [ ] Created DynamoDbMeasureDataRepository
- [ ] Added table configuration
- [ ] Registered repository in DI
- [ ] Added Pulumi table definition
- [ ] Added integration tests

**Notes:** [Any relevant notes]
```


