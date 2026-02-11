# Measure Integration System - Final Data Model

## Document Control
- **Version:** 5.0 (Final - With Seeded Metadata)
- **Date:** November 10, 2025
- **Key Changes:** 
  - System/Measure/Parameters are SEEDED (reference data)
  - Templates stored in S3
  - Dates auto-calculated by orchestration engine
  - Simplified admin role

---

## 1. Overview

### Architecture Principle: Reference Data + Instance Data

**Reference Data (SEEDED by Developers):**
- Systems, MeasureCatalog, SystemMeasureConfig, Parameters
- These are predefined in code and seeded during deployment
- Admin can VIEW but generally cannot create/modify (except adding manual-only MeasureCatalog entries)

**Instance Data (User-Managed):**
- Connections, Measures, MeasureIntegrations, Readings
- Users create and manage these through the UI

---

## 2. Reference Data Tables (SEEDED)

### 2.1 SystemCategory

**Purpose:** Categorize external systems

**Managed By:** Developers (seeded in code)

**Admin Can:** View only

```sql
CREATE TABLE SystemCategory (
    Id INT PRIMARY KEY IDENTITY(1,1),
    Name NVARCHAR(100) NOT NULL UNIQUE,
    Description NVARCHAR(500),
    Icon NVARCHAR(50),
    SortOrder INT NOT NULL DEFAULT 0,
    IsActive BIT NOT NULL DEFAULT 1,
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2,
    
    INDEX IX_SystemCategory_Active (IsActive, SortOrder)
);
```

**Seeded Data:**
```csharp
// Seed in code during deployment
public static class SystemCategorySeed
{
    public static List<SystemCategory> GetSeedData() => new()
    {
        new() { Id = 1, Name = "Finance", Description = "Financial and accounting systems", SortOrder = 1 },
        new() { Id = 2, Name = "CRM", Description = "Customer relationship management systems", SortOrder = 2 },
        new() { Id = 3, Name = "ProjectManagement", Description = "Project and task management", SortOrder = 3 },
        new() { Id = 4, Name = "ERP", Description = "Enterprise resource planning", SortOrder = 4 },
        new() { Id = 5, Name = "Support", Description = "Customer support and ticketing", SortOrder = 5 },
    };
}
```

### 2.2 System

**Purpose:** Supported external systems

**Managed By:** Developers (seeded in code)

**Admin Can:** View only

```sql
CREATE TABLE System (
    SystemKey NVARCHAR(50) PRIMARY KEY, -- Code constant: 'quickbooks', 'salesforce'
    DisplayName NVARCHAR(200) NOT NULL,
    Description NVARCHAR(1000),
    SystemCategoryId INT NOT NULL,
    ConnectionType NVARCHAR(20) NOT NULL DEFAULT 'MCP', -- ENUM: 'MCP', 'Direct', 'Custom'
    
    -- Visual
    LogoUrl NVARCHAR(500),
    PrimaryColor NVARCHAR(7),
    
    -- Metadata
    VendorName NVARCHAR(200),
    VendorWebsite NVARCHAR(500),
    DocumentationUrl NVARCHAR(500),
    
    -- Status
    IsActive BIT NOT NULL DEFAULT 1,
    IsBeta BIT NOT NULL DEFAULT 0,
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2,
    
    CONSTRAINT FK_System_Category 
        FOREIGN KEY (SystemCategoryId) 
        REFERENCES SystemCategory(Id),
    
    INDEX IX_System_Category (SystemCategoryId, IsActive),
    INDEX IX_System_Active (IsActive)
);
```

**Seeded Data:**
```csharp
// System keys are CODE CONSTANTS
public static class SystemKeys
{
    public const string QuickBooks = "quickbooks";
    public const string Xero = "xero";
    public const string Salesforce = "salesforce";
    public const string HubSpot = "hubspot";
    public const string SapBusinessOne = "sap-b1";
}

public static class SystemSeed
{
    public static List<System> GetSeedData() => new()
    {
        new() 
        { 
            SystemKey = SystemKeys.QuickBooks,
            DisplayName = "QuickBooks Online",
            SystemCategoryId = 1, // Finance
            ConnectionType = "MCP",
            VendorName = "Intuit",
            LogoUrl = "/assets/logos/quickbooks.svg",
            IsActive = true
        },
        new() 
        { 
            SystemKey = SystemKeys.Salesforce,
            DisplayName = "Salesforce",
            SystemCategoryId = 2, // CRM
            ConnectionType = "MCP",
            VendorName = "Salesforce.com",
            LogoUrl = "/assets/logos/salesforce.svg",
            IsActive = true
        },
        // ... more systems
    };
}
```

### 2.3 MeasureCatalog

**Purpose:** Generic Measure definitions

**Managed By:** 
- Developers seed initial catalog
- Admin CAN add manual-only Measures (not linked to systems)

**Admin Can:** View all, Add (manual-only Measures)

