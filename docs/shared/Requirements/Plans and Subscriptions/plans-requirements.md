# Plan requirements (Revised)

# Subscription & Billing System — Product Requirements Document
**Version 2.0 — Final Specification - February 2026**
* * *
## Table of Contents
1. Core Concepts & Definitions
2. Feature Sets
3. Plans & Extensions
4. Subscriptions & Lifecycle
5. Billing & Payments
6. Proration & Plan Changes
7. Downgrade Rules
8. User Self-Service Workflow
9. Notifications & Legal Compliance
10. Audit & Activity
11. Scope Boundaries
12. Open Items
* * *
## 1\. Core Concepts & Definitions

| Term | Definition |
| ---| --- |
| Tenant | An organizational unit in the system. Every user belongs to exactly one tenant. Each tenant has exactly one active subscription at any time. |
| Tenant Owner | The single user with administrative authority over the tenant's subscription, billing, and payment methods. There is exactly one tenant owner per tenant. Only the tenant owner can manage subscriptions and billing. |
| Active User | A user who has an active account and can log in. Deactivated users and pending invitations do not count toward user limits. Only active users count against the plan's Included Users and Max Users limits. |
| People | Records representing individuals tracked within the system (e.g., employees, contacts, stakeholders). People records are distinct from user accounts; a person may or may not have a user account. |
| Organization Unit | A structural division within the tenant's organization (e.g., department, team, division). Used for organizational hierarchy and reporting. |
| Plan | A named product offering with a description, feature set, and pricing. Plans can be published (user-selectable) or hidden (admin/automation-assigned only). |
| Feature Set | A named collection of features, options, and numerical limits that defines what a plan provides. Each plan is linked to exactly one feature set. Feature set components are pre-defined in the system; the admin assigns values to create specific feature sets. |
| Extension / Add-on | An optional rider attached to a specific plan that modifies features or limits for an additional cost. Extensions cannot be purchased independently. Each extension is independent of other extensions on the same plan. |
| Subscription | The binding between a tenant and a plan, with an effective date and optionally a termination date. A tenant cannot have overlapping active subscriptions for the same period. |
| Billing Cycle | A monthly period starting on the 1st and ending on the last day of the month (UTC). All billing activity is aligned to this cycle. |
| Payment Schedule | The billing frequency chosen by the tenant owner (e.g., monthly, quarterly, annually). Determines the number of months covered per payment and affects pricing. |
| Grace Period | A plan-defined period (in days) after subscription termination during which the plan remains in effect. The intent is to avoid blocking access due to an occasional late payment. Applies to the entire subscription including extensions. |
| Fallback Plan | An admin-designated free plan that a subscription transitions to after the grace period elapses without payment resolution. If no fallback plan is defined, access is blocked. |
| Trial Plan | A specific plan designated by the admin as the default trial. It is free, has a defined feature set, grace period, and expiration. It cannot be extended by the user. Assigned automatically to new tenants at registration. |
| Admin Override | A tenant-specific modification that adds features or increases limits beyond what the plan's feature set provides. Overrides can only expand capabilities, never restrict them. An override can have a termination date or persist for the life of the subscription. |

### 1.1 Time & Timezone Policy
All dates and times in the system are stored and maintained in UTC. Billing cycle boundaries (1st of the month) are calculated in UTC. Display of dates to the user may be converted to the tenant's local timezone for readability, but all system calculations use UTC.
* * *
## 2\. Feature Sets
### 2.1 Overview
A feature set is a named configuration that defines the capabilities available to tenants subscribing to a given plan. Each feature set has a name, a status (active/inactive), and a collection of features, limits, and options.
The feature set components are pre-defined in the system (listed below). The admin uses the admin portal to create feature sets by assigning specific values to each component, then associates feature sets with plans.
### 2.2 Feature Catalog
The following table lists all available feature components. Each has a defined type that determines how it is configured and enforced.

| Category | Feature | Type | Description & Enforcement |
| ---| ---| ---| --- |
| AI | Token Limits | Numeric Limit | Maximum AI tokens available per billing period. Resets at the start of each billing cycle. When the limit is reached, AI features are unavailable until the next cycle. |
|  | LLM Model Level | Tier (Basic / Premium) | Determines which AI models are available. Basic provides standard models; Premium unlocks advanced models. |
|  | Conversation Coaching | Boolean (On/Off) | AI-powered conversation coaching feature. When off, the feature is hidden from the UI. |
|  | Topic Levels | Tier (Basic / Advanced / Premium / Ultimate) | Determines the depth and breadth of available AI topic analysis. |
| Organization | Included Users | Numeric Limit | Number of active users included in the base plan price. Users beyond this count may incur additional cost via extensions. |
|  | Max Users | Numeric Limit | Hard cap on total active users in the tenant. The system will not allow adding users beyond this number, even with extensions. |
|  | Max People | Numeric Limit | Maximum people records that can be created in the system. |
|  | Max Organization Units | Numeric Limit | Maximum organizational units (departments, teams, etc.) that can be defined. |
|  | Max Roles | Numeric Limit | Maximum role definitions that can be created. |
|  | Max Positions | Numeric Limit | Maximum position definitions that can be created. |
| Strategic Planning | Max Active Goals | Numeric Limit | Maximum number of goals that can be in an active state simultaneously. |
|  | Max Strategies per Goal | Numeric Limit | Maximum strategies that can be linked to a single goal. |
|  | Max Active Measures | Numeric Limit | Maximum active performance measures across the tenant. |
| Integrations & API | Max Integrations | Numeric Limit | Maximum number of third-party integrations that can be configured. |
|  | API Access | Boolean (On/Off) | Enables or disables access to the platform API. |
| Premium Features | Premium Widgets | Boolean (On/Off) | Access to premium dashboard widgets. When off, premium widgets are hidden. |
|  | Personal Measures | Boolean (On/Off) | Individual user performance measures. Distinct from tenant-level Active Measures. |
|  | AI Insights | Boolean (On/Off) | AI-powered analytics and insights dashboards. |
|  | Roles, Positions & Org Chart | Boolean (On/Off) | Organizational structure management tools including visual org chart. |

