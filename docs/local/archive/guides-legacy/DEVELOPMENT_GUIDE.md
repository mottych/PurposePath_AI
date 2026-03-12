# PurposePath AI Coaching - Development Guide

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- AWS CLI configured with proper credentials
- AWS SAM CLI installed
- Docker (for local development)
- Git

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/mottych/PurposePath_Api.git
cd PurposePath_Api/pp_ai

# Setup virtual environment and dependencies
.\setup.ps1

# Deploy to development environment
.\deploy.ps1 -Stage dev -HostedZoneId YOUR_HOSTED_ZONE_ID
```

## 🌳 Branching Strategy

### Branch Overview

```
master (production)  ←── PR ←── staging ←── PR ←── dev ←── feature branches
     ↓                        ↓                 ↓
ai-coaching.purposepath.app   staging.app     dev.app
```

### Branch Purposes

| Branch | Environment | Purpose | Auto-Deploy |
|--------|-------------|---------|-------------|
| `master` | Production | Live customer-facing API | ❌ Manual |
| `staging` | Staging | Pre-production testing | ❌ Manual |
| `dev` | Development | Integration testing | ✅ Continuous |

### Feature Development Workflow

#### 1. Start New Feature

```bash
# Switch to dev and get latest changes
git checkout dev
git pull origin dev

# Create feature branch with descriptive name
git checkout -b feature/user-session-improvements
```

#### 2. Develop and Test

```bash
# Make your changes...
# Run tests
cd coaching && uv run pytest

# Commit with conventional commit format
git add .
git commit -m "feat: improve user session handling with better error messages"
```

#### 3. Complete Feature

```bash
# Switch back to dev
git checkout dev
git pull origin dev  # Get any new changes

# Merge your feature (fast-forward)
git merge feature/user-session-improvements

# Clean up
git branch -d feature/user-session-improvements

# Push to dev
git push origin dev
```

#### 4. Deploy to Dev (Automatic)

```bash
# Deploy to development environment for testing
.\deploy.ps1 -Stage dev
```

#### 5. Promote to Staging

When `dev` is stable and ready for staging:

```bash
# Create PR from dev to staging via GitHub UI
# OR merge directly if you have permissions:
git checkout staging
git pull origin staging
git merge dev
git push origin staging

# Deploy to staging
.\deploy.ps1 -Stage staging
```

#### 6. Promote to Production

When `staging` is verified and ready for production:

```bash
# Create PR from staging to master via GitHub UI
# After approval and merge:
git checkout master
git pull origin master

# Deploy to production
.\deploy.ps1 -Stage production
```

## 🚀 Deployment Guide

### Environment Configuration

Each environment has its own:
- Domain name
- AWS resources
- Configuration parameters
- SSL certificates

| Environment | Domain | Stack Prefix |
|-------------|--------|--------------|
| Development | `ai-coaching.dev.purposepath.app` | `purposepath-coaching-api-dev` |
| Staging | `ai-coaching.staging.purposepath.app` | `purposepath-coaching-api-staging` |
| Production | `ai-coaching.purposepath.app` | `purposepath-coaching-api-production` |

### Deployment Commands

```bash
# Development
.\deploy.ps1 -Stage dev -Region us-east-1 -HostedZoneId Z09156212RNBEXAMPLE

# Staging
.\deploy.ps1 -Stage staging -Region us-east-1 -HostedZoneId Z09156212RNBEXAMPLE

# Production
.\deploy.ps1 -Stage production -Region us-east-1 -HostedZoneId Z09156212RNBEXAMPLE
```

### Deployment Process

1. **Domain Setup** - Creates SSL certificate and custom domain
2. **Service Build** - Compiles and packages the coaching service
3. **Infrastructure Deploy** - Creates/updates AWS resources
4. **API Mapping** - Maps custom domain to API Gateway

## 🧪 Testing Strategy

### Local Testing

```bash
# Run unit tests
cd coaching
uv run pytest tests/unit/ -v

# Run integration tests  
uv run pytest tests/integration/ -v

# Run all tests
uv run pytest tests/ -v
```

### Environment Testing

- **Dev**: Automated testing after each merge
- **Staging**: Manual testing and user acceptance testing
- **Production**: Monitoring and health checks

## 📝 Commit Conventions

Use conventional commit format:

```
type(scope): description

feat(coaching): add new conversation templates
fix(api): resolve session timeout issues
docs(readme): update deployment instructions
test(integration): add coaching workflow tests
refactor(models): simplify user preference structure
```

### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding or updating tests
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `ci`: CI/CD changes

## 🔧 Development Tools

### Required Tools

```bash
# Python package manager
pip install uv

# AWS tools
pip install aws-sam-cli
aws configure

# Testing
pip install pytest pytest-asyncio

# Code quality
pip install black ruff mypy
```

### VS Code Extensions

- Python
- AWS Toolkit
- GitLens
- Prettier
- Thunder Client (API testing)

## 🚨 Troubleshooting

### Common Issues

#### Deployment Fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify SAM CLI
sam --version

# Clean and rebuild
cd coaching
sam build --clean
```

#### Tests Failing
```bash
# Install dependencies
uv sync

# Run specific test
uv run pytest tests/unit/test_specific.py -v -s
```

#### Import Errors
```bash
# Verify Python path
cd coaching
export PYTHONPATH=".:../shared:$PYTHONPATH"
```

### Getting Help

1. Check this development guide
2. Review error logs in CloudWatch
3. Consult the team in Slack
4. Create GitHub issue for bugs

## 📊 Monitoring

### CloudWatch Logs

- Lambda function logs: `/aws/lambda/purposepath-coaching-*`
- API Gateway logs: Look for the coaching API in CloudWatch

### Health Check

```bash
# Check development environment
curl https://ai-coaching.dev.purposepath.app/coaching/api/v1/health

# Check production environment  
curl https://ai-coaching.purposepath.app/coaching/api/v1/health
```

## 🔐 Security

### Environment Variables

Never commit:
- API keys
- Database credentials
- AWS access keys
- Environment-specific configs

Use AWS Parameter Store or Secrets Manager for sensitive data.

### Code Review

- All changes require code review
- Use GitHub pull requests
- Run security scans before deployment