```sql
CREATE TABLE MeasureCatalog (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CatalogKey NVARCHAR(100) NOT NULL UNIQUE, -- Code constant: 'revenue-by-category'
    Name NVARCHAR(200) NOT NULL,
    Description NVARCHAR(MAX),
    Category NVARCHAR(50) NOT NULL, -- 'financial', 'sales', 'support', 'operations'
    
    -- Default display properties
    DefaultUnit NVARCHAR(50),
    DefaultDirection NVARCHAR(20), -- 'higher-is-better', 'lower-is-better', 'target-based'
    DefaultDataType NVARCHAR(20) NOT NULL DEFAULT 'number', -- 'number', 'currency', 'percentage', 'duration'
    
    -- Source
    IsSystemDefined BIT NOT NULL DEFAULT 1, -- true = seeded by devs, false = admin-created
    
    -- Metadata
    Tags NVARCHAR(MAX), -- JSON array
    Icon NVARCHAR(50),
    
    -- Status
    IsActive BIT NOT NULL DEFAULT 1,
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy NVARCHAR(200),
    UpdatedAt DATETIME2,
    UpdatedBy NVARCHAR(200),
    
    INDEX IX_MeasureCatalog_Key (CatalogKey),
    INDEX IX_MeasureCatalog_Category (Category, IsActive),
    INDEX IX_MeasureCatalog_SystemDefined (IsSystemDefined, IsActive)
);
```

**Seeded Data:**
```csharp
// Measure keys are CODE CONSTANTS
public static class MeasureCatalogKeys
{
    public const string Revenue = "revenue";
    public const string RevenueByCategory = "revenue-by-category";
    public const string AvgTimeToResolve = "avg-time-to-resolve";
    public const string CustomerAcquisitionCost = "customer-acquisition-cost";
    public const string GrossProfitMargin = "gross-profit-margin";
}

public static class MeasureCatalogSeed
{
    public static List<MeasureCatalog> GetSeedData() => new()
    {
        new() 
        { 
            CatalogKey = MeasureCatalogKeys.RevenueByCategory,
            Name = "Revenue by Category",
            Description = "Total revenue from sales filtered by product/service category",
            Category = "financial",
            DefaultUnit = "USD",
            DefaultDirection = "higher-is-better",
            DefaultDataType = "currency",
            IsSystemDefined = true
        },
        new() 
        { 
            CatalogKey = MeasureCatalogKeys.AvgTimeToResolve,
            Name = "Average Time to Resolve",
            Description = "Average time to close support tickets",
            Category = "support",
            DefaultUnit = "hours",
            DefaultDirection = "lower-is-better",
            DefaultDataType = "duration",
            IsSystemDefined = true
        },
        // ... more Measures
    };
}
```

### 2.4 TemplateMetadata (NEW)

**Purpose:** Store S3 location and metadata for prompt templates

**Managed By:** Developers (seeded in code)

**Admin Can:** View only (templates are in S3)

```sql
CREATE TABLE TemplateMetadata (
    TemplateKey NVARCHAR(100) PRIMARY KEY, -- Code constant: 'qb-revenue-by-category'
    Name NVARCHAR(200) NOT NULL,
    Description NVARCHAR(1000),
    Version NVARCHAR(20) NOT NULL DEFAULT '1.0.0',
    
    -- S3 Location
    S3Bucket NVARCHAR(200) NOT NULL,
    S3Key NVARCHAR(500) NOT NULL, -- e.g., 'templates/quickbooks/revenue-by-category/v1.0.0.json'
    S3Region NVARCHAR(50) NOT NULL DEFAULT 'us-east-1',
    
    -- Template metadata
    SystemKey NVARCHAR(50) NOT NULL, -- Which system this template is for
    TemplateFormat NVARCHAR(20) NOT NULL DEFAULT 'handlebars', -- 'handlebars', 'jinja2', 'mustache'
    
    -- Status
    IsActive BIT NOT NULL DEFAULT 1,
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2,
    
    CONSTRAINT FK_TemplateMetadata_System 
        FOREIGN KEY (SystemKey) 
        REFERENCES System(SystemKey),
    
    INDEX IX_TemplateMetadata_System (SystemKey, IsActive),
    INDEX IX_TemplateMetadata_Active (IsActive)
);
```

**Template File in S3 (JSON format):**
```json
// s3://measure-templates/quickbooks/revenue-by-category/v1.0.0.json
{
  "templateKey": "qb-revenue-by-category",
  "version": "1.0.0",
  "systemKey": "quickbooks",
  
  "systemPrompt": "You are a Measure data retrieval assistant connected to QuickBooks Online via MCP. Use the available MCP tools to retrieve invoice data and calculate the requested revenue.",
  
  "userPromptTemplate": "Get all invoices between {{fromDate}} and {{toDate}} where the item category equals '{{itemCategory}}'. {{#if clientType}}Also filter by client type '{{clientType}}'.{{/if}} Calculate the sum of all invoice line item amounts. Return the result as JSON with the format: {\"value\": <number>, \"currency\": \"USD\", \"invoiceCount\": <number>, \"itemCount\": <number>}",
  
  "parameters": [
    {
      "name": "fromDate",
      "isSystemGenerated": true,
      "description": "Calculated by orchestration engine based on frequency"
    },
    {
      "name": "toDate",
      "isSystemGenerated": true,
      "description": "Calculated by orchestration engine based on frequency"
    },
    {
      "name": "itemCategory",
      "isSystemGenerated": false,
      "description": "User-selected item category"
    },
    {
      "name": "clientType",
      "isSystemGenerated": false,
      "description": "Optional client type filter"
    }
  ],
  
  "expectedResponseSchema": {
    "type": "object",
    "properties": {
      "value": { "type": "number" },
      "currency": { "type": "string" },
      "invoiceCount": { "type": "number" },
      "itemCount": { "type": "number" }
    },
    "required": ["value"]
  },
  
  "validationRules": {
    "valueMin": 0,
    "valueMax": 1000000000
  }
}
```

