# AI Parameters Refactoring - Parameter Analysis & Review

**Version:** 1.2  
**Date:** January 11, 2026  
**Status:** REVIEWED (Updated with GET /measures/summary endpoint)

---

## Decision Legend

- INCLUDE - Parameter will be implemented
- EXCLUDE - Parameter not needed, will not implement
- DEFER - Consider for future phase

---

## Section 1: Business Foundation Parameters (NEW)

### 1.1 Business Profile - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| business_name | string | GET /business/foundation | Company name | INCLUDE |
| business_description | string | GET /business/foundation | Full company description | INCLUDE |
| business_address | object | GET /business/foundation | Address (street, city, state, zip, country) | INCLUDE |
| industry | string | GET /business/foundation | Industry category | INCLUDE |
| sub_industry | string | GET /business/foundation | Sub-industry specialization | INCLUDE |
| company_stage | enum | GET /business/foundation | startup/growth/scale/mature | INCLUDE |
| company_size | enum | GET /business/foundation | solo/micro/small/medium/large/enterprise | INCLUDE |
| revenue_range | enum | GET /business/foundation | Revenue bracket | INCLUDE |
| year_founded | number | GET /business/foundation | Year company was founded | INCLUDE |
| geographic_focus | array | GET /business/foundation | local/regional/national/global | INCLUDE |
| headquarters_location | string | GET /business/foundation | HQ location | INCLUDE |
| website_url | string | GET /business/foundation | Company website | INCLUDE |

### 1.2 Core Identity - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| vision | string | GET /business/foundation | Vision statement | INCLUDE |
| vision_timeframe | string | GET /business/foundation | Timeframe for vision | INCLUDE |
| purpose | string | GET /business/foundation | Purpose/mission statement | INCLUDE |
| who_we_serve | string | GET /business/foundation | Description of who we serve | INCLUDE |
| core_values | array | GET /business/foundation | List of core values with details | INCLUDE |
| core_values_summary | string | COMPUTED | Formatted summary of core values | INCLUDE |

### 1.3 Target Market - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| niche_statement | string | GET /business/foundation | Niche market description | INCLUDE |
| market_size | string | GET /business/foundation | Target market size estimate | INCLUDE |
| growth_trend | enum | GET /business/foundation | declining/stable/growing/rapidly_growing | INCLUDE |
| icas | array | GET /business/foundation | Ideal Customer Avatars (detailed) | INCLUDE |
| icas_summary | string | COMPUTED | Formatted summary of ICAs | INCLUDE |
| primary_ica | object | COMPUTED | First/primary ICA | INCLUDE |

### 1.4 Products and Services - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| products | array | GET /business/foundation | Full product catalog | INCLUDE |
| products_summary | string | COMPUTED | Formatted summary of products | INCLUDE |
| products_count | number | COMPUTED | Number of products/services | INCLUDE |
| primary_product | object | COMPUTED | Main product/service | INCLUDE |
| active_products | array | COMPUTED | Products with status=active | INCLUDE |

### 1.5 Value Proposition - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| unique_selling_proposition | string | GET /business/foundation | USP statement | INCLUDE |
| key_differentiators | string | GET /business/foundation | What makes us different | INCLUDE |
| proof_points | string | GET /business/foundation | Evidence supporting claims | INCLUDE |
| customer_outcomes | string | GET /business/foundation | Results customers achieve | INCLUDE |
| brand_promise | string | GET /business/foundation | Brand commitment | INCLUDE |
| primary_competitors | array | GET /business/foundation | List of main competitors | INCLUDE |
| competitive_advantage | string | GET /business/foundation | Competitive edge description | INCLUDE |
| market_position | enum | GET /business/foundation | leader/challenger/niche/emerging | INCLUDE |

