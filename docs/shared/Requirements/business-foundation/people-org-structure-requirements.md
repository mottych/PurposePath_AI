# People & Organizational Structure Module - Requirements Specification

**Document Version:** 1.0  
**Created:** December 21, 2025  
**Status:** Draft - Pending Frontend Review  
**Author:** Development Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Requirements](#2-business-requirements)
3. [Entity Definitions](#3-entity-definitions)
4. [Relationships & Rules](#4-relationships--rules)
5. [System Behaviors](#5-system-behaviors)
6. [User Interface Requirements](#6-user-interface-requirements)
7. [Data Migration](#7-data-migration)
8. [Future Considerations](#8-future-considerations)
9. [Glossary](#9-glossary)

---

## 1. Executive Summary

### 1.1 Purpose

This module introduces a comprehensive system for managing **all people related to a business**, regardless of whether they have system access. It establishes an **organizational chart** through roles and reporting relationships, enabling businesses to:

- Track employees, consultants, vendors, and other stakeholders
- Define organizational structure with roles and reporting lines
- Establish cross-functional relationships between roles
- Assign work items (actions, KPIs, issues) to appropriate people
- Visualize the organization through an interactive org chart

### 1.2 Key Changes

| Current State | Future State |
|---------------|--------------|
| User entity contains personal info (name, email, phone) | User links to Person; personal info stored in Person |
| Only system users can be assigned work | Any "assignable" person can receive assignments |
| No organizational structure | Roles define positions with accountability |
| No reporting hierarchy | Roles have "reports to" relationships |
| No cross-functional relationships | Roles can have user-defined relationships |

### 1.3 Scope

**In Scope:**
- Person entity with type, status, tags, and assignability
- Role entity with accountability and reporting structure
- Role relationships (dotted lines, support relationships, etc.)
- Role templates for quick organizational setup
- User-to-Person linking
- Assignment system updates (Actions, KPIs, Issues)
- Data migration for existing users
- Person-Role assignment history with effective dating

**Out of Scope (Future Phases):**
- User role permissions (system access control)
- Person-to-User invitation workflow
- Multiple contact methods per person
- CRM-style contact management
- System-wide audit infrastructure

---

## 2. Business Requirements

### 2.1 People Management

#### BR-2.1.1 Contact Directory
The system shall maintain a directory of all people related to the business, including but not limited to employees, consultants, vendors, partners, and advisors.

#### BR-2.1.2 Person Information
Each person record shall contain:
- First name (required)
- Last name (required)
- Email address (optional, unique within tenant if provided)
- Phone number (optional)
- Title (optional) - Independent of role assignment
- Person Type (required) - Categorizes the relationship to the business
- Status (required) - Active or Inactive
- Assignable flag (required) - Determines if work items can be assigned
- Notes/Comments (optional) - Free-text field for additional context
- Tags (optional) - Multiple user-defined labels for filtering

#### BR-2.1.3 Person Types
Person Types categorize individuals by their relationship to the business:
- Types are user-defined and tenant-specific
- Each type has a name, description, and "assignable by default" property
- When creating a new person, the assignable flag defaults from the selected type
- Users can override the default assignable value per person
- Examples: Employee, Consultant, Vendor, Partner, Advisor, Board Member

#### BR-2.1.4 Person Tags
Tags provide flexible labeling for filtering and organization:
- Tags are user-defined and tenant-specific
- A person can have zero or more tags
- Users can create new tags on-the-fly when assigning
- Examples: Leadership Team, Sales Department, Remote Worker, Executive Committee

#### BR-2.1.5 Person Status
- **Active**: Person is currently engaged with the business
- **Inactive**: Person is no longer actively engaged but retained for historical purposes

Note: A Person linked to an Active User can still be marked Inactive if they are no longer involved in business operations but retain system access for administrative purposes.

### 2.2 Organizational Roles

#### BR-2.2.1 Role Definition
A Role represents a position within the organizational structure:
- Name (required) - The position title (e.g., "VP of Sales")
- Code (required) - Unique identifier within tenant (e.g., "VP_SALES")
- Accountability (required) - Description of what this role is responsible for
- Reports To (optional) - Reference to another role in the hierarchy
- Status (required) - Active or Inactive

#### BR-2.2.2 Role Assignment
- A role can be assigned to zero or one person at any time (vacant or filled)
- A person can hold zero or more roles simultaneously
- One role must be designated as the person's "primary role"
- Role assignments have effective dates and termination dates

#### BR-2.2.3 Role Assignment History
The system shall maintain history of role assignments:
- When a person is assigned to a role, record the effective date
- When a person is unassigned, record the termination date
- If a new person is assigned to an occupied role, auto-terminate the previous assignment
- Frontend may specify dates; system provides defaults if not specified

#### BR-2.2.4 Reporting Relationships (Org Chart)
- Each role may report to exactly one other role (or none if at top)
- Multiple roles can report to the same role (team structures)
- This creates the traditional organizational hierarchy
- A role cannot report to itself (directly or indirectly - no circular references)

### 2.3 Role Relationships (Cross-Functional)

#### BR-2.3.1 Relationship Types
Beyond reporting hierarchy, roles can have other relationships:
- Relationship types are user-defined and tenant-specific
- Each type has:
  - Code (required) - Unique identifier (e.g., "SUPPORT")
  - Name (required) - Descriptive label (e.g., "Support Relationship")
  - Forward Verb (required) - Describes A→B (e.g., "supports")
  - Reverse Verb (required) - Describes B→A (e.g., "is supported by")

#### BR-2.3.2 Role Relationships
- A relationship connects two roles with a specific type
- Relationships are directional (Role A → Role B)
- A role can have multiple relationships of the same type with different roles
- Example: "IT Support" supports "Marketing" AND "IT Support" supports "Sales"

### 2.4 Role Templates

#### BR-2.4.1 Template Structure
Role templates provide quick organizational setup:
- **Role Template**: Contains name, industry category, and description
- **Template Roles**: Predefined roles with names, codes, reporting structure, and accountability

#### BR-2.4.2 Template Management
- Templates are system-defined and maintained by administrators
- Templates are global (not tenant-specific)
- Admin portal provides CRUD operations for templates

#### BR-2.4.3 Template Application
- Users can select a template to initialize their tenant's role structure
- If tenant already has roles, perform non-invasive merge:
  - Add only roles that don't exist (matched by code)
  - Do not modify existing roles even if template has same code
- Users maintain their own roles after template application

### 2.5 User-Person Integration

#### BR-2.5.1 User Linking
- Every User must be linked to exactly one Person
- A Person may be linked to zero or one User
- Personal information (name, email, phone) is stored in Person, not User
- User retains: credentials, preferences, avatar, audit history, status, permissions

#### BR-2.5.2 Profile Updates
- When a User updates their profile, they update their linked Person record
- User-specific settings (avatar, preferences) remain on the User record

### 2.6 Assignment System

#### BR-2.6.1 Assignable People List
When assigning work items (Actions, KPIs, Issues):
- Show all people where Assignable = true AND Status = Active
- Display person's name, title, and primary role
- Indicate which person is the current logged-in user ("Me")
- Support filtering by tags

#### BR-2.6.2 Assignment Storage
- Work items store reference to Person ID (not User ID)
- This allows assignment to people without system access

---

## 3. Entity Definitions

### 3.1 Person

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | PersonId (GUID) | Yes | Unique identifier |
| TenantId | TenantId | Yes | Owning tenant |
| FirstName | string | Yes | First name |
| LastName | string | Yes | Last name |
| Email | Email | No* | Email address (unique within tenant if provided) |
| IsEmailVerified | bool | Yes | Whether email has been verified |

*Note: Email is **required** when Person is linked to a User (for registration, invitations, and password reset). Email is optional for non-user persons (vendors, advisors, etc.).
| Phone | string | No | Phone number |
| Title | string | No | Job title (independent of role) |
| PersonTypeId | PersonTypeId | Yes | Reference to person type |
| IsActive | bool | Yes | Active/Inactive status |
| IsAssignable | bool | Yes | Can receive work assignments |
| Notes | string | No | Free-text comments |
| UserId | UserId | No | Linked user (if any) |
| CreatedAt | DateTime | Yes | Creation timestamp |
| UpdatedAt | DateTime | No | Last update timestamp |
| CreatedBy | UserId | Yes | User who created |
| UpdatedBy | UserId | No | User who last updated |

### 3.2 Person Type

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | PersonTypeId (GUID) | Yes | Unique identifier |
| TenantId | TenantId | Yes | Owning tenant |
| Code | string | Yes | Unique code within tenant |
| Name | string | Yes | Display name |
| Description | string | No | Description |
| IsAssignableByDefault | bool | Yes | Default assignable value for new persons |
| DisplayOrder | int | Yes | Sort order |
| IsActive | bool | Yes | Can be used for new persons |
| CreatedAt | DateTime | Yes | Creation timestamp |
| UpdatedAt | DateTime | No | Last update timestamp |

### 3.3 Person Tag

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | PersonTagId (GUID) | Yes | Unique identifier |
| TenantId | TenantId | Yes | Owning tenant |
| Name | string | Yes | Tag name (unique within tenant) |
| CreatedAt | DateTime | Yes | Creation timestamp |

### 3.4 Person-Tag Assignment (Many-to-Many)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| PersonId | PersonId | Yes | Reference to person |
| TagId | PersonTagId | Yes | Reference to tag |
| AssignedAt | DateTime | Yes | When tag was assigned |

### 3.5 Role

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | RoleId (GUID) | Yes | Unique identifier |
| TenantId | TenantId | Yes | Owning tenant |
| Code | string | Yes | Unique code within tenant |
| Name | string | Yes | Role name/title |
| Accountability | string | Yes | What this role is accountable for |
| ReportsToRoleId | RoleId | No | Parent role in hierarchy |
| IsActive | bool | Yes | Active/Inactive status |
| CreatedAt | DateTime | Yes | Creation timestamp |
| UpdatedAt | DateTime | No | Last update timestamp |
| CreatedBy | UserId | Yes | User who created |
| UpdatedBy | UserId | No | User who last updated |

### 3.6 Person-Role Assignment

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | PersonRoleId (GUID) | Yes | Unique identifier |
| PersonId | PersonId | Yes | Assigned person |
| RoleId | RoleId | Yes | Assigned role |
| IsPrimary | bool | Yes | Is this the person's primary role |
| EffectiveDate | DateTime | Yes | When assignment begins |
| TerminationDate | DateTime | No | When assignment ended (null = current) |
| CreatedAt | DateTime | Yes | Creation timestamp |
| CreatedBy | UserId | Yes | User who created |

### 3.7 Role Relationship Type

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | RoleRelationshipTypeId (GUID) | Yes | Unique identifier |
| TenantId | TenantId | Yes | Owning tenant |
| Code | string | Yes | Unique code within tenant |
| Name | string | Yes | Display name |
| ForwardVerb | string | Yes | Verb from A→B (e.g., "supports") |
| ReverseVerb | string | Yes | Verb from B→A (e.g., "is supported by") |
| IsActive | bool | Yes | Can be used for new relationships |
| CreatedAt | DateTime | Yes | Creation timestamp |
| UpdatedAt | DateTime | No | Last update timestamp |

### 3.8 Role Relationship

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | RoleRelationshipId (GUID) | Yes | Unique identifier |
| TenantId | TenantId | Yes | Owning tenant |
| FromRoleId | RoleId | Yes | Source role |
| ToRoleId | RoleId | Yes | Target role |
| RelationshipTypeId | RoleRelationshipTypeId | Yes | Type of relationship |
| CreatedAt | DateTime | Yes | Creation timestamp |
| CreatedBy | UserId | Yes | User who created |

### 3.9 Role Template (System/Admin)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | RoleTemplateId (GUID) | Yes | Unique identifier |
| Name | string | Yes | Template name |
| IndustryCategory | string | Yes | Industry (e.g., "Technology", "Healthcare") |
| Description | string | No | Template description |
| IsActive | bool | Yes | Available for selection |
| CreatedAt | DateTime | Yes | Creation timestamp |
| UpdatedAt | DateTime | No | Last update timestamp |

### 3.10 Role Template Item

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Id | RoleTemplateItemId (GUID) | Yes | Unique identifier |
| TemplateId | RoleTemplateId | Yes | Parent template |
| Code | string | Yes | Role code |
| Name | string | Yes | Role name |
| Accountability | string | Yes | Default accountability text |
| ReportsToCode | string | No | Code of parent role in template |
| DisplayOrder | int | Yes | Sort order |

### 3.11 User (Modified)

| Field | Type | Required | Change |
|-------|------|----------|--------|
| Id | UserId | Yes | No change |
| PersonId | PersonId | Yes | **NEW** - Link to Person |
| Username | string | Yes | **NEW** - Unique login identifier (globally unique) |
| Email | Email | Yes | **REMOVE** - Stored on Person only |
| FirstName | string | Yes | **REMOVE** - Get from Person |
| LastName | string | Yes | **REMOVE** - Get from Person |
| Phone | string | No | **REMOVE** - Get from Person |
| TenantId | TenantId | Yes | No change |
| Status | UserStatus | Yes | No change |
| PasswordHash | string | No | No change |
| AvatarUrl | string | No | No change |
| Preferences | UserPreferences | Yes | No change |
| IsEmailVerified | bool | Yes | **REMOVE** - Email verification moves to Person |
| LastLoginAt | DateTime | No | No change |
| LoginAttempts | int | Yes | No change |
| IsLocked | bool | Yes | No change |
| LockedUntil | DateTime | No | No change |

#### 3.11.1 Username-Based Authentication

**Breaking Change:** Login will transition from email-based to username-based:

| Aspect | Before | After |
|--------|--------|-------|
| Login identifier | Email (globally unique) | Username (globally unique) |
| Email storage | User table | Person table only |
| Email uniqueness | Global (one user per email) | Per-tenant (same email can exist in multiple tenants) |
| Email verification | Required for User | Required for Person (when provided) |
| Forgot password | Send to email from User | Send to email from linked Person |
| Forgot username | N/A | **NEW** - Send usernames to verified email |

**Migration Strategy:**
- Current email values become usernames automatically (no data migration needed)
- Rename field from `Email` to `Username` in User table
- JWT tokens unchanged (still use UserId and TenantId)
- Login endpoint parameter changes from `email` to `username`

**New "Forgot Username" Flow:**
1. User enters their email address
2. System finds all Persons with that verified email
3. For each Person linked to a User, include the username
4. Send email listing all associated usernames

#### 3.11.2 Username Validation Rules

| Rule | Description |
|------|-------------|
| Uniqueness | Globally unique across all tenants |
| Length | 3-50 characters |
| Characters | Alphanumeric, dots (.), underscores (_), hyphens (-), at-sign (@) |
| Start | Must start with alphanumeric character |
| Case | Case-insensitive for uniqueness (stored as provided, compared lowercase) |
| Reserved | Cannot use reserved words (admin, system, support, etc.) |

#### 3.11.3 Username Change Rules

| Rule | Description |
|------|-------------|
| Rate Limit | Maximum one username change per 30 days |
| Confirmation | Requires current password verification |
| Audit | Username changes are logged with timestamp and old/new values |
| Cooldown | Previous username cannot be claimed by others for 90 days |
| Notification | Email sent to linked Person's email confirming change |

---

## 4. Relationships & Rules

### 4.1 Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐
│   PersonType    │         │   PersonTag     │
│                 │         │                 │
│ - Code          │         │ - Name          │
│ - Name          │         └────────┬────────┘
│ - IsAssignable  │                  │ M:N
│   ByDefault     │                  │
└────────┬────────┘         ┌────────┴────────┐
         │ 1:N              │ PersonTagAssign │
         │                  │                 │
┌────────┴────────┐         │ - PersonId (FK) │
│     Person      │◄────────┤ - TagId (FK)    │
│                 │         └─────────────────┘
│ - FirstName     │
│ - LastName      │         ┌─────────────────┐
│ - Email         │         │      Role       │
│ - Title         │         │                 │
│ - IsAssignable  │         │ - Code          │
│ - Notes         │         │ - Name          │
│                 │◄───┐    │ - Accountability│
└────────┬────────┘    │    │ - ReportsToRole │──┐
         │             │    └────────┬────────┘  │
         │ 0..1:1      │             │           │
         │             │    ┌────────┴────────┐  │
┌────────┴────────┐    │    │ PersonRole      │  │ Self-ref
│      User       │    │    │ Assignment      │  │ (hierarchy)
│                 │    │    │                 │  │
│ - PersonId (FK) │    │    │ - PersonId (FK) │──┘
│ - Status        │    │    │ - RoleId (FK)   │
│ - Preferences   │    └────┤ - IsPrimary     │
│ - Avatar        │         │ - EffectiveDate │
└─────────────────┘         │ - TerminationDt │
                            └─────────────────┘

┌─────────────────┐         ┌─────────────────┐
│ RoleRelType     │         │ RoleRelationship│
│                 │         │                 │
│ - Code          │◄────────┤ - FromRoleId    │
│ - Name          │         │ - ToRoleId      │
│ - ForwardVerb   │         │ - TypeId (FK)   │
│ - ReverseVerb   │         └─────────────────┘
└─────────────────┘
```

### 4.2 Business Rules

#### Person Rules
1. Person email must be unique within tenant (if provided)
2. Person email must be verified before it can be used for password reset
3. Person must have exactly one PersonType
4. IsAssignable defaults from PersonType.IsAssignableByDefault but can be overridden
5. A Person can only be linked to one User (and vice versa)
6. Deleting a Person with a linked User is not allowed
7. Deleting a Person with active role assignments is not allowed
8. Deleting a Person requires reassigning or completing all active work items (Actions, Issues, KPIs)
9. When a Person is deactivated:
   - All active role assignments are terminated (with current date)
   - Work items remain assigned for historical purposes
   - Cannot be assigned new work until reactivated

#### Role Rules
1. Role code must be unique within tenant
2. A role cannot report to itself (no self-reference)
3. Reporting chain cannot have circular references
4. An active role can have at most one current (non-terminated) person assignment
5. Deleting (deactivating) a role:
   - Terminates all active person assignments
   - Clears "primary role" for affected persons (prompt to select new primary)
   - Removes ReportsTo references from subordinate roles (they become top-level)
   - Deletes all role relationships involving this role

#### Person-Role Assignment Rules
1. Each person can have at most one primary role at any time
2. When assigning a person to an occupied role, previous assignment auto-terminates
3. EffectiveDate defaults to current date if not specified
4. TerminationDate is set when assignment ends
5. Cannot have overlapping active assignments for same person-role combination

#### Role Relationship Rules
1. Relationship must have a valid type
2. FromRole and ToRole must be different (no self-relationships)
3. Duplicate relationships (same from, to, and type) are not allowed
4. Deleting a RoleRelationshipType:
   - Only allowed if no relationships of that type exist
   - Alternative: deactivate type (prevent new relationships, keep existing)

#### Person Type Rules
1. PersonType code must be unique within tenant
2. Deleting (deactivating) a PersonType:
   - Only allowed if no persons of that type exist
   - Alternative: reassign persons to different type first

#### Person Tag Rules
1. Tag name must be unique within tenant
2. Deleting a tag removes all person-tag assignments (cascade delete)

---

## 5. System Behaviors

### 5.1 New User Registration

When a new user registers and creates a tenant:
1. Create new Tenant
2. Seed all 6 default PersonTypes for the tenant (see Appendix A.1)
3. Create new Person with:
   - Name, email from registration (email required for User-linked persons)
   - PersonType = "Employee" (default type)
   - IsActive = true
   - IsAssignable = true (from default type)
   - IsEmailVerified = true (verified during registration)
4. Create new User linked to Person
   - Username = email address (can be changed later)
5. Assign user role = "Owner" (system user role, not organizational role)

### 5.2 Assignable People Query

When fetching assignable people:
```
SELECT Person with:
  - IsActive = true
  - IsAssignable = true
  - Include: PrimaryRole (if any), Title
  - Flag: IsCurrentUser (PersonId matches current user's linked Person)
Optional filters:
  - Tags (any match)
  - PersonType
```

### 5.3 Role Assignment Flow

**Assign Person to Role:**
1. If role has current occupant:
   - Set TerminationDate on existing assignment (use provided date or current date)
2. Create new PersonRoleAssignment:
   - EffectiveDate = provided or current date
   - IsPrimary = true if person has no other roles, else false
3. Update role's current occupant cache (if maintained)

**Unassign Person from Role:**
1. Find current assignment (TerminationDate is null)
2. Set TerminationDate (use provided date or current date)
3. If this was primary role, system should prompt to select new primary (or clear if no other roles)

### 5.4 Template Application

When user applies a role template:
1. Load template and its role items
2. For each template role item:
   - Check if tenant has role with same Code
   - If NOT exists: Create new role with template values
   - If EXISTS: Skip (no modification)
3. After all roles created, establish ReportsTo relationships based on ReportsToCode
4. Return summary: X roles added, Y roles skipped (already existed)

### 5.5 Org Chart Data

Query for org chart visualization:
```
Get all active Roles with:
  - Role details (name, accountability)
  - Current person assignment (if any) with person details
  - Direct reports (roles where ReportsToRoleId = this role)
  - Cross-functional relationships (from RoleRelationship)
```

### 5.6 Person Deactivation Flow

When deactivating a person:

1. **Terminate all active role assignments**
   - Set TerminationDate on all current PersonRoleAssignments
   - Clear primary role designation

2. **Check for assigned work items**
   - Query all Actions, KPIs, Issues assigned to this person
   - Return count of affected items to frontend

3. **Work item handling options**:
   - **Option A (Reassign)**: Frontend provides new assignee ID
     - Bulk reassign all work items to specified person
     - Validate new assignee is active and assignable
   - **Option B (Keep Historical)**: No reassignment
     - Items remain assigned for historical purposes
     - Display person as "(Inactive)" in assignment views
     - Prevent new assignments to this person

4. **Post-deactivation**:
   - Person cannot receive new work assignments
   - Person cannot be assigned to roles
   - Person can be reactivated later

**Validation**: If person is linked to a User, prompt whether to also deactivate the User account.

---

## 6. User Interface Requirements

### 6.1 People Management Screen

**List View:**
- Display: Name, Title, Type, Primary Role, Status, Assignable flag
- Filter by: Type, Status, Assignable, Tags
- Search by: Name, Email, Title
- Actions: Add, Edit, View, Deactivate

**Detail/Edit View:**
- Personal info: First name, Last name, Email, Phone, Title
- Classification: Type (dropdown), Status toggle, Assignable toggle
- Tags: Multi-select with ability to add new
- Notes: Text area
- Roles: List of assigned roles with:
  - Role name, Primary indicator, Effective date
  - Ability to add role assignment, remove role, change primary
- Linked User: Show if linked, link to user profile

### 6.2 Roles Management Screen

**List View:**
- Display: Code, Name, Reports To, Current Occupant, Status
- Filter by: Status, Has Occupant
- Search by: Name, Code, Accountability
- Actions: Add, Edit, View, Deactivate

**Detail/Edit View:**
- Role info: Code, Name, Accountability (text area), Status
- Reporting: Reports To (role dropdown)
- Current Occupant: Person assignment with effective date
- Relationships: List of cross-functional relationships
- Reports (subordinates): Roles that report to this role

### 6.3 Org Chart View

**Visualization:**
- Hierarchical display based on ReportsTo relationships
- Each node shows: Role name, Accountability summary, Person photo/name (or "Vacant")
- Click node to expand/collapse subordinates
- Click person to view person details
- Visual indicators for cross-functional relationships (dotted lines)

**Features:**
- Zoom in/out
- Pan/drag
- Search to highlight specific role or person
- Export options (PDF, image)

### 6.4 Assignment Dropdowns

**Standard Assignment Dropdown:**
- Show: Person name, Primary role (if any)
- Mark current user with "(Me)" suffix
- Group by: Role or Department (tag)
- Search/filter capability

---

## 7. Data Migration

### 7.1 Migration Strategy

**Phase 1: Schema Updates**
1. Create all new tables (Person, PersonType, PersonTag, Role, etc.)
2. Add PersonId column to User (nullable initially)
3. Seed default PersonType "Employee" for each tenant

**Phase 2: Data Migration**
1. For each existing User:
   - Create Person record with:
     - FirstName, LastName, Email, Phone from User
     - PersonType = "Employee"
     - IsActive = (User.Status == Active)
     - IsAssignable = true
     - TenantId from User
   - Update User.PersonId to new Person
2. Verify all Users have linked Persons

**Phase 3: Assignment Updates**
1. Update Action.AssignedPersonId to reference Person (currently references User)
2. Update Issue.OwnerId to reference Person
3. Update Measure.OwnerId to reference Person
4. (Any other entities with user assignments)

**Phase 4: Cleanup**
1. Remove FirstName, LastName, Phone from User table
2. Make User.PersonId non-nullable
3. Update all queries/services to use Person for name/contact info

### 7.2 Rollback Plan

- Keep backup of User table before migration
- Migration scripts are idempotent (can re-run safely)
- Feature flag to switch between old/new data access patterns

### 7.3 Environments

| Environment | Migration Timing |
|-------------|------------------|
| Development | During feature development |
| Staging | After code deployment, before QA |
| Production | After staging validation |

---

## 8. Future Considerations

### 8.1 Phase 2: User Invitations
- Process to convert Person to User
- Invitation workflow with email
- Integration with subscription tier limits

### 8.2 Phase 3: User Role Permissions
- System access control based on user roles
- Restrict certain actions (e.g., only Admin can manage roles)
- Integration with existing Owner/Admin/Member user roles

### 8.3 Phase 4: Enhanced Contact Management
- Multiple phone numbers/emails per person
- Communication preferences
- External organization tracking for vendors/partners

### 8.4 Phase 5: System-Wide Audit
- Unified audit log across all entities
- Audit viewer in admin portal
- Retention policies and archival

---

## 9. Glossary

| Term | Definition |
|------|------------|
| **Person** | Any individual related to the business, may or may not have system access |
| **User** | A person with PurposePath login credentials and system access |
| **Role** | A position in the organizational structure with defined accountability |
| **Person Type** | Category defining the person's relationship to business (Employee, Vendor, etc.) |
| **Tag** | Flexible label for grouping/filtering people |
| **Primary Role** | The main role for a person holding multiple positions |
| **Reports To** | The hierarchical relationship between roles forming the org chart |
| **Role Relationship** | Cross-functional link between roles (support, advisory, etc.) |
| **Role Template** | Pre-defined organizational structure for quick setup |
| **Assignable** | Flag indicating if a person can receive work assignments |
| **Tenant** | A customer organization using PurposePath |
| **User Role** | System permission level (Owner, Admin, Member) - NOT organizational role |

---

## Appendix A: Default Seed Data

### A.1 Default Person Types

All 6 default Person Types are seeded for each new tenant during tenant creation:

| Code | Name | Assignable By Default |
|------|------|----------------------|
| EMPLOYEE | Employee | Yes |
| CONSULTANT | Consultant | Yes |
| VENDOR | Vendor | No |
| PARTNER | Partner | No |
| ADVISOR | Advisor | No |
| BOARD | Board Member | No |

### A.2 Default Role Relationship Types

| Code | Name | Forward Verb | Reverse Verb |
|------|------|--------------|--------------|
| SUPPORT | Support | supports | is supported by |
| ADVISE | Advisory | advises | is advised by |
| COLLABORATE | Collaboration | collaborates with | collaborates with |
| MENTOR | Mentorship | mentors | is mentored by |

### A.3 Sample Role Template: "Technology Startup"

| Code | Name | Reports To | Accountability |
|------|------|------------|----------------|
| CEO | Chief Executive Officer | - | Overall company vision, strategy, and performance |
| CTO | Chief Technology Officer | CEO | Technology strategy and engineering execution |
| CFO | Chief Financial Officer | CEO | Financial planning, reporting, and compliance |
| COO | Chief Operating Officer | CEO | Day-to-day operations and process efficiency |
| VP_ENG | VP of Engineering | CTO | Engineering team leadership and delivery |
| VP_PROD | VP of Product | CEO | Product vision and roadmap |
| ENG_MGR | Engineering Manager | VP_ENG | Team management and project execution |
| PROD_MGR | Product Manager | VP_PROD | Feature definition and prioritization |

---

**Document End**

*This document will be updated following frontend review and endpoint specification finalization.*