**Seeded Data:**
```csharp
public static class TemplateKeys
{
    public const string QbRevenueByCategory = "qb-revenue-by-category";
    public const string QbGrossProfitMargin = "qb-gross-profit-margin";
    public const string SfCustomerAcquisitionCost = "sf-customer-acquisition-cost";
    public const string HsAvgTimeToResolve = "hs-avg-time-to-resolve";
}

public static class TemplateMetadataSeed
{
    public static List<TemplateMetadata> GetSeedData() => new()
    {
        new() 
        { 
            TemplateKey = TemplateKeys.QbRevenueByCategory,
            Name = "QuickBooks Revenue by Category",
            SystemKey = SystemKeys.QuickBooks,
            S3Bucket = "measure-integration-templates",
            S3Key = "templates/quickbooks/revenue-by-category/v1.0.0.json",
            Version = "1.0.0",
            IsActive = true
        },
        // ... more templates
    };
}
```

### 2.5 SystemMeasureConfig

**Purpose:** Links System + MeasureCatalog + Template (one per combination)

**Managed By:** Developers (seeded in code)

**Admin Can:** View only

```sql
CREATE TABLE SystemMeasureConfig (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    SystemKey NVARCHAR(50) NOT NULL,
    MeasureCatalogId UNIQUEIDENTIFIER NOT NULL,
    TemplateKey NVARCHAR(100) NOT NULL, -- References TemplateMetadata
    
    -- Display
    DisplayName NVARCHAR(200), -- Optional override
    Description NVARCHAR(MAX), -- System-specific description
    
    -- Metadata
    Notes NVARCHAR(MAX),
    DataSourceDescription NVARCHAR(500),
    
    -- Status
    IsActive BIT NOT NULL DEFAULT 1,
    IsBeta BIT NOT NULL DEFAULT 0,
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2,
    
    CONSTRAINT FK_SystemMeasureConfig_System 
        FOREIGN KEY (SystemKey) 
        REFERENCES System(SystemKey),
    CONSTRAINT FK_SystemMeasureConfig_MeasureCatalog 
        FOREIGN KEY (MeasureCatalogId) 
        REFERENCES MeasureCatalog(Id),
    CONSTRAINT FK_SystemMeasureConfig_Template 
        FOREIGN KEY (TemplateKey) 
        REFERENCES TemplateMetadata(TemplateKey),
    
    -- ONE template per System-Measure combination
    CONSTRAINT UQ_SystemMeasureConfig_SystemMeasure 
        UNIQUE (SystemKey, MeasureCatalogId),
    
    INDEX IX_SystemMeasureConfig_System (SystemKey, IsActive),
    INDEX IX_SystemMeasureConfig_MeasureCatalog (MeasureCatalogId, IsActive),
    INDEX IX_SystemMeasureConfig_Template (TemplateKey)
);
```

**Seeded Data:**
```csharp
public static class SystemMeasureConfigSeed
{
    public static List<SystemMeasureConfig> GetSeedData() => new()
    {
        new() 
        { 
            SystemKey = SystemKeys.QuickBooks,
            MeasureCatalogId = GetMeasureCatalogId(MeasureCatalogKeys.RevenueByCategory),
            TemplateKey = TemplateKeys.QbRevenueByCategory,
            IsActive = true
        },
        new() 
        { 
            SystemKey = SystemKeys.Salesforce,
            MeasureCatalogId = GetMeasureCatalogId(MeasureCatalogKeys.CustomerAcquisitionCost),
            TemplateKey = TemplateKeys.SfCustomerAcquisitionCost,
            IsActive = true
        },
        // ... more configurations
    };
}
```

### 2.6 SystemMeasureParameterConfig

**Purpose:** Defines USER-CONFIGURABLE parameters (excludes system-generated dates)

**Managed By:** Developers (seeded in code)

**Admin Can:** View only

**Important:** Does NOT include fromDate/toDate - those are auto-calculated

