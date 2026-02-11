# Production Promotion Checklist

This checklist verifies that automatic promotion from `staging` to `master` reliably deploys to production.

## 1) GitHub Branch and Workflow Alignment

- [ ] Repository default branch is `master`
- [ ] Production workflow trigger is `pull_request` closed on `master`
- [ ] Production workflow validates merged PR source branch is `staging`
- [ ] `deploy-production.yml` workflow is enabled

Quick checks:

```bash
gh repo view --json defaultBranchRef
gh api repos/:owner/:repo/actions/workflows
gh run list --workflow "deploy-production.yml" --limit 10
```

## 2) GitHub Repository Secrets

Required:

- [ ] `AWS_ACCESS_KEY_ID`
- [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] `PULUMI_ACCESS_TOKEN`

Quick check:

```bash
gh secret list
```

## 3) GitHub Environments and Protection

Recommended for production safety:

- [ ] Create `production` environment in GitHub
- [ ] Add required reviewers for production deployments
- [ ] Restrict deployments to `master`

Quick check:

```bash
gh api repos/:owner/:repo/environments
```

## 4) Branch Protection Rules

Recommended branch protection:

- [ ] Protect `master`
- [ ] Require PR before merge
- [ ] Require status checks to pass before merge
- [ ] Restrict direct pushes

Quick check:

```bash
gh api repos/:owner/:repo/branches/master/protection
```

## 5) AWS Account Access and Resources

- [ ] AWS identity used by deployment has production deployment permissions
- [ ] Production API domain exists (`api.purposepath.app`)
- [ ] Production data resources exist and are healthy

Quick checks:

```bash
aws sts get-caller-identity
aws apigatewayv2 get-domain-names --output table
aws dynamodb list-tables --output table
```

## 6) Pulumi Stack Readiness

Production deploy workflow currently targets stack name `prod`.

- [ ] `coaching/pulumi` has stack `prod`
- [ ] If infrastructure is managed separately, production infra stack is deployed and stable

Quick checks:

```bash
cd coaching/pulumi
pulumi stack ls
```

If `prod` stack does not exist:

```bash
cd coaching/pulumi
pulumi stack init prod
pulumi config set aws:region us-east-1 --stack prod
```

## 7) Promotion Execution

1. Merge PR from `staging` into `master`
2. Confirm `Deploy Production` workflow starts automatically
3. Confirm deployment job succeeds
4. Confirm smoke tests succeed
5. Confirm API health endpoint returns expected status

Post-deployment verification:

```bash
gh run list --workflow "deploy-production.yml" --limit 5
curl -i https://api.purposepath.app/coaching/health
```
