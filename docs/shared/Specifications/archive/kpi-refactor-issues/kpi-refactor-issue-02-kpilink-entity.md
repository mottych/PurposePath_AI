# Issue #XXX-2: Domain - Create KpiLink Entity

**Parent Epic:** KPI Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `domain`, `entity`, `kpi-link`  
**Estimated Effort:** 4-6 hours

---

## 📋 Description

Create the new `KpiLink` entity by renaming and enhancing `GoalKpiLink` to support linking KPIs to Goals, Strategies, and Persons.

---

## 🏗️ Entity Design

### KpiLink Entity

Location: `PurposePath.Domain/Entities/KpiLink.cs`

```csharp
using PurposePath.Domain.Common;
using PurposePath.Domain.Events;
using PurposePath.Domain.ValueObjects;

namespace PurposePath.Domain.Entities;

/// <summary>
/// Represents a link between a KPI and an entity (Person, Goal, Strategy)
/// A KPI is always linked to a Person who is responsible for the values.
/// Optionally, the KPI can be linked to a Goal and/or Strategy for organizational context.
/// </summary>
public class KpiLink : FullyAuditableEntity
{
    public KpiLinkId Id { get; private set; }
    public TenantId TenantId { get; private set; }
    public KpiId KpiId { get; private set; }
    
    /// <summary>
    /// Person responsible for targets/actuals on this link.
    /// Required - every KpiLink must have a person assigned.
    /// </summary>
    public PersonId PersonId { get; private set; }
    
    /// <summary>
    /// Optional Goal association.
    /// When set, this KpiLink measures progress toward a specific goal.
    /// </summary>
    public GoalId? GoalId { get; private set; }
    
    /// <summary>
    /// Optional Strategy association (only valid when GoalId is set).
    /// When set, this KpiLink measures progress toward a specific strategy within the goal.
    /// </summary>
    public StrategyId? StrategyId { get; private set; }
    
    public DateTime LinkedAt { get; private set; }
    
    // Relationship metadata
    public string? LinkType { get; private set; }
    public decimal? Weight { get; private set; }
    public int? DisplayOrder { get; private set; }
    public bool IsPrimary { get; private set; }
    public decimal? ThresholdPct { get; private set; }

    // Navigation properties
    public Kpi? Kpi { get; private set; }
    public Goal? Goal { get; private set; }
    public Strategy? Strategy { get; private set; }

    private KpiLink()
    {
        Id = null!;
        TenantId = null!;
        KpiId = null!;
        PersonId = null!;
        CreatedBy = null!;
    }

    public KpiLink(
        KpiLinkId id,
        TenantId tenantId,
        KpiId kpiId,
        PersonId personId,
        UserId createdBy,
        GoalId? goalId = null,
        StrategyId? strategyId = null,
        decimal? thresholdPct = null,
        string? linkType = null,
        decimal? weight = null,
        int? displayOrder = null,
        bool isPrimary = false)
    {
        // Validation
        ValidateStrategyRequiresGoal(goalId, strategyId);
        ValidateThreshold(thresholdPct);
        ValidateWeight(weight);

        Id = id ?? throw new ArgumentNullException(nameof(id));
        TenantId = tenantId ?? throw new ArgumentNullException(nameof(tenantId));
        KpiId = kpiId ?? throw new ArgumentNullException(nameof(kpiId));
        PersonId = personId ?? throw new ArgumentNullException(nameof(personId));
        CreatedBy = createdBy ?? throw new ArgumentNullException(nameof(createdBy));
        GoalId = goalId;
        StrategyId = strategyId;
        ThresholdPct = thresholdPct;
        LinkType = linkType?.Trim();
        Weight = weight;
        DisplayOrder = displayOrder;
        IsPrimary = isPrimary;
        LinkedAt = DateTime.UtcNow;

        AddDomainEvent(new KpiLinkedEvent(Id, TenantId, KpiId, PersonId, GoalId, StrategyId, CreatedBy));
    }

    /// <summary>
    /// Factory method to restore KpiLink from persistence layer
    /// </summary>
    public static KpiLink Restore(
        KpiLinkId id,
        TenantId tenantId,
        KpiId kpiId,
        PersonId personId,
        UserId createdBy,
        DateTime linkedAt,
        GoalId? goalId = null,
        StrategyId? strategyId = null,
        decimal? thresholdPct = null,
        string? linkType = null,
        decimal? weight = null,
        int? displayOrder = null,
        bool isPrimary = false,
        DateTime? updatedAt = null)
    {
        return new KpiLink
        {
            Id = id,
            TenantId = tenantId,
            KpiId = kpiId,
            PersonId = personId,
            GoalId = goalId,
            StrategyId = strategyId,
            CreatedBy = createdBy,
            LinkedAt = linkedAt,
            ThresholdPct = thresholdPct,
            LinkType = linkType,
            Weight = weight,
            DisplayOrder = displayOrder,
            IsPrimary = isPrimary,
            UpdatedAt = updatedAt
        };
    }

    /// <summary>
    /// Factory method for creating a new KPI link
    /// </summary>
    public static KpiLink Create(
        TenantId tenantId,
        KpiId kpiId,
        PersonId personId,
        UserId createdBy,
        GoalId? goalId = null,
        StrategyId? strategyId = null,
        decimal? thresholdPct = null,
        string? linkType = null,
        decimal? weight = null,
        int? displayOrder = null,
        bool isPrimary = false)
    {
        return new KpiLink(
            KpiLinkId.New(),
            tenantId,
            kpiId,
            personId,
            createdBy,
            goalId,
            strategyId,
            thresholdPct,
            linkType,
            weight,
            displayOrder,
            isPrimary);
    }

    // Query methods
    public bool BelongsToGoal(GoalId goalId) => GoalId == goalId;
    public bool BelongsToStrategy(StrategyId strategyId) => StrategyId == strategyId;
    public bool BelongsToKpi(KpiId kpiId) => KpiId == kpiId;
    public bool BelongsToPerson(PersonId personId) => PersonId == personId;
    public bool IsPersonOnly => GoalId == null && StrategyId == null;
    public bool IsGoalLevel => GoalId != null && StrategyId == null;
    public bool IsStrategyLevel => StrategyId != null;

    // Update methods
    public void UpdateThreshold(decimal? thresholdPct)
    {
        ValidateThreshold(thresholdPct);
        ThresholdPct = thresholdPct;
        UpdatedAt = DateTime.UtcNow;
        AddDomainEvent(new KpiLinkThresholdUpdatedEvent(Id, TenantId, KpiId, thresholdPct));
    }

    public void UpdateLinkType(string? linkType)
    {
        LinkType = linkType?.Trim();
        UpdatedAt = DateTime.UtcNow;
    }

    public void UpdateWeight(decimal? weight)
    {
        ValidateWeight(weight);
        Weight = weight;
        UpdatedAt = DateTime.UtcNow;
    }

    public void UpdateDisplayOrder(int? displayOrder)
    {
        DisplayOrder = displayOrder;
        UpdatedAt = DateTime.UtcNow;
    }

    public void SetPrimaryStatus(bool isPrimary)
    {
        IsPrimary = isPrimary;
        UpdatedAt = DateTime.UtcNow;
    }

    public void UpdatePerson(PersonId personId)
    {
        PersonId = personId ?? throw new ArgumentNullException(nameof(personId));
        UpdatedAt = DateTime.UtcNow;
    }

    // Validation
    private static void ValidateStrategyRequiresGoal(GoalId? goalId, StrategyId? strategyId)
    {
        if (strategyId != null && goalId == null)
        {
            throw new InvalidOperationException(
                "StrategyId can only be set when GoalId is also set. " +
                "A KPI can be linked to a Strategy only within the context of a Goal.");
        }
    }

    private static void ValidateThreshold(decimal? thresholdPct)
    {
        if (thresholdPct.HasValue && (thresholdPct.Value < 0 || thresholdPct.Value > 100))
        {
            throw new ArgumentOutOfRangeException(nameof(thresholdPct),
                "Threshold percentage must be between 0 and 100");
        }
    }

    private static void ValidateWeight(decimal? weight)
    {
        if (weight.HasValue && (weight.Value < 0 || weight.Value > 1))
        {
            throw new ArgumentOutOfRangeException(nameof(weight),
                "Weight must be between 0.0 and 1.0");
        }
    }
}
```

