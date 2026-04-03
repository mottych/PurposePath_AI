# Email Template Service Integration (archived stub)

**Status:** Superseded — do not use this file for integration details.

**Canonical contract (notifications catalog + email templates):**

- `docs/shared/Specifications/api-admin/admin-api-specification.md` (v2.4+)
  - `GET /notifications/catalog` — registry-first catalog (`{ success, data: { items } }`)
  - `GET` / `PATCH /email-templates/by-key/{templateKey}` — template fetch/update by catalog `template_id`

**Admin portal implementation (this repo):**

- `purposepath-admin/src/services/emailTemplateService.ts`
- `purposepath-admin/src/services/notificationCatalogService.ts`
- `purposepath-admin/src/hooks/useEmailTemplates.ts`, `useNotificationCatalog.ts`

The previous long-form guide in this path described outdated endpoints and hooks and has been removed.
