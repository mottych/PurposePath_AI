# Organization Chart Redesign Requirements

**Document Version:** 1.0  
**Date:** January 2, 2026  
**Status:** Draft  

---

## 1. Overview

This document outlines the requirements for redesigning the organization chart structure to support more flexible and realistic organizational hierarchies. The current design, which centers on Roles with direct person assignments, will be enhanced with new entities: **Positions** and **Organization Units (Business Units)**.

---

## 2. Current State

### 2.1 Existing Entities

- **Person**: An individual in the system
- **Role**: A job function with:
  - Description and accountability
  - One person assigned (or vacant)
  - Reports-to relationship (hierarchy defined at role level)

### 2.2 Current Limitations

1. Each role can only have one person assigned
2. Cannot represent multiple people serving the same function (e.g., multiple developers)
3. No concept of organizational groupings (departments, teams, etc.)
4. Hierarchy is rigid, tied to role definitions rather than actual reporting structures

---

## 3. Proposed Design

### 3.1 New Entities

#### 3.1.1 Position

A **Position** is a placeholder that connects a person to a role within the organizational hierarchy.

**Attributes:**
- Position ID (unique identifier)
- Position Name (required)
- Position Description (optional - extends Role description)
- Specific Accountability (optional - extends the role accountability)
- Role (required - reference to Role entity)
- Person (optional - reference to Person entity, null if vacant)
- Reports-To Position (optional - reference to another Position, null if top-level)
- Organization Unit (required - reference to Organization Unit)
- Status (Active, Inactive)
- Tenant ID (required - all org-structure entities are tenant-scoped)
- Created/Modified timestamps

**Behaviors:**
- A Position always has exactly one Role
- A Position may be vacant (no Person assigned) or filled (one Person assigned)
- A Position reports to another Position (or is top-level with no Reports-To)
- When creating a new Position:
  - Default Reports-To should be a Position whose Role matches the new Position's Role's default Reports-To Role
  - User may override the Reports-To to any other Position regardless of Role hierarchy

#### 3.1.2 Organization Unit (Business Unit)

An **Organization Unit** represents a logical grouping within the organization (e.g., department, team, practice).

**Attributes:**
- Organization Unit ID (unique identifier)
- Name
- Organization Unit Type (required - reference to Organization Unit Type)
- Parent Organization Unit (optional - reference to another Organization Unit, null if top-level)
- Unit Lead (optional - reference to Person)
- Created/Modified timestamps

**Behaviors:**
- An Organization Unit has exactly one Type
- An Organization Unit may be part of a parent Organization Unit (hierarchical)
- An Organization Unit may have one Person designated as the Unit Lead

#### 3.1.3 Organization Unit Type

An **Organization Unit Type** defines the category of an Organization Unit.

**Attributes:**
- Organization Unit Type ID (unique identifier)
- Name (e.g., "Company", "Department", "Team", "Community of Practice", "Community of Interest")
- Description
- Created/Modified timestamps

**Behaviors:**
- User-defined (customers can create their own types)
- Used to categorize Organization Units


#### 3.1.4 Role Type

A **Role Type** Categorize the Role level.

**Attributes:**
- Role Type ID (unique identifier)
- Name (e.q. "Executive", "Senior Manager", "Manager", "Assoicate")
- Description
- Is Stretch Role (Falg indication if this role is a full time or an extended responsibility)
- Created/Modified timestamps

**Behaviors:**
- User-defined (customers can create their own types)
- Used to categorize Roles

---

### 3.2 Modified Entities

#### 3.2.1 Role (Modified)

**Removed Attributes:**
- ~~Assigned-To Person~~ (moved to Position)
- ~~Reports-To Role~~ (hierarchy now at Position level; may retain for default behavior - TBD)

**Retained Attributes:**
- Role ID
- Name
- Description
- Accountability
- (Optional) Default Reports-To Role - used as a template when creating new Positions

