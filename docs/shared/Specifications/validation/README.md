# API Contract Validation Notes

Use this folder when contract-sensitive implementation files changed but API contracts did not.

Current artifacts:
- `2026-03-27-billing-epic-pr-781.md`
- `2026-03-27-streamlined-email-cutover-readiness.md`

Purpose:
- Provide explicit evidence that request/response payloads, constraints, and error contracts still match specifications.
- Prevent accidental drift when making bug fixes or internal refactors.

When required:
- Any PR/commit that changes controller, DTO request/response, mapper, or application command/result/handler files for API services,
  and does not update specs under docs/shared/Specifications.

File naming:
- `YYYY-MM-DD-<short-topic>.md`

Minimum template:

```
# Contract Validation - <topic>

## Scope
- Issue/PR: <id>
- Files checked:
  - <path>

## Contract Impact
- Contract impact: none
- Endpoints reviewed:
  - <METHOD> <PATH>

## Verification
- Request payload unchanged: yes/no
- Response payload unchanged: yes/no
- Validation/error behavior unchanged: yes/no
- Spec references:
  - <spec file + section>

## Notes
- <additional context>
```
