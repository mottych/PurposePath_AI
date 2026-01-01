# Issue #XXX-5: Infrastructure - MeasureLink Data Model, Mapper, Repository

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `infrastructure`, `data-model`, `repository`, `measure-link`  
**Estimated Effort:** 6-8 hours

---

## 📋 Description

Implement the infrastructure layer components for the new `MeasureLink` entity, including DynamoDB data model, mapper, and repository.

---

## 🏗️ Implementation Details

### 1. Data Model

Location: `PurposePath.Infrastructure/DataModels/MeasureLinkDataModel.cs`

```csharp
using Amazon.DynamoDBv2.DataModel;
using PurposePath.Infrastructure.DataModels;

namespace PurposePath.Infrastructure.DataModels;

[DynamoDBTable("purposepath-measure-links")]
public class MeasureLinkDataModel : BaseDataModel
{
    [DynamoDBHashKey("id")]
    public string Id { get; set; } = string.Empty;

    [DynamoDBProperty("tenant_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("tenant-index")]
    public string TenantId { get; set; } = string.Empty;

    [DynamoDBProperty("kpi_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("measure-index")]
    public string MeasureId { get; set; } = string.Empty;

    [DynamoDBProperty("person_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("person-index")]
    public string PersonId { get; set; } = string.Empty;

    [DynamoDBProperty("goal_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("goal-index")]
    public string? GoalId { get; set; }

    [DynamoDBProperty("strategy_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("strategy-index")]
    public string? StrategyId { get; set; }

    [DynamoDBProperty("linked_at")]
    public string LinkedAt { get; set; } = string.Empty;

    [DynamoDBProperty("link_type")]
    public string? LinkType { get; set; }

    [DynamoDBProperty("weight")]
    public decimal? Weight { get; set; }

    [DynamoDBProperty("display_order")]
    public int? DisplayOrder { get; set; }

    [DynamoDBProperty("is_primary")]
    public bool IsPrimary { get; set; }

    [DynamoDBProperty("threshold_pct")]
    public decimal? ThresholdPct { get; set; }

    // Composite index for uniqueness enforcement
    // Format: "kpi_id#goal_id" or "kpi_id#strategy_id" or "kpi_id#person_id#PERSONAL"
    [DynamoDBGlobalSecondaryIndexHashKey("uniqueness-index")]
    public string UniquenessKey { get; set; } = string.Empty;

    // Audit fields
    [DynamoDBProperty("created_by")]
    public string CreatedBy { get; set; } = string.Empty;

    [DynamoDBProperty("created_at")]
    public string CreatedAt { get; set; } = string.Empty;

    [DynamoDBProperty("updated_at")]
    public string? UpdatedAt { get; set; }
}
```

### 2. DynamoDB Table Configuration

Location: Update `PurposePath.Infrastructure/Configuration/DynamoDbSettings.cs`

```csharp
public const string MeasureLinksTableName = "purposepath-measure-links";
```

### 3. GSI Configuration

| GSI Name | Partition Key | Purpose |
|----------|---------------|---------|
| `tenant-index` | tenant_id | List links by tenant |
| `measure-index` | kpi_id | Get all links for a Measure |
| `person-index` | person_id | Get all links for a person |
| `goal-index` | goal_id | Get all links for a goal |
| `strategy-index` | strategy_id | Get all links for a strategy |
| `uniqueness-index` | uniqueness_key | Enforce uniqueness constraints |

### 4. Mapper

Location: `PurposePath.Infrastructure/Mappers/MeasureLinkMapper.cs`

