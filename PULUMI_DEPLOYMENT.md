# Pulumi Deployment Guide

Complete guide for deploying PurposePath AI infrastructure and services using Pulumi.

## Overview

The PurposePath AI platform uses **two separate Pulumi projects**:

1. **Infrastructure Project** (`infrastructure/pulumi/`) - Core AWS resources
2. **Lambda Project** (`coaching/pulumi/`) - Application deployment

## Prerequisites

### Required Tools

- **Pulumi CLI** 3.0+
  ```powershell
  choco install pulumi
  # or download from https://www.pulumi.com/docs/get-started/install/
  ```

- **AWS CLI** configured with credentials
  ```powershell
  aws configure
  ```

- **Python** 3.11+
  ```powershell
  python --version
  ```

- **Node.js** 18+ (for Lambda Pulumi project)
  ```powershell
  node --version
  npm --version
  ```

- **Docker Desktop** (for building Lambda container images)
  ```powershell
  docker --version
  ```

### Pulumi Account Setup

```powershell
# Login to Pulumi (first time only)
pulumi login

# Or use local backend
pulumi login --local
```

## Project Structure

```text
pp_ai/
├── infrastructure/pulumi/     # Infrastructure Pulumi project
│   ├── __main__.py           # DynamoDB tables, S3 buckets
│   ├── Pulumi.yaml
│   └── requirements.txt
│
└── coaching/pulumi/          # Lambda Pulumi project
    ├── __main__.py           # Lambda, API Gateway, IAM
    ├── index.ts              # Alternative TypeScript implementation
    ├── Pulumi.yaml
    ├── package.json
    └── requirements.txt
```

## Infrastructure Project

### What It Deploys

- **DynamoDB Tables**:
  - `coaching_conversations` - Conversation history
  - `coaching_sessions` - Session tracking
  - `llm_prompts` - LLM prompt templates
- **S3 Bucket**: `purposepath-coaching-prompts-dev` - Prompt storage
- **Features**:
  - Point-in-Time Recovery enabled
  - DynamoDB Streams on `llm_prompts`
  - S3 versioning and encryption
  - Public access blocking

### Deploy Infrastructure

```powershell
# Navigate to infrastructure project
cd infrastructure/pulumi

# Install Python dependencies
pip install -r requirements.txt

# Preview changes
pulumi preview

# Deploy
pulumi up

# View outputs
pulumi stack output
```

### Expected Outputs

```yaml
dynamoTables:
  coachingConversations: coaching_conversations
  coachingSessions: coaching_sessions
  llmPrompts: llm_prompts
promptsBucket: purposepath-coaching-prompts-dev
tableArns:
  conversations: arn:aws:dynamodb:us-east-1:ACCOUNT:table/coaching_conversations
  sessions: arn:aws:dynamodb:us-east-1:ACCOUNT:table/coaching_sessions
  prompts: arn:aws:dynamodb:us-east-1:ACCOUNT:table/llm_prompts
```

## Lambda Project

### What It Deploys

- **ECR Repository**: `purposepath-coaching` - Docker image storage
- **Docker Image**: Built from `coaching/Dockerfile`
- **Lambda Function**: `coaching-api` - FastAPI application
- **IAM Role & Policies**:
  - DynamoDB access (read/write)
  - Bedrock access (InvokeModel)
  - S3 access (prompts bucket)
- **API Gateway HTTP API**: Routes to Lambda
- **API Mapping**: `https://api.dev.purposepath.app/coaching`

### Deploy Lambda

```powershell
# Navigate to Lambda project
cd coaching/pulumi

# Install dependencies (Python)
pip install -r requirements.txt

# OR install dependencies (Node.js/TypeScript)
npm install

# Preview changes
pulumi preview

# Deploy (builds Docker image automatically)
pulumi up

# View outputs
pulumi stack output
```

### Expected Outputs

```yaml
apiId: abc123xyz
customDomainUrl: https://api.dev.purposepath.app/coaching
lambdaArn: arn:aws:lambda:us-east-1:ACCOUNT:function:coaching-api-abc123
```

## Stack Management

### Create New Stack

```powershell
# Create staging stack
pulumi stack init staging

# Create production stack
pulumi stack init production
```

### Switch Between Stacks

```powershell
# List all stacks
pulumi stack ls

# Switch to dev
pulumi stack select dev

# Switch to staging
pulumi stack select staging

# Switch to production
pulumi stack select production
```

### Stack-Specific Configuration

