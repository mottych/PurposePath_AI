# Issue #XXX-10: API - Update KPI Planning Endpoints

**Parent Epic:** KPI Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `api`, `controllers`, `kpi-data`  
**Estimated Effort:** 8-10 hours

---

## 📋 Description

Update the Traction Lambda API controllers and DTOs to support the new KpiData functionality, including targets with subtypes (Expected, Optimal, Minimal) and actuals with subtypes (Estimate, Measured).

---

## 🏗️ API Changes

### New/Updated Endpoints

| Method | Endpoint | Description | Change |
|--------|----------|-------------|--------|
| GET | `/kpi-links/{linkId}/targets` | Get all targets for a link | New endpoint |
| POST | `/kpi-links/{linkId}/targets` | Create target | New endpoint |
| PUT | `/kpi-links/{linkId}/targets` | Batch update targets | New endpoint |
| GET | `/kpi-links/{linkId}/actuals` | Get all actuals for a link | New endpoint |
| POST | `/kpi-links/{linkId}/actuals` | Record actual value | New endpoint |
| GET | `/kpi-links/{linkId}/planning` | Get combined planning data | New endpoint |

### Deprecated Endpoints (map to new)

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| GET `/kpi-planning/kpis/{id}/milestones` | GET `/kpi-links/{linkId}/targets` | Requires link ID |
| PUT `/kpi-planning/kpis/{id}/milestones` | PUT `/kpi-links/{linkId}/targets` | Requires link ID |
| GET `/kpi-planning/kpis/{id}/actuals` | GET `/kpi-links/{linkId}/actuals` | Requires link ID |
| POST `/kpi-planning/kpis/{id}/actuals` | POST `/kpi-links/{linkId}/actuals` | Requires link ID |
| GET `/kpi-planning/kpis/{id}/plan` | GET `/kpi-links/{linkId}/planning` | Requires link ID |

---

## 📋 Request/Response DTOs

### CreateKpiTargetRequest

Location: `DTOs/Requests/KpiData/CreateKpiTargetRequest.cs`

```csharp
public record CreateKpiTargetRequest
{
    /// <summary>
    /// Target subtype: Expected, Optimal, or Minimal
    /// </summary>
    [Required]
    public string Subtype { get; init; } = string.Empty;
    
    /// <summary>
    /// Target value
    /// </summary>
    [Required]
    public decimal TargetValue { get; init; }
    
    /// <summary>
    /// Target date (ISO 8601)
    /// </summary>
    [Required]
    public string TargetDate { get; init; } = string.Empty;
    
    /// <summary>
    /// Start date of measurement period (for aggregate KPIs)
    /// </summary>
    public string? PeriodStartDate { get; init; }
    
    /// <summary>
    /// Label for the target (e.g., "Q1 Target")
    /// </summary>
    public string? Label { get; init; }
    
    /// <summary>
    /// Confidence level (1-5)
    /// </summary>
    [Range(1, 5)]
    public int? ConfidenceLevel { get; init; }
    
    /// <summary>
    /// Rationale for the target value
    /// </summary>
    public string? Rationale { get; init; }
}
```

### BatchUpdateTargetsRequest

Location: `DTOs/Requests/KpiData/BatchUpdateTargetsRequest.cs`

```csharp
public record BatchUpdateTargetsRequest
{
    /// <summary>
    /// List of targets to create or update
    /// </summary>
    [Required]
    public IEnumerable<TargetItem> Targets { get; init; } = Array.Empty<TargetItem>();
}

public record TargetItem
{
    /// <summary>
    /// ID for existing target (null for new)
    /// </summary>
    public string? Id { get; init; }
    
    /// <summary>
    /// Target subtype: Expected, Optimal, or Minimal
    /// </summary>
    [Required]
    public string Subtype { get; init; } = string.Empty;
    
    /// <summary>
    /// Target value
    /// </summary>
    [Required]
    public decimal TargetValue { get; init; }
    
    /// <summary>
    /// Target date (ISO 8601)
    /// </summary>
    [Required]
    public string TargetDate { get; init; } = string.Empty;
    
    public string? Label { get; init; }
    public int? ConfidenceLevel { get; init; }
    public string? Rationale { get; init; }
}
```

### RecordActualRequest

Location: `DTOs/Requests/KpiData/RecordActualRequest.cs`