### 1.6 Business Model - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| business_model_types | array | GET /business/foundation | b2b/b2c/saas/etc | INCLUDE |
| primary_revenue_stream | string | GET /business/foundation | Main revenue source | INCLUDE |
| secondary_revenue_streams | array | GET /business/foundation | Other revenue sources | INCLUDE |
| pricing_strategy | string | GET /business/foundation | Pricing approach | INCLUDE |
| key_partners | array | GET /business/foundation | Strategic partners | INCLUDE |
| distribution_channels | array | GET /business/foundation | How products reach customers | INCLUDE |
| customer_acquisition | string | GET /business/foundation | CAC strategy | INCLUDE |

### 1.7 Foundation Meta - EXCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| health_score | number | GET /business/foundation | Foundation completeness (0-100) | EXCLUDE |
| section_statuses | object | GET /business/foundation | Status per section | EXCLUDE |
| foundation_updated_at | datetime | GET /business/foundation | Last update timestamp | EXCLUDE |

**Reason:** Meta fields are for UI progress tracking, not needed for AI prompts.

---

## Section 2: Organizational Structure Parameters (NEW)

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| departments | array | GET /org/departments | List of departments | INCLUDE |
| departments_count | number | COMPUTED | Number of departments | INCLUDE |
| positions | array | GET /org/positions | List of positions | INCLUDE |
| positions_count | number | COMPUTED | Number of positions | INCLUDE |
| org_chart | object | GET /org/chart | Organizational hierarchy | EXCLUDE |

**Note:** Org chart excluded - complex hierarchical data not useful for prompts.

---

## Section 3: People Parameters (NEW) - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| people | array | GET /people | All people in organization | INCLUDE |
| people_count | number | COMPUTED | Total headcount | INCLUDE |
| person_by_id | object | GET /people/{id} | Specific person details | INCLUDE |
| people_by_department | object | COMPUTED | People grouped by department | INCLUDE |
| active_people | array | COMPUTED | Active employees only | INCLUDE |

---

## Section 4: Goals Parameters (ENHANCED)

### 4.1 Single Goal

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| goal | object | GET /goals/{id} | Complete goal data | INCLUDE |
| goal_name | string | GET /goals/{id} | Goal title (renamed from title) | INCLUDE |
| goal_description | string | GET /goals/{id} | Goal description | INCLUDE |
| goal_type | enum | GET /goals/{id} | annual/quarterly/custom | INCLUDE |
| goal_status | enum | GET /goals/{id} | draft/active/at_risk/behind/on_track/completed/cancelled | INCLUDE |
| goal_start_date | datetime | GET /goals/{id} | When goal period starts | INCLUDE |
| goal_target_date | datetime | GET /goals/{id} | Due date | INCLUDE |
| goal_owner | object | GET /goals/{id} | Person who owns the goal | INCLUDE |
| goal_progress | number | GET /goals/{id} | Completion percentage (0-100) | INCLUDE |
| goal_alignment_score | number | GET /goals/{id} | Alignment to foundation (0-100) | INCLUDE |
| goal_parent_id | string | GET /goals/{id} | Parent goal for cascading | EXCLUDE |
| goal_children | array | GET /goals/{id} | Child goals | EXCLUDE |

**Note:** Parent/children excluded - goal hierarchy not needed for AI coaching prompts.

### 4.2 Goals Collection - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| goals | array | GET /goals | All goals | INCLUDE |
| goals_count | number | COMPUTED | Total goal count | INCLUDE |
| goals_summary | string | COMPUTED | Brief goals overview | INCLUDE |
| goals_by_status | object | COMPUTED | Goals grouped by status | INCLUDE |
| goals_by_type | object | COMPUTED | Goals grouped by type | INCLUDE |
| active_goals | array | COMPUTED | Goals with status=active | INCLUDE |
| at_risk_goals | array | COMPUTED | Goals with status=at_risk | INCLUDE |
| annual_goals | array | COMPUTED | Goals with type=annual | INCLUDE |
| quarterly_goals | array | COMPUTED | Goals with type=quarterly | INCLUDE |

---

## Section 5: Strategy Parameters (NEW)

