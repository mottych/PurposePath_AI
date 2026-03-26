# FE Billing QA/UAT Regression Checklist

## Scope

This checklist covers user-facing billing/subscription workflows aligned to:

- `docs/shared/Requirements/Plans and Subscriptions/plans-requirements.md` (sections 5-9)
- `docs/shared/Specifications/api-fe/billing-frontend-api-specification.md`

Issue tracking:

- Epic: `#805`
- QA/UAT suite: `#814`

## Automation Matrix

| Journey | Requirement Alignment | Automated Coverage | Evidence |
| --- | --- | --- | --- |
| Tenant read surfaces (summary/catalog/entitlements) | Sections 5, 6 | `src/components/AccountManagement.test.tsx` | Vitest run |
| Owner lifecycle render (status/grace/trial/access) | Sections 5, 6 | `src/components/AccountManagement.test.tsx` | Vitest run |
| Plan/schedule preview-confirm flow | Sections 6, 7 | `src/components/AccountManagement.test.tsx`, `e2e/billing-workflows.pw.ts` | Vitest + Playwright |
| Extension preview-confirm + removal flow | Sections 6, 7 | `src/components/AccountManagement.test.tsx`, `e2e/billing-workflows.pw.ts` | Vitest + Playwright |
| Payment method setup/confirm flow | Sections 5, 8 | `src/components/AccountManagement.test.tsx`, `e2e/billing-workflows.pw.ts` | Vitest + Playwright |
| Payment history + detail + receipt | Sections 5, 8 | `src/components/AccountManagement.test.tsx`, `e2e/billing-workflows.pw.ts` | Vitest + Playwright |
| Cancel/reactivate lifecycle controls | Sections 5, 8, 9 | `src/components/AccountManagement.test.tsx`, `e2e/billing-workflows.pw.ts` | Vitest + Playwright |
| Billing audit timeline visibility | Sections 8, 10 | `src/components/AccountManagement.test.tsx` | Vitest run |
| Role boundary regression (`tenant_user` vs `tenant_owner`) | Sections 5, 9 | `src/components/AccountManagement.test.tsx`, `e2e/billing-workflows.pw.ts` | Vitest + Playwright |

## UAT Execution Checklist

### Core Journeys

- [ ] Owner can preview and confirm plan/schedule change with pricing summary.
- [ ] Owner can preview and confirm extension change and schedule extension removal.
- [ ] Owner can update payment method via setup-intent + confirm token.
- [ ] Owner can open payment detail drill-in from history and trigger receipt download.
- [ ] Owner can cancel auto-renew with confirmation and optional reason.
- [ ] Owner can reactivate subscription with optional payment token.
- [ ] Owner can filter and paginate billing audit timeline entries.

### Role/Lifecycle

- [ ] `tenant_user` sees read-only billing surfaces; owner mutation controls are hidden.
- [ ] `tenant_owner` sees all management surfaces and mutation controls.
- [ ] Grace, cancelled, and active lifecycle states render expected banners/messages.
- [ ] Access-state rendering remains consistent after billing mutations.

### Compliance-Oriented UX Checks

- [ ] Cancel control remains explicit and easy to access in account billing page.
- [ ] Cancellation confirms effective behavior (active through termination date).
- [ ] Receipt access remains available from payment history.

## Execution Commands

```bash
npx vitest run src/components/AccountManagement.test.tsx
npx playwright test e2e/billing-workflows.pw.ts
npm test -- --watchAll=false
npm run build -- --emptyOutDir=false
```

## Known Gaps / Follow-ups

- No visual-diff snapshot baseline is currently enforced for billing screens.
- No dedicated production telemetry assertion coverage for billing mutations in E2E.
- If these become release gates, create follow-up issues for:
  - visual regression snapshots for `AccountManagement`
  - test assertions against emitted analytics/telemetry events
