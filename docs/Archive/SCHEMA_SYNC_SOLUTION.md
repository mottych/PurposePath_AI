# Database Schema Synchronization Solution

## 🎯 Current State Analysis

### .NET Project (pp_api) - **Source of Truth**
- ✅ **Rich Domain Models**: Goal, KPI, Action, etc. with business logic
- ✅ **DynamoDB Data Models**: GoalDataModel, KpiDataModel with `[DynamoDBProperty]` attributes  
- ✅ **Mappers**: Convert between domain and data models
- ✅ **Current Schema**: Up-to-date with latest business requirements

### Python Project (pp_ai) - **Needs Sync**
- ❌ **Outdated YAML**: coaching/template.yaml doesn't match current schema
- ❌ **Missing Tables**: Only has conversations and sessions, missing goals, KPIs, etc.
- ❌ **Type Mismatches**: Python types don't match C# models

## 🏗️ **Recommended Solution: Schema-First Code Generation**

### Phase 1: Extract Schema from .NET (Immediate)

Create a schema extraction tool that reads the C# data models and generates:

1. **DynamoDB CloudFormation templates** (for Python deployment)
2. **Python Pydantic models** (for type safety)
3. **TypeScript types** (for any frontend work)

### Phase 2: Establish Shared Schema Repository (Long-term)

Move to a centralized schema definition that generates code for both projects.

---

## 🚀 **Implementation Plan**

### Step 1: Schema Extraction Tool

```csharp
// Tools/SchemaExtractor/Program.cs
public class SchemaExtractor
{
    public void ExtractSchema()
    {
        var dataModels = GetAllDataModels();
        
        foreach (var model in dataModels)
        {
            var schema = ExtractFromDataModel(model);
            GenerateCloudFormation(schema);
            GeneratePydanticModel(schema);
            GenerateTypeScript(schema);
        }
    }
}
```

### Step 2: Generated Outputs

#### A. CloudFormation Templates (for Python deployment)
```yaml
# Generated: pp_ai/infra/tables/goals-table.yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  GoalsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub purposepath-goals-${Stage}
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: goal_id
          AttributeType: S
        - AttributeName: tenant_id
          AttributeType: S
        - AttributeName: user_id
          AttributeType: S
      KeySchema:
        - AttributeName: goal_id
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: tenant_id-index
          KeySchema:
            - AttributeName: tenant_id
              KeyType: HASH
          Projection: { ProjectionType: ALL }
```

#### B. Python Pydantic Models (for type safety)
```python
# Generated: pp_ai/shared/types/generated/goal_models.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class GoalDataModel(BaseModel):
    """Generated from C# GoalDataModel"""
    goal_id: str = Field(..., alias="goal_id")
    tenant_id: str = Field(..., alias="tenant_id") 
    user_id: Optional[str] = Field(None, alias="user_id")
    title: str = Field(..., alias="title")
    intent: str = Field(..., alias="intent")
    alignment_score: Optional[int] = Field(None, alias="alignment_score")
    alignment_explanation: Optional[str] = Field(None, alias="alignment_explanation")
    alignment_suggestions: Optional[List[str]] = Field(None, alias="alignment_suggestions")
    status: str = Field(..., alias="status")
    priority: str = Field(..., alias="priority")
    time_horizon: str = Field(..., alias="time_horizon")
    target_date: Optional[str] = Field(None, alias="target_date")
    progress_percentage: float = Field(..., alias="progress_percentage")
    tags: List[str] = Field(default_factory=list, alias="tags")
    metadata: str = Field(..., alias="metadata")
    
    # Audit fields (from BaseDataModel)
    created_at: str = Field(..., alias="created_at")
    updated_at: Optional[str] = Field(None, alias="updated_at")
    created_by: str = Field(..., alias="created_by")
    updated_by: Optional[str] = Field(None, alias="updated_by")
    
    class Config:
        allow_population_by_field_name = True
```

### Step 3: Build Process Integration

#### A. .NET Build Process
```xml
<!-- pp_api/PurposePath.Backend.csproj -->
<Target Name="GenerateSchemas" BeforeTargets="Build">
  <Exec Command="dotnet run --project Tools/SchemaExtractor" />
  <Copy SourceFiles="generated/**" DestinationFolder="../pp_ai/shared/types/generated/" />
</Target>
```

#### B. Python Build Process  
```python
# pp_ai/scripts/update_schema.py
import subprocess
import shutil

def update_schema():
    """Update Python schema from .NET source"""
    # Run .NET schema extractor
    subprocess.run(["dotnet", "run", "--project", "../pp_api/Tools/SchemaExtractor"])
    
    # Copy generated files
    shutil.copytree("../generated/python", "shared/types/generated", dirs_exist_ok=True)
    shutil.copytree("../generated/cloudformation", "infra/tables", dirs_exist_ok=True)
```

---

## 🔄 **Development Workflow**

### When Changing Schema:

1. **Update .NET Data Model** (e.g., `GoalDataModel.cs`)
2. **Run Schema Extractor** (`dotnet run --project Tools/SchemaExtractor`)
3. **Python Auto-Updates** (generated files copied to `pp_ai/`)
4. **Deploy Python Infrastructure** (new CloudFormation templates)
5. **Update Python Code** (use new Pydantic models)

### Schema Change Example:

```csharp
// pp_api: Add new field to GoalDataModel
[DynamoDBProperty("goal_type")]
public string GoalType { get; set; } = "personal";
```

After running schema extractor:

```python
# pp_ai: Auto-generated Python model
class GoalDataModel(BaseModel):
    # ... existing fields ...
    goal_type: str = Field(default="personal", alias="goal_type")  # NEW!
```

```yaml
# pp_ai: Auto-generated CloudFormation
# Table automatically includes new field in schema
```

---

## 🎯 **Benefits of This Approach**

✅ **Single Source of Truth** - .NET models remain authoritative
✅ **Automatic Sync** - Python schema updates with every .NET build  
✅ **Type Safety** - Generated Pydantic models provide full type checking
✅ **Zero Manual Work** - Completely automated synchronization
✅ **Backward Compatible** - Existing .NET code unchanged
✅ **Infrastructure as Code** - CloudFormation templates for Python deployment

---

## 🚀 **Quick Start Implementation**

Want me to create the schema extractor tool? I can build:

1. **C# Console App** that reads your data models
2. **Python script** that generates Pydantic models
3. **CloudFormation templates** for your Python infrastructure
4. **Build integration** that runs automatically

This would immediately solve your schema sync problem and establish a robust long-term solution.

Would you like me to start building the schema extractor tool?