### 2.3 Limit Enforcement Rules
When a numeric limit is reached, the following rules apply:
*   **Consumable limits** (e.g., Token Limits): The feature becomes unavailable for the remainder of the billing cycle. No overage billing. The counter resets at the start of the next cycle.
*   **Capacity limits** (e.g., Max Users, Max People, Max Goals): The system prevents creating new items beyond the limit. Existing items remain accessible. The user receives an inline message indicating the limit has been reached and suggesting an upgrade.
*   **Boolean features**: When off, the feature is hidden from the UI entirely.
*   **Tier features**: The UI adapts to show only the capabilities available at the assigned tier level.
### 2.4 Feature Set Administration
Feature sets, plans, billing schedules, and extensions are all defined and managed by the system admin through the admin portal. The admin portal allows the admin to:
*   Create and edit feature sets by assigning values to each pre-defined feature component.
*   Associate feature sets with plans.
*   Define billing schedules
*   Associate billing schedules and define pricing for each plan and billing schedule.
*   Define extensions and their per-schedule pricing.
*   Designate a plan as the trial plan or the fallback (free) plan.
*   Apply admin overrides to specific tenants (additive only — overrides can expand features but never restrict them).
* * *
## 3\. Plans & Extensions
### 3.1 Plan Definition
A plan is the product offering that tenants subscribe to. Plans are created and managed by the admin.

| Attribute | Description | Required |
| ---| ---| --- |
| Name | Display name of the plan | Yes |
| Description | User-facing text explanation of what is included | Yes |
| Feature Set | The feature set associated with this plan (exactly one) | Yes |
| Duration Type | Timed (has an expiration date) or Perpetual (no expiration) | Yes |
| Visibility | Published (visible to users for self-service selection) or Hidden (assignable only by admin or automation) | Yes |
| Trial Designation | Whether this plan is the default trial plan for new registrations. Only one plan can be designated as the trial at any time. | No (default: false) |
| Fallback Designation | Whether this plan serves as the fallback (free) plan after grace period expiration. Only one plan can be designated as the fallback. | No (default: false) |
| Payment Schedules | List of available billing periods with pricing (see 3.2) | Yes, for paid plans |
| Grace Period (days) | Number of days after termination before fallback/blocking occurs | Yes, for paid plans |
| Extensions | Available add-ons with per-schedule pricing (see 3.3) | Optional |

