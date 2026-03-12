# PurposePath AI Coaching - Deployment Guide

**Version:** 2.0.0  
**Last Updated:** October 10, 2025  
**Architecture:** Phase 7 (API Layer with Auth-based Context)

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Local Development](#local-development)
5. [AWS SAM Deployment](#aws-sam-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deployment of the PurposePath AI Coaching API using AWS SAM (Serverless Application Model). The application uses:

- **AWS Lambda** - Serverless compute for API
- **Amazon API Gateway (HTTP API)** - API endpoint management
- **Amazon DynamoDB** - NoSQL database for conversations and sessions
- **Amazon S3** - Prompt template storage
- **Amazon Bedrock** - LLM inference
- **AWS Secrets Manager** - JWT secret management

### Current Architecture (Phase 7)

The application now uses:
- `main_v2.py` - FastAPI application with Phase 7 architecture
- Auth-based context extraction (JWT tokens)
- New API routes: conversations_v2.py, analysis.py
- Middleware: error handling, rate limiting, logging
- Dependency injection for Phase 4-6 services

---

## Architecture

### Application Entry Point

**Lambda Handler**: `src.api.main_v2.handler`

The handler is defined in `/coaching/src/api/main_v2.py`:

```python
from mangum import Mangum
from fastapi import FastAPI

app = FastAPI(
    title="PurposePath AI Coaching API",
    version="2.0.0",
    # ... configuration
)

# Middleware stack
app.add_middleware(CORSMiddleware, ...)
app.add_middleware(RateLimitingMiddleware, ...)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Routes
app.include_router(conversations_v2.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1/health")

# Lambda handler
handler = Mangum(app, lifespan="off")
```

### API Routes

The SAM template (`coaching/template.yaml`) defines these routes:

**Phase 7 Routes:**
- `GET /` - Root endpoint
- `GET /api/v1/health` - Health check
- `POST /api/v1/conversations/initiate` - Start conversation
- `POST /api/v1/conversations/{id}/message` - Send message
- `GET /api/v1/conversations/{id}` - Get conversation
- `GET /api/v1/conversations/` - List conversations
- `POST /api/v1/conversations/{id}/pause` - Pause conversation
- `POST /api/v1/conversations/{id}/complete` - Complete conversation
- `POST /api/v1/analysis/alignment` - Alignment analysis
- `POST /api/v1/analysis/strategy` - Strategy analysis
- `POST /api/v1/analysis/kpi` - KPI analysis
- `POST /api/v1/analysis/operations` - Operations analysis

**Legacy Routes (backward compatibility):**
- `/api/v1/suggestions/*` - Suggestion endpoints

### Database Tables

**1. Conversations Table** (`purposepath-conversations-{stage}`)
- Primary Key: `conversation_id` (HASH)
- GSIs:
  - `tenant_id-user_id-index` - Multi-tenant queries
  - `user_id-created_at-index` - User conversation history

**2. Coaching Sessions Table** (`purposepath-coaching-sessions-{stage}`)
- Primary Key: `session_id` (HASH)
- GSIs:
  - `tenant_id-user_id-index` - Multi-tenant queries
  - `user_id-topic-index` - Topic-based queries
  - `tenant_id-started_at-index` - Time-based queries

### Storage

**S3 Bucket**: `purposepath-coaching-prompts-{stage}`
- Stores prompt templates (YAML format)
- Organized by topic and analysis type
- Versioned for rollback capability

---

## Prerequisites

### Required Tools

1. **AWS CLI** (v2.x or later)
   ```bash
   aws --version
   ```

2. **AWS SAM CLI** (v1.x or later)
   ```bash
   sam --version
   ```

3. **Docker** (for building Lambda images)
   ```bash
   docker --version
   ```

4. **Python** (3.11 or later)
   ```bash
   python --version
   ```

### AWS Credentials

Configure AWS credentials with appropriate permissions:

```bash
aws configure
```

Required IAM permissions:
- CloudFormation full access
- Lambda full access
- API Gateway full access
- DynamoDB full access
- S3 full access
- Secrets Manager read/write
- Bedrock invoke model

---

## Local Development

### Setup Virtual Environment

```bash
cd coaching

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create `.env` file in `/coaching`:

```env
# Application
STAGE=dev
LOG_LEVEL=DEBUG
APPLICATION_NAME=PurposePath
API_PREFIX=/api/v1

# Database
CONVERSATIONS_TABLE=purposepath-conversations-dev
COACHING_SESSIONS_TABLE=purposepath-coaching-sessions-dev

# AWS Services
AWS_REGION=us-east-1
PROMPTS_S3_BUCKET=purposepath-coaching-prompts-dev

# Authentication
JWT_SECRET_ARN=arn:aws:secretsmanager:us-east-1:123456789012:secret:purposepath/jwt-secret/dev
# OR for local dev
JWT_SECRET=your-local-jwt-secret-here

# Redis (optional for caching)
REDIS_CLUSTER_ENDPOINT=
REDIS_SSL=false
REDIS_PASSWORD=

# LLM Configuration
DEFAULT_LLM_PROVIDER=bedrock
DEFAULT_LLM_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

### Run Locally

**Option 1: Direct Python (Development)**

```bash
cd coaching
python -m uvicorn src.api.main_v2:app --reload --port 8000
```

Access at: http://localhost:8000
- API docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

**Option 2: SAM Local (Lambda Simulation)**

```bash
cd coaching

# Build
sam build

# Start local API
sam local start-api --port 3000

# Test with curl
curl http://localhost:3000/api/v1/health
```

**Option 3: Docker Compose (Full Stack)**

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  api:
    build: ./coaching
    ports:
      - "8000:8080"
    environment:
      - STAGE=local
      - LOG_LEVEL=DEBUG
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=us-east-1
    volumes:
      - ./coaching/src:/var/task/src

  dynamodb-local:
    image: amazon/dynamodb-local
    ports:
      - "8001:8000"
    command: -jar DynamoDBLocal.jar -sharedDb

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

Run: `docker-compose up`

---

## AWS SAM Deployment

### Build the Application

```bash
cd coaching

# Build Docker image
sam build
```

This will:
1. Build Docker image using `Dockerfile`
2. Install Python dependencies from `requirements.txt`
3. Package application code
4. Prepare CloudFormation template

### Deploy to AWS

**First-time deployment:**

```bash
sam deploy --guided
```

You'll be prompted for:
- **Stack Name**: `purposepath-coaching-api-dev`
- **AWS Region**: `us-east-1`
- **Parameter Stage**: `dev`
- **Parameter LogLevel**: `INFO`
- **Confirm changes before deploy**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`
- **Save arguments to samconfig.toml**: `Y`

**Subsequent deployments:**

```bash
sam deploy
```

### Deployment Parameters

Configure in `samconfig.toml` or pass via CLI:

```bash
sam deploy \
  --parameter-overrides \
    Stage=dev \
    LogLevel=INFO \
    NameSuffix=-v2 \
    EnableCustomDomain=false
```

**Available Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `Stage` | Deployment stage | `dev` |
| `LogLevel` | Logging level | `INFO` |
| `JwtSecretArn` | ARN of JWT secret (optional) | `` |
| `NameSuffix` | Resource name suffix | `-v2` |
| `EnableCustomDomain` | Use custom domain | `false` |
| `CustomDomainName` | Custom domain name | `` |
| `ApiMappingKey` | API mapping key | `coaching` |
| `SubnetIds` | VPC subnet IDs (optional) | `` |
| `LambdaSecurityGroupIds` | Security group IDs (optional) | `` |
| `RedisClusterEndpoint` | Redis endpoint (optional) | `` |

### Verify Deployment

```bash
# Get API endpoint
aws cloudformation describe-stacks \
  --stack-name purposepath-coaching-api-dev \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text

# Test health endpoint
curl https://<api-endpoint>/api/v1/health

# Test with authentication
curl -X POST https://<api-endpoint>/api/v1/conversations/initiate \
  -H "Authorization: Bearer <your-jwt-token>" \
  -H "Content-Type: application/json" \
  -d '{"topic": "core_values"}'
```

---

## Environment Configuration

### JWT Secret Setup

**Create JWT Secret:**

```bash
aws secretsmanager create-secret \
  --name purposepath/jwt-secret/dev \
  --description "JWT signing secret for PurposePath API" \
  --secret-string '{"secret":"<64-char-random-string>"}'
```

**Generate Random Secret:**

```python
import secrets
secret = secrets.token_urlsafe(64)
print(secret)
```

### S3 Prompt Bucket Setup

**Create bucket:**

```bash
aws s3 mb s3://purposepath-coaching-prompts-dev
```

**Upload prompt templates:**

```bash
cd coaching
aws s3 sync prompts/ s3://purposepath-coaching-prompts-dev/
```

**Prompt structure:**

```
s3://purposepath-coaching-prompts-dev/
├── coaching/
│   ├── core_values.yaml
│   ├── purpose.yaml
│   ├── vision.yaml
│   └── goals.yaml
└── analysis/
    ├── alignment.yaml
    ├── strategy.yaml
    ├── kpi.yaml
    └── operations.yaml
```

### DynamoDB Table Initialization

Tables are created automatically by SAM template. To pre-populate:

```python
import boto3

dynamodb = boto3.resource('dynamodb')

# Example: Add test data
table = dynamodb.Table('purposepath-conversations-dev-v2')
table.put_item(Item={
    'conversation_id': 'conv_test_123',
    'user_id': 'user_test',
    'tenant_id': 'tenant_test',
    'topic': 'core_values',
    'status': 'active',
    'created_at': '2025-10-10T00:00:00Z'
})
```

---

## Monitoring and Logging

### CloudWatch Logs

**View logs:**

```bash
sam logs -n CoachingApiFunction --stack-name purposepath-coaching-api-dev --tail
```

**Log groups:**
- `/aws/lambda/purposepath-coaching-api-dev-CoachingApiFunction-<hash>`

**Structured logging format:**

```json
{
  "timestamp": "2025-10-10T18:00:00.000Z",
  "level": "info",
  "event": "conversation_initiated",
  "conversation_id": "conv_abc123",
  "user_id": "user_123",
  "tenant_id": "tenant_456",
  "topic": "core_values"
}
```

### CloudWatch Metrics

**Custom metrics:**
- `ConversationInitiated` - Count of new conversations
- `MessageProcessed` - Count of messages processed
- `AnalysisRequested` - Count of analysis requests
- `APILatency` - Request latency
- `RateLimitExceeded` - Rate limit violations

**View metrics:**

```bash
aws cloudwatch get-metric-statistics \
  --namespace PurposePath/Coaching \
  --metric-name ConversationInitiated \
  --dimensions Name=Stage,Value=dev \
  --start-time 2025-10-10T00:00:00Z \
  --end-time 2025-10-10T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

### X-Ray Tracing

**Enable tracing** (already enabled in template):

```yaml
Tracing: Active
```

**View traces:**

```bash
# In AWS Console
# X-Ray → Service Map
# X-Ray → Traces
```

### Alarms

**Create CloudWatch alarm:**

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name purposepath-api-errors-dev \
  --alarm-description "Alert on API errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --dimensions Name=FunctionName,Value=purposepath-coaching-api-dev-CoachingApiFunction-<hash>
```

---

## Troubleshooting

### Common Issues

**1. Lambda Handler Not Found**

```
Error: Runtime.HandlerNotFound
```

**Solution:**
- Verify `CMD` in `Dockerfile` points to `src.api.main_v2.handler`
- Check file exists at `coaching/src/api/main_v2.py`
- Rebuild: `sam build --use-container`

**2. Import Errors**

```
Error: ModuleNotFoundError: No module named 'coaching'
```

**Solution:**
- Verify directory structure in Docker image
- Check `COPY` commands in `Dockerfile`
- Ensure `src` directory is copied

**3. JWT Validation Fails**

```
Error: 401 Unauthorized - "Invalid or expired token"
```

**Solution:**
- Verify JWT secret is accessible
- Check token format and claims
- Ensure `JWT_SECRET_ARN` environment variable is set

**4. DynamoDB Access Denied**

```
Error: AccessDeniedException
```

**Solution:**
- Verify Lambda execution role has DynamoDB permissions
- Check table names match environment variables
- Verify tables exist in correct region

**5. Rate Limit Issues**

```
Error: 429 Too Many Requests
```

**Solution:**
- Review rate limiting middleware configuration
- Adjust limits in `main_v2.py` if needed
- Implement client-side backoff

### Debug Mode

**Enable debug logging:**

```bash
sam deploy --parameter-overrides LogLevel=DEBUG
```

**Test locally with debug:**

```bash
LOG_LEVEL=DEBUG python -m uvicorn src.api.main_v2:app --reload
```

### Health Checks

**Verify all systems:**

```bash
# Health endpoint
curl https://<api-endpoint>/api/v1/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2025-10-10T18:00:00Z",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "llm": "healthy",
    "storage": "healthy"
  }
}
```

---

## Multi-Stage Deployment

### Stages

- **dev** - Development environment
- **staging** - Pre-production testing
- **prod** - Production environment

### Deploy to Staging

```bash
sam build
sam deploy \
  --stack-name purposepath-coaching-api-staging \
  --parameter-overrides Stage=staging LogLevel=INFO