```csharp
public record RecordActualRequest
{
    /// <summary>
    /// Actual subtype: Estimate or Measured
    /// </summary>
    [Required]
    public string Subtype { get; init; } = string.Empty;
    
    /// <summary>
    /// Actual value
    /// </summary>
    [Required]
    public decimal Value { get; init; }
    
    /// <summary>
    /// Measurement date (ISO 8601)
    /// </summary>
    [Required]
    public string MeasurementDate { get; init; } = string.Empty;
    
    /// <summary>
    /// Start date of measurement period (for aggregate KPIs)
    /// </summary>
    public string? PeriodStartDate { get; init; }
    
    /// <summary>
    /// Data source: Manual, Integration, System, Import
    /// </summary>
    public string DataSource { get; init; } = "Manual";
    
    /// <summary>
    /// Reference ID for integration source
    /// </summary>
    public string? SourceReferenceId { get; init; }
}
```

### KpiTargetResponse

Location: `DTOs/Responses/KpiData/KpiTargetResponse.cs`

```csharp
public record KpiTargetResponse
{
    public string Id { get; init; } = string.Empty;
    public string Subtype { get; init; } = string.Empty;  // Expected, Optimal, Minimal
    public decimal TargetValue { get; init; }
    public string TargetDate { get; init; } = string.Empty;
    public string? PeriodStartDate { get; init; }
    public string? Label { get; init; }
    public int? ConfidenceLevel { get; init; }
    public string? Rationale { get; init; }
    public string RecordedBy { get; init; } = string.Empty;
    public string RecordedAt { get; init; } = string.Empty;
}
```

### KpiActualResponse

Location: `DTOs/Responses/KpiData/KpiActualResponse.cs`

```csharp
public record KpiActualResponse
{
    public string Id { get; init; } = string.Empty;
    public string Subtype { get; init; } = string.Empty;  // Estimate, Measured
    public decimal PostValue { get; init; }
    public string PostDate { get; init; } = string.Empty;
    public string? PeriodStartDate { get; init; }
    public string DataSource { get; init; } = string.Empty;
    public string? SourceReferenceId { get; init; }
    
    // Override info
    public bool IsManualOverride { get; init; }
    public decimal? OriginalValue { get; init; }
    public string? OverrideComment { get; init; }
    
    // Replan flags
    public bool TriggersReplan { get; init; }
    public bool ReplanThresholdExceeded { get; init; }
    
    // Calculated fields
    public decimal? ExpectedValue { get; init; }
    public decimal? Variance { get; init; }
    public decimal? VariancePercentage { get; init; }
    
    public string RecordedBy { get; init; } = string.Empty;
    public string RecordedAt { get; init; } = string.Empty;
}
```

### KpiPlanningResponse

Location: `DTOs/Responses/KpiData/KpiPlanningResponse.cs`

```csharp
public record KpiPlanningResponse
{
    public KpiLinkResponse Link { get; init; } = null!;
    
    // Target series for graphing
    public TargetSeriesResponse ExpectedSeries { get; init; } = null!;
    public TargetSeriesResponse? OptimalSeries { get; init; }
    public TargetSeriesResponse? MinimalSeries { get; init; }
    
    // Actual data
    public IEnumerable<KpiActualResponse> Actuals { get; init; } = Array.Empty<KpiActualResponse>();
    
    // Summary
    public decimal? LatestActualValue { get; init; }
    public string? LatestActualDate { get; init; }
    public decimal? CurrentExpectedValue { get; init; }
    public decimal? CurrentVariance { get; init; }
    public decimal? CurrentVariancePercentage { get; init; }
    public string Status { get; init; } = string.Empty;  // on_track, at_risk, off_track, achieved
}

public record TargetSeriesResponse
{
    public string Subtype { get; init; } = string.Empty;
    public IEnumerable<KpiTargetResponse> Points { get; init; } = Array.Empty<KpiTargetResponse>();
}
```

---

## 🎮 Controller Implementation

Location: `Services/PurposePath.Traction.Lambda/Controllers/KpiDataController.cs`

