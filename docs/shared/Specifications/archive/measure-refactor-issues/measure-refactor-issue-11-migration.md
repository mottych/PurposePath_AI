# Issue #XXX-11: Data Migration Scripts

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** Critical  
**Labels:** `migration`, `data`, `dynamodb`  
**Estimated Effort:** 12-16 hours

---

## 📋 Description

Create and execute data migration scripts to:
1. Migrate `GoalMeasureLink` data to `MeasureLink` table
2. Migrate `MeasureMilestone` data to `MeasureData` table (as Targets)
3. Migrate `MeasureActual` data to `MeasureData` table (as Actuals)
4. Migrate `MeasureReading` data to `MeasureData` table (as Actuals)

---

## ⚠️ Critical Notes

- **BACKUP ALL DATA BEFORE MIGRATION**
- Run on dev/staging environments first
- Verify data integrity after each step
- Keep old tables until migration is verified
- Create rollback scripts

---

## 🏗️ Migration Steps

### Phase 1: Create New Tables

Before migration, ensure new DynamoDB tables exist:
- `purposepath-measure-links`
- `purposepath-measure-data`

### Phase 2: Migrate GoalMeasureLink → MeasureLink

#### Script: `migrate-goal-measure-links.cs`

```csharp
public class MigrateGoalMeasureLinksScript
{
    public async Task ExecuteAsync()
    {
        // 1. Read all GoalMeasureLink records
        var oldLinks = await _oldLinkRepo.GetAllAsync();
        
        foreach (var oldLink in oldLinks)
        {
            // 2. Determine PersonId
            // Strategy: Use the Measure's OwnerId, or the user who created the link
            var measure = await _kpiRepo.GetByIdAsync(oldLink.MeasureId);
            var personId = await ResolvePersonId(measure?.OwnerId ?? oldLink.CreatedBy);
            
            // 3. Create new MeasureLink
            var newLink = MeasureLink.Create(
                tenantId: oldLink.TenantId,
                kpiId: oldLink.MeasureId,
                personId: personId,
                createdBy: oldLink.CreatedBy,
                goalId: oldLink.GoalId,
                strategyId: null,  // GoalMeasureLink didn't have strategies
                thresholdPct: oldLink.ThresholdPct,
                linkType: oldLink.LinkType,
                weight: oldLink.Weight,
                displayOrder: oldLink.DisplayOrder,
                isPrimary: oldLink.IsPrimary);
            
            // 4. Preserve original ID for reference
            // Use Restore method to set specific ID
            var restoredLink = MeasureLink.Restore(
                id: MeasureLinkId.From(oldLink.Id.ToString()),  // Keep same ID!
                // ... other fields
            );
            
            await _newLinkRepo.CreateAsync(restoredLink);
            
            // 5. Log migration
            _logger.LogInformation("Migrated GoalMeasureLink {OldId} to MeasureLink {NewId}",
                oldLink.Id, restoredLink.Id);
        }
    }
    
    private async Task<PersonId> ResolvePersonId(UserId userId)
    {
        // Find Person linked to this User
        var person = await _personRepo.GetByLinkedUserIdAsync(userId);
        if (person != null)
            return person.Id;
        
        // If no Person exists, create one (during Person migration)
        // For now, use UserId as PersonId (same GUID)
        return PersonId.From(userId.ToString());
    }
}
```

### Phase 3: Migrate MeasureMilestone → MeasureData (Targets)

#### Script: `migrate-measure-milestones.cs`

