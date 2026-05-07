# Billing First-Time Enablement Runbook

Last updated: March 26, 2026
Related issues: #735, #749

## Purpose

This runbook defines the first-time enablement sequence for the backend billing system. It assumes a greenfield rollout with no legacy billing migration or historical billing backfill.

## Scope

This runbook covers:

- environment readiness checks
- staged enablement sequence
- operational monitoring gates
- rollback decision points
- required evidence before production cutover

This runbook does not cover frontend release tasks in other repositories.

## Preconditions

Complete these checks before enabling billing outside local development.

### Code and Contract Readiness

1. All billing child issues under epic `#735` are completed or explicitly deferred.
2. The solution builds clean with no warnings or errors.
3. The billing validation matrix in [billing-rollout-validation-matrix.md](../../validation/billing-rollout-validation-matrix.md) is current.
4. API contracts remain aligned with:
   - the deployed Account runtime OpenAPI endpoint for owner billing flows
   - the deployed Admin runtime OpenAPI endpoint for billing administration flows
   - [README.md](../../shared/Specifications/README.md) for the canonical contract-source and thin-spec workflow

### Environment and Secret Readiness

1. Stripe API keys and webhook signing secret exist for the target environment.
2. SES sender/domain verification is healthy.
3. DynamoDB tables, lambda functions, and billing EventBridge rules are deployed.
4. CloudWatch logging and alarm destinations are configured for billing lambdas.
5. A designated fallback plan is configured if fallback access is expected after grace expiry.
6. Billing settings are populated with intentional values for:
   - retry delay days
   - max automatic attempts per cycle
   - card expiry warning days
   - price change notice minimum days
   - annual renewal reminder lead window days
   - notification policies

### Operator Readiness

1. Admin/operator knows how to:
   - inspect billing audit entries
   - inspect payment history and receipts
   - review webhook failures
   - disable billing EventBridge schedules
   - revert production enablement if smoke checks fail
2. Support team has a path for manual refund handling and Stripe investigation.

## Enablement Sequence

### Stage 1: Dev Verification

1. Run billing-focused tests and a full solution build.
2. Confirm local configuration can start billing lambdas and owner/admin controllers.
3. Verify no open compile, lint, or contract alignment issues remain.

Exit gate:
- build clean
- targeted billing tests green

### Stage 2: Staging Deployment

1. Deploy the current epic branch contents through the normal staging path.
2. Confirm the following lambdas are present and healthy:
   - billing webhook handler
   - renewal handler
   - retry handler
   - notification sweep handler
3. Confirm EventBridge rules exist for retry, renewal, and notification sweep.
4. Confirm Stripe staging/test configuration and webhook delivery.

Exit gate:
- services deployed successfully
- logs visible in CloudWatch
- alarms attached or explicitly noted as pending

### Stage 3: Staging Smoke Validation

Execute the following flow set in staging and capture evidence in issue `#749`.

1. Admin billing catalog smoke:
   - list plans, schedules, price tiers, settings
   - verify admin audit endpoint returns billing events
2. Trial-to-paid enrollment:
   - enroll a trial tenant into a paid plan
   - verify proration/payment result, receipt availability, and owner audit visibility
3. Payment method flow:
   - create setup intent
   - confirm payment method
   - verify masked payment method read
4. Renewal and retry flow:
   - run renewal handler against controlled test data
   - verify payment success path
   - run failure/retry path and confirm grace behavior
5. Notification sweep:
   - verify annual renewal reminder or payment-method expiry reminder is queued when expected
6. Webhook replay safety:
   - replay a duplicate provider event and confirm idempotent handling
7. Fallback/block path:
   - validate post-grace behavior for a tenant with controlled data

Exit gate:
- no unexplained billing failures
- audit and reconciliation evidence available
- notification queueing observed for expected scenarios

### Stage 4: Production Readiness Review

Before production cutover, review the staging evidence and explicitly answer:

1. Are all high-risk flows in the validation matrix covered by either automated evidence or staging smoke evidence?
2. Are any unresolved blockers still open?
3. Is fallback configuration intentional and confirmed?
4. Are rollback operators available during the cutover window?

If any answer is no, do not enable production billing.

### Stage 5: Production Enablement

1. Deploy the validated billing build/artifact.
2. Confirm secrets and config one final time.
3. Enable billing EventBridge rules only after deployment health is confirmed.
4. Run a narrow production smoke check using a controlled internal/admin-owned tenant if policy allows.
5. Monitor logs, alarms, and audit output closely through the initial billing window.

## Monitoring Gates

The following signals must stay healthy during enablement:

1. No sustained 5xx responses from account/admin billing endpoints.
2. No unexpected webhook signature or parsing failures.
3. Renewal/retry handlers complete without unexplained spikes in failure count.
4. Notification sweep completes and does not flood duplicate requests.
5. Reconciliation discrepancy volume remains explainable and low.

## Rollback Strategy

Rollback goal: stop new billing mutations and scheduled billing side effects while preserving data for investigation.

### Immediate Containment Steps

1. Disable EventBridge schedules for renewal, retry, and notification sweep.
2. Stop any production smoke activity that is still in progress.
3. Preserve CloudWatch logs, billing audit data, and reconciliation evidence.

### Functional Rollback Decision Tree

Use containment-only rollback when:

- recurring charges are behaving unexpectedly
- notification sweeps are noisy or duplicating
- webhook processing is unreliable

Use full release rollback when:

- owner/admin billing endpoints are producing incorrect mutations
- billing state transitions are corrupting subscription access state
- provider integration is charging incorrectly

### Full Rollback Actions

1. Revert to the last validated non-billing production release if one exists in the rollout plan.
2. Keep billing tables and audit data intact for investigation.
3. Do not delete or mutate recorded payment/audit history during rollback.
4. Open follow-up incident or blocker issues before attempting a new enablement.

## Evidence Required Before Closing Issue 749

1. Current validation matrix committed in the repo.
2. Staging smoke summary captured in issue comments.
3. Build and targeted test evidence captured in issue comments.
4. Any unresolved blockers called out explicitly.

## Notes

- This is a first-time enablement runbook, not a legacy migration runbook.
- If production-specific prerequisites cannot be verified from the repo, they remain external gates and must be tracked as such rather than assumed complete.