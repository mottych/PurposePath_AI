# Issue #XXX-12: Cleanup - Remove Deprecated Entities and Tables

**Parent Epic:** Measure Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** Medium  
**Labels:** `cleanup`, `deprecation`, `technical-debt`  
**Estimated Effort:** 8-10 hours

---

## 📋 Description

After successful migration and verification period, remove deprecated entities, tables, and code related to the old Measure linking and data model.

---

## ⚠️ Prerequisites

Before executing this cleanup:

- [ ] Migration completed successfully (Issue #XXX-11)
- [ ] All validation checks pass
- [ ] Application running on new code for at least 7 days
- [ ] No errors related to Measure functionality in production
- [ ] Stakeholder approval for cleanup

---

## 🗑️ Entities to Remove

### Domain Layer

| Entity | File | Notes |
|--------|------|-------|
| `GoalMeasureLink` | `PurposePath.Domain/Entities/GoalMeasureLink.cs` | Replaced by MeasureLink |
| `MeasureMilestone` | `PurposePath.Domain/Entities/MeasureMilestone.cs` | Replaced by MeasureData |
| `MeasureActual` | `PurposePath.Domain/Entities/MeasureActual.cs` | Replaced by MeasureData |
| `MeasureReading` | `PurposePath.Domain/Entities/MeasureReading.cs` | Replaced by MeasureData |
| `GoalMeasureLinkId` | `PurposePath.Domain/ValueObjects/GoalMeasureLinkId.cs` | Replaced by MeasureLinkId |
| `MeasureMilestoneId` | `PurposePath.Domain/ValueObjects/MeasureMilestoneId.cs` | Replaced by MeasureDataId |
| `MeasureActualId` | `PurposePath.Domain/ValueObjects/MeasureActualId.cs` | Replaced by MeasureDataId |
| `MeasureReadingId` | `PurposePath.Domain/ValueObjects/MeasureReadingId.cs` | Replaced by MeasureDataId |

### Domain Events

| Event | File | Notes |
|-------|------|-------|
| `GoalMeasureLinkedEvent` | `PurposePath.Domain/Events/GoalMeasureLinkedEvent.cs` | Replaced by MeasureLinkedEvent |
| `MeasureThresholdUpdatedEvent` | Keep or update | May need to update to use MeasureLinkId |
| `MeasureMilestoneCreatedEvent` | `PurposePath.Domain/Events/MeasureMilestoneEvents.cs` | Replaced |
| `MeasureMilestoneUpdatedEvent` | `PurposePath.Domain/Events/MeasureMilestoneEvents.cs` | Replaced |
| `MeasureActualRecordedEvent` | `PurposePath.Domain/Events/MeasureActualEvents.cs` | Update for new model |

### Repository Interfaces

| Interface | File | Notes |
|-----------|------|-------|
| `IGoalMeasureLinkRepository` | `PurposePath.Domain/Repositories/IGoalMeasureLinkRepository.cs` | Replaced by IMeasureLinkRepository |
| `IMeasureMilestoneRepository` | `PurposePath.Domain/Repositories/IMeasureMilestoneRepository.cs` | Replaced by IMeasureDataRepository |
| `IMeasureActualRepository` | `PurposePath.Domain/Repositories/IMeasureActualRepository.cs` | Replaced by IMeasureDataRepository |
| `IMeasureReadingRepository` | `PurposePath.Domain/Repositories/IMeasureReadingRepository.cs` | Replaced by IMeasureDataRepository |

---

## 🗄️ Infrastructure to Remove

### Data Models

| Data Model | File |
|------------|------|
| `GoalMeasureLinkDataModel` | `PurposePath.Infrastructure/DataModels/GoalMeasureLinkDataModel.cs` |
| `MeasureMilestoneDataModel` | `PurposePath.Infrastructure/DataModels/MeasureMilestoneDataModel.cs` |
| `MeasureActualDataModel` | `PurposePath.Infrastructure/DataModels/MeasureActualDataModel.cs` |
| `MeasureReadingDataModel` | `PurposePath.Infrastructure/DataModels/MeasureReadingDataModel.cs` |

### Mappers

| Mapper | File |
|--------|------|
| `GoalMeasureLinkMappingProfile` | `PurposePath.Infrastructure/Mappers/GoalMeasureLinkMappingProfile.cs` |
| `MeasureMilestoneMapper` | `PurposePath.Infrastructure/Mappers/MeasureMilestoneMapper.cs` |
| `MeasureActualMapper` | `PurposePath.Infrastructure/Mappers/MeasureActualMapper.cs` |
| `MeasureReadingMappingProfile` | `PurposePath.Infrastructure/Mappers/MeasureReadingMappingProfile.cs` |

### Repositories

| Repository | File |
|------------|------|
| `DynamoDbGoalMeasureLinkRepository` | `PurposePath.Infrastructure/Repositories/DynamoDbGoalMeasureLinkRepository.cs` |
| `DynamoDbMeasureMilestoneRepository` | `PurposePath.Infrastructure/Repositories/DynamoDbMeasureMilestoneRepository.cs` |
| `DynamoDbMeasureActualRepository` | `PurposePath.Infrastructure/Repositories/DynamoDbMeasureActualRepository.cs` |
| `DynamoDbMeasureReadingRepository` | `PurposePath.Infrastructure/Repositories/DynamoDbMeasureReadingRepository.cs` |

---

## 📡 API Layer Cleanup

### Controllers to Remove/Update

| Controller | Action |
|------------|--------|
| `GoalMeasureController` | Remove deprecated endpoints |
| `MeasurePlanningController` | Remove deprecated endpoints |

### DTOs to Remove

| DTO | Notes |
|-----|-------|
| Old milestone request/response DTOs | Replaced by MeasureData DTOs |
| Old actual request/response DTOs | Replaced by MeasureData DTOs |

---

## 🗃️ DynamoDB Tables to Delete

**⚠️ Only delete after verification period!**

| Table Name | Notes |
|------------|-------|
| `purposepath-goal-measure-links` | Replaced by `purposepath-measure-links` |
| `purposepath-measure-milestones` | Replaced by `purposepath-measure-data` |
| `purposepath-measure-actuals` | Replaced by `purposepath-measure-data` |
| `purposepath-measure-readings` | Replaced by `purposepath-measure-data` |

---

## 📋 Cleanup Checklist

### Phase 1: Code Cleanup (Safe to do after migration)

- [ ] Remove deprecated entity classes
- [ ] Remove deprecated value objects
- [ ] Remove deprecated repository interfaces
- [ ] Remove deprecated repository implementations
- [ ] Remove deprecated data models
- [ ] Remove deprecated mappers
- [ ] Remove deprecated events (or update references)
- [ ] Update DI registrations in `ServiceCollectionExtensions.cs`
- [ ] Remove deprecated API endpoints
- [ ] Remove deprecated DTOs
- [ ] Remove deprecated validators
- [ ] Update any remaining references

### Phase 2: Build Verification

- [ ] Solution builds without errors
- [ ] All tests pass
- [ ] No dead code warnings
- [ ] Code analysis passes

### Phase 3: Deployment

- [ ] Deploy cleanup to dev
- [ ] Verify dev environment works
- [ ] Deploy cleanup to staging
- [ ] Verify staging environment works
- [ ] Deploy cleanup to production
- [ ] Monitor for issues

### Phase 4: Database Cleanup (After verification period)

- [ ] Final backup of old tables
- [ ] Delete `purposepath-goal-measure-links` table
- [ ] Delete `purposepath-measure-milestones` table
- [ ] Delete `purposepath-measure-actuals` table
- [ ] Delete `purposepath-measure-readings` table
- [ ] Update Pulumi/CloudFormation to remove old table definitions

---

## 🔍 Finding All References

Use these grep patterns to find remaining references:

```bash
# Find GoalMeasureLink references
grep -r "GoalMeasureLink" --include="*.cs" .

# Find MeasureMilestone references
grep -r "MeasureMilestone" --include="*.cs" .

# Find MeasureActual references
grep -r "MeasureActual" --include="*.cs" .

# Find MeasureReading references
grep -r "MeasureReading" --include="*.cs" .

# Find old table names
grep -r "goal-measure-links" --include="*.cs" .
grep -r "measure-milestones" --include="*.cs" .
grep -r "measure-actuals" --include="*.cs" .
grep -r "measure-readings" --include="*.cs" .
```

---

## 📁 Summary of Files to Delete

### Domain Layer (~15 files)
- 4 entity files
- 4 value object files
- 4 repository interface files
- 3+ event files

### Infrastructure Layer (~12 files)
- 4 data model files
- 4 mapper files
- 4 repository implementation files

### Application Layer (~20+ files)
- Command files
- Query files
- Handler files
- Validator files

### API Layer (~10+ files)
- DTO files
- Controller methods

---

## 🔗 Dependencies

- Issue #XXX-11: Migration must be complete and verified

---

## ✅ Definition of Done

- [ ] All deprecated code removed
- [ ] Solution builds without errors
- [ ] All tests pass
- [ ] No remaining references to old entities
- [ ] Deployed to all environments
- [ ] Old DynamoDB tables deleted (after verification period)
- [ ] Documentation updated

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Code Cleanup Progress:**
- [ ] Domain entities removed
- [ ] Value objects removed
- [ ] Repository interfaces removed
- [ ] Repository implementations removed
- [ ] Data models removed
- [ ] Mappers removed
- [ ] Events updated
- [ ] Application layer cleaned
- [ ] API layer cleaned

**Build Status:** [Pass / Fail]
**Test Status:** [X/Y passing]

**Remaining References Found:** [List any]

**Notes:** [Any relevant notes]
```