```csharp
public class MigrateMeasureMilestonesScript
{
    public async Task ExecuteAsync()
    {
        var milestones = await _milestoneRepo.GetAllAsync();
        
        foreach (var milestone in milestones)
        {
            // 1. Find the MeasureLink for this Measure
            var links = await _newLinkRepo.GetByMeasureIdAsync(milestone.MeasureId);
            
            foreach (var link in links)
            {
                // 2. Create MeasureData as Expected target
                var target = MeasureData.Restore(
                    id: MeasureDataId.From(milestone.Id.ToString()),  // Keep original ID
                    kpiLinkId: link.Id,
                    dataCategory: MeasureDataCategory.Target,
                    targetSubtype: TargetSubtype.Expected,  // Default to Expected
                    actualSubtype: null,
                    postValue: milestone.TargetValue,
                    postDate: milestone.MilestoneDate,
                    measuredPeriodStartDate: null,
                    label: milestone.Label,
                    confidenceLevel: milestone.ConfidenceLevel,
                    rationale: milestone.Rationale,
                    originalValue: null,
                    isManualOverride: false,
                    overrideComment: null,
                    dataSource: DataSource.Manual,
                    sourceReferenceId: null,
                    triggersReplan: false,
                    replanThresholdExceeded: false,
                    autoAdjustmentApplied: null,
                    recordedBy: milestone.CreatedBy.ToString(),
                    recordedAt: DateTimeOffset.FromFileTime(milestone.CreatedAt.ToFileTime()),
                    createdBy: milestone.CreatedBy,
                    createdAt: milestone.CreatedAt,
                    updatedBy: milestone.UpdatedBy,
                    updatedAt: milestone.UpdatedAt);
                
                await _kpiDataRepo.CreateAsync(target);
                
                _logger.LogInformation("Migrated MeasureMilestone {MilestoneId} to MeasureData {DataId} for Link {LinkId}",
                    milestone.Id, target.Id, link.Id);
            }
        }
    }
}
```

### Phase 4: Migrate MeasureActual → MeasureData (Actuals)

#### Script: `migrate-measure-actuals.cs`

```csharp
public class MigrateMeasureActualsScript
{
    public async Task ExecuteAsync()
    {
        var actuals = await _actualRepo.GetAllAsync();
        
        foreach (var actual in actuals)
        {
            var links = await _newLinkRepo.GetByMeasureIdAsync(actual.MeasureId);
            
            foreach (var link in links)
            {
                var data = MeasureData.Restore(
                    id: MeasureDataId.From(actual.Id.ToString()),
                    kpiLinkId: link.Id,
                    dataCategory: MeasureDataCategory.Actual,
                    targetSubtype: null,
                    actualSubtype: ActualSubtype.Measured,  // Existing actuals are "Measured"
                    postValue: actual.ActualValue,
                    postDate: actual.MeasurementDate,
                    measuredPeriodStartDate: null,
                    label: null,
                    confidenceLevel: null,
                    rationale: null,
                    originalValue: actual.OriginalValue,
                    isManualOverride: actual.IsManualOverride,
                    overrideComment: actual.OverrideComment,
                    dataSource: actual.DataSource,
                    sourceReferenceId: actual.SourceReferenceId,
                    triggersReplan: actual.TriggersReplan,
                    replanThresholdExceeded: actual.ReplanThresholdExceeded,
                    autoAdjustmentApplied: actual.AutoAdjustmentApplied,
                    recordedBy: actual.RecordedBy,
                    recordedAt: actual.RecordedAt,
                    createdBy: UserId.From(actual.RecordedBy),
                    createdAt: actual.RecordedAt.DateTime,
                    updatedBy: null,
                    updatedAt: null);
                
                await _kpiDataRepo.CreateAsync(data);
                
                _logger.LogInformation("Migrated MeasureActual {ActualId} to MeasureData {DataId}",
                    actual.Id, data.Id);
            }
        }
    }
}
```

### Phase 5: Migrate MeasureReading → MeasureData (Actuals)

Similar to Phase 4, but handle the different field names.

---

## 🔍 Validation Scripts

### Script: `validate-migration.cs`

