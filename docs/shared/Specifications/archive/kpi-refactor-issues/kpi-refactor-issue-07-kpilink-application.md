# Issue #XXX-7: Application - MeasureLink Commands and Queries

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `application`, `cqrs`, `measure-link`  
**Estimated Effort:** 8-10 hours

---

## 📋 Description

Implement the application layer commands and queries for MeasureLink operations, including linking KPIs to Goals, Strategies, and Persons.

---

## 🏗️ Implementation Details

### Commands to Create/Update

#### 1. LinkKpiCommand (replaces LinkKpiToGoalCommand)

Location: `PurposePath.Application/Commands/MeasureLink/LinkKpiCommand.cs`

```csharp
using MediatR;
using PurposePath.Domain.ValueObjects;

namespace PurposePath.Application.Commands.MeasureLink;

/// <summary>
/// Command to link a Measure to a Person, Goal, or Strategy
/// </summary>
public record LinkKpiCommand : IRequest<LinkKpiResult>
{
    public TenantId TenantId { get; init; } = null!;
    public MeasureId MeasureId { get; init; } = null!;
    public PersonId PersonId { get; init; } = null!;
    public GoalId? GoalId { get; init; }
    public StrategyId? StrategyId { get; init; }
    public UserId CreatedBy { get; init; } = null!;
    
    // Optional metadata
    public decimal? ThresholdPct { get; init; }
    public string? LinkType { get; init; }
    public decimal? Weight { get; init; }
    public int? DisplayOrder { get; init; }
    public bool IsPrimary { get; init; }
}

public record LinkKpiResult
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public bool Success { get; init; }
    public string? ErrorMessage { get; init; }
}
```

#### 2. UnlinkKpiCommand

Location: `PurposePath.Application/Commands/MeasureLink/UnlinkKpiCommand.cs`

```csharp
public record UnlinkKpiCommand : IRequest<UnlinkKpiResult>
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public TenantId TenantId { get; init; } = null!;
    public UserId RequestedBy { get; init; } = null!;
}
```

#### 3. UpdateKpiLinkCommand

Location: `PurposePath.Application/Commands/MeasureLink/UpdateKpiLinkCommand.cs`

```csharp
public record UpdateKpiLinkCommand : IRequest<UpdateKpiLinkResult>
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public TenantId TenantId { get; init; } = null!;
    public UserId UpdatedBy { get; init; } = null!;
    
    public decimal? ThresholdPct { get; init; }
    public string? LinkType { get; init; }
    public decimal? Weight { get; init; }
    public int? DisplayOrder { get; init; }
}
```

#### 4. SetPrimaryKpiLinkCommand

Location: `PurposePath.Application/Commands/MeasureLink/SetPrimaryKpiLinkCommand.cs`

```csharp
public record SetPrimaryKpiLinkCommand : IRequest<SetPrimaryKpiLinkResult>
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public GoalId GoalId { get; init; } = null!;  // Context for primary status
    public TenantId TenantId { get; init; } = null!;
    public UserId UpdatedBy { get; init; } = null!;
}
```

### Queries to Create/Update

#### 1. GetKpiLinksQuery

Location: `PurposePath.Application/Queries/MeasureLink/GetKpiLinksQuery.cs`

```csharp
public record GetKpiLinksQuery : IRequest<GetKpiLinksResult>
{
    public TenantId TenantId { get; init; } = null!;
    
    // Filter options (all optional)
    public MeasureId? MeasureId { get; init; }
    public GoalId? GoalId { get; init; }
    public StrategyId? StrategyId { get; init; }
    public PersonId? PersonId { get; init; }
    public bool? PersonalOnly { get; init; }  // Only person-level links (no goal/strategy)
}

public record GetKpiLinksResult
{
    public IEnumerable<MeasureLinkDto> Links { get; init; } = Array.Empty<MeasureLinkDto>();
}

public record MeasureLinkDto
{
    public string Id { get; init; } = string.Empty;
    public string MeasureId { get; init; } = string.Empty;
    public string MeasureName { get; init; } = string.Empty;
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
}
```

#### 2. GetKpiLinkDetailsQuery

Location: `PurposePath.Application/Queries/MeasureLink/GetKpiLinkDetailsQuery.cs`

```csharp
public record GetKpiLinkDetailsQuery : IRequest<MeasureLinkDetailsResult?>
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public TenantId TenantId { get; init; } = null!;
}

public record MeasureLinkDetailsResult
{
    public MeasureLinkDto Link { get; init; } = null!;
    public MeasureDetailsDto Measure { get; init; } = null!;
    public IEnumerable<MeasureDataSummaryDto> TargetSummary { get; init; } = Array.Empty<MeasureDataSummaryDto>();
    public IEnumerable<MeasureDataSummaryDto> ActualSummary { get; init; } = Array.Empty<MeasureDataSummaryDto>();
}
```

