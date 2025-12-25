# Issue #XXX-1: Domain - Add New Enums and Value Objects

**Parent Epic:** KPI Linking & Data Model Refactoring  
**Type:** Task  
**Priority:** High  
**Labels:** `domain`, `enums`, `value-objects`  
**Estimated Effort:** 2-3 hours

---

## 📋 Description

Create new enums and value objects required for the KPI linking and data refactoring.

---

## ✅ Tasks

### 1. Add New Enums to `TractionEnums.cs`

Location: `PurposePath.Domain/Common/TractionEnums.cs`

```csharp
/// <summary>
/// Category of KPI data point
/// </summary>
public enum KpiDataCategory
{
    /// <summary>Target/planned value</summary>
    Target,
    /// <summary>Actual/recorded value</summary>
    Actual
}

/// <summary>
/// Subtype for Target data points
/// </summary>
public enum TargetSubtype
{
    /// <summary>Expected target - realistic, committed goal (main target line)</summary>
    Expected,
    /// <summary>Optimal target - stretch, best-case aspirational goal (green line)</summary>
    Optimal,
    /// <summary>Minimal target - floor, below which indicates trouble (red line)</summary>
    Minimal
}

/// <summary>
/// Subtype for Actual data points
/// </summary>
public enum ActualSubtype
{
    /// <summary>Estimated value - user's best guess when no measurement available</summary>
    Estimate,
    /// <summary>Measured value - actual recorded value (wins over Estimate for same period)</summary>
    Measured
}
```

### 2. Create New Value Objects

#### KpiLinkId

Location: `PurposePath.Domain/ValueObjects/KpiLinkId.cs`

```csharp
namespace PurposePath.Domain.ValueObjects;

/// <summary>
/// Strongly-typed identifier for KpiLink entities
/// </summary>
public record KpiLinkId(Guid Value)
{
    public static KpiLinkId New() => new(Guid.NewGuid());
    public static KpiLinkId From(string value) => new(Guid.Parse(value));
    public static KpiLinkId From(Guid value) => new(value);
    public override string ToString() => Value.ToString();
    
    public static implicit operator Guid(KpiLinkId id) => id.Value;
    public static implicit operator string(KpiLinkId id) => id.Value.ToString();
}
```

#### KpiDataId

Location: `PurposePath.Domain/ValueObjects/KpiDataId.cs`

```csharp
namespace PurposePath.Domain.ValueObjects;

/// <summary>
/// Strongly-typed identifier for KpiData entities
/// </summary>
public record KpiDataId(Guid Value)
{
    public static KpiDataId New() => new(Guid.NewGuid());
    public static KpiDataId From(string value) => new(Guid.Parse(value));
    public static KpiDataId From(Guid value) => new(value);
    public override string ToString() => Value.ToString();
    
    public static implicit operator Guid(KpiDataId id) => id.Value;
    public static implicit operator string(KpiDataId id) => id.Value.ToString();
}
```

---

## 🧪 Testing

- [ ] Enum values serialize/deserialize correctly
- [ ] Value objects can be created with `New()`, `From(string)`, `From(Guid)`
- [ ] Value objects support implicit conversion to Guid and string
- [ ] Equality comparisons work correctly for value objects

---

## 📁 Files to Create/Modify

| File | Action |
|------|--------|
| `PurposePath.Domain/Common/TractionEnums.cs` | Modify - add new enums |
| `PurposePath.Domain/ValueObjects/KpiLinkId.cs` | Create |
| `PurposePath.Domain/ValueObjects/KpiDataId.cs` | Create |

---

## 🔗 Dependencies

- None (this is a foundational issue)

---

## ✅ Definition of Done

- [ ] All enums added to `TractionEnums.cs`
- [ ] `KpiLinkId` value object created
- [ ] `KpiDataId` value object created
- [ ] Unit tests pass
- [ ] Code compiles without errors

---

## 📝 Progress Comments Template

```markdown
### Progress Update - [DATE]

**Status:** [In Progress / Blocked / Complete]

**Completed:**
- [ ] Added enums to TractionEnums.cs
- [ ] Created KpiLinkId value object
- [ ] Created KpiDataId value object
- [ ] Added unit tests

**Notes:** [Any relevant notes]
```