### 5.1 Single Strategy - INCLUDE ALL (with additions)

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| strategy | object | GET /strategies/{id} | Complete strategy data | INCLUDE |
| strategy_name | string | GET /strategies/{id} | Strategy title | INCLUDE |
| strategy_description | string | GET /strategies/{id} | Detailed description | INCLUDE |
| strategy_status | enum | GET /strategies/{id} | draft/active/completed/cancelled | INCLUDE |
| strategy_type | enum | GET /strategies/{id} | rock/initiative/program | INCLUDE |
| strategy_owner | object | GET /strategies/{id} | Strategy owner | INCLUDE |
| strategy_progress | number | GET /strategies/{id} | Progress percentage | INCLUDE |
| strategy_goal_ids | array | GET /strategies/{id} | Linked goal IDs | INCLUDE |
| strategy_start_date | datetime | GET /strategies/{id} | Start date | INCLUDE |
| strategy_target_date | datetime | GET /strategies/{id} | Target completion | INCLUDE |
| strategy_alignment_score | number | GET /strategies/{id} | Alignment to business foundation (0-100) | INCLUDE NEW |
| strategy_alignment_explanation | string | GET /strategies/{id} | Explanation of alignment score | INCLUDE NEW |

**Note:** Added alignment_score and alignment_explanation for strategy alignment analysis.

### 5.2 Strategies Collection - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| strategies | array | GET /strategies | All strategies | INCLUDE |
| strategies_count | number | COMPUTED | Total strategy count | INCLUDE |
| strategies_summary | string | COMPUTED | Brief strategies overview | INCLUDE |
| strategies_by_status | object | COMPUTED | Strategies grouped by status | INCLUDE |
| active_strategies | array | COMPUTED | Active strategies | INCLUDE |
| strategies_for_goal | array | COMPUTED | Strategies linked to specific goal | INCLUDE |

---

## Section 6: Measures (KPI) Parameters (ENHANCED)

### 6.1 Single Measure

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| measure | object | GET /measures/{id} | Complete measure data | INCLUDE |
| measure_name | string | GET /measures/{id} | Measure name | INCLUDE |
| measure_description | string | GET /measures/{id} | Detailed description | INCLUDE |
| measure_unit | string | GET /measures/{id} | Unit of measurement | INCLUDE |
| measure_direction | enum | GET /measures/{id} | up/down/maintain | INCLUDE |
| measure_frequency | enum | GET /measures/{id} | daily/weekly/monthly/quarterly | INCLUDE |
| measure_owner | object | GET /measures/{id} | Measure owner | INCLUDE |
| measure_current_value | number | GET /measures/{id} | Latest actual value | INCLUDE |
| measure_target_value | number | GET /measures/{id} | Target value | INCLUDE |
| measure_status | string | COMPUTED | on_track/at_risk/behind based on actual vs target | EXCLUDE |
| measure_trend | string | COMPUTED | improving/declining/stable | INCLUDE |

**Note:** measure_status excluded - varies by measure link threshold and depends on direction.

### 6.2 Measures Collection - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| measures | array | GET /measures | All measures | INCLUDE |
| measures_count | number | COMPUTED | Total measure count | INCLUDE |
| measures_summary | string | COMPUTED | Brief measures overview | INCLUDE |
| measures_by_status | object | COMPUTED | Measures grouped by status | INCLUDE |
| at_risk_measures | array | COMPUTED | Measures not meeting target | INCLUDE |
| measures_for_goal | array | COMPUTED | Measures linked to goal | INCLUDE |
| measures_for_strategy | array | COMPUTED | Measures linked to strategy | INCLUDE |

### 6.3 Measure Data (Historical) - INCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| measure_history | array | GET /measures/{id}/data | Historical data points | INCLUDE |
| measure_actuals | array | COMPUTED | Actual values over time | INCLUDE |
| measure_targets | array | COMPUTED | Target values over time | INCLUDE |

### 6.4 Measures Summary (NEW - Issue #526) - INCLUDE ALL