#### 3. GetAvailableKpisForLinkingQuery

Location: `PurposePath.Application/Queries/MeasureLink/GetAvailableKpisForLinkingQuery.cs`

```csharp
public record GetAvailableKpisForLinkingQuery : IRequest<GetAvailableKpisResult>
{
    public TenantId TenantId { get; init; } = null!;
    public GoalId? GoalId { get; init; }  // If provided, exclude already linked KPIs
    public StrategyId? StrategyId { get; init; }  // If provided, exclude already linked KPIs
}
```

### Command Handlers

#### LinkKpiCommandHandler

Key validation logic:
```csharp
// Validate Strategy requires Goal
if (command.StrategyId != null && command.GoalId == null)
    throw new ValidationException("StrategyId requires GoalId to be specified");

// Check uniqueness for Goal-level link
if (command.GoalId != null && command.StrategyId == null)
{
    var exists = await _kpiLinkRepository.ExistsForGoalAsync(command.MeasureId, command.GoalId, ct);
    if (exists)
        throw new ConflictException($"Measure {command.MeasureId} is already linked to Goal {command.GoalId}");
}

// Check uniqueness for Strategy-level link
if (command.StrategyId != null)
{
    var exists = await _kpiLinkRepository.ExistsForStrategyAsync(command.MeasureId, command.StrategyId, ct);
    if (exists)
        throw new ConflictException($"Measure {command.MeasureId} is already linked to Strategy {command.StrategyId}");
}
```

---

## 📁 Files to Create/Modify

### Commands
| File | Action |
|------|--------|
| `PurposePath.Application/Commands/MeasureLink/LinkKpiCommand.cs` | Create |
| `PurposePath.Application/Commands/MeasureLink/UnlinkKpiCommand.cs` | Create |
| `PurposePath.Application/Commands/MeasureLink/UpdateKpiLinkCommand.cs` | Create |
| `PurposePath.Application/Commands/MeasureLink/SetPrimaryKpiLinkCommand.cs` | Create |

### Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Commands/MeasureLink/LinkKpiCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/MeasureLink/UnlinkKpiCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/MeasureLink/UpdateKpiLinkCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/MeasureLink/SetPrimaryKpiLinkCommandHandler.cs` | Create |

### Queries
| File | Action |
|------|--------|
| `PurposePath.Application/Queries/MeasureLink/GetKpiLinksQuery.cs` | Create |
| `PurposePath.Application/Queries/MeasureLink/GetKpiLinkDetailsQuery.cs` | Create |
| `PurposePath.Application/Queries/MeasureLink/GetAvailableKpisForLinkingQuery.cs` | Create |

### Query Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Queries/MeasureLink/GetKpiLinksQueryHandler.cs` | Create |
| `PurposePath.Application/Handlers/Queries/MeasureLink/GetKpiLinkDetailsQueryHandler.cs` | Create |
| `PurposePath.Application/Handlers/Queries/MeasureLink/GetAvailableKpisForLinkingQueryHandler.cs` | Create |

### Validators
| File | Action |
|------|--------|
| `PurposePath.Application/Validators/MeasureLink/LinkKpiCommandValidator.cs` | Create |
| `PurposePath.Application/Validators/MeasureLink/UpdateKpiLinkCommandValidator.cs` | Create |

---

## 🧪 Testing

### Command Tests
- [ ] Link Measure to Person only (personal scorecard)
- [ ] Link Measure to Person + Goal
- [ ] Link Measure to Person + Goal + Strategy
- [ ] Validation: Strategy without Goal fails
- [ ] Validation: Duplicate Goal link fails
- [ ] Validation: Duplicate Strategy link fails
- [ ] Unlink removes link correctly
- [ ] Update modifies metadata correctly
- [ ] Set primary updates correct links

### Query Tests
- [ ] Get links by Measure
- [ ] Get links by Goal
- [ ] Get links by Strategy
- [ ] Get links by Person
- [ ] Get personal-only links
- [ ] Get available KPIs excludes already linked

---

## 🔗 Dependencies

- Issue #XXX-5: MeasureLink infrastructure (repository)

---

## ✅ Definition of Done

- [ ] All commands created with proper validation
- [ ] All command handlers implemented
- [ ] All queries created
- [ ] All query handlers implemented
- [ ] Validators created with FluentValidation
- [ ] Unit tests pass
- [ ] Registered in MediatR

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created LinkKpiCommand and handler
- [ ] Created UnlinkKpiCommand and handler
- [ ] Created UpdateKpiLinkCommand and handler
- [ ] Created SetPrimaryKpiLinkCommand and handler
- [ ] Created GetKpiLinksQuery and handler
- [ ] Created GetKpiLinkDetailsQuery and handler
- [ ] Created GetAvailableKpisForLinkingQuery and handler
- [ ] Created validators
- [ ] Added unit tests

**Notes:** [Any relevant notes]
```


