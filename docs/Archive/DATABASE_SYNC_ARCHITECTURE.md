# Database Schema Synchronization Architecture

## 🎯 Problem Statement

Two separate applications (C# .NET API and Python AI service) need to access the same DynamoDB tables with consistent schema definitions and type safety.

## 🏗️ **Option 1: Shared Schema-as-Code (RECOMMENDED)**

### Architecture Overview

```
shared-schema/
├── dynamodb/
│   ├── tables.yaml           # Master table definitions
│   ├── migrations/           # Schema version history
│   │   ├── v1.0.0.yaml      # Initial schema
│   │   ├── v1.1.0.yaml      # Add user preferences
│   │   └── v1.2.0.yaml      # Add conversation metadata
│   └── docs/
│       ├── data-model.md    # Data model documentation
│       └── api-contract.md  # Cross-service contracts
├── types/
│   ├── generators/
│   │   ├── generate-csharp.py
│   │   ├── generate-python.py
│   │   └── generate-typescript.py
│   ├── generated/
│   │   ├── csharp/          # Auto-generated C# models
│   │   ├── python/          # Auto-generated Python models
│   │   └── typescript/      # Auto-generated TS types
│   └── templates/
│       ├── csharp.jinja2
│       ├── python.jinja2
│       └── typescript.jinja2
└── scripts/
    ├── deploy-schema.ps1     # Deploy schema to environments
    ├── generate-types.ps1    # Generate type definitions
    ├── validate-schema.ps1   # Validate schema changes
    └── migrate-schema.ps1    # Run schema migrations
```

### Benefits
✅ **Single Source of Truth** - One schema definition for all services
✅ **Type Safety** - Generated types for each language
✅ **Version Control** - Schema changes tracked with migrations
✅ **Automated Sync** - CI/CD automatically generates types
✅ **Breaking Change Detection** - Validation prevents incompatible changes

### Implementation Process

1. **Extract Current Schema** - Move table definitions to shared location
2. **Create Type Generators** - Scripts to generate C#/Python models
3. **Setup CI/CD Pipeline** - Automatically sync on schema changes
4. **Migrate Existing Code** - Update both projects to use generated types

---

## 🏗️ **Option 2: Database-First with Code Generation**

Use AWS tools to generate models directly from deployed DynamoDB tables.

### Architecture
```
DynamoDB Tables (Source of Truth)
    ↓
AWS CLI + Custom Scripts
    ↓
Generated Models → pp_api/ & pp_ai/
```

### Benefits
✅ **Minimal Setup** - Leverage existing AWS tooling
✅ **Always in Sync** - Generate from live database
✅ **No Schema Drift** - Database is the authority

### Drawbacks
❌ **No Version Control** - Schema changes not tracked
❌ **Runtime Discovery** - Must connect to DB to know schema
❌ **Limited Type Safety** - Basic types only

---

## 🏗️ **Option 3: Shared Data Access Layer**

Create a separate microservice that owns all database operations.

### Architecture
```
pp_api (C#) ──────┐
                  ├─→ shared-data-service ──→ DynamoDB
pp_ai (Python) ───┘
```

### Benefits
✅ **Centralized Logic** - One place for all DB operations
✅ **Consistent APIs** - REST/GraphQL interface
✅ **Easy to Secure** - Single point of access control

### Drawbacks
❌ **Network Overhead** - Extra service call for every operation
❌ **Complexity** - Additional service to maintain
❌ **Latency** - Not suitable for high-performance scenarios

---

## 🏗️ **Option 4: Event-Driven Synchronization**

Use DynamoDB Streams + EventBridge to keep schemas in sync.

### Architecture
```
DynamoDB ──→ DynamoDB Streams ──→ EventBridge ──→ Schema Update Services
```

### Benefits
✅ **Real-time Sync** - Immediate propagation of changes
✅ **Loose Coupling** - Services remain independent
✅ **Audit Trail** - All changes tracked

### Drawbacks
❌ **Eventual Consistency** - Temporary inconsistencies possible
❌ **Complex Setup** - Many moving parts
❌ **Debugging Difficulty** - Harder to trace issues

---

## 🎯 **Recommendation: Option 1 - Shared Schema-as-Code**

This is the most robust solution for your use case because:

1. **You have control** over both codebases
2. **Type safety** is critical for both C# and Python
3. **Schema evolution** needs to be carefully managed
4. **CI/CD integration** can automate the entire process

### Next Steps

1. **Create shared-schema directory structure**
2. **Extract existing table definitions from coaching/template.yaml**
3. **Build type generators for C# and Python**
4. **Setup CI/CD pipeline for automatic synchronization**
5. **Migrate both projects to use generated types**

Would you like me to help implement Option 1? I can start by creating the shared schema structure and extracting your current table definitions.