**New Attributes**
- Role Type (Required - Identifies the role level)

**Behaviors:**
- Role becomes a template/definition only
- Positions inherit description and accountability from their Role and can extend it aith additional specific details
- Role no longer directly holds a person or hierarchy
- Role has exactly one type

#### 3.2.2 Person (Modified)

**New Attributes**
- Primary Position (Identifies what position is the primary position of the person)

**New Relationships:**
- A Person may hold one or more Positions
- A Person may belong to one or more Organization Units (through their Positions)
- One Organization Unit is designated as the Person's **Primary Unit** (derived from Primary Position)

**Constraint:**
- A Person may only belong to an Organization Unit if they hold a Position that belongs to that Unit

**Behaviors**
- A person has exactly one primary position. The first assigned position will default as primary and can be changed
- The Person's Primary Organization Unit is automatically determined by their Primary Position's Organization Unit

#### 3.2.3 Position Relationships (Replaces Role Relationships)

**Attributes**
- Position Relationship ID (unique identifier)
- From Position ID (required - reference to Position)
- To Position ID (required - reference to Position)
- Relationship Type ID (required - reference to existing Relationship Type entity)
- Tenant ID (required)
- Created/Modified timestamps

**Behaviors**
- Relationships are now defined between Positions rather than Roles
- Uses the existing Relationship Type entity for categorization (e.g., collaborates-with, delegates-to, escalates-to)

---

## 4. Hierarchy and Relationships

### 4.1 Position Hierarchy

```
Position A (CTO Role) - Executive Role Type - Top Level - Part of IT Department and Leads the It Department
├── Position B (Team Lead Role - Manager Role Type ) - Reports to Position A - Part of Platform Team, and Platform Team Lead
│   ├── Position D (Developer Role - Associate Role Type) - Reports to Position B - Part of Platform Team
│   ├── Position E (Developer Role - Associate Role Type) - Reports to Position B - Part of  Platform Team
│   ├── Position F (Developer Role - Associate Role Type) - Reports to Position B - Part of Platform Team
│   ├── Position G (Developer Role - Associate Role Type) - Reports to Position B - Part of Platform Team
│   └── Position H (Developer Role - Associate Role Type) - Reports to Position B - Part of Platform Team
├── Position C (Team Lead Role  - Manager Role Type) - Reports to Position A - Part of Product Team, and Team B Lead
│   ├── Position I (Developer Role - Associate Role Type) - Reports to Position C - Part of Product Team
│   ├── Position J (Developer Role - Associate Role Type) - Reports to Position C - Part of Product Team
│   ├── Position K (Developer Role - Associate Role Type) - Reports to Position C - Part of Product Team
│   ├── Position L (Developer Role - Associate Role Type) - Reports to Position C - Part of Product Team
│   └── Position M (Developer Role - Associate Role Type) - Reports to Position C - Part of Product Team
├── Position N (Developer Role - Associate Role Type) - Reports directly to Position A - Part of IT Department
└── Position O (Developer Role - Associate Role Type) - Reports directly to Position A - Part of IT Department
```

### 4.2 Organization Unit Hierarchy

```
Company (Company Type)
├── IT Department (Department Type)
│   ├── Platform Team (Development Team Type)
│   └── Product Team (Development Team Type)
├── Sales Department (Department Type)
└── Leadership Team (Leadership Team Type)
```

### 4.3 Example Scenario

**Roles Defined:**
1. CTO - Reports to: (none/top-level) - Executive Tole Type
2. Team Lead - Default Reports to: CTO - Manager Role Type
3. Developer - Default Reports to: Team Lead - Associate Role Type

**Positions Created:**
- 1 Position for CTO (filled by John)
- 2 Positions for Team Lead (filled by Alice and Bob)
- 12 Positions for Developer:
  - 5 report to Alice's Position
  - 5 report to Bob's Position
  - 2 report directly to John's Position (override from default)

---

## 5. Business Rules

