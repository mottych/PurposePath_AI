# Issue #XXX-9: API - Update KPI Linking Endpoints

**Parent Epic:** KPI Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `api`, `controllers`, `kpi-link`  
**Estimated Effort:** 6-8 hours

---

## 📋 Description

Update the Traction Lambda API controllers and DTOs to support the new KpiLink functionality, including linking to Person, Goal, and Strategy.

---

## 🏗️ API Changes

### New/Updated Endpoints

| Method | Endpoint | Description | Change |
|--------|----------|-------------|--------|
| POST | `/kpi-links` | Create KPI link | New endpoint |
| GET | `/kpi-links` | List KPI links with filters | New endpoint |
| GET | `/kpi-links/{id}` | Get link details | New endpoint |
| PUT | `/kpi-links/{id}` | Update link metadata | New endpoint |
| DELETE | `/kpi-links/{id}` | Remove link | New endpoint |
| GET | `/goals/{goalId}/kpi-links` | Get links for goal | New endpoint |
| GET | `/strategies/{strategyId}/kpi-links` | Get links for strategy | New endpoint |
| GET | `/people/{personId}/kpi-links` | Get personal scorecards | New endpoint |

### Deprecated Endpoints (redirect to new)

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| POST `/goals/{goalId}/kpis:link` | POST `/kpi-links` | Add goalId in body |
| POST `/goals/{goalId}/kpis:unlink` | DELETE `/kpi-links/{id}` | Use link ID |
| GET `/goals/{goalId}/kpis` | GET `/goals/{goalId}/kpi-links` | Returns links with KPI data |

---

## 📋 Request/Response DTOs

### CreateKpiLinkRequest

Location: `Services/PurposePath.Traction.Lambda/DTOs/Requests/KpiLink/CreateKpiLinkRequest.cs`

```csharp
public record CreateKpiLinkRequest
{
    /// <summary>
    /// ID of the KPI to link
    /// </summary>
    [Required]
    public string KpiId { get; init; } = string.Empty;
    
    /// <summary>
    /// ID of the person responsible for values on this link
    /// </summary>
    [Required]
    public string PersonId { get; init; } = string.Empty;
    
    /// <summary>
    /// Optional goal to link to
    /// </summary>
    public string? GoalId { get; init; }
    
    /// <summary>
    /// Optional strategy to link to (requires GoalId)
    /// </summary>
    public string? StrategyId { get; init; }
    
    /// <summary>
    /// Link type: "primary", "secondary", "supporting", "monitoring"
    /// </summary>
    public string? LinkType { get; init; }
    
    /// <summary>
    /// Importance weight (0.0 to 1.0)
    /// </summary>
    [Range(0, 1)]
    public decimal? Weight { get; init; }
    
    /// <summary>
    /// Display order for sorting
    /// </summary>
    public int? DisplayOrder { get; init; }
    
    /// <summary>
    /// Whether this is the primary KPI for the goal
    /// </summary>
    public bool IsPrimary { get; init; }
    
    /// <summary>
    /// Threshold percentage for variance alerts (0-100)
    /// </summary>
    [Range(0, 100)]
    public decimal? ThresholdPct { get; init; }
}
```

### KpiLinkResponse

Location: `Services/PurposePath.Traction.Lambda/DTOs/Responses/KpiLink/KpiLinkResponse.cs`

```csharp
public record KpiLinkResponse
{
    public string Id { get; init; } = string.Empty;
    public string KpiId { get; init; } = string.Empty;
    public string KpiName { get; init; } = string.Empty;
    public string KpiUnit { get; init; } = string.Empty;
    public string KpiDirection { get; init; } = string.Empty;
    
    public string PersonId { get; init; } = string.Empty;
    public string PersonName { get; init; } = string.Empty;
    
    public string? GoalId { get; init; }
    public string? GoalTitle { get; init; }
    
    public string? StrategyId { get; init; }
    public string? StrategyTitle { get; init; }
    
    public DateTime LinkedAt { get; init; }
    public string? LinkType { get; init; }
    public decimal? Weight { get; init; }
    public int? DisplayOrder { get; init; }
    public bool IsPrimary { get; init; }
    public decimal? ThresholdPct { get; init; }
    
    // Summary data
    public decimal? CurrentValue { get; init; }
    public string? CurrentValueDate { get; init; }
    public decimal? ExpectedValue { get; init; }
    public decimal? Variance { get; init; }
    public decimal? VariancePercentage { get; init; }
    public string? Status { get; init; }  // on_track, at_risk, off_track
}
```

### KpiLinkListResponse

