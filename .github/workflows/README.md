# GitHub Actions Workflows

## Workflow Overview

### CI/CD Pipeline (`ci.yml`)
**Trigger**: Automatic on push to `dev` or `master` branches, and on pull requests
**Purpose**: Run tests, linting, type checking, and security scans
**Does NOT deploy** - only validates code quality

### Deploy Dev (`deploy-dev.yml`)
**Trigger**: Push to `dev`, or manual `workflow_dispatch`
**Purpose**: Deploy coaching service to dev environment
**How to run**: 
```bash
gh workflow run deploy-dev.yml --ref dev
```
Or via GitHub UI: Actions → Deploy Dev → Run workflow

### Deploy Staging (`deploy-staging.yml`)
**Trigger**: Push to `staging`, or manual `workflow_dispatch`  
**Purpose**: Deploy staging stack and run smoke checks

### Deploy Preprod (`deploy-preprod.yml`)
**Trigger**: Push to `hotfix/**` or `preprod`, or manual `workflow_dispatch`  
**Purpose**: Permanent preprod deployment path for hotfix validation before production promotion

How to run manually:
```bash
gh workflow run deploy-preprod.yml --ref preprod -f branch=preprod
```

## Required GitHub Secrets

For deployment to work, ensure these secrets are configured:
- `AWS_ACCESS_KEY_ID` - AWS access key with deployment permissions
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `PULUMI_ACCESS_TOKEN` - Pulumi access token

Environment-specific recommendations:
- Configure protected `preprod` and `production` GitHub Environments
- Scope deployment secrets to those environments where possible

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
2. `deploy-dev.yml` deploys dev stack
3. Workflow builds Docker image and deploys to AWS
4. Service available at: `https://api.dev.purposepath.app/coaching/api/v1/`

## Production Promotion Flow

`deploy-production.yml` deploys production on merged PRs into `master` from:
- `staging` (existing promotion path)
- `preprod` (hotfix promotion path)

- Trigger: `pull_request` closed event where:
  - base branch is `master`
  - source branch is `staging` or `preprod`
  - PR was merged
- Manual override remains available via `workflow_dispatch`.

### Same-artifact promotion (preprod -> prod)

- Preprod deploy exports `deployedImageUri` from Pulumi and captures promotion metadata.
- Production promotion resolves the image URI (explicit manual input or preprod ECR tag digest) and injects it via `COACHING_IMAGE_URI`.
- `deploy-production.yml` verifies the deployed prod image URI matches the resolved promotion image URI.
