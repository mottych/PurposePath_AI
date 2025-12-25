# Issue #XXX-8: Application - KpiData Commands and Queries

**Parent Epic:** KPI Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `application`, `cqrs`, `kpi-data`  
**Estimated Effort:** 10-12 hours

---

## 📋 Description

Implement the application layer commands and queries for KpiData operations, including creating/updating targets and actuals with support for subtypes.

---

## 🏗️ Implementation Details

### Commands to Create

#### 1. CreateKpiTargetCommand

Location: `PurposePath.Application/Commands/KpiData/CreateKpiTargetCommand.cs`

```csharp
public record CreateKpiTargetCommand : IRequest<CreateKpiTargetResult>
{
    public KpiLinkId KpiLinkId { get; init; } = null!;
    public TargetSubtype Subtype { get; init; }  // Expected, Optimal, Minimal
    public decimal TargetValue { get; init; }
    public string TargetDate { get; init; } = string.Empty;  // ISO 8601
    public string RecordedBy { get; init; } = string.Empty;
    
    // Optional
    public DateTime? PeriodStartDate { get; init; }
    public string? Label { get; init; }
    public int? ConfidenceLevel { get; init; }
    public string? Rationale { get; init; }
}

public record CreateKpiTargetResult
{
    public KpiDataId Id { get; init; } = null!;
    public bool Success { get; init; }
    public string? ErrorMessage { get; init; }
}
```

#### 2. CreateKpiActualCommand

Location: `PurposePath.Application/Commands/KpiData/CreateKpiActualCommand.cs`

```csharp
public record CreateKpiActualCommand : IRequest<CreateKpiActualResult>
{
    public KpiLinkId KpiLinkId { get; init; } = null!;
    public ActualSubtype Subtype { get; init; }  // Estimate, Measured
    public decimal Value { get; init; }
    public string MeasurementDate { get; init; } = string.Empty;  // ISO 8601
    public string RecordedBy { get; init; } = string.Empty;
    public DataSource DataSource { get; init; } = DataSource.Manual;
    
    // Optional
    public DateTime? PeriodStartDate { get; init; }
    public string? SourceReferenceId { get; init; }
}

public record CreateKpiActualResult
{
    public KpiDataId Id { get; init; } = null!;
    public bool Success { get; init; }
    
    // Calculated on-the-fly for response
    public decimal? ExpectedValue { get; init; }
    public decimal? Variance { get; init; }
    public decimal? VariancePercentage { get; init; }
    public bool SuggestsReplan { get; init; }
}
```

#### 3. UpdateKpiTargetsCommand (Batch update)

Location: `PurposePath.Application/Commands/KpiData/UpdateKpiTargetsCommand.cs`

```csharp
public record UpdateKpiTargetsCommand : IRequest<UpdateKpiTargetsResult>
{
    public KpiLinkId KpiLinkId { get; init; } = null!;
    public IEnumerable<TargetUpdateItem> Targets { get; init; } = Array.Empty<TargetUpdateItem>();
    public string UpdatedBy { get; init; } = string.Empty;
}

public record TargetUpdateItem
{
    public KpiDataId? Id { get; init; }  // Null for new targets
    public TargetSubtype Subtype { get; init; }
    public decimal TargetValue { get; init; }
    public string TargetDate { get; init; } = string.Empty;
    public string? Label { get; init; }
    public int? ConfidenceLevel { get; init; }
    public string? Rationale { get; init; }
}
```

#### 4. MarkActualAsReplanTriggerCommand

Location: `PurposePath.Application/Commands/KpiData/MarkActualAsReplanTriggerCommand.cs`

```csharp
public record MarkActualAsReplanTriggerCommand : IRequest<Unit>
{
    public KpiDataId ActualId { get; init; } = null!;
    public bool ThresholdExceeded { get; init; }
    public bool AutoAdjustmentApplied { get; init; }
}
```

### Queries to Create

#### 1. GetKpiTargetsQuery