```sql
CREATE TABLE SystemMeasureParameterConfig (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    SystemMeasureConfigId UNIQUEIDENTIFIER NOT NULL,
    ParameterSeq INT NOT NULL, -- Display order
    ParameterKey NVARCHAR(100) NOT NULL, -- Code constant: 'itemCategory', 'clientType'
    DisplayName NVARCHAR(200) NOT NULL,
    Description NVARCHAR(500),
    DataType NVARCHAR(20) NOT NULL, -- 'string', 'number', 'enum', 'multi-select'
    
    -- Parameter behavior
    IsRequired BIT NOT NULL DEFAULT 0,
    AllowsMultipleValues BIT NOT NULL DEFAULT 0,
    
    -- Value source
    ValueSourceType NVARCHAR(20) NOT NULL DEFAULT 'mcp', -- 'mcp', 'static', 'user-input'
    McpToolName NVARCHAR(100), -- e.g., 'get_item_categories', 'list_clients'
    StaticValues NVARCHAR(MAX), -- JSON array if ValueSourceType = 'static'
    
    -- Validation
    ValidationRules NVARCHAR(MAX), -- JSON
    Placeholder NVARCHAR(200),
    HelpText NVARCHAR(500),
    
    -- Status
    IsActive BIT NOT NULL DEFAULT 1,
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2,
    
    CONSTRAINT FK_ParamConfig_SystemMeasureConfig 
        FOREIGN KEY (SystemMeasureConfigId) 
        REFERENCES SystemMeasureConfig(Id) ON DELETE CASCADE,
    
    CONSTRAINT UQ_ParamConfig_SeqPerConfig 
        UNIQUE (SystemMeasureConfigId, ParameterSeq),
    
    INDEX IX_ParamConfig_SystemMeasureConfig (SystemMeasureConfigId, ParameterSeq)
);
```

**Seeded Data:**
```csharp
public static class ParameterKeys
{
    // User-configurable parameters
    public const string ItemCategory = "itemCategory";
    public const string ClientType = "clientType";
    public const string SupportTier = "supportTier";
    public const string Priority = "priority";
    
    // NOTE: fromDate and toDate are NOT here - they're system-generated
}

public static class SystemMeasureParameterConfigSeed
{
    public static List<SystemMeasureParameterConfig> GetSeedData() => new()
    {
        // QuickBooks Revenue by Category parameters
        new() 
        { 
            SystemMeasureConfigId = GetConfigId(SystemKeys.QuickBooks, MeasureCatalogKeys.RevenueByCategory),
            ParameterSeq = 1,
            ParameterKey = ParameterKeys.ItemCategory,
            DisplayName = "Item Category",
            Description = "Select the product/service category to track",
            DataType = "enum",
            IsRequired = true,
            ValueSourceType = "mcp",
            McpToolName = "get_item_categories",
            HelpText = "This will show categories from your QuickBooks"
        },
        new() 
        { 
            SystemMeasureConfigId = GetConfigId(SystemKeys.QuickBooks, MeasureCatalogKeys.RevenueByCategory),
            ParameterSeq = 2,
            ParameterKey = ParameterKeys.ClientType,
            DisplayName = "Client Type",
            Description = "Optional: Filter by client type",
            DataType = "enum",
            IsRequired = false,
            ValueSourceType = "mcp",
            McpToolName = "get_client_types",
            HelpText = "Leave blank to include all client types"
        },
        // ... more parameters
    };
}
```

---

## 3. Instance Data Tables (User-Managed)

### 3.1 Measures (EXISTING - Minor Updates)

```sql
-- EXISTING TABLE - Add these columns:
ALTER TABLE Measures
ADD MeasureCatalogId UNIQUEIDENTIFIER NULL,
    IsCustom BIT NOT NULL DEFAULT 1,
    CONSTRAINT FK_Measure_MeasureCatalog 
        FOREIGN KEY (MeasureCatalogId) 
        REFERENCES MeasureCatalog(Id);

CREATE INDEX IX_Measure_Catalog ON Measures(MeasureCatalogId) WHERE MeasureCatalogId IS NOT NULL;
```

### 3.2 ConnectionConfiguration (NEW)

**Purpose:** Tenant's connections to external systems

**Managed By:** Users

```sql
CREATE TABLE ConnectionConfiguration (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    TenantId UNIQUEIDENTIFIER NOT NULL,
    SystemKey NVARCHAR(50) NOT NULL,
    
    -- User-provided details
    DisplayName NVARCHAR(200) NOT NULL, -- e.g., "My QuickBooks Company A"
    Description NVARCHAR(500), -- Optional friendly description
    
    -- Authentication (all credentials encrypted)
    AuthType NVARCHAR(20) NOT NULL, -- 'oauth2', 'credentials', 'api-key'
    EncryptedCredentials NVARCHAR(MAX) NOT NULL, -- JSON blob, encrypted
    TokenExpiresAt DATETIME2,
    
    -- Connection metadata
    InstanceUrl NVARCHAR(500),
    ApiVersion NVARCHAR(20),
    TenantIdentifier NVARCHAR(200), -- System's ID for this tenant (e.g., Realm ID)
    
    -- Health tracking
    IsActive BIT NOT NULL DEFAULT 1,
    LastSuccessfulConnection DATETIME2,
    LastFailedConnection DATETIME2,
    LastErrorMessage NVARCHAR(MAX),
    ConsecutiveFailures INT NOT NULL DEFAULT 0,
    
    -- Usage tracking
    TotalRequestsCount INT NOT NULL DEFAULT 0,
    LastRequestAt DATETIME2,
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy UNIQUEIDENTIFIER NOT NULL,
    UpdatedAt DATETIME2,
    UpdatedBy UNIQUEIDENTIFIER,
    
    CONSTRAINT FK_Connection_Tenant 
        FOREIGN KEY (TenantId) 
        REFERENCES Tenants(Id),
    CONSTRAINT FK_Connection_System 
        FOREIGN KEY (SystemKey) 
        REFERENCES System(SystemKey),
    
    INDEX IX_Connection_Tenant (TenantId, IsActive),
    INDEX IX_Connection_System (SystemKey),
    INDEX IX_Connection_TenantSystem (TenantId, SystemKey) -- Support multiple connections per system
);
```