**Endpoint:** `GET /measures/summary` - Single call returns comprehensive measure data with progress, links, and statistics.

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| measures_summary_data | object | GET /measures/summary | Complete summary response | INCLUDE |
| measures_health_score | number | GET /measures/summary | Overall health score (0-100) | INCLUDE |
| measures_status_breakdown | object | GET /measures/summary | Count by status (on_track, at_risk, behind, no_data) | INCLUDE |
| measures_category_breakdown | array | GET /measures/summary | Count by category with status | INCLUDE |
| measures_owner_breakdown | array | GET /measures/summary | Count by owner | INCLUDE |
| measures_with_progress | array | GET /measures/summary | All measures with progress details per link | INCLUDE |
| on_track_measures | array | COMPUTED | Measures with status "on_track" | INCLUDE |
| behind_measures | array | COMPUTED | Measures with status "behind" | INCLUDE |
| measures_trend_data | object | COMPUTED | Historical trend data for each measure | INCLUDE |

**Note:** This endpoint is a major optimization - returns everything in one call instead of multiple individual calls. Should be the primary retrieval method for measures data.

---

## Section 7: Actions Parameters (ENHANCED) - INCLUDE ALL

### 7.1 Single Action

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| action | object | GET /actions/{id} | Complete action data | INCLUDE |
| action_title | string | GET /actions/{id} | Action title | INCLUDE |
| action_description | string | GET /actions/{id} | Detailed description | INCLUDE |
| action_status | enum | GET /actions/{id} | not_started/in_progress/completed/blocked | INCLUDE |
| action_priority | enum | GET /actions/{id} | low/medium/high/urgent | INCLUDE |
| action_due_date | datetime | GET /actions/{id} | Due date | INCLUDE |
| action_assigned_to | object | GET /actions/{id} | Assigned person | INCLUDE |
| action_assigned_to_name | string | GET /actions/{id} | Assigned person name | INCLUDE |
| action_progress | number | GET /actions/{id} | Progress percentage | INCLUDE |
| action_estimated_hours | number | GET /actions/{id} | Estimated effort | INCLUDE |
| action_actual_hours | number | GET /actions/{id} | Actual effort | INCLUDE |
| action_connections | object | GET /actions/{id} | Linked goals, strategies, issues | INCLUDE |

### 7.2 Actions Collection

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| actions | array | GET /actions | All actions | INCLUDE |
| actions_count | number | COMPUTED | Total action count | INCLUDE |
| actions_summary | string | COMPUTED | Brief actions overview | INCLUDE |
| pending_actions | array | COMPUTED | Actions not_started or in_progress | INCLUDE |
| pending_actions_count | number | COMPUTED | Count of pending actions | INCLUDE |
| overdue_actions | array | COMPUTED | Actions past due date | INCLUDE |
| actions_by_status | object | COMPUTED | Actions grouped by status | INCLUDE |
| actions_by_priority | object | COMPUTED | Actions grouped by priority | INCLUDE |
| actions_for_goal | array | COMPUTED | Actions linked to goal | INCLUDE |
| actions_for_strategy | array | COMPUTED | Actions linked to strategy | INCLUDE |
| actions_for_issue | array | COMPUTED | Actions linked to issue | INCLUDE |
| my_actions | array | COMPUTED | Actions assigned to current user | INCLUDE |

---

## Section 8: Issues Parameters (ENHANCED) - INCLUDE ALL

### 8.1 Single Issue

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| issue | object | GET /issues/{id} | Complete issue data | INCLUDE |
| issue_title | string | GET /issues/{id} | Issue title | INCLUDE |
| issue_description | string | GET /issues/{id} | Detailed description | INCLUDE |
| issue_type | string | GET /issues/{id} | Issue type from config | INCLUDE |
| issue_status | string | GET /issues/{id} | Issue status from config | INCLUDE |
| issue_priority | enum | GET /issues/{id} | low/medium/high/critical | INCLUDE |
| issue_impact | string | GET /issues/{id} | Business impact description | INCLUDE |
| issue_reporter | object | GET /issues/{id} | Person who reported | INCLUDE |
| issue_assigned_to | object | GET /issues/{id} | Assigned person | INCLUDE |
| issue_assigned_to_name | string | GET /issues/{id} | Assigned person name | INCLUDE |
| issue_due_date | datetime | GET /issues/{id} | Resolution deadline | INCLUDE |
| issue_tags | array | GET /issues/{id} | Categorization tags | INCLUDE |
| issue_connections | object | GET /issues/{id} | Linked goals, strategies, actions | INCLUDE |
| issue_root_causes | array | GET /issues/{id} | Identified root causes | INCLUDE |

