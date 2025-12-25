# Issue #XXX-7: Application - KpiLink Commands and Queries

**Parent Epic:** KPI Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `application`, `cqrs`, `kpi-link`  
**Estimated Effort:** 8-10 hours

---

## 📋 Description

Implement the application layer commands and queries for KpiLink operations, including linking KPIs to Goals, Strategies, and Persons.

---

## 🏗️ Implementation Details

### Commands to Create/Update

#### 1. LinkKpiCommand (replaces LinkKpiToGoalCommand)

Location: `PurposePath.Application/Commands/KpiLink/LinkKpiCommand.cs`

```csharp
using MediatR;
using PurposePath.Domain.ValueObjects;

namespace PurposePath.Application.Commands.KpiLink;

/// <summary>
/// Command to link a KPI to a Person, Goal, or Strategy
/// </summary>
public record LinkKpiCommand : IRequest<LinkKpiResult>
{
    public TenantId TenantId { get; init; } = null!;
    public KpiId KpiId { get; init; } = null!;
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
    public KpiLinkId LinkId { get; init; } = null!;
    public bool Success { get; init; }
    public string? ErrorMessage { get; init; }
}
```

#### 2. UnlinkKpiCommand

Location: `PurposePath.Application/Commands/KpiLink/UnlinkKpiCommand.cs`

```csharp
public record UnlinkKpiCommand : IRequest<UnlinkKpiResult>
{
    public KpiLinkId LinkId { get; init; } = null!;
    public TenantId TenantId { get; init; } = null!;
    public UserId RequestedBy { get; init; } = null!;
}
```

#### 3. UpdateKpiLinkCommand

Location: `PurposePath.Application/Commands/KpiLink/UpdateKpiLinkCommand.cs`

```csharp
public record UpdateKpiLinkCommand : IRequest<UpdateKpiLinkResult>
{
    public KpiLinkId LinkId { get; init; } = null!;
    public TenantId TenantId { get; init; } = null!;
    public UserId UpdatedBy { get; init; } = null!;
    
    public decimal? ThresholdPct { get; init; }
    public string? LinkType { get; init; }
    public decimal? Weight { get; init; }
    public int? DisplayOrder { get; init; }
}
```

#### 4. SetPrimaryKpiLinkCommand

Location: `PurposePath.Application/Commands/KpiLink/SetPrimaryKpiLinkCommand.cs`

```csharp
public record SetPrimaryKpiLinkCommand : IRequest<SetPrimaryKpiLinkResult>
{
    public KpiLinkId LinkId { get; init; } = null!;
    public GoalId GoalId { get; init; } = null!;  // Context for primary status
    public TenantId TenantId { get; init; } = null!;
    public UserId UpdatedBy { get; init; } = null!;
}
```

### Queries to Create/Update

#### 1. GetKpiLinksQuery

Location: `PurposePath.Application/Queries/KpiLink/GetKpiLinksQuery.cs`

```csharp
public record GetKpiLinksQuery : IRequest<GetKpiLinksResult>
{
    public TenantId TenantId { get; init; } = null!;
    
    // Filter options (all optional)
    public KpiId? KpiId { get; init; }
    public GoalId? GoalId { get; init; }
    public StrategyId? StrategyId { get; init; }
    public PersonId? PersonId { get; init; }
    public bool? PersonalOnly { get; init; }  // Only person-level links (no goal/strategy)
}

public record GetKpiLinksResult
{
    public IEnumerable<KpiLinkDto> Links { get; init; } = Array.Empty<KpiLinkDto>();
}

public record KpiLinkDto
{
    public string Id { get; init; } = string.Empty;
    public string KpiId { get; init; } = string.Empty;
    public string KpiName { get; init; } = string.Empty;
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

Location: `PurposePath.Application/Queries/KpiLink/GetKpiLinkDetailsQuery.cs`

```csharp
public record GetKpiLinkDetailsQuery : IRequest<KpiLinkDetailsResult?>
{
    public KpiLinkId LinkId { get; init; } = null!;
    public TenantId TenantId { get; init; } = null!;
}

public record KpiLinkDetailsResult
{
    public KpiLinkDto Link { get; init; } = null!;
    public KpiDetailsDto Kpi { get; init; } = null!;
    public IEnumerable<KpiDataSummaryDto> TargetSummary { get; init; } = Array.Empty<KpiDataSummaryDto>();
    public IEnumerable<KpiDataSummaryDto> ActualSummary { get; init; } = Array.Empty<KpiDataSummaryDto>();
}
```

#### 3. GetAvailableKpisForLinkingQuery

Location: `PurposePath.Application/Queries/KpiLink/GetAvailableKpisForLinkingQuery.cs`

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
    var exists = await _kpiLinkRepository.ExistsForGoalAsync(command.KpiId, command.GoalId, ct);
    if (exists)
        throw new ConflictException($"KPI {command.KpiId} is already linked to Goal {command.GoalId}");
}

// Check uniqueness for Strategy-level link
if (command.StrategyId != null)
{
    var exists = await _kpiLinkRepository.ExistsForStrategyAsync(command.KpiId, command.StrategyId, ct);
    if (exists)
        throw new ConflictException($"KPI {command.KpiId} is already linked to Strategy {command.StrategyId}");
}
```

---

## 📁 Files to Create/Modify

### Commands
| File | Action |
|------|--------|
| `PurposePath.Application/Commands/KpiLink/LinkKpiCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiLink/UnlinkKpiCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiLink/UpdateKpiLinkCommand.cs` | Create |
| `PurposePath.Application/Commands/KpiLink/SetPrimaryKpiLinkCommand.cs` | Create |

### Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Commands/KpiLink/LinkKpiCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/KpiLink/UnlinkKpiCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/KpiLink/UpdateKpiLinkCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/KpiLink/SetPrimaryKpiLinkCommandHandler.cs` | Create |

### Queries
| File | Action |
|------|--------|
| `PurposePath.Application/Queries/KpiLink/GetKpiLinksQuery.cs` | Create |
| `PurposePath.Application/Queries/KpiLink/GetKpiLinkDetailsQuery.cs` | Create |
| `PurposePath.Application/Queries/KpiLink/GetAvailableKpisForLinkingQuery.cs` | Create |

### Query Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Queries/KpiLink/GetKpiLinksQueryHandler.cs` | Create |
| `PurposePath.Application/Handlers/Queries/KpiLink/GetKpiLinkDetailsQueryHandler.cs` | Create |
| `PurposePath.Application/Handlers/Queries/KpiLink/GetAvailableKpisForLinkingQueryHandler.cs` | Create |

### Validators
| File | Action |
|------|--------|
| `PurposePath.Application/Validators/KpiLink/LinkKpiCommandValidator.cs` | Create |
| `PurposePath.Application/Validators/KpiLink/UpdateKpiLinkCommandValidator.cs` | Create |

---

## 🧪 Testing

### Command Tests
- [ ] Link KPI to Person only (personal scorecard)
- [ ] Link KPI to Person + Goal
- [ ] Link KPI to Person + Goal + Strategy
- [ ] Validation: Strategy without Goal fails
- [ ] Validation: Duplicate Goal link fails
- [ ] Validation: Duplicate Strategy link fails
- [ ] Unlink removes link correctly
- [ ] Update modifies metadata correctly
- [ ] Set primary updates correct links

### Query Tests
- [ ] Get links by KPI
- [ ] Get links by Goal
- [ ] Get links by Strategy
- [ ] Get links by Person
- [ ] Get personal-only links
- [ ] Get available KPIs excludes already linked

---

## 🔗 Dependencies

- Issue #XXX-5: KpiLink infrastructure (repository)

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