**Note:** User CAN have multiple connections to same system (e.g., "QuickBooks Company A", "QuickBooks Company B")

### 3.3 MeasureIntegration (NEW)

**Purpose:** Links a Measure to a Connection with parameter values and schedule

**Managed By:** Users

**Important:** 
- Dates (fromDate, toDate) are NOT stored here
- Only user-configurable parameter values are stored
- Frequency determines how dates are calculated

```sql
CREATE TABLE MeasureIntegration (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    TenantId UNIQUEIDENTIFIER NOT NULL,
    MeasureId UNIQUEIDENTIFIER NOT NULL,
    ConnectionId UNIQUEIDENTIFIER NOT NULL,
    SystemMeasureConfigId UNIQUEIDENTIFIER NOT NULL,
    
    -- User-configured parameters (EXCLUDES dates)
    ParameterValues NVARCHAR(MAX) NOT NULL, -- JSON: {"itemCategory": "Machinery", "clientType": null}
    
    -- Schedule configuration
    Frequency NVARCHAR(20) NOT NULL, -- ENUM: 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    ScheduleTime NVARCHAR(10), -- e.g., '06:00' for daily at 6 AM
    ScheduleDayOfWeek INT, -- 0-6 for weekly (0=Sunday)
    ScheduleDayOfMonth INT, -- 1-31 for monthly
    IsEnabled BIT NOT NULL DEFAULT 1,
    
    -- Execution tracking
    NextScheduledRun DATETIME2,
    LastExecutionAt DATETIME2,
    LastExecutionStatus NVARCHAR(20), -- 'success', 'failed', 'running', 'partial'
    LastExecutionDuration INT, -- milliseconds
    LastResultValue DECIMAL(18, 4),
    LastErrorMessage NVARCHAR(MAX),
    
    -- Date range used in last execution (for reference)
    LastExecutionFromDate DATETIME2,
    LastExecutionToDate DATETIME2,
    
    -- Reliability tracking
    ConsecutiveFailures INT NOT NULL DEFAULT 0,
    TotalExecutions INT NOT NULL DEFAULT 0,
    SuccessfulExecutions INT NOT NULL DEFAULT 0,
    FailedExecutions INT NOT NULL DEFAULT 0,
    
    -- Performance
    AverageExecutionTime INT, -- milliseconds
    AverageCost DECIMAL(10, 6), -- USD
    
    -- Audit
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CreatedBy UNIQUEIDENTIFIER NOT NULL,
    UpdatedAt DATETIME2,
    UpdatedBy UNIQUEIDENTIFIER,
    
    CONSTRAINT FK_MeasureIntegration_Tenant 
        FOREIGN KEY (TenantId) 
        REFERENCES Tenants(Id),
    CONSTRAINT FK_MeasureIntegration_Measure 
        FOREIGN KEY (MeasureId) 
        REFERENCES Measures(Id),
    CONSTRAINT FK_MeasureIntegration_Connection 
        FOREIGN KEY (ConnectionId) 
        REFERENCES ConnectionConfiguration(Id),
    CONSTRAINT FK_MeasureIntegration_SystemMeasureConfig 
        FOREIGN KEY (SystemMeasureConfigId) 
        REFERENCES SystemMeasureConfig(Id),
    
    -- A Measure can only have one active integration
    CONSTRAINT UQ_MeasureIntegration_Measure 
        UNIQUE (MeasureId),
    
    INDEX IX_MeasureIntegration_Tenant (TenantId),
    INDEX IX_MeasureIntegration_Schedule (NextScheduledRun, IsEnabled),
    INDEX IX_MeasureIntegration_Connection (ConnectionId),
    INDEX IX_MeasureIntegration_Status (LastExecutionStatus, IsEnabled)
);
```

**Frequency Enum:**
```csharp
public enum IntegrationFrequency
{
    Daily,      // Runs daily at ScheduleTime
    Weekly,     // Runs weekly on ScheduleDayOfWeek at ScheduleTime
    Monthly,    // Runs monthly on ScheduleDayOfMonth at ScheduleTime
    Quarterly,  // Runs quarterly on ScheduleDayOfMonth
    Yearly      // Runs yearly on specific date
}
```

### 3.4 MeasureReadings (EXISTING - Minor Updates)