```csharp
public class ValidateMigrationScript
{
    public async Task<MigrationValidationResult> ValidateAsync()
    {
        var result = new MigrationValidationResult();
        
        // 1. Count validation
        var oldLinkCount = await _oldLinkRepo.CountAsync();
        var newLinkCount = await _newLinkRepo.CountAsync();
        result.AddCheck("GoalMeasureLink count", oldLinkCount == newLinkCount);
        
        var oldMilestoneCount = await _milestoneRepo.CountAsync();
        var oldActualCount = await _actualRepo.CountAsync();
        var newTargetCount = await _kpiDataRepo.CountTargetsAsync();
        var newActualCount = await _kpiDataRepo.CountActualsAsync();
        result.AddCheck("Milestone count", oldMilestoneCount <= newTargetCount);
        result.AddCheck("Actual count", oldActualCount <= newActualCount);
        
        // 2. Data integrity validation
        // Sample random records and compare
        var sampleLinks = await _oldLinkRepo.GetRandomSampleAsync(100);
        foreach (var oldLink in sampleLinks)
        {
            var newLink = await _newLinkRepo.GetByIdAsync(MeasureLinkId.From(oldLink.Id.ToString()));
            result.AddCheck($"Link {oldLink.Id} exists", newLink != null);
            result.AddCheck($"Link {oldLink.Id} MeasureId matches", 
                newLink?.MeasureId.ToString() == oldLink.MeasureId.ToString());
        }
        
        // 3. Orphan check
        var orphanedData = await _kpiDataRepo.FindOrphanedAsync();
        result.AddCheck("No orphaned MeasureData", !orphanedData.Any());
        
        return result;
    }
}
```

---

## 📋 Migration Checklist

### Pre-Migration
- [ ] Create backup of all DynamoDB tables
- [ ] Verify new tables exist with correct schema
- [ ] Run migration on dev environment
- [ ] Validate dev migration
- [ ] Run migration on staging environment
- [ ] Validate staging migration
- [ ] Schedule production migration window
- [ ] Notify stakeholders

### Migration Execution
- [ ] Take final production backup
- [ ] Execute Phase 1: Create tables (if not done)
- [ ] Execute Phase 2: Migrate GoalMeasureLink
- [ ] Validate Phase 2
- [ ] Execute Phase 3: Migrate MeasureMilestone
- [ ] Validate Phase 3
- [ ] Execute Phase 4: Migrate MeasureActual
- [ ] Validate Phase 4
- [ ] Execute Phase 5: Migrate MeasureReading
- [ ] Validate Phase 5
- [ ] Run full validation script
- [ ] Verify application functionality

### Post-Migration
- [ ] Monitor for errors
- [ ] Keep old tables for 7 days
- [ ] Document any issues found
- [ ] Update runbook with lessons learned

---

## 🔙 Rollback Plan

If migration fails:

1. Stop migration script
2. Identify affected records
3. Clear new table data (if partial migration)
4. Fix issue
5. Re-run migration from last known good state

If application issues after migration:

1. Switch application to use old tables (feature flag)
2. Investigate and fix
3. Re-run migration if needed

---

## 📁 Files to Create

| File | Purpose |
|------|---------|
| `scripts/migration/MigrateGoalMeasureLinks.cs` | GoalMeasureLink migration |
| `scripts/migration/MigrateMeasureMilestones.cs` | MeasureMilestone migration |
| `scripts/migration/MigrateMeasureActuals.cs` | MeasureActual migration |
| `scripts/migration/MigrateMeasureReadings.cs` | MeasureReading migration |
| `scripts/migration/ValidateMigration.cs` | Validation script |
| `scripts/migration/MigrationRunner.cs` | Main runner |
| `scripts/migration/README.md` | Migration documentation |

---

## 🔗 Dependencies

- Issue #XXX-5: MeasureLink infrastructure (new tables/repos)
- Issue #XXX-6: MeasureData infrastructure (new tables/repos)

---

## ✅ Definition of Done

- [ ] All migration scripts created
- [ ] Validation scripts created
- [ ] Successfully migrated dev environment
- [ ] Successfully migrated staging environment
- [ ] Successfully migrated production environment
- [ ] All validation checks pass
- [ ] Documentation updated

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Environment:** [Dev / Staging / Production]

**Migration Status:**
- [ ] Phase 2: GoalMeasureLink migration - X records
- [ ] Phase 3: MeasureMilestone migration - X records
- [ ] Phase 4: MeasureActual migration - X records
- [ ] Phase 5: MeasureReading migration - X records

**Validation Results:**
- Total checks: X
- Passed: X
- Failed: X

**Issues Found:** [List any issues]

**Notes:** [Any relevant notes]
```