Location: `PurposePath.Application/Queries/KpiData/GetKpiTargetsQuery.cs`

```csharp
public record GetKpiTargetsQuery : IRequest<GetKpiTargetsResult>
{
    public KpiLinkId KpiLinkId { get; init; } = null!;
    public TargetSubtype? Subtype { get; init; }  // Filter by subtype (optional)
    public DateTime? StartDate { get; init; }
    public DateTime? EndDate { get; init; }
}

public record GetKpiTargetsResult
{
    public IEnumerable<KpiTargetDto> Targets { get; init; } = Array.Empty<KpiTargetDto>();
}

public record KpiTargetDto
{
    public string Id { get; init; } = string.Empty;
    public string Subtype { get; init; } = string.Empty;  // Expected, Optimal, Minimal
    public decimal TargetValue { get; init; }
    public string TargetDate { get; init; } = string.Empty;
    public DateTime? PeriodStartDate { get; init; }
    public string? Label { get; init; }
    public int? ConfidenceLevel { get; init; }
    public string? Rationale { get; init; }
    public string RecordedBy { get; init; } = string.Empty;
    public DateTimeOffset RecordedAt { get; init; }
}
```

#### 2. GetKpiActualsQuery

Location: `PurposePath.Application/Queries/KpiData/GetKpiActualsQuery.cs`

```csharp
public record GetKpiActualsQuery : IRequest<GetKpiActualsResult>
{
    public KpiLinkId KpiLinkId { get; init; } = null!;
    public ActualSubtype? Subtype { get; init; }  // Filter by subtype (optional)
    public DateTime? StartDate { get; init; }
    public DateTime? EndDate { get; init; }
    public bool IncludeCalculatedFields { get; init; } = true;
}

public record GetKpiActualsResult
{
    public IEnumerable<KpiActualDto> Actuals { get; init; } = Array.Empty<KpiActualDto>();
}

public record KpiActualDto
{
    public string Id { get; init; } = string.Empty;
    public string Subtype { get; init; } = string.Empty;  // Estimate, Measured
    public decimal PostValue { get; init; }
    public string PostDate { get; init; } = string.Empty;
    public DateTime? PeriodStartDate { get; init; }
    public string DataSource { get; init; } = string.Empty;
    public string? SourceReferenceId { get; init; }
    
    // Override info
    public bool IsManualOverride { get; init; }
    public decimal? OriginalValue { get; init; }
    public string? OverrideComment { get; init; }
    
    // Replan triggers
    public bool TriggersReplan { get; init; }
    public bool ReplanThresholdExceeded { get; init; }
    
    // Calculated fields (computed on-the-fly)
    public decimal? ExpectedValue { get; init; }
    public decimal? Variance { get; init; }
    public decimal? VariancePercentage { get; init; }
    
    public string RecordedBy { get; init; } = string.Empty;
    public DateTimeOffset RecordedAt { get; init; }
}
```

#### 3. GetKpiPlanningDataQuery (Combined targets + actuals)

Location: `PurposePath.Application/Queries/KpiData/GetKpiPlanningDataQuery.cs`

```csharp
public record GetKpiPlanningDataQuery : IRequest<GetKpiPlanningDataResult>
{
    public KpiLinkId KpiLinkId { get; init; } = null!;
    public DateTime? StartDate { get; init; }
    public DateTime? EndDate { get; init; }
}

public record GetKpiPlanningDataResult
{
    public KpiLinkDto Link { get; init; } = null!;
    
    // Target series (for graph lines)
    public IEnumerable<KpiTargetDto> ExpectedTargets { get; init; } = Array.Empty<KpiTargetDto>();
    public IEnumerable<KpiTargetDto> OptimalTargets { get; init; } = Array.Empty<KpiTargetDto>();
    public IEnumerable<KpiTargetDto> MinimalTargets { get; init; } = Array.Empty<KpiTargetDto>();
    
    // Actual series
    public IEnumerable<KpiActualDto> Actuals { get; init; } = Array.Empty<KpiActualDto>();
    
    // Summary
    public decimal? LatestActualValue { get; init; }
    public string? LatestActualDate { get; init; }
    public decimal? CurrentVariance { get; init; }
    public decimal? CurrentVariancePercentage { get; init; }
    public string? PerformanceStatus { get; init; }  // "on_track", "at_risk", "off_track"
}
```