```csharp
[ApiController]
[Route("kpi-links/{linkId}")]
public class KpiDataController : ControllerBase
{
    private readonly IMediator _mediator;

    public KpiDataController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Get targets for a KPI link
    /// </summary>
    [HttpGet("targets")]
    [ProducesResponseType(typeof(ApiResponse<IEnumerable<KpiTargetResponse>>), 200)]
    public async Task<IActionResult> GetTargets(
        string linkId,
        [FromQuery] string? subtype,
        [FromQuery] string? startDate,
        [FromQuery] string? endDate,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Create a target for a KPI link
    /// </summary>
    [HttpPost("targets")]
    [ProducesResponseType(typeof(ApiResponse<KpiTargetResponse>), 201)]
    public async Task<IActionResult> CreateTarget(
        string linkId,
        [FromBody] CreateKpiTargetRequest request,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Batch update targets for a KPI link
    /// </summary>
    [HttpPut("targets")]
    [ProducesResponseType(typeof(ApiResponse<IEnumerable<KpiTargetResponse>>), 200)]
    public async Task<IActionResult> UpdateTargets(
        string linkId,
        [FromBody] BatchUpdateTargetsRequest request,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Get actuals for a KPI link
    /// </summary>
    [HttpGet("actuals")]
    [ProducesResponseType(typeof(ApiResponse<IEnumerable<KpiActualResponse>>), 200)]
    public async Task<IActionResult> GetActuals(
        string linkId,
        [FromQuery] string? subtype,
        [FromQuery] string? startDate,
        [FromQuery] string? endDate,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Record an actual value
    /// </summary>
    [HttpPost("actuals")]
    [ProducesResponseType(typeof(ApiResponse<KpiActualResponse>), 201)]
    public async Task<IActionResult> RecordActual(
        string linkId,
        [FromBody] RecordActualRequest request,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Get combined planning data
    /// </summary>
    [HttpGet("planning")]
    [ProducesResponseType(typeof(ApiResponse<KpiPlanningResponse>), 200)]
    public async Task<IActionResult> GetPlanningData(
        string linkId,
        [FromQuery] string? startDate,
        [FromQuery] string? endDate,
        CancellationToken ct)
    {
        // Implementation
    }
}
```

---

## 📁 Files to Create/Modify

### DTOs
| File | Action |
|------|--------|
| `DTOs/Requests/KpiData/CreateKpiTargetRequest.cs` | Create |
| `DTOs/Requests/KpiData/BatchUpdateTargetsRequest.cs` | Create |
| `DTOs/Requests/KpiData/RecordActualRequest.cs` | Create |
| `DTOs/Responses/KpiData/KpiTargetResponse.cs` | Create |
| `DTOs/Responses/KpiData/KpiActualResponse.cs` | Create |
| `DTOs/Responses/KpiData/KpiPlanningResponse.cs` | Create |

### Controllers
| File | Action |
|------|--------|
| `Controllers/KpiDataController.cs` | Create |
| `Controllers/KpiPlanningController.cs` | Modify - add deprecation notices |

### Validators
| File | Action |
|------|--------|
| `Validators/KpiData/CreateKpiTargetRequestValidator.cs` | Create |
| `Validators/KpiData/RecordActualRequestValidator.cs` | Create |
| `Validators/KpiData/BatchUpdateTargetsRequestValidator.cs` | Create |

### Mappers
| File | Action |
|------|--------|
| `Mappers/TractionLambdaMappingProfile.cs` | Modify - add KpiData mappings |

---

## 🧪 Testing

### Target Endpoint Tests
- [ ] GET targets - all subtypes
- [ ] GET targets - filter by subtype
- [ ] GET targets - filter by date range
- [ ] POST target - Expected
- [ ] POST target - Optimal
- [ ] POST target - Minimal
- [ ] POST target - validation errors
- [ ] PUT targets - batch update

### Actual Endpoint Tests
- [ ] GET actuals - all subtypes
- [ ] GET actuals - filter by subtype (Estimate/Measured)
- [ ] GET actuals - filter by date range
- [ ] POST actual - Estimate
- [ ] POST actual - Measured
- [ ] POST actual - includes calculated variance
- [ ] POST actual - triggers replan warning

### Planning Endpoint Tests
- [ ] GET planning - returns all series
- [ ] GET planning - calculates current variance
- [ ] GET planning - determines status correctly

---

## 🔗 Dependencies

- Issue #XXX-8: KpiData application layer

---

## ✅ Definition of Done

- [ ] All new endpoints implemented
- [ ] DTOs created with proper validation
- [ ] Controllers implemented
- [ ] Validators created
- [ ] Mapper profiles updated
- [ ] OpenAPI documentation generated
- [ ] API tests pass
- [ ] Variance calculated on-the-fly in responses
- [ ] Backward compatibility with deprecation notices

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created request DTOs
- [ ] Created response DTOs
- [ ] Created KpiDataController
- [ ] Created validators
- [ ] Updated mapper profiles
- [ ] Added API tests
- [ ] Updated OpenAPI documentation

**Notes:** [Any relevant notes]
```


