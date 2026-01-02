# Issue #XXX-9: API - Update Measure Linking Endpoints

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `api`, `controllers`, `measure-link`  
**Estimated Effort:** 6-8 hours

---

## 📋 Description

Update the Traction Lambda API controllers and DTOs to support the new MeasureLink functionality, including linking to Person, Goal, and Strategy.

---

## 🏗️ API Changes

### New/Updated Endpoints

| Method | Endpoint | Description | Change |
|--------|----------|-------------|--------|
| POST | `/measure-links` | Create Measure link | New endpoint |
| GET | `/measure-links` | List Measure links with filters | New endpoint |
| GET | `/measure-links/{id}` | Get link details | New endpoint |
| PUT | `/measure-links/{id}` | Update link metadata | New endpoint |
| DELETE | `/measure-links/{id}` | Remove link | New endpoint |
| GET | `/goals/{goalId}/measure-links` | Get links for goal | New endpoint |
| GET | `/strategies/{strategyId}/measure-links` | Get links for strategy | New endpoint |
| GET | `/people/{personId}/measure-links` | Get personal scorecards | New endpoint |

### Deprecated Endpoints (redirect to new)

| Old Endpoint | New Endpoint | Notes |
|--------------|--------------|-------|
| POST `/goals/{goalId}/measures:link` | POST `/measure-links` | Add goalId in body |
| POST `/goals/{goalId}/measures:unlink` | DELETE `/measure-links/{id}` | Use link ID |
| GET `/goals/{goalId}/measures` | GET `/goals/{goalId}/measure-links` | Returns links with Measure data |

---

## 📋 Request/Response DTOs

### CreateMeasureLinkRequest

Location: `Services/PurposePath.Traction.Lambda/DTOs/Requests/MeasureLink/CreateMeasureLinkRequest.cs`

```csharp
public record CreateMeasureLinkRequest
{
    /// <summary>
    /// ID of the Measure to link
    /// </summary>
    [Required]
    public string MeasureId { get; init; } = string.Empty;
    
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
    /// Whether this is the primary Measure for the goal
    /// </summary>
    public bool IsPrimary { get; init; }
    
    /// <summary>
    /// Threshold percentage for variance alerts (0-100)
    /// </summary>
    [Range(0, 100)]
    public decimal? ThresholdPct { get; init; }
}
```

### MeasureLinkResponse

Location: `Services/PurposePath.Traction.Lambda/DTOs/Responses/MeasureLink/MeasureLinkResponse.cs`

```csharp
public record MeasureLinkResponse
{
    public string Id { get; init; } = string.Empty;
    public string MeasureId { get; init; } = string.Empty;
    public string MeasureName { get; init; } = string.Empty;
    public string MeasureUnit { get; init; } = string.Empty;
    public string MeasureDirection { get; init; } = string.Empty;
    
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

### MeasureLinkListResponse

```csharp
public record MeasureLinkListResponse
{
    public IEnumerable<MeasureLinkResponse> Items { get; init; } = Array.Empty<MeasureLinkResponse>();
    public int TotalCount { get; init; }
}
```

---

## 🎮 Controller Implementation

Location: `Services/PurposePath.Traction.Lambda/Controllers/MeasureLinksController.cs`

```csharp
[ApiController]
[Route("measure-links")]
public class MeasureLinksController : ControllerBase
{
    private readonly IMediator _mediator;

    public MeasureLinksController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Create a new Measure link
    /// </summary>
    [HttpPost]
    [ProducesResponseType(typeof(ApiResponse<MeasureLinkResponse>), 201)]
    [ProducesResponseType(typeof(ApiErrorResponse), 400)]
    [ProducesResponseType(typeof(ApiErrorResponse), 409)]
    public async Task<IActionResult> CreateLink(
        [FromBody] CreateMeasureLinkRequest request,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Get Measure links with optional filtering
    /// </summary>
    [HttpGet]
    [ProducesResponseType(typeof(ApiResponse<MeasureLinkListResponse>), 200)]
    public async Task<IActionResult> GetLinks(
        [FromQuery] string? measureId,
        [FromQuery] string? goalId,
        [FromQuery] string? strategyId,
        [FromQuery] string? personId,
        [FromQuery] bool? personalOnly,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Get a specific Measure link
    /// </summary>
    [HttpGet("{id}")]
    [ProducesResponseType(typeof(ApiResponse<MeasureLinkResponse>), 200)]
    [ProducesResponseType(typeof(ApiErrorResponse), 404)]
    public async Task<IActionResult> GetLink(string id, CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Update Measure link metadata
    /// </summary>
    [HttpPut("{id}")]
    [ProducesResponseType(typeof(ApiResponse<MeasureLinkResponse>), 200)]
    [ProducesResponseType(typeof(ApiErrorResponse), 404)]
    public async Task<IActionResult> UpdateLink(
        string id,
        [FromBody] UpdateMeasureLinkRequest request,
        CancellationToken ct)
    {
        // Implementation
    }

    /// <summary>
    /// Delete a Measure link
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
| `DTOs/Requests/MeasureLink/CreateMeasureLinkRequest.cs` | Create |
| `DTOs/Requests/MeasureLink/UpdateMeasureLinkRequest.cs` | Create |
| `DTOs/Responses/MeasureLink/MeasureLinkResponse.cs` | Create |
| `DTOs/Responses/MeasureLink/MeasureLinkListResponse.cs` | Create |

### Controllers
| File | Action |
|------|--------|
| `Controllers/MeasureLinksController.cs` | Create |
| `Controllers/GoalMeasureController.cs` | Modify - add deprecation notices |

### Validators
| File | Action |
|------|--------|
| `Validators/MeasureLink/CreateMeasureLinkRequestValidator.cs` | Create |
| `Validators/MeasureLink/UpdateMeasureLinkRequestValidator.cs` | Create |

### Mappers
| File | Action |
|------|--------|
| `Mappers/TractionLambdaMappingProfile.cs` | Modify - add MeasureLink mappings |

---

## 🧪 Testing

### API Tests
- [ ] POST /measure-links - create with Person only
- [ ] POST /measure-links - create with Person + Goal
- [ ] POST /measure-links - create with Person + Goal + Strategy
- [ ] POST /measure-links - validation error for Strategy without Goal
- [ ] POST /measure-links - conflict for duplicate Goal link
- [ ] GET /measure-links - filter by measureId
- [ ] GET /measure-links - filter by goalId
- [ ] GET /measure-links - filter by personId
- [ ] GET /measure-links - filter personalOnly=true
- [ ] GET /measure-links/{id} - success
- [ ] GET /measure-links/{id} - not found
- [ ] PUT /measure-links/{id} - update metadata
- [ ] DELETE /measure-links/{id} - success

### Backward Compatibility
- [ ] Old endpoints still work (with deprecation warning)

---

## 🔗 Dependencies

- Issue #XXX-7: MeasureLink application layer

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
- [ ] Created MeasureLinksController
- [ ] Created validators
- [ ] Updated mapper profiles
- [ ] Added API tests
- [ ] Updated OpenAPI documentation

**Notes:** [Any relevant notes]
```