---

## 📁 Files to Create/Modify

| File | Action |
|------|--------|
| `PurposePath.Domain/Entities/KpiLink.cs` | Create |
| `PurposePath.Domain/Entities/GoalKpiLink.cs` | Keep for now (mark deprecated) |
| `PurposePath.Domain/Events/KpiLinkedEvent.cs` | Create (rename from GoalKpiLinkedEvent) |
| `PurposePath.Domain/Events/KpiLinkThresholdUpdatedEvent.cs` | Create |
| `PurposePath.Domain/Repositories/IKpiLinkRepository.cs` | Create |

---

## 🧪 Testing

- [ ] KpiLink creation with Person only (personal scorecard)
- [ ] KpiLink creation with Person + Goal
- [ ] KpiLink creation with Person + Goal + Strategy
- [ ] Validation: Strategy without Goal throws exception
- [ ] Validation: Threshold must be 0-100
- [ ] Validation: Weight must be 0-1
- [ ] All query methods (BelongsToGoal, IsPersonOnly, etc.)
- [ ] Update methods modify fields correctly

---

## 🔗 Dependencies

- Issue #XXX-1: Domain enums and value objects (for `KpiLinkId`)
- Person entity must be defined (see `people-org-structure-technical-design.md`)

---

## ✅ Definition of Done

- [ ] `KpiLink` entity created with all properties and methods
- [ ] Repository interface `IKpiLinkRepository` created
- [ ] Domain events created
- [ ] Unit tests pass
- [ ] `GoalKpiLink` marked as deprecated (not removed yet)

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created KpiLink entity
- [ ] Created IKpiLinkRepository interface
- [ ] Created domain events
- [ ] Added unit tests
- [ ] Marked GoalKpiLink as deprecated

**Blockers:** [e.g., Waiting for Person entity]

**Notes:** [Any relevant notes]
```