### 8.2 Issues Collection

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| issues | array | GET /issues | All issues | INCLUDE |
| issues_count | number | COMPUTED | Total issue count | INCLUDE |
| issues_summary | string | COMPUTED | Brief issues overview | INCLUDE |
| open_issues | array | COMPUTED | Issues with open status | INCLUDE |
| open_issues_count | number | COMPUTED | Count of open issues | INCLUDE |
| critical_issues | array | COMPUTED | Issues with priority=critical | INCLUDE |
| critical_issues_count | number | COMPUTED | Count of critical issues | INCLUDE |
| issues_by_status | object | COMPUTED | Issues grouped by status | INCLUDE |
| issues_by_priority | object | COMPUTED | Issues grouped by priority | INCLUDE |
| issues_for_goal | array | COMPUTED | Issues linked to goal | INCLUDE |
| issues_for_strategy | array | COMPUTED | Issues linked to strategy | INCLUDE |
| my_issues | array | COMPUTED | Issues assigned to current user | INCLUDE |

---

## Section 9: Dashboard and Reports Parameters - EXCLUDE ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| dashboard_summary | object | GET /dashboard | Overall dashboard data | EXCLUDE |
| performance_score | number | GET /performance/score | Overall performance (0-100) | EXCLUDE |
| goal_completion_rate | number | COMPUTED | Percent of goals completed | EXCLUDE |
| strategy_completion_rate | number | COMPUTED | Percent of strategies completed | EXCLUDE |
| action_completion_rate | number | COMPUTED | Percent of actions completed | EXCLUDE |
| issue_resolution_rate | number | COMPUTED | Percent of issues resolved | EXCLUDE |
| team_alignment_score | number | GET /team/alignment | Team alignment metric | EXCLUDE |
| activity_feed | array | GET /activities | Recent activities | EXCLUDE |

**Reason:** Dashboard metrics are for UI display, not needed for AI coaching prompts.

---

## Section 10: User and Session Parameters (EXISTING) - KEEP ALL

| Parameter Name | Type | API Source | Description | Decision |
|---------------|------|------------|-------------|:--------:|
| user_id | string | REQUEST | User identifier | KEEP |
| tenant_id | string | REQUEST | Tenant identifier | KEEP |
| user_name | string | GET /user/profile | User display name | KEEP |
| user_email | string | GET /user/profile | User email | KEEP |
| user_role | string | GET /user/profile | User role | KEEP |
| user_department | string | GET /user/profile | Users department | KEEP |
| user_position | string | GET /user/profile | Users position | KEEP |
| session_id | string | REQUEST | Session identifier | KEEP |

---

## Section 11: Existing Parameters to REMOVE (Dead Code)

| Parameter Name | Current Retrieval | Issue | Action Required |
|---------------|-------------------|-------|-----------------|
| mission_statement | get_business_foundation.mission_statement | Field renamed to purpose | Rename extraction path |
| vision_statement | get_business_foundation.vision_statement | Field renamed to vision | Rename extraction path |
| target_audience | get_business_foundation.target_audience | Field replaced by market.icas | Replace with new field |
| short_term_objectives | get_business_foundation | Field removed | Delete parameter |
| long_term_objectives | get_business_foundation | Field removed | Delete parameter |
| brand_voice | get_business_foundation | Field removed | Delete parameter |
| brand_personality | get_business_foundation | Field removed | Delete parameter |
| goal_horizon | get_goal_by_id.horizon | Field renamed to type | Rename extraction path |
| goal_kpis | get_goal_by_id | Field renamed to measures/links | Update mapping |

---

## Section 12: Retrieval Methods - Analysis

### 12.1 Retrieval Methods to ADD

