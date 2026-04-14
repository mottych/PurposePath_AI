# Deployment

AWS infrastructure and application deployment use **Pulumi**, not AWS SAM or CloudFormation templates in this repository.

- Coaching Lambda/API: `coaching/pulumi/`
- Broader platform infra: `infrastructure/pulumi/` (and related docs)

Legacy SAM templates and `sam deploy` helper scripts previously under `deployment/account-service/` and `deployment/shared-infrastructure/` have been removed as unused.

See `PULUMI_DEPLOYMENT.md` at the repository root for the current workflow.