```

### Deploy to Production

```bash
sam build
sam deploy \
  --stack-name purposepath-coaching-api-prod \
  --parameter-overrides \
    Stage=prod \
    LogLevel=WARNING \
    EnableCustomDomain=true \
    CustomDomainName=api.purposepath.ai
```

---

## Rollback

**Rollback to previous version:**

```bash
# List stack events
aws cloudformation describe-stack-events \
  --stack-name purposepath-coaching-api-dev

# Rollback
aws cloudformation rollback-stack \
  --stack-name purposepath-coaching-api-dev
```

**Or use SAM:**

```bash
aws cloudformation delete-stack \
  --stack-name purposepath-coaching-api-dev

# Redeploy previous version
git checkout <previous-commit>
sam build
sam deploy
```

---

## Cleanup

**Delete stack (warning: destroys all resources):**

```bash
sam delete --stack-name purposepath-coaching-api-dev
```

**Or manually:**

```bash
aws cloudformation delete-stack \
  --stack-name purposepath-coaching-api-dev
```

---

## Support

- **Documentation**: https://docs.purposepath.ai
- **API Reference**: [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Integration Guide**: [API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)
- **Support Email**: devops@purposepath.ai

---

**Last Updated**: October 10, 2025  
**Version**: 2.0.0  
**Architecture**: Phase 7 (Complete API Layer)
