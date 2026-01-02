# Issue #XXX-7: Application - MeasureLink Commands and Queries

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `application`, `cqrs`, `measure-link`  
**Estimated Effort:** 8-10 hours

---

## 📋 Description

Implement the application layer commands and queries for MeasureLink operations, including linking Measures to Goals, Strategies, and Persons.

---

## 🏗️ Implementation Details

### Commands to Create/Update

#### 1. LinkMeasureCommand (replaces LinkMeasureToGoalCommand)

Location: `PurposePath.Application/Commands/MeasureLink/LinkMeasureCommand.cs`

```csharp
using MediatR;
using PurposePath.Domain.ValueObjects;

namespace PurposePath.Application.Commands.MeasureLink;

/// <summary>
/// Command to link a Measure to a Person, Goal, or Strategy
/// </summary>
public record LinkMeasureCommand : IRequest<LinkMeasureResult>
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

public record LinkMeasureResult
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public bool Success { get; init; }
    public string? ErrorMessage { get; init; }
}
```

#### 2. UnlinkMeasureCommand

Location: `PurposePath.Application/Commands/MeasureLink/UnlinkMeasureCommand.cs`

```csharp
public record UnlinkMeasureCommand : IRequest<UnlinkMeasureResult>
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public TenantId TenantId { get; init; } = null!;
    public UserId RequestedBy { get; init; } = null!;
}
```

#### 3. UpdateMeasureLinkCommand

Location: `PurposePath.Application/Commands/MeasureLink/UpdateMeasureLinkCommand.cs`

```csharp
public record UpdateMeasureLinkCommand : IRequest<UpdateMeasureLinkResult>
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

#### 4. SetPrimaryMeasureLinkCommand

Location: `PurposePath.Application/Commands/MeasureLink/SetPrimaryMeasureLinkCommand.cs`

```csharp
public record SetPrimaryMeasureLinkCommand : IRequest<SetPrimaryMeasureLinkResult>
{
    public MeasureLinkId LinkId { get; init; } = null!;
    public GoalId GoalId { get; init; } = null!;  // Context for primary status
    public TenantId TenantId { get; init; } = null!;
    public UserId UpdatedBy { get; init; } = null!;
}
```

### Queries to Create/Update

#### 1. GetMeasureLinksQuery

Location: `PurposePath.Application/Queries/MeasureLink/GetMeasureLinksQuery.cs`

```csharp
public record GetMeasureLinksQuery : IRequest<GetMeasureLinksResult>
{
    public TenantId TenantId { get; init; } = null!;
    
    // Filter options (all optional)
    public MeasureId? MeasureId { get; init; }
    public GoalId? GoalId { get; init; }
    public StrategyId? StrategyId { get; init; }
    public PersonId? PersonId { get; init; }
    public bool? PersonalOnly { get; init; }  // Only person-level links (no goal/strategy)
}

public record GetMeasureLinksResult
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

#### 2. GetMeasureLinkDetailsQuery

Location: `PurposePath.Application/Queries/MeasureLink/GetMeasureLinkDetailsQuery.cs`

```csharp
public record GetMeasureLinkDetailsQuery : IRequest<MeasureLinkDetailsResult?>
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

#### 3. GetAvailableMeasuresForLinkingQuery

Location: `PurposePath.Application/Queries/MeasureLink/GetAvailableMeasuresForLinkingQuery.cs`

```csharp
public record GetAvailableMeasuresForLinkingQuery : IRequest<GetAvailableMeasuresResult>
{
    public TenantId TenantId { get; init; } = null!;
    public GoalId? GoalId { get; init; }  // If provided, exclude already linked Measures
    public StrategyId? StrategyId { get; init; }  // If provided, exclude already linked Measures
}
```

### Command Handlers

#### LinkMeasureCommandHandler

Key validation logic:
```csharp
// Validate Strategy requires Goal
if (command.StrategyId != null && command.GoalId == null)
    throw new ValidationException("StrategyId requires GoalId to be specified");

// Check uniqueness for Goal-level link
if (command.GoalId != null && command.StrategyId == null)
{
    var exists = await _measureLinkRepository.ExistsForGoalAsync(command.MeasureId, command.GoalId, ct);
    if (exists)
        throw new ConflictException($"Measure {command.MeasureId} is already linked to Goal {command.GoalId}");
}

// Check uniqueness for Strategy-level link
if (command.StrategyId != null)
{
    var exists = await _measureLinkRepository.ExistsForStrategyAsync(command.MeasureId, command.StrategyId, ct);
    if (exists)
        throw new ConflictException($"Measure {command.MeasureId} is already linked to Strategy {command.StrategyId}");
}
```

---

## 📁 Files to Create/Modify

### Commands
| File | Action |
|------|--------|
| `PurposePath.Application/Commands/MeasureLink/LinkMeasureCommand.cs` | Create |
| `PurposePath.Application/Commands/MeasureLink/UnlinkMeasureCommand.cs` | Create |
| `PurposePath.Application/Commands/MeasureLink/UpdateMeasureLinkCommand.cs` | Create |
| `PurposePath.Application/Commands/MeasureLink/SetPrimaryMeasureLinkCommand.cs` | Create |

### Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Commands/MeasureLink/LinkMeasureCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/MeasureLink/UnlinkMeasureCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/MeasureLink/UpdateMeasureLinkCommandHandler.cs` | Create |
| `PurposePath.Application/Handlers/Commands/MeasureLink/SetPrimaryMeasureLinkCommandHandler.cs` | Create |

### Queries
| File | Action |
|------|--------|
| `PurposePath.Application/Queries/MeasureLink/GetMeasureLinksQuery.cs` | Create |
| `PurposePath.Application/Queries/MeasureLink/GetMeasureLinkDetailsQuery.cs` | Create |
| `PurposePath.Application/Queries/MeasureLink/GetAvailableMeasuresForLinkingQuery.cs` | Create |

### Query Handlers
| File | Action |
|------|--------|
| `PurposePath.Application/Handlers/Queries/MeasureLink/GetMeasureLinksQueryHandler.cs` | Create |
| `PurposePath.Application/Handlers/Queries/MeasureLink/GetMeasureLinkDetailsQueryHandler.cs` | Create |
| `PurposePath.Application/Handlers/Queries/MeasureLink/GetAvailableMeasuresForLinkingQueryHandler.cs` | Create |

### Validators
| File | Action |
|------|--------|
| `PurposePath.Application/Validators/MeasureLink/LinkMeasureCommandValidator.cs` | Create |
| `PurposePath.Application/Validators/MeasureLink/UpdateMeasureLinkCommandValidator.cs` | Create |

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
- [ ] Get available Measures excludes already linked

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
- [ ] Created LinkMeasureCommand and handler
- [ ] Created UnlinkMeasureCommand and handler
- [ ] Created UpdateMeasureLinkCommand and handler
- [ ] Created SetPrimaryMeasureLinkCommand and handler
- [ ] Created GetMeasureLinksQuery and handler
- [ ] Created GetMeasureLinkDetailsQuery and handler
- [ ] Created GetAvailableMeasuresForLinkingQuery and handler
- [ ] Created validators
- [ ] Added unit tests

**Notes:** [Any relevant notes]
```