### Calculation Service

Location: `PurposePath.Application/Services/KpiVarianceCalculationService.cs`

```csharp
public interface IKpiVarianceCalculationService
{
    /// <summary>
    /// Calculate expected value at a given date based on targets
    /// </summary>
    decimal? CalculateExpectedValue(
        IEnumerable<KpiData> targets,
        string measurementDate,
        InterpolationMethod interpolationMethod);

    /// <summary>
    /// Calculate variance and percentage
    /// </summary>
    (decimal? Variance, decimal? VariancePercentage) CalculateVariance(
        decimal actualValue,
        decimal? expectedValue,
        KpiDirection direction);

    /// <summary>
    /// Determine if replan is suggested based on variance
    /// </summary>
    bool ShouldSuggestReplan(
        decimal? variancePercentage,
        decimal thresholdPct);
}
```

---

## 📁 Files to Create/Modify

### Commands
| File | Action |
|------|--------|
| `PurposePath.Application/Commands/KpiData/CreateKpiTargetCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiData/CreateKpiActualCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiData/UpdateKpiTargetsCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiData/UpdateKpiActualCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiData/DeleteKpiDataCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiData/MarkActualAsReplanTriggerCommand.cs` | Create |

### Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Commands/KpiData/*.cs` | Create (one per command) |

### Queries
| File | Action |
|------|--------|
| `PurposePath.Application/Queries/KpiData/GetKpiTargetsQuery.cs` | Create |
| `PurposePath.Application/Queries/KpiData/GetKpiActualsQuery.cs` | Create |
| `PurposePath.Application/Queries/KpiData/GetKpiPlanningDataQuery.cs` | Create |
| `PurposePath.Application/Queries/KpiData/GetLatestActualQuery.cs` | Create |

### Query Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Queries/KpiData/*.cs` | Create (one per query) |

### Services
| File | Action |
|------|--------|
| `PurposePath.Application/Services/IKpiVarianceCalculationService.cs` | Create |
| `PurposePath.Application/Services/KpiVarianceCalculationService.cs` | Create |

### Validators
| File | Action |
|------|--------|
| `PurposePath.Application/Validators/KpiData/*.cs` | Create |

---

## 🧪 Testing

### Target Tests
- [ ] Create Expected target
- [ ] Create Optimal target
- [ ] Create Minimal target
- [ ] Batch update targets
- [ ] Get targets by subtype
- [ ] Get targets by date range

### Actual Tests
- [ ] Create Estimate actual
- [ ] Create Measured actual
- [ ] Measured wins over Estimate for same date
- [ ] Get actuals with calculated variance
- [ ] Mark as replan trigger

### Calculation Tests
- [ ] Expected value interpolation (linear)
- [ ] Expected value interpolation (exponential)
- [ ] Expected value interpolation (step)
- [ ] Variance calculation (positive direction)
- [ ] Variance calculation (negative direction)
- [ ] Replan suggestion based on threshold

---

## 🔗 Dependencies

- Issue #XXX-6: KpiData infrastructure (repository)
- Issue #XXX-7: KpiLink application (for link validation)

---

## ✅ Definition of Done

- [ ] All target commands and handlers implemented
- [ ] All actual commands and handlers implemented
- [ ] All queries and handlers implemented
- [ ] Variance calculation service implemented
- [ ] Validators created
- [ ] Unit tests pass
- [ ] Calculated fields computed correctly on-the-fly

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created target commands and handlers
- [ ] Created actual commands and handlers
- [ ] Created queries and handlers
- [ ] Created variance calculation service
- [ ] Created validators
- [ ] Added unit tests

**Notes:** [Any relevant notes]
```