### 5.1 Position Rules

| Rule ID | Rule Description |
|---------|------------------|
| POS-001 | A Position must always be associated with exactly one Role |
| POS-002 | A Position must always belong to exactly one Organization Unit |
| POS-003 | A Position may have zero or one Person assigned |
| POS-004 | A Position may report to zero or one other Position |
| POS-005 | When creating a Position, the default Reports-To should be a Position whose Role matches the new Position's Role's default Reports-To (if defined) |
| POS-006 | The user may override the Reports-To to any Position, regardless of Role hierarchy |
| POS-007 | A Position cannot report to itself (no circular reference of depth 1) |
| POS-008 | Circular reporting chains are not allowed at any depth |
| POS-009 | Deleting a Position with subordinates requires reassigning or deleting subordinates first |

### 5.2 Organization Unit Rules

| Rule ID | Rule Description |
|---------|------------------|
| ORG-001 | An Organization Unit must have exactly one Organization Unit Type |
| ORG-002 | An Organization Unit may have zero or one parent Organization Unit |
| ORG-003 | An Organization Unit may have zero or one Unit Lead (Person who holds a Position in that Unit) |
| ORG-004 | Circular parent-child relationships are not allowed |
| ORG-005 | Deleting an Organization Unit with child units requires reassigning or deleting children first |
| ORG-006 | Deleting an Organization Unit with Positions requires reassigning Positions first |

### 5.3 Person-Organization Unit Rules

| Rule ID | Rule Description |
|---------|------------------|
| PER-001 | A Person may belong to multiple Organization Units |
| PER-002 | A Person must have exactly one Primary Organization Unit (if they belong to any) |
| PER-003 | A Person may only belong to an Organization Unit if they hold a Position in that Unit |
| PER-004 | When a Person is removed from their last Position in a Unit, they are automatically removed from that Unit |

### 5.4 Role Rules (Modified)

| Rule ID | Rule Description |
|---------|------------------|
| ROL-001 | A Role defines the description and accountability inherited by Positions |
| ROL-002 | A Role may define a default Reports-To Role (used as template for Position creation) |
| ROL-003 | Deleting a Role requires all associated Positions to be deleted or reassigned first |

---

## 6. Migration Considerations

### 6.1 Data Migration

No data migration is needed

### 6.2 Backward Compatibility

- Existing relationships that reference Roles should be migrated to reference Positions
- API endpoints for Roles should be renamed and updated to Positions and adjusted with new attributes 
- Existing relationships that reference RolesReltionship should be migrated to reference PositionRelationship
- API endpoints for RoleRelatuiiosip should be updated to PositionRelationship
  

---

## 7 Data Seeding

Seding data should be added to the existing datas seeding when a new tenant is created 

### 7.1 Seed Data Requirements
- Seed default Organization Unit Types:
  - Company
  - Department
  - Team
  - Community of Practice
  - Community of Interest
  
- Seed default Role Types:
  - Executive
  - Leader
  - Senior Manager
  - Mannager
  - Senior Associate
  - Associate
  - Intern
  
Research online for initial roles recommended by Entrpreneureal Operating System (EOS) and seed 
- Organization Units
- Roles
- Positions

---

## 8. API Considerations

### 8.1 New Endpoints

**Position Endpoints:**
- `GET /positions` - List positions
- `GET /positions/{id}` - Get position details
- `POST /positions` - Create position
- `PUT /positions/{id}` - Update position
- `DELETE /positions/{id}` - Delete position
- `PUT /positions/{id}/assign` - Assign person to position
- `PUT /positions/{id}/unassign` - Remove person from position

**Organization Unit Endpoints:**
- `GET /organization-units` - List organization units
- `GET /organization-units/{id}` - Get organization unit details
- `POST /organization-units` - Create organization unit
- `PUT /organization-units/{id}` - Update organization unit
- `DELETE /organization-units/{id}` - Delete organization unit