```csharp
using PurposePath.Domain.Entities;
using PurposePath.Domain.ValueObjects;
using PurposePath.Infrastructure.DataModels;

namespace PurposePath.Infrastructure.Mappers;

public static class MeasureLinkMapper
{
    public static MeasureLinkDataModel ToDataModel(MeasureLink entity)
    {
        return new MeasureLinkDataModel
        {
            Id = entity.Id.ToString(),
            TenantId = entity.TenantId.ToString(),
            MeasureId = entity.MeasureId.ToString(),
            PersonId = entity.PersonId.ToString(),
            GoalId = entity.GoalId?.ToString(),
            StrategyId = entity.StrategyId?.ToString(),
            LinkedAt = entity.LinkedAt.ToString("O"),
            LinkType = entity.LinkType,
            Weight = entity.Weight,
            DisplayOrder = entity.DisplayOrder,
            IsPrimary = entity.IsPrimary,
            ThresholdPct = entity.ThresholdPct,
            UniquenessKey = BuildUniquenessKey(entity),
            CreatedBy = entity.CreatedBy.ToString(),
            CreatedAt = entity.CreatedAt.ToString("O"),
            UpdatedAt = entity.UpdatedAt?.ToString("O")
        };
    }

    public static MeasureLink ToDomain(MeasureLinkDataModel dataModel)
    {
        return MeasureLink.Restore(
            id: MeasureLinkId.From(dataModel.Id),
            tenantId: TenantId.From(dataModel.TenantId),
            measureId: MeasureId.From(dataModel.MeasureId),
            personId: PersonId.From(dataModel.PersonId),
            createdBy: UserId.From(dataModel.CreatedBy),
            linkedAt: DateTime.Parse(dataModel.LinkedAt),
            goalId: string.IsNullOrEmpty(dataModel.GoalId) ? null : GoalId.From(dataModel.GoalId),
            strategyId: string.IsNullOrEmpty(dataModel.StrategyId) ? null : StrategyId.From(dataModel.StrategyId),
            thresholdPct: dataModel.ThresholdPct,
            linkType: dataModel.LinkType,
            weight: dataModel.Weight,
            displayOrder: dataModel.DisplayOrder,
            isPrimary: dataModel.IsPrimary,
            updatedAt: string.IsNullOrEmpty(dataModel.UpdatedAt) ? null : DateTime.Parse(dataModel.UpdatedAt));
    }

    private static string BuildUniquenessKey(MeasureLink entity)
    {
        var measureId = entity.MeasureId.ToString();
        
        if (entity.StrategyId != null)
            return $"{measureId}#STRATEGY#{entity.StrategyId}";
        
        if (entity.GoalId != null)
            return $"{measureId}#GOAL#{entity.GoalId}";
        
        // Personal scorecard - allow multiple per person
        return $"{measureId}#PERSON#{entity.PersonId}#{entity.Id}";
    }
}
```

### 5. Repository Interface

Already defined in Issue #XXX-2. Implementation here.

### 6. Repository Implementation

Location: `PurposePath.Infrastructure/Repositories/DynamoDbKpiLinkRepository.cs`

