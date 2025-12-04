# PurposePath AI Coaching Service

Serverless AI-powered coaching platform built with Pulumi, FastAPI, and Amazon Bedrock.

## Quick Start

### Prerequisites

- Python 3.11+
- AWS CLI configured
- Pulumi CLI (`choco install pulumi` or download from pulumi.com)
- Node.js 18+ (for Lambda Pulumi project)
- Docker (for building Lambda container images)

### Setup

```powershell
# Install dependencies
pip install -r requirements.txt

# Configure Pulumi (first time only)
pulumi login
```

### Deploy

```powershell
# Deploy infrastructure (DynamoDB tables, S3 buckets)
cd infrastructure/pulumi
pulumi up

# Deploy Lambda function and API Gateway
cd ../../coaching/pulumi
pulumi up
```

## Architecture

- **Coaching Service**: AI coaching conversations, insights, business data analysis
- **Shared Types**: Strongly-typed definitions for consistency across services
- **Custom Domain**: `api.dev.purposepath.app`
- **API Paths**:
  - `/account/api/v1/*` → Account Service
  - `/coaching/api/v1/*` → Coaching Service
  - `/traction/api/v1/*` → Traction Service

## Infrastructure

- **AWS Lambda** (Serverless Python functions in Docker containers)
- **Amazon Bedrock** (Claude 3.5 Sonnet for AI coaching)
- **DynamoDB** (Data storage with typed models, Point-in-Time Recovery enabled)
- **S3 Buckets** (Prompts and file storage with versioning and encryption)
- **Custom Domain** with SSL certificate
- **API Gateway HTTP API** deployed via Pulumi
- **ECR** (Container registry for Lambda images)

## Development Workflow

### Branching Strategy

We follow a **GitFlow-inspired** workflow with three main branches:

```text
master (production)  ←── PR ←── staging ←── PR ←── dev ←── feature branches
```

#### Main Branches

- **`master`** - Production environment
- **`staging`** - Staging environment
- **`dev`** - Development environment (`api.dev.purposepath.app/coaching`)

#### Feature Development Process

1. **Create feature branch** from `dev`:

   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/your-feature-name
   ```

2. **Develop and commit** your changes:

   ```bash
   git add .
   git commit -m "feat: description of your feature"
   ```

3. **Merge to dev** when feature is complete:

   ```bash
   git checkout dev
   git merge feature/your-feature-name
   git branch -d feature/your-feature-name  # Delete feature branch
   git push origin dev
   ```

4. **Deploy to dev** for testing:

   ```powershell
   cd infrastructure/pulumi
   pulumi up
   cd ../../coaching/pulumi
   pulumi up
   ```

5. **Create PR to staging** when dev is stable:

   ```bash
   git checkout staging
   git pull origin staging
   # Create PR from dev to staging via GitHub
   ```

6. **Deploy staging** after PR approval (use staging stack):

   ```powershell
   pulumi stack select staging
   pulumi up
   ```

7. **Create PR to master** when staging is verified:

   ```bash
   # Create PR from staging to master via GitHub
   ```

8. **Deploy production** after PR approval (use production stack):

   ```powershell
   pulumi stack select production
   pulumi up
   ```

### Environment Endpoints

- **Development**: `https://api.dev.purposepath.app/coaching/api/v1/`

## Deployment

### Pulumi Projects

The infrastructure is split into two Pulumi projects:

1. **`infrastructure/pulumi`** - Core infrastructure (DynamoDB tables, S3 buckets)
2. **`coaching/pulumi`** - Lambda function, API Gateway, and application resources

### Deployment Steps

```powershell
# 1. Deploy infrastructure first
cd infrastructure/pulumi
pulumi up

# 2. Deploy Lambda and API Gateway
cd ../../coaching/pulumi
pulumi up
```

### Stack Management

```powershell
# List available stacks
pulumi stack ls

# Switch to a different stack
pulumi stack select dev

# View stack outputs
pulumi stack output
```

## Shared Types System

The PurposePath AI service uses a comprehensive shared types system for type safety and consistency.

### Quick Usage

```python
from shared.domain_types import UserId, create_user_id, ConversationId
from shared.domain_types.coaching_models import SessionData, BusinessContext

# Strong typing with domain IDs
user_id = create_user_id("usr_123")
conversation_id = create_conversation_id()

# Typed coaching session data
session_data: SessionData = {
    "phase": "introduction",
    "context": {},
    "business_context": business_context,
    "user_preferences": user_preferences
}
```

### Features

- **Strong Domain IDs**: `UserId`, `TenantId`, `ConversationId` with compile-time safety
- **DynamoDB Inheritance**: All items inherit from `DynamoDBBaseItem` 
- **Repository Types**: Specific `TypedDict` for all method returns
- **External APIs**: Types for Stripe, Google OAuth, AWS Lambda
- **Consistency**: Eliminates `dict[str, Any]` usage project-wide

📖 **See [`docs/shared-types-guide.md`](docs/shared-types-guide.md) for complete documentation**

## Project Automation

Issues and PRs can be auto-added to a GitHub Project. See `docs/github-projects-setup.md` to configure the required secret and variable.