```sql
ALTER TABLE MeasureReadings
ADD IntegrationId UNIQUEIDENTIFIER NULL,
    DataSource NVARCHAR(50) NOT NULL DEFAULT 'manual', -- 'manual', 'integration', 'import', 'api'
    ExecutionId NVARCHAR(100) NULL, -- Links to Integration Service execution log
    ConfidenceScore DECIMAL(3, 2) NULL,
    DataQuality NVARCHAR(20) NULL,
    CONSTRAINT FK_MeasureReading_Integration 
        FOREIGN KEY (IntegrationId) 
        REFERENCES MeasureIntegration(Id);

CREATE INDEX IX_MeasureReading_Integration ON MeasureReadings(IntegrationId) WHERE IntegrationId IS NOT NULL;
CREATE INDEX IX_MeasureReading_ExecutionId ON MeasureReadings(ExecutionId) WHERE ExecutionId IS NOT NULL;
```

---

## 4. Date Calculation Logic

### 4.1 How Dates Are Calculated

**Orchestration Engine calculates dates based on Frequency:**

```csharp
public class DateCalculator
{
    public static (DateTime fromDate, DateTime toDate) CalculateDateRange(
        IntegrationFrequency frequency,
        DateTime executionDate)
    {
        return frequency switch
        {
            IntegrationFrequency.Daily => 
                CalculateDaily(executionDate),
            
            IntegrationFrequency.Weekly => 
                CalculateWeekly(executionDate),
            
            IntegrationFrequency.Monthly => 
                CalculateMonthly(executionDate),
            
            IntegrationFrequency.Quarterly => 
                CalculateQuarterly(executionDate),
            
            IntegrationFrequency.Yearly => 
                CalculateYearly(executionDate),
            
            _ => throw new ArgumentException("Invalid frequency")
        };
    }
    
    private static (DateTime, DateTime) CalculateDaily(DateTime executionDate)
    {
        // Yesterday to today
        var fromDate = executionDate.Date.AddDays(-1);
        var toDate = executionDate.Date;
        return (fromDate, toDate);
    }
    
    private static (DateTime, DateTime) CalculateWeekly(DateTime executionDate)
    {
        // Last 7 days
        var fromDate = executionDate.Date.AddDays(-7);
        var toDate = executionDate.Date;
        return (fromDate, toDate);
    }
    
    private static (DateTime, DateTime) CalculateMonthly(DateTime executionDate)
    {
        // Previous month
        // Example: Executed on Nov 10 → Oct 1 to Oct 31
        var toDate = new DateTime(executionDate.Year, executionDate.Month, 1).AddDays(-1);
        var fromDate = new DateTime(toDate.Year, toDate.Month, 1);
        return (fromDate, toDate);
    }
    
    private static (DateTime, DateTime) CalculateQuarterly(DateTime executionDate)
    {
        // Previous quarter
        var currentQuarter = (executionDate.Month - 1) / 3 + 1;
        var previousQuarter = currentQuarter == 1 ? 4 : currentQuarter - 1;
        var year = currentQuarter == 1 ? executionDate.Year - 1 : executionDate.Year;
        
        var fromDate = new DateTime(year, (previousQuarter - 1) * 3 + 1, 1);
        var toDate = fromDate.AddMonths(3).AddDays(-1);
        return (fromDate, toDate);
    }
    
    private static (DateTime, DateTime) CalculateYearly(DateTime executionDate)
    {
        // Previous year
        var fromDate = new DateTime(executionDate.Year - 1, 1, 1);
        var toDate = new DateTime(executionDate.Year - 1, 12, 31);
        return (fromDate, toDate);
    }
}
```

### 4.2 Template Parameter Injection

**Orchestration Engine injects BOTH user parameters AND calculated dates:**

```csharp
public class PromptBuilder
{
    public async Task<string> BuildPrompt(
        string templateContent, 
        MeasureIntegration integration,
        DateTime executionDate)
    {
        // 1. Load template from S3
        var template = await LoadTemplateFromS3(integration.TemplateKey);
        
        // 2. Calculate dates based on frequency
        var (fromDate, toDate) = DateCalculator.CalculateDateRange(
            integration.Frequency, 
            executionDate);
        
        // 3. Merge user parameters with system parameters
        var allParameters = new Dictionary<string, object>();
        
        // Add user-configured parameters
        var userParams = JsonSerializer.Deserialize<Dictionary<string, object>>(
            integration.ParameterValues);
        foreach (var param in userParams)
        {
            allParameters[param.Key] = param.Value;
        }
        
        // Add system-generated date parameters
        allParameters["fromDate"] = fromDate.ToString("yyyy-MM-dd");
        allParameters["toDate"] = toDate.ToString("yyyy-MM-dd");
        
        // 4. Render template with Handlebars/Mustache
        var handlebars = Handlebars.Create();
        var templateFunc = handlebars.Compile(template.UserPromptTemplate);
        var renderedPrompt = templateFunc(allParameters);
        
        // 5. Store dates used in execution
        integration.LastExecutionFromDate = fromDate;
        integration.LastExecutionToDate = toDate;
        await UpdateIntegration(integration);
        
        return renderedPrompt;
    }
}
```

**Example:**
```
Template: "Get invoices between {{fromDate}} and {{toDate}} where category = '{{itemCategory}}'"

User configured:
{
  "itemCategory": "Machinery"
}

System calculates (for Monthly on Nov 10):
{
  "fromDate": "2025-10-01",
  "toDate": "2025-10-31"
}

Final prompt:
"Get invoices between 2025-10-01 and 2025-10-31 where category = 'Machinery'"
```