### 3.2 Price Definition & Price Tiers
**Note:** For a full explanation of price tier logic—including all tier types, how they are applied, and fallback rules—see the [Price Tiers](http:///price-tiers) sub-page.
#### Where Standard Prices Are Defined and at What Level
Standard (base) prices are defined at the **plan** level, per **payment schedule** (e.g., monthly, quarterly, annually). For each plan, the admin sets the price for each available payment schedule in the admin portal.
**Extensions** (add-ons) also have prices defined per schedule, and these prices are tied to the parent plan. This means that for any selected plan and payment schedule, there is a clearly defined price for both the plan and each extension.
**Summary of Price Tiers:** The system supports price tiers as an optional overlay on base prices for plans, schedules, and extensions. Price tiers allow alternate pricing (such as discounts or overrides) to be defined for specific groups or scenarios. Price tiers can be assigned to a tenant or applied via discount codes. If no price for a tier is set, the system falls back to the standard price. For full logic, types, and application rules, refer to the [Price Tiers](http:///price-tiers) sub-page.
### 3.3 Payment Schedules
A paid plan offers one or more payment schedules. Each schedule defines a name, the number of months covered per payment. The admin defines payment schedules and price per plan. Longer schedules may offer discounted effective monthly rates.
> **Example: Premium Plan Payment Schedules**  
> Monthly — 1 month, $100/payment ($100/mo effective)  
> Quarterly — 3 months, $270/payment ($90/mo effective)  
> Annually — 12 months, $960/payment ($80/mo effective)
### 3.4 Extensions / Add-ons
**Clarification: How Extensions Work**
Extensions (sometimes called add-ons) are optional enhancements that allow a plan's feature set to be expanded beyond its standard limits. Each extension is always tied both to:
*   A specific **plan** (cannot be purchased independently or transferred between plans)
*   A specific **feature** defined in the system (for example, users, AI tokens, max goals, etc.)
Extensions enable tenants to increase the limits or capabilities provided by their base plan. Extensions are defined by the admin for each plan and feature, specifying:
*   The **feature** being extended (e.g., "Included Users", "AI Token Limits", etc.)
*   The **unit value** of the extension (e.g., an extension might add 3 users or 200 AI tokens per unit)
*   The **unit price** (which may vary by payment schedule, e.g., monthly vs. annual)
**Extension quantity:** When a tenant selects an extension, they also choose how many units to purchase. The total added to the plan's feature limit is:
> `(Extension unit value) × (Quantity purchased by user)`
Thus, the new feature limit is:
> `(Base plan limit) + (Extension unit value × Quantity purchased)`
**Example:** A plan includes 10 users. The user adds an extension called "Additional 3 Users" and purchases 2 units. The total user limit becomes `10 + (2 × 3) = 16 users`.
**Important:** The distinction between the **extension’s unit value** (how much each extension increases the feature) and the **quantity purchased** (how many times the extension is applied) must be made clear in the UI and all documentation.
* * *
## 4\. Subscriptions & Lifecycle
### 4.1 Subscription Definition
A subscription is the binding between a tenant and a plan. It is the central record that determines a tenant's capabilities, billing obligations, and system access.

| Attribute | Description |
| ---| --- |
| Plan | The plan associated with this subscription |
| Effective Date | The date the plan became (or will become) active for the tenant |
| Termination Date | The date the subscription expires. Determined by plan type and payment schedule. Extended on each successful payment. May be null for perpetual plans. |
| Status | Active or Inactive (see 4.2) |
| Auto-Renew | Whether the subscription will automatically renew at the end of the current period (true/false) |
| Is Trial | Whether this subscription is on the designated trial plan (true/false) |
| In Grace Period | Whether the subscription is currently in its grace period (true/false; only applicable when status is Inactive) This could be a computed value derived from expiration date and plan grace period. |
| Grace Period End Date | The date the grace period expires (termination date + plan's grace period days) This property is calculated and not persisted. |
| Payment Schedule | The selected billing frequency (monthly, quarterly, annual, etc.) |
| Active Extensions | List of extensions currently active on this subscription |

### 4.2 Subscription Status Model
The subscription uses a two-state model with supplementary flags that provide additional context for system behavior and UI display.

| Status | Flags | Description | Tenant Access |
| ---| ---| ---| --- |
| Active | is\_trial=true, auto\_renew=false | New registration. Default trial plan is in effect. Tenant has full access per the trial plan's feature set. | Full access per trial plan features |
| Active | is\_trial=false, auto\_renew=true | Paid subscription is current and auto-renewing. Normal operating state. | Full access per plan features |
| Active | is\_trial=false, auto\_renew=false | Tenant owner cancelled auto-renewal. Subscription remains active until termination date. | Full access until termination date |
| Inactive | is\_trial=false, auto\_renew=false | Tenant owner has cancelled the plan. | Fallback plan features, or access is blocked |
| Inactive | auto\_renew=true, in\_grace=true | Termination date has passed (payment failed or trial expired) but grace period is still in effect. The plan's feature set remains available. | Full access per plan features (grace period active) |
| Inactive | in\_grace=false | Grace period has elapsed without resolution. If a fallback plan is defined, it is now active. If no fallback plan exists, access is blocked. | Fallback plan features, or access blocked |

### 4.3 Lifecycle Transitions
The following table defines every valid state transition in the subscription lifecycle.

| From State | To State | Trigger | System Action |
| ---| ---| ---| --- |
| (New Registration) | Active (trial) | User completes registration | Create subscription with trial plan, set effective date to today, set termination per trial plan duration |
| Active (trial) | Active (paid) | User selects a paid plan and payment succeeds | Create new subscription with selected plan; charge prorated amount for remainder of billing cycle |
| Active (trial) | Inactive (grace) | Trial termination date passes without plan selection | Set status to Inactive, begin grace period countdown |
| Active (paid) | Active (paid) | Successful billing payment received | Extend termination date by payment schedule duration; record payment; send receipt |
| Active (paid) | Active (cancelled) | Tenant owner cancels auto-renewal | Set auto\_renew=false; subscription remains active until termination date; send cancellation confirmation |
| Active (cancelled) | Active (paid) | Tenant owner reactivates before termination date | Set auto\_renew=true; resume normal billing |
| Active (cancelled) | Inactive (grace) | Termination date reached | Set status to Inactive, no grace period; proceed directly to fallback/block |
| Active (paid) | Inactive (grace) | Payment fails twice and termination date passes | Set status to Inactive, grace period in effect |
| Inactive (grace) | Active (paid) | Successful payment received during grace period | Restore to Active, extend termination date, clear grace period |
| Inactive (grace) | Inactive (expired) | Grace period elapses without payment | Switch to fallback plan (if defined) or block access |
| Inactive (expired) | Active (paid) | User selects and pays for a new plan | Create new subscription; same enrollment workflow as new subscriber, regain access to old data |
| Any Active | Active (new plan) | Tenant owner changes plan (upgrade or same-tier) | Calculate proration; if upgrade, charge difference and apply immediately; if downgrade, schedule for next cycle |

### 4.4 Admin Overrides
An admin can apply overrides to a specific tenant's subscription. Overrides are strictly additive:
*   The admin can grant additional features or increase limits beyond what the plan's feature set provides.
*   The admin cannot remove features or reduce limits below the plan's feature set values.
*   An override can have a specific termination date (e.g., grant premium AI access for 30 days) or persist as long as the subscription is active.
*   When a plan changes, active overrides are preserved unless they conflict with the new plan (e.g., an override granting 50 max users is irrelevant if the new plan already includes 100). The admin should review overrides after plan changes.
> **Example: Admin Override**  
> Tenant is on the Basic plan, which includes LLM Model Level = Basic.  
> Admin grants an override: LLM Model Level = Premium, with termination date of March 31.  
> The tenant now has Premium AI access until March 31, after which it reverts to Basic.  
> The admin cannot override LLM Model Level to a lower value than what the plan provides.
* * *
## 5\. Billing & Payments
### 5.1 Payment Provider
The system currently supports credit card payments via Stripe. The architecture uses a provider abstraction layer to support additional billing providers in the future. Stripe handles all credit card storage and tokenization; the system never stores raw card numbers. The system should follow Stripe's integration best practices for PCI compliance.
### 5.2 Billing Cycle
All billing cycles are monthly, starting on the 1st and ending on the last day of the month, calculated in UTC. The billing cycle determines when automatic charges are attempted and when subscription periods are calculated.
### 5.3 First-Time Enrollment
Users can enroll in a paid plan at any time during the month. On first enrollment:
1. The system calculates the prorated charge from the enrollment date through the end of the current billing cycle (last day of the month, UTC).
2. The user is charged the prorated amount immediately.
3. The subscription termination date is set to the end of the billing cycle covered by the payment schedule (e.g., for monthly: end of the current month; for quarterly: end of the month 3 months out).
4. Starting the next billing cycle, normal full-period billing applies on the 1st of the month.
> **Example: Mid-Month Enrollment**  
> User enrolls in Premium Plan ($100/mo, monthly schedule) on January 15.  
> Prorated charge: $100 × (17 days / 31 days) = $54.84 for Jan 15–31.  
> On February 1, the system charges the full $100 for February.
### 5.4 Recurring Payment Flow
On the billing date (1st of each applicable month), the system performs the following:
1. Attempt to charge the credit card on file for the plan price plus any active extensions.
2. On success: extend the subscription termination date by the payment schedule duration, record the payment, and send a receipt to the tenant owner via email.
3. On first failure: send a notification to the tenant owner immediately. Schedule a retry after a configurable number of days (admin system setting; default: 3 days).
4. On second failure: send a notification to the tenant owner. The subscription enters the grace period once the termination date passes. The status becomes Inactive, but the plan's features remain available during the grace period.
5. Grace period expiration: if a fallback (free) plan is defined, the subscription switches to it. If no fallback is defined, access is blocked. The tenant owner is notified.
> **Design Note: Retry Configuration** The retry delay (days between first and second attempt) is a system-level setting managed by the admin. Default value: 3 days. The admin can update this at any time via the admin portal. Only two automatic attempts are made per billing cycle. Additional retries are not performed.
### 5.5 Refund Policy
The system does not support automated refunds. Specifically:
*   No refund is issued on subscription cancellation. The subscription remains active until the termination date.
*   No refund is issued when removing extensions mid-cycle. The extension remains active until the end of the current period.
*   No refund is issued on plan downgrades. The current plan remains active until the end of the billing period, at which point the downgrade takes effect.
*   For exceptional circumstances (billing errors, duplicate charges, disputed transactions), the tenant owner must contact support via email. Refunds in these cases require manual intervention by the support team through the Stripe dashboard.
### 5.6 Payment Method Management
The tenant owner can view the current payment method (showing only the last 4 digits of the card) and update the payment method at any time through the subscription management UI. The system monitors card expiration dates and sends a notification 14 days before expiration. If a card expires and is not updated, the next billing attempt will fail and follow the standard retry/grace period flow.
### 5.7 Receipts & Invoices
Receipts and invoices are the same document. The tenant owner can download a receipt for any payment from the subscription management UI. Each receipt includes the payment date, amount, plan name, billing period covered, line items (plan + extensions), and the last 4 digits of the card used.
* * *
## 6\. Proration & Plan Changes
### 6.1 General Principle
Users can enroll in or switch plans at any time. The system calculates prorated charges and credits based on the remaining days in the current billing cycle. No refunds are issued; instead, the system uses credits and deferred effective dates to handle transitions fairly.
### 6.2 Upgrade (New Plan Cost ≥ Remaining Balance)
When the prorated cost of the new plan for the remainder of the selected billing period is equal to or greater than the unused credit from the current plan:
1. Calculate the unused portion of the current plan for the remainder of the billing period (credit).
2. Calculate the prorated cost of the new plan for the remainder of the newly selected billing period (charge).
3. Charge the difference (new plan prorated amount minus credit).
4. The new plan takes effect immediately.
5. Any extensions on the old plan are removed. The user may add new extensions available on the new plan during the change workflow.
### 6.3 Downgrade (Remaining Balance > New Plan Cost)
When the unused balance from the current plan exceeds the prorated cost of the new plan:
1. No charge is made today.
2. The new plan takes effect at the end of the current billing period.
3. The current plan remains fully active until then.
4. At the start of the next billing cycle, the new plan and its billing apply.
### 6.4 Payment Schedule Changes
When a tenant owner changes only the payment schedule (e.g., from monthly to annual) without changing the plan, the change takes effect at the next billing cycle. The current period continues under the existing schedule. The new schedule's pricing applies starting with the next charge.
### 6.5 Cost Summary Display
Before confirming any plan or extension change, the system displays a clear cost summary to the tenant owner showing all line items:
> **Example: Plan Change Cost Summary**  
>   

| Line Item | Amount |
| ---| --- |
| Premium Plan – Monthly (prorated Jan 24–31, normally $100/mo) | $26.00 |
| Credit for Basic Plan (prorated Jan 24–31) | ($12.00) |
| Extension: Advanced AI (prorated Jan 24–31, normally $20/mo) | $4.00 |
| Total Due Today | $18.00 |

>   
The user must confirm the charges before proceeding to payment.
* * *
## 7\. Downgrade Rules
### 7.1 General Principle
When a tenant downgrades to a plan with lower limits or fewer features, data is retained but may become partially inaccessible. The system never deletes data on downgrade. Features and items that were already consumed but exceed the new plan's limits will not be charged, but the tenant will not be able to consume additional resources beyond the new plan's limits.
### 7.2 User Count Validation
Before a downgrade is allowed, the system checks the tenant's active user count against the new plan:
*   If active users exceed the new plan's **Max Users**: the downgrade is **blocked**. The user must deactivate users to meet the new plan's limit before proceeding.
*   If active users exceed the new plan's **Included Users** but are within Max Users: the system **warns** about the additional per-user cost (if an extension exists) or blocks the downgrade (if no additional-users extension is available).
### 7.3 Capacity-Based Features (Goals, Integrations, Roles, etc.)
For features with numeric limits (Max Active Goals, Max Integrations, Max Roles, Max Positions, Max Organization Units, Max Strategies per Goal, Max Active Measures, Max People):
**Pre-Downgrade Warning:** Before the downgrade is confirmed, the system displays a clear warning listing every feature where the current usage exceeds the new plan's limit. For each, the system shows:
*   The current count and the new plan's limit.
*   A recommendation that the user manually select which items to delete or deactivate before proceeding.
*   A notice that if the user proceeds without reducing items, the system will keep only the first N items (ordered by creation date) active and disable the rest.
**Post-Downgrade Behavior:** If the user proceeds without reducing items to within the new limit:
*   The first N items (by creation date, where N = the new plan's limit) remain active and accessible.
*   Remaining items are set to a "disabled" state: they are visible in the UI (grayed out or marked as disabled) but cannot be edited, used, or interacted with.
*   No items are deleted. The user can re-enable items by either upgrading their plan or manually deleting other active items to free up capacity.
*   The user cannot create new items of that type until usage is within the new plan's limit.
### 7.4 Boolean Features
For boolean features (Premium Widgets, Personal Measures, AI Insights, Org Chart, API Access, Conversation Coaching):
*   If a feature is on in the current plan and off in the new plan, the feature becomes unavailable in the UI after the downgrade takes effect.
*   Any data associated with the feature is retained. If the tenant upgrades again, previously created data becomes accessible again.
*   The pre-downgrade warning lists all boolean features that will be lost.
### 7.5 Tier Features
For tier features (LLM Model Level, Topic Levels):
*   The feature automatically adjusts to the new plan's tier level. No data is lost, but the user's experience changes to match the new tier (e.g., Premium AI models become unavailable, reverting to Basic).
### 7.6 Consumable Features (Token Limits)
If the tenant has already consumed tokens beyond the new plan's limit for the current billing period, no additional charge is applied. However, no more tokens can be consumed until the next billing cycle, at which point the new plan's limit applies.
* * *
## 8\. User Self-Service Workflow
### 8.1 Navigation & Access
The active subscription's plan name is displayed in the main navigation bar. Behavior varies by user role:
*   **Tenant Owner:** Clicking the plan name navigates to the Subscription & Billing management page with full management capabilities.
*   **Other Users:** The plan name is visible but not clickable. Non-owner users do not have access to subscription or billing management.
### 8.2 Subscription Management Page
The subscription management page is accessible only to the tenant owner and displays the following:

| Section | Details |
| ---| --- |
| Active Subscription | Plan name, status (Active/Inactive with relevant indicators: trial, cancelled, grace period), expiration date, payment schedule. |
| Change Plan | Displays published plans. Validates user count, warns about excess features (see Section 7), shows cost summary with proration. Requires confirmation before proceeding. |
| Change Schedule | Select a different payment schedule for the current plan. Takes effect next billing cycle. |
| Extensions | View active extensions. Add new extensions (charged immediately, prorated). Remove extensions (effective next period, no refund). Shows pricing for the tenant's selected payment schedule. |
| Cancel Subscription | Cancels auto-renewal. Subscription remains active until termination date. Requires a confirmation dialog ("Are you sure?"). Sends cancellation confirmation notification. |
| Payment History | Chronological list of all payments. Each entry shows: payment date, amount, plan name, billing period covered, last 4 digits of card. Click any payment for detailed view. |
| Payment Method | View current card (last 4 digits only). Update card. System stores card via Stripe tokenization; no raw card data is stored. |
| Receipts | Download receipt/invoice (same document) for any past payment. |

### 8.3 Plan Change Workflow (Step by Step)
1. Tenant owner clicks "Change Plan" from the subscription management page.
2. System displays all published plans (excluding the current plan). Each plan shows its name, description, and key features/limits.
3. The system shows price for the current selected billing schedule (if available) of the new plan. If the new plan does not support the current schedule, the system will show price for the first available schedule and display a warning that the current schedule is not avilable
4. The user can change the billing schedule to see prices for different billing schedules.
5. Tenant owner selects a new plan.
6. System validates the tenant's current state against the new plan's limits (see Section 7: Downgrade Rules). If blocked, the user is informed and returned to plan selection.
7. System displays available extensions for the new plan (if any). Tenant owner optionally selects extensions.
8. System displays the complete cost summary (prorated charges, credits, total due). For downgrades: shows the effective date and any features that will be disabled.
9. Tenant owner confirms the change.
10. Tenant owner enters or confirms credit card information.
11. System processes payment. On success: creates the new subscription (immediately for upgrades, next cycle for downgrades). On failure: notifies the user and allows correction of payment information.
* * *
## 9\. Notifications & Legal Compliance
### 9.1 Delivery Channels
All billing and subscription notifications are sent via email to the tenant owner and displayed in the application UI notification center. Notification preferences are managed through the existing notification preferences system. Additional notification categories are added for subscription and billing events.
### 9.2 Notification Schedule
The following notifications are required. Items marked with ★ are recommended for legal compliance with US Automatic Renewal Laws (ARLs) and FTC regulations.

| Event | Timing | Content | Legal Basis |
| ---| ---| ---| --- |
| Enrollment Confirmation ★ | Immediately after first enrollment | Plan name, price, billing frequency, renewal terms, cancellation instructions | FTC / State ARLs |
| Subscription Expiration Reminder | 7 days and 1 day before termination date | Plan name, termination date, renewal information, link to subscription page | Best practice |
| Renewal Reminder ★ | 15–45 days before annual renewal; annually for shorter schedules | Upcoming charge amount, renewal date, billing frequency, how to cancel (with direct link) | CA/CO/NY ARLs |
| Trial Expiration Warning ★ | 7 days and 1 day before trial ends | Trial end date, what happens next (fallback or access blocked), link to select a plan, how to cancel | FTC (free-to-paid) |
| Payment Success | Immediately after successful charge | Amount charged, plan name, period covered, receipt download link | Best practice |
| Payment Failed | Immediately after each failed attempt | Failure reason (if available from Stripe), next retry date, link to update payment method | Best practice |
| Grace Period Started | Immediately when grace period begins | Grace period end date, what happens at expiration, link to update payment method | Best practice |
| Grace Period Ending | 1 day before grace period expiration | Final warning, grace period end date, consequences, payment link | Best practice |
| Fallback Plan Applied | Immediately when fallback plan is applied | New plan name, features lost, how to re-upgrade | Best practice |
| Access Blocked | Immediately when access is blocked (no fallback plan) | Reason, how to restore access (select a plan), support contact | Best practice |
| Plan Change Confirmed ★ | Immediately after plan change | New plan name, effective date, amount charged (if any), new terms, cancellation instructions | FTC |
| Cancellation Confirmed ★ | Immediately after cancellation | Confirmation of cancellation, effective end date, what happens after, how to reactivate | FTC Click-to-Cancel |
| Payment Method Expiring | 14 days before card expiration | Last 4 digits, expiration date, link to update | Best practice |
| Price Change Notice ★ | At least 7 days before new price takes effect | Current price, new price, effective date, how to cancel | CA ARL |

### 9.3 Legal Compliance Requirements
The following regulatory requirements apply to US subscription billing as of early 2026:
*   **FTC Click-to-Cancel Rule:** Users who sign up online must be able to cancel online via a simple, easy-to-use mechanism. A prominent cancel button must be accessible on the subscription page.
*   **Enrollment Disclosure:** Before collecting billing information, clearly display the price, billing frequency, and cancellation procedure.
*   **Post-Transaction Acknowledgement:** After enrollment, send a confirmation (email) that the customer can retain, including all material terms.
*   **Annual Renewal Reminders:** For subscriptions with terms of 1 year or longer, send a renewal reminder 15–45 days before renewal with cancellation instructions.
*   **Trial-to-Paid Conversion:** For free trials, send a reminder before the trial converts to a paid subscription, including how to cancel before charges begin.
*   **Price Change Notification:** Notify customers at least 7 days before a price increase takes effect, with cancellation instructions.
*   **Cancellation Confirmation:** Send a clear confirmation after cancellation, including the effective end date.
**Important:** These requirements are based on current federal (FTC) and state-level (California, Colorado, New York, Delaware, Illinois) Automatic Renewal Laws as of early 2026. Requirements vary by state and are evolving. Consult legal counsel to ensure full compliance for your specific user base.
### 9.4 Notification Preferences
The existing notification preferences system is extended with the following additional categories. Tenant owners can opt in or opt out of each category except those marked as mandatory (required for legal compliance).

| Category | Default | Can Opt Out? | Reason |
| ---| ---| ---| --- |
| Enrollment & Cancellation Confirmations | On | No | Required by FTC |
| Renewal Reminders | On | No | Required by state ARLs |
| Trial Expiration Warnings | On | No | Required for free-to-paid |
| Price Change Notices | On | No | Required by CA ARL |
| Payment Success Receipts | On | Yes | Best practice |
| Payment Failure Alerts | On | No | Critical for account health |
| Grace Period Alerts | On | No | Critical for account health |
| Payment Method Expiration | On | Yes | Best practice |
| Plan Change Confirmations | On | No | Required by FTC |

* * *
## 10\. Audit & Activity
### 10.1 Auditable Events
All changes related to subscriptions, plans, and payments generate an immutable audit record. The audit log is append-only and cannot be modified or deleted. The following events are audited:
*   Plan selection and plan changes (including the from/to plan)
*   Payment schedule changes
*   Extension additions and removals
*   Payment method updates (old last-4 and new last-4; no full card data)
*   Payment transactions: successful charges, failed attempts, and retries
*   Subscription cancellations and reactivations
*   Grace period entry and exit
*   Fallback plan transitions and access blocking events
*   Admin overrides applied, modified, or expired
*   Admin changes to system settings (retry delay, fallback plan designation, trial plan designation)
### 10.2 Audit Record Schema

| Field | Type | Description |
| ---| ---| --- |
| id | UUID | Unique identifier for the audit record |
| timestamp | DateTime (UTC) | When the event occurred |
| tenant\_id | UUID | The tenant this event pertains to |
| actor\_type | Enum | Who performed the action: tenant\_owner, admin, system |
| actor\_id | UUID | The user ID of the actor (null for system-initiated events) |
| event\_type | Enum | The type of event (from the auditable events list above) |
| description | String | Human-readable summary of the event |
| before\_state | JSON | Relevant state before the change (e.g., previous plan, previous schedule) |
| after\_state | JSON | Relevant state after the change |
| metadata | JSON | Additional context (e.g., Stripe charge ID, proration details, failure reason) |

### 10.3 Access & Retention
*   Tenant owners can view their own tenant's audit history through the subscription management UI (limited to subscription and billing events).
*   Admins can view audit records for any tenant through the admin portal.
*   Audit records are retained indefinitely. A retention policy may be defined in a future phase.
*   Admin reporting dashboards and analytics are out of scope for this phase.
* * *
## 11\. Scope Boundaries
### 11.1 Internationalization & Compliance
The system will initially support US users only. The following are explicitly out of scope for this phase:
*   Internationalization and localization (i18n/l10n)
*   Multi-currency support
*   International tax handling
> **Recommendation: US Sales Tax** Even for US-only, SaaS products may be subject to state-level sales tax depending on the jurisdiction. As of 2026, many US states require sales tax collection on SaaS products. Consider integrating Stripe Tax or a similar service to handle state-level tax calculation and collection before launch. Consult a tax advisor to determine your obligations based on your nexus states.
### 11.2 API & Integration
External API and integration requirements are explicitly out of scope for this project.
> **Recommendation: API-First Architecture** Even though the external API is out of scope, the system should be built with an internal API-first architecture. All subscription management, billing, and feature set operations should be implemented as internal API services. This approach ensures that when external API access is needed in the future, it can be exposed with minimal refactoring.
### 11.3 Admin Reporting
Admin reporting dashboards and analytics are out of scope for this phase. The audit log (Section 10) provides the data foundation for future reporting capabilities.
* * *
## 12\. Open Items
The following items are identified as areas that may warrant further discussion or clarification during the design phase.

| # | Area | Item | Recommendation |
| ---| ---| ---| --- |
| 1 | Billing | Stripe webhook handling: How should the system respond to Stripe-initiated events such as disputes, chargebacks, and automatic card updates? | Implement webhook listeners for critical Stripe events. Handle disputes by notifying the admin. Accept Stripe's automatic card updates. |
| 2 | Compliance | US state-level SaaS sales tax obligations should be assessed before launch. | Integrate Stripe Tax or consult a tax advisor. |
| 3 | Timezone | Access restriction by local date is under consideration. Define the rules for how local timezone affects billing date display and access gating. | Use UTC for all calculations; display local timezone in the UI. Avoid mixing timezones in business logic. |
| 4 | Trial | Should the trial plan show an upgrade prompt or banner as the expiration date approaches? | Yes — display a persistent banner starting 7 days before trial expiration with a link to the plan selection page. |
| 5 | Downgrade | Should disabled items be prioritized differently (e.g., most recently created, or user-selected) instead of the default creation-date order? | Start with creation-date ordering (first N active); add user selection in a future iteration. |
| 6 | Extensions | Should the system allow the same extension type to be stacked (e.g., two blocks of additional users)? | Recommend against stacking. Extensions adjust a specific limit; use a single extension with quantity if needed. |
| 7 | Security | PCI DSS compliance documentation for the integration architecture. | Document Stripe integration pattern (tokenization, no raw card storage) as part of security architecture. |

# Price Tiers

# Price Tiers
Price tiers provide a flexible mechanism for defining alternate pricing for plans, extensions, and payment schedules. They allow the system to offer targeted pricing to specific tenants or transactions, beyond the standard (base) prices.
## Price Tier Types
A price tier can define pricing in one of three ways for any item (plan, extension, or schedule):
1. **Percent Discount:** The price is calculated by applying a percentage discount to the base price (e.g., 10% off).
2. **Fixed Amount Discount:** The price is calculated by subtracting a fixed amount from the base price (e.g., $20 off).
3. **Override Price:** The price is set to a specific value, overriding the base price entirely for the item.

## Application of Price Tiers
Price tiers can be associated with a transaction in two ways:
1. **Tenant Subscription Tier:** If a tenant has a price tier defined in their subscription, the system uses the prices from that tier for all relevant items (if defined). If not defined for an item, the base price is used.
2. **Discount Code Tier:** A discount code can assign a price tier for a transaction under certain conditions. The discount code engine determines if a price tier applies and returns the tier to use for the transaction.

## Fallback Logic
If a price is not defined for an item at the requested tier, the system automatically falls back to the base price for that item and schedule.
## Other Pricing Rules
All other pricing logic—such as proration, schedule changes, and extension pricing—continues to apply as before. Price tiers only affect the effective price selected for the transaction; all calculations and workflows otherwise remain unchanged.
## Summary
*   Price tiers can be defined as a percent discount, a fixed amount discount, or an override price.
*   Price tiers may be assigned to a tenant (for all their transactions) or dynamically applied via discount codes.
*   If a price is not set for a given tier, the system uses the base price.
*   All existing billing and proration logic continues to function the same, regardless of price tier.

# Feature Sets

The following features and limits should be available to assign to a specific tiers when designing the deafferent tiers

AI
*   Token Limits
*   LLM Model level (Basic / Premium)
*   Include conversation coaching
*   Topic Levels (Basic / Advanced / Premium / Ultimate)

Organization
*   Included users
*   Max Users
*   Max People
*   Max Organization Units
*   Max Roles
*   Max Positions

Strategic Planning
*   Max Active Goals
*   Max Strategies per Goal
*   Max Active Measures

Integrations & API
*   Max Integrations
*   API Access

Features
*   Premium Widgets
*   Personal Measures
*   AI Insights
*   Roles, positions & Org Chart

# Discount Codes

An admin need to maintain discount codes that could be applied by users to apply discount on their purchases

Discount Features

## Validity Timeframe
A discount code may have effective and termination date for the period that it is active

## Effective Timeframe
Once applied, for how long the discount applies (in subscription model). This could be limited by date, or referencing a base date such as the date the discount was applied. For example - 20% discount for the first 3 months.
This feature is applicable only to renewable subscriptions.

## Price Change
A discount could be one of three modes:
*   Percent - A percentage discount on the price
*   Amount - A fixed discount amount
*   Override - A new price that will replace the original price for any product or plan/billing frequency this discount is applied to.

## Service Affected
A discount code could be limited to a specific category or product/service
Categories - subscription, rider (extended features), coaching
Specific product or service are those that are priced in the system. for example:
*   Plan + frequency
*   Rider + plan + frequency
*   specific coaching offering

## Eligibility
The discount code may be limited for specific type of uses. for example - new users, renewals, referrals, list-matching, specific domain, specific tenant
The discount may not be available If a tenant is associated with a discount pricing tier
## Repeatability and combination
Determines how frequent can a user use this discount, and if it is allowed to be used with other discounts.
For example, a use of a discount code that is effective for 3 months, may prohibit the user to use a different discount code, even on a different product, for as long as it is active.