**Organization Unit Type Endpoints:**
- `GET /organization-unit-types` - List organization unit types
- `GET /organization-unit-types/{id}` - Get organization unit type details
- `POST /organization-unit-types` - Create organization unit type
- `PUT /organization-unit-types/{id}` - Update organization unit type
- `DELETE /organization-unit-types/{id}` - Delete organization unit type

**Role Type Endpoints:**
- `GET /role-types` - List role types
- `GET /role-types/{id}` - Get role type details
- `POST /role-types` - Create role type
- `PUT /role-types/{id}` - Update role type
- `DELETE /role-types/{id}` - Delete role type

**Position Relationship Endpoints:**
- `GET /position-relationships` - List position relationships
- `GET /position-relationships/{id}` - Get position relationship details
- `POST /position-relationships` - Create position relationship
- `PUT /position-relationships/{id}` - Update position relationship
- `DELETE /position-relationships/{id}` - Delete position relationship

> **Note:** All org-structure entities are tenant-scoped. All endpoints require X-Tenant-Id header and return only data for the authenticated tenant.

### 8.2 Modified Endpoints

**Role Endpoints:**
- Remove person assignment functionality
- Keep for role definition management only

**Person Endpoints:**
- Add ability to view/manage Position assignments
- Add ability to view/manage Organization Unit memberships
- Add Primary Organization Unit designation

---

## 9. Open Questions

| ID | Question | Status |
|----|----------|--------|
| Q1 | Should Role retain a "default Reports-To Role" for auto-populating Position Reports-To? | **Yes** - Retained as optional attribute |
| Q2 | Can a Person hold multiple Positions? | **Yes** (confirmed) - No restrictions on number |
| Q3 | Should we support Position history (tracking who held a position over time)? | Pending |
| Q4 | What happens to existing measures/goals linked to Roles? | N/A - No existing data to migrate |
| Q5 | Should Organization Unit Type have a hierarchy/ordering? | Pending |
| Q6 | Should stretch role flag impose constraints on positions? | **No** - No restrictions at this time |

---

## 10. Success Criteria

1. Multiple people can serve in the same role (via multiple Positions)
2. Reporting hierarchy is independent of role definitions
3. Users can define and manage organizational groupings
4. Existing functionality (accountability, role descriptions) is preserved through Position inheritance
5. Org Chart displays the actual organizational structure (Positions, not Roles)
6. Smooth migration path from current Role-based structure

---

## 11. Appendix

### 11.1 Glossary

| Term | Definition |
|------|------------|
| Position | A placeholder that connects a Person to a Role within an Organization Unit |
| Role | A template defining a job function with description and accountability |
| Organization Unit | A logical grouping within the organization (department, team, etc.) |
| Organization Unit Type | A category definition for Organization Units |
| Unit Lead | The Person designated as the leader of an Organization Unit |
| Primary Unit | The main Organization Unit a Person belongs to (when they belong to multiple) |
| Vacant | A Position with no Person assigned |

### 11.2 Entity Relationship Diagram (Conceptual)

```
┌──────────────────┐         ┌──────────────────┐
│   Organization   │         │   Organization   │
│    Unit Type     │◄────────│      Unit        │
└──────────────────┘  has    └────────┬─────────┘
                                      │ has
                                      ▼
                              ┌──────────────────┐
                              │     Position     │──────────┐
                              └────────┬─────────┘          │
                                       │                    │ reports to
                            has role   │                    │
                                       ▼                    │
                              ┌──────────────────┐          │
                              │      Role        │          │
                              └──────────────────┘          │
                                       ▲                    │
                                       │                    │
                              ┌────────┴─────────┐          │
                              │     Person       │◄─────────┘
                              └──────────────────┘
                                       │
                                       │ holds position
                                       │ (1 to many)
                                       ▼
                              ┌──────────────────┐
                              │     Position     │
                              └──────────────────┘
```

---

*Document End*