---

## 5. Data Flow Examples

### 5.1 Developer Seeds Reference Data

```csharp
// During deployment/migration
public class Seeder
{
    public async Task SeedReferenceData()
    {
        // 1. Seed categories
        await SeedSystemCategories();
        
        // 2. Seed systems
        await SeedSystems();
        
        // 3. Seed Measure catalog
        await SeedMeasureCatalog();
        
        // 4. Upload templates to S3
        await UploadTemplatesToS3();
        
        // 5. Seed template metadata
        await SeedTemplateMetadata();
        
        // 6. Seed system-Measure configurations
        await SeedSystemMeasureConfigs();
        
        // 7. Seed parameter configurations
        await SeedSystemMeasureParameterConfigs();
    }
    
    private async Task UploadTemplatesToS3()
    {
        var templates = new[]
        {
            new 
            { 
                Key = "qb-revenue-by-category",
                Content = LoadTemplateFile("templates/quickbooks/revenue-by-category.json")
            },
            // ... more templates
        };
        
        foreach (var template in templates)
        {
            await _s3Client.PutObjectAsync(new PutObjectRequest
            {
                BucketName = "measure-integration-templates",
                Key = $"templates/{template.Key}/v1.0.0.json",
                ContentBody = template.Content,
                ContentType = "application/json"
            });
        }
    }
}
```

### 5.2 User Configures Integration

```
1. User connects QuickBooks
   POST /api/v1/connections
   → Creates ConnectionConfiguration

2. User creates Measure "Machinery Revenue"
   POST /api/v1/measures
   {
     "name": "Machinery Revenue",
     "kpiCatalogId": "{revenue-by-category-id}",
     "isCustom": false
   }
   → Creates Measure record

3. User views available integrations
   GET /api/v1/measures/{kpiId}/available-integrations
   
   Backend queries:
   SELECT skc.*
   FROM SystemMeasureConfig skc
   JOIN ConnectionConfiguration cc ON cc.SystemKey = skc.SystemKey
   WHERE cc.TenantId = @tenantId
   AND skc.MeasureCatalogId = @kpiCatalogId
   AND skc.IsActive = 1
   
   Returns: "QuickBooks supports this Measure"

4. User clicks "Enable Integration"
   GET /api/v1/system-measure-configs/{id}/parameters
   
   Returns:
   [
     {
       "parameterKey": "itemCategory",
       "displayName": "Item Category",
       "dataType": "enum",
       "valueSourceType": "mcp",
       "mcpToolName": "get_item_categories"
     },
     {
       "parameterKey": "clientType",
       "displayName": "Client Type",
       "dataType": "enum",
       "valueSourceType": "mcp",
       "mcpToolName": "get_client_types"
     }
   ]

5. User selects parameter values
   For itemCategory:
   GET /api/v1/connections/{connectionId}/parameter-values?toolName=get_item_categories
   
   Backend → Integration Service (internal)
   Integration Service calls MCP
   Returns: ["Electronics", "Machinery", "Services", "Furniture"]
   
   User selects: "Machinery"

6. User configures schedule
   User selects:
   - Frequency: Monthly
   - Day of month: 1 (first day of month)
   - Time: 06:00

7. User saves integration
   POST /api/v1/measure-integrations
   {
     "kpiId": "...",
     "connectionId": "...",
     "systemMeasureConfigId": "...",
     "parameterValues": {
       "itemCategory": "Machinery",
       "clientType": null
     },
     "frequency": "monthly",
     "scheduleDayOfMonth": 1,
     "scheduleTime": "06:00"
   }
   
   Backend creates MeasureIntegration
   Backend calculates NextScheduledRun: Dec 1, 2025 at 06:00
   Backend creates EventBridge schedule
```

### 5.3 Execution Flow

```
1. Dec 1, 2025 at 06:00 → EventBridge fires
   → Publishes to SQS

2. Integration Service receives message
   → Loads full configuration:
   
   GET /internal/measure-integrations/{id}/full-config
   
   Backend returns:
   {
     "integration": {
       "id": "...",
       "frequency": "monthly",
       "parameterValues": {"itemCategory": "Machinery"}
     },
     "systemMeasureConfig": {
       "templateKey": "qb-revenue-by-category"
     },
     "connection": {
       "systemKey": "quickbooks",
       "credentials": {...}
     }
   }

3. Integration Service calculates dates
   Execution date: Dec 1, 2025
   Frequency: Monthly
   → fromDate: Nov 1, 2025
   → toDate: Nov 30, 2025

4. Integration Service loads template from S3
   S3Key: templates/quickbooks/revenue-by-category/v1.0.0.json
   
   Template: "Get invoices between {{fromDate}} and {{toDate}} where category = '{{itemCategory}}'"

5. Integration Service merges parameters
   User params: {"itemCategory": "Machinery"}
   System params: {"fromDate": "2025-11-01", "toDate": "2025-11-30"}
   
   Final prompt: "Get invoices between 2025-11-01 and 2025-11-30 where category = 'Machinery'"

6. Integration Service executes via MCP + AI
   → AI calls MCP tools
   → Returns: {"value": 45000.50, "currency": "USD"}

7. Integration Service stores result
   POST /internal/measure-readings
   {
     "kpiId": "...",
     "value": 45000.50,
     "integrationId": "...",
     "dataSource": "integration"
   }

8. Backend processes
   → Creates MeasureReading
   → Updates Measure.CurrentValue = 45000.50
   → Updates MeasureIntegration.LastExecutionFromDate = Nov 1
   → Updates MeasureIntegration.LastExecutionToDate = Nov 30
   → Calculates next run: Jan 1, 2026 at 06:00
```