```powershell
# Set configuration for current stack
pulumi config set aws:region us-east-1
pulumi config set stage dev

# Set secrets (encrypted)
pulumi config set --secret jwtSecret "your-secret-key"

# View configuration
pulumi config
```

## Full Deployment Workflow

### First-Time Deployment

```powershell
# 1. Deploy infrastructure
cd infrastructure/pulumi
pulumi stack select dev
pulumi up

# 2. Deploy Lambda and API
cd ../../coaching/pulumi
pulumi stack select dev
pulumi up
```

### Update Deployment

```powershell
# Update infrastructure only
cd infrastructure/pulumi
pulumi up

# Update Lambda only (rebuilds Docker image)
cd coaching/pulumi
pulumi up
```

### Rollback

```powershell
# View deployment history
pulumi stack history

# Rollback to previous version
pulumi stack export --version 5 > previous.json
pulumi stack import --file previous.json
```

## Environment-Specific Deployments

### Development

```powershell
pulumi stack select dev
pulumi config set stage dev
pulumi config set aws:region us-east-1
pulumi up
```

### Staging

```powershell
pulumi stack select staging
pulumi config set stage staging
pulumi config set aws:region us-east-1
pulumi up
```

### Production

```powershell
pulumi stack select production
pulumi config set stage production
pulumi config set aws:region us-east-1
pulumi up
```

## Troubleshooting

### Docker Build Fails

```powershell
# Check Docker is running
docker ps

# Manually build to test
cd coaching
docker build -t test-image .
```

### ECR Authentication Issues

```powershell
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
```

### Pulumi State Issues

```powershell
# Refresh state from AWS
pulumi refresh

# Export state for backup
pulumi stack export > backup.json
```

### Lambda Deployment Timeout

```powershell
# Increase timeout in __main__.py
timeout=600  # 10 minutes
```

## Destroy Resources

### Destroy Lambda Resources

```powershell
cd coaching/pulumi
pulumi destroy
```

### Destroy Infrastructure

**⚠️ WARNING: This deletes all DynamoDB tables and S3 buckets!**

```powershell
cd infrastructure/pulumi
pulumi destroy
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to AWS

on:
  push:
    branches: [dev, staging, main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Install Pulumi
        uses: pulumi/actions@v4
      
      - name: Deploy Infrastructure
        working-directory: infrastructure/pulumi
        run: |
          pip install -r requirements.txt
          pulumi stack select dev
          pulumi up --yes
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
      
      - name: Deploy Lambda
        working-directory: coaching/pulumi
        run: |
          pip install -r requirements.txt
          pulumi stack select dev
          pulumi up --yes
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

## Best Practices

### 1. Always Preview First

```powershell
pulumi preview  # Review changes before applying
```

### 2. Use Stack References

The Lambda project references the infrastructure project:

```python
infra = pulumi.StackReference("mottych/purposepath-infrastructure/dev")
prompts_bucket = infra.get_output("promptsBucket")
```

### 3. Tag All Resources

```python
common_tags = {
    "Project": "PurposePath",
    "ManagedBy": "Pulumi",
    "Environment": pulumi.get_stack(),
}
```

### 4. Enable Point-in-Time Recovery

```python
point_in_time_recovery=aws.dynamodb.TablePointInTimeRecoveryArgs(enabled=True)
```

### 5. Use Secrets for Sensitive Data

```powershell
pulumi config set --secret apiKey "secret-value"
```

## Monitoring

### View Logs

```powershell
# Lambda logs
pulumi logs --follow

# Or use AWS CLI
aws logs tail /aws/lambda/coaching-api --follow
```

### Check Resource Status

```powershell
# List all resources in stack
pulumi stack

# View specific resource details
pulumi stack export | jq '.deployment.resources[] | select(.type=="aws:lambda/function:Function")'
```

## Support

- **Pulumi Documentation**: https://www.pulumi.com/docs/
- **AWS Provider Docs**: https://www.pulumi.com/registry/packages/aws/
- **Project Issues**: Create an issue in the repository

## Migration from SAM

If you previously used SAM, note these changes:

| SAM | Pulumi |
|-----|--------|
| `template.yaml` | `__main__.py` |
| `sam build` | Automatic in `pulumi up` |
| `sam deploy` | `pulumi up` |
| `samconfig.toml` | `Pulumi.yaml` + stack config |
| CloudFormation stacks | Pulumi stacks |
| Parameters | `pulumi config` |

All SAM templates and deployment scripts have been removed from the repository.
