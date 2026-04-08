# Contract Validation - issue-901-email-template-subject-no-contract-change

## Scope
- Issue/PR: #901 / #902
- Files checked:
  - PurposePath.Application/Commands/Admin/EmailTemplates/EmailTemplateCommands.cs
  - PurposePath.Application/Handlers/Admin/EmailTemplates/EmailTemplateHandlers.cs
  - Services/PurposePath.Admin.Lambda/Controllers/EmailTemplatesController.cs
  - PurposePath.Application/Services/Admin/IEmailTemplateAdminService.cs
  - PurposePath.Application/Services/Admin/EmailTemplateAdminService.cs

## Contract Impact
- Contract impact: none
- Endpoints reviewed:
  - PATCH /admin/api/v1/email-templates/{id}
  - PATCH /admin/api/v1/email-templates/by-key/{templateKey}
  - GET /admin/api/v1/email-templates/{id}
  - GET /admin/api/v1/email-templates/by-key/{templateKey}

## Verification
- Request payload unchanged: yes
- Response payload unchanged: yes
- Validation/error behavior unchanged: yes
- Spec references:
  - docs/shared/Specifications/api-admin/admin-api-specification.md

## Notes
- The implementation now persists the existing `subject` field already present in PATCH request models.
- No new request/response fields were added and no endpoint routes or HTTP methods changed.
- Fix scope is internal propagation (controller -> command -> handler -> service) and persistence behavior parity.
