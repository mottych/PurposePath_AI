# MEASURE Planning Requirements

**Document Version:** 1.0  
**Date:** November 21, 2025  
**Purpose:** Define comprehensive requirements for MEASURE planning, association, and milestone tracking in PurposePath

---

## Table of Contents

1. [Overview](#overview)
2. [MEASURE Association Patterns](#measure-association-patterns)
3. [MEASURE Sources](#measure-sources)
4. [Primary MEASURE Management](#primary-measure-management)
5. [Milestone and Actuals Tracking](#milestone-and-actuals-tracking)
6. [Business Rules](#business-rules)
7. [Data Model Implications](#data-model-implications)
8. [User Workflows](#user-workflows)
9. [Timeline Horizon Planning](#timeline-horizon-planning)
10. [MEASURE Tracking and Performance Monitoring](#measure-tracking-and-performance-monitoring)
11. [Replanning and Adjustments](#replanning-and-adjustments)
12. [Replan Rules Configuration](#replan-rules-configuration)
13. [Success Criteria](#success-criteria)
14. [Future Enhancements](#future-enhancements)

---

## 1. Overview

The MEASURE Planning system enables users to associate Key Performance Indicators with goals, track progress through milestones, and report actual values. MEASUREs can be shared across multiple goals, with each goal having one designated primary MEASURE.

### Key Capabilities

- **MEASURE Reusability**: A single MEASURE instance can be associated with multiple goals
- **Flexible Creation**: MEASUREs can be created from catalog templates or as custom definitions
- **Multi-Goal Visibility**: Milestone and actual values for a MEASURE are visible across all associated goals
- **Primary MEASURE Designation**: Each goal has exactly one primary MEASURE for reporting and alignment

---

## 2. MEASURE Association Patterns

### 2.1 Existing MEASURE Selection

**Definition**: User selects a MEASURE that already exists in the system (may be associated with other goals).

**Behavior**:
- Creates a new **link** between the existing MEASURE instance and the current goal
- No new MEASURE instance is created
- Milestone and actual data from the existing MEASURE are immediately visible in the current goal
- Changes to milestones/actuals affect all goals linked to this MEASURE

**Use Cases**:
- Tracking the same MEASURE across related goals (e.g., "Revenue Growth" for both "Expand Market Share" and "Increase Profitability")
- Departmental MEASUREs shared across multiple team goals
- Company-wide metrics cascaded to multiple strategic goals

### 2.2 New MEASURE Creation

**Definition**: User creates a brand-new MEASURE instance and associates it with the goal.

**Behavior**:
- Creates a new MEASURE instance in the system
- Automatically creates a link between the new MEASURE and the current goal
- MEASURE starts with no milestone or actual data (clean slate)
- MEASURE can later be associated with additional goals if needed

**Creation Methods**:

#### 2.2.1 Catalog-Based MEASURE

**Definition**: MEASURE created from a predefined catalog template.

**Inherited Properties** (from catalog):
- Name
- Description
- Unit of measurement (e.g., "$", "%", "Count")
- Direction (Higher is Better / Lower is Better)
- Category/Classification
- Recommended measurement frequency
- Industry benchmarks (if applicable)

**User-Defined Properties**:
- Current value (starting point)
- Current value date (when starting point was measured)
- Goal-specific context or notes

**Benefits**:
- Consistency across organization
- Pre-validated definitions
- Built-in best practices
- Easier onboarding for new users

#### 2.2.2 Custom MEASURE

**Definition**: MEASURE created entirely by user with custom properties.

**User-Defined Properties** (all):
- Name
- Description
- Unit of measurement
- Direction (Higher is Better / Lower is Better)
- Current value (starting point)
- Current value date (when starting point was measured)
- Any additional metadata

**Benefits**:
- Flexibility for unique business needs
- Support for industry-specific or proprietary metrics
- Innovation and experimentation

---

## 3. MEASURE Sources

### 3.1 Catalog MEASUREs

**Characteristics**:
- Predefined templates maintained by system/organization
- Standardized definitions ensure consistency
- Metadata includes industry best practices
- Immutable template (instances can be customized)

**Examples**:
- Revenue Growth Rate (%)
- Customer Acquisition Cost ($)
- Net Promoter Score (0-100)
- Employee Retention Rate (%)
- Lead Conversion Rate (%)

### 3.2 Custom MEASUREs

**Characteristics**:
- User-defined from scratch
- No inheritance from catalog
- Fully customizable properties
- Can be saved to organization's custom library for reuse

**Examples**:
- Proprietary product-specific metrics
- Industry-unique measurements
- Experimental or innovative MEASUREs
- Internal operational metrics

---

## 4. Primary MEASURE Management

### 4.1 Primary MEASURE Definition

**Definition**: Each goal has exactly **one** MEASURE designated as the "primary" MEASURE for that goal.

**Purpose**:
- Primary focus for goal achievement tracking
- Featured in dashboards and reports
- Used for goal-level alignment calculations
- Determines goal status/health indicators

### 4.2 Primary MEASURE Assignment Rules

#### Rule 1: Default Assignment
**Behavior**: The **first MEASURE associated** with a goal automatically becomes the primary MEASURE.

**Applies To**:
- New MEASURE created and linked
- Existing MEASURE linked to goal with no current MEASUREs

#### Rule 2: User Override
**Behavior**: User can **change** which MEASURE is primary at any time.

**Requirements**:
- Only MEASUREs currently linked to the goal can be selected as primary
- Only one MEASURE can be primary at a time
- UI should clearly indicate current primary MEASURE

#### Rule 3: Mandatory Primary on Disassociation
**Behavior**: When disassociating a MEASURE that is currently primary, user **must** select a new primary MEASURE.

**Conditions**:
- **If** goal has other MEASUREs remaining: User must select one as new primary
- **If** goal has only one MEASURE (the primary): Disassociation is allowed, goal has no MEASUREs and no primary

**Validation**:
- System prevents removing primary MEASURE unless:
  - User first changes primary to another MEASURE, OR
  - User is removing the last MEASURE from the goal

**User Experience**:
- When attempting to disassociate primary MEASURE:
  - If other MEASUREs exist: Show modal/prompt to select new primary
  - If no other MEASUREs: Show confirmation that goal will have no MEASUREs/primary

---

## 5. Milestone and Actuals Tracking

### 5.1 Milestone Management

**Definition**: Milestones are target values with specific due dates that represent planned progress for a MEASURE.

**Scope**: 
- Milestones are attached to the **MEASURE instance**, not individual goal-MEASURE links
- All goals linked to a MEASURE share the same milestones

**Properties**:
- **Target Value**: Numeric target (e.g., 100,000 for revenue)
- **Target Date**: When the target should be achieved
- **Description** (optional): Context or rationale for the milestone
- **Status**: Not Started / In Progress / Achieved / Missed

**Behavior**:
- User can create multiple milestones for a MEASURE
- Milestones should be chronologically ordered by target date
- Milestones are visible in all goals that link to the MEASURE
- Achieving a milestone updates status across all linked goals

**Use Cases**:
- Quarterly targets for annual goals
- Phased rollout targets
- Progressive improvement targets

### 5.2 Actuals Reporting

**Definition**: Actuals are real measured values reported at specific dates, tracking actual performance.

**Scope**:
- Actuals are attached to the **MEASURE instance**, not individual goal-MEASURE links
- All goals linked to a MEASURE see the same actual values

**Properties**:
- **Actual Value**: Measured numeric value
- **Recorded Date**: When the value was measured/recorded
- **Notes** (optional): Context about the measurement
- **Data Source** (optional): Where the data came from

**Behavior**:
- User can report actuals at any frequency
- Multiple actuals can exist for different dates
- Actuals are displayed chronologically
- Latest actual becomes the MEASURE's "current value"
- Actuals are compared against milestones to calculate progress
- Progress calculations reflect in all goals linked to the MEASURE

**Use Cases**:
- Weekly/monthly performance reporting
- Real-time dashboard updates
- Historical trend analysis

### 5.3 Multi-Goal Visibility

**Key Principle**: Milestone and actual data for a MEASURE are **shared** across all goals the MEASURE is linked to.

**Implications**:

**Data Consistency**:
- One source of truth for MEASURE progress
- No data duplication
- Eliminates conflicting values across goals

**Update Propagation**:
- Adding a milestone to a MEASURE updates all linked goals
- Reporting an actual value updates all linked goals
- Deleting a milestone/actual affects all linked goals

**Calculation Impact**:
- Goal achievement percentages calculated from shared MEASURE data
- Goal health/status reflects shared MEASURE progress
- Alignment calculations use consistent MEASURE values

**User Experience**:
- User sees MEASURE progress in context of each goal
- Same MEASURE data, different goal contexts
- Clear indication that MEASURE is shared across goals

---

## 6. Business Rules

### 6.1 MEASURE Association Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| BR-001 | A goal can have zero or more MEASUREs linked to it | System allows 0..n links |
| BR-002 | A MEASURE can be linked to multiple goals | System allows 1..n links |
| BR-003 | A goal can have at most one primary MEASURE | System enforces uniqueness |
| BR-004 | A goal with at least one MEASURE must have exactly one primary MEASURE | System validation |
| BR-005 | The first MEASURE linked to a goal becomes primary by default | System automatic assignment |
| BR-006 | User can change which linked MEASURE is primary | UI/API operation |
| BR-007 | Cannot remove primary MEASURE without selecting new primary (if other MEASUREs exist) | System validation |
| BR-008 | Can remove last MEASURE from goal (results in no primary) | System allows with confirmation |

### 6.2 MEASURE Creation Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| BR-101 | Catalog-based MEASUREs inherit name, unit, direction, description from catalog | System copies from template |
| BR-102 | Custom MEASUREs require user to define all properties | UI validation |
| BR-103 | All MEASUREs must have: name, unit, direction | System validation (required fields) |
| BR-104 | New MEASURE creation automatically links to the goal being edited | System automatic linking |

### 6.3 Milestone and Actuals Rules

| Rule ID | Rule | Enforcement |
|---------|------|-------------|
| BR-201 | Milestones are attached to MEASURE instance, not goal-MEASURE link | Data model constraint |
| BR-202 | Actuals are attached to MEASURE instance, not goal-MEASURE link | Data model constraint |
| BR-203 | Milestone target date should be chronologically ordered | UI guidance (not enforced) |
| BR-204 | Latest actual becomes MEASURE current value | System automatic update |
| BR-205 | Deleting a milestone affects all goals linked to the MEASURE | System cascade behavior |
| BR-206 | Reporting an actual updates all goals linked to the MEASURE | System cascade behavior |

---

## 7. Data Model Implications

### 7.1 Core Entities

**MEASURE**
- MEASURE instance (source of truth for definition and values)
- Properties: id, name, unit, direction, currentValue, currentValueDate, catalogId (nullable), tenantId
- Relationships: links to multiple goals, has milestones, has actuals

**Goal-MEASURE Link**
- Association between goal and MEASURE
- Properties: goalId, measureId, isPrimary, linkedDate, linkedBy
- Purpose: Many-to-many relationship, tracks primary designation per goal

**MEASURE Milestone**
- Target value with due date
- Properties: id, measureId, targetValue, targetDate, description, status
- Attached to: MEASURE instance (not link)

**MEASURE Actual**
- Reported measurement value
- Properties: id, measureId, actualValue, recordedDate, notes, dataSource
- Attached to: MEASURE instance (not link)

**MEASURE Catalog**
- Template for creating MEASUREs
- Properties: id, name, description, unit, direction, category, recommendedFrequency
- Immutable template

### 7.2 Key Relationships

```
Goal (1) ----< (n) GoalMeasureLink (n) >---- (1) MEASURE
                      |
                      |- isPrimary flag
                      
MEASURE (1) ----< (n) MeasureMilestone
MEASURE (1) ----< (n) MeasureActual

MeasureCatalog (1) ----< (n) MEASURE [optional relationship via catalogId]
```

### 7.3 Query Patterns

**Get all MEASUREs for a Goal** (with primary indicator):
- Query GoalMeasureLink by goalId
- Join to MEASURE to get details
- Filter by isPrimary for primary MEASURE

**Get all Goals for a MEASURE**:
- Query GoalMeasureLink by measureId
- Join to Goal to get details

**Get Milestones/Actuals for a MEASURE** (visible in all linked goals):
- Query MeasureMilestone or MeasureActual by measureId
- No filtering by goal needed (shared data)

---

## 8. User Workflows

### 8.1 Associate Existing MEASURE to Goal

**Steps**:
1. User navigates to goal details
2. Clicks "Add MEASURE"
3. Selects "Choose Existing MEASURE"
4. System shows list of available MEASUREs (from tenant)
5. User selects MEASURE
6. System creates GoalMeasureLink
7. If first MEASURE for goal: System sets isPrimary = true
8. If not first MEASURE: System sets isPrimary = false
9. User sees MEASURE in goal's MEASURE list with all existing milestones/actuals

### 8.2 Create New Catalog-Based MEASURE

**Steps**:
1. User navigates to goal details
2. Clicks "Add MEASURE"
3. Selects "Create from Catalog"
4. System shows catalog MEASURE templates
5. User selects catalog template
6. System pre-fills: name, unit, direction, description (from catalog)
7. User provides: currentValue, currentValueDate
8. System creates new MEASURE instance with catalogId reference
9. System creates GoalMeasureLink
10. If first MEASURE for goal: System sets isPrimary = true
11. User sees new MEASURE in goal's MEASURE list (no milestones/actuals yet)

### 8.3 Create New Custom MEASURE

**Steps**:
1. User navigates to goal details
2. Clicks "Add MEASURE"
3. Selects "Create Custom MEASURE"
4. User provides: name, unit, direction, description, currentValue, currentValueDate
5. System creates new MEASURE instance with catalogId = null
6. System creates GoalMeasureLink
7. If first MEASURE for goal: System sets isPrimary = true
8. User sees new MEASURE in goal's MEASURE list (no milestones/actuals yet)

### 8.4 Change Primary MEASURE

**Steps**:
1. User navigates to goal details
2. Views list of linked MEASUREs (current primary indicated)
3. Selects different MEASURE
4. Clicks "Set as Primary"
5. System updates GoalMeasureLink: previous primary isPrimary = false, selected isPrimary = true
6. UI updates to show new primary indicator

### 8.5 Disassociate MEASURE from Goal

**Scenario A: Removing Non-Primary MEASURE**
1. User selects non-primary MEASURE
2. Clicks "Remove from Goal"
3. System shows confirmation
4. User confirms
5. System deletes GoalMeasureLink
6. MEASURE still exists, milestones/actuals preserved, other goal links unaffected

**Scenario B: Removing Primary MEASURE (other MEASUREs exist)**
1. User selects primary MEASURE
2. Clicks "Remove from Goal"
3. System detects primary removal with other MEASUREs present
4. System shows modal: "This is the primary MEASURE. Please select a new primary MEASURE:"
5. User selects replacement primary from remaining MEASUREs
6. System updates new primary isPrimary = true
7. System deletes original GoalMeasureLink
8. Goal now has new primary MEASURE

**Scenario C: Removing Last MEASURE**
1. User selects last/only MEASURE
2. Clicks "Remove from Goal"
3. System shows confirmation: "This will remove the primary MEASURE. Goal will have no MEASUREs."
4. User confirms
5. System deletes GoalMeasureLink
6. Goal has no MEASUREs, no primary MEASURE

### 8.6 Add Milestone to MEASURE

**Steps**:
1. User navigates to MEASURE details (from any linked goal)
2. Clicks "Add Milestone"
3. Provides: targetValue, targetDate, description (optional)
4. System creates MeasureMilestone attached to MEASURE
5. Milestone appears in all goals linked to this MEASURE

### 8.7 Report Actual for MEASURE

**Steps**:
1. User navigates to MEASURE details (from any linked goal)
2. Clicks "Report Actual"
3. Provides: actualValue, recordedDate, notes (optional)
4. System creates MeasureActual attached to MEASURE
5. System updates MEASURE.currentValue = actualValue, MEASURE.currentValueDate = recordedDate
6. Actual and updated current value appear in all goals linked to this MEASURE
7. System recalculates progress vs milestones across all linked goals

---

## 9. Timeline Horizon Planning

### 9.1 Overview

Timeline horizon planning allows users to see how their MEASURE will progress over time based on the milestones they set. The system automatically calculates expected values for periods between milestones, creating a complete picture of the planned trajectory.

### 9.2 How It Works

When you set milestones for a MEASURE, the system automatically fills in the gaps between those milestones. For example, if you set a milestone for Q1 (March 31) and another for Q2 (June 30), the system will calculate what the expected value should be for each month in between.

**Interpolation Methods:**
- **Linear**: The system draws a straight line between milestones, assuming steady progress
- **Exponential**: The system assumes accelerating or decelerating growth
- **Step**: The system maintains the same value until the next milestone

### 9.3 Viewing Planning Data

Users can view the planning data at different time granularities:

- **Monthly View**: See expected values for each month
- **Quarterly View**: See expected values for each quarter
- **Yearly View**: See expected values for each year

The system shows:
- **Start Value**: What the MEASURE value should be at the beginning of the period
- **End Value**: What the MEASURE value should be at the end of the period
- **Delta**: How much the value should change during the period
- **Growth Rate**: The percentage change expected during the period

### 9.4 Visualizing the Plan

The system provides visual representations of the planned trajectory:

- **Timeline View**: Shows milestones on a timeline with current position
- **Period Grid**: Shows all calculated periods in a table format
- **Chart View**: Displays planned trajectory as a line or area chart
- **Variance Chart**: Compares actual values against planned values

### 9.5 How Milestones Create the Plan

When you create milestones, the system uses them as anchor points:

1. The system takes your milestones and their target dates
2. It calculates what the value should be at each point in time between milestones
3. It creates "interpolated periods" that show expected values for each time period
4. These periods are used to compare against actual measurements

**Example:**
- Milestone 1: March 31, 2025 - Target: $50,000
- Milestone 2: June 30, 2025 - Target: $75,000

The system calculates:
- April 2025: Expected to reach ~$58,333 (linear interpolation)
- May 2025: Expected to reach ~$66,667
- June 2025: Expected to reach $75,000

### 9.6 Updating the Plan

When you update milestones:
- The system recalculates all interpolated periods automatically
- All affected goals linked to the MEASURE see the updated plan
- Historical actuals remain unchanged (they're still compared against the new plan)

---

## 10. MEASURE Tracking and Performance Monitoring

### 10.1 Recording Actual Values

Users can record actual measured values for their MEASUREs at any time. This is how you track real performance against your plan.

**What You Record:**
- **Actual Value**: The measured number (e.g., $45,000 in revenue)
- **Measurement Date**: When this value was measured
- **Data Source**: Where the data came from (manual entry, integration, action completion)
- **Notes**: Optional context about the measurement

### 10.2 Automatic Variance Calculation

When you record an actual value, the system automatically:

1. **Calculates Expected Value**: Looks at your milestones and determines what the value should have been on that date
2. **Calculates Variance**: Compares actual vs expected (actual - expected)
3. **Calculates Variance Percentage**: Shows how far off you are as a percentage
4. **Determines Status**: Classifies performance as "on track", "at risk", or "off track"

**Example:**
- Expected value on January 31: $44,000
- Actual value recorded: $45,000
- Variance: +$1,000 (positive is good if direction is "up")
- Variance Percentage: +2.27%

### 10.3 Performance Status

The system automatically determines your MEASURE's performance status:

- **Achieved**: You've met or exceeded the target
- **On Track**: You're performing close to expectations (small variance)
- **At Risk**: You're behind but can still catch up
- **Off Track**: You're significantly behind and may need to adjust the plan

### 10.4 Historical Tracking

All actual values are stored historically, allowing you to:

- See trends over time
- Compare performance across different periods
- Identify patterns in variance
- Track improvement or decline

### 10.5 Current Value

The system automatically updates the MEASURE's "current value" to the most recent actual measurement. This current value is used for:

- Dashboard displays
- Progress calculations
- Goal achievement tracking
- Reporting

---

## 11. Replanning and Adjustments

### 11.1 When Replanning is Needed

Sometimes actual performance deviates significantly from your plan. When this happens, you may need to adjust your milestones to reflect the new reality. This is called "replanning" or "plan adjustment."

**Common Scenarios:**
- You're consistently behind target and need to adjust expectations
- You're ahead of target and want to set more ambitious goals
- Business conditions have changed (market shifts, resource changes, etc.)
- You've learned new information that affects your projections

### 11.2 Automatic Variance Detection

The system automatically detects when actual values deviate significantly from expected values. When you record an actual that shows a large variance, the system:

1. **Checks the Variance**: Compares it against your replan threshold (default: 10%)
2. **Evaluates Trends**: Looks at consecutive misses (default: 2 in a row)
3. **Suggests Replanning**: If thresholds are exceeded, suggests you review and adjust the plan

### 11.3 Adjustment Strategies

When replanning, you can choose from different strategies:

**Maintain Final Goal**
- Keep the same end target (final milestone)
- Adjust the path to get there (steeper or gentler slope)
- Use this when you still believe the final goal is achievable

**Proportional Shift**
- Shift all future milestones by the same percentage
- Maintains the same growth rate but adjusts the baseline
- Use this when conditions have changed uniformly

**Custom**
- Manually adjust specific milestones
- Full control over which targets to change
- Use this when you need precise control or have specific reasons for each change

### 11.4 The Adjustment Process

When the system detects significant variance:

1. **Alert Appears**: You see a notification that replanning is recommended
2. **Review Variance**: You see the actual vs expected comparison
3. **See Suggestions**: The system shows previews of different adjustment strategies
4. **Choose Strategy**: You select which approach makes sense
5. **Preview Impact**: You see how the adjustment will affect future milestones
6. **Provide Rationale**: You explain why you're making the adjustment
7. **Apply Adjustment**: The system updates milestones and recalculates periods

### 11.5 Cross-Goal Impact

When a MEASURE is shared across multiple goals, adjusting the plan affects all of them. The system:

- Shows you which goals will be impacted
- Displays the impact level (high, medium, low)
- Allows you to see how each goal's progress will change
- May require coordination with other goal owners

### 11.6 Adjustment History

All plan adjustments are recorded with:
- When the adjustment was made
- What triggered it (which actual value)
- What strategy was used
- What milestones changed
- Who made the adjustment
- Why it was made (rationale)

This creates an audit trail of how and why plans evolved over time.

### 11.7 Automatic Replanning (Optional)

You can configure the system to automatically adjust plans when variance exceeds thresholds:

- **Variance Threshold**: Set the percentage variance that triggers replanning (e.g., 10%)
- **Consecutive Misses**: Require multiple misses before triggering (e.g., 2 in a row)
- **Auto-Adjustment**: Enable automatic application of adjustments
- **User Approval**: Require approval before applying automatic adjustments
- **Notifications**: Get notified when automatic replanning occurs

**Note:** Automatic replanning requires configuration of replan rules (see section 12).

---

## 12. Replan Rules Configuration

### 12.1 What Are Replan Rules?

Replan rules tell the system when and how to automatically suggest or apply plan adjustments. You configure these rules per MEASURE to match your preferences and risk tolerance.

### 12.2 Configurable Settings

**Variance Threshold**
- The percentage difference between actual and expected that triggers replanning
- Example: If set to 10%, a 12% variance will trigger a replan suggestion
- Default: 10%

**Consecutive Misses Required**
- How many times in a row you need to miss target before triggering
- Example: If set to 2, you need two consecutive actuals that exceed the threshold
- Default: 2

**Auto-Adjustment Enabled**
- Whether the system should automatically apply adjustments
- If disabled, system only suggests adjustments for manual review
- Default: Disabled (manual review required)

**Preferred Adjustment Strategy**
- Which strategy to use for automatic adjustments
- Options: Maintain Final Goal, Proportional Shift, or Custom
- Default: Maintain Final Goal

**Require User Approval**
- Whether automatic adjustments need your confirmation
- If enabled, system suggests adjustment but waits for your approval
- Default: Enabled

**Notification Settings**
- Whether to notify you when replanning is triggered
- Who should receive notifications (you, goal owner, team members)
- Default: Notify goal owner

### 12.3 How Replan Rules Work

1. You record an actual value
2. System calculates variance
3. System checks your replan rules
4. If thresholds are met:
   - If auto-adjustment enabled: System applies adjustment automatically (or requests approval)
   - If auto-adjustment disabled: System shows suggestion for you to review
5. You see the adjustment and can accept, modify, or dismiss it

### 12.4 Best Practices

- **Conservative Thresholds**: Start with higher thresholds (15-20%) to avoid over-adjusting
- **Require Approval**: Always require approval for automatic adjustments initially
- **Monitor Trends**: Adjust rules based on how often replanning is triggered
- **Team Coordination**: For shared MEASUREs, coordinate replan rules with other goal owners

---

## 13. Success Criteria

### 13.1 Functional Requirements Met

- ✅ Users can associate existing MEASUREs with goals
- ✅ Users can create new MEASUREs (catalog-based or custom) when associating with goals
- ✅ Each goal has exactly one primary MEASURE when MEASUREs are linked
- ✅ System prevents invalid primary MEASURE states
- ✅ Milestones and actuals are shared across all goals linked to a MEASURE
- ✅ MEASURE data updates propagate to all linked goals
- ✅ Users can change primary MEASURE designation
- ✅ Users can disassociate MEASUREs with proper primary MEASURE handling
- ✅ Users can set milestones and view interpolated planning periods
- ✅ Users can record actual values and see variance calculations
- ✅ System detects significant variance and suggests replanning
- ✅ Users can apply plan adjustments using different strategies
- ✅ System shows cross-goal impact when adjusting shared MEASUREs
- ⚠️ Users can configure replan rules (backend ready, UI pending)

### 13.2 Data Integrity

- ✅ No orphaned GoalMeasureLink records
- ✅ Primary MEASURE constraint enforced (1 per goal if MEASUREs exist)
- ✅ Milestones/actuals attached to MEASURE instance, not links
- ✅ MEASURE deletion cascades properly (or is prevented if linked to goals)
- ✅ Catalog inheritance preserved in MEASURE instances

### 13.3 User Experience

- ✅ Clear indication of primary MEASURE in UI
- ✅ Intuitive workflow for adding MEASUREs (existing vs new, catalog vs custom)
- ✅ Proper warnings when removing primary MEASURE
- ✅ Consistent MEASURE data across all goal views
- ✅ Easy navigation between goals sharing a MEASURE

---

## 14. Future Enhancements

**Not in Current Scope - For Future Consideration**:

- **MEASURE Templates**: Save custom MEASUREs as organization templates
- **MEASURE Hierarchies**: Parent-child MEASURE relationships (composite metrics)
- **Automated Actuals**: Integration with data sources for automatic reporting
- **MEASURE Forecasting**: Predictive analytics for milestone achievement
- **MEASURE Benchmarking**: Compare MEASURE performance against industry standards
- **MEASURE Alerts**: Notifications when MEASURE deviates from plan
- **Goal-Specific MEASURE Weighting**: Different importance weights for same MEASURE across goals
- **Conditional Milestones**: Milestones that adjust based on external factors

---

**End of Requirements Document**