```csharp
using Amazon.DynamoDBv2.DataModel;
using Amazon.DynamoDBv2.DocumentModel;
using PurposePath.Domain.Entities;
using PurposePath.Domain.Repositories;
using PurposePath.Domain.ValueObjects;
using PurposePath.Infrastructure.DataModels;
using PurposePath.Infrastructure.Mappers;

namespace PurposePath.Infrastructure.Repositories;

public class DynamoDbKpiLinkRepository : IKpiLinkRepository
{
    private readonly IDynamoDBContext _context;

    public DynamoDbKpiLinkRepository(IDynamoDBContext context)
    {
        _context = context;
    }

    public async Task<MeasureLink?> GetByIdAsync(MeasureLinkId id, CancellationToken ct = default)
    {
        var dataModel = await _context.LoadAsync<MeasureLinkDataModel>(id.ToString(), ct);
        return dataModel == null ? null : MeasureLinkMapper.ToDomain(dataModel);
    }

    public async Task<IEnumerable<MeasureLink>> GetByKpiIdAsync(MeasureId measureId, CancellationToken ct = default)
    {
        var query = _context.QueryAsync<MeasureLinkDataModel>(
            measureId.ToString(),
            new DynamoDBOperationConfig { IndexName = "measure-index" });

        var results = await query.GetRemainingAsync(ct);
        return results.Select(MeasureLinkMapper.ToDomain);
    }

    public async Task<IEnumerable<MeasureLink>> GetByGoalIdAsync(GoalId goalId, CancellationToken ct = default)
    {
        var query = _context.QueryAsync<MeasureLinkDataModel>(
            goalId.ToString(),
            new DynamoDBOperationConfig { IndexName = "goal-index" });

        var results = await query.GetRemainingAsync(ct);
        return results.Select(MeasureLinkMapper.ToDomain);
    }

    public async Task<IEnumerable<MeasureLink>> GetByPersonIdAsync(PersonId personId, CancellationToken ct = default)
    {
        var query = _context.QueryAsync<MeasureLinkDataModel>(
            personId.ToString(),
            new DynamoDBOperationConfig { IndexName = "person-index" });

        var results = await query.GetRemainingAsync(ct);
        return results.Select(MeasureLinkMapper.ToDomain);
    }

    public async Task<IEnumerable<MeasureLink>> GetByStrategyIdAsync(StrategyId strategyId, CancellationToken ct = default)
    {
        var query = _context.QueryAsync<MeasureLinkDataModel>(
            strategyId.ToString(),
            new DynamoDBOperationConfig { IndexName = "strategy-index" });

        var results = await query.GetRemainingAsync(ct);
        return results.Select(MeasureLinkMapper.ToDomain);
    }

    public async Task<MeasureLink?> GetByGoalAndKpiAsync(GoalId goalId, MeasureId measureId, CancellationToken ct = default)
    {
        var links = await GetByGoalIdAsync(goalId, ct);
        return links.FirstOrDefault(l => l.MeasureId == measureId && l.StrategyId == null);
    }

    public async Task<MeasureLink?> GetByStrategyAndKpiAsync(StrategyId strategyId, MeasureId measureId, CancellationToken ct = default)
    {
        var links = await GetByStrategyIdAsync(strategyId, ct);
        return links.FirstOrDefault(l => l.MeasureId == measureId);
    }

    public async Task CreateAsync(MeasureLink link, CancellationToken ct = default)
    {
        var dataModel = MeasureLinkMapper.ToDataModel(link);
        await _context.SaveAsync(dataModel, ct);
    }

    public async Task UpdateAsync(MeasureLink link, CancellationToken ct = default)
    {
        var dataModel = MeasureLinkMapper.ToDataModel(link);
        await _context.SaveAsync(dataModel, ct);
    }

    public async Task DeleteAsync(MeasureLinkId id, CancellationToken ct = default)
    {
        await _context.DeleteAsync<MeasureLinkDataModel>(id.ToString(), ct);
    }

    public async Task<bool> ExistsForGoalAsync(MeasureId measureId, GoalId goalId, CancellationToken ct = default)
    {
        var link = await GetByGoalAndKpiAsync(goalId, measureId, ct);
        return link != null;
    }

    public async Task<bool> ExistsForStrategyAsync(MeasureId measureId, StrategyId strategyId, CancellationToken ct = default)
    {
        var link = await GetByStrategyAndKpiAsync(strategyId, measureId, ct);
        return link != null;
    }
}
```

---

## 📁 Files to Create/Modify

| File | Action |
|------|--------|
| `PurposePath.Infrastructure/DataModels/MeasureLinkDataModel.cs` | Create |
| `PurposePath.Infrastructure/Mappers/MeasureLinkMapper.cs` | Create |
| `PurposePath.Infrastructure/Repositories/DynamoDbKpiLinkRepository.cs` | Create |
| `PurposePath.Infrastructure/Configuration/DynamoDbSettings.cs` | Modify |
| `PurposePath.Infrastructure/ServiceCollectionExtensions.cs` | Modify - register repository |
| `Pulumi/DynamoDbStack.cs` or equivalent | Modify - add table and GSIs |

---

## 🧪 Testing

- [ ] Create MeasureLink and retrieve by ID
- [ ] Query by MeasureId
- [ ] Query by GoalId  
- [ ] Query by PersonId
- [ ] Query by StrategyId
- [ ] Check existence for Goal
- [ ] Check existence for Strategy
- [ ] Update MeasureLink
- [ ] Delete MeasureLink
- [ ] Mapper correctly converts between domain and data model

---

## 🔗 Dependencies

- Issue #XXX-2: MeasureLink domain entity

---

## ✅ Definition of Done

- [ ] Data model created with correct DynamoDB attributes
- [ ] Mapper implemented with correct conversions
- [ ] Repository implemented with all CRUD operations
- [ ] DynamoDB table and GSIs configured in Pulumi
- [ ] Repository registered in DI container
- [ ] Integration tests pass

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Created MeasureLinkDataModel
- [ ] Created MeasureLinkMapper
- [ ] Created DynamoDbKpiLinkRepository
- [ ] Added table configuration
- [ ] Registered repository in DI
- [ ] Added Pulumi table definition
- [ ] Added integration tests

**Notes:** [Any relevant notes]
```