```csharp
public record KpiLinkListResponse
{
    public IEnumerable<KpiLinkResponse> Items { get; init; } = Array.Empty<KpiLinkResponse>();
    public int TotalCount { get; init; }
}
```

---

## 🎮 Controller Implementation

Location: `Services/PurposePath.Traction.Lambda/Controllers/KpiLinksController.cs`

```csharp
[ApiController]
[Route("kpi-links")]
public class KpiLinksController : ControllerBase
{
    private readonly IMediator _mediator;

    public KpiLinksController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Create a new KPI link
    /// </summary>
    [HttpPost]
    [ProducesResponseType(typeof(ApiResponse<KpiLinkResponse>), 201)]
    [ProducesResponseType(typeof(ApiErrorResponse), 400)]
    [ProducesResponseType(typeof(ApiErrorResponse), 409)]
    public async Task<IActionResult> CreateLink(
        [FromBody] CreateKpiLinkRequest request,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Get KPI links with optional filtering
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(ApiResponse<KpiLinkListResponse>), 200)]
    public async Task<IActionResult> GetLinks(
        [FromQuery] string? kpiId,
        [FromQuery] string? goalId,
        [FromQuery] string? strategyId,
        [FromQuery] string? personId,
        [FromQuery] bool? personalOnly,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Get a specific KPI link
    /// </summary>
    [HttpGet("{id}")]
    [ProducesResponseType(typeof(ApiResponse<KpiLinkResponse>), 200)]
    [ProducesResponseType(typeof(ApiErrorResponse), 404)]
    public async Task<IActionResult> GetLink(string id, CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Update KPI link metadata
    /// </summary>
    [HttpPut("{id}")]
    [ProducesResponseType(typeof(ApiResponse<KpiLinkResponse>), 200)]
    [ProducesResponseType(typeof(ApiErrorResponse), 404)]
    public async Task<IActionResult> UpdateLink(
        string id,
        [FromBody] UpdateKpiLinkRequest request,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Delete a KPI link
    /// </summary>
    [HttpDelete("{id}")]
    [ProducesResponseType(204)]
    [ProducesResponseType(typeof(ApiErrorResponse), 404)]
    public async Task<IActionResult> DeleteLink(string id, CancellationToken ct)
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
| `DTOs/Requests/KpiLink/CreateKpiLinkRequest.cs` | Create |
| `DTOs/Requests/KpiLink/UpdateKpiLinkRequest.cs` | Create |
| `DTOs/Responses/KpiLink/KpiLinkResponse.cs` | Create |
| `DTOs/Responses/KpiLink/KpiLinkListResponse.cs` | Create |

### Controllers
| File | Action |
|------|--------|
| `Controllers/KpiLinksController.cs` | Create |
| `Controllers/GoalKpiController.cs` | Modify - add deprecation notices |

### Validators
| File | Action |
|------|--------|
| `Validators/KpiLink/CreateKpiLinkRequestValidator.cs` | Create |
| `Validators/KpiLink/UpdateKpiLinkRequestValidator.cs` | Create |

### Mappers
| File | Action |
|------|--------|
| `Mappers/TractionLambdaMappingProfile.cs` | Modify - add KpiLink mappings |

---

## 🧪 Testing

### API Tests
- [ ] POST /kpi-links - create with Person only
- [ ] POST /kpi-links - create with Person + Goal
- [ ] POST /kpi-links - create with Person + Goal + Strategy
- [ ] POST /kpi-links - validation error for Strategy without Goal
- [ ] POST /kpi-links - conflict for duplicate Goal link
- [ ] GET /kpi-links - filter by kpiId
- [ ] GET /kpi-links - filter by goalId
- [ ] GET /kpi-links - filter by personId
- [ ] GET /kpi-links - filter personalOnly=true
- [ ] GET /kpi-links/{id} - success
- [ ] GET /kpi-links/{id} - not found
- [ ] PUT /kpi-links/{id} - update metadata
- [ ] DELETE /kpi-links/{id} - success

### Backward Compatibility
- [ ] Old endpoints still work (with deprecation warning)

---

## 🔗 Dependencies

- Issue #XXX-7: KpiLink application layer

---

## ✅ Definition of Done

- [ ] All new endpoints implemented
- [ ] DTOs created with proper validation
- [ ] Controller implemented
- [ ] Validators created
- [ ] Mapper profiles updated
- [ ] OpenAPI documentation generated
- [ ] API tests pass
- [ ] Backward compatibility maintained

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created request DTOs
- [ ] Created response DTOs
- [ ] Created KpiLinksController
- [ ] Created validators
- [ ] Updated mapper profiles
- [ ] Added API tests
- [ ] Updated OpenAPI documentation

**Notes:** [Any relevant notes]
```


