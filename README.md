# PurposePath AI Coaching Service

Serverless AI-powered coaching platform built with AWS SAM, FastAPI, and Amazon Bedrock.

## Quick Start

### Prerequisites

- Python 3.11+
- AWS CLI configured
- AWS SAM CLI
- Docker (for local development)

### Setup

```powershell
.\setup.ps1
```

### Deploy

```powershell
# Deploy coaching service to dev
.\deploy.ps1 -Stage dev
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

- **AWS Lambda** (Serverless Python functions)
- **Amazon Bedrock** (Claude 3.5 Sonnet for AI coaching)
- **DynamoDB** (Data storage with typed models)
- **S3 Buckets** (Prompts and file storage)
- **Custom Domain** with SSL certificate
- **API Gateway** with AWS SAM deployment

## Development Workflow

### Branching Strategy

We follow a **GitFlow-inspired** workflow with three main branches:

```
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
   ```bash
   .\deploy.ps1 -Stage dev
   ```

5. **Create PR to staging** when dev is stable:
   ```bash
   git checkout staging
   git pull origin staging
   # Create PR from dev to staging via GitHub
   ```

6. **Deploy staging** after PR approval:
   ```bash
   .\deploy.ps1 -Stage staging
   ```

7. **Create PR to master** when staging is verified:
   ```bash
   # Create PR from staging to master via GitHub
   ```

8. **Deploy production** after PR approval:
   ```bash
   .\deploy.ps1 -Stage production
   ```

### Environment Endpoints

- **Development**: `https://api.dev.purposepath.app/coaching/api/v1/`

## Deployment

### Quick Deploy

```powershell
# Development
.\deploy.ps1 -Stage dev
```

### Files

- `deploy.ps1` - Deployment script
- `coaching/template.yaml` - Coaching service SAM template

## Shared Types System

The PurposePath AI service uses a comprehensive shared types system for type safety and consistency. 

### Quick Usage

```python
from shared.types import UserId, create_user_id, ConversationId
from shared.types.coaching_models import SessionData, BusinessContext

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
