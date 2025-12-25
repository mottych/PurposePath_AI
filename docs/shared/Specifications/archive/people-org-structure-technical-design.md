# People & Organizational Structure - Technical Design Document

**Document Version:** 1.0  
**Created:** December 21, 2025  
**Status:** Draft - Pending Frontend Review  

---

## Table of Contents

1. [Overview](#1-overview)
2. [Impact Analysis](#2-impact-analysis)
3. [New Domain Entities](#3-new-domain-entities)
4. [User Entity Refactoring](#4-user-entity-refactoring)
5. [Assignment System Changes](#5-assignment-system-changes)
6. [Database Schema](#6-database-schema)
7. [API Endpoints](#7-api-endpoints)
8. [Implementation Phases](#8-implementation-phases)
9. [Migration Strategy](#9-migration-strategy)
10. [Testing Strategy](#10-testing-strategy)

---

## 1. Overview

This document details the technical implementation of the People & Organizational Structure module, including:
- New entities (Person, Role, PersonType, etc.)
- Refactoring of the User entity
- Changes to existing assignment patterns
- API endpoint specifications
- Migration approach

---

## 2. Impact Analysis

### 2.1 Entities Requiring Changes

| Entity | Current State | Required Changes |
|--------|---------------|------------------|
| **User** | Contains FirstName, LastName, Email, Phone | Add PersonId; Remove FirstName, LastName, Phone; Rename Email to Username |
| **Action** | AssignedPersonId: UserId | Change to PersonId |
| **Issue** | OwnerId: UserId | Change to PersonId |
| **Kpi** | OwnerId: UserId | Change to PersonId |
| **Goal** | OwnerId: UserId | Change to PersonId |
| **Strategy** | OwnerId: UserId | Change to PersonId |
| **Subscription** | OwnerId: UserId | Keep as UserId (billing is user-specific) |

### 2.2 Files Requiring Modification

#### Domain Layer
```
PurposePath.Domain/
├── Entities/
│   ├── User.cs                 # MAJOR: Remove name/phone, add PersonId
│   ├── Action.cs               # MINOR: Change AssignedPersonId type
│   ├── Issue.cs                # MINOR: Change OwnerId type
│   ├── Kpi.cs                  # MINOR: Change OwnerId type
│   ├── Goal.cs                 # MINOR: Change OwnerId type
│   ├── Strategy.cs             # MINOR: Change OwnerId type
│   ├── Person.cs               # NEW
│   ├── PersonType.cs           # NEW
│   ├── PersonTag.cs            # NEW
│   ├── PersonTagAssignment.cs  # NEW
│   ├── Role.cs                 # NEW
│   ├── PersonRoleAssignment.cs # NEW
│   ├── RoleRelationshipType.cs # NEW
│   └── RoleRelationship.cs     # NEW
├── ValueObjects/
│   ├── PersonId.cs             # NEW
│   ├── PersonTypeId.cs         # NEW
│   ├── PersonTagId.cs          # NEW
│   ├── RoleId.cs               # NEW
│   ├── RoleRelationshipTypeId.cs # NEW
│   └── RoleRelationshipId.cs   # NEW
├── Repositories/
│   ├── IPersonRepository.cs         # NEW
│   ├── IPersonTypeRepository.cs     # NEW
│   ├── IPersonTagRepository.cs      # NEW
│   ├── IRoleRepository.cs           # NEW
│   ├── IPersonRoleRepository.cs     # NEW
│   ├── IRoleRelationshipRepository.cs # NEW
│   └── IRoleRelationshipTypeRepository.cs # NEW
├── Events/
│   ├── PersonCreatedEvent.cs        # NEW
│   ├── PersonRoleAssignedEvent.cs   # NEW
│   └── RoleCreatedEvent.cs          # NEW
└── Services/
    └── IPersonDomainService.cs      # NEW
```

#### Infrastructure Layer
```
PurposePath.Infrastructure/
├── DataModels/
│   ├── UserDataModel.cs             # MODIFY: Remove name/phone, add PersonId
│   ├── ActionDataModel.cs           # VERIFY: AssignedPersonId
│   ├── PersonDataModel.cs           # NEW
│   ├── PersonTypeDataModel.cs       # NEW
│   ├── PersonTagDataModel.cs        # NEW
│   ├── PersonTagAssignmentDataModel.cs # NEW
│   ├── RoleDataModel.cs             # NEW
│   ├── PersonRoleAssignmentDataModel.cs # NEW
│   ├── RoleRelationshipTypeDataModel.cs # NEW
│   └── RoleRelationshipDataModel.cs # NEW
├── Repositories/
│   ├── DynamoDbPersonRepository.cs       # NEW
│   ├── DynamoDbPersonTypeRepository.cs   # NEW
│   ├── DynamoDbPersonTagRepository.cs    # NEW
│   ├── DynamoDbRoleRepository.cs         # NEW
│   ├── DynamoDbPersonRoleRepository.cs   # NEW
│   ├── DynamoDbRoleRelationshipRepository.cs # NEW
│   └── DynamoDbRoleRelationshipTypeRepository.cs # NEW
└── Mappers/
    ├── PersonMapper.cs              # NEW
    ├── RoleMapper.cs                # NEW
    └── UserMapper.cs                # MODIFY
```

#### Application Layer
```
PurposePath.Application/
├── Commands/
│   ├── Person/                      # NEW folder
│   │   ├── CreatePersonCommand.cs
│   │   ├── UpdatePersonCommand.cs
│   │   └── AssignPersonToRoleCommand.cs
│   ├── Role/                        # NEW folder
│   │   ├── CreateRoleCommand.cs
│   │   ├── UpdateRoleCommand.cs
│   │   └── ApplyRoleTemplateCommand.cs
│   └── PersonType/                  # NEW folder
│       ├── CreatePersonTypeCommand.cs
│       └── UpdatePersonTypeCommand.cs
├── Queries/
│   ├── Person/                      # NEW folder
│   │   ├── GetPersonQuery.cs
│   │   ├── GetPeopleQuery.cs
│   │   └── GetAssignablePeopleQuery.cs
│   ├── Role/                        # NEW folder
│   │   ├── GetRoleQuery.cs
│   │   ├── GetRolesQuery.cs
│   │   └── GetOrgChartQuery.cs
│   └── PersonType/                  # NEW folder
└── Services/
    ├── IPersonApplicationService.cs # NEW
    └── PersonApplicationService.cs  # NEW
```

#### API Layer (Traction Lambda - People/Roles endpoints)
```
Services/PurposePath.Traction.Lambda/
├── Controllers/
│   ├── PeopleController.cs          # NEW
│   ├── PersonTypesController.cs     # NEW
│   ├── RolesController.cs           # NEW
│   └── RoleRelationshipsController.cs # NEW
├── DTOs/
│   ├── Requests/
│   │   ├── CreatePersonRequest.cs
│   │   ├── UpdatePersonRequest.cs
│   │   ├── CreateRoleRequest.cs
│   │   └── AssignRoleRequest.cs
│   └── Responses/
│       ├── PersonResponse.cs
│       ├── PersonListItemResponse.cs
│       ├── RoleResponse.cs
│       └── OrgChartResponse.cs
└── Validators/
    ├── CreatePersonRequestValidator.cs
    └── CreateRoleRequestValidator.cs
```

#### Admin Lambda (Role Templates)
```
Services/PurposePath.Admin.Lambda/
├── Controllers/
│   └── RoleTemplatesController.cs   # NEW
└── DTOs/
    ├── RoleTemplateRequest.cs
    └── RoleTemplateResponse.cs
```

---

## 3. New Domain Entities

### 3.1 Person Entity

```csharp
namespace PurposePath.Domain.Entities;

public class Person : FullyAuditableEntity
{
    public PersonId Id { get; private set; }
    public TenantId TenantId { get; private set; }
    public string FirstName { get; private set; }
    public string LastName { get; private set; }
    public Email? Email { get; private set; }
    public bool IsEmailVerified { get; private set; }  // Moved from User
    public string? Phone { get; private set; }
    public string? Title { get; private set; }
    public PersonTypeId PersonTypeId { get; private set; }
    public bool IsActive { get; private set; }
    public bool IsAssignable { get; private set; }
    public string? Notes { get; private set; }
    public UserId? LinkedUserId { get; private set; }

    // Factory method
    public static Person Create(
        PersonId id,
        TenantId tenantId,
        string firstName,
        string lastName,
        PersonTypeId personTypeId,
        bool isAssignableByDefault,
        Email? email = null,
        string? phone = null,
        string? title = null,
        string? notes = null,
        bool isEmailVerified = false);

    // Business methods
    public void UpdatePersonalInfo(string firstName, string lastName, Email? email, string? phone, string? title);
    public void UpdateClassification(PersonTypeId typeId, bool isAssignable);
    public void SetNotes(string? notes);
    public void VerifyEmail();
    public void Activate();
    public void Deactivate();
    public void LinkToUser(UserId userId);
    public void UnlinkFromUser();
}
```

### 3.2 Role Entity

```csharp
namespace PurposePath.Domain.Entities;

public class Role : FullyAuditableEntity
{
    public RoleId Id { get; private set; }
    public TenantId TenantId { get; private set; }
    public string Code { get; private set; }
    public string Name { get; private set; }
    public string Accountability { get; private set; }
    public RoleId? ReportsToRoleId { get; private set; }
    public bool IsActive { get; private set; }

    // Factory method
    public static Role Create(
        RoleId id,
        TenantId tenantId,
        string code,
        string name,
        string accountability,
        RoleId? reportsToRoleId = null);

    // Business methods
    public void Update(string name, string accountability);
    public void SetReportsTo(RoleId? reportsToRoleId);
    public void Activate();
    public void Deactivate();

    // Validation - prevents circular reporting
    public bool WouldCreateCircularReference(RoleId proposedParentId, IEnumerable<Role> allRoles);
}
```

### 3.3 PersonRoleAssignment Entity

```csharp
namespace PurposePath.Domain.Entities;

public class PersonRoleAssignment : AuditableEntity
{
    public PersonRoleAssignmentId Id { get; private set; }
    public PersonId PersonId { get; private set; }
    public RoleId RoleId { get; private set; }
    public bool IsPrimary { get; private set; }
    public DateTime EffectiveDate { get; private set; }
    public DateTime? TerminationDate { get; private set; }

    public bool IsActive => TerminationDate == null || TerminationDate > DateTime.UtcNow;

    // Factory method
    public static PersonRoleAssignment Create(
        PersonRoleAssignmentId id,
        PersonId personId,
        RoleId roleId,
        bool isPrimary,
        DateTime effectiveDate);

    // Business methods
    public void Terminate(DateTime terminationDate);
    public void SetPrimary(bool isPrimary);
}
```

### 3.4 Value Objects

```csharp
// PersonId.cs
public record PersonId(Guid Value)
{
    public static PersonId New() => new(Guid.NewGuid());
    public static PersonId From(string value) => new(Guid.Parse(value));
    public override string ToString() => Value.ToString();
}

// RoleId.cs
public record RoleId(Guid Value)
{
    public static RoleId New() => new(Guid.NewGuid());
    public static RoleId From(string value) => new(Guid.Parse(value));
    public override string ToString() => Value.ToString();
}

// PersonTypeId.cs, PersonTagId.cs, etc. follow same pattern
```

### 3.5 RoleRelationshipType Entity

```csharp
namespace PurposePath.Domain.Entities;

public class RoleRelationshipType : AuditableEntity
{
    public RoleRelationshipTypeId Id { get; private set; }
    public TenantId TenantId { get; private set; }
    public string Code { get; private set; }
    public string Name { get; private set; }
    public string ForwardVerb { get; private set; }
    public string ReverseVerb { get; private set; }
    public bool IsActive { get; private set; }

    // Factory method
    public static RoleRelationshipType Create(
        RoleRelationshipTypeId id,
        TenantId tenantId,
        string code,
        string name,
        string forwardVerb,
        string reverseVerb);

    // Business methods
    public void Update(string name, string forwardVerb, string reverseVerb);
    public void Activate();
    public void Deactivate();
}
```

### 3.6 RoleRelationship Entity

```csharp
namespace PurposePath.Domain.Entities;

public class RoleRelationship : AuditableEntity
{
    public RoleRelationshipId Id { get; private set; }
    public TenantId TenantId { get; private set; }
    public RoleId FromRoleId { get; private set; }
    public RoleId ToRoleId { get; private set; }
    public RoleRelationshipTypeId RelationshipTypeId { get; private set; }

    // Factory method
    public static RoleRelationship Create(
        RoleRelationshipId id,
        TenantId tenantId,
        RoleId fromRoleId,
        RoleId toRoleId,
        RoleRelationshipTypeId relationshipTypeId);

    // Validation
    public static void ValidateNotSelfReference(RoleId fromRoleId, RoleId toRoleId);
}
```

### 3.7 RoleRelationship Repository Interface

```csharp
namespace PurposePath.Domain.Repositories;

public interface IRoleRelationshipRepository
{
    Task<RoleRelationship?> GetByIdAsync(RoleRelationshipId id, CancellationToken cancellationToken = default);
    Task<IEnumerable<RoleRelationship>> GetByRoleIdAsync(RoleId roleId, CancellationToken cancellationToken = default);
    Task<IEnumerable<RoleRelationship>> GetByTenantIdAsync(TenantId tenantId, CancellationToken cancellationToken = default);
    Task<bool> ExistsAsync(RoleId fromRoleId, RoleId toRoleId, RoleRelationshipTypeId typeId, CancellationToken cancellationToken = default);
    Task CreateAsync(RoleRelationship relationship, CancellationToken cancellationToken = default);
    Task DeleteAsync(RoleRelationshipId id, CancellationToken cancellationToken = default);
    Task DeleteByRoleIdAsync(RoleId roleId, CancellationToken cancellationToken = default);
}

public interface IRoleRelationshipTypeRepository
{
    Task<RoleRelationshipType?> GetByIdAsync(RoleRelationshipTypeId id, CancellationToken cancellationToken = default);
    Task<RoleRelationshipType?> GetByCodeAsync(TenantId tenantId, string code, CancellationToken cancellationToken = default);
    Task<IEnumerable<RoleRelationshipType>> GetByTenantIdAsync(TenantId tenantId, bool activeOnly = true, CancellationToken cancellationToken = default);
    Task<bool> HasRelationshipsAsync(RoleRelationshipTypeId typeId, CancellationToken cancellationToken = default);
    Task CreateAsync(RoleRelationshipType type, CancellationToken cancellationToken = default);
    Task UpdateAsync(RoleRelationshipType type, CancellationToken cancellationToken = default);
}
```

### 3.8 RoleRelationship DataModels

```csharp
[DynamoDBTable("purposepath-role-relationship-types")]
public class RoleRelationshipTypeDataModel : BaseDataModel
{
    [DynamoDBHashKey("id")]
    public string Id { get; set; } = string.Empty;

    [DynamoDBProperty("tenant_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("tenant-index")]
    public string TenantId { get; set; } = string.Empty;

    [DynamoDBProperty("code")]
    public string Code { get; set; } = string.Empty;

    [DynamoDBProperty("name")]
    public string Name { get; set; } = string.Empty;

    [DynamoDBProperty("forward_verb")]
    public string ForwardVerb { get; set; } = string.Empty;

    [DynamoDBProperty("reverse_verb")]
    public string ReverseVerb { get; set; } = string.Empty;

    [DynamoDBProperty("is_active")]
    public bool IsActive { get; set; } = true;

    // GSI: tenant-code-index for unique code lookup
    [DynamoDBGlobalSecondaryIndexHashKey("tenant-code-index")]
    public string TenantCodeIndex => $"{TenantId}#{Code}";
}

[DynamoDBTable("purposepath-role-relationships")]
public class RoleRelationshipDataModel : BaseDataModel
{
    [DynamoDBHashKey("id")]
    public string Id { get; set; } = string.Empty;

    [DynamoDBProperty("tenant_id")]
    public string TenantId { get; set; } = string.Empty;

    [DynamoDBProperty("from_role_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("from-role-index")]
    public string FromRoleId { get; set; } = string.Empty;

    [DynamoDBProperty("to_role_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("to-role-index")]
    public string ToRoleId { get; set; } = string.Empty;

    [DynamoDBProperty("relationship_type_id")]
    [DynamoDBGlobalSecondaryIndexHashKey("type-index")]
    public string RelationshipTypeId { get; set; } = string.Empty;

    // Composite key for duplicate detection
    [DynamoDBGlobalSecondaryIndexHashKey("unique-relationship-index")]
    public string UniqueRelationshipKey => $"{FromRoleId}#{ToRoleId}#{RelationshipTypeId}";
}
```

---

## 4. User Entity Refactoring

### 4.1 Current User Entity

```csharp
public class User : FullyAuditableEntity
{
    public UserId Id { get; private set; }
    public Email Email { get; private set; }           // BECOMES Username
    public string FirstName { get; private set; }      // TO REMOVE
    public string LastName { get; private set; }       // TO REMOVE
    public TenantId TenantId { get; private set; }
    public UserStatus Status { get; private set; }
    public bool IsEmailVerified { get; private set; }  // TO REMOVE (moves to Person)
    public string? PasswordHash { get; private set; }
    public string? Phone { get; private set; }         // TO REMOVE
    public string? AvatarUrl { get; private set; }
    public UserPreferences Preferences { get; private set; }
    // ... login tracking fields
}
```

### 4.2 Refactored User Entity

```csharp
public class User : FullyAuditableEntity
{
    public UserId Id { get; private set; }
    public PersonId PersonId { get; private set; }     // NEW - Link to Person
    public string Username { get; private set; }       // RENAMED from Email - Globally unique login identifier
    public TenantId TenantId { get; private set; }
    public UserStatus Status { get; private set; }
    public string? PasswordHash { get; private set; }
    public string? AvatarUrl { get; private set; }
    public UserPreferences Preferences { get; private set; }
    // ... login tracking fields (unchanged)

    // Convenience properties (fetched from linked Person in queries)
    // NOT stored - retrieved via join or separate query
}
```

### 4.3 Username-Based Authentication Changes

**Key Change:** Login identifier changes from email to username.

| Aspect | Before | After |
|--------|--------|-------|
| Login field | `Email` (globally unique) | `Username` (globally unique) |
| Email storage | User table | Person table only |
| Email uniqueness | Global | Per-tenant |
| JWT claims | UserId, TenantId | UserId, TenantId (unchanged) |

**Migration:** Current email values become usernames - rename field only, no data transformation.

**Username Validation Rules:**

| Rule | Description |
|------|-------------|
| Uniqueness | Globally unique across all tenants |
| Length | 3-50 characters |
| Characters | Alphanumeric, dots (.), underscores (_), hyphens (-), at-sign (@) |
| Start | Must start with alphanumeric character |
| Case | Case-insensitive for uniqueness (stored as provided, compared lowercase) |
| Reserved | Cannot use reserved words (admin, system, support, purposepath, etc.) |

**Username Change Rules:**

| Rule | Description |
|------|-------------|
| Rate Limit | Maximum one username change per 30 days |
| Confirmation | Requires current password verification |
| Audit | Username changes logged with timestamp, old/new values, IP address |
| Cooldown | Previous username cannot be claimed by others for 90 days |
| Notification | Email sent to linked Person's email confirming change |

**Authentication Flow Changes:**

```csharp
// Login Request - Before
public record LoginRequest(string Email, string Password);

// Login Request - After
public record LoginRequest(string Username, string Password);

// New Forgot Username Request
public record ForgotUsernameRequest(string Email);
```

**New Endpoint:** `POST /api/auth/forgot-username`
- Input: Email address
- Action: Find all Persons with verified email, get linked usernames
- Output: Email sent with all associated usernames

### 4.4 Transition Strategy

### 4.4 Transition Strategy

**Phase 1: Add PersonId and Username to User (nullable PersonId)**
- Add PersonId column as nullable
- Rename Email column to Username
- Create Person for each existing User (email goes to Person)
- Update User.PersonId to point to Person

**Phase 2: Make PersonId required**
- Make PersonId non-nullable
- Update all queries to join with Person for name/contact

**Phase 3: Remove deprecated fields**
- Remove FirstName, LastName, Phone, IsEmailVerified from User
- Update all mappers and DTOs
- Update login endpoint to use Username parameter

---

## 5. Assignment System Changes

### 5.1 Current Assignment Pattern

```csharp
// Action entity - current
public UserId AssignedPersonId { get; private set; }

// Issue entity - current
public UserId? OwnerId { get; private set; }
```

### 5.2 New Assignment Pattern

```csharp
// Action entity - new
public PersonId AssignedPersonId { get; private set; }

// Issue entity - new
public PersonId? OwnerId { get; private set; }
```

### 5.3 Backward Compatibility

During migration, both UserId and PersonId will reference the same underlying GUID for existing users. This allows:
- Existing data to remain valid
- Frontend to continue sending the same IDs
- Gradual transition without breaking changes

### 5.4 Assignable People Query

```csharp
public interface IPersonRepository
{
    Task<IEnumerable<Person>> GetAssignableAsync(
        TenantId tenantId,
        UserId? currentUserId = null,  // To mark "Me"
        IEnumerable<PersonTagId>? filterByTags = null,
        CancellationToken cancellationToken = default);
}
```

**Response includes:**
- PersonId, Name, Title
- Primary Role (name) if any
- IsCurrentUser flag (true if this Person is linked to currentUserId)

---

## 6. Database Schema

### 6.1 New DynamoDB Tables

| Table Name | Partition Key | Sort Key | Description |
|------------|---------------|----------|-------------|
| purposepath-people | id (PersonId) | - | Person records |
| purposepath-person-types | id (PersonTypeId) | - | Person type definitions |
| purposepath-person-tags | id (PersonTagId) | - | Tag definitions |
| purposepath-person-tag-assignments | person_id | tag_id | Person-Tag M:N |
| purposepath-roles | id (RoleId) | - | Role definitions |
| purposepath-person-role-assignments | id | - | Person-Role assignments |
| purposepath-role-relationship-types | id | - | Relationship type definitions |
| purposepath-role-relationships | id | - | Role-Role relationships |
| purposepath-role-templates | id | - | Admin role templates |
| purposepath-role-template-items | template_id | code | Template role items |

### 6.2 Global Secondary Indexes (GSIs)

**purposepath-people:**
| GSI Name | Partition Key | Sort Key | Purpose |
|----------|---------------|----------|---------|
| tenant-index | tenant_id | - | List people by tenant |
| tenant-email-index | tenant_id | email | Lookup by tenant+email |
| linked-user-index | linked_user_id | - | Find person by linked user |
| tenant-status-index | tenant_id | is_active | Filter active/inactive by tenant |

**purposepath-roles:**
| GSI Name | Partition Key | Sort Key | Purpose |
|----------|---------------|----------|---------|
| tenant-index | tenant_id | - | List roles by tenant |
| tenant-code-index | tenant_id | code | Unique code lookup |
| reports-to-index | reports_to_role_id | - | Find subordinate roles |

**purposepath-person-role-assignments:**
| GSI Name | Partition Key | Sort Key | Purpose |
|----------|---------------|----------|---------|
| person-index | person_id | effective_date | Get person's role history |
| role-index | role_id | effective_date | Get role's assignment history |
| role-active-index | role_id | termination_date | Find current occupant (where termination_date = null) |

**purposepath-role-relationships:**
| GSI Name | Partition Key | Sort Key | Purpose |
|----------|---------------|----------|---------|
| from-role-index | from_role_id | - | Get outgoing relationships |
| to-role-index | to_role_id | - | Get incoming relationships |
| unique-index | from#to#type | - | Prevent duplicate relationships |
| type-index | relationship_type_id | - | Find all relationships of a type |

**purposepath-role-relationship-types:**
| GSI Name | Partition Key | Sort Key | Purpose |
|----------|---------------|----------|---------|
| tenant-index | tenant_id | - | List types by tenant |
| tenant-code-index | tenant_id | code | Unique code lookup |

**purposepath-users (Modified):**
| GSI Name | Change | Purpose |
|----------|--------|---------|
| email-index | RENAME to username-index | Login lookup by username |
| person-index | ADD | Find user by linked person |

### 6.3 Modified Tables

**purposepath-users (Modified)**
- RENAME: `email` → `username` (globally unique)
- ADD: `person_id` (string, GUID)
- ADD GSI: `person-index` on `person_id`
- RENAME GSI: `email-index` → `username-index`
- REMOVE (Phase 3): `first_name`, `last_name`, `phone`, `is_email_verified`

### 6.4 PersonDataModel

```csharp
[DynamoDBTable("purposepath-people")]
public class PersonDataModel : BaseDataModel
{
    [DynamoDBHashKey("id")]
    public string Id { get; set; } = string.Empty;

    [DynamoDBProperty("tenant_id")]
    public string TenantId { get; set; } = string.Empty;

    [DynamoDBProperty("first_name")]
    public string FirstName { get; set; } = string.Empty;

    [DynamoDBProperty("last_name")]
    public string LastName { get; set; } = string.Empty;

    [DynamoDBProperty("email")]
    public string? Email { get; set; }

    [DynamoDBProperty("is_email_verified")]
    public bool IsEmailVerified { get; set; } = false;

    [DynamoDBProperty("phone")]
    public string? Phone { get; set; }

    [DynamoDBProperty("title")]
    public string? Title { get; set; }

    [DynamoDBProperty("person_type_id")]
    public string PersonTypeId { get; set; } = string.Empty;

    [DynamoDBProperty("is_active")]
    public bool IsActive { get; set; } = true;

    [DynamoDBProperty("is_assignable")]
    public bool IsAssignable { get; set; } = true;

    [DynamoDBProperty("notes")]
    public string? Notes { get; set; }

    [DynamoDBProperty("linked_user_id")]
    public string? LinkedUserId { get; set; }

    // GSI Keys
    [DynamoDBGlobalSecondaryIndexHashKey("tenant-index")]
    public string TenantIndex => TenantId;

    [DynamoDBGlobalSecondaryIndexHashKey("tenant-email-index", "tenant-status-index")]
    public string TenantKey => TenantId;

    [DynamoDBGlobalSecondaryIndexRangeKey("tenant-email-index")]
    public string? EmailIndex => Email?.ToLowerInvariant();

    [DynamoDBGlobalSecondaryIndexRangeKey("tenant-status-index")]
    public bool StatusIndex => IsActive;

    [DynamoDBGlobalSecondaryIndexHashKey("linked-user-index")]
    public string? LinkedUserIndex => LinkedUserId;
}
```

---

## 7. API Endpoints

### 7.1 People Endpoints (Traction Service)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/people | List people with filtering |
| GET | /api/people/assignable | Get assignable people for dropdowns |
| GET | /api/people/{id} | Get person details |
| POST | /api/people | Create person |
| PUT | /api/people/{id} | Update person |
| DELETE | /api/people/{id} | Soft delete person |
| POST | /api/people/{id}/activate | Activate a deactivated person |
| POST | /api/people/{id}/deactivate | Deactivate person (terminates role assignments) |
| POST | /api/people/{id}/link-user | Link person to a user account |
| POST | /api/people/{id}/tags | Add tags to person |
| DELETE | /api/people/{id}/tags/{tagId} | Remove tag from person |
| GET | /api/people/{id}/roles | Get person's current role assignments |
| GET | /api/people/{id}/roles/history | Get person's role assignment history |
| POST | /api/people/{id}/roles | Assign role to person |
| PUT | /api/people/{id}/roles/{roleId}/primary | Set role as person's primary |
| DELETE | /api/people/{id}/roles/{roleId} | Unassign role from person |

**Query Parameters for GET /api/people:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status: `active`, `inactive`, `all` (default: `active`) |
| isAssignable | bool? | Filter by assignable flag |
| personTypeId | guid | Filter by person type |
| tags | guid[] | Filter by tags (any match) |
| search | string | Search by name, email, or title |
| page | int | Page number (default: 1) |
| pageSize | int | Items per page (default: 20, max: 100) |
| sortBy | string | Sort field: `name`, `createdAt`, `type` (default: `name`) |
| sortOrder | string | Sort order: `asc`, `desc` (default: `asc`) |

### 7.2 Person Types Endpoints (Traction Service)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/person-types | List person types |
| GET | /api/person-types/{id} | Get person type details |
| POST | /api/person-types | Create person type |
| PUT | /api/person-types/{id} | Update person type |
| DELETE | /api/person-types/{id} | Deactivate person type |

**Query Parameters for GET /api/person-types:**
| Parameter | Type | Description |
|-----------|------|-------------|
| includeInactive | bool | Include inactive types (default: false) |

### 7.3 Person Tags Endpoints (Traction Service)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/person-tags | List available tags |
| POST | /api/person-tags | Create new tag |
| PUT | /api/person-tags/{id} | Update tag name |
| DELETE | /api/person-tags/{id} | Delete tag (cascade removes assignments) |

### 7.4 Roles Endpoints (Traction Service)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/roles | List roles |
| GET | /api/roles/{id} | Get role details |
| POST | /api/roles | Create role |
| PUT | /api/roles/{id} | Update role |
| DELETE | /api/roles/{id} | Deactivate role (terminates assignments, clears ReportsTo) |
| GET | /api/roles/{id}/assignments | Get role's current assignment |
| GET | /api/roles/{id}/assignments/history | Get role's assignment history |
| GET | /api/roles/org-chart | Get org chart data |
| POST | /api/roles/apply-template | Apply role template |
| POST | /api/roles/preview-template | Preview template application (what will be added/skipped) |

**Query Parameters for GET /api/roles:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter: `active`, `inactive`, `all` (default: `active`) |
| hasOccupant | bool? | Filter by occupancy status |
| search | string | Search by name, code, or accountability |
| reportsToRoleId | guid? | Filter by parent role |

### 7.5 Role Relationships Endpoints (Traction Service)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/role-relationship-types | List relationship types |
| GET | /api/role-relationship-types/{id} | Get relationship type details |
| POST | /api/role-relationship-types | Create relationship type |
| PUT | /api/role-relationship-types/{id} | Update relationship type |
| DELETE | /api/role-relationship-types/{id} | Deactivate type (fails if relationships exist) |
| GET | /api/roles/{id}/relationships | Get role's relationships (both directions) |
| POST | /api/roles/{id}/relationships | Add relationship from this role |
| DELETE | /api/roles/{roleId}/relationships/{relId} | Remove relationship |

### 7.6 Role Templates Endpoints (Admin Service)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/role-templates | List all templates |
| GET | /api/admin/role-templates/{id} | Get template details with items |
| POST | /api/admin/role-templates | Create template |
| PUT | /api/admin/role-templates/{id} | Update template |
| DELETE | /api/admin/role-templates/{id} | Delete template |
| POST | /api/admin/role-templates/{id}/items | Add item to template |
| PUT | /api/admin/role-templates/{id}/items/{itemId} | Update template item |
| DELETE | /api/admin/role-templates/{id}/items/{itemId} | Delete template item |

**Query Parameters for GET /api/admin/role-templates:**
| Parameter | Type | Description |
|-----------|------|-------------|
| industry | string | Filter by industry category |
| includeInactive | bool | Include inactive templates |

### 7.7 Authentication Endpoint Changes (Account Service)

| Method | Endpoint | Changes |
|--------|----------|---------|
| POST | /api/auth/login | Change `email` parameter to `username` |
| POST | /api/auth/forgot-username | **NEW** - Send usernames to email address |
| POST | /api/auth/forgot-password | Uses Person email (via linked User) |

### 7.8 User Profile Changes (Account Service)

| Method | Endpoint | Changes |
|--------|----------|---------|
| GET | /api/user/profile | Return Person data for name/contact |
| PUT | /api/user/profile | Update linked Person record |
| PUT | /api/user/username | **NEW** - Change username (requires password confirmation) |

---

## 8. Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Create new entities and infrastructure without breaking existing functionality

1. Create new value objects (PersonId, RoleId, RoleRelationshipTypeId, etc.)
2. Create Person, PersonType, PersonTag entities
3. Create Role, PersonRoleAssignment entities
4. Create RoleRelationshipType, RoleRelationship entities
5. Create all repository interfaces and implementations
6. Create data models and mappers
7. Add PersonId to User entity (nullable)
8. Rename Email to Username in User entity
9. Seed default PersonTypes for existing tenants
10. Create Pulumi infrastructure for new tables

### Phase 2: Data Migration (Week 2)
**Goal:** Migrate existing user data to Person records

1. Create migration script to generate Person for each User
   - Copy email to Person.Email
   - Email becomes Username in User (same value, field renamed)
2. Update User.PersonId to point to Person
3. Verify data integrity
4. Run migration on dev/staging

### Phase 3: People & Roles API (Week 2-3)
**Goal:** Implement new CRUD endpoints

1. Implement People controller and endpoints
2. Implement PersonTypes controller and endpoints
3. Implement PersonTags controller and endpoints
4. Implement Roles controller and endpoints
5. Implement RoleRelationshipTypes controller and endpoints
6. Implement RoleRelationships controller and endpoints
7. Implement Org Chart query endpoint
8. Write unit and integration tests

### Phase 4: Assignment Integration (Week 3)
**Goal:** Update assignment system to use PersonId

1. Create GetAssignablePeople query/endpoint
2. Update Action entity to use PersonId
3. Update Issue entity to use PersonId
4. Update Kpi entity to use PersonId
5. Update Goal entity to use PersonId
6. Update Strategy entity to use PersonId
7. Update all related queries and commands
8. Update frontend-facing response DTOs

### Phase 5: User Refactoring & Authentication Changes (Week 4)
**Goal:** Complete User entity refactoring and switch to username-based auth

1. Update login endpoint to accept `username` instead of `email`
2. Implement new `POST /api/auth/forgot-username` endpoint
3. Update User profile endpoints to use Person data
4. Update authentication to fetch Person data for email
5. Implement `PUT /api/user/username` for username changes
6. Remove deprecated fields from User entity (FirstName, LastName, Phone, IsEmailVerified)
7. Update all User-related mappers and DTOs
8. Comprehensive regression testing

### Phase 6: Role Templates (Week 4)
**Goal:** Implement admin template system

1. Create RoleTemplate and RoleTemplateItem entities
2. Implement Admin API endpoints
3. Implement template application logic
4. Seed initial templates
5. Test template merge behavior

### Phase 7: Testing & Cleanup (Week 5)
**Goal:** Ensure quality and stability

1. E2E testing of all new features
2. Performance testing
3. Documentation updates
4. Code review and cleanup
5. Production deployment preparation

---

## 9. Migration Strategy

### 9.1 Migration Scripts

**Script 1: Create Person for existing Users**
```csharp
// Pseudocode
foreach (var user in await userRepository.GetAllAsync())
{
    // Check if Person already exists for this user
    var existingPerson = await personRepository.GetByLinkedUserIdAsync(user.Id);
    if (existingPerson != null) continue;

    // Get or create default PersonType
    var employeeType = await personTypeRepository.GetByCodeAsync(user.TenantId, "EMPLOYEE");
    
    // Create Person from User data
    // Note: User's email becomes Person's email AND User's username (same value)
    var person = Person.Create(
        PersonId.New(),
        user.TenantId,
        user.FirstName,
        user.LastName,
        employeeType.Id,
        isAssignableByDefault: true,
        email: user.Email,  // Email moves to Person
        phone: user.Phone,
        isEmailVerified: user.IsEmailVerified);  // Email verification moves to Person
    
    person.LinkToUser(user.Id);
    await personRepository.CreateAsync(person);
    
    // Update User: PersonId and rename Email→Username
    user.SetPersonId(person.Id);
    user.SetUsername(user.Email.Value);  // Current email becomes username
    await userRepository.UpdateAsync(user);
}
```

**Script 2: Rename User.Email to User.Username**
```csharp
// DynamoDB attribute rename (data stays the same, just field name changes)
// This is essentially a no-op for existing data since current emails ARE valid usernames
// Just update the attribute name in the data model
```

**Script 2: Update Assignment References**
```csharp
// For each entity type with assignments
// The migration is seamless because PersonId will have the same GUID value
// as the original UserId for migrated records

// Verify integrity
foreach (var action in await actionRepository.GetAllAsync())
{
    var person = await personRepository.GetByIdAsync(PersonId.From(action.AssignedPersonId.ToString()));
    if (person == null)
    {
        // Log warning - orphaned assignment
    }
}
```

### 9.2 Rollback Procedures

1. **Database:** Maintain backup of all tables before migration
2. **Code:** Feature flags for new vs old data access patterns
3. **Scripts:** Idempotent migrations that can be re-run safely

---

## 10. Testing Strategy

### 10.1 Unit Tests

- Person entity creation and validation
- Role hierarchy validation (no circular references)
- PersonRoleAssignment effective dating logic
- PersonType default assignable behavior

### 10.2 Integration Tests

- Person CRUD operations
- Role CRUD operations
- Assignment flow (assign/unassign person to role)
- Org chart query with various structures
- Template application and merge behavior
- User-Person linking

### 10.3 E2E Tests

- Complete person management workflow
- Complete role management workflow
- Assignment dropdown with current user indication
- Org chart visualization data
- User profile updates via Person

### 10.4 Migration Tests

- Verify Person created for all Users
- Verify User.PersonId populated
- Verify assignment references still work
- Verify name/email retrieval works post-migration

---

## Appendix: Endpoint Request/Response Schemas

### Error Response Format

All endpoints return consistent error responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "One or more validation errors occurred",
    "details": [
      { "field": "email", "message": "Email is already in use within this tenant" },
      { "field": "code", "message": "Role code must be unique" }
    ]
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request validation failed |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict (e.g., duplicate code) |
| FORBIDDEN | 403 | Action not allowed (e.g., delete person with linked user) |
| CIRCULAR_REFERENCE | 400 | Role hierarchy would create circular reference |
| PERSON_HAS_ASSIGNMENTS | 400 | Cannot delete person with active role assignments |
| PERSON_HAS_LINKED_USER | 400 | Cannot delete person linked to a user |
| TYPE_IN_USE | 400 | Cannot delete type with existing references |
| RELATIONSHIP_TYPE_IN_USE | 400 | Cannot delete relationship type with existing relationships |

### Create Person Request
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "title": "Senior Engineer",
  "personTypeId": "guid",
  "isAssignable": true,
  "notes": "Works remotely",
  "tags": ["guid1", "guid2"]
}
```

### Person Response
```json
{
  "id": "guid",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "title": "Senior Engineer",
  "personType": {
    "id": "guid",
    "code": "EMPLOYEE",
    "name": "Employee"
  },
  "isActive": true,
  "isAssignable": true,
  "notes": "Works remotely",
  "tags": [
    { "id": "guid1", "name": "Engineering" },
    { "id": "guid2", "name": "Remote" }
  ],
  "primaryRole": {
    "id": "guid",
    "name": "Tech Lead"
  },
  "roles": [
    { "id": "guid", "name": "Tech Lead", "isPrimary": true, "effectiveDate": "2024-01-15" },
    { "id": "guid", "name": "Scrum Master", "isPrimary": false, "effectiveDate": "2024-06-01" }
  ],
  "linkedUserId": "guid",
  "hasSystemAccess": true,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-12-21T14:00:00Z"
}
```

### Assignable Person Response (for dropdowns)
```json
{
  "id": "guid",
  "name": "John Doe",
  "title": "Senior Engineer",
  "primaryRole": "Tech Lead",
  "isCurrentUser": true
}
```

### Create Role Request
```json
{
  "code": "TECH_LEAD",
  "name": "Tech Lead",
  "accountability": "Responsible for technical direction and mentoring of the engineering team",
  "reportsToRoleId": "guid"
}
```

### Org Chart Response
```json
{
  "roles": [
    {
      "id": "guid",
      "code": "CEO",
      "name": "Chief Executive Officer",
      "accountability": "Overall company strategy and vision",
      "reportsToRoleId": null,
      "currentOccupant": {
        "personId": "guid",
        "name": "Jane Smith",
        "title": "CEO & Founder"
      },
      "subordinates": ["guid1", "guid2", "guid3"],
      "relationships": [
        {
          "type": "ADVISES",
          "verb": "advises",
          "targetRole": { "id": "guid", "name": "Board of Directors" }
        }
      ]
    }
  ]
}
```

### Role Relationship Type Request/Response

**Create Role Relationship Type Request:**
```json
{
  "code": "SUPPORT",
  "name": "Support Relationship",
  "forwardVerb": "supports",
  "reverseVerb": "is supported by"
}
```

**Role Relationship Type Response:**
```json
{
  "id": "guid",
  "code": "SUPPORT",
  "name": "Support Relationship",
  "forwardVerb": "supports",
  "reverseVerb": "is supported by",
  "isActive": true,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-12-21T14:00:00Z"
}
```

### Role Relationship Request/Response

**Create Role Relationship Request:**
```json
{
  "toRoleId": "guid",
  "relationshipTypeId": "guid"
}
```

**Role Relationships Response (for a role):**
```json
{
  "outgoing": [
    {
      "id": "relationship-guid",
      "type": {
        "id": "type-guid",
        "code": "SUPPORT",
        "name": "Support Relationship",
        "verb": "supports"
      },
      "targetRole": {
        "id": "role-guid",
        "code": "MARKETING",
        "name": "Marketing Director"
      }
    }
  ],
  "incoming": [
    {
      "id": "relationship-guid",
      "type": {
        "id": "type-guid",
        "code": "ADVISE",
        "name": "Advisory",
        "verb": "is advised by"
      },
      "sourceRole": {
        "id": "role-guid",
        "code": "CFO",
        "name": "Chief Financial Officer"
      }
    }
  ]
}
```

### Person Role Assignment Request/Response

**Assign Role Request:**
```json
{
  "roleId": "guid",
  "isPrimary": false,
  "effectiveDate": "2024-01-15"
}
```

**Person Role Assignment Response:**
```json
{
  "id": "assignment-guid",
  "role": {
    "id": "role-guid",
    "code": "TECH_LEAD",
    "name": "Tech Lead"
  },
  "isPrimary": true,
  "effectiveDate": "2024-01-15T00:00:00Z",
  "terminationDate": null,
  "isActive": true
}
```

**Role Assignment History Response:**
```json
{
  "current": [
    {
      "id": "assignment-guid",
      "role": { "id": "guid", "code": "TECH_LEAD", "name": "Tech Lead" },
      "isPrimary": true,
      "effectiveDate": "2024-01-15T00:00:00Z"
    }
  ],
  "historical": [
    {
      "id": "assignment-guid",
      "role": { "id": "guid", "code": "SR_ENG", "name": "Senior Engineer" },
      "isPrimary": true,
      "effectiveDate": "2022-06-01T00:00:00Z",
      "terminationDate": "2024-01-14T00:00:00Z"
    }
  ]
}
```

### Template Preview Response

**POST /api/roles/preview-template Request:**
```json
{
  "templateId": "guid"
}
```

**Response:**
```json
{
  "templateName": "Technology Startup",
  "rolesToCreate": [
    { "code": "CEO", "name": "Chief Executive Officer" },
    { "code": "CTO", "name": "Chief Technology Officer" }
  ],
  "rolesToSkip": [
    { "code": "CFO", "name": "Chief Financial Officer", "reason": "Role with code 'CFO' already exists" }
  ],
  "summary": {
    "totalInTemplate": 8,
    "willCreate": 6,
    "willSkip": 2
  }
}
```

### Deactivate Person Request/Response

**POST /api/people/{id}/deactivate Request (optional body):**
```json
{
  "reassignWorkItemsTo": "guid"  // Optional: bulk reassign all items to this person
}
```

**Response:**
```json
{
  "deactivated": true,
  "roleAssignmentsTerminated": 2,
  "workItemsAffected": {
    "actions": 5,
    "kpis": 2,
    "issues": 1
  },
  "workItemsReassignedTo": "guid"  // or null if not reassigned
}
```

### Change Username Request/Response

**PUT /api/user/username Request:**
```json
{
  "newUsername": "john.doe",
  "currentPassword": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "username": "john.doe",
  "previousUsername": "johnd",
  "nextChangeAllowedAt": "2025-01-20T14:00:00Z"  // 30 days from now
}
```

**Validation Errors:**
```json
{
  "error": {
    "code": "USERNAME_CHANGE_TOO_SOON",
    "message": "Username can only be changed once every 30 days",
    "details": {
      "nextChangeAllowedAt": "2025-01-15T10:30:00Z"
    }
  }
}
```

### Forgot Username Request/Response

**POST /api/auth/forgot-username Request:**
```json
{
  "email": "john.doe@example.com"
}
```

**Response (always 200 to prevent email enumeration):**
```json
{
  "message": "If the email is associated with any accounts, instructions have been sent."
}
```

**Email Content:**
```
Subject: Your PurposePath Username(s)

Hello,

A request was made to retrieve usernames associated with this email address.

Your associated usernames:
- johnd (Company: Acme Corp)
- john.doe (Company: Personal Project)

If you did not request this, please ignore this email.
```

---

**Document End**

*This document will be updated as implementation progresses and frontend specifications are finalized.*