---

## 6. Admin UI Simplified

### 6.1 What Admin CAN Do

**View Reference Data:**
- View all Systems
- View all Measure Catalog entries
- View System-Measure mappings
- View Parameters per System-Measure

**Add Manual Measures:**
- Create MeasureCatalog entries for manual data entry
- These won't have SystemMeasureConfig links
- Users can create Measures based on these but without integration

**NOT Allowed:**
- Modify seeded Systems (read-only)
- Modify SystemMeasureConfig links (code-managed)
- Modify Parameters (code-managed)
- Modify templates (S3-managed)

### 6.2 Admin UI Screens

**Screen 1: Systems Overview (Read-Only)**
```
Systems

Finance
  ✓ QuickBooks Online          [5 Measures supported]  [View]
  ✓ Xero                        [3 Measures supported]  [View]
  
CRM
  ✓ Salesforce                  [4 Measures supported]  [View]
  ✓ HubSpot                     [3 Measures supported]  [View]
```

**Screen 2: Measure Catalog**
```
Measure Catalog                                        [+] Add Manual Measure

System-Integrated Measures:
✓ Revenue by Category          [5 systems]  [View Details]
✓ Gross Profit Margin          [2 systems]  [View Details]
✓ Customer Acquisition Cost    [3 systems]  [View Details]

Manual-Only Measures:
○ Employee Engagement Score    [Manual]     [Edit] [Delete]
○ Customer Satisfaction        [Manual]     [Edit] [Delete]
```

**Screen 3: System Measure Details (Read-Only)**
```
QuickBooks Online > Revenue by Category

Template: qb-revenue-by-category (v1.0.0)
Template Location: s3://measure-templates/templates/quickbooks/revenue-by-category/v1.0.0.json
Status: Active

User-Configurable Parameters:
1. Item Category (Required)
   - Type: Enum
   - Source: MCP Tool 'get_item_categories'
   
2. Client Type (Optional)
   - Type: Enum
   - Source: MCP Tool 'get_client_types'

System-Generated Parameters:
- fromDate (calculated by orchestration engine)
- toDate (calculated by orchestration engine)
```

---

## 7. Key Takeaways

### What Changed from Previous Version

**BEFORE:**
- Admin could create/modify systems and Measure configs via UI
- Templates stored in database
- Dates were user parameters

**AFTER:**
- Systems, Measures, SystemMeasureConfigs are **SEEDED** (code-managed)
- Templates stored in **S3** with metadata in DB
- Dates are **AUTO-CALCULATED** by orchestration engine
- Admin can only **VIEW** reference data (and add manual-only Measures)

### Benefits of This Approach

1. **Code-Managed Configuration:** Systems and Measures defined in version-controlled code
2. **S3 Template Storage:** Templates can be versioned and deployed independently
3. **Automated Date Handling:** No user confusion about date ranges
4. **Simplified Admin UI:** Admin doesn't need to manage complex configurations
5. **Consistent Date Logic:** All integrations use same date calculation rules
6. **No Cache Needed:** One-time configuration makes caching unnecessary

### Developer Workflow

```
1. Developer defines new system integration:
   - Add to SystemSeed
   - Add to MeasureCatalogSeed
   - Create template JSON file
   - Upload to S3 during deployment
   - Add to TemplateMetadataSeed
   - Add to SystemMeasureConfigSeed
   - Add to SystemMeasureParameterConfigSeed

2. Run migration/seed:
   - Tables populated
   - Templates uploaded to S3
   - System ready for users

3. Users can now:
   - Connect to new system
   - Enable integrations
   - See parameter dropdowns populated from their data
```

---

## 8. Summary Table

| Table | Managed By | User Can | Admin Can | Source |
|-------|------------|----------|-----------|--------|
| SystemCategory | Developers | View | View | Seeded |
| System | Developers | View | View | Seeded |
| MeasureCatalog | Developers + Admin | View | View + Add manual | Seeded + DB |
| TemplateMetadata | Developers | View | View | Seeded |
| Templates (S3) | Developers | - | View | S3 Files |
| SystemMeasureConfig | Developers | View | View | Seeded |
| SystemMeasureParameterConfig | Developers | View | View | Seeded |
| ConnectionConfiguration | Users | CRUD | View | DB |
| MeasureIntegration | Users | CRUD | View | DB |
| Measures | Users | CRUD | View | DB |
| MeasureReadings | Users + System | View | View | DB |

---

**END OF FINAL DATA MODEL**
