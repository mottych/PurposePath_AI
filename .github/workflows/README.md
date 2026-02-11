# GitHub Actions Workflows

## Workflow Overview

### CI/CD Pipeline (`ci.yml`)
**Trigger**: Automatic on push to `dev` or `master` branches, and on pull requests
**Purpose**: Run tests, linting, type checking, and security scans
**Does NOT deploy** - only validates code quality

### Deploy Dev (`deploy-dev.yml`)
**Trigger**: Manual only (workflow_dispatch)
**Purpose**: Deploy coaching service to dev environment
**How to run**: 
```bash
gh workflow run deploy-dev.yml --ref dev
```
Or via GitHub UI: Actions → Deploy Dev → Run workflow

## Required GitHub Secrets

For deployment to work, ensure these secrets are configured:
- `AWS_ACCESS_KEY_ID` - AWS access key with deployment permissions
- `AWS_SECRET_ACCESS_KEY` - AWS secret key

## Required AWS IAM Permissions

The GitHub Actions user needs these permissions:
- `ecr:GetAuthorizationToken`
- `ecr:BatchCheckLayerAvailability`
- `ecr:GetDownloadUrlForLayer`
- `ecr:BatchGetImage`
- `ecr:PutImage`
- `ecr:InitiateLayerUpload`
- `ecr:UploadLayerPart`
- `ecr:CompleteLayerUpload`
- CloudFormation full access
- Lambda full access
- DynamoDB full access
- API Gateway full access
- S3 access for SAM artifacts
- Secrets Manager read access

## Deployment Flow

1. Push code to `dev` branch → CI workflow runs automatically (tests only)
2. Manually trigger `deploy-dev.yml` workflow when ready to deploy
3. Workflow builds Docker image and deploys to AWS
4. Service available at: `https://api.dev.purposepath.app/coaching/api/v1/`

## Production Promotion Flow

`deploy-production.yml` now deploys automatically when a PR from `staging` into `master` is merged.

- Trigger: `pull_request` closed event where:
  - base branch is `master`
  - source branch is `staging`
  - PR was merged
- Manual override remains available via `workflow_dispatch`.