| Method Name | Endpoint | Description | Provides Parameters |
|-------------|----------|-------------|---------------------|
| `get_measures_summary` | `GET /measures/summary` | Comprehensive measure data with progress, links, stats | measures_summary_data, measures_health_score, measures_status_breakdown, measures_category_breakdown, measures_owner_breakdown, measures_with_progress, on_track_measures, behind_measures, at_risk_measures, measures_trend_data |
| `get_strategies` | `GET /strategies` | List all strategies | strategies, strategies_count, active_strategies, strategies_by_status |
| `get_strategy_by_id` | `GET /strategies/{id}` | Single strategy details | strategy, strategy_name, strategy_description, strategy_status, strategy_type, strategy_owner, strategy_progress |
| `get_people` | `GET /people` | List all people | people, people_count, active_people, people_by_department |
| `get_departments` | `GET /org/departments` | List departments | departments, departments_count |

### 12.2 Optimization Opportunities

IMPORTANT: Use summary endpoints to reduce API calls

| Optimization | Current Approach | Recommended Endpoint | Benefit |
|--------------|------------------|---------------------|---------|
| Business Foundation | Single GET /business/foundation | Keep as-is (returns full object) | Single call for all foundation data |
| **Measures Summary** | Multiple GET /measures/{id} calls | **GET /measures/summary** | Returns ALL measures with progress, links, stats, health score in ONE call |
| Goals Summary | Multiple GET /goals/{id} calls | GET /goals (list endpoint) | Reduces N calls to 1 call |
| Strategies Summary | Multiple GET /strategies/{id} calls | GET /strategies (list endpoint) | Reduces N calls to 1 call |

**⚠️ Key Optimization:** `GET /measures/summary` should be the **primary retrieval method** for measures data. It provides:
- All measures with full details
- Progress calculation per goal/strategy link
- Summary statistics (totals, by status, by category, by owner)
- Overall health score (0-100)
- Trend data for each measure

---

## Summary Statistics (Updated v1.2)

| Category | Total | Include | Exclude | Reason for Exclusions |
|----------|-------|---------|---------|----------------------|
| Business Foundation (1.1-1.6) | 42 | 42 | 0 | - |
| Foundation Meta (1.7) | 3 | 0 | 3 | UI progress tracking only |
| Org Structure | 5 | 4 | 1 | org_chart too complex |
| People | 5 | 5 | 0 | - |
| Goals (4.1-4.2) | 21 | 19 | 2 | parent_id, children not needed |
| Strategies | 18 | 18 | 0 | +2 alignment params added |
| Measures (KPIs) 6.1-6.3 | 21 | 20 | 1 | measure_status computed at link level |
| **Measures Summary (6.4)** | **9** | **9** | **0** | **NEW - GET /measures/summary** |
| Actions | 22 | 22 | 0 | - |
| Issues | 24 | 24 | 0 | - |
| Dashboard/Reports | 8 | 0 | 8 | UI metrics only |
| User/Session | 8 | 8 | 0 | - |
| **TOTAL** | **186** | **171** | **15** | |

---

## Review Sign-Off

Reviewer: Motty
Date: January 11, 2026
Status: APPROVED

Key Decisions:
1. Exclude Foundation Meta (1.7) - UI tracking only
2. Exclude org_chart - too complex for prompts
3. Exclude goal_parent_id, goal_children - hierarchy not needed
4. Added strategy_alignment_score and strategy_alignment_explanation
5. Exclude measure_status - computed at link level with thresholds
6. Exclude all Dashboard/Reports (Section 9) - UI metrics only
7. Optimize retrieval with summary endpoints where available
8. **Use GET /measures/summary as primary measures retrieval** - single call provides all measures data with progress, links, and health score

---

## Related Documents

- GitHub Issue: #197 - AI Parameter Registry Refactoring (https://github.com/mottych/PurposePath_AI/issues/197)
- Business Foundation API Spec: ../shared/Specifications/user-app/business-foundation-api.md
- Traction Service API Spec: ../shared/Specifications/user-app/traction-service/
- People Service API Spec: ../shared/Specifications/user-app/people-service.md
- Org Structure API Spec: ../shared/Specifications/user-app/org-structure-service.md
